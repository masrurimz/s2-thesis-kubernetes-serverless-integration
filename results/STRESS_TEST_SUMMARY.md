# Stress Test Results Summary

**Date:** 2026-02-11
**Test Configuration:** CPU-throttled K8s (`test-app-warm` at `10m`), k6 stress profile from `infrastructure/load-tests/stress.js`

## Scenario Results

### S1: K8s-Only (Baseline)
- **Error Rate:** 85.13%
- **Throughput:** 347.91 req/s
- **p95 Latency:** 5001ms (5s)
- **Status:** Catastrophic failure as expected under CPU throttling

### S2: Serverless-Only (Baseline)
- **Error Rate:** 0%
- **Throughput:** 585.71 req/s
- **p95 Latency:** 1.18ms
- **Status:** Strong baseline with serverless path

### S3: Hybrid-Reactive (Algorithm 1) — Rerun `v3`
- **Error Rate:** 90.10%
- **Throughput:** 383.28 req/s
- **p95 Latency:** 5000.66ms
- **SCALE_OUT Decisions:** 17
- **Weight Verification:** PASS (no verification failures, successful updates logged)
- **Observed Weight Ramp:** `100/0 -> 90/10 -> 80/20 -> 70/30 -> 60/40 -> 50/50`

### S4: Hybrid-Predictive (Algorithm 1 + Algorithm 2) — Rerun `v3`
- **Error Rate:** 92.18%
- **Throughput:** 409.06 req/s
- **p95 Latency:** 5000.67ms
- **SCALE_OUT Decisions:** 17
- **PREDICTIVE Decisions:** 0
- **Weight Verification:** PASS (no verification failures, successful updates logged)
- **Observed Weight Ramp:** `100/0 -> 90/10 -> 80/20 -> 70/30 -> 60/40 -> 50/50`

## Key Findings

### 1. Weight Verifier Bug Is Resolved
The prior blocker is fixed in runtime validation:
- No `Weight verification failed` events in S3/S4 v3 daemon logs
- No `No such server` failures in the rerun logs
- Multiple `Weights updated successfully via HTTP` confirmations in both runs

### 2. Hybrid Routing Applied Correctly But Did Not Recover SLO
Even with correct traffic shifting and serverless ramp-up, the stress profile still produced high timeout/error behavior.
This means the prior "verification bug" confounder is removed; results now reflect system behavior under test conditions.

### 3. Predictive Path Did Not Trigger in S4
S4 recorded zero `PREDICTIVE` actions in v3, so it behaved effectively like reactive scale-out under this run.

### 4. Remaining Bottleneck
Routing daemon could not query Prometheus reliably during runs (`Failed to update load history` repeated), limiting predictive inputs and observability quality.

## Evidence Files

- S3 summary: `infrastructure/results/knative-real/stress-test/s3-hybrid-reactive-v3/summary.json`
- S3 daemon log: `infrastructure/results/knative-real/stress-test/s3-hybrid-reactive-v3/daemon.log`
- S4 summary: `infrastructure/results/knative-real/stress-test/s4-hybrid-predictive-v3/summary.json`
- S4 daemon log: `infrastructure/results/knative-real/stress-test/s4-hybrid-predictive-v3/daemon.log`

## Hypothesis Status (Current)

- **H1 (Proposed system outperforms baselines):** Not supported by current stress reruns (S3/S4 still high error/latency), but now measured with valid weight updates.
- **H2 (Predictive better than Reactive):** Inconclusive in v3 rerun because predictive actions did not trigger.

## Next Steps

1. Fix Prometheus reachability from daemon (`--prometheus-url`) to restore load-history and predictive inputs.
2. Re-run S4 after Prometheus fix and confirm non-zero `PREDICTIVE` decisions.
3. Repeat S3/S4 under a calibrated stress profile to separate infra saturation effects from routing-policy effects.
