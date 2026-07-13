# Phase B: Replicated Comparison Results

**Date:** 2026-07-13T13:00:59.149273
**Git:** 83ef48c
**Runs:** 3 clean, 1 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s1-k8s-only | 1 | 96.3 | 2457.7 | 6665.1 | 0.000 | 189.6 | 78257 | 0 | 0 |
| s2-serverless-only | 1 | 74.7 | 290.0 | 1401.9 | 0.000 | 199.9 | 12859 | 0 | 0 |
| s3-hybrid-reactive | 1 | 69.7 | 375.0 | 874.4 | 0.000 | 199.9 | 23913 | 1 | 0 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s1-k8s-only | 1/1 |
| s2-serverless-only | 1/1 |
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 0/1 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s1-k8s-only | 1/1 | 2 | 0/1 |
| s3-hybrid-reactive | 1/1 | 2 | 0/1 |

## Analysis Set Coverage

| Scenario | Included in Inferential Set |
|----------|-----------------------------|
| s1-k8s-only | 1/1 |
| s2-serverless-only | 1/1 |
| s3-hybrid-reactive | 1/1 |

### Gate Failures

- s4-hybrid-predictive run 1: forecast horizon shorter than measured provisioning delay

## Statistical Comparisons

### s2-serverless-only vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 6665.07 (n=1) |
| Comparison mean | 1401.92 (n=1) |
| Difference | -5263.16 (-79.0%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-5263.16, -5263.16] |
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
| Baseline mean | 6665.07 (n=1) |
| Comparison mean | 874.44 (n=1) |
| Difference | -5790.63 (-86.9%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-5790.63, -5790.63] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |

### s3-hybrid-reactive vs s2-serverless-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 1401.92 (n=1) |
| Comparison mean | 874.44 (n=1) |
| Difference | -527.47 (-37.6%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-527.47, -527.47] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |

## Excluded Runs

- s4-hybrid-predictive run 1: forecast horizon shorter than measured provisioning delay