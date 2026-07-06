# Phase B: Replicated Comparison Results

**Date:** 2026-07-06T07:44:07.489729
**Git:** 303eecc
**Runs:** 4 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s1-k8s-only | 1 | 8.5 | 11.2 | 11.2 | 0.000 | 73.2 | 0 | 0 | 0 |
| s2-serverless-only | 1 | 0.7 | 1.1 | 1.1 | 0.000 | 73.2 | 1 | 0 | 0 |
| s3-hybrid-reactive | 1 | 8.4 | 11.7 | 11.7 | 0.000 | 73.2 | 0 | 0 | 0 |
| s4-hybrid-predictive | 1 | 8.4 | 11.6 | 11.6 | 0.000 | 73.2 | 0 | 0 | 0 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s1-k8s-only | 1/1 |
| s2-serverless-only | 1/1 |
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 1/1 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s1-k8s-only | 1/1 | 2 | 0/1 |
| s3-hybrid-reactive | 1/1 | 0 | 0/1 |
| s4-hybrid-predictive | 1/1 | 0 | 0/1 |

## Analysis Set Coverage

| Scenario | Included in Inferential Set |
|----------|-----------------------------|
| s1-k8s-only | 1/1 |
| s2-serverless-only | 1/1 |
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 1/1 |

## Statistical Comparisons

### s2-serverless-only vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 11.20 (n=1) |
| Comparison mean | 1.05 (n=1) |
| Difference | -10.15 (-90.6%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-10.15, -10.15] |
| Cohen's d | nan (large) |
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
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |

### s3-hybrid-reactive vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 11.20 (n=1) |
| Comparison mean | 11.68 (n=1) |
| Difference | +0.48 (+4.2%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+0.48, +0.48] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |

### s3-hybrid-reactive vs s2-serverless-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 1.05 (n=1) |
| Comparison mean | 11.68 (n=1) |
| Difference | +10.62 (+1007.1%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+10.62, +10.62] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 11.68 (n=1) |
| Comparison mean | 11.63 (n=1) |
| Difference | -0.05 (-0.5%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-0.05, -0.05] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6)

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
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 11.20 (n=1) |
| Comparison mean | 11.63 (n=1) |
| Difference | +0.42 (+3.8%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+0.42, +0.42] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |
