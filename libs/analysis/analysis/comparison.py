"""Pairwise statistical comparison between scenarios.

Wraps :mod:`shared.stats` primitives to build a
:class:`shared.models.experiment.StatisticalComparison` from raw run dicts.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy import stats as scipy_stats
from shared.models.experiment import PairedComparison, StatisticalComparison
from shared.stats import (
    bootstrap_ci_diff,
    cohens_d,
    cohens_d_paired,
    effect_size_label,
    paired_bootstrap_ci,
    paired_permutation_test,
)


def run_pairwise_comparison(
    results: Sequence[dict],
    baseline_scenario: str,
    comparison_scenario: str,
    metric: str,
    label: str,
) -> StatisticalComparison:
    """Compare two scenarios on a metric using Welch t, Mann-Whitney U, bootstrap CI, Cohen's d.

    Parameters
    ----------
    results:
        Run dicts; each must have ``scenario`` and the named ``metric`` key.
    baseline_scenario, comparison_scenario:
        Scenario identifiers (e.g. ``"s1-k8s-only"``).
    metric:
        Numeric key to compare (e.g. ``"p99_latency_ms"``).
    label:
        Human-readable comparison label stored on the result.

    Raises
    ------
    ValueError
        If either scenario has zero runs for the metric.
    """
    baseline_vals = [r[metric] for r in results if r["scenario"] == baseline_scenario]
    comp_vals = [r[metric] for r in results if r["scenario"] == comparison_scenario]

    if not baseline_vals or not comp_vals:
        raise ValueError(f"No data for {baseline_scenario} vs {comparison_scenario} on {metric}")

    b_mean = float(np.mean(baseline_vals))
    c_mean = float(np.mean(comp_vals))

    # Welch's t-test (comparison vs baseline)
    t_stat, t_p = scipy_stats.ttest_ind(comp_vals, baseline_vals, equal_var=False)

    # Mann-Whitney U (non-parametric, primary for small n)
    try:
        u_stat, u_p = scipy_stats.mannwhitneyu(comp_vals, baseline_vals, alternative="two-sided")
    except ValueError:
        u_stat, u_p = 0.0, 1.0

    ci_lo, ci_hi = bootstrap_ci_diff(baseline_vals, comp_vals)
    d = cohens_d(baseline_vals, comp_vals)

    return StatisticalComparison(
        baseline_scenario=baseline_scenario,
        comparison_scenario=comparison_scenario,
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


def apply_holm_bonferroni(comparisons: list[StatisticalComparison]) -> None:
    """Apply Holm-Bonferroni correction in place across a comparison family.

    Mutates ``welch_p_corrected`` and ``mannwhitney_p_corrected`` on each
    comparison. Call once after building the full family (H1 + H2 together).
    """
    from shared.stats import holm_bonferroni

    welch_ps = [c.welch_p_value for c in comparisons]
    mw_ps = [c.mannwhitney_p_value for c in comparisons]
    welch_corrected = holm_bonferroni(welch_ps)
    mw_corrected = holm_bonferroni(mw_ps)
    for i, c in enumerate(comparisons):
        c.welch_p_corrected = welch_corrected[i]
        c.mannwhitney_p_corrected = mw_corrected[i]


def run_paired_comparison(
    baseline_values: Sequence[float],
    comparison_values: Sequence[float],
    metric: str,
    pair_ids: Sequence[str] | None = None,
    label: str = "",
) -> PairedComparison:
    """Build a PairedComparison for paired S3/S4 data.

    Uses paired bootstrap CI and one-sided permutation test
    (H1: comparison < baseline).
    """
    n = len(baseline_values)
    assert len(comparison_values) == n, "Paired comparison requires equal-length arrays"

    base_arr = np.asarray(baseline_values, dtype=float)
    comp_arr = np.asarray(comparison_values, dtype=float)

    base_mean = float(np.mean(base_arr))
    comp_mean = float(np.mean(comp_arr))
    mean_diff = comp_mean - base_mean

    ci_lo, ci_hi = paired_bootstrap_ci(base_arr.tolist(), comp_arr.tolist(), seed=42)
    perm_p = paired_permutation_test(base_arr.tolist(), comp_arr.tolist(), seed=42)
    d_paired = cohens_d_paired(base_arr.tolist(), comp_arr.tolist())

    # H2 supported: comparison mean lower AND CI excludes zero AND p < 0.05
    h2_supported = comp_mean < base_mean and ci_hi < 0 and perm_p < 0.05

    return PairedComparison(
        metric=metric,
        label=label,
        n_pairs=n,
        baseline_mean=base_mean,
        comparison_mean=comp_mean,
        mean_difference=mean_diff,
        paired_ci_lower=ci_lo,
        paired_ci_upper=ci_hi,
        permutation_p_value=perm_p,
        cohens_d_paired=d_paired,
        effect_size_interpretation=effect_size_label(abs(d_paired)),
        baseline_values=list(base_arr),
        comparison_values=list(comp_arr),
        pair_ids=list(pair_ids) if pair_ids else [f"pair_{i}" for i in range(n)],
        h2_supported=h2_supported,
    )


def apply_holm_paired(comparisons: list[PairedComparison]) -> None:
    """Apply Holm-Bonferroni correction to paired comparison p-values."""
    from shared.stats import holm_bonferroni

    ps = [c.permutation_p_value for c in comparisons]
    corrected = holm_bonferroni(ps)
    for i, c in enumerate(comparisons):
        c.permutation_p_corrected = corrected[i]
        # Re-check h2_supported with corrected p-value
        c.h2_supported = c.comparison_mean < c.baseline_mean and c.paired_ci_upper < 0 and corrected[i] < 0.05
