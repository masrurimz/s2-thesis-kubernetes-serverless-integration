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

### 4.3.2 Paired H2 Comparison (July Batch, n=5)

The July bundle uses five counterbalanced S3/S4 pairs under the ClarkNet variable-load replay. Both scenarios use the same multi-node testbed, utilization-based node consolidation, and workload configuration. S4 uses the final GRU horizon of 9 control steps (9 × 15 seconds = 135 seconds); its forecasts are used for proactive scaling, while routing remains capacity- and observed-load-driven.

**Table 4.8: Definitive paired results**

| Metric | S3 (Reactive) | S4 (Predictive) | Difference / statistic |
|---|---:|---:|---|
| Mean p99 | 188.5 ms | 126.0 ms | −62.5 ms (−33.1%); p=0.0312, d=−1.26 |
| 95% paired CI | — | — | [−100.9, −26.2] ms |
| Mean SLO violations | 656 | 130 | −526 (−80.2%); descriptive secondary |
| Mean p95 | 95.8 ms | 81.9 ms | −13.9 ms (−14.5%); corrected p=0.1248 |
| Projected monthly cost | USD 163 | USD 163 | Identical; projected, not billed |

The pre-specified primary p99 permutation test in this batch is significant at p=0.0312, with a large paired effect (d=−1.26) and a confidence interval entirely below zero. The value is the design floor: 1/32 is the smallest p attainable with five pairs, because all five pairs fell the same way. The stored bundle artifact records 0.0304 from an older analysis routine; the current `thesis experiment analyze` recomputes 1/32. The verdict, however, changed after a provenance audit. The 2026-07-14 manifest records an empty predictor block, so this batch's weights cannot be verified, and the artifact deployed on 2026-09-12 (commit 98e17d1, LFS oid 7f8244bcc403c59a3e2be5d31b1ee5586f01c0052416c2705c0a325d1cc3099d) was later shown to be the synthetic-trained winner rather than the ClarkNet winner. The batch is therefore reported as historical: its significance is real within the batch, but its result is not attributable to the ClarkNet-trained predictor the thesis deploys. S4 won all five paired p99 comparisons in this batch. SLO and p95 differences are reported descriptively because their multiplicity-corrected p-value is 0.1248; they are not separate confirmatory claims.

All five S4 runs passed validity gates, delivered complete forecasts (280/280 predictions), and recorded predictive activity. The h=9 horizon covers the measured provisioning-delay regime, while the ClarkNet ramps and surges provide conditions in which proactive scaling can act.

### 4.3.3 Superseded Data (Historical Audit Trail)

The February Phase B dataset (20 runs, nominally 100 RPS, with earlier H1/H2 statistics such as p=0.173 and p=0.865) is **superseded and is not evidence for the final thesis claims**. Bugs 1–7 documented in `results/claims/INCONSISTENCIES.md` affected the SLO monitor, action priority, Prometheus collection, HAProxy server identity, daemon freshness, metric naming, and invariant checks. Those bundles remain immutable for auditability, but their numbers must not be mixed with the corrected July results.

The earlier July paired bundle `2026-07-12_paired-h2-clean-v2` is also superseded by the definitive tuned bundle: it used the h=5 model, no node consolidation, and an untuned reactive controller. The definitive evidence source for H2 is `results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5`.

### 4.3.4 Interpretation

The diagnostic establishes the corrected testbed's directional H1 contrast. The paired studies establish that the predictive advantage is not statistically detectable: the only significant batch (July) used an unverifiable predictor later shown to be synthetic-trained, and every ClarkNet-attributable batch is null on the pre-specified test. The results do not claim that every secondary metric is statistically significant or that proxy costs are billed cloud expenditure.

### 4.3.5 Replication History and the Quiet-Host Verdict

Two initial replication batches from 2026-08-07 were deleted from the working tree before commit and are excluded from the evidence record; their numbers survive only as superseded prose. The retained replication record comprises the August batches (RUN1 p=0.436 null, RUN2 p=0.062 marginal) and the September ClarkNet-attributable batches, followed by a pre-registered quiet-host replication:

- `2026-09-13_h2-pair-5p` (ClarkNet winner 20623c19, n=5): +153.3 ms, p=0.656.
- `2026-09-13_h2-confirmatory-10p` (ClarkNet winner, n=10): −104.2 ms, p=0.168; three slow runs coincided with a settling host (peak 66–100% CPU busy), and the host-load series added in this batch shows peak host CPU-busy correlating with p99 at r=0.69.
- `2026-09-20_h2-confirmatory-10p` (pre-registered quiet-host replication, n=10, host load gated under 0.1 of capacity, 20/20 runs valid): S4 146.8 ms versus S3 160.4 ms, −13.6 ms (95% CI [−63.5, +35.6], p=0.307, d=−0.16), S4 winning 5 of 10 pairs.
- Pooled over the 25 ClarkNet-attributable pairs: −16.5 ms (95% CI [−194.0, +182.5], p=0.50, d=−0.03).

An interim quiet-host subset estimate drawn from the September batch (−101.3 ms, p=0.039, the eight pairs under 40% host busy) does not survive the dedicated replication; it was an artifact of subset selection. The final H2 verdict is therefore: **not supported on the pre-specified primary p99 test**, with the hybrid-versus-saturated-Kubernetes result (H1) unaffected.

*Evidence: `results/claims/FINAL_NUMBERS.md`; `results/claims/CLAIMS_TO_EVIDENCE.md`; bundles `2026-07-11_scaling_fix_n1`, `2026-07-14_clarknet-tuned-paired-n5` (historical), `2026-09-13_h2-pair-5p`, `2026-09-13_h2-confirmatory-10p`, `2026-09-20_h2-confirmatory-10p`.*
