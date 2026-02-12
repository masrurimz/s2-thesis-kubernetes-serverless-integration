# Stress Tests — Phase A1

**Date:** 2026-02-11
**Purpose:** Intentional saturation testing to find system breaking points. NOT a controlled experiment.

## Results

### S3 (Hybrid Reactive) — k6 saturation at 1000 VUs
- Total requests: 80,490 (383 RPS achieved)
- Success rate: 15.9% (12,813 pass / 67,677 fail)
- p95 latency: 5,001ms
- Median latency: 0.21ms (most requests failed fast)
- Source: `raw/stress-s3-hybrid-reactive-summary.json`

### S4 (Hybrid Predictive) — k6 at 200 VUs
- Total requests: 122,999 (586 RPS achieved)
- Success rate: 100% (0 failures)
- p95 latency: 0.52ms
- Source: `raw/stress-s4-hybrid-predictive-summary.json`

### Legacy validation_20260211_232450.json
This file was previously stored in `thesis/results/raw/phase_b/` and mislabeled as Phase B experiment data. It actually contains stress test results with 79-97% error rates — it is early validation data, not the controlled Phase B 20-run experiment.

| Scenario | p99 (ms) | Error Rate | Throughput |
|----------|----------|------------|------------|
| S1 | 6,000 | 79.2% | 348 RPS |
| S2 | 2 | 0.0% | 586 RPS |
| S3 | 5,500 | 90.1% | 383 RPS |
| S4 | 5,200 | 96.9% | 536 RPS |

## Interpretation

These stress tests are NOT controlled experiments. They demonstrate system behavior under extreme overload. The S4 result (0% failure at 200 VUs vs S3 84% failure at 1000 VUs) is interesting but uses different VU counts — not a fair comparison.
