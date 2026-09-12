"""One-lever-at-a-time GRU probe harness against OLS autoregression.

Frozen measurement contract (from the probe task; do not redesign):

- Series: ClarkNet 15 s resampled series (``load_clarknet_series``) multiplied
  by the replay manifest ``scale_factor`` (``manifest_scale_factor``), exactly
  as the leak-free study produces it.
- Train on ``[0, 26205)`` (the study's train+validation region), evaluate on
  ``[26243, end)``. The replay window ``[28940, 29020]`` stays inside the test
  region and out of training. Every 30-sample-window variant scores on
  identical windows: same origins, same targets.
- Each variant isolates ONE modern lever. ``window120`` is the sanctioned
  exception: its boundaries are derived (recorded in its JSON) because a
  120-sample window cannot satisfy the frozen 38-sample embargo gaps.
- Baselines scored alongside every variant on the same windows: OLS
  autoregression on the same input window (fitted on the training region
  only), persistence, linear trend, seasonal naive.
- Metrics per arm: RMSE, MAE, RMSE as a percentage of the mean target, skill
  against persistence and against the OLS arm, mean and p90 under-prediction
  on rising targets, per-horizon RMSE for steps 1..9.
- Training budget: 200 epochs, early-stopping patience 25, seeds 42/43/44 by
  default, deterministic via ``_set_deterministic``. Early stopping validates
  on the study's frozen validation region — never on the test region.

The OLS arm is fitted on ``values[:val_end]`` (the training region) only and
scored on the same test windows as the network, so a variant JSON directly
answers "did this lever beat linear on the held-out region?".
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import numpy as np
import structlog
from prediction.gru_predictor import GRUConfig, GRUPredictor
from shared.stats import cohens_d_paired, paired_permutation_test

from experiment.tuning.gru_hpo import (
    DEFAULT_HORIZON,
    EVAL_CHUNK_SIZE,
    FIXED_BATCH_SIZE,
    FIXED_SAMPLE_INTERVAL,
    PROJECT_ROOT,
    _make_sequences,
    _set_deterministic,
    evaluate_on_values,
    linear_trend_baseline,
    persistence_baseline,
    seasonal_naive_baseline,
)
from experiment.tuning.gru_study import (
    CLARKNET_TEST_START,
    CLARKNET_TRAIN_END,
    CLARKNET_VAL_END,
    CLARKNET_VAL_START,
    DEFAULT_SEASON,
    _torch_device,
    build_splits,
    load_clarknet_series,
    manifest_scale_factor,
)

logger = structlog.get_logger(__name__)

# Ticket literal for the window120 embargo. The formula minimum is
# 120 + 9 - 1 = 128; the task pins 382, which is strictly stronger and still
# keeps the replay window inside the test region. Both numbers are recorded.
WINDOW120_EMBARGO = 382
WINDOW120_FORMULA_MIN = 120 + DEFAULT_HORIZON - 1
WINDOW120_VAL_SPAN = 500

PROBE_REPLAY_WINDOW = (28940, 29020)

PINBALL_QUANTILE = 0.9

VARIANTS = ("baseline", "window120", "calendar", "revin", "log_target", "pinball", "ensemble")

DEFAULT_STUDY_BUNDLE = PROJECT_ROOT / "results" / "models" / "gru" / "study"

_EPS = 1e-8


# ── Split boundaries ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ProbeWindows:
    """Probe split boundaries in full-series index space.

    Network fit uses ``[0, fit_end)`` with early stopping on
    ``[val_start, val_end)`` (the study's frozen validation region for
    30-sample windows). The test region ``[test_start, n_total)`` is scored
    once. Every gap is at least ``seq_len + horizon - 1``.
    """

    seq_len: int
    horizon: int
    fit_end: int
    val_start: int
    val_end: int
    test_start: int
    embargo_used: int

    @property
    def embargo_min(self) -> int:
        return self.seq_len + self.horizon - 1

    def __post_init__(self) -> None:
        if self.val_start - self.fit_end < self.embargo_min:
            raise ValueError(f"fit→val gap {self.val_start - self.fit_end} < embargo {self.embargo_min}")
        if self.test_start - self.val_end < self.embargo_min:
            raise ValueError(f"val→test gap {self.test_start - self.val_end} < embargo {self.embargo_min}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "seq_len": self.seq_len,
            "horizon": self.horizon,
            "fit_end": self.fit_end,
            "val_start": self.val_start,
            "val_end": self.val_end,
            "test_start": self.test_start,
            "embargo_min_required": self.embargo_min,
            "embargo_used": self.embargo_used,
            "train_region": [0, self.val_end],
            "test_region": [self.test_start, "end"],
        }


def probe_windows(variant: str, n_total: int = 40315) -> ProbeWindows:
    """Frozen boundaries for 30-sample variants; derived ones for window120."""
    if variant == "window120":
        val_end = CLARKNET_VAL_END
        fit_end = val_end - WINDOW120_EMBARGO - WINDOW120_VAL_SPAN
        val_start = fit_end + WINDOW120_FORMULA_MIN
        windows = ProbeWindows(
            seq_len=120,
            horizon=DEFAULT_HORIZON,
            fit_end=fit_end,
            val_start=val_start,
            val_end=val_end,
            test_start=val_end + WINDOW120_EMBARGO,
            embargo_used=WINDOW120_EMBARGO,
        )
        replay_start, replay_end = PROBE_REPLAY_WINDOW
        if windows.test_start > replay_start:
            raise ValueError(
                f"derived test_start {windows.test_start} pushes the replay window "
                f"({replay_start}, {replay_end}) out of the test region"
            )
        return windows

    splits = build_splits(n_total, seq_len=30, horizon=DEFAULT_HORIZON, source="clarknet")
    if (splits.train_end, splits.val_start, splits.val_end, splits.test_start) != (
        CLARKNET_TRAIN_END,
        CLARKNET_VAL_START,
        CLARKNET_VAL_END,
        CLARKNET_TEST_START,
    ):
        raise ValueError("frozen ClarkNet boundaries changed; probe contract is stale")
    return ProbeWindows(
        seq_len=30,
        horizon=DEFAULT_HORIZON,
        fit_end=splits.train_end,
        val_start=splits.val_start,
        val_end=splits.val_end,
        test_start=splits.test_start,
        embargo_used=splits.test_start - splits.val_end,
    )


# ── Window construction with global indices ──────────────────────────────────


def _segment_sequences(
    series: np.ndarray,
    seg_start: int,
    seg_end: int,
    seq_len: int,
    horizon: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Windows inside ``series[seg_start:seg_end]`` plus global start indices.

    ``base[i]`` is the full-series index of window ``i``'s first input step, so
    window ``i`` consumes global indices ``base[i] .. base[i] + seq_len +
    horizon - 1`` — all inside ``[seg_start, seg_end)`` by construction.
    """
    X, y, last_inputs = _make_sequences(series[seg_start:seg_end], seq_len, horizon)
    base = np.arange(len(X), dtype=np.int64) + seg_start
    return X, y, last_inputs, base


def segment_index_matrix(seg_start: int, seg_end: int, seq_len: int, horizon: int) -> np.ndarray:
    """Global indices consumed by every window in ``[seg_start, seg_end)``."""
    n_seq = (seg_end - seg_start) - seq_len - horizon + 1
    if n_seq <= 0:
        raise ValueError(f"segment [{seg_start}, {seg_end}) too small for seq={seq_len}, horizon={horizon}")
    base = np.arange(n_seq, dtype=np.int64) + seg_start
    return base[:, None] + np.arange(seq_len + horizon, dtype=np.int64)[None, :]


# ── OLS autoregression arm (fitted on the training region only) ──────────────


def ols_autoreg_fit(values: np.ndarray, windows: ProbeWindows) -> np.ndarray:
    """Least-squares AR(seq_len) → horizon coefficients from the training region.

    Uses ``values[:val_end]`` (the full training region) exclusively; the test
    region never influences the fit.
    """
    X, y, _, _ = _segment_sequences(values, 0, windows.val_end, windows.seq_len, windows.horizon)
    design = np.hstack([np.ones((len(X), 1)), X.astype(np.float64)])
    coef, *_ = np.linalg.lstsq(design, y.astype(np.float64), rcond=None)
    return coef  # (seq_len + 1, horizon)


def ols_autoreg_predict(coef: np.ndarray, X_windows: np.ndarray) -> np.ndarray:
    """Predict from raw input windows using fitted AR coefficients."""
    design = np.hstack([np.ones((len(X_windows), 1)), X_windows.astype(np.float64)])
    return design @ coef


