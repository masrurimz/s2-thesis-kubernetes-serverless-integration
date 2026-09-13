"""Cross-corpus pretraining lever: pretrain on Calgary, fine-tune on ClarkNet.

Motivation (measured regime problem): the ClarkNet training regions have 0%
weekend while the deployment test region is 81.9% weekend, so day-type
structure cannot be learned from ClarkNet alone. Calgary spans 352 days (44
full weekends in its pretraining region, weekend share ~28%) and is the only
available corpus long enough to contain weekends.

Split protocol: everything comes from ``experiment.tuning.splits`` — the
frozen-protocol module owns the boundaries, the assertions, and the
normalizers. This module never computes a split or a normalization statistic
of its own.

- Stage A — pretrain on the Calgary ``calgary_pretrain_split`` training
  region only, early-stop on its pure Sat+Sun validation block. The
  post-cut Calgary tail (which temporally overlaps the ClarkNet week plus a
  4 h guard band) is never read.
- Stage B — fine-tune on each ClarkNet evaluation spec's training region:
  blocked-CV selection folds b2/b3/b4 (screening), OOD fold b5 (reported
  separately, never in the selection aggregate), and the frozen deployment
  split (replay window inside test, reported separately). Early stopping
  uses an internal carve from the tail of each spec's own training region —
  never the eval block, never the deployment test region.
- Amplitude: ClarkNet counts per 15 s bucket drive the CV arms (matching the
  splits-module reference numbers); the deployment arm uses the raw trace
  multiplied by the manifest ``scale_factor`` (33.0) for both the series and
  the normalizer fit, so the fitted statistics match what serving sees.
  Calgary is used raw (counts, no amplification). Per-corpus/per-arm
  normalizers are fitted through ``normalizer_stats`` on the training region
  only; the amplitude mismatch is absorbed by normalisation and never leaks
  across corpora.
- Near-zero handling: Calgary has a complete 15 s grid (no missing buckets
  over 352 days); 84-85% of buckets are genuine zero-request buckets. They
  are kept as 0 counts — no interpolation, no dropping. After log1p the IQR
  is zero, so the mandated std fallback engages (recorded in the stats).
- Units: CV-arm and Calgary numbers are in counts per 15 s bucket; the
  deployment arm is in amplified RPS (counts/15 × 33). Every metric states
  its fold and unit.

Pre-registered prior (from EDA, recorded before any run): Calgary's
autocorrelation collapses almost immediately (lag-1 0.355, lag-120 0.070,
lag-480 0.053, weekly 0.051 vs ClarkNet 0.731/0.544/0.481/0.455) and it is
~6x more variable — close to white noise at these lags. The lever's value is
day-type coverage, not dynamics transfer. If the pretrained model gains
nothing on the selection-fold gate, that is the expected outcome and a
reportable finding. Each seed's per-epoch stage-A validation loss is
recorded so the pretraining stage's own learnability is visible.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import structlog
from experiment.tuning.gru_hpo import (
    EVAL_CHUNK_SIZE,
    _make_sequences,
)
from experiment.tuning.gru_study import manifest_scale_factor
from experiment.tuning.splits import (
    CALGARY_ANCHOR,
    CALGARY_N,
    CLARKNET_ANCHOR,
    DAY,
    EMBARGO,
    HORIZON,
    REPLAY_WINDOW,
    SEQUENCE_LENGTH,
    NormalizerStats,
    SplitSpec,
    aggregate_block_metrics,
    apply_normalizer,
    blocked_cv,
    calgary_pretrain_split,
    deployment_split,
    invert_normalizer,
    load_series,
    normalizer_stats,
)

logger = structlog.get_logger(__name__)

# Protocol pin: the frozen split geometry this module is wired against. The
# runtime hash is verified against this value and recorded in every output.
SPLITS_SHA256 = "5f937edb361fbcea1a49334d92d768d409eefd1b12c563c5e708b9a1919631e3"


def splits_protocol_pin() -> dict[str, Any]:
    """sha256 of splits.py plus the series-construction provenance for records."""
    import hashlib

    path = Path(__file__).resolve().parent / "splits.py"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "splits_py_sha256": digest,
        "splits_py_sha256_expected": SPLITS_SHA256,
        "matches_pinned_revision": digest == SPLITS_SHA256,
        "series_construction": {
            "loader": "experiment.tuning.splits.load_series (canonical; asserts corpus/unit/frozen length)",
            "calgary": "load_series('calgary', 'counts') - raw counts per 15 s bucket",
            "clarknet_cv": "load_series('clarknet', 'counts') - counts per 15 s bucket (splits reference units)",
            "clarknet_deployment": "load_series('clarknet', 'rps', scale_factor=33.0) - served amplitude; "
            "scale applied after unit conversion",
            "unit_note": "split-module references are counts/15s; divide by 15 for RPS; the deployment arm "
            "is 33x the rps series",
        },
    }


PRETRAIN_WINDOW_STRIDE = 12  # one window per 3 min; ~146k fit / ~1k val windows
PRETRAIN_VAL_WINDOW_STRIDE = 12
INTERNAL_VAL_FRACTION = 0.2  # early-stop carve from the tail of each training region
INTERNAL_VAL_MAX = DAY  # at most one day

_EPS = 1e-8

# Pre-registered prior, echoed into every record and dry-run report.
PRIOR_NOTE = (
    "Calgary autocorrelation is near white noise beyond one step "
    "(lag-1 0.355, lag-120 0.070, lag-480 0.053, weekly 0.051 vs ClarkNet "
    "0.731/0.544/0.481/0.455) with ~6x the coefficient of variation. Expected "
    "outcome: no gain on the selection-fold gate; a null result is a reportable "
    "finding, not a failure. Per-epoch stage-A validation loss is recorded."
)

# Parent-provided fold-wiring references (counts/15 s, horizon 9) used only by
# the dry run to prove this harness wires the folds identically.
REFERENCE_PERSISTENCE_SELECTION = (22.572, 0.124)
REFERENCE_PERSISTENCE_OOD_B5 = 16.564
REFERENCE_PERSISTENCE_DEPLOYMENT = 18.060
REFERENCE_TOLERANCE = 0.30


# ── Series loaders (unit-explicit; splits owns the grid) ─────────────────────


def calgary_counts() -> np.ndarray:
    """Calgary 15 s counts, raw amplitude (no amplification exists for it)."""
    return load_series("calgary", unit="counts")


def clarknet_counts() -> np.ndarray:
    """ClarkNet 15 s counts — CV arms (b2-b5) train/screen/score on these."""
    return load_series("clarknet", unit="counts")


def clarknet_deployment_series() -> np.ndarray:
    """ClarkNet RPS × manifest scale factor — the deployment arm's served amplitude.

    ``unit='rps'`` (counts/15) is numerically identical to the study's
    ``load_clarknet_series``; the scale factor is applied after unit
    conversion, so this is the amplified series serving sees. It feeds
    ``deployment_split`` and ``normalizer_stats``; the split geometry is
    unaffected by the amplification.
    """
    return load_series("clarknet", unit="rps", scale_factor=manifest_scale_factor())


def calgary_sparsity_stats(values: np.ndarray, spec: SplitSpec) -> dict[str, Any]:
    """Bucket-count and sparsity statistics for the record (counts units)."""
    train = values[spec.require_region("train").start : spec.require_region("train").stop]
    zeros = values == 0
    return {
        "buckets_total": int(len(values)),
        "unit": "counts per 15 s bucket",
        "span_days": round(len(values) * 15 / 86400, 3),
        "missing_buckets": 0,  # complete grid: length equals the frozen corpus size
        "zero_buckets": int(zeros.sum()),
        "zero_share": round(float(zeros.mean()), 6),
        "zero_share_train_portion": round(float((train == 0).mean()), 6),
        "near_zero_lt_1_count_share": round(float((values < 1.0).mean()), 6),
        "mean_counts": round(float(values.mean()), 6),
        "std_counts": round(float(values.std()), 6),
        "mean_counts_train_portion": round(float(train.mean()), 6),
        "std_counts_train_portion": round(float(train.std()), 6),
        "min_counts": float(values.min()),
        "max_counts": float(values.max()),
        "coefficient_of_variation": round(float(values.std() / (values.mean() + _EPS)), 4),
        "weekend_share_train": round(spec.profiles["train"].weekend_share, 6),
        "near_zero_handling": (
            "zero buckets kept as 0 counts (genuine empty buckets, complete grid); "
            "no interpolation, no dropping; log1p+median/IQR with the std fallback "
            "(IQR is zero at 84% zeros) normalises them"
        ),
    }


# ── Stage A: strided Calgary windows ─────────────────────────────────────────


@dataclass(frozen=True)
class StridedWindows:
    """Windows for one Calgary region plus the global indices they consume."""

    X: np.ndarray  # (n, seq_len) normalised
    y: np.ndarray  # (n, horizon) normalised
    n_windows: int
    stride: int
    max_index_consumed: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_windows": self.n_windows,
            "stride": self.stride,
            "max_index_consumed": self.max_index_consumed,
        }


def _strided_sequences(
    seg: np.ndarray,
    seq_len: int,
    horizon: int,
    stride: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Windows at bases ``0, stride, 2*stride, ...`` inside one region.

    Window ``i`` consumes indices ``i*stride .. i*stride + seq_len + horizon - 1``
    of the segment, all inside it by construction.
    """
    if stride < 1:
        raise ValueError(f"stride must be >= 1, got {stride}")
    n_strided = (len(seg) - seq_len - horizon) // stride + 1
    if n_strided <= 0:
        raise ValueError(f"region too small for seq={seq_len}, horizon={horizon}, stride={stride}")
    bases = np.arange(n_strided, dtype=np.int64) * stride
    idx_X = bases[:, None] + np.arange(seq_len)[None, :]
    idx_y = bases[:, None] + np.arange(seq_len, seq_len + horizon)[None, :]
    return seg[idx_X], seg[idx_y]


