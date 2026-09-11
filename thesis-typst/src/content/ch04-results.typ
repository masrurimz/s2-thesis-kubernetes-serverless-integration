// Chapter 4 — Results and Discussion
// Numbers in this chapter come from results/claims/FINAL_NUMBERS.md and the
// six experiment bundles listed below. Earlier bundles (February 2026 and
// 2026-07-08/10) are invalidated by Bugs 1–13 documented in
// results/claims/INCONSISTENCIES.md and are not used.
#import "figures.typ": *
#import "headings.typ": H, cap

= #H("ch4")

This chapter presents the experimental results for the hybrid Kubernetes-serverless architecture with GRU-based workload prediction. The chapter organizes the results into sections on GRU model performance, system mechanism validation, the comparative evaluation across deployment scenarios, cost analysis, and a discussion. Every quantitative claim in this chapter is traceable to the consolidated experiment record in the experiment registry. _Important caveat:_ the four-scenario comparative and cost results come from the `2026-07-11_scaling_fix_n1` baseline, which is an *n = 1 diagnostic* run (H1). These results are framed as diagnostic rather than confirmatory. Six infrastructure fixes (Bugs 8-13) invalidated all previous experiment bundles (February and July 8-10, 2026): (1) enforced node CPU limits, (2) recalibrated `r_saturation_per_replica`, (3) a fairness cap on Kubernetes replicas, (4) calibration tooling, (5) a GRU-server hard gate, and (6) separation of prediction from routing. By contrast, the definitive *n = 5* paired experiment (`2026-07-14_clarknet-tuned-paired-n5`, Appendix B) establishes the predictive-versus-reactive comparison (H2). Its primary p99 result is statistically significant (p = 0.030).

== #H("ch4-gru")

The prediction model is trained and evaluated under a leak-free chronological protocol. ClarkNet is resampled to 15 seconds and scaled by the same factor the replay applies, so the model trains at the amplitude it later serves. The training, validation, and test portions are separated by an embargo of `sequence_length + horizon - 1` samples, the normalisation statistics come from the training portion alone, and no input or target window crosses a boundary. Hyperparameters and the epoch budget are selected on the validation portion, the model is refitted on the training and validation portions at that budget, and the test portion is scored once per seed. The replay window lies inside the test portion, so the model is never trained on the traffic it later serves.

The Tree-structured Parzen Estimator search @optuna2019 selected a two-layer network with 256 hidden units, a 30-sample input window, head dropout 0.055, and a learning rate of $1.53 times 10^(-4)$, at a frozen budget of 23 epochs. Table @tab:gru-performance reports the held-out accuracy over three seeds, and the baselines scored on identical windows.

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
    [Inference latency], [~40 ms],
  ),
  caption: cap([GRU model performance under the leak-free protocol], [Kinerja model GRU pada protokol bebas kebocoran]),
) <tab:gru-performance>

Two conclusions follow, and the second is uncomfortable. First, the forecast carries real signal. It reduces error by 21.6 percent against persistence, the reduction is stable across seeds (standard deviation 0.016), and the model transfers to synthetic archetypes it never saw (spike 26.58, ramp 24.27, periodic 25.42, stationary 4.74). A rolling-origin pass over the test region reproduces the same level, 29.039 against 29.635. Second, the network does not beat a linear autoregression on the same 30-sample window: 29.635 against 29.465. No accuracy advantage over a linear model may therefore be claimed at 15-second resolution. The absolute error is also far above the pre-registered target, since RMSE is 39.6 percent of the mean load against a target of 10 percent. The gap is a property of the task rather than of the network: a persistence forecast, which repeats the last observation, already reaches 50.5 percent of the mean load at this resolution.

An operational finding shaped the design of the predictive controller. During live experiments the GRU predictions lagged behind actual load surges. The forecast therefore feeds Algorithm 2's Kubernetes replica planning through a confidence-gated upper envelope. Algorithm 1 routes from observed load, ready-replica capacity, and SLO status. The GRU confidence score gates predictive scaling; it does not directly set the routing split. Under the leak-free model the reported confidence is 0.6, because the score is derived from the ratio of validation RMSE to mean load and that ratio now exceeds the 0.15 threshold. The gate still passes its 0.5 default, so predictive scaling remains enabled, but the score no longer varies within a run.

The synthetic arm of the same harness re-derives the pre-registered accuracy target under the identical protocol, and its result is reported with the study bundle rather than mixed into the table above.

== #H("ch4-phasea1")

Phase A1 validated the correct operation of the individual system mechanisms under a controlled ramp-load profile. Over the experiment duration the routing controller made 18 decisions. These decisions exhibited all four action types in their correct priority order: SCALE_OUT (7), MAINTAIN (8), OPTIMIZE_COST (2), and PREDICTIVE (1).

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
  caption: cap([Routing-controller decision distribution (Phase A1)], [Distribusi keputusan kontroler _routing_ (Phase A1)]),
) <tab:phase-a1-decisions>

The experiment validated weight shifting. Traffic weights moved from 100/0 (pure Kubernetes) through successive scale-out steps to 50/50 (maximum serverless engagement) as tail latency exceeded the SLO threshold. Each step shifted the split by ten percentage points. The experiment validated the PREDICTIVE action while the system was in a healthy state (p99 = 146 ms). The GRU predicted a 47% workload increase with 72% confidence, and the controller triggered PREDICTIVE to maintain the 50/50 split. This preserved serverless readiness before any SLO violation occurred. This is the core contribution of the predictive mechanism: it sustains serverless engagement during healthy periods when a surge is anticipated.

== #H("ch4-comparative")

The comparative evaluation compares four deployment scenarios: S1 (Kubernetes with HPA), S2 (serverless-only), S3 (hybrid with reactive routing), and S4 (hybrid with predictive routing). All scenarios replayed the ClarkNet HTTP trace at a mean of 73 requests per second (peak 164 RPS). Each scenario used a calibrated node capacity of Docker `--cpus=1.0` per workload node (2.0 CPU total), with `max_k8s_replicas = 6` capped to schedulable capacity and no per-pod CPU limits. These are *n = 1 diagnostic* results from the single-run diagnostic baseline. The four-scenario comparison (H1) was subsequently replicated at n = 5, as reported below. The S3-vs-S4 paired comparison (H2) is reported below as a definitive n = 5 experiment. All four scenarios ran on this fixed infrastructure, so the comparison is like-for-like within a single bundle. The superseded July bundles differed: in them, S1/S2 and S3/S4 came from different controller configurations.

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
  caption: cap([Per-scenario summary (n = 1 diagnostic)], [Ringkasan per-skenario (n = 1 diagnostik)]),
) <tab:scenario-summary>

The four scenarios separate into two regimes. S1 (pure Kubernetes with HPA) saturates under the ClarkNet load. Its p99 reaches 2,421.3 ms and it accrues 6,717 SLO violations (7.66% SLO violation rate), far exceeding the 200 ms SLO threshold. The other three scenarios keep the p99 well under the SLO. S2 (serverless-only) reaches 77.7 ms, S3 (hybrid-reactive) reaches 98.8 ms, and S4 (hybrid-predictive) reaches 118.2 ms. Their SLO violation rates are at or near zero (0.02%, 0.00%, and 0.12% respectively). Two directed comparisons assess the role of the hybrid scenarios: the predictive scenario against the reactive scenario (S4 vs S3), and the hybrid predictive scenario against pure Kubernetes (S4 vs S1). Only a single run is available per scenario for this table. No inferential statistics (t-tests, effect sizes, confidence intervals) are computed here. The S4-vs-S1 verdict is a descriptive *n = 1 diagnostic*. The S4-vs-S3 comparison (H2) uses the definitive n = 5 paired design reported in the subsections below. In the table, the SLO threshold is p99 < 200 ms; SLO Violations and SLO Rate are for the single run, and Serverless % is the share of requests routed to Knative. PREDICTIVE counts forecast-driven routing decisions (weight shifts toward serverless), not replica scale-ups. The count is low because PREDICTIVE fires only in a narrow window: a GRU forecast must clear the confidence gate, place the predicted load above the observed load, and produce an actual change to the split, all outside the 15 s cooldown between adjustments. Over the 1,200 s experiment (about 80 control cycles) only 9 cycles satisfied these gates; most cycles were comfortably within the ready replicas' capacity (MAINTAIN or OPTIMIZE_COST) or showed no forecast-driven shift.

The completed four-scenario replication ran on 2026-08-08 and 2026-08-09 (`2026-08-09_clarknet-replay_032257`, Appendix D). It ran 4 scenarios, 5 runs each (20 clean runs). All validity gates passed (5/5 per scenario), and treatment fidelity was delivered in every S4 run. Per-scenario mean p99 was S1 110.3 ms, S2 79.7 ms, S3 151.6 ms, and S4 99.1 ms. SLO violations were S1 253, S2 2, S3 1,998, and S4 92. The replication did not reproduce the n = 1 diagnostic's S1 saturation. The reason is the replica cap. The n = 1 diagnostic used `max_k8s_replicas = 6`, which forced pure Kubernetes to saturate (p99 2,421.3 ms). The replication used the definitive calibration override `max_k8s_replicas = 10`. With that headroom, HPA alone covered the ClarkNet load, and S1 did not saturate and therefore did not reproduce at n = 5. S4 vs S1 was -10.2% with p = 0.24 (not significant). This is an important methodological finding. The hybrid's advantage over pure Kubernetes appears when the baseline is capacity-constrained, not when HPA has ample headroom.

#figure(
  fig-p99-boxplot(),
  caption: cap([Per-scenario p99 latency (n = 5 four-scenario replication)], [Latensi p99 per-skenario (n = 5, replikasi empat skenario)]),
) <fig:p99-box-n5>

#figure(
  fig-slo-violations(),
  caption: cap([SLO violations per scenario (n = 5 replication)], [Pelanggaran SLO per skenario (n = 5, replikasi)]),
) <fig:slo-violations-n5>

=== #H("ch4-h2-initial")

The study ran a counterbalanced paired experiment (n = 5 S3/S4 pairs, the initial paired bundle) to test H2. All 5 pairs delivered complete GRU forecasts (56 eligible prediction cycles per run, 0 failures). The primary endpoint is the paired p99 latency difference. @tab:paired-h2-primary reports the result.

#emph[This section documents the initial clean n = 5 result, obtained with the 5-step (75 s) forecast horizon and an untuned reactive baseline. The definitive result uses the 9-step (135 s) horizon, a tuned reactive baseline, and utilization-based node consolidation. That result is reported in @sec:definitive-h2 below.]

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
  caption: cap([Paired S4-vs-S3 p99 latency comparison (initial n = 5)], [Perbandingan latensi p99 S4-vs-S3 berpasangan (n = 5 awal)]),
) <tab:paired-h2-primary>

The mean difference favors S4 (S4 is 8.1 ms faster on average). The 95% CI [-36.7, +14.5] crosses zero, and the permutation test is not significant (p = 0.38). H2 (predictive latency superiority) is therefore *not statistically supported in this initial experiment; the definitive experiment (@sec:definitive-h2) achieves significance after horizon extension and baseline tuning*. The direction is still consistent with the hypothesis. S4 wins 2 of 5 pairs. Pair 4 drives the mean advantage (S3 = 173 ms, S4 = 112 ms).

