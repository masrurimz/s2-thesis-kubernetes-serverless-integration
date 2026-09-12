#!/usr/bin/env python3
"""Committed provenance for the GRU-predictor analysis numbers.

Subcommands (all read-only on stdout; ``--json <path>`` is the only writer):

- ``holdout --artifact <path>``: score one artifact on the held-out test region
  against persistence, linear trend, seasonal naive, and an OLS autoregression
  on the same input window.
- ``ensemble --bundle <dir>``: average the seeds' predictions and score them
  the same way.
- ``paired-cells --bundle-a <dir> --bundle-b <dir>``: paired GRU-vs-LSTM
  statistics (one-sided permutation p, bootstrap CI, paired Cohen's d) from
  each bundle's ``metrics_partial.json``.
- ``leak-sensitivity``: leak-versus-clean validation measurement on a
  9000-sample development slice.

Conventions copied from the throwaway scripts this file replaces
(``/tmp/score_new_model.py``, ``/tmp/score_with_ols.py``, ``/tmp/score_ensemble.py``,
``/tmp/leak_sensitivity.py``) and from the study harness they reused, so the
numbers are identical:

- series = 15 s ClarkNet RPS × replay manifest scale factor, float64;
- windows at seq 30 / horizon 9 on the frozen test region;
- GRU forward: predictor z-score (float32) → network → denormalize, single-shot;
- persistence, linear trend, and seasonal naive come from ``gru_hpo`` (the
  study's own baselines, scored on identical windows);
- the OLS autoregression is fitted on ``values[:test_start]`` — everything
  before the test region, which includes the embargo gap (the throwaway
  convention from ``/tmp/score_with_ols.py``);
- ensemble: each seed normalized with its own artifact scaler, then averaged;
- leak arm of ``leak-sensitivity``: scaler on the whole slice and windows built
  across the split — the historical behavior this measurement quantifies.

Runs on CPU with the GPU hidden via ``ROCR_VISIBLE_DEVICES`` and friends.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

# Hide every GPU before torch is imported anywhere in this process.
for _gpu_var in ("ROCR_VISIBLE_DEVICES", "HIP_VISIBLE_DEVICES", "CUDA_VISIBLE_DEVICES"):
    os.environ.setdefault(_gpu_var, "")

import numpy as np
import pandas as pd
import torch

from experiment.tuning.gru_hpo import linear_trend_baseline, persistence_baseline, seasonal_naive_baseline
from experiment.tuning.gru_study import (
    DEFAULT_SEASON,
    build_splits,
    load_clarknet_series,
    manifest_scale_factor,
)
from prediction.gru_predictor import GRUConfig, GRUNetwork, GRUPredictor
from shared.stats import cohens_d_paired, paired_bootstrap_ci, paired_permutation_test

SEQ = 30
HORIZON = 9
SEEDS = (42, 43, 44)
DEV_SAMPLES = 9000
LEAK_EPOCHS = 25
LEAK_TRAIN_END = 7000


def _series() -> np.ndarray:
    return (load_clarknet_series() * manifest_scale_factor()).values.astype(np.float64)


def _windows(test: np.ndarray, seq_len: int = SEQ, horizon: int = HORIZON) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(inputs, targets, last inputs) for every window in the test region."""
    n = len(test) - seq_len - horizon + 1
    b = np.arange(n)
    X = test[b[:, None] + np.arange(seq_len)[None, :]]
    Y = test[b[:, None] + np.arange(seq_len, seq_len + horizon)[None, :]]
    last = test[b + seq_len - 1]
    return X, Y, last


def _gru_predict(predictor: GRUPredictor, X_norm: np.ndarray) -> np.ndarray:
    assert isinstance(predictor.model, torch.nn.Module), "artifact has no torch network"
    predictor.model.eval()
    with torch.no_grad():
        out = predictor.model(torch.FloatTensor(X_norm[:, :, None])).numpy()
    return predictor._denormalize(out)


