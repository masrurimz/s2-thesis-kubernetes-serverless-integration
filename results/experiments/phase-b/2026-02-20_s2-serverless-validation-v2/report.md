# Phase B: S2 Serverless Validation v2 (App-Duration Instrumented)

**Date:** 2026-02-21
**Runs:** 1 (s2-serverless-only)
**Purpose:** Validate S2-only execution with app `duration_ms` captured by k6 and enforce CPU accounting sanity checks.

## Summary

- S2 run passed run-valid gate (`k8s_replica_seconds=0`, no K8s pod placement evidence).
- k6 app duration signal is now captured in `results_final.json` (`app_duration_avg_ms=380.85`, `app_duration_p95_ms=1201`).
- This run experienced heavy latency and low SLO compliance (`p95/p99 ~4626ms`, success 46.9%), so it is a stress-biased sample rather than a steady-state S2 baseline.

## Evidence

- `results/experiments/phase-b/2026-02-20_s2-serverless-validation-v2/results_final.json`
- `results/experiments/phase-b/2026-02-20_s2-serverless-validation-v2/s2-serverless-only_run1/`
