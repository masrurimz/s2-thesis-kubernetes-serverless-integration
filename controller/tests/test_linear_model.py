"""Tests for linear regression prediction model."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import time

from prediction_engine.linear_model import TrafficPredictor


class TestTrafficPredictor:
    """Tests for TrafficPredictor class."""
    
    @pytest.fixture
    def predictor(self):
        """Create fresh predictor instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "model.joblib"
            yield TrafficPredictor(model_path=str(model_path))
    
    @pytest.fixture
    def training_data(self):
        """Generate synthetic training data."""
        base_time = int(datetime.now().timestamp())
        data = []
        for i in range(200):
            hour = (i // 60) % 24
            requests = 100 + 50 * np.sin(2 * np.pi * hour / 24) + np.random.normal(0, 5)
            data.append({
                'timestamp': base_time + i * 30,
                'total_requests': max(10, int(requests)),
                'avg_response_time': 25 + np.random.normal(0, 3),
                'error_rate': 0.01 + np.random.uniform(0, 0.02),
                'k3s_requests': max(8, int(requests * 0.8)),
                'knative_requests': max(2, int(requests * 0.2)),
                'k3s_weight': 80,
                'knative_weight': 20
            })
        return pd.DataFrame(data)
    
    def test_init(self, predictor):
        """Test predictor initialization."""
        assert predictor.is_trained is False
        assert predictor.model is not None
        assert predictor.scaler is not None
    
    def test_train_with_valid_data(self, predictor, training_data):
        """Test training with valid data."""
        metrics = predictor.train(training_data)
        
        assert predictor.is_trained is True
        assert 'rmse' in metrics
        assert 'r2_score' in metrics
        assert metrics['rmse'] >= 0
        assert -1 <= metrics['r2_score'] <= 1
    
    def test_train_with_insufficient_data(self, predictor):
        """Test training fails with insufficient data."""
        small_data = pd.DataFrame({
            'timestamp': [int(datetime.now().timestamp())],
            'total_requests': [100],
            'avg_response_time': [25.0],
            'error_rate': [0.01],
            'k3s_requests': [80],
            'knative_requests': [20],
            'k3s_weight': [80],
            'knative_weight': [20]
        })
        
        with pytest.raises(ValueError, match="Insufficient"):
            predictor.train(small_data)
    
    def test_predict_after_training(self, predictor, training_data):
        """Test prediction after training."""
        predictor.train(training_data)
        
        current_stats = {
            'timestamp': int(time.time()),
            'total_requests': 100,
            'avg_response_time': 25.0,
            'k3s_requests': 80,
            'knative_requests': 20
        }
        
        result = predictor.predict(current_stats)
        
        assert 'predicted_requests' in result
        assert 'confidence' in result
        assert result['predicted_requests'] >= 0
        assert 0 <= result['confidence'] <= 1
    
    def test_predict_before_training(self, predictor):
        """Test prediction fails before training when no model file exists."""
        current_stats = {'timestamp': int(time.time())}
        
        with pytest.raises(ValueError, match="not trained"):
            predictor.predict(current_stats)
    
    def test_save_and_load_model(self, predictor, training_data):
        """Test model persistence."""
        predictor.train(training_data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "model.joblib"
            predictor.model_path = model_path
            predictor.save_model()
            
            assert model_path.exists()
            
            new_predictor = TrafficPredictor(model_path=str(model_path))
            success = new_predictor.load_model()
            
            assert success is True
            assert new_predictor.is_trained is True
    
    def test_feature_extraction(self, predictor):
        """Test temporal feature extraction."""
        timestamp = 1704067200  # 2024-01-01 00:00:00 UTC
        
        features = predictor._extract_temporal_features(timestamp)
        
        assert len(features) == 4
        assert all(isinstance(f, (int, float)) for f in features)
    
    def test_calculate_trend(self, predictor):
        """Test trend calculation."""
        increasing = pd.Series([1, 2, 3, 4, 5])
        decreasing = pd.Series([5, 4, 3, 2, 1])
        flat = pd.Series([3, 3, 3, 3, 3])
        
        inc_trend = predictor._calculate_trend(increasing)
        dec_trend = predictor._calculate_trend(decreasing)
        flat_trend = predictor._calculate_trend(flat)
        
        assert inc_trend > 0
        assert dec_trend < 0
        assert abs(flat_trend) < 0.1
    
    def test_prepare_features(self, predictor, training_data):
        """Test feature preparation from DataFrame."""
        X, y = predictor.prepare_features(training_data)
        
        assert len(X) > 0
        assert len(y) > 0
        assert len(X) == len(y)
        assert X.shape[1] > 0


class TestTrafficPredictorEdgeCases:
    """Edge case tests for TrafficPredictor."""
    
    @pytest.fixture
    def predictor(self):
        """Create predictor with temp model path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "model.joblib"
            yield TrafficPredictor(model_path=str(model_path))
    
    def test_load_nonexistent_model(self, predictor):
        """Test loading model that doesn't exist."""
        success = predictor.load_model()
        assert success is False
        assert predictor.is_trained is False
    
    def test_retrain_if_needed_untrained(self, predictor):
        """Test retrain_if_needed when model is not trained."""
        data = self._generate_minimal_data()
        
        result = predictor.retrain_if_needed(data)
        
        assert result is True
        assert predictor.is_trained is True
    
    def _generate_minimal_data(self):
        """Generate minimal valid training data."""
        base_time = int(datetime.now().timestamp())
        data = []
        for i in range(50):
            data.append({
                'timestamp': base_time + i * 30,
                'total_requests': 100 + i,
                'avg_response_time': 25.0,
                'error_rate': 0.01,
                'k3s_requests': 80,
                'knative_requests': 20,
                'k3s_weight': 80,
                'knative_weight': 20
            })
        return pd.DataFrame(data)
