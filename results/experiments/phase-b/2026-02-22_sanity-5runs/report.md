# Phase B: Replicated Comparison Results

**Date:** 2026-02-22T07:07:28.114799
**Git:** 04eced9
**Runs:** 5 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s1-k8s-only | 1 | 0.4 | 0.6 | 0.6 | 0.000 | 73.2 | 0 | 0 | 0 |
| s2-serverless-only | 1 | 626.7 | 4649.2 | 4649.2 | 0.000 | 67.0 | 42944 | 0 | 0 |
| s3-hybrid-reactive | 1 | 209.8 | 22120.8 | 22120.8 | 0.000 | 52.0 | 32082 | 4 | 0 |
| s4-hybrid-predictive | 2 | 655.7 | 26719.0 | 26719.0 | 0.000 | 51.5 | 69552 | 0 | 0 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s1-k8s-only | 1/1 |
| s2-serverless-only | 1/1 |
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 2/2 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s1-k8s-only | 0/1 | 0 | 1/1 |
| s3-hybrid-reactive | 1/1 | 2 | 1/1 |
| s4-hybrid-predictive | 2/2 | 2 | 2/2 |

## Analysis Set Coverage

| Scenario | Included in Inferential Set |
|----------|-----------------------------|
| s1-k8s-only | 0/1 |
| s2-serverless-only | 1/1 |
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 2/2 |

### Gate Failures

- s1-k8s-only run 1: No dynamic node provisioning events captured; No workload pod observed on dynamic nodes

## Statistical Comparisons

### s3-hybrid-reactive vs s2-serverless-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 4649.20 (n=1) |
| Comparison mean | 22120.84 (n=1) |
| Difference | +17471.64 (+375.8%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+17471.64, +17471.64] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 22120.84 (n=1) |
| Comparison mean | 26718.98 (n=2) |
| Difference | +4598.14 (+20.8%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 2.0 |
| Mann-Whitney p | 0.6667 |
| 95% CI | [+3187.43, +6008.85] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6)

| Metric | Value |
|--------|-------|
| Baseline mean | 32082.00 (n=1) |
| Comparison mean | 34776.00 (n=2) |
| Difference | +2694.00 (+8.4%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 2.0 |
| Mann-Whitney p | 0.6667 |
| 95% CI | [+2624.00, +2764.00] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |
