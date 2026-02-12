#!/usr/bin/env python3
"""
Cloud Cost Analysis for Thesis Scenarios (S1, S2, S3, S4)

Fixes vs previous version:
1) Serverless compute unit bug: use GB-seconds pricing (NOT GB-ms).
2) Kubernetes node pricing: charge by node instance $/hour (avoid CPU+RAM double counting).
3) AKS control plane should be $0.00 (free) instead of $0.10.
4) Use real list pricing for AWS Lambda + EKS and reasonable GCP/Azure equivalents.

Notes / simplifications (kept intentionally):
- We ignore free tiers (Lambda/Azure/GCP) to keep comparisons linear and easier to interpret.
- K8s node scaling is simplified (autoscaler-like): pay for an integer number of nodes
  based on a utilization factor, with a minimum node count when a cluster is "enabled".
- GCP serverless is modeled using Cloud Run request-based pricing (vCPU + memory + requests),
  because Cloud Functions Gen2 runs on Cloud Run.
"""

import json
import math
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "controller"))

import structlog

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class CloudPricing:
    provider: str  # AWS, GCP, Azure

    # Kubernetes costs
    k8s_control_plane_cost_per_hour: float  # EKS/GKE fee; AKS = 0
    k8s_node_instance_cost_per_hour: float  # price of a representative 2 vCPU / 8GB node VM

    # Serverless request cost
    serverless_request_cost_per_million: float  # $ per 1,000,000 requests/executions

    # Serverless compute costs
    # If serverless_compute_cost_per_gb_second > 0, compute is billed as GB-seconds (AWS Lambda / Azure Functions).
    serverless_compute_cost_per_gb_second: float = 0.0

    # If vCPU+memory model is used (GCP Cloud Run request-based)
    serverless_compute_cost_per_vcpu_second: float = 0.0
    serverless_compute_cost_per_gib_second: float = 0.0

    # Data transfer out (very rough; varies by tier/region)
    data_transfer_cost_per_gb: float = 0.09


@dataclass
class CostBreakdown:
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


