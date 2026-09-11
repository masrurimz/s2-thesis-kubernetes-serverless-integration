"""Tests for fallback handler."""

import pytest
import time

from routing.algorithm.fallback_handler import FallbackHandler


class TestFallbackHandler:
    """Tests for FallbackHandler class."""

    @pytest.fixture
    def handler(self):
        """Create fallback handler."""
        return FallbackHandler()

    def test_init(self, handler):
        """Test handler initialization."""
        assert handler.safe_k3s_weight == 80
        assert handler.safe_knative_weight == 20
        assert handler.emergency_k3s_weight == 100
        assert handler.emergency_knative_weight == 0
        assert handler.get_status()["in_fallback"] is False

    def test_init_custom_weights(self):
        """Test handler with custom weights."""
        handler = FallbackHandler(
            safe_k3s_weight=70, safe_knative_weight=30, emergency_k3s_weight=90, emergency_knative_weight=10
        )

        assert handler.safe_k3s_weight == 70
        assert handler.safe_knative_weight == 30

    def test_get_fallback_weights_normal(self, handler):
        """Test fallback weights under normal conditions."""
        normal_stats = {"total_requests": 1000, "avg_response_time": 25.0, "error_rate": 0.0}

        weights = handler.get_fallback_weights(normal_stats)

        assert weights["k3s"] == 80
        assert weights["knative"] == 20

    def test_get_fallback_weights_high_load(self, handler):
        """Test fallback weights under high load."""
        high_load_stats = {"current_rps": 800, "cpu_usage": 0.5, "error_rate": 0.0}

        weights = handler.get_fallback_weights(high_load_stats)

        assert weights["k3s"] == 80
        assert weights["knative"] == 20

    def test_get_fallback_weights_low_load(self, handler):
        """Test fallback weights under low load."""
        low_load_stats = {"current_rps": 5, "p99_latency_ms": 20.0, "error_rate": 0.0}

        weights = handler.get_fallback_weights(low_load_stats)

        assert weights["k3s"] == 80
        assert weights["knative"] == 20

    def test_get_fallback_weights_emergency_high_error(self, handler):
        """Test fallback weights with high error rate."""
        emergency_stats = {"current_rps": 100, "p99_latency_ms": 100.0, "error_rate": 0.15}

        weights = handler.get_fallback_weights(emergency_stats)

        assert weights["k3s"] == 100
        assert weights["knative"] == 0

    def test_get_fallback_weights_emergency_high_latency(self, handler):
        """Test fallback weights with very high response time."""
        emergency_stats = {"current_rps": 100, "p99_latency_ms": 1500.0, "error_rate": 0.0}

        weights = handler.get_fallback_weights(emergency_stats)

        assert weights["k3s"] == 100
        assert weights["knative"] == 0


class TestFallbackConditions:
    """Tests for condition detection."""

    @pytest.fixture
    def handler(self):
        """Create fallback handler."""
        return FallbackHandler()

    def test_is_emergency_condition_high_error(self, handler):
        """Test emergency detection with high error rate."""
        stats = {"error_rate": 0.15, "p99_latency_ms": 25.0}
        assert handler._is_emergency_condition(stats) is True

    def test_is_emergency_condition_high_latency(self, handler):
        """Test emergency detection with high latency."""
        stats = {"error_rate": 0.0, "p99_latency_ms": 1500.0}
        assert handler._is_emergency_condition(stats) is True

    def test_is_emergency_condition_normal(self, handler):
        """Test emergency detection under normal conditions."""
        stats = {"error_rate": 0.01, "avg_response_time": 25.0}
        assert handler._is_emergency_condition(stats) is False

    def test_is_high_load_condition_by_rps(self, handler):
        """Test high load detection by request rate."""
        stats = {"current_rps": 800, "cpu_usage": 0.3}
        assert handler._is_high_load_condition(stats) is True

    def test_is_high_load_condition_by_cpu(self, handler):
        """Test high load detection by CPU utilization."""
        stats = {"current_rps": 100, "cpu_usage": 0.9}
        assert handler._is_high_load_condition(stats) is True

    def test_is_high_load_condition_normal(self, handler):
        """Test high load detection under normal conditions."""
        stats = {"total_requests": 1000, "avg_response_time": 25.0}
        assert handler._is_high_load_condition(stats) is False

    def test_is_low_load_condition(self, handler):
        """Test low load detection."""
        stats = {"total_requests": 50}
        assert handler._is_low_load_condition(stats) is True

    def test_is_low_load_condition_normal(self, handler):
        """Test low load detection under normal conditions."""
        stats = {"current_rps": 50}
        assert handler._is_low_load_condition(stats) is False


class TestFallbackRecovery:
    """Tests for fallback recovery behavior."""

    @pytest.fixture
    def handler(self):
        """Create fallback handler."""
        return FallbackHandler()

    def test_should_enable_intelligent_routing_normal(self, handler):
        """Test re-enabling intelligent routing under normal conditions."""
        assert handler.should_enable_intelligent_routing() is True

    def test_should_enable_intelligent_routing_emergency(self, handler):
        """Test re-enabling blocked while in fallback."""
        handler._in_fallback = True
        handler._fallback_start_time = time.time()
        assert handler.should_enable_intelligent_routing() is False

    def test_should_enable_intelligent_routing_recent_fallback(self, handler):
        """Test re-enabling blocked within fallback timeout."""
        handler._in_fallback = True
        handler._fallback_start_time = time.time() - 60
        assert handler.should_enable_intelligent_routing() is False

    def test_should_enable_intelligent_routing_old_fallback(self, handler):
        """Test re-enabling allowed after fallback timeout."""
        handler.fallback_mode = True
        handler.last_fallback_time = int(time.time()) - 400
        assert handler.should_enable_intelligent_routing() is True

    def test_reset_fallback_state(self, handler):
        """Test resetting fallback state."""
        handler._in_fallback = True
        handler._fallback_start_time = 123.0
        handler._recovery_count = 2

        handler.reset_fallback_state()

        assert handler._in_fallback is False
        assert handler._fallback_start_time is None
        assert handler._recovery_count == 0

    def test_get_recovery_weights_not_in_fallback(self, handler):
        """Test recovery weights when not in fallback mode."""
        target = {"k3s": 70, "knative": 30}

        result = handler.get_recovery_weights(target)

        assert result == target

    def test_get_recovery_weights_in_fallback(self, handler):
        """Test recovery weights during fallback mode."""
        handler._in_fallback = True
        target = {"k3s": 60, "knative": 40}

        result = handler.get_recovery_weights(target)

        assert result["k3s"] != target["k3s"]
        assert result["k3s"] + result["knative"] == 100

    def test_get_status(self, handler):
        """Test getting handler status."""
        status = handler.get_status()

        assert "in_fallback" in status
        assert "fallback_start_time" in status
        assert "recovery_count" in status
        assert "timeout_sec" in status
