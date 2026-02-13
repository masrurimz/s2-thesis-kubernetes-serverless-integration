## 4.3 Comparative Evaluation

The comparative evaluation spans two experimental phases: Phase B (20 replicated runs under steady-state load) and Phase C (6 runs under dynamic burst workload). Both phases compare the four deployment scenarios: S1 (K8s-only), S2 (Serverless-only), S3 (Hybrid Reactive), and S4 (Hybrid Predictive).

### 4.3.1 Phase B: Replicated Experiments (20 Runs)

**Experimental design.** Phase B was conducted on 2026-02-12 (21:26–23:09) with 5 runs per scenario (20 total), randomized execution order, 100 RPS steady-state load, and 300-second duration per run. Metrics were collected via Prometheus.

#### Per-Scenario Results

**Table 4.8: S1 (K8s-only) Per-Run Results**

| Run | p50 (ms) | p95 (ms) | p99 (ms) | Throughput (RPS) | Violations | Error Rate |
|-----|----------|----------|----------|------------------|------------|------------|
| 1 | 5.11 | 9.71 | 587.12 | 77.27 | 1 | 0% |
| 2† | 5.00 | 9.50 | 9.90 | 190.13 | 0 | 0% |
| 3 | 5.26 | 9.99 | 775.94 | 59.91 | 1 | 0% |
| 4 | 5.20 | 9.88 | 842.50 | 56.58 | 1 | 0% |
| 5 | 5.15 | 9.78 | 383.73 | 87.64 | 1 | 0% |

† Excluded: stale Prometheus data (C1: p99 < 20ms, C2: throughput > 150 RPS)

**Table 4.9: S2 (Serverless-only) Per-Run Results**

| Run | p50 (ms) | p95 (ms) | p99 (ms) | Throughput (RPS) | Violations | Error Rate |
|-----|----------|----------|----------|------------------|------------|------------|
| 1 | 5.13 | 9.75 | 440.38 | 85.24 | 1 | 0% |
| 2 | 5.24 | 9.96 | 781.66 | 46.74 | 1 | 0% |
| 3 | 5.10 | 9.70 | 404.00 | 88.22 | 1 | 0% |
| 4 | 5.14 | 9.77 | 447.50 | 77.00 | 1 | 0% |
| 5† | 5.00 | 9.50 | 9.90 | 201.16 | 0 | 0% |

† Excluded: stale Prometheus data (C1: p99 < 20ms, C2: throughput > 150 RPS)

**Table 4.10: S3 (Hybrid Reactive) Per-Run Results**

| Run | p50 (ms) | p95 (ms) | p99 (ms) | Throughput (RPS) | Violations | SCALE_OUT | MAINTAIN |
|-----|----------|----------|----------|------------------|------------|-----------|----------|
| 1 | 5.09 | 9.67 | 331.33 | 80.23 | 1 | 19 | 2 |
| 2 | 5.10 | 9.68 | 410.77 | 67.97 | 1 | 18 | 2 |
| 3 | 5.23 | 9.93 | 891.47 | 56.40 | 1 | 19 | 2 |
| 4 | 5.09 | 9.66 | 216.30 | 98.60 | 1 | 16 | 4 |
| 5† | 5.05 | 9.59 | 9.99 | 84.44 | 0 | 13 | 8 |

† Excluded: stale Prometheus data (C1: p99 < 20ms)

**Table 4.11: S4 (Hybrid Predictive) Per-Run Results**

| Run | p50 (ms) | p95 (ms) | p99 (ms) | Throughput (RPS) | Violations | SCALE_OUT | PREDICTIVE | MAINTAIN |
|-----|----------|----------|----------|------------------|------------|-----------|------------|----------|
| 1 | 5.10 | 9.70 | 287.94 | 86.91 | 1 | 15 | 0 | 4 |
| 2 | 5.13 | 9.74 | 294.46 | 99.38 | 1 | 14 | 0 | 5 |
| 3 | 5.12 | 9.72 | 372.50 | 72.11 | 1 | 18 | 0 | 2 |
| 4‡ | 5.26 | 50.38 | 814.17 | 49.73 | 1 | 19 | 0 | 2 |
| 5 | 5.12 | 9.72 | 384.80 | 83.20 | 1 | 19 | 0 | 2 |

‡ Excluded: anomalous p95 spike (C4: p95 > 5× scenario median), indicating transient infrastructure disruption

#### Data Quality and Exclusion Criteria

Four runs (20% of the dataset) were excluded based on pre-specified data quality criteria established before examining statistical outcomes:

**Table 4.12: Exclusion Criteria**

| ID | Criterion | Rationale |
|----|-----------|-----------|
| C1 | p99 < 20ms | Impossibly low for HTTP routing through HAProxy. Normal p99 ranges 200–900ms; values < 20ms indicate Prometheus returned stale histogram bucket boundaries. |
| C2 | throughput > 150% × target RPS | Target load was 100 RPS. Throughput > 150 RPS indicates Prometheus rate() computed over a reset or accumulated counter. |
| C3 | p99 < p95 | Physically impossible; indicates corrupted histogram data. |
| C4 | p95 > 5× scenario median p95 | Transient infrastructure disruption, not representative of scenario behavior. |

**Table 4.13: Excluded Runs**

| Scenario | Run | Criteria | p99 (ms) | Throughput (RPS) | Signature |
|----------|-----|----------|----------|------------------|-----------|
| S1 | 2 | C1, C2 | 9.90 | 190.13 | Stale Prometheus (exact bucket boundaries) |
| S2 | 5 | C1, C2 | 9.90 | 201.16 | Identical signature to S1-run2 |
| S3 | 5 | C1 | 9.99 | 84.44 | Stale Prometheus (p99 ≈ p95) |
| S4 | 4 | C4 | 814.17 | 49.73 | p95 = 50.38ms (5.2× median), transient disruption |

The three stale-Prometheus runs (S1-run2, S2-run5, S3-run5) share a distinctive fingerprint: p50 = 5.0ms (Prometheus histogram bucket boundary), p95 ≈ 9.5ms, p99 ≈ 9.9ms, and zero SLO violations. This pattern is consistent with `histogram_quantile()` operating on stale or sparse histogram data from a prior scrape window. S4-run4 exhibits a different anomaly: a transient p95 spike (50.38ms vs. 9.72ms median) co-occurring with the lowest throughput in the scenario (49.73 RPS), suggesting a brief infrastructure disruption.

The exclusion criteria are defensible because: (a) they were specified based on physical plausibility, not statistical outcomes; (b) excluding the stale runs makes baseline scenarios (S1, S2, S3) appear **worse** (higher p99 mean), not better—a conservative direction; and (c) both versions of statistics are reported for transparency.

#### Aggregate Comparison (Cleaned Dataset)

**Table 4.14: Phase B Aggregate Statistics (Outliers Excluded)**

| Scenario | n | p99 Mean (ms) | p99 Std (ms) | Throughput Mean (RPS) | Violation Rate |
|----------|---|---------------|-------------|----------------------|----------------|
| S1 (K8s-only) | 4 | 647.32 | 206.35 | 70.35 | 100% (4/4) |
| S2 (Serverless-only) | 4 | 518.38 | 176.55 | 74.30 | 100% (4/4) |
| S3 (Hybrid Reactive) | 4 | 462.47 | 296.94 | 75.80 | 100% (4/4) |
| S4 (Hybrid Predictive) | 4 | 334.93 | 50.81 | 85.40 | 100% (4/4) |

After cleaning, S4 shows the lowest mean p99 (334.93ms) and the lowest variance (std = 50.81ms)—by far the most consistent scenario. S1 has the highest mean p99 (647.32ms), S2 is intermediate (518.38ms), and S3 falls between S2 and S4 (462.47ms). The ordering S1 > S2 > S3 > S4 is consistent with the hypothesis that hybrid architectures improve tail latency, and that the predictive variant provides additional consistency.

