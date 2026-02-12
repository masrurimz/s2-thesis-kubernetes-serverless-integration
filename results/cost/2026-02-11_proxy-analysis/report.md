# Cost Analysis (Proxy-Based)

**Date:** 2026-02-11
**Type:** Estimated costs using published cloud pricing. NOT real billing data.

## Summary (AWS, Monthly @ 100 RPS)

| Scenario | K8s Cost | Serverless Cost | Total | vs S1 | vs S2 |
|----------|----------|-----------------|-------|-------|-------|
| S1 (K8s-only) | $141.12 | $0.00 | $162.85 | — | -44% |
| S2 (Serverless) | $0.00 | $267.84 | $289.57 | +78% | — |
| S3 (Hybrid Reactive) | $141.12 | $42.77 | $205.62 | +26% | -29% |
| S4 (Hybrid Predictive) | $141.12 | $30.46 | $193.31 | +19% | -33% |

## Key Finding

S4 (Predictive) is **$12.31/month cheaper than S3 (Reactive)** on AWS — a 6% reduction. The predictive routing reduces unnecessary serverless invocations by anticipating load rather than reacting to violations.

## Cross-Provider Comparison (Monthly)

| Scenario | AWS | GCP | Azure |
|----------|-----|-----|-------|
| S1 | $162.85 | $149.22 | $90.12 |
| S2 | $289.57 | $320.57 | $280.20 |
| S3 | $205.62 | $198.14 | $131.59 |
| S4 | $193.31 | $184.50 | $119.67 |

S4 is consistently cheaper than S3 across all providers (6-9% savings).

## Limitations

- Proxy estimates based on published pricing, not actual usage metering
- Assumes constant 100 RPS workload — real workloads vary
- Does not account for free tiers, reserved instances, or volume discounts
- K8s control plane cost varies: AWS $0.10/hr, GCP $0.10/hr, Azure $0/hr

## Source

Raw data: `raw/cost_analysis_20260211_234542.json`
