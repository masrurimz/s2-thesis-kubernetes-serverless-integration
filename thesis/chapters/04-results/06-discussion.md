## 4.6 Discussion

This section synthesizes the final evidence across the diagnostic and definitive bundles. The corrected architecture assigns GRU prediction to replica scaling (Algorithm 2), while V3 routing responds to observed load, ready capacity, and tail latency.

### 4.6.1 Synthesis of Findings

The n=1 four-scenario diagnostic (`2026-07-11_scaling_fix_n1`) establishes directional mechanism evidence. S4 p99 was 118.2 ms versus 2,421.3 ms for S1 (−95.1%), while S3 was 98.8 ms. These values should not be treated as inferential H1 evidence because the diagnostic has one run per scenario.

The definitive ClarkNet paired bundle (`2026-07-14_clarknet-tuned-paired-n5`) establishes H2 for its pre-specified primary p99 metric. Across five counterbalanced pairs, S3 mean p99 was 188.5 ms and S4 mean p99 was 126.0 ms (difference −62.5 ms; 95% CI [−100.9, −26.2]; p=0.030; paired d=−1.26). S4 won all five pairs. Thus the earlier statement that statistical superiority could not be established is superseded: **H2 is established for the primary p99 comparison**.

Mean SLO violations also favored S4 (656 versus 130, −80.2%), but p95 and SLO are secondary metrics. Their multiplicity-corrected p-value is 0.1216, so these effects are reported descriptively rather than as additional confirmatory claims. S3 and S4 have identical projected monthly cost, USD 163.

The GRU result remains mixed by data source: synthetic RMSE is 4.75% after HPO (6.01% pre-HPO), whereas ClarkNet RMSE is 17.78%. The mechanism is usable under confidence gating, but real-trace accuracy does not meet the original threshold.

### 4.6.2 Interpretation of the Architectural Separation

Prediction and routing have different operational time constants. Algorithm 2 can use a 135-second forecast (9 × 15 seconds) to prepare replicas for node and pod provisioning delay. Algorithm 1 must react to observed capacity and tail latency on the 15-second loop; prediction does not directly set HAProxy weights. Observed-load trend extrapolation may gate proactive routing, but the GRU forecast is assigned to scaling. This separation prevents forecast error from directly over-routing traffic to the serverless backend while preserving lead time where it is useful.

### 4.6.3 Testbed and Evidence Limitations

The testbed is a bounded multi-node k3d cluster: two static workload nodes plus dynamically provisioned workload nodes, with Docker `--cpus` limits. This is a stress harness for exercising pending pods, node provisioning, serverless offload, and consolidation; it is not a managed-cloud deployment. The historical single-node localhost-loopback bias remains relevant to the superseded S2-era evidence, but it is not the topology used for the final July diagnostic and paired bundle.

Node-provisioning delay is emulated rather than obtained from cloud VM boot. The 135-second horizon was selected to cover the measured delay range plus a safety margin; this does not eliminate differences in cloud APIs, image pulls, networking, quotas, or availability-zone placement. Costs remain projected AWS proxy values, not billed costs.

The paired H2 result is valid for the specified ClarkNet replay, h=9 model, consolidation policy, and tuned S3 controller. Broader workload classes and a production deployment require further evaluation. The n=1 H1 evidence is explicitly directional.

### 4.6.4 Defensible Contributions

1. A GRU-based workload predictor whose synthetic accuracy meets the target and whose real-trace limitation is disclosed.
2. A V3 capacity-driven routing controller with the priority order **SCALE_OUT > PREDICTIVE > OPTIMIZE_COST > MAINTAIN**, with no separate SCALE_IN action.
3. An implemented Algorithm 2 that uses $R=\alpha x+\beta$ and assigns prediction to proactive Kubernetes scaling rather than routing weights.
4. A counterbalanced paired evaluation showing H2 primary p99 superiority (p=0.030, d=−1.26) at identical projected S3/S4 cost, while reporting corrected secondary metrics descriptively.

### 4.6.5 Comparison with the ElaX Framework

ElaX's two-layer structure is retained: Algorithm 1 governs routing and Algorithm 2 governs cluster capacity. The delivered system extends it with heterogeneous Kubernetes-serverless backends, SLO-aware capacity-driven routing, GRU-assisted replica scaling, confidence gating, cooldowns, and utilization-based consolidation. The final experiment isolates the predictive scaling signal from the routing actuator, making the H2 comparison interpretable.

### 4.6.6 Defensible Position

The final evidence supports the following framing: the hybrid system mechanisms are implemented and validated; H1 is directional at n=1; and H2 is supported for the pre-specified primary p99 metric in the definitive paired n=5 experiment. Secondary p95 and SLO effects are favorable but not statistically significant after correction (p=0.1216). The result is strong mechanism and primary-performance evidence under a controlled multi-node stress harness, not a claim of universal cloud performance or billed-cost savings.

---

*Evidence: `results/claims/FINAL_NUMBERS.md`, `results/claims/CLAIMS_TO_EVIDENCE.md`, `results/experiments/phase-b/2026-07-11_scaling_fix_n1`, and `results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5`.*
