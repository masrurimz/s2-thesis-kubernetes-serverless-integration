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
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
import numpy as np
import pandas as pd
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
    CLARKNET_TOTAL,
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

from experiment.tuning import splits as split_protocol  # noqa: E402  (protocol pin below)

# Ticket literal for the window120 embargo. The formula minimum is
# 120 + 9 - 1 = 128; the task pins 382, which is strictly stronger and still
# keeps the replay window inside the test region. Both numbers are recorded.
WINDOW120_EMBARGO = 382
WINDOW120_FORMULA_MIN = 120 + DEFAULT_HORIZON - 1
WINDOW120_VAL_SPAN = 500

PROBE_REPLAY_WINDOW = (28940, 29020)

PINBALL_QUANTILE = 0.9


VARIANTS = (
    "baseline",
    "window120",
    "calendar",
    "revin",
    "log_target",
    "pinball",
    "ensemble",
    # ── second probe wave: interval, normalization, representation levers ──
    "interval30",
    "interval60",
    "revin_robust",
    "nlinear",
    "diff_target",
    "robust_scale",
    "quantile_norm",
    "nbeats",
    "roll_stats",
    "ewma",
    "diff_input",
    "decomp",
    # ── cross-corpus lever: pretrain on Calgary, fine-tune on ClarkNet ──
    "calgary_pretrain",
    # ── capacity-relative target: time/probability of crossing the
    # calibration capacity threshold instead of nine absolute RPS values ──
    "t_cross",
)


def probe_capacity(config_path: str | Path | None = None) -> dict[str, Any]:
    """Capacity threshold for the t_cross target, from the central calibration.

    The controller's saturation model: r_saturation_per_replica RPS per
    replica, capped at the calibration replica bound (max_k8s_replicas). The
    threshold is scenario-dependent: ``config_path`` resolves it from the
    calibration a specific arm runs under (e.g. the definitive paired H2
    profile, whose calibration overrides the cap to 10); without it the code
    defaults apply. Never hard-coded; the resolved values and their source
    are recorded in the variant JSON.
    """
    from shared.models.calibration import CalibrationConfig, get_calibration

    if config_path is not None:
        cal = CalibrationConfig.load(config_path)
        source = f"shared.models.calibration.CalibrationConfig.load({config_path})"
    else:
        cal = get_calibration()
        source = "shared.models.calibration.get_calibration()"
    return {
        "r_saturation_per_replica": float(cal.r_saturation_per_replica),
        "replicas_at_capacity": int(cal.max_k8s_replicas),
        "capacity_rps": float(cal.r_saturation_per_replica) * int(cal.max_k8s_replicas),
        "source": source,
    }


DEFAULT_STUDY_BUNDLE = PROJECT_ROOT / "results" / "models" / "gru" / "study"

# Resampled-series variants: sample interval in seconds. Splits are re-derived
# proportionally from the frozen fractions; the wall-clock horizon stays at
# 135 s via horizon_steps = ceil(135 / interval).
INTERVAL_VARIANTS = {"interval30": 30, "interval60": 60}
HORIZON_WALL_CLOCK_SEC = 135

# Causal (trailing) input-channel levers. Windows are in 15 s samples.
ROLL_WINDOWS_SAMPLES = (8, 40)  # 2 min and 10 min at 15 s
EWMA_HALFLIFE_SAMPLES = (4, 20)  # ~1 min and ~5 min at 15 s
DIFF_INPUT_LAGS = (1, 4)  # first and fourth differences
DECOMP_MA_SAMPLES = 40  # 10 min trailing moving-average trend
FEATURE_VARIANTS = ("roll_stats", "ewma", "diff_input", "decomp")

NEW_WAVE_VARIANTS = (
    *INTERVAL_VARIANTS,
    "revin_robust",
    "nlinear",
    "diff_target",
    "robust_scale",
    "quantile_norm",
    "nbeats",
    *FEATURE_VARIANTS,
)

# Canonical-normalized variants: value-channel statistics come from the
# protocol's normalizer_stats (log1p + median/IQR on the train region only).
CANONICAL_VARIANTS = (*INTERVAL_VARIANTS, "nbeats", *FEATURE_VARIANTS)

# Early-stopping span carved from each blocked-CV fold's train tail, with the
# formula embargo between the fit region and the early-stop window.
FOLD_VAL_SPAN = 500

# sha256 of apps/experiment/experiment/tuning/splits.py, the protocol module every
# probe record fingerprints. The tripwire is deliberate: a probe result is only
# comparable to another probe result when both ran against the same protocol, so
# moving this pin is a decision, not a formality.
#
# 2026-09-13: 5f937edb… → fe9534ab… — dropped a stray `f` prefix from a literal
# with no placeholders (ruff F541) in the summary writer.
# 2026-09-13: fe9534ab… → d0f28820… — added SplitSpec.require_region and routed
# the call sites that assumed a present region through it. Every boundary,
# embargo, fold geometry and normalizer statistic is unchanged; the new method
# raises where the old code would have raised AttributeError on None.
#
# Both moves were cosmetic or refactor-only, which is the pin's weakness: it
# hashes source text, so it cannot tell a renamed local from a moved boundary.
# A fingerprint over the protocol's *outputs* (the boundary tuples and fold
# geometry) would fire only on changes that can actually invalidate a record.
# Worth doing before the next probe wave; not done here.
SPLITS_PIN_SHA256 = "d0f288203f07c4ff6f7ed64fd7aa0c509a285161b607244966ce7915ad3c9e1c"

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
    eval_end: int | None = None  # bounded evaluation block (blocked-CV folds)
    stats_end: int | None = None  # region end for statistic fitting (defaults to fit_end)

    @property
    def embargo_min(self) -> int:
        return self.seq_len + self.horizon - 1

    def __post_init__(self) -> None:
        if self.val_start - self.fit_end < self.embargo_min:
            raise ValueError(f"fit→val gap {self.val_start - self.fit_end} < embargo {self.embargo_min}")
        if self.test_start - self.val_end < self.embargo_min:
            raise ValueError(f"val→test gap {self.test_start - self.val_end} < embargo {self.embargo_min}")
        if self.eval_end is not None and self.eval_end - self.test_start < self.seq_len + self.horizon:
            raise ValueError(
                f"eval block [{self.test_start}, {self.eval_end}) cannot host a {self.seq_len}+{self.horizon} window"
            )

    def to_dict(self) -> dict[str, Any]:
        out = {
            "seq_len": self.seq_len,
            "horizon": self.horizon,
            "fit_end": self.fit_end,
            "val_start": self.val_start,
            "val_end": self.val_end,
            "test_start": self.test_start,
            "embargo_min_required": self.embargo_min,
            "embargo_used": self.embargo_used,
            "train_region": [0, self.val_end],
            "test_region": [self.test_start, self.eval_end if self.eval_end is not None else "end"],
        }
        if self.stats_end is not None:
            out["stats_end"] = self.stats_end
        return out


