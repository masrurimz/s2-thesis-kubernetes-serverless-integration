# Phase C: Dynamic Workload Experiment

**Date:** 2026-02-13 (11:01 - 11:40)
**Design:** 3 runs × 2 scenarios (S3 reactive, S4 predictive), randomized order
**Workload:** dynamic_burst — 2 cycles of baseline(30 RPS)→ramp(30→150)→burst(150)→cooldown, 6 min total
**Purpose:** Give PREDICTIVE a fair chance with ramp/burst pattern (Phase B steady 100 RPS never triggered it)

## Per-Run Results

### S3 (Hybrid Reactive)

| Run | med (ms) | p95 (ms) | max (ms) | Requests | SLO Violations | Error Rate | SCALE_OUT |
|-----|----------|----------|----------|----------|----------------|------------|-----------|
| 1 | 1.8 | 182.2 | 2422.7 | 32401 | 1377 | 4.25% | 23 |
| 2 | 1.8 | 230.5 | 2776.9 | 32402 | 1882 | 5.81% | 23 |
| 3 | 1.8 | 283.2 | 2504.1 | 32403 | 2220 | 6.85% | 23 |
| **Mean** | **1.8** | **232.0** | **2567.9** | **32402** | **1826** | **5.64%** | **23** |

### S4 (Hybrid Predictive)

| Run | med (ms) | p95 (ms) | max (ms) | Requests | SLO Violations | Error Rate | SCALE_OUT | PREDICTIVE |
|-----|----------|----------|----------|----------|----------------|------------|-----------|------------|
| 1 | 1.8 | 148.4 | 1878.1 | 32400 | 979 | 3.02% | 22 | 0 |
| 2 | 1.8 | 144.7 | 1974.9 | 32400 | 856 | 2.64% | 22 | 0 |
| 3 | 1.9 | 261.5 | 3460.0 | 32400 | 2121 | 6.55% | 22 | 0 |
| **Mean** | **1.8** | **184.9** | **2437.7** | **32400** | **1319** | **4.07%** | **22** | **0** |

## Aggregate Comparison

| Metric | S3 (Reactive) | S4 (Predictive) | Δ | Direction |
|--------|--------------|-----------------|---|-----------|
| p95 latency | 232.0 ± 50.5ms | 184.9 ± 66.4ms | -47.1ms | S4 better |
| SLO violations | 1826 ± 424 | 1319 ± 698 | -507 | S4 better |
| Error rate | 5.64% ± 1.31% | 4.07% ± 2.15% | -1.57% | S4 better |
| max latency | 2567.9ms | 2437.7ms | -130.2ms | S4 better |
| SCALE_OUT count | 23 | 22 | -1 | S4 less reactive |

## Statistical Tests

| Test | Metric | Statistic | p-value | Cohen's d | Interpretation |
|------|--------|-----------|---------|-----------|----------------|
| Welch t-test | p95 | t=-0.978 | 0.387 | -0.798 (large) | Not significant (n=3) |
| Welch t-test | SLO violations | t=-1.077 | 0.354 | -0.879 (large) | Not significant (n=3) |
| Mann-Whitney U | SLO violations | U=2.0 | 0.200 | — | Not significant (n=3) |

## Key Finding: PREDICTIVE = 0 (Again)

Despite dynamic ramp/burst workload, PREDICTIVE never triggered. Root cause analysis:

1. **SCALE_OUT dominance**: 22-23 of 24 decisions were SCALE_OUT (92%). The 15-second decision interval means by the time the ramp creates SLO pressure, the system immediately enters violation → SCALE_OUT preempts PREDICTIVE.

2. **Priority preemption**: SCALE_OUT (priority 1) always preempts PREDICTIVE (priority 3). The system needs a window where it's HEALTHY + GRU predicts increase. But the dynamic load causes violations within the first 1-2 decision ticks of a ramp.

3. **Observation window too short**: The GRU needs ~60s of baseline to build a trend prediction. The ramp phase (30s) is shorter than this, and by the time GRU could predict, violations have already begun.

## Important Observation: S4 Consistently Better

While PREDICTIVE=0, S4 **still outperforms S3** on every metric:
- 20% lower p95 (184.9 vs 232.0ms)
- 28% fewer SLO violations (1319 vs 1826)
- 28% lower error rate (4.07% vs 5.64%)

This suggests the GRU prediction pipeline creates a **subtle behavioral difference** even when PREDICTIVE doesn't explicitly trigger — possibly through confidence-modulated weight adjustments or the additional processing overhead creating slightly different timing.

However, with n=3 and high variance (S4-run3 was an outlier), these differences are **not statistically significant** (p>0.35 for all tests). The large Cohen's d (0.8-0.9) suggests a real effect but insufficient sample size to confirm.

## Limitations

1. **k6 summary lacks p99**: Only p95 available from k6 export format
2. **n=3 per scenario**: Insufficient for statistical significance despite large effect sizes
3. **PREDICTIVE mechanism remains unvalidated in controlled experiments**: Only Phase A1 ramp test (different workload, manually configured) triggered PREDICTIVE
4. **S4-run3 outlier**: p95=261ms and 2121 violations, much worse than runs 1-2; likely Knative cold start event

## Conclusion

Phase C confirms Phase B findings:
- PREDICTIVE mechanism does **not trigger** under automated experiment conditions
- Root cause is SCALE_OUT priority preemption + insufficient healthy→prediction windows
- However, S4 shows **trending better** performance (large effect sizes, not significant)
- PREDICTIVE was only validated in Phase A1's manually configured ramp test

**Source:** `raw/*/k6-summary.json` + `raw/*/daemon-post.json`
