= CONCLUSION AND SUGGESTIONS

This research designed, implemented, and evaluated a hybrid Kubernetes-serverless architecture with GRU-based workload prediction for intelligent traffic routing. The system addresses elastic scalability management in heterogeneous cloud environments through SLO-aware decision making. Three research questions were posed; each is answered below with direct reference to experimental evidence. _Caveat:_ the performance results cited in this chapter are drawn from the `2026-07-11_scaling_fix_n1` baseline, an *n = 1 diagnostic* run on infrastructure corrected for six prior bugs (Bugs 8-13). All earlier experiment bundles are superseded. n = 5 replication is required before any hypothesis verdict can be reported as statistically significant; the verdicts below are therefore diagnostic, not confirmatory.

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

H1 (hybrid architecture outperforms pure approaches): *Confirmed at n = 1.* Under the correctly bounded infrastructure (Docker `--cpus=1.0` per node, `max_k8s_replicas = 6`), the hybrid predictive scenario S4 reduced p99 latency by 95.1% (118.2 ms vs 2,421.3 ms for S1) and SLO violations by 98.5% (104 vs 6,717). The earlier negative finding was an artifact of un-enforced CPU limits and S1 dynamic-node over-provisioning (Bugs 8 and 11), not a property of the hybrid mechanism. n = 5 replication is required to establish statistical significance.

H2 (predictive scaling outperforms reactive): *Partially confirmed at n = 1* — cost efficiency demonstrated, latency superiority requires further validation. S4 does not provide a latency advantage over S3 (p99 118.2 ms vs 98.8 ms, +19.7%; both keep the SLO violation rate near zero), but it provides a cost advantage: 50.2% fewer serverless requests (2,666 vs 5,354) and $5/month lower cost ($142 vs $147). The cost advantage arises because, under the corrected architecture, prediction drives Kubernetes *scaling* rather than serverless *routing* (Bug 13 fix), so S4 provisions warm capacity earlier and spills less to Knative.

H3 (GRU prediction adequacy): Validated on synthetic data — 4.75% RMSE post-HPO with confidence 0.72-0.82. Partial on real traces: ClarkNet RMSE 17.78% falls below original thresholds due to workload non-stationarity.

Cost analysis is now grounded in the `2026-07-11_scaling_fix_n1` baseline: S1 = $132/mo (but fails the SLO catastrophically, p99 = 2,421 ms), S2 = $394/mo, S3 = $147/mo, S4 = $142/mo. On a cost-performance Pareto analysis (minimizing monthly cost and p99 latency), S4 is a Pareto-optimal point: no scenario achieves both lower cost *and* lower p99 latency than S4 ($142/mo, 118.2 ms). S1 is cheaper ($132) but its 2,421 ms p99 violates the SLO, so it is not a viable operating point; S2 is faster (77.7 ms) but more than twice as expensive ($394/mo); S3 is close to S4 on both axes, and the two do not dominate each other (S4 is $5 cheaper, S3 is 19 ms faster). Among viable SLO-compliant scenarios, S4 offers the lowest cost while halving serverless dependency, making it the recommended cost-performance operating point. These are n = 1 diagnostic estimates and require replication.

In summary, this research validates the proposed mechanisms and demonstrates their benefit under corrected infrastructure. The GRU predictor achieves target accuracy on synthetic data, the routing controller correctly shifts traffic based on SLO status, and hybrid predictive routing (S4) reduces p99 latency by 95.1% over pure Kubernetes (H1, confirmed at n = 1) while halving serverless dependency for a lower monthly cost than the reactive hybrid (H2, cost advantage confirmed at n = 1). The predictive mechanism now drives Kubernetes scaling rather than serverless routing. These findings are provisional: they rest on a single *n = 1 diagnostic* run, and n = 5 replication is needed to establish statistical significance.

== Future Work

Based on the limitations identified during evaluation, six directions are recommended:

Multi-node cloud deployment: Although the corrected n = 1 baseline already shows hybrid superiority, the single-node k3d testbed still lacks realistic inter-node network latency. Deploying on a multi-node cloud cluster (3+ nodes on AWS EKS or GCP GKE with Knative on separate nodes) would validate the results under production network conditions and is the appropriate setting for the n = 5 confirmatory replication.

Algorithm 2 full integration: The horizontal scaling formula should be fully integrated with Kubernetes HPA coordination, enabling proactive replica scaling based on GRU predictions.

Dynamic workload experiments with extended ramp periods: PREDICTIVE requires a healthy observation window longer than the ramp duration to build trend predictions. Future experiments should use workload patterns with gradual ramps (90+ seconds) and longer baseline periods.

GRU retraining on production HTTP traces: Real-trace performance (17.78% RMSE) falls short of thresholds due to non-stationarity. Retraining on production traces with time-of-day encoding, day-of-week seasonality, and online learning would improve applicability.

Knative minScale configuration: Setting minScale=1 would maintain a warm serverless instance, eliminating cold start latency and isolating the routing mechanism's contribution to performance.

Extended statistical validation: The current results rest on a single n = 1 diagnostic run per scenario. Future work should run n = 5 (minimum) to n = 30+ replications per scenario to satisfy normality assumptions and achieve adequate power, providing definitive statistical evidence for the H1 and H2 verdicts that are currently only directionally supported.
