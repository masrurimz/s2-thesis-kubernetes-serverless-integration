"""Tests for decision logger."""

import pytest
from pathlib import Path
import tempfile
import time
import json

from routing.algorithm.decision_logger import DecisionLogger


class TestDecisionLogger:
    """Tests for DecisionLogger class."""

    @pytest.fixture
    def logger(self, temp_db):
        """Create logger with temp database."""
        return DecisionLogger(db_path=str(temp_db))

    def test_init_creates_database(self, temp_db):
        """Test logger creates database on init."""
        logger = DecisionLogger(db_path=str(temp_db))
        assert temp_db.exists()

    def test_log_decision(self, logger):
        """Test logging a routing decision."""
        decision = {
            "timestamp": int(time.time()),
            "decision_type": "intelligent",
            "current_stats": {"total_requests": 1000},
            "prediction": {"predicted_requests": 1200, "confidence": 0.85},
            "previous_weights": {"k3s": 80, "knative": 20},
            "target_weights": {"k3s": 70, "knative": 30},
            "weights_changed": True,
            "decision_latency": 0.045,
        }

        result = logger.log_decision(decision)

        assert result is True

    def test_log_multiple_decisions(self, logger):
        """Test logging multiple decisions."""
        for i in range(10):
            decision = {
                "timestamp": int(time.time()) + i,
                "decision_type": "intelligent" if i % 2 == 0 else "fallback",
                "current_stats": {"total_requests": 1000 + i * 10},
                "prediction": {"predicted_requests": 1200, "confidence": 0.85},
                "previous_weights": {"k3s": 80, "knative": 20},
                "target_weights": {"k3s": 80, "knative": 20},
                "weights_changed": i % 3 == 0,
                "decision_latency": 0.05,
            }
            logger.log_decision(decision)

        decisions = logger.get_recent_decisions(hours=1)
        assert len(decisions) == 10

    def test_log_decision_minimal_data(self, logger):
        """Test logging with minimal data."""
        decision = {"timestamp": int(time.time())}

        result = logger.log_decision(decision)

        assert result is True

    def test_get_recent_decisions(self, logger):
        """Test retrieving recent decisions."""
        for i in range(5):
            logger.log_decision(
                {
                    "timestamp": int(time.time()) + i,
                    "decision_type": "intelligent",
                    "current_stats": {},
                    "prediction": {},
                    "previous_weights": {},
                    "target_weights": {},
                    "weights_changed": False,
                    "decision_latency": 0.05,
                }
            )

        decisions = logger.get_recent_decisions(hours=1)

        assert len(decisions) == 5

    def test_get_recent_decisions_empty(self, logger):
        """Test retrieving decisions when none exist."""
        decisions = logger.get_recent_decisions(hours=1)
        assert decisions == []

    def test_get_decision_stats(self, logger):
        """Test getting decision statistics."""
        for i in range(10):
            logger.log_decision(
                {
                    "timestamp": int(time.time()) + i,
                    "decision_type": "intelligent" if i < 7 else "fallback",
                    "current_stats": {"total_requests": 1000},
                    "prediction": {"predicted_requests": 1200, "confidence": 0.8},
                    "previous_weights": {"k3s": 80, "knative": 20},
                    "target_weights": {"k3s": 75, "knative": 25},
                    "weights_changed": i % 2 == 0,
                    "decision_latency": 0.05,
                }
            )

        stats = logger.get_decision_stats(hours=1)

        assert stats["total_decisions"] == 10
        assert stats["intelligent_decisions"] == 7
        assert stats["fallback_decisions"] == 3
        assert stats["weight_changes"] == 5
        assert "avg_latency" in stats
        assert "avg_confidence" in stats


class TestDecisionLoggerExport:
    """Tests for decision export functionality."""

    @pytest.fixture
    def logger(self, temp_db):
        """Create logger with sample data."""
        log = DecisionLogger(db_path=str(temp_db))
        for i in range(5):
            log.log_decision(
                {
                    "timestamp": int(time.time()) + i,
                    "decision_type": "intelligent",
                    "current_stats": {"total_requests": 1000},
                    "prediction": {"predicted_requests": 1200, "confidence": 0.85},
                    "previous_weights": {"k3s": 80, "knative": 20},
                    "target_weights": {"k3s": 75, "knative": 25},
                    "weights_changed": True,
                    "decision_latency": 0.05,
                }
            )
        return log

    def test_export_decisions(self, logger):
        """Test exporting decisions to JSON."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name

        result = logger.export_decisions(hours=1, output_path=output_path)

        assert result is True
        assert Path(output_path).exists()

        with open(output_path) as f:
            data = json.load(f)

        assert "decisions" in data
        assert "statistics" in data
        assert len(data["decisions"]) == 5

        Path(output_path).unlink()

    def test_export_decisions_empty(self, temp_db):
        """Test exporting when no decisions exist."""
        logger = DecisionLogger(db_path=str(temp_db))

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name

        result = logger.export_decisions(hours=1, output_path=output_path)

        assert result is True

        with open(output_path) as f:
            data = json.load(f)

        assert data["decisions"] == []

        Path(output_path).unlink()


class TestDecisionLoggerCleanup:
    """Tests for decision cleanup functionality."""

    @pytest.fixture
    def logger(self, temp_db):
        """Create logger with old and new data."""
        log = DecisionLogger(db_path=str(temp_db))

        old_time = int(time.time()) - (10 * 24 * 3600)
        for i in range(5):
            log.log_decision(
                {
                    "timestamp": old_time + i,
                    "decision_type": "intelligent",
                    "current_stats": {},
                    "prediction": {},
                    "previous_weights": {},
                    "target_weights": {},
                    "weights_changed": False,
                    "decision_latency": 0.05,
                }
            )

        for i in range(3):
            log.log_decision(
                {
                    "timestamp": int(time.time()) + i,
                    "decision_type": "intelligent",
                    "current_stats": {},
                    "prediction": {},
                    "previous_weights": {},
                    "target_weights": {},
                    "weights_changed": False,
                    "decision_latency": 0.05,
                }
            )

        return log

    def test_cleanup_old_decisions(self, logger):
        """Test cleaning up old decisions."""
        deleted = logger.cleanup_old_decisions(keep_days=7)

        assert deleted == 5

        remaining = logger.get_recent_decisions(hours=24)
        assert len(remaining) == 3
