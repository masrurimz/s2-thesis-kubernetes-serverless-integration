// Chapter 1 — Introduction (Pendahuluan)
// English-first body. Structure restored per advisory.

= INTRODUCTION

Cloud computing adoption has accelerated over the past decade. It changed how organizations deploy, scale, and manage software systems. The Flexera 2023 State of the Cloud Report shows that 87% of enterprises use a multi-cloud strategy. This reflects an industry-wide shift toward cloud-native architectures. These architectures adapt to changing demand while controlling operational costs. This growth created two main paradigms for deploying cloud-native applications: container orchestration and serverless computing. Each paradigm offers distinct advantages. Each also imposes trade-offs. These trade-offs become significant under dynamic, real-world workload conditions.

*Kubernetes* is the de facto standard for container orchestration. It provides automated deployment, horizontal scaling, and self-healing for containerized applications. Kubernetes manages workloads across machine clusters. It uses declarative configuration and a control loop architecture. Its Horizontal Pod Autoscaler (HPA) monitors resource utilization metrics, such as CPU and memory usage. It adjusts the number of running pods to match. However, the HPA reacts to observed metric thresholds. It does not anticipate future demand. This reactive behavior creates a gap between the start of a workload surge and the end of scaling actions. Service Level Objective (SLO) violations can occur during this gap.

*Serverless computing* offers a different model. Platforms include AWS Lambda, Google Cloud Functions, and the open-source Knative framework. Developers deploy individual functions and do not manage the underlying infrastructure. The cloud platform provisions compute resources for each invocation. It scales to zero when idle. This removes the need for capacity planning. However, serverless has its own challenges. Cold start latency is the delay when a function instance starts from scratch. It can add tens to hundreds of milliseconds to response time. This depends on the runtime and function complexity. Also, serverless cost scales linearly with invocation count. It is expensive for sustained workloads.

These strengths and weaknesses motivate a *hybrid approach*. It routes traffic between Kubernetes and serverless backends based on current and expected workload conditions. Kubernetes handles baseline traffic. Its always-warm pods deliver consistent low latency and cost-efficient resource utilization. Serverless absorbs traffic spikes. Its near-instantaneous scaling prevents the queuing delays of Kubernetes pod provisioning. The key challenge is deciding *when* and *how much* traffic to route to each backend. This decision requires awareness of both current system state and future workload trajectory.

Effective hybrid control depends on knowing current conditions and the near-term workload trajectory. A forecast with enough accuracy and lead time can prepare Kubernetes replicas before demand exceeds capacity. The routing controller continues to use observed load, ready capacity, and SLO status for traffic distribution. This separation keeps the fast observed-load response of routing. It reserves prediction for the slower replica-scaling path. Time-series forecasting with deep learning models shows promise in this domain. The Gated Recurrent Unit (GRU) neural network offers a good balance between prediction accuracy and computational efficiency.

The algorithmic foundation builds on the *ElaX algorithm* proposed by @yang2019elax. ElaX combines a workload predictor, a resource allocation model $R = alpha dot.op x + beta$, and an online controller with slack-based scaling. This thesis extends ElaX with GRU-based prediction and SLO-aware cross-platform routing (Algorithm 1) and cluster scaling (Algorithm 2). These thesis-specific algorithms are not attributed to ElaX itself.

This thesis investigates whether a hybrid Kubernetes-serverless architecture can manage elastic scalability in heterogeneous cloud environments. The architecture adds GRU-based workload prediction and SLO-aware routing decisions. The research designs, implements, and evaluates each component: the prediction model, the routing controller, and the integrated hybrid architecture. It tests these components through systematic experiments on synthetic and real-world workload traces.

== Problem Formulation (Rumusan Masalah)

Based on the background analysis presented above, this research addresses the following research questions:

1. *How to design workload traffic prediction for a web application using GRU?*  
   This question concerns the design and training of a GRU neural network model. The model predicts HTTP request traffic over time. It covers the selection of input features and prediction horizon. It also covers synthetic training data that captures representative workload patterns (diurnal cycles, bursty spikes, gradual ramps). Finally, it covers validation of prediction accuracy against real HTTP trace datasets (ClarkNet and Calgary). The model must achieve prediction latency suitable for real-time routing decisions (target: inference under 50 ms).

2. *How to design and implement decision making by modifying the ElaX algorithm for scaling on a server cluster and distributing traffic to different cluster types?*  
   This question addresses the modification of ElaX's workload-prediction and resource-control layers for hybrid traffic distribution. The cluster-level scaling component (Algorithm 2) consumes the confidence-gated GRU upper forecast in predictive mode. Algorithm 1 routes using observed load, ready-replica capacity, and SLO monitoring. The routing controller uses a priority-based decision framework. SLO violation triggers take precedence over predictive actions. It also adjusts traffic weights between Kubernetes and serverless backends.

3. *How to evaluate the modified ElaX mechanism for automatic scaling and load distribution in a Kubernetes and serverless integrated environment?*  
   This question concerns the experimental methodology for evaluating the hybrid system. It evaluates several dimensions: prediction accuracy (RMSE, MAE, MAPE), system performance (tail latency, throughput, error rate), and cost efficiency. The evaluation compares four scenarios: K8s + HPA Baseline, Knative-Only (KPA), hybrid-reactive, and hybrid-predictive. These scenarios validate the correctness of individual mechanisms and the integrated system behavior.
== Hypotheses (Hipotesis)

The research questions are operationalized as three testable hypotheses:

  - #strong[H1 (hybrid vs pure)]: A hybrid Kubernetes-serverless architecture with dynamic traffic routing outperforms a pure Kubernetes baseline (HPA) in tail latency and SLO compliance at comparable cost. Tested as S4 vs S1; the result is directional at n = 1.

  - #strong[H2 (predictive vs reactive)]: Adding GRU-based workload prediction to the hybrid controller (predictive scaling) outperforms the same controller driven by observed load only (reactive scaling) on tail latency and SLO compliance at equal cost. Tested as S4 vs S3; the primary p99 comparison supports H2 (p = 0.0304, d = -1.26).

  - #strong[H3 (predictor adequacy)]: A GRU workload predictor achieves the pre-registered accuracy target (RMSE < 10% of normalized range, MAE < 5%, inference < 50 ms) on synthetic test data. The target is supported on synthetic data and only partially validated on real traces.


== Research Objectives (Tujuan Penelitian)

The objectives of this research are:

1. *Design and implement a GRU-based workload prediction model* capable of forecasting HTTP traffic patterns for real-time control decisions. The model trains on synthetic workload patterns that represent common traffic shapes (diurnal, bursty, ramp). It is validated against real HTTP trace datasets (ClarkNet and Calgary). The target accuracy is an RMSE under 10% of the normalized traffic range on synthetic test data, with inference latency under 50 ms.

2. *Develop a modified ElaX algorithm* that integrates workload prediction with SLO-aware hybrid control. Specifically: Algorithm 2 (Cluster Controller) uses the GRU confidence-gated upper forecast for Kubernetes replica scaling in predictive mode, while Algorithm 1 (Routing Controller) uses observed load and ready-replica capacity for traffic routing; its priority framework is SCALE_OUT > PREDICTIVE > OPTIMIZE_COST > MAINTAIN. Algorithm 2 uses R = α·x + β.

3. *Evaluate the hybrid system* through systematic experimentation encompassing prediction model accuracy, mechanism validation, multi-scenario comparison (S1–S4), and honest assessment of experimental limitations.

== Research Benefits (Manfaat Penelitian)

Academic Benefits: contributes to hybrid cloud knowledge, reproducible methodology, extends ElaX.

Practical Benefits: working architecture blueprint, validates GRU latency for real-time, empirical trade-off data.

== Research Contribution (Kontribusi Penelitian)

1. GRU-Based Workload Predictor for HTTP Traffic (30-sample input window at 15 s, 9-step / 135 s horizon, test RMSE 4.75% post-HPO with 6.01% as the pre-HPO manual baseline, ~40 ms inference).

2. Extended ElaX hybrid controller: prediction drives Kubernetes replica scaling (Algorithm 2). Algorithm 1 does SLO-aware routing using observed load and capacity. It uses graduated weight shifts and a priority hierarchy.

3. Multi-Scenario Evaluation Framework with Transparent Validity Assessment (Phase A1 mechanism validation, n = 1 four-scenario diagnostic, and definitive counterbalanced paired Phase B n = 5 / 10-run comparison, with threats documented).

== Problem Constraints (Batasan Masalah)

Platform: K3s + Knative + Kourier + HAProxy.

Prediction: GRU only; prediction drives Algorithm 2 replica scaling, while Algorithm 1 routing uses observed load and capacity.

Training: synthetic + validation on ClarkNet/Calgary.

Metrics: p99, throughput, error; cost proxy.

SLO: 200 ms p99.

Environment: multi-node k3d (two workload nodes, CPU-bounded, with dynamic nodes in high-load diagnostics).

Traffic: HTTP request-response.

== Writing Systematics (Sistematika Penulisan)

Chapter 1: Introduction (this).

Chapter 2: Literature Review.

Chapter 3: Methodology.

Chapter 4: Results and Discussion.

Chapter 5: Conclusion and Future Work.

(Full details in source markdown.)
