#!/usr/bin/env python3
"""
GRU Neural Network Predictor.

Implements workload prediction using Gated Recurrent Units per thesis section 3.4.1.
Target: RMSE < 10% of average traffic.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass

import structlog

logger = structlog.get_logger(__name__)

# Try to import PyTorch, fall back to sklearn if not available
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
    """GRU model configuration."""

    input_size: int = 1  # Features per timestep
    hidden_size: int = 64
    num_layers: int = 2
    dropout: float = 0.2
    sequence_length: int = 30  # Look-back window
    prediction_horizon: int = 1  # Steps ahead to predict
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 100
    early_stopping_patience: int = 10


if TORCH_AVAILABLE:

    class GRUNetwork(nn.Module):
        """GRU neural network for time series prediction."""

        def __init__(self, config: GRUConfig):
            super().__init__()
            self.config = config

            self.gru = nn.GRU(
                input_size=config.input_size,
                hidden_size=config.hidden_size,
                num_layers=config.num_layers,
                dropout=config.dropout if config.num_layers > 1 else 0,
                batch_first=True,
            )

            self.fc = nn.Sequential(
                nn.Linear(config.hidden_size, config.hidden_size // 2),
                nn.ReLU(),
                nn.Dropout(config.dropout),
                nn.Linear(config.hidden_size // 2, 1),
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x shape: (batch, seq_len, input_size)
            gru_out, _ = self.gru(x)
            # Take last timestep
            last_hidden = gru_out[:, -1, :]
            output = self.fc(last_hidden)
            return output.squeeze(-1)


class GRUPredictor:
    """
    GRU-based workload predictor per thesis section 3.4.1.

    Uses sliding window approach for sequence prediction.
    """

    def __init__(self, config: Optional[GRUConfig] = None):
        self.config = config or GRUConfig()
        self.model = None
        self.scaler_mean = 0.0
        self.scaler_std = 1.0
        self.is_trained = False
        self.training_history: List[Dict] = []

        # Metrics
        self.rmse = None
        self.mae = None
        self.r2_score = None

        if TORCH_AVAILABLE:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = None

        logger.info(
            "GRUPredictor initialized",
            torch_available=TORCH_AVAILABLE,
            device=str(self.device) if self.device else "cpu",
        )

    def _normalize(self, data: np.ndarray) -> np.ndarray:
        """Normalize data using stored statistics."""
        return (data - self.scaler_mean) / (self.scaler_std + 1e-8)

    def _denormalize(self, data: np.ndarray) -> np.ndarray:
        """Denormalize data using stored statistics."""
        return data * self.scaler_std + self.scaler_mean

    def _create_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create input sequences and targets for training."""
        seq_len = self.config.sequence_length
        horizon = self.config.prediction_horizon

        X, y = [], []
        for i in range(len(data) - seq_len - horizon + 1):
            X.append(data[i : i + seq_len])
            y.append(data[i + seq_len + horizon - 1])

        return np.array(X), np.array(y)

    def train(self, df: pd.DataFrame, val_ratio: float = 0.2) -> Dict:
        """
        Train GRU model on traffic data.

        Args:
            df: DataFrame with 'total_requests' or 'rps' column
            val_ratio: Validation split ratio

        Returns:
            Training metrics dictionary
        """
        # Extract values
        if "total_requests" in df.columns:
            values = df["total_requests"].values.astype(np.float32)
        elif "rps" in df.columns:
            values = df["rps"].values.astype(np.float32)
        else:
            raise ValueError("DataFrame must have 'total_requests' or 'rps' column")

        if len(values) < self.config.sequence_length + 10:
            raise ValueError(f"Need at least {self.config.sequence_length + 10} samples")

        # Store normalization parameters
        self.scaler_mean = float(np.mean(values))
        self.scaler_std = float(np.std(values))

        # Normalize
        normalized = self._normalize(values)

        # Create sequences
        X, y = self._create_sequences(normalized)

        # Split train/val
        split_idx = int(len(X) * (1 - val_ratio))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        logger.info(
            "Training GRU model",
            train_samples=len(X_train),
            val_samples=len(X_val),
            sequence_length=self.config.sequence_length,
        )

        if TORCH_AVAILABLE:
            metrics = self._train_torch(X_train, y_train, X_val, y_val)
        else:
            metrics = self._train_sklearn(X_train, y_train, X_val, y_val)

        self.is_trained = True
        self.rmse = metrics.get("val_rmse")
        self.mae = metrics.get("val_mae")

        return metrics

    def _train_torch(self, X_train, y_train, X_val, y_val) -> Dict:
        """Train using PyTorch."""
        # Reshape for GRU: (batch, seq, features)
        X_train = X_train.reshape(-1, self.config.sequence_length, 1)
        X_val = X_val.reshape(-1, self.config.sequence_length, 1)

        # Create tensors
        train_dataset = TensorDataset(torch.FloatTensor(X_train), torch.FloatTensor(y_train))
        train_loader = DataLoader(train_dataset, batch_size=self.config.batch_size, shuffle=True)

        X_val_t = torch.FloatTensor(X_val).to(self.device)
        y_val_t = torch.FloatTensor(y_val).to(self.device)

        # Initialize model
        self.model = GRUNetwork(self.config).to(self.device)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.config.learning_rate)
        criterion = nn.MSELoss()

        # Training loop
        best_val_loss = float("inf")
        patience_counter = 0

        for epoch in range(self.config.epochs):
            self.model.train()
            train_loss = 0.0

            for batch_X, batch_y in train_loader:
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device)

                optimizer.zero_grad()
                predictions = self.model(batch_X)
                loss = criterion(predictions, batch_y)
                loss.backward()
                optimizer.step()

                train_loss += loss.item()

            train_loss /= len(train_loader)

            # Validation
            self.model.eval()
            with torch.no_grad():
                val_pred = self.model(X_val_t)
                val_loss = criterion(val_pred, y_val_t).item()

            self.training_history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss})

            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= self.config.early_stopping_patience:
                    logger.info("Early stopping", epoch=epoch)
                    break

            if epoch % 10 == 0:
                logger.debug("Training progress", epoch=epoch, train_loss=train_loss, val_loss=val_loss)

        # Calculate final metrics
        self.model.eval()
        with torch.no_grad():
            val_pred = self.model(X_val_t).cpu().numpy()

        # Denormalize for metrics
        val_pred_denorm = self._denormalize(val_pred)
        y_val_denorm = self._denormalize(y_val)

        rmse = np.sqrt(np.mean((val_pred_denorm - y_val_denorm) ** 2))
        mae = np.mean(np.abs(val_pred_denorm - y_val_denorm))
        avg_val = np.mean(y_val_denorm)

        return {
            "val_rmse": rmse,
            "val_mae": mae,
            "val_rmse_percent": (rmse / avg_val) * 100,
            "epochs_trained": len(self.training_history),
            "best_val_loss": best_val_loss,
        }

    def _train_sklearn(self, X_train, y_train, X_val, y_val) -> Dict:
        """Fallback training using sklearn MLPRegressor."""
        from sklearn.neural_network import MLPRegressor

        # Flatten sequences for MLP
        X_train_flat = X_train.reshape(len(X_train), -1)
        X_val_flat = X_val.reshape(len(X_val), -1)

        self.model = MLPRegressor(
            hidden_layer_sizes=(64, 32), max_iter=500, early_stopping=True, validation_fraction=0.1, random_state=42
        )

        self.model.fit(X_train_flat, y_train)

        val_pred = self.model.predict(X_val_flat)
        val_pred_denorm = self._denormalize(val_pred)
        y_val_denorm = self._denormalize(y_val)

        rmse = np.sqrt(np.mean((val_pred_denorm - y_val_denorm) ** 2))
        mae = np.mean(np.abs(val_pred_denorm - y_val_denorm))
        avg_val = np.mean(y_val_denorm)

        return {
            "val_rmse": rmse,
            "val_mae": mae,
            "val_rmse_percent": (rmse / avg_val) * 100,
            "epochs_trained": self.model.n_iter_,
            "model_type": "sklearn_mlp",
        }

    def predict(self, recent_values: np.ndarray) -> Dict:
        """
        Predict next value given recent history.

        Args:
            recent_values: Array of recent values (length >= sequence_length)

        Returns:
            Prediction dictionary with predicted value and confidence
        """
        if not self.is_trained:
            raise RuntimeError("Model not trained")

        # Use last sequence_length values
        values = recent_values[-self.config.sequence_length :]
        if len(values) < self.config.sequence_length:
            # Pad with mean if not enough history
            padding = np.full(self.config.sequence_length - len(values), self.scaler_mean)
            values = np.concatenate([padding, values])

        # Normalize
        normalized = self._normalize(values.astype(np.float32))

        if TORCH_AVAILABLE and isinstance(self.model, nn.Module):
            self.model.eval()
            with torch.no_grad():
                X = torch.FloatTensor(normalized).reshape(1, -1, 1).to(self.device)
                pred_norm = self.model(X).cpu().numpy()[0]
        else:
            X = normalized.reshape(1, -1)
            pred_norm = self.model.predict(X)[0]

        predicted = self._denormalize(pred_norm)

        return {
            "predicted_requests": float(max(0, predicted)),
            "confidence": 0.8 if self.rmse and (self.rmse / self.scaler_mean) < 0.15 else 0.6,
            "model_rmse": self.rmse,
        }

    def save_model(self, path: Path):
        """Save trained model."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        metadata = {
            "scaler_mean": self.scaler_mean,
            "scaler_std": self.scaler_std,
            "config": self.config.__dict__,
            "rmse": self.rmse,
            "mae": self.mae,
            "is_trained": self.is_trained,
        }

        if TORCH_AVAILABLE and isinstance(self.model, nn.Module):
            import torch

            torch.save({"model_state": self.model.state_dict(), "metadata": metadata}, path)
        else:
            import joblib

            joblib.dump({"model": self.model, "metadata": metadata}, path)

        logger.info("Model saved", path=str(path))

    def load_model(self, path: Path) -> bool:
        """Load trained model."""
        path = Path(path)
        if not path.exists():
            return False

        try:
            if TORCH_AVAILABLE and str(path).endswith(".pt"):
                import torch

                checkpoint = torch.load(path, map_location=self.device, weights_only=False)
                metadata = checkpoint["metadata"]

                self.config = GRUConfig(**metadata["config"])
                self.model = GRUNetwork(self.config).to(self.device)
                self.model.load_state_dict(checkpoint["model_state"])
            else:
                import joblib

                data = joblib.load(path)
                metadata = data["metadata"]
                self.model = data["model"]

            self.scaler_mean = metadata["scaler_mean"]
            self.scaler_std = metadata["scaler_std"]
            self.rmse = metadata.get("rmse")
            self.mae = metadata.get("mae")
            self.is_trained = True

            logger.info("Model loaded", path=str(path))
            return True

        except Exception as e:
            logger.error("Failed to load model", error=str(e))
            return False
