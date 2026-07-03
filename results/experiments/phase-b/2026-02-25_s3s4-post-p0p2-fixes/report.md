# Phase B: Replicated Comparison Results

**Date:** 2026-02-25T18:43:30.697443
**Git:** c6c0cb5
**Runs:** 2 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s3-hybrid-reactive | 1 | 3876.3 | 27453.5 | 27453.5 | 0.000 | 42.9 | 47648 | 2 | 0 |
| s4-hybrid-predictive | 1 | 2312.5 | 19704.8 | 19704.8 | 0.000 | 55.3 | 51534 | 1 | 0 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 1/1 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s3-hybrid-reactive | 1/1 | 1 | 1/1 |
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
| Baseline mean | 27453.52 (n=1) |
| Comparison mean | 19704.76 (n=1) |
| Difference | -7748.75 (-28.2%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-7748.75, -7748.75] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6)

| Metric | Value |
|--------|-------|
| Baseline mean | 47648.00 (n=1) |
| Comparison mean | 51534.00 (n=1) |
| Difference | +3886.00 (+8.2%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+3886.00, +3886.00] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |
