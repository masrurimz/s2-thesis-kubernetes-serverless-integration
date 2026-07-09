"""Controller parameter optimization using Optuna TPE.

Two-stage approach (oracle-reviewed):
  Stage 1: Screening — 8-10 single-run trials to identify promising regions
  Stage 2: Confirmation — top 3 candidates re-run with n=3 for stability

Search space (4 highest-impact knobs):
  - proactive_trend_threshold: [1.0, 10.0]
  - proactive_approach_ratio: [0.3, 0.9]
  - kp_burn: [0.1, 2.0]
  - target_cpu_util: [0.3, 0.9]

Objective: minimize SLO violations subject to p99 <= 500ms and cost guardrail.
Config injection: write trial params to JSON artifact, not source mutation.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List

import optuna
import structlog

logger = structlog.get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
TRIALS_DIR = PROJECT_ROOT / "results" / "experiments" / "tuning" / "trials"


def write_trial_config(trial_id: str, params: Dict) -> Path:
    """Write controller trial parameters to a JSON artifact.

    The experiment runner reads this file to override CalibrationConfig.
    """
    TRIALS_DIR.mkdir(parents=True, exist_ok=True)
    trial_dir = TRIALS_DIR / trial_id
    trial_dir.mkdir(exist_ok=True)
    config_path = trial_dir / "config.json"

    with open(config_path, "w") as f:
        json.dump(
            {
                "trial_id": trial_id,
                "params": params,
                "timestamp": datetime.now().isoformat(),
            },
            f,
            indent=2,
        )

    return config_path


def read_trial_result(trial_id: str) -> Dict:
    """Read experiment results for a completed trial."""
    trial_dir = TRIALS_DIR / trial_id

    # Look for result.json in the experiment output
    for result_path in trial_dir.rglob("result.json"):
        with open(result_path) as f:
            return json.load(f)

    return {}


def run_single_experiment(
    config_path: Path,
    scenario: str = "s4-hybrid-predictive",
    output_dir: str | None = None,
) -> Dict:
    """Run a single experiment with the given controller config.

    Sets CALIBRATION_OVERRIDE env var pointing to the config JSON.
    The experiment runner reads this to override CalibrationConfig defaults.
    """
    output_dir = output_dir or str(config_path.parent / "experiment")

    env = os.environ.copy()
    env["CALIBRATION_OVERRIDE"] = str(config_path)

    cmd = [
        str(Path(PROJECT_ROOT) / ".venv" / "bin" / "thesis-experiment"),
        "run",
        "--runs",
        "1",
        "--scenarios",
        scenario,
        "--output",
        output_dir,
    ]

    logger.info("running_experiment", cmd=" ".join(cmd), config=str(config_path))

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env,
        timeout=3600,  # 1 hour max per run
    )

    if result.returncode != 0:
        logger.error("experiment_failed", returncode=result.returncode, stderr=result.stderr[-500:])

    # Read results
    output_path = Path(output_dir)
    for result_file in output_path.rglob("result.json"):
        with open(result_file) as f:
            return json.load(f)

    return {"error": "No result.json found", "returncode": result.returncode}


def create_controller_objective(scenario: str = "s4-hybrid-predictive") -> Callable:
    """Return Optuna objective function for controller HPO.

    Objective: minimize SLO violations + penalty for p99 > 500ms + cost guardrail.
    """

    def objective(trial: optuna.Trial) -> float:
        # Suggest 4 highest-impact parameters
        params = {
            "proactive_trend_threshold": trial.suggest_float("proactive_trend_threshold", 1.0, 10.0),
            "proactive_approach_ratio": trial.suggest_float("proactive_approach_ratio", 0.3, 0.9),
            "kp_burn": trial.suggest_float("kp_burn", 0.1, 2.0),
            "target_cpu_util": trial.suggest_float("target_cpu_util", 0.3, 0.9),
        }

        trial_id = f"ctrl_trial_{trial.number:03d}"
        config_path = write_trial_config(trial_id, params)

        result = run_single_experiment(config_path, scenario=scenario)

        slo = result.get("slo_violations_k6", 10000)
        p99 = result.get("p99_latency_ms", 1000)

        # Cost-aware objective: penalize p99 > 500ms
        penalty = max(0, (p99 - 500) * 10)

        objective_value = slo + penalty
        logger.info(
            "controller_trial",
            trial=trial.number,
            slo=slo,
            p99=round(p99, 1),
            penalty=penalty,
            objective=round(objective_value, 1),
            params=params,
        )

        return objective_value

    return objective


def run_controller_screening(n_trials: int = 10, scenario: str = "s4-hybrid-predictive") -> List[Dict]:
    """Stage 1: Quick screening to identify promising parameter regions.

    Each trial is a single experiment run (~20 min).
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    study_name = f"controller_screening_{timestamp}"

    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=42),
        study_name=study_name,
        storage=f"sqlite:///{TRIALS_DIR / 'screening.db'}",
    )

    objective = create_controller_objective(scenario)
    study.optimize(objective, n_trials=n_trials)

    # Sort trials by objective value
    completed = [
        {
            "number": t.number,
            "params": t.params,
            "objective": t.value if t.value else float("inf"),
        }
        for t in study.trials
        if t.state == optuna.trial.TrialState.COMPLETE
    ]
    completed.sort(key=lambda x: x["objective"])

    logger.info(
        "screening_complete",
        n_completed=len(completed),
        best_trial=completed[0]["number"] if completed else None,
        best_objective=completed[0]["objective"] if completed else None,
    )

    return completed


def run_controller_confirmation(
    top_trials: List[Dict],
    n_runs: int = 3,
    scenario: str = "s4-hybrid-predictive",
) -> Dict:
    """Stage 2: Re-run top candidates with n=3 for statistical stability.

    Args:
        top_trials: Top screening results (recommend top 3).
        n_runs: Number of runs per candidate.

    Returns:
        Dict with per-candidate mean SLO, p99, and recommendation.
    """
    confirmations = []

    for trial in top_trials[:3]:  # Top 3 only
        trial_id = f"ctrl_confirm_{trial['number']:03d}"
        params = trial["params"]
        config_path = write_trial_config(trial_id, params)

        # Run n=3 experiments
        results = []
        for run in range(n_runs):
            run_id = f"{trial_id}_run{run + 1}"
            run_output = str(TRIALS_DIR / run_id)
            result = run_single_experiment(config_path, scenario=scenario, output_dir=run_output)
            results.append(result)

        # Compute statistics
        slo_values = [r.get("slo_violations_k6", 10000) for r in results]
        p99_values = [r.get("p99_latency_ms", 1000) for r in results]

        import numpy as np

        confirmation = {
            "trial_number": trial["number"],
            "params": params,
            "n_runs": n_runs,
            "mean_slo": float(np.mean(slo_values)),
            "std_slo": float(np.std(slo_values)),
            "mean_p99": float(np.mean(p99_values)),
            "std_p99": float(np.std(p99_values)),
            "all_slo": slo_values,
            "all_p99": p99_values,
        }
        confirmations.append(confirmation)

        logger.info(
            "confirmation_result",
            trial=trial["number"],
            mean_slo=confirmation["mean_slo"],
            mean_p99=round(confirmation["mean_p99"], 1),
        )

    # Select winner: lowest mean SLO with p99 < 200ms
    eligible = [c for c in confirmations if c["mean_p99"] < 200]
    winner = min(eligible, key=lambda x: x["mean_slo"]) if eligible else None

    return {
        "confirmations": confirmations,
        "winner": winner,
        "timestamp": datetime.now().isoformat(),
    }
