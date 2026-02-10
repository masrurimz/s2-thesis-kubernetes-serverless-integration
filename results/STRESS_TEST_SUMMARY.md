# Stress Test Results Summary

**Date:** 2026-02-11  
**Test Configuration:** CPU-intensive fib(n=35) endpoint, 100 RPS spike load

## Scenario Results

### S1: K8s-Only (Baseline)
- **Error Rate:** 85.13%
- **Throughput:** 347.91 req/s
- **p95 Latency:** 5001ms (5s)
- **Status:** Catastrophic failure as expected - K8s CPU throttled to 10m

### S2: Serverless-Only (Baseline)
- **Error Rate:** 0%
- **Throughput:** 585.71 req/s
- **p95 Latency:** 1.18ms
- **Status:** Excellent performance - Knative auto-scaling handles load

### S3: Hybrid-Reactive (Algorithm 1)
- **Error Rate:** 95.38%
- **p95 Latency:** 53.72s
- **SLO Violations:** 1110
- **SCALE_OUT Decisions:** 6
- **Weight Updates:** Failed verification (parsing issue)
- **Status:** Algorithm detected violations but weight verification failed

### S4: Hybrid-Predictive (Algorithm 1 + Algorithm 2)
- **Error Rate:** 99.15%
- **p95 Latency:** 60s (timeout)
- **SLO Violations:** 587
- **SCALE_OUT Decisions:** 4
- **Weight Updates:** Failed verification (parsing issue)
- **GRU Predictions:** Available but reactive mode dominated

## Key Findings

### 1. Weight Verification Issue
The routing daemon correctly detects SLO violations and makes SCALE_OUT decisions,
but fails to verify weight updates due to HAProxy stats parsing. The TCP commands
are sent successfully but verification fails with:
```
Could not parse current weights from HAProxy stats
```

### 2. Algorithm Behavior
- S3 made 6 SCALE_OUT decisions (more aggressive)
- S4 made 4 SCALE_OUT decisions (with prediction input)
- Both scenarios attempted to shift traffic from 80/20 toward 50/50

### 3. Hypothesis Validation
- **H1 (Proposed system outperforms baselines):** INCONCLUSIVE - Weight verification issue prevented proper testing
- **H2 (Predictive vs Reactive):** INCONCLUSIVE - Need weight fix to compare properly

## Next Steps
1. Fix HAProxy stats parsing in weight_adjuster.py
2. Re-run S3 and S4 tests
3. Verify weight changes are applied and effective
