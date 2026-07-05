# Phase B: Replicated Comparison Results

**Date:** 2026-07-05T10:32:33.294479
**Git:** 4e8afb1
**Runs:** 2 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s1-k8s-only | 1 | 8286.6 | 29584.8 | 29584.8 | 0.000 | 39.9 | 0 | 0 | 0 |
| s4-hybrid-predictive | 1 | 7307.3 | 14708.4 | 14708.4 | 0.000 | 42.5 | 0 | 0 | 0 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s1-k8s-only | 1/1 |
| s4-hybrid-predictive | 1/1 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s1-k8s-only | 1/1 | 0 | 0/1 |
| s4-hybrid-predictive | 1/1 | 0 | 0/1 |

## Analysis Set Coverage

| Scenario | Included in Inferential Set |
|----------|-----------------------------|
| s1-k8s-only | 1/1 |
| s4-hybrid-predictive | 1/1 |

## Statistical Comparisons

### s4-hybrid-predictive vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 29584.76 (n=1) |
| Comparison mean | 14708.41 (n=1) |
| Difference | -14876.34 (-50.3%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-14876.34, -14876.34] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |
