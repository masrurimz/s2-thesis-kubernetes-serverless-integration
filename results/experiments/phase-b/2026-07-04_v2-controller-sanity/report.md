# Phase B: Replicated Comparison Results

**Date:** 2026-07-04T08:39:59.102172
**Git:** 2c0bb08
**Runs:** 2 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s3-hybrid-reactive | 1 | 857.0 | 23943.0 | 23943.0 | 0.000 | 50.1 | 35255 | 3 | 0 |
| s4-hybrid-predictive | 1 | 884.0 | 20605.4 | 20605.4 | 0.000 | 53.6 | 36652 | 1 | 0 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 1/1 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s3-hybrid-reactive | 1/1 | 2 | 1/1 |
| s4-hybrid-predictive | 1/1 | 2 | 1/1 |

## Analysis Set Coverage

| Scenario | Included in Inferential Set |
|----------|-----------------------------|
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 1/1 |

## Statistical Comparisons

### s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 23943.01 (n=1) |
| Comparison mean | 20605.39 (n=1) |
| Difference | -3337.62 (-13.9%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-3337.62, -3337.62] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6)

| Metric | Value |
|--------|-------|
| Baseline mean | 35255.00 (n=1) |
| Comparison mean | 36652.00 (n=1) |
| Difference | +1397.00 (+4.0%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+1397.00, +1397.00] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |
