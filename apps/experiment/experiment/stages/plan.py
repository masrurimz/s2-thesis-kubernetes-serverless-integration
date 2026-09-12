"""Plan stage: generate run order, seeds, and batch manifest.

Extracted from scripts/run_phase_b_experiments.py lines 1814-1854
(ExperimentRunner.run_replicated schedule generation).
"""

import json
import random
from datetime import datetime
from pathlib import Path

import structlog
from shared.models.experiment import BatchManifest, RunManifest
from shared.models.pipeline import PipelineContext

from experiment.stages.base import BaseStage

logger = structlog.get_logger(__name__)

SCENARIOS = [
    "s1-k8s-only",
    "s2-serverless-only",
    "s3-hybrid-reactive",
    "s4-hybrid-predictive",
]


def _git_commit_hash() -> str:
    try:
        result = __import__("subprocess").run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


class PlanStage(BaseStage):
    """Generate the experiment run order, seeds, and batch manifest.

    Reads ctx.config to determine scenarios and runs.
    Writes the batch manifest to ctx.manifest and the run schedule
    to the output directory.
    """

    name = "plan"

    def _run(self, ctx: PipelineContext) -> None:
        config = ctx.config
        scenarios = SCENARIOS  # Use canonical list
        num_runs = config.runs
        seed = config.seed

        # Generate randomized schedule
        schedule = [(s, r) for s in scenarios for r in range(1, num_runs + 1)]
        rng = random.Random(seed)
        rng.shuffle(schedule)

        # Create batch manifest
        BatchManifest(
            batch_id=f"batch-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            date=datetime.now().strftime("%Y-%m-%d"),
            phase=config.phase,
            scenarios=scenarios,
            workload={
                "type": "clarknet_trace_replay",
                "endpoint": "/fib?n=34",
                "duration_sec": config.duration_sec,
            },
            runs_per_scenario=num_runs,
            git_commit=_git_commit_hash(),
            timestamp=datetime.now().isoformat(),
        )

        # Save schedule to output dir
        output_dir = Path(ctx.output_dir) if ctx.output_dir else Path(".")
        output_dir.mkdir(parents=True, exist_ok=True)
        schedule_doc = {
            "seed": seed,
            "num_runs": num_runs,
            "scenarios": scenarios,
            "order": [{"scenario": s, "run_id": r, "idx": i} for i, (s, r) in enumerate(schedule)],
            "timestamp": datetime.now().isoformat(),
        }
        with open(output_dir / "experiment_schedule.json", "w") as f:
            json.dump(schedule_doc, f, indent=2)

        logger.info("experiment_schedule", total=len(schedule), seed=seed)

        # Store manifest on context
        ctx.manifest = RunManifest(
            scenario=ctx.scenario,
            run_id=ctx.run_id,
            run_order_idx=0,
            random_seed=seed,
            git_commit=_git_commit_hash(),
            k6_script=str(schedule_doc.get("k6_script", "")),
            k6_stages_json=str(schedule_doc.get("k6_stages_json", "")),
            replay_manifest=config.replay_manifest,
            daemon_config=config.daemon_config,
            scaling_config=config.scaling_config,
            timestamp=datetime.now().isoformat(),
        )
