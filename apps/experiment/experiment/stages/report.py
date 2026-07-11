"""Report stage: Markdown report generation from experiment data.

Extracted from scripts/run_phase_b_experiments.py lines 1919-2053 (_generate_report).
"""

import subprocess
from datetime import datetime
from typing import List

import numpy as np
import structlog

from shared.models.experiment import ExperimentResult, PairedComparison, StatisticalComparison
from shared.models.pipeline import PipelineContext

from experiment.stages.base import BaseStage

logger = structlog.get_logger(__name__)

SCENARIOS = [
    "s1-k8s-only",
    "s2-serverless-only",
    "s3-hybrid-reactive",
    "s4-hybrid-predictive",
]


def _git_commit_hash() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


class ReportStage(BaseStage):
    """Generate Markdown report from accumulated experiment results and comparisons.

    Expects ctx to carry the analysis results set by the analyze stage.
    """

    name = "report"

    def _run(self, ctx: PipelineContext) -> None:
        """Generate report from ctx data.

        For batch analysis, the orchestrator should call generate_report() directly
        and pass the results/comparisons.
        """
        # Single-run stage: no-op. Batch reporting via generate_report().
        pass

    def generate_report(
        self,
        clean: List[ExperimentResult],
        analysis_set: List[ExperimentResult],
        excluded: List[ExperimentResult],
        comparisons: List[StatisticalComparison],
    ) -> str:
        """Generate Markdown report from analysis results."""
        lines = [
            "# Phase B: Replicated Comparison Results",
            "",
            f"**Date:** {datetime.now().isoformat()}",
            f"**Git:** {_git_commit_hash()}",
            f"**Runs:** {len(clean)} clean, {len(excluded)} excluded",
            "",
            "## Per-Scenario Summary",
            "",
            "| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |",
            "|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|",
        ]

        for s in SCENARIOS:
            rs = [r for r in clean if r.scenario == s]
            if not rs:
                continue
            n = len(rs)
            p50 = np.mean([r.p50_latency_ms for r in rs])
            p95 = np.mean([r.p95_latency_ms for r in rs])
            p99 = np.mean([r.p99_latency_ms for r in rs])
            err = np.mean([r.error_rate for r in rs])
            rps = np.mean([r.throughput_rps for r in rs])
            slo = sum(r.slo_violations_k6 for r in rs)
            su = sum(r.scale_up_events for r in rs)
            sd = sum(r.scale_down_events for r in rs)
            lines.append(
                f"| {s} | {n} | {p50:.1f} | {p95:.1f} | {p99:.1f} | {err:.3f} | {rps:.1f} | {slo} | {su} | {sd} |"
            )

        lines.extend(["", "## Run Validity Gates", ""])
        lines.extend(
            [
                "| Scenario | Run-Valid / Total |",
                "|----------|-------------------|",
            ]
        )
        for s in SCENARIOS:
            rs = [r for r in clean + excluded if r.scenario == s]
            if not rs:
                continue
            pass_count = sum(1 for r in rs if r.run_validity_passed)
            lines.append(f"| {s} | {pass_count}/{len(rs)} |")

        lines.extend(["", "## Stress Validity Coverage", ""])
        lines.extend(
            [
                "| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |",
                "|----------|--------------------------|---------------------|-----------------|",
            ]
        )
        for s in ("s1-k8s-only", "s3-hybrid-reactive", "s4-hybrid-predictive"):
            rs = [r for r in clean if r.scenario == s]
            if not rs:
                continue
            stress_count = sum(1 for r in rs if r.stress_validity_passed)
            dyn_sum = sum(r.nodes_provisioned for r in rs)
            cross_runs = sum(1 for r in rs if r.cross_node_observed)
            lines.append(f"| {s} | {stress_count}/{len(rs)} | {dyn_sum} | {cross_runs}/{len(rs)} |")

        lines.extend(["", "## Analysis Set Coverage", ""])
        lines.extend(
            [
                "| Scenario | Included in Inferential Set |",
                "|----------|-----------------------------|",
            ]
        )
        for s in SCENARIOS:
            total = len([r for r in clean if r.scenario == s])
            inc = len([r for r in analysis_set if r.scenario == s])
            if total == 0:
                continue
            lines.append(f"| {s} | {inc}/{total} |")

        failing = [r for r in (clean + excluded) if (not r.run_validity_passed or not r.stress_validity_passed)]
        if failing:
            lines.extend(["", "### Gate Failures", ""])
            for r in failing:
                reasons: List[str] = []
                if not r.run_validity_passed:
                    reasons.extend(r.run_validity_notes)
                if not r.stress_validity_passed:
                    reasons.extend(r.stress_validity_notes)
                reason = "; ".join(reasons) if reasons else "unspecified"
                lines.append(f"- {r.scenario} run {r.run_id}: {reason}")

        lines.extend(["", "## Statistical Comparisons", ""])

        for c in comparisons:
            sig = "✅ Significant" if c.welch_p_value < 0.05 else "⚠️ Not significant"
            lines.extend(
                [
                    f"### {c.comparison_scenario} vs {c.baseline_scenario} ({c.metric})",
                    "",
                    "| Metric | Value |",
                    "|--------|-------|",
                    f"| Baseline mean | {c.baseline_mean:.2f} (n={c.n_baseline}) |",
                    f"| Comparison mean | {c.comparison_mean:.2f} (n={c.n_comparison}) |",
                    f"| Difference | {c.difference:+.2f} ({c.percent_change:+.1f}%) |",
                    f"| Welch t-stat | {c.welch_t_stat:.3f} |",
                    f"| Welch p-value | {c.welch_p_value:.4f} |",
                    f"| Mann-Whitney U | {c.mannwhitney_u_stat:.1f} |",
                    f"| Mann-Whitney p | {c.mannwhitney_p_value:.4f} |",
                    f"| 95% CI | [{c.ci_lower:+.2f}, {c.ci_upper:+.2f}] |",
                    f"| Cohen's d | {c.cohens_d:.3f} ({c.effect_size_interpretation}) |",
                    f"| Verdict | {sig} |",
                    "",
                ]
            )

        if excluded:
            lines.extend(["## Excluded Runs", ""])
            for r in excluded:
                if not r.run_validity_passed:
                    reason = "; ".join(r.run_validity_notes) if r.run_validity_notes else "run validity failure"
                    lines.append(f"- {r.scenario} run {r.run_id}: {reason}")
                elif (
                    r.scenario in ("s1-k8s-only", "s3-hybrid-reactive", "s4-hybrid-predictive")
                    and not r.stress_validity_passed
                ):
                    reason = (
                        "; ".join(r.stress_validity_notes) if r.stress_validity_notes else "stress validity failure"
                    )
                    lines.append(f"- {r.scenario} run {r.run_id}: {reason}")
                else:
                    lines.append(f"- {r.scenario} run {r.run_id}: invalid/empty metrics")

        return "\n".join(lines)

    def generate_paired_report(
        self,
        primary: PairedComparison,
        secondaries: List[PairedComparison],
        n_pairs: int,
    ) -> str:
        """Generate Markdown report for paired H2 experiment.

        Uses paired statistics (bootstrap CI, permutation test) rather than
        unpaired comparisons. Reports primary endpoint (p99 latency) and
        Holm-corrected secondary endpoints.
        """
        lines = [
            "# H2 Paired Experiment: S4 vs S3",
            "",
            f"**Date:** {datetime.now().isoformat()}",
            f"**Git:** {_git_commit_hash()}",
            f"**Design:** Counterbalanced paired (n={n_pairs})",
            "**Primary endpoint:** p99 latency (one-sided S4 < S3)",
            "",
            "## Primary Endpoint: p99 Latency",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| S3 mean | {primary.baseline_mean:.2f} ms |",
            f"| S4 mean | {primary.comparison_mean:.2f} ms |",
            f"| Mean difference (S4-S3) | {primary.mean_difference:+.2f} ms |",
            f"| Paired 95% CI | [{primary.paired_ci_lower:+.2f}, {primary.paired_ci_upper:+.2f}] |",
            f"| Permutation p-value | {primary.permutation_p_value:.4f} |",
            f"| Cohen's d (paired) | {primary.cohens_d_paired:.3f} ({primary.effect_size_interpretation}) |",
            f"| H2 verdict | {'✅ SUPPORTED' if primary.h2_supported else '⚠️ NOT SUPPORTED'} |",
            "",
            "### Per-Pair Values",
            "",
            "| Pair | S3 p99 (ms) | S4 p99 (ms) | Diff (ms) |",
            "|------|-------------|-------------|-----------|",
        ]

        for i, pid in enumerate(primary.pair_ids):
            s3_v = primary.baseline_values[i]
            s4_v = primary.comparison_values[i]
            lines.append(f"| {pid} | {s3_v:.1f} | {s4_v:.1f} | {s4_v - s3_v:+.1f} |")

        lines.extend(["", "## Secondary Endpoints (Holm-corrected)", ""])
        lines.extend(
            [
                "| Metric | S3 mean | S4 mean | Diff | Perm p (corrected) | Significant |",
                "|--------|---------|---------|------|---------------------|-------------|",
            ]
        )

        for s in secondaries:
            sig = "✅" if s.permutation_p_corrected < 0.05 else "⚠️"
            lines.append(
                f"| {s.metric} | {s.baseline_mean:.2f} | {s.comparison_mean:.2f} "
                f"| {s.mean_difference:+.2f} | {s.permutation_p_corrected:.4f} | {sig} |"
            )

        h2_gate = (
            primary.h2_supported and primary.comparison_mean < primary.baseline_mean and primary.paired_ci_upper < 0
        )

        lines.extend(
            [
                "",
                "## H2 Decision Gate",
                "",
                "H2 (predictive S4 outperforms reactive S3 on p99 latency) is **SUPPORTED** only if:",
                f"1. S4 p99 < S3 p99: {'✅' if primary.comparison_mean < primary.baseline_mean else '❌'}",
                f"2. Paired 95% CI excludes zero: {'✅' if primary.paired_ci_upper < 0 else '❌'}",
                f"3. Permutation p < 0.05: {'✅' if primary.permutation_p_value < 0.05 else '❌'}",
                "",
                f"**Overall verdict: {'H2 SUPPORTED' if h2_gate else 'H2 NOT SUPPORTED — partial/negative result retained'}**",
                "",
            ]
        )

        return "\n".join(lines)
