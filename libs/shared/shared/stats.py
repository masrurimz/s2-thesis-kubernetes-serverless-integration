"""Pure statistical primitives for experiment analysis.

Single source of truth for the effect-size / resampling / multiple-comparison
helpers that were previously triplicated across the analysis scripts and
inlined in ``apps/experiment/experiment/stages/analyze.py``.

These functions are deliberately dependency-light (numpy + scipy only) and
carry no thesis/domain coupling, so they live in the foundation package and
are consumed by ``libs/analysis``, ``apps/analysis`` and ``apps/experiment``.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy import stats as scipy_stats


def cohens_d(group1: Sequence[float], group2: Sequence[float]) -> float:
    """Cohen's d (comparison - baseline) with pooled SD.

    Uses the average-of-variances pooled standard deviation, matching the
    formulation in the thesis (§3.5.2). Returns 0.0 when the pooled SD is 0
    (identical groups) instead of dividing by zero.
    """
    s1 = np.std(group1, ddof=1)
    s2 = np.std(group2, ddof=1)
    pooled = np.sqrt((s1**2 + s2**2) / 2)
    if pooled == 0:
        return 0.0
    return float((np.mean(group2) - np.mean(group1)) / pooled)


def bootstrap_ci(
    data: Sequence[float],
    n_bootstrap: int = 10000,
    confidence: float = 0.95,
    seed: int | None = None,
) -> tuple[float, float]:
    """Bootstrap confidence interval for the mean of a single sample.

    Resamples ``data`` with replacement ``n_bootstrap`` times and returns the
    percentile interval at the requested confidence level.
    """
    rng = np.random.default_rng(seed=seed)
    arr = np.asarray(data, dtype=float)
    means = np.empty(n_bootstrap)
    for i in range(n_bootstrap):
        means[i] = np.mean(rng.choice(arr, size=len(arr), replace=True))
    alpha = 1 - confidence
    lo, hi = np.percentile(means, [alpha / 2 * 100, (1 - alpha / 2) * 100])
    return float(lo), float(hi)


def bootstrap_ci_diff(
    baseline: Sequence[float],
    comparison: Sequence[float],
    n_bootstrap: int = 10000,
    confidence: float = 0.95,
    seed: int = 42,
) -> tuple[float, float]:
    """Bootstrap confidence interval for the difference of means (comparison - baseline)."""
    rng = np.random.default_rng(seed=seed)
    base = np.asarray(baseline, dtype=float)
    comp = np.asarray(comparison, dtype=float)
    diffs = np.empty(n_bootstrap)
    for i in range(n_bootstrap):
        bs = rng.choice(base, size=len(base), replace=True)
        cs = rng.choice(comp, size=len(comp), replace=True)
        diffs[i] = np.mean(cs) - np.mean(bs)
    alpha = 1 - confidence
    lo, hi = np.percentile(diffs, [alpha / 2 * 100, (1 - alpha / 2) * 100])
    return float(lo), float(hi)


def effect_size_label(d: float) -> str:
    """Cohen's d interpretation: negligible / small / medium / large.

    Thresholds follow Cohen (1988): 0.2 / 0.5 / 0.8.
    """
    if not np.isfinite(d):
        return "undefined"
    ad = abs(d)
    if ad < 0.2:
        return "negligible"
    if ad < 0.5:
        return "small"
    if ad < 0.8:
        return "medium"
    return "large"


def holm_bonferroni(p_values: Sequence[float]) -> list[float]:
    """Holm-Bonferroni correction.

    Returns corrected p-values in the ORIGINAL order. Enforces monotonicity
    along the sorted rank so a smaller raw p never gets a larger corrected
    value than a preceding one.
    """
    m = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    corrected = [0.0] * m
    for rank_0, (orig_idx, p) in enumerate(indexed):
        corrected[orig_idx] = min(p * (m - rank_0), 1.0)
    sorted_indices = [idx for idx, _ in indexed]
    for i in range(1, m):
        prev = sorted_indices[i - 1]
        curr = sorted_indices[i]
        if corrected[curr] < corrected[prev]:
            corrected[curr] = corrected[prev]
    return corrected


def welch_ttest(group1: Sequence[float], group2: Sequence[float]) -> tuple[float, float]:
    """Welch's unequal-variance two-sample t-test. Returns (t_stat, two-sided p_value)."""
    t_stat, p_value = scipy_stats.ttest_ind(group2, group1, equal_var=False)
    return float(t_stat), float(p_value)


def mann_whitney_u(group1: Sequence[float], group2: Sequence[float]) -> tuple[float, float]:
    """Mann-Whitney U test (two-sided). Returns (0.0, 1.0) when a test cannot be computed
    (e.g. all-identical samples), matching the analysis-script fallback."""
    try:
        u_stat, p_value = scipy_stats.mannwhitneyu(group2, group1, alternative="two-sided")
    except ValueError:
        return 0.0, 1.0
    return float(u_stat), float(p_value)


def paired_bootstrap_ci(
    baseline: Sequence[float],
    comparison: Sequence[float],
    n_bootstrap: int = 10000,
    confidence: float = 0.95,
    seed: int = 42,
) -> tuple[float, float]:
    """Bootstrap CI for the mean of paired differences (comparison - baseline).

    Resamples the per-pair differences with replacement. This controls for
    shared temporal/system effects when S3 and S4 are run back-to-back.
    """
    arr = np.asarray(comparison, dtype=float) - np.asarray(baseline, dtype=float)
    rng = np.random.default_rng(seed=seed)
    means = np.empty(n_bootstrap)
    for i in range(n_bootstrap):
        means[i] = np.mean(rng.choice(arr, size=len(arr), replace=True))
    alpha = 1 - confidence
    lo, hi = np.percentile(means, [alpha / 2 * 100, (1 - alpha / 2) * 100])
    return float(lo), float(hi)


# Above this many pairs the sign-flip space is enumerated by sampling instead of in
# full: 2^20 arrangements is the last one that fits in a loop a person will wait for.
_EXACT_PERMUTATION_MAX_PAIRS = 20


def paired_permutation_p_from_diffs(
    diffs: Sequence[float],
    n_permutations: int = 10000,
    seed: int = 42,
) -> float:
    """One-sided paired permutation p for H1: mean(comparison - baseline) < 0.

    The statistic is the mean difference; the null distribution comes from flipping
    each pair's sign, the observed arrangement included, so the smallest attainable
    p is 2^-n — five pairs all in the hypothesised direction give 0.03125.

    Exact for up to ``_EXACT_PERMUTATION_MAX_PAIRS`` pairs; larger samples are
    sampled, seeded, so a rerun over the same data gives the same answer.
    """
    values = np.asarray(diffs, dtype=float)
    n = len(values)
    if n == 0:
        return 1.0
    observed = float(np.mean(values))

    if n <= _EXACT_PERMUTATION_MAX_PAIRS:
        totals = np.zeros(1, dtype=float)
        for value in values:
            totals = np.concatenate([totals + value, totals - value])
        count = int(np.count_nonzero(totals / n <= observed))
        return count / len(totals)

    rng = np.random.default_rng(seed=seed)
    count = 0
    for _ in range(n_permutations):
        signs = rng.choice([-1, 1], size=n)
        if np.mean(values * signs) <= observed:
            count += 1
    # The observed arrangement is always one of the possibilities, so it counts:
    # without it a maximal effect would be reported as p = 0, which no permutation
    # test can attain.
    return (count + 1) / (n_permutations + 1)


def paired_permutation_test(
    baseline: Sequence[float],
    comparison: Sequence[float],
    n_permutations: int = 10000,
    seed: int = 42,
) -> float:
    """One-sided paired permutation test: H1: comparison < baseline.

    ``paired_permutation_p_from_diffs`` on the per-pair differences; see it for the
    exact/sampled split.
    """
    diffs = np.asarray(comparison, dtype=float) - np.asarray(baseline, dtype=float)
    return paired_permutation_p_from_diffs(diffs, n_permutations=n_permutations, seed=seed)


def cohens_d_paired(baseline: Sequence[float], comparison: Sequence[float]) -> float:
    """Cohen's d for paired samples (mean_diff / sd_diff).

    Undefined — NaN — for a single pair: the standard deviation of one difference is
    not zero, it is unknown, and reporting a number there would let a one-pair bundle
    name an effect size it cannot support.
    """
    diffs = np.asarray(comparison, dtype=float) - np.asarray(baseline, dtype=float)
    if len(diffs) < 2:
        return float("nan")
    sd = float(np.std(diffs, ddof=1))
    if not np.isfinite(sd):
        return float("nan")
    if sd == 0:
        return 0.0
    return float(np.mean(diffs) / sd)
