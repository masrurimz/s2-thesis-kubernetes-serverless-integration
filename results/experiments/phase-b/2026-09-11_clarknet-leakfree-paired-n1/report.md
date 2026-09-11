# Phase B: Replicated Comparison Results

**Date:** 2026-09-11T09:23:23.293078
**Git:** bd7e59c
**Runs:** 2 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s3-hybrid-reactive | 1 | 69.6 | 90.1 | 120.4 | 0.000 | 73.2 | 117 | 0 | 0 |
| s4-hybrid-predictive | 1 | 70.8 | 100.3 | 152.6 | 0.000 | 73.2 | 254 | 0 | 0 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 1/1 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s3-hybrid-reactive | 1/1 | 0 | 0/1 |
| s4-hybrid-predictive | 1/1 | 0 | 0/1 |

## Analysis Set Coverage

| Scenario | Included in Inferential Set |
|----------|-----------------------------|
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 1/1 |

## Statistical Comparisons

### s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 120.45 (n=1) |
| Comparison mean | 152.63 (n=1) |
| Difference | +32.19 (+26.7%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+32.19, +32.19] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6)

| Metric | Value |
|--------|-------|
| Baseline mean | 117.00 (n=1) |
| Comparison mean | 254.00 (n=1) |
| Difference | +137.00 (+117.1%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+137.00, +137.00] |
| Cohen's d | nan (large) |
| Verdict | ⚠️ Not significant |
