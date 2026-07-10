// Chapter 1 — Introduction (Pendahuluan)
// English-first body. Structure restored per advisory.

#counter(page).update(1)
#set page(numbering: "1")

= INTRODUCTION

The adoption of cloud computing has accelerated substantially over the past decade, transforming how organizations deploy, scale, and manage software systems. According to the Flexera 2023 State of the Cloud Report, 87% of enterprises have adopted a multi-cloud strategy, reflecting an industry-wide shift toward cloud-native architectures that can adapt to fluctuating demand while controlling operational costs. This growth has given rise to two dominant paradigms for deploying cloud-native applications: container orchestration and serverless computing. Each paradigm offers distinct advantages but also imposes trade-offs that become significant under dynamic, real-world workload conditions.

*Kubernetes* has become the de facto standard for container orchestration, providing automated deployment, horizontal scaling, and self-healing for containerized applications. Kubernetes manages workloads across clusters of machines through declarative configuration and a control loop architecture. Its Horizontal Pod Autoscaler (HPA) monitors resource utilization metrics—such as CPU and memory usage—and adjusts the number of running pods accordingly. However, HPA operates reactively: it responds to observed metric thresholds rather than anticipating future demand. This reactive behavior introduces a critical gap between the onset of a workload surge and the completion of scaling actions, during which Service Level Objective (SLO) violations may occur.

*Serverless computing*, as exemplified by platforms such as AWS Lambda, Google Cloud Functions, and the open-source Knative framework, offers a contrasting model in which developers deploy individual functions without managing the underlying infrastructure. The cloud platform automatically provisions compute resources per invocation and scales to zero when idle, eliminating the need for capacity planning. However, serverless introduces its own challenges. Cold start latency—the delay incurred when a function instance must be initialized from scratch—can add tens to hundreds of milliseconds to response time, depending on the runtime and function complexity. Additionally, serverless cost scales linearly with invocation count, making it expensive for sustained workloads.

These complementary strengths and weaknesses motivate a *hybrid approach* that routes traffic between Kubernetes and serverless backends based on current and anticipated workload conditions. Under such an architecture, Kubernetes handles baseline traffic where its always-warm pods deliver consistent low latency and cost-efficient resource utilization, while serverless absorbs traffic spikes where its near-instantaneous scaling prevents the queuing delays associated with Kubernetes pod provisioning. The key challenge lies in deciding *when* and *how much* traffic to route to each backend—a decision that requires awareness of both current system state and future workload trajectory.

Effective traffic routing in a hybrid system therefore depends on *workload prediction*. If the system can forecast incoming traffic patterns with sufficient accuracy and lead time, it can proactively shift routing weights before demand exceeds the capacity of the Kubernetes backend. This predictive capability transforms the scaling decision from a reactive recovery action into a proactive optimization, reducing SLO violations and improving resource utilization. Time-series forecasting using deep learning models has shown promise in this domain. In particular, the Gated Recurrent Unit (GRU) neural network architecture offers an attractive balance between prediction accuracy and computational efficiency.

The algorithmic foundation for this research builds on the *ElaX algorithm* proposed by @yang2019elax, which addresses elastic resource provisioning in containerized environments. ElaX defines a two-layer decision framework: Algorithm 1 governs traffic routing between execution platforms, while Algorithm 2 manages cluster-level resource scaling (e.g., adding or removing nodes). This research proposes a modification to ElaX that integrates GRU-based workload prediction into the routing decision layer (Algorithm 1) and extends the decision logic to incorporate SLO-aware routing between Kubernetes and serverless backends.

This thesis investigates whether a hybrid Kubernetes-serverless architecture, augmented with GRU-based workload prediction and SLO-aware routing decisions, can effectively manage elastic scalability in heterogeneous cloud environments. The research designs, implements, and evaluates each component of this system—the prediction model, the routing controller, and the integrated hybrid architecture—through systematic experimentation on both synthetic and real-world workload traces.

== Problem Formulation (Rumusan Masalah)

Based on the background analysis presented above, this research addresses the following research questions:

