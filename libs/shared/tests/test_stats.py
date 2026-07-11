"""Behavioral tests for the shared statistical primitives.

These functions are load-bearing across libs/analysis, apps/analysis, and
apps/experiment — they must keep their sign/magnitude contract.
"""

from __future__ import annotations


from shared.stats import (
    bootstrap_ci,
    bootstrap_ci_diff,
    cohens_d,
    cohens_d_paired,
    effect_size_label,
    holm_bonferroni,
    mann_whitney_u,
    paired_bootstrap_ci,
    paired_permutation_test,
    welch_ttest,
)


class TestCohensD:
    def test_positive_when_group2_larger(self):
        assert cohens_d([1, 2, 3], [4, 5, 6]) > 0

    def test_negative_when_group2_smaller(self):
        assert cohens_d([4, 5, 6], [1, 2, 3]) < 0

    def test_zero_for_identical_groups(self):
        assert cohens_d([1, 2, 3], [1, 2, 3]) == 0.0

    def test_zero_for_constant_groups(self):
        # pooled SD is 0 → must not divide by zero
        assert cohens_d([5, 5, 5], [5, 5, 5]) == 0.0


class TestEffectSizeLabel:
    def test_thresholds(self):
        assert effect_size_label(0.1) == "negligible"
        assert effect_size_label(0.3) == "small"
        assert effect_size_label(0.6) == "medium"
        assert effect_size_label(1.0) == "large"

    def test_negative_d_uses_absolute_value(self):
        assert effect_size_label(-0.3) == "small"

    def test_boundary_at_0_2(self):
        assert effect_size_label(0.19) == "negligible"
        assert effect_size_label(0.2) == "small"


class TestBootstrapCI:
    def test_ci_contains_sample_mean(self):
        data = [1, 2, 3, 4, 5]
        lo, hi = bootstrap_ci(data, seed=0)
        assert lo < 3.0 < hi

    def test_ci_is_ordered(self):
        lo, hi = bootstrap_ci([10, 20, 30, 40, 50], seed=1)
        assert lo < hi

    def test_seed_reproducibility(self):
        d = [1, 2, 3, 4, 5]
        assert bootstrap_ci(d, seed=42) == bootstrap_ci(d, seed=42)


class TestBootstrapCIDiff:
    def test_negative_when_comparison_smaller(self):
        lo, hi = bootstrap_ci_diff([10, 20, 30], [1, 2, 3], seed=0)
        # comparison - baseline is negative
        assert hi < 0

    def test_contains_zero_when_groups_overlap(self):
        lo, hi = bootstrap_ci_diff([1, 2, 3, 10], [2, 3, 4, 5], seed=0)
        assert lo <= 0 <= hi


class TestHolmBonferroni:
    def test_smallest_p_gets_smallest_correction(self):
        ps = [0.04, 0.01, 0.03]
        corrected = holm_bonferroni(ps)
        # the smallest raw p (0.01 at index 1) gets the strongest correction
        assert corrected[1] <= corrected[0]
        assert corrected[1] <= corrected[2]

    def test_returns_same_length(self):
        assert len(holm_bonferroni([0.01, 0.02])) == 2

    def test_corrected_does_not_exceed_one(self):
        assert all(c <= 1.0 for c in holm_bonferroni([0.5, 0.6, 0.7]))

    def test_monotonicity_in_sorted_order(self):
        ps = [0.01, 0.04, 0.03]
        corrected = holm_bonferroni(ps)
        indexed = sorted(enumerate(ps), key=lambda x: x[1])
        sorted_corrected = [corrected[i] for i, _ in indexed]
        for i in range(1, len(sorted_corrected)):
            assert sorted_corrected[i] >= sorted_corrected[i - 1]


class TestWelchAndMannWhitney:
    def test_welch_returns_floats(self):
        t, p = welch_ttest([1, 2, 3, 4, 5], [10, 11, 12, 13, 14])
        assert isinstance(t, float)
        assert isinstance(p, float)

    def test_mann_whitney_returns_floats(self):
        u, p = mann_whitney_u([1, 2, 3, 4, 5], [10, 11, 12, 13, 14])
        assert isinstance(u, float)
        assert isinstance(p, float)
        assert 0.0 <= p <= 1.0


class TestPairedStatistics:
    """Tests for paired bootstrap CI, permutation test, and paired Cohen's d."""

    def test_paired_bootstrap_ci_excludes_zero_when_consistent(self):
        """When comparison is consistently lower, CI should exclude zero."""
        baseline = [100, 110, 120, 130, 140]
        comparison = [90, 100, 110, 120, 130]
        lo, hi = paired_bootstrap_ci(baseline, comparison, n_bootstrap=5000, seed=42)
        assert hi < 0, f"Expected CI entirely below 0, got [{lo}, {hi}]"

    def test_paired_bootstrap_ci_includes_zero_when_no_diff(self):
        """When baseline == comparison, CI should include zero."""
        vals = [100, 110, 120, 130, 140]
        lo, hi = paired_bootstrap_ci(vals, vals, n_bootstrap=5000, seed=42)
        assert lo <= 0 <= hi

    def test_paired_permutation_significant(self):
        """Permutation test should detect consistent difference."""
        baseline = [100, 110, 120, 130, 140]
        comparison = [80, 90, 100, 110, 120]
        p = paired_permutation_test(baseline, comparison, n_permutations=5000, seed=42)
        assert p < 0.05, f"Expected p < 0.05 for consistent S4 < S3, got {p}"

    def test_paired_permutation_not_significant(self):
        """Permutation test should not reject when no difference."""
        baseline = [100, 110, 120]
        comparison = [110, 100, 120]  # Same values, different pair assignment
        p = paired_permutation_test(baseline, comparison, n_permutations=5000, seed=42)
        assert p > 0.1, f"Expected p > 0.1 for no effect, got {p}"

    def test_cohens_d_paired_negative_when_comparison_lower(self):
        """Paired Cohen's d should be negative when comparison < baseline."""
        d = cohens_d_paired([100, 110, 120, 130], [95, 102, 112, 125])
        assert d < 0

    def test_cohens_d_paired_zero_when_identical(self):
        """Paired Cohen's d should be zero when all diffs are zero."""
        d = cohens_d_paired([100, 110, 120], [100, 110, 120])
        assert d == 0.0

    def test_paired_stats_require_equal_length(self):
        """Paired functions should work with equal-length arrays."""
        lo, hi = paired_bootstrap_ci([1, 5, 3, 7], [3, 8, 6, 12])
        assert lo > 0  # comparison is consistently higher
        d = cohens_d_paired([1, 5, 3, 7], [3, 8, 6, 12])
        assert d > 0
