# Chapter 1: Introduction (Pendahuluan)

## 1.1 Background (Latar Belakang)

The adoption of cloud computing has accelerated substantially over the past decade, transforming how organizations deploy, scale, and manage software systems. According to the Flexera 2023 State of the Cloud Report, 87% of enterprises have adopted a multi-cloud strategy, reflecting an industry-wide shift toward cloud-native architectures that can adapt to fluctuating demand while controlling operational costs. This growth has given rise to two dominant paradigms for deploying cloud-native applications: container orchestration and serverless computing. Each paradigm offers distinct advantages but also imposes trade-offs that become significant under dynamic, real-world workload conditions.

**Kubernetes** has become the de facto standard for container orchestration, providing automated deployment, horizontal scaling, and self-healing for containerized applications. Kubernetes manages workloads across clusters of machines through declarative configuration and a control loop architecture. Its Horizontal Pod Autoscaler (HPA) monitors resource utilization metrics—such as CPU and memory usage—and adjusts the number of running pods accordingly. However, HPA operates reactively: it responds to observed metric thresholds rather than anticipating future demand. This reactive behavior introduces a critical gap between the onset of a workload surge and the completion of scaling actions, during which Service Level Objective (SLO) violations may occur. Furthermore, Kubernetes requires manual or semi-automated capacity planning; over-provisioning wastes resources, while under-provisioning risks performance degradation.

**Serverless computing**, as exemplified by platforms such as AWS Lambda, Google Cloud Functions, and the open-source Knative framework, offers a contrasting model in which developers deploy individual functions without managing the underlying infrastructure. The cloud platform automatically provisions compute resources per invocation and scales to zero when idle, eliminating the need for capacity planning. However, serverless introduces its own challenges. Cold start latency—the delay incurred when a function instance must be initialized from scratch—can add tens to hundreds of milliseconds to response time, depending on the runtime and function complexity. Additionally, serverless cost scales linearly with invocation count, making it expensive for sustained high-throughput workloads. Execution time limits and constrained resource allocations further restrict its applicability for long-running or compute-intensive tasks.

These complementary strengths and weaknesses motivate a **hybrid approach** that routes traffic between Kubernetes and serverless backends based on current and anticipated workload conditions. Under such an architecture, Kubernetes handles baseline traffic where its always-warm pods deliver consistent low latency and cost-efficient resource utilization, while serverless absorbs traffic spikes where its near-instantaneous scaling prevents the queuing delays associated with Kubernetes pod provisioning. The key challenge lies in deciding *when* and *how much* traffic to route to each backend—a decision that requires awareness of both current system state and future workload trajectory.

Effective traffic routing in a hybrid system depends on observed capacity and tail latency, while workload prediction provides lead time for scaling. If the system can forecast incoming traffic patterns with sufficient accuracy and a horizon longer than provisioning delay, Algorithm 2 can proactively scale Kubernetes replicas before demand exceeds available capacity. Algorithm 1 still routes from observed load, ready capacity, and SLO state; GRU output does not directly set routing weights. Time-series forecasting using deep learning models has shown promise in this domain. In particular, the Gated Recurrent Unit (GRU) neural network architecture offers an attractive balance between prediction accuracy and computational efficiency.

The algorithmic foundation for this research builds on the **ElaX algorithm** proposed by Yang et al. (2019), which addresses elastic resource provisioning in containerized environments. ElaX defines a two-layer decision framework: Algorithm 1 governs traffic routing between execution platforms, while Algorithm 2 manages cluster-level resource scaling (e.g., adding or removing nodes). This research modifies ElaX by using observed capacity and SLO-aware logic for routing, and by integrating GRU-based workload prediction into Algorithm 2 for proactive Kubernetes replica scaling. The cluster-level scaling component is integrated into the routing daemon for real-time replica scaling.

This thesis investigates whether a hybrid Kubernetes-serverless architecture, augmented with GRU-based workload prediction and SLO-aware routing decisions, can effectively manage elastic scalability in heterogeneous cloud environments. The research designs, implements, and evaluates each component of this system—the prediction model, the routing controller, and the integrated hybrid architecture—through systematic experimentation on both synthetic and real-world workload traces.

## 1.2 Problem Formulation (Rumusan Masalah)

Based on the background analysis presented above, this research addresses the following research questions:

