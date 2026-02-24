# Phase B: Replicated Comparison Results

**Date:** 2026-02-15T21:04:14.053290
**Git:** 3e2aab1
**Runs:** 3 clean, 1 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s2-serverless-only | 1 | 9.5 | 269.3 | 269.3 | 0.000 | 73.2 | 4859 | 0 | 0 |
| s3-hybrid-reactive | 1 | 9.9 | 5066.5 | 5066.5 | 0.000 | 71.0 | 23739 | 5 | 5 |
| s4-hybrid-predictive | 1 | 9.4 | 2868.0 | 2868.0 | 0.000 | 71.9 | 13166 | 0 | 0 |

## Statistical Comparisons

### s3-hybrid-reactive vs s2-serverless-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 269.29 (n=1) |
| Comparison mean | 5066.51 (n=1) |
| Difference | +4797.22 (+1781.4%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+4797.22, +4797.22] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 5066.51 (n=1) |
| Comparison mean | 2867.97 (n=1) |
| Difference | -2198.54 (-43.4%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-2198.54, -2198.54] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6)

| Metric | Value |
|--------|-------|
| Baseline mean | 23739.00 (n=1) |
| Comparison mean | 13166.00 (n=1) |
| Difference | -10573.00 (-44.5%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-10573.00, -10573.00] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |

## Excluded Runs

- s1-k8s-only run 1: p99=10.9ms (< 15ms threshold)