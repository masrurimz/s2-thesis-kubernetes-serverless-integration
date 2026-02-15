# Phase B Reanalysis — All 20 Runs (No Outlier Exclusion)

**Generated:** 2026-02-15T11:33:43.291434
**Runs per scenario:** 5 × 4 = 20 total
**Outliers excluded:** None

## 1. Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | Total Req | SLO Viol | Scale-Up | Scale-Down | k8s WTP | srv WTP |
|----------|---|----------|----------|----------|--------|-----|-----------|----------|----------|------------|---------|---------|
| S1 (K8s-Only) | 5 | 5.6 ± 0.0 | 5.9 ± 0.0 | 5.9 ± 0.0 | 0.0000 | 73.2 | 87840 | 0 ± 0 | 0.0 | 0.0 | 126000 | 0 |
| S2 (Serverless-Only) | 5 | 6.6 ± 0.0 | 9.3 ± 1.8 | 9.3 ± 1.8 | 0.0000 | 73.2 | 87840 | 2022 ± 220 | 0.0 | 0.0 | 0 | 126000 |
| S3 (Hybrid Reactive) | 5 | 5.7 ± 0.0 | 3280.1 ± 183.2 | 3280.1 ± 183.2 | 0.0000 | 71.6 | 85917 | 16519 ± 1521 | 0.2 | 0.2 | 119520 | 6480 |
| S4 (Hybrid Predictive) | 5 | 5.7 ± 0.0 | 2821.7 ± 424.3 | 2821.7 ± 424.3 | 0.0000 | 72.0 | 86349 | 11302 ± 1974 | 0.0 | 0.0 | 94590 | 31410 |

## 2. H1 Comparisons — Hybrid vs Baselines

### s2-serverless-only vs s1-k8s-only — p99_latency_ms (Platform baseline)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 5.89 ± 0.01 (n=5) |
| Comparison mean ± std | 9.31 ± 1.83 (n=5) |
| Difference | +3.42 (+58.1%) |
| Welch t-stat | 4.176 |
| Welch p-value (raw) | 0.0140 |
| Welch p-value (Holm-Bonferroni) | 0.1257 |
| Mann-Whitney U | 25.0 |
| Mann-Whitney p (raw) | 0.0079 |
| Mann-Whitney p (Holm-Bonferroni) | 0.0675 |
| Bootstrap 95% CI | [+2.01, +4.82] |
| Cohen's d | 2.641 (large) |
| Verdict (Welch corrected) | ⚠️ Not significant |
| Verdict (MW corrected) | ⚠️ Not significant |

### s2-serverless-only vs s1-k8s-only — error_rate (Platform baseline)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 0.00 ± 0.00 (n=5) |
| Comparison mean ± std | 0.00 ± 0.00 (n=5) |
| Difference | +0.00 (+0.0%) |
| Welch t-stat | nan |
| Welch p-value (raw) | nan |
| Welch p-value (Holm-Bonferroni) | nan |
| Mann-Whitney U | 12.5 |
| Mann-Whitney p (raw) | 1.0000 |
| Mann-Whitney p (Holm-Bonferroni) | 1.0000 |
| Bootstrap 95% CI | [+0.00, +0.00] |
| Cohen's d | 0.000 (negligible) |
| Verdict (Welch corrected) | ⚠️ Not significant |
| Verdict (MW corrected) | ⚠️ Not significant |

### s3-hybrid-reactive vs s1-k8s-only — p99_latency_ms (Reactive vs K8s)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 5.89 ± 0.01 (n=5) |
| Comparison mean ± std | 3280.09 ± 183.21 (n=5) |
| Difference | +3274.20 (+55593.2%) |
| Welch t-stat | 39.961 |
| Welch p-value (raw) | 0.0000 |
| Welch p-value (Holm-Bonferroni) | 0.0000 |
| Mann-Whitney U | 25.0 |
| Mann-Whitney p (raw) | 0.0079 |
| Mann-Whitney p (Holm-Bonferroni) | 0.0675 |
| Bootstrap 95% CI | [+3122.54, +3410.23] |
| Cohen's d | 25.273 (large) |
| Verdict (Welch corrected) | ✅ Significant |
| Verdict (MW corrected) | ⚠️ Not significant |

### s3-hybrid-reactive vs s1-k8s-only — slo_violations_k6 (Reactive vs K8s)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 0.00 ± 0.00 (n=5) |
| Comparison mean ± std | 16519.40 ± 1521.22 (n=5) |
| Difference | +16519.40 (+0.0%) |
| Welch t-stat | 24.282 |
| Welch p-value (raw) | 0.0000 |
| Welch p-value (Holm-Bonferroni) | 0.0001 |
| Mann-Whitney U | 25.0 |
| Mann-Whitney p (raw) | 0.0075 |
| Mann-Whitney p (Holm-Bonferroni) | 0.0675 |
| Bootstrap 95% CI | [+15396.40, +17722.04] |
| Cohen's d | 15.357 (large) |
| Verdict (Welch corrected) | ✅ Significant |
| Verdict (MW corrected) | ⚠️ Not significant |

### s3-hybrid-reactive vs s2-serverless-only — p99_latency_ms (Reactive vs Serverless)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 9.31 ± 1.83 (n=5) |
| Comparison mean ± std | 3280.09 ± 183.21 (n=5) |
| Difference | +3270.78 (+35137.5%) |
| Welch t-stat | 39.917 |
| Welch p-value (raw) | 0.0000 |
| Welch p-value (Holm-Bonferroni) | 0.0000 |
| Mann-Whitney U | 25.0 |
| Mann-Whitney p (raw) | 0.0079 |
| Mann-Whitney p (Holm-Bonferroni) | 0.0675 |
| Bootstrap 95% CI | [+3119.72, +3406.93] |
| Cohen's d | 25.246 (large) |
| Verdict (Welch corrected) | ✅ Significant |
| Verdict (MW corrected) | ⚠️ Not significant |

### s4-hybrid-predictive vs s1-k8s-only — p99_latency_ms (Predictive vs K8s)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 5.89 ± 0.01 (n=5) |
| Comparison mean ± std | 2821.69 ± 424.33 (n=5) |
| Difference | +2815.80 (+47809.8%) |
| Welch t-stat | 14.838 |
| Welch p-value (raw) | 0.0001 |
| Welch p-value (Holm-Bonferroni) | 0.0005 |
| Mann-Whitney U | 25.0 |
| Mann-Whitney p (raw) | 0.0079 |
| Mann-Whitney p (Holm-Bonferroni) | 0.0675 |
| Bootstrap 95% CI | [+2503.63, +3154.96] |
| Cohen's d | 9.384 (large) |
| Verdict (Welch corrected) | ✅ Significant |
| Verdict (MW corrected) | ⚠️ Not significant |

### s4-hybrid-predictive vs s1-k8s-only — slo_violations_k6 (Predictive vs K8s)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 0.00 ± 0.00 (n=5) |
| Comparison mean ± std | 11302.20 ± 1974.00 (n=5) |
| Difference | +11302.20 (+0.0%) |
| Welch t-stat | 12.803 |
| Welch p-value (raw) | 0.0002 |
| Welch p-value (Holm-Bonferroni) | 0.0006 |
| Mann-Whitney U | 25.0 |
| Mann-Whitney p (raw) | 0.0075 |
| Mann-Whitney p (Holm-Bonferroni) | 0.0675 |
| Bootstrap 95% CI | [+9773.80, +12786.00] |
| Cohen's d | 8.097 (large) |
| Verdict (Welch corrected) | ✅ Significant |
| Verdict (MW corrected) | ⚠️ Not significant |

## 3. H2 Comparisons — Predictive vs Reactive

### s4-hybrid-predictive vs s3-hybrid-reactive — p99_latency_ms (Predictive vs Reactive)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 3280.09 ± 183.21 (n=5) |
| Comparison mean ± std | 2821.69 ± 424.33 (n=5) |
| Difference | -458.41 (-14.0%) |
| Welch t-stat | -2.218 |
| Welch p-value (raw) | 0.0730 |
| Welch p-value (Holm-Bonferroni) | 0.0730 |
| Mann-Whitney U | 4.0 |
| Mann-Whitney p (raw) | 0.0952 |
| Mann-Whitney p (Holm-Bonferroni) | 0.1905 |
| Bootstrap 95% CI | [-820.18, -96.86] |
| Cohen's d | -1.403 (large) |
| Verdict (Welch corrected) | ⚠️ Not significant |
| Verdict (MW corrected) | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive — slo_violations_k6 (Predictive vs Reactive)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 16519.40 ± 1521.22 (n=5) |
| Comparison mean ± std | 11302.20 ± 1974.00 (n=5) |
| Difference | -5217.20 (-31.6%) |
| Welch t-stat | -4.681 |
| Welch p-value (raw) | 0.0019 |
| Welch p-value (Holm-Bonferroni) | 0.0037 |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p (raw) | 0.0079 |
| Mann-Whitney p (Holm-Bonferroni) | 0.0675 |
| Bootstrap 95% CI | [-7206.87, -3313.60] |
| Cohen's d | -2.961 (large) |
| Verdict (Welch corrected) | ✅ Significant |
| Verdict (MW corrected) | ⚠️ Not significant |

## 4. Cost Proxy Analysis

Cost proxy: `cost(β) = k8s_WTP + β × srv_WTP`, normalized so S1 mean = 1.0

| Scenario | Serverless Share | Violation Rate | β=0.5 | β=0.7 | β=1.0 | β=1.5 |
|----------|-----------------|----------------|-------|-------|-------|-------|
| S1 (K8s-Only) | 0.000 ± 0.000 | 0.0000 ± 0.0000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 |
| S2 (Serverless-Only) | 1.000 ± 0.000 | 0.0230 ± 0.0025 | 0.500 ± 0.000 | 0.700 ± 0.000 | 1.000 ± 0.000 | 1.500 ± 0.000 |
| S3 (Hybrid Reactive) | 0.051 ± 0.011 | 0.1922 ± 0.0168 | 0.974 ± 0.006 | 0.985 ± 0.003 | 1.000 ± 0.000 | 1.026 ± 0.006 |
| S4 (Hybrid Predictive) | 0.249 ± 0.010 | 0.1310 ± 0.0233 | 0.875 ± 0.005 | 0.925 ± 0.003 | 1.000 ± 0.000 | 1.125 ± 0.005 |

## 5. Key Findings Summary

- **Total comparisons:** 9
- **Significant after Holm-Bonferroni (Welch):** 6/9
- **Significant after Holm-Bonferroni (Mann-Whitney):** 0/9

- s2-serverless-only vs s1-k8s-only (p99_latency_ms): Δ=+3.42 (+58.1%), d=2.641 (large), Welch p=0.1257 ⚠️, MW p=0.0675 ⚠️
- s2-serverless-only vs s1-k8s-only (error_rate): Δ=+0.00 (+0.0%), d=0.000 (negligible), Welch p=nan ⚠️, MW p=1.0000 ⚠️
- s3-hybrid-reactive vs s1-k8s-only (p99_latency_ms): Δ=+3274.20 (+55593.2%), d=25.273 (large), Welch p=0.0000 ✅, MW p=0.0675 ⚠️
- s3-hybrid-reactive vs s1-k8s-only (slo_violations_k6): Δ=+16519.40 (+0.0%), d=15.357 (large), Welch p=0.0001 ✅, MW p=0.0675 ⚠️
- s3-hybrid-reactive vs s2-serverless-only (p99_latency_ms): Δ=+3270.78 (+35137.5%), d=25.246 (large), Welch p=0.0000 ✅, MW p=0.0675 ⚠️
- s4-hybrid-predictive vs s1-k8s-only (p99_latency_ms): Δ=+2815.80 (+47809.8%), d=9.384 (large), Welch p=0.0005 ✅, MW p=0.0675 ⚠️
- s4-hybrid-predictive vs s1-k8s-only (slo_violations_k6): Δ=+11302.20 (+0.0%), d=8.097 (large), Welch p=0.0006 ✅, MW p=0.0675 ⚠️
- s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms): Δ=-458.41 (-14.0%), d=-1.403 (large), Welch p=0.0730 ⚠️, MW p=0.1905 ⚠️
- s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6): Δ=-5217.20 (-31.6%), d=-2.961 (large), Welch p=0.0037 ✅, MW p=0.0675 ⚠️
