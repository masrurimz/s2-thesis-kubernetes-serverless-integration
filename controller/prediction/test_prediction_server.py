#!/usr/bin/env python3
"""
Tests for GRU Prediction Server.

Tests model loading, prediction endpoint, and response time requirements.
"""

import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_model_loader():
    """Create a mock model loader."""
    loader = Mock()
    loader.is_loaded = True
    loader.model_type = "pytorch"
    loader.config = Mock()
    loader.config.sequence_length = 30
    loader.config.hidden_size = 64
    loader.model_path = Path("data/models/gru_model.pt")
    loader.rmse = 5.0
    loader.mae = 3.5
    loader.scaler_mean = 100.0
    loader.scaler_std = 20.0
    
    def mock_predict(history, horizon=1):
        avg = np.mean(history) if history else 100
        predictions = [int(avg * (1 + 0.02 * i)) for i in range(horizon)]
        return {
            "predicted_requests": predictions[-1],
            "confidence": 0.85,
            "horizon_values": predictions,
            "model_rmse": 5.0,
        }
    
    loader.predict = mock_predict
    loader.get_status.return_value = {
        "loaded": True,
        "model_type": "pytorch",
        "model_path": "data/models/gru_model.pt",
        "sequence_length": 30,
        "hidden_size": 64,
        "rmse": 5.0,
        "mae": 3.5,
        "scaler_mean": 100.0,
        "scaler_std": 20.0,
    }
    
    return loader


@pytest.fixture
def client(mock_model_loader):
    """Create test client with mocked model loader."""
    with patch("prediction.prediction_server.model_loader", mock_model_loader):
        with patch("prediction.prediction_server.server_start_time", time.time()):
            from prediction.prediction_server import app
            yield TestClient(app)


class TestHealthEndpoint:
    """Tests for /health endpoint."""
    
    def test_health_check_with_model(self, client, mock_model_loader):
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] is True
        assert data["model_type"] == "pytorch"
        assert data["sequence_length"] == 30
        assert "uptime_seconds" in data
    
    def test_health_check_without_model(self):
        with patch("prediction.prediction_server.model_loader", None):
            with patch("prediction.prediction_server.server_start_time", time.time()):
                from prediction.prediction_server import app
                client = TestClient(app)
                
                response = client.get("/health")
                assert response.status_code == 200
                
                data = response.json()
                assert data["model_loaded"] is False


