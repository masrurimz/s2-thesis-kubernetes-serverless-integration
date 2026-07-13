# Phase B: Replicated Comparison Results

**Date:** 2026-07-14T00:39:27.472264
**Git:** afc93cf
**Runs:** 2 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s3-hybrid-reactive | 1 | 64.6 | 98.8 | 228.4 | 0.000 | 73.2 | 1085 | 9 | 1 |
| s4-hybrid-predictive | 1 | 64.7 | 82.0 | 113.0 | 0.000 | 73.2 | 40 | 6 | 0 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 1/1 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s3-hybrid-reactive | 1/1 | 3 | 0/1 |
| s4-hybrid-predictive | 1/1 | 5 | 0/1 |

## Analysis Set Coverage

| Scenario | Included in Inferential Set |
|----------|-----------------------------|
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 1/1 |

## Statistical Comparisons

### s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 228.36 (n=1) |
| Comparison mean | 112.99 (n=1) |
| Difference | -115.37 (-50.5%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-115.37, -115.37] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6)

| Metric | Value |
|--------|-------|
| Baseline mean | 1085.00 (n=1) |
| Comparison mean | 40.00 (n=1) |
| Difference | -1045.00 (-96.3%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-1045.00, -1045.00] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |
