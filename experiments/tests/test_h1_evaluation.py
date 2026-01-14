"""Tests for H1 evaluation."""
import pytest
from pathlib import Path
import sys
import tempfile

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
