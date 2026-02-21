# Phase B: S2 Serverless-Only Validation (Single Run)

**Date:** 2026-02-20
**Runs:** 1 (s2-serverless-only)
**Purpose:** Validate S2-only gating and corrected workload endpoint after runner fixes.

## Summary

- S2 run passed run-valid gate with no K8s replicas and no K8s pod placements.
- `time_in_serverless_pct` = 100%.
- k6 p95 latency (reported) = 0.595 ms; CPU per request remains very small, so Lambda execution time sits at 10.1 ms floor.

## Evidence

- `results/experiments/phase-b/2026-02-20_s2-serverless-validation/results_final.json`
- `results/experiments/phase-b/2026-02-20_s2-serverless-validation/s2-serverless-only_run1/`
