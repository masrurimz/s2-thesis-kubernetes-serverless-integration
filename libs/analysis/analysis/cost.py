"""Cloud cost model — unified AWS mapping (EKS + EC2 + Lambda PC).

Maps the experiment architecture to AWS services and computes a cost
breakdown per scenario. Also provides the cost-proxy metric (β-weighted
weight-time products) used in the statistical reanalysis.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from shared.models.calibration import CALIBRATION

from analysis.constants import (
    BETA_VALUES,
    CLOUD_NODES,
    DEFAULT_CLOUD_NODE,
    EKS_CONTROL_PLANE_RATE,
    EC2_T3_MEDIUM_RATE,
    LAMBDA_MEM_GB,
    LAMBDA_ONDEMAND_RATE,
    LAMBDA_OVERHEAD_SEC,
    LAMBDA_PC_EXEC_RATE,
    LAMBDA_PC_RATE,
    LAMBDA_REQUEST_RATE,
    POD_CPU_REQUEST,
    TARGET_CPU_UTIL,
    TARGET_MEM_UTIL,
)
from analysis.data_loaders import ScenarioMetrics
from shared.scenarios import SCENARIO_ORDER


@dataclass(frozen=True)
class CloudPricing:
    """Cloud provider pricing snapshot."""

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
    """Legacy per-scenario cost breakdown (kept for backward compatibility).

    The current primary path is :func:`analyze_from_experiment`, which returns
    a plain dict. This dataclass is retained for any consumer still expecting
    the old shape.
    """

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
    vs_s1_percent: float | None = None
    vs_s2_percent: float | None = None


def analyze_from_experiment(metrics: ScenarioMetrics) -> dict[str, Any]:
    """Unified AWS cost model mapping experiment architecture to AWS services.

    Architecture mapping:
      K8s HPA pods  → EKS control plane + EC2 nodes
      Knative pods  → AWS Lambda Provisioned Concurrency

    Per-scenario:
      S1: EKS + EC2 only (all K8s), no Lambda
      S2: Lambda only (all serverless), no EKS/EC2
      S3/S4: EKS + EC2 (K8s share) + Lambda (serverless share)
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

    if metrics.app_duration_serverless_avg_ms > 0:
        metrics.lambda_exec_time_sec = (metrics.app_duration_serverless_avg_ms / 1000.0) + LAMBDA_OVERHEAD_SEC
        metrics.execution_time_source = "app_duration_serverless_avg"
    elif metrics.app_duration_avg_ms > 0 and scenario.startswith("s2"):
        metrics.lambda_exec_time_sec = (metrics.app_duration_avg_ms / 1000.0) + LAMBDA_OVERHEAD_SEC
        metrics.execution_time_source = "app_duration_avg"
    else:
        if scenario.startswith("s1"):
            serverless_pct_tmp = 0.0
        elif scenario.startswith("s2"):
            serverless_pct_tmp = 100.0
        else:
            serverless_pct_tmp = metrics.serverless_traffic_pct
        serverless_requests_tmp = int(metrics.total_requests * (serverless_pct_tmp / 100.0))
        if serverless_requests_tmp > 0 and metrics.knative_cpu_seconds > 1.0:
            knative_cpu_per_req_sec = metrics.knative_cpu_seconds / serverless_requests_tmp
            metrics.lambda_exec_time_sec = knative_cpu_per_req_sec / POD_CPU_REQUEST + LAMBDA_OVERHEAD_SEC
            metrics.execution_time_source = "knative_cpu_per_serverless_req"
        else:
            # Calibration fallback: metrics-server misses CPU bursts for short-lived
            # fib requests. Use measured compute time from capacity test (SeBS: arXiv:2012.14132).
            # Note: Lambda bills WALL-CLOCK duration. fib(33) is pure CPU (14ms).
            # Real workloads add I/O waits (50-200ms), making serverless 3-10× more expensive.
            metrics.lambda_exec_time_sec = CALIBRATION.lambda_compute_ms / 1000 + LAMBDA_OVERHEAD_SEC
            metrics.execution_time_source = "calibration_measured"

    # --- Serverless request routing ---
    if scenario.startswith("s1"):
        serverless_pct = 0.0
    elif scenario.startswith("s2"):
        serverless_pct = 100.0
    else:
        serverless_pct = metrics.serverless_traffic_pct

    serverless_rps = rps * (serverless_pct / 100.0)
    serverless_requests = int(metrics.total_requests * (serverless_pct / 100.0))

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

    # === LAMBDA PROVISIONED CONCURRENCY ===
    lambda_capacity = lambda_execution = lambda_requests = lambda_overflow = 0.0
    data_transfer_cost = 0.0

    if has_serverless and metrics.lambda_pc_instances > 0:
        pc_billable_sec = math.ceil(metrics.duration_sec / 300) * 300
        pc_gb_seconds = metrics.lambda_pc_instances * LAMBDA_MEM_GB * pc_billable_sec
        lambda_capacity = pc_gb_seconds * LAMBDA_PC_RATE

        exec_gb_seconds = serverless_requests * LAMBDA_MEM_GB * metrics.lambda_exec_time_sec
        lambda_execution = exec_gb_seconds * LAMBDA_PC_EXEC_RATE

        lambda_requests = serverless_requests / 1_000_000 * LAMBDA_REQUEST_RATE

        pc_capacity_rps = (
            metrics.lambda_pc_instances / metrics.lambda_exec_time_sec if metrics.lambda_exec_time_sec > 0 else 0
        )
        # Size overflow from peak demand, not run-average (ClarkNet peak/mean ≈ 2.25)
        peak_serverless_rps = serverless_rps * 2.25
        overflow_rps = max(0, peak_serverless_rps - pc_capacity_rps)
        overflow_requests = int(overflow_rps * metrics.duration_sec)
        if overflow_requests > 0:
            overflow_gb_seconds = overflow_requests * LAMBDA_MEM_GB * metrics.lambda_exec_time_sec
            lambda_overflow = overflow_gb_seconds * LAMBDA_ONDEMAND_RATE

        avg_response_bytes = 1024  # ~1KB JSON for fib(34)
        data_transfer_gb = (serverless_requests * avg_response_bytes) / (1024**3)
        data_transfer_cost = data_transfer_gb * 0.09

    lambda_total = lambda_capacity + lambda_execution + lambda_requests + lambda_overflow + data_transfer_cost
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
    successful_rps = slo_compliant_requests / metrics.duration_sec if metrics.duration_sec > 0 else 0.0

    def per_m(cost: float, count: int) -> float:
        return round(cost / count * 1_000_000, 2) if count > 0 else 0.0

    return {
        "scenario": metrics.scenario,
        "duration_sec": metrics.duration_sec,
        "total_requests": metrics.total_requests,
        "successful_requests": metrics.successful_requests,
        "slo_compliant_requests": slo_compliant_requests,
        "slo_noncompliant_requests": max(0, metrics.total_requests - slo_compliant_requests),
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
            "lambda_overflow": round(lambda_overflow, 6),
            "data_transfer": round(data_transfer_cost, 6),
            "total": round(aws_total, 6),
        },
        "stress_harness_ec2": {
            "base_node": round(base_node_hours * EC2_T3_MEDIUM_RATE, 6),
            "dynamic_nodes": round(dynamic_hours * EC2_T3_MEDIUM_RATE, 6),
            "total": round(ec2_stress_total, 6),
        },
        "per_million_requests": per_m(aws_total, metrics.total_requests),
        "per_million_successful": per_m(aws_total, metrics.successful_requests),
        "per_million_slo_compliant": per_m(aws_total, slo_compliant_requests),
        "usd_per_successful_request": round(aws_total / metrics.successful_requests, 8)
        if metrics.successful_requests > 0
        else 0.0,
        "successful_requests_per_usd": round(metrics.successful_requests / aws_total, 2) if aws_total > 0 else 0.0,
    }


