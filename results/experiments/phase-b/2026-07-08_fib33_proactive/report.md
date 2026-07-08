# Phase B: Replicated Comparison Results

**Date:** 2026-07-09T00:20:54.063601
**Git:** 71b1f10
**Runs:** 10 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s3-hybrid-reactive | 5 | 64.9 | 157.3 | 309.5 | 0.000 | 73.2 | 14027 | 0 | 0 |
| s4-hybrid-predictive | 5 | 64.7 | 99.2 | 187.9 | 0.000 | 73.2 | 3509 | 0 | 0 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s3-hybrid-reactive | 5/5 |
| s4-hybrid-predictive | 5/5 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s3-hybrid-reactive | 5/5 | 0 | 0/5 |
| s4-hybrid-predictive | 5/5 | 0 | 0/5 |

## Analysis Set Coverage

| Scenario | Included in Inferential Set |
|----------|-----------------------------|
| s3-hybrid-reactive | 5/5 |
| s4-hybrid-predictive | 5/5 |

## Statistical Comparisons

### s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 309.54 (n=5) |
| Comparison mean | 187.90 (n=5) |
| Difference | -121.65 (-39.3%) |
| Welch t-stat | -1.919 |
| Welch p-value | 0.1216 |
| Mann-Whitney U | 9.0 |
| Mann-Whitney p | 0.5476 |
| 95% CI | [-229.35, -10.33] |
| Cohen's d | -1.214 (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6)

| Metric | Value |
|--------|-------|
| Baseline mean | 2805.40 (n=5) |
| Comparison mean | 701.80 (n=5) |
| Difference | -2103.60 (-75.0%) |
| Welch t-stat | -1.922 |
| Welch p-value | 0.1247 |
| Mann-Whitney U | 9.0 |
| Mann-Whitney p | 0.5476 |
| 95% CI | [-3995.60, -239.80] |
| Cohen's d | -1.215 (large) |
| Verdict | ⚠️ Not significant |
