#!/usr/bin/env python3
"""
Tests for Routing Daemon.
"""

import time
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from daemon.routing_daemon import (
    RoutingDaemon,
    Scenario,
    SCENARIO_CONFIGS,
    ScenarioConfig,
)
from config import settings
from daemon.gru_client import GRUClient, PredictionResult
from intelligent_router.weight_adjuster import HAProxyWeightAdjuster
from monitoring_v2.slo_monitor import SLOStatus


class TestScenarioConfigs:
    """Test scenario configuration."""
    
    def test_all_scenarios_defined(self):
        """All scenarios have configs."""
        for scenario in Scenario:
            assert scenario in SCENARIO_CONFIGS
    
    def test_s1_k8s_only_config(self):
        """S1 routes 100% to K8s."""
        config = SCENARIO_CONFIGS[Scenario.S1_K8S_ONLY]
        assert config.k3s_weight == 100
        assert config.knative_weight == 0
        assert config.use_algorithm is False
        assert config.use_predictions is False
    
    def test_s2_serverless_only_config(self):
        """S2 routes 100% to serverless."""
        config = SCENARIO_CONFIGS[Scenario.S2_SERVERLESS_ONLY]
        assert config.k3s_weight == 0
        assert config.knative_weight == 100
        assert config.use_algorithm is False
        assert config.use_predictions is False
    
    def test_s3_hybrid_reactive_config(self):
        """S3 uses algorithm without predictions."""
        config = SCENARIO_CONFIGS[Scenario.S3_HYBRID_REACTIVE]
        assert config.k3s_weight == 80
        assert config.knative_weight == 20
        assert config.use_algorithm is True
        assert config.use_predictions is False
    
    def test_s4_hybrid_predictive_config(self):
        """S4 uses algorithm with predictions."""
        config = SCENARIO_CONFIGS[Scenario.S4_HYBRID_PREDICTIVE]
        assert config.k3s_weight == 80
        assert config.knative_weight == 20
        assert config.use_algorithm is True
        assert config.use_predictions is True


class TestGRUClient:
    """Test GRU prediction client."""
    
    def test_init(self):
        """Test client initialization."""
        client = GRUClient(base_url="http://test:8090")
        assert client.base_url == "http://test:8090"
        assert client.timeout == 5.0
    
    def test_empty_history_returns_error(self):
        """Empty history returns error result."""
        client = GRUClient()
        result = client.predict([])
        assert result.success is False
        assert "Empty" in result.error
    
    @patch("requests.get")
    def test_is_healthy_success(self, mock_get):
        """Health check succeeds with healthy response."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "status": "healthy",
            "model_loaded": True,
        }
        
        client = GRUClient()
        assert client.is_healthy() is True
    
    @patch("requests.get")
    def test_is_healthy_failure(self, mock_get):
        """Health check fails with unhealthy response."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "status": "degraded",
            "model_loaded": False,
        }
        
        client = GRUClient()
        assert client.is_healthy() is False
    
    @patch("requests.post")
    def test_predict_success(self, mock_post):
        """Prediction succeeds with valid response."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "predicted_requests": 150,
            "confidence": 0.85,
            "horizon_values": [140, 145, 150, 155, 160],
            "latency_ms": 12.5,
        }
        
        client = GRUClient()
        result = client.predict([100, 110, 120, 130, 140])
        
        assert result.success is True
        assert result.predicted_requests == 150
        assert result.confidence == 0.85
        assert len(result.horizon_values) == 5
    
    @patch("requests.post")
    def test_predict_connection_error(self, mock_post):
        """Prediction handles connection errors."""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        client = GRUClient(retry_count=0)
        result = client.predict([100, 110, 120])
        
        assert result.success is False
        assert "Connection" in result.error


@pytest.fixture
def mock_weight_adjuster():
    """Create a mock HAProxyWeightAdjuster."""
    with patch("daemon.routing_daemon.HAProxyWeightAdjuster") as mock_class:
        mock_instance = MagicMock()
        mock_instance.socket_available = True
        mock_instance.set_weights_with_retry.return_value = True
        mock_instance.get_current_weights.return_value = {"k3s": 80, "knative": 20}
        mock_class.return_value = mock_instance
        yield mock_instance


class TestRoutingDaemon:
    """Test routing daemon."""
    
    def test_init_s1_scenario(self, mock_weight_adjuster):
        """Initialize with S1 scenario."""
        # Use settings defaults for other params
        daemon = RoutingDaemon(scenario="s1-k8s-only")
        
        assert daemon.scenario == Scenario.S1_K8S_ONLY
        assert daemon.current_weights["k3s"] == 100
        assert daemon.current_weights["knative"] == 0
    
    def test_init_s4_scenario(self, mock_weight_adjuster):
        """Initialize with S4 scenario."""
        daemon = RoutingDaemon(scenario="s4-hybrid-predictive")
        
        assert daemon.scenario == Scenario.S4_HYBRID_PREDICTIVE
        assert daemon.scenario_config.use_predictions is True
    

    def test_init_syncs_algorithm_controller_weights(self, mock_weight_adjuster):
        """Controller must start from scenario baseline weights."""
        daemon = RoutingDaemon(scenario="s3-hybrid-reactive")

        assert daemon.current_weights == {"k3s": 80, "knative": 20}
        assert daemon.algorithm_controller.current_weights == {"k3s": 80, "knative": 20}
        assert daemon.algorithm_controller.serverless_enabled is True
    def test_init_invalid_scenario(self):
        """Invalid scenario raises error."""
        with pytest.raises(ValueError) as exc:
            RoutingDaemon(scenario="invalid-scenario")
        assert "Invalid scenario" in str(exc.value)
    
    def test_get_status(self, mock_weight_adjuster):
        """Get status returns expected structure."""
        daemon = RoutingDaemon(scenario="s3-hybrid-reactive")
        
        status = daemon.get_status()
        
        assert "scenario" in status
        assert "weights" in status
        assert "decision_count" in status
        assert "uptime_seconds" in status
        assert status["scenario"] == "s3-hybrid-reactive"
    
    def test_set_scenario(self, mock_weight_adjuster):
        """Changing scenario updates weights."""
        daemon = RoutingDaemon(scenario="s1-k8s-only")
        
        assert daemon.current_weights["k3s"] == 100
        
        daemon.set_scenario("s2-serverless-only")
        
        assert daemon.scenario == Scenario.S2_SERVERLESS_ONLY
        assert daemon.current_weights["k3s"] == 0
        assert daemon.current_weights["knative"] == 100
    
    def test_set_invalid_scenario(self, mock_weight_adjuster):
        """Setting invalid scenario raises error."""
        daemon = RoutingDaemon(scenario="s1-k8s-only")
        
        with pytest.raises(ValueError):
            daemon.set_scenario("invalid")


class TestDecisionLoop:
    """Test decision loop execution."""
    
    def test_static_scenario_no_algorithm(self, mock_weight_adjuster):
        """Static scenarios don't run algorithm."""
        daemon = RoutingDaemon(scenario="s1-k8s-only")
        
        initial_count = daemon._decision_count
        daemon._execute_decision_loop()
        
        assert daemon._decision_count == initial_count + 1
        assert daemon._last_decision_time is not None
    
    @patch("requests.get")
    def test_reactive_scenario_runs_algorithm(self, mock_get, mock_weight_adjuster):
        """Reactive scenario runs algorithm."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "status": "success",
            "data": {"result": [{"value": [0, "100"]}]},
        }
        
        daemon = RoutingDaemon(scenario="s3-hybrid-reactive")
        
        daemon._execute_decision_loop()
        
        assert daemon._decision_count == 1
        assert daemon.algorithm_controller.total_decisions == 1


    @patch("requests.get")
    def test_blocked_optimize_cost_does_not_apply_weights(self, mock_get, mock_weight_adjuster):
        """Readiness gate must prevent blocked OPTIMIZE_COST from changing applied weights."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "status": "success",
            "data": {"result": [{"value": [0, "0"]}]},
        }

        daemon = RoutingDaemon(scenario="s3-hybrid-reactive")
        daemon.current_weights = {"k3s": 100, "knative": 0}

        blocked_decision = MagicMock()
        blocked_decision.action = "OPTIMIZE_COST"
        blocked_decision.weights = {"k3s": 55, "knative": 45}
        blocked_decision.reason = "test"
        daemon.algorithm_controller.make_decision = MagicMock(return_value=blocked_decision)
        daemon.algorithm_controller._maintain = MagicMock(
            return_value=MagicMock(
                action="MAINTAIN",
                weights={"k3s": 100, "knative": 0},
                reason="maintain",
            )
        )
        daemon.algorithm_controller.commit_applied_decision = MagicMock()

        daemon.k8s_scaler = MagicMock()
        daemon.k8s_scaler.is_ready.return_value = False
        daemon.cluster_controller = MagicMock()

        daemon._execute_decision_loop()

        mock_weight_adjuster.set_weights_with_retry.assert_not_called()
        daemon.algorithm_controller.commit_applied_decision.assert_not_called()
        assert daemon.current_weights == {"k3s": 100, "knative": 0}


class TestIntegration:
    """Integration tests."""
    
    def test_stop_daemon(self, mock_weight_adjuster):
        """Daemon can be stopped."""
        daemon = RoutingDaemon(scenario="s1-k8s-only")
        
        daemon.stop()
        assert daemon._shutdown_event.is_set()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