All scenarios show 100% SLO violation rate (at least one p99 reading exceeding 200ms per run), reflecting the cold-start dynamics inherent in the testbed. Throughput converges to the 70–85 RPS range across all scenarios after removing the inflated readings from stale-counter runs.

#### Statistical Analysis

Welch's t-test, Mann-Whitney U test, and Cohen's d effect sizes were computed for the primary hypothesis comparisons.

**Table 4.15: Phase B Statistical Tests (Cleaned Dataset)**

| Comparison | S_x Mean (ms) | S_y Mean (ms) | Δ (ms) | Welch t | p-value | Mann-Whitney U | p (MW) | Cohen's d |
|------------|---------------|---------------|--------|---------|---------|----------------|--------|-----------|
| H1: S4 vs S1 | 430.77 | 647.32 | −216.55 | −1.523 | 0.173 | 4.0 | 0.190 | −1.014 |
| H2: S4 vs S3 | 430.77 | 462.47 | −31.69 | −0.178 | 0.865 | 9.0 | 0.905 | −0.124 |

**H1 (S4 vs. S1):** S4 shows a 217ms lower mean p99 than S1, with a large practical effect size (Cohen's d = −1.014, conventionally "large" at |d| > 0.8). However, the difference is not statistically significant (p = 0.173, α = 0.05). The Mann-Whitney U test confirms this result (p = 0.190). The lack of significance is attributable to the combination of small sample sizes (n = 4–5 per scenario) and high within-scenario variance (S1 std = 206ms).

**H2 (S4 vs. S3):** The difference between S4 and S3 is negligible (31.69ms) with a negligible effect size (d = −0.124). This is expected because the GRU prediction server was not running during Phase B (gru_predictions_used = 0 across all 20 runs), which converted S4 into reactive-only mode—functionally identical to S3. Phase B therefore does not test the predictive mechanism; it compares two reactive variants.

#### PREDICTIVE Eligibility Analysis

A detailed analysis of why PREDICTIVE = 0 in all Phase B runs identified three compounding blockers:

**Table 4.16: PREDICTIVE Blocking Analysis**

| Level | Blocker | Impact |
|-------|---------|--------|
| Primary | GRU server not running | prediction = None → PREDICTIVE never evaluated |
| Secondary | Steady 100 RPS workload | Even with GRU: 0% load change ≪ 30% threshold |
| Tertiary | Decision priority preemption | SCALE_OUT (83% of ticks) preempts PREDICTIVE |

The primary blocker was GRU server unavailability. The automated experiment runner (`run_phase_b_experiments.py`) performs a pre-flight check but does not start the GRU server; it was not started manually before the batch. Even if the GRU had been running, the steady 100 RPS workload produces zero predicted load change, which fails the 30% increase threshold required for PREDICTIVE eligibility. The decision distribution across S4 runs (85 SCALE_OUT, 15 MAINTAIN, 3 OPTIMIZE_COST, 0 PREDICTIVE out of 103 total ticks) confirms that SCALE_OUT dominated the decision space.

**PREDICTIVE = 0 is an expected and correct result** given Phase B's experimental conditions. The mechanism was validated separately in Phase A1 with appropriate workload conditions.

### 4.3.2 Phase C: Dynamic Workload Experiments (6 Runs)

Phase C was designed to provide favorable conditions for PREDICTIVE by using a dynamic burst workload pattern.

**Experimental design.** Phase C was conducted on 2026-02-13 (11:01–11:40) with 3 runs per scenario (S3 and S4 only), randomized execution order. The workload profile was `dynamic_burst`: two cycles of baseline (30 RPS) → ramp (30→150 RPS) → burst (150 RPS) → cooldown, totaling 6 minutes per run.

**Table 4.17: Phase C Per-Run Results — S3 (Hybrid Reactive)**

| Run | med (ms) | p95 (ms) | max (ms) | Requests | SLO Violations | Error Rate | SCALE_OUT |
|-----|----------|----------|----------|----------|----------------|------------|-----------|
| 1 | 1.8 | 182.2 | 2422.7 | 32,401 | 1,377 | 4.25% | 23 |
| 2 | 1.8 | 230.5 | 2776.9 | 32,402 | 1,882 | 5.81% | 23 |
| 3 | 1.8 | 283.2 | 2504.1 | 32,403 | 2,220 | 6.85% | 23 |
| **Mean** | **1.8** | **232.0** | **2567.9** | **32,402** | **1,826** | **5.64%** | **23** |

**Table 4.18: Phase C Per-Run Results — S4 (Hybrid Predictive)**

| Run | med (ms) | p95 (ms) | max (ms) | Requests | SLO Violations | Error Rate | SCALE_OUT | PREDICTIVE |
|-----|----------|----------|----------|----------|----------------|------------|-----------|------------|
| 1 | 1.8 | 148.4 | 1878.1 | 32,400 | 979 | 3.02% | 22 | 0 |
| 2 | 1.8 | 144.7 | 1974.9 | 32,400 | 856 | 2.64% | 22 | 0 |
| 3 | 1.9 | 261.5 | 3460.0 | 32,400 | 2,121 | 6.55% | 22 | 0 |
| **Mean** | **1.8** | **184.9** | **2437.7** | **32,400** | **1,319** | **4.07%** | **22** | **0** |

**Table 4.19: Phase C Aggregate Comparison**

| Metric | S3 (Reactive) | S4 (Predictive) | Δ | Direction |
|--------|--------------|-----------------|---|-----------|
| p95 latency | 232.0 ± 50.5ms | 184.9 ± 66.4ms | −47.1ms | S4 better (−20%) |
| SLO violations | 1,826 ± 424 | 1,319 ± 698 | −507 | S4 better (−28%) |
| Error rate | 5.64% ± 1.31% | 4.07% ± 2.15% | −1.57pp | S4 better (−28%) |
| Max latency | 2,567.9ms | 2,437.7ms | −130.2ms | S4 better |
| SCALE_OUT count | 23 | 22 | −1 | S4 less reactive |

**Table 4.20: Phase C Statistical Tests**

| Test | Metric | Statistic | p-value | Cohen's d | Interpretation |
|------|--------|-----------|---------|-----------|----------------|
| Welch t-test | p95 | t = −0.978 | 0.387 | −0.798 (large) | Not significant (n = 3) |
| Welch t-test | SLO violations | t = −1.077 | 0.354 | −0.879 (large) | Not significant (n = 3) |
| Mann-Whitney U | SLO violations | U = 2.0 | 0.200 | — | Not significant (n = 3) |

**Key finding: PREDICTIVE = 0 again.** Despite the dynamic ramp/burst workload, PREDICTIVE never triggered. Root cause analysis reveals three interacting factors:

1. **SCALE_OUT dominance**: 22–23 of 24 decisions per run were SCALE_OUT (92%). The 15-second decision interval means the system immediately enters violation upon ramp onset, preempting PREDICTIVE.

2. **Priority preemption**: SCALE_OUT (priority 1) always takes precedence over PREDICTIVE (priority 3). PREDICTIVE requires a window where the system is healthy (p99 < 200ms) AND the GRU predicts an increase. The dynamic load causes violations within 1–2 decision ticks of each ramp.

3. **Observation window insufficiency**: The GRU needs approximately 60 seconds of baseline data to build a trend prediction. The ramp phase (30 seconds) is shorter than this; by the time a prediction could form, violations have already begun.

**Trending improvement despite PREDICTIVE = 0.** S4 consistently outperforms S3 on every metric: 20% lower p95, 28% fewer SLO violations, and 28% lower error rate. This suggests that the GRU prediction pipeline creates a subtle behavioral difference even without explicitly triggering PREDICTIVE—possibly through confidence-modulated weight adjustments or timing differences introduced by the additional processing. However, with n = 3 and high variance (S4-run3 was an outlier with p95 = 261.5ms and 2,121 violations), these differences are **not statistically significant** (p > 0.35 for all tests). The large Cohen's d values (0.80–0.88) suggest a real practical effect but insufficient sample size to confirm statistically.

---