def mapped_replay_window(sample_interval_sec: int) -> tuple[int, int]:
    """Replay window indices mapped from the frozen 15 s literals by ratio."""
    factor = sample_interval_sec // FIXED_SAMPLE_INTERVAL
    return (PROBE_REPLAY_WINDOW[0] // factor, PROBE_REPLAY_WINDOW[1] // factor)


def derived_interval_windows(sample_interval_sec: int, n_total: int) -> ProbeWindows:
    """Proportional splits for a resampled series with the derived embargo.

    Boundaries start at the frozen ClarkNet fractions (train 22500/40315,
    validation 22539-26205, test 26243/40315) scaled to ``n_total``; each gap
    is then widened to the embargo ``seq_len + horizon_steps - 1`` when the
    proportional position falls short. The wall-clock horizon is held at
    135 s via ``horizon_steps = ceil(135 / interval)`` (5 steps at 30 s,
    3 at 60 s), so the realised wall-clock horizon is 150 s / 180 s.
    """
    horizon = math.ceil(HORIZON_WALL_CLOCK_SEC / sample_interval_sec)
    seq_len = 30
    embargo = seq_len + horizon - 1

    fit_end = CLARKNET_TRAIN_END * n_total // CLARKNET_TOTAL
    val_start = max(CLARKNET_VAL_START * n_total // CLARKNET_TOTAL, fit_end + embargo)
    val_end = CLARKNET_VAL_END * n_total // CLARKNET_TOTAL
    test_start = max(CLARKNET_TEST_START * n_total // CLARKNET_TOTAL, val_end + embargo)

    windows = ProbeWindows(
        seq_len=seq_len,
        horizon=horizon,
        fit_end=fit_end,
        val_start=val_start,
        val_end=val_end,
        test_start=test_start,
        embargo_used=max(test_start - val_end, val_start - fit_end),
    )
    replay = mapped_replay_window(sample_interval_sec)
    if windows.test_start > replay[0] or replay[1] >= n_total:
        raise ValueError(
            f"resampled {sample_interval_sec}s test_start {windows.test_start} leaves the replay "
            f"window {replay} outside the test portion [test_start, {n_total}) — protocol violated"
        )
    if val_end <= val_start or fit_end <= 0 or test_start + seq_len + horizon + 1 > n_total:
        raise ValueError(f"derived {sample_interval_sec}s boundaries leave no usable region: {windows.to_dict()}")
    return windows


def probe_windows(variant: str, n_total: int = 40315) -> ProbeWindows:
    """Frozen boundaries for 30-sample variants; derived ones for window120/resampled."""
    if variant in INTERVAL_VARIANTS:
        return derived_interval_windows(INTERVAL_VARIANTS[variant], n_total)
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


def ols_autoreg_fit(values: np.ndarray, windows: ProbeWindows, fit_end: int | None = None) -> np.ndarray:
    """Least-squares AR(seq_len) → horizon coefficients from the training region.

    Uses ``values[:val_end]`` (the full training region) exclusively; the test
    region never influences the fit. ``fit_end`` narrows the fit to
    ``values[:fit_end]`` for the validation-screening reference arm, which
    must stay blind to the windows it is scored on.
    """
    end = windows.val_end if fit_end is None else fit_end
    X, y, _, _ = _segment_sequences(values, 0, end, windows.seq_len, windows.horizon)
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
    mode: str  # "zscore" | "revin" | "revin_robust" | "robust" | "quantile" | "nlinear" | "diff"
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
    test_mu: np.ndarray | None = None  # revin-family per-window centre (n_test,)
    test_sd: np.ndarray | None = None  # revin-family per-window scale (n_test,)
    val_mu: np.ndarray | None = None  # revin-family validation per-window centre
    val_sd: np.ndarray | None = None  # revin-family validation per-window scale
    y_val_raw: np.ndarray | None = None  # (n_val, horizon) RPS targets for validation screening
    last_val_raw: np.ndarray | None = None  # (n_val,) last observed value per validation window
    scaler: Any = None  # fitted sklearn transformer (quantile_norm only)
    capacity_rps: float | None = None  # t_cross threshold (calibration-derived)
    target_mode: str = "point"  # "point" | "t_cross"

    def _denorm(self, preds_norm: np.ndarray, split: str) -> np.ndarray:
        """Map normalised network outputs back to the original RPS scale."""
        if self.target_mode == "t_cross":
            # Outputs are per-step crossing logits; stable sigmoid to [0, 1].
            pos = preds_norm >= 0
            probs = np.empty_like(preds_norm, dtype=np.float64)
            probs[pos] = 1.0 / (1.0 + np.exp(-preds_norm[pos]))
            ex = np.exp(preds_norm[~pos])
            probs[~pos] = ex / (1.0 + ex)
            return probs
        if self.mode == "canonical":
            if self.scaler is None:
                raise ValueError("canonical variant is missing its protocol normalizer stats")
            return split_protocol.invert_normalizer(preds_norm, self.scaler)
        if self.mode in ("revin", "revin_robust"):
            mu, sd = (self.test_mu, self.test_sd) if split == "test" else (self.val_mu, self.val_sd)
            if mu is None or sd is None:
                raise ValueError(f"{self.mode} variant is missing its per-window statistics for {split}")
            preds = preds_norm * sd[:, None] + mu[:, None]
        elif self.mode == "nlinear":
            last = self.last_test_raw if split == "test" else self.last_val_raw
            if last is None:
                raise ValueError(f"nlinear variant is missing last-value anchors for {split}")
            preds = preds_norm * self.z_std + last[:, None]
        elif self.mode == "diff":
            last = self.last_test_raw if split == "test" else self.last_val_raw
            if last is None:
                raise ValueError(f"diff variant is missing last-value anchors for {split}")
            deltas = preds_norm * self.z_std + self.z_mean
            preds = last[:, None] + np.cumsum(deltas, axis=1)
        elif self.mode == "quantile":
            if self.scaler is None:
                raise ValueError("quantile_norm variant is missing its fitted transformer")
            shape = preds_norm.shape
            preds = self.scaler.inverse_transform(preds_norm.reshape(-1, 1)).reshape(shape)
        else:  # "zscore" | "robust" (z_mean/z_std hold median/IQR for robust)
            preds = preds_norm * self.z_std + self.z_mean
        if self.log_space:
            preds = np.expm1(preds)
        return preds

    def denormalize_predictions(self, preds_norm: np.ndarray) -> np.ndarray:
        """Map normalised network outputs back to the original RPS scale (test)."""
        return self._denorm(preds_norm, "test")

    def denormalize_val_predictions(self, preds_norm: np.ndarray) -> np.ndarray:
        """Map normalised validation outputs back to the original RPS scale."""
        return self._denorm(preds_norm, "val")


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


def _revin_robust_normalize(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Instance-normalise each window with its own median and IQR.

    The bursty request series puts in-window outliers inside every window;
    median/IQR statistics ignore them instead of being dragged by them.
    """
    mu = np.median(X, axis=1)
    sd = np.percentile(X, 75, axis=1) - np.percentile(X, 25, axis=1) + _EPS
    X_norm = (X - mu[:, None]) / sd[:, None]
    y_norm = (y - mu[:, None]) / sd[:, None]
    return X_norm.astype(np.float32), y_norm.astype(np.float32), mu.astype(np.float32), sd.astype(np.float32)


def _trailing_feature_channels(variant: str, values: np.ndarray) -> tuple[np.ndarray | None, list[str]]:
    """Causal per-step extra input channels; trailing windows only (no future leakage)."""
    s = pd.Series(values, dtype=np.float64)
    cols: list[pd.Series] = []
    names: list[str] = []
    if variant == "roll_stats":
        for w in ROLL_WINDOWS_SAMPLES:
            roll = s.rolling(w, min_periods=1)
            cols += [roll.mean(), roll.std(), roll.min(), roll.max()]
        names = [f"{stat}_tr{w}s" for w in ROLL_WINDOWS_SAMPLES for stat in ("mean", "std", "min", "max")]
    elif variant == "ewma":
        cols = [s.ewm(halflife=h, adjust=False).mean() for h in EWMA_HALFLIFE_SAMPLES]
        names = [f"ewma_hl{h}" for h in EWMA_HALFLIFE_SAMPLES]
    elif variant == "diff_input":
        cols = [s.diff(lag) for lag in DIFF_INPUT_LAGS]
        names = [f"diff_lag{lag}" for lag in DIFF_INPUT_LAGS]
    elif variant == "decomp":
        trend = s.rolling(DECOMP_MA_SAMPLES, min_periods=1).mean()
        cols = [trend, s - trend]
        names = ["ma_trend_tr40", "ma_residual_tr40"]
    else:
        return None, []
    arr = np.stack([c.to_numpy(dtype=np.float64) for c in cols], axis=1)
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    return arr, names


def _gather_channels(
    channels: np.ndarray,
    base: np.ndarray,
    seq_len: int,
    fit_end: int,
) -> np.ndarray:
    """Slice per-step channel values for windows at ``base``, z-scored with train stats."""
    steps = base[:, None] + np.arange(seq_len, dtype=np.int64)[None, :]
    raw = channels[steps]  # (n, seq_len, k)
    stats_src = channels[:fit_end]
    mean = stats_src.mean(axis=0)
    std = stats_src.std(axis=0) + _EPS
    return ((raw - mean[None, None, :]) / std[None, None, :]).astype(np.float32)


def build_variant_arrays(
    variant: str,
    values: np.ndarray,
    windows: ProbeWindows,
    capacity: float | None = None,
    canonical_spec: Any = None,
) -> VariantArrays:
    """Build fit/val/test arrays isolating exactly one lever.

    ``canonical_spec`` supplies the protocol normalizer for canonical-mode
    variants: statistics come from ``normalizer_stats`` fitted on the spec's
    train region only (splits.py, rationale 4) — never fitted by hand.
    ``windows.stats_end`` overrides the region every lever-specific statistic
    is fitted on (blocked-CV folds fit on the full fold-train tail).
    """
    seq, horizon = windows.seq_len, windows.horizon
    log_space = variant == "log_target"
    series = np.log1p(values.astype(np.float64)) if log_space else values.astype(np.float64)

    if variant == "diff_target":
        work = np.diff(series, prepend=series[:1])  # first delta is 0, length preserved
    else:
        work = series

    stats_end = windows.stats_end if windows.stats_end is not None else windows.fit_end
    eval_stop = windows.eval_end if windows.eval_end is not None else len(values)
    norm_stats: Any = None
    if variant in CANONICAL_VARIANTS:
        if canonical_spec is None:
            raise ValueError(
                f"{variant} is canonical-normalized: pass the protocol SplitSpec so "
                "normalizer_stats fits on the train region only"
            )
        norm_stats = split_protocol.normalizer_stats(values, canonical_spec)
        work = split_protocol.apply_normalizer(work, norm_stats)

    X_fit_s, y_fit_s, last_fit_s, base_fit = _segment_sequences(work, 0, windows.fit_end, seq, horizon)
    scaler: Any = None
    X_val_s, y_val_s, last_val_s, base_val = _segment_sequences(work, windows.val_start, windows.val_end, seq, horizon)
    X_test_s, _, last_test_s, base_test = _segment_sequences(work, windows.test_start, eval_stop, seq, horizon)

    if variant == "t_cross":
        # Capacity-relative target: identical z-scored value inputs as the
        # baseline, but per-step binary labels (raw RPS >= capacity) instead
        # of absolute RPS targets. The lever is the label, nothing else.
        cap = float(probe_capacity()["capacity_rps"] if capacity is None else capacity)
        feat_mean = float(work[: windows.fit_end].mean())
        feat_std = float(work[: windows.fit_end].std()) + _EPS
        _, y_test_raw_t, last_test_raw_t, _ = _segment_sequences(
            values.astype(np.float64), windows.test_start, len(values), seq, horizon
        )
        _, y_val_raw_t, last_val_raw_t, _ = _segment_sequences(
            values.astype(np.float64), windows.val_start, windows.val_end, seq, horizon
        )
        return VariantArrays(
            variant=variant,
            mode="zscore",
            log_space=False,
            seq_len=seq,
            horizon=horizon,
            X_fit=((X_fit_s - feat_mean) / feat_std).astype(np.float32)[:, :, None],
            y_fit=crossing_labels(y_fit_s, cap),
            X_val=((X_val_s - feat_mean) / feat_std).astype(np.float32)[:, :, None],
            y_val=crossing_labels(y_val_s, cap),
            X_test=((X_test_s - feat_mean) / feat_std).astype(np.float32)[:, :, None],
            y_test_raw=y_test_raw_t,
            last_test_raw=last_test_raw_t,
            z_mean=0.0,  # identity: outputs are logits, not scaled RPS
            z_std=1.0,
            y_val_raw=y_val_raw_t,
            last_val_raw=last_val_raw_t,
            capacity_rps=cap,
            target_mode="t_cross",
        )

    if variant in ("revin", "revin_robust"):
        norm = _revin_normalize if variant == "revin" else _revin_robust_normalize
        X_fit, y_fit, _, _ = norm(X_fit_s, y_fit_s)
        X_val, y_val, val_mu, val_sd = norm(X_val_s, y_val_s)
        if variant == "revin":
            mu_test = X_test_s.mean(axis=1)
            sd_test = X_test_s.std(axis=1) + _EPS
        else:
            mu_test = np.median(X_test_s, axis=1)
            sd_test = np.percentile(X_test_s, 75, axis=1) - np.percentile(X_test_s, 25, axis=1) + _EPS
        X_test = ((X_test_s - mu_test[:, None]) / sd_test[:, None]).astype(np.float32)
        test_mu, test_sd = mu_test.astype(np.float32), sd_test.astype(np.float32)
        mode, z_mean, z_std = variant, 0.0, 1.0
    elif variant == "nlinear":
        residuals = X_fit_s - last_fit_s[:, None]
        z_mean, z_std = 0.0, float(residuals.std()) + _EPS
        X_fit = ((X_fit_s - last_fit_s[:, None]) / z_std).astype(np.float32)
        y_fit = ((y_fit_s - last_fit_s[:, None]) / z_std).astype(np.float32)
        X_val = ((X_val_s - last_val_s[:, None]) / z_std).astype(np.float32)
        y_val = ((y_val_s - last_val_s[:, None]) / z_std).astype(np.float32)
        X_test = ((X_test_s - last_test_s[:, None]) / z_std).astype(np.float32)
        test_mu, test_sd, val_mu, val_sd = None, None, None, None
        mode = "nlinear"
    elif variant == "diff_target":
        z_mean = float(work[:stats_end].mean())
        z_std = float(work[:stats_end].std()) + _EPS
        X_fit = ((X_fit_s - z_mean) / z_std).astype(np.float32)
        y_fit = ((y_fit_s - z_mean) / z_std).astype(np.float32)
        X_val = ((X_val_s - z_mean) / z_std).astype(np.float32)
        y_val = ((y_val_s - z_mean) / z_std).astype(np.float32)
        X_test = ((X_test_s - z_mean) / z_std).astype(np.float32)
        test_mu, test_sd, val_mu, val_sd = None, None, None, None
        mode = "diff"
    elif variant == "robust_scale":
        fit_slice = series[:stats_end]
        z_mean = float(np.median(fit_slice))
        z_std = float(np.percentile(fit_slice, 75) - np.percentile(fit_slice, 25)) + _EPS
        X_fit = ((X_fit_s - z_mean) / z_std).astype(np.float32)
        y_fit = ((y_fit_s - z_mean) / z_std).astype(np.float32)
        X_val = ((X_val_s - z_mean) / z_std).astype(np.float32)
        y_val = ((y_val_s - z_mean) / z_std).astype(np.float32)
        X_test = ((X_test_s - z_mean) / z_std).astype(np.float32)
        test_mu, test_sd, val_mu, val_sd = None, None, None, None
        mode = "robust"
    elif variant == "quantile_norm":
        from sklearn.preprocessing import QuantileTransformer

        transformer = QuantileTransformer(
            output_distribution="normal",
            n_quantiles=min(1000, stats_end),
            subsample=100_000,
            random_state=42,
        )
        transformer.fit(series[:stats_end].reshape(-1, 1))

        def _t(a: np.ndarray) -> np.ndarray:
            return transformer.transform(a.reshape(-1, 1)).reshape(a.shape).astype(np.float32)

        X_fit, y_fit = _t(X_fit_s), _t(y_fit_s)
        X_val, y_val = _t(X_val_s), _t(y_val_s)
        X_test = _t(X_test_s)
        test_mu, test_sd, val_mu, val_sd = None, None, None, None
        scaler = transformer
        mode, z_mean, z_std = "quantile", 0.0, 1.0
    elif variant in CANONICAL_VARIANTS:
        # Windows are already in canonical normalized space; denormalization
        # goes through invert_normalizer with the fitted protocol stats.
        X_fit, y_fit = X_fit_s.astype(np.float32), y_fit_s.astype(np.float32)
        X_val, y_val = X_val_s.astype(np.float32), y_val_s.astype(np.float32)
        X_test = X_test_s.astype(np.float32)
        test_mu, test_sd, val_mu, val_sd = None, None, None, None
        scaler = norm_stats
        mode, z_mean, z_std = "canonical", 0.0, 1.0
    else:
        z_mean = float(series[:stats_end].mean())
        z_std = float(series[:stats_end].std()) + _EPS
        X_fit = ((X_fit_s - z_mean) / z_std).astype(np.float32)
        y_fit = ((y_fit_s - z_mean) / z_std).astype(np.float32)
        X_val = ((X_val_s - z_mean) / z_std).astype(np.float32)
        y_val = ((y_val_s - z_mean) / z_std).astype(np.float32)
        X_test = ((X_test_s - z_mean) / z_std).astype(np.float32)
        test_mu, test_sd, val_mu, val_sd = None, None, None, None
        mode = "zscore"

    if variant == "calendar":
        # Value channel is already normalised; append raw sin/cos in [-1, 1].
        X_fit = np.concatenate([X_fit[:, :, None], _calendar_features(base_fit, seq)], axis=-1)
        X_val = np.concatenate([X_val[:, :, None], _calendar_features(base_val, seq)], axis=-1)
        X_test = np.concatenate([X_test[:, :, None], _calendar_features(base_test, seq)], axis=-1)
    elif variant in FEATURE_VARIANTS:
        channels, _names = _trailing_feature_channels(variant, values.astype(np.float64))
        assert channels is not None
        X_fit = np.concatenate([X_fit[:, :, None], _gather_channels(channels, base_fit, seq, stats_end)], axis=-1)
        X_val = np.concatenate([X_val[:, :, None], _gather_channels(channels, base_val, seq, stats_end)], axis=-1)
        X_test = np.concatenate([X_test[:, :, None], _gather_channels(channels, base_test, seq, stats_end)], axis=-1)
    else:
        X_fit = X_fit[:, :, None]
        X_val = X_val[:, :, None]
        X_test = X_test[:, :, None]

    _, y_test_raw, last_test_raw, _ = _segment_sequences(
        values.astype(np.float64), windows.test_start, eval_stop, seq, horizon
    )
    _, y_val_raw, last_val_raw, _ = _segment_sequences(
        values.astype(np.float64), windows.val_start, windows.val_end, seq, horizon
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
        val_mu=val_mu,
        val_sd=val_sd,
        y_val_raw=y_val_raw,
        last_val_raw=last_val_raw,
        scaler=scaler,
    )


def variant_input_size(variant: str) -> int:
    """Feature channels per timestep for each variant (1 value + extras)."""
    if variant == "calendar":
        return 3
    if variant == "roll_stats":
        return 1 + 2 * 4
    if variant == "ewma":
        return 1 + len(EWMA_HALFLIFE_SAMPLES)
    if variant == "diff_input":
        return 1 + len(DIFF_INPUT_LAGS)
    if variant == "decomp":
        return 3
    return 1


def probe_config(variant: str, windows: ProbeWindows, epochs: int, patience: int) -> GRUConfig:
    """Current recipe (GRUConfig defaults) at the probe budget and window."""
    return GRUConfig(
        input_size=variant_input_size(variant),
        cell="gru",
        hidden_size=128,
        num_layers=1,
        sequence_length=windows.seq_len,
        prediction_horizon=windows.horizon,
        sample_interval_sec=INTERVAL_VARIANTS.get(variant, FIXED_SAMPLE_INTERVAL),
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


# ── Capacity-relative target (t_cross): labels, metrics, distributions ──────


def crossing_labels(y_raw: np.ndarray, capacity: float) -> np.ndarray:
    """Per-step binary labels: 1 where the raw target meets or exceeds capacity."""
    return (np.asarray(y_raw, dtype=np.float64) >= capacity).astype(np.float32)


def _first_crossing_steps(labels: np.ndarray) -> np.ndarray:
    """First crossing step (0-based) per window; -1 when the horizon never crosses."""
    crossed = labels >= 0.5
    any_cross = crossed.any(axis=1)
    return np.where(any_cross, crossed.argmax(axis=1), -1).astype(np.int64)


def score_crossing_predictions(probs: np.ndarray, y_raw: np.ndarray, capacity: float) -> dict[str, Any]:
    """Capacity-relative metric block for one arm on identical windows.

    ``probs`` are per-step crossing probabilities in [0, 1]; the OLS arm is
    scored by thresholding its RPS forecasts at the same capacity. Primary
    metric: per-step Brier (lower is better). ``t_cross_mae_steps`` is
    measured on windows whose true horizon contains a crossing; a
    predicted-no-crossing counts as ``horizon + 1`` steps late. NaN means no
    window in the region ever crosses — the label is degenerate there.
    """
    z = (np.asarray(y_raw, dtype=np.float64) >= capacity).astype(np.float64)
    p = np.clip(np.asarray(probs, dtype=np.float64), 0.0, 1.0)
    horizon = z.shape[1]

    brier = float(np.mean((p - z) ** 2))
    p_win = 1.0 - np.prod(1.0 - p, axis=1)
    actual_win = z.any(axis=1)
    pred_win = p_win >= 0.5

    tp = int(np.sum(pred_win & actual_win))
    fp = int(np.sum(pred_win & ~actual_win))
    fn = int(np.sum(~pred_win & actual_win))
    tn = int(np.sum(~pred_win & ~actual_win))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    t_actual = _first_crossing_steps(z)
    t_pred = _first_crossing_steps(p)
    crossed_mask = t_actual >= 0
    if crossed_mask.sum() > 0:
        ta, tpred = t_actual[crossed_mask], t_pred[crossed_mask]
        err = np.where(tpred >= 0, np.abs(tpred - ta), float(horizon + 1))
        t_mae = float(np.mean(err))
        detected = float(np.mean(tpred >= 0))
    else:
        t_mae = float("nan")
        detected = 0.0
    false_alarm = float(np.mean(pred_win[~actual_win])) if (~actual_win).sum() > 0 else 0.0

    return {
        "brier_per_step": brier,
        "brier_window": float(np.mean((p_win - actual_win.astype(float)) ** 2)),
        "crossing_accuracy": float(np.mean(pred_win == actual_win)),
        "crossing_precision": precision,
        "crossing_recall": recall,
        "crossing_f1": f1,
        "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "t_cross_mae_steps": t_mae,
        "t_cross_detection_rate": detected,
        "false_alarm_rate": false_alarm,
        "n_windows_crossed": int(crossed_mask.sum()),
        "n_windows": int(len(z)),
    }


def crossing_label_distribution(values: np.ndarray, windows: ProbeWindows, capacity: float) -> dict[str, Any]:
    """Crossing prevalence per region on the variant's own windows (report only).

    Reported for class-balance assessment before any training. The test-region
    row is recorded for completeness; selection never consults it.
    """
    out: dict[str, Any] = {}
    regions = (
        ("fit", 0, windows.fit_end),
        ("validation", windows.val_start, windows.val_end),
        ("test", windows.test_start, len(values)),
    )
    for name, a, b in regions:
        _, y_raw, _, _ = _segment_sequences(values.astype(np.float64), a, b, windows.seq_len, windows.horizon)
        z = crossing_labels(y_raw, capacity)
        out[name] = {
            "n_windows": int(len(z)),
            "n_crossed": int(z.any(axis=1).sum()),
            "frac_windows_crossed": float(z.any(axis=1).mean()),
            "frac_steps_at_or_above_capacity": float(z.mean()),
        }
    return out


def screen_t_cross_on_validation(
    values: np.ndarray,
    windows: ProbeWindows,
    arrays: VariantArrays,
    val_probs: np.ndarray,
    capacity: float,
) -> dict[str, Any]:
    """Validation-region screening for t_cross; the test region is never consulted.

    Mirrors the blind-OLS discipline of ``screen_variant_on_validation``: the
    OLS reference is fitted on ``values[:fit_end]`` only, then its validation
    forecasts are thresholded at the same capacity. Selection uses this block
    only; ``beats_ols`` compares per-step Brier scores on identical windows.
    """
    seq, horizon = windows.seq_len, windows.horizon
    X_val_raw, y_val_raw, _, _ = _segment_sequences(
        values.astype(np.float64), windows.val_start, windows.val_end, seq, horizon
    )
    coef = ols_autoreg_fit(values, windows, fit_end=windows.fit_end)
    ols_val_preds = ols_autoreg_predict(coef, X_val_raw)

    var_block = score_crossing_predictions(val_probs, y_val_raw, capacity)
    ols_block = score_crossing_predictions((ols_val_preds >= capacity).astype(float), y_val_raw, capacity)
    return {
        "region": "validation",
        "test_used_for_selection": False,
        "capacity_rps": float(capacity),
        "variant": var_block,
        "ols": ols_block,
        "beats_ols": bool(var_block["brier_per_step"] < ols_block["brier_per_step"]),
    }


# ── Second-wave metric additions (validation screening, MASE, DM, day type) ──


def mase_against_seasonal_naive(arm: dict[str, Any], seasonal_naive: dict[str, Any]) -> float:
    """MASE with the seasonal period scaled to the variant's sample interval.

    The denominator is the seasonal-naive arm's MAE on the same windows and
    the same season length (one day expressed in the variant's samples), so
    the ratio stays comparable across intervals.
    """
    denom = seasonal_naive.get("mae")
    return float(arm["mae"] / denom) if denom and denom > 0 else float("nan")


def diebold_mariano(
    residuals_variant: np.ndarray,
    residuals_ols: np.ndarray,
    horizon: int,
) -> dict[str, Any]:
    """Diebold-Mariano test of squared-error loss against the OLS forecast.

    Loss is averaged across the horizon per forecast origin; the HAC variance
    uses ``horizon - 1`` lags (Newey-West), the standard correction for
    overlapping h-step forecasts. One-sided p-value under H1 "variant loss is
    lower": negative DM statistics give small p.
    """
    l_var = np.mean(residuals_variant**2, axis=1)
    l_ols = np.mean(residuals_ols**2, axis=1)
    d = l_var - l_ols
    n = len(d)
    dbar = float(d.mean())

    def gamma(k: int) -> float:
        if k == 0:
            return float(np.mean((d - dbar) ** 2))
        return float(np.mean((d[:-k] - dbar) * (d[k:] - dbar)))

    lag = max(horizon - 1, 1)
    hac_var = gamma(0) + 2.0 * sum(gamma(k) for k in range(1, lag + 1))
    if hac_var <= 0:
        dm = 0.0
    else:
        dm = dbar / math.sqrt(hac_var / n)
    p_one_sided = 0.5 * (1.0 + math.erf(dm / math.sqrt(2.0)))
    return {
        "dm_stat": float(dm),
        "p_value_one_sided": float(p_one_sided),
        "hac_lag": int(lag),
        "n_origins": int(n),
        "hypothesis": "one-sided H1: variant squared-error loss < OLS loss",
    }


DAY_TYPE_SEGMENTS = ("fri_evening", "sat", "sun", "mon")


def day_type_labels(origin_timestamps: pd.DatetimeIndex) -> np.ndarray:
    """Bucket test-window origins into Fri-evening / Sat / Sun / Mon labels.

    The frozen test region starts Friday 1995-09-01 evening and ends Monday
    1995-09-04 03:59 UTC; the day-type split quantifies the weekend-regime
    gap instead of arguing about it.
    """
    out: list[str] = []
    for ts in origin_timestamps:
        day = ts.dayofweek  # Monday=0 .. Sunday=6
        if day == 4:  # Friday
            out.append("fri_evening")
        elif day == 5:
            out.append("sat")
        elif day == 6:
            out.append("sun")
        elif day == 0:
            out.append("mon")
        else:
            out.append("other")
    return np.array(out)


def split_metrics_by_day_type(
    preds_variant: np.ndarray,
    preds_ols: np.ndarray,
    y_test: np.ndarray,
    labels: np.ndarray,
) -> dict[str, Any]:
    """Per-day-type RMSE/MAE for the variant and the OLS arm on identical windows."""
    out: dict[str, Any] = {}
    for seg in list(DAY_TYPE_SEGMENTS) + ["other"]:
        mask = labels == seg
        if mask.sum() == 0:
            continue
        var_res = y_test[mask] - preds_variant[mask]
        ols_res = y_test[mask] - preds_ols[mask]
        var_rmse = float(np.sqrt(np.mean(var_res**2)))
        ols_rmse = float(np.sqrt(np.mean(ols_res**2)))
        out[seg] = {
            "n_windows": int(mask.sum()),
            "variant_rmse": var_rmse,
            "variant_mae": float(np.mean(np.abs(var_res))),
            "ols_rmse": ols_rmse,
            "ols_mae": float(np.mean(np.abs(ols_res))),
            "skill_vs_ols": 1.0 - var_rmse / ols_rmse if ols_rmse > 0 else 0.0,
        }
    return out


def splits_module_fingerprint() -> dict[str, Any]:
    """sha256 of the protocol module, checked against the pinned revision."""
    import hashlib as _hashlib

    path = Path(split_protocol.__file__)
    digest = _hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "sha256": digest,
        "pinned": SPLITS_PIN_SHA256,
        "matches_pin": digest == SPLITS_PIN_SHA256,
    }


def selection_fold_windows(
    interval_sec: int,
    n_total: int,
) -> list[tuple[split_protocol.SplitSpec, ProbeWindows, split_protocol.SplitSpec]]:
    """Protocol selection folds (b2/b3/b4) mapped into probe windows.

    Fold identity and day-block geometry come from ``blocked_cv`` (15 s space,
    frozen defaults). For resampled series the day-aligned blocks are mapped
    by ratio and the embargo is re-derived in resampled samples
    (seq_len + horizon_steps - 1). Each fold carves an early-stopping span of
    ``FOLD_VAL_SPAN`` samples from its train tail, separated by the embargo.
    Returns ``(mapped_spec, probe_windows, protocol_spec)`` per fold.
    """
    factor = interval_sec // FIXED_SAMPLE_INTERVAL
    horizon = math.ceil(HORIZON_WALL_CLOCK_SEC / interval_sec)
    embargo = 30 + horizon - 1
    day = split_protocol.DAY // factor
    plan = split_protocol.blocked_cv()
    out = []
    for spec in plan.selection_folds():
        assert spec.train is not None and spec.validation is not None
        b = spec.require_region("validation").start // split_protocol.DAY
        eval_start = b * day
        eval_stop = min((b + 1) * day, n_total)
        train_stop = eval_start - embargo
        fit_end = train_stop - FOLD_VAL_SPAN - embargo
        val_start = fit_end + embargo
        windows = ProbeWindows(
            seq_len=30,
            horizon=horizon,
            fit_end=fit_end,
            val_start=val_start,
            val_end=train_stop,
            test_start=eval_start,
            embargo_used=embargo,
            eval_end=eval_stop,
            stats_end=train_stop,
        )
        replay = mapped_replay_window(interval_sec)
        if replay[0] < train_stop:
            raise ValueError(
                f"fold {spec.name}: mapped train [0, {train_stop}) contains the replay window "
                f"{replay} — protocol violation"
            )
        mapped = split_protocol.SplitSpec(
            name=f"{spec.name}@{interval_sec}s",
            corpus=spec.corpus,
            role=spec.role,
            eval_of_record=spec.eval_of_record,
            train=split_protocol.IndexRange(0, train_stop),
            validation=split_protocol.IndexRange(eval_start, eval_stop),
            test=None,
            embargo=embargo,
            profiles=spec.profiles,
            rationale=spec.rationale,
            used_for_selection=spec.used_for_selection,
        )
        out.append((mapped, windows, spec))
    if len(out) < 2:
        raise ValueError(f"protocol produced {len(out)} selection folds; screening needs >= 2")
    return out


def fold_reference_arms(values: np.ndarray, windows: ProbeWindows, season: int) -> dict[str, Any]:
    """Blind reference arms on one fold's bounded eval block."""
    seq, horizon = windows.seq_len, windows.horizon
    eval_stop = windows.eval_end if windows.eval_end is not None else len(values)
    X_eval_raw, y_eval, last_eval, _ = _segment_sequences(values, windows.test_start, eval_stop, seq, horizon)
    coef = ols_autoreg_fit(values, windows)  # fits [0, val_end) = fold train only
    ols_preds = ols_autoreg_predict(coef, X_eval_raw)
    pers_preds, pers_targets, pers_last = persistence_baseline(values[windows.test_start : eval_stop], seq, horizon)
    seas_all, seas_targets_all, seas_last_all = seasonal_naive_baseline(
        values, seq, horizon, season, windows.test_start
    )
    n_eval = len(y_eval)
    seas_preds = seas_all[:n_eval]
    if not np.array_equal(pers_targets, y_eval) or not np.array_equal(pers_last, last_eval):
        raise ValueError("persistence windows diverge from the fold's eval windows")
    if not np.array_equal(seas_targets_all[:n_eval], y_eval) or not np.array_equal(seas_last_all[:n_eval], last_eval):
        raise ValueError("seasonal naive windows diverge from the fold's eval windows")
    ols_block = score_predictions(ols_preds, y_eval, last_eval)
    pers_block = score_predictions(pers_preds, y_eval, last_eval)
    seas_block = score_predictions(seas_preds, y_eval, last_eval)
    return {
        "y_eval": y_eval,
        "last_eval": last_eval,
        "ols_preds": ols_preds,
        "ols": ols_block,
        "persistence": pers_block,
        "seasonal_naive": seas_block,
    }


def screen_variant_on_folds(
    variant: str,
    values: np.ndarray,
    interval: int,
    season: int,
    epochs: int,
    patience: int,
    device: str,
    seed: int = 42,
) -> dict[str, Any]:
    """Selection screening on the protocol's selection folds (b2/b3/b4).

    One training per fold on the fold's train region, scored once on its
    bounded eval block against blind references (OLS fitted on the fold train
    only). Aggregation uses ``aggregate_block_metrics``; the test/deployment
    region is never consulted here.
    """
    folds = selection_fold_windows(interval, len(values))
    per_fold: dict[str, Any] = {}
    var_rmse: dict[str, float] = {}
    ols_rmse: dict[str, float] = {}
    pers_rmse: dict[str, float] = {}
    for mapped_spec, fw, spec in folds:
        arrays = build_variant_arrays(variant, values, fw, canonical_spec=mapped_spec)
        config = probe_config(variant, fw, epochs, patience)
        loss_name = "mse"
        model, epochs_trained = train_probe_model(arrays, config, seed, loss_name, device)
        preds = predict_raw(model, arrays, device)
        refs = fold_reference_arms(values, fw, season)
        y_eval, last_eval = refs["y_eval"], refs["last_eval"]
        if arrays.y_test_raw is None:
            raise ValueError(f"{variant} fold arrays missing eval targets")
        if not np.array_equal(arrays.y_test_raw, y_eval) or not np.array_equal(arrays.last_test_raw, last_eval):
            raise ValueError(f"{variant} fold windows diverge from the reference arms")
        var_block = _with_skills(
            score_predictions(preds, y_eval, last_eval),
            refs["persistence"],
            refs["ols"],
        )
        var_block["mase"] = mase_against_seasonal_naive(var_block, refs["seasonal_naive"])
        var_block["dm_vs_ols"] = diebold_mariano(y_eval - preds, y_eval - refs["ols_preds"], fw.horizon)
        var_block["epochs_trained"] = epochs_trained
        per_fold[spec.name] = {
            "variant": var_block,
            "ols": refs["ols"],
            "persistence": refs["persistence"],
            "seasonal_naive": refs["seasonal_naive"],
            "windows": fw.to_dict(),
            "day_type_coverage": {
                name: round(share, 4) for name, share in spec.profiles["validation"].day_shares.items()
            },
        }
        var_rmse[spec.name] = var_block["rmse"]
        ols_rmse[spec.name] = refs["ols"]["rmse"]
        pers_rmse[spec.name] = refs["persistence"]["rmse"]

    agg_var = split_protocol.aggregate_block_metrics(var_rmse)
    agg_ols = split_protocol.aggregate_block_metrics(ols_rmse)
    agg_pers = split_protocol.aggregate_block_metrics(pers_rmse)
    return {
        "region": "selection_folds_b2_b3_b4",
        "test_used_for_selection": False,
        "per_fold": per_fold,
        "aggregate": {
            "variant_rmse": agg_var,
            "ols_rmse": agg_ols,
            "persistence_rmse": agg_pers,
            "skill_vs_ols_mean": 1.0 - agg_var["mean"] / agg_ols["mean"],
        },
        "beats_ols": bool(agg_var["mean"] < agg_ols["mean"]),
    }


def persistence_wiring_check(values: np.ndarray, interval: int, season: int) -> dict[str, Any]:
    """Fold-wiring sanity against the protocol's published persistence numbers.

    Protocol references (counts per 15 s bucket on the raw trace): selection
    folds 22.572 ± 0.124, b5 16.564, deployment 18.060. This harness measures
    RPS at the replay amplitude (counts / 15 × 33.0), so the expected values
    are the references divided by 15 and multiplied by 33.
    """
    folds = selection_fold_windows(interval, len(values))
    pers: dict[str, float] = {}
    for _, fw, spec in folds:
        refs = fold_reference_arms(values, fw, season)
        pers[spec.name] = refs["persistence"]["rmse"]
    agg = split_protocol.aggregate_block_metrics(pers)
    plan = split_protocol.blocked_cv()
    b5 = next(s for s in plan.ood_folds() if s.name.endswith("b5"))
    assert b5.validation is not None
    horizon = math.ceil(HORIZON_WALL_CLOCK_SEC / interval)
    day = split_protocol.DAY // (interval // FIXED_SAMPLE_INTERVAL)
    b5_start = (b5.validation.start // split_protocol.DAY) * day
    b5_stop = min((b5.validation.stop // split_protocol.DAY) * day, len(values))
    seq = 30
    _, y5, last5, _ = _segment_sequences(values, b5_start, b5_stop, seq, horizon)
    b5_rmse = float(np.sqrt(np.mean((np.tile(last5[:, None], (1, horizon)) - y5) ** 2)))
    expected_sel = 22.572 / 15.0 * 33.0
    expected_b5 = 16.564 / 15.0 * 33.0
    expected_ols_gate = 16.677 / 15.0 * 33.0
    ratio = agg["mean"] / expected_sel
    # At 15 s the wiring must match the protocol reference closely. Resampled
    # intervals change the persistence error systematically (bucket smoothing
    # and a 150/180 s realised horizon vs the 135 s reference), so the band
    # only guards against unit/amplitude swaps (15x or 33x), not interval
    # effects.
    lo, hi = (0.8, 1.2) if interval == FIXED_SAMPLE_INTERVAL else (0.5, 2.0)
    if not lo <= ratio <= hi:
        raise ValueError(
            f"fold wiring suspect: persistence on selection folds is {agg['mean']:.3f} RPS-amplified, "
            f"expected ≈ {expected_sel:.3f} (protocol 22.572 counts/bucket / 15 × 33); "
            "a 15x or 33x gap is a unit/amplitude mismatch, not a modelling difference"
        )
    return {
        "selection_folds_persistence_rmse": agg,
        "expected_from_protocol": {
            "counts_per_bucket": 22.572,
            "rps_amplified": expected_sel,
            "unit_conversion": "counts/bucket / 15 s * 33.0",
        },
        "ratio_to_expected": float(ratio),
        "b5_ood_persistence_rmse": b5_rmse,
        "b5_expected_rps_amplified": expected_b5,
        "ols_gate_reference": {
            "counts_per_bucket": 16.677,
            "rps_amplified": expected_ols_gate,
            "note": "per-fold OLS fitted on [0, block_start - 38); the keep gate",
        },
    }


def deployment_arm_spec(values: np.ndarray, interval: int, windows: ProbeWindows) -> Any:
    """Protocol spec for the deployment (frozen test) arm of a variant.

    15 s variants use the validated ``deployment_split`` directly. Resampled
    variants get the frozen deployment regions mapped by ratio (day-aligned,
    embargo re-derived in resampled samples), unvalidated because the module's
    assertions are 15 s-indexed; the mapped geometry is asserted here instead.
    """
    if interval == FIXED_SAMPLE_INTERVAL:
        return split_protocol.deployment_split(values)
    factor = interval // FIXED_SAMPLE_INTERVAL
    anchor = split_protocol.CLARKNET_ANCHOR
    tr = split_protocol.IndexRange(0, windows.fit_end)
    va = split_protocol.IndexRange(windows.val_start, windows.val_end)
    te = split_protocol.IndexRange(windows.test_start, len(values))
    step = interval
    spec = split_protocol.SplitSpec(
        name=f"clarknet-deployment-frozen@{interval}s",
        corpus="clarknet",
        role="deployment",
        eval_of_record="test",
        train=tr,
        validation=va,
        test=te,
        embargo=windows.embargo_used,
        profiles={
            "train": split_protocol.region_profile(anchor, tr.start, tr.stop, step=step),
            "validation": split_protocol.region_profile(anchor, va.start, va.stop, step=step),
            "test": split_protocol.region_profile(anchor, te.start, te.stop, step=step),
        },
        rationale=(
            f"frozen deployment regions mapped by {factor}x ratio to the {interval}s grid; "
            "geometry asserted in gru_probe (module assertions are 15 s-indexed)"
        ),
        used_for_selection=False,
    )
    if (
        windows.val_start - windows.fit_end < windows.embargo_min
        or windows.test_start - windows.val_end < windows.embargo_min
    ):
        raise ValueError(f"mapped deployment geometry violates the embargo: {windows.to_dict()}")
    return spec


def build_nbeats_tower(
    seq_len: int,
    horizon: int,
    hidden: int = 128,
    blocks_per_stack: int = 3,
    trend_degree: int = 3,
):
    """Small doubly-residual N-BEATS tower (Oreshkin et al. 2020, 1905.10437).

    Two stacks: a polynomial-trend stack (degree 3 basis) and a generic stack
    (free theta of full backcast/forecast dimensionality). The paper's
    Fourier/seasonality stack is deliberately omitted: the frozen split has
    zero weekend samples in train+validation and 81.9% weekend in test, so
    any periodic basis would extrapolate a regime the network has never seen.
    """
    import numpy as _np
    import torch
    from torch import nn

    t_back = _np.linspace(-1.0, 1.0, seq_len, dtype=_np.float32)
    t_fore = _np.linspace(-1.0, 1.0, horizon, dtype=_np.float32)
    trend_basis_back = _np.stack([t_back**k for k in range(trend_degree + 1)])
    trend_basis_fore = _np.stack([t_fore**k for k in range(trend_degree + 1)])

    class _Block(nn.Module):
        # Registered buffers are attributes at runtime; the annotations tell the
        # type checker what ``register_buffer`` puts there, which ``nn.Module``
        # alone cannot express.
        basis_back: torch.Tensor
        basis_fore: torch.Tensor

        def __init__(self, theta_dim: int, basis_back: torch.Tensor, basis_fore: torch.Tensor):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(seq_len, hidden),
                nn.ReLU(),
                nn.Linear(hidden, hidden),
                nn.ReLU(),
                nn.Linear(hidden, hidden),
                nn.ReLU(),
                nn.Linear(hidden, hidden),
                nn.ReLU(),
                nn.Linear(hidden, theta_dim),
            )
            self.register_buffer("basis_back", basis_back)
            self.register_buffer("basis_fore", basis_fore)

        def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
            theta = self.net(x)
            dim_back = self.basis_back.shape[0]
            return (
                torch.einsum("bt,td->bd", theta[:, :dim_back], self.basis_back),
                torch.einsum("bt,td->bd", theta[:, dim_back:], self.basis_fore),
            )

    class _Tower(nn.Module):
        def __init__(self):
            super().__init__()
            trend_b = torch.from_numpy(trend_basis_back)
            trend_f = torch.from_numpy(trend_basis_fore)
            eye_b = torch.eye(seq_len)
            eye_f = torch.eye(horizon)
            self.trend_stack = nn.ModuleList(
                [_Block(2 * (trend_degree + 1), trend_b, trend_f) for _ in range(blocks_per_stack)]
            )
            self.generic_stack = nn.ModuleList(
                [_Block(seq_len + horizon, eye_b, eye_f) for _ in range(blocks_per_stack)]
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            if x.dim() == 3:  # (batch, seq, 1) from the shared probe pipeline
                x = x.squeeze(-1)
            forecast = x.new_zeros((x.shape[0], horizon))
            for block in (*self.trend_stack, *self.generic_stack):
                back, fore = block(x)
                x = x - back
                forecast = forecast + fore
            return forecast

    return _Tower()


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
    pos_weight: float | None = None,
    init_state: dict[str, Any] | None = None,
    epoch_callback: Callable[[int, float], None] | None = None,
) -> tuple[Any, int]:
    """Train one seed mirroring the serving trainer: Adam, best-state restore.

    ``init_state`` warm-starts the network from a state_dict of the same
    architecture (cross-corpus pretraining); ``epoch_callback`` observes each
    epoch's validation loss. Both default to off — existing variants are
    byte-identical in behaviour.
    """
    import torch
    from prediction.gru_predictor import GRUNetwork
    from torch import nn
    from torch.utils.data import DataLoader, TensorDataset

    if config.input_size != arrays.X_fit.shape[2]:
        raise ValueError("config input_size does not match built feature count")

    _set_deterministic(seed)
    if arrays.variant == "nbeats":
        model = build_nbeats_tower(arrays.seq_len, arrays.horizon).to(device)
    else:
        model = GRUNetwork(config).to(device)
    if init_state is not None:
        model.load_state_dict(init_state)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    if loss_name == "bce":
        # t_cross: per-step binary crossing labels; pos_weight (neg/pos from
        # the fit region only) offsets class imbalance without touching the
        # validation or test regions.
        criterion = torch.nn.BCEWithLogitsLoss(
            pos_weight=torch.tensor(float(pos_weight), device=device) if pos_weight else None
        )
    else:
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
        if epoch_callback is not None:
            epoch_callback(epoch, val_loss)

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


def predict_val_raw(model: Any, arrays: VariantArrays, device: str) -> np.ndarray:
    """Chunked forward pass on validation inputs, denormalised to RPS."""
    import torch

    X_t = torch.FloatTensor(arrays.X_val).to(device)
    parts = []
    with torch.no_grad():
        for i in range(0, len(X_t), EVAL_CHUNK_SIZE):
            parts.append(model(X_t[i : i + EVAL_CHUNK_SIZE]).cpu().numpy())
    preds_norm = np.concatenate(parts, axis=0)
    return arrays.denormalize_val_predictions(preds_norm)


def _save_artifact(model: Any, config: GRUConfig, arrays: VariantArrays, path: Path) -> str:
    """Persist a probe artifact under the probe output dir (never data/models)."""
    wrapper = GRUPredictor(config=config)
    wrapper.model = model
    wrapper.scaler_mean = arrays.z_mean if arrays.mode == "zscore" else 0.0
    wrapper.scaler_std = arrays.z_std if arrays.mode == "zscore" else 1.0
    wrapper.is_trained = True
    wrapper.target_mode = getattr(arrays, "target_mode", "point")
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


def load_probe_series(sample_interval_sec: int = FIXED_SAMPLE_INTERVAL) -> np.ndarray:
    """ClarkNet series at the replay amplitude, exactly as the study scales it.

    ``sample_interval_sec`` resamples the parquet at the requested bucket
    size (the same loader the study uses, so 30 s / 60 s buckets are
    per-bucket mean RPS over that interval) before the manifest scale factor.
    """
    series = load_clarknet_series(bucket_sec=sample_interval_sec)
    scale = manifest_scale_factor()
    return (series.to_numpy(dtype=np.float32) * scale).astype(np.float32)


def probe_series_index(sample_interval_sec: int = FIXED_SAMPLE_INTERVAL) -> pd.DatetimeIndex:
    """Timestamp index of the resampled series (day-type bucketing only)."""
    return pd.DatetimeIndex(load_clarknet_series(bucket_sec=sample_interval_sec).index)


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
        if variant == "calgary_pretrain":
            from experiment.tuning.calgary_pretrain import dry_run_calgary_pretrain

            return dry_run_calgary_pretrain(epochs, patience)
        if variant == "t_cross":
            from experiment.tuning.t_cross import dry_run_t_cross

            return dry_run_t_cross(epochs, patience)
        if variant in INTERVAL_VARIANTS:
            raise ValueError(
                "dry-run is not supported for resampled variants; the derived splits need the resampled length"
            )
        return _run_dry_run(variant, epochs, patience)

    if output_dir is None:
        raise ValueError("--output-dir is required for probe runs (the probe never writes into results/)")

    if variant == "calgary_pretrain":
        from experiment.tuning.calgary_pretrain import run_calgary_pretrain

        return run_calgary_pretrain(
            seeds=tuple(seeds),
            output_dir=output_dir,
            epochs=epochs,
            patience=patience,
        )

    if variant == "t_cross":
        from experiment.tuning.t_cross import run_t_cross

        return run_t_cross(
            seeds=tuple(seeds),
            output_dir=output_dir,
            epochs=epochs,
            patience=patience,
        )

    interval = INTERVAL_VARIANTS.get(variant, FIXED_SAMPLE_INTERVAL)
    if variant in NEW_WAVE_VARIANTS and interval == FIXED_SAMPLE_INTERVAL:
        values = split_protocol.load_series("clarknet", unit="rps", scale_factor=manifest_scale_factor())
        series_path = (
            "splits.load_series('clarknet', unit='rps', scale_factor=33.0) - canonical "
            "loader, numerically identical to the study's load_clarknet_series path"
        )
    else:
        values = load_probe_series(interval)
        series_path = (
            f"gru_probe.load_probe_series({interval}) - load_clarknet_series(bucket_sec={interval}) "
            "per-bucket mean RPS, then manifest scale factor 33.0 (the canonical loader is "
            "15 s-only; resampling uses the same sum-then-divide parquet path)"
        )
    windows = probe_windows(variant, len(values))
    device = _torch_device()
    season = DEFAULT_SEASON * FIXED_SAMPLE_INTERVAL // interval  # one day, in this interval's samples
    baselines = run_baselines(values, windows, season=season)
    replay = mapped_replay_window(interval) if variant in INTERVAL_VARIANTS else PROBE_REPLAY_WINDOW
    if windows.test_start > replay[0] or replay[1] >= len(values):
        raise ValueError(
            f"replay window {replay} is not strictly inside the test portion "
            f"[{windows.test_start}, {len(values)}) for variant {variant}"
        )

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    bundle = Path(study_bundle) if study_bundle else DEFAULT_STUDY_BUNDLE

    record: dict[str, Any] = {
        "variant": variant,
        "created": datetime.now().isoformat(timespec="seconds"),
        "seeds": list(seeds),
        "device": device,
        "splits": windows.to_dict(),
        "replay_window": list(replay),
        "replay_inside_test": windows.test_start <= replay[0],
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
    if variant in INTERVAL_VARIANTS:
        record["sample_interval_sec"] = interval
        record["horizon_steps"] = windows.horizon
        record["wall_clock_horizon_sec"] = interval * windows.horizon
        record["resample_note"] = (
            f"series resampled to {interval}s buckets by the study loader (per-bucket mean RPS); "
            f"splits re-derived proportionally from the frozen fractions with embargo "
            f"{windows.embargo_used} = seq_len {windows.seq_len} + horizon {windows.horizon} - 1; "
            f"wall-clock horizon held at the 135s target -> {windows.horizon} steps = "
            f"{interval * windows.horizon}s realised; replay window mapped to {replay}"
        )
    if variant in NEW_WAVE_VARIANTS:
        record["sample_interval_sec"] = interval
        record["horizon_steps"] = windows.horizon
        record["screen_region"] = "selection_folds_b2_b3_b4"
        record["test_used_for_selection"] = False
        record["mase_season_samples"] = season
        record["splits_module"] = splits_module_fingerprint()
        record["series_construction"] = {
            "path": series_path,
            "units": "RPS at replay amplitude (raw per-bucket mean RPS * 33.0)",
            "protocol_units_note": (
                "splits.py references are counts per 15 s bucket on the raw trace; "
                "this harness measures RPS at the served amplitude (counts / 15 * 33.0)"
            ),
        }
        record["metric_units"] = "RPS at replay amplitude (divide by 33.0 for raw RPS)"

    if variant == "t_cross":
        cap_block = probe_capacity()
        cap = float(cap_block["capacity_rps"])
        record["capacity"] = cap_block
        record["screen_region"] = "validation"
        record["test_used_for_selection"] = False
        record["label_definition"] = {
            "target": "per-step binary crossing label; first-crossing time derived at scoring",
            "threshold_rule": "raw RPS >= capacity_rps (inclusive)",
            "capacity_rps": cap,
            "step_sec": FIXED_SAMPLE_INTERVAL,
            "horizon_steps": windows.horizon,
        }
        record["label_distribution"] = crossing_label_distribution(values, windows, cap)

    if variant == "ensemble":
        ens = run_ensemble(values, windows, tuple(seeds), out, bundle, baselines)
        record.update(ens)
        record["epochs_trained_per_seed"] = None
        metric_block = ens.get("metrics")
        aggregate = None
    else:
        arrays = build_variant_arrays(
            variant,
            values,
            windows,
            capacity=cap if variant == "t_cross" else None,
            canonical_spec=deployment_arm_spec(values, interval, windows) if variant in CANONICAL_VARIANTS else None,
        )
        config = probe_config(variant, windows, epochs, patience)
        if variant == "pinball":
            loss_name = "pinball"
        elif variant == "t_cross":
            loss_name = "bce"
        else:
            loss_name = "mse"
        record["loss"] = loss_name
        feature_labels = {
            "zscore": "value_z",
            "canonical": "value_canonical_log1p_robust",
            "revin": "value_revin",
            "revin_robust": "value_revin_robust",
            "robust": "value_robust_global",
            "quantile": "value_quantile_gauss",
            "nlinear": "value_nlinear_anchor",
            "diff": "value_diff_z",
        }
        feature_label = feature_labels[arrays.mode]
        if variant == "calendar":
            record["input_features"] = [feature_label, "sin_tod", "cos_tod"]
        elif variant in FEATURE_VARIANTS:
            _, chan_names = _trailing_feature_channels(variant, values.astype(np.float64))
            record["input_features"] = [feature_label, *chan_names]
        else:
            record["input_features"] = [feature_label]
        record["normalization"] = arrays.mode + ("+log1p" if arrays.log_space else "")
        if variant == "nbeats":
            record["architecture_note"] = (
                "N-BEATS tower: polynomial-trend stack (degree 3) + generic stack, "
                "3 blocks each, hidden 128; the Fourier/seasonality stack is omitted because "
                "the split contains zero weekend samples in train+validation"
            )

        ols_test_preds = baselines["_arrays"]["ols_preds"]
        if variant in NEW_WAVE_VARIANTS:
            series_index = probe_series_index(interval)
            base_test = np.arange(arrays.X_test.shape[0], dtype=np.int64) + windows.test_start
            day_labels = day_type_labels(series_index[base_test])
        else:
            day_labels = None

        pos_weight = None
        ols_cross: dict[str, Any] | None = None
        if variant == "t_cross":
            pos_count = float(arrays.y_fit.sum())
            neg_count = float(arrays.y_fit.size) - pos_count
            pos_weight = neg_count / pos_count if pos_count > 0 else None
            record["bce_pos_weight"] = {"value": pos_weight, "derived_from": "fit-region labels only"}
            ols_cross = score_crossing_predictions((ols_test_preds >= cap).astype(float), arrays.y_test_raw, cap)
            record["ols_crossing_arm"] = ols_cross

        per_seed: dict[str, Any] = {}
        seed_rmses: list[float] = []
        epochs_per_seed: dict[str, int] = {}
        artifacts: list[dict[str, Any]] = []
        for seed in seeds:
            model, epochs_trained = train_probe_model(arrays, config, seed, loss_name, device, pos_weight=pos_weight)
            preds = predict_raw(model, arrays, device)
            if variant == "t_cross":
                # Set in the t_cross branch above; the two conditions are the
                # same test, so this only makes the invariant explicit.
                assert ols_cross is not None
                block = score_crossing_predictions(preds, arrays.y_test_raw, cap)
                if ols_cross["brier_per_step"] > 0:
                    block["skill_vs_ols_brier"] = 1.0 - block["brier_per_step"] / ols_cross["brier_per_step"]
                else:
                    block["skill_vs_ols_brier"] = 0.0
                val_probs = predict_val_raw(model, arrays, device)
                block["screening"] = screen_t_cross_on_validation(values, windows, arrays, val_probs, cap)
                per_seed[str(seed)] = block
                seed_rmses.append(block["brier_per_step"])
                epochs_per_seed[str(seed)] = epochs_trained
                artifact_path = out / "artifacts" / f"{variant}_s{seed}.pt"
                artifacts.append(
                    {
                        "path": str(artifact_path),
                        "seed": seed,
                        "sha256": _save_artifact(model, config, arrays, artifact_path),
                    }
                )
                continue
            block = _with_skills(
                score_predictions(preds, arrays.y_test_raw, arrays.last_test_raw),
                baselines["persistence"],
                baselines["ols"],
            )
            block["mase"] = mase_against_seasonal_naive(block, baselines["seasonal_naive"])
            block["mase_season_samples"] = int(season)
            block["dm_vs_ols"] = diebold_mariano(
                arrays.y_test_raw - preds, arrays.y_test_raw - ols_test_preds, windows.horizon
            )
            if variant in NEW_WAVE_VARIANTS:
                # Set alongside the same variant test above.
                assert day_labels is not None
                block["by_day_type"] = split_metrics_by_day_type(preds, ols_test_preds, arrays.y_test_raw, day_labels)
            per_seed[str(seed)] = block
            seed_rmses.append(block["rmse"])
            epochs_per_seed[str(seed)] = epochs_trained
            if variant == "nbeats":
                artifacts.append({"seed": seed, "note": "artifact not saved: N-BEATS tower is not serving-compatible"})
            else:
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
        record["serving_compatible"] = variant in ("baseline", "t_cross")
        if variant == "t_cross":
            first_block = next(iter(per_seed.values()))
            aggregate = None
            record["aggregate_t_cross"] = {
                "brier_mean": float(np.mean(seed_rmses)),
                "brier_std": float(np.std(seed_rmses, ddof=1)) if len(seed_rmses) > 1 else 0.0,
                "t_cross_mae_mean": float(np.mean([b["t_cross_mae_steps"] for b in per_seed.values()])),
                "crossing_recall_mean": float(np.mean([b["crossing_recall"] for b in per_seed.values()])),
                "skill_vs_ols_brier_mean": float(np.mean([b["skill_vs_ols_brier"] for b in per_seed.values()])),
                "val_brier": float(first_block["screening"]["variant"]["brier_per_step"]),
                "val_ols_brier": float(first_block["screening"]["ols"]["brier_per_step"]),
                "beats_ols_on_validation_brier": bool(first_block["screening"]["beats_ols"]),
            }
            record["note"] = "t_cross: capacity-relative metrics in aggregate_t_cross; rmse columns n/a"
            if len(seed_rmses) > 1:
                assert ols_cross is not None
                ref_brier = ols_cross["brier_per_step"]
                record["paired_test_vs_ols"] = {
                    "p_value": paired_permutation_test([ref_brier] * len(seed_rmses), seed_rmses),
                    "cohens_d_paired": cohens_d_paired([ref_brier] * len(seed_rmses), seed_rmses),
                    "note": "one-sided: variant seed Brier below OLS+threshold Brier",
                }
        else:
            aggregate = {
                "rmse_mean": float(np.mean(seed_rmses)),
                "rmse_std": float(np.std(seed_rmses, ddof=1)) if len(seed_rmses) > 1 else 0.0,
                "mae_mean": float(np.mean([b["mae"] for b in per_seed.values()])),
                "rmse_pct_mean": float(np.mean([b["rmse_pct_of_mean_target"] for b in per_seed.values()])),
                "skill_vs_persistence_mean": float(np.mean([b["skill_vs_persistence"] for b in per_seed.values()])),
                "skill_vs_ols_mean": float(np.mean([b["skill_vs_ols"] for b in per_seed.values()])),
            }
            if variant in NEW_WAVE_VARIANTS:
                record["screening"] = screen_variant_on_folds(
                    variant, values, interval, season, epochs, patience, device, seed=seeds[0]
                )
                record["fold_wiring_check"] = persistence_wiring_check(values, interval, season)
                first_block = next(iter(per_seed.values()))
                aggregate["mase_mean"] = float(first_block["mase"])
                fold_agg = record["screening"]["aggregate"]
                aggregate["selection_fold_rmse_mean"] = float(fold_agg["variant_rmse"]["mean"])
                aggregate["selection_fold_rmse_std"] = float(fold_agg["variant_rmse"]["std"])
                aggregate["selection_fold_ols_rmse_mean"] = float(fold_agg["ols_rmse"]["mean"])
                aggregate["beats_ols_on_selection_folds"] = bool(record["screening"]["beats_ols"])
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
        dm_p: Any = "n/a"
        if not paired:
            per_seed = record.get("per_seed") or {}
            for block in per_seed.values():
                dm = block.get("dm_vs_ols") if isinstance(block, dict) else None
                if dm:
                    dm_p = round(dm["p_value_one_sided"], 4)
                    break
        return {
            "variant": variant,
            "seeds": ",".join(str(s) for s in seeds),
            "rmse_mean": round(aggregate["rmse_mean"], 4),
            "rmse_std": round(aggregate["rmse_std"], 4),
            "mae": round(aggregate["mae_mean"], 4),
            "rmse_pct_mean": round(aggregate["rmse_pct_mean"], 4),
            "skill_vs_persistence": round(aggregate["skill_vs_persistence_mean"], 4),
            "skill_vs_ols": round(aggregate["skill_vs_ols_mean"], 4),
            "p_paired_vs_ols": round(paired["p_value"], 4) if paired else dm_p,
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