# ── Variant feature construction ─────────────────────────────────────────────


@dataclass
class VariantArrays:
    """Normalised network inputs plus raw scoring targets for one variant."""

    variant: str
    mode: str  # "zscore" | "revin"
    log_space: bool
    seq_len: int
    horizon: int
    X_fit: np.ndarray  # (n, seq_len, F)
    y_fit: np.ndarray  # (n, horizon) normalised targets
    X_val: np.ndarray
    y_val: np.ndarray
    X_test: np.ndarray  # (n_test, seq_len, F) normalised
    y_test_raw: np.ndarray  # (n_test, horizon) original RPS scale
    last_test_raw: np.ndarray  # (n_test,) original scale
    z_mean: float = 0.0
    z_std: float = 1.0
    test_mu: np.ndarray | None = None  # revin per-window means (n_test,)
    test_sd: np.ndarray | None = None  # revin per-window stds (n_test,)

    def denormalize_predictions(self, preds_norm: np.ndarray) -> np.ndarray:
        """Map normalised network outputs back to the original RPS scale."""
        if self.mode == "revin":
            if self.test_sd is None or self.test_mu is None:
                raise ValueError("revin variant is missing its per-window statistics")
            preds = preds_norm * self.test_sd[:, None] + self.test_mu[:, None]
        else:
            preds = preds_norm * self.z_std + self.z_mean
        if self.log_space:
            preds = np.expm1(preds)
        return preds


def _calendar_features(base: np.ndarray, seq_len: int) -> np.ndarray:
    """Sine/cosine time-of-day per step, in [-1, 1], from global indices.

    One day = 86400 s / 15 s = 5760 samples, matching DEFAULT_SEASON.
    """
    steps = base[:, None] + np.arange(seq_len, dtype=np.int64)[None, :]
    phase = (steps * FIXED_SAMPLE_INTERVAL) % 86400 / 86400 * 2.0 * np.pi
    return np.stack([np.sin(phase), np.cos(phase)], axis=-1).astype(np.float32)


def _revin_normalize(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Instance-normalise each window with its own statistics only."""
    mu = X.mean(axis=1)
    sd = X.std(axis=1) + _EPS
    X_norm = (X - mu[:, None]) / sd[:, None]
    y_norm = (y - mu[:, None]) / sd[:, None]
    return X_norm.astype(np.float32), y_norm.astype(np.float32), mu.astype(np.float32), sd.astype(np.float32)


def build_variant_arrays(variant: str, values: np.ndarray, windows: ProbeWindows) -> VariantArrays:
    """Build fit/val/test arrays isolating exactly one lever."""
    seq, horizon = windows.seq_len, windows.horizon
    log_space = variant == "log_target"
    series = np.log1p(values.astype(np.float64)) if log_space else values.astype(np.float64)

    X_fit_s, y_fit_s, _, base_fit = _segment_sequences(series, 0, windows.fit_end, seq, horizon)
    X_val_s, y_val_s, _, base_val = _segment_sequences(series, windows.val_start, windows.val_end, seq, horizon)
    X_test_s, _, _, base_test = _segment_sequences(series, windows.test_start, len(values), seq, horizon)

    if variant == "revin":
        X_fit, y_fit, _, _ = _revin_normalize(X_fit_s, y_fit_s)
        X_val, y_val, _, _ = _revin_normalize(X_val_s, y_val_s)
        mu_test = X_test_s.mean(axis=1)
        sd_test = X_test_s.std(axis=1) + _EPS
        X_test = ((X_test_s - mu_test[:, None]) / sd_test[:, None]).astype(np.float32)
        test_mu, test_sd = mu_test.astype(np.float32), sd_test.astype(np.float32)
        mode, z_mean, z_std = "revin", 0.0, 1.0
    else:
        z_mean = float(series[: windows.fit_end].mean())
        z_std = float(series[: windows.fit_end].std()) + _EPS
        X_fit = ((X_fit_s - z_mean) / z_std).astype(np.float32)
        y_fit = ((y_fit_s - z_mean) / z_std).astype(np.float32)
        X_val = ((X_val_s - z_mean) / z_std).astype(np.float32)
        y_val = ((y_val_s - z_mean) / z_std).astype(np.float32)
        X_test = ((X_test_s - z_mean) / z_std).astype(np.float32)
        test_mu, test_sd = None, None
        mode = "zscore"

    if variant == "calendar":
        # Value channel is already normalised; append raw sin/cos in [-1, 1].
        X_fit = np.concatenate([X_fit[:, :, None], _calendar_features(base_fit, seq)], axis=-1)
        X_val = np.concatenate([X_val[:, :, None], _calendar_features(base_val, seq)], axis=-1)
        X_test = np.concatenate([X_test[:, :, None], _calendar_features(base_test, seq)], axis=-1)
    else:
        X_fit = X_fit[:, :, None]
        X_val = X_val[:, :, None]
        X_test = X_test[:, :, None]

    _, y_test_raw, last_test_raw, _ = _segment_sequences(
        values.astype(np.float64), windows.test_start, len(values), seq, horizon
    )

    return VariantArrays(
        variant=variant,
        mode=mode,
        log_space=log_space,
        seq_len=seq,
        horizon=horizon,
        X_fit=X_fit.astype(np.float32),
        y_fit=y_fit.astype(np.float32),
        X_val=X_val.astype(np.float32),
        y_val=y_val.astype(np.float32),
        X_test=X_test.astype(np.float32),
        y_test_raw=y_test_raw,
        last_test_raw=last_test_raw,
        z_mean=z_mean,
        z_std=z_std,
        test_mu=test_mu,
        test_sd=test_sd,
    )


def probe_config(variant: str, windows: ProbeWindows, epochs: int, patience: int) -> GRUConfig:
    """Current recipe (GRUConfig defaults) at the probe budget and window."""
    return GRUConfig(
        input_size=3 if variant == "calendar" else 1,
        cell="gru",
        hidden_size=128,
        num_layers=1,
        sequence_length=windows.seq_len,
        prediction_horizon=windows.horizon,
        sample_interval_sec=FIXED_SAMPLE_INTERVAL,
        epochs=epochs,
        early_stopping_patience=patience,
        batch_size=FIXED_BATCH_SIZE,
    )


# ── Scoring (frozen metric block) ────────────────────────────────────────────


def score_predictions(
    preds: np.ndarray,
    targets: np.ndarray,
    last_inputs: np.ndarray,
) -> dict[str, Any]:
    """Frozen metric block for one arm on identical windows."""
    horizon = targets.shape[1]
    residuals = targets - preds
    rmse = float(np.sqrt(np.mean(residuals**2)))
    mae = float(np.mean(np.abs(residuals)))
    mean_target = float(np.mean(targets))
    rmse_pct_mean = rmse / mean_target * 100.0 if mean_target > 0 else float("nan")

    per_h_rmse: list[float] = []
    underpred_mean: list[float] = []
    underpred_p90: list[float] = []
    for h in range(horizon):
        per_h_rmse.append(float(np.sqrt(np.mean(residuals[:, h] ** 2))))
        rising = targets[:, h] > last_inputs
        if rising.sum() > 0:
            res_rising = residuals[rising, h]
            underpred_mean.append(float(np.mean(res_rising)))
            underpred_p90.append(float(np.percentile(res_rising, 90)))
        else:
            underpred_mean.append(0.0)
            underpred_p90.append(0.0)

    return {
        "rmse": rmse,
        "mae": mae,
        "rmse_pct_of_mean_target": rmse_pct_mean,
        "per_horizon_rmse_steps_1_to_9": per_h_rmse,
        "underpred_rising_mean": underpred_mean,
        "underpred_rising_p90": underpred_p90,
    }


def _with_skills(arm: dict[str, Any], persistence: dict[str, Any], ols: dict[str, Any]) -> dict[str, Any]:
    arm = dict(arm)
    for ref_name, ref in (("persistence", persistence), ("ols", ols)):
        ref_rmse = ref["rmse"]
        arm[f"skill_vs_{ref_name}"] = 1.0 - arm["rmse"] / ref_rmse if ref_rmse > 0 else 0.0
        arm[f"skill_vs_{ref_name}_per_horizon"] = [
            1.0 - m / r if r > 0 else 0.0
            for m, r in zip(arm["per_horizon_rmse_steps_1_to_9"], ref["per_horizon_rmse_steps_1_to_9"], strict=True)
        ]
    return arm


def run_baselines(values: np.ndarray, windows: ProbeWindows, season: int = DEFAULT_SEASON) -> dict[str, Any]:
    """Score OLS, persistence, linear trend, seasonal naive on the variant's windows."""
    seq, horizon = windows.seq_len, windows.horizon
    test_values = values[windows.test_start :]

    coef = ols_autoreg_fit(values, windows)
    X_test_raw, y_test, last_inputs, _ = _segment_sequences(values, windows.test_start, len(values), seq, horizon)
    ols_preds = ols_autoreg_predict(coef, X_test_raw)

    pers_preds, pers_targets, pers_last = persistence_baseline(test_values, seq, horizon)
    trend_preds, _, _ = linear_trend_baseline(test_values, seq, horizon)
    seas_preds, _, _ = seasonal_naive_baseline(values, seq, horizon, season, windows.test_start)

    for name, preds, tgts, last in (
        ("ols", ols_preds, y_test, last_inputs),
        ("persistence", pers_preds, pers_targets, pers_last),
        ("linear_trend", trend_preds, pers_targets, pers_last),
        ("seasonal_naive", seas_preds, pers_targets, pers_last),
    ):
        if not np.array_equal(tgts, y_test) or not np.array_equal(last, last_inputs):
            raise ValueError(f"{name} arm windows diverge from the frozen test windows")

    ols_block = score_predictions(ols_preds, y_test, last_inputs)
    pers_block = score_predictions(pers_preds, pers_targets, pers_last)
    trend_block = score_predictions(trend_preds, pers_targets, pers_last)
    seas_block = score_predictions(seas_preds, pers_targets, pers_last)

    return {
        "ols": _with_skills(ols_block, pers_block, ols_block),
        "persistence": _with_skills(pers_block, pers_block, ols_block),
        "linear_trend": _with_skills(trend_block, pers_block, ols_block),
        "seasonal_naive": _with_skills(seas_block, pers_block, ols_block),
        "_arrays": {
            "y_test": y_test,
            "last_inputs": last_inputs,
            "persistence_preds": pers_preds,
            "ols_preds": ols_preds,
        },
    }


# ── Network training and prediction ──────────────────────────────────────────


def _pinball_loss(preds: Any, targets: Any, quantile: float = PINBALL_QUANTILE) -> Any:
    import torch

    err = targets - preds
    return torch.mean(torch.maximum(quantile * err, (quantile - 1.0) * err))


def train_probe_model(
    arrays: VariantArrays,
    config: GRUConfig,
    seed: int,
    loss_name: str,
    device: str,
) -> tuple[Any, int]:
    """Train one seed mirroring the serving trainer: Adam, best-state restore."""
    import torch
    from prediction.gru_predictor import GRUNetwork
    from torch import nn
    from torch.utils.data import DataLoader, TensorDataset

    if config.input_size != arrays.X_fit.shape[2]:
        raise ValueError("config input_size does not match built feature count")

    _set_deterministic(seed)
    model = GRUNetwork(config).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    criterion: Callable[[Any, Any], Any] = nn.MSELoss() if loss_name == "mse" else _pinball_loss

    train_loader = DataLoader(
        TensorDataset(torch.FloatTensor(arrays.X_fit), torch.FloatTensor(arrays.y_fit)),
        batch_size=config.batch_size,
        shuffle=True,
    )
    X_val_t = torch.FloatTensor(arrays.X_val).to(device)
    y_val_t = torch.FloatTensor(arrays.y_val).to(device)

    best_val_loss = float("inf")
    best_state: dict[str, Any] | None = None
    best_epoch = -1
    patience_counter = 0
    epochs_trained = 0

    for epoch in range(config.epochs):
        model.train()
        for batch_X, batch_y in train_loader:
            batch_X = batch_X.to(device)
            batch_y = batch_y.to(device)
            optimizer.zero_grad()
            loss = criterion(model(batch_X), batch_y)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            val_parts = [model(X_val_t[i : i + EVAL_CHUNK_SIZE]) for i in range(0, len(X_val_t), EVAL_CHUNK_SIZE)]
            val_loss = criterion(torch.cat(val_parts), y_val_t).item()

        epochs_trained = epoch + 1
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            best_epoch = epoch
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= config.early_stopping_patience:
                break

    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()
    logger.info("probe_seed_trained", variant=arrays.variant, seed=seed, epochs=epochs_trained, best_epoch=best_epoch)
    return model, epochs_trained


def predict_raw(model: Any, arrays: VariantArrays, device: str) -> np.ndarray:
    """Chunked forward pass, denormalised to the original RPS scale."""
    import torch

    X_t = torch.FloatTensor(arrays.X_test).to(device)
    parts = []
    with torch.no_grad():
        for i in range(0, len(X_t), EVAL_CHUNK_SIZE):
            parts.append(model(X_t[i : i + EVAL_CHUNK_SIZE]).cpu().numpy())
    preds_norm = np.concatenate(parts, axis=0)
    return arrays.denormalize_predictions(preds_norm)


def _save_artifact(model: Any, config: GRUConfig, arrays: VariantArrays, path: Path) -> str:
    """Persist a probe artifact under the probe output dir (never data/models)."""
    wrapper = GRUPredictor(config=config)
    wrapper.model = model
    wrapper.scaler_mean = arrays.z_mean if arrays.mode == "zscore" else 0.0
    wrapper.scaler_std = arrays.z_std if arrays.mode == "zscore" else 1.0
    wrapper.is_trained = True
    path.parent.mkdir(parents=True, exist_ok=True)
    wrapper.save_model(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ── Ensemble (no training; reuses artifacts on disk) ─────────────────────────


def run_ensemble(
    values: np.ndarray,
    windows: ProbeWindows,
    seeds: tuple[int, ...],
    output_dir: Path,
    study_bundle: Path,
    baselines: dict[str, Any],
) -> dict[str, Any]:
    """Average the baseline seed predictions, reusing artifacts when present."""
    y_test = baselines["_arrays"]["y_test"]
    last_inputs = baselines["_arrays"]["last_inputs"]

    combined: list[dict[str, Any]] = []
    per_seed_preds: list[np.ndarray] = []
    for seed in seeds:
        for candidate in (
            output_dir / "artifacts" / f"baseline_s{seed}.pt",
            study_bundle / "artifacts" / f"clarknet_gru_s{seed}.pt",
        ):
            if not candidate.exists():
                continue
            predictor = GRUPredictor()
            if not predictor.load_model(candidate):
                continue
            if predictor.config.prediction_horizon != windows.horizon:
                continue
            preds, targets, last = evaluate_on_values(predictor, values[windows.test_start :])
            if not np.array_equal(targets, y_test) or not np.array_equal(last, last_inputs):
                combined.append(
                    {"artifact": str(candidate), "seed": seed, "skipped": "window mismatch with frozen contract"}
                )
                continue
            per_seed_preds.append(preds)
            combined.append(
                {
                    "artifact": str(candidate),
                    "seed": seed,
                    "sha256": hashlib.sha256(Path(candidate).read_bytes()).hexdigest(),
                    "seq_len": predictor.config.sequence_length,
                }
            )
            break

    record: dict[str, Any] = {
        "variant": "ensemble",
        "combined_artifacts": combined,
        "artifacts_found": len(per_seed_preds),
        "artifacts_expected": len(seeds),
    }
    if not per_seed_preds:
        record["note"] = (
            "no reusable baseline artifacts on disk (probe output dir or study bundle); "
            "run the baseline variant first, or wait for the study to finish writing artifacts"
        )
        return record

    mean_preds = np.mean(np.stack(per_seed_preds, axis=0), axis=0)
    record["metrics"] = _with_skills(
        score_predictions(mean_preds, y_test, last_inputs),
        baselines["persistence"],
        baselines["ols"],
    )
    return record


# ── Probe runner ─────────────────────────────────────────────────────────────


def load_probe_series() -> np.ndarray:
    """ClarkNet 15 s series at the replay amplitude, exactly as the study."""
    series = load_clarknet_series()
    scale = manifest_scale_factor()
    return (series.to_numpy(dtype=np.float32) * scale).astype(np.float32)


def _append_probes_row(output_dir: Path, row: dict[str, Any]) -> None:
    probes_md = output_dir / "probes.md"
    header = (
        "| variant | seeds | rmse_mean | rmse_std | mae | rmse_pct_mean | "
        "skill_vs_persistence | skill_vs_ols | p_paired_vs_ols | test_start |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
    )
    if not probes_md.exists():
        probes_md.write_text(header)
    with probes_md.open("a") as fh:
        fh.write(
            f"| {row['variant']} | {row['seeds']} | {row['rmse_mean']} | {row['rmse_std']} | "
            f"{row['mae']} | {row['rmse_pct_mean']} | {row['skill_vs_persistence']} | "
            f"{row['skill_vs_ols']} | {row['p_paired_vs_ols']} | {row['test_start']} |\n"
        )


def run_probe(
    variant: str = "baseline",
    seeds: tuple[int, ...] = (42, 43, 44),
    output_dir: str | Path | None = None,
    epochs: int = 200,
    patience: int = 25,
    dry_run: bool = False,
    study_bundle: str | Path | None = None,
) -> dict[str, Any]:
    """Train/score one variant (or dry-run the linear arms) under the frozen contract."""
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant {variant!r}; expected one of {VARIANTS}")
    if dry_run:
        return _run_dry_run(variant, epochs, patience)

    if output_dir is None:
        raise ValueError("--output-dir is required for probe runs (the probe never writes into results/)")

    values = load_probe_series()
    windows = probe_windows(variant, len(values))
    device = _torch_device()
    baselines = run_baselines(values, windows)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    bundle = Path(study_bundle) if study_bundle else DEFAULT_STUDY_BUNDLE

    record: dict[str, Any] = {
        "variant": variant,
        "created": datetime.now().isoformat(timespec="seconds"),
        "seeds": list(seeds),
        "device": device,
        "splits": windows.to_dict(),
        "replay_window": list(PROBE_REPLAY_WINDOW),
        "replay_inside_test": windows.test_start <= PROBE_REPLAY_WINDOW[0],
        "epochs_budget": epochs,
        "patience": patience,
        "ols": baselines["ols"],
        "persistence": baselines["persistence"],
        "linear_trend": baselines["linear_trend"],
        "seasonal_naive": baselines["seasonal_naive"],
    }

    if variant == "window120":
        record["boundary_derivation"] = (
            f"frozen 38-sample gaps cannot host a 120-sample window; derived fit/val/test "
            f"boundaries with embargo {WINDOW120_EMBARGO} (ticket literal; formula minimum "
            f"{WINDOW120_FORMULA_MIN}) between val_end and test_start, and "
            f"{WINDOW120_FORMULA_MIN} between fit and val"
        )

    if variant == "ensemble":
        ens = run_ensemble(values, windows, tuple(seeds), out, bundle, baselines)
        record.update(ens)
        record["epochs_trained_per_seed"] = None
        metric_block = ens.get("metrics")
        aggregate = None
    else:
        arrays = build_variant_arrays(variant, values, windows)
        config = probe_config(variant, windows, epochs, patience)
        loss_name = "pinball" if variant == "pinball" else "mse"
        record["loss"] = loss_name
        feature_label = "value_z" if arrays.mode == "zscore" else "value_revin"
        record["input_features"] = [feature_label, "sin_tod", "cos_tod"] if variant == "calendar" else [feature_label]
        record["normalization"] = arrays.mode + ("+log1p" if arrays.log_space else "")

        per_seed: dict[str, Any] = {}
        seed_rmses: list[float] = []
        epochs_per_seed: dict[str, int] = {}
        artifacts: list[dict[str, Any]] = []
        for seed in seeds:
            model, epochs_trained = train_probe_model(arrays, config, seed, loss_name, device)
            preds = predict_raw(model, arrays, device)
            block = _with_skills(
                score_predictions(preds, arrays.y_test_raw, arrays.last_test_raw),
                baselines["persistence"],
                baselines["ols"],
            )
            per_seed[str(seed)] = block
            seed_rmses.append(block["rmse"])
            epochs_per_seed[str(seed)] = epochs_trained
            artifact_path = out / "artifacts" / f"{variant}_s{seed}.pt"
            artifacts.append(
                {
                    "path": str(artifact_path),
                    "seed": seed,
                    "sha256": _save_artifact(model, config, arrays, artifact_path),
                }
            )

        record["per_seed"] = per_seed
        record["epochs_trained_per_seed"] = epochs_per_seed
        record["artifacts"] = artifacts
        record["serving_compatible"] = variant == "baseline"
        aggregate = {
            "rmse_mean": float(np.mean(seed_rmses)),
            "rmse_std": float(np.std(seed_rmses, ddof=1)) if len(seed_rmses) > 1 else 0.0,
            "mae_mean": float(np.mean([b["mae"] for b in per_seed.values()])),
            "rmse_pct_mean": float(np.mean([b["rmse_pct_of_mean_target"] for b in per_seed.values()])),
            "skill_vs_persistence_mean": float(np.mean([b["skill_vs_persistence"] for b in per_seed.values()])),
            "skill_vs_ols_mean": float(np.mean([b["skill_vs_ols"] for b in per_seed.values()])),
        }
        record["aggregate"] = aggregate
        if len(seed_rmses) > 1:
            ols_rmse = baselines["ols"]["rmse"]
            record["paired_test_vs_ols"] = {
                "p_value": paired_permutation_test([ols_rmse] * len(seed_rmses), seed_rmses),
                "cohens_d_paired": cohens_d_paired([ols_rmse] * len(seed_rmses), seed_rmses),
                "note": "one-sided: variant seed RMSE below OLS RMSE",
            }
        metric_block = None

    json_path = out / f"{variant}.json"
    json_path.write_text(json.dumps(record, indent=2, default=float))

    _append_probes_row(out, _probes_row(variant, seeds, windows, metric_block, aggregate, record))
    logger.info("probe_complete", variant=variant, output=str(json_path))
    return record


def _probes_row(
    variant: str,
    seeds: tuple[int, ...],
    windows: ProbeWindows,
    metric_block: dict[str, Any] | None,
    aggregate: dict[str, Any] | None,
    record: dict[str, Any],
) -> dict[str, Any]:
    """One summary row per probe run for probes.md."""
    if metric_block is not None:
        return {
            "variant": variant,
            "seeds": ",".join(str(s) for s in seeds),
            "rmse_mean": round(metric_block["rmse"], 4),
            "rmse_std": 0.0,
            "mae": round(metric_block["mae"], 4),
            "rmse_pct_mean": round(metric_block["rmse_pct_of_mean_target"], 4),
            "skill_vs_persistence": round(metric_block["skill_vs_persistence"], 4),
            "skill_vs_ols": round(metric_block["skill_vs_ols"], 4),
            "p_paired_vs_ols": "n/a",
            "test_start": windows.test_start,
        }
    if aggregate is not None:
        paired = record.get("paired_test_vs_ols") or {}
        return {
            "variant": variant,
            "seeds": ",".join(str(s) for s in seeds),
            "rmse_mean": round(aggregate["rmse_mean"], 4),
            "rmse_std": round(aggregate["rmse_std"], 4),
            "mae": round(aggregate["mae_mean"], 4),
            "rmse_pct_mean": round(aggregate["rmse_pct_mean"], 4),
            "skill_vs_persistence": round(aggregate["skill_vs_persistence_mean"], 4),
            "skill_vs_ols": round(aggregate["skill_vs_ols_mean"], 4),
            "p_paired_vs_ols": round(paired["p_value"], 4) if paired else "n/a",
            "test_start": windows.test_start,
        }
    return {
        "variant": variant,
        "seeds": ",".join(str(s) for s in seeds),
        "rmse_mean": "n/a",
        "rmse_std": "n/a",
        "mae": "n/a",
        "rmse_pct_mean": "n/a",
        "skill_vs_persistence": "n/a",
        "skill_vs_ols": "n/a",
        "p_paired_vs_ols": "n/a",
        "test_start": windows.test_start,
        "note": record.get("note", ""),
    }


def _run_dry_run(variant: str, epochs: int, patience: int) -> dict[str, Any]:
    """Score OLS and the statistical baselines only — no network, no writes."""
    values = load_probe_series()
    windows = probe_windows(variant, len(values))
    device = _torch_device()
    baselines = run_baselines(values, windows)

    lines = [
        f"dry-run variant={variant} device={device} epochs_budget={epochs} patience={patience}",
        f"boundaries={json.dumps(windows.to_dict())}",
    ]
    for name in ("ols", "persistence", "linear_trend", "seasonal_naive"):
        b = baselines[name]
        lines.append(
            f"{name}: rmse={b['rmse']:.4f} mae={b['mae']:.4f} "
            f"rmse_pct={b['rmse_pct_of_mean_target']:.4f} "
            f"per_h_rmse={[round(r, 3) for r in b['per_horizon_rmse_steps_1_to_9']]}"
        )
    report = "\n".join(lines)
    logger.info("probe_dry_run_complete", variant=variant)
    print(report)
    return {
        "dry_run": True,
        "variant": variant,
        "report": report,
        "baselines": {k: v for k, v in baselines.items() if k != "_arrays"},
    }
