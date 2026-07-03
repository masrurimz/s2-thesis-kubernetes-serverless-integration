"""Tests for experiment runner."""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from experiments.experiment_runner import ExperimentRunner


class TestExperimentRunner:
    """Tests for ExperimentRunner class."""

    @pytest.fixture
    def runner(self, tmp_path):
        """Create runner with temp directories."""
        with patch("experiments.experiment_runner.ExperimentLogger"):
            runner = ExperimentRunner(db_path=str(tmp_path / "test.db"))
            runner.results_dir = tmp_path / "results"
            runner.scenarios_dir = tmp_path / "scenarios"
            runner.results_dir.mkdir()
            runner.scenarios_dir.mkdir()
            return runner

    def test_scenarios_constant(self):
        """Test scenario list is correct."""
        assert "s1-k8s-only" in ExperimentRunner.SCENARIOS
        assert "s2-serverless-only" in ExperimentRunner.SCENARIOS
        assert "s3-hybrid-reactive" in ExperimentRunner.SCENARIOS
        assert "s4-hybrid-predictive" in ExperimentRunner.SCENARIOS
        assert len(ExperimentRunner.SCENARIOS) == 4

    def test_workloads_constant(self):
        """Test workload list is correct."""
        assert "steady" in ExperimentRunner.WORKLOADS
        assert "spike" in ExperimentRunner.WORKLOADS
        assert "endurance" in ExperimentRunner.WORKLOADS
        assert len(ExperimentRunner.WORKLOADS) == 3

    def test_invalid_scenario_raises(self, runner):
        """Test invalid scenario raises error."""
        with pytest.raises(ValueError, match="Unknown scenario"):
            runner.run_scenario("invalid-scenario", "steady")

    def test_invalid_workload_raises(self, runner):
        """Test invalid workload raises error."""
        with pytest.raises(ValueError, match="Unknown workload"):
            runner.run_scenario("s1-k8s-only", "invalid-workload")
