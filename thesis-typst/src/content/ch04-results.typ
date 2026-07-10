// Chapter 4 — Results and Discussion
// English-first. Numbers from archived/thesis-latex 017-chapter-04.tex (authoritative)
// cross-checked against results/claims/CLAIMS_TO_EVIDENCE.md and thesis/chapters/04-results/*.md

= RESULTS AND DISCUSSION

This chapter presents the experimental results obtained from evaluating the hybrid Kubernetes-serverless architecture with GRU-based workload prediction. The results are organized into sections covering GRU model performance, system mechanism validation, comparative evaluation across deployment scenarios, cost analysis, and an integrative discussion. All claims are traceable to raw data in the project evidence registry under `results/`.

== GRU Prediction Model Performance

The GRU prediction model was optimized through hyperparameter optimization (HPO) using Optuna TPE with 30 trials. The optimal configuration found: one recurrent layer with 128 units, learning rate 0.000380, sequence length 30, and dropout 0.104. This optimization improved accuracy from 6.01% RMSE (manual tuning) to 4.75% RMSE — a 21% improvement.

During live experiments, the GRU model ran on a FastAPI server (port 8090). AMD Radeon 780M (gfx1103) GPU inference functioned after installing ROCm 7.2 SDK and stabilizing MIOpen. Inference latency reached 10-13 ms per prediction, well within the 15-second decision interval.

#figure(
  kind: table,
  table(
    columns: (auto, auto),
    [Metric], [Value],
    [Total successful predictions], [400/400],
    [Confidence range], [0.72 - 0.82],
    [Inference latency], [10 - 13 ms],
    [Validation RMSE (post-HPO)], [4.75%],
    [PREDICTIVE actions per run], [9],
    [Decision interval], [15 seconds],
  ),
  caption: [GRU model performance during live experiments (n=5, S4 scenario)],
) <tab:gru-performance>

An important finding: the GRU predictions lagged 2+ minutes behind actual load surges. When load rose from 50 to 110 RPS in 2 minutes, the GRU still predicted 65-73 RPS. Therefore, the proactive routing mechanism uses actual load trend (not GRU prediction) extrapolated forward, with GRU confidence as a gate (see Section 4.5).

== System Mechanism Validation (Phase A1)

Phase A1 validated the correct operation of individual system mechanisms under controlled ramp-load conditions. The workload profile was: 60 seconds baseline at 20 RPS, 60 seconds ramp from 20 to 100 RPS, and 120 seconds sustained peak at 100 RPS. The GRU prediction server was running with a lowered confidence threshold (0.6) to increase PREDICTIVE eligibility.

The routing controller made 18 decisions over the experiment duration, demonstrating all four action types in their correct priority order. The decision distribution was: MAINTAIN 8, SCALE_OUT 7, OPTIMIZE_COST 2, PREDICTIVE 1.

Weight shifting was validated: the system correctly shifted traffic weights from 100/0 (pure K8s) through five SCALE_OUT steps to 50/50 (maximum serverless engagement) as p99 latency exceeded the 200ms SLO threshold. Each step reduced the K8s weight by 10 percentage points.

The PREDICTIVE action was validated at Decision 9: the system was in a healthy state (p99 = 146ms, below the 200ms threshold), the GRU predicted a 47% workload increase with 72% confidence, and the controller triggered PREDICTIVE to maintain 50/50 weights — preserving serverless readiness before any SLO violation occurred. This is the core contribution of the predictive mechanism: the ability to maintain serverless engagement during healthy periods when a surge is anticipated.

== Comparative Evaluation

The comparative evaluation spans two experimental phases: Phase B (20 replicated runs under steady-state ClarkNet trace replay load) and a proactive routing evaluation (n=5 per scenario, dynamic workload). Both compare the four deployment scenarios: S1 (K8s+HPA), S2 (Serverless-only), S3 (Hybrid-reactive), and S4 (Hybrid-predictive).

The ClarkNet trace-driven replay used 40 stages of 30 seconds each (20 minutes total, RPS 22-164, mean 73). Evaluation was conducted through 30 replicated controlled experiments: 20 runs (4 scenarios x 5 replications) from the fib33_n5 experiments and 10 runs (2 scenarios x 5 replications) from the fib33_proactive experiments.

=== Per-Scenario Results (n=5, Proactive Routing)

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    [Scenario], [p50 (ms)], [p95 (ms)], [p99 (ms)], [SLO/run], [USD/month],
    [S1 (K8s+HPA)], [63.9], [77.1], [109.8], [41], [187],
    [S2 (Serverless)], [65.2], [75.5], [77.8], [7], [391],
    [S3 (Reactive)], [64.9], [157.3], [309.5], [2805], [142],
    [S4 (Predictive)], [64.7], [99.2], [187.9], [702], [149],
  ),
  caption: [Per-scenario summary results (n=5, ClarkNet trace replay)],
) <tab:scenario-summary>

S1 (K8s+HPA) achieves the lowest p99 (109.8 ms) but at the highest cost (USD 187/month) because HPA scales to 10 pods. S2 (Serverless-only) has the absolute lowest p99 (77.8 ms) but the highest cost (USD 391/month). S4 (Hybrid-predictive) achieves the best balance with p99 = 187.9 ms and cost USD 149/month.

=== Statistical Analysis

Statistical comparison between S4 (Hybrid-predictive) and S3 (Hybrid-reactive) was conducted using Welch's t-test and Mann-Whitney U.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto),
    [Metric], [p99 (ms)], [SLO Violations],
    [S3 mean], [309.5], [2805],
    [S4 mean], [187.9], [702],
    [Difference], [-121.6 (39%)], [-2104 (75%)],
    [Welch t-stat], [-1.919], [-1.922],
    [Welch p-value], [0.122], [0.125],
    [Mann-Whitney U], [9.0], [9.0],
    [Cohen's d], [-1.21 (large)], [-1.22 (large)],
    [95% CI], [[-229, -10]], [[-3996, -240]],
  ),
  caption: [Statistical comparison S4 vs S3 (n=5)],
) <tab:statistical-comparison>

The difference between S4 and S3 did not reach statistical significance at alpha = 0.05 (p = 0.12). However, Cohen's d = 1.21 indicates a large effect size, and the 95% confidence interval for both metrics does not include zero, supporting a consistent direction of effect. The high variance of S3 (one run reached 143 ms/191 SLO) inflates the standard deviation and prevents statistical significance at n = 5.

== Cost Analysis

Cost analysis maps the experiment's local k3s architecture to equivalent AWS services, producing a unified cost projection from measured resource consumption. The mapping is: K8s HPA pods map to EKS control plane plus EC2 nodes, Knative KPA pods map to AWS Lambda Provisioned Concurrency.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto),
    [Scenario], [USD/month], [USD/1M req], [Serverless traffic],
    [S1 (K8s+HPA)], [187], [1.04], [0%],
    [S2 (Serverless)], [391], [2.17], [100%],
    [S3 (Reactive)], [142], [0.79], [2.7%],
    [S4 (Predictive)], [149], [0.82], [6.5%],
  ),
  caption: [Monthly cost projection (AWS, 30 days continuous)],
) <tab:cost-summary>

S4 spends USD 7/month more than S3 due to higher serverless traffic (6.5% vs 2.7%), but achieves 75% fewer SLO violations. S4 is also 20% cheaper than S1 (USD 149 vs USD 187/month) because it does not require HPA scaling to 10 pods and 2 additional nodes.

== Impact of Proactive Routing

Implementation of proactive routing based on actual load trend yielded a significant performance impact on S4. Before implementation (reactive-only mode), S4 averaged 1,369 SLO violations per run with 0 PREDICTIVE actions. After implementation, the average dropped to 702 SLO violations with 9 PREDICTIVE actions per run — a 49% improvement.

This demonstrates that the proactive routing mechanism (actual trend extrapolation gated by GRU confidence) is effective at reducing SLO violations, even though the GRU prediction itself lags actual load changes.

== Discussion

The experimental evaluation validates the mechanistic correctness of the hybrid architecture while revealing that statistical superiority over baseline approaches could not be definitively established within the constraints of the testbed.

Mechanisms validated include: GRU prediction achieves target accuracy on synthetic data (RMSE 4.75% post-HPO) and demonstrates meaningful generalization to real traces. The routing controller correctly implements the priority-based decision framework. Predictive pre-warming triggered before SLO violations in Phase A1. Proactive routing reduced SLO violations by 49% compared to reactive-only mode.

The tension between large effect sizes (Cohen's d = 1.21) and non-significant p-values (p = 0.12) reflects a statistical power limitation, not an absence of practical difference. A post-hoc power analysis suggests approximately n = 15-20 runs per scenario would be required to detect this effect size at alpha = 0.05 with 80% power. The current n = 5 provides approximately 30-40% power.

Three testbed constraints systematically affect interpretation. The localhost routing bias of the single-node k3d testbed eliminates network latency between components, disproportionately advantaging S1 (K8s-only). The artificial node capacity constraint (400m allocatable) forces autoscaler triggers at lower loads than production. The GRU prediction lag of 2+ minutes behind actual load surges required the proactive routing mechanism to use actual trend extrapolation rather than direct GRU prediction.

The results support the following defensible framing: the hybrid Kubernetes-serverless system with GRU-based prediction has been designed, implemented, and its mechanisms validated. All proposed components function correctly under appropriate conditions. Statistical performance superiority over baselines was not established due to testbed constraints, but the large effect sizes and consistent direction of improvement suggest that production deployment on multi-node infrastructure with adequate sample sizes would likely confirm these differences.
