# Phase B: Replicated Comparison Results

**Date:** 2026-08-09T11:05:58.981665
**Git:** 920b6f9
**Runs:** 20 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s1-k8s-only | 5 | 64.0 | 76.7 | 110.3 | 0.000 | 73.2 | 253 | 0 | 0 |
| s2-serverless-only | 5 | 64.9 | 73.1 | 79.7 | 0.000 | 73.2 | 2 | 0 | 0 |
| s3-hybrid-reactive | 5 | 64.3 | 92.6 | 151.6 | 0.000 | 73.2 | 1998 | 70 | 25 |
| s4-hybrid-predictive | 5 | 64.1 | 76.8 | 99.1 | 0.000 | 73.2 | 92 | 55 | 15 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s1-k8s-only | 5/5 |
| s2-serverless-only | 5/5 |
| s3-hybrid-reactive | 5/5 |
| s4-hybrid-predictive | 5/5 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s1-k8s-only | 5/5 | 10 | 0/5 |
| s3-hybrid-reactive | 5/5 | 10 | 0/5 |
| s4-hybrid-predictive | 5/5 | 10 | 0/5 |

## Analysis Set Coverage

| Scenario | Included in Inferential Set |
|----------|-----------------------------|
| s1-k8s-only | 5/5 |
| s2-serverless-only | 5/5 |
| s3-hybrid-reactive | 5/5 |
| s4-hybrid-predictive | 5/5 |

## Statistical Comparisons

### s2-serverless-only vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 110.31 (n=5) |
| Comparison mean | 79.72 (n=5) |
| Difference | -30.60 (-27.7%) |
| Welch t-stat | -8.826 |
| Welch p-value | 0.0004 |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 0.0079 |
| 95% CI | [-36.13, -24.09] |
| Cohen's d | -5.582 (large) |
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

### s3-hybrid-reactive vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 110.31 (n=5) |
| Comparison mean | 151.58 (n=5) |
| Difference | +41.26 (+37.4%) |
| Welch t-stat | 1.682 |
| Welch p-value | 0.1652 |
| Mann-Whitney U | 18.0 |
| Mann-Whitney p | 0.3095 |
| 95% CI | [+3.64, +88.10] |
| Cohen's d | 1.064 (large) |
| Verdict | ⚠️ Not significant |

### s3-hybrid-reactive vs s2-serverless-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 79.72 (n=5) |
| Comparison mean | 151.58 (n=5) |
| Difference | +71.86 (+90.1%) |
| Welch t-stat | 2.955 |
| Welch p-value | 0.0416 |
| Mann-Whitney U | 25.0 |
| Mann-Whitney p | 0.0079 |
| 95% CI | [+35.22, +116.67] |
| Cohen's d | 1.869 (large) |
| Verdict | ✅ Significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 151.58 (n=5) |
| Comparison mean | 99.08 (n=5) |
| Difference | -52.50 (-34.6%) |
| Welch t-stat | -2.055 |
| Welch p-value | 0.0970 |
| Mann-Whitney U | 2.0 |
| Mann-Whitney p | 0.0317 |
| 95% CI | [-102.60, -11.81] |
| Cohen's d | -1.300 (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6)

| Metric | Value |
|--------|-------|
| Baseline mean | 399.60 (n=5) |
| Comparison mean | 18.40 (n=5) |
| Difference | -381.20 (-95.4%) |
| Welch t-stat | -1.541 |
| Welch p-value | 0.1978 |
| Mann-Whitney U | 2.0 |
| Mann-Whitney p | 0.0345 |
| 95% CI | [-881.80, -60.80] |
| Cohen's d | -0.974 (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 110.31 (n=5) |
| Comparison mean | 99.08 (n=5) |
| Difference | -11.24 (-10.2%) |
| Welch t-stat | -1.314 |
| Welch p-value | 0.2419 |
| Mann-Whitney U | 5.0 |
| Mann-Whitney p | 0.1508 |
| 95% CI | [-23.70, +5.43] |
| Cohen's d | -0.831 (large) |
| Verdict | ⚠️ Not significant |
