# Final Experiment Numbers

**Date:** 2026-07-11  
**Source:** `results/experiments/phase-b/2026-07-11_scaling_fix_n1` (n=1 diagnostic)  
**Rule:** Thesis Ch4/Ch5/abstracts must use ONLY numbers from this file.

**IMPORTANT:** These are n=1 diagnostic results. n=5 replication required for statistical claims. All previous experiment bundles (Feb 2026, July 8-10) are superseded due to infrastructure fixes (CPU limits, calibration, fairness cap, prediction-scaling separation).

---

## Configuration

| Parameter | Value |
|---|---|
| Node CPU | Docker --cpus=1.0 per node (2 workload nodes = 2.0 CPU total) |
| Pod CPU limits | None (node-level limit sufficient) |
| r_saturation_per_replica | 33.3 (calibrated: S1 saturates at 100 RPS) |
| max_k8s_replicas | 6 (matches schedulable capacity, prevents dynamic nodes) |
| proactive_approach_ratio | 0.8 |
| Workload | ClarkNet g=33, mean 73 RPS, peak 164 RPS |
| SLO threshold | p99 < 200ms |

---

## Scenario Summary (n=1 Diagnostic)

| Scenario | p99 (ms) | SLO Violations | SLO Rate | PREDICTIVE | Serverless % | Nodes |
|---|---|---|---|---|---|---|
| S1 (K8s+HPA) | 2,421.3 | 6,717 | 7.66% | 0 | 0.0% | 0 |
| S2 (Serverless) | 77.7 | 19 | 0.02% | 0 | 100.0% | 0 |
| S3 (Hybrid-reactive) | 98.8 | 3 | 0.00% | 0 | 31.8% | 0 |
| S4 (Hybrid-predictive) | 118.2 | 104 | 0.12% | 9 | 24.7% | 0 |

---

## Cost Analysis (AWS Monthly Projection)

| Scenario | Total/mo | $/1M SLO-OK | Serverless Reqs | EC2 Nodes |
|---|---|---|---|---|
| S1 (K8s-only) | $132 | $0.79 | 0 | 2 |
| S2 (Serverless) | $394 | $2.19 | 87,840 | 0 |
| S3 (Hybrid-reactive) | $147 | $0.81 | 5,354 | 2 |
| S4 (Hybrid-predictive) | $142 | $0.79 | 2,666 | 2 |

---

## Statistical Comparisons (n=1, not significant)

### H1: S4 vs S1 (Hybrid vs Pure K8s)

| Metric | S1 | S4 | Improvement |
|---|---|---|---|
| p99 latency | 2,421ms | 118ms | **-95.1%** |
| SLO violations | 6,717 | 104 | **-98.5%** |

**Verdict:** Strongly confirmed (n=1). Hybrid routing crushes pure K8s.

### H2: S4 vs S3 (Predictive vs Reactive)

| Metric | S3 | S4 | Difference |
|---|---|---|---|
| p99 latency | 99ms | 118ms | +19.7% (S4 worse) |
| SLO violations | 3 | 104 | +3367% (S4 worse) |
| Serverless requests | 5,354 | 2,666 | **-50.2% (S4 better)** |
| Monthly cost | $147 | $142 | **-3.4% (S4 cheaper)** |

**Verdict:** Not confirmed for latency (n=1). S4 provides **cost advantage** through reduced serverless dependency (proactive K8s scaling). n=5 needed.

---

## Key Architecture Decision (July 11, 2026)

**Prediction drives K8s SCALING, not serverless ROUTING.**

Previous architecture: GRU prediction → serverless weight adjustment → over-routing during moderate load → Knative overhead → worse p99.

Fixed architecture: GRU prediction → trend extrapolation → Algorithm 2 proactive K8s replica scaling → more warm capacity → less serverless overflow → lower cost.

This separation ensures S4 never routes MORE to serverless than S3 (avoiding unnecessary Knative overhead), while still benefiting from prediction via earlier K8s scaling.
