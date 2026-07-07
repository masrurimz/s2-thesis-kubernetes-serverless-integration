"""Workload calibration: find the Goldilocks RPS for thesis experiments.

Sweeps scenarios x RPS levels with a curl-based load test, reads p99/error
metrics from Prometheus, and recommends the lowest RPS that produces a
"stressed but functional" load (200ms < p99 <= 500ms, error_rate <= 10%).

Ported from scripts/run_calibration.py. Entry point: run_full_calibration().
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import requests
import structlog

from shared.config import settings

logger = structlog.get_logger(__name__)

# apps/experiment/experiment/calibration.py -> 4 levels up to repo root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DAEMON_API = f"http://localhost:{settings.DAEMON_API_PORT}"


@dataclass
class CalibrationResult:
    """Result from a calibration run."""

    scenario: str
    rps: int
    duration_sec: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    error_rate: float
    actual_rps: float
    stress_level: str
    recommended: bool


def load_test_curl(
    rps: int, duration_sec: int, endpoint: str = "http://localhost:18082/work?duration_ms=10"
) -> Tuple[int, int, float]:
    """
    Run load test using parallel curl requests and measure results via Prometheus.
    Returns: (total_requests, errors, actual_rps)
    """
    logger.info("starting_load_test", rps=rps, duration_sec=duration_sec)

    total_requests = 0
    errors = 0
    start_time = time.time()

    # Max 100 parallel curl per second
    batch_size = min(rps, 100)

    while time.time() - start_time < duration_sec:
        batch_start = time.time()

        # Spawn parallel curl processes
        procs = []
        for _ in range(batch_size):
            proc = subprocess.Popen(
                [
                    "curl",
                    "-s",
                    "-o",
                    "/dev/null",
                    "-w",
                    "%{http_code}",
                    "-H",
                    "Host: test-app.default.127.0.0.1.sslip.io",
                    endpoint,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            procs.append(proc)

        # Collect results
        for proc in procs:
            try:
                stdout, _ = proc.communicate(timeout=5)
                status_code = stdout.decode().strip()
                total_requests += 1
                if status_code != "200":
                    errors += 1
            except subprocess.TimeoutExpired:
                proc.kill()
                errors += 1

        # Sleep to maintain target RPS rate
        elapsed = time.time() - batch_start
        sleep_time = max(0, 1.0 - elapsed)
        if sleep_time > 0:
            time.sleep(sleep_time)

    actual_duration = time.time() - start_time
    actual_rps = total_requests / actual_duration if actual_duration > 0 else 0
    error_rate = errors / total_requests if total_requests > 0 else 0

    logger.info(
        "load_test_complete",
        total_requests=total_requests,
        errors=errors,
        actual_rps=round(actual_rps, 2),
        error_rate=round(error_rate, 4),
    )

    return total_requests, errors, actual_rps


def get_prometheus_metrics(url: str = settings.PROMETHEUS_URL) -> Dict[str, float]:
    """Get latency and error metrics from Prometheus."""
    metrics = {
        "p50": 0.0,
        "p95": 0.0,
        "p99": 0.0,
        "error_rate": 0.0,
        "throughput": 0.0,
    }

    try:
        # Get p99 latency
        resp = requests.get(
            f"{url}/api/v1/query",
            params={
                "query": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[1m])) by (le)) * 1000"
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                results = data.get("data", {}).get("result", [])
                if results:
                    metrics["p99"] = float(results[0].get("value", [0, 0])[1])

        # Get error rate
        resp = requests.get(
            f"{url}/api/v1/query",
            params={
                "query": 'sum(rate(http_requests_total{status=~"5.."}[1m])) / sum(rate(http_requests_total[1m])) * 100'
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                results = data.get("data", {}).get("result", [])
                if results:
                    metrics["error_rate"] = float(results[0].get("value", [0, 0])[1])

        # Get throughput
        resp = requests.get(f"{url}/api/v1/query", params={"query": "sum(rate(http_requests_total[1m]))"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                results = data.get("data", {}).get("result", [])
                if results:
                    metrics["throughput"] = float(results[0].get("value", [0, 0])[1])

    except Exception as e:
        logger.warning("prometheus_query_failed", error=str(e))

    return metrics


def determine_stress_level(p99: float, error_rate: float) -> Tuple[str, bool]:
    """Determine stress level and if suitable for experiments."""
    if error_rate > 0.1:
        return "critical", False
    elif p99 > 500:
        return "severe", False
    elif p99 > 200:
        return "stressed", True  # Goldilocks: stressed but functional
    else:
        return "healthy", True  # Also acceptable


def run_calibration(
    scenario: str,
    rps: int,
    duration_sec: int,
    haproxy_stats: str = settings.HAPROXY_STATS_URL,
) -> CalibrationResult:
    """Run a single calibration test."""

    logger.info("running_calibration", scenario=scenario, rps=rps, duration_sec=duration_sec)

    # Start routing daemon for this scenario
    daemon_proc = None
    if scenario != "baseline":
        daemon_cmd = [
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
            haproxy_stats,
            "--gru-url",
            settings.GRU_SERVICE_URL,
            "--interval",
            "15",
            "--api-port",
            str(settings.DAEMON_API_PORT),
        ]

        env = {**os.environ, "HSA_OVERRIDE_GFX_VERSION": "11.0.0", "PREDICTION_CONFIDENCE_THRESHOLD": "0.6"}

        daemon_proc = subprocess.Popen(
            daemon_cmd,
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for daemon to start
        time.sleep(5)

        # Verify daemon is running
        try:
            resp = requests.get(f"{DAEMON_API}/health", timeout=5)
            if resp.status_code != 200:
                logger.error("daemon_not_healthy")
                daemon_proc.terminate()
                daemon_proc.wait()
                daemon_proc = None
        except Exception as e:
            logger.error("daemon_not_responding", error=str(e))
            daemon_proc = None

    # Wait for system to stabilize
    time.sleep(5)

    # Run load test
    total_reqs, errors, actual_rps = load_test_curl(rps, duration_sec)

    # Get metrics from Prometheus
    prom_metrics = get_prometheus_metrics()

    # Stop daemon if running
    if daemon_proc:
        daemon_proc.terminate()
        daemon_proc.wait()
        time.sleep(3)  # Cool down

    # Determine stress level
    stress_level, recommended = determine_stress_level(prom_metrics["p99"], prom_metrics["error_rate"])

    return CalibrationResult(
        scenario=scenario,
        rps=rps,
        duration_sec=duration_sec,
        p50_ms=prom_metrics["p50"],
        p95_ms=prom_metrics["p95"],
        p99_ms=prom_metrics["p99"],
        error_rate=prom_metrics["error_rate"],
        actual_rps=actual_rps,
        stress_level=stress_level,
        recommended=recommended,
    )


def run_full_calibration(scenarios: List[str], rps_levels: List[int], duration_sec: int) -> List[CalibrationResult]:
    """Run full calibration across scenarios and RPS levels."""
    from rich.console import Console
    from rich.table import Table

    from shared.progress import countdown, create_progress, run_phase

    console = Console()
    results: List[CalibrationResult] = []
    total = len(scenarios) * len(rps_levels)

    with create_progress(console) as progress:
        task = progress.add_task("[bold]Calibration sweep[/bold]", total=total)

        for scenario in scenarios:
            logger.info("calibrating_scenario", scenario=scenario)

            for rps in rps_levels:
                logger.info("calibrating_rps", scenario=scenario, rps=rps)

                with run_phase(console, f"{scenario} @ {rps} RPS"):
                    result = run_calibration(scenario, rps, duration_sec)
                    results.append(result)

                logger.info(
                    "calibration_result",
                    scenario=result.scenario,
                    rps=result.rps,
                    p99=result.p99_ms,
                    error_rate=result.error_rate,
                    stress_level=result.stress_level,
                    recommended=result.recommended,
                )

                progress.advance(task)

                # Cool down between tests
                with countdown(console, 10, "Cooldown"):
                    pass

    # Print results table
    table = Table(title="Calibration Results", show_lines=False)
    table.add_column("Scenario", style="cyan")
    table.add_column("RPS", justify="right")
    table.add_column("p99 (ms)", justify="right")
    table.add_column("Error Rate", justify="right")
    table.add_column("Stress", style="magenta")
    table.add_column("Recommended", justify="center")

    for r in results:
        rec = "[green]✓[/green]" if r.recommended else ""
        table.add_row(
            r.scenario,
            str(r.rps),
            f"{r.p99_ms:.0f}",
            f"{r.error_rate:.4%}",
            r.stress_level,
            rec,
        )

    console.print(table)
    return results


def analyze_results(results: List[CalibrationResult]) -> Dict:
    """Analyze calibration results and recommend Goldilocks load."""

    # Find recommended loads
    recommended = [r for r in results if r.recommended]

    # Group by scenario
    by_scenario: Dict[str, List[CalibrationResult]] = {}
    for r in results:
        by_scenario.setdefault(r.scenario, []).append(r)

    # Find best RPS for each scenario
    best_rps: Dict[str, int] = {}
    for scenario, scenario_results in by_scenario.items():
        stressed = [r for r in scenario_results if r.stress_level == "stressed"]
        if stressed:
            # Pick lowest RPS that causes stress
            best_rps[scenario] = min(stressed, key=lambda x: x.rps).rps
        else:
            # Pick highest RPS tested
            healthy = [r for r in scenario_results if r.stress_level == "healthy"]
            if healthy:
                best_rps[scenario] = max(healthy, key=lambda x: x.rps).rps

    # Overall recommendation
    if "s1-k8s-only" in best_rps:
        goldilocks_rps = best_rps["s1-k8s-only"]
    else:
        goldilocks_rps = 100  # Default

    return {
        "goldilocks_rps": goldilocks_rps,
        "best_rps_by_scenario": best_rps,
        "recommended_results": [asdict(r) for r in recommended],
        "all_results": [asdict(r) for r in results],
        "analysis_timestamp": datetime.now().isoformat(),
    }
