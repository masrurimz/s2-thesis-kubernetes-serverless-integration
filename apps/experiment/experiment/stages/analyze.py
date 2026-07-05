"""Analyze stage: statistical analysis (Welch, Mann-Whitney, bootstrap CI, Cohen's d).

Extracted from scripts/run_phase_b_experiments.py lines 1092-1183 (StatisticalAnalyzer).
"""

from typing import List, Optional, Tuple

import numpy as np
import structlog

from shared.models.experiment import ExperimentResult, StatisticalComparison
from shared.models.pipeline import PipelineContext

from experiment.stages.base import BaseStage

logger = structlog.get_logger(__name__)


class AnalyzeStage(BaseStage):
    """Statistical analysis: outlier detection, pairwise comparisons, bootstrap CI.

    Operates on accumulated ExperimentResult list (set on ctx.results_for_analysis).
    Writes StatisticalComparison list to ctx.statistics.
    """

    name = "analyze"

    OUTLIER_P99_FLOOR_MS = 0.0  # disabled; low-latency can be legitimate for S2

    def __init__(self, comparisons: Optional[List[Tuple[str, str, str]]] = None):
        """Initialize with comparison pairs.

        Args:
            comparisons: List of (baseline, comparison, metric) tuples.
                         Defaults to the standard thesis comparison set.
        """
        self._comparisons = comparisons or [
            ("s1-k8s-only", "s2-serverless-only", "p99_latency_ms"),
            ("s1-k8s-only", "s2-serverless-only", "error_rate"),
            ("s1-k8s-only", "s3-hybrid-reactive", "p99_latency_ms"),
            ("s2-serverless-only", "s3-hybrid-reactive", "p99_latency_ms"),
            ("s3-hybrid-reactive", "s4-hybrid-predictive", "p99_latency_ms"),
            ("s3-hybrid-reactive", "s4-hybrid-predictive", "slo_violations_k6"),
            ("s1-k8s-only", "s4-hybrid-predictive", "p99_latency_ms"),
        ]

    def _run(self, ctx: PipelineContext) -> None:
        """Run statistical analysis on accumulated results.

        Expects ctx.result to be the ExperimentResult for a single run.
        For batch analysis, the pipeline orchestrator should call analyze_batch() directly.
        """
        # Single-run stage: no-op for batch analysis
        # Batch analysis is done via analyze_batch() called from pipeline orchestrator
        pass

    def detect_outliers(self, results: List[ExperimentResult]) -> Tuple[List[ExperimentResult], List[ExperimentResult]]:
        """Returns (clean, excluded) results."""
        clean, excluded = [], []
        for r in results:
            if (
                r.total_requests <= 0
                or r.p99_latency_ms <= self.OUTLIER_P99_FLOOR_MS
                or not np.isfinite(r.p99_latency_ms)
            ):
                excluded.append(r)
                logger.warning(
                    "outlier_detected",
                    scenario=r.scenario,
                    run_id=r.run_id,
                    p99=r.p99_latency_ms,
                    reason="invalid/empty metrics",
                )
            else:
                clean.append(r)
        return clean, excluded

    def compare(
        self,
        results: List[ExperimentResult],
        baseline: str,
        comparison: str,
        metric: str,
    ) -> StatisticalComparison:
        """Compare two scenarios on a given metric using Welch t-test, Mann-Whitney U, bootstrap CI, and Cohen's d."""
        baseline_vals = [getattr(r, metric) for r in results if r.scenario == baseline]
        comp_vals = [getattr(r, metric) for r in results if r.scenario == comparison]

        if not baseline_vals or not comp_vals:
            raise ValueError(f"Insufficient data for {baseline} vs {comparison} on {metric}")

        # Welch's t-test + Mann-Whitney U + bootstrap CI + Cohen's d — delegated
        # to shared.stats (single source of truth, shared with libs/analysis).
        from shared.stats import (
            bootstrap_ci_diff,
            cohens_d,
            effect_size_label,
            mann_whitney_u,
            welch_ttest,
        )

        t_stat, t_p = welch_ttest(baseline_vals, comp_vals)
        u_stat, u_p = mann_whitney_u(baseline_vals, comp_vals)
        ci_lo, ci_hi = bootstrap_ci_diff(baseline_vals, comp_vals)
        d = cohens_d(baseline_vals, comp_vals)
        interp = effect_size_label(d)

        base_mean = float(np.mean(baseline_vals))
        comp_mean = float(np.mean(comp_vals))

        return StatisticalComparison(
            baseline_scenario=baseline,
            comparison_scenario=comparison,
            metric=metric,
            baseline_mean=base_mean,
            comparison_mean=comp_mean,
            difference=comp_mean - base_mean,
            percent_change=((comp_mean - base_mean) / base_mean * 100) if base_mean != 0 else 0,
            welch_t_stat=float(t_stat),
            welch_p_value=float(t_p),
            mannwhitney_u_stat=float(u_stat),
            mannwhitney_p_value=float(u_p),
            ci_lower=float(ci_lo),
            ci_upper=float(ci_hi),
            cohens_d=float(d),
            effect_size_interpretation=interp,
            n_baseline=len(baseline_vals),
            n_comparison=len(comp_vals),
        )

    def analyze_batch(
        self,
        results: List[ExperimentResult],
    ) -> Tuple[List[ExperimentResult], List[ExperimentResult], List[StatisticalComparison]]:
        """Run full batch analysis: outlier detection + pairwise comparisons.

        Returns (clean, excluded, comparisons).
        """
        clean, excluded = self.detect_outliers(results)

        # Filter by validity gates
        run_invalid = [r for r in clean if not r.run_validity_passed]
        if run_invalid:
            logger.warning("run_validity_failed", count=len(run_invalid))
            clean = [r for r in clean if r.run_validity_passed]
            excluded = excluded + run_invalid

        # Primary inferential set: stress-valid for S1/S3/S4, run-valid for S2
        analysis_set: List[ExperimentResult] = []
        for r in clean:
            if r.scenario == "s2-serverless-only":
                analysis_set.append(r)
            elif r.stress_validity_passed:
                analysis_set.append(r)

        comparisons: List[StatisticalComparison] = []
        for baseline, comp, metric in self._comparisons:
            try:
                stat = self.compare(analysis_set, baseline, comp, metric)
                comparisons.append(stat)
            except ValueError as e:
                logger.warning("comparison_skipped", error=str(e))

        return clean, excluded, comparisons
