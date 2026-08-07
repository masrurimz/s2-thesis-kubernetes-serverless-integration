## 4.3 Comparative Evaluation

The final comparison uses two evidence tiers. The four-scenario diagnostic bundle `2026-07-11_scaling_fix_n1` provides directional mechanism and H1 evidence at n=1. The definitive H2 bundle `2026-07-14_clarknet-tuned-paired-n5` provides a counterbalanced paired comparison of S3 and S4 at n=5 (10 runs total).

### 4.3.1 Four-Scenario Diagnostic (n=1)

This diagnostic exercised S1 (K8s+HPA), S2 (Knative-only), S3 (hybrid-reactive), and S4 (hybrid-predictive) on the corrected multi-node testbed. It is descriptive and directional, not an inferential comparison.

| Scenario | p99 (ms) | SLO violations | SLO rate | Serverless time | Projected monthly cost |
|---|---:|---:|---:|---:|---:|
| S1 (K8s+HPA) | 2,421.3 | 6,717 | 7.66% | 0.0% | USD 132 |
| S2 (Knative-only) | 77.7 | 19 | 0.02% | 100.0% | USD 394 |
| S3 (hybrid-reactive) | 98.8 | 3 | 0.00% | 31.8% | USD 147 |
| S4 (hybrid-predictive) | 118.2 | 104 | 0.12% | 24.7% | USD 142 |

For H1, S4 is 95.1% lower in p99 than S1 (118.2 versus 2,421.3 ms), and has 98.5% fewer SLO violations. Because this is n=1, the result is reported as directional mechanism evidence rather than statistical superiority.

### 4.3.2 Definitive Paired H2 Comparison (n=5)

The definitive bundle uses five counterbalanced S3/S4 pairs under the ClarkNet variable-load replay. Both scenarios use the same multi-node testbed, utilization-based node consolidation, and workload configuration. S4 uses the final GRU horizon of 9 control steps (9 × 15 seconds = 135 seconds); its forecasts are used for proactive scaling, while routing remains capacity- and observed-load-driven.

**Table 4.8: Definitive paired results**

| Metric | S3 (Reactive) | S4 (Predictive) | Difference / statistic |
|---|---:|---:|---|
| Mean p99 | 188.5 ms | 126.0 ms | −62.5 ms (−33.1%); p=0.030, d=−1.26 |
| 95% paired CI | — | — | [−100.9, −26.2] ms |
| Mean SLO violations | 656 | 130 | −526 (−80.2%); descriptive secondary |
| Mean p95 | 95.8 ms | 81.9 ms | −13.9 ms (−14.5%); corrected p=0.1216 |
| Projected monthly cost | USD 163 | USD 163 | Identical; projected, not billed |

The pre-specified primary p99 permutation test is significant at p=0.030 (the unrounded value is 0.0304), with a large paired effect (d=−1.26) and a confidence interval entirely below zero. S4 won all five paired p99 comparisons. SLO and p95 differences are reported descriptively because their multiplicity-corrected p-value is 0.1216; they are not separate confirmatory claims.

All five S4 runs passed validity gates, delivered complete forecasts (280/280 predictions), and recorded predictive activity. The h=9 horizon covers the measured provisioning-delay regime, while the ClarkNet ramps and surges provide conditions in which proactive scaling can act.

### 4.3.3 Superseded Data (Historical Audit Trail)

The February Phase B dataset (20 runs, nominally 100 RPS, with earlier H1/H2 statistics such as p=0.173 and p=0.865) is **superseded and is not evidence for the final thesis claims**. Bugs 1–7 documented in `results/claims/INCONSISTENCIES.md` affected the SLO monitor, action priority, Prometheus collection, HAProxy server identity, daemon freshness, metric naming, and invariant checks. Those bundles remain immutable for auditability, but their numbers must not be mixed with the corrected July results.

The earlier July paired bundle `2026-07-12_paired-h2-clean-v2` is also superseded by the definitive tuned bundle: it used the h=5 model, no node consolidation, and an untuned reactive controller. The definitive evidence source for H2 is `results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5`.

### 4.3.4 Interpretation

The diagnostic establishes the corrected testbed's directional H1 contrast and the paired study establishes H2 for the pre-specified primary p99 metric. Together they show that prediction is useful when assigned to the scaling actuator: S4 improves tail latency over S3 without a projected cost difference. The results do not claim that every secondary metric is statistically significant or that proxy costs are billed cloud expenditure.

### 4.3.5 Independent Replication (2026-08-07)

An independent, configuration-matched re-run (`2026-08-07_paired-h2_060200`, same ClarkNet trace, seed 42, `max_k8s_replicas=10` override, h=9) confirmed the *direction* of H2: S4 won 4 of 5 pairs (S3 131.7 ms vs S4 109.9 ms, Δ −21.8 ms; SLO violations 172 vs 101, −41%), with d=−0.71 and one-sided permutation p=0.0958 (not significant). The effect was smaller than July's because the reactive baseline was faster in the replication (131.7 vs 188.5 ms). The replication is evidence of repeatability and directional stability, not a replacement for the definitive July statistics. A default-configuration re-run (cap 6) produced a qualitatively different comparison and is documented as a config-drift diagnostic in `thesis/DRIFT_ANALYSIS.md` §6b.

*Evidence: `results/claims/FINAL_NUMBERS.md`; `results/claims/CLAIMS_TO_EVIDENCE.md`; bundles `2026-07-11_scaling_fix_n1`, `2026-07-14_clarknet-tuned-paired-n5`, `2026-08-07_paired-h2_060200` (plus `2026-08-06_paired-h2_034648` n=3 and `2026-08-06_paired-h2_234256` config diagnostic).*
