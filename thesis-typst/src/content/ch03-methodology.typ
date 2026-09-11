#import "ch03-figures.typ": *
#import "headings.typ": H, cap

// ---------------------------------------------------------------------------
// Algorithm block — matches the proposal docx style: a bordered box with a
// bold "Algorithm N: Title" heading, a bold Input/Parameters preamble, and
// numbered steps (1:, 2:, ...) with bold control-flow keywords and `<-`
// assignment. An algorithm is NOT a Gambar figure.
// ---------------------------------------------------------------------------
#let algo(title, head, steps) = block(
  stroke: 0.7pt + rgb("#5a6b80"),
  inset: (x: 12pt, y: 10pt),
  radius: 3pt,
  breakable: true,
)[
  #align(center, text(size: 11pt)[#title])
  #v(5pt)
  #head
  #v(4pt)
  #for (n, b) in steps [
    #grid(
      columns: (2.6em, 1fr),
      column-gutter: 0.5em,
      align(right)[#n:],
      b,
    )
  ]
]

= #H("ch3")

This chapter explains the methodology used to answer the research questions and achieve the objectives. It covers the research flow, data collection, system architecture, implementation of the prediction model and online controllers, and the evaluation plan. The evaluation plan includes experimental scenarios, metrics, and threats to validity.

== #H("ch3-flow")

The research follows a six-phase methodology. It moves from theoretical foundations through system design, implementation, and experimental evaluation.

Literature Study surveys cloud computing architectures, workload prediction methods, and elastic scaling algorithms. It establishes the theoretical foundation and identifies the research gap. Data Collection generates synthetic workload patterns for GRU model training. It also adds real HTTP trace datasets (ClarkNet and Calgary) for baseline comparison and validation. Method Design specifies the hybrid Kubernetes-serverless architecture, the routing and scaling algorithms, and the SLO-based decision framework. Implementation develops the GRU prediction server, the routing controller (Algorithm 1), the integrated cluster controller (Algorithm 2) with real Kubernetes replica scaling, the monitoring infrastructure, and the traffic routing layer. Evaluation conducts systematic experimental evaluation across four deployment scenarios. It includes mechanism validation (Phase A1), trace-driven replicated comparison using ClarkNet replay (Phase B), dynamic burst validation (Phase C), and statistical analysis. Report Writing documents findings with truth-aligned claims. These claims distinguish validated mechanisms from unestablished superiority claims.

Each phase produces artifacts that feed the next phases. The literature study informs the system design. The collected data trains the prediction model. The implemented system undergoes experimental evaluation. The evaluation results inform the thesis conclusions. The flow is gated rather than strictly linear: when evaluation results are unsatisfactory, the work returns to method design for revision before conclusions are drawn.

#figure(
  align(center, fig-research-flow()),
  caption: cap([Research methodology flow], [Alur metodologi penelitian]),
) <fig:research-flow>

== #H("ch3-data")

The GRU prediction model requires time-series workload data for training and validation. The research uses two data sources: synthetic workload patterns and real HTTP trace datasets. It is important to distinguish two separate uses of this data: *training data*, which builds and validates the prediction model, and *replay load*, which constructs the experiment's workload. They are not the same artifact.

=== #H("ch3-training")

Two data sources are used, and each is scored as a separate arm. The primary arm is the deployment trace itself. ClarkNet is resampled to 15 seconds and multiplied by the same factor the replay applies (33), so the model trains at the amplitude it will later serve. The trace is split chronologically into training, validation, and test portions, with an embargo of `sequence_length + horizon - 1` samples at every boundary, so no input or target window crosses a boundary and no training window overlaps a validation or test window. The normalisation statistics are fitted on the training portion alone. Hyperparameters and the training epoch budget are selected on the validation portion, the model is refitted on the training and validation portions at that frozen budget, and the test portion is scored once, per seed. The replay window described below lies inside the test portion, so the model is never trained on the traffic it later serves. The second arm is synthetic workload patterns. These patterns encode common traffic shapes: diurnal cycles, random bursts, and gradual ramps, generated at 1-second resolution and held across 15-second buckets. This arm is retained because the pre-registered accuracy target is defined on synthetic data, and it is scored under the identical protocol at the same horizon. The real trace aggregates at 1-minute, 5-minute, and 10-minute intervals described in earlier runs belong to the superseded protocol. Calgary is archived as too sparse for the 15-second task.

