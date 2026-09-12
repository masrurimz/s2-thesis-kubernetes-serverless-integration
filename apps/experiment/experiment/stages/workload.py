"""Workload stage: run k6 ClarkNet trace replay and capture results.

The k6 binary, the script, the stages file and the target URL are constructor
parameters resolved at construction time (environment first, then the defaults),
so a run can be pointed at a different trace or a stub binary without editing this
module. The parsed summary is a typed model, not a nested dict.
"""

import json
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import IO, Callable, Optional

import structlog
from pydantic import BaseModel, Field
from shared.config import settings
from shared.models.calibration import get_calibration
from shared.models.pipeline import PipelineContext, WorkloadResult

from experiment.stages.base import BaseStage

logger = structlog.get_logger(__name__)

DEFAULT_K6_PATH = str(Path.home() / ".local/share/mise/installs/k6/1.6.0/k6-v1.6.0-linux-amd64/k6")

# Project paths — apps/experiment/experiment/stages/workload.py → 5 levels up to root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
DEFAULT_K6_SCRIPT = (
    PROJECT_ROOT / "apps" / "experiment" / "experiment" / "load_tests" / "canonical" / "clarknet_replay.js"
)

WORKLOAD_STAGES = {
    "clarknet": "clarknet_k6_stages.json",
    "spike": "archetype_spike_k6_stages.json",
    "periodic": "archetype_periodic_k6_stages.json",
    "ramp": "archetype_ramp_k6_stages.json",
    "stationary": "archetype_stationary_k6_stages.json",
    "high_load": "archetype_high_load_k6_stages.json",
    "smoke": "smoke_linear_k6_stages.json",
}


def default_stages_path(workload: str | None = None) -> Path:
    """The stages file for a workload name, rejecting one that does not exist."""
    name = workload or os.environ.get("WORKLOAD", "clarknet")
    if name not in WORKLOAD_STAGES:
        available = ", ".join(sorted(WORKLOAD_STAGES))
        raise ValueError(f"Unknown workload {name!r}; available workloads: {available}")
    return PROJECT_ROOT / "data" / "trace-replay" / WORKLOAD_STAGES[name]


class K6RunMetrics(BaseModel):
    """The metrics one k6 run reported, in the units the analysis uses."""

    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    error_rate: float = 0.0
    total_requests: int = 0
    failed_requests: int = 0
    successful_requests: int = 0
    actual_rps: float = 0.0
    slo_violations: int = 0
    total_errors: int = 0
    app_duration_avg_ms: float = 0.0
    app_duration_p50_ms: float = 0.0
    app_duration_p95_ms: float = 0.0
    app_duration_serverless_avg_ms: float = 0.0
    app_duration_serverless_p95_ms: float = 0.0
    app_duration_k8s_avg_ms: float = 0.0


class K6Summary(BaseModel):
    """One run's k6 outcome: where the raw summary is and what it reported."""

    scenario: str
    run_id: int
    k6_summary_path: str = ""
    metrics: K6RunMetrics = Field(default_factory=K6RunMetrics)

    @classmethod
    def from_handle_summary(cls, raw: dict, scenario: str, run_id: int, summary_path: str = "") -> "K6Summary":
        """Read a k6 ``handleSummary`` document into the model.

        A summary that omits p(99) reports the p95 in its place: k6's summaryTrendStats
        does not always carry it, and a run without a tail number would otherwise be
        read as a zero tail.
        """
        m = raw.get("metrics", {}) or {}
        dur = (m.get("http_req_duration", {}) or {}).get("values", {}) or {}
        reqs = (m.get("http_reqs", {}) or {}).get("values", {}) or {}
        slo = (m.get("slo_violations", {}) or {}).get("values", {}) or {}
        failed = (m.get("http_req_failed", {}) or {}).get("values", {}) or {}

        p95 = dur.get("p(95)") or 0
        p99 = dur.get("p(99)")
        if p99 is None:
            p99 = p95

        total_requests = reqs.get("count") or 0
        failed_requests = failed.get("fails", 0) or 0
        slo_violations = slo.get("count") or 0

        def app(metric: str, stat: str) -> float:
            return ((m.get(metric, {}) or {}).get("values", {}) or {}).get(stat) or 0

        return cls(
            scenario=scenario,
            run_id=run_id,
            k6_summary_path=summary_path,
            metrics=K6RunMetrics(
                p50_latency_ms=dur.get("med") or 0,
                p95_latency_ms=p95,
                p99_latency_ms=p99,
                avg_latency_ms=dur.get("avg") or 0,
                max_latency_ms=dur.get("max") or 0,
                error_rate=failed.get("rate", 0) or 0,
                total_requests=total_requests,
                failed_requests=failed_requests,
                successful_requests=total_requests - failed_requests,
                actual_rps=reqs.get("rate") or 0,
                slo_violations=slo_violations,
                total_errors=slo_violations + failed_requests,
                app_duration_avg_ms=app("app_duration_ms", "avg"),
                app_duration_p50_ms=app("app_duration_ms", "p(50)"),
                app_duration_p95_ms=app("app_duration_ms", "p(95)"),
                app_duration_serverless_avg_ms=app("app_duration_serverless_ms", "avg"),
                app_duration_serverless_p95_ms=app("app_duration_serverless_ms", "p(95)"),
                app_duration_k8s_avg_ms=app("app_duration_k8s_ms", "avg"),
            ),
        )


