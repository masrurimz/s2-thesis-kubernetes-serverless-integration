# Chapter 1: Introduction (Pendahuluan)

## 1.1 Background (Latar Belakang)

The adoption of cloud computing has accelerated substantially over the past decade, transforming how organizations deploy, scale, and manage software systems. According to the Flexera 2023 State of the Cloud Report, 87% of enterprises have adopted a multi-cloud strategy, reflecting an industry-wide shift toward cloud-native architectures that can adapt to fluctuating demand while controlling operational costs. This growth has given rise to two dominant paradigms for deploying cloud-native applications: container orchestration and serverless computing. Each paradigm offers distinct advantages but also imposes trade-offs that become significant under dynamic, real-world workload conditions.

**Kubernetes** has become the de facto standard for container orchestration, providing automated deployment, horizontal scaling, and self-healing for containerized applications. Kubernetes manages workloads across clusters of machines through declarative configuration and a control loop architecture. Its Horizontal Pod Autoscaler (HPA) monitors resource utilization metrics—such as CPU and memory usage—and adjusts the number of running pods accordingly. However, HPA operates reactively: it responds to observed metric thresholds rather than anticipating future demand. This reactive behavior introduces a critical gap between the onset of a workload surge and the completion of scaling actions, during which Service Level Objective (SLO) violations may occur. Furthermore, Kubernetes requires manual or semi-automated capacity planning; over-provisioning wastes resources, while under-provisioning risks performance degradation.

**Serverless computing**, as exemplified by platforms such as AWS Lambda, Google Cloud Functions, and the open-source Knative framework, offers a contrasting model in which developers deploy individual functions without managing the underlying infrastructure. The cloud platform automatically provisions compute resources per invocation and scales to zero when idle, eliminating the need for capacity planning. However, serverless introduces its own challenges. Cold start latency—the delay incurred when a function instance must be initialized from scratch—can add tens to hundreds of milliseconds to response time, depending on the runtime and function complexity. Additionally, serverless cost scales linearly with invocation count, making it expensive for sustained high-throughput workloads. Execution time limits and constrained resource allocations further restrict its applicability for long-running or compute-intensive tasks.

These complementary strengths and weaknesses motivate a **hybrid approach** that routes traffic between Kubernetes and serverless backends based on current and anticipated workload conditions. Under such an architecture, Kubernetes handles baseline traffic where its always-warm pods deliver consistent low latency and cost-efficient resource utilization, while serverless absorbs traffic spikes where its near-instantaneous scaling prevents the queuing delays associated with Kubernetes pod provisioning. The key challenge lies in deciding *when* and *how much* traffic to route to each backend—a decision that requires awareness of both current system state and future workload trajectory.

Effective traffic routing in a hybrid system therefore depends on **workload prediction**. If the system can forecast incoming traffic patterns with sufficient accuracy and lead time, it can proactively shift routing weights before demand exceeds the capacity of the Kubernetes backend. This predictive capability transforms the scaling decision from a reactive recovery action into a proactive optimization, reducing SLO violations and improving resource utilization. Time-series forecasting using deep learning models has shown promise in this domain. In particular, the Gated Recurrent Unit (GRU) neural network architecture offers an attractive balance between prediction accuracy and computational efficiency. GRU networks achieve comparable performance to Long Short-Term Memory (LSTM) networks on many time-series tasks while requiring fewer parameters, resulting in faster training and lower inference latency—a practical advantage for real-time prediction in production systems (Mondal et al., 2023).

The algorithmic foundation for this research builds on the **ElaX algorithm** proposed by Yang et al. (2019), which addresses elastic resource provisioning in containerized environments. ElaX defines a two-layer decision framework: Algorithm 1 governs traffic routing between execution platforms, while Algorithm 2 manages cluster-level resource scaling (e.g., adding or removing nodes). This research proposes a modification to ElaX that integrates GRU-based workload prediction into the routing decision layer (Algorithm 1) and extends the decision logic to incorporate SLO-aware routing between Kubernetes and serverless backends. The cluster-level scaling component (Algorithm 2) is proposed as a proof-of-concept design but is not the primary focus of the experimental evaluation, which concentrates on the routing and prediction mechanisms.

This thesis investigates whether a hybrid Kubernetes-serverless architecture, augmented with GRU-based workload prediction and SLO-aware routing decisions, can effectively manage elastic scalability in heterogeneous cloud environments. The research designs, implements, and evaluates each component of this system—the prediction model, the routing controller, and the integrated hybrid architecture—through systematic experimentation on both synthetic and real-world workload traces.

## 1.2 Problem Formulation (Rumusan Masalah)

Based on the background analysis presented above, this research addresses the following research questions:

1. **How to design workload traffic prediction for a web application using GRU?**
   This question concerns the design and training of a GRU neural network model for time-series prediction of HTTP request traffic. It encompasses the selection of input features and prediction horizon, the generation and use of synthetic training data that captures representative workload patterns (diurnal cycles, bursty spikes, gradual ramps), and the validation of prediction accuracy against real HTTP trace datasets (ClarkNet and Calgary). The model must achieve prediction latency suitable for real-time routing decisions (target: inference under 50 milliseconds).

2. **How to design and implement decision making by modifying the ElaX algorithm for scaling on a server cluster and distributing traffic to different cluster types?**
   This question addresses the modification of the ElaX algorithm's routing layer (Algorithm 1) to integrate GRU prediction outputs with SLO monitoring for hybrid traffic distribution. The routing controller must implement a priority-based decision framework—where SLO violation triggers take precedence over predictive actions—and dynamically adjust traffic weights between Kubernetes and serverless backends. The cluster-level scaling component (Algorithm 2) is proposed as a design contribution and implemented as a proof-of-concept.

3. **How to evaluate the modified ElaX mechanism for automatic scaling and load distribution in a Kubernetes and serverless integrated environment?**
   This question concerns the experimental methodology for evaluating the hybrid system across multiple dimensions: prediction accuracy (RMSE, MAE, MAPE), system performance (tail latency, throughput, error rate), and cost efficiency. The evaluation compares four scenarios—K8s-only, serverless-only, hybrid-reactive, and hybrid-predictive—to validate both the correctness of individual mechanisms and the integrated system behavior.

## 1.3 Research Objectives (Tujuan Penelitian)

The objectives of this research are:

1. **Design and implement a GRU-based workload prediction model** capable of forecasting HTTP traffic patterns for use in real-time routing decisions. The model is trained on synthetic workload patterns that represent common traffic shapes (diurnal, bursty, ramp) and validated against real HTTP trace datasets (ClarkNet and Calgary). The target accuracy is an RMSE below 10% of the normalized traffic range on synthetic test data, with inference latency under 50 milliseconds.

2. **Develop a modified ElaX algorithm** that integrates workload prediction with SLO-aware routing decisions in a hybrid Kubernetes-serverless architecture. Specifically:
   - Algorithm 1 (Routing Controller): a fully implemented routing decision engine that combines GRU prediction output, real-time SLO monitoring (99th percentile tail latency), and a priority-based action framework (SCALE_OUT > PREDICTIVE > OPTIMIZE > MAINTAIN) to dynamically distribute traffic between Kubernetes and Knative serverless backends.
   - Algorithm 2 (Cluster Controller): a proposed design for cluster-level resource scaling, implemented as a proof-of-concept to demonstrate the architectural integration with Algorithm 1.

3. **Evaluate the hybrid system** through systematic experimentation encompassing:
   - Prediction model accuracy on both synthetic and real-world trace data.
   - Mechanism validation: confirming that routing weight adjustment, serverless backend engagement, and predictive action triggering function correctly.
   - Multi-scenario comparison across K8s-only (S1), serverless-only (S2), hybrid-reactive (S3), and hybrid-predictive (S4) configurations.
   - Honest assessment of experimental limitations, including testbed constraints that affect performance comparisons.

## 1.4 Research Benefits (Manfaat Penelitian)

### Academic Benefits

- Contributes to the body of knowledge on hybrid cloud architectures by demonstrating a concrete integration of container orchestration and serverless computing with machine learning-based prediction.
- Provides a reproducible methodology for evaluating hybrid routing mechanisms, including a transparent assessment of testbed limitations and their impact on experimental validity.
- Extends the ElaX algorithm framework with prediction-integrated routing logic and SLO-aware decision making, offering a reference design for future research on elastic scalability in heterogeneous cloud environments.

### Practical Benefits

- Demonstrates a working architecture for intelligent traffic routing between Kubernetes and serverless backends that can serve as a blueprint for production hybrid deployments.
- Validates that GRU-based prediction can operate within the latency constraints required for real-time routing decisions, supporting its practical applicability in autoscaling systems.
- Provides empirical data on the trade-offs between different deployment strategies (pure Kubernetes, pure serverless, hybrid-reactive, hybrid-predictive), informing architectural decisions for cloud practitioners.

## 1.5 Research Contribution (Kontribusi Penelitian)

This research makes three primary contributions:

1. **GRU-Based Workload Predictor for HTTP Traffic Routing**

   A multi-point prediction model based on the GRU architecture, designed for forecasting HTTP request traffic at a 30-second prediction horizon. The model is trained on synthetic workload patterns that encode common traffic shapes—diurnal cycles, random bursts, and gradual ramps—achieving a test RMSE of 6.01% and MAE of 4.91% on synthetic data. Validation against real HTTP trace logs (ClarkNet at 5-minute aggregation) demonstrates that the model generalizes with diminished accuracy (RMSE 17.78%), which is expected given the non-stationarity and irregular burst patterns present in real-world traces. The model operates with approximately 40 milliseconds inference latency, meeting the real-time constraint for integration with the routing controller. Prediction confidence scores (range 0.72–0.88 observed in live operation) provide a gating mechanism for the routing controller to modulate its reliance on predictions.