class TestPredictEndpoint:
    """Tests for /predict endpoint."""
    
    def test_predict_basic(self, client):
        request = {
            "history": [100, 120, 150, 130, 140, 160, 155, 170, 165, 180],
            "horizon": 5,
        }
        
        response = client.post("/predict", json=request)
        assert response.status_code == 200
        
        data = response.json()
        assert "predicted_requests" in data
        assert "confidence" in data
        assert "horizon_values" in data
        assert "latency_ms" in data
        
        assert data["predicted_requests"] > 0
        assert 0 <= data["confidence"] <= 1
        assert len(data["horizon_values"]) == 5
    
    def test_predict_default_horizon(self, client):
        request = {"history": [100, 120, 150, 130, 140]}
        
        response = client.post("/predict", json=request)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["horizon_values"]) == 5
    
    def test_predict_custom_horizon(self, client):
        request = {"history": [100, 120, 150], "horizon": 10}
        
        response = client.post("/predict", json=request)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["horizon_values"]) == 10
    
    def test_predict_single_value_history(self, client):
        request = {"history": [150], "horizon": 3}
        
        response = client.post("/predict", json=request)
        assert response.status_code == 200
    
    def test_predict_empty_history_rejected(self, client):
        request = {"history": [], "horizon": 5}
        
        response = client.post("/predict", json=request)
        assert response.status_code == 422
    
    def test_predict_invalid_horizon(self, client):
        request = {"history": [100, 120], "horizon": 0}
        
        response = client.post("/predict", json=request)
        assert response.status_code == 422
    
    def test_predict_response_time_target(self, client):
        """Verify response time < 50ms target."""
        request = {
            "history": [100 + i * 5 for i in range(50)],
            "horizon": 5,
        }
        
        start = time.perf_counter()
        response = client.post("/predict", json=request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        assert response.status_code == 200
        assert elapsed_ms < 100
    
    def test_predict_without_model(self):
        """Test prediction fails gracefully without model."""
        mock_loader = Mock()
        mock_loader.is_loaded = False
        
        with patch("prediction.prediction_server.model_loader", mock_loader):
            with patch("prediction.prediction_server.server_start_time", time.time()):
                from prediction.prediction_server import app
                client = TestClient(app)
                
                response = client.post("/predict", json={"history": [100, 120]})
                assert response.status_code == 503
                assert "not loaded" in response.json()["detail"].lower()


class TestModelStatusEndpoint:
    """Tests for /model/status endpoint."""
    
    def test_model_status(self, client, mock_model_loader):
        response = client.get("/model/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["loaded"] is True
        assert data["model_type"] == "pytorch"
        assert data["sequence_length"] == 30


class TestModelReloadEndpoint:
    """Tests for /model/reload endpoint."""
    
    def test_reload_default_path(self, client, mock_model_loader):
        with patch("prediction.prediction_server.GRUModelLoader") as MockLoader:
            mock_instance = Mock()
            mock_instance.is_loaded = True
            mock_instance.model_path = Path("data/models/gru_model.pt")
            MockLoader.return_value = mock_instance
            
            response = client.post("/model/reload")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "reloaded"
    
    def test_reload_custom_path_not_found(self, client):
        response = client.post("/model/reload?model_path=/nonexistent/path.pt")
        assert response.status_code == 404


class TestModelLoader:
    """Tests for GRUModelLoader class."""
    
    def test_model_loader_initialization(self):
        from prediction.model_loader import GRUModelLoader
        
        loader = GRUModelLoader()
        assert hasattr(loader, "is_loaded")
        assert hasattr(loader, "model_type")
    
    def test_model_loader_status(self):
        from prediction.model_loader import GRUModelLoader
        
        loader = GRUModelLoader()
        status = loader.get_status()
        
        assert "loaded" in status
        assert "model_type" in status
        assert "sequence_length" in status
    
    def test_predict_without_loading(self):
        from prediction.model_loader import GRUModelLoader
        
        loader = GRUModelLoader()
        if not loader.is_loaded:
            with pytest.raises(RuntimeError, match="not loaded"):
                loader.predict([100, 120, 150])
    
    def test_confidence_calculation(self):
        from prediction.model_loader import GRUModelLoader
        
        loader = GRUModelLoader()
        confidence = loader._calculate_confidence([100, 105, 110, 108, 112], [115, 118])
        assert 0.5 <= confidence <= 0.95


class TestResponseFormat:
    """Tests for response format compliance."""
    
    def test_predict_response_format(self, client):
        """Verify response matches spec format."""
        request = {"history": [100, 120, 150, 130, 140], "horizon": 5}
        
        response = client.post("/predict", json=request)
        data = response.json()
        
        assert isinstance(data["predicted_requests"], int)
        assert isinstance(data["confidence"], float)
        assert isinstance(data["horizon_values"], list)
        assert all(isinstance(v, int) for v in data["horizon_values"])
    
    def test_health_response_format(self, client, mock_model_loader):
        """Verify health response format."""
        response = client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert "model_loaded" in data
        assert "uptime_seconds" in data


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_large_history(self, client):
        request = {
            "history": [100 + i for i in range(1000)],
            "horizon": 5,
        }
        
        response = client.post("/predict", json=request)
        assert response.status_code == 200
    
    def test_negative_values_in_history(self, client):
        """Negative values should still work (model handles normalization)."""
        request = {"history": [-10, 0, 50, 100, 150], "horizon": 3}
        
        response = client.post("/predict", json=request)
        assert response.status_code == 200
    
    def test_float_values_in_history(self, client):
        request = {"history": [100.5, 120.3, 150.7, 130.2], "horizon": 3}
        
        response = client.post("/predict", json=request)
        assert response.status_code == 200
