#!/usr/bin/env python3
"""
Cloud Cost Analysis for Thesis Scenarios (S1, S2, S3, S4)

Three billing models for scientifically defensible comparison:
  Model 1: AWS Lambda Provisioned Concurrency (concurrency-slot corrected)
  Model 2: Google Cloud Run Always-Allocated (actual vCPU/memory usage)
  Model 3: EC2 Node-Hours (infrastructure-level, most defensible)

Key corrections vs v1:
  1) Concurrency-slot mapping: 1 Knative pod (target=10) = 10 Lambda instances
  2) Little's Law service time: wall-clock = concurrency_slots / throughput
  3) Lambda memory mapping: 200m CPU ≈ 354 MB Lambda memory (1 vCPU at 1769 MB)
  4) Always count ALL running pods (including idle K8s deployment in S2)
  5) Use actual measured CPU-seconds from metrics-server, not avg_latency

Usage:
    # Experiment-based analysis (PRIMARY — uses actual measured data)
    uv run python thesis/scripts/cost_analyzer.py \\
        --experiment-dir results/experiments/phase-b/2026-02-16_validation-metrics-fixes

    # Legacy generic analysis (backward compat)
    uv run python thesis/scripts/cost_analyzer.py --legacy
"""

import argparse
import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent / "controller"))

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Pod resource configuration (from K8s manifests)
# ---------------------------------------------------------------------------
POD_CPU_REQUEST = 0.200       # vCPU (200m) — infrastructure/test-app/*.yaml
POD_MEM_REQUEST_GIB = 0.125   # 128Mi
KNATIVE_TARGET_CONCURRENCY = 10  # autoscaling.knative.dev/target: "10"
# EKS control plane (us-east-1, 2025)
EKS_CONTROL_PLANE_RATE = 0.10  # $/hour

# Real cloud node sizing (production projection)
# After kube-reserved + system-reserved (~200m typical):
CLOUD_NODES = {
    "t3.medium": {"vcpu": 2, "allocatable": 1.8, "rate": 0.0416},
    "m5.xlarge": {"vcpu": 4, "allocatable": 3.8, "rate": 0.192},
}
DEFAULT_CLOUD_NODE = "t3.medium"

# Lambda gives 1 vCPU at 1769 MB. 200m/1000 × 1769 ≈ 354 MB
LAMBDA_MEM_MB = 354
LAMBDA_MEM_GB = LAMBDA_MEM_MB / 1024


# ---------------------------------------------------------------------------
# Pricing constants
# ---------------------------------------------------------------------------

# AWS Lambda Provisioned Concurrency (x86, us-east-1, 2025 list prices)
LAMBDA_PC_RATE = 0.0000041667       # $/GB-s provisioned (warm) capacity
LAMBDA_PC_EXEC_RATE = 0.0000097222  # $/GB-s execution while provisioned
LAMBDA_ONDEMAND_RATE = 0.0000166667 # $/GB-s on-demand (overflow)
LAMBDA_REQUEST_RATE = 0.20          # $/1M requests

# Google Cloud Run always-allocated (us-central1, 2025 list prices)
CR_VCPU_RATE = 0.0000240    # $/vCPU-second
CR_MEM_RATE = 0.0000025     # $/GiB-second
CR_REQUEST_RATE = 0.40       # $/1M requests

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

    # Derived (computed by analyzer)
    implied_service_time_sec: float = 0.0
    k8s_service_time_sec: float = 0.0
    lambda_concurrency_slots: float = 0.0


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
    avg_k8s_pods = 0.0
    avg_kn_pods = 0.0
    max_kn_pods = 0

    if util_path.exists():
        with open(util_path) as f:
            samples = json.load(f)

        by_ts: Dict[float, Dict[str, float]] = defaultdict(
            lambda: {"cpu": 0.0, "mem": 0.0, "k8s_cpu": 0.0, "kn_cpu": 0.0, "k8s_pods": 0, "kn_pods": 0}
        )
        for s in samples:
            ts = s["timestamp"]
            by_ts[ts]["cpu"] += s["cpu_millicores"]
            by_ts[ts]["mem"] += s["memory_mib"]
            if s["backend"] == "k8s":
                by_ts[ts]["k8s_cpu"] += s["cpu_millicores"]
                by_ts[ts]["k8s_pods"] += 1
            else:
                by_ts[ts]["kn_cpu"] += s["cpu_millicores"]
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
        avg_k8s_pods=avg_k8s_pods,
        avg_kn_pods=avg_kn_pods,
        max_kn_pods=max_kn_pods,
        serverless_traffic_pct=result.get("time_in_serverless_pct", 0),
        nodes_provisioned=result.get("nodes_provisioned", 0),
        first_provision_delay_sec=result.get("first_provision_delay_sec", 0),
        desired_replicas_final=result.get("desired_replicas_final", 0),
        k8s_replica_seconds=result.get("k8s_replica_seconds", 0),
    )


def analyze_from_experiment(metrics: ScenarioMetrics) -> Dict[str, Any]:
    """
    Three-model cost analysis using actual experiment measurements.

    Model 1 — Lambda Provisioned Concurrency:
      - 1 Knative pod (target_concurrency=10) = 10 Lambda PC instances
      - Execution duration from Little's Law: concurrency_slots / throughput
      - Lambda memory = 354MB (CPU-equivalent for 200m)

    Model 2 — Cloud Run Always-Allocated:
      - Uses actual measured vCPU-seconds and GiB-seconds from metrics-server

    Model 3 — EC2 Node-Hours:
      - Infrastructure cost: base node + CA-provisioned dynamic nodes
      - Most defensible since both K8s and Knative run on same k3s nodes
    """
    duration_hours = metrics.duration_sec / 3600
    rps = metrics.total_requests / metrics.duration_sec if metrics.duration_sec > 0 else 0

    # Little's Law: implied wall-clock service time per request (Knative)
    kn_conc_slots = metrics.avg_kn_pods * KNATIVE_TARGET_CONCURRENCY
    if rps > 0 and kn_conc_slots > 0:
        metrics.implied_service_time_sec = kn_conc_slots / rps

    # Little's Law: K8s service time (each pod handles ~1 request at a time)
    # avg_replicas = k8s_replica_seconds / duration; service_time = avg_replicas / k8s_rps
    avg_k8s_replicas = metrics.k8s_replica_seconds / metrics.duration_sec if metrics.duration_sec > 0 else 0
    k8s_rps = rps * (1 - metrics.serverless_traffic_pct / 100) if rps > 0 else 0
    if k8s_rps > 0 and avg_k8s_replicas > 0:
        metrics.k8s_service_time_sec = avg_k8s_replicas / k8s_rps
    else:
        # Floor: CPU-share minimum (fib(32) ~10ms on full core, ÷ 200m = 50ms)
        metrics.k8s_service_time_sec = 0.010 / POD_CPU_REQUEST

    metrics.lambda_concurrency_slots = kn_conc_slots + metrics.avg_k8s_pods

    kn_requests = int(metrics.total_requests * metrics.serverless_traffic_pct / 100)
    k8s_requests = metrics.total_requests - kn_requests

    # === MODEL 1: Lambda Provisioned Concurrency ===
    pc_gb_seconds = metrics.lambda_concurrency_slots * LAMBDA_MEM_GB * metrics.duration_sec
    pc_capacity_cost = pc_gb_seconds * LAMBDA_PC_RATE

    kn_exec_gbs = kn_requests * LAMBDA_MEM_GB * metrics.implied_service_time_sec
    k8s_exec_gbs = k8s_requests * LAMBDA_MEM_GB * metrics.k8s_service_time_sec
    pc_execution_cost = (kn_exec_gbs + k8s_exec_gbs) * LAMBDA_PC_EXEC_RATE

    pc_request_cost = metrics.total_requests / 1_000_000 * LAMBDA_REQUEST_RATE
    lambda_pc_total = pc_capacity_cost + pc_execution_cost + pc_request_cost

    # === MODEL 2: Cloud Run Always-Allocated ===
    cr_vcpu_cost = metrics.total_cpu_seconds * CR_VCPU_RATE
    cr_mem_cost = metrics.total_mem_gib_seconds * CR_MEM_RATE
    cr_request_cost = metrics.total_requests / 1_000_000 * CR_REQUEST_RATE
    cr_total = cr_vcpu_cost + cr_mem_cost + cr_request_cost

    # === MODEL 3a: EC2 Node-Hours (observed / constrained) ===
    base_node_hours = duration_hours
    if metrics.nodes_provisioned > 0:
        dynamic_hours = metrics.nodes_provisioned * (
            metrics.duration_sec - metrics.first_provision_delay_sec
        ) / 3600
    else:
        dynamic_hours = 0.0
    ec2_observed_total = (base_node_hours + dynamic_hours) * EC2_T3_MEDIUM_RATE

    # === MODEL 3b: EC2 Production Projection (real cloud node capacity) ===
    # Uses actual cloud node allocatable CPU (not k3d's artificial constraint).
    # k3d used system-reserved=15600m → 400m allocatable (2 pods/node) to force CA triggers.
    # Real t3.medium: ~1.8 vCPU allocatable → 9 pods/node at 200m each.
    cloud_node = CLOUD_NODES[DEFAULT_CLOUD_NODE]
    pods_per_real_node = int(cloud_node["allocatable"] / POD_CPU_REQUEST)
    total_pod_peak = metrics.desired_replicas_final + metrics.max_kn_pods
    total_cpu_requested = total_pod_peak * POD_CPU_REQUEST
    production_nodes = max(1, math.ceil(total_cpu_requested / cloud_node["allocatable"]))
    # +1 headroom node for HA / burst capacity
    production_nodes_ha = production_nodes + 1
    production_node_hours = production_nodes_ha * duration_hours
    ec2_control_plane = EKS_CONTROL_PLANE_RATE * duration_hours
    ec2_production_total = production_node_hours * cloud_node["rate"] + ec2_control_plane

    success_rate = metrics.successful_requests / metrics.total_requests if metrics.total_requests > 0 else 0

    def per_m(cost: float, count: int) -> float:
        return round(cost / count * 1_000_000, 2) if count > 0 else 0.0

    return {
        "scenario": metrics.scenario,
        "duration_sec": metrics.duration_sec,
        "total_requests": metrics.total_requests,
        "successful_requests": metrics.successful_requests,
        "success_rate": round(success_rate, 4),
        "rps": round(rps, 1),
        "implied_service_time_sec": round(metrics.implied_service_time_sec, 3),
        "k8s_service_time_sec": round(metrics.k8s_service_time_sec, 3),
        "lambda_concurrency_slots": round(metrics.lambda_concurrency_slots, 1),
        "avg_kn_pods": round(metrics.avg_kn_pods, 1),
        "avg_k8s_pods": round(metrics.avg_k8s_pods, 1),
        "max_kn_pods": metrics.max_kn_pods,
        "desired_replicas_final": metrics.desired_replicas_final,
        "total_cpu_seconds": round(metrics.total_cpu_seconds, 1),
        "total_mem_gib_seconds": round(metrics.total_mem_gib_seconds, 1),
        "production_nodes": production_nodes_ha,
        "pods_per_real_node": pods_per_real_node,
        "cloud_node_type": DEFAULT_CLOUD_NODE,
        "model1_lambda_pc": {
            "provisioned_capacity": round(pc_capacity_cost, 6),
            "execution": round(pc_execution_cost, 6),
            "requests": round(pc_request_cost, 6),
            "total": round(lambda_pc_total, 6),
        },
        "model2_cloud_run": {
            "vcpu": round(cr_vcpu_cost, 6),
            "memory": round(cr_mem_cost, 6),
            "requests": round(cr_request_cost, 6),
            "total": round(cr_total, 6),
        },
        "model3a_ec2_observed": {
            "base_node": round(base_node_hours * EC2_T3_MEDIUM_RATE, 6),
            "dynamic_nodes": round(dynamic_hours * EC2_T3_MEDIUM_RATE, 6),
            "total": round(ec2_observed_total, 6),
        },
        "model3b_ec2_production": {
            "compute": round(production_node_hours * cloud_node["rate"], 6),
            "control_plane": round(ec2_control_plane, 6),
            "total": round(ec2_production_total, 6),
        },
        "per_million_requests": {
            "lambda_pc": per_m(lambda_pc_total, metrics.total_requests),
            "cloud_run": per_m(cr_total, metrics.total_requests),
            "ec2_observed": per_m(ec2_observed_total, metrics.total_requests),
            "ec2_production": per_m(ec2_production_total, metrics.total_requests),
        },
        "per_million_successful": {
            "lambda_pc": per_m(lambda_pc_total, metrics.successful_requests),
            "cloud_run": per_m(cr_total, metrics.successful_requests),
            "ec2_observed": per_m(ec2_observed_total, metrics.successful_requests),
            "ec2_production": per_m(ec2_production_total, metrics.successful_requests),
        },
    }


