# Unified AWS Cost Analysis — S2 Validation v2 (App-Duration Based)

**Date:** 2026-02-21
**Source experiment:** `results/experiments/phase-b/2026-02-20_s2-serverless-validation-v2/`
**Analyzer:** `scripts/cost_analyzer.py` v5 (execution source: app_duration_avg)

## Scope

Single-run S2 validation using app-reported `duration_ms` from response payload to size Lambda execution time.

## Cost Summary (per 1200s run)

| Scenario | AWS Total | Lambda Capacity | Lambda Execution | Lambda Requests |
|----------|----------:|----------------:|-----------------:|----------------:|
| S2 (Serverless-only) | $0.1682 | $0.0467 | $0.1055 | $0.0161 |

## Fairness-Normalized Cost

| Scenario | $/1M requests | $/1M successful |
|----------|--------------:|----------------:|
| S2 | $2.09 | $4.46 |

## Notes

- `execution_time_source=app_duration_avg`, `lambda_exec_time_ms=390.8`, `lambda_pc_instances=27`.
- This run is latency-degraded and not directly comparable to prior pilot means; it demonstrates corrected pricing sensitivity when realistic execution time is used.

## Evidence

- `results/cost/2026-02-21_s2-validation-v2-unified-aws-cost/cost_results.json`
- `results/experiments/phase-b/2026-02-20_s2-serverless-validation-v2/results_final.json`
