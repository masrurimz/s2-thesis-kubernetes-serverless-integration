# Phase B: Replicated Comparison Results

**Date:** 2026-07-08T18:09:46.641426
**Git:** c90cc19
**Runs:** 20 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s1-k8s-only | 5 | 63.9 | 77.1 | 109.8 | 0.000 | 73.2 | 206 | 0 | 0 |
| s2-serverless-only | 5 | 65.2 | 75.5 | 77.8 | 0.000 | 73.2 | 35 | 0 | 0 |
| s3-hybrid-reactive | 5 | 65.0 | 185.1 | 382.1 | 0.000 | 73.2 | 15467 | 0 | 0 |
| s4-hybrid-predictive | 5 | 64.8 | 131.1 | 233.6 | 0.000 | 73.2 | 6847 | 0 | 0 |

## Run Validity Gates

| Scenario | Run-Valid / Total |
|----------|-------------------|
| s1-k8s-only | 5/5 |
| s2-serverless-only | 5/5 |
| s3-hybrid-reactive | 5/5 |
| s4-hybrid-predictive | 5/5 |

## Stress Validity Coverage

| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |
|----------|--------------------------|---------------------|-----------------|
| s1-k8s-only | 5/5 | 10 | 0/5 |
| s3-hybrid-reactive | 5/5 | 0 | 0/5 |
| s4-hybrid-predictive | 5/5 | 0 | 0/5 |

## Analysis Set Coverage

| Scenario | Included in Inferential Set |
|----------|-----------------------------|
| s1-k8s-only | 5/5 |
| s2-serverless-only | 5/5 |
| s3-hybrid-reactive | 5/5 |
| s4-hybrid-predictive | 5/5 |

## Statistical Comparisons

### s2-serverless-only vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 109.78 (n=5) |
| Comparison mean | 77.77 (n=5) |
| Difference | -32.01 (-29.2%) |
| Welch t-stat | -11.361 |
| Welch p-value | 0.0003 |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 0.0079 |
| 95% CI | [-36.08, -26.44] |
| Cohen's d | -7.185 (large) |
| Verdict | ✅ Significant |

### s2-serverless-only vs s1-k8s-only (error_rate)

| Metric | Value |
|--------|-------|
| Baseline mean | 0.00 (n=5) |
| Comparison mean | 0.00 (n=5) |
| Difference | +0.00 (+0.0%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 12.5 |
| Mann-Whitney p | nan |
| 95% CI | [+0.00, +0.00] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |

### s3-hybrid-reactive vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 109.78 (n=5) |
| Comparison mean | 382.09 (n=5) |
| Difference | +272.31 (+248.0%) |
| Welch t-stat | 2.332 |
| Welch p-value | 0.0800 |
| Mann-Whitney U | 25.0 |
| Mann-Whitney p | 0.0079 |
| 95% CI | [+123.27, +506.24] |
| Cohen's d | 1.475 (large) |
| Verdict | ⚠️ Not significant |

### s3-hybrid-reactive vs s2-serverless-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 77.77 (n=5) |
| Comparison mean | 382.09 (n=5) |
| Difference | +304.32 (+391.3%) |
| Welch t-stat | 2.607 |
| Welch p-value | 0.0596 |
| Mann-Whitney U | 25.0 |
| Mann-Whitney p | 0.0079 |
| 95% CI | [+157.49, +538.95] |
| Cohen's d | 1.649 (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 382.09 (n=5) |
| Comparison mean | 233.64 (n=5) |
| Difference | -148.45 (-38.9%) |
| Welch t-stat | -1.238 |
| Welch p-value | 0.2772 |
| Mann-Whitney U | 7.0 |
| Mann-Whitney p | 0.3095 |
| 95% CI | [-383.09, +16.04] |
| Cohen's d | -0.783 (medium) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6)

| Metric | Value |
|--------|-------|
| Baseline mean | 3093.40 (n=5) |
| Comparison mean | 1369.40 (n=5) |
| Difference | -1724.00 (-55.7%) |
| Welch t-stat | -1.354 |
| Welch p-value | 0.2369 |
| Mann-Whitney U | 6.0 |
| Mann-Whitney p | 0.2222 |
| 95% CI | [-4104.24, +203.60] |
| Cohen's d | -0.856 (large) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 109.78 (n=5) |
| Comparison mean | 233.64 (n=5) |
| Difference | +123.86 (+112.8%) |
| Welch t-stat | 4.488 |
| Welch p-value | 0.0104 |
| Mann-Whitney U | 25.0 |
| Mann-Whitney p | 0.0079 |
| 95% CI | [+71.93, +168.93] |
| Cohen's d | 2.839 (large) |
| Verdict | ✅ Significant |
