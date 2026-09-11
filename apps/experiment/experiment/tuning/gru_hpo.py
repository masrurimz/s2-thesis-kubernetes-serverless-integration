"""GRU hyperparameter optimization with temporal cross-validation.

Replaces leakage-prone random splits with gap-aware expanding-window temporal CV.
The production-aligned objective optimizes the actual deployed multi-horizon
output (default horizon 9, the calibration horizon): mean horizon-normalized
RMSE + 2 × mean normalized underprediction on rising targets. A promotion gate
compares the best GRU against persistence and linear-trend baselines on an
untouched chronological holdout.

Per thesis plan §2 (replace leakage-prone GRU selection with temporal model
selection).
"""

from __future__ import annotations

import json
import os

# Soften MIOpen on gfx1103 — must precede torch import
os.environ.setdefault("MIOPEN_DEBUG_CONV_DIRECT", "0")
os.environ.setdefault("MIOPEN_FIND_MODE", "FAST")
os.environ.setdefault("HSA_ENABLE_SDMA", "0")
os.environ.setdefault("GPU_MAX_HW_QUEUES", "1")

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
import optuna
import pandas as pd
import structlog

logger = structlog.get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent

# ── Constants ─────────────────────────────────────────────────────────────────

HPO_SEED = 42
DEFAULT_TRIALS = 30
DEFAULT_N_FOLDS = 3
DEFAULT_HOLDOUT_RATIO = 0.2
FIXED_EPOCHS = 100
FIXED_PATIENCE = 15
FIXED_BATCH_SIZE = 32
DEFAULT_HORIZON = 9  # Calibration horizon (was 5 in the pre-study HPO run)
FIXED_SAMPLE_INTERVAL = 15
EVAL_CHUNK_SIZE = 512  # Match the predictor's chunked eval forwards
COVERAGE_THRESHOLD = 0.85

# Fixed GRU training parameters (not searched)
_FIXED_TRAIN_PARAMS: dict[str, Any] = {
    "prediction_horizon": DEFAULT_HORIZON,
    "sample_interval_sec": FIXED_SAMPLE_INTERVAL,
    "epochs": FIXED_EPOCHS,
    "early_stopping_patience": FIXED_PATIENCE,
    "batch_size": FIXED_BATCH_SIZE,
}


@dataclass
class FoldBoundary:
    """A single expanding-window temporal CV fold.

    Indices refer to positions in the development value array.
    Training data = values[:train_end], validation = values[val_start:val_end].
    Gap (train_end .. val_start) prevents temporal leakage.
    """

    train_end: int
    val_start: int
    val_end: int

    @property
    def gap(self) -> int:
        return self.val_start - self.train_end


# ── Temporal splitting ────────────────────────────────────────────────────────


def temporal_split(
    values: np.ndarray,
    seq_len: int = 30,
    horizon: int = DEFAULT_HORIZON,
    holdout_ratio: float = DEFAULT_HOLDOUT_RATIO,
) -> tuple[np.ndarray, np.ndarray]:
    """Split chronologically into development and untouched holdout.

    The final *holdout_ratio* of samples is reserved as an untouched model
    holdout — never accessed during HPO. Expanding-window CV operates on the
    earlier development portion.

    Args:
        values: 1-D time-ordered array.
        seq_len: Model sequence length (used for minimum-size validation).
        horizon: Prediction horizon (used for minimum-size validation).
        holdout_ratio: Fraction reserved as holdout.

    Returns:
        (dev_values, holdout_values) — contiguous, non-overlapping.
    """
    n = len(values)
    holdout_start = int(n * (1 - holdout_ratio))
    dev = values[:holdout_start].copy()
    holdout = values[holdout_start:].copy()

    if len(holdout) < seq_len + horizon:
        raise ValueError(f"Holdout ({len(holdout)}) too small for seq_len={seq_len} + horizon={horizon}")

    return dev, holdout


