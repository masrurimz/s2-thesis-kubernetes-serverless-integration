"""Tests for model training and validation."""

import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from train_and_validate_model import generate_synthetic_traffic, validate_model
from prediction_engine.linear_model import TrafficPredictor


class TestSyntheticDataGeneration:
    """Tests for synthetic data generation."""

    def test_generates_correct_sample_count(self):
        """Test synthetic data has expected sample count."""
        data = generate_synthetic_traffic(duration_hours=1, base_rps=100)
        assert len(data) == 60  # 1 sample per minute

    def test_has_required_columns(self):
        """Test synthetic data has all required columns."""
        data = generate_synthetic_traffic(duration_hours=1, base_rps=100)

        required_cols = [
            "timestamp",
            "total_requests",
            "avg_response_time",
            "error_rate",
            "k3s_requests",
            "knative_requests",
        ]
        for col in required_cols:
            assert col in data.columns, f"Missing column: {col}"

    def test_requests_are_positive(self):
        """Test that request counts are always positive."""
        data = generate_synthetic_traffic(duration_hours=2, base_rps=100)
        assert data["total_requests"].min() >= 10


class TestModelTraining:
    """Tests for model training pipeline."""

    def test_model_training_produces_metrics(self):
        """Test that training produces expected metrics."""
        train_data = generate_synthetic_traffic(duration_hours=4, base_rps=100)

        predictor = TrafficPredictor()
        metrics = predictor.train(train_data)

        assert "rmse" in metrics
        assert "r2_score" in metrics
        assert "rmse_percent" in metrics
        assert metrics["rmse"] > 0

    def test_model_can_make_predictions(self):
        """Test trained model can make predictions."""
        train_data = generate_synthetic_traffic(duration_hours=4, base_rps=100)

        predictor = TrafficPredictor()
        predictor.train(train_data)

        result = predictor.predict(
            {
                "timestamp": int(np.datetime64("now").astype("int64") // 10**9),
                "total_requests": 100,
                "avg_response_time": 25,
                "k3s_requests": 80,
                "knative_requests": 20,
            }
        )

        assert "predicted_requests" in result
        assert result["predicted_requests"] >= 0


class TestModelValidation:
    """Tests for model validation."""

    def test_validation_produces_metrics(self):
        """Test full training and validation pipeline."""
        np.random.seed(42)
        train_data = generate_synthetic_traffic(duration_hours=4, base_rps=100)
        test_data = generate_synthetic_traffic(duration_hours=1, base_rps=100)

        predictor = TrafficPredictor()
        predictor.train(train_data)

        metrics = validate_model(predictor, test_data)

        assert "rmse" in metrics
        assert "rmse_percent" in metrics
        assert "mae" in metrics
        assert "mape" in metrics
        assert metrics["num_predictions"] > 0

    def test_rmse_is_reasonable(self):
        """Test RMSE is within reasonable bounds for synthetic data."""
        np.random.seed(42)
        train_data = generate_synthetic_traffic(duration_hours=8, base_rps=100)
        test_data = generate_synthetic_traffic(duration_hours=2, base_rps=100)

        predictor = TrafficPredictor()
        predictor.train(train_data)

        metrics = validate_model(predictor, test_data)

        # RMSE should be reasonable for synthetic data
        assert metrics["rmse_percent"] < 50, f"RMSE too high: {metrics['rmse_percent']:.2f}%"
