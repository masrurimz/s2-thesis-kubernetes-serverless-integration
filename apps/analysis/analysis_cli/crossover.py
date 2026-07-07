"""S1-vs-S2 cost crossover analysis + multi-cloud projection constants.

Ported from ``apps/scripts/scripts/cost_analyzer.py`` (``_s1_cost_per_hour``,
``_s2_cost_per_hour``, ``_find_crossover``, ``generate_crossover_graph`` +
the GCP/Cloudflare pricing constants used by the multi-cloud monthly
projection table).

These are CLI/presentation concerns (analytical sweep + multi-cloud
projection), so they live here rather than in ``libs/analysis``.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Optional, TypedDict

from analysis.constants import (
    CLOUD_NODES,
    DEFAULT_CLOUD_NODE,
    EKS_CONTROL_PLANE_RATE,
    LAMBDA_MEM_GB,
    LAMBDA_OVERHEAD_SEC,
    LAMBDA_PC_EXEC_RATE,
    LAMBDA_PC_RATE,
    LAMBDA_REQUEST_RATE,
    POD_CPU_REQUEST,
    TARGET_CPU_UTIL,
)

# ---------------------------------------------------------------------------
# Multi-cloud pricing constants (used by the monthly projection table in
# the `cost` command). us-east-1 / us-central1 / Cloudflare Paid, 2025 list.
# ---------------------------------------------------------------------------
# GCP Cloud Run (us-central1, 2025)
GCP_REQUEST_RATE = 0.40  # $/1M requests
GCP_VCPU_SEC_RATE = 0.000024  # $/vCPU-second
GCP_MEM_GB_SEC_RATE = 0.0000025  # $/GB-second (memory)
GCP_FREE_REQUESTS = 2_000_000  # per month free tier
GCP_FREE_VCPU_SEC = 360_000  # per month
GCP_FREE_GB_SEC = 180_000  # per month

# Cloudflare Workers (Paid plan, 2025)
CF_BASE_FEE = 5.00  # $/month base subscription
CF_REQUEST_RATE = 0.30  # $/1M requests (after 10M free)
CF_FREE_REQUESTS = 10_000_000  # per month
CF_CPU_MS_RATE = 0.02  # $/1M CPU-ms (after 30M free)
CF_FREE_CPU_MS = 30_000_000  # per month


class Workload(TypedDict):
    label: str
    cpu_per_request_sec: float


def _s1_cost_per_hour(rps: float, cpu_per_request_sec: float) -> float:
    """Analytical $/hr for S1 (EKS control plane + EC2 nodes) at a given RPS."""
    cloud_node = CLOUD_NODES[DEFAULT_CLOUD_NODE]
    node_cpu_capacity = cloud_node["allocatable_cpu"] * TARGET_CPU_UTIL
    nodes_needed = math.ceil(rps * cpu_per_request_sec / node_cpu_capacity) if rps > 0 else 0
    production_nodes = max(1, nodes_needed) + 1  # +1 HA
    return EKS_CONTROL_PLANE_RATE + production_nodes * cloud_node["rate"]


def _s2_cost_per_hour(rps: float, cpu_per_request_sec: float) -> float:
    """Analytical $/hr for S2 (Lambda Provisioned Concurrency) at a given RPS."""
    if rps <= 0:
        return 0.0
    exec_time = cpu_per_request_sec / POD_CPU_REQUEST + LAMBDA_OVERHEAD_SEC
    pc_instances = math.ceil(rps * exec_time)
    capacity_cost = pc_instances * LAMBDA_MEM_GB * 3600 * LAMBDA_PC_RATE
    execution_cost = rps * 3600 * LAMBDA_MEM_GB * exec_time * LAMBDA_PC_EXEC_RATE
    request_cost = rps * 3600 / 1_000_000 * LAMBDA_REQUEST_RATE
    return capacity_cost + execution_cost + request_cost


def _find_crossover(rps_values: list[int], s1_costs: list[float], s2_costs: list[float]) -> Optional[dict[str, float]]:
    """Find the RPS at which S1 and S2 cost curves cross (linear interpolation)."""
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
    """Generate the analytical S1 vs S2 cost-crossover graph (PNG + PDF)."""
    import matplotlib.pyplot as plt

    output_dir.mkdir(parents=True, exist_ok=True)

    workloads: list[Workload] = [
        {"label": "fib(32)", "cpu_per_request_sec": 0.01090},
        {"label": "fib(34)", "cpu_per_request_sec": 0.01090 * 2.6},
        {"label": "fib(35)", "cpu_per_request_sec": 0.01090 * (55 / 8)},
    ]

    rps_values = list(range(1, 501))
    fig, ax = plt.subplots(figsize=(10, 6), facecolor="white")
    ax.set_facecolor("white")

    crossover_points: dict[str, dict[str, float]] = {}
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
