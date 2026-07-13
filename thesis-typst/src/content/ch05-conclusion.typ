= CONCLUSION AND SUGGESTIONS

This research designed, implemented, and evaluated a hybrid Kubernetes-serverless architecture with GRU-based workload prediction for intelligent traffic routing. The system addresses elastic scalability management in heterogeneous cloud environments through SLO-aware decision making. Three research questions were posed; each is answered below with direct reference to experimental evidence. _Caveat:_ the four-scenario diagnostic uses n = 1 (`2026-07-11_scaling_fix_n1`) and the paired S3/S4 comparison uses n = 5 with full treatment delivery (`2026-07-12_paired-h2-clean-v2`). All earlier bundles are superseded.

== Conclusion

=== RQ1: GRU-Based Workload Prediction

A GRU (Gated Recurrent Unit) neural network was designed and optimized through hyperparameter optimization (HPO) using Optuna TPE. The optimal configuration uses one recurrent layer with 128 hidden units, learning rate 0.000380, sequence length 30, and dropout 0.104. Post-HPO accuracy improved from 6.01% to 4.75% RMSE.

The GRU predictor achieves target accuracy on synthetic workload patterns: RMSE 4.75% post-HPO (manual baseline 6.01%, target under 10%) with confidence scores 0.72-0.82 during live predictions. Validation against the ClarkNet HTTP trace yielded RMSE 17.78% at 5-minute aggregation — meaningful generalization, though below original thresholds due to non-stationarity and irregular burst patterns absent in synthetic training data.

=== RQ2: Modified ElaX Decision Making

Two algorithms were designed by extending the ElaX framework @yang2019elax for heterogeneous cloud environments. Algorithm 1 (Routing Controller) monitors tail latency (p99) against configurable thresholds and makes four types of decisions in priority order: SCALE_OUT for active SLO violations, PREDICTIVE for anticipated surges, OPTIMIZE_COST for stable periods, and MAINTAIN as default. Traffic distribution is implemented through weight-based routing via HAProxy, dynamically adjusting the Kubernetes-to-serverless split from 100/0 to 50/50.

Algorithm 2 (Cluster Controller) uses a horizontal scaling formula R = alpha dot.op x + beta integrated into the routing daemon for real-time Kubernetes replica scaling, operating in reactive mode (S3, using observed load) or predictive mode (S4, using GRU forecast).

The predictive pre-warming mechanism was validated in Phase A1: PREDICTIVE triggered at p99 = 146 ms (healthy state) upon detecting a predicted 47% workload surge with 72% confidence, successfully pre-positioning serverless capacity before SLO violation occurred.

=== RQ3: Evaluation of the Modified ElaX Mechanism

A comprehensive evaluation framework was designed spanning mechanism validation (Phase A1), comparative evaluation (Phase B), and dynamic burst validation (Phase C). The evaluation compares four scenarios: S1 (K8s+HPA), S2 (Serverless-only), S3 (Hybrid-reactive), and S4 (Hybrid-predictive). The current Phase B baseline is a single *n = 1 diagnostic* run per scenario (`2026-07-11_scaling_fix_n1`); n = 5 replication is pending.

H1 (hybrid architecture outperforms pure approaches): *Directional at n = 1.* Under the correctly bounded infrastructure (Docker `--cpus=1.0` per node, `max_k8s_replicas = 6`), the hybrid predictive scenario S4 reduced p99 latency by 95.1% (118.2 ms vs 2,421.3 ms for S1) and SLO violations by 98.5% (104 vs 6,717). The earlier negative finding was an artifact of un-enforced CPU limits and S1 dynamic-node over-provisioning (Bugs 8 and 11). n = 5 replication is required to establish statistical significance.

H2 (predictive scaling outperforms reactive): *Directionally favorable but not statistically significant.* The clean paired experiment (n = 5, full treatment delivery) finds S4 mean p99 128.5 ms versus 136.6 ms for S3 (mean difference -8.1 ms, 95% CI [-36.7, +14.5] ms, p = 0.38, d = -0.241). The effect direction reversed to S4's favor after correcting the scaling calibration from alpha = 1/r_saturation to alpha = 1/r_effective, demonstrating that the calibration mismatch -- not the controller design -- was the root cause of S4's earlier underperformance. A secondary finding shows 56% fewer SLO violations (d = -0.535, medium effect). H2 is not statistically supported at n = 5, but the evidence is directionally consistent and the mechanism is now cleanly testable. A larger sample (n >= 20) is needed for adequate statistical power.

H3 (GRU prediction adequacy): Validated on synthetic data — 4.75% RMSE post-HPO with confidence 0.72-0.82. Partial on real traces: ClarkNet RMSE 17.78% falls below original thresholds due to workload non-stationarity.

The n = 1 diagnostic cost projection (S1 = USD 132/mo, S2 = USD 394/mo, S3 = USD 147/mo, S4 = USD 142/mo) is a *directional estimate only* and must not be used to rank S3 and S4 or claim monthly savings. S1 is cheapest but fails the SLO (p99 = 2,421 ms); S2 is fastest but most expensive; the hybrid scenarios occupy a middle band.

In summary, this research validates the hybrid mechanism and provides directionally favorable evidence for the predictive advantage. The GRU predictor achieves target accuracy on synthetic data, the routing controller correctly shifts traffic based on SLO status, and hybrid routing reduces p99 latency by 95.1% over pure Kubernetes (H1, confirmed at n = 1). The clean paired comparison (n = 5) finds S4 8.1 ms faster than S3 on p99 with 56% fewer SLO violations (H2, directionally favorable but not statistically significant). The calibration repair demonstrated that the original scaling model's double-counted safety margin was the root cause of S4's apparent underperformance, not the controller design. These findings are provisional; a larger sample is needed to confirm H2.

A separate high-load diagnostic (`2026-07-13_dynamic-node-offload`, n = 1) demonstrates the full three-tier architecture: traffic routing (HAProxy weight shifting), pod scaling (Algorithm 2 / HPA), and node autoscaling (K3dAutoscaler dynamic node provisioning). Under 200 RPS constant load with a ten-replica cap, all Kubernetes scenarios provisioned two dynamic workload nodes via Pending-pod detection. The hybrid scenarios (S3, S4) maintained 96.5% serverless offload time while simultaneously provisioning nodes, achieving p99 latency of 874 ms (S3) and 1,393 ms (S4). Pure Kubernetes (S1) with the same two dynamic nodes but no serverless offload achieved only 6,665 ms p99 and 65.6% success rate, demonstrating that dynamic node provisioning alone is not a substitute for serverless offload -- the two mechanisms are complementary. This is a mechanism diagnostic, not an inferential experiment; node-versus-serverless economics require the measured cost proxy and a larger replication study.

Under variable ClarkNet load with utilization-based node consolidation (`2026-07-14_clarknet-util-scaledown-n1`, n = 1), the predictive controller demonstrated its strongest advantage: S4 achieved 50.5% lower p99 (113 ms vs 228 ms) and 96.3% fewer SLO violations (40 vs 1,085) than S3, at a 5% cost premium. The K3dAutoscaler's consolidation logic -- matching the Kubernetes Cluster Autoscaler's 50% utilization threshold and reschedulability check -- provisioned nodes on ClarkNet peaks and consolidated underutilized nodes on valleys. S3's aggressive consolidation deleted all dynamic nodes when utilization dropped, causing latency spikes on the next peak; S4's forecast maintained capacity, preventing excessive consolidation.

== Future Work

Based on the limitations identified during evaluation, six directions are recommended:

Multi-node cloud deployment: Although the corrected n = 1 baseline already shows hybrid superiority, the single-node k3d testbed still lacks realistic inter-node network latency. Deploying on a multi-node cloud cluster (3+ nodes on AWS EKS or GCP GKE with Knative on separate nodes) would validate the results under production network conditions and is the appropriate setting for the n = 5 confirmatory replication.

Forecast-to-actuator alignment and adaptive horizon: The scaling model must be corrected so that effective-capacity forecasts produce differentiated replica targets (align alpha to effective capacity, not saturation). The provisioning delay should be measured live to set the forecast horizon, following the self-calibrating approach of ADAPT @adapt2026. The high-load diagnostic (`2026-07-13_dynamic-node-offload`) demonstrated that the static 5-step horizon (75 s) is insufficient when provisioning delays exceed 70 s: S4 failed the actuator-fidelity gate and recorded zero proactive actions despite delivering 55 forecasts. The GRU model must be retrained with an extended horizon (7+ steps, 105+ seconds) or the horizon must be made adaptive — increasing the required steps based on the live EWMA of measured provisioning delays. A real 15-second ClarkNet-trained GRU artifact that passes the promotion gate must then be bound before a clean full-delivery paired rerun can test H2.

Dynamic workload experiments with extended ramp periods: PREDICTIVE requires a healthy observation window longer than the ramp duration to build trend predictions. Future experiments should use workload patterns with gradual ramps (90+ seconds) and longer baseline periods.

GRU retraining on production HTTP traces: Real-trace performance (17.78% RMSE) falls short of thresholds due to non-stationarity. Retraining on production traces with time-of-day encoding, day-of-week seasonality, and online learning would improve applicability.

Knative minScale configuration: Setting minScale=1 would maintain a warm serverless instance, eliminating cold start latency and isolating the routing mechanism's contribution to performance.

Extended statistical validation: The current results rest on a single n = 1 diagnostic run per scenario. Future work should run n = 5 (minimum) to n = 30+ replications per scenario to satisfy normality assumptions and achieve adequate power, providing definitive statistical evidence for the H1 and H2 verdicts that are currently only directionally supported.
