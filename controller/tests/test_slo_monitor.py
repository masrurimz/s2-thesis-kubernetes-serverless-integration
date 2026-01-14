"""Tests for SLO monitor."""
import pytest
import time

from monitoring_v2.slo_monitor import SLOMonitor, SLOConfig, SLOStatus, MockSLOMonitor


class TestSLOConfig:
    def test_default_values(self):
        config = SLOConfig()
        assert config.p99_threshold_ms == 200.0
        assert config.violation_window_sec == 30
        assert config.healthy_margin == 0.7


class TestMockSLOMonitor:
    @pytest.fixture
    def monitor(self):
        return MockSLOMonitor()
    
    def test_check_slo_healthy(self, monitor):
        monitor.set_mock_metrics(p99=50.0)
        status = monitor.check_slo()
        
        assert status.p99_latency_ms == 50.0
        assert status.is_violating is False
        assert status.recommendation == "OPTIMIZE_COST"  # Below healthy margin
    
    def test_check_slo_violating(self, monitor):
        monitor.set_mock_metrics(p99=250.0)
        status = monitor.check_slo()
        
        assert status.is_violating is True
    
    def test_check_slo_sustained_violation(self, monitor):
        monitor.set_mock_metrics(p99=250.0)
        
        # First check starts violation timer
        status1 = monitor.check_slo()
        assert status1.violation_duration_sec == 0
        
        # Simulate time passing
        monitor.violation_start_time = int(time.time()) - 35
        
        status2 = monitor.check_slo()
        assert status2.violation_duration_sec >= 30
        assert status2.recommendation == "SCALE_OUT"
    
    def test_statistics(self, monitor):
        monitor.check_slo()
        monitor.check_slo()
        
        stats = monitor.get_statistics()
        assert stats["total_checks"] == 2