def run_experiment_analysis(experiment_dir: Path) -> int:
    """Load experiment results and run three-model cost analysis."""
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
    scenarios = [r["scenario"] for r in results]
    print("\n" + "=" * 80)
    print("COST ANALYSIS — Three Models × {} Scenarios".format(len(results)))
    print("Lambda memory: {}MB (CPU-equivalent for {}m)".format(LAMBDA_MEM_MB, int(POD_CPU_REQUEST * 1000)))
    print("Knative target concurrency: {}".format(KNATIVE_TARGET_CONCURRENCY))
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
        ("Success rate", "success_rate", "{:>13.1%}"),
        ("RPS", "rps", "{:>14.1f}"),
        ("CPU-seconds (vCPU·s)", "total_cpu_seconds", "{:>14.1f}"),
        ("Memory GiB-seconds", "total_mem_gib_seconds", "{:>14.1f}"),
        ("Avg Knative pods", "avg_kn_pods", "{:>14.1f}"),
        ("Max Knative pods", "max_kn_pods", "{:>14}"),
        ("Desired K8s replicas", "desired_replicas_final", "{:>14}"),
        ("Production nodes (+1 HA)", "production_nodes", "{:>14}"),
        ("Lambda concurrency slots", "lambda_concurrency_slots", "{:>14.0f}"),
        ("Kn service time (s)", "implied_service_time_sec", "{:>14.3f}"),
        ("K8s service time (s)", "k8s_service_time_sec", "{:>14.3f}"),
    ]:
        print(f"  {label:<28}", end="")
        for r in results:
            val = r[key]
            if fmt.endswith("%}"):
                print(f" {fmt.format(val)}", end="")
            else:
                print(f" {fmt.format(val)}", end="")
        print()

    # Cost tables
    for model_name, model_key in [
        ("Model 1: Lambda Provisioned Concurrency", "model1_lambda_pc"),
        ("Model 2: Cloud Run Always-Allocated", "model2_cloud_run"),
        ("Model 3a: EC2 Node-Hours (observed)", "model3a_ec2_observed"),
        ("Model 3b: EC2 Production (t3.medium +1 HA)", "model3b_ec2_production"),
    ]:
        print(f"\n--- {model_name} ---")
        components = list(results[0][model_key].keys())
        for comp in components:
            label = comp.replace("_", " ").title()
            print(f"  {label:<28}", end="")
            for r in results:
                val = r[model_key][comp]
                print(f" ${val:>13.4f}", end="")
            print()

    # Per-request costs
    print(f"\n--- $/1M Requests ---")
    for model_label, model_key in [("Lambda PC", "lambda_pc"), ("Cloud Run", "cloud_run"), ("EC2 Observed", "ec2_observed"), ("EC2 Production", "ec2_production")]:
        print(f"  {model_label:<28}", end="")
        for r in results:
            print(f" ${r['per_million_requests'][model_key]:>13.2f}", end="")
        print()

    print(f"\n--- $/1M Successful Requests ---")
    for model_label, model_key in [("Lambda PC", "lambda_pc"), ("Cloud Run", "cloud_run"), ("EC2 Observed", "ec2_observed"), ("EC2 Production", "ec2_production")]:
        print(f"  {model_label:<28}", end="")
        for r in results:
            print(f" ${r['per_million_successful'][model_key]:>13.2f}", end="")
        print()

    # Monthly projection
    if results:
        scale = 30 * 24 * 3600 / results[0]["duration_sec"]
        print(f"\n--- Monthly Projection (30d continuous) ---")
        for model_label, model_key in [
            ("Lambda PC", "model1_lambda_pc"),
            ("Cloud Run", "model2_cloud_run"),
            ("EC2 Observed", "model3a_ec2_observed"),
            ("EC2 Production", "model3b_ec2_production"),
        ]:
            print(f"  {model_label:<28}", end="")
            for r in results:
                print(f" ${r[model_key]['total'] * scale:>13.0f}", end="")
            print()

    # Save results
    output_dir = Path("results/cost_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"cost_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "experiment_dir": str(experiment_dir),
            "config": {
                "lambda_mem_mb": LAMBDA_MEM_MB,
                "pod_cpu_request": POD_CPU_REQUEST,
                "knative_target_concurrency": KNATIVE_TARGET_CONCURRENCY,
                "cloud_node_type": DEFAULT_CLOUD_NODE,
                "cloud_node_allocatable_vcpu": CLOUD_NODES[DEFAULT_CLOUD_NODE]["allocatable"],
                "cloud_node_rate": CLOUD_NODES[DEFAULT_CLOUD_NODE]["rate"],
                "eks_control_plane_rate": EKS_CONTROL_PLANE_RATE,
            },
            "scenarios": results,
        }, f, indent=2)
    print(f"\nResults saved to: {output_file}")

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
        if self.pricing.serverless_compute_cost_per_vcpu_second > 0 or self.pricing.serverless_compute_cost_per_gib_second > 0:
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
        k8s_costs = self.calculate_k8s_cost(duration_hours=duration_hours, enabled=k8s_enabled, avg_utilization=avg_util)
        serverless_costs = self.calculate_serverless_cost(
            num_requests=serverless_requests, avg_execution_ms=avg_latency_ms, memory_mb=512.0, gcp_vcpu=0.25,
        )
        data_transfer_gb = (total_requests * 1000) / (1024 ** 3)
        data_transfer_cost = data_transfer_gb * self.pricing.data_transfer_cost_per_gb
        total_cost = k8s_costs["total"] + serverless_costs["total"] + data_transfer_cost
        cost_per_million = (total_cost / total_requests) * 1_000_000 if total_requests > 0 else 0.0
        return CostBreakdown(
            scenario=scenario, provider=self.pricing.provider,
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
                scenario=name, duration_hours=duration_hours,
                total_requests=total_requests, k8s_percentage=cfg["k8s_pct"], avg_latency_ms=cfg["latency"],
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
        for pricing in (CloudCostSimulator.AWS_PRICING, CloudCostSimulator.GCP_PRICING, CloudCostSimulator.AZURE_PRICING):
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
        "--experiment-dir", type=Path,
        help="Path to experiment results directory containing per-scenario subdirs with result.json",
    )
    parser.add_argument("--legacy", action="store_true", help="Run legacy generic analysis")
    args = parser.parse_args()

    if args.experiment_dir:
        return run_experiment_analysis(args.experiment_dir)
    elif args.legacy:
        return run_legacy_analysis()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