class CloudCostSimulator:
    """
    Pricing baselines are chosen for clarity, not for perfect per-region fidelity.
    """

    # AWS (commonly cited us-east-1 list prices)
    # - Lambda: $0.20 / 1M requests; $0.0000166667 / GB-second (x86)
    # - EKS control plane: $0.10 / hour
    # - Node example: m5.large on-demand ~$0.096 / hour
    AWS_PRICING = CloudPricing(
        provider="AWS",
        k8s_control_plane_cost_per_hour=0.10,  # EKS
        k8s_node_instance_cost_per_hour=0.096,  # m5.large (2 vCPU, 8 GiB)
        serverless_request_cost_per_million=0.20,  # Lambda requests
        serverless_compute_cost_per_gb_second=0.0000166667,  # Lambda GB-second (x86)
        data_transfer_cost_per_gb=0.09,
    )

    # GCP (Cloud Run request-based, us-central1 list prices)
    # - Requests: $0.40 / 1M
    # - CPU: $0.000024 / vCPU-second (active)
    # - Memory: $0.0000025 / GiB-second (active)
    # - GKE cluster management: often modeled as $0.10/hr (ignoring the free tier credit here)
    # - Node example: e2-standard-2 is $0.06701142/hr in us-central1
    GCP_PRICING = CloudPricing(
        provider="GCP",
        k8s_control_plane_cost_per_hour=0.10,  # GKE mgmt fee (ignoring free credit)
        k8s_node_instance_cost_per_hour=0.06701142,  # e2-standard-2 (2 vCPU, 8 GiB)
        serverless_request_cost_per_million=0.40,  # Cloud Run requests (per 1M)
        serverless_compute_cost_per_vcpu_second=0.000024,  # Cloud Run CPU active time
        serverless_compute_cost_per_gib_second=0.0000025,  # Cloud Run memory active time
        data_transfer_cost_per_gb=0.12,  # rough; egress varies
    )

    # Azure
    # - AKS control plane: free ($0), pay for nodes
    # - Azure Functions Consumption: commonly $0.20 / 1M + ~$0.000016 / GB-second
    # - Node VM: choose a representative 2 vCPU / 8 GiB Linux VM.
    #   NOTE: exact VM pricing varies by region/SKU; adjust to your chosen VM if needed.
    AZURE_PRICING = CloudPricing(
        provider="Azure",
        k8s_control_plane_cost_per_hour=0.0,  # AKS control plane is free
        k8s_node_instance_cost_per_hour=0.096,  # representative 2 vCPU / 8 GiB Linux VM (adjust if needed)
        serverless_request_cost_per_million=0.20,  # Functions executions
        serverless_compute_cost_per_gb_second=0.000016,  # Functions GB-second
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
        """
        K8s model:
        - If enabled=False, cluster doesn't exist => $0.
        - If enabled=True, control plane is charged + N node instances charged.
        - Nodes are scaled to an integer count based on utilization, but never below min_nodes.
        """
        if not enabled:
            return {"control_plane": 0.0, "nodes": 0.0, "total": 0.0, "node_count": 0}

        control_plane_cost = self.pricing.k8s_control_plane_cost_per_hour * duration_hours

        # simplified autoscaler model: scale between min_nodes and max_nodes
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
        """
        Serverless model supports:
        - AWS/Azure style GB-second billing: cost_per_gb_second
        - GCP Cloud Run style vCPU-second + GiB-second billing

        Unit correctness:
        - execution_seconds = avg_execution_ms / 1000
        - GB-seconds = (memory_mb / 1024) * execution_seconds * num_requests
        """
        if num_requests <= 0:
            return {"requests": 0.0, "compute": 0.0, "total": 0.0}

        request_cost = (num_requests / 1_000_000) * self.pricing.serverless_request_cost_per_million

        exec_seconds = avg_execution_ms / 1000.0

        # GCP Cloud Run model (vCPU + GiB)
        if self.pricing.serverless_compute_cost_per_vcpu_second > 0 or self.pricing.serverless_compute_cost_per_gib_second > 0:
            vcpu_seconds = num_requests * gcp_vcpu * exec_seconds
            gib_seconds = num_requests * (memory_mb / 1024.0) * exec_seconds  # treat GiB ~= GB for this model

            compute_cost = (
                vcpu_seconds * self.pricing.serverless_compute_cost_per_vcpu_second
                + gib_seconds * self.pricing.serverless_compute_cost_per_gib_second
            )
        else:
            # AWS/Azure GB-second model
            gb_seconds = num_requests * (memory_mb / 1024.0) * exec_seconds
            compute_cost = gb_seconds * self.pricing.serverless_compute_cost_per_gb_second

        total = request_cost + compute_cost
        return {
            "requests": round(request_cost, 2),
            "compute": round(compute_cost, 2),
            "total": round(total, 2),
        }

    def analyze_scenario(
        self,
        scenario: str,
        duration_hours: float,
        total_requests: int,
        k8s_percentage: float,
        avg_latency_ms: float,
    ) -> CostBreakdown:
        logger.info("analyzing_scenario", scenario=scenario, provider=self.pricing.provider)

        k8s_requests = int(total_requests * (k8s_percentage / 100.0))
        serverless_requests = total_requests - k8s_requests

        # If scenario is serverless-only, we assume no k8s cluster exists at all.
        k8s_enabled = k8s_requests > 0

        # very simple utilization heuristic
        avg_util = 0.30 if k8s_enabled else 0.0

        k8s_costs = self.calculate_k8s_cost(
            duration_hours=duration_hours,
            enabled=k8s_enabled,
            avg_utilization=avg_util,
            max_nodes=3,
            min_nodes=1,
        )

        serverless_costs = self.calculate_serverless_cost(
            num_requests=serverless_requests,
            avg_execution_ms=avg_latency_ms,
            memory_mb=512.0,
            gcp_vcpu=0.25,  # chosen to represent a small function-like container
        )

        # Data transfer: assume 1KB response per request (rough)
        data_transfer_gb = (total_requests * 1000) / (1024 ** 3)
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


def print_cost_report(results: Dict[str, CostBreakdown], provider: str) -> None:
    print("\n" + "=" * 80)
    print(f"CLOUD COST ANALYSIS - {provider}")
    print("=" * 80)

    print(f"\n{'Scenario':<25} {'Total Cost':>12} {'vs S1':>12} {'vs S2':>12} {'$/1M req':>12}")
    print("-" * 80)

    for name, r in results.items():
        vs_s1 = f"{r.vs_s1_percent:+.1f}%" if r.vs_s1_percent is not None else "N/A"
        vs_s2 = f"{r.vs_s2_percent:+.1f}%" if r.vs_s2_percent is not None else "N/A"
        print(f"{name:<25} ${r.total_cost:>10.2f} {vs_s1:>11} {vs_s2:>11} ${r.cost_per_million_requests:>10.2f}")

    print("-" * 80)

    s4 = results.get("S4 (Hybrid Predictive)")
    if s4:
        print(f"\nS4 (Hybrid Predictive) Cost Breakdown:")
        print(f"  Kubernetes:")
        print(f"    Control Plane:    ${s4.k8s_control_plane_cost:.2f}")
        print(f"    Nodes:            ${s4.k8s_nodes_cost:.2f}")
        print(f"    K8s Total:        ${s4.k8s_total_cost:.2f}")
        print(f"  Serverless:")
        print(f"    Requests:         ${s4.serverless_request_cost:.2f}")
        print(f"    Compute:          ${s4.serverless_compute_cost:.2f}")
        print(f"    Serverless Total: ${s4.serverless_total_cost:.2f}")
        print(f"  Data Transfer:      ${s4.data_transfer_cost:.2f}")
        print(f"  ─────────────────────────────────")
        print(f"  TOTAL:              ${s4.total_cost:.2f}")

    print("\n" + "=" * 80)


def main() -> int:
    time_periods = [
        ("1 hour", 1.0),
        ("1 day", 24.0),
        ("1 month (720hr)", 720.0),
    ]

    requests_per_hour = 360_000  # 100 RPS * 3600

    all_results: Dict[str, Dict[str, CostBreakdown]] = {}

    for period_name, hours in time_periods:
        total_requests = int(requests_per_hour * hours)

        print(f"\n{'#' * 80}")
        print(f"# TIME PERIOD: {period_name}")
        print(f"# Duration: {hours} hours")
        print(f"# Requests: {total_requests:,}")
        print(f"{'#' * 80}")

        for pricing in (CloudCostSimulator.AWS_PRICING, CloudCostSimulator.GCP_PRICING, CloudCostSimulator.AZURE_PRICING):
            sim = CloudCostSimulator(pricing)
            results = sim.compare_all_scenarios(duration_hours=hours, total_requests=total_requests)
            print_cost_report(results, pricing.provider)
            all_results[f"{pricing.provider.lower()}_{period_name}"] = results

    # Save results
    results_dir = Path("results/cost_analysis")
    results_dir.mkdir(parents=True, exist_ok=True)

    results_file = results_dir / f"cost_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    serializable = {k: {sk: asdict(sv) for sk, sv in v.items()} for k, v in all_results.items()}

    with open(results_file, "w") as f:
        json.dump(serializable, f, indent=2)

    print(f"\nFull results saved to: {results_file}")

    # Simple summary (use dataclass attributes, not dict indexing)
    print("\n" + "=" * 80)
    print("COST ANALYSIS SUMMARY")
    print("=" * 80)

    aws_day = all_results.get("aws_1 day")
    if aws_day:
        s1 = aws_day["S1 (K8s-Only)"]
        s2 = aws_day["S2 (Serverless-Only)"]
        s4 = aws_day["S4 (Hybrid Predictive)"]

        print("\nAWS (1 day) - savings of S4:")
        if s1.total_cost:
            savings_vs_s1 = s1.total_cost - s4.total_cost
            pct_s1 = (savings_vs_s1 / s1.total_cost) * 100
            print(f"  vs S1: ${savings_vs_s1:.2f} saved ({pct_s1:.1f}%)")
        if s2.total_cost:
            savings_vs_s2 = s2.total_cost - s4.total_cost
            pct_s2 = (savings_vs_s2 / s2.total_cost) * 100
            print(f"  vs S2: ${savings_vs_s2:.2f} saved ({pct_s2:.1f}%)")

    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
