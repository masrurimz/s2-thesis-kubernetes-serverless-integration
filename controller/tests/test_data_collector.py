"""Tests for data collector."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import time

from prediction_engine.data_collector import DataCollector


class TestDataCollector:
    """Tests for DataCollector class."""

    @pytest.fixture
    def collector(self, temp_db):
        """Create collector with temp database."""
        return DataCollector(db_path=str(temp_db))

    def test_init_creates_database(self, temp_db):
        """Test collector creates database on init."""
        collector = DataCollector(db_path=str(temp_db))
        assert temp_db.exists()

    def test_store_and_retrieve_stats(self, collector):
        """Test storing and retrieving stats."""
        stats = {
            "timestamp": int(time.time()),
            "total_requests": 100,
            "avg_response_time": 25.5,
            "error_rate": 0.01,
            "k3s_requests": 80,
            "knative_requests": 20,
            "k3s_weight": 80,
            "knative_weight": 20,
        }

        result = collector.store_stats(stats)
        assert result is True

        df = collector.get_historical_data(hours=1)
        assert len(df) >= 1

    def test_store_multiple_stats(self, collector):
        """Test storing multiple stats records."""
        base_time = int(time.time())

        for i in range(10):
            stats = {
                "timestamp": base_time + i * 30,
                "total_requests": 100 + i,
                "avg_response_time": 25.0,
                "error_rate": 0.01,
                "k3s_requests": 80,
                "knative_requests": 20,
                "k3s_weight": 80,
                "knative_weight": 20,
            }
            collector.store_stats(stats)

        df = collector.get_historical_data(hours=1)
        assert len(df) == 10

    @patch("requests.get")
    def test_collect_current_stats_success(self, mock_get, collector, mock_haproxy_stats):
        """Test collecting current stats from HAProxy."""
        mock_response = Mock()
        mock_response.text = mock_haproxy_stats
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        stats = collector.collect_current_stats()

        assert stats is not None
        assert "timestamp" in stats
        assert "total_requests" in stats

    @patch("requests.get")
    def test_collect_current_stats_failure(self, mock_get, collector):
        """Test handling stats collection failure."""
        mock_get.side_effect = Exception("Connection failed")

        stats = collector.collect_current_stats()
        assert stats is None

    @patch("requests.get")
    def test_collect_current_stats_timeout(self, mock_get, collector):
        """Test handling stats collection timeout."""
        import requests

        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        stats = collector.collect_current_stats()
        assert stats is None

    def test_export_data_csv(self, collector):
        """Test exporting data to CSV."""
        for i in range(10):
            collector.store_stats(
                {
                    "timestamp": int(time.time()) + i,
                    "total_requests": 100 + i,
                    "avg_response_time": 25,
                    "error_rate": 0.01,
                    "k3s_requests": 80,
                    "knative_requests": 20,
                    "k3s_weight": 80,
                    "knative_weight": 20,
                }
            )

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            output_path = f.name

        result = collector.export_data(output_path, format="csv")
        assert result is True
        assert Path(output_path).exists()

        Path(output_path).unlink()

    def test_export_data_json(self, collector):
        """Test exporting data to JSON."""
        for i in range(5):
            collector.store_stats(
                {
                    "timestamp": int(time.time()) + i,
                    "total_requests": 100 + i,
                    "avg_response_time": 25,
                    "error_rate": 0.01,
                    "k3s_requests": 80,
                    "knative_requests": 20,
                    "k3s_weight": 80,
                    "knative_weight": 20,
                }
            )

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name

        result = collector.export_data(output_path, format="json")
        assert result is True
        assert Path(output_path).exists()

        Path(output_path).unlink()

    def test_get_historical_data_generates_synthetic(self, collector):
        """Test that synthetic data is generated when insufficient data exists."""
        df = collector.get_historical_data(hours=1, min_points=10)
        assert len(df) >= 10


class TestDataCollectorSyntheticData:
    """Tests for synthetic data generation."""

    @pytest.fixture
    def collector(self, temp_db):
        """Create collector with temp database."""
        return DataCollector(db_path=str(temp_db))

    def test_generate_synthetic_data(self, collector):
        """Test synthetic data generation."""
        df = collector._generate_synthetic_data(50)

        assert len(df) == 50
        assert "timestamp" in df.columns
        assert "total_requests" in df.columns
        assert "k3s_requests" in df.columns
        assert "knative_requests" in df.columns
        assert "avg_response_time" in df.columns
        assert "error_rate" in df.columns

    def test_synthetic_data_values(self, collector):
        """Test synthetic data has reasonable values."""
        df = collector._generate_synthetic_data(100)

        assert df["total_requests"].min() > 0
        assert df["k3s_requests"].min() >= 0
        assert df["knative_requests"].min() >= 0
        assert (df["avg_response_time"] > 0).all()
        assert (df["error_rate"] >= 0).all()


class TestDataCollectorExportFormats:
    """Tests for different export formats."""

    @pytest.fixture
    def collector(self, temp_db):
        """Create collector with sample data."""
        coll = DataCollector(db_path=str(temp_db))
        for i in range(10):
            coll.store_stats(
                {
                    "timestamp": int(time.time()) + i,
                    "total_requests": 100,
                    "avg_response_time": 25,
                    "error_rate": 0.01,
                    "k3s_requests": 80,
                    "knative_requests": 20,
                    "k3s_weight": 80,
                    "knative_weight": 20,
                }
            )
        return coll

    def test_export_invalid_format(self, collector):
        """Test exporting with invalid format."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            output_path = f.name

        result = collector.export_data(output_path, format="invalid")
        assert result is False

        Path(output_path).unlink(missing_ok=True)
