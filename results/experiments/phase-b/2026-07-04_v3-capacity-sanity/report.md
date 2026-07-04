# Phase B: Replicated Comparison Results

**Date:** 2026-07-04T11:35:22.973806
**Git:** 33e914c
**Runs:** 2 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s3-hybrid-reactive | 1 | 2881.5 | 26305.5 | 26305.5 | 0.000 | 46.1 | 39282 | 1 | 0 |
| s4-hybrid-predictive | 1 | 405.7 | 16565.7 | 16565.7 | 0.000 | 62.1 | 39930 | 1 | 0 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 1/1 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s3-hybrid-reactive | 1/1 | 5 | 1/1 |
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
| Baseline mean | 26305.50 (n=1) |
| Comparison mean | 16565.73 (n=1) |
| Difference | -9739.77 (-37.0%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-9739.77, -9739.77] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6)

| Metric | Value |
|--------|-------|
| Baseline mean | 39282.00 (n=1) |
| Comparison mean | 39930.00 (n=1) |
| Difference | +648.00 (+1.6%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+648.00, +648.00] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |
