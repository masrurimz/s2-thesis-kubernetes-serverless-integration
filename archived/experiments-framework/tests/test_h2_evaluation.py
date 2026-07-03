"""Tests for H2 evaluation."""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluations.h2_evaluation import H2Evaluator, H2ScenarioResult


class TestH2Evaluator:
    @pytest.fixture
    def evaluator(self, tmp_path):
        return H2Evaluator(results_dir=tmp_path / "results")
    
    def test_simulate_run(self, evaluator):
        result = evaluator._simulate_run("s3-hybrid-reactive", "spike")
        
        assert isinstance(result, H2ScenarioResult)
        assert result.scenario == "s3-hybrid-reactive"
        assert result.slo_violations >= 0
    
    def test_full_evaluation(self, evaluator):
        result = evaluator.run_evaluation(
            scenarios=["s3-hybrid-reactive", "s4-hybrid-predictive"],
            workloads=["spike"],
            repetitions=2,
            simulate=True
        )
        
        assert result.hypothesis_proven is not None
        assert "slo_violations" in result.s4_vs_s3_improvement
    
    def test_proactive_ratio_calculated(self, evaluator):
        result = evaluator.run_evaluation(
            repetitions=1,
            simulate=True
        )
        
        assert 0 <= result.proactive_ratio <= 1
