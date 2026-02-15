# Phase B: Replicated Comparison Results

**Date:** 2026-02-15T08:43:23.816231
**Git:** f7c9fe6
**Runs:** 10 clean, 10 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s3-hybrid-reactive | 5 | 5.7 | 3280.1 | 3280.1 | 0.000 | 71.6 | 82597 | 1 | 1 |
| s4-hybrid-predictive | 5 | 5.7 | 2821.7 | 2821.7 | 0.000 | 72.0 | 56511 | 0 | 0 |

## Statistical Comparisons

### s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 3280.09 (n=5) |
| Comparison mean | 2821.69 (n=5) |
| Difference | -458.41 (-14.0%) |
| Welch t-stat | -2.218 |
| Welch p-value | 0.0730 |
| Mann-Whitney U | 4.0 |
| Mann-Whitney p | 0.0952 |
| 95% CI | [-820.18, -96.86] |
| Cohen's d | -1.403 (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6)

| Metric | Value |
|--------|-------|
| Baseline mean | 16519.40 (n=5) |
| Comparison mean | 11302.20 (n=5) |
| Difference | -5217.20 (-31.6%) |
| Welch t-stat | -4.681 |
| Welch p-value | 0.0019 |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 0.0079 |
| 95% CI | [-7206.87, -3313.60] |
| Cohen's d | -2.961 (large) |
| Verdict | ✅ Significant |

## Excluded Runs

- s2-serverless-only run 1: p99=11.4ms (< 15ms threshold)
- s1-k8s-only run 5: p99=5.9ms (< 15ms threshold)
- s2-serverless-only run 5: p99=7.8ms (< 15ms threshold)
- s2-serverless-only run 2: p99=8.4ms (< 15ms threshold)
- s1-k8s-only run 2: p99=5.9ms (< 15ms threshold)
- s1-k8s-only run 3: p99=5.9ms (< 15ms threshold)
- s2-serverless-only run 3: p99=11.2ms (< 15ms threshold)
- s2-serverless-only run 4: p99=7.8ms (< 15ms threshold)
- s1-k8s-only run 1: p99=5.9ms (< 15ms threshold)
- s1-k8s-only run 4: p99=5.9ms (< 15ms threshold)