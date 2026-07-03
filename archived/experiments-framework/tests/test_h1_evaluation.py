"""Tests for H1 evaluation."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluations.h1_evaluation import H1Evaluator, ScenarioResult


class TestH1Evaluator:
    @pytest.fixture
    def evaluator(self, tmp_path):
        return H1Evaluator(results_dir=tmp_path / "results")
    
    def test_simulate_run(self, evaluator):
        result = evaluator._simulate_run("s1-k8s-only", "steady")
        
        assert isinstance(result, ScenarioResult)
        assert result.scenario == "s1-k8s-only"
        assert result.workload == "steady"
        assert result.p99_latency_ms > 0
    
    def test_full_evaluation(self, evaluator):
        result = evaluator.run_evaluation(
            scenarios=["s1-k8s-only", "s4-hybrid-predictive"],
            workloads=["steady"],
            repetitions=2,
            simulate=True
        )
        
        assert result.hypothesis_proven is not None
        assert "p99_latency" in result.s4_vs_s1_improvement
    
    def test_results_saved(self, evaluator):
        evaluator.run_evaluation(
            scenarios=["s1-k8s-only"],
            workloads=["steady"],
            repetitions=1,
            simulate=True
        )
        
        files = list(evaluator.results_dir.glob("*.csv"))
        assert len(files) >= 1


class TestExecuteRun:
    """Tests for _execute_run with mocked infrastructure."""
    
    @pytest.fixture
    def mock_k6_result(self):
        """Create a mock K6Result."""
        mock = Mock()
        mock.success = True
        mock.http_reqs = 15000
        mock.http_req_duration_p95 = 45.5
        mock.http_req_duration_p99 = 85.2
        mock.http_req_failed_rate = 0.002
        mock.vus_max = 50
        mock.raw_output = "k6 output"
        return mock
    
    @pytest.fixture
    def mock_prometheus_latencies(self):
        return {"p50": 25.0, "p95": 55.0, "p99": 95.0}
    
    @pytest.fixture
    def evaluator_with_mocks(self, tmp_path, mock_k6_result, mock_prometheus_latencies):
        """Create evaluator with all dependencies mocked."""
        with patch("evaluations.h1_evaluation.K6Runner") as mock_k6_cls, \
             patch("evaluations.h1_evaluation.PrometheusClient") as mock_prom_cls, \
             patch("evaluations.h1_evaluation.requests") as mock_requests:
            
            mock_k6 = Mock()
            mock_k6.run_workload.return_value = mock_k6_result
            mock_k6_cls.return_value = mock_k6
            
            mock_prom = Mock()
            mock_prom.get_latency_percentiles.return_value = mock_prometheus_latencies
            mock_prom.get_error_rate.return_value = 0.003
            mock_prom.get_throughput.return_value = 100.5
            mock_prom.query_instant.side_effect = lambda expr: (
                8000.0 if "k3s-cluster" in expr else 2000.0
            )
            mock_prom_cls.return_value = mock_prom
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_requests.post.return_value = mock_response
            
            evaluator = H1Evaluator(results_dir=tmp_path / "results")
            evaluator._mock_k6 = mock_k6
            evaluator._mock_prom = mock_prom
            evaluator._mock_requests = mock_requests
            
            yield evaluator
    
    def test_execute_run_calls_configure_scenario(self, evaluator_with_mocks):
        """Test that _execute_run calls the routing daemon to set scenario."""
        with patch.object(evaluator_with_mocks, "_configure_scenario") as mock_config:
            with patch.object(evaluator_with_mocks, "_calculate_cost_proxy", return_value=1.2):
                result = evaluator_with_mocks._execute_run("s1-k8s-only", "steady")
        
        mock_config.assert_called_once_with("s1-k8s-only")
        assert result.scenario == "s1-k8s-only"
    
    def test_execute_run_runs_k6_workload(self, evaluator_with_mocks):
        """Test that _execute_run runs k6 load test."""
        with patch.object(evaluator_with_mocks, "_configure_scenario"):
            with patch.object(evaluator_with_mocks, "_calculate_cost_proxy", return_value=1.0):
                result = evaluator_with_mocks._execute_run("s4-hybrid-predictive", "spike")
        
        evaluator_with_mocks.k6_runner.run_workload.assert_called_once()
        call_kwargs = evaluator_with_mocks.k6_runner.run_workload.call_args
        assert call_kwargs.kwargs["workload"] == "spike"
        assert call_kwargs.kwargs["scenario"] == "s4-hybrid-predictive"
        assert call_kwargs.kwargs["duration_sec"] == 300
    
    def test_execute_run_queries_prometheus_metrics(self, evaluator_with_mocks):
        """Test that _execute_run queries Prometheus for metrics."""
        with patch.object(evaluator_with_mocks, "_configure_scenario"):
            with patch.object(evaluator_with_mocks, "_calculate_cost_proxy", return_value=1.1):
                result = evaluator_with_mocks._execute_run("s2-serverless-only", "endurance")
        
        evaluator_with_mocks.prometheus.get_latency_percentiles.assert_called_once()
        evaluator_with_mocks.prometheus.get_error_rate.assert_called_once()
        evaluator_with_mocks.prometheus.get_throughput.assert_called_once()
        
        assert result.p50_latency_ms == 25.0
        assert result.p95_latency_ms == 55.0
        assert result.p99_latency_ms == 95.0
    
    def test_execute_run_returns_valid_scenario_result(self, evaluator_with_mocks):
        """Test that _execute_run returns a valid ScenarioResult."""
        with patch.object(evaluator_with_mocks, "_configure_scenario"):
            with patch.object(evaluator_with_mocks, "_calculate_cost_proxy", return_value=1.25):
                result = evaluator_with_mocks._execute_run("s4-hybrid-predictive", "steady")
        
        assert isinstance(result, ScenarioResult)
        assert result.scenario == "s4-hybrid-predictive"
        assert result.workload == "steady"
        assert result.p99_latency_ms > 0
        assert result.cost_proxy == 1.25
        assert result.duration_sec == 300
        assert result.timestamp > 0
    
    def test_execute_run_falls_back_to_k6_metrics(self, evaluator_with_mocks):
        """Test fallback to k6 metrics when Prometheus returns zeros."""
        evaluator_with_mocks.prometheus.get_latency_percentiles.return_value = {
            "p50": 0.0, "p95": 0.0, "p99": 0.0
        }
        
        with patch.object(evaluator_with_mocks, "_configure_scenario"):
            with patch.object(evaluator_with_mocks, "_calculate_cost_proxy", return_value=1.0):
                result = evaluator_with_mocks._execute_run("s1-k8s-only", "steady")
        
        assert result.p95_latency_ms == 45.5
        assert result.p99_latency_ms == 85.2


class TestConfigureScenario:
    """Tests for _configure_scenario helper."""
    
    def test_configure_scenario_posts_to_daemon(self, tmp_path):
        """Test that _configure_scenario sends POST to routing daemon."""
        with patch("evaluations.h1_evaluation.requests") as mock_requests, \
             patch("evaluations.h1_evaluation.K6Runner"), \
             patch("evaluations.h1_evaluation.PrometheusClient"):
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_requests.post.return_value = mock_response
            
            evaluator = H1Evaluator(
                results_dir=tmp_path / "results",
                routing_daemon_url="http://localhost:9104"
            )
            evaluator._configure_scenario("s4-hybrid-predictive")
            
            mock_requests.post.assert_called_once_with(
                "http://localhost:9104/set_scenario",
                json={"scenario": "s4-hybrid-predictive"},
                timeout=10,
            )
    
    def test_configure_scenario_raises_on_failure(self, tmp_path):
        """Test that _configure_scenario raises RuntimeError on failure."""
        with patch("evaluations.h1_evaluation.requests") as mock_requests, \
             patch("evaluations.h1_evaluation.K6Runner"), \
             patch("evaluations.h1_evaluation.PrometheusClient"):
            
            import requests as real_requests
            mock_requests.post.side_effect = real_requests.RequestException("Connection refused")
            mock_requests.RequestException = real_requests.RequestException
            
            evaluator = H1Evaluator(results_dir=tmp_path / "results")
            
            with pytest.raises(RuntimeError, match="Failed to configure scenario"):
                evaluator._configure_scenario("s1-k8s-only")


class TestCalculateCostProxy:
    """Tests for _calculate_cost_proxy helper."""
    
    def test_cost_proxy_pure_k8s(self, tmp_path):
        """Test cost proxy for pure K8s (all requests to k3s)."""
        with patch("evaluations.h1_evaluation.K6Runner"), \
             patch("evaluations.h1_evaluation.PrometheusClient") as mock_prom_cls:
            
            mock_prom = Mock()
            mock_prom.query_instant.side_effect = lambda expr: (
                10000.0 if "k3s-cluster" in expr else 0.0
            )
            mock_prom_cls.return_value = mock_prom
            
            evaluator = H1Evaluator(results_dir=tmp_path / "results")
            cost = evaluator._calculate_cost_proxy()
            
            assert cost == 1.0
    
    def test_cost_proxy_pure_serverless(self, tmp_path):
        """Test cost proxy for pure serverless (all requests to knative)."""
        with patch("evaluations.h1_evaluation.K6Runner"), \
             patch("evaluations.h1_evaluation.PrometheusClient") as mock_prom_cls:
            
            mock_prom = Mock()
            mock_prom.query_instant.side_effect = lambda expr: (
                0.0 if "k3s-cluster" in expr else 10000.0
            )
            mock_prom_cls.return_value = mock_prom
            
            evaluator = H1Evaluator(results_dir=tmp_path / "results")
            cost = evaluator._calculate_cost_proxy()
            
            assert cost == 1.5
    
    def test_cost_proxy_hybrid_80_20(self, tmp_path):
        """Test cost proxy for 80/20 hybrid split."""
        with patch("evaluations.h1_evaluation.K6Runner"), \
             patch("evaluations.h1_evaluation.PrometheusClient") as mock_prom_cls:
            
            mock_prom = Mock()
            mock_prom.query_instant.side_effect = lambda expr: (
                8000.0 if "k3s-cluster" in expr else 2000.0
            )
            mock_prom_cls.return_value = mock_prom
            
            evaluator = H1Evaluator(results_dir=tmp_path / "results")
            cost = evaluator._calculate_cost_proxy()
            
            assert cost == 1.1
    
    def test_cost_proxy_no_requests(self, tmp_path):
        """Test cost proxy when no requests (defaults to 1.0)."""
        with patch("evaluations.h1_evaluation.K6Runner"), \
             patch("evaluations.h1_evaluation.PrometheusClient") as mock_prom_cls:
            
            mock_prom = Mock()
            mock_prom.query_instant.return_value = None
            mock_prom_cls.return_value = mock_prom
            
            evaluator = H1Evaluator(results_dir=tmp_path / "results")
            cost = evaluator._calculate_cost_proxy()
            
            assert cost == 1.0
