"""Tests for fallback handler."""
import pytest
from unittest.mock import Mock, patch
import time

from intelligent_router.fallback_handler import FallbackHandler


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
        assert handler.emergency_k3s_weight == 95
        assert handler.emergency_knative_weight == 5
        assert handler.fallback_mode is False
        assert handler.emergency_mode is False
    
    def test_init_custom_weights(self):
        """Test handler with custom weights."""
        handler = FallbackHandler(
            safe_k3s_weight=70,
            safe_knative_weight=30,
            emergency_k3s_weight=90,
            emergency_knative_weight=10
        )
        
        assert handler.safe_k3s_weight == 70
        assert handler.safe_knative_weight == 30
    
    def test_get_fallback_weights_normal(self, handler):
        """Test fallback weights under normal conditions."""
        normal_stats = {
            'total_requests': 1000,
            'avg_response_time': 25.0,
            'error_rate': 0.0
        }
        
        weights = handler.get_fallback_weights(normal_stats)
        
        assert weights['k3s'] == 80
        assert weights['knative'] == 20
    
    def test_get_fallback_weights_high_load(self, handler):
        """Test fallback weights under high load."""
        high_load_stats = {
            'total_requests': 3000,
            'avg_response_time': 250.0,
            'error_rate': 0.0
        }
        
        weights = handler.get_fallback_weights(high_load_stats)
        
        assert weights['k3s'] == 60
        assert weights['knative'] == 40
        assert handler.fallback_mode is True
    
    def test_get_fallback_weights_low_load(self, handler):
        """Test fallback weights under low load."""
        low_load_stats = {
            'total_requests': 50,
            'avg_response_time': 20.0,
            'error_rate': 0.0
        }
        
        weights = handler.get_fallback_weights(low_load_stats)
        
        assert weights['k3s'] == 90
        assert weights['knative'] == 10
        assert handler.fallback_mode is True
    
    def test_get_fallback_weights_emergency_high_error(self, handler):
        """Test fallback weights with high error rate."""
        emergency_stats = {
            'total_requests': 1000,
            'avg_response_time': 100.0,
            'error_rate': 0.1
        }
        
        weights = handler.get_fallback_weights(emergency_stats)
        
        assert weights['k3s'] == 95
        assert weights['knative'] == 5
        assert handler.emergency_mode is True
    
    def test_get_fallback_weights_emergency_high_latency(self, handler):
        """Test fallback weights with very high response time."""
        emergency_stats = {
            'total_requests': 1000,
            'avg_response_time': 1500.0,
            'error_rate': 0.0
        }
        
        weights = handler.get_fallback_weights(emergency_stats)
        
        assert weights['k3s'] == 95
        assert weights['knative'] == 5
        assert handler.emergency_mode is True


class TestFallbackConditions:
    """Tests for condition detection."""
    
    @pytest.fixture
    def handler(self):
        """Create fallback handler."""
        return FallbackHandler()
    
    def test_is_emergency_condition_high_error(self, handler):
        """Test emergency detection with high error rate."""
        stats = {'error_rate': 0.06, 'avg_response_time': 25.0}
        assert handler._is_emergency_condition(stats) is True
    
    def test_is_emergency_condition_high_latency(self, handler):
        """Test emergency detection with high latency."""
        stats = {'error_rate': 0.0, 'avg_response_time': 1500.0}
        assert handler._is_emergency_condition(stats) is True
    
    def test_is_emergency_condition_normal(self, handler):
        """Test emergency detection under normal conditions."""
        stats = {'error_rate': 0.01, 'avg_response_time': 25.0}
        assert handler._is_emergency_condition(stats) is False
    
    def test_is_high_load_condition_by_volume(self, handler):
        """Test high load detection by request volume."""
        stats = {'total_requests': 2500, 'avg_response_time': 25.0}
        assert handler._is_high_load_condition(stats) is True
    
    def test_is_high_load_condition_by_latency(self, handler):
        """Test high load detection by elevated latency."""
        stats = {'total_requests': 1000, 'avg_response_time': 300.0}
        assert handler._is_high_load_condition(stats) is True
    
    def test_is_high_load_condition_normal(self, handler):
        """Test high load detection under normal conditions."""
        stats = {'total_requests': 1000, 'avg_response_time': 25.0}
        assert handler._is_high_load_condition(stats) is False
    
    def test_is_low_load_condition(self, handler):
        """Test low load detection."""
        stats = {'total_requests': 50}
        assert handler._is_low_load_condition(stats) is True
    
    def test_is_low_load_condition_normal(self, handler):
        """Test low load detection under normal conditions."""
        stats = {'total_requests': 500}
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
        """Test re-enabling blocked during emergency mode."""
        handler.emergency_mode = True
        assert handler.should_enable_intelligent_routing() is False
    
    def test_should_enable_intelligent_routing_recent_fallback(self, handler):
        """Test re-enabling blocked after recent fallback."""
        handler.fallback_mode = True
        handler.last_fallback_time = int(time.time())
        assert handler.should_enable_intelligent_routing() is False
    
    def test_should_enable_intelligent_routing_old_fallback(self, handler):
        """Test re-enabling allowed after fallback timeout."""
        handler.fallback_mode = True
        handler.last_fallback_time = int(time.time()) - 400
        assert handler.should_enable_intelligent_routing() is True
    
    def test_reset_fallback_state(self, handler):
        """Test resetting fallback state."""
        handler.fallback_mode = True
        handler.emergency_mode = True
        handler.fallback_reason = "test"
        
        handler.reset_fallback_state()
        
        assert handler.fallback_mode is False
        assert handler.emergency_mode is False
        assert handler.fallback_reason is None
    
    def test_get_recovery_weights_not_in_fallback(self, handler):
        """Test recovery weights when not in fallback mode."""
        target = {'k3s': 70, 'knative': 30}
        
        result = handler.get_recovery_weights(target)
        
        assert result == target
    
    def test_get_recovery_weights_in_fallback(self, handler):
        """Test recovery weights during fallback mode."""
        handler.fallback_mode = True
        target = {'k3s': 60, 'knative': 40}
        
        result = handler.get_recovery_weights(target)
        
        assert result['k3s'] != target['k3s']
        assert result['k3s'] + result['knative'] == 100
    
    def test_get_status(self, handler):
        """Test getting handler status."""
        status = handler.get_status()
        
        assert 'fallback_mode' in status
        assert 'emergency_mode' in status
        assert 'safe_weights' in status
        assert 'emergency_weights' in status
