# Phase B: Replicated Comparison Results

**Date:** 2026-02-19T10:38:23.010137
**Git:** 1d95a39
**Runs:** 8 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s1-k8s-only | 2 | 275.2 | 12152.0 | 12152.0 | 0.000 | 63.2 | 60162 | 7 | 0 |
| s2-serverless-only | 2 | 0.3 | 0.4 | 0.4 | 0.000 | 73.2 | 0 | 0 | 0 |
| s3-hybrid-reactive | 2 | 1716.8 | 16428.3 | 16428.3 | 0.000 | 55.8 | 87900 | 7 | 1 |
| s4-hybrid-predictive | 2 | 139.3 | 16261.7 | 16261.7 | 0.000 | 59.1 | 69629 | 2 | 0 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s1-k8s-only | 2/2 |
| s2-serverless-only | 2/2 |
| s3-hybrid-reactive | 2/2 |
| s4-hybrid-predictive | 2/2 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s1-k8s-only | 2/2 | 4 | 2/2 |
| s3-hybrid-reactive | 2/2 | 4 | 2/2 |
| s4-hybrid-predictive | 2/2 | 2 | 2/2 |

## Analysis Set Coverage

| Scenario | Included in Inferential Set |
|----------|-----------------------------|
| s1-k8s-only | 2/2 |
| s2-serverless-only | 2/2 |
| s3-hybrid-reactive | 2/2 |
| s4-hybrid-predictive | 2/2 |

## Statistical Comparisons

### s2-serverless-only vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 12152.01 (n=2) |
| Comparison mean | 0.44 (n=2) |
| Difference | -12151.57 (-100.0%) |
| Welch t-stat | -1.742 |
| Welch p-value | 0.3318 |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 0.3333 |
| 95% CI | [-19128.72, -5174.42] |
| Cohen's d | -1.742 (large) |
| Verdict | ⚠️ Not significant |

### s2-serverless-only vs s1-k8s-only (error_rate)

| Metric | Value |
|--------|-------|
| Baseline mean | 0.00 (n=2) |
| Comparison mean | 0.00 (n=2) |
| Difference | +0.00 (+0.0%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 2.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+0.00, +0.00] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |

### s3-hybrid-reactive vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 12152.01 (n=2) |
| Comparison mean | 16428.26 (n=2) |
| Difference | +4276.25 (+35.2%) |
| Welch t-stat | 0.548 |
| Welch p-value | 0.6552 |
| Mann-Whitney U | 3.0 |
| Mann-Whitney p | 0.6667 |
| 95% CI | [-6203.98, +14756.49] |
| Cohen's d | 0.548 (medium) |
| Verdict | ⚠️ Not significant |

### s3-hybrid-reactive vs s2-serverless-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 0.44 (n=2) |
| Comparison mean | 16428.26 (n=2) |
| Difference | +16427.82 (+3732812.9%) |
| Welch t-stat | 4.690 |
| Welch p-value | 0.1338 |
| Mann-Whitney U | 4.0 |
| Mann-Whitney p | 0.3333 |
| 95% CI | [+12924.72, +19930.93] |
| Cohen's d | 4.690 (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 16428.26 (n=2) |
| Comparison mean | 16261.70 (n=2) |
| Difference | -166.56 (-1.0%) |
| Welch t-stat | -0.046 |
| Welch p-value | 0.9700 |
| Mann-Whitney U | 2.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-4558.61, +4225.49] |
| Cohen's d | -0.046 (negligible) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6)

| Metric | Value |
|--------|-------|
| Baseline mean | 43950.00 (n=2) |
| Comparison mean | 34814.50 (n=2) |
| Difference | -9135.50 (-20.8%) |
| Welch t-stat | -1.750 |
| Welch p-value | 0.3284 |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 0.3333 |
| 95% CI | [-14731.00, -3540.00] |
| Cohen's d | -1.750 (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 12152.01 (n=2) |
| Comparison mean | 16261.70 (n=2) |
| Difference | +4109.69 (+33.8%) |
| Welch t-stat | 0.584 |
| Welch p-value | 0.6609 |
| Mann-Whitney U | 2.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-3756.40, +11975.78] |
| Cohen's d | 0.584 (medium) |
| Verdict | ⚠️ Not significant |
