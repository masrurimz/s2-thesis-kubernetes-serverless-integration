"""Workload stage: run k6 ClarkNet trace replay and capture results.

Extracted from scripts/run_phase_b_experiments.py lines 830-932 (K6Runner).
Uses infra.k6 for the k6 binary path, but runs the specific ClarkNet trace replay
configuration with custom env vars and file-based output parsing.
"""

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Callable, Dict, Optional

import structlog
from shared.config import settings
from shared.models.calibration import get_calibration
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
    "smoke": "smoke_linear_k6_stages.json",
}
K6_STAGES = PROJECT_ROOT / "data" / "trace-replay" / _WORKLOAD_MAP.get(_WORKLOAD, "clarknet_k6_stages.json")

# Service endpoints
TARGET_URL = f"http://localhost:{settings.HAPROXY_HTTP_PORT}"


class WorkloadStage(BaseStage):
    """Run k6 ClarkNet trace replay and capture structured results.

    Executes k6 with scenario-specific env vars, waits for completion,
    and parses the handleSummary JSON output into WorkloadResult.
    """

    name = "workload"

    def _run(self, ctx: PipelineContext, on_progress: Callable[[str], None] | None = None) -> None:
        scenario = ctx.scenario
        run_id = ctx.run_id
        run_dir = Path(ctx.output_dir) if ctx.output_dir else Path(".")

        if _WORKLOAD not in _WORKLOAD_MAP:
            available = ", ".join(sorted(_WORKLOAD_MAP))
            raise ValueError(f"Unknown workload {_WORKLOAD!r}; available workloads: {available}")

        k6_summary = self._run_k6(scenario, run_id, run_dir, on_progress=on_progress)

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
            slo_violations=metrics.get("slo_violations", 0),
            app_duration_avg_ms=metrics.get("app_duration_avg_ms", 0.0),
            app_duration_p50_ms=metrics.get("app_duration_p50_ms", 0.0),
            app_duration_p95_ms=metrics.get("app_duration_p95_ms", 0.0),
            app_duration_serverless_avg_ms=metrics.get("app_duration_serverless_avg_ms", 0.0),
            app_duration_serverless_p95_ms=metrics.get("app_duration_serverless_p95_ms", 0.0),
            app_duration_k8s_avg_ms=metrics.get("app_duration_k8s_avg_ms", 0.0),
        )

    def _run_k6(
        self,
        scenario: str,
        run_id: int,
        results_dir: Path,
        on_progress: "Callable[[str], None] | None" = None,
    ) -> Optional[Dict]:
        """Execute k6 and return parsed metrics dict.

        Args:
            on_progress: Optional callback invoked with each k6 stderr progress line.
                         Use to update a spinner/progress bar description.
        """
        k6_results_dir = results_dir / "k6"
        # Keep summaries inside this run's k6 directory; use invocation time to
        # reject stale files left by an earlier run.
        t_start = time.time()
        k6_results_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            K6_PATH,
            "run",
            "--out",
            "json=/dev/null",  # disable verbose json streaming
            "-e",
            f"TARGET_URL={TARGET_URL}",
            "-e",
            f"ENDPOINT={get_calibration().endpoint}",
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

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(PROJECT_ROOT),
            bufsize=1,
        )

        # k6 writes its progress UI to stdout. If stdout is piped but not
        # drained, the child can block once the OS pipe fills and never exit.
        stdout_lines: list[str] = []
        stderr_lines: list[str] = []

        def _read_stream(stream: object, sink: list[str], report_progress: bool = False) -> None:
            for line in stream:  # type: ignore[operator]
                sink.append(line)
                if report_progress and on_progress:
                    stripped = line.strip()
                    if stripped:
                        on_progress(stripped)

        import threading

        readers = [
            threading.Thread(target=_read_stream, args=(proc.stdout, stdout_lines, True), daemon=True),
            threading.Thread(target=_read_stream, args=(proc.stderr, stderr_lines, False), daemon=True),
        ]
        for reader in readers:
            reader.start()

        try:
            proc.wait(timeout=3600)  # 60 min max (V1 death spiral causes slow k6 completion)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            for reader in readers:
                reader.join(timeout=5)
            logger.error("k6_timeout", scenario=scenario, run_id=run_id)
            return None

        for reader in readers:
            reader.join(timeout=5)
        stderr_text = "".join(stderr_lines)
        stdout_text = "".join(stdout_lines)

        # k6 exit code 99 = thresholds crossed (test completed, data valid)
        if proc.returncode not in (0, 99):
            logger.error(
                "k6_failed",
                returncode=proc.returncode,
                stderr=stderr_text[:500],
                stdout=stdout_text[:500],
            )
            return None
        if proc.returncode == 99:
            logger.warning("k6_threshold_crossed", scenario=scenario, run_id=run_id)

        # k6 handleSummary saves the detailed JSON to k6_results_dir
        k6_files = list(k6_results_dir.glob("clarknet_replay_*.json"))
        fresh_files = [path for path in k6_files if path.stat().st_mtime >= t_start]
        if len(fresh_files) != len(k6_files):
            logger.warning(
                "k6_stale_summaries_skipped",
                count=len(k6_files) - len(fresh_files),
                run_t_start=t_start,
            )
        if not fresh_files:
            logger.error("k6_no_output_file", dir=str(k6_results_dir), run_t_start=t_start)
            return None
        newest = max(fresh_files, key=lambda path: path.stat().st_mtime)

        try:
            with open(newest) as f:
                raw = json.load(f)
            summary = self._extract_metrics(raw, scenario, run_id)
            summary["k6_summary_path"] = str(newest)
            logger.info(
                "k6_complete",
                scenario=scenario,
                run_id=run_id,
                p99=summary.get("metrics", {}).get("p99_latency_ms"),
                total_requests=summary.get("metrics", {}).get("total_requests"),
            )
            return summary
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("k6_parse_failed", error=str(e), file=str(newest))
            return None

    @staticmethod
    def _extract_metrics(raw: Dict, scenario: str, run_id: int) -> Dict:
        """Extract structured metrics from raw k6 handleSummary JSON."""
        m = raw.get("metrics", {})
        dur = m.get("http_req_duration", {}).get("values", {})
        reqs = m.get("http_reqs", {}).get("values", {})
        slo = m.get("slo_violations", {}).get("values", {})
        failed = m.get("http_req_failed", {}).get("values", {})

        p99 = dur.get("p(99)")
        p95 = dur.get("p(95)") or 0
        if p99 is None:
            p99 = p95  # Fallback if k6 summaryTrendStats omits p(99)

        total_reqs = reqs.get("count") or 0
        failed_reqs = failed.get("fails", 0) if isinstance(failed, dict) else 0
        successful_reqs = total_reqs - failed_reqs
        slo_violations = slo.get("count") or 0

        return {
            "scenario": scenario,
            "run_id": run_id,
            "metrics": {
                "p50_latency_ms": dur.get("med") or 0,
                "p95_latency_ms": p95,
                "p99_latency_ms": p99,
                "avg_latency_ms": dur.get("avg") or 0,
                "max_latency_ms": dur.get("max") or 0,
                # Availability: did the request complete? (Google SRE availability SLI)
                "error_rate": failed.get("rate", 0),
                "total_requests": total_reqs,
                "failed_requests": failed_reqs,
                "successful_requests": successful_reqs,
                "actual_rps": reqs.get("rate") or 0,
                # SLO compliance: was a SUCCESSFUL request fast enough? (Google SRE latency SLI)
                "slo_violations": slo_violations,
                # Combined: any request that was either slow OR failed
                "total_errors": slo_violations + failed_reqs,
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
