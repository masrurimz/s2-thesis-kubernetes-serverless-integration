// Chapter 1 — Introduction (Pendahuluan)
// English-first body. Structure restored per advisory.
#import "headings.typ": H


= #H("ch1")

Cloud computing adoption has accelerated over the past decade. It changed how organizations deploy, scale, and manage software systems. In the Flexera 2023 State of the Cloud Report, 87% of the 750 respondents reported multi-cloud use @flexera2023. This reflects an industry-wide shift toward cloud-native architectures. These architectures adapt to changing demand while controlling operational costs. This growth created two main paradigms for deploying cloud-native applications: container orchestration and serverless computing. Each paradigm offers distinct advantages. Each also imposes trade-offs. These trade-offs become significant under dynamic, real-world workload conditions.

*Kubernetes* is the de facto standard for container orchestration. It provides automated deployment, horizontal scaling, and self-healing for containerized applications. Kubernetes manages workloads across machine clusters. It uses declarative configuration and a control loop architecture. Its Horizontal Pod Autoscaler (HPA) monitors resource utilization metrics, such as CPU and memory usage. It adjusts the number of running pods to match. However, the HPA reacts to observed metric thresholds. It does not anticipate future demand @hypa2023. This reactive behavior creates a gap between the start of a workload surge and the end of scaling actions. Service Level Objective (SLO) violations can occur during this gap.

*Serverless computing* offers a different model. Platforms include AWS Lambda, Google Cloud Functions, and the open-source Knative framework. Developers deploy individual functions and do not manage the underlying infrastructure @sadaqat2018serverless @savage2018going. The cloud platform provisions compute resources for each invocation. It scales to zero when idle. This removes the need for capacity planning. However, serverless has its own challenges. Cold start latency is the delay when a function instance starts from scratch @golec2023cold @yu2020characterizing. It can add tens to hundreds of milliseconds to response time. This depends on the runtime and function complexity. Also, serverless cost scales linearly with invocation count. It is expensive for sustained workloads @dehigama2024.

These strengths and weaknesses motivate a *hybrid approach* @dehigama2024. It routes traffic between Kubernetes and serverless backends based on the observed workload and the ready capacity of each backend. Kubernetes handles baseline traffic. Its always-warm pods deliver consistent low latency and cost-efficient resource utilization. Serverless absorbs traffic spikes. Its near-instantaneous scaling prevents the queuing delays of Kubernetes pod provisioning. Earlier systems already use serverless functions to cover the start-up lag of virtual machines @zhang2019mark @gunasekaran2019spock. The key challenge is deciding *when* and *how much* traffic to route to each backend. Replica scaling needs the near-term workload trajectory, so a forecast informs that decision.

Effective hybrid control depends on knowing current conditions and the near-term workload trajectory. A forecast with enough accuracy and lead time can prepare Kubernetes replicas before demand exceeds capacity @yuan2024time. The routing controller continues to use observed load, ready capacity, and SLO status for traffic distribution. This separation keeps the fast observed-load response of routing. It reserves prediction for the slower replica-scaling path. Time-series forecasting with deep learning models shows promise in this domain @mondal2023toward. The Gated Recurrent Unit (GRU) performs comparably to the LSTM on sequence modeling @chung2014empirical, and a GRU predictor of CPU usage in a Kubernetes autoscaler has been reported as both accurate and efficient @mondal2023toward.

The algorithmic foundation builds on the *ElaX algorithm* proposed by @yang2019elax. ElaX combines a workload predictor, a resource allocation model $R = alpha dot.op x + beta$, and an online controller with slack-based scaling. Its LSTM predicts 60 per-minute points once an hour, and its reservation rule takes the largest predicted workload over the next hour. This thesis changes the decision factor in three ways. First, a GRU replaces the LSTM and predicts nine 15-second steps (135 s), refreshed every 15 s. Second, Algorithm 2 keeps the largest-value rule but applies it to the GRU upper envelope and the observed target, and it holds a raised target for 90 s. Third, Algorithm 1 adds a decision that ElaX does not make, the traffic split between Kubernetes and serverless. This thesis does not reimplement the slack-based online controller or ElaX's vertical scaling. These thesis-specific algorithms are not attributed to ElaX itself.

This thesis investigates whether a hybrid Kubernetes-serverless architecture can manage elastic scalability in heterogeneous cloud environments. The architecture adds GRU-based workload prediction for replica scaling and capacity-aware traffic distribution. The research designs, implements, and evaluates each component: the prediction model, the routing controller, and the integrated hybrid architecture. It tests these components through systematic experiments on synthetic and real-world workload traces.

== #H("ch1-problem")

Based on the background analysis presented above, this research addresses the following research questions:

1. *How to design workload traffic prediction for a web application using GRU?*  
   This question concerns the design and training of a GRU neural network model. The model predicts HTTP request traffic over time. It covers the selection of input features and prediction horizon. It also covers synthetic training data that captures representative workload patterns (diurnal cycles, bursty spikes, gradual ramps). Finally, it covers validation of prediction accuracy against real HTTP trace datasets (ClarkNet and Calgary). The model must achieve prediction latency suitable for real-time routing decisions (target: inference under 50 ms).

2. *How to design and implement decision making by modifying the ElaX algorithm for scaling on a server cluster and distributing traffic to different cluster types?*  
   This question addresses the modification of ElaX's workload-prediction and resource-control layers for hybrid traffic distribution. The cluster-level scaling component (Algorithm 2) consumes the GRU upper forecast in predictive mode. Algorithm 1 sets the traffic weights between Kubernetes and serverless backends from observed load and ready-replica capacity. Routing weights do not use the forecast.

3. *How to evaluate the modified ElaX mechanism for automatic scaling and load distribution in a Kubernetes and serverless integrated environment?*  
   This question concerns the experimental methodology for evaluating the hybrid system. It evaluates several dimensions: prediction accuracy (RMSE, MAE, MAPE), system performance (tail latency, throughput, error rate), and cost efficiency. The evaluation compares four scenarios: K8s + HPA Baseline, Knative-Only (KPA), hybrid-reactive, and hybrid-predictive. These scenarios validate the correctness of individual mechanisms and the integrated system behavior.
== #H("ch1-hypotheses")

The research questions are operationalized as three testable hypotheses:

  - #strong[H1 (hybrid vs pure)]: A hybrid Kubernetes-serverless architecture with dynamic traffic routing outperforms a pure Kubernetes baseline (HPA) in tail latency and SLO compliance at comparable cost. Tested as S4 vs S1; the result is directional at n = 1.

  - #strong[H2 (predictive vs reactive)]: Adding GRU-based workload prediction to the hybrid controller (predictive scaling) outperforms the same controller driven by observed load only (reactive scaling) on tail latency and SLO compliance at equal cost. Tested as S4 vs S3. In a pre-registered batch of 10 pairs S4 ran 13.6 ms faster on average (p = 0.307), and across all 25 pairs that ran the ClarkNet-trained predictor 16.5 ms faster, but both 95% intervals span zero, so the data show no clear win. Chapter 4 also reports the earlier batches as history, including a July batch with p = 0.0312 whose predictor cannot be verified.

  - #strong[H3 (predictor adequacy)]: A GRU workload predictor achieves the pre-registered accuracy target (RMSE < 10% of normalized range, MAE < 5%, inference < 50 ms) on synthetic test data. The target is met on synthetic data under the leak-free protocol (RMSE 5.2% of the mean, MAE 4.1%) and is not met on the held-out region of the real deployment trace (RMSE 39.6% of the mean), where the network matches a linear autoregression on the same input window. A twelve-lever representation search under the leak-free fold protocol found no variant that beats the linear model, so the disclosed conclusion is that the deployed point predictor should be the linear autoregression.


== #H("ch1-objectives")

The objectives of this research are:

1. *Design and implement a GRU-based workload prediction model* capable of forecasting HTTP traffic patterns for real-time control decisions. The deployed model trains on the ClarkNet 15-second series under chronological splits with an embargo. A synthetic arm represents common traffic shapes (diurnal, bursty, ramp) and is studied separately. Validation uses real HTTP trace datasets (ClarkNet and Calgary). The target accuracy is an RMSE under 10% of the normalized traffic range on synthetic test data, with inference latency under 50 ms.

2. *Develop a modified ElaX algorithm* that integrates workload prediction with SLO-aware hybrid control. Specifically: Algorithm 2 (Cluster Controller) uses the GRU upper forecast for Kubernetes replica scaling in predictive mode. It takes the larger of the observed and the forecast replica target. Algorithm 1 (Routing Controller) splits traffic by observed load and ready-replica capacity. Its SLO pacing term is part of the design but did not fire in any reported run. Algorithm 2 uses R = α·x + β.

3. *Evaluate the hybrid system* through systematic experimentation encompassing prediction model accuracy, mechanism validation, multi-scenario comparison (S1–S4), and honest assessment of experimental limitations.

== #H("ch1-benefits")

- *Academic Benefits:* contributes to hybrid cloud knowledge, reproducible methodology, extends ElaX.

- *Practical Benefits:* working architecture blueprint, validates GRU latency for real-time, empirical trade-off data.

== #H("ch1-contribution")

1. Integrated control architecture that coordinates Kubernetes replica scaling (Algorithm 2) and capacity-aware traffic distribution (Algorithm 1) between Kubernetes and Knative serverless services under a 200 ms p99 SLO.

2. Extension of ElaX's scaling decision with multi-step GRU forecasts. The GRU replaces ElaX's LSTM, forecasts nine 15-second steps (135 s), and refreshes every control cycle. Algorithm 2 takes the larger of the observed and the forecast (upper-envelope) replica target and holds a raised target for 90 s. Routing does not use the forecast. The GRU is trained and evaluated under a leak-free chronological protocol: 5.2% RMSE on the synthetic arm, 39.6% on the held-out real trace, and parity with a linear autoregression.

3. Evaluation of the hybrid-predictive mechanism (S4) against Kubernetes-only (HPA, S1), serverless-only (Knative KPA, S2), and hybrid-reactive (S3), with validity gates on every run and per-run host-load records.

== #H("ch1-constraints")

- *Platform:* K3s + Knative + Kourier + HAProxy.

- *Prediction:* GRU only; prediction drives Algorithm 2 replica scaling, while Algorithm 1 routing uses observed load and capacity.

- *Training:* the deployed artifact trains on the ClarkNet 15-second series with chronological splits and an embargo; the synthetic arm is studied separately; validation on ClarkNet/Calgary.

- *Metrics:* p99, throughput, error; cost proxy.

- *SLO:* 200 ms p99.

- *Environment:* multi-node k3d (one or two CPU-bounded workload nodes depending on the bundle, with dynamic nodes in high-load diagnostics).

- *Traffic:* HTTP request-response.

== #H("ch1-systematics")

1. Chapter 1: Introduction (this).

2. Chapter 2: Literature Review.

3. Chapter 3: Methodology.

4. Chapter 4: Results and Discussion.

5. Chapter 5: Conclusion and Future Work.
