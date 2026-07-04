"""Tests for SLO monitor."""

import pytest
import time

from unittest.mock import Mock, patch

from routing.monitoring.slo_monitor import SLOMonitor, SLOConfig, MockSLOMonitor


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


class TestSLOMonitorSources:
    @patch("routing.monitoring.slo_monitor.requests.get")
    def test_prometheus_primary_over_haproxy(self, mock_get):
        config = SLOConfig(prometheus_url="http://prom", haproxy_stats_url="http://hap")
        monitor = SLOMonitor(config)

        prom_resp = Mock()
        prom_resp.raise_for_status.return_value = None
        prom_resp.json.return_value = {
            "status": "success",
            "data": {"result": [{"value": [0, "150"]}]},
        }

        mock_get.return_value = prom_resp

        p99 = monitor._get_p99_latency()

        assert p99 == 150.0
        assert mock_get.call_args_list[0].kwargs["params"]["query"].startswith("histogram_quantile")

    @patch("routing.monitoring.slo_monitor.requests.get")
    def test_haproxy_fallback_interval_recovery(self, mock_get):
        config = SLOConfig(use_haproxy_fallback=True)
        monitor = SLOMonitor(config)

        prom_fail = Mock()
        prom_fail.raise_for_status.side_effect = Exception("prom down")

        hap_priming = Mock()
        hap_priming.raise_for_status.return_value = None

        def make_haproxy_csv(stot: int, rtime: int, rtime_max: int) -> str:
            cols = [""] * 93
            cols[0] = "servers"
            cols[1] = "BACKEND"
            cols[7] = str(stot)
            cols[60] = str(rtime)
            cols[92] = str(rtime_max)
            return ",".join(cols) + "\n"

        hap_priming.text = make_haproxy_csv(stot=100, rtime=300, rtime_max=2000)

        hap_second = Mock()
        hap_second.raise_for_status.return_value = None
        hap_second.text = make_haproxy_csv(stot=200, rtime=400, rtime_max=900)

        mock_get.side_effect = [prom_fail, hap_priming, prom_fail, hap_second]

        first = monitor._get_p99_latency()
        second = monitor._get_p99_latency()

        assert first == 0.0
        assert second > 0.0

    def test_reset_clears_haproxy_fallback_state(self):
        monitor = SLOMonitor(SLOConfig())
        monitor._last_haproxy_total_requests = 10
        monitor._last_haproxy_total_rtime_ms = 1000.0

        monitor.reset()

        assert monitor._last_haproxy_total_requests is None
        assert monitor._last_haproxy_total_rtime_ms is None
