#!/usr/bin/env python3
"""
Phase B Reanalysis — all 20 runs, no outlier exclusion.

Reads results_final.json and produces:
  - reanalysis_report.md     (full markdown report)
  - reanalysis_statistics.json (structured comparison results)
  - cost_analysis.json        (cost proxy analysis)

Usage:
    cd controller && uv run python ../thesis/scripts/reanalyze_phase_b.py \
        --results-dir ../results/experiments/phase-b/2026-02-15_clarknet-replay
"""

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import structlog
from scipy import stats as scipy_stats

logger = structlog.get_logger(__name__)

SCENARIOS = ["s1-k8s-only", "s2-serverless-only", "s3-hybrid-reactive", "s4-hybrid-predictive"]

SCENARIO_LABELS = {
    "s1-k8s-only": "S1 (K8s-Only)",
    "s2-serverless-only": "S2 (Serverless-Only)",
    "s3-hybrid-reactive": "S3 (Hybrid Reactive)",
    "s4-hybrid-predictive": "S4 (Hybrid Predictive)",
}

# Comparison definitions per thesis §3.5.2
H1_COMPARISONS = [
    # (baseline, comparison, metric, label)
    ("s1-k8s-only", "s2-serverless-only", "p99_latency_ms", "Platform baseline"),
    ("s1-k8s-only", "s2-serverless-only", "error_rate", "Platform baseline"),
    ("s1-k8s-only", "s3-hybrid-reactive", "p99_latency_ms", "Reactive vs K8s"),
    ("s1-k8s-only", "s3-hybrid-reactive", "slo_violations_k6", "Reactive vs K8s"),
    ("s2-serverless-only", "s3-hybrid-reactive", "p99_latency_ms", "Reactive vs Serverless"),
    ("s1-k8s-only", "s4-hybrid-predictive", "p99_latency_ms", "Predictive vs K8s"),
    ("s1-k8s-only", "s4-hybrid-predictive", "slo_violations_k6", "Predictive vs K8s"),
]

H2_COMPARISONS = [
    ("s3-hybrid-reactive", "s4-hybrid-predictive", "p99_latency_ms", "Predictive vs Reactive"),
    ("s3-hybrid-reactive", "s4-hybrid-predictive", "slo_violations_k6", "Predictive vs Reactive"),
]

BETA_VALUES = [0.5, 0.7, 1.0, 1.5]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class StatisticalComparison:
    baseline_scenario: str
    comparison_scenario: str
    metric: str
    label: str
    baseline_mean: float
    comparison_mean: float
    difference: float
    percent_change: float
    baseline_std: float
    comparison_std: float
    # Welch's t-test
    welch_t_stat: float
    welch_p_value: float
    # Mann-Whitney U (primary for small n)
    mannwhitney_u_stat: float
    mannwhitney_p_value: float
    # Bootstrap CI
    ci_lower: float
    ci_upper: float
    # Effect size
    cohens_d: float
    effect_size_interpretation: str
    # Sample sizes
    n_baseline: int
    n_comparison: int
    # Holm-Bonferroni corrected p-values
    welch_p_corrected: float = 1.0
    mannwhitney_p_corrected: float = 1.0


# ---------------------------------------------------------------------------
# Statistical helpers
# ---------------------------------------------------------------------------


def bootstrap_ci_diff(
    baseline: List[float], comparison: List[float], n_bootstrap: int = 10000, confidence: float = 0.95, seed: int = 42
) -> Tuple[float, float]:
    """Bootstrap 95% CI for difference of means (comparison - baseline)."""
    rng = np.random.default_rng(seed=seed)
    diffs = []
    for _ in range(n_bootstrap):
        bs = rng.choice(baseline, size=len(baseline), replace=True)
        cs = rng.choice(comparison, size=len(comparison), replace=True)
        diffs.append(float(np.mean(cs) - np.mean(bs)))
    alpha = 1 - confidence
    lo, hi = np.percentile(diffs, [alpha / 2 * 100, (1 - alpha / 2) * 100])
    return float(lo), float(hi)


def cohens_d(group1: List[float], group2: List[float]) -> float:
    """Cohen's d with pooled SD (average of variances)."""
    s1 = np.std(group1, ddof=1)
    s2 = np.std(group2, ddof=1)
    pooled = np.sqrt((s1**2 + s2**2) / 2)
    if pooled == 0:
        return 0.0
    return float((np.mean(group2) - np.mean(group1)) / pooled)


def effect_size_label(d: float) -> str:
    ad = abs(d)
    if ad < 0.2:
        return "negligible"
    elif ad < 0.5:
        return "small"
    elif ad < 0.8:
        return "medium"
    return "large"


def holm_bonferroni(p_values: List[float]) -> List[float]:
    """Holm-Bonferroni correction. Returns corrected p-values in original order."""
    m = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    corrected = [0.0] * m
    for rank_0, (orig_idx, p) in enumerate(indexed):
        corrected[orig_idx] = min(p * (m - rank_0), 1.0)
    # enforce monotonicity: corrected[i] >= corrected[i-1] in sorted order
    sorted_indices = [idx for idx, _ in indexed]
    for i in range(1, m):
        prev = sorted_indices[i - 1]
        curr = sorted_indices[i]
        if corrected[curr] < corrected[prev]:
            corrected[curr] = corrected[prev]
    return corrected


# ---------------------------------------------------------------------------
# Core comparison
# ---------------------------------------------------------------------------


def run_comparison(
    results: List[Dict],
    baseline_scenario: str,
    comp_scenario: str,
    metric: str,
    label: str,
) -> StatisticalComparison:
    baseline_vals = [r[metric] for r in results if r["scenario"] == baseline_scenario]
    comp_vals = [r[metric] for r in results if r["scenario"] == comp_scenario]

    if not baseline_vals or not comp_vals:
        raise ValueError(f"No data for {baseline_scenario} vs {comp_scenario} on {metric}")

    b_mean = float(np.mean(baseline_vals))
    c_mean = float(np.mean(comp_vals))

    # Welch's t-test
    t_stat, t_p = scipy_stats.ttest_ind(comp_vals, baseline_vals, equal_var=False)

    # Mann-Whitney U
    try:
        u_stat, u_p = scipy_stats.mannwhitneyu(comp_vals, baseline_vals, alternative="two-sided")
    except ValueError:
        u_stat, u_p = 0.0, 1.0

    # Bootstrap CI
    ci_lo, ci_hi = bootstrap_ci_diff(baseline_vals, comp_vals)

    # Cohen's d
    d = cohens_d(baseline_vals, comp_vals)

    return StatisticalComparison(
        baseline_scenario=baseline_scenario,
        comparison_scenario=comp_scenario,
        metric=metric,
        label=label,
        baseline_mean=b_mean,
        comparison_mean=c_mean,
        difference=c_mean - b_mean,
        percent_change=((c_mean - b_mean) / b_mean * 100) if b_mean != 0 else 0.0,
        baseline_std=float(np.std(baseline_vals, ddof=1)),
        comparison_std=float(np.std(comp_vals, ddof=1)),
        welch_t_stat=float(t_stat),
        welch_p_value=float(t_p),
        mannwhitney_u_stat=float(u_stat),
        mannwhitney_p_value=float(u_p),
        ci_lower=ci_lo,
        ci_upper=ci_hi,
        cohens_d=d,
        effect_size_interpretation=effect_size_label(d),
        n_baseline=len(baseline_vals),
        n_comparison=len(comp_vals),
    )


# ---------------------------------------------------------------------------
# Cost proxy analysis
# ---------------------------------------------------------------------------


def compute_cost_proxy(results: List[Dict]) -> Dict[str, Any]:
    """Per-run cost proxy metrics per thesis §3.5.2."""
    out: Dict[str, Any] = {"per_run": [], "per_scenario": {}}

    for r in results:
        k8s = r["k8s_weight_time_product"]
        srv = r["serverless_weight_time_product"]
        total_wt = k8s + srv

        serverless_share = srv / total_wt if total_wt > 0 else 0.0
        total_req = r["total_requests"]
        violation_rate = r["slo_violations_k6"] / total_req if total_req > 0 else 0.0

        cost_proxies = {}
        for beta in BETA_VALUES:
            cost_proxies[f"beta_{beta}"] = k8s + beta * srv

        out["per_run"].append(
            {
                "scenario": r["scenario"],
                "run_id": r["run_id"],
                "k8s_weight_time_product": k8s,
                "serverless_weight_time_product": srv,
                "serverless_share": serverless_share,
                "total_requests": total_req,
                "slo_violations_k6": r["slo_violations_k6"],
                "violation_rate": violation_rate,
                **cost_proxies,
            }
        )

    # Normalize to S1 mean = 1.0 for each beta
    s1_runs = [pr for pr in out["per_run"] if pr["scenario"] == "s1-k8s-only"]
    normalization = {}
    for beta in BETA_VALUES:
        key = f"beta_{beta}"
        s1_mean = float(np.mean([pr[key] for pr in s1_runs])) if s1_runs else 1.0
        normalization[key] = s1_mean

    for pr in out["per_run"]:
        for beta in BETA_VALUES:
            key = f"beta_{beta}"
            norm_key = f"beta_{beta}_normalized"
            pr[norm_key] = pr[key] / normalization[key] if normalization[key] > 0 else 0.0

    # Per-scenario summary
    for s in SCENARIOS:
        runs = [pr for pr in out["per_run"] if pr["scenario"] == s]
        if not runs:
            continue
        summary: Dict[str, Any] = {
            "n": len(runs),
            "serverless_share_mean": float(np.mean([r["serverless_share"] for r in runs])),
            "serverless_share_std": float(np.std([r["serverless_share"] for r in runs], ddof=1)),
            "violation_rate_mean": float(np.mean([r["violation_rate"] for r in runs])),
            "violation_rate_std": float(np.std([r["violation_rate"] for r in runs], ddof=1)),
        }
        for beta in BETA_VALUES:
            raw_key = f"beta_{beta}"
            norm_key = f"beta_{beta}_normalized"
            summary[f"{raw_key}_mean"] = float(np.mean([r[raw_key] for r in runs]))
            summary[f"{raw_key}_std"] = float(np.std([r[raw_key] for r in runs], ddof=1))
            summary[f"{norm_key}_mean"] = float(np.mean([r[norm_key] for r in runs]))
            summary[f"{norm_key}_std"] = float(np.std([r[norm_key] for r in runs], ddof=1))
        out["per_scenario"][s] = summary

    return out


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def generate_report(
    results: List[Dict],
    h1_comps: List[StatisticalComparison],
    h2_comps: List[StatisticalComparison],
    cost: Dict[str, Any],
) -> str:
    lines: List[str] = []

    lines.append("# Phase B Reanalysis — All 20 Runs (No Outlier Exclusion)")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().isoformat()}")
    lines.append("**Runs per scenario:** 5 × 4 = 20 total")
    lines.append("**Outliers excluded:** None")
    lines.append("")

    # ── 1. Per-Scenario Summary ──
    lines.append("## 1. Per-Scenario Summary")
    lines.append("")
    lines.append(
        "| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | "
        "Total Req | SLO Viol | Scale-Up | Scale-Down | k8s WTP | srv WTP |"
    )
    lines.append(
        "|----------|---|----------|----------|----------|--------|-----|"
        "-----------|----------|----------|------------|---------|---------|"
    )
    for s in SCENARIOS:
        rs = [r for r in results if r["scenario"] == s]
        n = len(rs)
        if n == 0:
            continue

        def _ms(key: str) -> str:
            vals = [r[key] for r in rs]
            return f"{np.mean(vals):.1f} ± {np.std(vals, ddof=1):.1f}"

        p50 = _ms("p50_latency_ms")
        p95 = _ms("p95_latency_ms")
        p99 = _ms("p99_latency_ms")
        err = f"{np.mean([r['error_rate'] for r in rs]):.4f}"
        rps = f"{np.mean([r['throughput_rps'] for r in rs]):.1f}"
        treq = f"{int(np.mean([r['total_requests'] for r in rs]))}"
        slo = f"{np.mean([r['slo_violations_k6'] for r in rs]):.0f} ± {np.std([r['slo_violations_k6'] for r in rs], ddof=1):.0f}"
        su = f"{np.mean([r['scale_up_events'] for r in rs]):.1f}"
        sd = f"{np.mean([r['scale_down_events'] for r in rs]):.1f}"
        kwtp = f"{np.mean([r['k8s_weight_time_product'] for r in rs]):.0f}"
        swtp = f"{np.mean([r['serverless_weight_time_product'] for r in rs]):.0f}"
        lines.append(
            f"| {SCENARIO_LABELS[s]} | {n} | {p50} | {p95} | {p99} | {err} | "
            f"{rps} | {treq} | {slo} | {su} | {sd} | {kwtp} | {swtp} |"
        )
    lines.append("")

    # ── 2. H1 Comparisons ──
    lines.append("## 2. H1 Comparisons — Hybrid vs Baselines")
    lines.append("")
    _render_comparisons(lines, h1_comps)

    # ── 3. H2 Comparisons ──
    lines.append("## 3. H2 Comparisons — Predictive vs Reactive")
    lines.append("")
    _render_comparisons(lines, h2_comps)

    # ── 4. Cost Proxy ──
    lines.append("## 4. Cost Proxy Analysis")
    lines.append("")
    lines.append("Cost proxy: `cost(β) = k8s_WTP + β × srv_WTP`, normalized so S1 mean = 1.0")
    lines.append("")
    lines.append("| Scenario | Serverless Share | Violation Rate | β=0.5 | β=0.7 | β=1.0 | β=1.5 |")
    lines.append("|----------|-----------------|----------------|-------|-------|-------|-------|")
    for s in SCENARIOS:
        sc = cost["per_scenario"].get(s)
        if not sc:
            continue
        ss = f"{sc['serverless_share_mean']:.3f} ± {sc['serverless_share_std']:.3f}"
        vr = f"{sc['violation_rate_mean']:.4f} ± {sc['violation_rate_std']:.4f}"
        betas = []
        for beta in BETA_VALUES:
            m = sc[f"beta_{beta}_normalized_mean"]
            sd = sc[f"beta_{beta}_normalized_std"]
            betas.append(f"{m:.3f} ± {sd:.3f}")
        lines.append(f"| {SCENARIO_LABELS[s]} | {ss} | {vr} | {' | '.join(betas)} |")
    lines.append("")

    # ── 5. Key Findings ──
    lines.append("## 5. Key Findings Summary")
    lines.append("")

    all_comps = h1_comps + h2_comps
    sig_welch = [c for c in all_comps if c.welch_p_corrected < 0.05]
    sig_mw = [c for c in all_comps if c.mannwhitney_p_corrected < 0.05]

    lines.append(f"- **Total comparisons:** {len(all_comps)}")
    lines.append(f"- **Significant after Holm-Bonferroni (Welch):** {len(sig_welch)}/{len(all_comps)}")
    lines.append(f"- **Significant after Holm-Bonferroni (Mann-Whitney):** {len(sig_mw)}/{len(all_comps)}")
    lines.append("")

    for c in all_comps:
        sig_w = "✅" if c.welch_p_corrected < 0.05 else "⚠️"
        sig_m = "✅" if c.mannwhitney_p_corrected < 0.05 else "⚠️"
        lines.append(
            f"- {c.comparison_scenario} vs {c.baseline_scenario} ({c.metric}): "
            f"Δ={c.difference:+.2f} ({c.percent_change:+.1f}%), "
            f"d={c.cohens_d:.3f} ({c.effect_size_interpretation}), "
            f"Welch p={c.welch_p_corrected:.4f} {sig_w}, "
            f"MW p={c.mannwhitney_p_corrected:.4f} {sig_m}"
        )
    lines.append("")

    return "\n".join(lines)


def _render_comparisons(lines: List[str], comps: List[StatisticalComparison]) -> None:
    for c in comps:
        sig_w = "✅ Significant" if c.welch_p_corrected < 0.05 else "⚠️ Not significant"
        sig_m = "✅ Significant" if c.mannwhitney_p_corrected < 0.05 else "⚠️ Not significant"
        lines.extend(
            [
                f"### {c.comparison_scenario} vs {c.baseline_scenario} — {c.metric} ({c.label})",
                "",
                "| Statistic | Value |",
                "|-----------|-------|",
                f"| Baseline mean ± std | {c.baseline_mean:.2f} ± {c.baseline_std:.2f} (n={c.n_baseline}) |",
                f"| Comparison mean ± std | {c.comparison_mean:.2f} ± {c.comparison_std:.2f} (n={c.n_comparison}) |",
                f"| Difference | {c.difference:+.2f} ({c.percent_change:+.1f}%) |",
                f"| Welch t-stat | {c.welch_t_stat:.3f} |",
                f"| Welch p-value (raw) | {c.welch_p_value:.4f} |",
                f"| Welch p-value (Holm-Bonferroni) | {c.welch_p_corrected:.4f} |",
                f"| Mann-Whitney U | {c.mannwhitney_u_stat:.1f} |",
                f"| Mann-Whitney p (raw) | {c.mannwhitney_p_value:.4f} |",
                f"| Mann-Whitney p (Holm-Bonferroni) | {c.mannwhitney_p_corrected:.4f} |",
                f"| Bootstrap 95% CI | [{c.ci_lower:+.2f}, {c.ci_upper:+.2f}] |",
                f"| Cohen's d | {c.cohens_d:.3f} ({c.effect_size_interpretation}) |",
                f"| Verdict (Welch corrected) | {sig_w} |",
                f"| Verdict (MW corrected) | {sig_m} |",
                "",
            ]
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase B Reanalysis — all 20 runs, no outlier exclusion")
    parser.add_argument(
        "--results-dir",
        type=str,
        required=True,
        help="Path to experiment directory containing results_final.json",
    )
    args = parser.parse_args()

    results_dir = Path(args.results_dir).resolve()
    results_file = results_dir / "results_final.json"

    if not results_file.exists():
        logger.error("results_file_not_found", path=str(results_file))
        return 1

    with open(results_file) as f:
        results: List[Dict] = json.load(f)

    logger.info("loaded_results", count=len(results), path=str(results_file))

    # -- Run all comparisons --
    all_comparisons: List[StatisticalComparison] = []

    h1_comps: List[StatisticalComparison] = []
    for baseline, comp, metric, label in H1_COMPARISONS:
        try:
            c = run_comparison(results, baseline, comp, metric, label)
            h1_comps.append(c)
            all_comparisons.append(c)
        except ValueError as e:
            logger.warning("comparison_skipped", error=str(e))

    h2_comps: List[StatisticalComparison] = []
    for baseline, comp, metric, label in H2_COMPARISONS:
        try:
            c = run_comparison(results, baseline, comp, metric, label)
            h2_comps.append(c)
            all_comparisons.append(c)
        except ValueError as e:
            logger.warning("comparison_skipped", error=str(e))

    # -- Holm-Bonferroni correction across ALL tests --
    welch_ps = [c.welch_p_value for c in all_comparisons]
    mw_ps = [c.mannwhitney_p_value for c in all_comparisons]

    welch_corrected = holm_bonferroni(welch_ps)
    mw_corrected = holm_bonferroni(mw_ps)

    for i, c in enumerate(all_comparisons):
        c.welch_p_corrected = welch_corrected[i]
        c.mannwhitney_p_corrected = mw_corrected[i]

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
        json.dump([asdict(c) for c in all_comparisons], f, indent=2)
    logger.info("wrote_statistics", path=str(stats_path))

    cost_path = results_dir / "cost_analysis.json"
    with open(cost_path, "w") as f:
        json.dump(cost, f, indent=2, default=str)
    logger.info("wrote_cost_analysis", path=str(cost_path))

    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
