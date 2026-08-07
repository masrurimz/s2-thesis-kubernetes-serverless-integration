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

**H2 — Predictive scaling outperforms reactive scaling:** **SUPPORTED** for the pre-specified primary p99 test. S3 mean p99 was 188.5 ms and S4 mean p99 was 126.0 ms, a −62.5 ms difference with 95% CI [−100.9, −26.2], p=0.030, and paired Cohen's d=−1.26. S4 won all five pairs. Mean SLO violations decreased from 656 to 130 (−80.2%), reported descriptively because secondary metrics have corrected p=0.1216. Projected monthly cost was identical at USD 163 for both S3 and S4.

**H1 — Hybrid versus pure Kubernetes:** **Directional at n=1**, not inferentially established. The diagnostic S4/S1 p99 contrast is large, but a confirmatory paired replication remains future work.

**H3 — GRU adequacy:** validated on synthetic data and partially validated on real traces. The synthetic RMSE is 4.75% post-HPO (6.01% pre-HPO); ClarkNet RMSE is 17.78%.

In summary, the work contributes a functioning hybrid control system, a corrected separation between prediction-for-scaling and observed-load routing, and a definitive paired result supporting H2 on the primary p99 metric. Secondary p95 and SLO results are large and favorable but descriptive after multiplicity correction. The AWS values are projected proxy costs, not billed expenditure.

---

## 5.2 Saran (Future Work)

1. **Production multi-node node autoscaling.** Algorithm 2 is implemented and exercised on the bounded multi-node k3d testbed. Future work should extend it to production Kubernetes node autoscaling (for example, EKS/GKE with a managed node provisioner), then evaluate cloud-specific provisioning, networking, quotas, and heterogeneous node types.

2. **Confirmatory H1 replication.** Repeat the four-scenario comparison with a paired or otherwise adequately powered design so the directional n=1 H1 contrast can be evaluated inferentially under a production-like multi-node topology.

3. **Longer and more varied workloads.** Evaluate additional ClarkNet windows and modern traces with ramps, bursts, and changing baselines. This will test the 135-second horizon under conditions different from the definitive bundle and quantify when proactive scaling is actionable.

4. **GRU retraining on production traces.** Real ClarkNet RMSE (17.78%) remains above the original target. Retraining with production traces, time-of-day features, and online adaptation may improve generalization while preserving confidence gating.

5. **Cold-start isolation.** Evaluate warm-serverless configurations (for example, Knative `minScale=1`) and separate cold-start overhead from routing and scaling effects. The historical cold-start analysis is retained with its invalidated-data banner and is not used as current comparative evidence.

6. **Cost validation.** Replace the unified AWS proxy with billed cloud measurements or a validated cloud-cost trace. Keep the current two-world framing: stress-harness behavior is evidence about mechanisms, while monthly USD values are projections.