def _ols_ar(values: np.ndarray, test_start: int) -> np.ndarray:
    """OLS AR(30): fitted on everything before the test region, scored on its windows."""
    train_region = values[:test_start]
    n_tr = len(train_region) - SEQ - HORIZON + 1
    b = np.arange(n_tr)
    x_a = np.column_stack([np.ones(n_tr), train_region[b[:, None] + np.arange(SEQ)[None, :]]])
    y_a = train_region[b[:, None] + np.arange(SEQ, SEQ + HORIZON)[None, :]]
    coef, *_ = np.linalg.lstsq(x_a, y_a, rcond=None)

    test = values[test_start:]
    X, _, _ = _windows(test)
    return np.column_stack([np.ones(len(X)), X]) @ coef


def _load_predictor(artifact: Path) -> GRUPredictor:
    predictor = GRUPredictor()
    assert predictor.load_model(artifact), f"artifact failed to load: {artifact}"
    return predictor


def _score_rows(candidates: list[tuple[str, np.ndarray]], Y: np.ndarray, last: np.ndarray) -> list[dict[str, Any]]:
    by_name = {name: float(np.sqrt(np.mean((Y - p) ** 2))) for name, p in candidates}
    ols_rmse = by_name["ols_ar30"]
    pers_rmse = by_name["persistence"]
    rows: list[dict[str, Any]] = []
    for name, _ in candidates:
        rmse = by_name[name]
        rows.append(
            {
                "model": name,
                "rmse": round(rmse, 4),
                "mae": round(float(np.mean(np.abs(Y - dict(candidates)[name]))), 4),
                "skill_vs_persistence": round(1 - rmse / pers_rmse, 4) if pers_rmse > 0 else 0.0,
                "skill_vs_ols": round(1 - rmse / ols_rmse, 4) if ols_rmse > 0 else 0.0,
            }
        )
    return rows


def _emit(payload: dict[str, Any], table: pd.DataFrame, json_path: Path | None) -> None:
    print(table.to_string(index=False))
    print(json.dumps(payload, indent=2))
    if json_path is not None:
        json_path.write_text(json.dumps(payload, indent=2, default=str))


def cmd_holdout(args: argparse.Namespace) -> None:
    values = _series()
    splits = build_splits(len(values), SEQ, HORIZON, "clarknet")
    test = values[splits.test_start :]
    X, Y, last = _windows(test)

    predictor = _load_predictor(Path(args.artifact))
    test_norm = predictor._normalize(test.astype(np.float32))
    X_norm = test_norm[np.arange(len(X))[:, None] + np.arange(SEQ)[None, :]]
    gru_pred = _gru_predict(predictor, X_norm)

    pers_pred, _, _ = persistence_baseline(test, SEQ, HORIZON)
    trend_pred, _, _ = linear_trend_baseline(test, SEQ, HORIZON)
    seas_pred, seas_targets, _ = seasonal_naive_baseline(values, SEQ, HORIZON, DEFAULT_SEASON, splits.test_start)
    assert np.array_equal(seas_targets, Y), "seasonal arm windows diverge"

    candidates = [
        ("gru", gru_pred),
        ("ols_ar30", _ols_ar(values, splits.test_start)),
        ("persistence", pers_pred),
        ("linear_trend", trend_pred),
        ("seasonal_naive", seas_pred),
    ]
    rows = _score_rows(candidates, Y, last)
    rising = Y > last[:, None]
    payload: dict[str, Any] = {
        "artifact": str(args.artifact),
        "test_start": int(splits.test_start),
        "windows": int(len(X)),
        "rising_fraction": round(float(rising.mean()), 4),
        "rows": rows,
    }
    _emit(payload, pd.DataFrame(rows), Path(args.json) if args.json else None)


