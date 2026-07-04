#!/usr/bin/env python3
"""
Model Comparison Script.

Compares Linear Regression against naive baselines.
Generates thesis-ready comparison table.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

from prediction.training.baselines.naive import NaivePredictor, SeasonalNaivePredictor
from prediction.training.baselines.moving_avg import MovingAveragePredictor, ExponentialMovingAveragePredictor
from prediction_engine.linear_model import TrafficPredictor  # archived module — legacy comparison only


def generate_synthetic_data(duration_hours: int = 24, base_rps: float = 100, noise_std: float = 10) -> pd.DataFrame:
    """Generate synthetic traffic with daily patterns."""
    samples_per_hour = 60
    total_samples = duration_hours * samples_per_hour

    base_time = datetime.now() - timedelta(hours=duration_hours)

    data = []
    for i in range(total_samples):
        timestamp = base_time + timedelta(minutes=i)

        hour_factor = np.sin((timestamp.hour - 6) * np.pi / 12) * 0.4 + 1.0
        requests = base_rps * hour_factor + np.random.normal(0, noise_std)
        requests = max(10, requests)

        data.append(
            {
                "timestamp": timestamp,
                "total_requests": int(requests),
                "avg_response_time": 25 + np.random.normal(0, 3),
                "k3s_requests": int(requests * 0.8),
                "knative_requests": int(requests * 0.2),
                "error_rate": 0.01,
            }
        )

    return pd.DataFrame(data)


def calculate_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
    """Calculate RMSE, MAE, MAPE metrics."""
    errors = predicted - actual
    rmse = np.sqrt(np.mean(errors**2))
    mae = np.mean(np.abs(errors))
    mean_actual = np.mean(actual)
    mape = np.mean(np.abs(errors / np.where(actual == 0, 1, actual))) * 100
    rmse_percent = (rmse / mean_actual) * 100

    return {"RMSE": rmse, "MAE": mae, "MAPE": mape, "RMSE %": rmse_percent}


def compare_models(train_data: pd.DataFrame, test_data: pd.DataFrame) -> pd.DataFrame:
    """Compare all models and return results DataFrame."""

    train_values = train_data["total_requests"].values
    test_values = test_data["total_requests"].values

    results = []

    naive = NaivePredictor()
    naive.fit(None, train_values)
    naive_pred = naive.predict_from_series(test_values)
    naive_metrics = calculate_metrics(test_values, naive_pred)
    naive_metrics["Model"] = "Naive (Last Value)"
    results.append(naive_metrics)

    seasonal = SeasonalNaivePredictor(period=60)
    seasonal.fit(None, train_values)
    seasonal_pred = seasonal.predict_from_series(test_values)
    seasonal_metrics = calculate_metrics(test_values, seasonal_pred)
    seasonal_metrics["Model"] = "Seasonal Naive (1h)"
    results.append(seasonal_metrics)

    ma5 = MovingAveragePredictor(window_size=5)
    ma5.fit(None, train_values)
    ma5_pred = ma5.predict_from_series(test_values)
    ma5_metrics = calculate_metrics(test_values, ma5_pred)
    ma5_metrics["Model"] = "Moving Avg (w=5)"
    results.append(ma5_metrics)

    ma15 = MovingAveragePredictor(window_size=15)
    ma15.fit(None, train_values)
    ma15_pred = ma15.predict_from_series(test_values)
    ma15_metrics = calculate_metrics(test_values, ma15_pred)
    ma15_metrics["Model"] = "Moving Avg (w=15)"
    results.append(ma15_metrics)

    ema = ExponentialMovingAveragePredictor(alpha=0.3)
    ema.fit(None, train_values)
    ema_pred = ema.predict_from_series(test_values)
    ema_metrics = calculate_metrics(test_values, ema_pred)
    ema_metrics["Model"] = "EMA (α=0.3)"
    results.append(ema_metrics)

    train_data_ts = train_data.copy()
    train_data_ts["timestamp"] = train_data_ts["timestamp"].apply(lambda x: int(x.timestamp()))

    lr = TrafficPredictor()
    lr.train(train_data_ts)

    lr_pred = []
    for i in range(len(test_data)):
        row = test_data.iloc[i]
        stats = {
            "timestamp": int(row["timestamp"].timestamp()),
            "total_requests": row["total_requests"],
            "avg_response_time": row.get("avg_response_time", 25),
            "k3s_requests": row.get("k3s_requests", int(row["total_requests"] * 0.8)),
            "knative_requests": row.get("knative_requests", int(row["total_requests"] * 0.2)),
            "error_rate": row.get("error_rate", 0.01),
        }
        pred = lr.predict(stats)
        lr_pred.append(pred["predicted_requests"])

    lr_pred = np.array(lr_pred)
    lr_metrics = calculate_metrics(test_values, lr_pred)
    lr_metrics["Model"] = "Linear Regression"
    results.append(lr_metrics)

    df = pd.DataFrame(results)
    df = df[["Model", "RMSE", "MAE", "MAPE", "RMSE %"]]
    df = df.sort_values("RMSE %")

    return df


def generate_latex_table(df: pd.DataFrame) -> str:
    """Generate LaTeX table for thesis."""
    latex = """\\begin{table}[h]