=== #H("ch3-replay")

The experiment load is a sampled window of the ClarkNet trace, separate from the training data. The ClarkNet and Calgary logs are continuous multi-month traces; replaying them in full is infeasible on a testbed. The experiment therefore selects one representative variable-load window, 1995-09-02 04:35:30 to 04:55:00 UTC, chosen for its high variance (coefficient of variation 0.468) with ramps and surges rather than a flat plateau. This window gives both reactive and predictive control decisions room to act. It is encoded as a k6 stage profile: 40 stages of 30 seconds each, 1,200 seconds (~20 minutes) total, at 22 to 164 RPS with a mean of 73 RPS (the raw 2.22 RPS mean scaled by a factor of 33 to reach the testbed's scaling-relevant regime). Phase B replays this profile through k6's ramping-arrival-rate executor.

== #H("ch3-arch")

The proposed system integrates three subsystems. They are an offline training pipeline, an online prediction and control plane, and a hybrid execution infrastructure. The architecture uses a two-layer design inspired by the ElaX algorithm framework. The thesis-specific roles are explicit. Algorithm 1 governs traffic routing from observed load, ready-replica capacity, and SLO status. Algorithm 2 manages Kubernetes replica scaling from observed load or the confidence-gated GRU upper forecast. Both algorithms run in a single routing daemon. The daemon executes them in a coordinated 15-second control loop. Algorithm 1 provides immediate traffic shedding to serverless. Algorithm 2 scales Kubernetes replicas to restore capacity. Then Algorithm 1 returns traffic to Kubernetes.

The execution infrastructure is a simulation of a real two-platform deployment on a single physical testbed. A production deployment would run Kubernetes and serverless as two separate managed platforms (for example, a managed Kubernetes service alongside a managed Knative/serverless platform). Reproducing that faithfully would require two physical clusters, which would complicate the controlled 15-second control-loop experiments. Instead, both platforms run on one physical k3d cluster, a single host that isolates the two platforms through the mechanisms described below.

=== #H("ch3-infra")

HAProxy is the entry point for all HTTP traffic. It distributes requests between the Kubernetes and serverless backends using weighted routing rules. HAProxy treats the two backends as two independent upstream endpoints and assigns them runtime-adjustable weights. Algorithm 1 adjusts the weights dynamically through the HAProxy Runtime API (TCP socket interface). HAProxy also exposes a statistics endpoint. This endpoint provides real-time throughput and latency metrics that the monitoring subsystem consumes.

K3s (Kubernetes Backend) is a lightweight, certified Kubernetes distribution. It is deployed via k3d (k3s-in-Docker). K3s runs the primary application workload as always-warm pods. It provides consistent low-latency responses for baseline traffic. In this study, K3s is the baseline warm capacity. The research evaluates the relative cost advantage empirically per run, not as an assumption made a priori.

Knative Serving (Serverless Backend) runs on the same physical k3d cluster but is operated as an independent platform. It uses Kourier as its own ingress controller. Knative provides scale-to-zero capability and rapid autoscaling for burst traffic. When the routing controller enables the serverless backend, Knative manages the pod lifecycle automatically. This includes cold start initialization. The serverless backend activates only when SLO violations occur or when the GRU model predicts an imminent load surge.

Four mechanisms enforce the logical isolation between the two platforms. First, separate namespaces and application instances: the warm workload runs as a Kubernetes Deployment (test-app-warm) with its own Service, while the serverless workload runs as a Knative Service. Second, separate ingress paths: the Kubernetes backend is reached through its own NodePort Service, whereas the serverless backend is reached through Knative's own ingress controller (Kourier), which routes on the Knative Host header. Third, independent autoscaling: Knative's KPA scales on concurrency and can scale to zero, while Kubernetes replicas are scaled by the HPA (S1) or by Algorithm 2 via kubectl (S3/S4). Fourth, independent lifecycle: the serverless backend can cold-start and scale to zero while the warm Kubernetes pods remain steady. Because the platforms are logically isolated and the control plane is platform-agnostic, this single-testbed simulation reproduces the behavior of a real deployment where Kubernetes and serverless are separate managed platforms.

=== #H("ch3-monitoring")

The system uses Prometheus for metrics collection. It also uses an SLO monitor component for real-time compliance checking. Prometheus scrapes HAProxy statistics at 1-second intervals. It collects request counts, response times, and backend health status. The SLO Monitor computes the 99th percentile (p99) tail latency from Prometheus time-series data. It also maintains a rolling violation window to detect sustained SLO breaches.

#figure(
  align(center, fig-control-loop()),
  caption: cap([Hybrid system architecture], [Arsitektur sistem hibrida]),
) <fig:control-loop>

