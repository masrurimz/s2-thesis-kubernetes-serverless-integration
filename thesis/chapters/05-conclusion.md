# BAB 5: KESIMPULAN DAN SARAN

## 5.1 Kesimpulan (Conclusion)

This research designed, implemented, and evaluated a hybrid Kubernetes-serverless architecture with GRU-based workload prediction. The final controller separates the two time scales of control: Algorithm 1 routes using observed capacity and tail-latency state, while Algorithm 2 uses the GRU forecast to scale Kubernetes replicas proactively. The evidence below follows the final bundles in `results/claims/FINAL_NUMBERS.md`.

### RQ1: How to design workload traffic prediction for an application using GRU?

A GRU predictor was implemented with a direct multi-horizon output. It uses a 9-step forecast at the 15-second control-loop resolution, giving a 135-second horizon. Synthetic evaluation achieved RMSE 4.75% after HPO (6.01% before HPO), while real ClarkNet evaluation achieved RMSE 17.78%. Thus the synthetic target was met, but real-trace accuracy remains below the original target because of non-stationarity and irregular bursts. The predictor is therefore validated for the scaling mechanism, with its real-data accuracy limitation explicitly retained.

### RQ2: How to design decision making by modifying ElaX for scaling and traffic distribution?

The delivered system extends ElaX through two coordinated algorithms:

1. **Algorithm 1 — V3 routing controller:** routes between Kubernetes and Knative using observed load, ready capacity, and tail-latency state. It uses the priority order **SCALE_OUT > PREDICTIVE > OPTIMIZE_COST > MAINTAIN**. There is no separate SCALE_IN action; cost optimization and consolidation are handled through the lower-priority optimization path.
2. **Algorithm 2 — cluster controller:** applies the resource model $R = \alpha x + \beta$ to Kubernetes replica scaling. S3 uses observed load ($x_{obs}$), while S4 uses the confidence-gated GRU forecast ($x_{pred}$). Prediction does not directly increase HAProxy routing weights; it supplies lead time to the scaling actuator. Routing can still respond to observed-load trend extrapolation and measured capacity.

This separation is a deliberate final design correction: prediction-for-routing was invalidated because it could over-route during forecast error, whereas node and replica provisioning require a forecast horizon long enough to cover their delay.

### RQ3: How to evaluate the modified ElaX mechanism?

The final evidence has two tiers:

- **Four-scenario diagnostic (`2026-07-11_scaling_fix_n1`, n=1):** S1/S2/S3/S4 p99 values were 2,421.3/77.7/98.8/118.2 ms, with projected monthly costs of USD 132/394/147/142. This is directional mechanism evidence. H1 is directional: S4 is 95.1% lower in p99 than S1.
- **Definitive paired H2 (`2026-07-14_clarknet-tuned-paired-n5`, n=5 pairs):** five counterbalanced S3/S4 pairs (10 runs) used ClarkNet variable load, h=9 (135 s), active consolidation, and a tuned reactive baseline.

**H2 — Predictive scaling outperforms reactive scaling:** **NOT SUPPORTED.** The July batch (`2026-07-14_clarknet-tuned-paired-n5`, n=5 pairs) showed S3 mean p99 188.5 ms versus S4 126.0 ms (−62.5 ms, 95% CI [−100.9, −26.2], p=0.0312, d=−1.26, the 1/32 design floor), but its manifest records no predictor block, and the artifact deployed on 2026-09-12 (commit 98e17d1) was later shown to be the synthetic-trained model — so that batch is not ClarkNet-attributable. Across the three ClarkNet-attributable batches, no batch clears the pre-specified primary p99 test: `2026-09-13_h2-pair-5p` +153.3 ms (p=0.656), `2026-09-13_h2-confirmatory-10p` −104.2 ms (p=0.168), and the pre-registered quiet-host replication `2026-09-20_h2-confirmatory-10p` (10 pairs, 20/20 runs valid, host load gated) −13.6 ms (95% CI [−63.5, +35.6], p=0.307, d=−0.16), with S4 winning 5 of 10 pairs. Pooling all 25 pairs gives −16.5 ms (95% CI [−194.0, +182.5], p=0.50, d=−0.03). An earlier quiet-host subset estimate (−101.3 ms, p=0.039, eight pairs of the September batch) does not survive the replication; it was an artifact of subset selection. The July batch's SLO and cost numbers remain descriptive history: SLO violations 656 to 130 (−80.2%), identical projected monthly cost USD 163.

**H1 — Hybrid versus pure Kubernetes:** **Directional at n=1**, not inferentially established. The diagnostic S4/S1 p99 contrast is large, but a confirmatory paired replication remains future work.

**H3 — GRU adequacy:** validated on synthetic data and partially validated on real traces. The synthetic RMSE is 4.75% post-HPO (6.01% pre-HPO); ClarkNet RMSE is 17.78%. Under the current leak-free fold protocol (2026-09-13, `results/models/gru/2026-09-13_probes-representation/`), a twelve-lever representation search found no variant that beats the linear autoregression on the selection folds; the disclosed conclusion is that the deployed point predictor should be the linear autoregression, and the network's parity is a limitation, not a hidden fact. A capacity-relative crossing head (`results/models/gru/2026-09-13_probe-t-cross/`) detects crossings the point forecast misses, with crossing recall 0.988 against 0.008 to 0.042 for the linear model plus threshold, but it is overconfident (per-step Brier 0.233 against 0.049) and its decision rule is recall at a bounded false-alarm rate, with calibration work pending.

In summary, the work contributes a functioning hybrid control system, a corrected separation between prediction-for-scaling and observed-load routing, and a replicated, validity-gated evaluation whose final verdict is that the predictive advantage is not statistically detectable on the pre-specified test. The July batch that showed significance used an unverifiable, later-identified synthetic predictor. Secondary p95 and SLO results are large and favorable but descriptive after multiplicity correction. The AWS values are projected proxy costs, not billed expenditure.

---

## 5.2 Saran (Future Work)

1. **Production multi-node node autoscaling.** Algorithm 2 is implemented and exercised on the bounded multi-node k3d testbed. Future work should extend it to production Kubernetes node autoscaling (for example, EKS/GKE with a managed node provisioner), then evaluate cloud-specific provisioning, networking, quotas, and heterogeneous node types.

2. **Confirmatory H1 replication.** Repeat the four-scenario comparison with a paired or otherwise adequately powered design so the directional n=1 H1 contrast can be evaluated inferentially under a production-like multi-node topology.

3. **Longer and more varied workloads.** Evaluate additional ClarkNet windows and modern traces with ramps, bursts, and changing baselines. This will test the 135-second horizon under conditions different from the definitive bundle and quantify when proactive scaling is actionable.

4. **GRU retraining on production traces.** Real ClarkNet RMSE (17.78%) remains above the original target. Retraining with production traces, time-of-day features, and online adaptation may improve generalization while preserving confidence gating.

5. **Cold-start isolation.** Evaluate warm-serverless configurations (for example, Knative `minScale=1`) and separate cold-start overhead from routing and scaling effects. The historical cold-start analysis is retained with its invalidated-data banner and is not used as current comparative evidence.

6. **Cost validation.** Replace the unified AWS proxy with billed cloud measurements or a validated cloud-cost trace. Keep the current two-world framing: stress-harness behavior is evidence about mechanisms, while monthly USD values are projections.
