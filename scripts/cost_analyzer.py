#!/usr/bin/env python3
"""
Cloud Cost Analysis for Thesis Scenarios (S1, S2, S3, S4)

Unified AWS cost model mapping experiment architecture to AWS services:
  K8s HPA pods  → EKS control plane ($0.10/hr) + EC2 nodes (t3.medium)
  Knative pods  → AWS Lambda Provisioned Concurrency
  k3s cluster   → EKS control plane

Per-scenario mapping:
  S1 (K8s-only):         EKS + EC2 only, no Lambda
  S2 (Serverless-only):  Lambda only, no EKS/EC2
  S3/S4 (Hybrid):        EKS + EC2 (K8s share) + Lambda (serverless share)

v5 corrections (vs v4):
  1) Unified AWS model replaces 3 separate models (Lambda/CloudRun/EC2)
  2) EC2 nodes sized from K8s CPU demand only (serverless pods → Lambda)
  3) Lambda uses serverless-specific CPU-seconds and request counts
  4) EKS control plane present only when scenario uses K8s (S1/S3/S4)
  5) Stress-harness EC2 (Model 3a) retained as appendix reference only

Usage:
    # Experiment-based analysis (PRIMARY — uses actual measured data)
    uv run python thesis/scripts/cost_analyzer.py \\
        --experiment-dir results/experiments/phase-b/2026-02-16_validation-metrics-fixes

    # Analytical crossover sweep (S1 vs S2)
    uv run python thesis/scripts/cost_analyzer.py --crossover-graph

    # Legacy generic analysis (backward compat)
    uv run python thesis/scripts/cost_analyzer.py --legacy
"""

import argparse
import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "controller"))

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Pod resource configuration (from K8s manifests)
# ---------------------------------------------------------------------------
POD_CPU_REQUEST = 0.200  # vCPU (200m) — infrastructure/test-app/*.yaml
POD_MEM_REQUEST_GIB = 0.125  # 128Mi
KNATIVE_TARGET_CONCURRENCY = 10  # autoscaling.knative.dev/target: "10"
# EKS control plane (us-east-1, 2025)
EKS_CONTROL_PLANE_RATE = 0.10  # $/hour

# Real cloud node sizing (production projection)
# After kube-reserved + system-reserved (~200m CPU, ~500Mi mem typical):
CLOUD_NODES = {
    "t3.medium": {"vcpu": 2, "allocatable_cpu": 1.8, "mem_gib": 4.0, "allocatable_mem_gib": 3.5, "rate": 0.0416},
    "m5.xlarge": {"vcpu": 4, "allocatable_cpu": 3.8, "mem_gib": 16.0, "allocatable_mem_gib": 15.0, "rate": 0.192},
}
DEFAULT_CLOUD_NODE = "t3.medium"

# Production sizing targets (conservative for burst headroom + DaemonSets)
TARGET_CPU_UTIL = 0.60
TARGET_MEM_UTIL = 0.70

# Lambda overhead (network + runtime init per invocation, sensitivity: 0/10/25ms)
LAMBDA_OVERHEAD_SEC = 0.010  # 10ms typical

# Lambda gives 1 vCPU at 1769 MB. 200m/1000 × 1769 ≈ 354 MB
LAMBDA_MEM_MB = 354
LAMBDA_MEM_GB = LAMBDA_MEM_MB / 1024


# ---------------------------------------------------------------------------
# Pricing constants
# ---------------------------------------------------------------------------

# AWS Lambda Provisioned Concurrency (x86, us-east-1, 2025 list prices)
LAMBDA_PC_RATE = 0.0000041667  # $/GB-s provisioned (warm) capacity
LAMBDA_PC_EXEC_RATE = 0.0000097222  # $/GB-s execution while provisioned
LAMBDA_ONDEMAND_RATE = 0.0000166667  # $/GB-s on-demand (overflow)
LAMBDA_REQUEST_RATE = 0.20  # $/1M requests

# EC2 reference node
EC2_T3_MEDIUM_RATE = 0.0416  # $/hour (2 vCPU, 4 GiB)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CloudPricing:
    provider: str
    k8s_control_plane_cost_per_hour: float
    k8s_node_instance_cost_per_hour: float
    serverless_request_cost_per_million: float
    serverless_compute_cost_per_gb_second: float = 0.0
    serverless_compute_cost_per_vcpu_second: float = 0.0
    serverless_compute_cost_per_gib_second: float = 0.0
    data_transfer_cost_per_gb: float = 0.09


@dataclass
class CostBreakdown:
    """LEGACY: Used by old analyze_scenario(). Kept for backward compat."""

    scenario: str
    provider: str
    k8s_control_plane_cost: float
    k8s_nodes_cost: float
    k8s_total_cost: float
    serverless_request_cost: float
    serverless_compute_cost: float
    serverless_total_cost: float
    data_transfer_cost: float
    total_cost: float
    cost_per_million_requests: float
    vs_s1_percent: Optional[float] = None
    vs_s2_percent: Optional[float] = None


@dataclass
class ScenarioMetrics:
    """Actual measured metrics from experiment result.json + resource_utilization.json."""

    scenario: str
    duration_sec: float
    total_requests: int
    successful_requests: int

    # From resource_utilization.json (trapezoidal integration of metrics-server data)
    total_cpu_seconds: float = 0.0
    k8s_cpu_seconds: float = 0.0
    knative_cpu_seconds: float = 0.0
    total_mem_gib_seconds: float = 0.0
    k8s_mem_gib_seconds: float = 0.0
    knative_mem_gib_seconds: float = 0.0

    # Pod counts (from resource_utilization.json snapshot aggregation)
    avg_k8s_pods: float = 0.0
    avg_kn_pods: float = 0.0
    max_kn_pods: int = 0

    # Routing (from daemon status)
    serverless_traffic_pct: float = 0.0

    # Node provisioning (from k3d autoscaler log)
    nodes_provisioned: int = 0
    first_provision_delay_sec: float = 0.0

    # HPA state (from result.json)
    desired_replicas_final: int = 0
    k8s_replica_seconds: float = 0.0

    # Direct app timing from k6-captured response payload (duration_ms)
    app_duration_avg_ms: float = 0.0
    app_duration_p50_ms: float = 0.0
    app_duration_p95_ms: float = 0.0
    app_duration_serverless_avg_ms: float = 0.0
    app_duration_serverless_p95_ms: float = 0.0
    app_duration_k8s_avg_ms: float = 0.0

    # Derived (computed by analyzer)
    cpu_per_request_sec: float = 0.0
    lambda_exec_time_sec: float = 0.0
    lambda_pc_instances: int = 0
    execution_time_source: str = "cpu_derived"


# ---------------------------------------------------------------------------
# Experiment-based cost analysis (PRIMARY)
# ---------------------------------------------------------------------------


def load_experiment_metrics(result_path: Path) -> ScenarioMetrics:
    """Load metrics from experiment result.json + resource_utilization.json."""
    with open(result_path) as f:
        result = json.load(f)

    util_path = result_path.parent / "resource_utilization.json"
    total_cpu_s = 0.0
    k8s_cpu_s = 0.0
    kn_cpu_s = 0.0
    total_mem_gibs = 0.0
    k8s_mem_gibs = 0.0
    kn_mem_gibs = 0.0
    avg_k8s_pods = 0.0
    avg_kn_pods = 0.0
    max_kn_pods = 0

    if util_path.exists():
        with open(util_path) as f:
            samples = json.load(f)

        by_ts: Dict[float, Dict[str, float]] = defaultdict(
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
        serverless_traffic_pct=result.get("time_in_serverless_pct", 0),
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


def analyze_from_experiment(metrics: ScenarioMetrics) -> Dict[str, Any]:
    """
    Unified AWS cost model mapping experiment architecture to AWS services.

    Architecture mapping:
      K8s HPA pods  → EKS control plane + EC2 nodes
      Knative pods  → AWS Lambda Provisioned Concurrency

    Per-scenario:
      S1: EKS + EC2 only (all K8s), no Lambda
      S2: Lambda only (all serverless), no EKS/EC2
      S3/S4: EKS + EC2 (K8s share) + Lambda (serverless share)

    Lambda sizing:
      exec_time = cpu_per_request / POD_CPU_REQUEST + 10ms overhead
      pc_instances = ceil(serverless_rps × exec_time)
      Memory = 354MB (CPU-proportional: 200m/1000m × 1769MB)

    EC2 sizing (K8s demand only):
      nodes = max(ceil(k8s_cpu / node_alloc / util), ceil(k8s_mem / node_alloc / util)) + 1 HA

    Stress-harness EC2 (appendix reference only):
      Uses observed k3d node counts with 400m allocatable — not for production projection.
    """
    duration_hours = metrics.duration_sec / 3600
    rps = metrics.total_requests / metrics.duration_sec if metrics.duration_sec > 0 else 0
    scenario = metrics.scenario.lower()

    has_k8s = not scenario.startswith("s2")
    has_serverless = not scenario.startswith("s1")

    # --- Execution-time sizing ---
    metrics.cpu_per_request_sec = (
        metrics.total_cpu_seconds / metrics.successful_requests if metrics.successful_requests > 0 else 0
    )
    cpu_derived_exec_time_sec = metrics.cpu_per_request_sec / POD_CPU_REQUEST + LAMBDA_OVERHEAD_SEC

    # Prefer serverless-specific execution signal for Lambda sizing.
    if metrics.app_duration_serverless_avg_ms > 0:
        metrics.lambda_exec_time_sec = (metrics.app_duration_serverless_avg_ms / 1000.0) + LAMBDA_OVERHEAD_SEC
        metrics.execution_time_source = "app_duration_serverless_avg"
    elif metrics.app_duration_avg_ms > 0 and scenario.startswith("s2"):
        # S2 is fully serverless, so blended app duration is still serverless-specific.
        metrics.lambda_exec_time_sec = (metrics.app_duration_avg_ms / 1000.0) + LAMBDA_OVERHEAD_SEC
        metrics.execution_time_source = "app_duration_avg"
    else:
        # Fallback: derive serverless compute time from knative CPU and serverless request count.
        if scenario.startswith("s1"):
            serverless_pct_tmp = 0.0
        elif scenario.startswith("s2"):
            serverless_pct_tmp = 100.0
        else:
            serverless_pct_tmp = metrics.serverless_traffic_pct
        serverless_requests_tmp = int(metrics.total_requests * (serverless_pct_tmp / 100.0))
        if serverless_requests_tmp > 0 and metrics.knative_cpu_seconds > 0:
            knative_cpu_per_req_sec = metrics.knative_cpu_seconds / serverless_requests_tmp
            metrics.lambda_exec_time_sec = knative_cpu_per_req_sec / POD_CPU_REQUEST + LAMBDA_OVERHEAD_SEC
            metrics.execution_time_source = "knative_cpu_per_serverless_req"
        else:
            metrics.lambda_exec_time_sec = cpu_derived_exec_time_sec
            metrics.execution_time_source = "cpu_derived"

    # --- Serverless request routing ---
    if scenario.startswith("s1"):
        serverless_pct = 0.0
    elif scenario.startswith("s2"):
        serverless_pct = 100.0
    else:
        serverless_pct = metrics.serverless_traffic_pct

    serverless_rps = rps * (serverless_pct / 100.0)
    serverless_requests = int(metrics.total_requests * (serverless_pct / 100.0))

    # Lambda PC instances = ceil(serverless_rps × exec_time)
    metrics.lambda_pc_instances = math.ceil(serverless_rps * metrics.lambda_exec_time_sec) if serverless_rps > 0 else 0

    # === EKS CONTROL PLANE ===
    eks_control_plane = EKS_CONTROL_PLANE_RATE * duration_hours if has_k8s else 0.0

    # === EC2 NODES (K8s demand only) ===
    cloud_node = CLOUD_NODES[DEFAULT_CLOUD_NODE]
    if has_k8s and metrics.k8s_cpu_seconds > 0:
        avg_k8s_cpu = metrics.k8s_cpu_seconds / metrics.duration_sec
        avg_k8s_mem = metrics.k8s_mem_gib_seconds / metrics.duration_sec
        nodes_cpu = math.ceil(avg_k8s_cpu / (cloud_node["allocatable_cpu"] * TARGET_CPU_UTIL))
        nodes_mem = math.ceil(avg_k8s_mem / (cloud_node["allocatable_mem_gib"] * TARGET_MEM_UTIL))
        production_nodes = max(1, nodes_cpu, nodes_mem) + 1  # +1 HA
    else:
        production_nodes = 0
        avg_k8s_cpu = 0.0
        avg_k8s_mem = 0.0
    ec2_compute = production_nodes * duration_hours * cloud_node["rate"] if production_nodes > 0 else 0.0

    # === LAMBDA PROVISIONED CONCURRENCY (serverless demand only) ===
    if has_serverless and metrics.lambda_pc_instances > 0:
        # Capacity: keep PC instances warm for the full duration
        pc_gb_seconds = metrics.lambda_pc_instances * LAMBDA_MEM_GB * metrics.duration_sec
        lambda_capacity = pc_gb_seconds * LAMBDA_PC_RATE

        # Execution: each serverless request billed at exec_time × memory
        exec_gb_seconds = serverless_requests * LAMBDA_MEM_GB * metrics.lambda_exec_time_sec
        lambda_execution = exec_gb_seconds * LAMBDA_PC_EXEC_RATE

        lambda_requests = serverless_requests / 1_000_000 * LAMBDA_REQUEST_RATE
    else:
        lambda_capacity = 0.0
        lambda_execution = 0.0
        lambda_requests = 0.0

    lambda_total = lambda_capacity + lambda_execution + lambda_requests
    aws_total = eks_control_plane + ec2_compute + lambda_total

    # === STRESS-HARNESS EC2 (appendix reference only) ===
    base_node_hours = duration_hours
    if metrics.nodes_provisioned > 0:
        dynamic_hours = metrics.nodes_provisioned * (metrics.duration_sec - metrics.first_provision_delay_sec) / 3600
    else:
        dynamic_hours = 0.0
    ec2_stress_total = (base_node_hours + dynamic_hours) * EC2_T3_MEDIUM_RATE

    success_rate = metrics.successful_requests / metrics.total_requests if metrics.total_requests > 0 else 0
    slo_compliant_requests = metrics.successful_requests
    slo_noncompliant_requests = max(0, metrics.total_requests - slo_compliant_requests)
    successful_rps = slo_compliant_requests / metrics.duration_sec if metrics.duration_sec > 0 else 0.0

    def per_m(cost: float, count: int) -> float:
        return round(cost / count * 1_000_000, 2) if count > 0 else 0.0

    return {
        "scenario": metrics.scenario,
        "duration_sec": metrics.duration_sec,
        "total_requests": metrics.total_requests,
        "successful_requests": metrics.successful_requests,
        "slo_compliant_requests": slo_compliant_requests,
        "slo_noncompliant_requests": slo_noncompliant_requests,
        "success_rate": round(success_rate, 4),
        "rps": round(rps, 1),
        "successful_rps": round(successful_rps, 1),
        "serverless_traffic_pct": round(serverless_pct, 1),
        "serverless_requests": serverless_requests,
        "cpu_per_request_ms": round(metrics.cpu_per_request_sec * 1000, 2),
        "app_duration_avg_ms": round(metrics.app_duration_avg_ms, 2),
        "app_duration_p50_ms": round(metrics.app_duration_p50_ms, 2),
        "app_duration_p95_ms": round(metrics.app_duration_p95_ms, 2),
        "app_duration_serverless_avg_ms": round(metrics.app_duration_serverless_avg_ms, 2),
        "app_duration_serverless_p95_ms": round(metrics.app_duration_serverless_p95_ms, 2),
        "app_duration_k8s_avg_ms": round(metrics.app_duration_k8s_avg_ms, 2),
        "execution_time_source": metrics.execution_time_source,
        "lambda_exec_time_ms": round(metrics.lambda_exec_time_sec * 1000, 1),
        "lambda_pc_instances": metrics.lambda_pc_instances,
        "avg_kn_pods": round(metrics.avg_kn_pods, 1),
        "avg_k8s_pods": round(metrics.avg_k8s_pods, 1),
        "max_kn_pods": metrics.max_kn_pods,
        "desired_replicas_final": metrics.desired_replicas_final,
        "total_cpu_seconds": round(metrics.total_cpu_seconds, 1),
        "k8s_cpu_seconds": round(metrics.k8s_cpu_seconds, 1),
        "knative_cpu_seconds": round(metrics.knative_cpu_seconds, 1),
        "total_mem_gib_seconds": round(metrics.total_mem_gib_seconds, 1),
        "k8s_mem_gib_seconds": round(metrics.k8s_mem_gib_seconds, 1),
        "knative_mem_gib_seconds": round(metrics.knative_mem_gib_seconds, 1),
        "production_nodes": production_nodes,
        "cloud_node_type": DEFAULT_CLOUD_NODE,
        "aws_cost": {
            "eks_control_plane": round(eks_control_plane, 6),
            "ec2_compute": round(ec2_compute, 6),
            "lambda_capacity": round(lambda_capacity, 6),
            "lambda_execution": round(lambda_execution, 6),
            "lambda_requests": round(lambda_requests, 6),
            "total": round(aws_total, 6),
        },
        "stress_harness_ec2": {
            "base_node": round(base_node_hours * EC2_T3_MEDIUM_RATE, 6),
            "dynamic_nodes": round(dynamic_hours * EC2_T3_MEDIUM_RATE, 6),
            "total": round(ec2_stress_total, 6),
        },
        "per_million_requests": round(per_m(aws_total, metrics.total_requests), 2),
        "per_million_successful": round(per_m(aws_total, metrics.successful_requests), 2),
        "per_million_slo_compliant": round(per_m(aws_total, slo_compliant_requests), 2),
        "usd_per_successful_request": round(aws_total / metrics.successful_requests, 8)
        if metrics.successful_requests > 0
        else 0.0,
        "successful_requests_per_usd": round(metrics.successful_requests / aws_total, 2) if aws_total > 0 else 0.0,
    }


def run_experiment_analysis(experiment_dir: Path) -> int:
    """Load experiment results and run unified AWS cost analysis."""
    result_files = sorted(experiment_dir.glob("*/result.json"))
    if not result_files:
        logger.error("no_result_files", dir=str(experiment_dir))
        return 1

    results: List[Dict[str, Any]] = []
    for rf in result_files:
        logger.info("loading_scenario", path=str(rf))
        metrics = load_experiment_metrics(rf)
        analysis = analyze_from_experiment(metrics)
        results.append(analysis)

    # Print summary
    print("\n" + "=" * 80)
    print("UNIFIED AWS COST ANALYSIS — {} Scenarios".format(len(results)))
    print("K8s → EKS + EC2 | Knative → Lambda PC | Lambda mem: {}MB".format(LAMBDA_MEM_MB))
    print(
        "EC2: {} (alloc {:.1f} vCPU) | EKS: ${:.2f}/hr | Lambda overhead: {}ms".format(
            DEFAULT_CLOUD_NODE,
            CLOUD_NODES[DEFAULT_CLOUD_NODE]["allocatable_cpu"],
            EKS_CONTROL_PLANE_RATE,
            int(LAMBDA_OVERHEAD_SEC * 1000),
        )
    )
    print("=" * 80)

    # Resource consumption
    print(f"\n{'Metric':<30}", end="")
    for r in results:
        print(f" {r['scenario'][:14]:>14}", end="")
    print()
    print("-" * (30 + 15 * len(results)))

    for label, key, fmt in [
        ("Total requests", "total_requests", "{:>14,}"),
        ("Successful requests", "successful_requests", "{:>14,}"),
        ("SLO-compliant req", "slo_compliant_requests", "{:>14,}"),
        ("SLO non-compliant", "slo_noncompliant_requests", "{:>14,}"),
        ("Success rate", "success_rate", "{:>13.1%}"),
        ("RPS", "rps", "{:>14.1f}"),
        ("Successful RPS", "successful_rps", "{:>14.1f}"),
        ("Serverless traffic %", "serverless_traffic_pct", "{:>13.1f}%"),
        ("Serverless requests", "serverless_requests", "{:>14,}"),
        ("K8s CPU-seconds", "k8s_cpu_seconds", "{:>14.1f}"),
        ("Knative CPU-seconds", "knative_cpu_seconds", "{:>14.1f}"),
        ("Total CPU-seconds", "total_cpu_seconds", "{:>14.1f}"),
        ("K8s mem GiB-seconds", "k8s_mem_gib_seconds", "{:>14.1f}"),
        ("Knative mem GiB-seconds", "knative_mem_gib_seconds", "{:>14.1f}"),
        ("CPU/request (ms@1vCPU)", "cpu_per_request_ms", "{:>14.2f}"),
        ("Lambda exec time (ms)", "lambda_exec_time_ms", "{:>14.1f}"),
        ("Lambda PC instances", "lambda_pc_instances", "{:>14}"),
        ("EC2 production nodes", "production_nodes", "{:>14}"),
    ]:
        print(f"  {label:<28}", end="")
        for r in results:
            val = r[key]
            print(f" {fmt.format(val)}", end="")
        print()

    # Unified AWS cost breakdown
    print("\n--- Unified AWS Cost Breakdown ---")
    for comp in ["eks_control_plane", "ec2_compute", "lambda_capacity", "lambda_execution", "lambda_requests", "total"]:
        label = comp.replace("_", " ").title()
        print(f"  {label:<28}", end="")
        for r in results:
            val = r["aws_cost"][comp]
            print(f" ${val:>13.4f}", end="")
        print()

    # Per-request costs
    print("\n--- $/1M Requests ---")
    print(f"  {'AWS Total':<28}", end="")
    for r in results:
        print(f" ${r['per_million_requests']:>13.2f}", end="")
    print()

    print("\n--- $/1M Successful Requests ---")
    print(f"  {'AWS Total':<28}", end="")
    for r in results:
        print(f" ${r['per_million_successful']:>13.2f}", end="")
    print()

    print("\n--- $/1M SLO-Compliant Requests ---")
    print(f"  {'AWS Total':<28}", end="")
    for r in results:
        print(f" ${r['per_million_slo_compliant']:>13.2f}", end="")
    print()

    print("\n--- Fairness-Normalized Throughput per $ ---")
    print(f"  {'Successful req / $':<28}", end="")
    for r in results:
        print(f" {r['successful_requests_per_usd']:>14.2f}", end="")
    print()

    # Monthly projection
    if results:
        scale = 30 * 24 * 3600 / results[0]["duration_sec"]
        print("\n--- Monthly Projection (30d continuous) ---")
        print(f"  {'AWS Total':<28}", end="")
        for r in results:
            print(f" ${r['aws_cost']['total'] * scale:>13.0f}", end="")
        print()

    # Stress-harness reference
    print("\n--- Stress-Harness EC2 (appendix reference) ---")
    for comp in ["base_node", "dynamic_nodes", "total"]:
        label = comp.replace("_", " ").title()
        print(f"  {label:<28}", end="")
        for r in results:
            val = r["stress_harness_ec2"][comp]
            print(f" ${val:>13.4f}", end="")
        print()

    # Save results
    output_dir = Path("results/cost_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"cost_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "experiment_dir": str(experiment_dir),
                "config": {
                    "version": "v5",
                    "model": "unified_aws",
                    "architecture_mapping": "K8s→EKS+EC2, Knative→Lambda",
                    "lambda_mem_mb": LAMBDA_MEM_MB,
                    "lambda_overhead_ms": LAMBDA_OVERHEAD_SEC * 1000,
                    "pod_cpu_request": POD_CPU_REQUEST,
                    "pod_mem_request_gib": POD_MEM_REQUEST_GIB,
                    "target_cpu_util": TARGET_CPU_UTIL,
                    "target_mem_util": TARGET_MEM_UTIL,
                    "cloud_node_type": DEFAULT_CLOUD_NODE,
                    "cloud_node_allocatable_cpu": CLOUD_NODES[DEFAULT_CLOUD_NODE]["allocatable_cpu"],
                    "cloud_node_allocatable_mem_gib": CLOUD_NODES[DEFAULT_CLOUD_NODE]["allocatable_mem_gib"],
                    "cloud_node_rate": CLOUD_NODES[DEFAULT_CLOUD_NODE]["rate"],
                    "eks_control_plane_rate": EKS_CONTROL_PLANE_RATE,
                },
                "scenarios": results,
            },
            f,
            indent=2,
        )
    print(f"\nResults saved to: {output_file}")

    return 0


def _s1_cost_per_hour(rps: float, cpu_per_request_sec: float) -> float:
    cloud_node = CLOUD_NODES[DEFAULT_CLOUD_NODE]
    node_cpu_capacity = cloud_node["allocatable_cpu"] * TARGET_CPU_UTIL
    nodes_needed = math.ceil(rps * cpu_per_request_sec / node_cpu_capacity) if rps > 0 else 0
    production_nodes = max(1, nodes_needed) + 1  # +1 HA
    return EKS_CONTROL_PLANE_RATE + production_nodes * cloud_node["rate"]


def _s2_cost_per_hour(rps: float, cpu_per_request_sec: float) -> float:
    if rps <= 0:
        return 0.0
    exec_time = cpu_per_request_sec / POD_CPU_REQUEST + LAMBDA_OVERHEAD_SEC
    pc_instances = math.ceil(rps * exec_time)
    capacity_cost = pc_instances * LAMBDA_MEM_GB * 3600 * LAMBDA_PC_RATE
    execution_cost = rps * 3600 * LAMBDA_MEM_GB * exec_time * LAMBDA_PC_EXEC_RATE
    request_cost = rps * 3600 / 1_000_000 * LAMBDA_REQUEST_RATE
    return capacity_cost + execution_cost + request_cost


