# Phase B: Replicated Comparison Results

**Date:** 2026-02-26T07:04:52.471223
**Git:** c6c0cb5
**Runs:** 2 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s3-hybrid-reactive | 1 | 1886.2 | 24566.6 | 24566.6 | 0.000 | 51.4 | 49539 | 4 | 0 |
| s4-hybrid-predictive | 1 | 3335.7 | 24137.9 | 24137.9 | 0.000 | 48.3 | 47882 | 1 | 0 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 1/1 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s3-hybrid-reactive | 1/1 | 2 | 1/1 |
| s4-hybrid-predictive | 1/1 | 1 | 1/1 |

## Analysis Set Coverage

| Scenario | Included in Inferential Set |
|----------|-----------------------------|
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 1/1 |

## Statistical Comparisons

### s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 24566.57 (n=1) |
| Comparison mean | 24137.88 (n=1) |
| Difference | -428.69 (-1.7%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-428.69, -428.69] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6)

| Metric | Value |
|--------|-------|
| Baseline mean | 49539.00 (n=1) |
| Comparison mean | 47882.00 (n=1) |
| Difference | -1657.00 (-3.3%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-1657.00, -1657.00] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |
