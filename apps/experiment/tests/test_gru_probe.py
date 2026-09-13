"""Tests for gru_probe window isolation and OLS train-region containment.

Pure-function tests — no torch training, no real data, no cluster.
"""

from __future__ import annotations

import numpy as np
from experiment.tuning.gru_probe import (
    PROBE_REPLAY_WINDOW,
    ProbeWindows,
    _segment_sequences,
    ols_autoreg_fit,
    ols_autoreg_predict,
    probe_windows,
    segment_index_matrix,
)

# Small synthetic protocol: same shape as the frozen ClarkNet splits
# (fit → val gap = seq_len + horizon - 1 = 38, val → test gap = 38).
SEQ_LEN, HORIZON = 30, 9
SYNTH = ProbeWindows(
    seq_len=SEQ_LEN,
    horizon=HORIZON,
    fit_end=300,
    val_start=338,
    val_end=400,
    test_start=438,
    embargo_used=38,
)


def test_training_windows_never_touch_test_region() -> None:
    """Training/validation windows are bit-identical when the test region mutates."""
    rng = np.random.default_rng(7)
    values = rng.normal(50.0, 5.0, size=800).astype(np.float64)

    fit_X, fit_y, _, _ = _segment_sequences(values, 0, SYNTH.fit_end, SEQ_LEN, HORIZON)
    val_X, val_y, _, _ = _segment_sequences(values, SYNTH.val_start, SYNTH.val_end, SEQ_LEN, HORIZON)

    mutated = values.copy()
    mutated[SYNTH.test_start :] += 1000.0
    fit_X_mut, fit_y_mut, _, _ = _segment_sequences(mutated, 0, SYNTH.fit_end, SEQ_LEN, HORIZON)
    val_X_mut, val_y_mut, _, _ = _segment_sequences(mutated, SYNTH.val_start, SYNTH.val_end, SEQ_LEN, HORIZON)

    np.testing.assert_array_equal(fit_X, fit_X_mut)
    np.testing.assert_array_equal(fit_y, fit_y_mut)
    np.testing.assert_array_equal(val_X, val_X_mut)
    np.testing.assert_array_equal(val_y, val_y_mut)

    fit_idx = segment_index_matrix(0, SYNTH.fit_end, SEQ_LEN, HORIZON)
    val_idx = segment_index_matrix(SYNTH.val_start, SYNTH.val_end, SEQ_LEN, HORIZON)
    assert fit_idx.max() == SYNTH.fit_end - 1
    assert val_idx.max() == SYNTH.val_end - 1
    assert fit_idx.max() < SYNTH.test_start
    assert val_idx.max() < SYNTH.test_start

    # Frozen 30-window boundaries and derived window120 boundaries keep the
    # replay window inside the test region with an embargo ≥ window+horizon-1.
    w30 = probe_windows("baseline")
    assert (w30.fit_end, w30.val_start, w30.val_end, w30.test_start) == (22500, 22539, 26205, 26243)
    w120 = probe_windows("window120")
    assert w120.test_start == 26205 + 382
    assert w120.test_start - w120.val_end >= w120.embargo_min
    assert w120.val_start - w120.fit_end >= w120.embargo_min
    assert w120.test_start <= PROBE_REPLAY_WINDOW[0]


def test_ols_arm_sees_only_training_region() -> None:
    """OLS fit and its test predictions are bit-identical under wild test-region values."""
    rng = np.random.default_rng(11)
    values = rng.normal(50.0, 5.0, size=800).astype(np.float64)

    coef = ols_autoreg_fit(values, SYNTH)
    X_test, _, _, _ = _segment_sequences(values, SYNTH.test_start, len(values), SEQ_LEN, HORIZON)
    preds = ols_autoreg_predict(coef, X_test)

    mutated = values.copy()
    mutated[SYNTH.test_start :] = rng.uniform(0.0, 1_000_000.0, size=len(values) - SYNTH.test_start)

    # The refit must be blind to the test region: identical coefficients and
    # identical predictions when scoring the original test windows.
    coef_mut = ols_autoreg_fit(mutated, SYNTH)
    preds_mut = ols_autoreg_predict(coef_mut, X_test)

    np.testing.assert_array_equal(coef, coef_mut)
    np.testing.assert_array_equal(preds, preds_mut)

    fit_region_max = segment_index_matrix(0, SYNTH.val_end, SEQ_LEN, HORIZON).max()
    assert fit_region_max == SYNTH.val_end - 1
    assert fit_region_max < SYNTH.test_start


def test_calgary_pretrain_splits_and_isolation() -> None:
    """Cross-corpus lever: sanctioned Calgary boundaries, post-cut tail never read."""

    from experiment.tuning.calgary_pretrain import build_stage_a_arrays
    from experiment.tuning.splits import CALGARY_N, calgary_pretrain_split

    spec = calgary_pretrain_split()
    assert (spec.require_region("train").start, spec.require_region("train").stop) == (0, 1_757_796)
    assert (spec.require_region("validation").start, spec.require_region("validation").stop) == (1_757_834, 1_769_354)
    assert spec.require_region("validation").stop < CALGARY_N  # post-cut tail exists and is unused

    rng = np.random.default_rng(21)
    series = rng.gamma(1.0, 0.05, size=CALGARY_N)
    fit, val, stats = build_stage_a_arrays(series, spec)
    assert fit.max_index_consumed == spec.require_region("train").stop - 1
    assert val.max_index_consumed == spec.require_region("validation").stop - 1
    assert stats.fit_range.stop == spec.require_region("train").stop  # normalizer fitted on train only

    # Stage-A arrays are bit-identical when the never-read post-cut tail mutates.
    mutated = series.copy()
    mutated[spec.require_region("validation").stop :] += 1_000.0
    fit_m, val_m, _ = build_stage_a_arrays(mutated, spec)
    np.testing.assert_array_equal(fit.X, fit_m.X)
    np.testing.assert_array_equal(val.X, val_m.X)


def test_fold_internal_carve_honours_embargo() -> None:
    """Stage-B early-stop carve stays inside the fold's training region."""
    from experiment.tuning.calgary_pretrain import _internal_carve
    from experiment.tuning.splits import EMBARGO

    (fit_start, fit_stop), (ival_start, ival_stop) = _internal_carve(22_500)
    assert fit_start == 0
    assert ival_start - fit_stop == EMBARGO
    assert ival_stop == 22_500
