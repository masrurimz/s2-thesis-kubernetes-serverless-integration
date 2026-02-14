> **⚠️ INVALIDATED (2026-02-14):** This experiment's controller decision data is invalidated due to three critical bugs fixed on 2026-02-14 (SLO monitor wrong HAProxy column, Algorithm 1 priority reversal, Prometheus not scraping daemon). k6 end-to-end latency data may remain valid but is not comparable to post-fix `/work` endpoint runs. See `results/claims/INCONSISTENCIES.md`.

# Phase B: Replicated Experiments (20 Runs)

**Date:** 2026-02-12 (21:26 - 23:09)
**Design:** 5 runs × 4 scenarios, randomized order, 100 RPS, 300s each

## Per-Run Results

### S1 (K8s-only)

| Run | p50 (ms) | p95 (ms) | p99 (ms) | Throughput | Violations | Error Rate |
|-----|----------|----------|----------|------------|------------|------------|
| 1 | 5.11 | 9.71 | 587.12 | 77.27 | 1 | 0% |
| 2 | 5.00 | 9.50 | 9.90 | 190.13 | 0 | 0% |
| 3 | 5.26 | 9.99 | 775.94 | 59.91 | 1 | 0% |
| 4 | 5.20 | 9.88 | 842.50 | 56.58 | 1 | 0% |
| 5 | 5.15 | 9.78 | 383.73 | 87.64 | 1 | 0% |
| **Mean** | **5.14** | **9.77** | **519.84** | **94.31** | **4/5** | **0%** |

### S2 (Serverless-only)

| Run | p50 (ms) | p95 (ms) | p99 (ms) | Throughput | Violations | Error Rate |
|-----|----------|----------|----------|------------|------------|------------|
| 1 | 5.13 | 9.75 | 440.38 | 85.24 | 1 | 0% |
| 2 | 5.24 | 9.96 | 781.66 | 46.74 | 1 | 0% |
| 3 | 5.10 | 9.70 | 404.00 | 88.22 | 1 | 0% |
| 4 | 5.14 | 9.77 | 447.50 | 77.00 | 1 | 0% |
| 5 | 5.00 | 9.50 | 9.90 | 201.16 | 0 | 0% |
| **Mean** | **5.12** | **9.74** | **416.69** | **99.67** | **4/5** | **0%** |

### S3 (Hybrid Reactive)

| Run | p50 (ms) | p95 (ms) | p99 (ms) | Throughput | Violations | Scale_Out | Maintain |
|-----|----------|----------|----------|------------|------------|-----------|----------|
| 1 | 5.09 | 9.67 | 331.33 | 80.23 | 1 | 19 | 2 |
| 2 | 5.10 | 9.68 | 410.77 | 67.97 | 1 | 18 | 2 |
| 3 | 5.23 | 9.93 | 891.47 | 56.40 | 1 | 19 | 2 |
| 4 | 5.09 | 9.66 | 216.30 | 98.60 | 1 | 16 | 4 |
| 5 | 5.05 | 9.59 | 9.99 | 84.44 | 0 | 13 | 8 |
| **Mean** | **5.11** | **9.71** | **371.97** | **77.53** | **4/5** | **17.0** | **3.6** |

### S4 (Hybrid Predictive)

| Run | p50 (ms) | p95 (ms) | p99 (ms) | Throughput | Violations | Scale_Out | Predictive | Maintain |
|-----|----------|----------|----------|------------|------------|-----------|------------|----------|
| 1 | 5.10 | 9.70 | 287.94 | 86.91 | 1 | 15 | 0 | 4 |
| 2 | 5.13 | 9.74 | 294.46 | 99.38 | 1 | 14 | 0 | 5 |
| 3 | 5.12 | 9.72 | 372.50 | 72.11 | 1 | 18 | 0 | 2 |
| 4 | 5.26 | 50.38 | 814.17 | 49.73 | 1 | 19 | 0 | 2 |
| 5 | 5.12 | 9.72 | 384.80 | 83.20 | 1 | 19 | 0 | 2 |
| **Mean** | **5.15** | **17.85** | **430.77** | **78.27** | **5/5** | **17.0** | **0** | **3.0** |

## Aggregate Comparison

| Scenario | Mean p99 (ms) | Std p99 | Mean Throughput | Violation Rate |
|----------|--------------|---------|-----------------|----------------|
| S1 (K8s-only) | 519.84 | 332.9 | 94.31 | 80% (4/5) |
| S2 (Serverless) | 416.69 | 283.8 | 99.67 | 80% (4/5) |
| S3 (Hybrid Reactive) | 371.97 | 319.6 | 77.53 | 80% (4/5) |
| S4 (Hybrid Predictive) | 430.77 | 216.1 | 78.27 | 100% (5/5) |

## Known Data Issues

1. **PREDICTIVE = 0 in all 20 runs.** The GRU pipeline was running but no PREDICTIVE actions triggered during Phase B. This means Phase B does NOT validate H2 mechanism — only Phase A1 ramp test does.
2. **Suspicious outlier runs:** S1-run2 (p99=9.9ms, throughput=190), S2-run5 (p99=9.9ms, throughput=201), S3-run5 (p99=10ms, throughput=84) all have abnormally low p99. Likely Prometheus had stale/reset metrics for these runs.
3. **S4-run4 p95 anomaly:** p95=50.38ms while all other runs show p95~9.7ms. Data collection artifact.
4. **Previous reports claimed "S1 mean=400.9ms, S4 mean=558.0ms"** — these don't match the raw per-run data above. The old reports may have excluded outlier runs or used different aggregation.

## Statistical Tests (Recomputed from Raw Data)

Using all 5 runs per scenario:

### H1: S4 vs S1 (p99 latency)
- S1 mean: 519.84ms (std=332.9)
- S4 mean: 430.77ms (std=216.1)
- Difference: -89.07ms (S4 actually LOWER)
- Note: High variance makes this statistically unreliable

### H2: S4 vs S3 (violations)
- S3: 4/5 runs had violations
- S4: 5/5 runs had violations
- S4 is WORSE, not better

## Honest Verdict

Phase B controlled experiments do NOT demonstrate superiority for H1 or H2. The environment limitations (k3d localhost, 100 RPS insufficient) and PREDICTIVE=0 mean this phase validates only that the system runs without errors, not that it outperforms baselines.

Source: `raw/experiments_final.json`
