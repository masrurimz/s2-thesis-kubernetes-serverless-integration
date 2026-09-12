# Phase B: Replicated Comparison Results

**Date:** 2026-09-12T16:13:39.776035
**Git:** 367b3c8
**Runs:** 10 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s1-k8s-only | 5 | 67.1 | 2324.7 | 4753.8 | 0.000 | 72.4 | 68827 | 0 | 0 |
| s2-serverless-only | 5 | 66.6 | 78.3 | 86.8 | 0.000 | 73.2 | 82 | 0 | 0 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s1-k8s-only | 5/5 |
| s2-serverless-only | 5/5 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s1-k8s-only | 5/5 | 5 | 0/5 |

## Analysis Set Coverage

| Scenario | Included in Inferential Set |
|----------|-----------------------------|
| s1-k8s-only | 5/5 |
| s2-serverless-only | 5/5 |

## Statistical Comparisons

### s2-serverless-only vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 4753.81 (n=5) |
| Comparison mean | 86.77 (n=5) |
| Difference | -4667.04 (-98.2%) |
| Welch t-stat | -4.611 |
| Welch p-value | 0.0099 |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 0.0079 |
| 95% CI | [-6699.19, -3334.81] |
| Cohen's d | -2.916 (large) |
| Verdict | ✅ Significant |

### s2-serverless-only vs s1-k8s-only (error_rate)

| Metric | Value |
|--------|-------|
| Baseline mean | 0.00 (n=5) |
| Comparison mean | 0.00 (n=5) |
| Difference | -0.00 (-100.0%) |
| Welch t-stat | -1.838 |
| Welch p-value | 0.1399 |
| Mann-Whitney U | 2.5 |
| Mann-Whitney p | 0.0254 |
| 95% CI | [-0.00, -0.00] |
| Cohen's d | -1.162 (large) |
| Verdict | ⚠️ Not significant |
