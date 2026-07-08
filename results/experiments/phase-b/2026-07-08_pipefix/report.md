# Phase B: Replicated Comparison Results

**Date:** 2026-07-08T00:41:10.559448
**Git:** b5d3d2f
**Runs:** 3 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s1-k8s-only | 1 | 54.7 | 56.8 | 59.2 | 0.000 | 73.2 | 1 | 0 | 0 |
| s3-hybrid-reactive | 1 | 54.9 | 57.0 | 59.2 | 0.000 | 73.2 | 0 | 0 | 0 |
| s4-hybrid-predictive | 1 | 54.9 | 56.9 | 59.3 | 0.000 | 73.2 | 0 | 0 | 0 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s1-k8s-only | 1/1 |
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 1/1 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s1-k8s-only | 1/1 | 0 | 0/1 |
| s3-hybrid-reactive | 1/1 | 0 | 0/1 |
| s4-hybrid-predictive | 1/1 | 0 | 0/1 |

## Analysis Set Coverage

| Scenario | Included in Inferential Set |
|----------|-----------------------------|
| s1-k8s-only | 1/1 |
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 1/1 |

## Statistical Comparisons

### s3-hybrid-reactive vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 59.22 (n=1) |
| Comparison mean | 59.22 (n=1) |
| Difference | +0.00 (+0.0%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+0.00, +0.00] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 59.22 (n=1) |
| Comparison mean | 59.26 (n=1) |
| Difference | +0.04 (+0.1%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+0.04, +0.04] |
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
| Baseline mean | 59.22 (n=1) |
| Comparison mean | 59.26 (n=1) |
| Difference | +0.04 (+0.1%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+0.04, +0.04] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |
