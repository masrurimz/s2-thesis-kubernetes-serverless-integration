"""Workload calibration: find the Goldilocks RPS for thesis experiments.

Sweeps scenarios x RPS levels with a k6 constant-arrival-rate load test,
reads p99/error metrics from k6's built-in metrics output, and recommends
the lowest RPS that produces a "stressed but functional" load
(200ms < p99 <= 500ms, error_rate <= 10%).

Entry point: run_full_calibration().
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


def load_test_k6(
    rps: int,
    duration_sec: int,
    endpoint: str = "/fib?n=33",
    base_url: str = "http://localhost:18082",
) -> Dict[str, float]:
    """Run load test using k6 constant-arrival-rate and parse metrics from JSON output.

    Returns dict with keys: p50_ms, p95_ms, p99_ms, error_rate, actual_rps, total_requests.
    """
    import json

    k6_script = PROJECT_ROOT / "apps/experiment/experiment/load_tests/calibration/calibration.js"
    duration_min = max(1, round(duration_sec / 60))

    cmd = [
        "k6",
        "run",
        "--quiet",
        "-e",
        f"RPS={rps}",
        "-e",
        f"DURATION={duration_min}",
        "-e",
        f"ENDPOINT={endpoint}",
        "-e",
        f"BASE_URL={base_url}",
        str(k6_script),
    ]

    logger.info("starting_k6_load_test", rps=rps, duration_min=duration_min, endpoint=endpoint)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration_sec + 120, cwd=str(PROJECT_ROOT))

    if result.returncode != 0:
        logger.error("k6_failed", returncode=result.returncode, stderr=result.stderr[:500])
        return {"p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0, "error_rate": 1.0, "actual_rps": 0.0, "total_requests": 0}

    # k6 calibration.js outputs JSON summary to stdout via handleSummary.
    # Format: {"scenario": "...", "rps": N, "metrics": {"p50_latency_ms": X, ...}}
    parsed = None
    try:
        parsed = json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if line.startswith("{"):
                try:
                    parsed = json.loads(line)
                    break
                except json.JSONDecodeError:
                    continue

    if parsed is None:
        logger.error("k6_json_parse_failed", stdout=result.stdout[:500])
        return {
            "p50_ms": 0.0,
            "p95_ms": 0.0,
            "p99_ms": 0.0,
            "error_rate": 1.0,
            "actual_rps": 0.0,
            "total_requests": 0,
        }

    # Handle both flat (calibrate_work.js) and nested (calibration.js) formats
    m = parsed.get("metrics", parsed)

    logger.info(
        "load_test_complete",
        rps=rps,
        actual_rps=m.get("actual_rps", 0),
        p99_ms=m.get("p99_ms", m.get("p99_latency_ms", 0)),
        error_rate=m.get("error_rate", 0),
        total_requests=m.get("total_requests", 0),
    )

    return {
        "p50_ms": m.get("p50_ms", m.get("p50_latency_ms", 0.0)),
        "p95_ms": m.get("p95_ms", m.get("p95_latency_ms", 0.0)),
        "p99_ms": m.get("p99_ms", m.get("p99_latency_ms", 0.0)),
        "error_rate": m.get("error_rate", 0.0),
        "actual_rps": m.get("actual_rps", 0.0),
        "total_requests": m.get("total_requests", 0),
    }


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

    # Run k6 load test (generates load + measures latency in one step)
    k6_metrics = load_test_k6(rps, duration_sec)

    # Stop daemon if running
    if daemon_proc:
        daemon_proc.terminate()
        daemon_proc.wait()
        time.sleep(3)  # Cool down

    # Determine stress level
    stress_level, recommended = determine_stress_level(k6_metrics["p99_ms"], k6_metrics["error_rate"])

    return CalibrationResult(
        scenario=scenario,
        rps=rps,
        duration_sec=duration_sec,
        p50_ms=k6_metrics["p50_ms"],
        p95_ms=k6_metrics["p95_ms"],
        p99_ms=k6_metrics["p99_ms"],
        error_rate=k6_metrics["error_rate"],
        actual_rps=k6_metrics["actual_rps"],
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