def build_stage_a_arrays(
    values: np.ndarray,
    spec: SplitSpec,
    fit_stride: int = PRETRAIN_WINDOW_STRIDE,
    val_stride: int = PRETRAIN_VAL_WINDOW_STRIDE,
) -> tuple[StridedWindows, StridedWindows, NormalizerStats]:
    """Stage-A windows, normalised through ``normalizer_stats`` (train region only)."""
    train_rng = spec.train
    val_rng = spec.validation
    assert train_rng is not None and val_rng is not None, f"{spec.name}: missing train/validation"
    stats = normalizer_stats(values, spec)  # fits on spec.train, refuses anything else

    X_fit, y_fit = _strided_sequences(
        apply_normalizer(values[train_rng.start : train_rng.stop], stats),
        SEQUENCE_LENGTH,
        HORIZON,
        fit_stride,
    )
    X_val, y_val = _strided_sequences(
        apply_normalizer(values[val_rng.start : val_rng.stop], stats),
        SEQUENCE_LENGTH,
        HORIZON,
        val_stride,
    )
    # train_probe_model expects (n, seq_len, features); the univariate stage-A
    # windows arrive as (n, seq_len) and need the trailing channel axis.
    X_fit = X_fit[..., None]
    X_val = X_val[..., None]
    fit_windows = StridedWindows(
        X=X_fit.astype(np.float32),
        y=y_fit.astype(np.float32),
        n_windows=len(X_fit),
        stride=fit_stride,
        max_index_consumed=train_rng.stop - 1,
    )
    val_windows = StridedWindows(
        X=X_val.astype(np.float32),
        y=y_val.astype(np.float32),
        n_windows=len(X_val),
        stride=val_stride,
        max_index_consumed=val_rng.stop - 1,
    )
    _assert_stage_a_isolation(spec, fit_windows, val_windows)
    return fit_windows, val_windows, stats


def _assert_stage_a_isolation(spec: SplitSpec, fit: StridedWindows, val: StridedWindows) -> None:
    """Stage-A windows stop inside the sanctioned regions; the cut tail is never read."""
    assert spec.train is not None and spec.validation is not None
    if fit.max_index_consumed != spec.require_region("train").stop - 1:
        raise ValueError("stage-A fit windows do not end exactly at calgary train_stop - 1")
    if val.max_index_consumed != spec.require_region("validation").stop - 1:
        raise ValueError("stage-A val windows do not end exactly at calgary validation_stop - 1")
    cut_tail_start = spec.require_region("validation").stop  # everything at/after the cut is unused
    for name, consumed in (("fit", fit.max_index_consumed), ("val", val.max_index_consumed)):
        if consumed >= cut_tail_start:
            raise ValueError(
                f"stage-A {name} window reads index {consumed} >= calgary cut {cut_tail_start} "
                "(post-cut tail overlaps the ClarkNet week; forbidden)"
            )


# ── Stage B: per-spec ClarkNet windows with an internal early-stop carve ─────


@dataclass(frozen=True)
class SpecWindows:
    """Normalised fit/internal-val windows and raw-scale eval windows for one spec."""

    X_fit: np.ndarray
    y_fit: np.ndarray
    X_ival: np.ndarray
    y_ival: np.ndarray
    X_eval: np.ndarray  # normalised inputs of the eval block
    y_eval_raw: np.ndarray  # (n, horizon) original series scale
    last_eval_raw: np.ndarray  # (n,) original series scale
    stats: NormalizerStats
    # Region ranges only, each a half-open [start, stop) pair. The embargo is a
    # module constant and is recorded at the record's top level, so it is not
    # duplicated here — mixing a scalar into this mapping is what made every
    # subscript look like it might be an int.
    carve: dict[str, list[int]]
    n_eval_windows: int


def _internal_carve(train_stop: int) -> tuple[tuple[int, int], tuple[int, int]]:
    """Split a training region [0, train_stop) into (fit, internal_val) with embargo."""
    val_len = min(int(train_stop * INTERNAL_VAL_FRACTION), INTERNAL_VAL_MAX)
    fit_stop = train_stop - val_len - EMBARGO
    if fit_stop <= SEQUENCE_LENGTH + HORIZON:
        raise ValueError(f"training region [0, {train_stop}) too small for an internal carve")
    return (0, fit_stop), (fit_stop + EMBARGO, train_stop)


def build_spec_windows(series: np.ndarray, spec: SplitSpec) -> SpecWindows:
    """Windows for one ClarkNet spec; every region honouring the embargo."""
    train = spec.train
    eval_rng = spec.region(spec.eval_of_record)
    assert train is not None and eval_rng is not None, f"{spec.name}: missing regions"
    stats = normalizer_stats(series, spec)  # fits on the spec's train region only

    (fit_start, fit_stop), (ival_start, ival_stop) = _internal_carve(train.stop)
    X_fit, y_fit, _ = _make_sequences(apply_normalizer(series[fit_start:fit_stop], stats), SEQUENCE_LENGTH, HORIZON)
    X_ival, y_ival, _ = _make_sequences(apply_normalizer(series[ival_start:ival_stop], stats), SEQUENCE_LENGTH, HORIZON)
    X_eval_norm, _, _ = _make_sequences(
        apply_normalizer(series[eval_rng.start : eval_rng.stop], stats), SEQUENCE_LENGTH, HORIZON
    )
    _, y_eval_raw, last_eval_raw = _make_sequences(
        series[eval_rng.start : eval_rng.stop].astype(np.float64), SEQUENCE_LENGTH, HORIZON
    )
    if fit_stop - EMBARGO >= ival_start or ival_stop > eval_rng.start:
        raise ValueError(f"{spec.name}: internal carve violates ordering/embargo")
    return SpecWindows(
        X_fit=X_fit[:, :, None].astype(np.float32),
        y_fit=y_fit.astype(np.float32),
        X_ival=X_ival[:, :, None].astype(np.float32),
        y_ival=y_ival.astype(np.float32),
        X_eval=X_eval_norm[:, :, None].astype(np.float32),
        y_eval_raw=y_eval_raw,
        last_eval_raw=last_eval_raw,
        stats=stats,
        carve={
            "fit": [fit_start, fit_stop],
            "internal_val": [ival_start, ival_stop],
            "train_region": [train.start, train.stop],
            "eval_region": [eval_rng.start, eval_rng.stop],
        },
        n_eval_windows=len(y_eval_raw),
    )


# ── Baselines on identical folds (linear only; no network) ───────────────────


def persistence_rmse_scalar(values: np.ndarray, start: int, stop: int, horizon: int = HORIZON) -> float:
    """splits-module persistence wiring, mirrored for the record."""
    target = values[start + horizon : stop]
    pred = values[start : stop - horizon]
    return float(np.sqrt(np.mean((pred - target) ** 2)))


def ols_autoreg_fold(values: np.ndarray, windows: SpecWindows) -> dict[str, Any]:
    """OLS AR(seq_len)→horizon refit on the fold's training region, scored on its eval."""
    train = windows.carve["train_region"]
    X_tr, y_tr, _ = _make_sequences(values[train[0] : train[1]].astype(np.float64), SEQUENCE_LENGTH, HORIZON)
    design = np.hstack([np.ones((len(X_tr), 1)), X_tr])
    coef, *_ = np.linalg.lstsq(design, y_tr, rcond=None)
    # Eval inputs in the original series scale, rebuilt from the raw eval block
    # (identical windows to the network arm — same origins, same targets).
    eval_rng = windows.carve["eval_region"]
    X_eval_raw, _, _ = _make_sequences(values[eval_rng[0] : eval_rng[1]].astype(np.float64), SEQUENCE_LENGTH, HORIZON)
    design_ev = np.hstack([np.ones((len(X_eval_raw), 1)), X_eval_raw])
    preds = design_ev @ coef
    return {"coef_shape": list(coef.shape), "train_windows": int(len(X_tr)), "preds": preds}


def spec_day_type_block(spec: SplitSpec) -> dict[str, Any]:
    """Day-type coverage of one spec's eval block, attached to every metric."""
    eval_rng = spec.region(spec.eval_of_record)
    assert eval_rng is not None
    prof = spec.profiles[spec.eval_of_record]
    return {
        "fold": spec.name,
        "role": spec.role,
        "used_for_selection": spec.used_for_selection,
        "eval_region": [eval_rng.start, eval_rng.stop],
        "eval_span_utc": [str(x) for x in eval_rng.span(CLARKNET_ANCHOR)],
        "eval_weekend_share": round(prof.weekend_share, 4),
        "eval_day_types": sorted(prof.days),
    }


# ── Two-stage training path ──────────────────────────────────────────────────


def _train_one(
    X_fit: np.ndarray,
    y_fit: np.ndarray,
    X_ival: np.ndarray,
    y_ival: np.ndarray,
    config: Any,
    seed: int,
    device: str,
    init_state: dict[str, Any] | None,
    epoch_callback: Any,
) -> tuple[Any, int]:
    from experiment.tuning.gru_probe import VariantArrays, train_probe_model

    arrays = VariantArrays(
        variant="calgary_pretrain",
        mode="zscore",  # label only: the robust transform lives in the windows/stats
        log_space=False,
        seq_len=SEQUENCE_LENGTH,
        horizon=HORIZON,
        X_fit=X_fit,
        y_fit=y_fit,
        X_val=X_ival,
        y_val=y_ival,
        X_test=np.empty((0, SEQUENCE_LENGTH, 1), dtype=np.float32),
        y_test_raw=np.empty((0, HORIZON)),
        last_test_raw=np.empty(0),
    )
    return train_probe_model(arrays, config, seed, "mse", device, init_state=init_state, epoch_callback=epoch_callback)


