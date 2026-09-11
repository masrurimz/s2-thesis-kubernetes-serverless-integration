"""Pytest fixtures for controller tests."""

import pytest
import tempfile
from pathlib import Path

import pandas as pd
from datetime import datetime, timedelta


@pytest.fixture
def temp_db():
    """Create temporary SQLite database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    db_path.unlink(missing_ok=True)


@pytest.fixture
def sample_traffic_data():
    """Sample traffic data for testing."""

    base_time = datetime.now()
    data = []
    for i in range(100):
        data.append(
            {
                "timestamp": int((base_time + timedelta(seconds=i * 30)).timestamp()),
                "total_requests": 100 + i % 20,
                "avg_response_time": 25.0 + (i % 10),
                "error_rate": 0.01 * (i % 5),
                "k3s_requests": 80 + i % 15,
                "knative_requests": 20 + i % 5,
                "k3s_weight": 80,
                "knative_weight": 20,
            }
        )
    return pd.DataFrame(data)


@pytest.fixture
def mock_prediction_response():
    """Mock prediction API response."""
    return {"predicted_requests": 1200, "confidence": 0.85, "model_rmse": 50.0, "model_r2": 0.75}
