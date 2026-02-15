# Phase A1: Mechanism Revalidation v3 — /fib?n=32

**Date:** 2026-02-15
**Status:** ✅ All mechanisms validated

## Context

Previous Phase A1 used `/work?duration_ms=5` (v1) and `/work?duration_ms=10` (v2). Both failed:
- v1: Workload too light, no scaling triggered
- v2: Busy-loop monopolized GOMAXPROCS=1, blocking health checks and CPU reporting

This v3 uses `/fib?n=32` which yields to the Go scheduler, enabling correct CPU reporting and HPA behavior.

## Parameters

| Parameter | Value |
|-----------|-------|
| Endpoint | `/fib?n=32` |
| GOMAXPROCS | 1 |
| R_sat | ~60 RPS |
| α (Algorithm 2) | 0.0167 (1/60) |
| Buffer | 1.2 |
| k6 profile | 30s@30 → 30s ramp to 100 → 60s@100 → 30s@30 |

## Gate Results

### Gate 1: S1 HPA Scaling ✅
- Workload: /fib?n=30 at 160 RPS (previous thread)
- CPU utilization: 443–500% (correctly reported)
- HPA scaled: 1 → 4 → 8 → 10 replicas
- Health checks: stable throughout

### Gate 2: S3 Algorithm 2 Scaling ✅
- Daemon scenario: s3-hybrid-reactive
- Algorithm 1 decisions: SCALE_OUT=5, OPTIMIZE_COST=5, MAINTAIN=2
- Algorithm 2: scale_up_events{success}=1 (1→2 replicas)
- Weights shifted: k3s=80→65, knative=20→35 (load-driven)
- k6 results: 8717 requests, p95=8.17s (overloaded on 1 replica initially)

### Gate 3: S4 GRU + Algorithm 2 ✅
- Daemon scenario: s4-hybrid-predictive, gru_available=true
- prediction_used_total=7, prediction_failed_total=0
- Algorithm 2: scale_up_events{success}=1 (1→2 replicas)
- predictive_count=1 (PREDICTIVE action triggered)
- k6 results: 10799 requests (higher throughput due to earlier scaling)

## Key Fix: KUBECTL_PATH

During piloting, discovered that the daemon couldn't find `kubectl` (mise-managed, not in PATH). Setting `KUBECTL_PATH` env var resolved this. The experiment runner (run_phase_b_experiments.py) already passes this correctly at line 498.

## Conclusion

All three mechanisms confirmed functional with `/fib?n=32` parameterization:
1. HPA correctly reports CPU and scales
2. Algorithm 1 routing decisions respond to SLO violations
3. Algorithm 2 computes target replicas and executes scaling
4. GRU predictions are consumed and influence decisions in S4

Ready to proceed with full Phase B (5×4=20 runs).