def _predict_raw(model: Any, windows: SpecWindows, stats: NormalizerStats, device: str) -> np.ndarray:
    import torch

    X_t = torch.FloatTensor(windows.X_eval).to(device)
    parts = []
    with torch.no_grad():
        for i in range(0, len(X_t), EVAL_CHUNK_SIZE):
            parts.append(model(X_t[i : i + EVAL_CHUNK_SIZE]).cpu().numpy())
    return invert_normalizer(np.concatenate(parts, axis=0), stats)


def _artifact_hash(model: Any, config: Any, path: Path) -> str:
    import hashlib

    from prediction.gru_predictor import GRUPredictor

    wrapper = GRUPredictor(config=config)
    wrapper.model = model
    wrapper.is_trained = True
    path.parent.mkdir(parents=True, exist_ok=True)
    wrapper.save_model(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _evaluation_specs() -> tuple[list[tuple[SplitSpec, np.ndarray, str]], dict[str, Any]]:
    """(spec, series, unit) triples for b2-b5 + deployment, plus skipped records."""
    ck = clarknet_counts()
    plan = blocked_cv(ck)
    amp = clarknet_deployment_series()
    dep = deployment_split(amp)
    triples = [(s, ck, "counts/15s") for s in plan.specs]
    triples.append((dep, amp, f"counts/15s x {manifest_scale_factor()} (amplified RPS)"))
    return triples, {"skipped": [dict(s) for s in plan.skipped]}


def run_calgary_pretrain(
    seeds: tuple[int, ...] = (42, 43, 44),
    output_dir: str | Path | None = None,
    epochs: int = 200,
    patience: int = 25,
    fit_stride: int = PRETRAIN_WINDOW_STRIDE,
    val_stride: int = PRETRAIN_VAL_WINDOW_STRIDE,
) -> dict[str, Any]:
    """Run both stages under the splits-module protocol; test regions never selected on."""
    from experiment.tuning.gru_hpo import FIXED_BATCH_SIZE
    from experiment.tuning.gru_probe import _torch_device, score_predictions
    from prediction.gru_predictor import GRUConfig

    if output_dir is None:
        raise ValueError(
            "--output-dir is required; use a date-stamped bundle under the governed tree, "
            "e.g. results/models/gru/2026-09-13_probe-calgary-pretrain/"
        )
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    device = _torch_device()

    calgary = calgary_counts()
    cal_spec = calgary_pretrain_split(calgary)
    cal_stats = calgary_sparsity_stats(calgary, cal_spec)
    fit_windows, val_windows, cal_norm = build_stage_a_arrays(calgary, cal_spec, fit_stride, val_stride)

    triples, skipped = _evaluation_specs()
    spec_windows = {s.name: build_spec_windows(series, s) for s, series, _ in triples}

    config = GRUConfig(
        input_size=1,
        cell="gru",
        hidden_size=128,
        num_layers=1,
        sequence_length=SEQUENCE_LENGTH,
        prediction_horizon=HORIZON,
        epochs=epochs,
        early_stopping_patience=patience,
        batch_size=FIXED_BATCH_SIZE,
    )

    record: dict[str, Any] = {
        "variant": "calgary_pretrain",
        "created": datetime.now().isoformat(timespec="seconds"),
        "seeds": list(seeds),
        "device": device,
        "prior": PRIOR_NOTE,
        "screen_region": "blocked_cv_selection_folds",
        "test_used_for_selection": False,
        "protocol": "experiment.tuning.splits (frozen); no local split or normalizer math",
        "protocol_pin": splits_protocol_pin(),
        "calgary_spec": {
            "name": cal_spec.name,
            "train": [cal_spec.require_region("train").start, cal_spec.require_region("train").stop],
            "validation": [cal_spec.require_region("validation").start, cal_spec.require_region("validation").stop],
            "train_span_utc": [str(x) for x in cal_spec.require_region("train").span(CALGARY_ANCHOR)],
            "validation_span_utc": [str(x) for x in cal_spec.require_region("validation").span(CALGARY_ANCHOR)],
            "post_cut_unused_from": cal_spec.require_region("validation").stop,
            "embargo": cal_spec.embargo,
        },
        "calgary_stats": cal_stats,
        "stage_a": {
            "fit": fit_windows.to_dict(),
            "val": val_windows.to_dict(),
            "normalizer": {
                "method": cal_norm.method,
                "center": cal_norm.center,
                "scale": cal_norm.scale,
                "fit_range": [cal_norm.fit_range.start, cal_norm.fit_range.stop],
            },
            "epoch_budget": epochs,
            "patience": patience,
            "levers": "cross-corpus pretraining only; architecture and protocol identical",
        },
        "amplitude_handling": {
            "calgary": "raw counts/15s, no amplification",
            "clarknet_cv_folds": "counts/15s (splits-module reference units)",
            "clarknet_deployment": "load_series('clarknet','rps') x manifest scale_factor 33.0 (unit chain: counts/15s -> /15 RPS -> x33 served)",
            "reconciliation": "per-arm normalizer_stats fits on the training region only",
        },
        "epoch_budgets": {"stage_a_pretrain": epochs, "stage_b_finetune": epochs},
        "skipped_blocks": skipped["skipped"],
    }

    per_seed: dict[str, Any] = {}
    artifacts: list[dict[str, Any]] = []
    for seed in seeds:
        stage_a_losses: list[float] = []

        def on_stage_a_epoch(_epoch: int, val_loss: float) -> None:
            stage_a_losses.append(val_loss)

        pre_model, pre_epochs = _train_one(
            fit_windows.X,
            fit_windows.y,
            val_windows.X,
            val_windows.y,
            config,
            seed,
            device,
            init_state=None,
            epoch_callback=on_stage_a_epoch,
        )
        stage_a_path = out / "artifacts" / f"calgary_pretrain_stage_a_s{seed}.pt"
        artifacts.append(
            {
                "stage": "a_pretrain",
                "seed": seed,
                "path": str(stage_a_path),
                "sha256": _artifact_hash(pre_model, config, stage_a_path),
            }
        )

        seed_block: dict[str, Any] = {
            "stage_a_epochs_trained": pre_epochs,
            "stage_a_val_loss_per_epoch": [round(v, 6) for v in stage_a_losses],
            "folds": {},
        }
        for spec, series, unit in triples:
            windows = spec_windows[spec.name]
            stage_b_losses: list[float] = []

            def on_stage_b_epoch(_epoch: int, val_loss: float) -> None:
                stage_b_losses.append(val_loss)

            model, fin_epochs = _train_one(
                windows.X_fit,
                windows.y_fit,
                windows.X_ival,
                windows.y_ival,
                config,
                seed,
                device,
                init_state=pre_model.state_dict(),
                epoch_callback=on_stage_b_epoch,
            )
            preds = _predict_raw(model, windows, windows.stats, device)
            net_block = score_predictions(preds, windows.y_eval_raw, windows.last_eval_raw)
            ols = ols_autoreg_fold(series, windows)
            ols_block = score_predictions(ols["preds"], windows.y_eval_raw, windows.last_eval_raw)
            pers_rmse = persistence_rmse_scalar(
                series, windows.carve["eval_region"][0], windows.carve["eval_region"][1]
            )
            seed_block["folds"][spec.name] = {
                "unit": unit,
                "epochs_trained": fin_epochs,
                "stage_b_val_loss_per_epoch": [round(v, 6) for v in stage_b_losses],
                "carve": windows.carve,
                "n_eval_windows": windows.n_eval_windows,
                **spec_day_type_block(spec),
                "network": net_block,
                "ols_gate": ols_block,
                "persistence_rmse": pers_rmse,
                "skill_vs_ols": 1.0 - net_block["rmse"] / ols_block["rmse"] if ols_block["rmse"] > 0 else 0.0,
            }
            fold_path = out / "artifacts" / f"calgary_pretrain_{spec.name}_s{seed}.pt"
            artifacts.append(
                {
                    "stage": "b_finetune",
                    "fold": spec.name,
                    "seed": seed,
                    "path": str(fold_path),
                    "sha256": _artifact_hash(model, config, fold_path),
                }
            )
        per_seed[str(seed)] = seed_block

    record["per_seed"] = per_seed
    record["artifacts"] = artifacts
    record["serving_compatible"] = False
    record["serving_note"] = (
        "final artifacts embed the log1p median/IQR (std-fallback) transform in their window "
        "pipeline; promoting to serving requires porting that transform into the serving path"
    )

    # Selection aggregate across b2-b4 (never b5, never deployment, never the test region).
    selection_names = [s.name for s, _, _ in triples if s.role == "selection"]
    ood_names = [s.name for s, _, _ in triples if s.role == "ood_report"]
    dep_names = [s.name for s, _, _ in triples if s.role == "deployment"]
    for metric in ("network", "ols_gate"):
        agg_input = {
            seed: {name: per_seed[seed]["folds"][name][metric]["rmse"] for name in selection_names} for seed in per_seed
        }
        record[f"selection_aggregate_{metric}"] = {
            "folds": selection_names,
            "per_seed_rmse": agg_input,
            "aggregate_per_seed": {seed: aggregate_block_metrics(vals) for seed, vals in agg_input.items()},
        }
    record["reported_separately"] = {
        "ood_folds": ood_names,
        "deployment": dep_names,
        "note": "b5 and the deployment split are reported per fold; never in the selection aggregate",
    }

    json_path = out / "calgary_pretrain.json"
    json_path.write_text(json.dumps(record, indent=2, default=float))
    logger.info("calgary_pretrain_complete", output=str(json_path))
    return record


# ── Dry run (no network, no writes, no epochs) ───────────────────────────────


def dry_run_calgary_pretrain(epochs: int, patience: int) -> dict[str, Any]:
    """Construct both stages' windows on the splits protocol and verify wiring; no training."""
    from experiment.tuning.gru_probe import _torch_device

    pin = splits_protocol_pin()

    calgary = calgary_counts()
    cal_spec = calgary_pretrain_split(calgary)
    stats = calgary_sparsity_stats(calgary, cal_spec)
    fit_windows, val_windows, cal_norm = build_stage_a_arrays(calgary, cal_spec)

    triples, skipped = _evaluation_specs()
    ck = clarknet_counts()

    lines = [
        f"dry-run variant=calgary_pretrain device={_torch_device()} epochs_budget={epochs} patience={patience}",
        f"prior: {PRIOR_NOTE}",
        (
            f"protocol_pin: splits.py sha256={pin['splits_py_sha256']} "
            f"matches_pinned={pin['matches_pinned_revision']} loader=splits.load_series "
            "(calgary=counts, clarknet_cv=counts, clarknet_deployment=rps x33)"
        ),
        "── stage A: calgary pretraining (splits.calgary_pretrain_split) ──",
        f"buckets={stats['buckets_total']} span_days={stats['span_days']} missing_buckets=0 unit=counts/15s",
        (
            f"sparsity: zero_share={stats['zero_share']:.4f} (train {stats['zero_share_train_portion']:.4f}) "
            f"cv={stats['coefficient_of_variation']} mean_counts={stats['mean_counts']}"
        ),
        f"handling: {stats['near_zero_handling']}",
        (
            f"train=[{cal_spec.require_region('train').start}, {cal_spec.require_region('train').stop}) span={cal_spec.require_region('train').span(CALGARY_ANCHOR)} "
            f"weekend_share={stats['weekend_share_train']}"
        ),
        (
            f"validation=[{cal_spec.require_region('validation').start}, {cal_spec.require_region('validation').stop}) "
            f"span={cal_spec.require_region('validation').span(CALGARY_ANCHOR)} (pure Sat+Sun block)"
        ),
        (
            f"post-cut tail [{cal_spec.require_region('validation').stop}, {CALGARY_N}) NEVER read "
            "(overlaps the ClarkNet week + 4h guard band)"
        ),
        f"stage_a_windows fit={fit_windows.to_dict()} val={val_windows.to_dict()}",
        (
            f"stage_a_isolation: fit_max={fit_windows.max_index_consumed} val_max={val_windows.max_index_consumed} "
            f"both < cut={cal_spec.require_region('validation').stop} OK; train ends before ClarkNet span start OK (asserted in splits)"
        ),
        (
            f"stage_a_normalizer: {cal_norm.method} center={cal_norm.center:.6f} scale={cal_norm.scale:.6f} "
            f"fit=[{cal_norm.fit_range.start}, {cal_norm.fit_range.stop}) (std fallback engaged: 84% zeros)"
        ),
        "── stage B: clarknet folds (splits.blocked_cv + deployment_split) ──",
        f"replay_window={list(REPLAY_WINDOW)} inside deployment test (asserted by splits); embargo={EMBARGO}",
    ]
    for sk in skipped["skipped"]:
        lines.append(f"SKIPPED {sk['block']}: eval={sk['eval']} - {sk['reason']}")

    fold_persistence: dict[str, float] = {}
    fold_ols: dict[str, float] = {}
    for spec, series, unit in triples:
        windows = build_spec_windows(series, spec)
        ols = ols_autoreg_fold(series, windows)
        from experiment.tuning.gru_probe import score_predictions as _sp

        ols_rmse = _sp(ols["preds"], windows.y_eval_raw, windows.last_eval_raw)["rmse"]
        fold_ols[spec.name] = ols_rmse
        pers = persistence_rmse_scalar(series, windows.carve["eval_region"][0], windows.carve["eval_region"][1])
        fold_persistence[spec.name] = pers
        day = spec_day_type_block(spec)
        lines.append(
            f"{spec.name} [{day['role']}] eval={day['eval_region']} weekend={day['eval_weekend_share']:.3f} "
            f"days={','.join(day['eval_day_types'])} unit={unit}"
        )
        lines.append(
            f"  carve fit={windows.carve['fit']} internal_val={windows.carve['internal_val']} "
            f"(early stop here, never the eval block) eval_windows={windows.n_eval_windows}"
        )
        lines.append(
            f"  normalizer={windows.stats.method} center={windows.stats.center:.4f} scale={windows.stats.scale:.4f}; "
            f"persistence_rmse={pers:.3f} ols_gate_rmse={ols_rmse:.3f} train_windows={ols['train_windows']}"
        )

    selection_names = [s.name for s, _, _ in triples if s.role == "selection"]
    sel = {name: fold_persistence[name] for name in selection_names}
    agg = aggregate_block_metrics(sel)
    ood_name = [s.name for s, _, _ in triples if s.role == "ood_report"][0]
    dep_name = [s.name for s, _, _ in triples if s.role == "deployment"][0]
    lines.append(
        f"persistence selection aggregate {sorted(sel)}: {agg['mean']:.3f} +/- {agg['std']:.3f} "
        f"(min {agg['min']:.3f}, max {agg['max']:.3f}, n={agg['n_blocks']}) unit=counts/15s"
    )
    ols_agg = aggregate_block_metrics({name: fold_ols[name] for name in selection_names})
    lines.append(
        f"OLS gate selection aggregate {sorted(selection_names)}: {ols_agg['mean']:.3f} +/- {ols_agg['std']:.3f} "
        f"(min {ols_agg['min']:.3f}, max {ols_agg['max']:.3f}); per-fold "
        + ", ".join(f"{name}={fold_ols[name]:.3f}" for name in selection_names)
        + "; kept only if calgary_pretrain beats this on the same folds"
    )
    lines.append(
        f"reference check: selection {REFERENCE_PERSISTENCE_SELECTION[0]:.3f} +/- "
        f"{REFERENCE_PERSISTENCE_SELECTION[1]:.3f}, ood {REFERENCE_PERSISTENCE_OOD_B5:.3f}, "
        f"deployment(counts) {REFERENCE_PERSISTENCE_DEPLOYMENT:.3f}; "
        f"this dry run: ood={fold_persistence[ood_name]:.3f} deployment={fold_persistence[dep_name]:.3f}"
    )
    if abs(agg["mean"] - REFERENCE_PERSISTENCE_SELECTION[0]) > REFERENCE_TOLERANCE:
        raise ValueError(
            f"selection persistence {agg['mean']:.3f} deviates from the reference "
            f"{REFERENCE_PERSISTENCE_SELECTION[0]:.3f} by more than {REFERENCE_TOLERANCE}: fold wiring is wrong"
        )
    if abs(fold_persistence[ood_name] - REFERENCE_PERSISTENCE_OOD_B5) > REFERENCE_TOLERANCE:
        raise ValueError(
            f"OOD fold persistence {fold_persistence[ood_name]:.3f} != reference {REFERENCE_PERSISTENCE_OOD_B5}"
        )
    dep_counts = persistence_rmse_scalar(ck, 26243, len(ck))
    if abs(dep_counts - REFERENCE_PERSISTENCE_DEPLOYMENT) > REFERENCE_TOLERANCE:
        raise ValueError(
            f"deployment persistence (counts) {dep_counts:.3f} != reference {REFERENCE_PERSISTENCE_DEPLOYMENT}"
        )
    lines.append(
        f"deployment arm series is amplified (x{manifest_scale_factor()}): persistence on the amplified "
        f"series = {fold_persistence[dep_name]:.3f} amplified-RPS units; counts-equivalent {dep_counts:.3f} matches"
    )
    lines.append(
        f"epoch_budgets: stage_a_pretrain={epochs} stage_b_finetune={epochs} patience={patience}; "
        "per-epoch stage-A validation loss recorded per seed"
    )
    lines.append(
        "artifacts (hash recorded at run time): <output-dir>/artifacts/"
        "calgary_pretrain_stage_a_s<seed>.pt, calgary_pretrain_<fold>_s<seed>.pt; run with "
        "--output-dir results/models/gru/<date>_probe-calgary-pretrain/ (governed tree; "
        "thesis-cited bundles must live under results/)"
    )
    lines.append(
        "screen_region=blocked_cv_selection_folds(b2,b3,b4) test_used_for_selection=false; "
        "b5 + deployment reported separately; NO epochs executed, NO files written"
    )

    report = "\n".join(lines)
    logger.info("calgary_pretrain_dry_run_complete")
    print(report)
    return {
        "protocol_pin": pin,
        "dry_run": True,
        "variant": "calgary_pretrain",
        "report": report,
        "calgary_spec": {
            "train": [cal_spec.require_region("train").start, cal_spec.require_region("train").stop],
            "validation": [cal_spec.require_region("validation").start, cal_spec.require_region("validation").stop],
        },
        "calgary_stats": stats,
        "stage_a": {"fit": fit_windows.to_dict(), "val": val_windows.to_dict()},
        "persistence_by_fold": fold_persistence,
        "selection_aggregate": agg,
    }
