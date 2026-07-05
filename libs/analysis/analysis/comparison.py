"""Pairwise statistical comparison between scenarios.

Wraps :mod:`shared.stats` primitives to build a
:class:`shared.models.experiment.StatisticalComparison` from raw run dicts.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy import stats as scipy_stats

from shared.models.experiment import StatisticalComparison
from shared.stats import bootstrap_ci_diff, cohens_d, effect_size_label


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
