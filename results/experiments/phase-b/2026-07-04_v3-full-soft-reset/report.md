# Phase B: Replicated Comparison Results

**Date:** 2026-07-04T15:10:42.469878
**Git:** 80be217
**Runs:** 2 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s3-hybrid-reactive | 1 | 1409.1 | 22626.8 | 22626.8 | 0.000 | 54.3 | 42024 | 0 | 0 |
| s4-hybrid-predictive | 1 | 1537.8 | 23567.2 | 23567.2 | 0.000 | 53.6 | 42938 | 0 | 0 |

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
