# Phase B Reanalysis — All 20 Runs (No Outlier Exclusion)

**Generated:** 2026-02-15T21:44:27.314544
**Runs per scenario:** 5 × 4 = 20 total
**Outliers excluded:** None

## 1. Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | Total Req | SLO Viol | Scale-Up | Scale-Down | k8s WTP | srv WTP |
|----------|---|----------|----------|----------|--------|-----|-----------|----------|----------|------------|---------|---------|
| S1 (K8s-Only) | 1 | 8.6 ± nan | 10.9 ± nan | 10.9 ± nan | 0.0000 | 73.2 | 87840 | 0 ± nan | 0.0 | 0.0 | 126000 | 0 |
| S2 (Serverless-Only) | 1 | 9.5 ± nan | 269.3 ± nan | 269.3 ± nan | 0.0000 | 73.2 | 87810 | 4859 ± nan | 0.0 | 0.0 | 0 | 126000 |
| S3 (Hybrid Reactive) | 1 | 9.9 ± nan | 5066.5 ± nan | 5066.5 ± nan | 0.0000 | 71.0 | 85229 | 23739 ± nan | 5.0 | 5.0 | 107700 | 18300 |
| S4 (Hybrid Predictive) | 1 | 9.4 ± nan | 2868.0 ± nan | 2868.0 ± nan | 0.0000 | 71.9 | 86245 | 13166 ± nan | 0.0 | 0.0 | 92775 | 33225 |

## 2. H1 Comparisons — Hybrid vs Baselines

### s2-serverless-only vs s1-k8s-only — p99_latency_ms (Platform baseline)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 10.93 ± nan (n=1) |
| Comparison mean ± std | 269.29 ± nan (n=1) |
| Difference | +258.36 (+2363.2%) |
| Welch t-stat | nan |
| Welch p-value (raw) | nan |
| Welch p-value (Holm-Bonferroni) | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p (raw) | 1.0000 |
| Mann-Whitney p (Holm-Bonferroni) | 1.0000 |
| Bootstrap 95% CI | [+258.36, +258.36] |
| Cohen's d | nan (large) |
| Verdict (Welch corrected) | ⚠️ Not significant |
| Verdict (MW corrected) | ⚠️ Not significant |

### s2-serverless-only vs s1-k8s-only — error_rate (Platform baseline)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 0.00 ± nan (n=1) |
| Comparison mean ± std | 0.00 ± nan (n=1) |
| Difference | +0.00 (+0.0%) |
| Welch t-stat | nan |
| Welch p-value (raw) | nan |
| Welch p-value (Holm-Bonferroni) | nan |
| Mann-Whitney U | 0.5 |
| Mann-Whitney p (raw) | 1.0000 |
| Mann-Whitney p (Holm-Bonferroni) | 1.0000 |
| Bootstrap 95% CI | [+0.00, +0.00] |
| Cohen's d | nan (large) |
| Verdict (Welch corrected) | ⚠️ Not significant |
| Verdict (MW corrected) | ⚠️ Not significant |

### s3-hybrid-reactive vs s1-k8s-only — p99_latency_ms (Reactive vs K8s)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 10.93 ± nan (n=1) |
| Comparison mean ± std | 5066.51 ± nan (n=1) |
| Difference | +5055.58 (+46242.0%) |
| Welch t-stat | nan |
| Welch p-value (raw) | nan |
| Welch p-value (Holm-Bonferroni) | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p (raw) | 1.0000 |
| Mann-Whitney p (Holm-Bonferroni) | 1.0000 |
| Bootstrap 95% CI | [+5055.58, +5055.58] |
| Cohen's d | nan (large) |
| Verdict (Welch corrected) | ⚠️ Not significant |
| Verdict (MW corrected) | ⚠️ Not significant |

### s3-hybrid-reactive vs s1-k8s-only — slo_violations_k6 (Reactive vs K8s)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 0.00 ± nan (n=1) |
| Comparison mean ± std | 23739.00 ± nan (n=1) |
| Difference | +23739.00 (+0.0%) |
| Welch t-stat | nan |
| Welch p-value (raw) | nan |
| Welch p-value (Holm-Bonferroni) | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p (raw) | 1.0000 |
| Mann-Whitney p (Holm-Bonferroni) | 1.0000 |
| Bootstrap 95% CI | [+23739.00, +23739.00] |
| Cohen's d | nan (large) |
| Verdict (Welch corrected) | ⚠️ Not significant |
| Verdict (MW corrected) | ⚠️ Not significant |

### s3-hybrid-reactive vs s2-serverless-only — p99_latency_ms (Reactive vs Serverless)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 269.29 ± nan (n=1) |
| Comparison mean ± std | 5066.51 ± nan (n=1) |
| Difference | +4797.22 (+1781.4%) |
| Welch t-stat | nan |
| Welch p-value (raw) | nan |
| Welch p-value (Holm-Bonferroni) | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p (raw) | 1.0000 |
| Mann-Whitney p (Holm-Bonferroni) | 1.0000 |
| Bootstrap 95% CI | [+4797.22, +4797.22] |
| Cohen's d | nan (large) |
| Verdict (Welch corrected) | ⚠️ Not significant |
| Verdict (MW corrected) | ⚠️ Not significant |

### s4-hybrid-predictive vs s1-k8s-only — p99_latency_ms (Predictive vs K8s)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 10.93 ± nan (n=1) |
| Comparison mean ± std | 2867.97 ± nan (n=1) |
| Difference | +2857.04 (+26132.6%) |
| Welch t-stat | nan |
| Welch p-value (raw) | nan |
| Welch p-value (Holm-Bonferroni) | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p (raw) | 1.0000 |
| Mann-Whitney p (Holm-Bonferroni) | 1.0000 |
| Bootstrap 95% CI | [+2857.04, +2857.04] |
| Cohen's d | nan (large) |
| Verdict (Welch corrected) | ⚠️ Not significant |
| Verdict (MW corrected) | ⚠️ Not significant |

