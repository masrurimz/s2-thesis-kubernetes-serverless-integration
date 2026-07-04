#!/usr/bin/env python3
"""
Train and evaluate GRU model on real ClarkNet/Calgary HTTP traces.

Thesis requirement: retrain GRU on real traces instead of synthetic data.
Reports RMSE, MAE (as % of mean), and MAPE.

Trains at multiple temporal resolutions (1-min, 5-min, 10-min) to find
the best granularity for each dataset.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import cast

import numpy as np
import pandas as pd

from prediction.gru_predictor import GRUPredictor, GRUConfig


DATA_DIR = Path(__file__).parent.parent / "data" / "processed"
RESULTS_DIR = Path(__file__).parent.parent / "results" / "models" / "gru" / "2026-02-13_training-clarknet-calgary"
MODEL_DIR = Path(__file__).parent.parent / "controller" / "data" / "models"


def load_clarknet(resample: str = "1min") -> pd.DataFrame:
    """Load ClarkNet trace resampled to given interval."""
    df = pd.read_parquet(DATA_DIR / "clarknet_real_rps.parquet")
    df = df.resample(resample).sum().fillna(0)
    df.columns = ["total_requests"]
    return df


def load_calgary(resample: str = "1min") -> pd.DataFrame:
    """Load Calgary trace resampled to given interval."""
    df = pd.read_parquet(DATA_DIR / "calgary_real_rps.parquet")
    df = df.resample(resample).sum().fillna(0)
    df.columns = ["total_requests"]
    return df


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, dataset_name: str) -> dict:
    """Compute RMSE, MAE, MAE%, and MAPE."""
    errors = y_pred - y_true
    abs_errors = np.abs(errors)
    mean_actual = np.mean(y_true)

    rmse = float(np.sqrt(np.mean(errors**2)))
    mae = float(np.mean(abs_errors))
    mae_pct = (mae / mean_actual) * 100 if mean_actual > 0 else float("inf")

    # MAPE: skip zeros in denominator
    nonzero_mask = y_true > 0
    if nonzero_mask.sum() > 0:
        mape = float(np.mean(np.abs(errors[nonzero_mask] / y_true[nonzero_mask])) * 100)
    else:
        mape = float("inf")

    rmse_pct = (rmse / mean_actual) * 100 if mean_actual > 0 else float("inf")

    return {
        "dataset": dataset_name,
        "rmse": round(rmse, 4),
        "rmse_pct": round(rmse_pct, 2),
        "mae": round(mae, 4),
        "mae_pct": round(mae_pct, 2),
        "mape": round(mape, 2),
        "mean_actual": round(mean_actual, 2),
        "n_samples": int(len(y_true)),
    }


def evaluate_on_test(
    predictor: GRUPredictor,
    test_values: np.ndarray,
    dataset_name: str,
) -> dict:
    """Run GRU predictions on test set and compute metrics."""
    seq_len = predictor.config.sequence_length
    preds = []
    for i in range(seq_len, len(test_values)):
        result = predictor.predict(test_values[i - seq_len : i])
        preds.append(result["predicted_requests"])

    y_true = test_values[seq_len:]
    y_pred = np.array(preds)
    return compute_metrics(y_true, y_pred, dataset_name)


def train_and_evaluate(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    dataset_name: str,
    config: GRUConfig,
) -> tuple[GRUPredictor, dict, dict]:
    """Train GRU on train_df, evaluate on test_df."""
    print(f"\n{'=' * 70}")
    print(f"Training on: {dataset_name}")
    print(f"{'=' * 70}")
    print(f"  Train samples: {len(train_df)}")
    print(f"  Test samples:  {len(test_df)}")
    print(f"  Train mean:    {train_df['total_requests'].mean():.2f}")
    print(f"  Test mean:     {test_df['total_requests'].mean():.2f}")

    predictor = GRUPredictor(config)
    train_metrics = predictor.train(train_df)
    print(f"  Val RMSE:      {train_metrics['val_rmse']:.4f}")
    print(f"  Val RMSE%:     {train_metrics['val_rmse_percent']:.2f}%")
    print(f"  Epochs:        {train_metrics['epochs_trained']}")

    test_metrics = evaluate_on_test(predictor, test_df["total_requests"].values.astype(np.float32), dataset_name)
    print("\n  Test Results:")
    print(f"    RMSE:   {test_metrics['rmse']:.4f} ({test_metrics['rmse_pct']:.2f}%)")
    print(f"    MAE:    {test_metrics['mae']:.4f} ({test_metrics['mae_pct']:.2f}%)")
    print(f"    MAPE:   {test_metrics['mape']:.2f}%")

    return predictor, train_metrics, test_metrics


def main():
    np.random.seed(42)

    print("=" * 70)
    print("GRU Training on Real HTTP Traces (ClarkNet + Calgary)")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    all_results = {}
    best_predictor = None
    best_rmse_pct = float("inf")

    # ============================================================
    # ClarkNet at multiple resolutions
    # ============================================================
    resolutions = [
        ("1min", 60, "ClarkNet 1-min"),
        ("5min", 60, "ClarkNet 5-min"),
        ("10min", 36, "ClarkNet 10-min"),
    ]

    for resample, seq_len, label in resolutions:
        print(f"\n--- {label} ---")
        df = load_clarknet(resample)

        n = len(df)
        val_end = int(n * 0.85)
        train = df.iloc[:val_end]
        test = df.iloc[val_end:]

        config = GRUConfig(
            hidden_size=128,
            num_layers=2,
            dropout=0.2,
            sequence_length=seq_len,
            prediction_horizon=1,
            learning_rate=0.0005,
            batch_size=32,
            epochs=200,
            early_stopping_patience=25,
        )

        predictor, train_m, test_m = train_and_evaluate(train, test, label, config)
        key = f"clarknet_{resample}"
        all_results[key] = {
            "train": train_m,
            "test": test_m,
            "config": config.__dict__,
            "resample": resample,
            "train_samples": len(train),
            "test_samples": len(test),
        }

        if test_m["rmse_pct"] < best_rmse_pct:
            best_rmse_pct = test_m["rmse_pct"]
            best_predictor = predictor
            best_label = label

    # ============================================================
    # Calgary at multiple resolutions
    # ============================================================
    cal_resolutions = [
        ("1min", 60, "Calgary 1-min (14d)"),
        ("5min", 60, "Calgary 5-min (30d)"),
    ]

    for resample, seq_len, label in cal_resolutions:
        print(f"\n--- {label} ---")
        df = load_calgary(resample)

        if "14d" in label:
            df = df.iloc[: 14 * 24 * 60]
        else:
            df = df.iloc[-30 * 24 * 12 :]

        n = len(df)
        val_end = int(n * 0.85)
        train = df.iloc[:val_end]
        test = df.iloc[val_end:]

        config = GRUConfig(
            hidden_size=128,
            num_layers=2,
            dropout=0.2,
            sequence_length=seq_len,
            prediction_horizon=1,
            learning_rate=0.0005,
            batch_size=32,
            epochs=200,
            early_stopping_patience=25,
        )

        predictor, train_m, test_m = train_and_evaluate(train, test, label, config)
        key = f"calgary_{resample}"
        all_results[key] = {
            "train": train_m,
            "test": test_m,
            "config": config.__dict__,
            "resample": resample,
            "train_samples": len(train),
            "test_samples": len(test),
        }

    # ---- Save best model ----
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_DIR / "gru_model_real.pt"
    if best_predictor is None:
        raise RuntimeError("No best predictor found during training")
    best_predictor.save_model(model_path)
    print(f"\nBest model ({best_label}) saved: {model_path}")

    # ---- Save results ----
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    raw_dir = RESULTS_DIR / "raw"
    raw_dir.mkdir(exist_ok=True)

    results_json = {
        "date": datetime.now().isoformat(),
        "best_model": best_label,
        "results": all_results,
    }

    with open(raw_dir / "training_results.json", "w") as f:
        json.dump(results_json, f, indent=2, default=str)

    # ---- Print summary ----
    print("\n" + "=" * 70)
    print("SUMMARY — All Configurations")
    print("=" * 70)
    print()
    fmt = "{:<28} {:>8} {:>8} {:>8} {:>8} {:>8} {:>6}"
    print(fmt.format("Dataset", "RMSE", "RMSE%", "MAE", "MAE%", "MAPE", "N"))
    print("-" * 78)
    for key, r in all_results.items():
        m = cast(dict, r["test"])
        print(
            fmt.format(
                m["dataset"],
                f"{m['rmse']:.2f}",
                f"{m['rmse_pct']:.1f}%",
                f"{m['mae']:.2f}",
                f"{m['mae_pct']:.1f}%",
                f"{m['mape']:.1f}%",
                str(m["n_samples"]),
            )
        )

    print()
    print(f"Best model: {best_label} (RMSE% = {best_rmse_pct:.2f}%)")
    print("Synthetic baseline: RMSE% = 6.01%, MAE% = 4.91%")
    print("Target thresholds: RMSE% < 10%, MAE% < 5%")

    return all_results


if __name__ == "__main__":
    main()
