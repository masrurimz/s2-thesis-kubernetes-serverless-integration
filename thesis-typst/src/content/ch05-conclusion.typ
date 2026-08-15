= CONCLUSION AND SUGGESTIONS

This research designed, implemented, and evaluated a hybrid Kubernetes-serverless architecture with GRU-based workload prediction for Kubernetes replica scaling and observed-load traffic routing. The system addresses elastic scalability management in heterogeneous cloud environments through SLO-aware decision making. Three research questions were posed; each is answered below with direct reference to experimental evidence. The definitive paired S3/S4 comparison uses n = 5 counterbalanced pairs with variable ClarkNet load, utilization-based node consolidation, and a tuned reactive baseline (`2026-07-14_clarknet-tuned-paired-n5`). Earlier bundles are retained as historical records.

== Conclusion

=== RQ1: GRU-Based Workload Prediction

A GRU (Gated Recurrent Unit) neural network was designed and optimized through hyperparameter optimization (HPO) using Optuna TPE. The optimal configuration uses one recurrent layer with 128 hidden units, learning rate 0.000380, sequence length 30, and dropout 0.104. Post-HPO accuracy improved from 6.01% to 4.75% RMSE.

The GRU predictor achieves target accuracy on synthetic workload patterns: RMSE 4.75% post-HPO (manual baseline 6.01%, target under 10%) with confidence scores 0.72-0.82 during live predictions. Validation against the ClarkNet HTTP trace yielded RMSE 17.78% at 5-minute aggregation. This is meaningful generalization, though below original thresholds. The gap comes from non-stationarity and irregular burst patterns that do not appear in synthetic training data.

=== RQ2: Modified ElaX Decision Making

The research extends the ElaX framework @yang2019elax with two algorithms for heterogeneous cloud environments. Algorithm 1 (Routing Controller) monitors tail latency (p99) against configurable thresholds. It makes four types of decisions in priority order: SCALE_OUT for active SLO violations, PREDICTIVE for anticipated surges, OPTIMIZE_COST for stable periods, and MAINTAIN as default. Weight-based routing via HAProxy implements traffic distribution. It adjusts the Kubernetes-to-serverless split from 100/0 to 50/50.

Algorithm 2 (Cluster Controller) uses a horizontal scaling formula R = alpha dot.op x + beta. It integrates this formula into the routing daemon for real-time Kubernetes replica scaling. It operates in reactive mode (S3, using observed load) or predictive mode (S4, using GRU forecast).

Phase A1 validated the predictive pre-warming mechanism. PREDICTIVE triggered at p99 = 146 ms (healthy state) when the observed-load trend indicated a predicted 47% workload surge and GRU confidence was 72%. It pre-positioned serverless capacity before an SLO violation occurred. In the definitive controller, the forecast also informs Algorithm 2 replica planning. Routing remains observed-load driven.

=== RQ3: Evaluation of the Modified ElaX Mechanism

A comprehensive evaluation framework spans mechanism validation (Phase A1), comparative evaluation (Phase B), and dynamic burst validation (Phase C). The evaluation compares four scenarios: S1 (K8s+HPA), S2 (Serverless-only), S3 (Hybrid-reactive), and S4 (Hybrid-predictive). The Phase B baseline is an *n = 1 diagnostic* run per scenario (`2026-07-11_scaling_fix_n1`). The definitive n = 5 paired experiment (`2026-07-14_clarknet-tuned-paired-n5`) confirms H2.

H1 (hybrid architecture outperforms the pure Kubernetes baseline): *Directional at n = 1.* Under the correctly bounded infrastructure (Docker `--cpus=1.0` per node, `max_k8s_replicas = 6`), the hybrid predictive scenario S4 reduced p99 latency by 95.1% (118.2 ms vs 2,421.3 ms for S1) and SLO violations by 98.5% (104 vs 6,717). The earlier negative finding was an artifact of un-enforced CPU limits and S1 dynamic-node over-provisioning (Bugs 8 and 11). n = 5 replication is required to establish statistical significance.

H2 (predictive scaling outperforms reactive): *Statistically supported (p = 0.030, d = -1.26, large effect).* The definitive paired experiment (n = 5 counterbalanced pairs, `2026-07-14_clarknet-tuned-paired-n5`) finds S4 mean p99 126.0 ms versus 188.5 ms for S3 (mean difference -62.5 ms, 95% CI [-100.9, -26.2], p = 0.030, Cohen's d = -1.26). S4 wins all 5 pairs and shows 80.2% fewer SLO violations (130 vs 656) at identical monthly cost (USD 163). The GRU forecast triggered 4--5 predictive decisions per S4 run. This result reverses the earlier non-significant finding (p = 0.38, d = -0.241). It includes three necessary conditions: an extended 9-step forecast horizon (135 s), utilization-based node consolidation matching Kubernetes Cluster Autoscaler semantics, and a tuned reactive baseline.

H3 (GRU prediction adequacy): Validated on synthetic data at 4.75% RMSE post-HPO with confidence 0.72-0.82. Partial on real traces: ClarkNet RMSE 17.78% falls below original thresholds due to workload non-stationarity.

The n = 1 diagnostic cost projection (S1 = USD 132/mo, S2 = USD 394/mo, S3 = USD 147/mo, S4 = USD 142/mo) is a *directional estimate only* and must not be used to rank S3 and S4 or claim monthly savings. S1 is cheapest but fails the SLO (p99 = 2,421 ms); S2 is fastest but most expensive; the hybrid scenarios occupy a middle band.

In summary, this research validates the hybrid mechanism. It provides statistically significant evidence for the predictive advantage. The GRU predictor achieves target accuracy on synthetic data. The routing controller correctly shifts traffic based on observed load and SLO status. Hybrid routing reduces p99 latency by 95.1% over pure Kubernetes (H1, directionally supported at n = 1). The definitive paired comparison (n = 5) finds S4 33.1% faster than S3 on p99 (126.0 ms vs 188.5 ms, p = 0.030, d = -1.26, large effect) with 80.2% fewer SLO violations at identical cost (H2, supported). The three-tier autoscaling architecture (routing, pod scaling, and utilization-based node consolidation) is shown under realistic variable load. These findings confirm that the hybrid predictive architecture can improve tail-latency compliance when forecast information drives replica scaling.

A separate high-load diagnostic (`2026-07-13_dynamic-node-offload`, n = 1) shows the full three-tier architecture: traffic routing (HAProxy weight shifting), pod scaling (Algorithm 2 / HPA), and node autoscaling (K3dAutoscaler dynamic node provisioning). Under 200 RPS constant load with a ten-replica cap, all Kubernetes scenarios provisioned two dynamic workload nodes via Pending-pod detection. The hybrid scenarios (S3, S4) maintained 96.5% serverless offload time while they provisioned nodes. They achieved p99 latency of 874 ms (S3) and 1,393 ms (S4). Pure Kubernetes (S1) had the same two dynamic nodes but no serverless offload. It achieved only 6,665 ms p99 and a 65.6% success rate. Dynamic node provisioning alone is not a substitute for serverless offload. The two mechanisms are complementary. This is a mechanism diagnostic, not an inferential experiment. Node-versus-serverless economics require the measured cost proxy and a larger replication study.

Under variable ClarkNet load with utilization-based node consolidation (`2026-07-14_clarknet-util-scaledown-n1`, n = 1), the predictive controller showed its strongest advantage. S4 achieved 50.5% lower p99 (113 ms vs 228 ms) and 96.3% fewer SLO violations (40 vs 1,085) than S3, at a 5% cost premium. The K3dAutoscaler's consolidation logic matched the Kubernetes Cluster Autoscaler's 50% utilization threshold and reschedulability check. It provisioned nodes on ClarkNet peaks and consolidated underutilized nodes on valleys. S3's aggressive consolidation deleted all dynamic nodes when utilization dropped. This caused latency spikes on the next peak. S4's forecast maintained capacity and prevented excessive consolidation.

== Future Work

Based on the limitations identified during evaluation, six directions are recommended:

Multi-node cloud deployment: Although the corrected n = 1 baseline directionally supports hybrid superiority, the CPU-bounded multi-node k3d testbed still lacks production network latency and contention. Deployment on a multi-node cloud cluster (3+ nodes on AWS EKS or GCP GKE with Knative on separate nodes) would validate the results under production network conditions. It is the appropriate setting for the n = 5 confirmatory replication.

Adaptive forecast horizon: The 9-step GRU horizon deployed in the definitive experiment covers provisioning delays up to 120 s. This was enough for the ClarkNet workload. Future work should make the horizon fully adaptive. It should follow the self-calibrating approach of ADAPT @adapt2026. It should increase the required forecast steps based on a live EWMA of measured provisioning delays. The horizon would then track real cluster conditions instead of a fixed step count.

Dynamic workload experiments with extended ramp periods: PREDICTIVE requires a healthy observation window longer than the ramp duration to build trend predictions. Future experiments should use workload patterns with gradual ramps (90+ seconds) and longer baseline periods.

GRU retraining on production HTTP traces: Real-trace performance (17.78% RMSE) falls short of thresholds due to non-stationarity. Future work could retrain on production traces with time-of-day encoding, day-of-week seasonality, and online learning. This would improve applicability.

Knative minScale configuration: Setting minScale=1 would maintain a warm serverless instance. This would remove cold start latency and isolate the routing mechanism's contribution to performance.

Extended statistical validation: H2 rests on the definitive n = 5 paired experiment with full treatment delivery. H1 remains a single n = 1 diagnostic. Future work should run n = 20+ replications to satisfy normality assumptions. It should also provide confirmatory replication of the H2 primary result (p = 0.030) and an inferential test of H1, which is currently directionally supported at n = 1.
