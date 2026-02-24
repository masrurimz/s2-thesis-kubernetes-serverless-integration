# Phase B: Replicated Comparison Results

**Date:** 2026-02-19T07:16:01.713670
**Git:** 1d95a39
**Runs:** 8 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s1-k8s-only | 2 | 0.5 | 19307.7 | 19307.7 | 0.000 | 56.9 | 25304 | 1 | 0 |
| s2-serverless-only | 2 | 0.4 | 0.6 | 0.6 | 0.000 | 73.2 | 0 | 0 | 0 |
| s3-hybrid-reactive | 2 | 3207.5 | 23919.9 | 23919.9 | 0.000 | 48.4 | 80425 | 8 | 0 |
| s4-hybrid-predictive | 2 | 436.8 | 22835.6 | 22835.6 | 0.000 | 51.1 | 64066 | 2 | 0 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s1-k8s-only | 2/2 |
| s2-serverless-only | 2/2 |
| s3-hybrid-reactive | 2/2 |
| s4-hybrid-predictive | 2/2 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s1-k8s-only | 2/2 | 0 | 2/2 |
| s3-hybrid-reactive | 2/2 | 4 | 2/2 |
| s4-hybrid-predictive | 2/2 | 2 | 2/2 |

## Analysis Set Coverage

| Scenario | Included in Inferential Set |
|----------|-----------------------------|
| s1-k8s-only | 2/2 |
| s2-serverless-only | 2/2 |
| s3-hybrid-reactive | 2/2 |
| s4-hybrid-predictive | 2/2 |

## Statistical Comparisons

### s2-serverless-only vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 19307.65 (n=2) |
| Comparison mean | 0.60 (n=2) |
| Difference | -19307.05 (-100.0%) |
| Welch t-stat | -10.659 |
| Welch p-value | 0.0596 |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 0.3333 |
| 95% CI | [-21118.48, -17495.63] |
| Cohen's d | -10.659 (large) |
| Verdict | ⚠️ Not significant |

### s2-serverless-only vs s1-k8s-only (error_rate)

| Metric | Value |
|--------|-------|
| Baseline mean | 0.00 (n=2) |
| Comparison mean | 0.00 (n=2) |
| Difference | +0.00 (+0.0%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 2.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+0.00, +0.00] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |

### s3-hybrid-reactive vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 19307.65 (n=2) |
| Comparison mean | 23919.88 (n=2) |
| Difference | +4612.23 (+23.9%) |
| Welch t-stat | 2.186 |
| Welch p-value | 0.1883 |
| Mann-Whitney U | 4.0 |
| Mann-Whitney p | 0.3333 |
| 95% CI | [+1719.55, +7504.90] |
| Cohen's d | 2.186 (large) |
| Verdict | ⚠️ Not significant |

### s3-hybrid-reactive vs s2-serverless-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 0.60 (n=2) |
| Comparison mean | 23919.88 (n=2) |
| Difference | +23919.28 (+3991525.7%) |
| Welch t-stat | 22.121 |
| Welch p-value | 0.0288 |
| Mann-Whitney U | 4.0 |
| Mann-Whitney p | 0.3333 |
| 95% CI | [+22837.99, +25000.57] |
| Cohen's d | 22.121 (large) |
| Verdict | ✅ Significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 23919.88 (n=2) |
| Comparison mean | 22835.64 (n=2) |
| Difference | -1084.24 (-4.5%) |
| Welch t-stat | -0.928 |
| Welch p-value | 0.4909 |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 0.6667 |
| 95% CI | [-2606.92, +438.44] |
| Cohen's d | -0.928 (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6)

| Metric | Value |
|--------|-------|
| Baseline mean | 40212.50 (n=2) |
| Comparison mean | 32033.00 (n=2) |
| Difference | -8179.50 (-20.3%) |
| Welch t-stat | -13.934 |
| Welch p-value | 0.0088 |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 0.3333 |
| 95% CI | [-8993.00, -7366.00] |
| Cohen's d | -13.934 (large) |
| Verdict | ✅ Significant |

### s4-hybrid-predictive vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 19307.65 (n=2) |
| Comparison mean | 22835.64 (n=2) |
| Difference | +3527.99 (+18.3%) |
| Welch t-stat | 1.892 |
| Welch p-value | 0.2887 |
| Mann-Whitney U | 4.0 |
| Mann-Whitney p | 0.3333 |
| 95% CI | [+1275.17, +5780.80] |
| Cohen's d | 1.892 (large) |
| Verdict | ⚠️ Not significant |
