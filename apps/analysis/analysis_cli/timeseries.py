"""Phase B time-series visualization.

Ported from ``apps/scripts/scripts/plot_phase_b_timeseries.py``. Data loading
delegates to ``analysis.data_loaders``; outlier check to the same package.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from analysis.data_loaders import is_outlier, load_outliers, load_phase_b_data
from shared.scenarios import SCENARIO_ORDER


def plot_scenario_summary(experiments: list[dict], outliers: list[dict], output_dir: Path) -> None:
    """Create summary plot: one subplot per scenario showing all runs."""
    # Group by scenario
    scenarios: dict[str, list[dict]] = {}
    for exp in experiments:
        scenarios.setdefault(exp["scenario"], []).append(exp)

    # Create figure with 4 subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Phase B: p99 Latency by Scenario (All Runs)", fontsize=14, fontweight="bold")

    scenario_labels = {
        "s1-k8s-only": "S1: K8s-only",
        "s2-serverless-only": "S2: Serverless-only",
        "s3-hybrid-reactive": "S3: Hybrid Reactive",
        "s4-hybrid-predictive": "S4: Hybrid Predictive",
    }

    for idx, scenario_name in enumerate(SCENARIO_ORDER):
        ax = axes[idx // 2, idx % 2]
        runs = scenarios.get(scenario_name, [])

        # Plot each run as a bar
        run_ids = [r["run_id"] for r in runs]
        p99_values = [r["p99_latency_ms"] for r in runs]
        violations = [r["slo_violation_count"] for r in runs]

        colors = []
        for run in runs:
            if is_outlier(scenario_name, run["run_id"], outliers):
                colors.append("#ff6b6b")  # Red for outliers
            elif run["slo_violation_count"] > 0:
                colors.append("#feca57")  # Yellow for violations
            else:
                colors.append("#48dbfb")  # Blue for clean

        bars = ax.bar(run_ids, p99_values, color=colors, alpha=0.7, edgecolor="black")

        # SLO threshold line
        ax.axhline(y=200, color="red", linestyle="--", linewidth=2, label="SLO Threshold (200ms)")

        # Labels
        ax.set_title(scenario_labels[scenario_name], fontweight="bold")
        ax.set_xlabel("Run ID")
        ax.set_ylabel("p99 Latency (ms)")
        ax.set_ylim(0, max(p99_values) * 1.1 if p99_values else 1000)
        ax.grid(axis="y", alpha=0.3)

        # Add violation counts as text
        for run_id, p99, viol in zip(run_ids, p99_values, violations):
            if viol > 0:
                ax.text(run_id, p99 + 20, f"V:{viol}", ha="center", fontsize=8, color="red")

        # Legend
        if idx == 0:
            outlier_patch = mpatches.Patch(color="#ff6b6b", label="Outlier (excluded)")
            violation_patch = mpatches.Patch(color="#feca57", label="SLO violation")
            clean_patch = mpatches.Patch(color="#48dbfb", label="Clean run")
            ax.legend(handles=[outlier_patch, violation_patch, clean_patch, ax.lines[0]], loc="upper left")

    plt.tight_layout()

    # Save
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "scenario_summary.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_path}")
    plt.close()


def plot_decision_comparison(experiments: list[dict], outliers: list[dict], output_dir: Path) -> None:
    """Plot decision counts by scenario."""
    # Group by scenario (exclude outliers)
    scenarios: dict[str, list[dict]] = {}
    for exp in experiments:
        if is_outlier(exp["scenario"], exp["run_id"], outliers):
            continue
        scenarios.setdefault(exp["scenario"], []).append(exp)

    # Aggregate decision counts
    scenario_labels = {
        "s1-k8s-only": "S1\nK8s",
        "s2-serverless-only": "S2\nServerless",
        "s3-hybrid-reactive": "S3\nReactive",
        "s4-hybrid-predictive": "S4\nPredictive",
    }

    maintain_counts = []
    scale_out_counts = []
    optimize_counts = []
    predictive_counts = []

    for scenario_name in SCENARIO_ORDER:
        runs = scenarios.get(scenario_name, [])
        if not runs:
            maintain_counts.append(0)
            scale_out_counts.append(0)
            optimize_counts.append(0)
            predictive_counts.append(0)
            continue

        maintain_counts.append(sum(r.get("maintain_count", 0) for r in runs))
        scale_out_counts.append(sum(r.get("scale_out_count", 0) for r in runs))
        optimize_counts.append(sum(r.get("optimize_cost_count", 0) for r in runs))
        predictive_counts.append(sum(r.get("predictive_count", 0) for r in runs))

    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(SCENARIO_ORDER))
    width = 0.6

    labels = [scenario_labels[s] for s in SCENARIO_ORDER]

    # Stacked bars
    p1 = ax.bar(x, maintain_counts, width, label="MAINTAIN", color="#95afc0")
    p2 = ax.bar(x, scale_out_counts, width, bottom=maintain_counts, label="SCALE_OUT", color="#eb4d4b")
    p3 = ax.bar(
        x,
        scale_out_counts,
        width,
        bottom=np.array(maintain_counts) + np.array(scale_out_counts),
        label="OPTIMIZE_COST",
        color="#6ab04c",
    )
    p4 = ax.bar(
        x,
        predictive_counts,
        width,
        bottom=np.array(maintain_counts) + np.array(scale_out_counts) + np.array(optimize_counts),
        label="PREDICTIVE",
        color="#f9ca24",
    )

    ax.set_ylabel("Decision Count (Total Across Clean Runs)", fontweight="bold")
    ax.set_title("Routing Decisions by Scenario (Outliers Excluded)", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()

    # Save
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "decision_comparison.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_path}")
    plt.close()


def plot_clean_vs_outlier_comparison(experiments: list[dict], outliers: list[dict], output_dir: Path) -> None:
    """Compare statistics with and without outliers."""
    labels = ["S1\nK8s", "S2\nServerless", "S3\nReactive", "S4\nPredictive"]

    with_outliers = []
    without_outliers = []

    for scenario in SCENARIO_ORDER:
        runs = [r for r in experiments if r["scenario"] == scenario]
        clean_runs = [r for r in runs if not is_outlier(scenario, r["run_id"], outliers)]

        p99_all = [r["p99_latency_ms"] for r in runs]
        p99_clean = [r["p99_latency_ms"] for r in clean_runs]

        with_outliers.append(np.mean(p99_all))
        without_outliers.append(np.mean(p99_clean))

    x = np.arange(len(SCENARIO_ORDER))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))

    bars1 = ax.bar(x - width / 2, with_outliers, width, label="With Outliers", color="#ff6b6b", alpha=0.7)
    bars2 = ax.bar(x + width / 2, without_outliers, width, label="Without Outliers (Clean)", color="#48dbfb", alpha=0.7)

    ax.set_ylabel("Mean p99 Latency (ms)", fontweight="bold")
    ax.set_title("Impact of Outlier Exclusion on Mean p99", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    ax.axhline(y=200, color="red", linestyle="--", linewidth=2, alpha=0.5, label="SLO Threshold")

    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0, height, f"{height:.0f}ms", ha="center", va="bottom", fontsize=9
            )

    plt.tight_layout()

    # Save
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "outlier_impact.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_path}")
    plt.close()


def generate_all_timeseries(phase_b_data: Path, outliers_data: Path, output_dir: Path) -> None:
    """Generate all Phase B time-series visualizations.

    Loads ``experiments_final.json`` + ``outliers.json`` via the shared loaders
    and writes 3 PNGs into ``output_dir``.
    """
    print("=" * 80)
    print("PHASE B TIME-SERIES VISUALIZATION")
    print("=" * 80)

    print("\n📊 Generating plots...\n")

    experiments = load_phase_b_data(phase_b_data)
    outliers = load_outliers(outliers_data)

    plot_scenario_summary(experiments, outliers, output_dir)
    plot_decision_comparison(experiments, outliers, output_dir)
    plot_clean_vs_outlier_comparison(experiments, outliers, output_dir)

    print("\n✅ All plots generated successfully!")
    print(f"\nOutput directory: {output_dir}")
    print("\nGenerated files:")
    print("  1. scenario_summary.png - p99 latency by scenario (bar chart)")
    print("  2. decision_comparison.png - Routing decisions by scenario (stacked bar)")
    print("  3. outlier_impact.png - Impact of outlier exclusion (comparison)")
