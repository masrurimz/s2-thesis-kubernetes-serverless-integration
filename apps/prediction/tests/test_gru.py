"""Tests for GRU predictor."""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from prediction.gru_predictor import GRUPredictor, GRUConfig


@pytest.fixture
def sample_data():
    """Generate synthetic traffic data for testing (200 samples)."""
    data = []
    base = datetime.now()
    for i in range(200):
        data.append(
            {
                "timestamp": base + timedelta(minutes=i),
                "total_requests": 100 + 20 * np.sin(i / 10) + np.random.normal(0, 5),
            }
        )
    return pd.DataFrame(data)


class TestGRUConfig:
    def test_default_values(self):
        config = GRUConfig()
        assert config.hidden_size == 128
        assert config.sequence_length == 30
        assert config.epochs == 100

    def test_custom_values(self):
        config = GRUConfig(hidden_size=128, sequence_length=60)
        assert config.hidden_size == 128
        assert config.sequence_length == 60


class TestGRUPredictor:
    def test_init(self):
        predictor = GRUPredictor()
        assert predictor.is_trained is False
        assert predictor.config.hidden_size == 128

    def test_train(self, sample_data):
        config = GRUConfig(epochs=5, sequence_length=10)
        predictor = GRUPredictor(config)

        metrics = predictor.train(sample_data)

        assert predictor.is_trained is True
        assert "val_rmse" in metrics
        assert metrics["val_rmse"] >= 0
        assert "val_rmse_percent" in metrics

    def test_predict_after_training(self, sample_data):
        config = GRUConfig(epochs=5, sequence_length=10)
        predictor = GRUPredictor(config)
        predictor.train(sample_data)

        recent = sample_data["total_requests"].values[-15:]
        result = predictor.predict(recent)

        assert "predicted_requests" in result
        assert result["predicted_requests"] > 0
        assert "confidence" in result

    def test_predict_before_training(self):
        predictor = GRUPredictor()

        with pytest.raises(RuntimeError, match="not trained"):
            predictor.predict(np.array([100, 110, 120]))

    def test_predict_with_short_history(self, sample_data):
        config = GRUConfig(epochs=5, sequence_length=10)
        predictor = GRUPredictor(config)
        predictor.train(sample_data)

        # Predict with fewer values than sequence_length
        short_history = np.array([100, 110, 120])
        result = predictor.predict(short_history)

        assert "predicted_requests" in result
        assert result["predicted_requests"] > 0

    def test_insufficient_data_error(self):
        config = GRUConfig(sequence_length=30)
        predictor = GRUPredictor(config)

        # Only 20 samples, need at least 40
        small_df = pd.DataFrame(
            {"timestamp": [datetime.now() + timedelta(minutes=i) for i in range(20)], "total_requests": [100] * 20}
        )

        with pytest.raises(ValueError, match="Need at least"):
            predictor.train(small_df)

    def test_normalization(self, sample_data):
        config = GRUConfig(epochs=5, sequence_length=10)
        predictor = GRUPredictor(config)
        predictor.train(sample_data)

        # Check scaler stats are set
        assert predictor.scaler_mean != 0
        assert predictor.scaler_std != 1

        # Test normalization roundtrip
        test_data = np.array([100.0, 150.0, 200.0])
        normalized = predictor._normalize(test_data)
        denormalized = predictor._denormalize(normalized)

        np.testing.assert_array_almost_equal(test_data, denormalized)

    def test_save_load_model(self, sample_data, tmp_path):
        config = GRUConfig(epochs=5, sequence_length=10)
        predictor = GRUPredictor(config)
        predictor.train(sample_data)

        # Save model
        model_path = tmp_path / "test_model.pt"
        predictor.save_model(model_path)

        assert model_path.exists()

        # Load in new predictor
        new_predictor = GRUPredictor()
        loaded = new_predictor.load_model(model_path)

        assert loaded is True
        assert new_predictor.is_trained is True
        assert new_predictor.scaler_mean == predictor.scaler_mean

        # Check predictions are similar
        recent = sample_data["total_requests"].values[-15:]
        orig_pred = predictor.predict(recent)
        loaded_pred = new_predictor.predict(recent)

        np.testing.assert_almost_equal(orig_pred["predicted_requests"], loaded_pred["predicted_requests"], decimal=1)

    def test_load_nonexistent_model(self, tmp_path):
        predictor = GRUPredictor()
        loaded = predictor.load_model(tmp_path / "nonexistent.pt")

        assert loaded is False
        assert predictor.is_trained is False


class TestGRUWithRPSColumn:
    def test_train_with_rps_column(self):
        config = GRUConfig(epochs=5, sequence_length=10)
        predictor = GRUPredictor(config)

        # Use 'rps' instead of 'total_requests'
        df = pd.DataFrame(
            {
                "timestamp": [datetime.now() + timedelta(minutes=i) for i in range(100)],
                "rps": [100 + 10 * np.sin(i / 5) for i in range(100)],
            }
        )

        metrics = predictor.train(df)

        assert predictor.is_trained is True
        assert "val_rmse" in metrics


class TestMultiHorizonForecast:
    """Tests for direct multi-horizon output (schema v2)."""

    @pytest.fixture
    def trained_predictor(self, sample_data):
        config = GRUConfig(epochs=5, sequence_length=10, prediction_horizon=5)
        predictor = GRUPredictor(config)
        predictor.train(sample_data)
        return predictor

    def test_predict_returns_five_horizons(self, trained_predictor):
        """predict() must return exactly prediction_horizon point/upper forecasts."""
        recent = np.arange(100, 115, dtype=np.float32)
        result = trained_predictor.predict(recent)
        assert len(result["point_forecasts"]) == 5
        assert len(result["upper_forecasts"]) == 5
        assert result["horizon"] == 5

    def test_predicted_requests_is_max_upper(self, trained_predictor):
        """predicted_requests must equal max(upper_forecasts) for conservative contract."""
        recent = np.arange(100, 115, dtype=np.float32)
        result = trained_predictor.predict(recent)
        assert result["predicted_requests"] == max(result["upper_forecasts"])

    def test_upper_forecasts_gte_point_forecasts(self, trained_predictor):
        """Upper envelope must be >= point forecast for every horizon."""
        recent = np.arange(100, 115, dtype=np.float32)
        result = trained_predictor.predict(recent)
        for pf, uf in zip(result["point_forecasts"], result["upper_forecasts"]):
            assert uf >= pf

    def test_upper_offsets_non_negative(self, trained_predictor):
        """Per-horizon upper offsets must be non-negative."""
        assert len(trained_predictor.upper_offsets) == 5
        assert all(o >= 0 for o in trained_predictor.upper_offsets)

    def test_val_coverage_reported(self, trained_predictor):
        """Validation coverage must be reported after training."""
        assert 0.0 <= trained_predictor.val_coverage <= 1.0

    def test_metrics_include_per_horizon(self, sample_data):
        """Training metrics must include per-horizon breakdown."""
        config = GRUConfig(epochs=5, sequence_length=10, prediction_horizon=5)
        predictor = GRUPredictor(config)
        metrics = predictor.train(sample_data)
        assert "rmse_per_horizon" in metrics
        assert len(metrics["rmse_per_horizon"]) == 5
        assert "upper_offsets" in metrics
        assert "val_upper_coverage" in metrics
        assert "underprediction_rising" in metrics


class TestArtifactSchemaV2:
    """Tests for versioned artifact save/load with strict validation."""

    def test_save_load_roundtrip_preserves_forecasts(self, sample_data, tmp_path):
        """Saved and reloaded model must produce identical predictions."""
        config = GRUConfig(epochs=5, sequence_length=10, prediction_horizon=5)
        predictor = GRUPredictor(config)
        predictor.train(sample_data)

        recent = sample_data["total_requests"].values[-15:]
        original_pred = predictor.predict(recent)

        model_path = tmp_path / "test_v2.pt"
        predictor.save_model(model_path)
        assert model_path.exists()

        loaded = GRUPredictor()
        assert loaded.load_model(model_path) is True
        assert loaded.is_trained is True
        assert loaded.config.prediction_horizon == 5

        loaded_pred = loaded.predict(recent)
        np.testing.assert_almost_equal(
            original_pred["predicted_requests"],
            loaded_pred["predicted_requests"],
            decimal=1,
        )

    def test_save_creates_json_sidecar(self, sample_data, tmp_path):
        """Artifact save must produce a human-readable JSON sidecar."""
        import json

        config = GRUConfig(epochs=5, sequence_length=10, prediction_horizon=5)
        predictor = GRUPredictor(config)
        predictor.train(sample_data)

        model_path = tmp_path / "sidecar.pt"
        predictor.save_model(model_path)

        sidecar = model_path.with_suffix(".json")
        assert sidecar.exists()
        meta = json.loads(sidecar.read_text())
        assert meta["schema_version"] == 2
        assert meta["prediction_horizon"] == 5
        assert "upper_offsets" in meta

    def test_load_rejects_v1_artifact(self, tmp_path):
        """Schema v1 (single-output) artifacts must be rejected."""
        import torch

        # Craft a v1 artifact (old format: no schema_version, prediction_horizon=1)
        v1_metadata = {
            "scaler_mean": 100.0,
            "scaler_std": 20.0,
            "config": {
                "input_size": 1,
                "hidden_size": 128,
                "num_layers": 1,
                "dropout": 0.1,
                "sequence_length": 30,
                "prediction_horizon": 1,
                "learning_rate": 0.001,
                "batch_size": 32,
                "epochs": 100,
                "early_stopping_patience": 10,
            },
            "rmse": 5.0,
            "mae": 3.0,
            "is_trained": True,
        }
        v1_path = tmp_path / "v1_model.pt"
        torch.save({"model_state": {}, "metadata": v1_metadata}, v1_path)

        predictor = GRUPredictor()
        result = predictor.load_model(v1_path)
        assert result is False
        assert predictor.is_trained is False

    def test_load_nonexistent_returns_false(self, tmp_path):
        predictor = GRUPredictor()
        assert predictor.load_model(tmp_path / "nonexistent.pt") is False
        assert predictor.is_trained is False

    def test_upper_offsets_preserved_through_roundtrip(self, sample_data, tmp_path):
        """Upper offsets must survive save/load exactly."""
        config = GRUConfig(epochs=5, sequence_length=10, prediction_horizon=5)
        predictor = GRUPredictor(config)
        predictor.train(sample_data)

        original_offsets = predictor.upper_offsets.copy()

        model_path = tmp_path / "offsets.pt"
        predictor.save_model(model_path)

        loaded = GRUPredictor()
        loaded.load_model(model_path)
        np.testing.assert_array_almost_equal(loaded.upper_offsets, original_offsets, decimal=5)


class TestConditionalDropout:
    """Tests for conditional recurrent dropout behavior."""

    def test_single_layer_recurrent_dropout_is_zero(self):
        """nn.GRU dropout must be zero for single-layer (PyTorch ignores it)."""
        config = GRUConfig(num_layers=1, dropout=0.3)
        assert config.effective_recurrent_dropout == 0.0

    def test_multi_layer_recurrent_dropout_applied(self):
        """nn.GRU dropout should be the configured value for multi-layer."""
        config = GRUConfig(num_layers=2, dropout=0.3)
        assert config.effective_recurrent_dropout == 0.3

    def test_head_dropout_always_active(self):
        """Head dropout applies regardless of layer count."""
        config1 = GRUConfig(num_layers=1, head_dropout=0.2)
        config2 = GRUConfig(num_layers=2, head_dropout=0.2)
        assert config1.head_dropout == 0.2
        assert config2.head_dropout == 0.2


class TestModelLoaderDelegation:
    """Tests that GRUModelLoader delegates to canonical GRUPredictor."""

    def test_model_loader_predict_returns_multi_horizon(self, sample_data, tmp_path):
        """ModelLoader.predict() must return point/upper forecasts."""
        from prediction.model_loader import GRUModelLoader

        config = GRUConfig(epochs=5, sequence_length=10, prediction_horizon=5)
        predictor = GRUPredictor(config)
        predictor.train(sample_data)
        model_path = tmp_path / "loader_test.pt"
        predictor.save_model(model_path)

        loader = GRUModelLoader(model_path)
        assert loader.is_loaded is True

        history = sample_data["total_requests"].values.tolist()[-15:]
        result = loader.predict(history)
        assert "point_forecasts" in result
        assert "upper_forecasts" in result
        assert len(result["point_forecasts"]) == 5
        assert result["predicted_requests"] > 0

    def test_model_loader_rejects_v1_artifact(self, tmp_path):
        """ModelLoader must reject schema v1 artifacts."""
        import torch
        from prediction.model_loader import GRUModelLoader

        v1_metadata = {
            "scaler_mean": 100.0,
            "scaler_std": 20.0,
            "config": {
                "input_size": 1,
                "hidden_size": 64,
                "num_layers": 2,
                "dropout": 0.2,
                "sequence_length": 30,
                "prediction_horizon": 1,
                "learning_rate": 0.001,
                "batch_size": 32,
                "epochs": 100,
                "early_stopping_patience": 10,
            },
            "rmse": 5.0,
            "mae": 3.0,
            "is_trained": True,
        }
        v1_path = tmp_path / "v1.pt"
        torch.save({"model_state": {}, "metadata": v1_metadata}, v1_path)

        loader = GRUModelLoader(v1_path)
        assert loader.is_loaded is False

    def test_model_loader_status_includes_horizon(self, sample_data, tmp_path):
        """ModelLoader.get_status() must include horizon and interval info."""
        from prediction.model_loader import GRUModelLoader

        config = GRUConfig(epochs=5, sequence_length=10, prediction_horizon=5, sample_interval_sec=15)
        predictor = GRUPredictor(config)
        predictor.train(sample_data)
        model_path = tmp_path / "status_test.pt"
        predictor.save_model(model_path)

        loader = GRUModelLoader(model_path)
        status = loader.get_status()
        assert status["loaded"] is True
        assert status["prediction_horizon"] == 5
        assert status["sample_interval_sec"] == 15
        assert status["schema_version"] == 2
