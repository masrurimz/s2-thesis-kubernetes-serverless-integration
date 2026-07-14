= METHODOLOGY

This chapter explains the methodology used to answer the research questions and achieve the objectives. It covers the research flow, data collection, system architecture, implementation of the prediction model and online controllers, and the evaluation plan including experimental scenarios, metrics, and threats to validity.

== Research Flow

The research follows a six-phase methodology, progressing from theoretical foundations through system design, implementation, and experimental evaluation.

Literature Study surveys cloud computing architectures, workload prediction methods, and elastic scaling algorithms to establish the theoretical foundation and identify the research gap. Data Collection generates synthetic workload patterns for GRU model training, supplemented by real HTTP trace datasets (ClarkNet and Calgary) for baseline comparison and validation. Method Design specifies the hybrid Kubernetes-serverless architecture, routing and scaling algorithms, and SLO-based decision framework. Implementation develops the GRU prediction server, routing controller (Algorithm 1), integrated cluster controller (Algorithm 2) with real Kubernetes replica scaling, monitoring infrastructure, and traffic routing layer. Evaluation conducts systematic experimental evaluation across four deployment scenarios with mechanism validation (Phase A1), trace-driven replicated comparison using ClarkNet replay (Phase B), dynamic burst validation (Phase C), and statistical analysis. Report Writing documents findings with truth-aligned claims that distinguish validated mechanisms from unestablished superiority claims.

Each phase produces artifacts that feed into subsequent phases: the literature study informs the system design, the collected data trains the prediction model, the implemented system undergoes experimental evaluation, and the evaluation results inform the thesis conclusions.

#figure(
  image("../figures/image11.png", width: 60%),
  caption: [Research methodology flow],
) <fig:research-flow>

== Data Collection

The GRU prediction model requires time-series workload data for training and validation. Two data sources are used: synthetic workload patterns generated to encode common traffic shapes (diurnal cycles, random bursts, and gradual ramps), and real HTTP trace datasets from ClarkNet (NASA ClarkNet WWW server, August 1995, mean 3.27 RPS per second) and Calgary (University of Calgary, October 1994, mean 1.20 RPS per second).

The synthetic generator produces configurable traffic patterns at 1-second RPS resolution with parameters for diurnal amplitude, burst frequency, and ramp slope. A 72-hour synthetic dataset is generated and split 70/15/15 into training, validation, and test sets. Real traces are aggregated to 1-minute, 5-minute, and 10-minute intervals to assess the effect of temporal resolution on prediction accuracy. The same model architecture and hyperparameters trained on synthetic data are applied to real traces for generalization assessment.

== System Architecture

The proposed system integrates three subsystems: an offline training pipeline, an online prediction and control plane, and a hybrid execution infrastructure. The architecture follows a two-layer design inspired by the ElaX algorithm framework, where Algorithm 1 governs traffic routing between execution platforms and Algorithm 2 manages cluster-level resource scaling. Both algorithms are integrated into a single routing daemon that executes them in a coordinated 15-second control loop: Algorithm 1 provides immediate traffic shedding to serverless, while Algorithm 2 scales Kubernetes replicas to restore capacity, after which Algorithm 1 returns traffic to Kubernetes.

=== Infrastructure Components

HAProxy serves as the entry point for all HTTP traffic, distributing requests between the Kubernetes and serverless backends according to weighted routing rules. Weights are dynamically adjusted by Algorithm 1 through the HAProxy Runtime API (TCP socket interface). HAProxy also exposes a statistics endpoint that provides real-time throughput and latency metrics consumed by the monitoring subsystem.

K3s (Kubernetes Backend) is a lightweight, certified Kubernetes distribution deployed via k3d (k3s-in-Docker). K3s runs the primary application workload as always-warm pods, providing consistent low-latency responses for baseline traffic. In this study, K3s serves as the baseline warm capacity; relative cost advantage is evaluated empirically per run rather than assumed a priori.

Knative Serving (Serverless Backend) is deployed on the same K3s cluster using Kourier as the ingress controller. Knative provides scale-to-zero capability and rapid autoscaling for burst traffic. When the routing controller enables the serverless backend, Knative automatically manages pod lifecycle including cold start initialization. The serverless backend is engaged only when SLO violations occur or when the GRU model predicts an imminent load surge.

=== Monitoring and Metrics Collection

