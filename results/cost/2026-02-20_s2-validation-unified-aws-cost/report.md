# Unified AWS Cost Analysis — S2 Serverless Validation (Single Run)

**Date:** 2026-02-20
**Source experiment:** `results/experiments/phase-b/2026-02-20_s2-serverless-validation/`
**Analyzer:** `thesis/scripts/cost_analyzer.py` v5

## Scope

Single-run S2 validation to confirm serverless-only gating and pricing pipeline after fixes to the Phase B runner.

## Cost Summary (per 1200s run)

| Scenario | AWS Total | Lambda Capacity | Lambda Execution | Lambda Requests |
|----------|----------:|----------------:|-----------------:|----------------:|
| S2 (Serverless-only) | $0.0223 | $0.0017 | $0.0030 | $0.0176 |

## Fairness-Normalized Cost

| Scenario | $/1M requests | $/1M successful |
|----------|--------------:|----------------:|
| S2 | $0.25 | $0.25 |

## Notes

- S2 run passed new validity checks (no K8s replicas or K8s pod placements).
- CPU per request remains extremely small (0.01ms @ 1 vCPU), keeping Lambda execution time at the 10.1ms floor.

## Evidence

- `results/cost/2026-02-20_s2-validation-unified-aws-cost/cost_results.json`
- `results/experiments/phase-b/2026-02-20_s2-serverless-validation/results_final.json`
