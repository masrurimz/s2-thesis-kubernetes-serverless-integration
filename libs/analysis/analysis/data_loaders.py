"""Data loaders for experiment results.

Unifies the four duplicate ``load_phase_b_data`` variants and the cost
analyzer's metrics loader into one parameterized API.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from analysis.constants import OUTLIER_RUNS


def load_outliers(path: Path) -> list[dict]:
    """Load the outlier list written by ``identify_outlier_runs``.

    Returns an empty list if the file is absent (fail-soft).
    """
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def is_outlier(scenario: str, run_id: int, outliers: Sequence[dict]) -> bool:
    """Check whether a (scenario, run_id) pair is in the outlier list."""
    return any(o["scenario"] == scenario and o["run_id"] == run_id for o in outliers)


def load_phase_b_data(path: Path, exclude_outliers: bool = False) -> list[dict]:
    """Load a Phase B ``experiments_final.json`` (or ``results_final.json``).

    Parameters
    ----------
    path:
        Path to the JSON file (NOT the directory).
    exclude_outliers:
        When True, drop runs listed in :data:`analysis.constants.OUTLIER_RUNS`.
    """
    with open(path) as f:
        raw = json.load(f)
    if not exclude_outliers:
        return raw
    return [run for run in raw if run["run_id"] not in OUTLIER_RUNS.get(run["scenario"], [])]


def group_by_scenario(data: Sequence[dict]) -> dict[str, list[dict]]:
    """Group experiment run dicts by their ``scenario`` key."""
    grouped: dict[str, list[dict]] = {}
    for run in data:
        grouped.setdefault(run["scenario"], []).append(run)
    return grouped


# ---------------------------------------------------------------------------
# Experiment metrics (from cost_analyzer.py) — resource utilization integration.
# ---------------------------------------------------------------------------


@dataclass
class ScenarioMetrics:
    """Actual measured metrics from experiment result.json + resource_utilization.json."""

    scenario: str
    duration_sec: float
    total_requests: int
    successful_requests: int

    # Trapezoidal integration of metrics-server samples (resource_utilization.json)
    total_cpu_seconds: float = 0.0
    k8s_cpu_seconds: float = 0.0
    knative_cpu_seconds: float = 0.0
    total_mem_gib_seconds: float = 0.0
    k8s_mem_gib_seconds: float = 0.0
    knative_mem_gib_seconds: float = 0.0

    avg_k8s_pods: float = 0.0
    avg_kn_pods: float = 0.0
    max_kn_pods: int = 0

    serverless_traffic_pct: float = 0.0

    nodes_provisioned: int = 0
    first_provision_delay_sec: float = 0.0

    desired_replicas_final: int = 0
    k8s_replica_seconds: float = 0.0

    app_duration_avg_ms: float = 0.0
    app_duration_p50_ms: float = 0.0
    app_duration_p95_ms: float = 0.0
    app_duration_serverless_avg_ms: float = 0.0
    app_duration_serverless_p95_ms: float = 0.0
    app_duration_k8s_avg_ms: float = 0.0

    # Derived (computed by analyze_from_experiment)
    cpu_per_request_sec: float = 0.0
    lambda_exec_time_sec: float = 0.0
    lambda_pc_instances: int = 0
    execution_time_source: str = "cpu_derived"


def load_experiment_metrics(result_path: Path) -> ScenarioMetrics:
    """Load metrics from experiment ``result.json`` + ``resource_utilization.json``.

    Performs trapezoidal integration of metrics-server CPU/memory samples
    over the timestamp axis. Sibling files are resolved relative to
    ``result_path.parent``.
    """
    with open(result_path) as f:
        result = json.load(f)

    util_path = result_path.parent / "resource_utilization.json"
    total_cpu_s = k8s_cpu_s = kn_cpu_s = 0.0
    total_mem_gibs = k8s_mem_gibs = kn_mem_gibs = 0.0
    avg_k8s_pods = avg_kn_pods = 0.0
    max_kn_pods = 0

    if util_path.exists():
        with open(util_path) as f:
            samples = json.load(f)

        by_ts: dict[float, dict[str, float]] = defaultdict(
            lambda: {
                "cpu": 0.0,
                "mem": 0.0,
                "k8s_cpu": 0.0,
                "kn_cpu": 0.0,
                "k8s_mem": 0.0,
                "kn_mem": 0.0,
                "k8s_pods": 0,
                "kn_pods": 0,
            }
        )
        for s in samples:
            ts = s["timestamp"]
            by_ts[ts]["cpu"] += s["cpu_millicores"]
            by_ts[ts]["mem"] += s["memory_mib"]
            if s["backend"] == "k8s":
                by_ts[ts]["k8s_cpu"] += s["cpu_millicores"]
                by_ts[ts]["k8s_mem"] += s["memory_mib"]
                by_ts[ts]["k8s_pods"] += 1
            else:
                by_ts[ts]["kn_cpu"] += s["cpu_millicores"]
                by_ts[ts]["kn_mem"] += s["memory_mib"]
                by_ts[ts]["kn_pods"] += 1

        snapshots = sorted(by_ts.items())
        n = len(snapshots)
        if n > 1:
            for i in range(1, n):
                dt = snapshots[i][0] - snapshots[i - 1][0]
                total_cpu_s += (snapshots[i][1]["cpu"] + snapshots[i - 1][1]["cpu"]) / 2 * dt / 1000
                k8s_cpu_s += (snapshots[i][1]["k8s_cpu"] + snapshots[i - 1][1]["k8s_cpu"]) / 2 * dt / 1000
                kn_cpu_s += (snapshots[i][1]["kn_cpu"] + snapshots[i - 1][1]["kn_cpu"]) / 2 * dt / 1000
                total_mem_gibs += (snapshots[i][1]["mem"] + snapshots[i - 1][1]["mem"]) / 2 * dt / 1024
                k8s_mem_gibs += (snapshots[i][1]["k8s_mem"] + snapshots[i - 1][1]["k8s_mem"]) / 2 * dt / 1024
                kn_mem_gibs += (snapshots[i][1]["kn_mem"] + snapshots[i - 1][1]["kn_mem"]) / 2 * dt / 1024

            avg_k8s_pods = sum(s[1]["k8s_pods"] for s in snapshots) / n
            avg_kn_pods = sum(s[1]["kn_pods"] for s in snapshots) / n
            max_kn_pods = max(int(s[1]["kn_pods"]) for s in snapshots)

    return ScenarioMetrics(
        scenario=result["scenario"],
        duration_sec=result["duration_sec"],
        total_requests=result["total_requests"],
        successful_requests=result["total_requests"] - result.get("slo_violations_k6", 0),
        total_cpu_seconds=total_cpu_s,
        k8s_cpu_seconds=k8s_cpu_s,
        knative_cpu_seconds=kn_cpu_s,
        total_mem_gib_seconds=total_mem_gibs,
        k8s_mem_gib_seconds=k8s_mem_gibs,
        knative_mem_gib_seconds=kn_mem_gibs,
        avg_k8s_pods=avg_k8s_pods,
        avg_kn_pods=avg_kn_pods,
        max_kn_pods=max_kn_pods,
        serverless_traffic_pct=_compute_actual_serverless_pct(result),
        nodes_provisioned=result.get("nodes_provisioned", 0),
        first_provision_delay_sec=result.get("first_provision_delay_sec", 0),
        desired_replicas_final=result.get("desired_replicas_final", 0),
        k8s_replica_seconds=result.get("k8s_replica_seconds", 0),
        app_duration_avg_ms=result.get("app_duration_avg_ms", 0),
        app_duration_p50_ms=result.get("app_duration_p50_ms", 0),
        app_duration_p95_ms=result.get("app_duration_p95_ms", 0),
        app_duration_serverless_avg_ms=result.get("app_duration_serverless_avg_ms", 0),
        app_duration_serverless_p95_ms=result.get("app_duration_serverless_p95_ms", 0),
        app_duration_k8s_avg_ms=result.get("app_duration_k8s_avg_ms", 0),
    )


def _compute_actual_serverless_pct(result: dict[str, Any]) -> float:
    """Compute actual serverless traffic split from HAProxy weight-time products.

    Weight-time integral gives the true traffic allocation ratio (not the
    fraction of scrapes where Knative had any weight, which overcounts).
    """
    k8s_wt = result.get("k8s_weight_time_product", 0)
    kn_wt = result.get("serverless_weight_time_product", 0)
    total_wt = k8s_wt + kn_wt
    if total_wt > 0:
        return kn_wt / total_wt * 100
    if result.get("scenario", "").startswith("s2"):
        return 100.0
    return 0.0