class WorkloadStage(BaseStage):
    """Run k6 ClarkNet trace replay and capture structured results.

    Executes k6 with scenario-specific env vars, waits for completion,
    and parses the handleSummary JSON output into WorkloadResult.
    """

    name = "workload"

    def __init__(
        self,
        k6_path: str | Path | None = None,
        k6_script: Path | None = None,
        k6_stages: Path | None = None,
        target_url: str | None = None,
    ) -> None:
        self.k6_path = str(k6_path or os.environ.get("K6_PATH") or DEFAULT_K6_PATH)
        self.k6_script = Path(k6_script or DEFAULT_K6_SCRIPT)
        self.k6_stages = Path(k6_stages) if k6_stages is not None else default_stages_path()
        self.target_url = target_url or f"http://localhost:{settings.HAPROXY_HTTP_PORT}"

    def _run(self, ctx: PipelineContext, on_progress: Callable[[str], None] | None = None) -> None:
        scenario = ctx.scenario
        run_id = ctx.run_id
        run_dir = Path(ctx.output_dir) if ctx.output_dir else Path(".")

        k6_summary = self._run_k6(scenario, run_id, run_dir, on_progress=on_progress)

        if k6_summary is None:
            ctx.workload = WorkloadResult(success=False)
            raise RuntimeError(f"k6 workload failed for {scenario} run {run_id}")

        metrics = k6_summary.metrics
        ctx.workload = WorkloadResult(
            success=True,
            k6_summary_path=k6_summary.k6_summary_path,
            total_requests=metrics.total_requests,
            p50_latency_ms=metrics.p50_latency_ms,
            p95_latency_ms=metrics.p95_latency_ms,
            p99_latency_ms=metrics.p99_latency_ms,
            error_rate=metrics.error_rate,
            throughput_rps=metrics.actual_rps,
            slo_violations=metrics.slo_violations,
            app_duration_avg_ms=metrics.app_duration_avg_ms,
            app_duration_p50_ms=metrics.app_duration_p50_ms,
            app_duration_p95_ms=metrics.app_duration_p95_ms,
            app_duration_serverless_avg_ms=metrics.app_duration_serverless_avg_ms,
            app_duration_serverless_p95_ms=metrics.app_duration_serverless_p95_ms,
            app_duration_k8s_avg_ms=metrics.app_duration_k8s_avg_ms,
        )

    def _run_k6(
        self,
        scenario: str,
        run_id: int,
        results_dir: Path,
        on_progress: "Callable[[str], None] | None" = None,
    ) -> Optional[K6Summary]:
        """Execute k6 and return the parsed summary.

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
            self.k6_path,
            "run",
            "--out",
            "json=/dev/null",  # disable verbose json streaming
            "-e",
            f"TARGET_URL={self.target_url}",
            "-e",
            f"ENDPOINT={get_calibration().endpoint}",
            "-e",
            f"SCENARIO={scenario}",
            "-e",
            f"RUN_ID={run_id}",
            "-e",
            f"RESULTS_DIR={k6_results_dir}",
            "-e",
            f"K6_STAGES_PATH={self.k6_stages}",
            str(self.k6_script),
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

        def _read_stream(stream: Optional[IO[str]], sink: list[str], report_progress: bool = False) -> None:
            if stream is None:  # subprocess.PIPE implies both, but the types are optional
                return
            for line in stream:
                sink.append(line)
                if report_progress and on_progress:
                    stripped = line.strip()
                    if stripped:
                        on_progress(stripped)

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

        # k6 exit code 99 = thresholds crossed (test completed, data valid)
        if proc.returncode not in (0, 99):
            logger.error(
                "k6_failed",
                returncode=proc.returncode,
                stderr=stderr_text[-500:],
            )
            return None

        # Find the summary file written by this invocation (ignore older runs).
        fresh_files = [
            path
            for path in k6_results_dir.glob("*.json")
            if path.stat().st_mtime >= t_start and not path.name.endswith("_metadata.json")
        ]
        if not fresh_files:
            logger.error("k6_no_output_file", dir=str(k6_results_dir), run_t_start=t_start)
            return None
        newest = max(fresh_files, key=lambda path: path.stat().st_mtime)

        try:
            with open(newest) as f:
                raw = json.load(f)
            summary = K6Summary.from_handle_summary(raw, scenario, run_id, summary_path=str(newest))
            logger.info(
                "k6_complete",
                scenario=scenario,
                run_id=run_id,
                p99=summary.metrics.p99_latency_ms,
                total_requests=summary.metrics.total_requests,
            )
            return summary
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error("k6_parse_failed", error=str(e), file=str(newest))
            return None