The system uses Prometheus for metrics collection and an SLO monitor component for real-time compliance checking. Prometheus scrapes HAProxy statistics at 1-second intervals, collecting request counts, response times, and backend health status. The SLO Monitor computes the 99th percentile (p99) tail latency from Prometheus time-series data and maintains a rolling violation window to detect sustained SLO breaches.

== Implementation

=== Workload Predictor (GRU Architecture)

The workload prediction model uses a Gated Recurrent Unit (GRU) neural network with a single recurrent layer of 128 hidden units followed by head dropout regularization. The model accepts a 30-sample input window of per-interval request counts (sampled at 15-second resolution) and outputs direct multi-horizon forecasts for nine 15-second steps ahead (135 seconds total), eliminating autoregressive error compounding. Training uses the Adam optimizer with Mean Squared Error loss, batch size 32, and early stopping with patience of 15 epochs (maximum 100). Per-horizon upper offsets, derived as the 90th percentile of positive validation residuals, are added to the point forecasts to form a conservative upper envelope (`upper_forecasts`) that directly addresses ramp underprediction.

The extended 9-step horizon (135 s) covers the K3dAutoscaler's maximum provisioning delay (120 s) plus a 15-second safety margin, following the self-calibrating approach of ADAPT @adapt2026. The forecast horizon is validated at runtime via the model-status endpoint.

The trained model is served via a FastAPI prediction server that accepts recent request-rate history as input and returns point forecasts, upper-envelope forecasts, and a scalar confidence score. The confidence score is derived from the model's normalized validation error (RMSE relative to the training-set mean) rather than prediction variance: a score of 0.8 indicates the model's error is below 15% of the mean. The routing controller gates proactive actions on this confidence exceeding a configurable threshold (default: 0.5).

=== Resource Allocation Model

where R is the target replica count, x is predicted or observed traffic intensity (requests per second), alpha is the resource-per-request coefficient (replicas per RPS), and beta is base replica overhead (minimum replicas at near-zero traffic). The coefficient alpha is derived from a calibrated saturation measurement: alpha = 1/r_effective, where r_effective = r_saturation_per_replica × target_cpu_util. At each control interval, the daemon computes a target replica count with a safety buffer gamma (typically 1.0), clamped to fixed bounds [3, 6] on the current testbed (two workload nodes at 300 millicores each).

=== Algorithm 1: Routing Controller

Algorithm 1 is the primary decision engine. It monitors SLO compliance and adjusts traffic routing weights between Kubernetes and serverless backends using a priority-based decision framework with four action types:

SCALE_OUT (Priority 1): When p99 latency exceeds the SLO threshold (200ms) for a sustained violation window, traffic is shifted toward the serverless backend by incrementing its weight in steps of 10%.

PREDICTIVE (Priority 2): When the system is healthy but the GRU model predicts a load increase exceeding 30% with confidence above 0.5, serverless is preemptively engaged to avoid a future SLO violation.

OPTIMIZE_COST (Priority 3): When p99 latency is well within the healthy margin (under 70% of the SLO threshold), serverless usage is gradually reduced to save cost.

MAINTAIN (Priority 4): When none of the above conditions are met, current weights are preserved.

Traffic weights shift gradually in increments of 10% to avoid oscillation, from 100/0 (K8s only) through 90/10, 80/20, 70/30, 60/40, to a maximum of 50/50. When serverless is first enabled, the controller sends a synthetic health-check request to the Knative service endpoint to trigger cold start initialization, reducing the latency penalty when actual traffic begins routing.

=== Algorithm 2: Cluster Controller

Algorithm 2 operates in two modes that share the same capacity model. In reactive mode (S3), the scaling signal is the mean observed RPS over the last 30 seconds. In predictive mode (S4), the daemon computes a predictive target from the GRU confidence-gated upper forecast and selects it only when it *strictly exceeds* the observed target; otherwise the observed target is used. A proactive hold interval (90 seconds) prevents premature rollback of a proactive scale-up while the forecast window is still active. In both scenarios, the V3 routing controller routes by *observed* ready-replica capacity; the forecast influences only Kubernetes replica planning, not the HAProxy weight split. This separation prevents over-routing to serverless during moderate load — a problem observed when the forecast directly drove routing weights.

Scaling is performed by invoking kubectl scale deployment, chosen for its determinism and explicit audit trail. Safety checks include cooldown periods (15 seconds for scale-up, 300 seconds for scale-down in V3 mode), replica bounds clamping, scale-down hysteresis (target below 50% of current capacity), and readiness verification before traffic returns to Kubernetes.

=== Node-Level Consolidation

The K3dAutoscaler implements utilization-based node consolidation matching the Kubernetes Cluster Autoscaler semantics @k8sca-faq: a dynamic node is a candidate for removal when its CPU request utilization falls below 50% of allocatable capacity @serracanta2025hpa, all workload pods can be rescheduled onto other nodes, and the node has remained underutilized for at least 90 seconds. The kubectl drain command evicts pods before deletion. A 120-second cooldown prevents cascading deletions @tinyautoscalers2022. Pod-level scale-down uses a 120-second cooldown and 0.75 utilization threshold.

== Evaluation Plan

=== Evaluation Scenarios

Four scenarios are defined to compare platform-native autoscaling baselines against the custom hybrid control plane, and to isolate the value of GRU prediction within the hybrid architecture:

S1 (K8s + HPA Baseline): 100% traffic to Kubernetes, HPA native CPU-based autoscaling, GRU off.

S2 (Knative-Only KPA): 100% traffic to Knative via HAProxy, KPA concurrency-based autoscaling with scale-to-zero, GRU off.

S3 (Hybrid Reactive): Dynamic K8s to Knative routing via Algorithm 1, Algorithm 2 scaling using observed RPS (observed), GRU off.

S4 (Hybrid Predictive): Dynamic K8s to Knative routing via Algorithm 1, Algorithm 2 scaling using GRU forecast (predicted), GRU on.

The S1 vs S2 comparison evaluates platform-native baselines. The S3 vs S1/S2 comparison evaluates whether the hybrid reactive control plane improves over either baseline alone. The S3 vs S4 comparison is designed to isolate the value of GRU prediction—both use hybrid routing and Algorithm 2 scaling, and both route by observed load. S4 additionally consumes the confidence-gated upper forecast for Kubernetes replica planning. A practical caveat applies: because the scaling model maps load to replicas via ceil(alpha dot.op x dot.op gamma) clamped to a minimum of three replicas, moderate-load forecasts (e.g., 62 RPS) can map to the same replica target as the observed signal, making the predictive and reactive paths operationally identical for that cycle. The comparison is therefore only discriminative when the forecast produces a *different* replica target than the observed signal—a condition that depends on the calibration margin and is analyzed in Chapter 4.

=== Evaluation Phases

Phase A0 validates infrastructure and autoscaler mechanisms. Phase A1 validates individual system mechanisms under a controlled ramp load. Phase B conducts replicated comparison with ClarkNet trace-driven workload (40 stages, 30 seconds each, RPS 22 to 164, mean 73) with n=5 replications per scenario and randomized run order. Phase C stresses the system with controlled burst profiles.

=== Metrics

User-perceived performance metrics include p50, p95, and p99 latency, error rate, and achieved throughput. The primary SLO metric is p99 latency with a threshold of 200ms. Routing and control-plane metrics include weight change count, time-in-serverless percentage, prediction usage rate, and control-loop latency. Kubernetes replica scaling metrics include desired replicas, current replicas, ready replicas, scale-up/down events and latencies, and oscillation index. Resource and cost proxy metrics include CPU/memory utilization, K8s capacity time, Knative active time, and cost-normalized metrics (USD/1M requests, USD/1M SLO-compliant requests).

=== Statistical Analysis Protocol

The paired S3/S4 comparison uses a pre-specified primary endpoint (p99 latency) with permutation testing (n=5, one-sided). Secondary endpoints (p95, SLO violations, throughput, error rate) are reported with Bonferroni-corrected p-values; only the primary endpoint may be claimed as statistically significant.

=== Threats to Validity

The experimental evaluation is subject to several documented threats. The localhost routing bias of the single-node k3d testbed eliminates network latency between components, limiting absolute performance comparison interpretability. Historical traces (1994-1995) may not match modern application semantics. Replay fidelity preserves request intensity but not client think times or cache behaviors. The single-threaded application constraint (GOMAXPROCS=1, /fib?n=32) creates reproducible saturation but does not represent typical multi-threaded web applications. The artificial node capacity constraint forces autoscaler triggers at lower loads than production. All results should be interpreted as mechanism validation rather than production-representative performance benchmarks.
