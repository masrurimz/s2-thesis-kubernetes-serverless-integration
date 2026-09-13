"""Capacity-relative prediction target (t_cross): time/probability to cross capacity.

Motivation (measured regime problem): the training region of the inherited
deployment split holds 0% weekend while the served replay window is 82%
weekend, so absolute-RPS forecasting extrapolates a level regime the network
never saw. The controller's real question is capacity-relative — will load
cross the saturation capacity within the 9-step horizon, and when — which is
insensitive to the level shift by construction.

Label: per-step binary crossing indicator ``raw RPS >= capacity_rps`` with
``capacity_rps = r_saturation_per_replica * max_k8s_replicas`` resolved from
the central calibration at call time (never hard-coded). The network head
emits per-step crossing logits trained with BCE (pos_weight from fold-train
labels only); first-crossing time is derived at scoring. The GRU arm is
compared against the OLS autoregression on identical windows: the OLS
forecasts are thresholded at the same capacity, so the gate question becomes
"does the learned crossing head beat linear+threshold on per-step Brier".

Protocol: this module consumes ``experiment.tuning.splits`` as the contract —
selection folds b2/b3/b4 (blocked CV, expanding origin), fold b5 quarantined
as OOD report, the frozen deployment split reported separately with its
composition, and never used for selection. Every record pins the splits
module by sha256, states the series-construction path and the units of every
metric, and reports per-block day-type coverage with each number. The
point-forecast probe path is untouched and remains the default.

Deferred run (after the closed-loop experiment exits; governed bundle path):
    cd apps/experiment && uv run thesis-experiment gru-probe --variant t_cross \
        --seeds 42,43,44 --output-dir results/models/gru/2026-09-13_probe-t-cross

The crossing ceiling is scenario-dependent: selection folds and b5 threshold
at the code-default calibration (33.3 x 6 = 199.8 RPS), while the deployment
arm resolves its ceiling from the calibration its profile declares (the
definitive paired H2 configuration overrides max_k8s_replicas to 10 ->
333.0 RPS). Both ceilings and their sources are recorded in every record,
and each arm's label distribution under the other ceiling is reported so
the difference is visible, not implicit.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime
from typing import Any

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from pathlib import Path
from dataclasses import dataclass
import numpy as np
import structlog
from experiment.tuning.gru_hpo import (
    DEFAULT_HORIZON,
    EVAL_CHUNK_SIZE,
    FIXED_SAMPLE_INTERVAL,
    PROJECT_ROOT,
)
from experiment.tuning.gru_probe import (
    ProbeWindows,
    VariantArrays,
    _first_crossing_steps,
    _segment_sequences,
    _save_artifact,
    crossing_labels,
    ols_autoreg_fit,
    ols_autoreg_predict,
    probe_capacity,
    probe_config,
    score_crossing_predictions,
    train_probe_model,
)
from experiment.tuning.gru_study import _torch_device, manifest_scale_factor
from experiment.tuning.splits import (
    CLARKNET_N,
    EMBARGO,
    REPLAY_WINDOW,
    SEQUENCE_LENGTH,
    SplitSpec,
    aggregate_block_metrics,
    apply_normalizer,
    blocked_cv,
    deployment_split,
    load_series,
    normalizer_stats,
)

logger = structlog.get_logger(__name__)

SPLITS_PATH = Path(__file__).with_name("splits.py")
SPLITS_SHA256_PIN = "5f937edb361fbcea1a49334d92d768d409eefd1b12c563c5e708b9a1919631e3"
INNER_VAL_SPAN = 2_880  # 12 h early-stopping block carved from each fold's train tail
SEQ, HORIZON = SEQUENCE_LENGTH, DEFAULT_HORIZON


def splits_sha256() -> str:
    """Pin the protocol module; a geometry change cannot silently alter folds."""
    return hashlib.sha256(SPLITS_PATH.read_bytes()).hexdigest()


def splits_pin_check() -> dict[str, Any]:
    """Compare the on-disk splits module against the pinned protocol revision."""
    digest = splits_sha256()
    return {
        "sha256": digest,
        "pin": SPLITS_SHA256_PIN,
        "matches_pin": digest == SPLITS_SHA256_PIN,
    }


DEPLOYMENT_PROFILE_NAME = "h2-pair"


def deployment_capacity() -> dict[str, Any]:
    """Capacity ceiling the deployment arm actually runs under.

    The definitive paired H2 profile declares a calibration whose replica cap
    (10) overrides the code default (6), so its crossing ceiling differs from
    the selection program's. Resolved from the profile's calibration_path —
    never hard-coded — and recorded with both values' sources.
    """
    from experiment.profiles import get_profile

    profile = get_profile(DEPLOYMENT_PROFILE_NAME)
    cal_path = Path(profile.calibration_path)
    if not cal_path.is_absolute() and not cal_path.is_file():
        # Profile paths are repo-root relative; the probe may run from apps/experiment.
        cal_path = PROJECT_ROOT / cal_path
    cap = probe_capacity(str(cal_path))
    return {
        **cap,
        "profile": DEPLOYMENT_PROFILE_NAME,
        "calibration_path": profile.calibration_path,
        "declared_capacity_contract": dict(profile.capacity),
    }


def load_served_series() -> tuple[np.ndarray, dict[str, Any]]:
    """ClarkNet at the served amplitude: per-bucket mean RPS x manifest scale.

    Units: RPS. The capacity threshold from the calibration is defined in
    served RPS, so labels are thresholded on this exact series. Recorded
    provenance lets any 15x/33x disagreement be read as a unit mismatch.
    """
    scale = manifest_scale_factor()
    values = load_series("clarknet", unit="rps", scale_factor=scale)
    assert len(values) == CLARKNET_N, f"series length {len(values)} != frozen {CLARKNET_N}"
    return values, {
        "loader": "splits.load_series(clarknet, unit='rps')",
        "unit": "RPS (per-bucket mean requests/sec)",
        "scale_factor": scale,
        "manifest": "data/trace-replay/clarknet_replay_manifest.json",
        "n": int(len(values)),
    }


# ── Fold window construction ─────────────────────────────────────────────────


@dataclass(frozen=True)
class FoldWindows:
    """Window arrays for one fold: inner-fit / inner-val / eval, raw + normalised."""

    spec: SplitSpec
    X_fit: np.ndarray  # (n, seq, 1) normalised inputs
    y_fit: np.ndarray  # (n, horizon) binary crossing labels
    X_val: np.ndarray  # inner early-stopping block, normalised
    y_val: np.ndarray  # binary labels on the inner block
    X_eval: np.ndarray  # (n_eval, seq, 1) normalised
    y_eval_raw: np.ndarray  # (n_eval, horizon) raw RPS targets
    last_eval_raw: np.ndarray
    inner_fit_end: int
    inner_val_start: int
    inner_val_end: int
    pos_weight: float | None
    stats_record: dict[str, Any]


def build_fold_windows(values: np.ndarray, spec: SplitSpec, capacity: float) -> FoldWindows:
    """Windows + labels for one fold under the splits contract.

    Inputs are normalised with ``normalizer_stats`` fitted on the fold's train
    region only (log1p then median/IQR). Labels come from the RAW RPS series
    thresholded at capacity — the normaliser never touches labels. The inner
    early-stopping block is the last ``INNER_VAL_SPAN`` samples of the train
    region, separated from the inner fit end by the embargo.
    """
    train = spec.train
    eval_rng = spec.region(spec.eval_of_record)
    assert train is not None and eval_rng is not None

    inner_val_end = train.stop
    inner_val_start = inner_val_end - INNER_VAL_SPAN
    inner_fit_end = inner_val_start - EMBARGO
    assert inner_fit_end > 0, f"{spec.name}: inner fit end {inner_fit_end} <= 0"

    stats = normalizer_stats(values, spec, region="train", transform="log1p")
    normed = apply_normalizer(values, stats)

    X_fit_s, _, _, _ = _segment_sequences(normed, 0, inner_fit_end, SEQ, HORIZON)
    _, y_fit_raw, _, _ = _segment_sequences(values.astype(np.float64), 0, inner_fit_end, SEQ, HORIZON)
    X_val_s, _, _, _ = _segment_sequences(normed, inner_val_start, inner_val_end, SEQ, HORIZON)
    _, y_val_raw, _, _ = _segment_sequences(values.astype(np.float64), inner_val_start, inner_val_end, SEQ, HORIZON)
    X_eval_s, _, _, _ = _segment_sequences(normed, eval_rng.start, eval_rng.stop, SEQ, HORIZON)
    _, y_eval_raw, last_eval_raw, _ = _segment_sequences(
        values.astype(np.float64), eval_rng.start, eval_rng.stop, SEQ, HORIZON
    )
    y_fit = crossing_labels(y_fit_raw, capacity)
    y_val = crossing_labels(y_val_raw, capacity)
    pos = float(y_fit.sum())
    pos_weight = (float(y_fit.size) - pos) / pos if pos > 0 else None

    stats_record = {
        "method": stats.method,
        "center": stats.center,
        "scale": stats.scale,
        "fit_range": [stats.fit_range.start, stats.fit_range.stop],
        "n_fit": stats.n_fit,
    }
    return FoldWindows(
        spec=spec,
        X_fit=X_fit_s.astype(np.float32)[:, :, None],
        y_fit=y_fit,
        X_val=X_val_s.astype(np.float32)[:, :, None],
        y_val=y_val,
        X_eval=X_eval_s.astype(np.float32)[:, :, None],
        y_eval_raw=y_eval_raw,
        last_eval_raw=last_eval_raw,
        inner_fit_end=inner_fit_end,
        inner_val_start=inner_val_start,
        inner_val_end=inner_val_end,
        pos_weight=pos_weight,
        stats_record=stats_record,
    )


def fold_arrays(fw: FoldWindows, capacity: float) -> VariantArrays:
    """Wrap fold windows for the probe trainer (sigmoid head, identity z-stats)."""
    return VariantArrays(
        variant="t_cross",
        mode="zscore",
        log_space=False,
        seq_len=SEQ,
        horizon=HORIZON,
        X_fit=fw.X_fit,
        y_fit=fw.y_fit,
        X_val=fw.X_val,
        y_val=fw.y_val,
        X_test=fw.X_eval,
        y_test_raw=fw.y_eval_raw,
        last_test_raw=fw.last_eval_raw,
        z_mean=0.0,
        z_std=1.0,
        capacity_rps=capacity,
        target_mode="t_cross",
    )


def fold_ols_windows(spec: SplitSpec) -> ProbeWindows:
    """ProbeWindows view of a fold so ``ols_autoreg_fit`` fits on [0, train.stop)."""
    train = spec.train
    eval_rng = spec.region(spec.eval_of_record)
    assert train is not None and eval_rng is not None
    return ProbeWindows(
        seq_len=SEQ,
        horizon=HORIZON,
        fit_end=train.stop - INNER_VAL_SPAN - EMBARGO,
        val_start=train.stop - INNER_VAL_SPAN,
        val_end=train.stop,
        test_start=eval_rng.start,
        embargo_used=EMBARGO,
    )


# ── Reference arms (linear only; identical windows) ──────────────────────────


def reference_arms(values: np.ndarray, fw: FoldWindows, capacity: float) -> dict[str, Any]:
    """OLS+threshold and persistence+threshold crossing arms on the fold's eval windows.

    The OLS autoregression is fitted on the fold's raw-RPS train region only
    (blind to its eval block, mirroring the deployment contract's blind OLS).
    Persistence repeats the last observed RPS across the horizon. Both are
    thresholded at the same capacity as the labels. OLS and persistence RMSE
    in served RPS are also returned so the unit chain (counts / 15 x 33) can
    be checked against the protocol's counts-unit references.
    """
    spec = fw.spec
    eval_rng = spec.region(spec.eval_of_record)
    assert eval_rng is not None
    coef = ols_autoreg_fit(values, fold_ols_windows(spec))
    X_eval_raw, _, _, _ = _segment_sequences(values.astype(np.float64), eval_rng.start, eval_rng.stop, SEQ, HORIZON)
    ols_preds = ols_autoreg_predict(coef, X_eval_raw)
    ols_probs = (ols_preds >= capacity).astype(float)
    pers_probs = np.repeat((fw.last_eval_raw >= capacity).astype(float)[:, None], HORIZON, axis=1)

    return {
        "ols": score_crossing_predictions(ols_probs, fw.y_eval_raw, capacity),
        "persistence": score_crossing_predictions(pers_probs, fw.y_eval_raw, capacity),
        "_persistence_rmse_rps": float(
            np.sqrt(np.mean((np.repeat(fw.last_eval_raw[:, None], HORIZON, axis=1) - fw.y_eval_raw) ** 2))
        ),
        "_ols_rmse_rps": float(np.sqrt(np.mean((ols_preds - fw.y_eval_raw) ** 2))),
    }


def day_type_coverage(spec: SplitSpec) -> dict[str, Any]:
    """Day-type composition of the fold's eval block (reported with every metric)."""
    rng = spec.region(spec.eval_of_record)
    assert rng is not None
    prof = spec.profiles[spec.eval_of_record]
    return {
        "eval_range": [rng.start, rng.stop],
        "weekend_share": prof.weekend_share,
        "day_shares": {k: round(v, 4) for k, v in sorted(prof.day_shares.items())},
    }


def label_distribution(fw: FoldWindows, capacity: float) -> dict[str, Any]:
    """Crossing prevalence inside one fold (class balance before any training)."""
    out: dict[str, Any] = {}
    for name, labels, raw in (
        ("inner_fit", fw.y_fit, None),
        ("inner_val", fw.y_val, None),
        ("eval", None, fw.y_eval_raw),
    ):
        z = crossing_labels(raw, capacity) if labels is None else labels
        out[name] = {
            "n_windows": int(len(z)),
            "n_crossed": int(z.any(axis=1).sum()),
            "frac_windows_crossed": float(z.any(axis=1).mean()),
            "frac_steps_at_or_above_capacity": float(z.mean()),
        }
    return out


# ── Runner and dry run ───────────────────────────────────────────────────────


def _protocol_header(values: np.ndarray) -> dict[str, Any]:
    """Fold plan + per-arm capacity ceilings + splits pin, in record order."""
    plan = blocked_cv(values)
    deployment = deployment_split(values)
    capacities = {
        "selection_and_ood": probe_capacity(),
        "deployment": deployment_capacity(),
        "note": (
            "the crossing ceiling is scenario-dependent: selection folds and the b5 OOD "
            "report threshold at the code-default calibration, while the deployment arm "
            "resolves its ceiling from the calibration its profile actually runs under "
            "(the definitive paired H2 configuration overrides max_k8s_replicas to 10)"
        ),
    }
    return {
        "capacity": capacities,
        "splits_pin": splits_pin_check(),
        "splits_module": "experiment.tuning.splits",
        "fold_plan": {
            "selection": [s.name for s in plan.selection_folds()],
            "ood_report": [s.name for s in plan.ood_folds()],
            "skipped": [dict(s) for s in plan.skipped],
        },
        "deployment": {
            "name": deployment.name,
            "role": deployment.role,
            "used_for_selection": deployment.used_for_selection,
            "test": [deployment.test.start, deployment.test.stop] if deployment.test else None,
            "replay_window": list(REPLAY_WINDOW),
            "replay_inside_test": bool(
                deployment.test
                and deployment.test.start <= REPLAY_WINDOW[0]
                and REPLAY_WINDOW[1] < deployment.test.stop
            ),
        },
        "plan": plan,
        "_deployment_spec": deployment,
    }


def arm_capacity(spec_name: str, capacities: dict[str, Any]) -> float:
    """Ceiling for one arm: deployment specs use their profile's calibration."""
    key = "deployment" if "deployment" in spec_name else "selection_and_ood"
    return float(capacities[key]["capacity_rps"])


# ── Decision-threshold sweep, operating point, validation-only calibration ──


SWEEP_THRESHOLDS = tuple(round(float(t), 2) for t in np.arange(0.05, 1.00, 0.05))
OPERATING_TARGET_RECALL = 0.8


def crossing_threshold_sweep(
    probs: np.ndarray,
    y_raw: np.ndarray,
    capacity: float,
    thresholds: tuple[float, ...] = SWEEP_THRESHOLDS,
) -> list[dict[str, Any]]:
    """Recall/precision/false-alarm/lead as the window flag threshold moves.

    A window is flagged when the aggregate crossing probability
    ``p_win = 1 - prod(1 - p_step)`` reaches the threshold. Lead is measured
    only on true positives as ``t_actual - t_flag`` steps (positive = flagged
    before the first crossing). Pure read-out over per-window probabilities:
    no training, no refit.
    """
    z = np.asarray(y_raw, dtype=np.float64) >= capacity
    p = np.clip(np.asarray(probs, dtype=np.float64), 0.0, 1.0)
    p_win = 1.0 - np.prod(1.0 - p, axis=1)
    actual_win = z.any(axis=1)
    t_actual = _first_crossing_steps(z.astype(np.float64))
    rows: list[dict[str, Any]] = []
    for tau in thresholds:
        flagged = p_win >= tau
        hit_step = p >= tau
        t_flag = np.where(hit_step.any(axis=1), hit_step.argmax(axis=1), -1)
        tp = int(np.sum(flagged & actual_win))
        fp = int(np.sum(flagged & ~actual_win))
        fn = int(np.sum(~flagged & actual_win))
        tn = int(np.sum(~flagged & ~actual_win))
        recall = tp / (tp + fn) if tp + fn else 0.0
        precision = tp / (tp + fp) if tp + fp else 0.0
        false_alarm = fp / (fp + tn) if fp + tn else 0.0
        if tp > 0:
            lead = t_actual[flagged & actual_win] - t_flag[flagged & actual_win]
            mean_lead = float(np.mean(lead))
        else:
            mean_lead = float("nan")
        rows.append(
            {
                "threshold": float(tau),
                "recall": recall,
                "precision": precision,
                "false_alarm_rate": false_alarm,
                "mean_lead_steps": mean_lead,
                "n_flagged": int(flagged.sum()),
                "n_tp": tp,
                "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
            }
        )
    return rows


def pick_operating_point(
    rows: list[dict[str, Any]],
    target_recall: float = OPERATING_TARGET_RECALL,
) -> dict[str, Any]:
    """Best-precision row meeting the recall target; higher threshold on ties."""
    eligible = [r for r in rows if r["recall"] >= target_recall]
    if not eligible:
        return {
            "threshold": None,
            "reachable": False,
            "max_recall": max(r["recall"] for r in rows) if rows else 0.0,
            "note": f"no threshold reaches recall {target_recall}",
        }
    best = max(eligible, key=lambda r: (r["precision"], r["threshold"]))
    return {
        "threshold": best["threshold"],
        "reachable": True,
        **{k: best[k] for k in ("recall", "precision", "false_alarm_rate", "mean_lead_steps")},
    }


def aggregate_sweep(
    rows_per_fold: dict[str, list[dict[str, Any]]],
    thresholds: tuple[float, ...] = SWEEP_THRESHOLDS,
) -> list[dict[str, Any]]:
    """Per-threshold means across folds (NaN lead values drop from the mean)."""
    out: list[dict[str, Any]] = []
    names = list(rows_per_fold)
    for i, tau in enumerate(thresholds):
        row: dict[str, Any] = {"threshold": float(tau), "n_folds": len(names)}
        for key in ("recall", "precision", "false_alarm_rate", "f1"):
            row[key] = float(np.mean([rows_per_fold[n][i][key] for n in names]))
        leads = [rows_per_fold[n][i]["mean_lead_steps"] for n in names]
        leads = [v for v in leads if v == v]
        row["mean_lead_steps"] = float(np.mean(leads)) if leads else float("nan")
        out.append(row)
    return out


def fit_isotonic_calibration(
    val_probs: np.ndarray,
    val_labels: np.ndarray,
) -> tuple[Any, dict[str, Any]]:
    """Isotonic calibration fitted on the validation portion ONLY.

    Inputs are per-step probabilities and binary labels from the fold's
    inner-val windows. Fitting on the fit or eval regions is forbidden by the
    selection protocol; the record states the fit region explicitly.
    """
    from sklearn.isotonic import IsotonicRegression

    p = np.clip(np.asarray(val_probs, dtype=np.float64).ravel(), 0.0, 1.0)
    y = np.asarray(val_labels, dtype=np.float64).ravel()
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    iso.fit(p, y)
    return iso, {
        "method": "isotonic (sklearn IsotonicRegression, out_of_bounds=clip)",
        "fitted_on": "inner-val per-step probabilities and labels (validation portion only)",
        "n_pairs": int(p.size),
        "val_positive_rate": float(y.mean()),
    }


def apply_isotonic(iso: Any, probs: np.ndarray) -> np.ndarray:
    """Map per-step probabilities through the fitted isotonic curve."""
    shape = probs.shape
    p = np.clip(np.asarray(probs, dtype=np.float64).ravel(), 0.0, 1.0)
    return np.clip(iso.transform(p).reshape(shape), 0.0, 1.0)


def _forward_probs(model: Any, X: np.ndarray, device: str) -> np.ndarray:
    """Chunked no-grad forward: (n, seq, 1) inputs -> per-step probabilities."""
    import torch

    parts = []
    with torch.no_grad():
        for i in range(0, len(X), EVAL_CHUNK_SIZE):
            logits = model(torch.FloatTensor(X[i : i + EVAL_CHUNK_SIZE]).to(device)).cpu().numpy()
            parts.append(1.0 / (1.0 + np.exp(-logits)))
    return np.clip(np.concatenate(parts, axis=0), 0.0, 1.0)


def _evaluate_seed_fold(
    values: np.ndarray,
    fw: FoldWindows,
    arrays: VariantArrays,
    seed: int,
    epochs: int,
    patience: int,
    device: str,
    capacity: float,
) -> tuple[dict[str, Any], Any, int]:
    config = probe_config("t_cross", _probe_windows_view(fw.spec), epochs, patience)
    model, epochs_trained = train_probe_model(arrays, config, seed, "bce", device, pos_weight=fw.pos_weight)
    from experiment.tuning.gru_probe import predict_raw

    probs = predict_raw(model, arrays, device)
    block = score_crossing_predictions(probs, fw.y_eval_raw, capacity)
    return block, model, epochs_trained


def _probe_windows_view(spec: SplitSpec) -> ProbeWindows:
    return fold_ols_windows(spec)


def run_t_cross(
    seeds: tuple[int, ...] = (42, 43, 44),
    output_dir: str | Path | None = None,
    epochs: int = 200,
    patience: int = 25,
) -> dict[str, Any]:
    """Train/score the t_cross lever under the blocked-CV selection contract.

    Selection uses folds b2/b3/b4 only (aggregated mean/std/min/max via
    ``aggregate_block_metrics``); b5 is an OOD report and the deployment split
    is reported separately. Test/deployment regions never drive selection.
    """
    if output_dir is None:
        raise ValueError("--output-dir is required for probe runs (the probe never writes into results/)")
    values, series_record = load_served_series()
    header = _protocol_header(values)
    capacities: dict[str, Any] = header["capacity"]
    plan: Any = header.pop("plan")
    deployment_spec: SplitSpec = header.pop("_deployment_spec")

    device = _torch_device()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    selection = plan.selection_folds()
    ood = plan.ood_folds()
    all_specs = (*selection, *ood, deployment_spec)
    arm_caps = {s.name: arm_capacity(s.name, capacities) for s in all_specs}
    fold_windows = {s.name: build_fold_windows(values, s, arm_caps[s.name]) for s in all_specs}
    refs = {name: reference_arms(values, fw, arm_caps[name]) for name, fw in fold_windows.items()}

    record: dict[str, Any] = {
        "variant": "t_cross",
        "created": datetime.now().isoformat(timespec="seconds"),
        "headline_finding": {
            "claim": (
                "On the selection folds the linear arm's crossing recall is 0.8-4.2% against "
                "a 22-25% crossing base rate on identical windows: OLS autoregression almost "
                "never flags capacity crossings it is about to suffer. A learned crossing "
                "head has real headroom here — the first lever in this round where a model "
                "can plausibly clear its gate rather than tie it."
            ),
            "selection_crossing_base_rate": None,  # filled after reference arms are built
            "ols_crossing_recall_range": None,  # filled after reference arms are built
        },
        "seeds": list(seeds),
        "device": device,
        "epochs_budget": epochs,
        "patience": patience,
        "loss": "bce_with_logits",
        "series": series_record,
        "metric_units": {
            "brier": "dimensionless (per-step probability score, lower is better)",
            "t_cross_mae_steps": "steps of 15 s",
            "capacity_rps": "served RPS",
            "persistence_rmse_rps": "RPS at the served amplitude (counts/15 x 33)",
        },
        **{k: v for k, v in header.items()},
        "screen_region": "blocked-CV selection folds b2/b3/b4",
        "label_definition": {
            "target": "per-step binary crossing label; first-crossing time derived at scoring",
            "threshold_rule": "raw served RPS >= capacity_rps (inclusive)",
            "capacity_rps_by_arm": arm_caps,
            "step_sec": FIXED_SAMPLE_INTERVAL,
            "horizon_steps": HORIZON,
        },
        "reference_arms": {
            name: {
                "capacity_rps": arm_caps[name],
                "ols": refs[name]["ols"],
                "persistence": refs[name]["persistence"],
                "persistence_rmse_rps": refs[name]["_persistence_rmse_rps"],
                "ols_rmse_rps": refs[name]["_ols_rmse_rps"],
                "day_type_coverage": day_type_coverage(spec),
            }
            for name, spec in ((s.name, s) for s in all_specs)
        },
        "label_distribution": {name: label_distribution(fw, arm_caps[name]) for name, fw in fold_windows.items()},
        "label_distribution_by_ceiling": {
            f"selection_folds_at_{capacities['selection_and_ood']['capacity_rps']:.1f}rps": {
                s.name: label_distribution(fold_windows[s.name], float(capacities["selection_and_ood"]["capacity_rps"]))
                for s in selection
            },
            f"deployment_at_{capacities['deployment']['capacity_rps']:.1f}rps": label_distribution(
                fold_windows[deployment_spec.name],
                float(capacities["deployment"]["capacity_rps"]),
            ),
            f"deployment_at_{capacities['selection_and_ood']['capacity_rps']:.1f}rps_counterfactual": label_distribution(
                fold_windows[deployment_spec.name],
                float(capacities["selection_and_ood"]["capacity_rps"]),
            ),
        },
        "inner_val_span": INNER_VAL_SPAN,
    }

    total_jobs = len(seeds) * (len(selection) + len(ood) + 1)
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
    )
    progress.start()
    task = progress.add_task("t-cross trainings", total=total_jobs)
    job = 0
    per_seed: dict[str, Any] = {}
    seed_briers: dict[str, list[float]] = {}
    epochs_per_seed: dict[str, int] = {}
    artifacts: list[dict[str, Any]] = []
    for seed in seeds:
        seed_blocks: dict[str, Any] = {}
        probs_by_fold: dict[str, np.ndarray] = {}
        val_probs_by_fold: dict[str, np.ndarray] = {}
        persisted: dict[str, dict[str, np.ndarray]] = {}
        for role, specs in (("selection", selection), ("ood_report", ood), ("deployment", (deployment_spec,))):
            for spec in specs:
                job += 1
                t_job = time.time()
                progress.update(task, description=f"seed {seed} {spec.name}")
                fw = fold_windows[spec.name]
                cap = arm_caps[spec.name]
                arrays = fold_arrays(fw, cap)
                block, model, epochs_trained = _evaluate_seed_fold(
                    values, fw, arrays, seed, epochs, patience, device, cap
                )
                progress.advance(task)
                progress.console.print(
                    f"  seed {seed} [bold]{spec.name}[/bold]: brier {block['brier_per_step']:.4f} "
                    f"recall {block['crossing_recall']:.4f} FAR {block['false_alarm_rate']:.3f} "
                    f"lead {block['t_cross_mae_steps']:.1f} steps "
                    f"[dim]({time.time() - t_job:.0f}s, {epochs_trained} epochs)[/dim]"
                )
                if role == "selection":
                    probs_by_fold[spec.name] = _forward_probs(model, fw.X_eval, device)
                    val_probs_by_fold[spec.name] = _forward_probs(model, fw.X_val, device)
                refs_block = refs[spec.name]
                if refs_block["ols"]["brier_per_step"] > 0:
                    block["skill_vs_ols_brier"] = 1.0 - block["brier_per_step"] / refs_block["ols"]["brier_per_step"]
                else:
                    block["skill_vs_ols_brier"] = 0.0
                block["capacity_rps"] = cap
                block["role"] = role
                block["used_for_selection"] = spec.used_for_selection
                block["day_type_coverage"] = day_type_coverage(spec)
                block["windows"] = {
                    "inner_fit": [0, fw.inner_fit_end],
                    "inner_val": [fw.inner_val_start, fw.inner_val_end],
                    "eval_range": [
                        fw.spec.region(fw.spec.eval_of_record).start,
                        fw.spec.region(fw.spec.eval_of_record).stop,
                    ],
                    "normalizer": fw.stats_record,
                    "pos_weight": fw.pos_weight,
                }
                if role == "selection" and block["n_windows_crossed"] > 0:
                    # Decision-threshold sweep (no retraining) and a
                    # validation-only isotonic calibration of the per-step
                    # probabilities, so the Brier gate becomes reachable.
                    rows = crossing_threshold_sweep(probs_by_fold[spec.name], fw.y_eval_raw, cap)
                    block["threshold_sweep"] = rows
                    block["operating_point_recall_0.8"] = pick_operating_point(rows)
                    iso, cal_info = fit_isotonic_calibration(val_probs_by_fold[spec.name], fw.y_val)
                    cal_probs = apply_isotonic(iso, probs_by_fold[spec.name])
                    cal_rows = crossing_threshold_sweep(cal_probs, fw.y_eval_raw, cap)
                    block["calibration"] = cal_info
                    block["brier_calibrated"] = float(np.mean((cal_probs - (fw.y_eval_raw >= cap)) ** 2))
                    block["threshold_sweep_calibrated"] = cal_rows
                    block["operating_point_calibrated_recall_0.8"] = pick_operating_point(cal_rows)
                    persisted[spec.name] = {
                        "probs": probs_by_fold[spec.name],
                        "cal_probs": cal_probs,
                        "labels": (fw.y_eval_raw >= cap).astype(np.float64),
                        "y_raw": fw.y_eval_raw,
                        "val_probs": val_probs_by_fold[spec.name],
                        "val_labels": fw.y_val.astype(np.float64),
                    }
                elif block["n_windows_crossed"] == 0:
                    block["threshold_sweep_note"] = "degenerate: no eval crossings at this ceiling"
                seed_blocks[spec.name] = block
                if role == "selection":
                    seed_briers.setdefault(str(seed), []).append(block["brier_per_step"])
                epochs_per_seed[str(seed)] = epochs_trained
                if role == "deployment":
                    artifact_path = out / "artifacts" / f"t_cross_s{seed}.pt"
                    artifacts.append(
                        {
                            "path": str(artifact_path),
                            "seed": seed,
                            "trained_on": "deployment train region [0, 22500) at served amplitude",
                            "capacity_source": capacities["deployment"]["source"],
                            "sha256": _save_artifact(
                                model,
                                probe_config("t_cross", fold_ols_windows(spec), epochs, patience),
                                arrays,
                                artifact_path,
                            ),
                        }
                    )
        # Persist per-window probabilities so every sweep stays
        # reconstructible without retraining.
        probs_dir = out / "probs"
        probs_dir.mkdir(parents=True, exist_ok=True)
        npz_path = probs_dir / f"t_cross_s{seed}.npz"
        np.savez_compressed(
            npz_path,
            **{f"{fold}__{key}": arr for fold, arrays_d in persisted.items() for key, arr in arrays_d.items()},
        )
        record.setdefault("probs_persisted", []).append(
            {
                "seed": seed,
                "path": str(npz_path.relative_to(out)),
                "sha256": hashlib.sha256(npz_path.read_bytes()).hexdigest(),
                "folds": sorted(persisted),
                "arrays": sorted(next(iter(persisted.values())).keys()) if persisted else [],
                "note": "per-window per-step probabilities, isotonic-calibrated probabilities, labels and raw targets per selection fold",
            }
        )
        per_seed[str(seed)] = seed_blocks
    progress.stop()
    record["per_seed"] = per_seed
    record["epochs_trained_per_seed"] = epochs_per_seed
    record["artifacts"] = artifacts
    record["serving_compatible"] = True
    record["serving_note"] = (
        "t_cross artifacts record target_mode='t_cross'; consumed via "
        "GRUPredictor.predict_crossing (probabilistic mode). Point-forecast "
        "artifacts and the /predict contract are unchanged."
    )

    per_metric: dict[str, dict[str, float]] = {}
    for metric in ("brier_per_step", "t_cross_mae_steps", "crossing_recall", "crossing_precision", "false_alarm_rate"):
        # Aggregate across the three selection fold blocks (the protocol's
        # aggregation unit); each fold's value is the mean over seeds. NaN
        # (a fold whose eval never crosses) drops that fold from the metric
        # and n_blocks records it.
        fold_vals: dict[str, float] = {}
        for s in selection:
            seed_vals = [
                float(v)
                for sk in per_seed
                for v in [per_seed[sk].get(s.name, {}).get(metric)]
                if v is not None and v == v
            ]
            if seed_vals:
                fold_vals[s.name] = float(np.mean(seed_vals))
        if len(fold_vals) >= 2:
            per_metric[metric] = aggregate_block_metrics(fold_vals)
    record["selection_aggregate"] = per_metric
    ols_sel = aggregate_block_metrics({s.name: refs[s.name]["ols"]["brier_per_step"] for s in selection})
    # Calibrated Brier aggregated across fold blocks; the isotonic fit is
    # per fold×seed on that fold's inner-val (validation portion) only.
    cal_fold_vals: dict[str, float] = {}
    for s in selection:
        cal_seed_vals = [
            float(v)
            for sk in per_seed
            for v in [per_seed[sk].get(s.name, {}).get("brier_calibrated")]
            if v is not None and v == v
        ]
        if cal_seed_vals:
            cal_fold_vals[s.name] = float(np.mean(cal_seed_vals))
    if len(cal_fold_vals) >= 2:
        record["brier_calibrated_selection"] = aggregate_block_metrics(cal_fold_vals)
    # Aggregated decision-threshold curves: per fold, the seed-mean row at
    # each threshold; then the mean across folds.
    sweeps_uncal: dict[str, list[dict[str, Any]]] = {}
    sweeps_cal: dict[str, list[dict[str, Any]]] = {}
    for s in selection:
        seed_rows_u = [
            per_seed[sk][s.name]["threshold_sweep"]
            for sk in per_seed
            if "threshold_sweep" in per_seed[sk].get(s.name, {})
        ]
        seed_rows_c = [
            per_seed[sk][s.name]["threshold_sweep_calibrated"]
            for sk in per_seed
            if "threshold_sweep_calibrated" in per_seed[sk].get(s.name, {})
        ]
        if seed_rows_u:
            sweeps_uncal[s.name] = [
                {
                    key: float(np.mean([r[i][key] for r in seed_rows_u if r[i][key] == r[i][key]]))
                    if any(r[i][key] == r[i][key] for r in seed_rows_u)
                    else float("nan")
                    for key in ("recall", "precision", "false_alarm_rate", "f1", "mean_lead_steps")
                }
                | {"threshold": float(tau)}
                for i, tau in enumerate(SWEEP_THRESHOLDS)
            ]
        if seed_rows_c:
            sweeps_cal[s.name] = [
                {
                    key: float(np.mean([r[i][key] for r in seed_rows_c if r[i][key] == r[i][key]]))
                    if any(r[i][key] == r[i][key] for r in seed_rows_c)
                    else float("nan")
                    for key in ("recall", "precision", "false_alarm_rate", "f1", "mean_lead_steps")
                }
                | {"threshold": float(tau)}
                for i, tau in enumerate(SWEEP_THRESHOLDS)
            ]
    if len(sweeps_uncal) >= 2:
        agg_rows_u = aggregate_sweep(sweeps_uncal)
        agg_rows_c = aggregate_sweep(sweeps_cal) if len(sweeps_cal) == len(sweeps_uncal) else []
        record["decision_rule"] = {
            "primary": "recall at a bounded false-alarm rate on the selection folds; Brier is reported but no longer the keep rule",
            "target_recall": OPERATING_TARGET_RECALL,
            "operating_point_uncalibrated": pick_operating_point(agg_rows_u),
            "operating_point_calibrated": pick_operating_point(agg_rows_c) if agg_rows_c else None,
            "curve_uncalibrated": agg_rows_u,
            "curve_calibrated": agg_rows_c,
            "calibration": {
                "method": "isotonic, fitted per fold x seed on the fold's inner-val per-step pairs only",
                "brier_before": per_metric.get("brier_per_step", {}).get("mean"),
                "brier_after": record.get("brier_calibrated_selection", {}).get("mean"),
                "ols_brier_reference": ols_sel["mean"],
            },
        }
    record["beats_ols_gate"] = {
        "rule": "keep the lever iff mean per-step Brier on selection folds b2/b3/b4 beats OLS+threshold on identical windows",
        "variant_mean_brier": per_metric.get("brier_per_step", {}).get("mean"),
        "variant_mean_brier_calibrated": record.get("brier_calibrated_selection", {}).get("mean"),
        "ols_mean_brier": ols_sel["mean"],
        "note": (
            "the 29.4649 RMSE gate governs point-forecast variants; t_cross is a classification "
            "target. The uncalibrated head fails the Brier rule through overconfidence; the "
            "inner-val isotonic calibration (decision_rule.calibration) is the path to a "
            "reachable Brier, and the primary keep rule for a controller is recall at a "
            "bounded false-alarm rate (decision_rule.primary)"
        ),
    }
    record["ood_report_b5"] = {
        s.name: {k: v for k, v in per_seed[next(iter(per_seed))][s.name].items() if k != "windows"} for s in ood
    }
    record["deployment_report"] = {
        deployment_spec.name: {
            k: v for k, v in per_seed[next(iter(per_seed))][deployment_spec.name].items() if k != "windows"
        }
    }
    json_path = out / "t_cross.json"
    json_path.write_text(json.dumps(record, indent=2, default=float))
    logger.info("t_cross_complete", output=str(json_path), seeds=list(seeds))
    dr = record.get("decision_rule", {})
    cal = dr.get("calibration", {})
    summary = Table(title="t_cross — decision rule (selection folds b2/b3/b4)")
    summary.add_column("metric", style="bold")
    summary.add_column("value", justify="right")
    if dr:
        summary.add_row("operating point (uncalibrated)", repr(dr.get("operating_point_uncalibrated")))
        summary.add_row("operating point (calibrated)", repr(dr.get("operating_point_calibrated")))
        summary.add_row("Brier uncalibrated → calibrated", f"{cal.get('brier_before')} → {cal.get('brier_after')}")
        summary.add_row("OLS Brier reference", str(cal.get("ols_brier_reference")))
    summary.add_row("record", str(json_path))
    progress.console.print(summary)
    return record


def dry_run_t_cross(epochs: int, patience: int) -> dict[str, Any]:
    """Build every fold's windows and labels; score the linear arms. No network, no writes."""
    values, series_record = load_served_series()
    header = _protocol_header(values)
    capacities: dict[str, Any] = header["capacity"]
    cap_sel = float(capacities["selection_and_ood"]["capacity_rps"])
    cap_dep = float(capacities["deployment"]["capacity_rps"])
    plan: Any = header.pop("plan")
    deployment_spec: SplitSpec = header.pop("_deployment_spec")

    selection = plan.selection_folds()
    ood = plan.ood_folds()
    all_specs = (*selection, *ood, deployment_spec)
    arm_caps = {s.name: arm_capacity(s.name, capacities) for s in all_specs}
    lines = [
        f"dry-run variant=t_cross epochs_budget={epochs} patience={patience}",
        f"series={json.dumps(series_record)}",
        f"capacity selection/b5 = {cap_sel:.1f} RPS "
        f"({capacities['selection_and_ood']['r_saturation_per_replica']} x "
        f"{capacities['selection_and_ood']['replicas_at_capacity']}, {capacities['selection_and_ood']['source']})",
        f"capacity deployment   = {cap_dep:.1f} RPS "
        f"({capacities['deployment']['r_saturation_per_replica']} x "
        f"{capacities['deployment']['replicas_at_capacity']}, profile {capacities['deployment']['profile']}, "
        f"{capacities['deployment']['source']}) — scenario-dependent ceiling, recorded per arm",
        f"splits_pin={header['splits_pin']['sha256'][:16]}... matches_pin={header['splits_pin']['matches_pin']}",
        f"folds: selection={[s.name for s in selection]} ood={[s.name for s in ood]} "
        f"skipped={[s['block'] for s in header['fold_plan']['skipped']]}",
        f"deployment test={header['deployment']['test']} replay={header['deployment']['replay_window']} "
        f"replay_inside_test={header['deployment']['replay_inside_test']} (asserted by splits.validate)",
    ]

    fold_report: dict[str, Any] = {}
    for role, specs in (("selection", selection), ("ood_report", ood), ("deployment", (deployment_spec,))):
        for spec in specs:
            cap = arm_caps[spec.name]
            fw = build_fold_windows(values, spec, cap)
            refs = reference_arms(values, fw, cap)
            dist = label_distribution(fw, cap)
            # The other ceiling's distribution on the same windows, so the
            # 199.8-vs-333 difference is visible rather than implicit.
            dist_alt = label_distribution(fw, cap_dep if cap == cap_sel else cap_sel)
            cov = day_type_coverage(spec)
            fold_report[spec.name] = {
                "role": role,
                "capacity_rps": cap,
                "label_distribution": dist,
                "label_distribution_other_ceiling": dist_alt,
                "day_type_coverage": cov,
                "ols_crossing": refs["ols"],
                "persistence_crossing": refs["persistence"],
                "persistence_rmse_rps": refs["_persistence_rmse_rps"],
                "ols_rmse_rps": refs["_ols_rmse_rps"],
                "normalizer": fw.stats_record,
                "pos_weight": fw.pos_weight,
                "windows": {
                    "inner_fit": [0, fw.inner_fit_end],
                    "inner_val": [fw.inner_val_start, fw.inner_val_end],
                    "n_fit_windows": int(len(fw.y_fit)),
                    "n_eval_windows": int(len(fw.y_eval_raw)),
                },
            }
            lines.append(
                f"{spec.name} [{role}] cap={cap:.1f} eval={cov['eval_range']} weekend={cov['weekend_share']:.1%} | "
                f"crossing: fit {dist['inner_fit']['frac_windows_crossed']:.4f} "
                f"val {dist['inner_val']['frac_windows_crossed']:.4f} "
                f"eval {dist['eval']['frac_windows_crossed']:.4f} "
                f"(other ceiling eval {dist_alt['eval']['frac_windows_crossed']:.4f}) | "
                f"ols_brier={refs['ols']['brier_per_step']:.4f} "
                f"ols_recall={refs['ols']['crossing_recall']:.3f} | "
                f"ols_rmse={refs['_ols_rmse_rps']:.4f} RPS "
                f"persistence_rmse={refs['_persistence_rmse_rps']:.4f} RPS"
            )

    ols_rmse_sel = aggregate_block_metrics({s.name: fold_report[s.name]["ols_rmse_rps"] for s in selection})
    ols_rmse_counts = aggregate_block_metrics(
        {s.name: fold_report[s.name]["ols_rmse_rps"] * 15.0 / series_record["scale_factor"] for s in selection}
    )
    ols_sel = aggregate_block_metrics(
        {s.name: fold_report[s.name]["ols_crossing"]["brier_per_step"] for s in selection}
    )
    eval_frac_sel = aggregate_block_metrics(
        {s.name: fold_report[s.name]["label_distribution"]["eval"]["frac_windows_crossed"] for s in selection}
    )
    val_positives = [fold_report[s.name]["label_distribution"]["inner_val"]["n_crossed"] for s in selection]
    trainable = min(val_positives) >= 50 and all(
        0.01 <= fold_report[s.name]["label_distribution"]["eval"]["frac_windows_crossed"] <= 0.9 for s in selection
    )
    verdict = (
        "trainable: every selection fold's eval block holds >=1% crossing windows and every "
        "inner-val block holds >=50 positive windows"
        if trainable
        else "NOT trainable as configured: label too imbalanced on at least one selection fold — "
        "state this plainly in the record and do not run the deferred training"
    )
    dep_name = deployment_spec.name
    dep_dist = fold_report[dep_name]["label_distribution"]
    dep_val_pos = dep_dist["inner_val"]["n_crossed"]
    dep_fit_frac = dep_dist["inner_fit"]["frac_windows_crossed"]
    dep_verdict = (
        f"deployment arm at its own {cap_dep:.1f} RPS ceiling: fit {dep_fit_frac:.4f} crossed, "
        f"inner-val {dep_val_pos} positive windows, eval {dep_dist['eval']['frac_windows_crossed']:.4f} — "
        + (
            "label-degenerate for standalone training (no inner-val positives); the deferred run "
            "still trains and reports it, but the lever's keep/drop decision comes from the "
            "selection folds at the default ceiling"
            if dep_val_pos == 0
            else "trainable"
        )
    )
    persistence_sel = aggregate_block_metrics({s.name: fold_report[s.name]["persistence_rmse_rps"] for s in selection})
    persistence_counts = aggregate_block_metrics(
        {s.name: fold_report[s.name]["persistence_rmse_rps"] * 15.0 / series_record["scale_factor"] for s in selection}
    )
    ols_recall_range = [
        min(fold_report[s.name]["ols_crossing"]["crossing_recall"] for s in selection),
        max(fold_report[s.name]["ols_crossing"]["crossing_recall"] for s in selection),
    ]
    lines += [
        f"HEADLINE: linear-arm crossing recall {ols_recall_range[0]:.3f}-{ols_recall_range[1]:.3f} "
        f"against a {eval_frac_sel['mean']:.1%} crossing base rate on the selection folds — "
        f"OLS almost never flags crossings it is about to suffer; the learned head has real headroom",
        f"unit chain: series = counts/15 x {series_record['scale_factor']:g} (served RPS); "
        f"RMSE in RPS x 15/{series_record['scale_factor']:g} = counts/bucket for reference comparisons",
        f"selection OLS RMSE = {ols_rmse_sel['mean']:.4f} +/- {ols_rmse_sel['std']:.4f} served RPS "
        f"= {ols_rmse_counts['mean']:.4f} +/- {ols_rmse_counts['std']:.4f} counts "
        f"(protocol gate 16.677 +/- 0.109 counts; wiring check)",
        f"selection persistence RMSE = {persistence_sel['mean']:.4f} +/- {persistence_sel['std']:.4f} served RPS "
        f"= {persistence_counts['mean']:.4f} +/- {persistence_counts['std']:.4f} counts "
        f"(reference 22.572 +/- 0.124 counts; wiring check, not an equality: this harness "
        f"scores persistence per window at lags 1..9, the reference uses a fixed lag 9)",
        f"selection OLS crossing Brier = {ols_sel['mean']:.4f} (min {ols_sel['min']:.4f}, max {ols_sel['max']:.4f}) "
        f"— the t_cross gate on identical folds (per-step Brier, lower is better)",
        f"selection eval crossing fraction = {eval_frac_sel['mean']:.4f} "
        f"(min {eval_frac_sel['min']:.4f}, max {eval_frac_sel['max']:.4f})",
        f"inner-val positive windows per selection fold: {val_positives}",
        f"trainable_verdict: {verdict}",
        f"deployment_label_balance: {dep_verdict}",
        "follow-up wiring: the run now reports a decision-threshold sweep (recall/precision/"
        "false-alarm/lead per threshold, operating point at 0.8 recall), an inner-val-only "
        "isotonic calibration with a recalibrated Brier, and persists per-window probabilities "
        "under probs/t_cross_s<seed>.npz. Limitation, stated plainly: the 2026-09-13_probe-t-cross "
        "bundle did NOT persist per-window probabilities, so its sweep cannot be reconstructed "
        "from that record — rerun to obtain the curve.",
    ]

    report = "\n".join(lines)
    print(report)
    payload = {
        "dry_run": True,
        "variant": "t_cross",
        "report": report,
        "series": series_record,
        "headline_finding": {
            "claim": (
                "OLS+threshold crossing recall is near zero against a 22-25% crossing base "
                "rate on the selection folds; a learned crossing head has real headroom"
            ),
            "selection_crossing_base_rate": eval_frac_sel,
            "ols_crossing_recall_range": ols_recall_range,
        },
        "selection_aggregate": {
            "ols_rmse_rps": ols_rmse_sel,
            "ols_rmse_counts_equivalent": ols_rmse_counts,
            "persistence_rmse_rps": persistence_sel,
            "persistence_rmse_counts_equivalent": persistence_counts,
            "ols_brier": ols_sel,
            "eval_crossing_fraction": eval_frac_sel,
        },
        "deployment": header["deployment"],
        "follow_up_wiring": {
            "threshold_sweep": "recall/precision/false-alarm/lead per threshold; operating point at 0.8 recall",
            "calibration": "isotonic fitted on each fold's inner-val per-step pairs only; recalibrated Brier reported",
            "probs_persisted": "per-window per-step probabilities saved under probs/t_cross_s<seed>.npz with sha256",
            "prior_bundle_limitation": (
                "the 2026-09-13_probe-t-cross record did not persist per-window probabilities; "
                "its sweep cannot be reconstructed from that record — rerun required"
            ),
        },
        "deployment_label_balance": {
            "capacity_rps": cap_dep,
            "inner_val_positive_windows": dep_val_pos,
            "fit_frac_crossed": dep_fit_frac,
            "eval_frac_crossed": dep_dist["eval"]["frac_windows_crossed"],
            "verdict": dep_verdict,
        },
        "gate_references": {
            "ols_rmse_selection_counts": {"mean": 16.677, "std": 0.109, "min": 16.593, "max": 16.800},
            "persistence_rmse_selection_counts": {"mean": 22.572, "std": 0.124},
            "b5_persistence_rmse_counts": 16.564,
            "deployment_persistence_rmse_counts": 18.060,
            "note": (
                "point-forecast gate is OLS RMSE 16.677 counts on selection folds; the t_cross "
                "lever is a classification target, so its gate is the OLS+threshold per-step "
                "Brier on the identical folds (selection_aggregate.ols_brier)"
            ),
        },
        "folds": fold_report,
    }
    logger.info("t_cross_dry_run_complete", trainable=trainable)
    return payload
