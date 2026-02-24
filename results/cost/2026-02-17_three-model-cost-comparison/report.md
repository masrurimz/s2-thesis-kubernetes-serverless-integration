# Unified AWS Cost Report: 4 Scenarios (v5)

**Date**: 2026-02-18 (v5 — unified AWS model)
**Source experiment**: `results/experiments/phase-b/2026-02-16_validation-metrics-fixes/`
**Duration**: 1200s per scenario, ClarkNet workload replay
**Analyzer**: `thesis/scripts/cost_analyzer.py` → `controller/results/cost_analysis/cost_analysis_20260218_132358.json`
**Reproduce**: `cd controller && HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python ../thesis/scripts/cost_analyzer.py --experiment-dir ../results/experiments/phase-b/2026-02-16_validation-metrics-fixes`

> **Architecture Mapping.** The experiment runs K8s HPA + Knative KPA on local k3s. For cost projection, this maps to AWS:
> - K8s HPA pods → **EKS control plane** ($0.10/hr) + **EC2 nodes** (t3.medium, $0.0416/hr)
> - Knative KPA pods → **AWS Lambda Provisioned Concurrency**
> - Per scenario: S1 = EKS+EC2 only, S2 = Lambda only, S3/S4 = EKS+EC2+Lambda

---

## Scenario-to-AWS Mapping

| Scenario | EKS Control Plane | EC2 Nodes | Lambda PC |
|----------|:-:|:-:|:-:|
| S1 (K8s-only) | ✅ $0.10/hr | ✅ sized from K8s CPU | ❌ none |
| S2 (Serverless-only) | ❌ none | ❌ none | ✅ all traffic |
| S3 (Hybrid Reactive) | ✅ $0.10/hr | ✅ K8s share CPU | ✅ serverless share |
| S4 (Hybrid Predictive) | ✅ $0.10/hr | ✅ K8s share CPU | ✅ serverless share |

---

## Resource Consumption Summary

| Metric | S1 (K8s) | S2 (Serverless) | S3 (Hybrid Reactive) | S4 (Hybrid Predictive) |
|--------|-------:|-------:|-------:|-------:|
| Total requests | 63,850 | 87,597 | 87,061 | 85,347 |
| Successful requests | 25,746 | 78,510 | 66,792 | 67,619 |
| Success rate | 40.3% | 89.6% | 76.7% | 79.2% |
| Serverless traffic % | 0.0% | 100.0% | 77.6% | 95.3% |
| Serverless requests | 0 | 87,597 | 67,600 | 81,330 |
| K8s CPU-seconds | 448.1 | 0.2 | 552.0 | 464.4 |
| Knative CPU-seconds | 1.0 | 855.4 | 226.7 | 313.0 |
| CPU-ms per successful request | 17.45 | 10.90 | 11.66 | 11.50 |
| Lambda exec time (ms) | 97.2 | 64.5 | 68.3 | 67.5 |
| Lambda PC instances | 0 | 5 | 4 | 5 |
| EC2 production nodes | 2 | 0 | 2 | 2 |

---

## Component Formulas

### EKS Control Plane
- $0.10/hr, present when scenario uses K8s (S1, S3, S4)
- S2 has no K8s traffic → no EKS needed → $0

### EC2 Nodes (K8s demand only)
- `avg_k8s_cpu = k8s_cpu_seconds / duration`
- `nodes = max(1, ceil(avg_k8s_cpu / 1.8 / 0.60), ceil(avg_k8s_mem / 3.5 / 0.70)) + 1 HA`
- Cost = nodes × duration_hours × $0.0416/hr
- S2: 0 nodes → $0

### Lambda Provisioned Concurrency (serverless demand only)
- `cpu_per_request = total_cpu_seconds / successful_requests`
- `lambda_exec_time = cpu_per_request / 0.2 + 0.010` (10ms overhead)
- `serverless_rps = rps × serverless_traffic_pct / 100`
- `pc_instances = ceil(serverless_rps × lambda_exec_time)`
- Memory = 354 MB (CPU-proportional: 200m/1000m × 1769 MB)
- S1: 0% serverless → 0 Lambda cost

---

## Unified AWS Cost per 1200s Run

| Component | S1 | S2 | S3 | S4 |
|-----------|---:|---:|---:|---:|
| EKS control plane | $0.0333 | $0.0000 | $0.0333 | $0.0333 |
| EC2 compute | $0.0277 | $0.0000 | $0.0277 | $0.0277 |
| Lambda capacity | $0.0000 | $0.0086 | $0.0069 | $0.0086 |
| Lambda execution | $0.0000 | $0.0190 | $0.0155 | $0.0184 |
| Lambda requests | $0.0000 | $0.0175 | $0.0135 | $0.0163 |
| **TOTAL** | **$0.0611** | **$0.0451** | **$0.0970** | **$0.1044** |

---

## Cost per 1M Requests

| | S1 | S2 | S3 | S4 |
|---|---:|---:|---:|---:|
| $/1M total requests | $0.96 | $0.52 | $1.11 | $1.22 |
| $/1M successful requests | $2.37 | $0.58 | $1.45 | $1.54 |

---

## Monthly Projection (30d Continuous)

Linear 2160× scaling from 1200s → 30 days. Assumes sustained load.

| Scenario | AWS Total |
|----------|----------:|
| S1 (K8s-only) | $132 |
| S2 (Serverless-only) | $98 |
| S3 (Hybrid Reactive) | $210 |
| S4 (Hybrid Predictive) | $226 |

---

## Key Findings

1. **S2 (pure serverless) is cheapest.** At $0.045/run, Lambda-only avoids the EKS control plane ($0.033/run) and EC2 node ($0.028/run) overhead entirely. This is 26% cheaper than S1 and 57% cheaper than S3/S4.

2. **Hybrid scenarios (S3/S4) are most expensive.** They pay dual infrastructure: EKS+EC2 for the K8s portion AND Lambda for the serverless overflow. S4 is slightly more expensive than S3 because its higher serverless traffic share (95.3% vs 77.6%) drives more Lambda cost while still requiring the same EKS+EC2 base.

3. **Infrastructure overhead dominates K8s costs.** EKS control plane ($0.033) + minimum EC2 HA ($0.028) = $0.061 before any workload runs. At this load level (~53-73 RPS), the infrastructure floor is the primary cost driver.

4. **S1's poor $/successful-request reflects stress-harness constraints.** The 40.3% success rate (from 400m allocatable nodes) inflates S1's cost-per-successful-request to $2.37/M, but this is an artifact of the stress test, not of K8s architecture.

---

## Stress-Harness EC2 (Appendix Reference)

For reference, stress-harness k3d nodes (400m allocatable) produced these costs. **Not for production projection.**

| Component | S1 | S2 | S3 | S4 |
|-----------|---:|---:|---:|---:|
| Base node (1 always-on) | $0.0139 | $0.0139 | $0.0139 | $0.0139 |
| Dynamic nodes | $0.0253 | $0.0000 | $0.0249 | $0.0250 |
| **Total** | **$0.0392** | **$0.0139** | **$0.0388** | **$0.0389** |

---

## Methodology Notes

- **CPU per request**: `total_cpu_seconds / successful_requests` (failed requests consume ~0 CPU)
- **Lambda memory**: 354 MB from CPU-proportional mapping (200m/1000m × 1769 MB = 354 MB)
- **Lambda execution time**: `cpu_per_request / 0.2 vCPU + 10ms overhead`
- **EC2 node sizing**: `ceil(k8s_cpu_demand / (1.8 × 0.60))` with +1 HA headroom
- **EKS control plane**: $0.10/hr (us-east-1, 2025 list prices)
- **Monthly projection**: Linear 2160× scaling — overestimates real-world cost
- **Serverless traffic split**: From routing daemon metrics in result.json

---

*Evidence: `controller/results/cost_analysis/cost_analysis_20260218_132358.json`. Analyzer: `thesis/scripts/cost_analyzer.py` v5.*