== #H("ch3-impl")

=== #H("ch3-predictor")

The workload prediction model uses a Gated Recurrent Unit (GRU) neural network with a direct multi-horizon output head. The model accepts an input window of per-interval request counts sampled at 15-second resolution. It outputs nine 15-second steps ahead (135 seconds total). The direct output eliminates autoregressive error compounding. Architecture and training hyperparameters are not fixed by hand. A Tree-structured Parzen Estimator search selects the hidden size, the number of recurrent layers, the dropout rates, the learning rate, and the input window length on the validation portion only, using expanding-window folds that carry the same embargo as the training split. Training uses the Adam optimizer with Mean Squared Error loss and a batch size of 32. Early stopping sets the epoch budget, which is then frozen for the refit on the training and validation portions. Chapter 4 reports the selected configuration and its held-out accuracy. The research derives per-horizon upper offsets as the 90th percentile of positive validation residuals. It adds these offsets to the point forecasts. This forms a conservative upper envelope (`upper_forecasts`) that directly addresses ramp underprediction.

The extended 9-step horizon (135 s) covers the K3dAutoscaler's maximum provisioning delay (120 s) plus a 15-second safety margin. This follows the self-calibrating approach of ADAPT @adapt2026. The system validates the forecast horizon at runtime via the model-status endpoint.

The trained model runs in a FastAPI prediction server. The server accepts recent request-rate history as input. It returns point forecasts, upper-envelope forecasts, and a scalar confidence score. The confidence score comes from the model's normalized validation error (RMSE relative to the training-set mean), not from prediction variance. A score of 0.8 means the model's error is below 15% of the mean. The routing controller gates proactive actions on this confidence. It exceeds a configurable threshold (default: 0.5).

=== #H("ch3-alloc")

The resource allocation model uses a linear form. In this model, R is the target replica count, x is predicted or observed traffic intensity (requests per second), alpha is the resource-per-request coefficient (replicas per RPS), and beta is base replica overhead (minimum replicas at near-zero traffic). The research derives alpha from a calibrated saturation measurement: alpha = 1/r_effective, where r_effective = r_saturation_per_replica × target_cpu_util. At each control interval, the daemon computes a target replica count with a safety buffer gamma (typically 1.0). It clamps this count to fixed bounds [3, 6] under the default calibration. Workload pods request 300 millicores. The two static workload nodes are CPU-bounded at 1.0 CPU each. The definitive paired H2 experiment used an experiment-local calibration override (`max_k8s_replicas = 10`, `prediction_horizon = 9`; see the definitive calibration override record). This override makes ClarkNet peaks exceed the six-pod static envelope and exercise node-level autoscaling. It matches the consolidated calibration record.

=== #H("ch3-algo1")

Algorithm 1 is the primary decision engine. It monitors SLO compliance and adjusts traffic routing weights between Kubernetes and serverless backends. It uses a priority-based decision framework with four action types:

- *SCALE_OUT (Priority 1):* When p99 latency exceeds the SLO threshold (200ms) for a sustained violation window, the controller shifts traffic toward the serverless backend. It increments the serverless weight in steps of 10%.
- *PREDICTIVE (Priority 2):* When the system is healthy and the observed-load trend indicates an approaching capacity boundary, the controller may adjust serverless engagement using observed signals and the confidence gate. The GRU forecast is consumed by Algorithm 2 for Kubernetes replica planning. It does not directly set routing weights.
- *OPTIMIZE_COST (Priority 3):* When p99 latency is well within the healthy margin (under 70% of the SLO threshold), the controller gradually reduces serverless usage to save cost.
- *MAINTAIN (Priority 4):* When none of the above conditions hold, the controller preserves current weights.

