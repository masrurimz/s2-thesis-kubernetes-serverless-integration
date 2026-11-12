// Chapter 4 — Results and Discussion
// Numbers in this chapter come from results/claims/FINAL_NUMBERS.md and the
// six experiment bundles listed below. Earlier bundles (February 2026 and
// 2026-07-08/10) are invalidated by Bugs 1–13 documented in
// results/claims/INCONSISTENCIES.md and are not used.
#import "figures.typ": *
#import "headings.typ": H, cap

= #H("ch4")

This chapter presents the experimental results for the hybrid Kubernetes-serverless architecture with GRU-based workload prediction.
The chapter organizes the results into sections on GRU model performance, system mechanism validation, the comparative evaluation across deployment scenarios, cost analysis, and a discussion.
Every quantitative claim in this chapter comes from an experiment listed in Appendix E, which maps each name used here to its result folder.
_Important caveat:_ the four-scenario comparative and cost results come from the four-scenario diagnostic, a single run per scenario.
This diagnostic is an *n = 1* run (H1).
These results are framed as diagnostic rather than confirmatory.
Six infrastructure fixes (Bugs 8-13) invalidated all earlier experiment bundles (February and July 8-10, 2026).
These fixes were (1) enforced node CPU limits and (2) recalibrated `r_saturation_per_replica`.
They also added (3) a fairness cap on Kubernetes replicas and (4) calibration tooling.
Finally, they added (5) a GRU-server hard gate and (6) separation of prediction from routing.
The predictive-versus-reactive comparison (H2) rests on one pre-registered confirmatory batch of 10 pairs (@sec:h2).
Earlier paired batches, including a July batch that reached p = 0.0312 with a predictor that cannot be verified, are summarized in @sec:h2-history.
The predictor evidence also includes the representation search and the crossing-target probes of 2026-09-13, reported with the GRU results in this chapter.

== #H("ch4-gru") <sec:gru-model>

The prediction model is trained and evaluated under a leak-free chronological protocol.
ClarkNet is resampled to 15 seconds and scaled by the same factor the replay applies, so the model trains at the amplitude it later serves.
The training, validation, and test portions are separated by an embargo of `sequence_length + horizon - 1` samples.
The normalisation statistics come from the training portion alone.
No input or target window crosses a boundary.
Hyperparameters and the epoch budget are selected on the validation portion.
The model is refitted on the training and validation portions at that budget.
The test portion is scored once per seed.
The replay window, 1995-09-02 04:35:30 to 04:55:00 UTC, lies inside the held-out test portion.
The model never trains on the traffic it later serves.
The deployment arm therefore serves out-of-sample load.
The training and validation regions contain no weekend buckets.
The test region is 81.9% weekend, so performance is reported per day type.
Across the split the level falls from 45.70 to 34.08 counts per 15 s bucket.
This equals 3.05 to 2.27 RPS.

The Tree-structured Parzen Estimator search @optuna2019 selected a two-layer network with 256 hidden units and a 30-sample input window.
It selected head dropout 0.055 and a learning rate of $1.53 times 10^(-4)$ at a frozen budget of 23 epochs.
Table @tab:gru-performance reports the held-out accuracy over three seeds.
The baselines scored on identical windows.

#figure(
  kind: table,
  table(
    columns: (auto, auto),
    [Metric], [Value],
    [Holdout RMSE], [29.635 $\pm$ 0.016],
    [Holdout MAE], [22.486 $\pm$ 0.079],
    [RMSE as percent of mean load], [39.6%],
    [Skill against persistence], [0.216],
    [Upper-envelope coverage on rising targets], [0.921],
    [Rolling-origin RMSE over the test region], [29.039 $\pm$ 6.893],
    [Persistence baseline RMSE], [37.813],
    [Linear trend baseline RMSE], [46.534],
    [Seasonal naive baseline RMSE], [53.688],
    [Linear autoregression, same window, RMSE], [29.465],
    [Inference latency (median, September bundle)], [4.0 ms (p95 5.1 ms)],
  ),
  caption: [GRU model performance under the leak-free protocol],
) <tab:gru-performance>

Two conclusions follow, and the second is uncomfortable.
First, the forecast carries real signal.
It reduces error by 21.6 percent against persistence.
The reduction is stable across seeds (standard deviation 0.016).
The model transfers to synthetic archetypes it never saw (spike 26.58, ramp 24.27, periodic 25.42, stationary 4.74).
A rolling-origin pass over the test region reproduces the same level, 29.039 against 29.635.
Second, the network does not beat a linear autoregression on the same 30-sample window: 29.635 against 29.465.
No accuracy advantage over a linear model may therefore be claimed at 15-second resolution.
The absolute error is far above the pre-registered target.
RMSE is 39.6 percent of the mean load against a target of 10 percent.
This error gap is a property of the task rather than the network.
A persistence forecast repeats the last observation.
It already reaches 50.5 percent of the mean load at this resolution.

A representation search then asked whether any input or target representation beats that linear model.
Twelve levers were specified against the per-fold autoregression under the leak-free fold protocol (Appendix E).
All twelve have records.
None beats the linear model.
Selection-fold skill ranges from -0.01 percent for `robust_scale`, which is parity to the fourth decimal, to -5.08 percent for `calendar`.
The closest lever is `nlinear` at -0.30 percent, with a Diebold-Mariano p of 0.29.
Parity holds within every day type.
Parity also holds on aggregate.
For `nlinear` against the autoregression, Friday evening reaches 46.0 against 45.6.
Saturday reaches 27.8 against 27.9.
Sunday reaches 25.2 against 25.3.
Monday reaches 27.8 against 27.7, in RPS at the served amplitude.
`nlinear` beats the autoregression on the test region and still fails the selection gate.
The selection folds decide.
The disclosed conclusion is that the deployed point predictor should be the linear autoregression.
The network's parity is a limitation of this thesis, not a hidden fact.

Two further probes bound the deployment choice.
First, coarser sampling lowers absolute error for any model.
At 60-second buckets, the fold error falls from 36.69 to 25.18 for the autoregression.
For the network, it falls from 36.69 to 25.30.
These errors are in RPS at the served amplitude.
The target becomes coarser, and the wall-clock horizon grows from 135 to 180 seconds.
This is an interval and horizon change, not a modelling win.
Second, a capacity-relative target detects capacity crossings where the point forecast does not (Appendix E).
Crossing recall is 0.988 $plus.minus$ 0.009, against 0.008 to 0.042 for the autoregression plus threshold and 0.119 to 0.163 for persistence.
The raw head is overconfident (per-step Brier 0.236 against the 0.049 linear reference).
An isotonic map was fitted per fold on that fold's inner-validation steps only.
Calibrated Brier falls to 0.043, under the reference.
The decision rule for this target is recall at a bounded false-alarm rate.
At the 0.80 recall target, the calibrated operating point sits at threshold 0.45.
It has precision 0.543, false-alarm rate 0.210, and mean lead 3.9 steps, about 58 seconds.
The labels exist only where the capacity ceiling is approached, which is the code default of six replicas rather than the paired configuration's ten.

An operational finding shaped the design of the predictive controller.
During live experiments the GRU predictions lagged behind actual load surges.
The forecast therefore feeds Algorithm 2's Kubernetes replica planning through an upper envelope.
Algorithm 1 routes from observed load, ready-replica capacity, and SLO status.
The forecast does not set the routing split.
Under the leak-free model the reported confidence is 0.6.
The score is derived from the ratio of validation RMSE to mean load.
That ratio now exceeds the 0.15 threshold, so the score fell from 0.8 to 0.6.
The score takes only these two values (current predictor). The July diagnostic logged values from 0.72 to 0.89 under an older predictor.
Algorithm 1 compares it with a 0.5 threshold, and both values pass.
Algorithm 2 does not check it.
The threshold therefore never blocks a forecast, and the score does not vary within a run.

The synthetic arm of the same test setup re-derives the pre-registered accuracy target under the identical protocol.
The study bundle reports its result rather than mixing it into the table above.

== #H("ch4-phasea1")

Phase A1 validated the correct operation of the individual system mechanisms under a controlled ramp-load profile. It ran the earlier priority-ladder routing controller, which the capacity-driven V3 controller later replaced. Over the experiment duration the routing controller made 18 decisions. These decisions exhibited all four action types in their correct priority order: SCALE_OUT (7), MAINTAIN (8), OPTIMIZE_COST (2), and PREDICTIVE (1).

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
  caption: [Routing-controller decision distribution (Phase A1)],
) <tab:phase-a1-decisions>

The experiment validated weight shifting. Traffic weights moved from 100/0 (pure Kubernetes) through successive scale-out steps to 50/50 (maximum serverless engagement) as tail latency exceeded the SLO threshold. Each step shifted the split by ten percentage points. The experiment validated the PREDICTIVE action while the system was in a healthy state (p99 = 146 ms). The GRU predicted a 47% workload increase with 72% confidence, and the controller triggered PREDICTIVE to maintain the 50/50 split. This preserved serverless readiness before any SLO violation occurred. With that earlier controller the forecast acted on routing. The V3 controller used in all paired runs does not (Chapter 3).

== #H("ch4-comparative")

The comparative evaluation compares four deployment scenarios: S1 (Kubernetes with HPA), S2 (serverless-only), S3 (hybrid with reactive routing), and S4 (hybrid with predictive replica scaling).
All scenarios replayed the ClarkNet HTTP trace at a mean of 73 requests per second (peak 164 RPS).
Each scenario used a calibrated node capacity of Docker `--cpus=1.0` per workload node (2.0 CPU total).
It set `max_k8s_replicas = 6` to schedulable capacity and used no per-pod CPU limits.
These are *n = 1 diagnostic* results from the four-scenario diagnostic.
The four-scenario comparison (H1) was later replicated at n = 5, as reported below.
The S3-versus-S4 paired comparison (H2) follows in @sec:h2.
All four scenarios ran on this fixed infrastructure, so the comparison is like-for-like within a single bundle.
The four-scenario bundles of July 8-10 are not used, because in them the S1 and S2 runs and the S3 and S4 runs came from different controller configurations.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    [Scenario], [p99 (ms)], [SLO Violations], [SLO Rate], [Time in serverless (%)], [PREDICTIVE],
    [S1 (K8s+HPA)], [2,421.3], [6,717], [7.66%], [0.0%], [0],
    [S2 (Serverless)], [77.7], [19], [0.02%], [100.0%], [0],
    [S3 (Reactive)], [98.8], [3], [0.00%], [31.8%], [0],
    [S4 (Predictive)], [118.2], [104], [0.12%], [24.7%], [9],
  ),
  caption: [Per-scenario summary (n = 1 diagnostic)],
) <tab:scenario-summary>

The four scenarios separate into two regimes.
S1 (pure Kubernetes with HPA) saturates under the ClarkNet load.
Its p99 reaches 2,421.3 ms and it accrues 6,717 SLO violations (7.66% SLO violation rate), far exceeding the 200 ms SLO threshold.
The other three scenarios keep the p99 well under the SLO.
S2 (serverless-only) reaches 77.7 ms, S3 (hybrid-reactive) reaches 98.8 ms, and S4 (hybrid-predictive) reaches 118.2 ms.
Their SLO violation rates are at or near zero (0.02%, 0.00%, and 0.12% respectively).
Two directed comparisons assess the hybrid scenarios.
One compares the predictive scenario against the reactive scenario (S4 vs S3).
The other compares the hybrid predictive scenario against pure Kubernetes (S4 vs S1).
Only a single run is available per scenario for this table.
No inferential statistics (t-tests, effect sizes, confidence intervals) are computed here.
The S4-vs-S1 verdict is a descriptive *n = 1 diagnostic*.
The S4-vs-S3 comparison (H2) uses the paired design of @sec:h2.
In the table, the SLO threshold is p99 < 200 ms.
SLO Violations and SLO Rate are for the single run.
Time in serverless is the share of run time with a Knative weight above zero. The traffic share, computed as the HAProxy weight-time product, is 6.1% for S3 and 3.0% for S4.
PREDICTIVE counts weight increases made while predicted_upper exceeded the observed load. The label does not change the split (Chapter 3).
The count is low because the label needs a load rise above 3 RPS per cycle, load above 80% of capacity, and a predicted value above the observed load.
In this run 8 of the 9 PREDICTIVE labels came from the observed-load extrapolation, with the GRU forecast below the observed load.
Over the 1,200 s experiment (about 80 control cycles), only 9 cycles produced a PREDICTIVE label.
Most cycles were within ready capacity (MAINTAIN or RECOVERY).

The four-scenario replication ran on 2026-08-08 and 2026-08-09 (Appendix D). Its bundle holds no analysis file, so every statistic here was recomputed from the 20 run results.
It ran 4 scenarios, 5 runs each (20 clean runs).
All validity gates passed (5/5 per scenario), and treatment fidelity was delivered in every S4 run.
The S4 arm ran before the leak-free GRU of @sec:gru-model was trained on 2026-09-10, so it measures an earlier predictor.
In the daemon log of the first S4 run, the point forecast is 76.2 RPS and the upper envelope 85.9 RPS, about 10 RPS apart. The leak-free model forecasts 55 to 60 RPS for the same load. The S1 and S2 comparisons in this batch therefore hold for the architecture, not for the forecaster of @sec:gru-model.
Per-scenario mean p99 was S1 110.3 ms, S2 79.7 ms, S3 151.6 ms, and S4 99.1 ms.
SLO violations summed over the five runs were S1 253, S2 2, S3 1,998, and S4 92 (per-run means 50.6, 0.4, 399.6, and 18.4).
The replication did not reproduce the n = 1 diagnostic's S1 saturation.
The reason is the replica cap.
The n = 1 diagnostic used `max_k8s_replicas = 6`, which forced pure Kubernetes to saturate (p99 2,421.3 ms).
The replication used the calibration override `max_k8s_replicas = 10`.
With that headroom, HPA alone covered the ClarkNet load.
S1 did not saturate and therefore did not reproduce at n = 5.
S4 vs S1 was -10.2% with p = 0.151 (not significant).
This is an important methodological finding.
The hybrid's advantage over pure Kubernetes appears when the baseline is capacity-constrained, not when HPA has ample headroom.

#figure(
  fig-p99-boxplot(),
  caption: [Per-scenario p99 latency (n = 5 four-scenario replication)],
) <fig:p99-box-n5>

#figure(
  fig-slo-violations(),
  caption: [Mean SLO violations per run in the four-scenario replication (5 runs per scenario)],
) <fig:slo-violations-n5>

=== #H("ch4-h2") <sec:h2>

H2 predicts that predictive replica scaling (S4) gives lower p99 latency than reactive scaling (S3).
The test is a confirmatory batch of 10 counterbalanced S3/S4 pairs (20 runs), run on 2026-09-20 and pre-registered, with its design and test fixed before the first run.
Its primary endpoint is the paired difference in p99 latency, tested one-sided with a paired permutation test.
All S4 runs used the ClarkNet-trained GRU of @sec:gru-model, which each run manifest names.

The batch before it had shown p99 climbing with host CPU load (@sec:h2-history), so this one ran behind a host-load gate.
That gate is coarse.
It reads a single sample before each run (a ratio of 0.07 here, against a warning threshold of 0.5) and stops watching once the run starts.
Load did rise during the runs; the mean host CPU-busy share was 0.14 to 0.27 per run, and the peak passed 0.5 in 7 of 20 runs.
All 20 runs passed the validity gates, and @tab:h2-primary reports the result.

#figure(
  kind: table,
  table(
    columns: (auto, auto),
    [Statistic], [Value],
    [S3 mean p99 (ms)], [160.4],
    [S4 mean p99 (ms)], [146.8],
    [Mean difference (ms)], [-13.6],
    [95% paired CI (ms)], [-63.5 to +35.6],
    [One-sided permutation p], [0.307],
    [Paired Cohen's d], [-0.16 (negligible)],
    [Pairs won by S4], [5 of 10],
  ),
  caption: [Pre-registered paired S4-vs-S3 comparison (10 pairs, 2026-09-20)],
) <tab:h2-primary>

S4 was 13.6 ms faster on average, but the 95% interval spans zero and p = 0.307.
S4 won 5 of 10 pairs.
H2 is therefore not supported on the pre-specified primary p99 test.

Two estimates put this result in context.
First, pooling all 25 pairs that ran the ClarkNet-trained predictor (this batch and the two batches of 2026-09-13) gives -16.5 ms (95% CI [-188.6, +184.5], one-sided p = 0.448, d = -0.03).
Second, the batch was pre-registered because an interim estimate looked promising.
That estimate used the eight pairs of the 2026-09-13 confirmatory batch with peak host load below 40% (-101.3 ms, p = 0.039).
It did not survive the pre-registered batch, which shows that it came from choosing the subset after seeing the data.

=== #H("ch4-h2-history") <sec:h2-history>

Eight batches compared S3 and S4 before the pre-registered batch.
@tab:h2-history lists each one with the reason it is not the H2 result, and @fig:replication-batches plots the batches that ran with the final controller configuration.
Two further batches from 2026-08-07 are left out, because their result files were deleted before they were committed.

#[
#set par(justify: false)
#figure(
  kind: table,
  table(
    columns: (1.2fr, auto, auto, auto, 2fr),
    align: (left, center, center, center, left),
    [Batch], [Pairs], [Mean difference (ms)], [p], [Why it is not the H2 result],
    [Pre-calibration (2026-07-11)], [5], [+10.0], [--], [Replica targets counted the safety margin twice, so S4 sized replicas exactly like S3],
    [Initial (2026-07-12)], [5], [-8.1], [0.38], [Five-step (75 s) forecast horizon and an untuned reactive baseline],
    [July (2026-07-14)], [5], [-62.5], [0.0312], [The manifest names no predictor, and the model deployed then was trained on synthetic data (Appendix B)],
    [August A (2026-08-08)], [5], [-4.0], [0.436], [Predictor trained before the leak-free protocol of @sec:gru-model],
    [August B (2026-08-08)], [5], [-58.0], [0.062], [Same predictor as August A],
    [Four-scenario replication (2026-08-09)], [5 runs per arm], [-52.5], [0.032], [Unpaired runs with the same earlier predictor; the Welch test gives p = 0.097],
    [September pair (2026-09-13)], [5], [+153.3], [0.656], [Host load not recorded; a 10-pair batch followed the same day],
    [First confirmatory (2026-09-13)], [10], [-104.2], [0.168], [p99 rose with host CPU load (r = 0.69); the three slowest runs had CPU-busy peaks of 66 to 100%],
  ),
  caption: [Earlier S4-vs-S3 batches. A negative difference favours S4.],
) <tab:h2-history>
]

#figure(
  image("../figures/fig04_6_replication_batches.png", width: 90%),
  caption: [S4-vs-S3 p99 difference with 95% confidence interval for each batch run with the final controller configuration],
) <fig:replication-batches>

Two earlier batches reached p < 0.05: the July batch and the Mann-Whitney test of the four-scenario replication.
Neither ran the ClarkNet-trained predictor, and the three batches that did run it found no significant difference.
The step from the initial batch to the July batch also changed three things at once.
The forecast horizon grew from 75 s to 135 s, node consolidation was added, and the reactive baseline was tuned.
Even if the July gain were real, it could not be credited to any one of them.

=== #H("ch4-s4vs1")

With the infrastructure correctly bounded (`--cpus=1.0` per node enforced, `max_k8s_replicas = 6`), pure Kubernetes (S1) saturates as designed under the ClarkNet load. The hybrid predictive scenario provides a large improvement (@tab:s4-vs-s1).

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto),
    [Metric], [S1 (K8s+HPA)], [S4 (Predictive)], [Improvement],
    [p99 latency (ms)], [2,421.3], [118.2], [-2,303.1 (-95.1%)],
    [SLO violations], [6,717], [104], [-6,613 (-98.5%)],
    [SLO violation rate], [7.66%], [0.12%], [-7.54 pp],
  ),
  caption: [Hybrid predictive (S4) versus pure Kubernetes (S1)],
) <tab:s4-vs-s1>

The hybrid predictive scenario reduces p99 latency by 95.1% (from 2,421.3 ms to 118.2 ms) and SLO violations by 98.5% (from 6,717 to 104) relative to pure Kubernetes.
This reverses the earlier negative finding.
The previous H1 result (S4 worse than S1) was an artifact of Bugs 8 and 11.
Node CPU limits were never enforced.
Pods consumed the full 16-core host.
S1's HPA provisioned dynamic nodes (4.0 CPU vs 2.0 CPU for S3/S4).
As a result, S1 never saturated.
With `--cpus=1.0` per node enforced and replicas capped at schedulable capacity, S1 saturates as intended and hybrid routing (S4) provides a clear benefit.
H1 is directionally supported at n = 1.
A single run cannot establish statistical significance.



== #H("ch4-cost")

Cost analysis maps the local testbed to equivalent cloud services. It maps Kubernetes HPA pods to a managed control plane plus compute nodes, and Knative concurrency to provisioned function concurrency. It then projects a unified monthly cost from measured resource consumption. The projections below come from the n = 1 diagnostic baseline and are single-run diagnostic estimates.

The cost proxy is a model, not a billing observation.
Break-even analyses distinguish the workload rates at which serverless and VM-backed capacity change relative advantage @skyrise2025.
Billing and scheduling granularity can inflate measured serverless resource cost beyond raw consumption @demystifying2025.
Keeping serverless instances warm adds CPU and memory overhead @highcost2025, which a hybrid cost comparison has to account for.
These anchors support reporting the proxy directionally.
They support retaining the paired equal-cost result rather than claiming universal savings.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto),
    [Scenario], [Nodes base→peak (dyn-hrs)], [Serverless reqs (PC)], [Total/mo = EKS+EC2+Lambda], [USD/1M SLO-OK],
    [S1 (K8s-only)], [2→2 (0)], [0 (0)], [USD 132 = 72+60+0], [USD 0.79],
    [S2 (Serverless)], [0→0], [87,840 (8)], [USD 395 = 0+0+395], [USD 2.19],
    [S3 (Hybrid-reactive)], [2→2 (0)], [5,354 (1)], [USD 147 = 72+60+15], [USD 0.81],
    [S4 (Hybrid-predictive)], [2→2 (0)], [2,666 (1)], [USD 143 = 72+60+11], [USD 0.79],
  ),
  caption: [AWS monthly cost projection (n = 1 diagnostic)],
) <tab:cost-analysis>

S1 is the cheapest scenario (USD 132/mo) but fails the SLO catastrophically (p99 = 2,421 ms, 7.66% violation rate). Its low cost reflects poor service rather than efficiency. S2 (serverless-only) is the most expensive (USD 395/mo) but achieves the best raw latency (77.7 ms). In the table, Nodes is base→peak with dynamic node-hours in parentheses; Total/mo decomposes into EKS+EC2+Lambda. These n = 1 cost projections are *directional diagnostic estimates only*. They must not be used to rank S3 and S4 or to claim monthly savings. The USD/1M SLO-OK column normalizes the total monthly cost by the count of SLO-satisfying requests.

#figure(
  fig-cost-comparison(),
  caption: [AWS monthly cost projection per scenario],
) <fig:cost-comparison>

== #H("ch4-node")

The n = 1 diagnostic baseline caps `max_k8s_replicas = 6` to match the two-node schedulable capacity. The K3dAutoscaler never fires, and the third tier (node-level autoscaling) is not exercised. A separate high-load three-tier diagnostic (n = 1) raises the cap to 10 replicas and applies a constant 200 RPS workload for 1,200 seconds. It deliberately exceeds the six-pod static envelope to trigger Pending pods, dynamic node provisioning, and sustained serverless offload simultaneously.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto),
    [Scenario], [p99 (ms)], [Nodes], [Delay (s)], [Time in serverless (%)], [Monthly USD], [SLO Violations],
    [S1 (K8s+HPA)], [6,665.1], [2], [54.8], [0.0%], [219], [78,257],
    [S2 (Serverless)], [1,401.9], [0], [---], [100.0%], [1,110], [12,859],
    [S3 (Reactive)], [874.4], [2], [51.8], [96.5%], [387], [23,913],
    [S4 (Predictive)], [1,393.3], [2], [70.5], [96.5%], [387], [46,245],
  ),
  caption: [Three-tier architecture diagnostic (n = 1)],
) <tab:dynamic-node-offload>

This diagnostic exercises all three tiers.

- Tier 1 (routing): the hybrid scenarios shift HAProxy weights between Kubernetes and Knative. S3 and S4 each accumulate over 24,000 serverless weight-time product.
- Tier 2 (pod scaling): HPA and Algorithm 2 scale replicas from 3 to 10 (the override cap).
- Tier 3 (node autoscaling): the K3dAutoscaler detects unschedulable Pending pods and provisions two dynamic workload nodes per run. Each run records the provision event sequence (pending detected, then provisioning started, then node created) in the provision event log.

In the table, Nodes counts the dynamic nodes provisioned by the K3dAutoscaler.
Delay is the first provisioning delay.
Time in serverless (%) is the share of experiment time with Knative weight above zero.
Monthly USD is a directional diagnostic estimate.

#figure(
  fig-node-provisioning(),
  caption: [Dynamic node provisioning timeline],
) <fig:node-provisioning>

The trade-off between adding nodes and offloading to serverless is visible in the data. S1 (pure Kubernetes with two dynamic nodes but no serverless offload) has the worst p99 (6,665 ms) and success rate (65.6%). S3 (hybrid-reactive with the same two dynamic nodes plus 96.5% serverless time) achieves the best p99 (874 ms). Knative absorbed the 51--70-second provisioning delay in S3 and S4 in this July diagnostic; the later batches measured delays of 50--125 s. The same delay caused severe latency degradation in S1, where no serverless fallback existed. Dynamic node provisioning alone is not a substitute for serverless offload. The two mechanisms are complementary. The hybrid architecture gains its value by using both concurrently.

S3 and S4 have identical monthly cost (USD 387/mo) despite different p99 latency. The cost difference between reactive and predictive modes is therefore negligible at this load. The dynamic-node EC2 cost (USD 0.028 per run, tracked separately from serverless Lambda cost) is the same for all K8s scenarios because all provision the same two nodes. These n = 1 cost projections are *directional diagnostic estimates*. They must not be used to claim universal cost superiority.

S4 underperformed S3 in this diagnostic.
S4's p99 was 1,393 ms versus 874 ms (+59%), and its SLO violations were 46,245 versus 23,913 (+93%).
S4 failed the actuator-fidelity validity gate.
The measured provisioning delay (70.5 s) plus the 15-second safety margin requires `ceil(85.5 / 15) = 6` forecast steps.
The deployed GRU model outputs only 5 steps (75-second forecast window).
S4 delivered 55 predictions at 100% delivery rate, yet it issued zero PREDICTIVE labels.
The forecasts did not change the actuator behaviour.
The 5-step horizon is adequate for the default 60-second provisioning delay estimate but not for the longer delays observed under high load.
This finding is consistent with the premise of ADAPT @adapt2026: the forecast horizon must adapt to the measured provisioning delay rather than remaining static.

=== #H("ch4-varload")

The constant-load diagnostic confirms the mechanism but cannot test predictive scaling.
Constant traffic gives the forecast nothing to anticipate.
A ClarkNet variable-load diagnostic (n = 1) uses the real ClarkNet trace (30--164 RPS ramps, mean 73 RPS).
It sets `max_k8s_replicas = 10` and uses the extended 9-step GRU horizon (135 s window).
ClarkNet peaks naturally exceed the six-pod static envelope.
They trigger dynamic nodes without artificial load inflation.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto, auto),
    [Scenario], [p99 (ms)], [Nodes], [Time in serverless], [Predictions], [Pred], [Pro. SU], [Monthly USD],
    [S1 (K8s+HPA)], [118.4], [2], [0.0%], [---], [---], [---], [187],
    [S2 (Serverless)], [79.0], [0], [100.0%], [---], [---], [---], [403],
    [S3 (Reactive)], [103.9], [2], [21.2%], [---], [---], [---], [196],
    [S4 (Predictive)], [108.3], [2], [17.6%], [55], [4], [1], [196],
  ),
  caption: [ClarkNet variable-load experiment (n = 1)],
) <tab:clarknet-dynamic-node>

Under variable load, the GRU forecast produced proactive actions for the first time.
The run issued four PREDICTIVE labels and one proactive replica scale-up before the observed load reached the target. PREDICTIVE labels do not change the split (Chapter 3).
All validity gates passed: the forecast horizon was sufficient and all 55 predictions were delivered.
In the table, Pred counts PREDICTIVE labels and Pro. SU counts proactive replica scale-ups. Monthly USD is a directional diagnostic estimate.
S4 used 17.6% serverless time versus S3's 21.2%.
The proactive scale-up added Kubernetes capacity earlier and reduced serverless dependency.
S3 achieved a slightly better p99 (103.9 ms vs 108.3 ms, +4.3%) and fewer SLO violations (14 vs 44), but n = 1 is not conclusive.
The identical monthly cost (USD 196/mo) confirms no cost penalty for the predictive mode at this load.

=== #H("ch4-consol")

The node autoscaler implements cluster-autoscaler-style consolidation, following the Kubernetes Cluster Autoscaler's default 50% utilization threshold @k8sca-faq.
A dynamic node is a candidate for removal when three conditions hold.
Its CPU request utilization falls below 50% of allocatable capacity.
All workload pods on the node can be rescheduled onto other workload nodes.
The node has remained underutilized for at least 90 seconds.
The `kubectl drain` command evicts pods to other nodes before the node container is deleted.
A 120-second cooldown prevents cascading deletions.

Under the same ClarkNet variable-load trace, consolidation produced the strongest S3-versus-S4 differentiation in the project:

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    [Scenario], [p99 (ms)], [SLO Violations], [Nodes Provisioned], [Scale-Downs], [Monthly USD],
    [S3 (Reactive)], [228.4], [1,085], [3], [3], [162],
    [S4 (Predictive)], [113.0], [40], [5], [3], [170],
  ),
  caption: [ClarkNet variable-load with node consolidation (n = 1)],
) <tab:clarknet-consolidation>

S4 achieved 50.5% lower p99 (113 ms vs 228 ms).
It achieved 96.3% fewer SLO violations (40 vs 1,085) than S3.
This came at a 5% cost premium (USD 170/mo vs 162/mo).
The mechanism is as follows.
S3's reactive controller aggressively consolidated all dynamic nodes when utilization dropped.
This caused severe latency spikes when ClarkNet load returned and no Kubernetes capacity was available.
S4's GRU forecast predicted load ramps and maintained Kubernetes capacity.
This prevented excessive consolidation.
The scale-down provision events record a node utilization of 0.3 against a 0.5 threshold, with one pod on the node, for each consolidation.
This confirms the utilization-based trigger fired correctly.
The bidirectional autoscaling loop is visible in the event log.
A node is created when pending pods are detected.
It is then consolidated when load drops.
It is re-provisioned when load rises again.
In the table, Scale-Downs counts node consolidation events, and Monthly USD is a directional diagnostic estimate computed from the actual per-node lifetime in the provision event timestamps.
These results come from the node-consolidation diagnostic.

== #H("ch4-hpo")

A separate hyperparameter optimization study explored four controller parameters via Optuna TPE screening: `target_cpu_util`, `kp_burn`, `proactive_trend_threshold`, and `proactive_approach_ratio`.
The study ran on the pre-fix infrastructure that predates the n = 1 diagnostic baseline.
The methodological finding is reported here for completeness.
Its specific quantitative results are *directional* and are superseded by Bugs 8-13.
They are not part of the current baseline.
They are not used in the comparative evaluation above.