1. **How to design workload traffic prediction for a web application using GRU?**
   This question concerns the design and training of a GRU neural network model for time-series prediction of HTTP request traffic. It encompasses the selection of input features and the final 9-step prediction horizon at 15-second control resolution (135 seconds), the generation and use of synthetic training data that captures representative workload patterns (diurnal cycles, bursty spikes, gradual ramps), and the validation of prediction accuracy against real HTTP trace datasets (ClarkNet and Calgary). The model must achieve prediction latency suitable for real-time control (target: inference under 50 milliseconds).

2. **How to design and implement decision making by modifying the ElaX algorithm for scaling on a server cluster and distributing traffic to different cluster types?**
   This question addresses the modification of the ElaX decision layers for heterogeneous backends. Algorithm 1 uses observed load, ready capacity, and SLO monitoring to adjust traffic weights, while Algorithm 2 integrates the GRU forecast for proactive Kubernetes replica scaling. The routing controller implements a priority-based decision framework in which SLO recovery takes precedence over predictive scaling and cost optimization.

3. **How to evaluate the modified ElaX mechanism for automatic scaling and load distribution in a Kubernetes and serverless integrated environment?**
   This question concerns the experimental methodology for evaluating the hybrid system across multiple dimensions: prediction accuracy (RMSE, MAE, MAPE), system performance (tail latency, throughput, error rate), and cost efficiency. The evaluation compares four scenarios—K8s + HPA Baseline, Knative-Only (KPA), hybrid-reactive, and hybrid-predictive—to validate both the correctness of individual mechanisms and the integrated system behavior.

## 1.3 Research Objectives (Tujuan Penelitian)

The objectives of this research are:

1. **Design and implement a GRU-based workload prediction model** capable of forecasting HTTP traffic patterns for proactive Kubernetes scaling. The model is trained on synthetic workload patterns that represent common traffic shapes (diurnal, bursty, ramp) and validated against real HTTP trace datasets (ClarkNet and Calgary). The target accuracy is an RMSE below 10% of the normalized traffic range on synthetic test data, with inference latency under 50 milliseconds.

2. **Develop a modified ElaX algorithm** that integrates workload prediction with SLO-aware routing decisions in a hybrid Kubernetes-serverless architecture. Specifically:
   - Algorithm 1 (Routing Controller): a fully implemented routing decision engine that uses observed load, ready capacity, and real-time SLO monitoring (99th percentile tail latency), with the priority-based action framework **SCALE_OUT > PREDICTIVE > OPTIMIZE_COST > MAINTAIN**. GRU prediction does not directly increase routing weights.
   - Algorithm 2 (Cluster Controller): integrated into the routing daemon for real-time Kubernetes replica scaling using the resource model $R = \alpha \cdot x + \beta$, operating in reactive mode (S3, using observed load) or predictive mode (S4, using the GRU forecast).

3. **Evaluate the hybrid system** through systematic experimentation encompassing:
   - Prediction model accuracy on both synthetic and real-world trace data.
   - Mechanism validation: confirming that routing weight adjustment, serverless backend engagement, and predictive action triggering function correctly.
   - Multi-scenario comparison across K8s-only (S1), Knative-only with KPA autoscaling (S2), hybrid-reactive (S3), and hybrid-predictive (S4) configurations.
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

1. **GRU-Based Workload Predictor for HTTP Traffic Scaling**

   A multi-point prediction model based on the GRU architecture, designed for a 9-step (9 × 15 seconds = 135 seconds) forecast of HTTP request traffic. The model is trained on synthetic workload patterns that encode common traffic shapes—diurnal cycles, random bursts, and gradual ramps—achieving a post-HPO test RMSE of 4.75% (6.01% before HPO). Validation against real HTTP trace logs (ClarkNet at 5-minute aggregation) demonstrates diminished accuracy (RMSE 17.78%), which is expected given the non-stationarity and irregular burst patterns present in real-world traces. The forecast is used for proactive scaling, not direct routing-weight changes.

2. **Modified ElaX Routing and Scaling Controllers with SLO-Aware Hybrid Logic**

   A V3 routing controller (Algorithm 1) that uses observed capacity, load, and tail latency to shift traffic between Kubernetes and Knative, combined with an integrated cluster controller (Algorithm 2). The latter uses the resource model $R = \alpha x + \beta$ and the GRU forecast in S4 to pre-scale Kubernetes replicas. The priority hierarchy is **SCALE_OUT > PREDICTIVE > OPTIMIZE_COST > MAINTAIN**, with no separate SCALE_IN action.

