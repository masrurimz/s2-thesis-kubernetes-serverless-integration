"""The paired permutation test: exact where it can be, and directional.

H2 claims S4 (predictive) beats S3 (reactive), so the p-value is the lower-tail
probability — the chance of seeing a mean difference at least this favourable if
prediction made no difference. An effect running the other way scores 1.0.

The number matters: five pairs is the design's minimum because 2^-5 = 0.03125 is the
smallest p five pairs can produce, so the exact test makes that bound reachable
instead of approximate.
"""

import numpy as np
import pytest

from shared.stats import (
    cohens_d_paired,
    effect_size_label,
    paired_permutation_p_from_diffs,
    paired_permutation_test,
)


class TestExactDirection:
    def test_five_favourable_pairs_hit_the_exact_bound(self):
        assert paired_permutation_p_from_diffs([-1.0, -2.0, -3.0, -4.0, -5.0]) == pytest.approx(1 / 32)

    def test_one_adverse_pair_doubles_the_count(self):
        # Three sign flips can still leave the sum negative: [4] adversed, plus the
        # all-favourable flip pattern itself.
        assert paired_permutation_p_from_diffs([-1.0, -2.0, -3.0, -4.0, 5.0]) == pytest.approx(10 / 32)

    def test_a_single_favourable_pair_cannot_clear_five_percent(self):
        assert paired_permutation_p_from_diffs([-60.0]) == pytest.approx(0.5)

    def test_a_single_adverse_pair_is_no_evidence(self):
        assert paired_permutation_p_from_diffs([60.0]) == pytest.approx(1.0)

    def test_an_all_adverse_sample_is_no_evidence(self):
        assert paired_permutation_p_from_diffs([1.0, 2.0, 3.0]) == pytest.approx(1.0)

    def test_no_pairs_is_one(self):
        assert paired_permutation_p_from_diffs([]) == 1.0

    def test_baseline_and_comparison_form_matches_the_diffs_form(self):
        baseline = [100.0, 110.0, 120.0]
        comparison = [90.0, 100.0, 105.0]

        assert paired_permutation_test(baseline, comparison) == pytest.approx(
            paired_permutation_p_from_diffs([-10.0, -10.0, -15.0])
        )


class TestSampledPath:
    def test_a_large_sample_is_sampled_and_seeded(self):
        diffs = [-1.0] * 25

        first = paired_permutation_p_from_diffs(diffs)
        second = paired_permutation_p_from_diffs(diffs)

        assert first == second
        # A maximal effect cannot be p = 0: the observed arrangement is one of the
        # possibilities, so the smallest reportable value is 1/(n_permutations + 1).
        assert first == pytest.approx(1 / 10001)


class TestEffectSize:
    def test_one_pair_has_no_defined_effect_size(self):
        assert np.isnan(cohens_d_paired([100.0], [160.0]))
        assert effect_size_label(cohens_d_paired([100.0], [160.0])) == "undefined"

    def test_a_separated_pair_sample_reports_large(self):
        d = cohens_d_paired([100.0, 100.0, 100.0], [160.0, 170.0, 165.0])

        assert d > 0.8
        assert effect_size_label(d) == "large"

    def test_identical_differences_are_a_zero_effect(self):
        assert cohens_d_paired([100.0, 100.0], [110.0, 110.0]) == 0.0
        assert effect_size_label(0.0) == "negligible"