def compute_cost_proxy(results: list[dict]) -> dict[str, Any]:
    """Per-run cost proxy metrics per thesis §3.5.2.

    ``cost(β) = k8s_WTP + β × srv_WTP``, normalized so the S1 mean = 1.0
    for each β. Returns ``per_run`` and ``per_scenario`` summaries.
    """
    out: dict[str, Any] = {"per_run": [], "per_scenario": {}}

    for r in results:
        k8s = r["k8s_weight_time_product"]
        srv = r["serverless_weight_time_product"]
        total_wt = k8s + srv

        serverless_share = srv / total_wt if total_wt > 0 else 0.0
        total_req = r["total_requests"]
        violation_rate = r["slo_violations_k6"] / total_req if total_req > 0 else 0.0

        cost_proxies = {f"beta_{beta}": k8s + beta * srv for beta in BETA_VALUES}

        out["per_run"].append(
            {
                "scenario": r["scenario"],
                "run_id": r["run_id"],
                "k8s_weight_time_product": k8s,
                "serverless_weight_time_product": srv,
                "serverless_share": serverless_share,
                "total_requests": total_req,
                "slo_violations_k6": r["slo_violations_k6"],
                "violation_rate": violation_rate,
                **cost_proxies,
            }
        )

    # Normalize to S1 mean = 1.0 for each beta
    s1_runs = [pr for pr in out["per_run"] if pr["scenario"] == "s1-k8s-only"]
    normalization = {}
    for beta in BETA_VALUES:
        key = f"beta_{beta}"
        s1_mean = float(np.mean([pr[key] for pr in s1_runs])) if s1_runs else 1.0
        normalization[key] = s1_mean

    for pr in out["per_run"]:
        for beta in BETA_VALUES:
            key = f"beta_{beta}"
            norm_key = f"beta_{beta}_normalized"
            pr[norm_key] = pr[key] / normalization[key] if normalization[key] > 0 else 0.0

    # Per-scenario summary
    for s in SCENARIO_ORDER:
        runs = [pr for pr in out["per_run"] if pr["scenario"] == s]
        if not runs:
            continue
        summary: dict[str, Any] = {
            "n": len(runs),
            "serverless_share_mean": float(np.mean([r["serverless_share"] for r in runs])),
            "serverless_share_std": float(np.std([r["serverless_share"] for r in runs], ddof=1)),
            "violation_rate_mean": float(np.mean([r["violation_rate"] for r in runs])),
            "violation_rate_std": float(np.std([r["violation_rate"] for r in runs], ddof=1)),
        }
        for beta in BETA_VALUES:
            raw_key = f"beta_{beta}"
            norm_key = f"beta_{beta}_normalized"
            summary[f"{raw_key}_mean"] = float(np.mean([r[raw_key] for r in runs]))
            summary[f"{raw_key}_std"] = float(np.std([r[raw_key] for r in runs], ddof=1))
            summary[f"{norm_key}_mean"] = float(np.mean([r[norm_key] for r in runs]))
            summary[f"{norm_key}_std"] = float(np.std([r[norm_key] for r in runs], ddof=1))
        out["per_scenario"][s] = summary

    return out