def expanding_window_folds(
    n_samples: int,
    seq_len: int,
    horizon: int,
    n_folds: int = DEFAULT_N_FOLDS,
) -> list[FoldBoundary]:
    """Generate expanding-window fold boundaries with leakage-preventing gap.

    The gap between train and validation equals ``seq_len + horizon - 1`` so
    no input or target window can span the boundary. Training windows expand
    with each fold; validation windows are contiguous blocks of equal size.

    Layout::

        [---- init_train ----][gap][val_0][gap][val_1][gap][val_2]

    Each fold trains on everything before its validation block minus the gap.

    Returns:
        List of :class:`FoldBoundary`.
    """
    gap = seq_len + horizon - 1
    min_train_samples = seq_len + horizon  # need ≥ 1 training sequence

    init_train = max(min_train_samples + gap, int(n_samples * 0.4))

    if init_train >= n_samples:
        raise ValueError(
            f"Not enough samples ({n_samples}) for expanding-window CV with seq_len={seq_len}, horizon={horizon}"
        )

    val_total = n_samples - init_train
    val_size = val_total // n_folds

    if val_size < seq_len + horizon:
        raise ValueError(
            f"Validation windows ({val_size}) too small for "
            f"seq_len={seq_len} + horizon={horizon}. "
            f"Need more data or fewer folds."
        )

    folds: list[FoldBoundary] = []
    for k in range(n_folds):
        val_start = init_train + k * val_size
        if k < n_folds - 1:
            val_end = val_start + val_size
        else:
            val_end = n_samples  # last fold absorbs remainder
        train_end = val_start - gap
        folds.append(FoldBoundary(train_end, val_start, val_end))

    return folds


# ── Sequence creation and evaluation ─────────────────────────────────────────


def _make_sequences(
    values: np.ndarray,
    seq_len: int,
    horizon: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Create (X, y, last_inputs) from a contiguous value array.

    Every input and target window lies entirely within ``values`` — no window
    crosses a boundary.
    """
    n_seq = len(values) - seq_len - horizon + 1
    if n_seq <= 0:
        raise ValueError(f"Need ≥ {seq_len + horizon} values, got {len(values)}")

    base = np.arange(n_seq)
    idx_X = base[:, None] + np.arange(seq_len)[None, :]
    idx_y = base[:, None] + np.arange(seq_len, seq_len + horizon)[None, :]
    idx_last = base + seq_len - 1

    X = values[idx_X]  # (n_seq, seq_len)
    y = values[idx_y]  # (n_seq, horizon)
    last_inputs = values[idx_last]  # (n_seq,)

    return X, y, last_inputs


def _batch_forward(predictor: Any, X_3d: np.ndarray) -> np.ndarray:
    """Batched forward pass through the predictor's model."""
    try:
        import torch
        from torch import nn as torch_nn

        if isinstance(predictor.model, torch_nn.Module):
            predictor.model.eval()
            with torch.no_grad():
                # Large single forward passes hang some ROCm stacks; eval
                # math is batch-independent, so slice into fixed chunks.
                X_t = torch.FloatTensor(X_3d).to(predictor.device)
                parts = [predictor.model(X_t[i : i + EVAL_CHUNK_SIZE]) for i in range(0, len(X_t), EVAL_CHUNK_SIZE)]
                return torch.cat(parts).cpu().numpy()
    except (ImportError, RuntimeError):
        pass

    # Sklearn fallback
    X_flat = X_3d.reshape(len(X_3d), -1)
    return predictor.model.predict(X_flat)


def evaluate_on_values(
    predictor: Any,
    values: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Evaluate a trained predictor on a contiguous value array.

    Applies the predictor's frozen normalization, creates sequences entirely
    within *values*, and returns denormalized predictions, targets, and the
    last input value per sample.
    """
    seq_len = predictor.config.sequence_length
    horizon = predictor.config.prediction_horizon

    normalized = predictor._normalize(values.astype(np.float32))
    X, y, last_inputs_norm = _make_sequences(normalized, seq_len, horizon)

    preds_norm = _batch_forward(predictor, X.reshape(len(X), seq_len, 1))

    preds = predictor._denormalize(preds_norm)
    targets = predictor._denormalize(y)
    last_inputs = predictor._denormalize(last_inputs_norm)

    return preds, targets, last_inputs


# ── Objective computation ────────────────────────────────────────────────────


def compute_objective(
    preds: np.ndarray,
    targets: np.ndarray,
    last_inputs: np.ndarray,
    horizon: int = DEFAULT_HORIZON,
) -> tuple[float, dict[str, Any]]:
    """Compute the predeclared scalar objective.

    objective = mean_h(norm_rmse_h) + 2 × mean_h(norm_underpred_rising_h)

    - **norm_rmse_h**: RMSE of horizon *h* divided by mean(target_h).
    - **rising**: target_h > last_input (the last observed value of the input).
    - **norm_underpred_rising_h**: mean(target_h − pred_h) over rising samples,
      divided by mean(target_h). Positive when the model under-predicts ramps.

    Returns:
        (objective_value, detail_dict)
    """
    eps = 1e-8
    norm_rmse_per_h: list[float] = []
    norm_underpred_per_h: list[float] = []

    for h in range(horizon):
        pred_h = preds[:, h]
        target_h = targets[:, h]
        mean_target_h = float(np.mean(target_h))

        rmse_h = float(np.sqrt(np.mean((target_h - pred_h) ** 2)))
        norm_rmse = rmse_h / mean_target_h if mean_target_h > eps else rmse_h
        norm_rmse_per_h.append(norm_rmse)

        rising = target_h > last_inputs
        if rising.sum() > 0:
            underpred_h = float(np.mean(target_h[rising] - pred_h[rising]))
            norm_underpred = underpred_h / mean_target_h if mean_target_h > eps else underpred_h
        else:
            norm_underpred = 0.0
        norm_underpred_per_h.append(norm_underpred)

    mean_norm_rmse = float(np.mean(norm_rmse_per_h))
    mean_norm_underpred = float(np.mean(norm_underpred_per_h))
    objective = mean_norm_rmse + 2.0 * mean_norm_underpred

    return objective, {
        "objective": objective,
        "mean_norm_rmse": mean_norm_rmse,
        "mean_norm_underpred": mean_norm_underpred,
        "norm_rmse_per_h": norm_rmse_per_h,
        "norm_underpred_per_h": norm_underpred_per_h,
    }


# ── Baselines ────────────────────────────────────────────────────────────────


def persistence_baseline(
    values: np.ndarray,
    seq_len: int,
    horizon: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Persistence: predict the last observed value for all horizons.

    Returns:
        (preds, targets, last_inputs) — all denormalized.
    """
    X, targets, last_inputs = _make_sequences(values, seq_len, horizon)
    preds = np.tile(last_inputs[:, np.newaxis], (1, horizon))
    return preds, targets, last_inputs


def linear_trend_baseline(
    values: np.ndarray,
    seq_len: int,
    horizon: int,
    trend_window: int = 10,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Linear trend: fit OLS on the last *trend_window* input values, extrapolate.

    Returns:
        (preds, targets, last_inputs) — all denormalized.
    """
    X, targets, last_inputs = _make_sequences(values, seq_len, horizon)
    n_seq = len(X)
    t = np.arange(trend_window, dtype=np.float64)
    preds = np.zeros((n_seq, horizon), dtype=np.float32)

    for i in range(n_seq):
        window = X[i, -trend_window:].astype(np.float64)
        slope, intercept = np.polyfit(t, window, 1)
        for h in range(horizon):
            preds[i, h] = intercept + slope * (trend_window + h)

    preds = np.maximum(preds, 0.0)
    return preds, targets, last_inputs


def seasonal_naive_baseline(
    values: np.ndarray,
    seq_len: int,
    horizon: int,
    season: int = 5760,
    eval_start: int = 0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Seasonal naive: predict the value observed one season earlier.

    ``values`` is the full series including history before the evaluation
    region; ``eval_start`` marks the first evaluation origin. For origin *t*
    and horizon step *h* (1-based), the prediction is
    ``values[t + seq_len - 1 + h - season]`` — the target index shifted back
    one season. Targets and last inputs come from ``_make_sequences`` exactly
    as in the other baselines; only the prediction source differs.

    A seasonal baseline needs *series history*, not window room: the model is
    limited to ``seq_len`` inputs, the baseline is limited by how much of the
    series precedes the evaluation region. Hence ``eval_start >= season``.

    Returns:
        (preds, targets, last_inputs) for origins ``t >= eval_start`` — the
        same origins the other baselines see on ``values[eval_start:]``.
    """
    if eval_start < season:
        raise ValueError(
            f"eval_start ({eval_start}) must be >= season ({season}) so a full "
            "season of history exists before the evaluation region"
        )

    X, targets, last_inputs = _make_sequences(values, seq_len, horizon)
    idx = np.arange(eval_start, len(X), dtype=np.int64)
    pred_idx = idx[:, np.newaxis] + seq_len - 1 + np.arange(1, horizon + 1, dtype=np.int64)[np.newaxis, :] - season
    preds = values[pred_idx]
    return preds.astype(np.float32), targets[idx], last_inputs[idx]


# ── Promotion gate ───────────────────────────────────────────────────────────


def evaluate_promotion_gate(
    gru_detail: dict[str, Any],
    pers_detail: dict[str, Any],
    coverage: float,
    coverage_threshold: float = COVERAGE_THRESHOLD,
) -> dict[str, Any]:
    """Evaluate whether the GRU passes the promotion gate.

    The GRU must beat persistence on **both** normalized RMSE and normalized
    underprediction on rising targets, **and** achieve ≥ *coverage_threshold*
    upper-envelope coverage on rising targets.
    """
    beats_rmse = gru_detail["mean_norm_rmse"] < pers_detail["mean_norm_rmse"]
    beats_underpred = gru_detail["mean_norm_underpred"] < pers_detail["mean_norm_underpred"]
    meets_coverage = coverage >= coverage_threshold
    promoted = beats_rmse and beats_underpred and meets_coverage

    return {
        "beats_persistence_rmse": bool(beats_rmse),
        "beats_persistence_underpred": bool(beats_underpred),
        "meets_coverage_threshold": bool(meets_coverage),
        "promoted": bool(promoted),
    }


def run_baseline_comparison(
    predictor: Any,
    values: np.ndarray,
    seq_len: int,
    horizon: int = DEFAULT_HORIZON,
    season: int = 5760,
    eval_start: int = 0,
) -> dict[str, Any]:
    """Compare GRU against persistence, linear-trend, and seasonal-naive baselines.

    ``values`` includes at least *season* samples of history before
    *eval_start*; all baselines and the model are evaluated on exactly the
    same origins and targets (model windows over ``values[eval_start:]``,
    seasonal naive restricted to origins ``>= eval_start`` with access to the
    preceding history). If the history is too short, the seasonal baseline is
    skipped and ``seasonal_naive_unavailable`` records the reason instead of
    failing the run. If the GRU fails the promotion gate, ``promoted_model``
    is ``None``.
    """
    eval_values = values[eval_start:]

    # GRU predictions on the evaluation region
    gru_preds, gru_targets, gru_last_inputs = evaluate_on_values(predictor, eval_values)
    _, gru_detail = compute_objective(gru_preds, gru_targets, gru_last_inputs, horizon)

    # Persistence baseline
    pers_preds, _, pers_last_inputs = persistence_baseline(eval_values, seq_len, horizon)
    _, pers_detail = compute_objective(pers_preds, gru_targets, pers_last_inputs, horizon)

    # Linear-trend baseline
    trend_preds, _, trend_last_inputs = linear_trend_baseline(eval_values, seq_len, horizon)
    _, trend_detail = compute_objective(trend_preds, gru_targets, trend_last_inputs, horizon)

    # Seasonal-naive baseline (same origins and targets, longer history)
    seas_detail: dict[str, Any] | None = None
    unavailable: str | None = None
    if eval_start >= season:
        seas_preds, _, seas_last_inputs = seasonal_naive_baseline(values, seq_len, horizon, season, eval_start)
        _, seas_detail = compute_objective(seas_preds, gru_targets, seas_last_inputs, horizon)
    else:
        unavailable = (
            f"eval_start ({eval_start}) < season ({season}): not enough series history before the evaluation region"
        )
        logger.warning("seasonal_naive_unavailable", reason=unavailable)

    # Upper-envelope coverage on rising targets
    upper_forecasts = gru_preds + predictor.upper_offsets[np.newaxis, :]
    rising_mask = gru_targets > gru_last_inputs[:, np.newaxis]
    covered = gru_targets <= upper_forecasts
    n_rising = int(rising_mask.sum())
    coverage = float(covered[rising_mask].mean()) if n_rising > 0 else 1.0

    gate = evaluate_promotion_gate(gru_detail, pers_detail, coverage)

    return {
        "gru": gru_detail,
        "persistence": pers_detail,
        "linear_trend": trend_detail,
        "seasonal_naive": seas_detail,
        "seasonal_naive_unavailable": unavailable,
        "gru_coverage": coverage,
        "n_rising_targets": n_rising,
        "promotion_gate": gate,
        "promoted_model": "gru" if gate["promoted"] else None,
    }


def locate_replay_window(
    series: Any,
    manifest_path: str | Path,
    holdout_start: int,
    embargo: int,
    sample_interval_sec: int = FIXED_SAMPLE_INTERVAL,
) -> tuple[int, int]:
    """Map the trace-replay window onto indices of the 15 s training series.

    The window is located by *time* from the replay manifest
    (``window_start_time`` + ``duration_sec``), then converted to sample
    indices on the same resampled series the model trains on.

    Raises:
        ValueError: if the window is not aligned to the sample grid, or does
            not lie strictly inside the test portion (after
            ``holdout_start + embargo``).

    Returns:
        (start_idx, end_idx) with end exclusive.
    """
    import json

    manifest = json.loads(Path(manifest_path).read_text())
    start_time = pd.Timestamp(manifest["window_start_time"])
    duration_sec = int(manifest["duration_sec"])

    t0 = series.index[0]
    offset_sec = (start_time - t0).total_seconds()
    if offset_sec < 0:
        raise ValueError(f"Replay window starts before the series: {start_time} < {t0}")
    if offset_sec % sample_interval_sec != 0:
        raise ValueError(
            f"Replay window start {start_time} is not aligned to the "
            f"{sample_interval_sec}s sample grid anchored at {t0}"
        )

    start_idx = int(offset_sec // sample_interval_sec)
    end_idx = start_idx + int(np.ceil(duration_sec / sample_interval_sec))

    earliest_allowed = holdout_start + embargo
    if start_idx <= earliest_allowed:
        raise ValueError(
            f"Replay window start index {start_idx} must lie strictly after "
            f"holdout_start + embargo = {holdout_start} + {embargo} = {earliest_allowed}"
        )
    if end_idx > len(series):
        raise ValueError(f"Replay window end index {end_idx} exceeds series length {len(series)}")

    return start_idx, end_idx


def rolling_origin_evaluation(
    predictor: Any,
    test_values: np.ndarray,
    seq_len: int,
    horizon: int = DEFAULT_HORIZON,
    n_blocks: int = 5,
) -> dict[str, Any]:
    """Evaluate a frozen model on rolling origins across the test portion.

    The test portion is cut into *n_blocks* contiguous blocks; per-block
    per-horizon RMSE and overall RMSE/MAE are reported together with their
    mean and standard deviation across blocks (stability check — the model is
    never retrained).
    """
    n = len(test_values)
    min_block = seq_len + horizon + 1
    if n < n_blocks * min_block:
        raise ValueError(f"Test portion ({n}) too small for {n_blocks} rolling blocks of ≥ {min_block} samples")

    edges = np.linspace(0, n, n_blocks + 1, dtype=int)
    folds: list[dict[str, Any]] = []
    for k in range(n_blocks):
        block = test_values[edges[k] : edges[k + 1]]
        preds, targets, last_inputs = evaluate_on_values(predictor, block)
        residuals = targets - preds
        folds.append(
            {
                "block": k,
                "start_idx": int(edges[k]),
                "end_idx": int(edges[k + 1]),
                "rmse_per_horizon": [float(np.sqrt(np.mean(residuals[:, h] ** 2))) for h in range(horizon)],
                "rmse": float(np.sqrt(np.mean(residuals**2))),
                "mae": float(np.mean(np.abs(residuals))),
            }
        )

    rmses = np.array([f["rmse"] for f in folds], dtype=np.float64)
    maes = np.array([f["mae"] for f in folds], dtype=np.float64)
    return {
        "n_blocks": n_blocks,
        "folds": folds,
        "rmse_mean": float(rmses.mean()),
        "rmse_std": float(rmses.std(ddof=1)) if len(rmses) > 1 else 0.0,
        "mae_mean": float(maes.mean()),
        "mae_std": float(maes.std(ddof=1)) if len(maes) > 1 else 0.0,
    }


# ── Optuna objective ────────────────────────────────────────────────────────


def _params_to_config(params: dict[str, Any]) -> Any:
    """Convert Optuna trial params to a :class:`GRUConfig`."""
    from prediction.gru_predictor import GRUConfig

    return GRUConfig(
        hidden_size=params["hidden_size"],
        num_layers=params["num_layers"],
        dropout=params.get("dropout", 0.0),
        head_dropout=params["head_dropout"],
        learning_rate=params["learning_rate"],
        sequence_length=params["sequence_length"],
        **_FIXED_TRAIN_PARAMS,
    )


def _set_deterministic(seed: int) -> None:
    """Set all RNG seeds and enable deterministic algorithms."""
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except ImportError:
        pass


def _train_and_evaluate_fold(
    config: Any,
    dev_values: np.ndarray,
    fold: FoldBoundary,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Train on the fold's training portion, evaluate on its validation portion.

    Training data = dev_values[:train_end], validation = dev_values[val_start:val_end].
    """
    train_values = dev_values[: fold.train_end]
    val_values = dev_values[fold.val_start : fold.val_end]

    train_df = pd.DataFrame({"total_requests": train_values})

    _set_deterministic(seed)

    from prediction.gru_predictor import GRUPredictor

    predictor = GRUPredictor(config=config)
    predictor.train(train_df, val_ratio=0.15)

    return evaluate_on_values(predictor, val_values)


def create_gru_objective(
    dev_values: np.ndarray,
    horizon: int = DEFAULT_HORIZON,
    n_folds: int = DEFAULT_N_FOLDS,
    seed: int = HPO_SEED,
) -> Callable[[optuna.Trial], float]:
    """Return an Optuna objective using expanding-window temporal CV.

    The objective is the mean across folds of the predeclared scalar:
    ``mean_h(norm_rmse_h) + 2 × mean_h(norm_underpred_rising_h)``.
    """

    def objective(trial: optuna.Trial) -> float:
        # ── Suggest hyperparameters ──
        hidden_size = trial.suggest_categorical("hidden_size", [64, 128, 256])
        num_layers = trial.suggest_int("num_layers", 1, 2)
        dropout = trial.suggest_float("dropout", 0.05, 0.3) if num_layers > 1 else 0.0
        head_dropout = trial.suggest_float("head_dropout", 0.0, 0.3)
        learning_rate = trial.suggest_float("learning_rate", 1e-4, 1e-3, log=True)
        sequence_length = trial.suggest_categorical("sequence_length", [20, 30, 45])

        config = _params_to_config(
            {
                "hidden_size": hidden_size,
                "num_layers": num_layers,
                "dropout": dropout,
                "head_dropout": head_dropout,
                "learning_rate": learning_rate,
                "sequence_length": sequence_length,
            }
        )

        # ── Expanding-window temporal CV ──
        folds = expanding_window_folds(len(dev_values), sequence_length, horizon, n_folds)

        all_preds: list[np.ndarray] = []
        all_targets: list[np.ndarray] = []
        all_last_inputs: list[np.ndarray] = []
        per_fold_details: list[dict] = []

        for fold_idx, fold in enumerate(folds):
            try:
                preds, targets, last_inputs = _train_and_evaluate_fold(config, dev_values, fold, seed)
            except Exception as e:
                logger.warning(
                    "gru_fold_train_failed",
                    trial=trial.number,
                    fold=fold_idx,
                    error=str(e),
                )
                return 1000.0

            all_preds.append(preds)
            all_targets.append(targets)
            all_last_inputs.append(last_inputs)

            _, detail = compute_objective(preds, targets, last_inputs, horizon)
            per_fold_details.append(detail)

        preds_cat = np.concatenate(all_preds)
        targets_cat = np.concatenate(all_targets)
        last_inputs_cat = np.concatenate(all_last_inputs)

        obj_val, obj_detail = compute_objective(preds_cat, targets_cat, last_inputs_cat, horizon)

        trial.set_user_attr("objective_detail", obj_detail)
        trial.set_user_attr("per_fold", per_fold_details)
        trial.set_user_attr("folds", [(f.train_end, f.val_start, f.val_end) for f in folds])

        logger.info(
            "gru_hpo_trial",
            trial=trial.number,
            objective=round(obj_val, 4),
            norm_rmse=round(obj_detail["mean_norm_rmse"], 4),
            norm_underpred=round(obj_detail["mean_norm_underpred"], 4),
            hidden_size=hidden_size,
            num_layers=num_layers,
            lr=learning_rate,
            seq_len=sequence_length,
        )

        return obj_val

    return objective


# ── Data loading ─────────────────────────────────────────────────────────────


def _load_data(data_source: str = "clarknet") -> np.ndarray:
    """Load time series values for HPO at the native control-loop resolution."""
    from prediction.training.train_gru_real import load_calgary, load_clarknet

    if data_source == "clarknet":
        df = load_clarknet(resample=f"{FIXED_SAMPLE_INTERVAL}s")
    elif data_source == "calgary":
        df = load_calgary(resample=f"{FIXED_SAMPLE_INTERVAL}s")
    else:
        raise ValueError(f"Unknown data_source: {data_source}")

    if "total_requests" in df.columns:
        return df["total_requests"].values.astype(np.float32)
    if "rps" in df.columns:
        return df["rps"].values.astype(np.float32)
    raise ValueError("DataFrame must have 'total_requests' or 'rps' column")


# ── Persistence helpers ──────────────────────────────────────────────────────


def _build_study_json(
    study: optuna.Study,
    seed: int,
    holdout_start: int,
    total_samples: int,
    data_source: str,
    n_trials: int,
) -> dict[str, Any]:
    """Build serializable study data with split boundaries and trial table."""
    return {
        "seed": seed,
        "data_source": data_source,
        "n_trials": n_trials,
        "total_samples": total_samples,
        "holdout_start_idx": holdout_start,
        "dev_samples": holdout_start,
        "holdout_samples": total_samples - holdout_start,
        "best_trial": study.best_trial.number,
        "best_objective": study.best_value,
        "best_params": study.best_params,
        "all_trials": [
            {
                "number": t.number,
                "params": t.params,
                "value": t.value if t.value is not None else float("inf"),
                "state": str(t.state),
                "objective_detail": t.user_attrs.get("objective_detail"),
                "per_fold": t.user_attrs.get("per_fold"),
                "folds": t.user_attrs.get("folds"),
            }
            for t in study.trials
        ],
    }


def _build_hpo_report(
    predictor: Any,
    train_metrics: dict[str, Any],
    comparison: dict[str, Any],
    best_params: dict[str, Any],
    best_objective: float,
    holdout_values: np.ndarray,
    seq_len: int,
    horizon: int = DEFAULT_HORIZON,
) -> dict[str, Any]:
    """Build HPO report with per-horizon holdout metrics and ramp-only error."""
    preds, targets, last_inputs = evaluate_on_values(predictor, holdout_values)
    _, holdout_detail = compute_objective(preds, targets, last_inputs, horizon)

    # Ramp-only error: error metrics computed on rising targets only
    rising_mask = targets > last_inputs[:, np.newaxis]
    ramp_residuals = (targets - preds)[rising_mask]
    ramp_rmse = float(np.sqrt(np.mean(ramp_residuals**2))) if len(ramp_residuals) > 0 else 0.0
    ramp_mae = float(np.mean(np.abs(ramp_residuals))) if len(ramp_residuals) > 0 else 0.0

    # Per-horizon RMSE/MAE on holdout
    rmse_per_h = [float(np.sqrt(np.mean((targets[:, h] - preds[:, h]) ** 2))) for h in range(horizon)]
    mae_per_h = [float(np.mean(np.abs(targets[:, h] - preds[:, h]))) for h in range(horizon)]

    # Underprediction per horizon on rising targets
    underpred_per_h: list[float] = []
    for h in range(horizon):
        rising_h = targets[:, h] > last_inputs
        if rising_h.sum() > 0:
            underpred_per_h.append(float(np.mean(targets[rising_h, h] - preds[rising_h, h])))
        else:
            underpred_per_h.append(0.0)

    return {
        "best_params": best_params,
        "best_objective": best_objective,
        "train_metrics": {
            "val_rmse": train_metrics.get("val_rmse"),
            "val_mae": train_metrics.get("val_mae"),
            "val_rmse_percent": train_metrics.get("val_rmse_percent"),
            "rmse_per_horizon": train_metrics.get("rmse_per_horizon"),
            "mae_per_horizon": train_metrics.get("mae_per_horizon"),
            "upper_offsets": train_metrics.get("upper_offsets"),
            "val_upper_coverage": train_metrics.get("val_upper_coverage"),
            "underprediction_rising": train_metrics.get("underprediction_rising"),
        },
        "holdout_metrics": holdout_detail,
        "holdout_per_horizon": {
            "rmse": rmse_per_h,
            "mae": mae_per_h,
            "underprediction_rising": underpred_per_h,
        },
        "ramp_only_error": {
            "rmse": ramp_rmse,
            "mae": ramp_mae,
            "n_rising": int(rising_mask.sum()),
        },
        "upper_envelope_coverage": comparison["gru_coverage"],
        "baseline_comparison": comparison,
    }


# ── Main HPO runner ─────────────────────────────────────────────────────────


def run_gru_hpo(
    data_source: str = "clarknet",
    n_trials: int = DEFAULT_TRIALS,
    output_dir: str | Path | None = None,
    seed: int = HPO_SEED,
    n_folds: int = DEFAULT_N_FOLDS,
    holdout_ratio: float = DEFAULT_HOLDOUT_RATIO,
    horizon: int = DEFAULT_HORIZON,
) -> dict[str, Any]:
    """Run full GRU HPO pipeline with temporal CV and baseline comparison.

    Steps:
        1. Load data at native 15-second resolution; reserve final 20% as holdout.
        2. Run Optuna TPE search with expanding-window temporal CV on the
           development set (80%).
        3. Train the best model on the full development set.
        4. Compare against persistence and linear-trend baselines on the
           untouched holdout. Apply the promotion gate.
        5. Persist study JSON, best params, best artifact, and report.

    Returns:
        Summary dict with best trial, objective, promotion gate result, and
        output paths.
    """
    output_dir = Path(output_dir) if output_dir else PROJECT_ROOT / "results" / "models" / "gru" / "hpo"
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Load data ──
    values = _load_data(data_source)
    logger.info("gru_hpo_data_loaded", data_source=data_source, n_samples=len(values))

    # ── Temporal split: reserve holdout BEFORE HPO ──
    dev_values, holdout_values = temporal_split(values, holdout_ratio=holdout_ratio)
    holdout_start = len(dev_values)
    logger.info(
        "gru_hpo_split",
        dev_samples=len(dev_values),
        holdout_samples=len(holdout_values),
        holdout_start_idx=holdout_start,
    )

    # ── Optuna study ──
    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=seed),
    )
    objective = create_gru_objective(dev_values, horizon, n_folds, seed)
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    best = study.best_trial
    best_params = best.params
    best_value = float(best.value) if best.value is not None else float("inf")

    logger.info(
        "gru_hpo_search_complete",
        best_trial=best.number,
        best_objective=round(best_value, 4),
        best_params=best_params,
    )

    # ── Train best model on full development set ──
    best_config = _params_to_config(best_params)
    _set_deterministic(seed)

    from prediction.gru_predictor import GRUPredictor

    best_predictor = GRUPredictor(config=best_config)
    dev_df = pd.DataFrame({"total_requests": dev_values})
    train_metrics = best_predictor.train(dev_df, val_ratio=0.15)

    # ── Baseline comparison on untouched holdout ──
    comparison = run_baseline_comparison(
        best_predictor, values, best_config.sequence_length, horizon, eval_start=holdout_start
    )

    if comparison["promoted_model"] is None:
        logger.warning(
            "gru_promotion_gate_failed",
            gate=comparison["promotion_gate"],
        )

    # ── Persist results ──
    best_predictor.save_model(output_dir / "best_artifact.pt")

    study_data = _build_study_json(study, seed, holdout_start, len(values), data_source, n_trials)
    (output_dir / "hpo_study.json").write_text(json.dumps(study_data, indent=2))

    best_data: dict[str, Any] = {"params": best_params, "objective": best_value}
    (output_dir / "best_params.json").write_text(json.dumps(best_data, indent=2))

    report = _build_hpo_report(
        best_predictor,
        train_metrics,
        comparison,
        best_params,
        best_value,
        holdout_values,
        best_config.sequence_length,
    )
    (output_dir / "hpo_report.json").write_text(json.dumps(report, indent=2))

    result: dict[str, Any] = {
        "best_trial": best.number,
        "best_objective": best_value,
        "best_params": best_params,
        "output_dir": str(output_dir),
        "promotion_gate": comparison["promotion_gate"],
        "promoted_model": comparison["promoted_model"],
    }

    logger.info(
        "gru_hpo_complete",
        output_dir=str(output_dir),
        promoted=comparison["promoted_model"],
    )

    return result
