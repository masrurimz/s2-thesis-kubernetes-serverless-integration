= METHODOLOGY

This chapter explains the methodology used to answer the research questions and achieve the objectives. It covers the research flow, data collection, system architecture, implementation of the prediction model and online controllers, and the evaluation plan. The evaluation plan includes experimental scenarios, metrics, and threats to validity.

== Research Flow

The research follows a six-phase methodology. It moves from theoretical foundations through system design, implementation, and experimental evaluation.

Literature Study surveys cloud computing architectures, workload prediction methods, and elastic scaling algorithms. It establishes the theoretical foundation and identifies the research gap. Data Collection generates synthetic workload patterns for GRU model training. It also adds real HTTP trace datasets (ClarkNet and Calgary) for baseline comparison and validation. Method Design specifies the hybrid Kubernetes-serverless architecture, the routing and scaling algorithms, and the SLO-based decision framework. Implementation develops the GRU prediction server, the routing controller (Algorithm 1), the integrated cluster controller (Algorithm 2) with real Kubernetes replica scaling, the monitoring infrastructure, and the traffic routing layer. Evaluation conducts systematic experimental evaluation across four deployment scenarios. It includes mechanism validation (Phase A1), trace-driven replicated comparison using ClarkNet replay (Phase B), dynamic burst validation (Phase C), and statistical analysis. Report Writing documents findings with truth-aligned claims. These claims distinguish validated mechanisms from unestablished superiority claims.

Each phase produces artifacts that feed the next phases. The literature study informs the system design. The collected data trains the prediction model. The implemented system undergoes experimental evaluation. The evaluation results inform the thesis conclusions.

#figure(
  image("../figures/image11.png", width: 60%),
  caption: [Research methodology flow],
) <fig:research-flow>

== Data Collection

The GRU prediction model requires time-series workload data for training and validation. The research uses two data sources. The first is synthetic workload patterns. These patterns encode common traffic shapes: diurnal cycles, random bursts, and gradual ramps. The second is real HTTP trace datasets. These come from ClarkNet (NASA ClarkNet WWW server, August 1995, mean 3.27 RPS per second) and Calgary (University of Calgary, October 1994, mean 1.20 RPS per second).

The synthetic generator produces configurable traffic patterns at 1-second RPS resolution. Its parameters cover diurnal amplitude, burst frequency, and ramp slope. The research generates a 72-hour synthetic dataset and splits it 70/15/15 into training, validation, and test sets. The research aggregates real traces to 1-minute, 5-minute, and 10-minute intervals. This aggregation assesses the effect of temporal resolution on prediction accuracy. The same model architecture and hyperparameters that train on synthetic data also apply to real traces for generalization assessment.

== System Architecture

The proposed system integrates three subsystems. They are an offline training pipeline, an online prediction and control plane, and a hybrid execution infrastructure. The architecture uses a two-layer design inspired by the ElaX algorithm framework. The thesis-specific roles are explicit. Algorithm 1 governs traffic routing from observed load, ready-replica capacity, and SLO status. Algorithm 2 manages Kubernetes replica scaling from observed load or the confidence-gated GRU upper forecast. Both algorithms run in a single routing daemon. The daemon executes them in a coordinated 15-second control loop. Algorithm 1 provides immediate traffic shedding to serverless. Algorithm 2 scales Kubernetes replicas to restore capacity. Then Algorithm 1 returns traffic to Kubernetes.

=== Infrastructure Components

HAProxy is the entry point for all HTTP traffic. It distributes requests between the Kubernetes and serverless backends using weighted routing rules. Algorithm 1 adjusts the weights dynamically through the HAProxy Runtime API (TCP socket interface). HAProxy also exposes a statistics endpoint. This endpoint provides real-time throughput and latency metrics that the monitoring subsystem consumes.

K3s (Kubernetes Backend) is a lightweight, certified Kubernetes distribution. It is deployed via k3d (k3s-in-Docker). K3s runs the primary application workload as always-warm pods. It provides consistent low-latency responses for baseline traffic. In this study, K3s is the baseline warm capacity. The research evaluates the relative cost advantage empirically per run, not as an assumption made a priori.

Knative Serving (Serverless Backend) is deployed on the same K3s cluster. It uses Kourier as the ingress controller. Knative provides scale-to-zero capability and rapid autoscaling for burst traffic. When the routing controller enables the serverless backend, Knative manages the pod lifecycle automatically. This includes cold start initialization. The serverless backend activates only when SLO violations occur or when the GRU model predicts an imminent load surge.

=== Monitoring and Metrics Collection

The system uses Prometheus for metrics collection. It also uses an SLO monitor component for real-time compliance checking. Prometheus scrapes HAProxy statistics at 1-second intervals. It collects request counts, response times, and backend health status. The SLO Monitor computes the 99th percentile (p99) tail latency from Prometheus time-series data. It also maintains a rolling violation window to detect sustained SLO breaches.

== Implementation

=== Workload Predictor (GRU Architecture)

The workload prediction model uses a Gated Recurrent Unit (GRU) neural network. It has one recurrent layer of 128 hidden units followed by head dropout regularization. The model accepts a 30-sample input window of per-interval request counts. These counts are sampled at 15-second resolution. The model outputs direct multi-horizon forecasts for nine 15-second steps ahead (135 seconds total). This direct output eliminates autoregressive error compounding. Training uses the Adam optimizer with Mean Squared Error loss, batch size 32, and early stopping with patience of 15 epochs (maximum 100). The research derives per-horizon upper offsets as the 90th percentile of positive validation residuals. It adds these offsets to the point forecasts. This forms a conservative upper envelope (`upper_forecasts`) that directly addresses ramp underprediction.

The extended 9-step horizon (135 s) covers the K3dAutoscaler's maximum provisioning delay (120 s) plus a 15-second safety margin. This follows the self-calibrating approach of ADAPT @adapt2026. The system validates the forecast horizon at runtime via the model-status endpoint.

The trained model runs in a FastAPI prediction server. The server accepts recent request-rate history as input. It returns point forecasts, upper-envelope forecasts, and a scalar confidence score. The confidence score comes from the model's normalized validation error (RMSE relative to the training-set mean), not from prediction variance. A score of 0.8 means the model's error is below 15% of the mean. The routing controller gates proactive actions on this confidence. It exceeds a configurable threshold (default: 0.5).

=== Resource Allocation Model

The resource allocation model uses a linear form. In this model, R is the target replica count, x is predicted or observed traffic intensity (requests per second), alpha is the resource-per-request coefficient (replicas per RPS), and beta is base replica overhead (minimum replicas at near-zero traffic). The research derives alpha from a calibrated saturation measurement: alpha = 1/r_effective, where r_effective = r_saturation_per_replica × target_cpu_util. At each control interval, the daemon computes a target replica count with a safety buffer gamma (typically 1.0). It clamps this count to fixed bounds [3, 6] under the default calibration. Workload pods request 300 millicores. The two static workload nodes are CPU-bounded at 1.0 CPU each. The definitive paired H2 experiment used an experiment-local calibration override (`max_k8s_replicas = 10`, `prediction_horizon = 9`; see `results/calibration/2026-08-06_definitive-repro.json`). This override makes ClarkNet peaks exceed the six-pod static envelope and exercise node-level autoscaling. It matches the configuration recorded in `results/claims/FINAL_NUMBERS.md`.

=== Algorithm 1: Routing Controller

Algorithm 1 is the primary decision engine. It monitors SLO compliance and adjusts traffic routing weights between Kubernetes and serverless backends. It uses a priority-based decision framework with four action types:

SCALE_OUT (Priority 1): When p99 latency exceeds the SLO threshold (200ms) for a sustained violation window, the controller shifts traffic toward the serverless backend. It increments the serverless weight in steps of 10%.

PREDICTIVE (Priority 2): When the system is healthy and the observed-load trend indicates an approaching capacity boundary, the controller may adjust serverless engagement using observed signals and the confidence gate. The GRU forecast is consumed by Algorithm 2 for Kubernetes replica planning. It does not directly set routing weights.

OPTIMIZE_COST (Priority 3): When p99 latency is well within the healthy margin (under 70% of the SLO threshold), the controller gradually reduces serverless usage to save cost.

MAINTAIN (Priority 4): When none of the above conditions hold, the controller preserves current weights.

Traffic weights shift gradually in increments of 10% to avoid oscillation. They move from 100/0 (K8s only) through 90/10, 80/20, 70/30, 60/40, to a maximum of 50/50. When serverless first enables, the controller sends a synthetic health-check request to the Knative service endpoint. This request triggers cold start initialization. It reduces the latency penalty when actual traffic starts routing.

=== Algorithm 2: Cluster Controller

Algorithm 2 operates in two modes that share the same capacity model. In reactive mode (S3), the scaling signal is the mean observed RPS over the last 30 seconds. In predictive mode (S4), the daemon computes a predictive target from the GRU confidence-gated upper forecast. It selects this target only when it *strictly exceeds* the observed target. Otherwise the observed target is used. A proactive hold interval (90 seconds) prevents premature rollback of a proactive scale-up while the forecast window is still active. In both scenarios, the V3 routing controller routes by *observed* ready-replica capacity. The forecast influences only Kubernetes replica planning, not the HAProxy weight split. This separation from the proposal's prediction-driven-routing framing is an empirically motivated design decision. Underprediction during ramps made direct forecast-based routing over-route to serverless. Scaling has the lead time needed to benefit from the 135-second horizon.

The controller scales by invoking kubectl scale deployment. It chose this command for its determinism and explicit audit trail. Safety checks include cooldown periods, replica bounds clamping, scale-down hysteresis, and readiness verification before traffic returns to Kubernetes. The cooldown periods are 15 seconds for scale-up and 300 seconds for scale-down in V3 mode. The definitive paired comparison used the tuned baseline: 120 s cooldown with a 0.75 scale-down threshold.

=== Node-Level Consolidation

The K3dAutoscaler implements utilization-based node consolidation. It matches the Kubernetes Cluster Autoscaler semantics @k8sca-faq. A dynamic node is a candidate for removal when three conditions hold. Its CPU request utilization falls below 50% of allocatable capacity @serracanta2025hpa. All workload pods can reschedule onto other nodes. The node has stayed underutilized for at least 90 seconds. The kubectl drain command evicts pods before deletion. A 120-second cooldown prevents cascading deletions @tinyautoscalers2022. Pod-level scale-down uses a 120-second cooldown and 0.75 utilization threshold.

== Evaluation Plan

=== Evaluation Scenarios

The research defines four scenarios. They compare platform-native autoscaling baselines against the custom hybrid control plane. They also isolate the value of GRU prediction within the hybrid architecture:

S1 (K8s + HPA Baseline): 100% traffic to Kubernetes, HPA native CPU-based autoscaling, GRU off.

S2 (Knative-Only KPA): 100% traffic to Knative via HAProxy, KPA concurrency-based autoscaling with scale-to-zero, GRU off.

S3 (Hybrid Reactive): Dynamic K8s to Knative routing via Algorithm 1, Algorithm 2 scaling using observed RPS (observed), GRU off.

S4 (Hybrid Predictive): Dynamic K8s to Knative routing via Algorithm 1, Algorithm 2 scaling using GRU forecast (predicted), GRU on.

The S1 vs S2 comparison evaluates platform-native baselines. The S3 vs S1/S2 comparison evaluates whether the hybrid reactive control plane improves over either baseline alone. The S3 vs S4 comparison isolates the value of GRU prediction. Both use hybrid routing and Algorithm 2 scaling. Both route by observed load. S4 also consumes the confidence-gated upper forecast for Kubernetes replica planning. A practical caveat applies. The scaling model maps load to replicas via ceil(alpha dot.op x dot.op gamma) clamped to a minimum of three replicas. Therefore moderate-load forecasts (e.g., 62 RPS) can map to the same replica target as the observed signal. This makes the predictive and reactive paths operationally identical for that cycle. The comparison is therefore only discriminative when the forecast produces a *different* replica target than the observed signal. This condition depends on the calibration margin and is analyzed in Chapter 4.

=== Evaluation Phases

Phase A0 validates infrastructure and autoscaler mechanisms. Phase A1 validates individual system mechanisms under a controlled ramp load. Phase B conducts a counterbalanced paired comparison with ClarkNet trace-driven workload (40 stages, 30 seconds each, RPS 22 to 164, mean 73). It uses 5 pairs (10 runs) that alternate scenario order between S3 and S4, plus n = 1 four-scenario diagnostics. Phase C stresses the system with controlled burst profiles.

=== Metrics

User-perceived performance metrics include p50, p95, and p99 latency, error rate, and achieved throughput. The primary SLO metric is p99 latency with a threshold of 200ms. Routing and control-plane metrics include weight change count, time-in-serverless percentage, prediction usage rate, and control-loop latency. Kubernetes replica scaling metrics include desired replicas, current replicas, ready replicas, scale-up/down events and latencies, and oscillation index. Resource and cost proxy metrics include CPU/memory utilization, K8s capacity time, Knative active time, and cost-normalized metrics (USD/1M requests, USD/1M SLO-compliant requests).

=== Statistical Analysis Protocol

The paired S3/S4 comparison uses a pre-specified one-sided permutation test on the paired p99 difference (alpha = 0.05). Secondary endpoints (p95, SLO violations, throughput, and error rate) are Bonferroni-corrected and reported descriptively. Only the primary endpoint may be claimed as statistically significant.

=== Threats to Validity

The experimental evaluation has several documented threats. The multi-node k3d testbed uses two CPU-bounded workload nodes and localhost-adjacent routing. It does not reproduce production network latency or network contention. Historical traces (1994-1995) may not match modern application semantics. Replay fidelity preserves request intensity but not client think times or cache behaviors. The single-threaded application constraint (GOMAXPROCS=1, /fib?n=33) creates reproducible saturation. It does not represent typical multi-threaded web applications. The artificial node capacity constraint forces autoscaler triggers at lower loads than production. All results should be interpreted as mechanism validation, not as production-representative performance guarantees.
