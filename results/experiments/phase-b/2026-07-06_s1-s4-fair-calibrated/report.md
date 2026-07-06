# Phase B: Replicated Comparison Results

**Date:** 2026-07-07T00:21:20.654439
**Git:** 9905595
**Runs:** 4 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s1-k8s-only | 1 | 64.3 | 275.9 | 275.9 | 0.000 | 72.3 | 5816 | 0 | 0 |
| s2-serverless-only | 1 | 0.7 | 1.1 | 1.1 | 0.000 | 73.2 | 4 | 0 | 0 |
| s3-hybrid-reactive | 1 | 65.1 | 191.3 | 191.3 | 0.000 | 73.2 | 3849 | 10 | 1 |
| s4-hybrid-predictive | 1 | 64.1 | 171.8 | 171.8 | 0.000 | 73.2 | 2482 | 6 | 0 |

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
| s3-hybrid-reactive | 1/1 | 2 | 0/1 |
| s4-hybrid-predictive | 1/1 | 2 | 0/1 |

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
| Baseline mean | 275.88 (n=1) |
| Comparison mean | 1.07 (n=1) |
| Difference | -274.81 (-99.6%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-274.81, -274.81] |
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
| Baseline mean | 275.88 (n=1) |
| Comparison mean | 191.29 (n=1) |
| Difference | -84.59 (-30.7%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-84.59, -84.59] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |

### s3-hybrid-reactive vs s2-serverless-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 1.07 (n=1) |
| Comparison mean | 191.29 (n=1) |
| Difference | +190.22 (+17804.7%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+190.22, +190.22] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 191.29 (n=1) |
| Comparison mean | 171.80 (n=1) |
| Difference | -19.48 (-10.2%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-19.48, -19.48] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6)

| Metric | Value |
|--------|-------|
| Baseline mean | 3849.00 (n=1) |
| Comparison mean | 2482.00 (n=1) |
| Difference | -1367.00 (-35.5%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-1367.00, -1367.00] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 275.88 (n=1) |
| Comparison mean | 171.80 (n=1) |
| Difference | -104.08 (-37.7%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-104.08, -104.08] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |
