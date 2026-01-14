"""Tests for intelligent routing controller."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import time

from intelligent_router.routing_controller import IntelligentRoutingController


class TestIntelligentRoutingController:
    """Tests for routing controller."""
    
    @pytest.fixture
    def controller(self):
        """Create controller with mocked dependencies."""
        with patch('intelligent_router.routing_controller.HAProxyWeightAdjuster'):
            with patch('intelligent_router.routing_controller.DecisionLogger'):
                with patch('intelligent_router.routing_controller.FallbackHandler'):
                    return IntelligentRoutingController(
                        enable_intelligent_routing=True
                    )
    
    def test_init(self, controller):
        """Test controller initialization."""
        assert controller.is_running is False
        assert controller.current_weights == {"k3s": 80, "knative": 20}
    
    def test_init_intelligent_routing_enabled(self, controller):
        """Test controller with intelligent routing enabled."""
        assert controller.enable_intelligent_routing is True
    
    def test_init_intelligent_routing_disabled(self):
        """Test controller with intelligent routing disabled."""
        with patch('intelligent_router.routing_controller.HAProxyWeightAdjuster'):
            with patch('intelligent_router.routing_controller.DecisionLogger'):
                with patch('intelligent_router.routing_controller.FallbackHandler'):
                    controller = IntelligentRoutingController(
                        enable_intelligent_routing=False
                    )
        assert controller.enable_intelligent_routing is False
    
    def test_calculate_intelligent_weights_high_confidence_increase(self, controller):
        """Test weight calculation with high confidence load increase."""
        current_stats = {'total_requests': 100}
        prediction = {
            'predicted_requests': 150,
            'confidence': 0.8
        }
        
        weights = controller._calculate_intelligent_weights(current_stats, prediction)
        
        assert weights['knative'] > 20
        assert weights['k3s'] + weights['knative'] == 100
    
    def test_calculate_intelligent_weights_high_confidence_decrease(self, controller):
        """Test weight calculation with high confidence load decrease."""
        current_stats = {'total_requests': 100}
        prediction = {
            'predicted_requests': 50,
            'confidence': 0.8
        }
        
        weights = controller._calculate_intelligent_weights(current_stats, prediction)
        
        assert weights['k3s'] >= 80
        assert weights['k3s'] + weights['knative'] == 100
    
    def test_calculate_intelligent_weights_low_confidence(self, controller):
        """Test weight calculation with low confidence."""
        current_stats = {'total_requests': 100}
        prediction = {
            'predicted_requests': 200,
            'confidence': 0.3
        }
        
        weights = controller._calculate_intelligent_weights(current_stats, prediction)
        
        assert 75 <= weights['k3s'] <= 85
    
    def test_calculate_intelligent_weights_medium_confidence_high_increase(self, controller):
        """Test weight calculation with medium confidence and very high load increase."""
        current_stats = {'total_requests': 100}
        prediction = {
            'predicted_requests': 200,
            'confidence': 0.6
        }
        
        weights = controller._calculate_intelligent_weights(current_stats, prediction)
        
        assert weights['knative'] >= 20
        assert weights['k3s'] + weights['knative'] == 100
    
    def test_calculate_intelligent_weights_with_recommendation(self, controller):
        """Test weight calculation with prediction recommendation."""
        current_stats = {'total_requests': 100}
        prediction = {
            'predicted_requests': 150,
            'confidence': 0.9,
            'recommendation': {
                'k3s_weight': 60,
                'knative_weight': 40
            }
        }
        
        weights = controller._calculate_intelligent_weights(current_stats, prediction)
        
        assert weights['k3s'] + weights['knative'] == 100
    
    def test_calculate_intelligent_weights_zero_requests(self, controller):
        """Test weight calculation with zero current requests."""
        current_stats = {'total_requests': 0}
        prediction = {
            'predicted_requests': 100,
            'confidence': 0.8
        }
        
        weights = controller._calculate_intelligent_weights(current_stats, prediction)
        
        assert weights['k3s'] + weights['knative'] == 100
    
    def test_get_status(self, controller):
        """Test getting controller status."""
        status = controller.get_status()
        
        assert 'is_running' in status
        assert 'current_weights' in status
        assert 'intelligent_routing_enabled' in status
        assert 'consecutive_failures' in status
        assert 'last_decision_time' in status


class TestRoutingControllerAsync:
    """Async tests for routing controller."""
    
    @pytest.fixture
    def controller(self):
        """Create controller with mocked dependencies."""
        with patch('intelligent_router.routing_controller.HAProxyWeightAdjuster') as mock_wa:
            with patch('intelligent_router.routing_controller.DecisionLogger'):
                with patch('intelligent_router.routing_controller.FallbackHandler') as mock_fh:
                    mock_wa_instance = Mock()
                    mock_wa_instance.test_connection.return_value = True
                    mock_wa_instance.set_weights_with_retry.return_value = True
                    mock_wa.return_value = mock_wa_instance
                    
                    mock_fh_instance = Mock()
                    mock_fh_instance.get_fallback_weights.return_value = {"k3s": 80, "knative": 20}
                    mock_fh.return_value = mock_fh_instance
                    
                    return IntelligentRoutingController()
    
    @pytest.mark.asyncio
    async def test_get_current_stats_success(self, controller):
        """Test getting current stats from HAProxy."""
        mock_stats = """# pxname,svname,stot
hybrid-backend,BACKEND,1250"""
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = mock_stats
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            stats = await controller._get_current_stats()
            
            assert stats is not None
            assert 'timestamp' in stats
    
    @pytest.mark.asyncio
    async def test_get_current_stats_failure(self, controller):
        """Test handling stats collection failure."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            
            stats = await controller._get_current_stats()
            
            assert stats is None
    
    @pytest.mark.asyncio
    async def test_get_prediction_success(self, controller, mock_prediction_response):
        """Test getting prediction from API."""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = mock_prediction_response
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response
            
            prediction = await controller._get_prediction()
            
            assert prediction is not None
            assert 'predicted_requests' in prediction
    
    @pytest.mark.asyncio
    async def test_get_prediction_failure(self, controller):
        """Test handling prediction API failure."""
        import requests
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException("API unavailable")
            
            prediction = await controller._get_prediction()
            
            assert prediction is None
    
    @pytest.mark.asyncio
    async def test_apply_weight_changes_small_change(self, controller):
        """Test that small weight changes are skipped."""
        controller.current_weights = {"k3s": 80, "knative": 20}
        target_weights = {"k3s": 82, "knative": 18}
        
        result = await controller._apply_weight_changes(target_weights)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_apply_weight_changes_significant_change(self, controller):
        """Test that significant weight changes are applied."""
        controller.current_weights = {"k3s": 80, "knative": 20}
        target_weights = {"k3s": 70, "knative": 30}
        
        result = await controller._apply_weight_changes(target_weights)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_stop_controller(self, controller):
        """Test stopping the controller."""
        controller.is_running = True
        
        await controller.stop()
        
        assert controller.is_running is False


class TestControllerFallbackMode:
    """Tests for fallback mode behavior."""
    
    @pytest.fixture
    def controller(self):
        """Create controller with mocked dependencies."""
        with patch('intelligent_router.routing_controller.HAProxyWeightAdjuster') as mock_wa:
            with patch('intelligent_router.routing_controller.DecisionLogger'):
                with patch('intelligent_router.routing_controller.FallbackHandler') as mock_fh:
                    mock_wa_instance = Mock()
                    mock_wa_instance.set_weights_with_retry.return_value = True
                    mock_wa.return_value = mock_wa_instance
                    
                    mock_fh_instance = Mock()
                    mock_fh_instance.get_fallback_weights.return_value = {"k3s": 80, "knative": 20}
                    mock_fh.return_value = mock_fh_instance
                    
                    return IntelligentRoutingController()
    
    @pytest.mark.asyncio
    async def test_enter_fallback_mode(self, controller):
        """Test entering fallback mode."""
        controller.is_running = True
        controller.enable_intelligent_routing = True
        
        with patch.object(controller, '_apply_weight_changes', new_callable=AsyncMock) as mock_apply:
            mock_apply.return_value = True
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                await controller._enter_fallback_mode()
        
        assert controller.consecutive_failures == 0
