# Phase B Reanalysis — All 20 Runs (No Outlier Exclusion)

**Generated:** 2026-09-11T09:23:30.439458
**Runs per scenario:** 5 × 4 = 20 total
**Outliers excluded:** None

## 1. Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | Total Req | SLO Viol | Scale-Up | Scale-Down | k8s WTP | srv WTP |
|----------|---|----------|----------|----------|--------|-----|-----------|----------|----------|------------|---------|---------|
| S3: Hybrid Reactive | 1 | 69.6 ± nan | 90.1 ± nan | 120.4 ± nan | 0.0000 | 73.2 | 87840 | 117 ± nan | 14.0 | 0.0 | 119535 | 6465 |
| S4: Hybrid Predictive | 1 | 70.8 ± nan | 100.3 ± nan | 152.6 ± nan | 0.0000 | 73.2 | 87840 | 254 ± nan | 5.0 | 0.0 | 120315 | 5685 |

## 2. H1 Comparisons — Hybrid vs Baselines

## 3. H2 Comparisons — Predictive vs Reactive

### s4-hybrid-predictive vs s3-hybrid-reactive — p99_latency_ms (Predictive vs Reactive)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 120.45 ± nan (n=1) |
| Comparison mean ± std | 152.63 ± nan (n=1) |
| Difference | +32.19 (+26.7%) |
| Welch t-stat | nan |
| Welch p-value (raw) | nan |
| Welch p-value (Holm-Bonferroni) | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p (raw) | 1.0000 |
| Mann-Whitney p (Holm-Bonferroni) | 1.0000 |
| Bootstrap 95% CI | [+32.19, +32.19] |
| Cohen's d | nan (large) |
| Verdict (Welch corrected) | ⚠️ Not significant |
| Verdict (MW corrected) | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive — slo_violations_k6 (Predictive vs Reactive)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 117.00 ± nan (n=1) |
| Comparison mean ± std | 254.00 ± nan (n=1) |
| Difference | +137.00 (+117.1%) |
| Welch t-stat | nan |
| Welch p-value (raw) | nan |
| Welch p-value (Holm-Bonferroni) | nan |
| Mann-Whitney U | 1.0 |
| Mann-Whitney p (raw) | 1.0000 |
| Mann-Whitney p (Holm-Bonferroni) | 1.0000 |
| Bootstrap 95% CI | [+137.00, +137.00] |
| Cohen's d | nan (large) |
| Verdict (Welch corrected) | ⚠️ Not significant |
| Verdict (MW corrected) | ⚠️ Not significant |

## 4. Cost Proxy Analysis

Cost proxy: `cost(β) = k8s_WTP + β × srv_WTP`, normalized so S1 mean = 1.0

| Scenario | Serverless Share | Violation Rate | β=0.5 | β=0.7 | β=1.0 | β=1.5 |
|----------|-----------------|----------------|-------|-------|-------|-------|
| S3: Hybrid Reactive | 0.051 ± nan | 0.0013 ± nan | 122767.500 ± nan | 124060.500 ± nan | 126000.000 ± nan | 129232.500 ± nan |
| S4: Hybrid Predictive | 0.045 ± nan | 0.0029 ± nan | 123157.500 ± nan | 124294.500 ± nan | 126000.000 ± nan | 128842.500 ± nan |

## 5. Key Findings Summary

- **Total comparisons:** 2
- **Significant after Holm-Bonferroni (Welch):** 0/2
- **Significant after Holm-Bonferroni (Mann-Whitney):** 0/2

- s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms): Δ=+32.19 (+26.7%), d=nan (large), Welch p=nan ⚠️, MW p=1.0000 ⚠️
- s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6): Δ=+137.00 (+117.1%), d=nan (large), Welch p=nan ⚠️, MW p=1.0000 ⚠️