### s4-hybrid-predictive vs s1-k8s-only — slo_violations_k6 (Predictive vs K8s)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 0.00 ± nan (n=1) |
| Comparison mean ± std | 13166.00 ± nan (n=1) |
| Difference | +13166.00 (+0.0%) |
| Welch t-stat | nan |
| Welch p-value (raw) | nan |
| Welch p-value (Holm-Bonferroni) | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p (raw) | 1.0000 |
| Mann-Whitney p (Holm-Bonferroni) | 1.0000 |
| Bootstrap 95% CI | [+13166.00, +13166.00] |
| Cohen's d | nan (large) |
| Verdict (Welch corrected) | ⚠️ Not significant |
| Verdict (MW corrected) | ⚠️ Not significant |

## 3. H2 Comparisons — Predictive vs Reactive

### s4-hybrid-predictive vs s3-hybrid-reactive — p99_latency_ms (Predictive vs Reactive)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 5066.51 ± nan (n=1) |
| Comparison mean ± std | 2867.97 ± nan (n=1) |
| Difference | -2198.54 (-43.4%) |
| Welch t-stat | nan |
| Welch p-value (raw) | nan |
| Welch p-value (Holm-Bonferroni) | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p (raw) | 1.0000 |
| Mann-Whitney p (Holm-Bonferroni) | 1.0000 |
| Bootstrap 95% CI | [-2198.54, -2198.54] |
| Cohen's d | nan (large) |
| Verdict (Welch corrected) | ⚠️ Not significant |
| Verdict (MW corrected) | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive — slo_violations_k6 (Predictive vs Reactive)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 23739.00 ± nan (n=1) |
| Comparison mean ± std | 13166.00 ± nan (n=1) |
| Difference | -10573.00 (-44.5%) |
| Welch t-stat | nan |
| Welch p-value (raw) | nan |
| Welch p-value (Holm-Bonferroni) | nan |
| Mann-Whitney U | 0.0 |
| Mann-Whitney p (raw) | 1.0000 |
| Mann-Whitney p (Holm-Bonferroni) | 1.0000 |
| Bootstrap 95% CI | [-10573.00, -10573.00] |
| Cohen's d | nan (large) |
| Verdict (Welch corrected) | ⚠️ Not significant |
| Verdict (MW corrected) | ⚠️ Not significant |

## 4. Cost Proxy Analysis

Cost proxy: `cost(β) = k8s_WTP + β × srv_WTP`, normalized so S1 mean = 1.0

| Scenario | Serverless Share | Violation Rate | β=0.5 | β=0.7 | β=1.0 | β=1.5 |
|----------|-----------------|----------------|-------|-------|-------|-------|
| S1 (K8s-Only) | 0.000 ± nan | 0.0000 ± nan | 1.000 ± nan | 1.000 ± nan | 1.000 ± nan | 1.000 ± nan |
| S2 (Serverless-Only) | 1.000 ± nan | 0.0553 ± nan | 0.500 ± nan | 0.700 ± nan | 1.000 ± nan | 1.500 ± nan |
| S3 (Hybrid Reactive) | 0.145 ± nan | 0.2785 ± nan | 0.927 ± nan | 0.956 ± nan | 1.000 ± nan | 1.073 ± nan |
| S4 (Hybrid Predictive) | 0.264 ± nan | 0.1527 ± nan | 0.868 ± nan | 0.921 ± nan | 1.000 ± nan | 1.132 ± nan |

## 5. Key Findings Summary

- **Total comparisons:** 9
- **Significant after Holm-Bonferroni (Welch):** 0/9
- **Significant after Holm-Bonferroni (Mann-Whitney):** 0/9

- s2-serverless-only vs s1-k8s-only (p99_latency_ms): Δ=+258.36 (+2363.2%), d=nan (large), Welch p=nan ⚠️, MW p=1.0000 ⚠️
- s2-serverless-only vs s1-k8s-only (error_rate): Δ=+0.00 (+0.0%), d=nan (large), Welch p=nan ⚠️, MW p=1.0000 ⚠️
- s3-hybrid-reactive vs s1-k8s-only (p99_latency_ms): Δ=+5055.58 (+46242.0%), d=nan (large), Welch p=nan ⚠️, MW p=1.0000 ⚠️
- s3-hybrid-reactive vs s1-k8s-only (slo_violations_k6): Δ=+23739.00 (+0.0%), d=nan (large), Welch p=nan ⚠️, MW p=1.0000 ⚠️
- s3-hybrid-reactive vs s2-serverless-only (p99_latency_ms): Δ=+4797.22 (+1781.4%), d=nan (large), Welch p=nan ⚠️, MW p=1.0000 ⚠️
- s4-hybrid-predictive vs s1-k8s-only (p99_latency_ms): Δ=+2857.04 (+26132.6%), d=nan (large), Welch p=nan ⚠️, MW p=1.0000 ⚠️
- s4-hybrid-predictive vs s1-k8s-only (slo_violations_k6): Δ=+13166.00 (+0.0%), d=nan (large), Welch p=nan ⚠️, MW p=1.0000 ⚠️
- s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms): Δ=-2198.54 (-43.4%), d=nan (large), Welch p=nan ⚠️, MW p=1.0000 ⚠️
- s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6): Δ=-10573.00 (-44.5%), d=nan (large), Welch p=nan ⚠️, MW p=1.0000 ⚠️
