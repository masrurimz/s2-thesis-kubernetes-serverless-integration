# Phase B Reanalysis — All 20 Runs (No Outlier Exclusion)

**Generated:** 2026-09-11T13:23:02.979710
**Runs per scenario:** 5 × 4 = 20 total
**Outliers excluded:** None

## 1. Per-Scenario Summary

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | Total Req | SLO Viol | Scale-Up | Scale-Down | k8s WTP | srv WTP |
|----------|---|----------|----------|----------|--------|-----|-----------|----------|----------|------------|---------|---------|
| S3: Hybrid Reactive | 5 | 69.1 ± 0.4 | 87.9 ± 2.2 | 103.7 ± 4.8 | 0.0000 | 73.2 | 87840 | 9 ± 12 | 15.0 | 0.0 | 118893 | 7107 |
| S4: Hybrid Predictive | 5 | 69.4 ± 0.5 | 91.9 ± 4.1 | 120.5 ± 16.3 | 0.0000 | 73.2 | 87840 | 79 ± 81 | 5.0 | 0.0 | 120243 | 5757 |

## 2. H1 Comparisons — Hybrid vs Baselines

## 3. H2 Comparisons — Predictive vs Reactive

### s4-hybrid-predictive vs s3-hybrid-reactive — p99_latency_ms (Predictive vs Reactive)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 103.72 ± 4.82 (n=5) |
| Comparison mean ± std | 120.51 ± 16.30 (n=5) |
| Difference | +16.79 (+16.2%) |
| Welch t-stat | 2.208 |
| Welch p-value (raw) | 0.0818 |
| Welch p-value (Holm-Bonferroni) | 0.1636 |
| Mann-Whitney U | 23.0 |
| Mann-Whitney p (raw) | 0.0317 |
| Mann-Whitney p (Holm-Bonferroni) | 0.0635 |
| Bootstrap 95% CI | [+4.91, +31.03] |
| Cohen's d | 1.397 (large) |
| Verdict (Welch corrected) | ⚠️ Not significant |
| Verdict (MW corrected) | ⚠️ Not significant |

### s4-hybrid-predictive vs s3-hybrid-reactive — slo_violations_k6 (Predictive vs Reactive)

| Statistic | Value |
|-----------|-------|
| Baseline mean ± std | 9.20 ± 11.69 (n=5) |
| Comparison mean ± std | 79.00 ± 80.97 (n=5) |
| Difference | +69.80 (+758.7%) |
| Welch t-stat | 1.908 |
| Welch p-value (raw) | 0.1262 |
| Welch p-value (Holm-Bonferroni) | 0.1636 |
| Mann-Whitney U | 23.0 |
| Mann-Whitney p (raw) | 0.0317 |
| Mann-Whitney p (Holm-Bonferroni) | 0.0635 |
| Bootstrap 95% CI | [+15.20, +139.60] |
| Cohen's d | 1.207 (large) |
| Verdict (Welch corrected) | ⚠️ Not significant |
| Verdict (MW corrected) | ⚠️ Not significant |

## 4. Cost Proxy Analysis

Cost proxy: `cost(β) = k8s_WTP + β × srv_WTP`, normalized so S1 mean = 1.0

| Scenario | Serverless Share | Violation Rate | β=0.5 | β=0.7 | β=1.0 | β=1.5 |
|----------|-----------------|----------------|-------|-------|-------|-------|
| S3: Hybrid Reactive | 0.056 ± 0.003 | 0.0001 ± 0.0001 | 122446.500 ± 183.513 | 123867.900 ± 110.108 | 126000.000 ± 0.000 | 129553.500 ± 183.513 |
| S4: Hybrid Predictive | 0.046 ± 0.001 | 0.0009 ± 0.0009 | 123121.500 ± 56.970 | 124272.900 ± 34.182 | 126000.000 ± 0.000 | 128878.500 ± 56.970 |

## 5. Key Findings Summary

- **Total comparisons:** 2
- **Significant after Holm-Bonferroni (Welch):** 0/2
- **Significant after Holm-Bonferroni (Mann-Whitney):** 0/2

- s4-hybrid-predictive vs s3-hybrid-reactive (p99_latency_ms): Δ=+16.79 (+16.2%), d=1.397 (large), Welch p=0.1636 ⚠️, MW p=0.0635 ⚠️
- s4-hybrid-predictive vs s3-hybrid-reactive (slo_violations_k6): Δ=+69.80 (+758.7%), d=1.207 (large), Welch p=0.1636 ⚠️, MW p=0.0635 ⚠️
