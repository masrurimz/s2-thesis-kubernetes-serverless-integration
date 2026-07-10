// Chapter 4 — Results and Discussion
// English-first. Numbers sourced ONLY from results/claims/FINAL_NUMBERS.md
// (the single source of truth), which in turn quotes only REGISTRY.yaml
// bundles with role: final. Do not introduce numbers from any other file.

= RESULTS AND DISCUSSION

This chapter presents the experimental results obtained from evaluating the hybrid Kubernetes-serverless architecture with GRU-based workload prediction. The results are organized into sections covering GRU model performance, system mechanism validation, the comparative evaluation across deployment scenarios, cost analysis, and an integrative discussion. Every quantitative claim in this chapter is traceable to a designated final bundle recorded in the experiment registry under `results/`, as consolidated in `results/claims/FINAL_NUMBERS.md`.

== GRU Prediction Model Performance

The GRU prediction model was tuned through hyperparameter optimization. On synthetic validation data, optimization reduced the root-mean-square error from 6.01% under manual tuning to 4.75%, with a mean absolute error of 4.91%. During live experiments the model issued predictions with a confidence range of 0.72 to 0.82 and an inference latency of approximately 40 ms, comfortably within the controller's decision interval. On real ClarkNet traces the best 5-minute-horizon model reached an RMSE of 17.78%, an MAE of 14.48%, and a MAPE of 18.74% — substantially above the synthetic accuracy, so prediction on real traffic is characterized as a partial validation rather than a confirmed target.

#figure(
  kind: table,
  table(
    columns: (auto, auto),
    [Metric], [Value],
    [Synthetic RMSE (manual tuning)], [6.01%],
    [Synthetic RMSE (post-HPO)], [4.75%],
    [Synthetic MAE], [4.91%],
    [Inference latency], [~40 ms],
    [Confidence range (live)], [0.72 to 0.82],
    [ClarkNet RMSE (5-min, best)], [17.78%],
    [ClarkNet MAE], [14.48%],
    [ClarkNet MAPE], [18.74%],
  ),
  caption: [GRU model performance. Synthetic metrics from the final training bundle; ClarkNet metrics from the real-trace evaluation bundle.],
) <tab:gru-performance>

An operational finding shaped the design of the predictive controller: during live experiments the GRU predictions lagged behind actual load surges. The proactive routing mechanism therefore extrapolates the observed load trend forward, with the GRU confidence score acting as a gating signal rather than the prediction itself driving the routing decision (see the comparative evaluation below).

== System Mechanism Validation (Phase A1)

Phase A1 validated the correct operation of the individual system mechanisms under a controlled ramp-load profile. Over the experiment duration the routing controller made 18 decisions, exhibiting all four action types in their correct priority order: SCALE_OUT (7), MAINTAIN (8), OPTIMIZE_COST (2), and PREDICTIVE (1).

#figure(
  kind: table,
  table(
    columns: (auto, auto),
    [Action], [Count],
    [SCALE_OUT], [7],
    [MAINTAIN], [8],
    [OPTIMIZE_COST], [2],
    [PREDICTIVE], [1],
    [Total], [18],
  ),
  caption: [Routing-controller decision distribution during the Phase A1 ramp-load experiment.],
) <tab:phase-a1-decisions>

Weight shifting was validated: traffic weights moved from 100/0 (pure Kubernetes) through successive scale-out steps to 50/50 (maximum serverless engagement) as tail latency exceeded the SLO threshold, each step shifting the split by ten percentage points. The PREDICTIVE action was validated while the system was in a healthy state (p99 = 146 ms): the GRU predicted a 47% workload increase with 72% confidence, and the controller triggered PREDICTIVE to maintain the 50/50 split — preserving serverless readiness before any SLO violation occurred. This is the core contribution of the predictive mechanism: the ability to sustain serverless engagement during healthy periods when a surge is anticipated.

== Comparative Evaluation

The comparative evaluation compares four deployment scenarios: S1 (Kubernetes with HPA), S2 (serverless-only), S3 (hybrid with reactive routing), and S4 (hybrid with predictive routing). All scenarios replayed the ClarkNet HTTP trace at a mean of 73.2 requests per second with a 0.000% error rate, with n = 5 replications per scenario and no excluded runs. S1 and S2 are drawn from the fib33_n5 bundle, in which the proactive routing mechanism is not yet enabled. S3 and S4 are drawn from the fib33_proactive bundle, in which proactive routing is enabled. The pre-proactive S3 and S4 values (p99 of 382.1 ms and 233.6 ms respectively) are superseded by the proactive bundle and are not used for the predictive-versus-reactive comparison; they are retained only for the like-for-like S4-versus-S1 comparison reported below.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto),
    [Scenario], [p50 (ms)], [p95 (ms)], [p99 (ms)], [SLO Violations],
    [S1 (K8s+HPA)], [63.9], [77.1], [109.8], [206],
    [S2 (Serverless)], [65.2], [75.5], [77.8], [35],
    [S3 (Reactive)], [64.9], [157.3], [309.5], [14027],
    [S4 (Predictive)], [64.7], [99.2], [187.9], [3509],
  ),
  caption: [Per-scenario summary (n = 5 runs each). S1/S2 from the fib33_n5 bundle; S3/S4 from the fib33_proactive bundle. SLO violation counts are totals across the five runs.],
) <tab:scenario-summary>

Across the four scenarios the p50 latencies are closely grouped (63.9 to 65.2 ms), so the scenarios are differentiated primarily by tail latency and by SLO violations. S2 (serverless-only) achieves the lowest p99 (77.8 ms) and the fewest SLO violations (35), while the hybrid scenarios S3 and S4 show higher p99 under the proactive configuration than either single-backend scenario. The role of the hybrid scenarios is therefore assessed through two directed comparisons: the predictive scenario against the reactive scenario (S4 vs S3), and the hybrid predictive scenario against pure Kubernetes (S4 vs S1).

=== Predictive versus Reactive (S4 vs S3)

Statistical comparison between S4 (hybrid-predictive) and S3 (hybrid-reactive) was conducted using Welch's t-test and the Mann-Whitney U test, with effect size reported as Cohen's d. All values are per-run means from the fib33_proactive bundle.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto),
    [Metric], [p99 (ms)], [SLO Violations],
    [S3 mean], [309.54], [2805.40],
    [S4 mean], [187.90], [701.80],
    [Difference], [-121.65 (-39.3%)], [-2103.60 (-75.0%)],
    [Welch t-stat], [-1.919], [-1.922],
    [Welch p-value], [0.1216], [0.1247],
    [Mann-Whitney U], [9.0], [9.0],
    [Mann-Whitney p], [0.5476], [0.5476],
    [95% CI], [[-229.35, -10.33]], [[-3995.60, -239.80]],
    [Cohen's d], [-1.214 (large)], [-1.215 (large)],
    [Significance (α = 0.05)], [Not significant], [Not significant],
  ),
  caption: [Statistical comparison of S4 versus S3 (n = 5 per scenario, proactive bundle).],
) <tab:statistical-comparison>

The predictive scenario S4 reduced mean p99 latency by 39.3% (from 309.54 ms to 187.90 ms) and mean SLO violations by 75.0% (from 2805.40 to 701.80 per run) relative to the reactive scenario S3. Both reductions correspond to large effect sizes (Cohen's d = 1.214 and 1.215). However, neither difference reached statistical significance at α = 0.05: Welch's t-test gave p = 0.1216 for p99 latency and p = 0.1247 for SLO violations, and the non-parametric Mann-Whitney U test gave p = 0.5476 for both metrics. The 95% confidence intervals (p99: -229.35 to -10.33 ms; SLO: -3995.60 to -239.80) exclude zero, supporting a consistent direction of effect. With only n = 5 runs per scenario and high run-to-run variance in S3, the comparison is underpowered. The defensible conclusion is that the predictive mechanism is validated and produces a large, consistently directed improvement, while statistical superiority over the reactive baseline is not established at the chosen significance level.

=== Hybrid versus Pure Kubernetes (S4 vs S1)

Comparing the hybrid predictive scenario against pure Kubernetes points the other way. To keep the comparison like-for-like, both values are taken from the fib33_n5 bundle (pre-proactive configuration), where S4 recorded a mean p99 of 233.64 ms against 109.78 ms for S1.

#figure(
  kind: table,
  table(
    columns: (auto, auto),
    [Metric], [Value],
    [S1 mean p99], [109.78 ms],
    [S4 mean p99], [233.64 ms],
    [Difference], [+123.86 ms (+112.8%)],
    [Welch t-stat], [4.488],
    [Welch p-value], [0.0104],
    [Cohen's d], [2.839 (large)],
    [Significance (α = 0.05)], [Significant — S4 worse],
  ),
  caption: [Statistical comparison of S4 versus S1 on p99 latency (n = 5 per scenario, fib33_n5 bundle).],
) <tab:s4-vs-s1>

S4 was significantly worse than S1 on p99 latency (Welch p = 0.0104, Cohen's d = 2.839). This significant negative result is attributed to localhost routing bias: on the single-node k3d testbed there is no network latency for the hybrid path to absorb, so the routing layer adds overhead without the latency benefit that a multi-node deployment would provide. H1 (hybrid superiority over pure Kubernetes) is therefore not supported by these results; the hybrid mechanism itself is nonetheless validated.

== Cost Analysis

Cost analysis for this architecture maps the local testbed to equivalent cloud services — Kubernetes HPA pods to a managed control plane plus compute nodes, and Knative concurrency to provisioned function concurrency — and projects a unified monthly cost from measured resource consumption. However, no cost bundle is designated as final for the July fib33 experiments. The earlier cost bundles correspond to a different controller version and are not comparable to the proactive routing evaluated here; mixing their estimates with the July latency results would conflate two configurations.

Accordingly, this chapter does not present a cost comparison as a final result. Directional cost estimates from the earlier configuration exist, but they require re-running against the final controller before they can support a thesis-level claim. The latency and SLO results above therefore stand without an accompanying final cost figure, and cost analysis is deferred to a confirmatory evaluation on the final controller.

== Discussion

The experimental evaluation validates the mechanistic correctness of the hybrid architecture while showing that statistical superiority over the baseline approaches could not be established within the constraints of the single-node testbed.

Several mechanisms were validated. The GRU model meets its accuracy target on synthetic data, with a validation RMSE of 4.75% after hyperparameter optimization and an MAE of 4.91%, at an inference latency of approximately 40 ms; on real ClarkNet traces the error is substantially higher (RMSE 17.78%, MAPE 18.74%), so real-traffic prediction is a partial validation. The routing controller correctly implements the priority-based decision framework, exhibiting all four action types. Predictive pre-warming triggered before any SLO violation during the Phase A1 ramp-load experiment, and traffic weights shifted from 100/0 to 50/50 as intended.

For the predictive-versus-reactive comparison, S4 reduced mean p99 latency by 39.3% and mean SLO violations by 75.0% relative to S3, with large effect sizes (Cohen's d of 1.214 and 1.215). These differences did not reach statistical significance at α = 0.05 (Welch p = 0.1216 for p99 and p = 0.1247 for SLO violations) with n = 5 runs per scenario. The 95% confidence intervals exclude zero, indicating a consistent direction of effect, but the small sample and the high run-to-run variance of S3 leave the comparison underpowered. The defensible conclusion is that the predictive mechanism is validated and produces a large, consistently directed improvement, while statistical superiority is not established at the chosen significance level.

For the hybrid-versus-pure-Kubernetes comparison, the result points the other way: on the localhost testbed the pre-proactive predictive scenario (S4, p99 = 233.64 ms) was significantly worse than pure Kubernetes (S1, p99 = 109.78 ms; Welch p = 0.0104, Cohen's d = 2.839). This negative result is attributed to localhost routing bias — on a single node there is no network latency for the hybrid path to absorb, so the routing layer adds overhead without the latency benefit of multi-node deployment. Hybrid superiority over pure Kubernetes is therefore not supported by these results; the mechanism is nonetheless validated.

Three testbed constraints systematically affect interpretation. First, the single-node k3d deployment eliminates inter-component network latency, disproportionately favoring the Kubernetes-only scenario. Second, the artificial node capacity constraint triggers autoscaling at lower loads than a production cluster. Third, GRU predictions lag actual load changes, which is why the proactive mechanism extrapolates the observed load trend rather than consuming the raw prediction.

Taken together, the results support a measured framing. The hybrid Kubernetes-serverless system with GRU-based prediction has been designed and implemented, and each of its mechanisms has been validated under appropriate conditions. Statistical performance superiority over the baselines was not established, largely because of testbed constraints and a small sample size. The large effect sizes and the consistent direction of improvement for the predictive mechanism indicate that production deployment on multi-node infrastructure with adequate replication would be the appropriate setting for a confirmatory evaluation.
