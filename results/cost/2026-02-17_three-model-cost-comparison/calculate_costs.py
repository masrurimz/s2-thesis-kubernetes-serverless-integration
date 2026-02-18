#!/usr/bin/env python3
"""
Calculate cost comparison across 3 pricing models for Phase B experiment scenarios.

Models:
  1. AWS Lambda Provisioned Concurrency (min-scale=1 ≈ always-warm)
  2. Google Cloud Run Always-Allocated
  3. Node-Hours (t3.medium reference — most defensible)

Source: results/experiments/phase-b/2026-02-16_validation-metrics-fixes/
"""

import json
import pathlib

# Pricing constants
LAMBDA_PROV_GB_SEC = 0.0000041667
LAMBDA_EXEC_GB_SEC = 0.0000097222
LAMBDA_REQ_PER_M = 0.20
CR_VCPU_SEC = 0.00002400
CR_MEM_SEC = 0.00000250
CR_REQ_PER_M = 0.40
EC2_T3_MEDIUM_HR = 0.0416

# Resource config from K8s manifests
CPU_REQUEST = 0.2  # 200m
MEM_ALLOC_GB = 128 / 1024  # 128Mi = 0.125 GiB
COLD_START_SEC = 0.950
MONTH_SEC = 30 * 24 * 3600

BASE_DIR = pathlib.Path(__file__).parent.parent.parent
EXPERIMENT_DIR = BASE_DIR / "experiments" / "phase-b" / "2026-02-16_validation-metrics-fixes"


def load_scenario(scenario_dir: str) -> dict:
    with open(EXPERIMENT_DIR / scenario_dir / "result.json") as f:
        return json.load(f)


def calc_model1(d: dict) -> dict:
    """AWS Lambda Provisioned Concurrency model."""
    svl_pct = d["time_in_serverless_pct"] / 100.0
    k8s_req = d["total_requests"] * (1.0 - svl_pct)
    svl_req = d["total_requests"] * svl_pct
    p50_sec = d["p50_latency_ms"] / 1000.0

    k8s_prov = d["k8s_replica_seconds"] * MEM_ALLOC_GB * LAMBDA_PROV_GB_SEC
    k8s_exec = k8s_req * p50_sec * MEM_ALLOC_GB * LAMBDA_EXEC_GB_SEC
    kn_prov = d["knative_active_seconds"] * MEM_ALLOC_GB * LAMBDA_PROV_GB_SEC
    kn_exec = svl_req * p50_sec * MEM_ALLOC_GB * LAMBDA_EXEC_GB_SEC
    kn_req = svl_req / 1_000_000 * LAMBDA_REQ_PER_M
    cold = d["weight_change_count"] * COLD_START_SEC * MEM_ALLOC_GB * LAMBDA_EXEC_GB_SEC

    if d["nodes_provisioned"] > 0:
        active = d["duration_sec"] - d["first_provision_delay_sec"]
        node = (active / 3600) * d["nodes_provisioned"] * EC2_T3_MEDIUM_HR
    else:
        node = 0.0

    total = k8s_prov + k8s_exec + kn_prov + kn_exec + kn_req + cold + node
    return {"k8s_prov": k8s_prov, "k8s_exec": k8s_exec, "kn_prov": kn_prov,
            "kn_exec": kn_exec, "kn_req": kn_req, "cold": cold, "node": node, "total": total}


def calc_model2(d: dict) -> dict:
    """Google Cloud Run Always-Allocated model."""
    total_rs = d["k8s_replica_seconds"] + d["knative_active_seconds"]
    vcpu = total_rs * CPU_REQUEST * CR_VCPU_SEC
    mem = total_rs * MEM_ALLOC_GB * CR_MEM_SEC
    req = d["total_requests"] / 1_000_000 * CR_REQ_PER_M

    if d["nodes_provisioned"] > 0:
        active = d["duration_sec"] - d["first_provision_delay_sec"]
        node = (active / 3600) * d["nodes_provisioned"] * EC2_T3_MEDIUM_HR
    else:
        node = 0.0

    total = vcpu + mem + req + node
    return {"vcpu": vcpu, "mem": mem, "req": req, "node": node, "total": total}


def calc_model3(d: dict) -> dict:
    """Node-Hours (t3.medium) model."""
    base_hrs = d["duration_sec"] / 3600
    base_cost = base_hrs * EC2_T3_MEDIUM_HR

    if d["nodes_provisioned"] > 0:
        dyn_sec = d["duration_sec"] - d["first_provision_delay_sec"]
        dyn_hrs = (dyn_sec / 3600) * d["nodes_provisioned"]
        dyn_cost = dyn_hrs * EC2_T3_MEDIUM_HR
    else:
        dyn_hrs = 0.0
        dyn_cost = 0.0

    total = base_cost + dyn_cost
    return {"base_hrs": base_hrs, "base_cost": base_cost,
            "dyn_hrs": dyn_hrs, "dyn_cost": dyn_cost, "total": total}


def main():
    scenario_dirs = {
        "S1": "s1-k8s-only_run1",
        "S2": "s2-serverless-only_run1",
        "S3": "s3-hybrid-reactive_run1",
        "S4": "s4-hybrid-predictive_run1",
    }

    results = {}
    for label, dirname in scenario_dirs.items():
        d = load_scenario(dirname)
        scale = MONTH_SEC / d["duration_sec"]
        succ = d["total_requests"] - d["slo_violations_k6"]

        m1 = calc_model1(d)
        m2 = calc_model2(d)
        m3 = calc_model3(d)

        results[label] = {
            "total_requests": d["total_requests"],
            "successful_requests": succ,
            "success_rate": succ / d["total_requests"] * 100,
            "model1": {**m1, "per_1m": m1["total"] / d["total_requests"] * 1e6,
                       "per_1m_succ": m1["total"] / succ * 1e6, "monthly": m1["total"] * scale},
            "model2": {**m2, "per_1m": m2["total"] / d["total_requests"] * 1e6,
                       "per_1m_succ": m2["total"] / succ * 1e6, "monthly": m2["total"] * scale},
            "model3": {**m3, "per_1m": m3["total"] / d["total_requests"] * 1e6,
                       "per_1m_succ": m3["total"] / succ * 1e6, "monthly": m3["total"] * scale},
        }

    output = pathlib.Path(__file__).parent / "cost_results.json"
    with open(output, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results written to {output}")

    # Print summary table
    print(f"\n{'Scenario':<8} {'M1 Total':>10} {'M2 Total':>10} {'M3 Total':>10} {'M3 $/1M succ':>14}")
    print("-" * 55)
    for label, r in results.items():
        print(f"{label:<8} ${r['model1']['total']:.4f} ${r['model2']['total']:.4f} "
              f"${r['model3']['total']:.4f} ${r['model3']['per_1m_succ']:.4f}")


if __name__ == "__main__":
    main()