The substantive lesson is methodological rather than numerical. On a shared-resource testbed with high run-to-run variance, no parameter deviation from the default calibration survived holdout validation. Configurations that looked strong on a single run degraded sharply under replication. They narrowed the Kubernetes safety margin and caused more frequent saturation under high variance. This is consistent with overfitting risks in model selection @cawley2010overfitting. It also highlights the difficulty of HPO in online systems, where the objective drifts over time @nonstationary2022 and each evaluation is noisy and costly @falkner2018bohb. In this testbed each evaluation is a full experiment on shared resources. The two-stage methodology (screening followed by confirmation) and the surrogate-assisted approach adapt the calibration to the observed baseline. No HPO-tuned deviation is used in the n = 1 diagnostic results.

== #H("ch4-discussion")

The experimental evaluation validates two things. It validates the mechanistic correctness of the hybrid architecture. Under the correctly bounded infrastructure, it also validates a clear performance advantage for hybrid routing over pure Kubernetes.

The study validated several mechanisms.
The GRU model meets its accuracy target on synthetic data.
On the synthetic arm, it achieves RMSE 5.2% of the mean load under the leak-free protocol.
This meets the target.
On the held-out region of the real deployment trace, it achieves 39.6%.
The target is not met there, and the model matches a linear autoregression on the same input window.
Median inference latency in the September bundle is 4.0 ms.
Real-traffic prediction is therefore a partial validation.
The Phase A1 controller implemented the priority-based decision framework and exhibited all four action types. The V3 controller replaces that framework with a capacity-driven split.
The GRU upper forecast feeds Algorithm 2's replica planning.
The S4 diagnostic run carried 9 PREDICTIVE labels. The labels do not set the split, and the forecast reaches the split only through replica counts.

For the hybrid-versus-pure-Kubernetes comparison (H1), the result is directionally positive at n = 1.
S4 reduced p99 latency by 95.1% (2,421.3 ms -> 118.2 ms).
It reduced SLO violations by 98.5% (6,717 -> 104) relative to S1.
The previous negative finding was an infrastructure artifact (un-enforced CPU limits and S1 dynamic-node over-provisioning).
It was not a property of the hybrid mechanism.
The n = 1 result does not establish inferential significance.
The n = 5 four-scenario replication did not reproduce this advantage.
It used `max_k8s_replicas = 10`, so S1 did not saturate (p99 110.3 ms).
S4 versus S1 was not significant (p = 0.151).
The hybrid's advantage therefore appears when the baseline is capacity-constrained, not when HPA has ample headroom.

For the predictive-versus-reactive comparison (H2), the verdict is: not supported.
The pre-registered confirmatory batch (10 counterbalanced pairs, all 20 runs valid) found S4 mean p99 146.8 ms versus 160.4 ms for S3.
The mean difference is -13.6 ms, with 95% CI [-63.5, +35.6] ms, p = 0.307, and d = -0.16, a negligible effect.
The secondary metrics agree: p95 differs by -0.9 ms and SLO violations by +3.6 per run, both negligible.
Pooling all 25 pairs that ran the ClarkNet-trained predictor gives -16.5 ms (95% CI [-188.6, +184.5] ms, one-sided p = 0.448, d = -0.03).
The earlier July batch found -62.5 ms (p = 0.0312), but its predictor cannot be verified, so @sec:h2-history reports it as history.

Two caveats bound these conclusions.
First, the n = 1 four-scenario diagnostic provides directional mechanism evidence but no inferential statistics for H1.
Second, power is limited at this effect scale.
The paired standard deviation is 484.5 ms over the 25 pairs, and the per-batch values range from 83.6 ms to 1057.3 ms (recomputed from the bundles).
The pre-registered batch ran ten pairs for this reason and still found a negligible difference.
Its primary p99 test was pre-specified.
Its secondary metrics (p95, SLO violations) are not significant after multiplicity correction (corrected p = 1.0) and are reported as descriptive.

Taken together, the results support H1 directionally (the hybrid architecture outperforms the saturated pure Kubernetes baseline at n = 1).
H2 is not supported.
The pre-registered batch found a negligible difference, and the pooled 25-pair estimate of -16.5 ms has a confidence interval spanning zero.
A batch can test H2 only when the predictive arm acts on its forecast.
Runs in which the forecast never changes replica planning measure the reactive controller under an S4 label and cannot separate the two arms.
The calibration repair showed that the original scaling model's double-counted safety margin caused S4's apparent underperformance, not the controller design.
Recent work on uncertainty-aware autoscaling @aapa2025 and delay-derived planning horizons @adapt2026 provides design directions for further improvement.
Benchmark studies @rayscale2026 show that even advanced autoscalers struggle to outperform well-calibrated baselines on cost.
