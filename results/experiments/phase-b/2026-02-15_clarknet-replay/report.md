# Phase B: Replicated Comparison Results

**Date:** 2026-02-15T23:49:39.870950
**Git:** 1ac10ae
**Runs:** 4 clean, 0 excluded

## Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |
|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|
| s1-k8s-only | 1 | 8.7 | 15.1 | 15.1 | 0.000 | 73.2 | 0 | 0 | 0 |
| s2-serverless-only | 1 | 9.5 | 410.0 | 410.0 | 0.000 | 73.2 | 5464 | 0 | 0 |
| s3-hybrid-reactive | 1 | 9.6 | 3378.2 | 3378.2 | 0.000 | 72.6 | 20976 | 6 | 6 |
| s4-hybrid-predictive | 1 | 9.3 | 3246.4 | 3246.4 | 0.000 | 71.9 | 14753 | 0 | 0 |

## Statistical Comparisons

### s2-serverless-only vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 15.06 (n=1) |
| Comparison mean | 410.02 (n=1) |
| Difference | +394.96 (+2621.8%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+394.96, +394.96] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |

### s2-serverless-only vs s1-k8s-only (error_rate)

| Metric | Value |
|--------|-------|
| Baseline mean | 0.00 (n=1) |
| Comparison mean | 0.00 (n=1) |
| Difference | +0.00 (+0.0%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.5 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+0.00, +0.00] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |

### s3-hybrid-reactive vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 15.06 (n=1) |
| Comparison mean | 3378.20 (n=1) |
| Difference | +3363.14 (+22325.0%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+3363.14, +3363.14] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |

### s3-hybrid-reactive vs s2-serverless-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 410.02 (n=1) |
| Comparison mean | 3378.20 (n=1) |
| Difference | +2968.18 (+723.9%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+2968.18, +2968.18] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 3378.20 (n=1) |
| Comparison mean | 3246.40 (n=1) |
| Difference | -131.80 (-3.9%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-131.80, -131.80] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6)

| Metric | Value |
|--------|-------|
| Baseline mean | 20976.00 (n=1) |
| Comparison mean | 14753.00 (n=1) |
| Difference | -6223.00 (-29.7%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [-6223.00, -6223.00] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |

### s4-hybrid-predictive vs s1-k8s-only (p99_latency_ms)

| Metric | Value |
|--------|-------|
| Baseline mean | 15.06 (n=1) |
| Comparison mean | 3246.40 (n=1) |
| Difference | +3231.34 (+21450.1%) |
| Welch t-stat | nan |
| Welch p-value | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p | 1.0000 |
| 95% CI | [+3231.34, +3231.34] |
| Cohen's d | 0.000 (negligible) |
| Verdict | ⚠️ Not significant |
