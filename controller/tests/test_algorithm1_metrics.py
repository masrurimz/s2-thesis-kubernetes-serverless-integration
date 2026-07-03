"""Tests for Algorithm 1 controller Prometheus metrics."""

import pytest
import time

from intelligent_router.algorithm1_controller import Algorithm1Controller
from intelligent_router.metrics import (
    slo_violation_total,
    routing_decision_total,
    reaction_time_ms,
    get_counter_value,
    get_histogram_sum,
)
from monitoring_v2.slo_monitor import MockSLOMonitor


class TestAlgorithm1Metrics:
    @pytest.fixture
    def monitor(self):
        return MockSLOMonitor()

    @pytest.fixture
    def controller(self, monitor):
        return Algorithm1Controller(slo_monitor=monitor)

    def test_scale_out_increments_slo_violation(self, controller, monitor):
        initial = get_counter_value(slo_violation_total, {"slo_name": "p99_latency"})

        monitor.set_mock_metrics(p99=250.0)
        monitor.violation_start_time = int(time.time()) - 35

        controller.make_decision()

        after = get_counter_value(slo_violation_total, {"slo_name": "p99_latency"})
        assert after == initial + 1

    def test_scale_out_increments_routing_decision(self, controller, monitor):
        initial = get_counter_value(routing_decision_total, {"decision_type": "SCALE_OUT"})

        monitor.set_mock_metrics(p99=250.0)
        monitor.violation_start_time = int(time.time()) - 35

        controller.make_decision()

        after = get_counter_value(routing_decision_total, {"decision_type": "SCALE_OUT"})
        assert after == initial + 1

    def test_optimize_cost_increments_routing_decision(self, controller, monitor):
        initial = get_counter_value(routing_decision_total, {"decision_type": "OPTIMIZE_COST"})

        monitor.set_mock_metrics(p99=100.0)

        controller.make_decision()

        after = get_counter_value(routing_decision_total, {"decision_type": "OPTIMIZE_COST"})
        assert after == initial + 1

    def test_predictive_increments_routing_decision(self, controller, monitor):
        initial = get_counter_value(routing_decision_total, {"decision_type": "PREDICTIVE"})

        monitor.set_mock_metrics(p99=150.0)

        prediction = {"predicted_requests": 200, "confidence": 0.9}

        controller.make_decision(prediction=prediction, current_load=100)

        after = get_counter_value(routing_decision_total, {"decision_type": "PREDICTIVE"})
        assert after == initial + 1

    def test_maintain_increments_routing_decision(self, controller, monitor):
        initial = get_counter_value(routing_decision_total, {"decision_type": "MAINTAIN"})

        monitor.set_mock_metrics(p99=150.0)

        controller.make_decision()

        after = get_counter_value(routing_decision_total, {"decision_type": "MAINTAIN"})
        assert after == initial + 1

    def test_reaction_time_recorded_on_scale_out(self, controller, monitor):
        initial_sum = get_histogram_sum(reaction_time_ms)

        monitor.set_mock_metrics(p99=250.0)

        controller.make_decision()

        monitor.violation_start_time = int(time.time()) - 35
        controller.make_decision()

        after_sum = get_histogram_sum(reaction_time_ms)
        assert after_sum > initial_sum

    def test_multiple_decisions_accumulate_metrics(self, controller, monitor):
        initial_optimize = get_counter_value(routing_decision_total, {"decision_type": "OPTIMIZE_COST"})
        initial_maintain = get_counter_value(routing_decision_total, {"decision_type": "MAINTAIN"})
        initial_scale_out = get_counter_value(routing_decision_total, {"decision_type": "SCALE_OUT"})

        # First: optimize cost
        monitor.set_mock_metrics(p99=100.0)
        controller.make_decision()

        # Second: maintain (due to cooldown)
        controller.make_decision()

        # Reset cooldown
        controller.last_adjustment_time = None

        # Third: scale out
        monitor.set_mock_metrics(p99=250.0)
        monitor.violation_start_time = int(time.time()) - 35
        controller.make_decision()

        assert get_counter_value(routing_decision_total, {"decision_type": "OPTIMIZE_COST"}) == initial_optimize + 1
        assert get_counter_value(routing_decision_total, {"decision_type": "MAINTAIN"}) == initial_maintain + 1
        assert get_counter_value(routing_decision_total, {"decision_type": "SCALE_OUT"}) == initial_scale_out + 1


class TestMetricsServer:
    def test_metrics_server_starts_and_serves(self):
        from intelligent_router.metrics_server import MetricsServer
        import urllib.request

        server = MetricsServer(port=9199)
        server.start()

        try:
            time.sleep(0.1)  # Let server start

            response = urllib.request.urlopen("http://localhost:9199/metrics", timeout=2)
            content = response.read().decode()

            assert response.status == 200
            assert "python_" in content or "process_" in content
        finally:
            server.stop()

    def test_health_endpoint(self):
        from intelligent_router.metrics_server import MetricsServer
        import urllib.request

        server = MetricsServer(port=9198)
        server.start()

        try:
            time.sleep(0.1)

            response = urllib.request.urlopen("http://localhost:9198/health", timeout=2)
            content = response.read().decode()

            assert response.status == 200
            assert content == "OK"
        finally:
            server.stop()

    def test_404_for_unknown_path(self):
        from intelligent_router.metrics_server import MetricsServer
        import urllib.request
        import urllib.error

        server = MetricsServer(port=9197)
        server.start()

        try:
            time.sleep(0.1)

            with pytest.raises(urllib.error.HTTPError) as exc_info:
                urllib.request.urlopen("http://localhost:9197/unknown", timeout=2)

            assert exc_info.value.code == 404
        finally:
            server.stop()
