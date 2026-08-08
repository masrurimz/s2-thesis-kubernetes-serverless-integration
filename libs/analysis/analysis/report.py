"""Markdown report generation for experiment reanalysis.

Builds the thesis-report comparison tables from a family of
:class:`shared.models.experiment.StatisticalComparison` and a cost-proxy dict.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import numpy as np

from analysis.constants import BETA_VALUES
from shared.models.experiment import StatisticalComparison
from shared.scenarios import SCENARIO_LABELS, SCENARIO_ORDER


def generate_report(
    results: list[dict],
    h1_comps: list[StatisticalComparison],
    h2_comps: list[StatisticalComparison],
    cost: dict[str, Any],
) -> str:
    """Render the full Phase B reanalysis markdown report."""
    lines: list[str] = []

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
    for s in SCENARIO_ORDER:
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
        treq = f"{int(np.mean([r.get('total_requests', r['throughput_rps'] * r['duration_sec']) for r in rs]))}"
        slo = f"{np.mean([r['slo_violations_k6'] for r in rs]):.0f} ± {np.std([r['slo_violations_k6'] for r in rs], ddof=1):.0f}"
        su = f"{np.mean([r.get('scale_up_events', r['scale_out_count']) for r in rs]):.1f}"
        sd = f"{np.mean([r.get('scale_down_events', 0) for r in rs]):.1f}"
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
    render_comparisons(lines, h1_comps)

    # ── 3. H2 Comparisons ──
    lines.append("## 3. H2 Comparisons — Predictive vs Reactive")
    lines.append("")
    render_comparisons(lines, h2_comps)

    # ── 4. Cost Proxy ──
    lines.append("## 4. Cost Proxy Analysis")
    lines.append("")
    lines.append("Cost proxy: `cost(β) = k8s_WTP + β × srv_WTP`, normalized so S1 mean = 1.0")
    lines.append("")
    lines.append("| Scenario | Serverless Share | Violation Rate | β=0.5 | β=0.7 | β=1.0 | β=1.5 |")
    lines.append("|----------|-----------------|----------------|-------|-------|-------|-------|")
    for s in SCENARIO_ORDER:
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


def render_comparisons(lines: list[str], comps: list[StatisticalComparison]) -> None:
    """Append a comparison-table section for each StatisticalComparison to ``lines``."""
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
