"""Leak-free GRU/LSTM horizon-9 study on ClarkNet (primary) and synthetic arms.

Frozen protocol (implemented here, do not redesign):

- Data: ClarkNet 15 s resampled series from ``data/processed/clarknet_real_rps.parquet``
  (column ``rps``), 40,315 samples. Chronological splits with an embargo of
  ``sequence_length + horizon - 1`` samples at every boundary:
  train ``[0, 22500)``, validation ``[22539, 26205)``, test ``[26243, 40315)``.
- Amplitude: the k6 replay multiplies raw ClarkNet by ``scale_factor`` from
  ``data/trace-replay/clarknet_replay_manifest.json`` (33.0), reaching ~73 RPS
  mean / 164 max inside the replay window. The predictor is fed that amplified
  series at serving time, so the study multiplies the resampled series by the
  manifest factor before splitting; the scaler is then fitted on the amplified
  training portion only and matches serving-time z-scores.
- Selection: hyperparameters and the epoch budget are chosen on the validation
  portion only (sequence lengths are restricted to 20/30 because a 45-sample
  look-back would need an embargo larger than the frozen 39-sample train→val
  gap). The winner is refit on train+validation at the frozen epoch budget
  (best epoch + 1 from the selection fit), then the test portion is evaluated
  exactly once per seed.
- Synthetic arm (H3 basis, deferrable): ``generate_realistic_traffic`` from
  ``apps/prediction/prediction/training/train_gru.py`` with seed 42, 72 hours
  at 1-minute resolution, base_rps 100. Each minute's value is held across its
  four 15-second buckets so the sample interval matches the deployment arm.
  Reported separately; never used for selection. ClarkNet stays the primary
  arm and the only producer of the deployment artifact.
- Reporting: per-horizon RMSE, MAE, normalised RMSE, skill score vs
  persistence, under-prediction on rising targets (mean and p90), upper
  envelope coverage, per-archetype RMSE (spike/ramp/periodic/stationary,
  out-of-distribution check only), baselines (persistence, linear trend,
  seasonal naive) on identical windows, rolling-origin folds over the test
  portion (mean ± std), and a paired permutation test between cells on
  per-seed holdout RMSE (reusing ``shared.stats``; no scipy fallback needed).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import optuna
import pandas as pd
import structlog
import yaml

from experiment.tuning.gru_hpo import (
    DEFAULT_HORIZON,
    DEFAULT_TRIALS,
    FIXED_BATCH_SIZE,
    FIXED_EPOCHS,
    FIXED_PATIENCE,
    FIXED_SAMPLE_INTERVAL,
    PROJECT_ROOT,
    _set_deterministic,
    compute_objective,
    evaluate_on_values,
    linear_trend_baseline,
    locate_replay_window,
    persistence_baseline,
    rolling_origin_evaluation,
    seasonal_naive_baseline,
)
from prediction.gru_predictor import GRUConfig, GRUPredictor
from shared.stats import cohens_d_paired, paired_bootstrap_ci, paired_permutation_test

logger = structlog.get_logger(__name__)

# ── Frozen ClarkNet protocol indices (40,315 samples at 15 s) ────────────────

CLARKNET_TOTAL = 40315
CLARKNET_TRAIN_END = 22500
CLARKNET_VAL_START = 22539
CLARKNET_VAL_END = 26205
CLARKNET_TEST_START = 26243
TRAIN_FRAC = CLARKNET_TRAIN_END / CLARKNET_TOTAL
VAL_FRAC = (CLARKNET_VAL_END - CLARKNET_VAL_START) / CLARKNET_TOTAL

# seq_len 45 would require an embargo of 53 > the frozen 39-sample gap.
SEARCH_SEQUENCE_LENGTHS = (20, 30)

DEFAULT_SEEDS = (42, 43, 44, 45, 46)
DEFAULT_CELLS = ("gru", "lstm")
DEFAULT_DATA_SOURCES = ("clarknet",)
DEFAULT_SEASON = 5760  # Seasonal-naive period: one day at 15 s samples (frozen protocol)
CLARKNET_PARQUET = PROJECT_ROOT / "data" / "processed" / "clarknet_real_rps.parquet"
REPLAY_MANIFEST = PROJECT_ROOT / "data" / "trace-replay" / "clarknet_replay_manifest.json"
ARCHETYPE_FILES = {
    "spike": PROJECT_ROOT / "data" / "trace-replay" / "archetype_spike_k6_stages.json",
    "ramp": PROJECT_ROOT / "data" / "trace-replay" / "archetype_ramp_k6_stages.json",
    "periodic": PROJECT_ROOT / "data" / "trace-replay" / "archetype_periodic_k6_stages.json",
    "stationary": PROJECT_ROOT / "data" / "trace-replay" / "archetype_stationary_k6_stages.json",
}
DEPLOYED_ARTIFACT = PROJECT_ROOT / "data" / "models" / "gru_model.pt"


@dataclass(frozen=True)
class StudySplits:
    """Chronological, embargoed split indices for one data arm."""

    n_total: int
    seq_len: int
    horizon: int
    train_end: int
    val_start: int
    val_end: int
    test_start: int

    @property
    def embargo(self) -> int:
        return self.seq_len + self.horizon - 1

    def to_dict(self) -> dict[str, int]:
        return {
            "n_total": self.n_total,
            "train_end": self.train_end,
            "val_start": self.val_start,
            "val_end": self.val_end,
            "test_start": self.test_start,
            "embargo": self.embargo,
        }


def build_splits(n_total: int, seq_len: int, horizon: int, source: str) -> StudySplits:
    """Return the frozen ClarkNet splits or proportional splits with embargo."""
    embargo = seq_len + horizon - 1

    if source == "clarknet":
        if n_total != CLARKNET_TOTAL:
            raise ValueError(f"ClarkNet series must have {CLARKNET_TOTAL} samples after 15 s resample, got {n_total}")
        frozen_gap = CLARKNET_VAL_START - CLARKNET_TRAIN_END
        if seq_len + horizon - 1 <= frozen_gap:
            # Frozen protocol literals: byte-identical for every window the
            # 38-sample gaps can host (the searched 20/30 space).
            splits = StudySplits(
                n_total=n_total,
                seq_len=seq_len,
                horizon=horizon,
                train_end=CLARKNET_TRAIN_END,
                val_start=CLARKNET_VAL_START,
                val_end=CLARKNET_VAL_END,
                test_start=CLARKNET_TEST_START,
            )
        else:
            # Derived boundaries for larger windows: preserve the frozen train
            # and validation spans exactly, enforce the embargo
            # (window + horizon - 1) at both gaps, and fail loudly when the
            # remaining test region cannot host windows.
            train_end = CLARKNET_TRAIN_END
            val_span = CLARKNET_VAL_END - CLARKNET_VAL_START
            val_start = train_end + embargo
            val_end = val_start + val_span
            test_start = val_end + embargo
            if test_start + seq_len + horizon + 1 > n_total:
                raise ValueError(
                    f"Derived ClarkNet boundaries for seq_len={seq_len} leave no test region: "
                    f"test_start={test_start}, n_total={n_total}"
                )
            splits = StudySplits(
                n_total=n_total,
                seq_len=seq_len,
                horizon=horizon,
                train_end=train_end,
                val_start=val_start,
                val_end=val_end,
                test_start=test_start,
            )
    else:
        train_end = int(round(n_total * TRAIN_FRAC))
        val_start = train_end + embargo
        val_end = val_start + int(round(n_total * VAL_FRAC))
        test_start = val_end + embargo
        if test_start + seq_len + horizon + 1 > n_total:
            raise ValueError(
                f"Not enough samples ({n_total}) for protocol splits with seq_len={seq_len}, horizon={horizon}"
            )
        splits = StudySplits(
            n_total=n_total,
            seq_len=seq_len,
            horizon=horizon,
            train_end=train_end,
            val_start=val_start,
            val_end=val_end,
            test_start=test_start,
        )

    for gap in (splits.val_start - splits.train_end, splits.test_start - splits.val_end):
        if gap < embargo:
            raise ValueError(f"Embargo violation: boundary gap {gap} < sequence_length + horizon - 1 = {embargo}")
    return splits


# ── Data loading ─────────────────────────────────────────────────────────────


def load_clarknet_series(parquet_path: Path = CLARKNET_PARQUET, bucket_sec: int = FIXED_SAMPLE_INTERVAL) -> pd.Series:
    """Load the 15 s ClarkNet series in RPS (per-bucket mean of the 1 s counts).

    ``resample(...).sum().dropna()`` yields exactly 40,315 non-empty 15 s
    buckets over the 7-day span; dividing by the bucket length converts
    request counts to the RPS amplitude the predictor sees at serving time.
    """
    df = pd.read_parquet(parquet_path)
    counts = df["rps"].resample(f"{bucket_sec}s").sum().dropna()
    return counts / bucket_sec


def load_synthetic_series(seed: int = 42, duration_hours: int = 72) -> np.ndarray:
    """Synthetic arm: 72 h at 1-minute resolution, held across 15 s buckets.

    Uses ``generate_realistic_traffic`` (base_rps 100) with the module-level
    numpy RNG seeded so the arm is reproducible; each minute value is repeated
    over its four 15-second buckets to match the deployment sample interval.
    """
    from prediction.training.train_gru import generate_realistic_traffic

    np.random.seed(seed)
    df = generate_realistic_traffic(duration_hours=duration_hours)
    minute_values = df["total_requests"].to_numpy(dtype=np.float32)
    # Hold each minute's value across its four 15-second buckets.
    return np.repeat(minute_values, 4)


def _torch_device() -> str:
    """Device the study actually trains on (harness stays device-agnostic)."""
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


def load_archetype_series() -> dict[str, np.ndarray]:
    """Expand the four archetype k6 stage files into 15 s series (OOD check).

    Each 30 s stage target is held across two 15 s samples, mirroring the
    synthetic_archetypes.py expansion used to generate the replay traces.
    """
    series: dict[str, np.ndarray] = {}
    for name, path in ARCHETYPE_FILES.items():
        stages = json.loads(path.read_text())
        targets = [float(stage["target"]) for stage in stages for _ in range(2)]
        series[name] = np.array(targets, dtype=np.float32)
    return series


def manifest_scale_factor(manifest_path: Path = REPLAY_MANIFEST) -> float:
    return float(json.loads(Path(manifest_path).read_text())["scale_factor"])


# ── Selection (HPO on the validation portion only) ──────────────────────────


def _suggest_config(
    trial: optuna.Trial,
    cell: str,
    horizon: int,
    epochs: int,
    sequence_lengths: tuple[int, ...] = SEARCH_SEQUENCE_LENGTHS,
) -> GRUConfig:
    hidden_size = trial.suggest_categorical("hidden_size", [64, 128, 256])
    num_layers = trial.suggest_int("num_layers", 1, 2)
    dropout = trial.suggest_float("dropout", 0.05, 0.3) if num_layers > 1 else 0.0
    head_dropout = trial.suggest_float("head_dropout", 0.0, 0.3)
    learning_rate = trial.suggest_float("learning_rate", 1e-4, 1e-3, log=True)
    sequence_length = trial.suggest_categorical("sequence_length", list(sequence_lengths))
    return GRUConfig(
        cell=cell,
        hidden_size=hidden_size,
        num_layers=num_layers,
        dropout=dropout,
        head_dropout=head_dropout,
        learning_rate=learning_rate,
        sequence_length=sequence_length,
        prediction_horizon=horizon,
        sample_interval_sec=FIXED_SAMPLE_INTERVAL,
        epochs=epochs,
        early_stopping_patience=FIXED_PATIENCE,
        batch_size=FIXED_BATCH_SIZE,
    )


def _trial_json_callback(bundle_dir: Path | None, source: str, cell: str):
    """Flush each completed trial to its own JSON before the next starts."""

    def callback(study: optuna.Study, trial: optuna.trial.FrozenTrial) -> None:
        if bundle_dir is None:
            return
        trial_dir = Path(bundle_dir) / "trials" / f"{source}_{cell}"
        trial_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "source": source,
            "cell": cell,
            "number": trial.number,
            "params": dict(trial.params),
            "value": trial.value,
            "state": str(trial.state),
            "epochs_selected": trial.user_attrs.get("epochs_selected"),
            "objective_detail": trial.user_attrs.get("objective_detail"),
        }
        (trial_dir / f"trial_{trial.number}.json").write_text(json.dumps(payload, indent=2))

    return callback


def _update_metrics_partial(partial_path: Path, record: dict[str, Any], source: str, cell: str) -> None:
    """Roll every completed refit record into metrics_partial.json."""
    partial: dict[str, Any] = {"records": []}
    if partial_path.exists():
        try:
            partial = json.loads(partial_path.read_text())
        except json.JSONDecodeError:
            partial = {"records": []}
    entry = {
        "source": source,
        "cell": cell,
        "seed": record["seed"],
        "rmse": record["overall"]["rmse"],
        "mae": record["overall"]["mae"],
        "skill_vs_persistence": record["overall"]["skill_vs_persistence"],
        "coverage": record["per_horizon"]["upper_envelope_coverage"],
        "artifact": record["artifact"],
        "artifact_sha256": record["artifact_sha256"],
    }
    partial["records"] = [
        r
        for r in partial.get("records", [])
        if not (r["source"] == source and r["cell"] == cell and r["seed"] == record["seed"])
    ]
    partial["records"].append(entry)
    partial["updated"] = datetime.now().isoformat(timespec="seconds")
    partial_path.write_text(json.dumps(partial, indent=2))


def selection_hpo(
    cell: str,
    values: np.ndarray,
    splits: StudySplits,
    horizon: int,
    n_trials: int,
    seed: int,
    bundle_dir: Path | None = None,
    source: str = "",
    sequence_lengths: tuple[int, ...] = SEARCH_SEQUENCE_LENGTHS,
) -> dict[str, Any]:
    """Select hyperparameters and the epoch budget on the validation portion.

    Each trial trains on ``values[:train_end]`` (scaler fitted there only,
    early stopping against the protocol validation slice) and is scored by
    the predeclared objective on the validation slice. Never touches the
    test portion.

    When *bundle_dir* is given, the study is persisted to
    ``<bundle_dir>/study.db`` (``load_if_exists=True``) so a process death
    resumes instead of repeating finished trials; every completed trial is
    also flushed to ``<bundle_dir>/trials/<source>_<cell>/trial_<n>.json``
    before the next trial starts.
    """
    storage_url = None
    if bundle_dir is not None:
        storage_url = f"sqlite:///{Path(bundle_dir) / 'study.db'}"
    storage = (
        optuna.storages.RDBStorage(url=storage_url, engine_kwargs={"connect_args": {"timeout": 30}})
        if storage_url
        else None
    )
    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=seed),
        storage=storage,
        study_name=f"gru_study_{source}_{cell}_h{horizon}",
        load_if_exists=True,
    )
    full_df = pd.DataFrame({"total_requests": values})
    val_values = values[splits.val_start : splits.val_end]

    def objective(trial: optuna.Trial) -> float:
        config = _suggest_config(trial, cell, horizon, FIXED_EPOCHS, sequence_lengths)
        _set_deterministic(seed)
        predictor = GRUPredictor(config=config)
        metrics = predictor.train(
            full_df,
            train_end=splits.train_end,
            val_start=splits.val_start,
            val_end=splits.val_end,
        )
        preds, targets, last_inputs = evaluate_on_values(predictor, val_values)
        obj, detail = compute_objective(preds, targets, last_inputs, horizon)
        trial.set_user_attr("objective_detail", detail)
        trial.set_user_attr("epochs_selected", int(metrics.get("best_epoch", FIXED_EPOCHS - 1)) + 1)
        return obj

    n_done = sum(1 for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE)
    remaining = n_trials - n_done
    if remaining > 0:
        study.optimize(
            objective,
            n_trials=remaining,
            show_progress_bar=False,
            callbacks=[_trial_json_callback(bundle_dir, source, cell)] if bundle_dir is not None else [],
        )
    else:
        logger.info(
            "study_selection_resumed",
            source=source,
            cell=cell,
            completed=n_done,
            requested=n_trials,
        )
    best = study.best_trial
    return {
        "best_trial": best.number,
        "best_params": dict(best.params),
        "best_objective": float(best.value) if best.value is not None else float("inf"),
        "epochs_selected": int(best.user_attrs.get("epochs_selected", FIXED_EPOCHS)),
        "trials": [
            {
                "number": t.number,
                "params": dict(t.params),
                "value": t.value if t.value is not None else float("inf"),
                "state": str(t.state),
                "epochs_selected": t.user_attrs.get("epochs_selected"),
            }
            for t in study.trials
        ],
    }


# ── Frozen refit and single-shot test evaluation ─────────────────────────────


def _final_config(cell: str, params: dict[str, Any], horizon: int, epochs: int, patience: int) -> GRUConfig:
    return GRUConfig(
        cell=cell,
        hidden_size=int(params["hidden_size"]),
        num_layers=int(params["num_layers"]),
        dropout=float(params.get("dropout", 0.0)),
        head_dropout=float(params["head_dropout"]),
        learning_rate=float(params["learning_rate"]),
        sequence_length=int(params["sequence_length"]),
        prediction_horizon=horizon,
        sample_interval_sec=FIXED_SAMPLE_INTERVAL,
        epochs=epochs,
        early_stopping_patience=patience,
        batch_size=FIXED_BATCH_SIZE,
    )


def refit_and_evaluate(
    cell: str,
    params: dict[str, Any],
    epochs_selected: int,
    values: np.ndarray,
    splits: StudySplits,
    horizon: int,
    seed: int,
    artifact_path: Path,
    season: int,
    n_rolling_blocks: int,
    archetype_series: dict[str, np.ndarray] | None = None,
) -> dict[str, Any]:
    """Refit on train+validation at the frozen budget, evaluate test once."""
    _set_deterministic(seed)
    full_df = pd.DataFrame({"total_requests": values})

    selection_predictor = GRUPredictor(config=_final_config(cell, params, horizon, FIXED_EPOCHS, FIXED_PATIENCE))
    selection_metrics = selection_predictor.train(
        full_df,
        train_end=splits.train_end,
        val_start=splits.val_start,
        val_end=splits.val_end,
    )

    final_predictor = GRUPredictor(
        config=_final_config(cell, params, horizon, epochs_selected, patience=epochs_selected + 1)
    )
    final_predictor.train(full_df, val_ratio=0.0, train_end=splits.val_end)
    # Upper envelope and error estimate come from the selection fit's
    # validation residuals/metrics: the final refit has no validation of its
    # own (val_ratio=0.0), so carrying them over keeps the artifact's
    # rmse/mae populated without ever reading the test region.
    final_predictor.upper_offsets = selection_predictor.upper_offsets
    final_predictor.val_coverage = selection_predictor.val_coverage
    final_predictor.rmse = selection_predictor.rmse
    final_predictor.mae = selection_predictor.mae

    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    final_predictor.save_model(artifact_path)

    test_values = values[splits.test_start :]
    seq_len = int(params["sequence_length"])

    preds, targets, last_inputs = evaluate_on_values(final_predictor, test_values)
    per_horizon = _per_horizon_metrics(preds, targets, last_inputs, final_predictor.upper_offsets)

    baselines: dict[str, dict[str, Any] | None] = {
        "persistence": None,
        "linear_trend": None,
        "seasonal_naive": None,
    }
    seasonal_unavailable: str | None = None
    for name, fn in (
        ("persistence", persistence_baseline),
        ("linear_trend", linear_trend_baseline),
    ):
        b_preds, _, b_last = fn(test_values, seq_len, horizon)
        _, b_detail = compute_objective(b_preds, targets, b_last, horizon)
        b_rmse_per_h = [float(np.sqrt(np.mean((targets[:, h] - b_preds[:, h]) ** 2))) for h in range(horizon)]
        baselines[name] = {
            "rmse": float(np.sqrt(np.mean((targets - b_preds) ** 2))),
            "mae": float(np.mean(np.abs(targets - b_preds))),
            "rmse_per_horizon": b_rmse_per_h,
            "mean_norm_rmse": b_detail["mean_norm_rmse"],
        }

    if splits.test_start >= season:
        seas_preds, _, seas_last = seasonal_naive_baseline(values, seq_len, horizon, season, splits.test_start)
        _, seas_detail = compute_objective(seas_preds, targets, seas_last, horizon)
        seas_rmse_per_h = [float(np.sqrt(np.mean((targets[:, h] - seas_preds[:, h]) ** 2))) for h in range(horizon)]
        baselines["seasonal_naive"] = {
            "rmse": float(np.sqrt(np.mean((targets - seas_preds) ** 2))),
            "mae": float(np.mean(np.abs(targets - seas_preds))),
            "rmse_per_horizon": seas_rmse_per_h,
            "mean_norm_rmse": seas_detail["mean_norm_rmse"],
        }
    else:
        seasonal_unavailable = (
            f"test_start ({splits.test_start}) < season ({season}): not enough series history "
            "before the evaluation region"
        )
        logger.warning("seasonal_naive_unavailable", cell=cell, reason=seasonal_unavailable)

    for name, detail in baselines.items():
        if detail is None:
            continue
        model_rmse_per_h = per_horizon["rmse"]
        per_horizon[f"skill_vs_{name}"] = [
            1.0 - model_rmse_per_h[h] / detail["rmse_per_horizon"][h] if detail["rmse_per_horizon"][h] > 0 else 0.0
            for h in range(horizon)
        ]

    overall_rmse = float(np.sqrt(np.mean((targets - preds) ** 2)))
    pers_detail = baselines["persistence"]
    overall_skill = 1.0 - overall_rmse / pers_detail["rmse"] if pers_detail and pers_detail["rmse"] > 0 else 0.0

    rolling = rolling_origin_evaluation(final_predictor, test_values, seq_len, horizon, n_rolling_blocks)

    archetype_rmse: dict[str, float] = {}
    for name, arch_values in (archetype_series or {}).items():
        if len(arch_values) < seq_len + horizon:
            continue
        a_preds, a_targets, _ = evaluate_on_values(final_predictor, arch_values)
        archetype_rmse[name] = float(np.sqrt(np.mean((a_targets - a_preds) ** 2)))

    return {
        "seed": seed,
        "cell": cell,
        "params": dict(params),
        "epochs_selected": epochs_selected,
        "selection_val_rmse": selection_metrics.get("val_rmse"),
        "artifact": str(artifact_path),
        "artifact_sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
        "overall": {
            "rmse": overall_rmse,
            "mae": float(np.mean(np.abs(targets - preds))),
            "nrmse": overall_rmse / float(np.mean(targets)),
            "skill_vs_persistence": overall_skill,
        },
        "per_horizon": per_horizon,
        "baselines": baselines,
        "seasonal_naive_unavailable": seasonal_unavailable,
        "rolling_origin": rolling,
        "archetype_rmse": archetype_rmse,
        "scaler_mean": final_predictor.scaler_mean,
        "scaler_std": final_predictor.scaler_std,
    }


def _per_horizon_metrics(
    preds: np.ndarray,
    targets: np.ndarray,
    last_inputs: np.ndarray,
    upper_offsets: np.ndarray,
) -> dict[str, Any]:
    """Per-horizon RMSE/MAE/nRMSE, rising-target under-prediction, coverage."""
    horizon = targets.shape[1]
    residuals = targets - preds
    rmse: list[float] = []
    mae: list[float] = []
    nrmse: list[float] = []
    underpred_mean: list[float] = []
    underpred_p90: list[float] = []
    for h in range(horizon):
        target_h = targets[:, h]
        mean_target_h = float(np.mean(target_h))
        rmse_h = float(np.sqrt(np.mean(residuals[:, h] ** 2)))
        rmse.append(rmse_h)
        mae.append(float(np.mean(np.abs(residuals[:, h]))))
        nrmse.append(rmse_h / mean_target_h if mean_target_h > 0 else rmse_h)
        rising = target_h > last_inputs
        if rising.sum() > 0:
            res_rising = residuals[rising, h]
            underpred_mean.append(float(np.mean(res_rising)))
            underpred_p90.append(float(np.percentile(res_rising, 90)))
        else:
            underpred_mean.append(0.0)
            underpred_p90.append(0.0)

    rising_mask = targets > last_inputs[:, np.newaxis]
    upper = preds + upper_offsets[np.newaxis, :]
    covered = targets <= upper
    n_rising = int(rising_mask.sum())
    coverage = float(covered[rising_mask].mean()) if n_rising > 0 else 1.0

    return {
        "rmse": rmse,
        "mae": mae,
        "nrmse": nrmse,
        "underpred_rising_mean": underpred_mean,
        "underpred_rising_p90": underpred_p90,
        "upper_envelope_coverage": coverage,
        "n_rising_targets": n_rising,
    }


# ── Aggregation, paired test, bundle ─────────────────────────────────────────


def _aggregate_seed_metrics(records: list[dict[str, Any]], horizon: int) -> dict[str, Any]:
    overall = {
        key: {
            "mean": float(np.mean([r["overall"][key] for r in records])),
            "std": float(np.std([r["overall"][key] for r in records], ddof=1)) if len(records) > 1 else 0.0,
            "per_seed": [r["overall"][key] for r in records],
        }
        for key in ("rmse", "mae", "nrmse", "skill_vs_persistence")
    }
    per_horizon_mean = {
        key: [float(np.mean([r["per_horizon"][key][h] for r in records])) for h in range(horizon)]
        for key in ("rmse", "mae", "nrmse", "underpred_rising_mean", "underpred_rising_p90")
    }
    per_horizon_std = {
        key: [
            float(np.std([r["per_horizon"][key][h] for r in records], ddof=1)) if len(records) > 1 else 0.0
            for h in range(horizon)
        ]
        for key in ("rmse", "mae", "underpred_rising_mean", "underpred_rising_p90")
    }
    return {
        "n_seeds": len(records),
        "overall": overall,
        "per_horizon_mean": per_horizon_mean,
        "per_horizon_std": per_horizon_std,
        "coverage_mean": float(np.mean([r["per_horizon"]["upper_envelope_coverage"] for r in records])),
        "archetype_rmse_mean": {
            name: float(np.mean([r["archetype_rmse"][name] for r in records if name in r["archetype_rmse"]]))
            for name in records[0]["archetype_rmse"]
        }
        if records and records[0]["archetype_rmse"]
        else {},
    }


def _paired_cell_test(gru_records: list[dict[str, Any]], lstm_records: list[dict[str, Any]]) -> dict[str, Any]:
    """Paired permutation test on per-seed holdout RMSE (LSTM vs GRU)."""
    baseline = [r["overall"]["rmse"] for r in gru_records]
    comparison = [r["overall"]["rmse"] for r in lstm_records]
    if len(baseline) != len(comparison) or len(baseline) < 2:
        return {"performed": False, "reason": "need ≥ 2 paired seeds per cell"}
    p = paired_permutation_test(baseline, comparison)
    ci_lo, ci_hi = paired_bootstrap_ci(baseline, comparison)
    d = cohens_d_paired(baseline, comparison)
    return {
        "performed": True,
        "baseline_cell": "gru",
        "comparison_cell": "lstm",
        "gru_rmse_per_seed": baseline,
        "lstm_rmse_per_seed": comparison,
        "mean_difference_lstm_minus_gru": float(np.mean(np.array(comparison) - np.array(baseline))),
        "bootstrap_ci95_lower": ci_lo,
        "bootstrap_ci95_upper": ci_hi,
        "permutation_p_one_sided": p,
        "cohens_d_paired": d,
    }


def _git_revision() -> dict[str, str]:
    try:
        head = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "-C", str(PROJECT_ROOT), "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        )
        return {"revision": head, "dirty": str(dirty).lower()}
    except (subprocess.CalledProcessError, OSError):
        return {"revision": "unknown", "dirty": "unknown"}


def _write_per_horizon_csvs(bundle: Path, arm_results: dict[str, Any], horizon: int) -> None:
    csv_dir = bundle / "per_horizon"
    csv_dir.mkdir(parents=True, exist_ok=True)
    for source, cells in arm_results.items():
        for cell, agg in cells.items():
            rows = {"horizon": list(range(1, horizon + 1))}
            for key, values in agg["per_horizon_mean"].items():
                rows[f"{key}_mean"] = values
            for key, values in agg["per_horizon_std"].items():
                rows[f"{key}_std"] = values
            baseline_keys = ("persistence", "linear_trend", "seasonal_naive")
            seed_records = agg["_records"]
            for bname in baseline_keys:
                b = seed_records[0]["baselines"].get(bname)
                rows[f"{bname}_rmse"] = b["rmse_per_horizon"] if b else [float("nan")] * horizon
            df = pd.DataFrame(rows)
            df.to_csv(csv_dir / f"{source}_{cell}.csv", index=False)

            rolling_dir = bundle / "rolling_folds"
            rolling_dir.mkdir(parents=True, exist_ok=True)
            rolling_rows = []
            for fold in seed_records[0]["rolling_origin"]["folds"]:
                rmse_across_seeds = [r["rolling_origin"]["folds"][fold["block"]]["rmse"] for r in seed_records]
                rolling_rows.append(
                    {
                        "block": fold["block"],
                        "start_idx": fold["start_idx"],
                        "end_idx": fold["end_idx"],
                        "rmse_mean": float(np.mean(rmse_across_seeds)),
                        "rmse_std": float(np.std(rmse_across_seeds, ddof=1)) if len(rmse_across_seeds) > 1 else 0.0,
                    }
                )
            pd.DataFrame(rolling_rows).to_csv(rolling_dir / f"{source}_{cell}.csv", index=False)


def _write_report(bundle: Path, meta: dict[str, Any], arm_results: dict[str, Any], metrics: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GRU/LSTM leak-free study (horizon 9)")
    lines.append("")
    lines.append(f"Generated: {meta['created']}  ")
    lines.append(f"Git: `{meta['git']['revision']}` (dirty={meta['git']['dirty']})  ")
    lines.append(f"Seeds: {list(meta['seeds'])} — trials per cell: {meta['n_trials']}")
    lines.append("")
    lines.append("## Protocol")
    lines.append("")
    lines.append(
        "Chronological splits with embargo = sequence_length + horizon - 1 at every boundary. "
        "Selection (hyperparameters + epoch budget) on the validation portion only; refit on "
        "train+validation at the frozen budget; test evaluated once per seed."
    )
    lines.append("")
    for source, info in meta["data"].items():
        lines.append(f"### Data arm: {source}")
        lines.append("")
        lines.append(f"- Samples: {info['n_samples']}")
        lines.append(
            f"- Split indices: train_end={info['splits']['train_end']}, val_start={info['splits']['val_start']}, "
            f"val_end={info['splits']['val_end']}, test_start={info['splits']['test_start']}, "
            f"embargo={info['splits']['embargo']}"
        )
        if "scale_factor" in info:
            lines.append(
                f"- Replay scale factor: {info['scale_factor']} (series multiplied before splitting; "
                "scaler fitted on the amplified training portion only)"
            )
        if "derivation" in info:
            lines.append(f"- Derivation: {info['derivation']}")
        lines.append("")
    lines.append("## Holdout results (test portion, mean ± std across seeds)")
    lines.append("")
    for source, cells in arm_results.items():
        lines.append(f"### {source}")
        lines.append("")
        lines.append("| cell | RMSE | MAE | nRMSE | skill vs persistence | coverage |")
        lines.append("|---|---|---|---|---|---|")
        for cell, agg in cells.items():
            ov = agg["overall"]
            lines.append(
                f"| {cell} | {ov['rmse']['mean']:.3f} ± {ov['rmse']['std']:.3f} "
                f"| {ov['mae']['mean']:.3f} ± {ov['mae']['std']:.3f} "
                f"| {ov['nrmse']['mean']:.4f} ± {ov['nrmse']['std']:.4f} "
                f"| {ov['skill_vs_persistence']['mean']:.3f} ± {ov['skill_vs_persistence']['std']:.3f} "
                f"| {agg['coverage_mean']:.3f} |"
            )
        lines.append("")
        for cell, agg in cells.items():
            arch = agg["archetype_rmse_mean"]
            if arch:
                arch_str = ", ".join(f"{k}={v:.2f}" for k, v in arch.items())
                lines.append(f"- {cell} archetype RMSE (OOD check): {arch_str}")
            b = agg["_records"][0]["baselines"]
            baseline_bits = [
                f"persistence RMSE {b['persistence']['rmse']:.3f}",
                f"linear trend {b['linear_trend']['rmse']:.3f}",
            ]
            if b.get("seasonal_naive"):
                baseline_bits.append(f"seasonal naive {b['seasonal_naive']['rmse']:.3f}")
            unavailable = agg["_records"][0].get("seasonal_naive_unavailable")
            if unavailable:
                baseline_bits.append(f"seasonal naive skipped ({unavailable})")
            lines.append(f"- Baselines on identical windows: {', '.join(baseline_bits)}")
            ro = agg["_records"][0]["rolling_origin"]
            lines.append(
                f"- Rolling-origin over test ({ro['n_blocks']} blocks): RMSE {ro['rmse_mean']:.3f} ± {ro['rmse_std']:.3f}"
            )
        lines.append("")
    paired = metrics.get("paired_tests", {})
    for name, test in paired.items():
        lines.append(f"## Paired test ({name})")
        lines.append("")
        if test.get("performed"):
            lines.append(
                f"Per-seed RMSE — {test['baseline_cell']}: "
                f"{[round(v, 3) for v in test['gru_rmse_per_seed']]}; "
                f"{test['comparison_cell']}: {[round(v, 3) for v in test['lstm_rmse_per_seed']]}. "
                f"One-sided permutation p = {test['permutation_p_one_sided']:.4f}, "
                f"mean Δ(lstm−gru) = {test['mean_difference_lstm_minus_gru']:.3f}, "
                f"Cohen's d = {test['cohens_d_paired']:.3f}."
            )
        else:
            lines.append(f"Not performed: {test.get('reason')}")
        lines.append("")
    winner = metrics.get("winner")
    lines.append("## Winner")
    lines.append("")
    if winner:
        lines.append(
            f"`{winner['source']}/{winner['cell']}` (mean RMSE {winner['mean_rmse']:.3f}); "
            f"artifact `{winner['artifact']}` (sha256 `{winner['sha256'][:16]}…`). "
            "Promotion to data/models/gru_model.pt happens only with --promote."
        )
        lines.append(
            f"Winner selection: {winner['selection_criterion']} (seed chosen on val RMSE {winner.get('seed_selection_val_rmse')})"
        )
    else:
        lines.append("No winner (need both cells on the clarknet arm).")
    lines.append("")
    (bundle / "report.md").write_text("\n".join(lines))


# ── Promotion (off by default, never exercised by the study itself) ─────────


def promote_winner(winner_artifact: Path) -> dict[str, str]:
    """Back up the deployed artifact, then copy the winner into its place."""
    if not winner_artifact.exists():
        raise FileNotFoundError(winner_artifact)
    DEPLOYED_ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if DEPLOYED_ARTIFACT.exists():
        backup = DEPLOYED_ARTIFACT.with_name(f"{DEPLOYED_ARTIFACT.name}.bak-{datetime.now():%Y%m%dT%H%M%S}")
        shutil.copy2(DEPLOYED_ARTIFACT, backup)
    shutil.copy2(winner_artifact, DEPLOYED_ARTIFACT)
    return {"promoted_to": str(DEPLOYED_ARTIFACT), "backup": str(backup) if backup else ""}


# ── Main study runner ────────────────────────────────────────────────────────


def run_study(
    data_sources: tuple[str, ...] | list[str] = DEFAULT_DATA_SOURCES,
    cells: tuple[str, ...] | list[str] = DEFAULT_CELLS,
    seeds: tuple[int, ...] | list[int] = DEFAULT_SEEDS,
    n_trials: int = DEFAULT_TRIALS,
    horizon: int = DEFAULT_HORIZON,
    output_dir: str | Path | None = None,
    promote: bool = False,
    season: int = DEFAULT_SEASON,
    n_rolling_blocks: int = 5,
    window: int = 30,
) -> dict[str, Any]:
    """Run the leak-free multi-cell study and write the reviewable bundle.

    Args:
        data_sources: Subset of ``("clarknet", "synthetic")``; clarknet is the
            primary arm and the only producer of the deployment artifact.
        cells: Subset of ``("gru", "lstm")`` sharing one protocol and budget.
        seeds: Training/refit seeds; holdout metrics reported per seed and
            aggregated (mean ± std), with a paired test across cells.
        n_trials: Optuna budget per (source, cell) — identical for all cells.
        horizon: Prediction horizon (calibration default 9).
        output_dir: Bundle directory (default ``results/models/gru/study``).
        promote: Back up ``data/models/gru_model.pt`` and copy the winning
            clarknet artifact there. Off by default.
        season: Seasonal-naive period in 15 s samples (frozen default
            DEFAULT_SEASON = 5760, one day). Needs that much history before
            the test region; skipped with a recorded reason otherwise.
        n_rolling_blocks: Rolling-origin blocks over the test portion.
        window: Input-window length that defines the split derivation. 30
            keeps the frozen ClarkNet boundaries byte-identical; any other
            window derives boundaries with embargo = window + horizon - 1 at
            both gaps while preserving the train and validation spans, and
            restricts the selection search to that single window.
    Returns:
        Summary dict with the winner, bundle path, and per-arm aggregates.
    """

    if window < 1:
        raise ValueError(f"window must be positive, got {window}")
    for cell in cells:
        if cell not in ("gru", "lstm"):
            raise ValueError(f"Unknown cell {cell!r}; expected 'gru' or 'lstm'")
    for source in data_sources:
        if source not in ("clarknet", "synthetic"):
            raise ValueError(f"Unknown data source {source!r}; expected 'clarknet' or 'synthetic'")

    sequence_lengths: tuple[int, ...] = tuple(SEARCH_SEQUENCE_LENGTHS) if window == 30 else (window,)
    bundle = Path(output_dir) if output_dir else PROJECT_ROOT / "results" / "models" / "gru" / "study"
    bundle.mkdir(parents=True, exist_ok=True)

    archetype_series = load_archetype_series()
    git_info = _git_revision()

    arm_series: dict[str, np.ndarray] = {}
    arm_meta: dict[str, dict[str, Any]] = {}
    for source in data_sources:
        if source == "clarknet":
            series = load_clarknet_series()
            scale = manifest_scale_factor()
            values = (series.to_numpy(dtype=np.float32) * scale).astype(np.float32)
            splits = build_splits(len(values), seq_len=window, horizon=horizon, source=source)
            replay_start, replay_end = locate_replay_window(
                series, REPLAY_MANIFEST, splits.test_start, splits.embargo, FIXED_SAMPLE_INTERVAL
            )
            if replay_start < splits.test_start or replay_end >= len(values):
                raise ValueError(
                    f"Replay window ({replay_start}, {replay_end}) escapes the test portion "
                    f"(test_start={splits.test_start}, n_total={len(values)}) for window={window}"
                )
            arm_meta[source] = {
                "path": str(CLARKNET_PARQUET.relative_to(PROJECT_ROOT)),
                "n_samples": len(values),
                "scale_factor": scale,
                "amplitude": "series × scale_factor (RPS) before splitting; scaler on amplified train portion",
                "replay_window_idx": [replay_start, replay_end],
                "splits": splits.to_dict(),
            }
            logger.info("study_replay_window_ok", start=replay_start, end=replay_end, test_start=splits.test_start)
        else:
            values = load_synthetic_series()
            splits = build_splits(len(values), seq_len=window, horizon=horizon, source=source)
            arm_meta[source] = {
                "path": "prediction.training.train_gru.generate_realistic_traffic",
                "n_samples": len(values),
                "derivation": "seed 42, 72 h at 1-minute resolution (base_rps 100); each minute value "
                "held across its four 15 s buckets; splits proportional to the ClarkNet protocol "
                "fractions with the same embargo rule",
                "splits": splits.to_dict(),
            }
        arm_series[source] = values

    arm_results: dict[str, dict[str, dict[str, Any]]] = {}
    study_data: dict[str, Any] = {}
    for source, values in arm_series.items():
        arm_results[source] = {}
        study_data[source] = {}
        for cell in cells:
            logger.info("study_selection_start", source=source, cell=cell, n_trials=n_trials)
            selection = selection_hpo(
                cell,
                values,
                build_splits(len(values), window, horizon, source),
                horizon,
                n_trials,
                seeds[0],
                bundle_dir=bundle,
                source=source,
                sequence_lengths=sequence_lengths,
            )
            study_data[source][cell] = selection
            logger.info(
                "study_selection_done",
                source=source,
                cell=cell,
                best_objective=round(selection["best_objective"], 4),
                epochs_selected=selection["epochs_selected"],
            )

            records = []
            for seed in seeds:
                artifact_path = bundle / "artifacts" / f"{source}_{cell}_s{seed}.pt"
                splits = build_splits(len(values), int(selection["best_params"]["sequence_length"]), horizon, source)
                record = refit_and_evaluate(
                    cell=cell,
                    params=selection["best_params"],
                    epochs_selected=selection["epochs_selected"],
                    values=values,
                    splits=splits,
                    horizon=horizon,
                    seed=seed,
                    artifact_path=artifact_path,
                    season=season,
                    n_rolling_blocks=n_rolling_blocks,
                    archetype_series=archetype_series if source == "clarknet" else archetype_series,
                )
                records.append(record)
                _update_metrics_partial(bundle / "metrics_partial.json", record, source, cell)
                logger.info(
                    "study_seed_done",
                    source=source,
                    cell=cell,
                    seed=seed,
                    rmse=round(record["overall"]["rmse"], 3),
                )

            arm_results[source][cell] = {
                **_aggregate_seed_metrics(records, horizon),
                "_records": records,
                "_selection": selection,
            }

    paired_tests: dict[str, Any] = {}
    for source, cells_results in arm_results.items():
        if "gru" in cells_results and "lstm" in cells_results:
            test = _paired_cell_test(cells_results["gru"]["_records"], cells_results["lstm"]["_records"])
            paired_tests[f"{source}:gru_vs_lstm"] = test

    winner = None
    winner_selection_criterion = (
        "cell: minimum selection best_objective (validation); "
        "seed: minimum selection-fit validation RMSE, ties broken by lowest seed; "
        "holdout never used for selection"
    )
    if "clarknet" in arm_results and arm_results["clarknet"]:
        best_cell = min(
            arm_results["clarknet"],
            key=lambda c: (
                arm_results["clarknet"][c]["_selection"]["best_objective"]
                if arm_results["clarknet"][c]["_selection"]["best_objective"] is not None
                else float("inf")
            ),
        )
        best_agg = arm_results["clarknet"][best_cell]
        best_record = min(
            best_agg["_records"],
            key=lambda r: (r["selection_val_rmse"] if r["selection_val_rmse"] is not None else float("inf"), r["seed"]),
        )
        winner = {
            "source": "clarknet",
            "cell": best_cell,
            "seed": best_record["seed"],
            "seed_selection_val_rmse": best_record["selection_val_rmse"],
            "mean_rmse": best_agg["overall"]["rmse"]["mean"],
            "artifact": best_record["artifact"],
            "sha256": best_record["artifact_sha256"],
            "selection_criterion": winner_selection_criterion,
        }

    metrics_json: dict[str, Any] = {"arms": {}, "paired_tests": paired_tests, "winner": winner}
    for source, cells_results in arm_results.items():
        metrics_json["arms"][source] = {}
        for cell, agg in cells_results.items():
            metrics_json["arms"][source][cell] = {k: v for k, v in agg.items() if not k.startswith("_")}

    meta = {
        "bundle_schema_version": 2,
        "study": "gru-leakfree-horizon9",
        "created": datetime.now().isoformat(timespec="seconds"),
        "git": git_info,
        "device": _torch_device(),
        "horizon": horizon,
        "window": window,
        "sequence_lengths_searched": list(sequence_lengths),
        "boundary_rule": (
            "frozen ClarkNet literals when window + horizon - 1 fits the 38-sample gaps; "
            "otherwise derived with embargo = window + horizon - 1 at both gaps while "
            "preserving the train (22500) and validation (3666) spans; replay window must "
            "stay inside the test portion"
        ),
        "embargo_rule": "sequence_length + horizon - 1 at every boundary",
        "seeds": list(seeds),
        "cells": list(cells),
        "n_trials": n_trials,
        "seasonal_naive_season": season,
        "rolling_blocks": n_rolling_blocks,
        "data": arm_meta,
        "winner": winner,
        "winner_selection_criterion": winner_selection_criterion,
        "artifacts": {
            record["artifact"].split("/")[-1]: record["artifact_sha256"]
            for cells_results in arm_results.values()
            for agg in cells_results.values()
            for record in agg["_records"]
        },
    }

    (bundle / "meta.yaml").write_text(yaml.safe_dump(meta, sort_keys=False))
    (bundle / "study.json").write_text(json.dumps(study_data, indent=2))
    (bundle / "metrics.json").write_text(json.dumps(metrics_json, indent=2))
    _write_report(bundle, meta, arm_results, metrics_json)

    promoted = promote_winner(Path(winner["artifact"])) if promote and winner else None

    logger.info(
        "study_complete",
        bundle=str(bundle),
        winner=None if winner is None else f"{winner['source']}/{winner['cell']}",
        promoted=bool(promoted),
    )
    return {
        "bundle": str(bundle),
        "winner": winner,
        "promoted": promoted,
        "paired_tests": paired_tests,
        "arms": {s: {c: a["overall"]["rmse"]["mean"] for c, a in cells.items()} for s, cells in arm_results.items()},
    }
