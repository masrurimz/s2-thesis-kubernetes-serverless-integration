= CONCLUSION AND SUGGESTIONS

This research designed, implemented, and evaluated a hybrid Kubernetes-serverless architecture with GRU-based workload prediction for intelligent traffic routing. The system addresses elastic scalability management in heterogeneous cloud environments through SLO-aware decision making. Three research questions were posed; each is answered below with direct reference to experimental evidence.

== Conclusion

=== RQ1: GRU-Based Workload Prediction

A GRU (Gated Recurrent Unit) neural network was designed and optimized through hyperparameter optimization (HPO) using Optuna TPE. The optimal configuration uses one recurrent layer with 128 hidden units, learning rate 0.000380, sequence length 30, and dropout 0.104. Post-HPO accuracy improved from 6.01% to 4.75% RMSE.

The GRU predictor achieves target accuracy on synthetic workload patterns: RMSE 4.75% post-HPO (manual baseline 6.01%, target under 10%) with confidence scores 0.72-0.82 during live predictions. Validation against the ClarkNet HTTP trace yielded RMSE 17.78% at 5-minute aggregation — meaningful generalization, though below original thresholds due to non-stationarity and irregular burst patterns absent in synthetic training data.

=== RQ2: Modified ElaX Decision Making

Two algorithms were designed by extending the ElaX framework @yang2019elax for heterogeneous cloud environments. Algorithm 1 (Routing Controller) monitors tail latency (p99) against configurable thresholds and makes four types of decisions in priority order: SCALE_OUT for active SLO violations, PREDICTIVE for anticipated surges, OPTIMIZE_COST for stable periods, and MAINTAIN as default. Traffic distribution is implemented through weight-based routing via HAProxy, dynamically adjusting the Kubernetes-to-serverless split from 100/0 to 50/50.

Algorithm 2 (Cluster Controller) uses a horizontal scaling formula R = alpha dot.op x + beta integrated into the routing daemon for real-time Kubernetes replica scaling, operating in reactive mode (S3, using observed load) or predictive mode (S4, using GRU forecast).

The predictive pre-warming mechanism was validated in Phase A1: PREDICTIVE triggered at p99 = 146 ms (healthy state) upon detecting a predicted 47% workload surge with 72% confidence, successfully pre-positioning serverless capacity before SLO violation occurred.

=== RQ3: Evaluation of the Modified ElaX Mechanism

A comprehensive evaluation framework was designed spanning mechanism validation (Phase A1), replicated comparison (Phase B, n=5 per scenario), and dynamic burst validation (Phase C). The evaluation compares four scenarios: S1 (K8s+HPA), S2 (Serverless-only), S3 (Hybrid-reactive), and S4 (Hybrid-predictive).

H1 (hybrid architecture outperforms pure approaches): Mechanism validated, but superiority not supported on the localhost testbed. S4 was significantly worse than S1 on p99 latency (233.6 ms vs 109.8 ms, p = 0.01, Cohen's d = 2.84) due to localhost routing bias — the hybrid routing overhead is not offset by multi-node network-latency benefits absent in a single-node k3d cluster.

H2 (predictive scaling outperforms reactive): Mechanism validated in Phase A1. S4 achieved 75% fewer SLO violations than S3 (per-run mean 702 vs 2805; totals 3509 vs 14027 across n = 5) with large effect size (Cohen's d = 1.21), but the difference was not statistically significant at this sample size (p = 0.12).

H3 (GRU prediction adequacy): Validated on synthetic data — 4.75% RMSE post-HPO with confidence 0.72-0.82. Partial on real traces: ClarkNet RMSE 17.78% falls below original thresholds due to workload non-stationarity.

Cost analysis remains directional: no July cost bundle is marked final. February estimates under a unified AWS model suggest S4 may be cheaper than S1, but these figures are not directly comparable to the July controller version and are treated as indicative only.

In summary, this research validates the proposed mechanisms — the GRU predictor achieves target accuracy on synthetic data, the routing controller correctly shifts traffic based on SLO status, and proactive routing shows a large effect (d = 1.21) on SLO violations under appropriate conditions. However, statistical significance was not established at n = 5 (p = 0.12); production multi-node deployment with larger sample sizes is needed.

== Future Work

Based on the limitations identified during evaluation, six directions are recommended:

Multi-node cloud deployment: The single-node k3d testbed introduces localhost routing bias. Deploying on a multi-node cloud cluster (3+ nodes on AWS EKS or GCP GKE with Knative on separate nodes) would provide realistic network conditions necessary to reach statistical significance for the large effects already observed.

Algorithm 2 full integration: The horizontal scaling formula should be fully integrated with Kubernetes HPA coordination, enabling proactive replica scaling based on GRU predictions.

Dynamic workload experiments with extended ramp periods: PREDICTIVE requires a healthy observation window longer than the ramp duration to build trend predictions. Future experiments should use workload patterns with gradual ramps (90+ seconds) and longer baseline periods.

GRU retraining on production HTTP traces: Real-trace performance (17.78% RMSE) falls short of thresholds due to non-stationarity. Retraining on production traces with time-of-day encoding, day-of-week seasonality, and online learning would improve applicability.

Knative minScale configuration: Setting minScale=1 would maintain a warm serverless instance, eliminating cold start latency and isolating the routing mechanism's contribution to performance.

Extended statistical validation: Future work should target n = 30+ runs per scenario to satisfy normality assumptions and achieve adequate power for the large effects observed (Cohen's d approximately 1.0). This would provide definitive evidence regarding H1 and H2 superiority claims.
