# Phase B: Replicated Comparison Results

**Date:** 2026-07-14T01:36:46.550778
**Git:** d807f90
**Runs:** 2 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s3-hybrid-reactive | 1 | 64.6 | 81.4 | 136.2 | 0.000 | 73.2 | 248 | 14 | 5 |
| s4-hybrid-predictive | 1 | 64.8 | 85.5 | 149.4 | 0.000 | 73.2 | 271 | 11 | 3 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 1/1 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s3-hybrid-reactive | 1/1 | 2 | 0/1 |
| s4-hybrid-predictive | 1/1 | 3 | 0/1 |

## Analysis Set Coverage

| Scenario | Included in Inferential Set |
|----------|-----------------------------|
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 1/1 |

## Statistical Comparisons

### s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 136.22 (n=1) |
| Comparison mean | 149.39 (n=1) |
| Difference | +13.17 (+9.7%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+13.17, +13.17] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6)

| Metric | Value |
|--------|-------|
| Baseline mean | 248.00 (n=1) |
| Comparison mean | 271.00 (n=1) |
| Difference | +23.00 (+9.3%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+23.00, +23.00] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |
