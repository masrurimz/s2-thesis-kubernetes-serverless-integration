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

A counterbalanced paired experiment (n = 5 S3/S4 pairs, `2026-07-12_paired-h2-clean-v2` bundle) was conducted to test H2. All 5 pairs delivered complete GRU forecasts (56 eligible prediction cycles per run, 0 failures). The primary endpoint is the paired p99 latency difference. @tab:paired-h2-primary reports the result.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto),
    [Statistic], [Value], [Interpretation],
    [S3 mean p99 (ms)], [136.62], [Reactive baseline],
    [S4 mean p99 (ms)], [128.54], [Predictive scenario],
    [Mean difference (ms)], [-8.08], [S4 faster],
    [95% paired CI (ms)], [-36.70 to +14.53], [Spans improvement and deterioration],
    [Permutation p (two-sided)], [0.3784], [Does not support H2],
    [Paired Cohen's d], [-0.241], [Small effect, S4 better],
  ),
  caption: [Paired S4-vs-S3 p99 latency comparison (n = 5, full treatment delivery, `2026-07-12_paired-h2-clean-v2`). The mean difference is in S4's favorable direction but the 95% CI includes zero.],
) <tab:paired-h2-primary>

The mean difference is in S4's favorable direction (S4 is 8.1 ms faster on average), but the 95% CI [-36.7, +14.5] crosses zero and the permutation test is not significant (p = 0.38). H2 (predictive latency superiority) is therefore *not statistically supported*, though the direction is consistent with the hypothesis. S4 wins 2 of 5 pairs; the mean advantage is driven primarily by pair 4 (S3 = 173 ms, S4 = 112 ms).

A notable secondary finding is that S4 shows 56% fewer SLO violations on average (100.8 vs 228.2, Cohen's d = -0.535, medium effect), though this is also not statistically significant at n = 5 (p = 0.19). This suggests proactive scaling keeps p99 below the SLO threshold more consistently, even when the mean p99 difference is small.

=== Calibration Repair and Effect Reversal

The clean paired comparison used a corrected scaling model. The original calibration used alpha = 1/r_saturation with a 1.2x buffer, which double-counted the safety margin (target_cpu_util already provides headroom). A forecast of 62 RPS mapped to ceil(62 / 33.3 times 1.2) = 3 replicas -- the same target as the observed signal, making S4 operationally identical to S3. The corrected model uses alpha = 1/r_effective (= 1 / (r_saturation times target_cpu_util) = 1/16.65) with buffer = 1.0. Now 62 RPS maps to ceil(62 times 0.060) = 4 replicas, differentiating the forecast from the observed 45-RPS target of 3.

This repair reversed the effect direction. The earlier (confounded) paired comparison found S4 10 ms *slower* (mean diff +10.0 ms); the clean comparison with the corrected calibration finds S4 8.1 ms *faster* (mean diff -8.1 ms). The reversal demonstrates that the calibration mismatch was the root cause of S4's apparent underperformance, not the controller design itself. However, the effect remains small (d = -0.241) and not statistically significant at n = 5, so H2 cannot be claimed.

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



== Cost Analysis

Cost analysis for this architecture maps the local testbed to equivalent cloud services — Kubernetes HPA pods to a managed control plane plus compute nodes, and Knative concurrency to provisioned function concurrency — and projects a unified monthly cost from measured resource consumption. The projections below come from the `2026-07-11_scaling_fix_n1` baseline and are *n = 1 diagnostic* estimates.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto),
    [Scenario], [Total/mo], [USD/1M SLO-OK], [Serverless Reqs], [EC2 Nodes],
    [S1 (K8s-only)], [USD 132], [USD 0.79], [0], [2],
    [S2 (Serverless)], [USD 394], [USD 2.19], [87,840], [0],
    [S3 (Hybrid-reactive)], [USD 147], [USD 0.81], [5,354], [2],
    [S4 (Hybrid-predictive)], [USD 142], [USD 0.79], [2,666], [2],
  ),
  caption: [AWS monthly cost projection (n = 1 diagnostic, `2026-07-11_scaling_fix_n1`). USD/1M SLO-OK normalizes total monthly cost by the count of SLO-satisfying requests.],
) <tab:cost-analysis>

S1 is the cheapest scenario (USD 132/mo) but fails the SLO catastrophically (p99 = 2,421 ms, 7.66% violation rate), so its low cost reflects poor service rather than efficiency. S2 (serverless-only) is the most expensive (USD 394/mo) but achieves the best raw latency (77.7 ms). These n = 1 cost projections are *directional diagnostic estimates only* and must not be used to rank S3 and S4 or claim monthly savings.

== Dynamic Node Provisioning and Serverless Offload

The baseline diagnostic (`2026-07-11_scaling_fix_n1`) caps `max_k8s_replicas = 6` to match the two-node schedulable capacity, so the K3dAutoscaler never fires and the third tier -- node-level autoscaling -- is not exercised. A separate high-load diagnostic (`2026-07-13_dynamic-node-offload`, n = 1) raises the cap to 10 replicas and applies a constant 200 RPS workload for 1,200 seconds, deliberately exceeding the six-pod static envelope to trigger Pending pods, dynamic node provisioning, and sustained serverless offload simultaneously.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto),
    [Scenario], [p99 (ms)], [Nodes], [Delay (s)], [Serverless %], [Monthly USD], [SLO Violations],
    [S1 (K8s+HPA)], [6,665.1], [2], [54.8], [0.0%], [219], [78,257],
    [S2 (Serverless)], [1,401.9], [0], [---], [100.0%], [1,110], [12,859],
    [S3 (Reactive)], [874.4], [2], [51.8], [96.5%], [387], [23,913],
    [S4 (Predictive)], [1,393.3], [2], [70.5], [96.5%], [387], [46,245],
  ),
  caption: [Three-tier architecture diagnostic (n = 1, `2026-07-13_dynamic-node-offload`). 200 RPS constant load for 1,200 seconds. Nodes = dynamic nodes provisioned by K3dAutoscaler; Delay = first provisioning delay; Serverless % = share of experiment time with Knative weight > 0. Monthly USD is a directional diagnostic estimate.],
) <tab:dynamic-node-offload>

All three tiers are exercised in this diagnostic. Tier 1 (routing): the hybrid scenarios shift HAProxy weights between K8s and Knative, with S3 and S4 each accumulating over 24,000 serverless weight-time product. Tier 2 (pod scaling): HPA and Algorithm 2 scale replicas from 3 to 10 (the override cap). Tier 3 (node autoscaling): the K3dAutoscaler detects Unschedulable Pending pods and provisions two dynamic workload nodes per run, each recording `pending_detected -> provision_delay_started -> node_created` in the provision event log.

The trade-off between adding nodes and offloading to serverless is visible in the data. S1 (pure Kubernetes with two dynamic nodes but no serverless offload) has the worst p99 (6,665 ms) and success rate (65.6%). S3 (hybrid-reactive with the same two dynamic nodes plus 96.5% serverless time) achieves the best p99 (874 ms). The 51--70-second provisioning delay was absorbed by Knative in S3 and S4 but caused severe latency degradation in S1, where no serverless fallback existed. This demonstrates that dynamic node provisioning alone is not a substitute for serverless offload; the two mechanisms are complementary, and the hybrid architecture's value lies in using both concurrently.

S3 and S4 have identical monthly cost (USD 387/mo) despite different p99 latency, confirming that the cost difference between reactive and predictive modes is negligible at this load. The dynamic-node EC2 cost (USD 0.028 per run, tracked separately from serverless Lambda cost) is the same for all K8s scenarios because all provision the same two nodes. These n = 1 cost projections are *directional diagnostic estimates* and must not be used to claim universal cost superiority.

S4 underperformed S3 in this diagnostic: p99 was 1,393 ms versus 874 ms (+59%), and SLO violations were 46,245 versus 23,913 (+93%). S4 failed the actuator-fidelity validity gate because the measured provisioning delay (70.5 s) plus the 15-second safety margin requires `ceil(85.5 / 15) = 6` forecast steps, but the deployed GRU model outputs only 5 steps (75-second forecast window). Despite delivering 55 predictions at 100% delivery rate, S4 recorded zero proactive scale-up actions (`predictive_count = 0`), meaning the forecasts did not change the actuator behaviour. The 5-step horizon is adequate for the default 60-second provisioning delay estimate but not for the longer delays observed under high load. This finding validates the ADAPT-inspired design direction @adapt2026: the forecast horizon must adapt to the measured provisioning delay rather than remaining static.

== Controller HPO and Holdout Validation

A separate hyperparameter optimization study explored four controller parameters via Optuna TPE screening: `target_cpu_util`, `kp_burn`, `proactive_trend_threshold`, and `proactive_approach_ratio`. The methodological finding from this study — conducted on the pre-fix infrastructure that predates the `2026-07-11_scaling_fix_n1` baseline — is reported here for completeness, but its specific quantitative results are *directional* and are superseded by Bugs 8-13; they are not part of the current baseline and are not used in the comparative evaluation above.

The substantive lesson is methodological rather than numerical: on a shared-resource testbed with high run-to-run variance, no parameter deviation from the default calibration survived holdout validation. Configurations that looked strong on a single run degraded sharply under replication, because they narrowed the Kubernetes safety margin and caused more frequent saturation under high variance. This is consistent with overfitting risks in model selection @cawley2010overfitting and highlights the difficulty of HPO in online systems where each evaluation requires a full experiment under noisy shared-resource conditions @nonstationary2022 @falkner2018bohb. The two-stage methodology (screening followed by robust confirmation) and the surrogate-assisted approach adapt techniques from @kapetanios2022. The conclusion directly shaped the current baseline: the default `target_cpu_util = 0.5` — equivalently the calibrated `r_saturation_per_replica = 33.3` at which S1 saturates at 100 RPS — was retained, and no HPO-tuned deviation is used in the `2026-07-11_scaling_fix_n1` results.

== Discussion

The experimental evaluation validates both the mechanistic correctness of the hybrid architecture and, under the correctly bounded infrastructure, a clear performance advantage for hybrid routing over pure Kubernetes.

Several mechanisms were validated. The GRU model meets its accuracy target on synthetic data, with a validation RMSE of 4.75% after hyperparameter optimization and an MAE of 4.91%, at an inference latency of approximately 40 ms; on real ClarkNet traces the error is substantially higher (RMSE 17.78%, MAPE 18.74%), so real-traffic prediction is a partial validation. The routing controller correctly implements the priority-based decision framework, exhibiting all four action types, and the corrected predictive mechanism fired 9 PREDICTIVE actions in the S4 diagnostic run, provisioning Kubernetes capacity proactively.

For the hybrid-versus-pure-Kubernetes comparison (H1), the result is now positive and large: S4 reduced p99 latency by 95.1% (2,421.3 ms -> 118.2 ms) and SLO violations by 98.5% (6,717 -> 104) relative to S1. The previous negative finding was an infrastructure artifact (un-enforced CPU limits and S1 dynamic-node over-provisioning), not a property of the hybrid mechanism. H1 is *confirmed at n = 1*.

For the predictive-versus-reactive comparison (H2), the clean paired experiment (n = 5, full treatment delivery) finds S4 mean p99 128.5 ms versus 136.6 ms for S3 (mean difference -8.1 ms, 95% CI [-36.7, +14.5] ms, p = 0.38). The effect direction is in S4's favor -- a reversal from the earlier confounded comparison (+10.0 ms) achieved by correcting the scaling calibration from alpha = 1/r_saturation to alpha = 1/r_effective. However, the effect is small (d = -0.241) and not statistically significant. A secondary finding shows S4 has 56% fewer SLO violations (d = -0.535, medium effect), suggesting the proactive mechanism improves tail-latency consistency even when the mean p99 difference is modest. H2 is *not statistically supported*, but the evidence is directionally consistent and the mechanism is now cleanly testable.

Two caveats bound these conclusions. First, the n = 1 four-scenario diagnostic provides directional mechanism evidence but no inferential statistics. Second, the n = 5 paired comparison, while clean and fully delivered, has insufficient statistical power to detect a small effect (d = -0.241) at alpha = 0.05. A larger sample (n >= 20) would be needed to confirm or refute H2 with adequate power.

Taken together, the results support H1 (hybrid routing outperforms pure Kubernetes, confirmed at n = 1) and provide directionally favorable but non-significant evidence for H2 (predictive scaling shows a small latency advantage and a medium SLO-violation reduction over reactive scaling). The calibration repair demonstrated that the original scaling model's double-counted safety margin was the root cause of S4's apparent underperformance, not the controller design. Recent work on uncertainty-aware autoscaling @aapa2025 and delay-derived planning horizons @adapt2026 provides design directions for further improvement, while benchmark studies @rayscale2026 show that even advanced autoscalers struggle to outperform well-calibrated baselines on cost.
