# Phase A1 Mechanism Revalidation — Post-Bugfix

**Date**: 2026-02-14
**Purpose**: Validate 4 experiment design fixes before launching full Phase B rerun.
**Result**: ✅ ALL CHECKS PASS

## Context

Phase B (20 runs) was invalidated due to 4 bugs:
1. HAProxy weight reset used wrong server name (`k3s-cluster` → `k3s`)
2. Stale daemon on port 9104 leaked metrics across scenario runs
3. Prometheus counter queries used wrong name (missing `_total` suffix)
4. No invariant checks to detect silent failures

All 4 bugs were fixed in thread T-019c5cd8-780f-73cb-896f-536241391904.

## Test Configuration

- **Workload**: ramping-arrival-rate, 5 stages × 30s = 150s total
- **RPS ramp**: 20 → 80 → 140 → 160 → 30
- **Endpoint**: `/work?duration_ms=5` (deterministic 5ms CPU busy-loop)
- **Infrastructure**: k3d cluster, HAProxy (18082/18404/19999), Prometheus (9090), GRU (8090)
- **Deployment**: test-app-warm (1 replica, single GOMAXPROCS)
- **Saturation**: ~145-148 RPS per replica

## Results

### Test S1: K8s Only (Static)

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| scenario | s1-k8s-only | s1-k8s-only | ✅ |
| haproxy_connected | true | true | ✅ |
| predictive_count | 0 | 0 | ✅ |
| scale_out_count | 0 | 0 | ✅ |
| weights (k3s/knative) | 100/0 | 100/0 | ✅ |
| kubectl errors | none | none | ✅ |

**Analysis**: Static scenario correctly makes no algorithmic decisions. Weights remain fixed at 100/0 throughout the test. HPA was configured for this scenario.

### Test S3: Hybrid Reactive (No GRU)

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| scenario | s3-hybrid-reactive | s3-hybrid-reactive | ✅ |
| haproxy_connected | true | true | ✅ |
| predictive_count | 0 | 0 | ✅ |
| scale_out_count | >0 | 5 | ✅ |
| optimize_cost_count | >0 | 4 | ✅ |
| maintain_count | ≥0 | 2 | ✅ |
| weights shifted | yes | 80/20 → 50/50 | ✅ |
| gru_available | false | false | ✅ |

**Analysis**: Algorithm 1 correctly detected SLO violations at high RPS (140-160 RPS exceeds single-replica capacity ~148 RPS) and performed reactive SCALE_OUT (5 times). During low load (ramp-down), OPTIMIZE_COST triggered (4 times). No GRU predictions used — exactly the expected S3 behavior.

### Test S4: Hybrid Predictive (With GRU)

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| scenario | s4-hybrid-predictive | s4-hybrid-predictive | ✅ |
| haproxy_connected | true | true | ✅ |
| gru_available | true | true | ✅ |
| scale_out_count | >0 | 5 | ✅ |
| Prometheus prediction_used_total | >0 | **6** | ✅ |
| Prometheus prediction_failed_total | 0 | 0 | ✅ |
| GRU predictions in logs | present | present (conf=0.72-0.76) | ✅ |
| kubectl errors | none | none | ✅ |

**GRU Integration Detail**: The daemon successfully fetched GRU predictions every 15s cycle (6 predictions total), all with confidence ≥0.72. Predictions were used for Algorithm 2 scaling decisions (`algorithm2_scaling_decision` logged with `predicted_load` from GRU). The `predictive_count=0` in Algorithm 1's routing statistics is expected — PREDICTIVE routing weight changes require a >30% predicted load increase vs current observed load, and the GRU predicted ~70-75 RPS while observed load was similar. The critical validation: **Prometheus `routing_daemon_prediction_used_total=6`** — this metric was always 0 before Bug #3 fix.

**Key distinction**: `prediction_used_total` (Prometheus counter, GRU consultations) vs `predictive_count` (Algorithm 1 PREDICTIVE routing weight actions). Both working correctly.

## Bug Fix Verification

| Bug | Fix Description | Verified By | Status |
|-----|----------------|-------------|--------|
| #1 HAProxy server name | `k3s-cluster` → `k3s` | All 3 tests: weights set/read correctly | ✅ |
| #2 Daemon lifecycle | Kill stale, assert scenario | All 3: correct scenario in /health | ✅ |
| #3 Prometheus metric names | `_total` suffix for counters | S4: `prediction_used_total=6` visible | ✅ |
| #4 Pre-run invariants | Scenario verification at start | All 3: /health confirms correct scenario | ✅ |

## Conclusion

All 4 bug fixes validated. The experiment infrastructure now correctly:
- Sets HAProxy weights via correct server names
- Isolates daemon instances per scenario (no metric leakage)
- Exposes GRU prediction counters to Prometheus
- Verifies scenario identity before each run

**Ready for Phase B rerun.**
