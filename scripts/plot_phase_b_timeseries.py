#!/usr/bin/env python3
"""
Generate time-series plots for Phase B experiments.

Visualization goals:
1. p99 latency over time per run
2. Overlay routing decisions (SCALE_OUT, OPTIMIZE_COST, PREDICTIVE, MAINTAIN)
3. Show SLO threshold (200ms) as reference line
4. Faceted by scenario for comparison

Output:
- Individual run plots (detailed)
- Scenario comparison plots (summary)
- Decision timing analysis
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from typing import List, Dict
import numpy as np

# Set publication-quality style
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['legend.fontsize'] = 9

def load_phase_b_data() -> List[Dict]:
    """Load Phase B experiments data."""
    phase_b_path = Path(__file__).parent.parent / "results/experiments/phase-b/2026-02-12_replicated-20runs/raw/experiments_final.json"
    with open(phase_b_path) as f:
        return json.load(f)

def load_outliers() -> List[Dict]:
    """Load outlier list."""
    outliers_path = Path(__file__).parent.parent / "results/experiments/phase-b/2026-02-12_replicated-20runs/raw/outliers.json"
    try:
        with open(outliers_path) as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def is_outlier(scenario: str, run_id: int, outliers: List[Dict]) -> bool:
    """Check if a run is an outlier."""
    for outlier in outliers:
        if outlier["scenario"] == scenario and outlier["run_id"] == run_id:
            return True
    return False

def plot_scenario_summary():
    """Create summary plot: one subplot per scenario showing all runs."""
    experiments = load_phase_b_data()
    outliers = load_outliers()
    
    # Group by scenario
    scenarios = {}
    for exp in experiments:
        scenario = exp["scenario"]
        if scenario not in scenarios:
            scenarios[scenario] = []
        scenarios[scenario].append(exp)
    
    # Create figure with 4 subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Phase B: p99 Latency by Scenario (All Runs)", fontsize=14, fontweight='bold')
    
    scenario_order = ["s1-k8s-only", "s2-serverless-only", "s3-hybrid-reactive", "s4-hybrid-predictive"]
    scenario_labels = {
        "s1-k8s-only": "S1: K8s-only",
        "s2-serverless-only": "S2: Serverless-only",
        "s3-hybrid-reactive": "S3: Hybrid Reactive",
        "s4-hybrid-predictive": "S4: Hybrid Predictive"
    }
    
    for idx, scenario_name in enumerate(scenario_order):
        ax = axes[idx // 2, idx % 2]
        runs = scenarios.get(scenario_name, [])
        
        # Plot each run as a bar
        run_ids = [r["run_id"] for r in runs]
        p99_values = [r["p99_latency_ms"] for r in runs]
        violations = [r["slo_violation_count"] for r in runs]
        
        colors = []
        for run in runs:
            if is_outlier(scenario_name, run["run_id"], outliers):
                colors.append('#ff6b6b')  # Red for outliers
            elif run["slo_violation_count"] > 0:
                colors.append('#feca57')  # Yellow for violations
            else:
                colors.append('#48dbfb')  # Blue for clean
        
        bars = ax.bar(run_ids, p99_values, color=colors, alpha=0.7, edgecolor='black')
        
        # SLO threshold line
        ax.axhline(y=200, color='red', linestyle='--', linewidth=2, label='SLO Threshold (200ms)')
        
        # Labels
        ax.set_title(scenario_labels[scenario_name], fontweight='bold')
        ax.set_xlabel("Run ID")
        ax.set_ylabel("p99 Latency (ms)")
        ax.set_ylim(0, max(p99_values) * 1.1 if p99_values else 1000)
        ax.grid(axis='y', alpha=0.3)
        
        # Add violation counts as text
        for i, (run_id, p99, viol) in enumerate(zip(run_ids, p99_values, violations)):
            if viol > 0:
                ax.text(run_id, p99 + 20, f'V:{viol}', ha='center', fontsize=8, color='red')
        
        # Legend
        if idx == 0:
            outlier_patch = mpatches.Patch(color='#ff6b6b', label='Outlier (excluded)')
            violation_patch = mpatches.Patch(color='#feca57', label='SLO violation')
            clean_patch = mpatches.Patch(color='#48dbfb', label='Clean run')
            ax.legend(handles=[outlier_patch, violation_patch, clean_patch, ax.lines[0]], loc='upper left')
    
    plt.tight_layout()
    
    # Save
    output_dir = Path(__file__).parent.parent / "results/experiments/phase-b/2026-02-12_replicated-20runs/figures"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "scenario_summary.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_path}")
    plt.close()

def plot_decision_comparison():
    """Plot decision counts by scenario."""
    experiments = load_phase_b_data()
    outliers = load_outliers()
    
    # Group by scenario (exclude outliers)
    scenarios = {}
    for exp in experiments:
        scenario = exp["scenario"]
        if is_outlier(scenario, exp["run_id"], outliers):
            continue
        if scenario not in scenarios:
            scenarios[scenario] = []
        scenarios[scenario].append(exp)
    
    # Aggregate decision counts
    scenario_labels = {
        "s1-k8s-only": "S1\nK8s",
        "s2-serverless-only": "S2\nServerless",
        "s3-hybrid-reactive": "S3\nReactive",
        "s4-hybrid-predictive": "S4\nPredictive"
    }
    
    scenario_order = ["s1-k8s-only", "s2-serverless-only", "s3-hybrid-reactive", "s4-hybrid-predictive"]
    
    # Count decisions
    maintain_counts = []
    scale_out_counts = []
    optimize_counts = []
    predictive_counts = []
    
    for scenario_name in scenario_order:
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
    
    x = np.arange(len(scenario_order))
    width = 0.6
    
    labels = [scenario_labels[s] for s in scenario_order]
    
    # Stacked bars
    p1 = ax.bar(x, maintain_counts, width, label='MAINTAIN', color='#95afc0')
    p2 = ax.bar(x, scale_out_counts, width, bottom=maintain_counts, label='SCALE_OUT', color='#eb4d4b')
    p3 = ax.bar(x, scale_out_counts, width, 
                bottom=np.array(maintain_counts) + np.array(scale_out_counts),
                label='OPTIMIZE_COST', color='#6ab04c')
    p4 = ax.bar(x, predictive_counts, width,
                bottom=np.array(maintain_counts) + np.array(scale_out_counts) + np.array(optimize_counts),
                label='PREDICTIVE', color='#f9ca24')
    
    ax.set_ylabel('Decision Count (Total Across Clean Runs)', fontweight='bold')
    ax.set_title('Routing Decisions by Scenario (Outliers Excluded)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    # Save
    output_dir = Path(__file__).parent.parent / "results/experiments/phase-b/2026-02-12_replicated-20runs/figures"
    output_path = output_dir / "decision_comparison.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_path}")
    plt.close()

def plot_clean_vs_outlier_comparison():
    """Compare statistics with and without outliers."""
    experiments = load_phase_b_data()
    outliers = load_outliers()
    
    scenarios = ["s1-k8s-only", "s2-serverless-only", "s3-hybrid-reactive", "s4-hybrid-predictive"]
    labels = ["S1\nK8s", "S2\nServerless", "S3\nReactive", "S4\nPredictive"]
    
    with_outliers = []
    without_outliers = []
    
    for scenario in scenarios:
        runs = [r for r in experiments if r["scenario"] == scenario]
        clean_runs = [r for r in runs if not is_outlier(scenario, r["run_id"], outliers)]
        
        p99_all = [r["p99_latency_ms"] for r in runs]
        p99_clean = [r["p99_latency_ms"] for r in clean_runs]
        
        with_outliers.append(np.mean(p99_all))
        without_outliers.append(np.mean(p99_clean))
    
    x = np.arange(len(scenarios))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars1 = ax.bar(x - width/2, with_outliers, width, label='With Outliers', color='#ff6b6b', alpha=0.7)
    bars2 = ax.bar(x + width/2, without_outliers, width, label='Without Outliers (Clean)', color='#48dbfb', alpha=0.7)
    
    ax.set_ylabel('Mean p99 Latency (ms)', fontweight='bold')
    ax.set_title('Impact of Outlier Exclusion on Mean p99', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    ax.axhline(y=200, color='red', linestyle='--', linewidth=2, alpha=0.5, label='SLO Threshold')
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.0f}ms',
                    ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    
    # Save
    output_dir = Path(__file__).parent.parent / "results/experiments/phase-b/2026-02-12_replicated-20runs/figures"
    output_path = output_dir / "outlier_impact.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_path}")
    plt.close()

def main():
    """Generate all visualizations."""
    print("=" * 80)
    print("PHASE B TIME-SERIES VISUALIZATION")
    print("=" * 80)
    
    print("\n📊 Generating plots...\n")
    
    plot_scenario_summary()
    plot_decision_comparison()
    plot_clean_vs_outlier_comparison()
    
    print("\n✅ All plots generated successfully!")
    print("\nOutput directory: results/experiments/phase-b/2026-02-12_replicated-20runs/figures/")
    print("\nGenerated files:")
    print("  1. scenario_summary.png - p99 latency by scenario (bar chart)")
    print("  2. decision_comparison.png - Routing decisions by scenario (stacked bar)")
    print("  3. outlier_impact.png - Impact of outlier exclusion (comparison)")

if __name__ == "__main__":
    main()
