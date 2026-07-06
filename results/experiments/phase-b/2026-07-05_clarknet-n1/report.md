# Phase B: Replicated Comparison Results

**Date:** 2026-07-06T13:56:02.311075
**Git:** 03f0f1f
**Runs:** 4 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s1-k8s-only | 1 | 13.6 | 77.2 | 77.2 | 0.000 | 73.2 | 3033 | 0 | 0 |
| s2-serverless-only | 1 | 0.7 | 1.0 | 1.0 | 0.000 | 73.2 | 2 | 0 | 0 |
| s3-hybrid-reactive | 1 | 13.7 | 393.8 | 393.8 | 0.000 | 73.2 | 7216 | 0 | 0 |
| s4-hybrid-predictive | 1 | 13.7 | 120.7 | 120.7 | 0.000 | 73.2 | 2636 | 0 | 0 |

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
| s1-k8s-only | 1/1 | 3 | 0/1 |
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
| Baseline mean | 77.16 (n=1) |
| Comparison mean | 0.95 (n=1) |
| Difference | -76.21 (-98.8%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-76.21, -76.21] |
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
| Baseline mean | 77.16 (n=1) |
| Comparison mean | 393.85 (n=1) |
| Difference | +316.69 (+410.4%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+316.69, +316.69] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |

### s3-hybrid-reactive vs s2-serverless-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 0.95 (n=1) |
| Comparison mean | 393.85 (n=1) |
| Difference | +392.90 (+41317.4%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+392.90, +392.90] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 393.85 (n=1) |
| Comparison mean | 120.69 (n=1) |
| Difference | -273.16 (-69.4%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-273.16, -273.16] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6)

| Metric | Value |
|--------|-------|
| Baseline mean | 7216.00 (n=1) |
| Comparison mean | 2636.00 (n=1) |
| Difference | -4580.00 (-63.5%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-4580.00, -4580.00] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 77.16 (n=1) |
| Comparison mean | 120.69 (n=1) |
| Difference | +43.53 (+56.4%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+43.53, +43.53] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |
