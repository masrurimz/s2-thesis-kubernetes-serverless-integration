# Unified AWS Cost Analysis — Pilot n=2 Validity-Gates Rerun

**Date:** 2026-02-19
**Source experiment:** `results/experiments/phase-b/2026-02-19_pilot-n2-validity-gates-rerun/`
**Analyzer:** `scripts/cost_analyzer.py` v5

## Scope

This is a pilot (`n=2` per scenario) used to verify end-to-end gate labels (`run_validity_passed`, `stress_validity_passed`) and fairness-normalized cost outputs on the updated pipeline.

## Mean Cost (per 1200s run)

| Scenario | Mean AWS total | Range (min-max) |
|----------|---------------:|----------------:|
| S1 (K8s-only) | $0.0611 | $0.0611-$0.0611 |
| S2 (Serverless-only) | $0.0223 | $0.0223-$0.0223 |
| S3 (Hybrid Reactive) | $0.1089 | $0.1006-$0.1171 |
| S4 (Hybrid Predictive) | $0.0917 | $0.0913-$0.0922 |

## Fairness-Normalized Cost (mean)

| Scenario | $/1M requests | $/1M successful |
|----------|--------------:|----------------:|
| S1 | $0.83 | $1.50 |
| S2 | $0.25 | $0.25 |
| S3 | $1.62 | $5.41 |
| S4 | $1.29 | $2.50 |

## Interpretation

- The fairness columns are present and populated for all scenarios.
- Directionally, S4 improves cost-efficiency over S3 on successful-work-normalized basis in this pilot.
- Because `n=2`, treat this bundle as a pipeline-validation artifact, not a final inferential result.

## Evidence

- `results/cost/2026-02-19_pilot-n2-unified-aws-cost/cost_results.json`
- `results/experiments/phase-b/2026-02-19_pilot-n2-validity-gates-rerun/report.md`
