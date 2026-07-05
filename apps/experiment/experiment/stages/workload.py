"""Workload stage: run k6 ClarkNet trace replay and capture results.

Extracted from scripts/run_phase_b_experiments.py lines 830-932 (K6Runner).
Uses infra.k6 for the k6 binary path, but runs the specific ClarkNet trace replay
configuration with custom env vars and file-based output parsing.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, Optional

import structlog

from shared.config import settings
from shared.models.pipeline import PipelineContext, WorkloadResult

from experiment.stages.base import BaseStage

logger = structlog.get_logger(__name__)

# Tool paths
K6_PATH = os.environ.get(
    "K6_PATH",
    str(Path.home() / ".local/share/mise/installs/k6/1.6.0/k6-v1.6.0-linux-amd64/k6"),
)

# Project paths — apps/experiment/experiment/stages/workload.py → 5 levels up to root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
K6_SCRIPT = PROJECT_ROOT / "apps" / "experiment" / "experiment" / "load_tests" / "canonical" / "clarknet_replay.js"
_WORKLOAD = os.environ.get("WORKLOAD", "clarknet")
_WORKLOAD_MAP = {
    "clarknet": "clarknet_k6_stages.json",
    "spike": "archetype_spike_k6_stages.json",
    "periodic": "archetype_periodic_k6_stages.json",
    "ramp": "archetype_ramp_k6_stages.json",
    "stationary": "archetype_stationary_k6_stages.json",
    "high_load": "archetype_high_load_k6_stages.json",
    "high_load_quick": "archetype_high_load_quick_k6_stages.json",
}
K6_STAGES = PROJECT_ROOT / "data" / "trace-replay" / _WORKLOAD_MAP.get(_WORKLOAD, "clarknet_k6_stages.json")

# Service endpoints
TARGET_URL = f"http://localhost:{settings.HAPROXY_HTTP_PORT}"
K6_ENDPOINT = "/fib?n=34"


class WorkloadStage(BaseStage):
    """Run k6 ClarkNet trace replay and capture structured results.

    Executes k6 with scenario-specific env vars, waits for completion,
    and parses the handleSummary JSON output into WorkloadResult.
    """

    name = "workload"

    def _run(self, ctx: PipelineContext) -> None:
        scenario = ctx.scenario
        run_id = ctx.run_id
        run_dir = Path(ctx.output_dir) if ctx.output_dir else Path(".")

        k6_summary = self._run_k6(scenario, run_id, run_dir)

        if k6_summary is None:
            ctx.workload = WorkloadResult(success=False)
            raise RuntimeError(f"k6 workload failed for {scenario} run {run_id}")

        metrics = k6_summary.get("metrics", {})
        ctx.workload = WorkloadResult(
            success=True,
            k6_summary_path=k6_summary.get("k6_summary_path", ""),
            total_requests=metrics.get("total_requests", 0),
            p50_latency_ms=metrics.get("p50_latency_ms", 0.0),
            p95_latency_ms=metrics.get("p95_latency_ms", 0.0),
            p99_latency_ms=metrics.get("p99_latency_ms", 0.0),
            error_rate=metrics.get("error_rate", 0.0),
            throughput_rps=metrics.get("actual_rps", 0.0),
        )

    def _run_k6(self, scenario: str, run_id: int, results_dir: Path) -> Optional[Dict]:
        """Execute k6 and return parsed metrics dict."""
        k6_results_dir = results_dir / "k6"
        k6_results_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            K6_PATH,
            "run",
            "--out",
            "json=/dev/null",  # disable verbose json streaming
            "-e",
            f"TARGET_URL={TARGET_URL}",
            "-e",
            f"ENDPOINT={K6_ENDPOINT}",
            "-e",
            f"SCENARIO={scenario}",
            "-e",
            f"RUN_ID={run_id}",
            "-e",
            f"RESULTS_DIR={k6_results_dir}",
            "-e",
            f"K6_STAGES_PATH={K6_STAGES}",
            str(K6_SCRIPT),
        ]

        logger.info("k6_start", scenario=scenario, run_id=run_id)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800,  # 30 min max
            cwd=str(PROJECT_ROOT),
        )

        # k6 exit code 99 = thresholds crossed (test completed, data valid)
        if result.returncode not in (0, 99):
            logger.error("k6_failed", returncode=result.returncode, stderr=result.stderr[:500])
            return None
        if result.returncode == 99:
            logger.warning("k6_threshold_crossed", scenario=scenario, run_id=run_id)

        # k6 handleSummary saves the detailed JSON to k6_results_dir
        k6_files = sorted(k6_results_dir.glob("clarknet_replay_*.json"))
        if not k6_files:
            logger.error("k6_no_output_file", dir=str(k6_results_dir))
            return None

        try:
            with open(k6_files[-1]) as f:
                raw = json.load(f)
            summary = self._extract_metrics(raw, scenario, run_id)
            summary["k6_summary_path"] = str(k6_files[-1])
            logger.info(
                "k6_complete",
                scenario=scenario,
                run_id=run_id,
                p99=summary.get("metrics", {}).get("p99_latency_ms"),
                total_requests=summary.get("metrics", {}).get("total_requests"),
            )
            return summary
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("k6_parse_failed", error=str(e), file=str(k6_files[-1]))
            return None

    @staticmethod
    def _extract_metrics(raw: Dict, scenario: str, run_id: int) -> Dict:
        """Extract structured metrics from raw k6 handleSummary JSON."""
        m = raw.get("metrics", {})
        dur = m.get("http_req_duration", {}).get("values", {})
        reqs = m.get("http_reqs", {}).get("values", {})
        errs = m.get("errors", {})
        slo = m.get("slo_violations", {}).get("values", {})

        p99 = dur.get("p(99)")
        p95 = dur.get("p(95)") or 0
        if p99 is None:
            p99 = p95  # k6 raw JSON may omit p99; fall back to p95

        return {
            "scenario": scenario,
            "run_id": run_id,
            "metrics": {
                "p50_latency_ms": dur.get("med") or 0,
                "p95_latency_ms": p95,
                "p99_latency_ms": p99,
                "avg_latency_ms": dur.get("avg") or 0,
                "max_latency_ms": dur.get("max") or 0,
                "error_rate": errs.get("rate", 0) if isinstance(errs, dict) else 0,
                "total_requests": reqs.get("count") or 0,
                "actual_rps": reqs.get("rate") or 0,
                "slo_violations": slo.get("count") or 0,
                "app_duration_avg_ms": m.get("app_duration_ms", {}).get("values", {}).get("avg") or 0,
                "app_duration_p50_ms": m.get("app_duration_ms", {}).get("values", {}).get("p(50)") or 0,
                "app_duration_p95_ms": m.get("app_duration_ms", {}).get("values", {}).get("p(95)") or 0,
                "app_duration_serverless_avg_ms": m.get("app_duration_serverless_ms", {}).get("values", {}).get("avg")
                or 0,
                "app_duration_serverless_p95_ms": m.get("app_duration_serverless_ms", {}).get("values", {}).get("p(95)")
                or 0,
                "app_duration_k8s_avg_ms": m.get("app_duration_k8s_ms", {}).get("values", {}).get("avg") or 0,
            },
        }
