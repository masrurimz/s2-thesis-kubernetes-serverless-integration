#!/usr/bin/env python3
"""Unit tests for H2Evaluator with mocked infrastructure dependencies."""

import json
import pytest
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
from dataclasses import asdict

import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from evaluations.h2_evaluation import H2Evaluator, H2ScenarioResult, H2EvaluationResult
from controller.workloads.k6_runner import K6Result


@pytest.fixture
def mock_prometheus_client():
    """Mock PrometheusClient for testing."""
    with patch("evaluations.h2_evaluation.PrometheusClient") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        
        mock_instance.query_instant.return_value = 0.0
        mock_instance.query_range.return_value = []
        mock_instance.get_latency_percentiles.return_value = {
            "p50": 50.0,
            "p95": 150.0,
            "p99": 180.0,
        }
        mock_instance.get_error_rate.return_value = 0.01
        
        yield mock_instance


@pytest.fixture
def mock_k6_runner():
    """Mock K6Runner for testing."""
    with patch("evaluations.h2_evaluation.K6Runner") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        
        mock_instance.run_workload.return_value = K6Result(
            success=True,
            http_reqs=10000,
            http_req_duration_p95=150.0,
            http_req_duration_p99=180.0,
            http_req_failed_rate=0.01,
            vus_max=100,
            raw_output="k6 test completed",
            metrics={},
        )
        
        yield mock_instance


@pytest.fixture
def mock_requests():
    """Mock requests for routing daemon API calls."""
    with patch("evaluations.h2_evaluation.requests") as mock_req:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok", "scenario": "s4-hybrid-predictive"}
        mock_response.raise_for_status = MagicMock()
        mock_req.post.return_value = mock_response
        
        yield mock_req


@pytest.fixture
def mock_experiment_logger():
    """Mock ExperimentLogger for testing."""
    with patch("evaluations.h2_evaluation.ExperimentLogger") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        mock_instance.start_run.return_value = 1
        
        yield mock_instance


@pytest.fixture
def evaluator(mock_prometheus_client, mock_k6_runner, mock_requests, mock_experiment_logger, tmp_path):
    """Create H2Evaluator with mocked dependencies."""
    return H2Evaluator(results_dir=tmp_path / "h2_results")


class TestH2EvaluatorInit:
    """Tests for H2Evaluator initialization."""
    
    def test_default_initialization(self, mock_prometheus_client, mock_k6_runner, mock_experiment_logger, tmp_path):
        """Test default configuration values."""
        evaluator = H2Evaluator(results_dir=tmp_path / "test")
        
        assert evaluator.routing_daemon_url == "http://localhost:9104"
        assert evaluator.prometheus_url == "http://localhost:9090"
        assert evaluator.k6_duration_sec == 300
    
    def test_custom_initialization(self, mock_prometheus_client, mock_k6_runner, mock_experiment_logger, tmp_path):
        """Test custom configuration values."""
        evaluator = H2Evaluator(
            results_dir=tmp_path / "test",
            routing_daemon_url="http://custom:9104",
            prometheus_url="http://custom:9090",
            k6_duration_sec=600,
        )
        
        assert evaluator.routing_daemon_url == "http://custom:9104"
        assert evaluator.prometheus_url == "http://custom:9090"
        assert evaluator.k6_duration_sec == 600
    
    def test_results_dir_created(self, mock_prometheus_client, mock_k6_runner, mock_experiment_logger, tmp_path):
        """Test that results directory is created."""
        results_dir = tmp_path / "nested" / "h2_results"
        evaluator = H2Evaluator(results_dir=results_dir)
        
        assert results_dir.exists()


class TestConfigureScenario:
    """Tests for _configure_scenario method."""
    
    def test_configure_scenario_success(self, evaluator, mock_requests):
        """Test successful scenario configuration."""
        evaluator._configure_scenario("s4-hybrid-predictive")
        
        mock_requests.post.assert_called_once()
        call_args = mock_requests.post.call_args
        assert "set_scenario" in call_args[0][0]
        assert call_args[1]["json"]["scenario"] == "s4-hybrid-predictive"
    
    def test_configure_scenario_failure(self, evaluator, mock_requests):
        """Test scenario configuration failure handling."""
        import requests as real_requests
        mock_requests.post.side_effect = real_requests.RequestException("Connection refused")
        mock_requests.RequestException = real_requests.RequestException
        
        with pytest.raises(RuntimeError) as exc_info:
            evaluator._configure_scenario("s4-hybrid-predictive")
        
        assert "Failed to configure scenario" in str(exc_info.value)


class TestGetControllerMetricsSnapshot:
    """Tests for _get_controller_metrics_snapshot method."""
    
    def test_get_metrics_snapshot(self, evaluator, mock_prometheus_client):
        """Test metrics snapshot collection."""
        mock_prometheus_client.query_instant.side_effect = [
            5.0,  # slo_violations
            10.0,  # PREDICTIVE
            3.0,  # SCALE_OUT
            2.0,  # OPTIMIZE_COST
            8.0,  # MAINTAIN
            1500.0,  # reaction_time_sum
            20.0,  # reaction_time_count
        ]
        
        metrics = evaluator._get_controller_metrics_snapshot()
        
        assert metrics["slo_violations"] == 5.0
        assert metrics["routing_predictive"] == 10.0
        assert metrics["routing_scale_out"] == 3.0
        assert metrics["reaction_time_sum"] == 1500.0
        assert metrics["reaction_time_count"] == 20.0
    
    def test_get_metrics_snapshot_with_none_values(self, evaluator, mock_prometheus_client):
        """Test metrics snapshot handles None values."""
        mock_prometheus_client.query_instant.return_value = None
        
        metrics = evaluator._get_controller_metrics_snapshot()
        
        assert metrics["slo_violations"] == 0.0
        assert metrics["routing_predictive"] == 0.0


class TestCalculateSloViolations:
    """Tests for _calculate_slo_violations method."""
    
    def test_calculate_violations_delta(self, evaluator):
        """Test SLO violations calculation."""
        baseline = {"slo_violations": 5.0}
        final = {"slo_violations": 12.0}
        
        result = evaluator._calculate_slo_violations(baseline, final)
        
        assert result == 7
    
    def test_calculate_violations_no_increase(self, evaluator):
        """Test SLO violations when no increase."""
        baseline = {"slo_violations": 10.0}
        final = {"slo_violations": 10.0}
        
        result = evaluator._calculate_slo_violations(baseline, final)
        
        assert result == 0
    
    def test_calculate_violations_negative_clamped(self, evaluator):
        """Test SLO violations negative values are clamped to 0."""
        baseline = {"slo_violations": 10.0}
        final = {"slo_violations": 5.0}
        
        result = evaluator._calculate_slo_violations(baseline, final)
        
        assert result == 0


class TestCalculateRoutingDecisions:
    """Tests for _calculate_routing_decisions method."""
    
    def test_calculate_predictive_decisions(self, evaluator):
        """Test predictive routing decisions calculation."""
        baseline = {"routing_predictive": 5.0}
        final = {"routing_predictive": 15.0}
        
        result = evaluator._calculate_routing_decisions(baseline, final, "PREDICTIVE")
        
        assert result == 10
    
    def test_calculate_scale_out_decisions(self, evaluator):
        """Test scale out routing decisions calculation."""
        baseline = {"routing_scale_out": 2.0}
        final = {"routing_scale_out": 8.0}
        
        result = evaluator._calculate_routing_decisions(baseline, final, "SCALE_OUT")
        
        assert result == 6


class TestCalculateAvgReactionTime:
    """Tests for _calculate_avg_reaction_time method."""
    
    def test_calculate_avg_reaction_time(self, evaluator):
        """Test average reaction time calculation."""
        baseline = {"reaction_time_sum": 1000.0, "reaction_time_count": 10.0}
        final = {"reaction_time_sum": 3500.0, "reaction_time_count": 20.0}
        
        result = evaluator._calculate_avg_reaction_time(baseline, final)
        
        assert result == 250.0
    
    def test_calculate_avg_reaction_time_no_samples(self, evaluator):
        """Test average reaction time with no new samples."""
        baseline = {"reaction_time_sum": 1000.0, "reaction_time_count": 10.0}
        final = {"reaction_time_sum": 1000.0, "reaction_time_count": 10.0}
        
        result = evaluator._calculate_avg_reaction_time(baseline, final)
        
        assert result == 0.0