1. *How to design workload traffic prediction for a web application using GRU?*  
   This question concerns the design and training of a GRU neural network model for time-series prediction of HTTP request traffic. It encompasses the selection of input features and prediction horizon, the generation and use of synthetic training data that captures representative workload patterns (diurnal cycles, bursty spikes, gradual ramps), and the validation of prediction accuracy against real HTTP trace datasets (ClarkNet and Calgary). The model must achieve prediction latency suitable for real-time routing decisions (target: inference under 50 ms).

2. *How to design and implement decision making by modifying the ElaX algorithm for scaling on a server cluster and distributing traffic to different cluster types?*  
   This question addresses the modification of the ElaX algorithm's routing layer (Algorithm 1) to integrate GRU prediction outputs with SLO monitoring for hybrid traffic distribution. The routing controller must implement a priority-based decision framework—where SLO violation triggers take precedence over predictive actions—and dynamically adjust traffic weights between Kubernetes and serverless backends. The cluster-level scaling component (Algorithm 2) is integrated into the routing daemon for real-time Kubernetes replica scaling.

3. *How to evaluate the modified ElaX mechanism for automatic scaling and load distribution in a Kubernetes and serverless integrated environment?*  
   This question concerns the experimental methodology for evaluating the hybrid system across multiple dimensions: prediction accuracy (RMSE, MAE, MAPE), system performance (tail latency, throughput, error rate), and cost efficiency. The evaluation compares four scenarios—K8s + HPA Baseline, Knative-Only (KPA), hybrid-reactive, and hybrid-predictive—to validate both the correctness of individual mechanisms and the integrated system behavior.

== Research Objectives (Tujuan Penelitian)

The objectives of this research are:

1. *Design and implement a GRU-based workload prediction model* capable of forecasting HTTP traffic patterns for use in real-time routing decisions. The model is trained on synthetic workload patterns that represent common traffic shapes (diurnal, bursty, ramp) and validated against real HTTP trace datasets (ClarkNet and Calgary). The target accuracy is an RMSE under 10% of the normalized traffic range on synthetic test data, with inference latency under 50 ms.

2. *Develop a modified ElaX algorithm* that integrates workload prediction with SLO-aware routing decisions in a hybrid Kubernetes-serverless architecture. Specifically: Algorithm 1 (Routing Controller) combines GRU output, real-time SLO monitoring (99th percentile tail latency), and priority framework (SCALE_OUT > PREDICTIVE > OPTIMIZE > MAINTAIN); Algorithm 2 (Cluster Controller) is integrated for real-time K8s replica scaling using R = α·x + β.

3. *Evaluate the hybrid system* through systematic experimentation encompassing prediction model accuracy, mechanism validation, multi-scenario comparison (S1–S4), and honest assessment of experimental limitations.

== Research Benefits (Manfaat Penelitian)

Academic Benefits: contributes to hybrid cloud knowledge, reproducible methodology, extends ElaX.

Practical Benefits: working architecture blueprint, validates GRU latency for real-time, empirical trade-off data.

== Research Contribution (Kontribusi Penelitian)

1. GRU-Based Workload Predictor for HTTP Traffic Routing (multi-point, 30s horizon, test RMSE 6.01% synthetic, ~40ms inference).

2. Modified ElaX Routing Controller with SLO-Aware Hybrid Decision Logic (graduated weight shift, priority hierarchy, cluster scaling integration).

3. Multi-Scenario Evaluation Framework with Transparent Validity Assessment (Phase A1 mechanism + Phase B n=5 replicated, threats documented).

== Problem Constraints (Batasan Masalah)

Platform: K3s + Knative + Kourier + HAProxy.

Prediction: GRU only.

Training: synthetic + validation on ClarkNet/Calgary.

Metrics: p99, throughput, error; cost proxy.

SLO: 200 ms p99.

Environment: single-node k3d (localhost bias acknowledged).

Traffic: HTTP request-response.

== Writing Systematics (Sistematika Penulisan)

Chapter 1: Introduction (this).

Chapter 2: Literature Review.

Chapter 3: Methodology.

Chapter 4: Results and Discussion.

Chapter 5: Conclusion and Future Work.

(Full details in source markdown.)
