#!/usr/bin/env python3
"""
GRU Neural Network Predictor — canonical multi-horizon implementation.

Direct multi-horizon output head: the network outputs prediction_horizon
values in a single forward pass, eliminating autoregressive error compounding.
The trained forecast contract matches the deployed inference contract exactly.

Artifact schema v2 includes: schema version, full model config, scaler state,
sample interval, horizon, per-horizon upper offsets (from validation residuals),
and empirical coverage statistics.

Per thesis section 3.4.1.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from dataclasses import dataclass

import structlog

logger = structlog.get_logger(__name__)

# Artifact schema version — v1 is the deprecated single-output format.
ARTIFACT_SCHEMA_VERSION = 2

# Max rows per forward pass during evaluation — large single batches hang
# some ROCm/gfx1103 stacks; eval math is batch-independent.
EVAL_CHUNK_SIZE = 512

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available, using sklearn MLPRegressor as fallback")


@dataclass
class GRUConfig:
    """Canonical GRU/LSTM model configuration.

    ``cell`` selects the recurrent cell ("gru" or "lstm"); both cells share
    the same network head, normalisation, splits, and serving contract.
    Artifacts record the trained cell; older artifacts default to "gru".

    Recurrent dropout is only meaningful for num_layers >= 2 (PyTorch nn.GRU
    ignores it for single-layer). head_dropout regularizes the output head
    independently and applies regardless of layer count.
    """

    input_size: int = 1  # Features per timestep
    cell: str = "gru"  # Recurrent cell: "gru" or "lstm"
    hidden_size: int = 128
    num_layers: int = 1
    dropout: float = 0.0  # Recurrent dropout (zero for single-layer GRU)
    head_dropout: float = 0.1  # Output head regularization (always active)
    sequence_length: int = 30  # Look-back window
    prediction_horizon: int = 5  # Direct multi-horizon steps
    sample_interval_sec: int = 15  # Sampling resolution matching control loop
    learning_rate: float = 0.000380
    batch_size: int = 32
    epochs: int = 100
    early_stopping_patience: int = 10

    def __post_init__(self) -> None:
        if self.cell not in ("gru", "lstm"):
            raise ValueError(f"cell must be 'gru' or 'lstm', got {self.cell!r}")

    @property
    def effective_recurrent_dropout(self) -> float:
        """Recurrent dropout applied to the RNN — zero for single-layer."""
        return self.dropout if self.num_layers > 1 else 0.0


if TORCH_AVAILABLE:

    class GRUNetwork(nn.Module):
        """GRU/LSTM network with direct multi-horizon output head.

        The recurrent cell is chosen by ``config.cell``; the module attribute
        stays ``gru`` so saved state-dict keys remain backward compatible.
        Outputs (batch, prediction_horizon) in a single forward pass.
        """

        def __init__(self, config: GRUConfig):
            super().__init__()
            self.config = config

            rnn_cls = nn.LSTM if config.cell == "lstm" else nn.GRU
            self.gru = rnn_cls(
                input_size=config.input_size,
                hidden_size=config.hidden_size,
                num_layers=config.num_layers,
                dropout=config.effective_recurrent_dropout,
                batch_first=True,
            )

            self.fc = nn.Sequential(
                nn.Linear(config.hidden_size, config.hidden_size // 2),
                nn.ReLU(),
                nn.Dropout(config.head_dropout),
                nn.Linear(config.hidden_size // 2, config.prediction_horizon),
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x shape: (batch, seq_len, input_size); nn.LSTM's extra state
            # tuple is discarded the same way as nn.GRU's hidden state.
            rnn_out, _ = self.gru(x)
            last_hidden = rnn_out[:, -1, :]
            output = self.fc(last_hidden)
            # output shape: (batch, prediction_horizon) — keep horizon dim
            return output


class GRUPredictor:
    """GRU-based multi-horizon workload predictor.

    Uses sliding window approach with direct multi-step output.
    Per-horizon upper offsets derived from validation residuals enable
    a conservative upper envelope for proactive scaling without runtime
    confidence multipliers.
    """

    def __init__(self, config: Optional[GRUConfig] = None):
        self.config = config or GRUConfig()
        self.model = None
        self.scaler_mean = 0.0
        self.scaler_std = 1.0
        self.is_trained = False
        self.training_history: List[Dict] = []
        # Indices of the last leak-free chronological split used by train()
        self.split_indices: Optional[Dict[str, int]] = None

        # Per-horizon upper offsets (90th percentile positive residuals)
        horizon = self.config.prediction_horizon
        self.upper_offsets: np.ndarray = np.zeros(horizon, dtype=np.float32)

        # Empirical coverage of upper envelope on validation data
        self.val_coverage: float = 0.0

        # Metrics
        self.rmse: Optional[float] = None
        self.mae: Optional[float] = None

        if TORCH_AVAILABLE:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = None

        logger.info(
            "GRUPredictor initialized",
            torch_available=TORCH_AVAILABLE,
            device=str(self.device) if self.device else "cpu",
            horizon=self.config.prediction_horizon,
            sample_interval_sec=self.config.sample_interval_sec,
        )

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    def _normalize(self, data: np.ndarray) -> np.ndarray:
        return (data - self.scaler_mean) / (self.scaler_std + 1e-8)

    def _denormalize(self, data: np.ndarray) -> np.ndarray:
        return data * self.scaler_std + self.scaler_mean

    # ------------------------------------------------------------------
    # Sequence creation (multi-horizon)
    # ------------------------------------------------------------------

    def _create_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create input sequences and multi-horizon targets.

        Each sample: X[i] = data[i:i+seq_len], y[i] = data[i+seq_len:i+seq_len+horizon]

        No input/target window crosses a split boundary when the caller splits
        at an index >= seq_len + horizon from both ends.
        """
        seq_len = self.config.sequence_length
        horizon = self.config.prediction_horizon

        X, y = [], []
        for i in range(len(data) - seq_len - horizon + 1):
            X.append(data[i : i + seq_len])
            y.append(data[i + seq_len : i + seq_len + horizon])

        return np.array(X), np.array(y)  # y shape: (n, horizon)

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(
        self,
        df: pd.DataFrame,
        val_ratio: float = 0.2,
        *,
        train_end: Optional[int] = None,
        val_start: Optional[int] = None,
        val_end: Optional[int] = None,
    ) -> Dict:
        """Train leak-free and compute per-horizon upper offsets.

        The scaler is fitted on the training portion only, and sliding
        windows are built per segment after the chronological split, so no
        window crosses a boundary. The embargo between the train and
        validation segments is at least ``sequence_length + horizon - 1``.

        Args:
            df: DataFrame with 'total_requests' or 'rps' column, sampled at
                config.sample_interval_sec resolution.
            val_ratio: Fraction of chronological samples for validation.
                0.0 trains on everything with no validation (final refit at
                a frozen epoch budget; upper offsets are left untouched).
            train_end: Exclusive end of the training portion (overrides
                val_ratio).
            val_start: First index of the validation portion (default
                train_end + embargo).
            val_end: Exclusive end of the validation portion (default end of
                series).

        Returns:
            Training metrics dictionary including per-horizon stats.
        """
        if "total_requests" in df.columns:
            values = df["total_requests"].values.astype(np.float32)
        elif "rps" in df.columns:
            values = df["rps"].values.astype(np.float32)
        else:
            raise ValueError("DataFrame must have 'total_requests' or 'rps' column")

        seq_len = self.config.sequence_length
        horizon = self.config.prediction_horizon
        embargo = seq_len + horizon - 1
        n = len(values)

        min_samples = seq_len + horizon + 10
        if n < min_samples:
            raise ValueError(f"Need at least {min_samples} samples")

        min_val_samples = seq_len + horizon + 1
        if train_end is None:
            train_end = int(n * (1 - val_ratio))
        if val_end is None:
            val_end = n
        if val_start is None:
            # Derived boundary: shift the split earlier if needed so the
            # validation slice can still form windows under the embargo.
            if train_end + embargo + min_val_samples > n:
                train_end = n - embargo - min_val_samples
            val_start = train_end + embargo

        if not 0 < train_end < n:
            raise ValueError(f"train_end must be in (0, {n}), got {train_end}")
        if val_start - train_end < embargo:
            raise ValueError(
                f"Embargo violation: val_start ({val_start}) must be at least "
                f"train_end + sequence_length + horizon - 1 ({train_end + embargo})"
            )
        if not train_end <= val_start <= val_end <= n:
            raise ValueError(f"Invalid split bounds: {train_end}, {val_start}, {val_end}, n={n}")

        train_values = values[:train_end]
        val_values = values[val_start:val_end]
        has_val = len(val_values) >= seq_len + horizon + 1

        if not has_val and val_ratio != 0.0:
            raise ValueError(
                f"Validation slice ({len(val_values)} samples) too small for "
                f"seq_len={seq_len} + horizon={horizon}; pass val_ratio=0.0 for a "
                "final refit without validation"
            )

        # Scaler fitted on the training portion only — validation and any
        # later holdout must not influence normalisation.
        self.scaler_mean = float(np.mean(train_values))
        self.scaler_std = float(np.std(train_values))

        self.split_indices = {
            "train_end": int(train_end),
            "val_start": int(val_start),
            "val_end": int(val_end),
            "embargo": int(embargo),
        }

        # Windows built per segment after the split — none crosses a boundary.
        X_train, y_train = self._create_sequences(self._normalize(train_values))

        logger.info(
            "Training model leak-free",
            cell=self.config.cell,
            train_samples=len(X_train),
            val_samples=(len(val_values) - seq_len - horizon + 1) if has_val else 0,
            sequence_length=seq_len,
            prediction_horizon=horizon,
            sample_interval_sec=self.config.sample_interval_sec,
        )

        # val_ratio == 0.0 is the final-refit contract: train on everything
        # up to train_end at a frozen epoch budget, with no early stopping
        # and no validation metrics — even if a slice exists past the
        # embargo, that slice must never influence the fit.
        if val_ratio == 0.0 or not has_val:
            metrics = self._train_final(X_train, y_train)
        elif TORCH_AVAILABLE:
            X_val, y_val = self._create_sequences(self._normalize(val_values))
            metrics = self._train_torch(X_train, y_train, X_val, y_val)
        else:
            X_val, y_val = self._create_sequences(self._normalize(val_values))
            metrics = self._train_sklearn(X_train, y_train, X_val, y_val)

        self.is_trained = True
        self.rmse = metrics.get("val_rmse")
        self.mae = metrics.get("val_mae")

        return metrics

    def _train_torch(self, X_train, y_train, X_val, y_val) -> Dict:
        """Train using PyTorch with direct multi-horizon output."""
        # Reshape for the recurrent cell: (batch, seq, features)
        X_train = X_train.reshape(-1, self.config.sequence_length, 1)
        X_val = X_val.reshape(-1, self.config.sequence_length, 1)

        train_dataset = TensorDataset(torch.FloatTensor(X_train), torch.FloatTensor(y_train))
        train_loader = DataLoader(train_dataset, batch_size=self.config.batch_size, shuffle=True)

        X_val_t = torch.FloatTensor(X_val).to(self.device)
        y_val_t = torch.FloatTensor(y_val).to(self.device)

        self.model = GRUNetwork(self.config).to(self.device)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.config.learning_rate)
        criterion = nn.MSELoss()
        best_val_loss = float("inf")
        best_state = None
        best_epoch = -1
        patience_counter = 0

        for epoch in range(self.config.epochs):
            self.model.train()
            train_loss = 0.0

            for batch_X, batch_y in train_loader:
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device)

                optimizer.zero_grad()
                predictions = self.model(batch_X)  # (batch, horizon)
                loss = criterion(predictions, batch_y)
                loss.backward()
                optimizer.step()

                train_loss += loss.item()

            train_loss /= len(train_loader)

            self.model.eval()
            with torch.no_grad():
                # Large single forward passes hang some ROCm stacks; eval
                # math is batch-independent, so slice into fixed chunks.
                val_parts = [
                    self.model(X_val_t[i : i + EVAL_CHUNK_SIZE]) for i in range(0, len(X_val_t), EVAL_CHUNK_SIZE)
                ]
                val_pred = torch.cat(val_parts)
                val_loss = criterion(val_pred, y_val_t).item()

            self.training_history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss})

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_state = {k: v.clone() for k, v in self.model.state_dict().items()}
                best_epoch = epoch
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= self.config.early_stopping_patience:
                    logger.info("Early stopping", epoch=epoch)
                    break

            if epoch % 10 == 0:
                logger.debug("Training progress", epoch=epoch, train_loss=train_loss, val_loss=val_loss)

        # Restore best model
        if best_state is not None:
            self.model.load_state_dict(best_state)

        # Recompute val predictions with best model for upper offsets
        self.model.eval()
        with torch.no_grad():
            val_parts = [self.model(X_val_t[i : i + EVAL_CHUNK_SIZE]) for i in range(0, len(X_val_t), EVAL_CHUNK_SIZE)]
            val_pred = torch.cat(val_parts).cpu().numpy()

        metrics = self._compute_val_metrics(val_pred, y_val)
        metrics["best_epoch"] = int(best_epoch)
        return metrics

    def _train_sklearn(self, X_train, y_train, X_val, y_val) -> Dict:
        """Fallback training using sklearn MLPRegressor (multi-output)."""
        from sklearn.neural_network import MLPRegressor

        X_train_flat = X_train.reshape(len(X_train), -1)
        X_val_flat = X_val.reshape(len(X_val), -1)

        self.model = MLPRegressor(
            hidden_layer_sizes=(64, 32), max_iter=500, early_stopping=True, validation_fraction=0.1, random_state=42
        )

        self.model.fit(X_train_flat, y_train)

        val_pred = self.model.predict(X_val_flat)
        return self._compute_val_metrics(val_pred, y_val)

    def _train_final(self, X_train, y_train) -> Dict:
        """Final refit on train+validation at a frozen epoch budget.

        No internal validation and no early stopping: the model trains for
        exactly ``config.epochs`` epochs. Upper offsets are left untouched —
        callers carry them over from the selection fit.
        """
        if TORCH_AVAILABLE:
            X_train = X_train.reshape(-1, self.config.sequence_length, 1)
            train_dataset = TensorDataset(torch.FloatTensor(X_train), torch.FloatTensor(y_train))
            train_loader = DataLoader(train_dataset, batch_size=self.config.batch_size, shuffle=True)

            self.model = GRUNetwork(self.config).to(self.device)
            optimizer = torch.optim.Adam(self.model.parameters(), lr=self.config.learning_rate)
            criterion = nn.MSELoss()

            self.model.train()
            for _epoch in range(self.config.epochs):
                epoch_loss = 0.0
                for batch_X, batch_y in train_loader:
                    batch_X = batch_X.to(self.device)
                    batch_y = batch_y.to(self.device)
                    optimizer.zero_grad()
                    loss = criterion(self.model(batch_X), batch_y)
                    loss.backward()
                    optimizer.step()
                    epoch_loss += loss.item()
                epoch_loss /= max(len(train_loader), 1)
                self.training_history.append({"epoch": _epoch, "train_loss": epoch_loss, "val_loss": float("nan")})

            return {
                "epochs_trained": self.config.epochs,
                "final_fit": True,
                "train_rmse_norm": float(np.sqrt(epoch_loss)),
            }

        from sklearn.neural_network import MLPRegressor

        X_train_flat = X_train.reshape(len(X_train), -1)
        self.model = MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=self.config.epochs, random_state=42)
        self.model.fit(X_train_flat, y_train)
        return {"epochs_trained": self.config.epochs, "final_fit": True}

    def _compute_val_metrics(self, val_pred_norm: np.ndarray, y_val_norm: np.ndarray) -> Dict:
        """Compute validation metrics and per-horizon upper offsets.

        Upper offset per horizon = 90th percentile of positive residuals
        (actual - prediction) on validation data. This directly addresses
        ramp underprediction without runtime confidence multipliers.
        """
        horizon = self.config.prediction_horizon

        # Denormalize
        val_pred_denorm = self._denormalize(val_pred_norm)
        y_val_denorm = self._denormalize(y_val_norm)

        residuals = y_val_denorm - val_pred_denorm  # (n_val, horizon)

        # Per-horizon metrics
        rmse_per_h = np.sqrt(np.mean(residuals**2, axis=0))
        mae_per_h = np.mean(np.abs(residuals), axis=0)

        # Overall (denormalized)
        rmse = float(np.sqrt(np.mean(residuals**2)))
        mae = float(np.mean(np.abs(residuals)))
        avg_val = float(np.mean(y_val_denorm))

        # Per-horizon upper offsets: 90th percentile of positive residuals
        upper_offsets = np.zeros(horizon, dtype=np.float32)
        for h in range(horizon):
            positive_res = residuals[:, h][residuals[:, h] > 0]
            if len(positive_res) > 0:
                upper_offsets[h] = np.percentile(positive_res, 90)
            else:
                upper_offsets[h] = 0.0

        self.upper_offsets = upper_offsets

        # Upper envelope coverage: fraction of rising targets covered
        rising_mask = y_val_denorm > val_pred_denorm  # actual > predicted
        upper_forecasts = val_pred_denorm + upper_offsets[np.newaxis, :]
        covered = y_val_denorm <= upper_forecasts
        # Coverage among rising targets
        rising_count = int(rising_mask.sum())
        if rising_count > 0:
            self.val_coverage = float(covered[rising_mask].mean())
        else:
            self.val_coverage = 1.0

        # Per-horizon underprediction on rising targets
        underpred_per_h = []
        for h in range(horizon):
            h_rising = y_val_denorm[:, h] > val_pred_denorm[:, h]
            if h_rising.sum() > 0:
                underpred_per_h.append(float(np.mean(residuals[h_rising, h])))
            else:
                underpred_per_h.append(0.0)

        return {
            "val_rmse": rmse,
            "val_mae": mae,
            "val_rmse_percent": (rmse / avg_val) * 100 if avg_val > 0 else 0.0,
            "epochs_trained": len(self.training_history),
            "best_val_loss": float(min(h["val_loss"] for h in self.training_history)) if self.training_history else 0.0,
            "rmse_per_horizon": [float(r) for r in rmse_per_h],
            "mae_per_horizon": [float(m) for m in mae_per_h],
            "upper_offsets": [float(o) for o in upper_offsets],
            "val_upper_coverage": self.val_coverage,
            "underprediction_rising": underpred_per_h,
        }

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict(self, recent_values: np.ndarray) -> Dict:
        """Predict multi-horizon workload from recent history.

        Returns point forecasts, upper envelope forecasts, and a conservative
        scalar ``predicted_requests`` (max of upper forecasts) for backward
        compatibility with the HTTP/controller contract.
        """
        if not self.is_trained:
            raise RuntimeError("Model not trained")

        values = recent_values[-self.config.sequence_length :]
        if len(values) < self.config.sequence_length:
            padding = np.full(self.config.sequence_length - len(values), self.scaler_mean)
            values = np.concatenate([padding, values])

        normalized = self._normalize(values.astype(np.float32))

        if TORCH_AVAILABLE and isinstance(self.model, nn.Module):
            self.model.eval()
            with torch.no_grad():
                X = torch.FloatTensor(normalized).reshape(1, -1, 1).to(self.device)
                pred_norm = self.model(X).cpu().numpy()[0]  # (horizon,)
        else:
            if self.model is None:
                raise RuntimeError("No model loaded for prediction")
            X = normalized.reshape(1, -1)
            pred_norm = self.model.predict(X)[0]  # (horizon,)

        point_forecasts = self._denormalize(pred_norm)
        point_forecasts = np.maximum(0, point_forecasts)

        upper_forecasts = point_forecasts + self.upper_offsets
        upper_forecasts = np.maximum(0, upper_forecasts)

        # Conservative scalar: max of upper forecasts across all horizons
        predicted_requests = float(np.max(upper_forecasts))

        confidence = 0.8 if self.rmse and self.scaler_mean > 0 and (self.rmse / self.scaler_mean) < 0.15 else 0.6

        return {
            "predicted_requests": predicted_requests,
            "confidence": confidence,
            "point_forecasts": [float(f) for f in point_forecasts],
            "upper_forecasts": [float(f) for f in upper_forecasts],
            "horizon": self.config.prediction_horizon,
            "sample_interval_sec": self.config.sample_interval_sec,
            "model_rmse": self.rmse,
        }

    # ------------------------------------------------------------------
    # Artifact save/load (schema v2)
    # ------------------------------------------------------------------

    def save_model(self, path: Path) -> None:
        """Save trained model as versioned artifact (schema v2)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        metadata: Dict[str, Any] = {
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            "sample_interval_sec": self.config.sample_interval_sec,
            "prediction_horizon": self.config.prediction_horizon,
            "cell": self.config.cell,
            "scaler_mean": self.scaler_mean,
            "scaler_std": self.scaler_std,
            "config": self.config.__dict__,
            "upper_offsets": [float(o) for o in self.upper_offsets],
            "val_coverage": self.val_coverage,
            "rmse": self.rmse,
            "mae": self.mae,
            "is_trained": self.is_trained,
        }

        if TORCH_AVAILABLE and isinstance(self.model, nn.Module):
            torch.save({"model_state": self.model.state_dict(), "metadata": metadata}, path)
        else:
            import joblib

            joblib.dump({"model": self.model, "metadata": metadata}, path)

        # Also save a human-readable sidecar JSON
        sidecar = path.with_suffix(".json")
        sidecar.write_text(json.dumps(metadata, indent=2, default=str))

        logger.info("Model saved", path=str(path), schema_version=ARTIFACT_SCHEMA_VERSION)

    def load_model(self, path: Path) -> bool:
        """Load trained model from versioned artifact.

        Rejects schema v1 artifacts (single-output, incompatible architecture)
        and incomplete artifacts. Returns False on any incompatibility.
        """
        path = Path(path)
        if not path.exists():
            return False

        try:
            if TORCH_AVAILABLE and str(path).endswith(".pt"):
                checkpoint = torch.load(path, map_location=self.device, weights_only=False)
            else:
                import joblib

                checkpoint = joblib.load(path)

            metadata = checkpoint["metadata"]

            # Strict schema version check
            version = metadata.get("schema_version", 1)
            if version < ARTIFACT_SCHEMA_VERSION:
                logger.error(
                    "Artifact schema deprecated",
                    found=version,
                    required=ARTIFACT_SCHEMA_VERSION,
                    path=str(path),
                )
                return False

            config_dict = metadata["config"]
            self.config = GRUConfig(**config_dict)

            horizon = self.config.prediction_horizon
            self.upper_offsets = np.array(metadata.get("upper_offsets", [0.0] * horizon), dtype=np.float32)
            self.val_coverage = float(metadata.get("val_coverage", 0.0))

            if TORCH_AVAILABLE and "model_state" in checkpoint:
                self.model = GRUNetwork(self.config).to(self.device)
                self.model.load_state_dict(checkpoint["model_state"])
                self.model.eval()
            elif "model" in checkpoint:
                self.model = checkpoint["model"]
            else:
                logger.error("Artifact missing model data", path=str(path))
                return False

            self.scaler_mean = metadata["scaler_mean"]
            self.scaler_std = metadata["scaler_std"]
            self.rmse = metadata.get("rmse")
            self.mae = metadata.get("mae")
            self.is_trained = True

            logger.info(
                "Model loaded",
                path=str(path),
                schema_version=version,
                horizon=horizon,
                sample_interval_sec=self.config.sample_interval_sec,
                val_coverage=self.val_coverage,
            )
            return True

        except Exception as e:
            logger.error("Failed to load model", error=str(e), path=str(path))
            return False