2. **Modified ElaX Routing Controller with SLO-Aware Hybrid Decision Logic**

   A routing controller (Algorithm 1) that extends the ElaX framework with three capabilities: (a) integration with GRU prediction output to enable proactive traffic redistribution before SLO violations occur, (b) dynamic weight adjustment between Kubernetes and Knative serverless backends using a graduated shifting mechanism (100/0 → 90/10 → ... → 50/50), and (c) a priority-based action hierarchy (SCALE_OUT, PREDICTIVE, OPTIMIZE, MAINTAIN) that ensures SLO violation recovery takes precedence over predictive optimization. The cluster-level scaling controller (Algorithm 2) is proposed as a design contribution and implemented as a proof-of-concept, demonstrating the architectural feasibility of two-layer elastic scaling but not subjected to full experimental evaluation.

3. **Multi-Scenario Evaluation Framework with Transparent Validity Assessment**

   A structured evaluation methodology that assesses the hybrid system across four deployment scenarios (S1–S4) using prediction accuracy metrics (RMSE, MAE, MAPE), system performance metrics (p99 latency, throughput, error rate), and cost analysis. The framework includes mechanism validation experiments (Phase A1) that confirm the correct operation of individual components under controlled conditions, replicated comparison experiments (Phase B) with randomized run ordering and statistical analysis, and an explicit threats-to-validity assessment that documents testbed limitations (localhost routing bias, GRU server unavailability in Phase B, load insufficiency) and their impact on the interpretability of results. This transparency distinguishes validated mechanism claims from unestablished superiority claims.

## 1.6 Problem Constraints (Batasan Masalah)

To maintain a focused research scope, the following constraints are applied:

1. **Platform**: The Kubernetes deployment uses K3s, a lightweight certified Kubernetes distribution optimized for resource-constrained environments. The serverless platform uses Knative Serving deployed on the same K3s cluster, with Kourier as the ingress controller. Traffic distribution is managed by HAProxy as the external load balancer.

2. **Prediction Model**: The workload prediction model uses the GRU (Gated Recurrent Unit) architecture exclusively. Comparison with alternative architectures (LSTM, Transformer, statistical models) is limited to literature review; no empirical head-to-head comparison is conducted within this research.

3. **Training Data**: The GRU model is trained on synthetic workload patterns generated to represent common HTTP traffic shapes (diurnal cycles, bursty spikes, gradual ramps). Real HTTP trace datasets—ClarkNet (August 1995) and Calgary (October 1994)—are used for validation of model generalization, not for training.

4. **Metrics Focus**: The primary performance metrics are tail latency (99th percentile), throughput (requests per second), and error rate. Cost analysis is based on proxy estimation using public cloud pricing models rather than actual cloud billing data.

5. **SLO Target**: The SLO threshold is set at 200 milliseconds for 99th percentile (p99) response latency. This threshold is used consistently across all experimental scenarios as the trigger for reactive scaling actions.

6. **Environment**: All experiments are conducted on a single-node local development cluster (k3d) running on a single physical machine. This constraint introduces a known localhost routing bias that affects absolute performance measurements, particularly benefiting the K8s-only baseline. The experimental results are therefore interpreted as mechanism validation rather than production-representative performance benchmarks.

7. **Traffic Pattern**: The research scope is limited to HTTP request-response workloads. Streaming, batch processing, WebSocket, and other communication patterns are not addressed.

## 1.7 Writing Systematics (Sistematika Penulisan)

This thesis is organized into the following chapters:

**Chapter 1: Introduction (Pendahuluan)** presents the research background, problem formulation, objectives, benefits, contributions, and constraints that define the scope of this work.

**Chapter 2: Literature Review (Tinjauan Pustaka)** reviews the theoretical foundations and prior work relevant to this research, including cloud computing architectures, Kubernetes container orchestration, serverless computing and Knative, workload prediction using recurrent neural networks (with emphasis on GRU), the ElaX algorithm for elastic provisioning, and SLO-based autoscaling. This chapter establishes the research gap that motivates the proposed hybrid approach.

**Chapter 3: Research Methodology (Metodologi Penelitian)** describes the research design, system architecture, experimental methodology, and evaluation metrics. It details the GRU model design, the modified ElaX algorithm specification (Algorithms 1 and 2), the four experimental scenarios (S1–S4), the phased experiment structure (Phase A1 mechanism validation, Phase B replicated comparison, Phase C dynamic workload), and the statistical analysis approach.

**Chapter 4: Implementation and Testing (Implementasi dan Pengujian)** presents the implementation of the prediction server, routing daemon, monitoring infrastructure, and load testing framework. It describes the experimental setup, execution of each experimental phase, and the raw results obtained from each scenario.

**Chapter 5: Results and Discussion (Hasil dan Pembahasan)** analyzes the experimental results across three dimensions: prediction model accuracy (synthetic and real-world traces), system performance (latency, throughput, SLO compliance across scenarios), and cost efficiency. This chapter provides an honest interpretation of results in light of the documented threats to validity, distinguishing between validated mechanisms and claims that could not be established due to testbed limitations.

**Chapter 6: Conclusion and Future Work (Kesimpulan dan Saran)** summarizes the research findings, states the conclusions that can be drawn from the evidence, and identifies directions for future work including cloud deployment, dynamic workload experimentation, and extended model comparison.
