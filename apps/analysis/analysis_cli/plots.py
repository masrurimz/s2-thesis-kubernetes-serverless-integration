"""Thesis-quality matplotlib figures.

Ported from ``apps/scripts/scripts/generate_plots.py``. Scenario constants
come from ``shared.scenarios`` (single source of truth); bootstrap CI from
``shared.stats``.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from analysis.data_loaders import load_outliers, load_phase_b_data
from shared.scenarios import SCENARIO_COLORS, SCENARIO_LABELS, SCENARIO_ORDER, SLO_THRESHOLD_MS
from shared.stats import bootstrap_ci


def parse_decision_log(report_path: Path) -> list[dict[str, Any]]:
    """Parse the Phase A1 decision log table from report.md."""
    text = report_path.read_text()
    decisions: list[dict[str, Any]] = []

    in_table = False
    for line in text.splitlines():
        if line.strip().startswith("| Decision #"):
            in_table = True
            continue
        if in_table and line.strip().startswith("|---"):
            continue
        if in_table and line.strip().startswith("| ..."):
            continue
        if in_table and line.strip().startswith("|"):
            cols = [c.strip().strip("**") for c in line.split("|")[1:-1]]
            if len(cols) >= 6:
                try:
                    decision_num = int(cols[0])
                except ValueError:
                    continue
                action = cols[1]
                timestamp_str = cols[2]
                p99_str = cols[4].replace("ms", "").replace(",", "").strip()
                weight_str = cols[5]

                try:
                    p99 = float(p99_str) if p99_str and p99_str != "-" else None
                except ValueError:
                    p99 = None

                k8s_w, sless_w = 80, 20
                if "/" in weight_str:
                    parts = weight_str.split("/")
                    try:
                        k8s_w = int(parts[0])
                        sless_w = int(parts[1])
                    except ValueError:
                        pass

                try:
                    ts = datetime.strptime(f"2026-02-12 {timestamp_str}", "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    ts = None

                decisions.append(
                    {
                        "num": decision_num,
                        "action": action,
                        "timestamp": ts,
                        "p99_ms": p99,
                        "k8s_weight": k8s_w,
                        "serverless_weight": sless_w,
                    }
                )
        elif in_table and not line.strip().startswith("|"):
            in_table = False

    return decisions


def plot_phase_a1_decision_timeline(decisions: list[dict], ax_main: plt.Axes) -> None:
    """Plot 1: Phase A1 Decision Timeline with p99 and weight overlay."""
    action_colors = {
        "SCALE_OUT": "#d62728",
        "PREDICTIVE": "#2ca02c",
        "OPTIMIZE_COST": "#1f77b4",
        "MAINTAIN": "#7f7f7f",
    }
    action_markers = {
        "SCALE_OUT": "v",
        "PREDICTIVE": "*",
        "OPTIMIZE_COST": "^",
        "MAINTAIN": "o",
    }

    valid = [d for d in decisions if d["timestamp"] is not None]
    if not valid:
        ax_main.text(
            0.5,
            0.5,
            "No timestamped decisions found",
            ha="center",
            va="center",
            transform=ax_main.transAxes,
            fontsize=12,
        )
        return

    base_time = valid[0]["timestamp"]
    t_sec = [(d["timestamp"] - base_time).total_seconds() for d in valid]
    p99_vals = [d["p99_ms"] for d in valid]
    actions = [d["action"] for d in valid]
    sless_weights = [d["serverless_weight"] for d in valid]

    # Plot p99 latency line (connect non-None values)
    t_p99 = [t for t, p in zip(t_sec, p99_vals) if p is not None]
    p99_clean = [p for p in p99_vals if p is not None]
    ax_main.plot(t_p99, p99_clean, color="#333333", linewidth=1.5, alpha=0.6, zorder=2)

    # SLO threshold line
    ax_main.axhline(
        y=SLO_THRESHOLD_MS,
        color="#e74c3c",
        linestyle="--",
        linewidth=1.2,
        alpha=0.7,
        label=f"SLO Threshold ({SLO_THRESHOLD_MS:.0f}ms)",
    )

    # Decision markers
    for i, d in enumerate(valid):
        if d["p99_ms"] is not None:
            color = action_colors.get(d["action"], "#999999")
            marker = action_markers.get(d["action"], "o")
            size = 180 if d["action"] == "PREDICTIVE" else 80
            ax_main.scatter(
                t_sec[i], d["p99_ms"], c=color, marker=marker, s=size, zorder=5, edgecolors="black", linewidths=0.5
            )

    # Fill violation region
    ax_main.axhspan(
        SLO_THRESHOLD_MS,
        ax_main.get_ylim()[1] if ax_main.get_ylim()[1] > SLO_THRESHOLD_MS else 7000,
        alpha=0.05,
        color="#e74c3c",
        zorder=0,
    )

    ax_main.set_xlabel("Time (seconds from start)", fontsize=11)
    ax_main.set_ylabel("p99 Latency (ms)", fontsize=11, color="#333333")
    ax_main.set_ylim(bottom=0, top=max(p99_clean) * 1.15 if p99_clean else 1000)
    ax_main.tick_params(axis="y", labelcolor="#333333")

    # Secondary Y axis: serverless weight
    ax_weight = ax_main.twinx()
    ax_weight.fill_between(t_sec, sless_weights, alpha=0.15, color="#2ca02c", step="post")
    ax_weight.step(t_sec, sless_weights, where="post", color="#2ca02c", linewidth=1.2, alpha=0.5, linestyle="-.")
    ax_weight.set_ylabel("Serverless Weight (%)", fontsize=11, color="#2ca02c")
    ax_weight.set_ylim(0, 100)
    ax_weight.tick_params(axis="y", labelcolor="#2ca02c")

    # Legend
    legend_patches = [
        mpatches.Patch(color=action_colors["SCALE_OUT"], label="SCALE_OUT (reactive)"),
        mpatches.Patch(color=action_colors["PREDICTIVE"], label="PREDICTIVE (proactive)"),
        mpatches.Patch(color=action_colors["OPTIMIZE_COST"], label="OPTIMIZE_COST"),
        mpatches.Patch(color=action_colors["MAINTAIN"], label="MAINTAIN"),
        plt.Line2D([0], [0], color="#e74c3c", linestyle="--", label=f"SLO ({SLO_THRESHOLD_MS:.0f}ms)"),
        plt.Line2D([0], [0], color="#2ca02c", linestyle="-.", alpha=0.5, label="Serverless weight"),
    ]
    ax_main.legend(handles=legend_patches, loc="upper right", fontsize=8, framealpha=0.9)
    ax_main.set_title("Phase A1: Decision Timeline — Predictive Trigger Validation", fontsize=13, fontweight="bold")
    ax_main.grid(axis="y", alpha=0.3)


def plot_phase_b_boxplots(experiments: list[dict], outliers: list[dict], ax: plt.Axes) -> None:
    """Plot 2: Phase B box plots of p99 across scenarios with individual run points."""
    outlier_keys = {(o["scenario"], o["run_id"]) for o in outliers}

    box_data = []
    positions = []
    for i, scenario in enumerate(SCENARIO_ORDER):
        runs = [e for e in experiments if e["scenario"] == scenario]
        p99s = [r["p99_latency_ms"] for r in runs]
        box_data.append(p99s)
        positions.append(i)

    bp = ax.boxplot(
        box_data,
        positions=positions,
        widths=0.5,
        patch_artist=True,
        showmeans=True,
        meanprops=dict(marker="D", markerfacecolor="white", markeredgecolor="black", markersize=6),
        medianprops=dict(color="black", linewidth=1.5),
        whiskerprops=dict(linewidth=1),
        capprops=dict(linewidth=1),
    )
    for patch, scenario in zip(bp["boxes"], SCENARIO_ORDER):
        patch.set_facecolor(SCENARIO_COLORS[scenario])
        patch.set_alpha(0.6)

    # Overlay individual runs
    for i, scenario in enumerate(SCENARIO_ORDER):
        runs = [e for e in experiments if e["scenario"] == scenario]
        for r in runs:
            is_outlier = (r["scenario"], r["run_id"]) in outlier_keys
            jitter = np.random.uniform(-0.12, 0.12)
            if is_outlier:
                ax.scatter(
                    i + jitter, r["p99_latency_ms"], c="red", marker="x", s=60, linewidths=1.2, zorder=5, alpha=0.7
                )
            else:
                ax.scatter(
                    i + jitter,
                    r["p99_latency_ms"],
                    c=SCENARIO_COLORS[scenario],
                    marker="o",
                    s=50,
                    edgecolors="black",
                    linewidths=0.8,
                    zorder=5,
                    alpha=0.9,
                )

    # SLO line
    ax.axhline(
        y=SLO_THRESHOLD_MS,
        color="#e74c3c",
        linestyle="--",
        linewidth=1,
        alpha=0.7,
        label=f"SLO Threshold ({SLO_THRESHOLD_MS:.0f}ms)",
    )

    ax.set_xticks(positions)
    ax.set_xticklabels([SCENARIO_LABELS[s] for s in SCENARIO_ORDER], fontsize=9, rotation=15, ha="right")
    ax.set_ylabel("p99 Latency (ms)", fontsize=11)
    ax.set_title("Phase B: p99 Latency Distribution by Scenario (5 runs each)", fontsize=13, fontweight="bold")
    ax.grid(axis="y", alpha=0.3)

    # Legend for outlier marking
    legend_elements = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#666", markersize=7, label="Valid run"),
        plt.Line2D(
            [0],
            [0],
            marker="x",
            color="w",
            markerfacecolor="#999",
            markeredgecolor="red",
            markersize=7,
            label="Suspected stale data",
        ),
        plt.Line2D([0], [0], color="#e74c3c", linestyle="--", label=f"SLO ({SLO_THRESHOLD_MS:.0f}ms)"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=8, framealpha=0.9)


def plot_scenario_dashboard(experiments: list[dict], axes: np.ndarray) -> None:
    """Plot 3: 2x2 dashboard — throughput, p99, violations, decision counts."""
    metrics = [
        ("throughput_rps", "Throughput (RPS)", "Mean Throughput (RPS)"),
        ("p99_latency_ms", "p99 Latency (ms)", "Mean p99 Latency (ms)"),
        ("slo_violation_count", "SLO Violations", "Mean SLO Violation Count"),
    ]

    for idx, (metric_key, title, ylabel) in enumerate(metrics):
        row, col = divmod(idx, 2)
        ax = axes[row, col]

        means = []
        ci_lows = []
        ci_highs = []
        for scenario in SCENARIO_ORDER:
            vals = [e[metric_key] for e in experiments if e["scenario"] == scenario]
            m = np.mean(vals)
            ci_lo, ci_hi = bootstrap_ci(vals)
            means.append(m)
            ci_lows.append(m - ci_lo)
            ci_highs.append(ci_hi - m)

        x = np.arange(len(SCENARIO_ORDER))
        colors = [SCENARIO_COLORS[s] for s in SCENARIO_ORDER]
        bars = ax.bar(
            x,
            means,
            yerr=[ci_lows, ci_highs],
            capsize=5,
            color=colors,
            alpha=0.75,
            edgecolor="black",
            linewidth=0.5,
            error_kw=dict(linewidth=1.2),
        )

        if metric_key == "p99_latency_ms":
            ax.axhline(y=SLO_THRESHOLD_MS, color="#e74c3c", linestyle="--", linewidth=1, alpha=0.7)

        ax.set_xticks(x)
        ax.set_xticklabels(
            [SCENARIO_LABELS[s].split(": ")[1] for s in SCENARIO_ORDER], fontsize=8, rotation=15, ha="right"
        )
        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.grid(axis="y", alpha=0.3)

    # Bottom-right: Decision type breakdown (stacked bar)
    ax = axes[1, 1]
    decision_types = ["maintain_count", "scale_out_count", "predictive_count", "optimize_cost_count"]
    decision_labels = ["MAINTAIN", "SCALE_OUT", "PREDICTIVE", "OPTIMIZE_COST"]
    decision_colors = ["#7f7f7f", "#d62728", "#2ca02c", "#1f77b4"]

    x = np.arange(len(SCENARIO_ORDER))
    bottoms = np.zeros(len(SCENARIO_ORDER))
    for dtype, dlabel, dcolor in zip(decision_types, decision_labels, decision_colors):
        vals = []
        for scenario in SCENARIO_ORDER:
            v = [e[dtype] for e in experiments if e["scenario"] == scenario]
            vals.append(np.mean(v))
        ax.bar(x, vals, bottom=bottoms, color=dcolor, alpha=0.75, label=dlabel, edgecolor="black", linewidth=0.3)
        bottoms += np.array(vals)

    ax.set_xticks(x)
    ax.set_xticklabels([SCENARIO_LABELS[s].split(": ")[1] for s in SCENARIO_ORDER], fontsize=8, rotation=15, ha="right")
    ax.set_ylabel("Mean Decision Count", fontsize=9)
    ax.set_title("Decision Type Distribution", fontsize=11, fontweight="bold")
    ax.legend(fontsize=7, loc="upper left")
    ax.grid(axis="y", alpha=0.3)


def generate_all_plots(repo_root: Path, figures_dir: Path | None = None) -> int:
    """Generate all 3 thesis figures (PNG + PDF) into ``figures_dir``.

    ``repo_root`` anchors the Phase A1 report + Phase B data paths.
    """
    if figures_dir is None:
        figures_dir = repo_root / "results/experiments/figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    phase_a1_report = repo_root / "results/experiments/phase-a1/2026-02-12_predictive-trigger/report.md"
    phase_b_data = repo_root / "results/experiments/phase-b/2026-02-12_replicated-20runs/raw/experiments_final.json"
    outliers_data = repo_root / "results/experiments/phase-b/2026-02-12_replicated-20runs/raw/outliers.json"

    # --- Plot 1: Phase A1 Decision Timeline ---
    decisions = parse_decision_log(phase_a1_report) if phase_a1_report.exists() else []
    fig1, ax1 = plt.subplots(figsize=(14, 6))
    plot_phase_a1_decision_timeline(decisions, ax1)
    fig1.tight_layout()
    path1 = figures_dir / "phase_a1_decision_timeline.png"
    fig1.savefig(path1, dpi=200, bbox_inches="tight")
    plt.close(fig1)
    print(f"✅ Plot 1 saved: {path1}")

    # Also save PDF for thesis
    path1_pdf = figures_dir / "phase_a1_decision_timeline.pdf"
    fig1_pdf, ax1_pdf = plt.subplots(figsize=(14, 6))
    plot_phase_a1_decision_timeline(decisions, ax1_pdf)
    fig1_pdf.tight_layout()
    fig1_pdf.savefig(path1_pdf, bbox_inches="tight")
    plt.close(fig1_pdf)
    print(f"   PDF: {path1_pdf}")

    # --- Plot 2: Phase B Box Plots ---
    experiments = load_phase_b_data(phase_b_data)
    outliers = load_outliers(outliers_data)
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    plot_phase_b_boxplots(experiments, outliers, ax2)
    fig2.tight_layout()
    path2 = figures_dir / "phase_b_p99_boxplots.png"
    fig2.savefig(path2, dpi=200, bbox_inches="tight")
    plt.close(fig2)
    print(f"✅ Plot 2 saved: {path2}")

    path2_pdf = figures_dir / "phase_b_p99_boxplots.pdf"
    fig2_pdf, ax2_pdf = plt.subplots(figsize=(10, 6))
    plot_phase_b_boxplots(experiments, outliers, ax2_pdf)
    fig2_pdf.tight_layout()
    fig2_pdf.savefig(path2_pdf, bbox_inches="tight")
    plt.close(fig2_pdf)
    print(f"   PDF: {path2_pdf}")

    # --- Plot 3: Scenario Dashboard ---
    fig3, axes3 = plt.subplots(2, 2, figsize=(14, 10))
    plot_scenario_dashboard(experiments, axes3)
    fig3.suptitle(
        "Phase B: Scenario Comparison Dashboard (5 runs × 4 scenarios)", fontsize=14, fontweight="bold", y=1.01
    )
    fig3.tight_layout()
    path3 = figures_dir / "phase_b_scenario_dashboard.png"
    fig3.savefig(path3, dpi=200, bbox_inches="tight")
    plt.close(fig3)
    print(f"✅ Plot 3 saved: {path3}")

    path3_pdf = figures_dir / "phase_b_scenario_dashboard.pdf"
    fig3_pdf, axes3_pdf = plt.subplots(2, 2, figsize=(14, 10))
    plot_scenario_dashboard(experiments, axes3_pdf)
    fig3_pdf.suptitle(
        "Phase B: Scenario Comparison Dashboard (5 runs × 4 scenarios)", fontsize=14, fontweight="bold", y=1.01
    )
    fig3_pdf.tight_layout()
    fig3_pdf.savefig(path3_pdf, bbox_inches="tight")
    plt.close(fig3_pdf)
    print(f"   PDF: {path3_pdf}")

    # Summary
    print(f"\n📊 Generated {3} plots ({6} files) in {figures_dir}/")
    print(f"   Decisions parsed from Phase A1: {len(decisions)}")
    print(f"   Phase B runs: {len(experiments)} ({len(outliers)} outliers marked)")

    return 0