class TestCalculateViolationDuration:
    """Tests for _calculate_violation_duration method."""
    
    def test_calculate_violation_duration(self, evaluator, mock_prometheus_client):
        """Test violation duration calculation."""
        mock_prometheus_client.query_range.return_value = [
            (1000, 1.0),  # violation
            (1060, 0.0),  # no violation
            (1120, 2.0),  # violation
            (1180, 1.0),  # violation
        ]
        
        result = evaluator._calculate_violation_duration(1000, 1200)
        
        assert result == 180  # 3 minutes * 60 seconds
    
    def test_calculate_violation_duration_no_violations(self, evaluator, mock_prometheus_client):
        """Test violation duration with no violations."""
        mock_prometheus_client.query_range.return_value = [
            (1000, 0.0),
            (1060, 0.0),
        ]
        
        result = evaluator._calculate_violation_duration(1000, 1200)
        
        assert result == 0


class TestExecuteRun:
    """Tests for _execute_run method."""
    
    def test_execute_run_success(
        self, evaluator, mock_prometheus_client, mock_k6_runner, mock_requests, mock_experiment_logger
    ):
        """Test successful run execution."""
        mock_prometheus_client.query_instant.side_effect = [
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,  # baseline
            5.0, 10.0, 3.0, 2.0, 8.0, 2500.0, 25.0,  # final
        ]
        mock_prometheus_client.query_range.return_value = [(1000, 1.0), (1060, 1.0)]
        
        result = evaluator._execute_run("s4-hybrid-predictive", "spike")
        
        assert isinstance(result, H2ScenarioResult)
        assert result.scenario == "s4-hybrid-predictive"
        assert result.workload == "spike"
        assert result.slo_violations == 5
        assert result.proactive_adjustments == 10
        assert result.reactive_adjustments == 3
    
    def test_execute_run_calls_configure_scenario(
        self, evaluator, mock_prometheus_client, mock_k6_runner, mock_requests, mock_experiment_logger
    ):
        """Test that execute_run calls configure_scenario."""
        mock_prometheus_client.query_instant.return_value = 0.0
        mock_prometheus_client.query_range.return_value = []
        
        evaluator._execute_run("s3-hybrid-reactive", "endurance")
        
        mock_requests.post.assert_called_once()
        assert "s3-hybrid-reactive" in str(mock_requests.post.call_args)
    
    def test_execute_run_calls_k6(
        self, evaluator, mock_prometheus_client, mock_k6_runner, mock_requests, mock_experiment_logger
    ):
        """Test that execute_run calls k6 runner."""
        mock_prometheus_client.query_instant.return_value = 0.0
        mock_prometheus_client.query_range.return_value = []
        
        evaluator._execute_run("s4-hybrid-predictive", "spike")
        
        mock_k6_runner.run_workload.assert_called_once_with(
            workload="spike",
            scenario="s4-hybrid-predictive",
            duration_sec=300,
        )
    
    def test_execute_run_logs_metrics(
        self, evaluator, mock_prometheus_client, mock_k6_runner, mock_requests, mock_experiment_logger
    ):
        """Test that execute_run logs metrics."""
        mock_prometheus_client.query_instant.return_value = 0.0
        mock_prometheus_client.query_range.return_value = []
        
        evaluator._execute_run("s4-hybrid-predictive", "spike")
        
        mock_experiment_logger.log_metrics.assert_called_once()
        mock_experiment_logger.end_run.assert_called()
    
    def test_execute_run_handles_k6_failure(
        self, evaluator, mock_prometheus_client, mock_k6_runner, mock_requests, mock_experiment_logger
    ):
        """Test that execute_run handles k6 failure gracefully."""
        mock_k6_runner.run_workload.return_value = K6Result(
            success=False,
            http_reqs=0,
            http_req_duration_p95=0.0,
            http_req_duration_p99=0.0,
            http_req_failed_rate=1.0,
            vus_max=0,
            raw_output="k6 test failed",
            metrics={},
        )
        mock_prometheus_client.query_instant.return_value = 0.0
        mock_prometheus_client.query_range.return_value = []
        
        result = evaluator._execute_run("s4-hybrid-predictive", "spike")
        
        assert isinstance(result, H2ScenarioResult)
    
    def test_execute_run_scenario_config_failure(
        self, evaluator, mock_prometheus_client, mock_k6_runner, mock_requests, mock_experiment_logger
    ):
        """Test that execute_run handles scenario config failure."""
        import requests as real_requests
        mock_requests.post.side_effect = real_requests.RequestException("Connection refused")
        mock_requests.RequestException = real_requests.RequestException
        
        with pytest.raises(RuntimeError):
            evaluator._execute_run("s4-hybrid-predictive", "spike")
        
        mock_experiment_logger.end_run.assert_called()


class TestSimulateRun:
    """Tests for _simulate_run method."""
    
    def test_simulate_run_s3(self, evaluator, mock_experiment_logger):
        """Test simulated run for S3 scenario."""
        result = evaluator._simulate_run("s3-hybrid-reactive", "spike")
        
        assert isinstance(result, H2ScenarioResult)
        assert result.scenario == "s3-hybrid-reactive"
        assert result.workload == "spike"
        assert result.proactive_adjustments == 0
    
    def test_simulate_run_s4(self, evaluator, mock_experiment_logger):
        """Test simulated run for S4 scenario."""
        result = evaluator._simulate_run("s4-hybrid-predictive", "spike")
        
        assert isinstance(result, H2ScenarioResult)
        assert result.scenario == "s4-hybrid-predictive"
        assert result.workload == "spike"
        assert result.proactive_adjustments > 0


class TestRunEvaluation:
    """Tests for run_evaluation method."""
    
    def test_run_evaluation_simulate(self, evaluator, mock_experiment_logger, tmp_path):
        """Test full evaluation with simulation."""
        result = evaluator.run_evaluation(
            scenarios=["s3-hybrid-reactive", "s4-hybrid-predictive"],
            workloads=["spike"],
            repetitions=1,
            simulate=True,
        )
        
        assert isinstance(result, H2EvaluationResult)
        assert "violation_reduction" in asdict(result)
    
    def test_run_evaluation_saves_results(self, evaluator, mock_experiment_logger, tmp_path):
        """Test that evaluation saves results to files."""
        evaluator.run_evaluation(
            scenarios=["s3-hybrid-reactive", "s4-hybrid-predictive"],
            workloads=["spike"],
            repetitions=1,
            simulate=True,
        )
        
        results_dir = evaluator.results_dir
        csv_files = list(results_dir.glob("h2_raw_data_*.csv"))
        json_files = list(results_dir.glob("h2_summary_*.json"))
        md_files = list(results_dir.glob("h2_report_*.md"))
        
        assert len(csv_files) == 1
        assert len(json_files) == 1
        assert len(md_files) == 1


class TestAnalyzeResults:
    """Tests for _analyze_results method."""
    
    def test_analyze_results_hypothesis_proven(self, evaluator, mock_experiment_logger):
        """Test analysis with hypothesis proven."""
        evaluator.results = [
            H2ScenarioResult(
                scenario="s3-hybrid-reactive", workload="spike", run_id=1,
                slo_violations=10, slo_violation_duration_sec=120,
                proactive_adjustments=0, reactive_adjustments=15,
                avg_reaction_time_ms=5000, p99_latency_ms=210, error_rate=0.02,
                timestamp=int(time.time()),
            ),
            H2ScenarioResult(
                scenario="s4-hybrid-predictive", workload="spike", run_id=2,
                slo_violations=2, slo_violation_duration_sec=20,
                proactive_adjustments=12, reactive_adjustments=3,
                avg_reaction_time_ms=1500, p99_latency_ms=160, error_rate=0.01,
                timestamp=int(time.time()),
            ),
        ]
        
        result = evaluator._analyze_results()
        
        assert result.hypothesis_proven == True
        assert result.violation_reduction > 50
        assert result.proactive_ratio > 0.5
    
    def test_analyze_results_hypothesis_not_proven(self, evaluator, mock_experiment_logger):
        """Test analysis with hypothesis not proven."""
        evaluator.results = [
            H2ScenarioResult(
                scenario="s3-hybrid-reactive", workload="spike", run_id=1,
                slo_violations=10, slo_violation_duration_sec=120,
                proactive_adjustments=0, reactive_adjustments=15,
                avg_reaction_time_ms=5000, p99_latency_ms=210, error_rate=0.02,
                timestamp=int(time.time()),
            ),
            H2ScenarioResult(
                scenario="s4-hybrid-predictive", workload="spike", run_id=2,
                slo_violations=8, slo_violation_duration_sec=100,
                proactive_adjustments=2, reactive_adjustments=12,
                avg_reaction_time_ms=4500, p99_latency_ms=200, error_rate=0.018,
                timestamp=int(time.time()),
            ),
        ]
        
        result = evaluator._analyze_results()
        
        assert result.hypothesis_proven == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
