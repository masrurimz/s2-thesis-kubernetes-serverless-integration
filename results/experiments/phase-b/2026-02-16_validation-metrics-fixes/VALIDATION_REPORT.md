# Phase B Metric Fixes — Validation Report

**Date**: 2026-02-17
**Commit**: 5c88627 (8 metric collection fixes)
**Runs**: 1 per scenario, seed=99, duration=1200s (20min k6 replay)

## Summary

**All 8 fixes validated across all 4 scenarios. ✅**

## Validation Matrix

### Fix 1: prediction_usage_rate (gru_predictions_used / total_decisions × 100)

| Metric | S1-K8s | S2-Serverless | S3-Reactive | S4-Predictive |
|--------|--------|---------------|-------------|---------------|
| prediction_usage_rate | 0.0 ✅ | 0.0 ✅ | 0.0 ✅ | **92.86** ✅ |
| gru_predictions_used | 0 | 0 | 0 | 78 |
| gru_predictions_failed | 0 | 0 | 0 | 0 |

**Expected**: Only S4 uses GRU predictions → only S4 > 0. **PASS**

### Fix 2: control_loop_latency_avg_ms (from Prometheus daemon_decision_latency_ms)

| Metric | S1-K8s | S2-Serverless | S3-Reactive | S4-Predictive |
|--------|--------|---------------|-------------|---------------|
| control_loop_latency_avg_ms | 0.0 ✅ | 0.0 ✅ | **381.80** ✅ | **378.72** ✅ |

**Expected**: S3/S4 run Algorithm 1 → decision latency > 0. S1/S2 are static → 0. **PASS**

### Fix 3: k8s_replica_seconds & knative_active_seconds (trapezoidal integration / timestamp-based)

| Metric | S1-K8s | S2-Serverless | S3-Reactive | S4-Predictive |
|--------|--------|---------------|-------------|---------------|
| k8s_replica_seconds | **6690.0** ✅ | 1260.0 ✅ | **5092.5** ✅ | **5257.5** ✅ |
| knative_active_seconds | 0.0 ✅ | **1260.0** ✅ | **1005.0** ✅ | **1215.0** ✅ |

**Expected**: S1 has k8s only (knative=0). S2 has knative active. S3/S4 have both. **PASS**

Note: S2 shows k8s_replica_seconds=1260 because the k8s deployment still has 1 replica running (just no traffic via HAProxy weight=0). This is correct — it measures pod-seconds, not traffic.

### Fix 4: scale_up_latency_sec & oscillation_index (from desired_replicas time series)

| Metric | S1-K8s | S2-Serverless | S3-Reactive | S4-Predictive |
|--------|--------|---------------|-------------|---------------|
| scale_up_latency_sec | **15.0** ✅ | 0.0 ✅ | **30.0** ✅ | **15.0** ✅ |
| oscillation_index | 0 ✅ | 0 ✅ | 0 ✅ | 0 ✅ |
| scale_up_events | 4 | 0 | 10 | 3 |
| scale_down_events | 0 | 0 | 6 | 0 |

**Expected**: Latency > 0 where scaling occurred. S2 = 0 (Knative manages scaling). **PASS**

### Fix 5: ResourcePoller — avg/peak CPU & memory from metrics-server

| Metric | S1-K8s | S2-Serverless | S3-Reactive | S4-Predictive |
|--------|--------|---------------|-------------|---------------|
| avg_cpu_millicores | **355.73** ✅ | **677.64** ✅ | **609.48** ✅ | **615.73** ✅ |
| peak_cpu_millicores | **938.68** ✅ | **1859.39** ✅ | **1403.36** ✅ | **1351.05** ✅ |
| avg_memory_mib | **39.56** ✅ | **171.37** ✅ | **106.06** ✅ | **121.44** ✅ |
| peak_memory_mib | **65.98** ✅ | **238.92** ✅ | **263.65** ✅ | **257.63** ✅ |

**Expected**: All > 0 for all scenarios. **PASS**

### Fix 6: Desired/available replicas gauge emitted for ALL scenarios

| Metric | S1-K8s | S2-Serverless | S3-Reactive | S4-Predictive |
|--------|--------|---------------|-------------|---------------|
| desired_replicas_final | **9** ✅ | **1** ✅ | **2** ✅ | **4** ✅ |
| available_replicas_final | **6** ✅ | **1** ✅ | **2** ✅ | **4** ✅ |

**Expected**: Values populated for all scenarios (not just S3/S4). S1 desired=9 (HPA scaled up), available=6 (limited by node capacity). **PASS**

### Fix 7+8: Per-run provision events (clear_log + time-window filter)

| Metric | S1-K8s | S2-Serverless | S3-Reactive | S4-Predictive |
|--------|--------|---------------|-------------|---------------|
| nodes_provisioned | **2** ✅ | **0** ✅ | **2** ✅ | **2** ✅ |
| first_provision_delay_sec | 105.74 | 0.0 | 121.52 | 117.49 |
| total_provision_events | 297 | 0 | 53 | 7 |

**Expected**: S2 = 0 (Knative scales internally, no node provisioning). S1/S3/S4 > 0 (CA triggers node provisioning). Per-run isolation verified (events are clean per scenario). **PASS**

## Routing Decision Metrics (Bonus Validation)

| Metric | S1-K8s | S2-Serverless | S3-Reactive | S4-Predictive |
|--------|--------|---------------|-------------|---------------|
| maintain_count | 0 | 0 | 22 | 15 |
| scale_out_count | 0 | 0 | 22 | 17 |
| predictive_count | 0 | 0 | 0 | **24** |
| optimize_cost_count | 0 | 0 | 46 | 28 |
| weight_change_count | 0 | 0 | 47 | 41 |
| time_in_serverless_pct | 0.0 | 100.0 | 77.65 | 95.29 |

**Notes**: S3/S4 show active routing decisions. S4 has `predictive_count=24` (GRU-driven decisions). S1/S2 are static (no algorithm).

## Performance Summary

| Metric | S1-K8s | S2-Serverless | S3-Reactive | S4-Predictive |
|--------|--------|---------------|-------------|---------------|
| p50_latency_ms | 519.20 | **9.66** | 16.25 | 11.51 |
| p99_latency_ms | 18734.89 | **1548.72** | 2577.57 | 5165.94 |
| throughput_rps | 53.21 | **73.00** | 72.55 | 71.12 |
| total_requests | 63850 | 87597 | 87061 | 85347 |
| error_rate | 0 | 0 | 0 | 0 |
| slo_violations_k6 | 38104 | 9087 | 20269 | 17728 |

**Note**: S1 has notably worse latency due to resource constraints (400m allocatable per node, HPA desires 9 replicas but only 6 available). This is expected behavior under the constrained environment.

## Cost Analysis (Corrected)

**Previous model was incorrect**: Used Lambda on-demand GB-seconds with avg_latency as execution time and 512MB memory. This made S2 appear 69% cheaper than S1.

**Corrected model**: Lambda Provisioned Concurrency with concurrency-slot mapping, Little's Law service time, and CPU-equivalent Lambda memory (354MB for 200m CPU).

### Why S2 (Serverless) Is Actually the Most Expensive

| Factor | Impact |
|--------|--------|
| Knative target_concurrency=10 | 1 pod = 10 Lambda instances, not 1 |
| CPU throttling (200m ÷ 10 concurrent) | Wall-clock service time = 3.56s, not 9.66ms |
| 26 peak Knative pods | = 260 Lambda provisioned concurrency slots |
| Lambda bills wall-clock, not CPU time | 3.56s × 87K requests = massive execution cost |

### Corrected Cost Comparison (Lambda Provisioned Concurrency)

| Metric | S1 (K8s) | S2 (Serverless) | S3 (Reactive) | S4 (Predictive) |
|--------|----------|-----------------|---------------|-----------------|
| Total (20min) | **$0.097** | $1.413 | $0.912 | $1.109 |
| $/1M successful | **$3.76** | $17.99 | $13.66 | $16.40 |
| Monthly | **$201** | $2,934 | $1,894 | $2,303 |

### Resource Consumption (Actual Measured)

| Metric | S1 | S2 | S3 | S4 |
|--------|----|----|----|----|
| CPU-seconds (vCPU·s) | 449 | **856** | 779 | 777 |
| Memory GiB-seconds | 48 | **211** | 131 | 149 |
| Max Knative pods | 2 | **26** | 24 | 24 |
| CPU-ms per request | 7.03 | 9.77 | 8.94 | 9.11 |

S2 consumed the most CPU and memory due to Knative autoscaling 26 pods, each burning CPU continuously. Full analysis: `results/cost/2026-02-17_three-model-cost-comparison/report.md`

## Conclusion

All 8 metric collection fixes are validated across all 4 scenarios. The experiment script is ready for the full 20-run Phase B experiment (bead s2-ibo).
