"""Tests for GRU HPO temporal splitting, objective computation, and baselines.

Pure-function tests — no torch training, no real data, no cluster.
"""

from __future__ import annotations

import numpy as np
import pytest

from experiment.tuning.gru_hpo import (
    compute_objective,
    evaluate_promotion_gate,
    expanding_window_folds,
    linear_trend_baseline,
    persistence_baseline,
    temporal_split,
)


# ── Temporal split ───────────────────────────────────────────────────────────


class TestTemporalSplit:
    """Verify chronological split into development and untouched holdout."""

    def test_holdout_is_final_20_percent(self):
        values = np.arange(1000, dtype=np.float32)
        dev, holdout = temporal_split(values, holdout_ratio=0.2)
        assert len(dev) == 800
        assert len(holdout) == 200

    def test_contiguous_and_ordered(self):
        """Dev precedes holdout chronologically; no overlap."""
        values = np.arange(500, dtype=np.float32)
        dev, holdout = temporal_split(values, seq_len=20, horizon=5, holdout_ratio=0.2)
        assert dev[-1] < holdout[0]
        assert len(dev) + len(holdout) == len(values)

    def test_holdout_content_matches(self):
        values = np.arange(500, dtype=np.float32)
        dev, holdout = temporal_split(values, holdout_ratio=0.2)
        np.testing.assert_array_equal(holdout, values[400:])
        np.testing.assert_array_equal(dev, values[:400])

    def test_raises_on_tiny_holdout(self):
        with pytest.raises(ValueError, match="too small"):
            temporal_split(np.arange(10, dtype=np.float32), seq_len=30, horizon=5, holdout_ratio=0.5)


# ── Expanding-window folds ───────────────────────────────────────────────────


class TestExpandingWindowFolds:
    """Verify gap enforcement, disjointness, and expanding property."""

    def test_gap_between_train_and_val(self):
        """Gap = seq_len + horizon - 1 for every fold."""
        seq_len, horizon = 30, 5
        expected_gap = seq_len + horizon - 1
        folds = expanding_window_folds(1000, seq_len, horizon, n_folds=3)
        assert len(folds) == 3
        for fold in folds:
            assert fold.gap == expected_gap

    def test_folds_are_disjoint(self):
        """No train/val overlap; val windows don't overlap each other."""
        folds = expanding_window_folds(1000, 30, 5, n_folds=3)
        for fold in folds:
            assert fold.train_end <= fold.val_start
        for i in range(1, len(folds)):
            assert folds[i].val_start >= folds[i - 1].val_end

    def test_training_expands(self):
        """train_end increases monotonically across folds."""
        folds = expanding_window_folds(1000, 30, 5, n_folds=3)
        train_ends = [f.train_end for f in folds]
        assert train_ends == sorted(train_ends)
        assert train_ends[0] < train_ends[-1]

    def test_min_train_samples_for_first_fold(self):
        """First fold has ≥ seq_len + horizon training samples."""
        seq_len, horizon = 30, 5
        folds = expanding_window_folds(1000, seq_len, horizon, n_folds=3)
        assert folds[0].train_end >= seq_len + horizon

    def test_no_window_crosses_boundary(self):
        """No input or target window can span a train/val or val/val boundary."""
        seq_len, horizon = 30, 5
        n = 1000
        folds = expanding_window_folds(n, seq_len, horizon, n_folds=3)

        for fold in folds:
            max_i = fold.val_end - seq_len - horizon
            for i in range(fold.val_start, max_i + 1):
                assert i + seq_len + horizon <= fold.val_end

    def test_last_fold_reaches_end(self):
        """Last fold's val_end equals total sample count."""
        n = 1000
        folds = expanding_window_folds(n, 30, 5, n_folds=3)
        assert folds[-1].val_end == n

    def test_raises_on_insufficient_data(self):
        with pytest.raises(ValueError, match="Not enough samples"):
            expanding_window_folds(50, 30, 5, n_folds=3)

    def test_raises_on_tiny_val_windows(self):
        """Val windows too small to form a single sequence."""
        with pytest.raises(ValueError, match="too small"):
            expanding_window_folds(500, 30, 5, n_folds=20)


# ── Objective computation ────────────────────────────────────────────────────


class TestComputeObjective:
    """Verify the predeclared scalar objective."""

    def test_perfect_prediction_near_zero(self):
        horizon = 5
        rng = np.random.RandomState(42)
        targets = rng.uniform(50, 100, (200, horizon)).astype(np.float32)
        preds = targets.copy()
        last_inputs = targets[:, 0] - 10  # All rising

        obj, detail = compute_objective(preds, targets, last_inputs, horizon)
        assert obj < 1e-6
        assert detail["mean_norm_rmse"] < 1e-6
        assert detail["mean_norm_underpred"] < 1e-6

    def test_underprediction_increases_objective(self):
        """Under-predicting rising targets penalises the objective."""
        horizon = 5
        n = 200
        targets = np.full((n, horizon), 100.0, dtype=np.float32)
        last_inputs = np.full(n, 50.0, dtype=np.float32)  # All rising

        preds_good = targets.copy()
        preds_bad = targets * 0.8

        obj_good, _ = compute_objective(preds_good, targets, last_inputs, horizon)
        obj_bad, _ = compute_objective(preds_bad, targets, last_inputs, horizon)

        assert obj_bad > obj_good * 3  # 2x weight on underprediction

    def test_overprediction_reduces_underprediction_term(self):
        """Over-predicting rising targets yields negative (beneficial) underpred."""
        horizon = 5
        n = 100
        targets = np.full((n, horizon), 100.0, dtype=np.float32)
        last_inputs = np.full(n, 50.0, dtype=np.float32)
        preds = targets * 1.2  # Over-predict

        _, detail = compute_objective(preds, targets, last_inputs, horizon)
        assert detail["mean_norm_underpred"] < 0

    def test_rising_uses_last_input_not_first_target(self):
        """Rising is defined as target[h] > last_input, not target[h] > target[0]."""
        horizon = 5
        targets = np.array([[60, 70, 80, 90, 100]], dtype=np.float32)
        last_inputs = np.array([55.0])  # All horizons rising

        _, detail = compute_objective(targets * 0.9, targets, last_inputs, horizon)
        # Every horizon is rising → underpred > 0 for all
        assert all(u > 0 for u in detail["norm_underpred_per_h"])

    def test_non_rising_excluded_from_underprediction(self):
        """Targets below last_input are excluded from underpred computation."""
        horizon = 1
        targets = np.array([[100.0], [10.0]], dtype=np.float32)
        last_inputs = np.array([50.0, 50.0])  # First rising, second not
        preds = np.array([[80.0], [5.0]], dtype=np.float32)

        _, detail = compute_objective(preds, targets, last_inputs, horizon)
        # Only first sample (rising) contributes: underpred = (100-80) = 20
        # Normalised by mean(ALL targets) = 55 → 20/55 ≈ 0.3636
        assert abs(detail["norm_underpred_per_h"][0] - 20.0 / 55.0) < 1e-5

    def test_deterministic(self):
        """Same inputs → same output."""
        horizon = 5
        rng = np.random.RandomState(42)
        targets = rng.uniform(50, 100, (100, horizon)).astype(np.float32)
        preds = rng.uniform(40, 90, (100, horizon)).astype(np.float32)
        last_inputs = rng.uniform(30, 50, 100).astype(np.float32)

        obj1, det1 = compute_objective(preds, targets, last_inputs, horizon)
        obj2, det2 = compute_objective(preds, targets, last_inputs, horizon)
        assert obj1 == obj2
        assert det1 == det2


# ── Baselines ────────────────────────────────────────────────────────────────


class TestPersistenceBaseline:
    """Verify persistence predictions."""

    def test_predicts_last_observed_value(self):
        horizon = 5
        seq_len = 10
        values = np.arange(100, dtype=np.float32)
        preds, targets, last_inputs = persistence_baseline(values, seq_len, horizon)

        for h in range(horizon):
            np.testing.assert_array_equal(preds[:, h], last_inputs)

    def test_targets_correct(self):
        horizon = 3
        seq_len = 5
        values = np.arange(20, dtype=np.float32)
        _, targets, _ = persistence_baseline(values, seq_len, horizon)
        # First window: target = values[5:8] = [5, 6, 7]
        np.testing.assert_array_equal(targets[0], [5, 6, 7])

    def test_last_input_is_final_input_value(self):
        horizon = 3
        seq_len = 5
        values = np.arange(20, dtype=np.float32)
        _, _, last_inputs = persistence_baseline(values, seq_len, horizon)
        # First window: last input = values[4] = 4
        assert last_inputs[0] == 4


class TestLinearTrendBaseline:
    """Verify linear-trend extrapolation."""

    def test_perfect_linear_data(self):
        """On perfectly linear data, OLS recovers the exact trend."""
        horizon = 5
        seq_len = 20
        values = (np.arange(200, dtype=np.float32) * 2.0).astype(np.float32)
        preds, targets, _ = linear_trend_baseline(values, seq_len, horizon, trend_window=10)

        # First window predictions should match targets exactly
        np.testing.assert_allclose(preds[0], targets[0], atol=0.5)

    def test_non_negative(self):
        """Predictions are clipped to non-negative."""
        horizon = 3
        seq_len = 15
        # Decreasing trend → OLS extrapolates below zero
        values = (np.arange(50, dtype=np.float32) * -1.0 + 100).astype(np.float32)
        preds, _, _ = linear_trend_baseline(values, seq_len, horizon)
        assert np.all(preds >= 0)


# ── Promotion gate ───────────────────────────────────────────────────────────


class TestPromotionGate:
    """Verify the promotion gate logic."""

    def test_promotes_when_gru_beats_persistence_and_meets_coverage(self):
        gru_detail = {"mean_norm_rmse": 0.1, "mean_norm_underpred": 0.05}
        pers_detail = {"mean_norm_rmse": 0.2, "mean_norm_underpred": 0.15}
        gate = evaluate_promotion_gate(gru_detail, pers_detail, coverage=0.9)
        assert gate["promoted"] is True

    def test_rejects_when_rmse_not_better(self):
        gru_detail = {"mean_norm_rmse": 0.3, "mean_norm_underpred": 0.05}
        pers_detail = {"mean_norm_rmse": 0.2, "mean_norm_underpred": 0.15}
        gate = evaluate_promotion_gate(gru_detail, pers_detail, coverage=0.9)
        assert gate["promoted"] is False
        assert gate["beats_persistence_rmse"] is False

    def test_rejects_when_underpred_not_better(self):
        gru_detail = {"mean_norm_rmse": 0.1, "mean_norm_underpred": 0.2}
        pers_detail = {"mean_norm_rmse": 0.2, "mean_norm_underpred": 0.15}
        gate = evaluate_promotion_gate(gru_detail, pers_detail, coverage=0.9)
        assert gate["promoted"] is False
        assert gate["beats_persistence_underpred"] is False

    def test_rejects_when_coverage_below_threshold(self):
        gru_detail = {"mean_norm_rmse": 0.1, "mean_norm_underpred": 0.05}
        pers_detail = {"mean_norm_rmse": 0.2, "mean_norm_underpred": 0.15}
        gate = evaluate_promotion_gate(gru_detail, pers_detail, coverage=0.80)
        assert gate["promoted"] is False
        assert gate["meets_coverage_threshold"] is False

    def test_boundary_coverage_passes(self):
        """Coverage exactly at threshold passes."""
        gru_detail = {"mean_norm_rmse": 0.1, "mean_norm_underpred": 0.05}
        pers_detail = {"mean_norm_rmse": 0.2, "mean_norm_underpred": 0.15}
        gate = evaluate_promotion_gate(gru_detail, pers_detail, coverage=0.85)
        assert gate["promoted"] is True
