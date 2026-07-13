# Final Experiment Numbers

**Date:** 2026-07-13
**Rule:** Thesis Ch4/Ch5/abstracts must use ONLY numbers from this file.

---

## Two evidence tiers (read this first)

| Tier | Bundle | What it is | Inferential status |
|---|---|---|---|
| **Diagnostic (n=1)** | `results/experiments/phase-b/2026-07-11_scaling_fix_n1` | Four-scenario (S1–S4) single-run diagnostic | Descriptive only. Directional mechanism evidence. |
| **Paired H2 (n=5, clean)** | `results/experiments/phase-b/2026-07-12_paired-h2-clean-v2` | Counterbalanced S3/S4 paired comparison, full treatment delivery | **Valid.** All 5 pairs delivered complete forecasts. H2 not supported but direction in S4's favor. |

The earlier `2026-07-11_paired-h2` bundle is retained as treatment-confounded historical record (only 3/5 S4 runs delivered forecasts). It is superseded by the clean v2 bundle.

---

## Tier 1 — Diagnostic four-scenario summary (n=1)

| Scenario | p99 (ms) | SLO Violations | SLO Rate | Serverless % |
|---|---|---|---|---|
| S1 (K8s+HPA) | 2,421.3 | 6,717 | 7.66% | 0.0% |
| S2 (Serverless) | 77.7 | 19 | 0.02% | 100.0% |
| S3 (Hybrid-reactive) | 98.8 | 3 | 0.00% | 31.8% |
| S4 (Hybrid-predictive) | 118.2 | 104 | 0.12% | 24.7% |

**H1 (hybrid > pure K8s):** Directional only (n=1). S4 p99 118.2 ms vs S1 2,421.3 ms (−95.1%).

---

## Tier 2 — Clean paired H2 result (n=5, full treatment delivery)

**Source:** `results/experiments/phase-b/2026-07-12_paired-h2-clean-v2/paired_analysis.json`

### Primary: p99 latency

| Metric | S3 (Reactive) | S4 (Predictive) | Difference |
|---|---|---|---|
| Mean p99 (ms) | 136.62 | 128.54 | −8.08 |
| 95% paired CI (ms) | — | — | [−36.70, +14.53] |
| Permutation p (two-sided) | — | — | 0.3784 |
| Cohen's d (paired) | — | — | −0.241 (small, S4 better) |

**Per-pair p99 (ms):**

| Pair | S3 | S4 | Diff | S4 better? |
|---|---|---|---|---|
| 1 | 112.7 | 134.1 | +21.3 | No |
| 2 | 157.6 | 137.5 | −20.1 | Yes |
| 3 | 119.1 | 129.3 | +10.2 | No |
| 4 | 173.0 | 111.7 | −61.4 | Yes |
| 5 | 120.6 | 130.2 | +9.6 | No |

**Verdict:** H2 (predictive latency superiority) is **not supported**. The mean difference is in S4's favorable direction (−8.1 ms), but the 95% CI includes zero and the permutation test is not significant (p=0.38). S4 wins 2 of 5 pairs.

### Secondary: SLO violations (notable)

| Metric | S3 mean | S4 mean | Difference | Cohen's d |
|---|---|---|---|---|
| SLO violations | 228.2 | 100.8 | −127.4 (−56%) | −0.535 (medium) |

S4 shows a **medium effect size** reduction in SLO violations (d=−0.535), though not statistically significant at n=5 (p=0.19). This suggests the proactive scaling keeps p99 below the SLO threshold more consistently, even when the mean p99 difference is small.

### Treatment fidelity (all 5 S4 runs)

| Field | Value |
|---|---|
| Eligible cycles per run | 56 |
| Model history ready | True (all runs) |
| Forecast horizon sufficient | True (all runs) |
| Delivery rate | 100% (0 failures) |
| Total predictions delivered | 280 (56 × 5 runs) |

### Comparison with previous (confounded) bundle

| Bundle | S3 mean | S4 mean | Diff | Direction |
|---|---|---|---|---|
| `2026-07-11_paired-h2` (confounded) | 111.2 ms | 121.3 ms | +10.0 ms | S4 worse |
| `2026-07-12_paired-h2-clean-v2` (clean) | 136.6 ms | 128.5 ms | −8.1 ms | S4 better |

The mechanism repair (alpha=1/r_effective, buffer=1.0) reversed the effect direction from S4-worse to S4-better. The difference is not statistically significant, but the reversal demonstrates that the calibration fix changed S4's operational behavior.

---

## Diagnostic cost model (n=1, directional only)

The n=1 AWS monthly projection (S1=USD 132, S2=USD 394, S3=USD 147, S4=USD 142/mo) is a directional diagnostic cost model only. It must not be used to rank S3 and S4 or claim monthly savings.
