// Chapter 4 — Results and Discussion
// English-first. Numbers sourced ONLY from results/claims/FINAL_NUMBERS.md
// (the single source of truth), which cites the current baseline bundle
// results/experiments/phase-b/2026-07-11_scaling_fix_n1 (n=1 diagnostic).
// All pre-2026-07-11 bundles are superseded (Bugs 8-13). n=5 replication
// is required for statistical significance; do not introduce numbers from
// any other file.

= RESULTS AND DISCUSSION

This chapter presents the experimental results obtained from evaluating the hybrid Kubernetes-serverless architecture with GRU-based workload prediction. The results are organized into sections covering GRU model performance, system mechanism validation, the comparative evaluation across deployment scenarios, cost analysis, and an integrative discussion. Every quantitative claim in this chapter is traceable to the experiment registry under `results/`, as consolidated in `results/claims/FINAL_NUMBERS.md`. _Important caveat:_ the comparative and cost results reported here are drawn from the `2026-07-11_scaling_fix_n1` baseline, which is an *n = 1 diagnostic* run. All previous experiment bundles (February and July 8-10, 2026) were invalidated by six infrastructure fixes (Bugs 8-13: enforced node CPU limits, recalibrated saturation, a fairness cap on Kubernetes replicas, and the separation of prediction from routing). An *n = 5* replication is required before any of these findings can be reported as statistically significant; throughout this chapter, effect sizes and verdicts are therefore framed as diagnostic rather than confirmatory.

== GRU Prediction Model Performance

The GRU prediction model was tuned through hyperparameter optimization using Optuna @optuna2019, a next-generation framework that employs the Tree-structured Parzen Estimator (TPE) algorithm. On synthetic validation data, optimization reduced the root-mean-square error from 6.01% under manual tuning to 4.75%, with a mean absolute error of 4.91%. The risk of overfitting in model selection was considered @cawley2010overfitting, and the holdout validation approach follows best practices for non-stationary workloads @nonstationary2022 @falkner2018bohb. During live experiments the model issued predictions with a confidence range of 0.72 to 0.82 and an inference latency of approximately 40 ms, comfortably within the controller's decision interval. On real ClarkNet traces the best 5-minute-horizon model reached an RMSE of 17.78%, an MAE of 14.48%, and a MAPE of 18.74% — substantially above the synthetic accuracy, so prediction on real traffic is characterized as a partial validation rather than a confirmed target. The SeBS benchmark suite @sebs2020 informed the workload characterization methodology.

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

The comparative evaluation compares four deployment scenarios: S1 (Kubernetes with HPA), S2 (serverless-only), S3 (hybrid with reactive routing), and S4 (hybrid with predictive routing). All scenarios replayed the ClarkNet HTTP trace at a mean of 73 requests per second (peak 164 RPS) under a calibrated node capacity of Docker `--cpus=1.0` per workload node (2.0 CPU total), with `max_k8s_replicas = 6` capped to schedulable capacity and no per-pod CPU limits. These are *n = 1 diagnostic* results from the `2026-07-11_scaling_fix_n1` baseline; n = 5 replication is pending. All four scenarios were run on this fixed infrastructure, so the comparison is like-for-like within a single bundle — unlike the superseded July bundles, in which S1/S2 and S3/S4 came from different controller configurations.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    [Scenario], [p99 (ms)], [SLO Violations], [SLO Rate], [Serverless %], [PREDICTIVE],
    [S1 (K8s+HPA)], [2,421.3], [6,717], [7.66%], [0.0%], [0],
    [S2 (Serverless)], [77.7], [19], [0.02%], [100.0%], [0],
    [S3 (Reactive)], [98.8], [3], [0.00%], [31.8%], [0],
    [S4 (Predictive)], [118.2], [104], [0.12%], [24.7%], [9],
  ),
  caption: [Per-scenario summary (n = 1 diagnostic run, `2026-07-11_scaling_fix_n1` baseline). SLO threshold: p99 < 200 ms. SLO Violations and SLO Rate are for the single run; Serverless % is the share of requests routed to Knative; PREDICTIVE is the count of proactive scaling actions fired.],
) <tab:scenario-summary>

The four scenarios separate sharply into two regimes. S1 (pure Kubernetes with HPA) saturates under the ClarkNet load: its p99 reaches 2,421.3 ms and it accrues 6,717 SLO violations (7.66% SLO violation rate), far exceeding the 200 ms SLO threshold. The other three scenarios all keep the p99 well under the SLO — S2 (serverless-only) at 77.7 ms, S3 (hybrid-reactive) at 98.8 ms, and S4 (hybrid-predictive) at 118.2 ms — with SLO violation rates at or near zero (0.02%, 0.00%, and 0.12% respectively). The role of the hybrid scenarios is therefore assessed through two directed comparisons: the predictive scenario against the reactive scenario (S4 vs S3), and the hybrid predictive scenario against pure Kubernetes (S4 vs S1). Because only a single run is available per scenario, no inferential statistics (t-tests, effect sizes, confidence intervals) are computed; the comparison is descriptive, and the verdicts below are explicitly framed as *n = 1 diagnostic* pending replication.

=== Predictive versus Reactive (S4 vs S3)

With the prediction-for-routing architecture corrected (see @sec:arch-decision below), the predictive scenario S4 no longer routes more traffic to serverless than the reactive S3; instead it provisions Kubernetes capacity earlier. The n = 1 comparison is summarized in @tab:s4-vs-s3.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto),
    [Metric], [S3 (Reactive)], [S4 (Predictive)], [Difference],
    [p99 latency (ms)], [98.8], [118.2], [+19.4 (+19.7%)],
    [SLO violations], [3], [104], [+101 (both near-zero rate)],
    [Serverless requests], [5,354], [2,666], [-2,688 (-50.2%)],
    [Serverless share], [31.8%], [24.7%], [-7.1 pp],
    [Monthly cost (AWS)], [$147], [$142], [-$5 (-3.4%)],
  ),
  caption: [Predictive (S4) versus reactive (S3) comparison (n = 1 diagnostic, `2026-07-11_scaling_fix_n1`). No inferential statistics are reported at n = 1.],
) <tab:s4-vs-s3>

S4 does *not* provide a latency advantage over S3 in this diagnostic run: its p99 is 19.7% higher (118.2 ms vs 98.8 ms) and it records more SLO violations (104 vs 3), though both scenarios keep the SLO violation rate near zero (0.12% vs 0.00%). Where S4 does win is cost and serverless dependency: it sends 50.2% fewer requests to serverless (2,666 vs 5,354) and projects $5/month cheaper ($142 vs $147), because proactive Kubernetes scaling absorbs load that S3 must spill to Knative. H2 (predictive scaling outperforms reactive) is therefore *partially supported at n = 1*: the cost advantage is demonstrated, but latency superiority is not, and both effects require n = 5 replication before they can be treated as established.

=== Hybrid versus Pure Kubernetes (S4 vs S1)

With the infrastructure correctly bounded (`--cpus=1.0` per node enforced, `max_k8s_replicas = 6`), pure Kubernetes (S1) saturates as designed under the ClarkNet load, and the hybrid predictive scenario provides a large improvement (@tab:s4-vs-s1).

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto),
    [Metric], [S1 (K8s+HPA)], [S4 (Predictive)], [Improvement],
    [p99 latency (ms)], [2,421.3], [118.2], [-2,303.1 (-95.1%)],
    [SLO violations], [6,717], [104], [-6,613 (-98.5%)],
    [SLO violation rate], [7.66%], [0.12%], [-7.54 pp],
  ),
  caption: [Hybrid predictive (S4) versus pure Kubernetes (S1) (n = 1 diagnostic, `2026-07-11_scaling_fix_n1`). No inferential statistics are reported at n = 1.],
) <tab:s4-vs-s1>

The hybrid predictive scenario reduces p99 latency by 95.1% (from 2,421.3 ms to 118.2 ms) and SLO violations by 98.5% (from 6,717 to 104) relative to pure Kubernetes. This reverses the earlier negative finding: the previous H1 result (S4 worse than S1) was an artifact of Bugs 8 and 11 — node CPU limits were never enforced (pods consumed the full 16-core host) and S1's HPA provisioned dynamic nodes (4.0 CPU vs 2.0 CPU for S3/S4), so S1 never saturated. With `--cpus=1.0` per node enforced and replicas capped at schedulable capacity, S1 saturates as intended and hybrid routing (S4) provides a clear benefit. H1 (hybrid routing outperforms pure Kubernetes) is therefore *confirmed at n = 1*, with the explicit caveat that a single run cannot establish statistical significance; n = 5 replication is required.

=== Architecture Decision: Prediction Drives Scaling, Not Routing <sec:arch-decision>

A key architectural decision, fixed as part of the Bug 13 correction, shapes the S4 results. In the earlier (superseded) design, the GRU prediction directly adjusted the serverless routing weight. This caused over-routing to serverless during moderate load: whenever the predictor anticipated a surge, traffic was shifted toward Knative, incurring cold-start and concurrency overhead that *worsened* p99 latency relative to the reactive baseline.

In the corrected architecture, prediction drives Kubernetes *scaling* rather than serverless *routing*. The GRU forecast is consumed by Algorithm 2 via trend extrapolation to provision Kubernetes replicas proactively (`proactive_approach_ratio = 0.8`), while the routing weight continues to use *actual* observed load only. This separation prevents over-routing to serverless during moderate load while enabling proactive resource provisioning: S4 never routes more traffic to serverless than S3 (eliminating unnecessary Knative overhead), yet still benefits from prediction through earlier Kubernetes capacity provisioning. This is why S4's serverless share (24.7%) is lower than S3's (31.8%), and why S4 is cheaper despite a marginally higher p99. The diagnostic run fired 9 PREDICTIVE actions in S4, confirming that the proactive scaling mechanism engages under this workload.

== Cost Analysis

Cost analysis for this architecture maps the local testbed to equivalent cloud services — Kubernetes HPA pods to a managed control plane plus compute nodes, and Knative concurrency to provisioned function concurrency — and projects a unified monthly cost from measured resource consumption. The projections below come from the `2026-07-11_scaling_fix_n1` baseline and are *n = 1 diagnostic* estimates.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto),
    [Scenario], [Total/mo], [$/1M SLO-OK], [Serverless Reqs], [EC2 Nodes],
    [S1 (K8s-only)], [$132], [$0.79], [0], [2],
    [S2 (Serverless)], [$394], [$2.19], [87,840], [0],
    [S3 (Hybrid-reactive)], [$147], [$0.81], [5,354], [2],
    [S4 (Hybrid-predictive)], [$142], [$0.79], [2,666], [2],
  ),
  caption: [AWS monthly cost projection (n = 1 diagnostic, `2026-07-11_scaling_fix_n1`). $/1M SLO-OK normalizes total monthly cost by the count of SLO-satisfying requests.],
) <tab:cost-analysis>

S1 is the cheapest scenario ($132/mo) but fails the SLO catastrophically (p99 = 2,421 ms, 7.66% violation rate), so its low cost reflects poor service rather than efficiency. S2 (serverless-only) is the most expensive ($394/mo) but achieves the best raw latency (77.7 ms). Among the hybrid scenarios, S4 is cheaper than S3 ($142 vs $147/mo) and matches S1's cost-efficiency ($0.79/1M SLO-OK) while cutting serverless dependency in half (2,666 vs 5,354 requests). A full cost-performance Pareto analysis is presented in the conclusion (Chapter 5).

== Controller HPO and Holdout Validation

A separate hyperparameter optimization study explored four controller parameters via Optuna TPE screening: `target_cpu_util`, `kp_burn`, `proactive_trend_threshold`, and `proactive_approach_ratio`. The methodological finding from this study — conducted on the pre-fix infrastructure that predates the `2026-07-11_scaling_fix_n1` baseline — is reported here for completeness, but its specific quantitative results are *directional* and are superseded by Bugs 8-13; they are not part of the current baseline and are not used in the comparative evaluation above.

The substantive lesson is methodological rather than numerical: on a shared-resource testbed with high run-to-run variance, no parameter deviation from the default calibration survived holdout validation. Configurations that looked strong on a single run degraded sharply under replication, because they narrowed the Kubernetes safety margin and caused more frequent saturation under high variance. This is consistent with overfitting risks in model selection @cawley2010overfitting and highlights the difficulty of HPO in online systems where each evaluation requires a full experiment under noisy shared-resource conditions @nonstationary2022 @falkner2018bohb. The two-stage methodology (screening followed by robust confirmation) and the surrogate-assisted approach adapt techniques from @kapetanios2022. The conclusion directly shaped the current baseline: the default `target_cpu_util = 0.5` — equivalently the calibrated `r_saturation_per_replica = 33.3` at which S1 saturates at 100 RPS — was retained, and no HPO-tuned deviation is used in the `2026-07-11_scaling_fix_n1` results.

== Discussion

The experimental evaluation validates both the mechanistic correctness of the hybrid architecture and, under the correctly bounded infrastructure, a clear performance advantage for hybrid routing over pure Kubernetes.

Several mechanisms were validated. The GRU model meets its accuracy target on synthetic data, with a validation RMSE of 4.75% after hyperparameter optimization and an MAE of 4.91%, at an inference latency of approximately 40 ms; on real ClarkNet traces the error is substantially higher (RMSE 17.78%, MAPE 18.74%), so real-traffic prediction is a partial validation. The routing controller correctly implements the priority-based decision framework, exhibiting all four action types, and the corrected predictive mechanism fired 9 PREDICTIVE actions in the S4 diagnostic run, provisioning Kubernetes capacity proactively.

For the hybrid-versus-pure-Kubernetes comparison (H1), the result is now positive and large: S4 reduced p99 latency by 95.1% (2,421.3 ms -> 118.2 ms) and SLO violations by 98.5% (6,717 -> 104) relative to S1. The previous negative finding was an infrastructure artifact (un-enforced CPU limits and S1 dynamic-node over-provisioning), not a property of the hybrid mechanism. H1 is *confirmed at n = 1*.

For the predictive-versus-reactive comparison (H2), the result is mixed: S4 does not beat S3 on latency (118.2 ms vs 98.8 ms, +19.7%) but provides a cost advantage — 50.2% fewer serverless requests and $5/month lower cost ($142 vs $147) — because proactive Kubernetes scaling absorbs load that the reactive controller spills to Knative. H2 is *partially supported at n = 1*: cost efficiency is demonstrated, latency superiority is not. Both scenarios keep the SLO violation rate near zero.

Two caveats bound these conclusions. First, all comparative numbers are from a single *n = 1 diagnostic* run (`2026-07-11_scaling_fix_n1`); no inferential statistics are reported, and n = 5 replication is required before the verdicts can be treated as statistically established. Second, GRU predictions lag actual load changes, which is why the corrected mechanism uses the GRU forecast to extrapolate the observed load trend for Kubernetes scaling rather than consuming the raw prediction for routing.

Taken together, the results support a positive but provisional framing. The hybrid Kubernetes-serverless system with GRU-based prediction has been designed and implemented, its mechanisms are validated, and hybrid routing delivers a large, directionally consistent performance improvement over pure Kubernetes while the predictive variant trades a small latency penalty for a meaningful cost reduction. Confirmatory evaluation at n = 5 on the fixed infrastructure is the appropriate next step. Recent benchmark studies @rayscale2026 show that even deep RL autoscalers struggle to outperform well-calibrated baselines on cost, while budget-aware approaches @bacc2026 @pobo2024 demonstrate that SLO compliance can be improved by explicitly accounting for remaining error budgets — directions that align with the proactive scaling mechanism validated here.
