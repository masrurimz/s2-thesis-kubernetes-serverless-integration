"""Behavioral tests for the shared statistical primitives.

These functions are load-bearing across libs/analysis, apps/analysis, and
apps/experiment — they must keep their sign/magnitude contract.
"""

from __future__ import annotations


from shared.stats import (
    bootstrap_ci,
    bootstrap_ci_diff,
    cohens_d,
    effect_size_label,
    holm_bonferroni,
    mann_whitney_u,
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