3. **Multi-Scenario Evaluation Framework with Transparent Validity Assessment**

   A structured evaluation methodology that assesses the hybrid system across four deployment scenarios (S1–S4) using prediction accuracy metrics (RMSE, MAE, MAPE), system performance metrics (p99 latency, throughput, error rate), and cost analysis. The framework includes mechanism validation experiments (Phase A1) that confirm the correct operation of individual components under controlled conditions, replicated comparison experiments (Phase B) with randomized run ordering and statistical analysis, and an explicit threats-to-validity assessment that documents testbed limitations (localhost routing bias, GRU server unavailability in Phase B, load insufficiency) and their impact on the interpretability of results. This transparency distinguishes validated mechanism claims from unestablished superiority claims.

## 1.6 Problem Constraints (Batasan Masalah)

To maintain a focused research scope, the following constraints are applied:

1. **Platform**: The Kubernetes deployment uses K3s, a lightweight certified Kubernetes distribution optimized for resource-constrained environments. The serverless platform uses Knative Serving deployed on the same K3s cluster, with Kourier as the ingress controller. Traffic distribution is managed by HAProxy as the external load balancer.

2. **Prediction Model**: The workload prediction model uses the GRU (Gated Recurrent Unit) architecture exclusively. Comparison with alternative architectures (LSTM, Transformer, statistical models) is limited to literature review; no empirical head-to-head comparison is conducted within this research.

3. **Training Data**: The GRU model is trained on synthetic workload patterns generated to represent common HTTP traffic shapes (diurnal cycles, bursty spikes, gradual ramps). Real HTTP trace datasets—ClarkNet (August 1995) and Calgary (October 1994)—are used for validation of model generalization, not for training.

4. **Metrics Focus**: The primary performance metrics are tail latency (99th percentile), throughput (requests per second), and error rate. Cost analysis is based on proxy estimation using public cloud pricing models rather than actual cloud billing data.

5. **SLO Target**: The SLO threshold is set at 200 milliseconds for 99th percentile (p99) response latency. This threshold is used consistently across all experimental scenarios as the trigger for reactive scaling actions.

6. **Environment**: All experiments are conducted on a multi-node local development cluster (k3d) running on a single physical machine, with two bounded workload nodes and dynamically provisioned workload nodes. Docker `--cpus` limits bound node capacity to exercise pending pods, node provisioning, and serverless offload. This stress-harness constraint affects absolute performance measurements; results are interpreted as controlled mechanism and comparison evidence rather than production-representative cloud benchmarks.

7. **Traffic Pattern**: The research scope is limited to HTTP request-response workloads. Streaming, batch processing, WebSocket, and other communication patterns are not addressed.

## 1.7 Writing Systematics (Sistematika Penulisan)

This thesis is organized into the following chapters:

**Chapter 1: Introduction (Pendahuluan)** presents the research background, problem formulation, objectives, benefits, contributions, and constraints that define the scope of this work.

**Chapter 2: Literature Review (Tinjauan Pustaka)** reviews the theoretical foundations and prior work relevant to this research, including cloud computing architectures, Kubernetes container orchestration, serverless computing and Knative, workload prediction using recurrent neural networks (with emphasis on GRU), the ElaX algorithm for elastic provisioning, and SLO-based autoscaling. This chapter establishes the research gap that motivates the proposed hybrid approach.

**Chapter 3: Research Methodology (Metodologi Penelitian)** describes the research design, system architecture, experimental methodology, and evaluation metrics. It details the GRU model design, the modified ElaX algorithm specification (Algorithms 1 and 2), the four experimental scenarios (S1–S4), the phased experiment structure (Phase A1 mechanism validation, Phase B replicated comparison, Phase C dynamic workload), and the statistical analysis approach.

**Chapter 4: Implementation and Testing (Implementasi dan Pengujian)** presents the implementation of the prediction server, routing daemon, monitoring infrastructure, and load testing framework. It describes the experimental setup, execution of each experimental phase, and the raw results obtained from each scenario.

**Chapter 5: Results and Discussion (Hasil dan Pembahasan)** analyzes the experimental results across three dimensions: prediction model accuracy (synthetic and real-world traces), system performance (latency, throughput, SLO compliance across scenarios), and cost efficiency. This chapter provides an honest interpretation of results in light of the documented threats to validity, distinguishing between validated mechanisms and claims that could not be established due to testbed limitations.

**Chapter 6: Conclusion and Future Work (Kesimpulan dan Saran)** summarizes the research findings, states the conclusions that can be drawn from the evidence, and identifies directions for future work including cloud deployment, dynamic workload experimentation, and extended model comparison.
