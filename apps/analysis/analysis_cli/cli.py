"""Typer sub-app for experiment analysis CLI.

Each command is a thin wrapper over ``libs/analysis`` (domain) and
``libs/shared`` (stats primitives, scenario constants). Registered as
``thesis analysis <subcommand>`` via ``apps/cli/cli/main.py``.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import structlog
import typer
from analysis.cold_start import (
    analyze_phase_a1_transition,
    compute_scenario_stats,
    correlation_scale_out_p99,
    theoretical_cold_start_impact,
    variance_decomposition,
)
from analysis.comparison import apply_holm_bonferroni, run_pairwise_comparison
from analysis.constants import (
    CLOUD_NODES,
    COLD_START_MS_S3,
    COLD_START_MS_S4,
    DEFAULT_CLOUD_NODE,
    EKS_CONTROL_PLANE_RATE,
    H1_COMPARISONS,
    H2_COMPARISONS,
    LAMBDA_MEM_GB,
    LAMBDA_MEM_MB,
    LAMBDA_OVERHEAD_SEC,
    POD_CPU_REQUEST,
    POD_MEM_REQUEST_GIB,
    TARGET_CPU_UTIL,
    TARGET_MEM_UTIL,
)
from analysis.cost import analyze_from_experiment, compute_cost_proxy
from analysis.data_loaders import build_results_final, group_by_scenario, load_experiment_metrics, load_phase_b_data
from analysis.report import generate_report
from scipy import stats as scipy_stats
from shared.artifacts import read_provision_events, read_result_dict
from shared.scenarios import SCENARIO_ORDER
from shared.stats import bootstrap_ci, cohens_d, effect_size_label

logger = structlog.get_logger(__name__)

app = typer.Typer(help="Experiment analysis CLI", no_args_is_help=True)

# Default paths (relative to repo / worktree root).
DEFAULT_PHASE_B_DATA = Path("results/experiments/phase-b/2026-02-12_replicated-20runs/raw/experiments_final.json")


# ---------------------------------------------------------------------------
# 1. reanalyze
# ---------------------------------------------------------------------------


@app.command()
def reanalyze(
    results_dir: Path = typer.Option(..., "--results-dir", help="Path to experiment dir containing results_final.json"),
) -> None:
    """Phase B reanalysis: all 20 runs, no outlier exclusion.

    Runs H1 + H2 comparisons, Holm-Bonferroni correction, cost proxy, and
    writes reanalysis_report.md / reanalysis_statistics.json / cost_analysis.json
    into the results dir.
    """
    results_dir = results_dir.resolve()
    results_file = results_dir / "results_final.json"

    if not results_file.exists():
        logger.error("results_file_not_found", path=str(results_file))
        raise typer.Exit(1)

    with open(results_file) as f:
        results: list[dict] = json.load(f)

    logger.info("loaded_results", count=len(results), path=str(results_file))

    # -- Run all comparisons --
    all_comparisons: list = []

    h1_comps = []
    for baseline, comp, metric, label in H1_COMPARISONS:
        try:
            c = run_pairwise_comparison(results, baseline, comp, metric, label)
            h1_comps.append(c)
            all_comparisons.append(c)
        except ValueError as e:
            logger.warning("comparison_skipped", error=str(e))

    h2_comps = []
    for baseline, comp, metric, label in H2_COMPARISONS:
        try:
            c = run_pairwise_comparison(results, baseline, comp, metric, label)
            h2_comps.append(c)
            all_comparisons.append(c)
        except ValueError as e:
            logger.warning("comparison_skipped", error=str(e))

    # -- Holm-Bonferroni correction across ALL tests --
    apply_holm_bonferroni(all_comparisons)

    # -- Cost proxy --
    cost = compute_cost_proxy(results)

    # -- Generate outputs --
    report = generate_report(results, h1_comps, h2_comps, cost)

    report_path = results_dir / "reanalysis_report.md"
    with open(report_path, "w") as f:
        f.write(report)
    logger.info("wrote_report", path=str(report_path))

    stats_path = results_dir / "reanalysis_statistics.json"
    with open(stats_path, "w") as f:
        json.dump([c.model_dump() for c in all_comparisons], f, indent=2)
    logger.info("wrote_statistics", path=str(stats_path))

    cost_path = results_dir / "cost_analysis.json"
    with open(cost_path, "w") as f:
        json.dump(cost, f, indent=2, default=str)
    logger.info("wrote_cost_analysis", path=str(cost_path))

    print(report)


@app.command(name="results-final")
def results_final_cmd(
    results_dir: Path = typer.Option(
        ...,
        "--results-dir",
        help="Path to experiment bundle dir containing per-run result.json",
    ),
    include_invalid: bool = typer.Option(
        False,
        "--include-invalid",
        help="Include runs that failed validity gates",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print projected record count without writing",
    ),
) -> None:
    """Project a bundle's per-run result.json files into legacy results_final.json.

    Lets ``thesis analysis reanalyze --results-dir <bundle>`` work on modern
    schema-v1/schema-v2 bundles. Writes results_final.json into the bundle root.
    """
    results_dir = results_dir.resolve()
    results = build_results_final(results_dir, include_invalid)

    if not results:
        typer.echo(f"No valid result.json records found in {results_dir}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Projected {len(results)} runs:")
    for scenario, runs in sorted(group_by_scenario(results).items()):
        typer.echo(f"  {scenario}: {len(runs)}")

    if not dry_run:
        output_path = results_dir / "results_final.json"
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        typer.echo(f"Wrote {output_path}")


# ---------------------------------------------------------------------------
# 2. robust-stats
# ---------------------------------------------------------------------------


@app.command(name="robust-stats")
def robust_stats(
    data_file: Path = typer.Option(DEFAULT_PHASE_B_DATA, "--data-file", help="Path to experiments_final.json"),
) -> None:
    """Robust statistical analysis (outliers excluded): Welch, Mann-Whitney, bootstrap, Cohen's d."""
    experiments = load_phase_b_data(data_file, exclude_outliers=True)

    print("=" * 80)
    print("ROBUST STATISTICAL ANALYSIS - PHASE B")
    print("=" * 80)

    # Filter data
    scenarios: dict[str, list[dict]] = {}
    for exp in experiments:
        scenarios.setdefault(exp["scenario"], []).append(exp)

    # Extract p99 values
    s1_p99 = [r["p99_latency_ms"] for r in scenarios["s1-k8s-only"]]
    s2_p99 = [r["p99_latency_ms"] for r in scenarios["s2-serverless-only"]]
    s3_p99 = [r["p99_latency_ms"] for r in scenarios["s3-hybrid-reactive"]]
    s4_p99 = [r["p99_latency_ms"] for r in scenarios["s4-hybrid-predictive"]]

    print("\n📊 Clean Data Sample Sizes (Outliers Excluded):")
    print(f"   S1 (K8s-only): n={len(s1_p99)}")
    print(f"   S2 (Serverless): n={len(s2_p99)}")
    print(f"   S3 (Reactive): n={len(s3_p99)}")
    print(f"   S4 (Predictive): n={len(s4_p99)}")

    print("\n" + "=" * 80)
    print("DESCRIPTIVE STATISTICS (Clean Data)")
    print("=" * 80)

    for name, data in [("S1", s1_p99), ("S2", s2_p99), ("S3", s3_p99), ("S4", s4_p99)]:
        mean = np.mean(data)
        std = np.std(data, ddof=1)
        median = np.median(data)
        lower_ci, upper_ci = bootstrap_ci(data)

        print(f"\n{name}:")
        print(f"   Mean: {mean:.1f}ms")
        print(f"   Std: {std:.1f}ms")
        print(f"   Median: {median:.1f}ms")
        print(f"   95% CI: [{lower_ci:.1f}, {upper_ci:.1f}]ms")

    print("\n" + "=" * 80)
    print("H1: S4 (Hybrid Predictive) vs S1 (K8s-only)")
    print("=" * 80)

    # Welch's t-test
    t_stat, p_value = scipy_stats.ttest_ind(s4_p99, s1_p99, equal_var=False)

    # Mann-Whitney U (non-parametric)
    u_stat, p_value_mw = scipy_stats.mannwhitneyu(s4_p99, s1_p99, alternative="two-sided")

    # Cohen's d
    effect_size = cohens_d(s4_p99, s1_p99)

    print("\n📊 Welch's t-test (unequal variances):")
    print(f"   t = {t_stat:.3f}")
    print(f"   p = {p_value:.4f}")
    print(f"   Result: {'Significant' if p_value < 0.05 else 'NOT significant'} at α=0.05")

    print("\n📊 Mann-Whitney U test (non-parametric):")
    print(f"   U = {u_stat:.1f}")
    print(f"   p = {p_value_mw:.4f}")
    print(f"   Result: {'Significant' if p_value_mw < 0.05 else 'NOT significant'} at α=0.05")

    print("\n📊 Effect Size (Cohen's d):")
    print(f"   d = {effect_size:.3f}")
    interpretation = effect_size_label(effect_size)
    print(f"   Interpretation: {interpretation} effect")

    print("\n💡 Practical Difference:")
    print(f"   S4 mean: {np.mean(s4_p99):.1f}ms")
    print(f"   S1 mean: {np.mean(s1_p99):.1f}ms")
    print(
        f"   Difference: {np.mean(s4_p99) - np.mean(s1_p99):.1f}ms "
        f"({((np.mean(s4_p99) - np.mean(s1_p99)) / np.mean(s1_p99)) * 100:.1f}%)"
    )

    print("\n" + "=" * 80)
    print("H2: S4 (Hybrid Predictive) vs S3 (Hybrid Reactive)")
    print("=" * 80)

    # Welch's t-test
    t_stat2, p_value2 = scipy_stats.ttest_ind(s4_p99, s3_p99, equal_var=False)

    # Mann-Whitney U
    u_stat2, p_value_mw2 = scipy_stats.mannwhitneyu(s4_p99, s3_p99, alternative="two-sided")

    # Cohen's d
    effect_size2 = cohens_d(s4_p99, s3_p99)

    print("\n📊 Welch's t-test:")
    print(f"   t = {t_stat2:.3f}")
    print(f"   p = {p_value2:.4f}")
    print(f"   Result: {'Significant' if p_value2 < 0.05 else 'NOT significant'} at α=0.05")

    print("\n📊 Mann-Whitney U test:")
    print(f"   U = {u_stat2:.1f}")
    print(f"   p = {p_value_mw2:.4f}")
    print(f"   Result: {'Significant' if p_value_mw2 < 0.05 else 'NOT significant'} at α=0.05")

    print("\n📊 Effect Size (Cohen's d):")
    print(f"   d = {effect_size2:.3f}")
    interpretation2 = effect_size_label(effect_size2)
    print(f"   Interpretation: {interpretation2} effect")

    print("\n💡 Practical Difference:")
    print(f"   S4 mean: {np.mean(s4_p99):.1f}ms")
    print(f"   S3 mean: {np.mean(s3_p99):.1f}ms")
    print(f"   Difference: {np.mean(s4_p99) - np.mean(s3_p99):.1f}ms")

    # Violations
    s3_violations = sum(1 for r in scenarios["s3-hybrid-reactive"] if r["slo_violation_count"] > 0)
    s4_violations = sum(1 for r in scenarios["s4-hybrid-predictive"] if r["slo_violation_count"] > 0)

    print("\n📊 SLO Violations:")
    print(f"   S3: {s3_violations}/{len(s3_p99)} runs ({s3_violations / len(s3_p99) * 100:.0f}%)")
    print(f"   S4: {s4_violations}/{len(s4_p99)} runs ({s4_violations / len(s4_p99) * 100:.0f}%)")

    print("\n" + "=" * 80)
    print("FINAL VERDICT")
    print("=" * 80)

    print(f"""
H1 (Hybrid vs K8s-only):
  • Statistical significance: NOT established (p={p_value:.4f})
  • Effect size: {interpretation} (d={effect_size:.3f})
  • Practical difference: S4 {np.mean(s4_p99) - np.mean(s1_p99):.0f}ms faster
  • Conclusion: Mechanism validated, superiority not statistically proven

H2 (Predictive vs Reactive):
  • Statistical significance: NOT established (p={p_value2:.4f})
  • Effect size: {interpretation2} (d={effect_size2:.3f})
  • Violations: Both 100% (S3 4/4, S4 5/5)
  • Root cause: GRU not running in Phase B
  • Conclusion: Mechanism validated in Phase A1, no predictive actions in Phase B
""")

    # Export
    output = {
        "h1": {
            "s4_mean": float(np.mean(s4_p99)),
            "s1_mean": float(np.mean(s1_p99)),
            "difference": float(np.mean(s4_p99) - np.mean(s1_p99)),
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "mann_whitney_u": float(u_stat),
            "p_value_mw": float(p_value_mw),
            "cohens_d": float(effect_size),
            "significant": bool(p_value < 0.05),
        },
        "h2": {
            "s4_mean": float(np.mean(s4_p99)),
            "s3_mean": float(np.mean(s3_p99)),
            "difference": float(np.mean(s4_p99) - np.mean(s3_p99)),
            "t_statistic": float(t_stat2),
            "p_value": float(p_value2),
            "mann_whitney_u": float(u_stat2),
            "p_value_mw": float(p_value_mw2),
            "cohens_d": float(effect_size2),
            "significant": bool(p_value2 < 0.05),
        },
    }

    output_path = data_file.parent.parent / "statistical_analysis.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n💾 Exported to: {output_path}")


# ---------------------------------------------------------------------------
# 3. cost
# ---------------------------------------------------------------------------


@app.command()
def cost(
    experiment_dir: Path = typer.Option(
        None, "--experiment-dir", help="Path to experiment results dir with per-scenario subdirs (result.json)"
    ),
    crossover_graph: bool = typer.Option(
        False, "--crossover-graph", help="Generate analytical S1 vs S2 crossover graph"
    ),
) -> None:
    """Unified AWS cloud cost analysis from experiment results."""
    from analysis_cli.crossover import (
        CF_BASE_FEE,
        CF_CPU_MS_RATE,
        CF_FREE_CPU_MS,
        CF_FREE_REQUESTS,
        CF_REQUEST_RATE,
        GCP_FREE_GB_SEC,
        GCP_FREE_REQUESTS,
        GCP_FREE_VCPU_SEC,
        GCP_MEM_GB_SEC_RATE,
        GCP_REQUEST_RATE,
        GCP_VCPU_SEC_RATE,
        generate_crossover_graph,
    )

    if crossover_graph:
        raise typer.Exit(generate_crossover_graph(Path("results/cost")))

    if experiment_dir is None:
        print("Error: --experiment-dir is required (or use --crossover-graph)")
        raise typer.Exit(1)

    experiment_dir = experiment_dir.resolve()
    result_files = sorted(experiment_dir.glob("*/result.json"))
    if not result_files:
        logger.error("no_result_files", dir=str(experiment_dir))
        raise typer.Exit(1)

    results: list[dict] = []
    for rf in result_files:
        logger.info("loading_scenario", path=str(rf))
        metrics = load_experiment_metrics(rf)

        # Load provision events for per-node lifetime computation (scale-down aware)
        provision_events = read_provision_events(rf.parent)

        analysis = analyze_from_experiment(metrics, provision_events=provision_events)
        # Attach cluster utilization from result.json (not in ScenarioMetrics)
        raw_result = read_result_dict(rf.parent)
        analysis["avg_cluster_cpu_pct"] = raw_result.get("avg_cluster_cpu_utilization_pct", 0)
        analysis["peak_cluster_cpu_pct"] = raw_result.get("peak_cluster_cpu_utilization_pct", 0)
        analysis["avg_cluster_mem_pct"] = raw_result.get("avg_cluster_mem_utilization_pct", 0)
        results.append(analysis)

    # Print summary
    print("\n" + "=" * 80)
    print("UNIFIED AWS COST ANALYSIS — {} Scenarios".format(len(results)))
    print("K8s → EKS + EC2 | Knative → Lambda PC | Lambda mem: {}MB".format(LAMBDA_MEM_MB))
    print(
        "EC2: {} (alloc {:.1f} vCPU) | EKS: ${:.2f}/hr | Lambda overhead: {}ms".format(
            DEFAULT_CLOUD_NODE,
            CLOUD_NODES[DEFAULT_CLOUD_NODE]["allocatable_cpu"],
            EKS_CONTROL_PLANE_RATE,
            int(LAMBDA_OVERHEAD_SEC * 1000),
        )
    )
    print("=" * 80)

    # Resource consumption
    print(f"\n{'Metric':<30}", end="")
    for r in results:
        print(f" {r['scenario'][:14]:>14}", end="")
    print()
    print("-" * (30 + 15 * len(results)))

    for label, key, fmt in [
        ("Total requests", "total_requests", "{:>14,}"),
        ("Successful requests", "successful_requests", "{:>14,}"),
        ("SLO-compliant req", "slo_compliant_requests", "{:>14,}"),
        ("SLO non-compliant", "slo_noncompliant_requests", "{:>14,}"),
        ("Success rate", "success_rate", "{:>13.1%}"),
        ("RPS", "rps", "{:>14.1f}"),
        ("Successful RPS", "successful_rps", "{:>14.1f}"),
        ("Serverless traffic %", "serverless_traffic_pct", "{:>13.1f}%"),
        ("Serverless requests", "serverless_requests", "{:>14,}"),
        ("K8s CPU-seconds", "k8s_cpu_seconds", "{:>14.1f}"),
        ("Knative CPU-seconds", "knative_cpu_seconds", "{:>14.1f}"),
        ("Cluster CPU util %", "avg_cluster_cpu_pct", "{:>13.1f}%"),
        ("Peak cluster CPU %", "peak_cluster_cpu_pct", "{:>13.1f}%"),
        ("Cluster mem util %", "avg_cluster_mem_pct", "{:>13.1f}%"),
        ("Knative mem GiB-seconds", "knative_mem_gib_seconds", "{:>14.1f}"),
        ("CPU/request (ms@1vCPU)", "cpu_per_request_ms", "{:>14.2f}"),
        ("Lambda exec time (ms)", "lambda_exec_time_ms", "{:>14.1f}"),
        ("Lambda PC instances", "lambda_pc_instances", "{:>14}"),
        ("EC2 production nodes", "production_nodes", "{:>14}"),
    ]:
        print(f"  {label:<28}", end="")
        for r in results:
            val = r[key]
            print(f" {fmt.format(val)}", end="")
        print()

    # Unified AWS cost breakdown
    print("\n--- Unified AWS Cost Breakdown ---")
    for comp in ["eks_control_plane", "ec2_compute", "lambda_capacity", "lambda_execution", "lambda_requests", "total"]:
        label = comp.replace("_", " ").title()
        print(f"  {label:<28}", end="")
        for r in results:
            val = r["aws_cost"][comp]
            print(f" ${val:>13.4f}", end="")
        print()

    # Per-request costs
    print("\n--- $/1M Requests ---")
    print(f"  {'AWS Total':<28}", end="")
    for r in results:
        print(f" ${r['per_million_requests']:>13.2f}", end="")
    print()

    print("\n--- $/1M Successful Requests ---")
    print(f"  {'AWS Total':<28}", end="")
    for r in results:
        print(f" ${r['per_million_successful']:>13.2f}", end="")
    print()

    print("\n--- $/1M SLO-Compliant Requests ---")
    print(f"  {'AWS Total':<28}", end="")
    for r in results:
        print(f" ${r['per_million_slo_compliant']:>13.2f}", end="")
    print()

    print("\n--- Fairness-Normalized Throughput per $ ---")
    print(f"  {'Successful req / $':<28}", end="")
    for r in results:
        print(f" {r['successful_requests_per_usd']:>14.2f}", end="")
    print()

    # Monthly projection
    if results:
        scale = 30 * 24 * 3600 / results[0]["duration_sec"]
        print("\n--- Monthly Projection (30d continuous) ---")
        print(f"  {'AWS Total':<28}", end="")
        for r in results:
            print(f" ${r['aws_cost']['total'] * scale:>13.0f}", end="")
        print()

        # Multi-cloud serverless projection (for serverless traffic only)
        print("\n--- Multi-Cloud Serverless Monthly Projection ---")
        print(f"  {'AWS Lambda':<28}", end="")
        for r in results:
            lambda_monthly = r["aws_cost"]["lambda_capacity"] + r["aws_cost"]["lambda_execution"]
            lambda_monthly += r["aws_cost"].get("lambda_requests", 0)
            lambda_monthly += r["aws_cost"].get("lambda_overflow", 0)
            lambda_monthly += r["aws_cost"].get("data_transfer", 0)
            print(f" ${lambda_monthly * scale:>13.0f}", end="")
        print()

        print(f"  {'GCP Cloud Run':<28}", end="")
        for r in results:
            rps = r["rps"]
            exec_sec = r["lambda_exec_time_ms"] / 1000
            cpu_per_req = r["cpu_per_request_ms"] / 1000
            mem_gb = LAMBDA_MEM_GB
            monthly_req = rps * 730 * 3600
            billable_req = max(0, monthly_req - GCP_FREE_REQUESTS)
            vcpu_sec = monthly_req * cpu_per_req
            gb_sec = monthly_req * mem_gb * exec_sec
            gcp_cost = (
                billable_req / 1e6 * GCP_REQUEST_RATE
                + max(0, vcpu_sec - GCP_FREE_VCPU_SEC) * GCP_VCPU_SEC_RATE
                + max(0, gb_sec - GCP_FREE_GB_SEC) * GCP_MEM_GB_SEC_RATE
            )
            print(f" ${gcp_cost:>13.0f}", end="")
        print()

        print(f"  {'Cloudflare Workers':<28}", end="")
        for r in results:
            rps = r["rps"]
            cpu_ms_per_req = r["cpu_per_request_ms"]
            monthly_req = rps * 730 * 3600
            billable_req = max(0, monthly_req - CF_FREE_REQUESTS)
            total_cpu_ms = monthly_req * cpu_ms_per_req
            cf_cost = (
                CF_BASE_FEE
                + billable_req / 1e6 * CF_REQUEST_RATE
                + max(0, total_cpu_ms - CF_FREE_CPU_MS) / 1e6 * CF_CPU_MS_RATE
            )
            print(f" ${cf_cost:>13.0f}", end="")
        print()

    # Stress-harness reference
    print("\n--- Stress-Harness EC2 (appendix reference) ---")
    for comp in ["base_node", "dynamic_nodes", "total"]:
        label = comp.replace("_", " ").title()
        print(f"  {label:<28}", end="")
        for r in results:
            val = r["stress_harness_ec2"][comp]
            print(f" ${val:>13.4f}", end="")
        print()

    # Save results
    output_dir = Path("results/cost_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"cost_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "experiment_dir": str(experiment_dir),
                "config": {
                    "version": "v5",
                    "model": "unified_aws",
                    "architecture_mapping": "K8s→EKS+EC2, Knative→Lambda",
                    "lambda_mem_mb": LAMBDA_MEM_MB,
                    "lambda_overhead_ms": LAMBDA_OVERHEAD_SEC * 1000,
                    "pod_cpu_request": POD_CPU_REQUEST,
                    "pod_mem_request_gib": POD_MEM_REQUEST_GIB,
                    "target_cpu_util": TARGET_CPU_UTIL,
                    "target_mem_util": TARGET_MEM_UTIL,
                    "cloud_node_type": DEFAULT_CLOUD_NODE,
                    "cloud_node_allocatable_cpu": CLOUD_NODES[DEFAULT_CLOUD_NODE]["allocatable_cpu"],
                    "cloud_node_allocatable_mem_gib": CLOUD_NODES[DEFAULT_CLOUD_NODE]["allocatable_mem_gib"],
                    "cloud_node_rate": CLOUD_NODES[DEFAULT_CLOUD_NODE]["rate"],
                    "eks_control_plane_rate": EKS_CONTROL_PLANE_RATE,
                },
                "scenarios": results,
            },
            f,
            indent=2,
        )
    print(f"\nResults saved to: {output_file}")


# ---------------------------------------------------------------------------
# 4. cold-start
# ---------------------------------------------------------------------------


@app.command(name="cold-start")
def cold_start(
    base_path: Path = typer.Option(Path("."), "--base-path", help="Repo/worktree root (anchors results/ paths)"),
) -> None:
    """Cold-start vs warm-start latency decomposition + variance model."""
    base_path = base_path.resolve()

    phase_b_data = base_path / "results/experiments/phase-b/2026-02-12_replicated-20runs/raw/experiments_final.json"

    print("=" * 80)
    print("COLD START vs WARM START LATENCY DECOMPOSITION")
    print("=" * 80)

    # 1. Load and analyze Phase B data
    print("\n## Phase B: Per-Scenario Statistics (excluding outliers)")
    print("-" * 60)

    data = load_phase_b_data(phase_b_data, exclude_outliers=True)
    grouped = group_by_scenario(data)

    stats_map = {}
    for scenario in SCENARIO_ORDER:
        runs = grouped.get(scenario, [])
        s = compute_scenario_stats(scenario, runs)
        stats_map[scenario] = s
        print(f"\n### {scenario} (n={s.n_runs})")
        print(f"  p99: mean={s.p99_mean:.1f}ms, std={s.p99_std:.1f}ms, CoV={s.p99_cov:.1f}%")
        print(f"  p99: min={s.p99_min:.1f}ms, max={s.p99_max:.1f}ms, median={s.p99_median:.1f}ms")
        print(f"  p95: mean={s.p95_mean:.1f}ms, p50: mean={s.p50_mean:.1f}ms")
        print(f"  throughput: {s.throughput_mean:.1f} RPS")
        print(f"  avg scale_out: {s.avg_scale_out_count:.1f}, avg total decisions: {s.avg_total_decisions:.1f}")

    # 2. Correlation: scale_out_count vs p99
    print("\n\n## Correlation: scale_out_count vs p99 (hybrid scenarios)")
    print("-" * 60)

    for scenario in ["s3-hybrid-reactive", "s4-hybrid-predictive"]:
        runs = grouped.get(scenario, [])
        r = correlation_scale_out_p99(runs)
        if r is not None:
            print(f"  {scenario}: r={r:.3f} (n={len(runs)})")
            if abs(r) > 0.5:
                print("    → Moderate-to-strong correlation: more scale-outs ↔ higher p99")
            elif abs(r) > 0.3:
                print("    → Weak correlation")
            else:
                print("    → No meaningful correlation")
        else:
            print(f"  {scenario}: insufficient data")

    # 3. Variance decomposition
    print("\n\n## Variance Decomposition")
    print("-" * 60)

    decomp = variance_decomposition(stats_map)
    if decomp:
        print(f"  Base variance (avg S1+S2): σ²={decomp['base_variance']:.0f}, σ={decomp['base_std']:.1f}ms")
        print(f"  S1 variance: σ²={decomp['s1_variance']:.0f}, σ={stats_map['s1-k8s-only'].p99_std:.1f}ms")
        print(f"  S2 variance: σ²={decomp['s2_variance']:.0f}, σ={stats_map['s2-serverless-only'].p99_std:.1f}ms")
        print(
            f"  S3 total variance: σ²={decomp['s3_total_variance']:.0f}, "
            f"σ={stats_map['s3-hybrid-reactive'].p99_std:.1f}ms"
        )
        print(
            f"  S3 excess (cold start + routing): σ²={decomp['s3_excess_variance']:.0f}, "
            f"σ={decomp['s3_excess_std']:.1f}ms"
        )
        print(f"  S3 % from cold start/routing: {decomp['s3_pct_from_cold_start']:.1f}%")
        print(
            f"  S4 total variance: σ²={decomp['s4_total_variance']:.0f}, "
            f"σ={stats_map['s4-hybrid-predictive'].p99_std:.1f}ms"
        )
        print(
            f"  S4 excess (cold start + routing): σ²={decomp['s4_excess_variance']:.0f}, "
            f"σ={decomp['s4_excess_std']:.1f}ms"
        )
        print(f"  S4 % from cold start/routing: {decomp['s4_pct_from_cold_start']:.1f}%")

    # 4. Phase A1 transition analysis
    print("\n\n## Phase A1: Weight Transition Cold Start Analysis")
    print("-" * 60)

    a1 = analyze_phase_a1_transition()
    print(f"  p99 before serverless (100/0): {a1['p99_before_serverless']:.0f}ms")
    print(f"  p99 at first SCALE_OUT (90/10): {a1['p99_at_first_scale_out']:.0f}ms")
    print(f"  p99 warm state mean: {a1['p99_warm_state_mean']:.0f}ms")
    print(f"  Measured cold start S3: {a1['cold_start_measured_s3']:.0f}ms")
    print(f"  Measured cold start S4: {a1['cold_start_measured_s4']:.0f}ms")
    print(f"  Average cold start: {a1['cold_start_average']:.0f}ms")

    print("\n  Weight ramp trajectory (decisions 3-7):")
    for d in a1["transition_decisions"]:
        k3s, kn = d["weights"]
        print(f"    Decision {d['decision']}: {d['action']:15s} p99={d['p99_ms']:.0f}ms  weights={k3s}/{kn}")

    print("\n  Warm state decisions:")
    for d in a1["warm_decisions"]:
        k3s, kn = d["weights"]
        print(f"    Decision {d['decision']}: {d['action']:15s} p99={d['p99_ms']:.0f}ms  weights={k3s}/{kn}")

    # 5. Theoretical cold start impact
    print("\n\n## Theoretical Cold Start Impact Model")
    print("-" * 60)

    for cs_ms, label in [
        (COLD_START_MS_S3, "S3 (682ms)"),
        (COLD_START_MS_S4, "S4 (1235ms)"),
        (958.0, "Average (958ms)"),
    ]:
        impact = theoretical_cold_start_impact(
            rps=100,
            duration_sec=300,
            cold_start_ms=cs_ms,
            weight_at_transition=10,
            n_scale_out_events=1,
            cold_start_duration_sec=5.0,
        )
        # Derived values (the libs model returns the core fields; compute the
        # presentation-only fraction + estimated p99 to match the original output).
        cold_start_fraction = (
            impact["cold_start_requests"] / impact["total_requests"] if impact["total_requests"] > 0 else 0
        )
        estimated_p99 = cs_ms if impact["cold_start_dominates_p99"] else None

        print(f"\n  ### {label}:")
        print(f"    Total requests: {impact['total_requests']}")
        print(f"    Cold-start affected requests: {impact['cold_start_requests']}")
        print(f"    p99 threshold (top 1%): {impact['p99_threshold_count']} requests")
        print(f"    Cold start fraction: {cold_start_fraction:.3%}")
        print(f"    Cold start dominates p99: {impact['cold_start_dominates_p99']}")
        if estimated_p99:
            print(f"    → Estimated p99 ≈ {estimated_p99:.0f}ms (cold start latency)")

    # 6. Summary
    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    cs_penalty = a1["cold_start_average"]
    warm_p99 = a1["p99_warm_state_mean"]

    # decomp may be None if S1/S2 p99 data is missing; guard the summary values.
    if decomp:
        base_std = decomp["base_std"]
        s3_excess_std = decomp["s3_excess_std"]
        s3_pct_from_cold_start = decomp["s3_pct_from_cold_start"]
    else:
        base_std = s3_excess_std = s3_pct_from_cold_start = 0.0

    print(f"""
  Cold Start Penalty Estimate:
    Measured range: {COLD_START_MS_S3:.0f}-{COLD_START_MS_S4:.0f}ms (avg {cs_penalty:.0f}ms)
    Warm state p99: {warm_p99:.0f}ms
    Cold start overhead: {cs_penalty - warm_p99:.0f}ms above warm state

  Variance Attribution (S3 reactive):
    Total p99 std: {stats_map["s3-hybrid-reactive"].p99_std:.0f}ms
    Base std (no routing): {base_std:.0f}ms
    Excess std (cold start + routing): {s3_excess_std:.0f}ms
    → {s3_pct_from_cold_start:.0f}% of S3 variance attributable to cold start/routing

  Correlation (scale_out ↔ p99):""")

    for scenario in ["s3-hybrid-reactive", "s4-hybrid-predictive"]:
        r = correlation_scale_out_p99(grouped.get(scenario, []))
        print(f"    {scenario}: r={r:.3f}" if r else f"    {scenario}: N/A")

    print(f"""
  Data Limitations:
    ⚠ No per-request latency data (only run-level aggregates)
    ⚠ No per-backend tagging (cannot separate k3s vs knative latency)
    ⚠ GRU was not running in Phase B (S4 fell back to reactive)
    ⚠ Cold start measurements from infra tests, not Phase B runs
    ⚠ Phase A1 had ramp load profile; Phase B used constant load

  Recommendations:
    1. Set minScale=1 to avoid cold starts (eliminates ~{cs_penalty:.0f}ms penalty)
    2. Keep pre-warming in SCALE_OUT path (already implemented)
    3. Collect per-request latency with backend tags in future experiments
    4. Run Phase B with GRU enabled to validate S4 predictive advantage
""")

    # Write JSON output for further analysis
    output = {
        "cold_start_penalty": {
            "measured_s3_ms": COLD_START_MS_S3,
            "measured_s4_ms": COLD_START_MS_S4,
            "average_ms": cs_penalty,
            "warm_state_p99_ms": warm_p99,
            "overhead_ms": cs_penalty - warm_p99,
        },
        "scenario_stats": {
            k: {
                "n_runs": v.n_runs,
                "p99_mean": round(v.p99_mean, 1),
                "p99_std": round(v.p99_std, 1),
                "p99_cov": round(v.p99_cov, 1),
                "avg_scale_out": round(v.avg_scale_out_count, 1),
            }
            for k, v in stats_map.items()
        },
        "variance_decomposition": {k: round(v, 1) if isinstance(v, float) else v for k, v in (decomp or {}).items()},
        "correlations": {
            scenario: round(correlation_scale_out_p99(grouped.get(scenario, [])) or 0, 3)
            for scenario in ["s3-hybrid-reactive", "s4-hybrid-predictive"]
        },
    }

    output_path = base_path / "results/experiments/phase-b/2026-02-12_replicated-20runs/cold_start_decomposition.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  JSON output written to: {output_path.relative_to(base_path)}")


# ---------------------------------------------------------------------------
# 5. hypotheses
# ---------------------------------------------------------------------------


@app.command()
def hypotheses() -> None:
    """Validate all three thesis hypotheses (H1, H2, H3)."""
    from analysis_cli.hypotheses import validate_all

    rc = validate_all()
    raise typer.Exit(rc)


# ---------------------------------------------------------------------------
# 6. plots
# ---------------------------------------------------------------------------


@app.command()
def plots(
    repo_root: Path = typer.Option(Path("."), "--repo-root", help="Repo root anchoring results/ paths"),
    output_dir: Path = typer.Option(
        None, "--output-dir", help="Figures output dir (default: results/experiments/figures)"
    ),
) -> None:
    """Generate thesis-quality matplotlib figures (decision timeline, boxplots, dashboard)."""
    from analysis_cli.plots import generate_all_plots

    raise typer.Exit(generate_all_plots(repo_root.resolve(), output_dir.resolve() if output_dir else None))


# ---------------------------------------------------------------------------
# 7. timeseries
# ---------------------------------------------------------------------------


@app.command()
def timeseries(
    repo_root: Path = typer.Option(Path("."), "--repo-root", help="Repo root anchoring results/ paths"),
    output_dir: Path = typer.Option(None, "--output-dir", help="Figures output dir"),
) -> None:
    """Generate Phase B time-series visualizations (scenario summary, decisions, outlier impact)."""
    from analysis_cli.timeseries import generate_all_timeseries

    repo_root = repo_root.resolve()
    phase_b_data = repo_root / "results/experiments/phase-b/2026-02-12_replicated-20runs/raw/experiments_final.json"
    outliers_data = repo_root / "results/experiments/phase-b/2026-02-12_replicated-20runs/raw/outliers.json"
    if output_dir is None:
        output_dir = repo_root / "results/experiments/phase-b/2026-02-12_replicated-20runs/figures"

    generate_all_timeseries(phase_b_data, outliers_data, output_dir.resolve())


# ---------------------------------------------------------------------------
# 8. gru-metrics
# ---------------------------------------------------------------------------


@app.command(name="gru-metrics")
def gru_metrics(
    output_dir: Path = typer.Option(None, "--output-dir", help="Output dir for percentage_metrics.json"),
) -> None:
    """Compute GRU MAE% and MAPE from training metrics."""
    from analysis_cli.gru_metrics import compute_percentage_metrics

    compute_percentage_metrics(output_dir.resolve() if output_dir else None)


# ---------------------------------------------------------------------------
# Bundle evidence: the tables a reader asks a finished bundle for
# ---------------------------------------------------------------------------


def _emit_json(payload) -> None:
    """The machine-readable half: the same fields the table prints, as data."""
    typer.echo(json.dumps(payload, indent=2, default=str))


@app.command()
def runs(
    bundle: Path = typer.Argument(..., help="Bundle directory holding per-run result.json files"),
    as_json: bool = typer.Option(False, "--json", help="Emit the payload as JSON instead of a table"),
) -> None:
    """What each run measured, and the conditions it was measured under."""
    from analysis.bundle_evidence import as_payload, run_evidence

    rows = run_evidence(bundle)
    if as_json:
        _emit_json(as_payload(rows))
        return
    header = (
        f"{'scenario':22} {'run':>3} {'valid':>5} {'p99 ms':>8} {'slo':>6} "
        f"{'nodes':>5} {'delay s':>7} {'delivered':>9} {'load':>5}"
    )
    typer.echo(header)
    for row in rows:
        typer.echo(
            f"{row.scenario:22} {row.run_id:3} {str(row.valid):>5} {row.p99_latency_ms:8.1f} "
            f"{row.slo_violations:6} {row.nodes_provisioned:5} {row.first_provision_delay_sec:7.1f} "
            f"{str(row.prediction_delivered):>9} "
            f"{(f'{row.host_load_ratio:.3f}' if row.host_load_ratio is not None else 'n/a'):>5}"
        )
    typer.echo(f"\n{len(rows)} run(s); host load is the conditions gate's busy-to-cores ratio.")


@app.command()
def mechanism(
    bundle: Path = typer.Argument(..., help="Bundle directory holding per-run artifacts"),
    as_json: bool = typer.Option(False, "--json", help="Emit the payload as JSON"),
) -> None:
    """When the node tier arrived relative to the load, beside the tail it explains."""
    from analysis.bundle_evidence import as_payload, mechanism_rows

    rows = mechanism_rows(bundle)
    if as_json:
        _emit_json(as_payload(rows))
        return
    typer.echo(f"{'scenario':22} {'run':>3} {'p99 ms':>8} {'prov delay s':>12} {'node at +s':>10} {'% serverless':>12}")
    for row in rows:
        offset = f"{row.node_arrival_offset_sec:.1f}" if row.node_arrival_offset_sec is not None else "n/a"
        share = f"{row.serverless_share_pct:.1f}" if row.serverless_share_pct is not None else "n/a"
        typer.echo(
            f"{row.scenario:22} {row.run_id:3} {row.p99_latency_ms:8.1f} "
            f"{row.provisioning_delay_sec:12.1f} {offset:>10} {share:>12}"
        )
    typer.echo("\nnode at +s is measured from the run's first provisioner event.")


@app.command()
def variance(
    bundle: Path = typer.Argument(..., help="Bundle directory holding per-run result.json files"),
    as_json: bool = typer.Option(False, "--json", help="Emit the payload as JSON"),
) -> None:
    """How far each arm moved run to run, and what n pairs can resolve."""
    from analysis.bundle_evidence import as_payload, variance_summary

    summary = variance_summary(bundle)
    if as_json:
        _emit_json(as_payload(summary))
        return
    typer.echo(f"{'scenario':22} {'n':>3} {'mean p99':>9} {'sd':>7} {'min':>8} {'max':>8}")
    for arm in summary.arms:
        typer.echo(
            f"{arm.scenario:22} {arm.n:3} {arm.mean_p99_ms:9.1f} {arm.sd_p99_ms:7.1f} "
            f"{arm.min_p99_ms:8.1f} {arm.max_p99_ms:8.1f}"
        )
    if summary.n_pairs:
        diffs = " ".join(f"{d:+.1f}" for d in summary.pair_differences_ms)
        typer.echo(f"\npaired differences (ms): {diffs}")
        typer.echo(f"mean {summary.mean_difference_ms:+.1f} ms", nl=False)
        if summary.sd_difference_ms is not None:
            typer.echo(f", sd {summary.sd_difference_ms:.1f} ms", nl=False)
        typer.echo(f"; smallest attainable p at {summary.n_pairs} pairs: {summary.smallest_attainable_p:.5f}")
    typer.echo(f"\n{summary.note}")


if __name__ == "__main__":
    app()
