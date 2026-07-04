# Phase B: Replicated Comparison Results

**Date:** 2026-07-04T16:05:06.465901
**Git:** 2c0f2ca
**Runs:** 2 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s3-hybrid-reactive | 1 | 85.3 | 11418.7 | 11418.7 | 0.000 | 63.6 | 31780 | 3 | 0 |
| s4-hybrid-predictive | 1 | 8447.9 | 15678.8 | 15678.8 | 0.000 | 41.3 | 47382 | 0 | 0 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 1/1 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s3-hybrid-reactive | 1/1 | 2 | 1/1 |
| s4-hybrid-predictive | 0/1 | 0 | 1/1 |

## Analysis Set Coverage

| Scenario | Included in Inferential Set |
|----------|-----------------------------|
| s3-hybrid-reactive | 1/1 |
| s4-hybrid-predictive | 0/1 |

### Gate Failures

- s4-hybrid-predictive run 1: No dynamic node provisioning events captured

## Statistical Comparisons