def _find_crossover(rps_values: List[int], s1_costs: List[float], s2_costs: List[float]) -> Optional[Dict[str, float]]:
    deltas = [s1 - s2 for s1, s2 in zip(s1_costs, s2_costs)]
    for idx in range(1, len(deltas)):
        prev_delta = deltas[idx - 1]
        curr_delta = deltas[idx]
        if prev_delta == 0:
            return {"rps": float(rps_values[idx - 1]), "cost": s1_costs[idx - 1]}
        if prev_delta < 0 <= curr_delta or prev_delta > 0 >= curr_delta:
            x0 = rps_values[idx - 1]
            x1 = rps_values[idx]
            y0 = prev_delta
            y1 = curr_delta
            if y1 == y0:
                rps_cross = float(x0)
            else:
                rps_cross = x0 + (0 - y0) * (x1 - x0) / (y1 - y0)
            s1_cross = s1_costs[idx - 1] + (s1_costs[idx] - s1_costs[idx - 1]) * (rps_cross - x0) / (x1 - x0)
            return {"rps": rps_cross, "cost": s1_cross}
    return None


def generate_crossover_graph(output_dir: Path) -> int:
    import matplotlib.pyplot as plt

    output_dir.mkdir(parents=True, exist_ok=True)

    workloads = [
        {"label": "fib(32)", "cpu_per_request_sec": 0.01090},
        {"label": "fib(34)", "cpu_per_request_sec": 0.01090 * 2.6},
        {"label": "fib(35)", "cpu_per_request_sec": 0.01090 * (55 / 8)},
    ]

    rps_values = list(range(1, 501))
    fig, ax = plt.subplots(figsize=(10, 6), facecolor="white")
    ax.set_facecolor("white")

    crossover_points: Dict[str, Dict[str, float]] = {}
    colors = ["#1f77b4", "#2ca02c", "#d62728"]

    for idx, workload in enumerate(workloads):
        cpu_per_req = workload["cpu_per_request_sec"]
        s1_costs = [_s1_cost_per_hour(rps, cpu_per_req) for rps in rps_values]
        s2_costs = [_s2_cost_per_hour(rps, cpu_per_req) for rps in rps_values]

        color = colors[idx % len(colors)]
        ax.plot(rps_values, s1_costs, color=color, linewidth=2.0, label=f"S1 EKS+EC2 {workload['label']}")
        ax.plot(
            rps_values, s2_costs, color=color, linewidth=2.0, linestyle="--", label=f"S2 Lambda {workload['label']}"
        )

        crossover = _find_crossover(rps_values, s1_costs, s2_costs)
        if crossover:
            crossover_points[workload["label"]] = crossover
            ax.axvline(crossover["rps"], color=color, linestyle=":", linewidth=1.5, alpha=0.8)
            ax.annotate(
                f"{workload['label']} ~{crossover['rps']:.0f} RPS",
                xy=(crossover["rps"], crossover["cost"]),
                xytext=(6, 12 + idx * 14),
                textcoords="offset points",
                fontsize=9,
                color=color,
            )

    ax.set_title("S1 (EKS+EC2) vs S2 (Lambda) Cost Crossover", fontsize=13)
    ax.set_xlabel("Requests per Second (RPS)")
    ax.set_ylabel("Cost per Hour (USD)")
    ax.grid(True, which="both", linestyle="--", linewidth=0.8, alpha=0.4)
    ax.legend(frameon=False, ncol=2)

    fig.tight_layout()

    png_path = output_dir / "cost_crossover_rps.png"
    pdf_path = output_dir / "cost_crossover_rps.pdf"
    fig.savefig(png_path, dpi=300)
    fig.savefig(pdf_path)
    plt.close(fig)

    print(f"Saved crossover graph: {png_path}")
    print(f"Saved crossover graph: {pdf_path}")
    for label, cross in crossover_points.items():
        print(f"Crossover {label}: ~{cross['rps']:.1f} RPS (${cross['cost']:.4f}/hr)")

    return 0


# ---------------------------------------------------------------------------
# LEGACY: Generic analysis (backward compatibility)
# ---------------------------------------------------------------------------


class CloudCostSimulator:
    """
    LEGACY: Generic cost simulator using assumed traffic splits and latencies.
    Use run_experiment_analysis() for accurate results from actual measurements.
    """

    AWS_PRICING = CloudPricing(
        provider="AWS",
        k8s_control_plane_cost_per_hour=0.10,
        k8s_node_instance_cost_per_hour=0.096,
        serverless_request_cost_per_million=0.20,
        serverless_compute_cost_per_gb_second=0.0000166667,
        data_transfer_cost_per_gb=0.09,
    )

    GCP_PRICING = CloudPricing(
        provider="GCP",
        k8s_control_plane_cost_per_hour=0.10,
        k8s_node_instance_cost_per_hour=0.06701142,
        serverless_request_cost_per_million=0.40,
        serverless_compute_cost_per_vcpu_second=0.000024,
        serverless_compute_cost_per_gib_second=0.0000025,
        data_transfer_cost_per_gb=0.12,
    )

    AZURE_PRICING = CloudPricing(
        provider="Azure",
        k8s_control_plane_cost_per_hour=0.0,
        k8s_node_instance_cost_per_hour=0.096,
        serverless_request_cost_per_million=0.20,
        serverless_compute_cost_per_gb_second=0.000016,
        data_transfer_cost_per_gb=0.087,
    )

    def __init__(self, pricing: CloudPricing):
        self.pricing = pricing

    def calculate_k8s_cost(
        self,
        duration_hours: float,
        enabled: bool,
        avg_utilization: float,
        max_nodes: int = 3,
        min_nodes: int = 1,
    ) -> Dict[str, float]:
        if not enabled:
            return {"control_plane": 0.0, "nodes": 0.0, "total": 0.0, "node_count": 0}
        control_plane_cost = self.pricing.k8s_control_plane_cost_per_hour * duration_hours
        desired = int(math.ceil(max_nodes * max(0.0, min(1.0, avg_utilization))))
        node_count = max(min_nodes, min(max_nodes, desired))
        nodes_cost = node_count * self.pricing.k8s_node_instance_cost_per_hour * duration_hours
        return {
            "control_plane": round(control_plane_cost, 2),
            "nodes": round(nodes_cost, 2),
            "total": round(control_plane_cost + nodes_cost, 2),
            "node_count": node_count,
        }

    def calculate_serverless_cost(
        self,
        num_requests: int,
        avg_execution_ms: float,
        memory_mb: float = 512.0,
        gcp_vcpu: float = 0.25,
    ) -> Dict[str, float]:
        """LEGACY: Uses avg_latency as execution time. See module docstring for why this is wrong."""
        if num_requests <= 0:
            return {"requests": 0.0, "compute": 0.0, "total": 0.0}
        request_cost = (num_requests / 1_000_000) * self.pricing.serverless_request_cost_per_million
        exec_seconds = avg_execution_ms / 1000.0
        if (
            self.pricing.serverless_compute_cost_per_vcpu_second > 0
            or self.pricing.serverless_compute_cost_per_gib_second > 0
        ):
            vcpu_seconds = num_requests * gcp_vcpu * exec_seconds
            gib_seconds = num_requests * (memory_mb / 1024.0) * exec_seconds
            compute_cost = (
                vcpu_seconds * self.pricing.serverless_compute_cost_per_vcpu_second
                + gib_seconds * self.pricing.serverless_compute_cost_per_gib_second
            )
        else:
            gb_seconds = num_requests * (memory_mb / 1024.0) * exec_seconds
            compute_cost = gb_seconds * self.pricing.serverless_compute_cost_per_gb_second
        total = request_cost + compute_cost
        return {"requests": round(request_cost, 2), "compute": round(compute_cost, 2), "total": round(total, 2)}

    def analyze_scenario(
        self,
        scenario: str,
        duration_hours: float,
        total_requests: int,
        k8s_percentage: float,
        avg_latency_ms: float,
    ) -> CostBreakdown:
        k8s_requests = int(total_requests * (k8s_percentage / 100.0))
        serverless_requests = total_requests - k8s_requests
        k8s_enabled = k8s_requests > 0
        avg_util = 0.30 if k8s_enabled else 0.0
        k8s_costs = self.calculate_k8s_cost(
            duration_hours=duration_hours, enabled=k8s_enabled, avg_utilization=avg_util
        )
        serverless_costs = self.calculate_serverless_cost(
            num_requests=serverless_requests,
            avg_execution_ms=avg_latency_ms,
            memory_mb=512.0,
            gcp_vcpu=0.25,
        )
        data_transfer_gb = (total_requests * 1000) / (1024**3)
        data_transfer_cost = data_transfer_gb * self.pricing.data_transfer_cost_per_gb
        total_cost = k8s_costs["total"] + serverless_costs["total"] + data_transfer_cost
        cost_per_million = (total_cost / total_requests) * 1_000_000 if total_requests > 0 else 0.0
        return CostBreakdown(
            scenario=scenario,
            provider=self.pricing.provider,
            k8s_control_plane_cost=float(k8s_costs["control_plane"]),
            k8s_nodes_cost=float(k8s_costs["nodes"]),
            k8s_total_cost=float(k8s_costs["total"]),
            serverless_request_cost=float(serverless_costs["requests"]),
            serverless_compute_cost=float(serverless_costs["compute"]),
            serverless_total_cost=float(serverless_costs["total"]),
            data_transfer_cost=round(data_transfer_cost, 2),
            total_cost=round(total_cost, 2),
            cost_per_million_requests=round(cost_per_million, 2),
        )

    def compare_all_scenarios(self, duration_hours: float, total_requests: int) -> Dict[str, CostBreakdown]:
        scenarios = {
            "S1 (K8s-Only)": {"k8s_pct": 100.0, "latency": 50},
            "S2 (Serverless-Only)": {"k8s_pct": 0.0, "latency": 100},
            "S3 (Hybrid Reactive)": {"k8s_pct": 80.0, "latency": 75},
            "S4 (Hybrid Predictive)": {"k8s_pct": 85.0, "latency": 70},
        }
        results: Dict[str, CostBreakdown] = {}
        for name, cfg in scenarios.items():
            results[name] = self.analyze_scenario(
                scenario=name,
                duration_hours=duration_hours,
                total_requests=total_requests,
                k8s_percentage=cfg["k8s_pct"],
                avg_latency_ms=cfg["latency"],
            )
        s1_cost = results["S1 (K8s-Only)"].total_cost
        s2_cost = results["S2 (Serverless-Only)"].total_cost
        for r in results.values():
            r.vs_s1_percent = ((r.total_cost - s1_cost) / s1_cost) * 100 if s1_cost else None
            r.vs_s2_percent = ((r.total_cost - s2_cost) / s2_cost) * 100 if s2_cost else None
        return results


def run_legacy_analysis() -> int:
    """LEGACY: Run generic cost analysis with assumed parameters."""
    requests_per_hour = 360_000
    for period_name, hours in [("1 hour", 1.0), ("1 day", 24.0), ("1 month (720hr)", 720.0)]:
        total_requests = int(requests_per_hour * hours)
        print(f"\n{'#' * 80}")
        print(f"# TIME PERIOD: {period_name} — {total_requests:,} requests")
        print(f"{'#' * 80}")
        for pricing in (
            CloudCostSimulator.AWS_PRICING,
            CloudCostSimulator.GCP_PRICING,
            CloudCostSimulator.AZURE_PRICING,
        ):
            sim = CloudCostSimulator(pricing)
            results = sim.compare_all_scenarios(duration_hours=hours, total_requests=total_requests)
            print(f"\n  {pricing.provider}:")
            for name, r in results.items():
                print(f"    {name:<25} ${r.total_cost:>10.2f}  (${r.cost_per_million_requests:.2f}/1M req)")
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Cloud Cost Analysis for Thesis Scenarios")
    parser.add_argument(
        "--experiment-dir",
        type=Path,
        help="Path to experiment results directory containing per-scenario subdirs with result.json",
    )
    parser.add_argument(
        "--crossover-graph",
        action="store_true",
        help="Generate analytical S1 vs S2 crossover graph and save to results/cost/",
    )
    parser.add_argument("--legacy", action="store_true", help="Run legacy generic analysis")
    args = parser.parse_args()

    if args.crossover_graph:
        return generate_crossover_graph(Path("results/cost"))
    elif args.experiment_dir:
        return run_experiment_analysis(args.experiment_dir)
    elif args.legacy:
        return run_legacy_analysis()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