def cmd_ensemble(args: argparse.Namespace) -> None:
    values = _series()
    splits = build_splits(len(values), SEQ, HORIZON, "clarknet")
    test = values[splits.test_start :]
    X, Y, last = _windows(test)

    preds: dict[int, np.ndarray] = {}
    for seed in SEEDS:
        artifact = Path(args.bundle) / "artifacts" / f"clarknet_gru_s{seed}.pt"
        predictor = _load_predictor(artifact)
        test_norm = predictor._normalize(test.astype(np.float32))
        X_norm = test_norm[np.arange(len(X))[:, None] + np.arange(SEQ)[None, :]]
        preds[seed] = _gru_predict(predictor, X_norm)
    ensemble = np.mean([preds[s] for s in SEEDS], axis=0)

    pers_pred, _, _ = persistence_baseline(test, SEQ, HORIZON)
    candidates = [(f"gru_s{s}", preds[s]) for s in SEEDS] + [
        ("gru_ensemble", ensemble),
        ("ols_ar30", _ols_ar(values, splits.test_start)),
        ("persistence", pers_pred),
    ]
    rows = _score_rows(candidates, Y, last)
    payload: dict[str, Any] = {"bundle": str(args.bundle), "seeds": list(SEEDS), "rows": rows}
    _emit(payload, pd.DataFrame(rows), Path(args.json) if args.json else None)


def _bundle_seed_rmse(bundle: Path) -> dict[int, float]:
    """Per-seed holdout RMSE from a bundle's metrics_partial.json (one cell per bundle)."""
    partial = json.loads((bundle / "metrics_partial.json").read_text())
    return {int(r["seed"]): float(r["rmse"]) for r in partial["records"]}


def cmd_paired_cells(args: argparse.Namespace) -> None:
    gru = _bundle_seed_rmse(Path(args.bundle_a))
    lstm = _bundle_seed_rmse(Path(args.bundle_b))
    seeds = sorted(set(gru) & set(lstm))
    assert seeds, "no matching seeds between bundles"
    gru_v = np.array([gru[s] for s in seeds], dtype=float)
    lstm_v = np.array([lstm[s] for s in seeds], dtype=float)

    # H0: mean(gru - lstm) >= 0 — a small p means gru below lstm.
    p_value = paired_permutation_test(lstm_v.tolist(), gru_v.tolist())
    ci_lo, ci_hi = paired_bootstrap_ci(gru_v.tolist(), lstm_v.tolist())
    rows = [
        {
            "seed": seed,
            "gru_rmse": round(float(g_rmse), 4),
            "lstm_rmse": round(float(l_rmse), 4),
            "diff_lstm_minus_gru": round(float(l_rmse - g_rmse), 4),
        }
        for seed, g_rmse, l_rmse in zip(seeds, gru_v, lstm_v, strict=True)
    ]
    payload: dict[str, Any] = {
        "bundle_a": str(args.bundle_a),
        "bundle_b": str(args.bundle_b),
        "seeds": seeds,
        "gru_mean": round(float(gru_v.mean()), 4),
        "lstm_mean": round(float(lstm_v.mean()), 4),
        "mean_difference_lstm_minus_gru": round(float((lstm_v - gru_v).mean()), 4),
        "cohens_d_paired": round(cohens_d_paired(gru_v.tolist(), lstm_v.tolist()), 4),
        "bootstrap_ci_diff": [round(ci_lo, 4), round(ci_hi, 4)],
        "permutation_p_one_sided_gru_lt_lstm": round(p_value, 4),
        "rows": rows,
    }
    _emit(payload, pd.DataFrame(rows), Path(args.json) if args.json else None)