Traffic weights shift gradually in increments of 10% to avoid oscillation. They move from 100/0 (K8s only) through 90/10, 80/20, 70/30, 60/40, to a maximum of 50/50. When serverless first enables, the controller sends a synthetic health-check request to the Knative service endpoint. This request triggers cold start initialization. It reduces the latency penalty when actual traffic starts routing.

#algo(
  cap([#text(weight: "bold")[Algorithm 1:] Routing Controller (priority decision framework)], [#text(weight: "bold")[Algoritma 1:] Kontroler _Routing_ (kerangka keputusan berprioritas)]),
  [
    *Input:* p99, violation_duration (SLO status); prediction = \{predicted_requests, confidence\} (S4 only); current_load (RPS); current weights (k3s, knative), serverless_enabled \
    *Parameters:* cooldown = 15 s, violation_window = 30 s, weight_step = 10, healthy_margin = 0.7, confidence_threshold = 0.5, load_change_threshold = 0.3, max_knative = 50
  ],
  (
    (1, [*if* now - last_adjust < cooldown *then*]),
    (2, [#h(1.4em) *return* MAINTAIN (current weights)]),
    (3, [*end if*]),
    (4, [*if* violation_duration >= violation_window *then* #h(2em) \{Priority 1\}]),
    (5, [#h(1.4em) *if* *not* serverless_enabled *then* enable + pre-warm Knative]),
    (6, [#h(1.4em) knative #sym.arrow.l min(max_knative, knative + weight_step) #h(2em) \{+10%, cap 50\}]),
    (7, [#h(1.4em) *return* SCALE_OUT (k3s = 100 - knative, knative)]),
    (8, [*end if*]),
    (9, [healthy #sym.arrow.l healthy_margin \* 200 #h(4em) \{140 ms\}]),
    (10, [*if* prediction *and* healthy <= p99 < 200 *then* #h(1.4em) \{Priority 2\}]),
    (11, [#h(1.4em) *if* confidence >= confidence_threshold *and*]),
    (12, [#h(2.8em) (predicted_requests - current_load) / current_load > load_change_threshold *then*]),
    (13, [#h(2.8em) knative #sym.arrow.l min(max_knative, knative + weight_step)]),
    (14, [#h(2.8em) *return* PREDICTIVE (k3s = 100 - knative, knative)]),
    (15, [#h(1.4em) *end if*]),
    (16, [*end if*]),
    (17, [*if* p99 < healthy *and* current_load > 0 *then* #h(2.8em) \{Priority 3\}]),
    (18, [#h(1.4em) k3s #sym.arrow.l min(100, k3s + weight_step / 2) #h(2em) \{+5% back to K8s\}]),
    (19, [#h(1.4em) *if* k3s = 100 *then* disable serverless (scale-to-zero)]),
    (20, [#h(1.4em) *return* OPTIMIZE_COST (k3s, knative = 100 - k3s)]),
    (21, [*end if*]),
    (22, [*return* MAINTAIN (current weights) #h(4.2em) \{Priority 4\}]),
  ),
)

=== #H("ch3-algo2")

Algorithm 2 operates in two modes that share the same capacity model. In reactive mode (S3), the scaling signal is the mean observed RPS over the last 30 seconds. In predictive mode (S4), the daemon computes a predictive target from the GRU confidence-gated upper forecast. It selects this target only when it *strictly exceeds* the observed target. Otherwise the observed target is used. A proactive hold interval (90 seconds) prevents premature rollback of a proactive scale-up while the forecast window is still active. In both scenarios, the V3 routing controller routes by *observed* ready-replica capacity. The forecast influences only Kubernetes replica planning, not the HAProxy weight split. This separation from the proposal's prediction-driven-routing framing is an empirically motivated design decision. Underprediction during ramps made direct forecast-based routing over-route to serverless. Scaling has the lead time needed to benefit from the 135-second horizon.

The controller scales by invoking kubectl scale deployment. It chose this command for its determinism and explicit audit trail. Safety checks include cooldown periods, replica bounds clamping, scale-down hysteresis, and readiness verification before traffic returns to Kubernetes. The cooldown periods are 15 seconds for scale-up and 300 seconds for scale-down in V3 mode. The definitive paired comparison used the tuned baseline: 120 s cooldown with a 0.75 scale-down threshold.

#algo(
  cap([#text(weight: "bold")[Algorithm 2:] Cluster Controller (Kubernetes replica scaling)], [#text(weight: "bold")[Algoritma 2:] Kontroler _Cluster_ (penskalaan replika Kubernetes)]),
  [
    *Input:* x_obs (mean observed RPS, last 30 s); predicted_upper (confidence-gated GRU upper forecast; S4 only); c (current desired replicas), p99 \
    *Parameters:* alpha = 1 / (r_sat \* cpu_util), beta = 0, buffer = 1.0, min_replicas = 3, max_replicas = 6, scale_down_threshold = 0.75, hold = 90 s, up_cooldown = 15 s, down_cooldown = 120 s
  ],
  (
    (1, [R(x) = clamp(ceil((alpha \* x + beta) \* buffer), min_replicas, max_replicas)]),
    (2, [observed_target #sym.arrow.l R(x_obs)]),
    (3, [target #sym.arrow.l observed_target; proactive #sym.arrow.l *false*]),
    (4, [*if* predictive mode (S4) *and* forecast available *then*]),
    (5, [#h(1.4em) predictive_target #sym.arrow.l R(predicted_upper)]),
    (6, [#h(1.4em) *if* predictive_target > observed_target *then* #h(1em) \{strictly exceeds\}]),
    (7, [#h(2.8em) target #sym.arrow.l predictive_target; proactive #sym.arrow.l *true*]),
    (8, [#h(2.8em) hold_until #sym.arrow.l now + hold]),
    (9, [#h(1.4em) *else if* now < hold_until *and* held_target > observed_target *then*]),
    (10, [#h(2.8em) target #sym.arrow.l held_target; proactive #sym.arrow.l *true* #h(1em) \{proactive hold\}]),
    (11, [#h(1.4em) *end if*]),
    (12, [*end if*]),
    (13, [*if* target > c *then* action #sym.arrow.l SCALE_UP]),
    (14, [*else if* target < c \* scale_down_threshold *then* action #sym.arrow.l SCALE_DOWN]),
    (15, [*else* action #sym.arrow.l MAINTAIN]),
    (16, [*end if*]),
    (17, [*if* action = SCALE_UP *and* now - last_up >= up_cooldown *then*]),
    (18, [#h(1.4em) kubectl scale deployment --replicas=target]),
    (19, [*else if* action = SCALE_DOWN *and* now - last_down >= down_cooldown]),
    (20, [#h(1.4em) *and* p99 < healthy *and* max(min_replicas, target) < c *then*]),
    (21, [#h(1.4em) kubectl scale deployment --replicas=max(min_replicas, target)]),
    (22, [*end if*]),
  ),
)

=== #H("ch3-consolidation")

The K3dAutoscaler implements utilization-based node consolidation. It matches the Kubernetes Cluster Autoscaler semantics @k8sca-faq. A dynamic node is a candidate for removal when three conditions hold. Its CPU request utilization falls below 50% of allocatable capacity @serracanta2025hpa. All workload pods can reschedule onto other nodes. The node has stayed underutilized for at least 90 seconds. The kubectl drain command evicts pods before deletion. A 120-second cooldown prevents cascading deletions @tinyautoscalers2022. Pod-level scale-down uses a 120-second cooldown and 0.75 utilization threshold.

== #H("ch3-evalplan")

=== #H("ch3-scenarios")

The research defines four scenarios. They compare platform-native autoscaling baselines against the custom hybrid control plane. They also isolate the value of GRU prediction within the hybrid architecture:

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, left, left),
    [*Scenario*], [*Description*], [*Autoscaling*], [*GRU*],
    [S1 (K8s + HPA Baseline)], [100% traffic to Kubernetes], [HPA native CPU-based autoscaling], [off],
    [S2 (Knative-Only KPA)], [100% traffic to Knative via HAProxy], [KPA concurrency-based autoscaling with scale-to-zero], [off],
    [S3 (Hybrid Reactive)], [Dynamic K8s to Knative routing via Algorithm 1], [Algorithm 2 scaling using observed RPS (observed)], [off],
    [S4 (Hybrid Predictive)], [Dynamic K8s to Knative routing via Algorithm 1], [Algorithm 2 scaling using GRU forecast (predicted)], [on],
  ),
  caption: cap([Experimental scenarios], [Skenario eksperimen]),
) <tab:scenarios>

The S1 vs S2 comparison evaluates platform-native baselines. The S3 vs S1/S2 comparison evaluates whether the hybrid reactive control plane improves over either baseline alone. The S3 vs S4 comparison isolates the value of GRU prediction. Both use hybrid routing and Algorithm 2 scaling. Both route by observed load. S4 also consumes the confidence-gated upper forecast for Kubernetes replica planning. A practical caveat applies. The scaling model maps load to replicas via ceil(alpha dot.op x dot.op gamma) clamped to a minimum of three replicas. Therefore moderate-load forecasts (e.g., 62 RPS) can map to the same replica target as the observed signal. This makes the predictive and reactive paths operationally identical for that cycle. The comparison is therefore only discriminative when the forecast produces a *different* replica target than the observed signal. This condition depends on the calibration margin and is analyzed in Chapter 4.

The original ElaX algorithm is not evaluated as a separate scenario. ElaX performs elasticity control within a single platform. It has no cross-platform routing layer, so it does not solve the hybrid routing problem studied in this research. The thesis therefore treats ElaX as the algorithmic foundation. It isolates the contribution through the S3 versus S4 ablation, which differs only in the scaling signal. Recent predictive autoscaling work uses the same evaluation method @adapt2026. It compares modified controllers against platform-native baselines and ablations. It does not re-implement the original algorithm.

=== #H("ch3-phases")

Phase A0 validates infrastructure and autoscaler mechanisms. Phase A1 validates individual system mechanisms under a controlled ramp load. Phase B conducts a counterbalanced paired comparison with ClarkNet trace-driven workload (40 stages, 30 seconds each, RPS 22 to 164, mean 73). Under this replay profile, S1 and S2 run on platform-native autoscaling (HPA and KPA respectively), while S3 and S4 run the custom control plane (Algorithm 1 routing plus Algorithm 2 scaling); all four scenarios receive the identical k6 replay load. It uses 5 pairs (10 runs) that alternate scenario order between S3 and S4, plus n = 1 four-scenario diagnostics. A four-scenario replication completed Phase B on 2026-08-09 (`2026-08-09_clarknet-replay_032257`). It ran 4 scenarios, 5 runs each (20 clean runs), with all validity gates passed (5/5 per scenario). Phase C stresses the system with controlled burst profiles.

=== #H("ch3-metrics")

User-perceived performance metrics include p50, p95, and p99 latency, error rate, and achieved throughput. The primary SLO metric is p99 latency with a threshold of 200ms. Routing and control-plane metrics include weight change count, time-in-serverless percentage, prediction usage rate, and control-loop latency. Kubernetes replica scaling metrics include desired replicas, current replicas, ready replicas, scale-up/down events and latencies, and oscillation index. Resource and cost proxy metrics include CPU/memory utilization, K8s capacity time, Knative active time, and cost-normalized metrics (USD/1M requests, USD/1M SLO-compliant requests).

=== #H("ch3-stats")

The paired S3/S4 comparison uses a pre-specified one-sided permutation test on the paired p99 difference (alpha = 0.05). Secondary endpoints (p95, SLO violations, throughput, and error rate) are Bonferroni-corrected and reported descriptively. Only the primary endpoint may be claimed as statistically significant. The four-scenario replication (S1, S2, S3, S4, n = 5 each) uses Welch's t-test and the Mann-Whitney U test on per-scenario p99 latency, with the same alpha = 0.05. This comparison is two-sided and reported as replication-tier evidence rather than as a pre-specified claim.

=== #H("ch3-threats")

The experimental evaluation has several documented threats. The multi-node k3d testbed uses two CPU-bounded workload nodes and localhost-adjacent routing. It does not reproduce production network latency or network contention. Historical traces (1994-1995) may not match modern application semantics. Replay fidelity preserves request intensity but not client think times or cache behaviors. The single-threaded application constraint (GOMAXPROCS=1, /fib?n=33) creates reproducible saturation. It does not represent typical multi-threaded web applications. The artificial node capacity constraint forces autoscaler triggers at lower loads than production. Because both platforms share the same physical nodes, they compete for the same CPU capacity, which a real split deployment would not; the measured results are therefore a conservative, mechanism-validating bound rather than a production capacity claim. All results should be interpreted as mechanism validation, not as production-representative performance guarantees.
