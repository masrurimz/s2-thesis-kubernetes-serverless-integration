"""Phase C: dynamic ramp/burst workload experiment (S3 vs S4).

Steady 100 RPS never triggered PREDICTIVE in Phase B. This runner uses a
dynamic ramp/burst workload (load_tests/canonical/dynamic_burst.js) that
creates repeated "healthy -> surge" windows, giving the GRU predictor a fair
chance to fire. Runs S3 (reactive) and S4 (predictive) with replicated runs
in randomized order, recording k6 latency/error metrics and daemon
decision-count deltas.

Ported from scripts/run_dynamic_experiment.py. This is a standalone CLI
workflow (not a pipeline Stage). Entry point: run_dynamic_experiment().
"""

from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
import structlog
from shared.config import settings

from experiment.stages.daemon import kill_process_on_port

logger = structlog.get_logger(__name__)

# apps/experiment/experiment/dynamic.py -> 4 levels up to repo root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
K6_SCRIPT = Path(__file__).resolve().parent / "load_tests" / "canonical" / "dynamic_burst.js"
RESULTS_BASE = PROJECT_ROOT / "results" / "experiments" / "phase-c"

DAEMON_API = f"http://localhost:{settings.DAEMON_API_PORT}"
PROMETHEUS_URL = settings.PROMETHEUS_URL
GRU_URL = settings.GRU_SERVICE_URL
HAPROXY_URL = f"http://localhost:{settings.HAPROXY_HTTP_PORT}"

# k6 binary path (mirrors experiment.stages.workload)
K6_PATH = os.environ.get(
    "K6_PATH",
    str(Path.home() / ".local/share/mise/installs/k6/1.6.0/k6-v1.6.0-linux-amd64/k6"),
)


@dataclass
class DynamicExperimentResult:
    """Single experiment run result."""

    scenario: str
    run_id: int
    workload: str
    duration_sec: int

    # Primary metrics (from k6 summary)
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate: float
    throughput_rps: float
    total_requests: int
    slo_violations: int

    # Decision counts (from daemon /status)
    maintain_count: int
    scale_out_count: int
    predictive_count: int
    optimize_cost_count: int

    # GRU metrics (S4 only)
    gru_predictions_used: int
    gru_avg_confidence: float

    timestamp: str


def set_scenario(scenario: str, daemon_api: str = DAEMON_API) -> bool:
    """Set the daemon's active scenario via its HTTP API (daemon must be running)."""
    try:
        resp = requests.post(f"{daemon_api}/set_scenario", json={"scenario": scenario}, timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def extract_decision_counts(pre: Optional[Dict], post: Optional[Dict]) -> Dict:
    """Compute decision-count deltas between pre/post daemon status snapshots."""
    if not post:
        return {}

    def get_count(status: Optional[Dict], key: str) -> int:
        if not status:
            return 0
        # Daemon may nest under "decision_counts" or at top level
        counts = status.get("decision_counts", status)
        return counts.get(key, 0)

    pre_counts = {
        "maintain": get_count(pre, "maintain_count"),
        "scale_out": get_count(pre, "scale_out_count"),
        "predictive": get_count(pre, "predictive_count"),
        "optimize_cost": get_count(pre, "optimize_cost_count"),
    }

    post_counts = {
        "maintain": get_count(post, "maintain_count"),
        "scale_out": get_count(post, "scale_out_count"),
        "predictive": get_count(post, "predictive_count"),
        "optimize_cost": get_count(post, "optimize_cost_count"),
    }

    return {k: post_counts[k] - pre_counts.get(k, 0) for k in post_counts}


class DynamicExperimentRunner:
    """Runs Phase C dynamic workload experiments."""

    def __init__(
        self,
        results_dir: Optional[Path] = None,
        cooldown_sec: int = 30,
    ):
        today = datetime.now().strftime("%Y-%m-%d")
        self.results_dir = results_dir or RESULTS_BASE / f"{today}_dynamic-workload"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.cooldown_sec = cooldown_sec

    # -- Infrastructure checks --------------------------------------------

    def check_infrastructure(self, scenario: str, skip_daemon: bool = False) -> bool:
        """Check all required services are running."""
        endpoints = {
            "haproxy": f"{HAPROXY_URL}/fib?n=33",
            "prometheus": f"{PROMETHEUS_URL}/-/healthy",
        }

        if not skip_daemon and scenario in ("s3-hybrid-reactive", "s4-hybrid-predictive"):
            endpoints["daemon"] = f"{DAEMON_API}/health"

        if scenario == "s4-hybrid-predictive":
            endpoints["gru"] = f"{GRU_URL}/health"

        checks = {}
        for name, url in endpoints.items():
            try:
                resp = requests.get(url, timeout=5)
                checks[name] = resp.status_code == 200
            except Exception:
                checks[name] = False

        all_ok = all(checks.values())
        if not all_ok:
            logger.error("infrastructure_not_ready", **checks)
        else:
            logger.info("infrastructure_ready", **checks)

        return all_ok

    # -- Daemon lifecycle -------------------------------------------------

    def start_daemon(self, scenario: str) -> Optional[subprocess.Popen]:
        """Start routing daemon for scenario."""
        cmd = [
            sys.executable,
            "-m",
            "routing.daemon.cli",
            "--scenario",
            scenario,
            "--haproxy-host",
            settings.HAPROXY_HOST,
            "--haproxy-port",
            str(settings.HAPROXY_SOCKET_PORT),
            "--haproxy-stats",
            settings.HAPROXY_STATS_URL,
            "--gru-url",
            GRU_URL,
            "--interval",
            "15",
            "--api-port",
            str(settings.DAEMON_API_PORT),
        ]

        env = {
            **os.environ,
            "HSA_OVERRIDE_GFX_VERSION": "11.0.0",
            "PREDICTION_CONFIDENCE_THRESHOLD": "0.6",
        }

        kill_process_on_port(settings.DAEMON_API_PORT, "routing_daemon")

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_ROOT),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            time.sleep(5)

            resp = requests.get(f"{DAEMON_API}/health", timeout=5)
            if resp.status_code == 200:
                # Require a fresh daemon running the requested scenario.
                status_resp = requests.get(f"{DAEMON_API}/status", timeout=5)
                status = status_resp.json() if status_resp.status_code == 200 else {}
                if status.get("uptime_seconds", 999) > 30 or status.get("scenario") != scenario:
                    logger.error(
                        "daemon_status_invalid",
                        scenario=scenario,
                        status_scenario=status.get("scenario"),
                        uptime_seconds=status.get("uptime_seconds"),
                    )
                    proc.terminate()
                    proc.wait()
                    return None
                logger.info("daemon_started", scenario=scenario, pid=proc.pid)
                return proc
            else:
                logger.error("daemon_health_failed", scenario=scenario)
                proc.terminate()
                proc.wait()
                return None
        except Exception as e:
            logger.error("daemon_start_error", error=str(e))
            return None

    def stop_daemon(self, proc: subprocess.Popen) -> None:
        """Stop routing daemon."""
        if proc:
            proc.terminate()
            proc.wait()
            time.sleep(3)
            logger.info("daemon_stopped", pid=proc.pid)

    def set_scenario(self, scenario: str) -> bool:
        """Set scenario via daemon API (delegates to module-level set_scenario)."""
        return set_scenario(scenario)

    def get_daemon_status(self) -> Optional[Dict]:
        """Get daemon status including decision counts."""
        try:
            resp = requests.get(f"{DAEMON_API}/status", timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None

    # -- k6 load test -----------------------------------------------------

    def run_k6_load_test(self, scenario: str, run_id: int, run_results_dir: Path) -> Optional[Dict]:
        """Run k6 dynamic_burst.js and parse summary output."""
        run_results_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            K6_PATH,
            "run",
            str(K6_SCRIPT),
            "-e",
            f"TARGET_URL={HAPROXY_URL}",
            "-e",
            f"BASE_URL={HAPROXY_URL}",
            "-e",
            f"SCENARIO={scenario}",
            "-e",
            f"RUN_ID={run_id}",
            "-e",
            f"RESULTS_DIR={run_results_dir}",
            "--out",
            # The per-request stream is not an artifact: nothing reads it, and at a
            # /fib?n=33 workload it is 160 MB of NDJSON per run (2.9 MB as zstd Parquet).
            # The paired pipeline already discards it the same way. If a future analysis
            # needs per-request samples, write them as Parquet, not as this stream.
            "json=/dev/null",
            "--summary-export",
            str(run_results_dir / "k6-summary.json"),
        ]

        logger.info("running_k6", scenario=scenario, run_id=run_id)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 min max
            )

            # Save full output
            (run_results_dir / "k6-stdout.txt").write_text(result.stdout)
            (run_results_dir / "k6-stderr.txt").write_text(result.stderr)

            # Parse summary JSON
            summary_path = run_results_dir / "k6-summary.json"
            if summary_path.exists():
                with open(summary_path) as f:
                    return json.load(f)

            # Fallback: parse stdout JSON (handleSummary writes to stdout)
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                logger.warning("k6_stdout_not_json", scenario=scenario, run_id=run_id)
                return None

        except subprocess.TimeoutExpired:
            logger.error("k6_timeout", scenario=scenario, run_id=run_id)
            return None
        except Exception as e:
            logger.error("k6_error", error=str(e))
            return None

    # -- Single experiment ------------------------------------------------

    def run_single_experiment(
        self, scenario: str, run_id: int, manage_daemon: bool = True
    ) -> Optional[DynamicExperimentResult]:
        """Run a single experiment: start daemon -> k6 -> collect metrics -> stop daemon."""

        logger.info(
            "experiment_start",
            scenario=scenario,
            run_id=run_id,
        )

        daemon_proc = None
        if manage_daemon:
            daemon_proc = self.start_daemon(scenario)
            if not daemon_proc:
                return None
        else:
            if not self.set_scenario(scenario):
                logger.error("set_scenario_failed", scenario=scenario)
                return None

        try:
            # Record pre-test daemon state
            pre_status = self.get_daemon_status()

            # Run k6 load test
            run_dir = self.results_dir / "raw" / f"{scenario}_run{run_id}"
            k6_summary = self.run_k6_load_test(scenario, run_id, run_dir)

            # Record post-test daemon state
            post_status = self.get_daemon_status()

            # Save daemon states
            if pre_status:
                (run_dir / "daemon-pre.json").write_text(json.dumps(pre_status, indent=2))
            if post_status:
                (run_dir / "daemon-post.json").write_text(json.dumps(post_status, indent=2))

            # Extract metrics from k6 summary
            metrics = self._extract_k6_metrics(k6_summary)

            # Extract decision counts from daemon
            decisions = self._extract_decision_counts(pre_status, post_status)

            result = DynamicExperimentResult(
                scenario=scenario,
                run_id=run_id,
                workload="dynamic_burst",
                duration_sec=360,
                p50_latency_ms=metrics.get("p50", 0.0),
                p95_latency_ms=metrics.get("p95", 0.0),
                p99_latency_ms=metrics.get("p99", 0.0),
                error_rate=metrics.get("error_rate", 0.0),
                throughput_rps=metrics.get("rps", 0.0),
                total_requests=metrics.get("total_requests", 0),
                slo_violations=metrics.get("slo_violations", 0),
                maintain_count=decisions.get("maintain", 0),
                scale_out_count=decisions.get("scale_out", 0),
                predictive_count=decisions.get("predictive", 0),
                optimize_cost_count=decisions.get("optimize_cost", 0),
                gru_predictions_used=decisions.get("gru_predictions_used", 0),
                gru_avg_confidence=decisions.get("gru_avg_confidence", 0.0),
                timestamp=datetime.now().isoformat(),
            )

            logger.info(
                "experiment_complete",
                scenario=scenario,
                run_id=run_id,
                p99=result.p99_latency_ms,
                predictive_count=result.predictive_count,
                error_rate=result.error_rate,
            )

            return result

        finally:
            if manage_daemon and daemon_proc:
                self.stop_daemon(daemon_proc)

    # -- Metric extraction ------------------------------------------------

    def _extract_k6_metrics(self, summary: Optional[Dict]) -> Dict:
        """Extract relevant metrics from k6 summary JSON."""
        if not summary:
            return {}

        req_dur = summary.get("metrics", {}).get("http_req_duration", {})
        reqs = summary.get("metrics", {}).get("http_reqs", {})
        errors = summary.get("metrics", {}).get("errors", {})
        slo = summary.get("metrics", {}).get("slo_violations", {})

        # k6 summary export uses "values" key
        dur_vals = req_dur.get("values", req_dur)
        req_vals = reqs.get("values", reqs)

        return {
            "p50": dur_vals.get("p(50)", 0.0),
            "p95": dur_vals.get("p(95)", 0.0),
            "p99": dur_vals.get("p(99)", 0.0),
            "error_rate": errors.get("values", errors).get("rate", 0.0),
            "rps": req_vals.get("rate", 0.0),
            "total_requests": req_vals.get("count", 0),
            "slo_violations": slo.get("values", slo).get("count", 0),
        }

    def _extract_decision_counts(self, pre: Optional[Dict], post: Optional[Dict]) -> Dict:
        """Decision-count deltas (delegates to module-level extract_decision_counts)."""
        return extract_decision_counts(pre, post)

    # -- Full experiment suite --------------------------------------------

    def run_all(
        self,
        scenarios: List[str],
        num_runs: int,
        manage_daemon: bool = True,
    ) -> List[DynamicExperimentResult]:
        """Run replicated experiments with randomized order."""
        from rich.console import Console
        from shared.progress import (
            countdown,
            create_progress,
            elapsed_str,
            print_run_failure,
            print_run_header,
        )

        console = Console()

        # Build and shuffle schedule
        schedule = [(scenario, run_id) for scenario in scenarios for run_id in range(1, num_runs + 1)]
        random.shuffle(schedule)

        logger.info(
            "experiment_schedule",
            total=len(schedule),
            schedule=[f"{s}-run{r}" for s, r in schedule],
        )

        results: List[DynamicExperimentResult] = []
        run_durations: List[float] = []
        total = len(schedule)

        with create_progress(console) as progress:
            batch_task = progress.add_task("[bold]Phase C Batch[/bold]", total=total)

            for i, (scenario, run_id) in enumerate(schedule, 1):
                print_run_header(console, i, total, scenario, run_id)

                logger.info("progress", current=i, total=total, scenario=scenario, run_id=run_id)

                if not self.check_infrastructure(scenario, skip_daemon=manage_daemon):
                    logger.error("skipping_run", scenario=scenario, run_id=run_id)
                    print_run_failure(console, scenario, "infrastructure not ready")
                    progress.advance(batch_task)
                    continue

                t0 = time.time()
                result = self.run_single_experiment(scenario, run_id, manage_daemon)
                run_dur = time.time() - t0
                run_durations.append(run_dur)

                if result:
                    results.append(result)
                    console.print(
                        f"  [green]✓[/green] [bold]{elapsed_str(run_dur)}[/bold] • "
                        f"p99=[magenta]{result.p99_latency_ms:.0f}ms[/magenta] • "
                        f"rps=[blue]{result.throughput_rps:.1f}[/blue] • "
                        f"errors=[red]{result.error_rate:.4%}[/red] • "
                        f"PREDICTIVE={result.predictive_count}"
                    )
                    self._save_results(results, "experiments_intermediate.json")
                else:
                    print_run_failure(console, scenario, "run failed")

                progress.advance(batch_task)

                if run_durations:
                    avg = sum(run_durations) / len(run_durations)
                    remaining = (total - i) * avg
                    progress.update(
                        batch_task,
                        description=f"[bold]Phase C Batch[/bold] • ~{elapsed_str(remaining)} remaining",
                    )

                # Cool down between runs
                if i < total:
                    with countdown(console, self.cooldown_sec, "Cooldown"):
                        pass

        # Save final results
        self._save_results(results, "experiments_final.json")
        self._generate_summary(results)

        return results

    # -- Output -----------------------------------------------------------

    def _save_results(self, results: List[DynamicExperimentResult], filename: str) -> None:
        """Save results to JSON."""
        path = self.results_dir / filename
        with open(path, "w") as f:
            json.dump([asdict(r) for r in results], f, indent=2)
        logger.info("results_saved", path=str(path))

    def _generate_summary(self, results: List[DynamicExperimentResult]) -> None:
        """Generate a quick summary report."""
        if not results:
            return

        report_lines = [
            "# Phase C: Dynamic Workload Experiment Summary",
            f"\n**Date:** {datetime.now().isoformat()}",
            "**Workload:** dynamic_burst (2 cycles x 3min = 6min per run)",
            f"**Total runs:** {len(results)}",
            "",
        ]

        for scenario in sorted(set(r.scenario for r in results)):
            runs = [r for r in results if r.scenario == scenario]
            report_lines.append(f"\n## {scenario}")
            report_lines.append(f"- Runs: {len(runs)}")

            p99s = [r.p99_latency_ms for r in runs]
            report_lines.append(
                f"- p99 latency: {min(p99s):.1f}-{max(p99s):.1f}ms (mean {sum(p99s) / len(p99s):.1f}ms)"
            )

            errs = [r.error_rate for r in runs]
            report_lines.append(f"- Error rate: {sum(errs) / len(errs):.4f}")

            preds = [r.predictive_count for r in runs]
            report_lines.append(f"- PREDICTIVE decisions: {preds} (total {sum(preds)})")

            slos = [r.slo_violations for r in runs]
            report_lines.append(f"- SLO violations: {slos}")

        report_lines.append("\n## Key Question")
        report_lines.append(
            "Did S4 produce PREDICTIVE > 0? If yes, dynamic workload succeeds where steady 100 RPS failed."
        )

        report_path = self.results_dir / "report.md"
        report_path.write_text("\n".join(report_lines))
        logger.info("report_saved", path=str(report_path))


def run_dynamic_experiment(
    scenarios: List[str],
    num_runs: int = 3,
    cooldown_sec: int = 30,
    manage_daemon: bool = True,
    results_dir: Optional[Path] = None,
) -> List[DynamicExperimentResult]:
    """Run the Phase C dynamic workload experiment suite.

    Thin entry over DynamicExperimentRunner for CLI consumption.
    """
    runner = DynamicExperimentRunner(results_dir=results_dir, cooldown_sec=cooldown_sec)
    return runner.run_all(scenarios=scenarios, num_runs=num_runs, manage_daemon=manage_daemon)
