# Unified AWS Cost Analysis — All Scenarios Rerun v2 (n=1 each)

**Date:** 2026-02-21
**Source experiment:** `results/experiments/phase-b/2026-02-21_all-scenarios-rerun-v2/`
**Analyzer:** `thesis/scripts/cost_analyzer.py` v5 (prefers app-duration execution time)

## Cost Summary (per 1200s run)

| Scenario | AWS Total | $/1M requests | $/1M successful |
|----------|----------:|--------------:|----------------:|
| S1 (K8s-only) | $0.0611 | $0.70 | $0.70 |
| S2 (Serverless-only) | $0.1685 | $2.10 | $4.46 |
| S3 (Hybrid Reactive) | $0.4856 | $8.08 | $15.70 |
| S4 (Hybrid Predictive) | $0.4322 | $6.92 | $13.28 |

## Interpretation

- With app-duration-informed execution sizing, S2 is no longer the cheapest in this rerun.
- S3/S4 costs are highest in this sample due to large app durations and resulting Lambda capacity/execution charges.
- This is a single-run rerun (`n=1` each), useful for pipeline and directional validation only.

## Evidence

- `results/cost/2026-02-21_all-scenarios-rerun-v2-unified-aws-cost/cost_results.json`
- `results/experiments/phase-b/2026-02-21_all-scenarios-rerun-v2/results_final.json`
