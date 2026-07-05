# Phase B: Replicated Comparison Results

**Date:** 2026-07-05T21:42:14.584823
**Git:** f321c7a
**Runs:** 2 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s1-k8s-only | 1 | 21.9 | 33378.3 | 33378.3 | 0.000 | 42.3 | 0 | 0 | 0 |
| s2-serverless-only | 1 | 4434.0 | 5332.2 | 5332.2 | 0.000 | 87.6 | 0 | 0 | 0 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s1-k8s-only | 1/1 |
| s2-serverless-only | 1/1 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s1-k8s-only | 1/1 | 2 | 0/1 |

## Analysis Set Coverage

| Scenario | Included in Inferential Set |
|----------|-----------------------------|
| s1-k8s-only | 1/1 |
| s2-serverless-only | 1/1 |

## Statistical Comparisons

### s2-serverless-only vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 33378.34 (n=1) |
| Comparison mean | 5332.23 (n=1) |
| Difference | -28046.11 (-84.0%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-28046.11, -28046.11] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |

### s2-serverless-only vs s1-k8s-only (error_rate)

| Metric | Value |
|--------|-------|
| Baseline mean | 0.00 (n=1) |
| Comparison mean | 0.00 (n=1) |
| Difference | +0.00 (+0.0%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.5 |
| Mann-Whitney p | nan |
| 95% CI | [+0.00, +0.00] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |
