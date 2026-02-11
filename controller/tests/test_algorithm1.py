"""Tests for Algorithm 1 controller."""
import pytest
import time
from unittest.mock import Mock

from intelligent_router.algorithm1_controller import (
    Algorithm1Controller, Algorithm1Config, RoutingDecision
)
from monitoring_v2.slo_monitor import SLOStatus, SLOConfig, MockSLOMonitor


class TestAlgorithm1Controller:
    @pytest.fixture
    def monitor(self):
        return MockSLOMonitor()
    
    @pytest.fixture
    def controller(self, monitor):
        controller = Algorithm1Controller(slo_monitor=monitor)
        controller._prewarm_knative = Mock(return_value=True)
        return controller
    
    def test_init(self, controller):
        assert controller.current_weights == {"k3s": 100, "knative": 0}
        assert controller.total_decisions == 0
    
    def test_maintain_when_normal(self, controller, monitor):
        monitor.set_mock_metrics(p99=150.0)  # Below threshold but above healthy
        
        decision = controller.make_decision()
        
        assert decision.action == "MAINTAIN"
        assert decision.weights == {"k3s": 100, "knative": 0}
    
    def test_scale_out_on_violation(self, controller, monitor):
        monitor.set_mock_metrics(p99=250.0)
        
        # First call starts violation timer
        controller.make_decision()
        
        # Simulate sustained violation
        monitor.violation_start_time = int(time.time()) - 35
        
        decision = controller.make_decision()

        assert decision.action == "SCALE_OUT"
        assert decision.weights["knative"] > 0
        assert decision.weights["k3s"] + decision.weights["knative"] == 100
    
    def test_optimize_cost_when_healthy(self, controller, monitor):
        # p99 < 200 * 0.7 = 140ms
        monitor.set_mock_metrics(p99=100.0)
        
        decision = controller.make_decision()

        assert decision.action == "OPTIMIZE_COST"
        assert decision.weights["k3s"] >= 100
    
    def test_predictive_scaling(self, controller, monitor):
        monitor.set_mock_metrics(p99=150.0)
        
        prediction = {
            "predicted_requests": 200,
            "confidence": 0.9
        }
        
        decision = controller.make_decision(
            prediction=prediction,
            current_load=100
        )

        assert decision.action == "PREDICTIVE"
        assert decision.weights["knative"] > 0
    
    def test_prediction_ignored_low_confidence(self, controller, monitor):
        monitor.set_mock_metrics(p99=150.0)
        
        prediction = {
            "predicted_requests": 200,
            "confidence": 0.5  # Below threshold
        }
        
        decision = controller.make_decision(
            prediction=prediction,
            current_load=100
        )
        
        assert decision.action == "MAINTAIN"
    
    def test_cooldown_respected(self, controller, monitor):
        monitor.set_mock_metrics(p99=100.0)
        
        # First decision
        decision1 = controller.make_decision()
        assert decision1.action == "OPTIMIZE_COST"
        
        # Immediate second call should maintain due to cooldown
        decision2 = controller.make_decision()
        assert decision2.action == "MAINTAIN"
    
    def test_statistics(self, controller, monitor):
        monitor.set_mock_metrics(p99=150.0)
        controller.make_decision()
        controller.make_decision()
        
        stats = controller.get_statistics()
        
        assert stats["total_decisions"] == 2
        assert "current_weights" in stats


class TestAlgorithm1Config:
    def test_default_config(self):
        config = Algorithm1Config()
        
        assert config.weight_step == 10
        assert config.cooldown_sec == 15
        assert config.healthy_margin == 0.7
        assert config.max_knative_weight == 50
    
    def test_custom_config(self):
        config = Algorithm1Config(
            weight_step=5,
            cooldown_sec=30,
            healthy_margin=0.8
        )
        
        assert config.weight_step == 5
        assert config.cooldown_sec == 30
        assert config.healthy_margin == 0.8


class TestRoutingDecision:
    def test_routing_decision_dataclass(self):
        decision = RoutingDecision(
            weights={"k3s": 70, "knative": 30},
            reason="Test reason",
            action="SCALE_OUT",
            metrics={"p99": 250.0}
        )
        
        assert decision.weights == {"k3s": 70, "knative": 30}
        assert decision.action == "SCALE_OUT"
        assert decision.metrics["p99"] == 250.0


class TestSLOViolationScenarios:
    """Test various SLO violation scenarios."""
    
    @pytest.fixture
    def monitor(self):
        return MockSLOMonitor()
    
    @pytest.fixture
    def controller(self, monitor):
        controller = Algorithm1Controller(slo_monitor=monitor)
        controller._prewarm_knative = Mock(return_value=True)
        return controller
    
    def test_brief_spike_no_scale_out(self, controller, monitor):
        """Brief latency spike should not trigger scale out."""
        monitor.set_mock_metrics(p99=250.0)
        
        # First call - violation just started
        decision = controller.make_decision()
        
        # Should not scale out immediately
        assert decision.action != "SCALE_OUT"
    
    def test_max_knative_weight_respected(self, controller, monitor):
        """Knative weight should not exceed max."""
        # Set initial weights close to max
        controller.current_weights = {"k3s": 55, "knative": 45}
        
        monitor.set_mock_metrics(p99=250.0)
        monitor.violation_start_time = int(time.time()) - 35
        
        decision = controller.make_decision()
        
        assert decision.weights["knative"] <= controller.config.max_knative_weight
    
    def test_k3s_weight_optimization_limit(self, controller, monitor):
        """k3s weight optimization should not exceed 100."""
        controller.current_weights = {"k3s": 94, "knative": 6}
        
        monitor.set_mock_metrics(p99=100.0)
        
        decision = controller.make_decision()

        assert decision.weights["k3s"] <= 100
