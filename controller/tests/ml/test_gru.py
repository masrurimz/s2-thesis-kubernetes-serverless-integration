"""Tests for GRU predictor."""
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from prediction.gru_predictor import GRUPredictor, GRUConfig


class TestGRUConfig:
    def test_default_values(self):
        config = GRUConfig()
        assert config.hidden_size == 64
        assert config.sequence_length == 30
        assert config.epochs == 100
    
    def test_custom_values(self):
        config = GRUConfig(hidden_size=128, sequence_length=60)
        assert config.hidden_size == 128
        assert config.sequence_length == 60


class TestGRUPredictor:
    @pytest.fixture
    def sample_data(self):
        data = []
        base = datetime.now()
        for i in range(200):
            data.append({
                'timestamp': base + timedelta(minutes=i),
                'total_requests': 100 + 20 * np.sin(i / 10) + np.random.normal(0, 5)
            })
        return pd.DataFrame(data)
    
    def test_init(self):
        predictor = GRUPredictor()
        assert predictor.is_trained is False
        assert predictor.config.hidden_size == 64
    
    def test_train(self, sample_data):
        config = GRUConfig(epochs=5, sequence_length=10)
        predictor = GRUPredictor(config)
        
        metrics = predictor.train(sample_data)
        
        assert predictor.is_trained is True
        assert 'val_rmse' in metrics
        assert metrics['val_rmse'] >= 0
        assert 'val_rmse_percent' in metrics
    
    def test_predict_after_training(self, sample_data):
        config = GRUConfig(epochs=5, sequence_length=10)
        predictor = GRUPredictor(config)
        predictor.train(sample_data)
        
        recent = sample_data['total_requests'].values[-15:]
        result = predictor.predict(recent)
        
        assert 'predicted_requests' in result
        assert result['predicted_requests'] > 0
        assert 'confidence' in result
    
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
        
        assert 'predicted_requests' in result
        assert result['predicted_requests'] > 0
    
    def test_insufficient_data_error(self):
        config = GRUConfig(sequence_length=30)
        predictor = GRUPredictor(config)
        
        # Only 20 samples, need at least 40
        small_df = pd.DataFrame({
            'timestamp': [datetime.now() + timedelta(minutes=i) for i in range(20)],
            'total_requests': [100] * 20
        })
        
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
        recent = sample_data['total_requests'].values[-15:]
        orig_pred = predictor.predict(recent)
        loaded_pred = new_predictor.predict(recent)
        
        np.testing.assert_almost_equal(
            orig_pred['predicted_requests'],
            loaded_pred['predicted_requests'],
            decimal=1
        )
    
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
        df = pd.DataFrame({
            'timestamp': [datetime.now() + timedelta(minutes=i) for i in range(100)],
            'rps': [100 + 10 * np.sin(i / 5) for i in range(100)]
        })
        
        metrics = predictor.train(df)
        
        assert predictor.is_trained is True
        assert 'val_rmse' in metrics
