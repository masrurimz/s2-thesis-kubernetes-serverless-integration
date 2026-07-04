# Phase B: Replicated Comparison Results

**Date:** 2026-07-04T12:36:39.080786
**Git:** b7701c9
**Runs:** 2 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s3-hybrid-reactive | 1 | 4007.8 | 26045.7 | 26045.7 | 0.000 | 43.0 | 38609 | 2 | 0 |
| s4-hybrid-predictive | 1 | 2704.6 | 25566.5 | 25566.5 | 0.000 | 49.4 | 38876 | 1 | 0 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 1/1 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s3-hybrid-reactive | 1/1 | 3 | 1/1 |
| s4-hybrid-predictive | 1/1 | 1 | 1/1 |

## Analysis Set Coverage

| Scenario | Included in Inferential Set |
|----------|-----------------------------|
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 1/1 |

## Statistical Comparisons

### s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 26045.69 (n=1) |
| Comparison mean | 25566.45 (n=1) |
| Difference | -479.24 (-1.8%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-479.24, -479.24] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6)

| Metric | Value |
|--------|-------|
| Baseline mean | 38609.00 (n=1) |
| Comparison mean | 38876.00 (n=1) |
| Difference | +267.00 (+0.7%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+267.00, +267.00] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |
