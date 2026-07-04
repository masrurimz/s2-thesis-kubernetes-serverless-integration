"""Tests for baseline models."""

import pytest
import numpy as np

from prediction.training.baselines.naive import NaivePredictor, SeasonalNaivePredictor
from prediction.training.baselines.moving_avg import MovingAveragePredictor, ExponentialMovingAveragePredictor


class TestNaivePredictor:
    def test_predict_from_series(self):
        predictor = NaivePredictor()
        series = np.array([10, 20, 30, 40, 50])
        predictions = predictor.predict_from_series(series)

        assert predictions[1] == 10
        assert predictions[2] == 20
        assert predictions[4] == 40

    def test_fit_stores_last_value(self):
        predictor = NaivePredictor()
        predictor.fit(None, np.array([1, 2, 3, 4, 5]))
        assert predictor.last_value == 5

    def test_predict_returns_last_value(self):
        predictor = NaivePredictor()
        predictor.fit(None, np.array([1, 2, 3, 4, 100]))
        predictions = predictor.predict(np.zeros(3))
        assert all(p == 100 for p in predictions)


class TestSeasonalNaivePredictor:
    def test_predict_from_series_with_period(self):
        predictor = SeasonalNaivePredictor(period=3)
        series = np.array([10, 20, 30, 40, 50, 60, 70])
        predictions = predictor.predict_from_series(series)

        assert predictions[3] == 10
        assert predictions[4] == 20
        assert predictions[6] == 40


class TestMovingAveragePredictor:
    def test_predict_from_series(self):
        predictor = MovingAveragePredictor(window_size=3)
        series = np.array([10, 20, 30, 40, 50])
        predictions = predictor.predict_from_series(series)

        assert predictions[3] == pytest.approx((10 + 20 + 30) / 3)
        assert predictions[4] == pytest.approx((20 + 30 + 40) / 3)

    def test_fit_stores_history(self):
        predictor = MovingAveragePredictor(window_size=3)
        predictor.fit(None, np.array([1, 2, 3, 4, 5]))
        assert predictor.history == [3, 4, 5]


class TestExponentialMovingAveragePredictor:
    def test_predict_from_series(self):
        predictor = ExponentialMovingAveragePredictor(alpha=0.5)
        series = np.array([100, 100, 100, 100])
        predictions = predictor.predict_from_series(series)

        assert all(p == 100 for p in predictions)

    def test_alpha_effect(self):
        high_alpha = ExponentialMovingAveragePredictor(alpha=0.9)
        low_alpha = ExponentialMovingAveragePredictor(alpha=0.1)

        series = np.array([0, 100, 100, 100])

        high_pred = high_alpha.predict_from_series(series)
        low_pred = low_alpha.predict_from_series(series)

        assert high_pred[2] > low_pred[2]