\\centering
\\caption{Prediction Model Comparison}
\\label{tab:model-comparison}
\\begin{tabular}{lrrrr}
\\toprule
Model & RMSE & MAE & MAPE (\\%) & RMSE (\\%) \\\\
\\midrule
"""
    for _, row in df.iterrows():
        latex += (
            f"{row['Model']} & {row['RMSE']:.2f} & {row['MAE']:.2f} & {row['MAPE']:.2f} & {row['RMSE %']:.2f} \\\\\n"
        )

    latex += """\\bottomrule
\\end{tabular}
\\end{table}"""

    return latex


def main():
    """Run model comparison."""
    print("=" * 70)
    print("Model Comparison: LR vs Naive Baselines")
    print("=" * 70)
    print()

    print("[1/3] Generating synthetic data...")
    train_data = generate_synthetic_data(duration_hours=48, base_rps=100)
    test_data = generate_synthetic_data(duration_hours=6, base_rps=100)
    print(f"  Train: {len(train_data)} samples, Test: {len(test_data)} samples")
    print()

    print("[2/3] Comparing models...")
    results = compare_models(train_data, test_data)
    print()

    print("[3/3] Results:")
    print()
    print(results.to_string(index=False))
    print()

    output_dir = Path(__file__).parent.parent / "results" / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "model_comparison.csv"
    results.to_csv(csv_path, index=False)
    print(f"Saved CSV: {csv_path}")

    latex_path = output_dir / "model_comparison.tex"
    latex = generate_latex_table(results)
    latex_path.write_text(latex)
    print(f"Saved LaTeX: {latex_path}")

    md_path = output_dir / "model_comparison.md"

    table_str = results.to_string(index=False)
    md_content = f"""# Model Comparison Results

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## Summary

```
{table_str}
```

## Analysis

- **Best Model**: {results.iloc[0]["Model"]} (RMSE: {results.iloc[0]["RMSE %"]:.2f}%)
- **Linear Regression**: RMSE {results[results["Model"] == "Linear Regression"]["RMSE %"].values[0]:.2f}%
- **Naive Baseline**: RMSE {results[results["Model"] == "Naive (Last Value)"]["RMSE %"].values[0]:.2f}%

## Thesis Target

- Target: RMSE < 20% of average traffic
- Linear Regression: {"✅ PASS" if results[results["Model"] == "Linear Regression"]["RMSE %"].values[0] < 20 else "❌ FAIL"}
"""
    md_path.write_text(md_content)
    print(f"Saved Markdown: {md_path}")

    print()
    print("=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    best = results.iloc[0]
    lr = results[results["Model"] == "Linear Regression"].iloc[0]
    naive = results[results["Model"] == "Naive (Last Value)"].iloc[0]

    print(f"Best model: {best['Model']} (RMSE: {best['RMSE %']:.2f}%)")
    print(f"LR improvement over naive: {naive['RMSE %'] - lr['RMSE %']:.2f}% reduction")

    if lr["RMSE %"] < naive["RMSE %"]:
        print("✓ Linear Regression outperforms naive baseline - model justified")
    else:
        print("✗ Linear Regression does not improve over naive")


if __name__ == "__main__":
    main()
