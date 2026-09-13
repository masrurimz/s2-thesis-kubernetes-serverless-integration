# Phase B: Replicated Comparison Results

**Date:** 2026-09-13T05:55:08.908442
**Git:** 7ff529a
**Runs:** 10 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s1-k8s-only | 5 | 64.0 | 80.6 | 124.6 | 0.000 | 73.2 | 457 | 0 | 0 |
| s2-serverless-only | 5 | 65.2 | 75.5 | 77.8 | 0.000 | 73.2 | 23 | 0 | 0 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s1-k8s-only | 5/5 |
| s2-serverless-only | 5/5 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s1-k8s-only | 5/5 | 10 | 0/5 |

## Analysis Set Coverage

| Scenario | Included in Inferential Set |
|----------|-----------------------------|
| s1-k8s-only | 5/5 |
| s2-serverless-only | 5/5 |

## Statistical Comparisons

### s2-serverless-only vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 124.65 (n=5) |
| Comparison mean | 77.83 (n=5) |
| Difference | -46.82 (-37.6%) |
| Welch t-stat | -7.285 |
| Welch p-value | 0.0018 |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 0.0079 |
| 95% CI | [-59.34, -37.53] |
| Cohen's d | -4.607 (large) |
| Verdict | ✅ Significant |

### s2-serverless-only vs s1-k8s-only (error_rate)

| Metric | Value |
|--------|-------|
| Baseline mean | 0.00 (n=5) |
| Comparison mean | 0.00 (n=5) |
| Difference | +0.00 (+0.0%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 12.5 |
| Mann-Whitney p | nan |
| 95% CI | [+0.00, +0.00] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |
