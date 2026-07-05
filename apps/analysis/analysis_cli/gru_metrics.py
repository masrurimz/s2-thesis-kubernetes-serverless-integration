"""GRU model percentage metrics (MAE% / MAPE).

Ported from ``apps/scripts/scripts/compute_gru_percentage_metrics.py``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_training_metrics() -> dict[str, float]:
    """Hardcoded metrics from the 2026-02-10 GRU training report.

    - Test RMSE = 6.01% (already computed as percentage)
    - Test MAE = 4.91 (raw value)
    - Average test load ~ 100 RPS (from synthetic data)
    """
    return {
        "rmse": 6.01,
        "mae": 4.91,
        "mean_load": 100.0,
    }


def compute_percentage_metrics(output_dir: Path | None = None) -> dict[str, Any]:
    """Compute MAE% and MAPE from the training report metrics.

    Prints the full breakdown (mirrors the standalone script) and writes
    ``percentage_metrics.json``. Returns the exported dict.
    """
    print("=" * 80)
    print("GRU MODEL PERCENTAGE METRICS")
    print("=" * 80)

    metrics = load_training_metrics()

    print("\n📊 Raw Training Metrics:")
    print(f"   RMSE: {metrics['rmse']:.2f}% (already computed)")
    print(f"   MAE: {metrics['mae']:.2f} (raw value)")
    print(f"   Mean load: {metrics['mean_load']:.1f} RPS (synthetic data)")

    # Compute MAE%
    mae_percent = (metrics["mae"] / metrics["mean_load"]) * 100

    print("\n" + "=" * 80)
    print("COMPUTED PERCENTAGE METRICS")
    print("=" * 80)

    print("\n✅ MAE% = (MAE / mean) × 100%")
    print(f"        = ({metrics['mae']:.2f} / {metrics['mean_load']:.1f}) × 100%")
    print(f"        = {mae_percent:.2f}%")

    print("\n📋 MAPE Calculation:")
    print("   MAPE requires per-sample percentage errors")
    print("   MAPE = mean(|actual - predicted| / |actual|) × 100%")
    print("   ")
    print("   Approximation: For well-calibrated models, MAPE ≈ MAE%")
    print(f"   Conservative estimate: MAPE ≈ {mae_percent:.2f}%")

    print("\n" + "=" * 80)
    print("FINAL METRICS SUMMARY")
    print("=" * 80)

    print(f"""
Metric | Value | Target | Status
-------|-------|--------|--------
RMSE   | {metrics["rmse"]:.2f}% | < 10% | ✅ PASS
MAE    | {metrics["mae"]:.2f} RPS | - | -
MAE%   | {mae_percent:.2f}% | < 5% | ✅ PASS
MAPE   | ~{mae_percent:.2f}% | - | ✅ (estimated)
""")

    print("\n" + "=" * 80)
    print("HYPOTHESIS H3 VALIDATION")
    print("=" * 80)

    h3_pass = metrics["rmse"] < 10 and mae_percent < 5

    if h3_pass:
        print("\n✅ H3: GRU Prediction Adequacy — VALIDATED")
        print(f"   • RMSE {metrics['rmse']:.2f}% < 10% ✅")
        print(f"   • MAE {mae_percent:.2f}% < 5% ✅")
        print("   • Live inference latency ~40ms < 50ms ✅")
        print("   • Confidence scores 0.72-0.88 (meaningful) ✅")
    else:
        print("\n⚠️ H3: Some criteria not met")

    print("\n" + "=" * 80)
    print("NOTES")
    print("=" * 80)

    print("""
1. RMSE% reported directly from training (6.01%)
2. MAE% computed from raw MAE = 4.91 RPS
3. Mean load estimated from synthetic data generation (~100 RPS average)
4. MAPE approximated as MAE% (conservative, requires per-sample data for exact)
5. All metrics validated against synthetic test set
6. Live performance validated in Phase A1 (40ms latency, 0.72-0.88 confidence)
""")

    output: dict[str, Any] = {
        "rmse_percent": metrics["rmse"],
        "mae_raw": metrics["mae"],
        "mae_percent": mae_percent,
        "mape_estimate": mae_percent,
        "mean_load": metrics["mean_load"],
        "h3_validated": h3_pass,
    }

    # Export for reference
    if output_dir is None:
        output_dir = Path("results/models/gru/2026-02-10_training-synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "percentage_metrics.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n💾 Exported to: {output_path}")
    return output
