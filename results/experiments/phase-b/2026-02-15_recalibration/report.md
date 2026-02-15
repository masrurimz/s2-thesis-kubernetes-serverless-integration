# Phase B Workload Recalibration — 2026-02-15

## Purpose

Phase B v1 (D=5ms) results showed scale_up_events=0 for ALL S3/S4 runs. Root cause:
- Single pod handles 145 RPS at 5ms busy-loop
- ClarkNet peak is only 164 RPS (1.13× saturation)
- Algorithm 2 computes target_replicas=1 for all loads < 121 RPS
- Neither HPA nor Algorithm 2 ever scaled up
- S3/S4 p99 ≈ 3s was entirely cold-start penalty from routing to idle serverless

## Calibration Results

### D=20ms (too aggressive)

| RPS | p95 (ms) | Error% | Status |
|-----|----------|--------|--------|
| 20  | 21.1     | 0%     | ✅ Healthy |
| 30  | 27.8     | 0%     | ✅ Healthy |
| 35  | 238      | 0%     | ⚠️ Saturating |
| 40  | 7207     | 3.1%   | 💀 Collapsed |

R_sat ≈ 30 RPS. Too low — ClarkNet mean (73 RPS) would need 3+ pods just for average load.

### D=10ms (selected)

| RPS | p95 (ms) | Error% | Status |
|-----|----------|--------|--------|
| 30  | 10.9     | 0%     | ✅ Healthy |
| 40  | 10.9     | 0%     | ✅ Healthy |
| 50  | 11.2     | 0%     | ✅ Healthy (at saturation) |
| 55  | 666      | 0%     | ⚠️ Degraded |
| 58  | 2018     | 0%     | ❌ Saturated |
| 60  | 5651     | 0.06%  | 💀 Collapsed |

**R_sat ≈ 50 RPS** (p95 stays < 200ms up to ~50 RPS).

## Selected Parameters

| Parameter | Old (D=5ms) | New (D=10ms) | Rationale |
|-----------|-------------|--------------|-----------|
| duration_ms | 5 | 10 | 2× heavier per request |
| R_sat | 145 RPS | 50 RPS | Measured single-pod saturation |
| α | 0.0069 (1/145) | 0.02 (1/50) | 1/R_sat |
| target at mean (73 RPS) | 1 replica | 2 replicas | Scaling exercised in steady state |
| target at peak (164 RPS) | 2 replicas | 4 replicas | Significant scaling at burst |
| Stages needing >1 pod | 4/40 (10%) | 34/40 (85%) | Scaling is the norm |

## Algorithm 2 Replica Targets (D=10ms, α=0.02, buffer=1.2)

| RPS | R = α×x | Buffered | Target Replicas |
|-----|---------|----------|-----------------|
| 22  | 0.44    | 0.53     | 1 |
| 40  | 0.80    | 0.96     | 1 |
| 50  | 1.00    | 1.20     | 2 |
| 73  | 1.46    | 1.75     | 2 |
| 100 | 2.00    | 2.40     | 3 |
| 140 | 2.80    | 3.36     | 4 |
| 164 | 3.28    | 3.94     | 4 |

## Conclusion

D=10ms provides a workload where:
1. Single pod can handle low traffic (22-42 RPS) — Algorithm 2 can MAINTAIN
2. Mean traffic (73 RPS) requires 2 pods — scaling is exercised
3. Peak traffic (164 RPS) requires 4 pods — significant scaling
4. The system is stressed but not overwhelmed (max target=4, well within maxReplicas=10)
