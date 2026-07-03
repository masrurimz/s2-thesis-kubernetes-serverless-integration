#!/usr/bin/env python3
"""
Experiment runner for thesis evaluation scenarios.
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Optional, List, Dict
import yaml
import structlog

from .experiment_logger import ExperimentLogger

logger = structlog.get_logger(__name__)


class ExperimentRunner:
    """Runs experiments across scenarios and workloads."""

    SCENARIOS = [
        "s1-k8s-only",
        "s2-serverless-only",
        "s3-hybrid-reactive",
        "s4-hybrid-predictive",
    ]
    WORKLOADS = ["steady", "spike", "endurance"]

    def __init__(self, db_path: str = "experiments/experiments.db"):
        self.logger = ExperimentLogger(db_path)
        self.results_dir = Path("results")
        self.scenarios_dir = Path("experiments/scenarios")

    def _load_scenario_config(self, scenario: str) -> Dict:
        """Load scenario configuration from YAML file."""
        config_path = self.scenarios_dir / scenario / "config.yaml"
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        return {}

    def _load_workload_config(self, workload: str) -> Dict:
        """Load workload configuration from YAML file."""
        config_path = Path("experiments/workloads") / f"{workload}.yaml"
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        return {}

    def run_scenario(
        self,
        scenario: str,
        workload: str,
        dataset: str = None,
        repetition: int = 1,
        dry_run: bool = False,
    ) -> int:
        """Run a single scenario experiment."""
        if scenario not in self.SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario}")
        if workload not in self.WORKLOADS:
            raise ValueError(f"Unknown workload: {workload}")

        scenario_config = self._load_scenario_config(scenario)
        workload_config = self._load_workload_config(workload)

        config = {
            "scenario": scenario_config,
            "workload": workload_config,
            "repetition": repetition,
            "dry_run": dry_run,
        }

        run_id = self.logger.start_run(scenario, workload, dataset, config)

        try:
            if dry_run:
                logger.info(
                    "Dry run - skipping actual execution",
                    scenario=scenario,
                    workload=workload,
                    run_id=run_id,
                )
                self.logger.log_metrics(
                    run_id,
                    {
                        "latency_p50_ms": 0.0,
                        "latency_p95_ms": 0.0,
                        "latency_p99_ms": 0.0,
                        "throughput_rps": 0.0,
                        "error_rate": 0.0,
                        "cost_normalized": 0.0,
                    },
                )
            else:
                # TODO: Implement actual scenario execution
                # 1. Setup infrastructure per scenario
                # 2. Start load generation per workload
                # 3. Collect metrics from Prometheus
                # 4. Store results
                logger.info(
                    "Scenario execution placeholder",
                    scenario=scenario,
                    workload=workload,
                    run_id=run_id,
                )

            self.logger.end_run(run_id, status="completed")

        except Exception as e:
            logger.error("Scenario failed", error=str(e))
            self.logger.end_run(run_id, status="failed", notes=str(e))
            raise

        return run_id

    def run_all(
        self,
        repetitions: int = 3,
        scenarios: List[str] = None,
        workloads: List[str] = None,
        dry_run: bool = False,
    ) -> List[int]:
        """Run full experiment matrix."""
        run_ids = []
        scenarios = scenarios or self.SCENARIOS
        workloads = workloads or self.WORKLOADS

        for scenario in scenarios:
            for workload in workloads:
                for rep in range(1, repetitions + 1):
                    logger.info(
                        "Running experiment",
                        scenario=scenario,
                        workload=workload,
                        repetition=rep,
                        total_repetitions=repetitions,
                    )
                    run_id = self.run_scenario(
                        scenario, workload, repetition=rep, dry_run=dry_run
                    )
                    run_ids.append(run_id)

        return run_ids

    def generate_summary(self) -> Dict:
        """Generate summary of all completed experiments."""
        summary = {}
        for scenario in self.SCENARIOS:
            scenario_summary = self.logger.get_scenario_summary(scenario)
            if scenario_summary:
                summary[scenario] = scenario_summary

        return summary

    def export_all_runs(self, output_dir: str = "results/raw") -> List[str]:
        """Export all completed runs to JSON files."""
        runs = self.logger.list_runs(status="completed")
        exported = []
        for run in runs:
            path = self.logger.export_run_to_json(
                run["id"], f"{output_dir}/run_{run['id']}.json"
            )
            exported.append(path)
        return exported
