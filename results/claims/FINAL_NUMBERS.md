# Final Experiment Numbers

**Date:** 2026-07-10  
**Source:** REGISTRY.yaml `role: final` bundles only.  
**Rule:** Thesis Ch4/Ch5/abstracts must use ONLY numbers from this file.

---

## Scenario Summary (Thesis Comparison Table)

**S1/S2 from `experiments.2026-07-08-fib33-n5` (pre-proactive, V3 controller, n=5 each):**

| Scenario | p50 (ms) | p95 (ms) | p99 (ms) | SLO Violations |
|---|---|---|---|---|
| S1 (K8s+HPA) | 63.9 | 77.1 | 109.8 | 206 |
| S2 (Serverless) | 65.2 | 75.5 | 77.8 | 35 |

**S3/S4 from `experiments.2026-07-08-fib33-proactive` (proactive routing, n=5 each):**

| Scenario | p50 (ms) | p95 (ms) | p99 (ms) | SLO Violations |
|---|---|---|---|---|
| S3 (Hybrid-reactive) | 64.9 | 157.3 | 309.5 | 14027 |
| S4 (Hybrid-predictive) | 64.7 | 99.2 | 187.9 | 3509 |

**Note:** S3/S4 from the n5 bundle (pre-proactive: S3 p99=382.1, S4 p99=233.6) are superseded by the proactive bundle and should NOT be used for H2 comparison.

All scenarios: RPS=73.2, Error%=0.000, n=5, 0 excluded.

---

## Statistical Comparison: S4 vs S3 (H2 — Predictive vs Reactive)

From `experiments.2026-07-08-fib33-proactive`:

### p99 Latency (ms)

| Metric | Value |
|---|---|
| S3 mean | 309.54 |
| S4 mean | 187.90 |
| Difference | -121.65 (-39.3%) |
| Welch t-stat | -1.919 |
| Welch p-value | 0.1216 |
| Mann-Whitney U | 9.0 |
| Mann-Whitney p | 0.5476 |
| 95% CI | [-229.35, -10.33] |
| Cohen's d | -1.214 (large) |
| Verdict | Not significant at α=0.05 |

### SLO Violations

| Metric | Value |
|---|---|
| S3 mean | 2805.40 |
| S4 mean | 701.80 |
| Difference | -2103.60 (-75.0%) |
| Welch t-stat | -1.922 |
| Welch p-value | 0.1247 |
| Mann-Whitney U | 9.0 |
| Mann-Whitney p | 0.5476 |
| 95% CI | [-3995.60, -239.80] |
| Cohen's d | -1.215 (large) |
| Verdict | Not significant at α=0.05 |

---

## S4 vs S1 (H1 — Hybrid vs Pure K8s)

From `experiments.2026-07-08-fib33-n5` (pre-proactive S4):

| Metric | Value |
|---|---|
| S1 mean p99 | 109.78 |
| S4 mean p99 | 233.64 |
| Difference | +123.86 (+112.8%) |
| Welch t-stat | 4.488 |
| Welch p-value | 0.0104 |
| Cohen's d | 2.839 (large) |
| Verdict | Significant — S4 is worse on p99 (localhost bias) |

**Interpretation:** On the localhost k3d testbed, hybrid routing adds overhead without the network-latency benefit of multi-node deployment. H1 superiority not supported; mechanism validated.

---

## GRU Model Performance

From `models/gru/2026-02-10_training-synthetic` (final):

| Metric | Value |
|---|---|
| Synthetic RMSE% (manual) | 6.01% |
| Synthetic RMSE% (post-HPO) | 4.75% |
| Synthetic MAE% | 4.91% |
| Inference latency | ~40ms |
| Confidence range (live) | 0.72–0.82 |

From `models/gru/2026-02-13_training-clarknet-calgary` (final):

| Metric | ClarkNet 5-min (best) |
|---|---|
| Real RMSE% | 17.78% |
| Real MAE% | 14.48% |
| Real MAPE | 18.74% |

---

## Phase A1 Mechanism Validation

From `experiments.2026-02-12-predictive-trigger` (final):

| Metric | Value |
|---|---|
| PREDICTIVE triggered at | p99=146ms (healthy) |
| Predicted load increase | 47% |
| Confidence | 72% |
| Total decisions | 18 |
| Decision distribution | SCALE_OUT:7, MAINTAIN:8, OPTIMIZE_COST:2, PREDICTIVE:1 |
| Weight shifting | 100/0 → 90/10 → ... → 50/50 verified |

---

## Cost Data

**Gap:** No cost bundle is marked `role: final` for the July fib33 experiments. The Feb cost bundles (`cost/2026-02-21_*`) are for a different controller version and should not be mixed. Cost analysis in Ch4 should note this gap or use the Feb directional estimates with explicit caveats.

---

## Honest Framing Rules for Thesis

1. **Never say** "proven", "hypothesis proven", "demonstrated superiority" for H1/H2.
2. **Use** "mechanism validated" for what works (weight shifting, PREDICTIVE trigger, GRU inference).
3. **Use** "large effect size (d=1.21) but not statistically significant (p=0.12, n=5)" for H2 SLO reduction.
4. **Use** "localhost routing bias limits interpretation" for H1 negative result.
5. **Use** "mechanism validated on synthetic data; real-trace accuracy below target thresholds" for H3 partial validation.