def cmd_leak_sensitivity(args: argparse.Namespace) -> None:
    values = _series()[:DEV_SAMPLES]
    frame = pd.DataFrame({"total_requests": values})
    seed = 42
    config = GRUConfig(
        cell="gru",
        hidden_size=128,
        num_layers=1,
        sequence_length=SEQ,
        prediction_horizon=HORIZON,
        learning_rate=3.8e-4,
        batch_size=32,
        epochs=LEAK_EPOCHS,
        early_stopping_patience=LEAK_EPOCHS,
    )
    embargo = SEQ + HORIZON - 1
    val_start = LEAK_TRAIN_END + embargo

    # Clean arm: the fixed code — scaler on the training portion, windows per segment.
    clean = GRUPredictor(config)
    clean.train(frame, train_end=LEAK_TRAIN_END, val_start=val_start)
    assert clean.rmse is not None, "clean arm produced no validation rmse"
    clean_val_rmse = float(clean.rmse)
    clean_pct = round(clean_val_rmse / float(values[val_start:DEV_SAMPLES].mean()) * 100, 3)

    # Leaky arm: scaler on the whole slice and windows built across the split.
    leaky = GRUPredictor(config)
    leaky.scaler_mean = float(np.mean(values))
    leaky.scaler_std = float(np.std(values))
    norm = leaky._normalize(values)
    x_all, y_all = leaky._create_sequences(norm)
    cut = val_start
    x_tr, y_tr, x_va, y_va = x_all[:cut], y_all[:cut], x_all[cut:], y_all[cut:]

    torch.manual_seed(seed)
    np.random.seed(seed)
    leaky.model = GRUNetwork(leaky.config).to(leaky.device)
    opt = torch.optim.Adam(leaky.model.parameters(), lr=leaky.config.learning_rate)
    loss_fn = torch.nn.MSELoss()
    xt = torch.FloatTensor(x_tr[:, :, None]).to(leaky.device)
    yt = torch.FloatTensor(y_tr).to(leaky.device)
    xv = torch.FloatTensor(x_va[:, :, None]).to(leaky.device)
    yv = torch.FloatTensor(y_va).to(leaky.device)
    loader = torch.utils.data.DataLoader(torch.utils.data.TensorDataset(xt, yt), batch_size=32, shuffle=True)
    for _ in range(LEAK_EPOCHS):
        assert leaky.model is not None
        leaky.model.train()
        for bx, by in loader:
            opt.zero_grad()
            loss_fn(leaky.model(bx), by).backward()
            opt.step()
    assert leaky.model is not None
    leaky.model.eval()
    with torch.no_grad():
        val_pred_norm = leaky.model(xv).cpu().numpy()
    res = leaky._denormalize(yv.numpy()) - leaky._denormalize(val_pred_norm)
    leaky_rmse = float(np.sqrt(np.mean(res**2)))
    leaky_pct = round(leaky_rmse / float(np.mean(leaky._denormalize(yv.numpy()))) * 100, 3)

    payload: dict[str, Any] = {
        "dev_samples": DEV_SAMPLES,
        "train_end": LEAK_TRAIN_END,
        "val_start": val_start,
        "embargo_samples": embargo,
        "clean_val_rmse": round(clean_val_rmse, 3),
        "clean_val_rmse_pct": clean_pct,
        "leaky_val_rmse": round(leaky_rmse, 3),
        "leaky_val_rmse_pct": leaky_pct,
        "rmse_gain_pct_from_leak": round((clean_val_rmse - leaky_rmse) / clean_val_rmse * 100, 2),
        "scaler_mean_clean": round(float(clean.scaler_mean), 2),
        "scaler_mean_leaky": round(float(leaky.scaler_mean), 2),
    }
    table = pd.DataFrame(
        [
            {"arm": "clean", "val_rmse": payload["clean_val_rmse"], "val_rmse_pct": clean_pct},
            {"arm": "leaky", "val_rmse": payload["leaky_val_rmse"], "val_rmse_pct": leaky_pct},
        ]
    )
    _emit(payload, table, Path(args.json) if args.json else None)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    holdout = sub.add_parser("holdout", help="Score one artifact on the held-out test region")
    holdout.add_argument("--artifact", required=True)
    holdout.add_argument("--json", default=None)
    holdout.set_defaults(func=cmd_holdout)

    ensemble = sub.add_parser("ensemble", help="Score the seed-ensemble average")
    ensemble.add_argument("--bundle", required=True)
    ensemble.add_argument("--json", default=None)
    ensemble.set_defaults(func=cmd_ensemble)

    paired = sub.add_parser("paired-cells", help="Paired GRU-vs-LSTM statistics from two bundles")
    paired.add_argument("--bundle-a", required=True, help="Baseline cell bundle (gru)")
    paired.add_argument("--bundle-b", required=True, help="Comparison cell bundle (lstm)")
    paired.add_argument("--json", default=None)
    paired.set_defaults(func=cmd_paired_cells)

    leak = sub.add_parser("leak-sensitivity", help="Leak-versus-clean validation measurement")
    leak.add_argument("--json", default=None)
    leak.set_defaults(func=cmd_leak_sensitivity)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