A secondary finding is that S4 shows 56% fewer SLO violations on average (100.8 vs 228.2, Cohen's d = -0.535, medium effect). This is also not statistically significant at n = 5 (p = 0.19). Proactive scaling appears to keep p99 below the SLO threshold more consistently, even when the mean p99 difference is small.

=== #H("ch4-calibration")

The clean paired comparison used a corrected scaling model. The original calibration used alpha = 1/r_saturation with a 1.2x buffer. This double-counted the safety margin (target_cpu_util already provides headroom). A forecast of 62 RPS mapped to ceil(62 / 33.3 times 1.2) = 3 replicas. This equals the target from the observed signal, so S4 behaved the same as S3. The corrected model uses alpha = 1/r_effective (= 1 / (r_saturation times target_cpu_util) = 1/16.65) with buffer = 1.0. Now 62 RPS maps to ceil(62 times 0.060) = 4 replicas. This separates the forecast from the observed 45-RPS target of 3.

This repair reversed the effect direction. The earlier (confounded) paired comparison found S4 10 ms *slower* (mean diff +10.0 ms). The clean comparison with the corrected calibration finds S4 8.1 ms *faster* (mean diff -8.1 ms). The reversal shows that the calibration mismatch caused S4's apparent underperformance, not the controller design. However, the effect remains small (d = -0.241) and not statistically significant in this initial experiment. The definitive experiment below shows that this happened because the forecast horizon was too short and the reactive baseline was untuned.

=== #H("ch4-h2-definitive") <sec:definitive-h2>

The initial paired experiment (above) used a 5-step forecast horizon (75 s window), no node consolidation, and a reactive baseline with a 300-second pod-level scale-down cooldown. That cooldown effectively limited S3 to three scale-down actions per run. Later improvements produced the definitive paired bundle (n = 5 counterbalanced pairs). The improvements were an extended 9-step GRU horizon (135 s), utilization-based node consolidation (matching the Kubernetes Cluster Autoscaler's 50% threshold @k8sca-faq), and a tuned reactive baseline (120-second cooldown, 0.75 threshold).

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto),
    [Metric], [S3 (Reactive)], [S4 (Predictive)], [Statistic],
    [Mean p99 (ms)], [188.5], [126.0], [diff -62.5, p = 0.030],
    [95% paired CI (ms)], [--], [--], [-100.9 to -26.2],
    [Paired Cohen's d], [--], [--], [-1.26 (large)],
    [Mean SLO violations], [656], [130], [-80.2%],
    [Monthly cost (USD)], [163], [163], [Identical],
  ),
  caption: cap([Definitive paired S4-vs-S3 comparison (n = 5)], [Perbandingan definitif berpasangan S4-vs-S3 (n = 5)]),
) <tab:paired-h2-definitive>

H2 is *statistically supported*. S4 achieves 33.1% lower mean p99 latency (126.0 ms vs 188.5 ms), with a permutation p-value of 0.030 (below alpha = 0.05) and a large effect size (Cohen's d = -1.26). S4 wins all 5 pairs. The 95% confidence interval [-100.9, -26.2] lies entirely below zero. S4 also shows 80.2% fewer SLO violations (130 vs 656) at identical monthly cost. The GRU forecast triggered 4--5 forecast-driven routing decisions per S4 run. Prediction therefore contributes to the latency advantage rather than consolidation noise. The progression from the initial non-significant result (p = 0.38, d = -0.241) to the definitive significant result (p = 0.030, d = -1.26) shows that forecast horizon adequacy, node consolidation, and reactive-baseline tuning were the decisive factors.

The monthly cost model charges provisioned EC2 nodes sized from average CPU plus Lambda concurrency. It does not itemize per-replica Kubernetes compute. S4 holds five warm replicas to S3's three, so S4 accumulates 9 percent more replica-seconds (7,608 vs 6,980 per run). This added idle capacity is invisible to a node-based model. Under a per-vCPU-second charge at the t3.medium rate, S4's Kubernetes compute would cost about USD 2.2 more per month. The reported identical cost therefore holds only for a model that bills provisioned capacity, not replica-seconds.

#figure(
  fig-paired-perpair(),
  caption: cap([Per-pair p99 latency (definitive paired comparison)], [Latensi p99 per-pasangan (perbandingan berpasangan definitif)]),
) <fig:paired-h2-perpair>

=== #H("ch4-replication") <sec:replication>

To verify repeatability, the study re-triggered the paired experiment twice from the aligned codebase on 2026-08-07. Those two initial replication batches (n = 5 each) were not retained. Their raw result and analysis files were deleted from the working tree before commit, and their numbers survive only as self-referential thesis text. The two batches are therefore excluded from the evidence record.

Two further paired batches ran on 2026-08-08 with fully retained artifacts. RUN1 (n = 5) was null (mean difference -4.0 ms, one-sided permutation p = 0.436). RUN2 (n = 5) was marginal (mean difference -58.0 ms, 95% CI [-161.5, -2.8], one-sided permutation p = 0.062). Both batches retained the S4-favorable direction. Pooled over the two 2026-08-08 batches (n = 10 pairs), the mean difference is -31.0 ms, one-sided permutation p = 0.188, d = -0.32. The full four-scenario replication (4 scenarios, 5 runs each, 20 clean runs) tested the S4-vs-S3 comparison with the pre-specified Welch t-test and with Mann-Whitney U. The Welch test was not significant (p = 0.097). The Mann-Whitney test was significant (p = 0.032) with d = -1.30. The replication is batch-dependent. Some batches reach significance and others do not. The direction is consistently S4-favorable across every batch.

#figure(
  image("../figures/fig04_6_replication_batches.png", width: 90%),
  caption: cap([S4-vs-S3 paired p99 difference across replication batches], [Selisih p99 berpasangan S4-vs-S3 lintas batch replikasi]),
) <fig:replication-batches>

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
  caption: cap([Hybrid predictive (S4) versus pure Kubernetes (S1)], [_Hybrid_ prediktif (S4) versus Kubernetes murni (S1)]),
) <tab:s4-vs-s1>

The hybrid predictive scenario reduces p99 latency by 95.1% (from 2,421.3 ms to 118.2 ms) and SLO violations by 98.5% (from 6,717 to 104) relative to pure Kubernetes. This reverses the earlier negative finding. The previous H1 result (S4 worse than S1) was an artifact of Bugs 8 and 11. Node CPU limits were never enforced (pods consumed the full 16-core host), and S1's HPA provisioned dynamic nodes (4.0 CPU vs 2.0 CPU for S3/S4). As a result, S1 never saturated. With `--cpus=1.0` per node enforced and replicas capped at schedulable capacity, S1 saturates as intended and hybrid routing (S4) provides a clear benefit. H1 is directionally supported at n = 1. A single run cannot establish statistical significance.



== #H("ch4-cost")

Cost analysis maps the local testbed to equivalent cloud services. It maps Kubernetes HPA pods to a managed control plane plus compute nodes, and Knative concurrency to provisioned function concurrency. It then projects a unified monthly cost from measured resource consumption. The projections below come from the n = 1 diagnostic baseline and are single-run diagnostic estimates.

The cost proxy is a model, not a billing observation. Break-even analyses distinguish the workload rates at which serverless and VM-backed capacity change relative advantage @skyrise2025. Billing and scheduling granularity can inflate measured serverless resource cost beyond raw consumption @demystifying2025. Keeping warm instances introduces overhead that affects hybrid cost comparisons @highcost2025. These anchors support reporting the proxy directionally and retaining the paired equal-cost result rather than claiming universal savings.

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
  caption: cap([AWS monthly cost projection (n = 1 diagnostic)], [Proyeksi biaya bulanan AWS (n = 1 diagnostik)]),
) <tab:cost-analysis>

S1 is the cheapest scenario (USD 132/mo) but fails the SLO catastrophically (p99 = 2,421 ms, 7.66% violation rate). Its low cost reflects poor service rather than efficiency. S2 (serverless-only) is the most expensive (USD 394/mo) but achieves the best raw latency (77.7 ms). These n = 1 cost projections are *directional diagnostic estimates only*. They must not be used to rank S3 and S4 or to claim monthly savings. The USD/1M SLO-OK column normalizes the total monthly cost by the count of SLO-satisfying requests.

#figure(
  fig-cost-comparison(),
  caption: cap([AWS monthly cost projection per scenario], [Proyeksi biaya bulanan AWS per skenario]),
) <fig:cost-comparison>

== #H("ch4-node")

The n = 1 diagnostic baseline caps `max_k8s_replicas = 6` to match the two-node schedulable capacity. The K3dAutoscaler never fires, and the third tier (node-level autoscaling) is not exercised. A separate high-load three-tier diagnostic (n = 1) raises the cap to 10 replicas and applies a constant 200 RPS workload for 1,200 seconds. It deliberately exceeds the six-pod static envelope to trigger Pending pods, dynamic node provisioning, and sustained serverless offload simultaneously.

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
  caption: cap([Three-tier architecture diagnostic (n = 1)], [Diagnostik arsitektur tiga _tier_ (n = 1)]),
) <tab:dynamic-node-offload>

This diagnostic exercises all three tiers.

- Tier 1 (routing): the hybrid scenarios shift HAProxy weights between Kubernetes and Knative. S3 and S4 each accumulate over 24,000 serverless weight-time product.
- Tier 2 (pod scaling): HPA and Algorithm 2 scale replicas from 3 to 10 (the override cap).
- Tier 3 (node autoscaling): the K3dAutoscaler detects unschedulable Pending pods and provisions two dynamic workload nodes per run. Each run records the provision event sequence (pending detected, then provisioning started, then node created) in the provision event log.

In the table, Nodes counts the dynamic nodes provisioned by the K3dAutoscaler, Delay is the first provisioning delay, and Serverless % is the share of experiment time with Knative weight above zero; Monthly USD is a directional diagnostic estimate.

#figure(
  fig-node-provisioning(),
  caption: cap([Dynamic node provisioning timeline], [Linimasa _provisioning node_ dinamis]),
) <fig:node-provisioning>

The trade-off between adding nodes and offloading to serverless is visible in the data. S1 (pure Kubernetes with two dynamic nodes but no serverless offload) has the worst p99 (6,665 ms) and success rate (65.6%). S3 (hybrid-reactive with the same two dynamic nodes plus 96.5% serverless time) achieves the best p99 (874 ms). Knative absorbed the 51--70-second provisioning delay in S3 and S4. The same delay caused severe latency degradation in S1, where no serverless fallback existed. Dynamic node provisioning alone is not a substitute for serverless offload. The two mechanisms are complementary. The hybrid architecture gains its value by using both concurrently.

S3 and S4 have identical monthly cost (USD 387/mo) despite different p99 latency. The cost difference between reactive and predictive modes is therefore negligible at this load. The dynamic-node EC2 cost (USD 0.028 per run, tracked separately from serverless Lambda cost) is the same for all K8s scenarios because all provision the same two nodes. These n = 1 cost projections are *directional diagnostic estimates*. They must not be used to claim universal cost superiority.

S4 underperformed S3 in this diagnostic. S4's p99 was 1,393 ms versus 874 ms (+59%), and its SLO violations were 46,245 versus 23,913 (+93%). S4 failed the actuator-fidelity validity gate. The measured provisioning delay (70.5 s) plus the 15-second safety margin requires `ceil(85.5 / 15) = 6` forecast steps, but the deployed GRU model outputs only 5 steps (75-second forecast window). S4 delivered 55 predictions at 100% delivery rate, yet the number of forecast-driven routing decisions was zero. The forecasts did not change the actuator behaviour. The 5-step horizon is adequate for the default 60-second provisioning delay estimate but not for the longer delays observed under high load. This finding validates the ADAPT-inspired design direction @adapt2026: the forecast horizon must adapt to the measured provisioning delay rather than remaining static.

=== #H("ch4-varload")

The constant-load diagnostic confirms the mechanism but cannot test predictive scaling. Constant traffic gives the forecast nothing to anticipate. A ClarkNet variable-load diagnostic (n = 1) uses the real ClarkNet trace (30--164 RPS ramps, mean 73 RPS) with `max_k8s_replicas = 10` and the extended 9-step GRU horizon (135 s window). ClarkNet peaks naturally exceed the six-pod static envelope. They trigger dynamic nodes without artificial load inflation.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto, auto),
    [Scenario], [p99 (ms)], [Nodes], [Serverless], [Predictions], [Pred], [Pro. SU], [Monthly USD],
    [S1 (K8s+HPA)], [118.4], [2], [0.0%], [---], [---], [---], [187],
    [S2 (Serverless)], [79.0], [0], [100.0%], [---], [---], [---], [403],
    [S3 (Reactive)], [103.9], [2], [21.2%], [---], [---], [---], [196],
    [S4 (Predictive)], [108.3], [2], [17.6%], [55], [4], [1], [196],
  ),
  caption: cap([ClarkNet variable-load experiment (n = 1)], [Eksperimen beban variabel ClarkNet (n = 1)]),
) <tab:clarknet-dynamic-node>

Under variable load, the GRU forecast produced proactive actions for the first time: four forecast-driven routing decisions and one proactive replica scale-up issued before the observed load reached the target. All validity gates passed: the forecast horizon was sufficient and all 55 predictions were delivered. In the table, Pred counts decisions influenced by the forecast and Pro. SU counts proactive replica scale-ups; Monthly USD is a directional diagnostic estimate. S4 used 17.6% serverless time versus S3's 21.2%. The proactive scale-up added Kubernetes capacity earlier and reduced serverless dependency. S3 achieved a slightly better p99 (103.9 ms vs 108.3 ms, +4.3%) and fewer SLO violations (14 vs 44), but n = 1 is not conclusive. The identical monthly cost (USD 196/mo) confirms no cost penalty for the predictive mode at this load.

=== #H("ch4-consol")

The node autoscaler implements cluster-autoscaler-style consolidation, matching the Kubernetes Cluster Autoscaler's default behaviour @k8sca-faq. A dynamic node is a candidate for removal when three conditions hold: its CPU request utilization falls below 50% of allocatable capacity, all workload pods on the node can be rescheduled onto other workload nodes, and the node has remained underutilized for at least 90 seconds. The `kubectl drain` command evicts pods to other nodes before the node container is deleted. A 120-second cooldown prevents cascading deletions.

Under the same ClarkNet variable-load trace, consolidation produced the strongest S3-versus-S4 differentiation in the project:

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    [Scenario], [p99 (ms)], [SLO Violations], [Nodes Provisioned], [Scale-Downs], [Monthly USD],
    [S3 (Reactive)], [228.4], [1,085], [3], [3], [162],
    [S4 (Predictive)], [113.0], [40], [5], [3], [170],
  ),
  caption: cap([ClarkNet variable-load with node consolidation (n = 1)], [Beban variabel ClarkNet dengan konsolidasi _node_ (n = 1)]),
) <tab:clarknet-consolidation>

S4 achieved 50.5% lower p99 (113 ms vs 228 ms) and 96.3% fewer SLO violations (40 vs 1,085) than S3, at a 5% cost premium (USD 170/mo vs 162/mo). The mechanism is as follows. S3's reactive controller aggressively consolidated all dynamic nodes when utilization dropped. This caused severe latency spikes when ClarkNet load returned and no Kubernetes capacity was available. S4's GRU forecast predicted load ramps and maintained Kubernetes capacity. This prevented excessive consolidation. The scale-down provision events record a node utilization of 0.3 against a 0.5 threshold, with one pod on the node, for each consolidation. This confirms the utilization-based trigger fired correctly. The bidirectional autoscaling loop is visible in the event log: a node is created when pending pods are detected, then consolidated when load drops, then re-provisioned when load rises again. In the table, Scale-Downs counts node consolidation events, and Monthly USD is a directional diagnostic estimate computed from the actual per-node lifetime in the provision event timestamps. These results come from the node-consolidation diagnostic.

== #H("ch4-hpo")

A separate hyperparameter optimization study explored four controller parameters via Optuna TPE screening: `target_cpu_util`, `kp_burn`, `proactive_trend_threshold`, and `proactive_approach_ratio`. The study ran on the pre-fix infrastructure that predates the n = 1 diagnostic baseline. The methodological finding is reported here for completeness. Its specific quantitative results are *directional* and are superseded by Bugs 8-13. They are not part of the current baseline and are not used in the comparative evaluation above.

The substantive lesson is methodological rather than numerical. On a shared-resource testbed with high run-to-run variance, no parameter deviation from the default calibration survived holdout validation. Configurations that looked strong on a single run degraded sharply under replication. They narrowed the Kubernetes safety margin and caused more frequent saturation under high variance. This is consistent with overfitting risks in model selection @cawley2010overfitting. It also highlights the difficulty of HPO in online systems, where each evaluation requires a full experiment under noisy shared-resource conditions @nonstationary2022 @falkner2018bohb. The two-stage methodology (screening followed by confirmation) and the surrogate-assisted approach adapt the calibration to the observed baseline. No HPO-tuned deviation is used in the n = 1 diagnostic results.

== #H("ch4-discussion")

The experimental evaluation validates two things. It validates the mechanistic correctness of the hybrid architecture. Under the correctly bounded infrastructure, it also validates a clear performance advantage for hybrid routing over pure Kubernetes.

The study validated several mechanisms. The GRU model meets its accuracy target on synthetic data. It achieves RMSE 5.2% of the mean load on the synthetic arm under the leak-free protocol, meeting the target, and 39.6% on the real deployment trace, where the target is not met and the model matches a linear autoregression on the same input window. Inference latency is about 40 ms. Real-traffic prediction is therefore a partial validation. The routing controller correctly implements the priority-based decision framework and exhibits all four action types. The confidence-gated forecast feeds Algorithm 2's replica planning. The corrected predictive mechanism fired 9 forecast-driven routing decisions in the S4 diagnostic run.

For the hybrid-versus-pure-Kubernetes comparison (H1), the result is directionally positive at n = 1. S4 reduced p99 latency by 95.1% (2,421.3 ms -> 118.2 ms) and SLO violations by 98.5% (6,717 -> 104) relative to S1. The previous negative finding was an infrastructure artifact (un-enforced CPU limits and S1 dynamic-node over-provisioning). It was not a property of the hybrid mechanism. The n = 1 result does not establish inferential significance. The n = 5 four-scenario replication did not reproduce this advantage. It used `max_k8s_replicas = 10`, so S1 did not saturate (p99 110.3 ms). S4 versus S1 was not significant (p = 0.24). The hybrid's advantage therefore appears when the baseline is capacity-constrained, not when HPA has ample headroom.

For the predictive-versus-reactive comparison (H2), the definitive paired experiment (n = 5 counterbalanced pairs, full treatment delivery) finds S4 mean p99 126.0 ms versus 188.5 ms for S3 (mean difference -62.5 ms, 95% CI [-100.9, -26.2] ms, p = 0.030, d = -1.26, large effect). S4 wins all 5 pairs. This result reverses the initial non-significant finding (p = 0.38, d = -0.241) documented in the superseded section above. The reversal came from three changes: extending the GRU forecast horizon from 5 to 9 steps (135 s), correcting the scaling calibration from alpha = 1/r_saturation to alpha = 1/r_effective, and adding utilization-based node consolidation. S4 also shows 80.2% fewer SLO violations (130 vs 656) at identical monthly cost. The corrected secondary p-values are descriptive only.

Two caveats bound these conclusions. First, the n = 1 four-scenario diagnostic provides directional mechanism evidence but no inferential statistics for H1. Second, the definitive n = 5 paired comparison is clean and fully delivered. It provides enough statistical power to detect the effect (d = -1.26, large). Secondary metrics (p95, SLO) are not significant after multiplicity correction (corrected p = 0.12) and are reported as descriptive. The primary p99 test was pre-specified. Larger samples (n >= 20) remain valuable as confirmatory replication but are not a prerequisite for the primary verdict.

Taken together, the results directionally support H1 (the hybrid architecture outperforms the pure Kubernetes baseline at n = 1). They also provide statistically significant evidence for H2 (primary p99 p = 0.030, d = -1.26; predictive scaling shows a large latency advantage and a substantial SLO-violation reduction over reactive scaling). The calibration repair showed that the original scaling model's double-counted safety margin caused S4's apparent underperformance, not the controller design. Recent work on uncertainty-aware autoscaling @aapa2025 and delay-derived planning horizons @adapt2026 provides design directions for further improvement. Benchmark studies @rayscale2026 show that even advanced autoscalers struggle to outperform well-calibrated baselines on cost.
