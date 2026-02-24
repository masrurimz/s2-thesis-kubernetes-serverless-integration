# Phase B: Replicated Comparison Results

**Date:** 2026-02-14T21:52:02.065710
**Git:** b05d71d
**Runs:** 6 clean, 14 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s1-k8s-only | 4 | 5.7 | 932.1 | 932.1 | 0.000 | 73.1 | 25213 | 0 | 81 |
| s2-serverless-only | 1 | 5.7 | 1411.3 | 1411.3 | 0.000 | 73.1 | 10121 | 0 | 20 |
| s4-hybrid-predictive | 1 | 5.7 | 1877.2 | 1877.2 | 0.000 | 73.1 | 9201 | 0 | 0 |

## Statistical Comparisons

### s4-hybrid-predictive vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 932.14 (n=4) |
| Comparison mean | 1877.21 (n=1) |
| Difference | +945.07 (+101.4%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 4.0 |
| Mann-Whitney p | 0.4000 |
| 95% CI | [+610.90, +1279.25] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |

## Excluded Runs

- s4-hybrid-predictive run 5: p99=0.0ms (< 15ms threshold)
- s2-serverless-only run 1: p99=0.0ms (< 15ms threshold)
- s3-hybrid-reactive run 5: p99=0.0ms (< 15ms threshold)
- s3-hybrid-reactive run 4: p99=0.0ms (< 15ms threshold)
- s4-hybrid-predictive run 4: p99=0.0ms (< 15ms threshold)
- s2-serverless-only run 2: p99=0.0ms (< 15ms threshold)
- s3-hybrid-reactive run 3: p99=0.0ms (< 15ms threshold)
- s4-hybrid-predictive run 3: p99=0.0ms (< 15ms threshold)
- s3-hybrid-reactive run 1: p99=0.0ms (< 15ms threshold)
- s1-k8s-only run 2: p99=0.0ms (< 15ms threshold)
- s3-hybrid-reactive run 2: p99=0.0ms (< 15ms threshold)
- s4-hybrid-predictive run 2: p99=0.0ms (< 15ms threshold)
- s2-serverless-only run 3: p99=0.0ms (< 15ms threshold)
- s2-serverless-only run 4: p99=0.0ms (< 15ms threshold)