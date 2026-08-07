= LITERATURE REVIEW

This chapter reviews the theoretical foundations and prior work underpinning this research. It covers cloud computing service models, container orchestration with Kubernetes, serverless computing and the cold start problem, hybrid integration patterns, cloud application performance metrics, workload prediction using recurrent neural networks, and Kubernetes scaling strategies including the ElaX algorithm that this research extends.

== Cloud Computing

Cloud computing is a model for enabling ubiquitous, convenient, on-demand network access to a shared pool of configurable computing resources—networks, servers, storage, applications, and services—that can be rapidly provisioned and released with minimal management effort or service provider interaction @mell2011nist. The model has become the dominant paradigm for deploying and operating software systems at scale, with 87% of enterprises adopting multi-cloud strategies as of 2023.

Cloud computing services are typically categorized into four models, each defining a different boundary of responsibility between the provider and the consumer:

IaaS (Infrastructure as a Service) provides raw compute, storage, and networking where the user manages applications, data, runtime, middleware, and OS while the provider handles virtualization, servers, storage, and networking. PaaS (Platform as a Service) adds managed runtime and middleware, leaving the user responsible only for applications and data. SaaS (Software as a Service) delivers complete applications with the user managing only their data. FaaS (Function as a Service) is the most granular model: developers deploy individual function code without awareness of the underlying execution environment. This research operates at the intersection of IaaS/PaaS (Kubernetes container orchestration) and FaaS (Knative serverless functions).

The hybrid cloud model is particularly relevant to this research, as the proposed architecture routes traffic between a Kubernetes cluster (analogous to a managed private environment) and a serverless platform (analogous to a public elastic service), selecting the appropriate backend based on real-time performance and predicted workload conditions.

== Containers and Kubernetes

Containers are lightweight, standalone executable packages that encapsulate application code, runtime, system tools, libraries, and configuration @pahl2019cloud. Unlike virtual machines, which each run a full guest operating system, containers share the host kernel and isolate processes through Linux namespaces and control groups @yadav2019docker. This architectural difference yields significant practical advantages: startup time drops from minutes to seconds, resource overhead is reduced to the shared kernel footprint, and deployment density increases from tens to hundreds of instances per host.

Kubernetes (K8s) is an open-source container orchestration platform originally designed at Google, drawing on over a decade of experience with the Borg and Omega cluster management systems. It automates deployment, scaling, and management of containerized applications across clusters of machines through declarative configuration and a reconciliation control loop.

The architecture consists of two planes. The Control Plane manages cluster-wide state and scheduling decisions through the API Server (the central management entity that exposes the Kubernetes REST API), the Scheduler (which selects appropriate nodes for newly created pods based on resource requirements and constraint policies), the Controller Manager (which runs reconciliation processes that watch and drive cluster state toward the desired state), and etcd (a consistent, highly available distributed key-value store used as the backing store for all cluster state data).

The Data Plane consists of Worker Nodes that run application workloads. Each node runs a Kubelet (an agent ensuring containers described in pod specifications are running and healthy) and a Kube-proxy (a network proxy maintaining rules allowing communication to pods). K3s, the lightweight Kubernetes distribution used in this research, maintains full API compatibility while reducing the memory footprint to approximately 512MB RAM, making it suitable for resource-constrained environments.

#figure(
  image("../figures/image6.png", width: 80%),
  caption: [Architecture of a Kubernetes cluster],
) <fig:k8s-architecture>

== Serverless Computing and Cold Start

Serverless computing is a cloud execution model in which the provider dynamically manages the allocation and provisioning of servers @sadaqat2018serverless. Despite the name, servers still exist—the abstraction simply removes server management from the developer's responsibility @savage2018going. Key characteristics include event-driven execution (functions triggered by events rather than running continuously), stateless processing (no persistent state between invocations), automatic scaling (from zero to thousands based on event rate), and pay-per-use pricing (billing based on actual compute time consumed, typically per 100ms of execution) @mampage2022holistic.

Major commercial platforms include AWS Lambda, Google Cloud Functions, and Azure Functions. In the open-source ecosystem, Knative provides a Kubernetes-native serverless runtime, while OpenFaaS offers a simpler function deployment model. This research uses Knative Serving as the serverless backend because it runs on the same Kubernetes cluster, enabling fair comparison and simplified traffic routing through a shared network namespace.

#figure(
  image("../figures/image8.png", width: 70%),
  caption: [Serverless computing architecture @mampage2022holistic],
) <fig:serverless-architecture>

The cloud service model and division of responsibilities is illustrated below @kavis2014.

#figure(
  image("../figures/image3.png", width: 80%),
  caption: [Cloud services and division of responsibilities @kavis2014],
) <fig:cloud-services>

The cold start problem is the primary performance limitation of serverless computing @golec2023cold. A cold start occurs when a function invocation arrives but no warm (pre-initialized) function instance exists to handle it. The platform must then perform several sequential initialization steps: container provisioning, runtime initialization, function code loading, and dependency initialization. Typical cold start latencies range from 100–500 ms for AWS Lambda, 200–600 ms for Google Cloud Functions, and 1000–3000 ms for Knative on Kubernetes (which must provision a full Kubernetes pod rather than a lightweight container sandbox). Beni et al. @beni2021reducing demonstrated that maintaining warm containers during elastic scaling of Kubernetes-based serverless platforms can reduce cold start latency by 50–80%, motivating the predictive pre-warming approach implemented in this research.

The cold start penalty is particularly significant for latency-sensitive applications with strict SLO targets. If p99 latency must remain below 200 ms, even a single cold start invocation can cause an SLO violation. This trade-off between serverless elasticity and cold start latency is a central motivation for the hybrid architecture proposed in this thesis: Kubernetes provides always-warm pods for baseline traffic, while serverless absorbs overflow—but only when prediction indicates sufficient lead time for warm-up.

== Kubernetes-Serverless Integration

The complementary strengths and weaknesses of Kubernetes (consistent low latency, cost-efficient for sustained loads, requires capacity planning) and serverless (instant elasticity, zero idle cost, cold start penalty) motivate their integration into hybrid architectures @dehigama2024. Dehigama et al. @dehigama2024 showed that hybrid VM-serverless deployment can reduce total cost by 7.5% compared to optimally provisioned VM-only setups while maintaining SLO compliance. PulseNet @pulsenet2025 proposed a dual-track control plane that separates sustainable and excessive traffic, achieving 35% better performance than FaaS-only systems at cost parity.

Integrating Kubernetes and serverless provides four key advantages: cost optimization (Kubernetes for predictable baseline load avoiding per-invocation serverless costs, serverless for burst traffic avoiding over-provisioning), performance (warm Kubernetes pods avoid cold start latency for the majority of requests while serverless handles overflow), flexibility (different workload components assigned to the most appropriate platform), and reliability (cross-platform routing provides fallback capability). LA-IMR @laimr2026 demonstrated up to 20.7% P99 latency reduction in hybrid cloud-edge environments through predictive in-memory routing and proactive autoscaling.

Two primary patterns have been identified in the literature. The Overflow Model routes all traffic to Kubernetes until saturation is detected by CPU, memory, or latency metrics, at which point excess traffic overflows to the serverless backend. This pattern is reactive—it responds to saturation after it occurs, and the latency between detection and serverless capacity becoming available creates a window during which SLO violations may occur. The Predictive Scaling pattern uses a forecasting model to anticipate demand and proactively adjust Kubernetes capacity before limits are reached. This pattern motivates the architecture proposed in this research, while its routing controller still uses observed load and ready capacity. AAPA @aapa2025 demonstrated that archetype-aware confidence weighting reduces SLO violations.

== Cloud Application Performance Metrics

Measuring and managing cloud application performance requires a structured framework of metrics, targets, and monitoring approaches.

A Service Level Agreement (SLA) is a contractual commitment between a service provider and consumer that defines expected performance levels and the consequences of failing to meet them. An SLA is operationalized through Service Level Indicators (SLI)—quantitative measures of a service aspect such as request latency, error rate, or throughput—and Service Level Objectives (SLO)—target values or ranges for an SLI, such as "p99 latency under 200ms."

This research uses p99 (99th percentile) latency as the primary SLO indicator, following the tail-at-scale principle: in distributed systems, overall user-perceived latency is determined by the slowest component in the request path. Optimizing tail latency—rather than mean or median—is therefore essential for maintaining consistent user experience.

Response time decomposes into network latency (routing overhead, backend selection), queue time (waiting in the Kubernetes or serverless request queue), and processing time (actual application computation). Cold start latency in serverless adds to the processing time component for the first invocation. Tail latency (p99, p99.9) represents the response time experienced by the slowest fraction of requests, capturing degradation before it affects the majority of users.

Scalability is the ability of a system to handle increasing workload by adding resources. Elasticity extends scalability with the ability to both acquire and release resources automatically in response to demand changes. Kubernetes achieves elasticity through the Horizontal Pod Autoscaler (HPA), which reacts to observed CPU or custom metrics. Serverless platforms offer inherent elasticity by provisioning function instances per invocation.

== Workload Prediction with Recurrent Neural Networks

Workload prediction transforms reactive scaling (responding to current metrics) into proactive scaling (preparing for anticipated demand). Time-series forecasting using recurrent neural networks has demonstrated effectiveness for cloud workload prediction tasks @mondal2023toward.

LSTM (Long Short-Term Memory), introduced by Hochreiter and Schmidhuber, is a recurrent neural network architecture designed to learn long-term dependencies in sequential data. The key innovation is the cell state—a conveyor belt of information regulated by three gating mechanisms: forget gate, input gate, and output gate. LSTM has been widely applied to cloud workload prediction @mondal2023toward. However, its three-gate architecture introduces substantial computational overhead: for a hidden state of size h, each LSTM cell requires $4h(h + x) + 4h$ parameters where x is the input dimension, resulting in slower training and higher inference latency.

GRU (Gated Recurrent Unit), proposed by Cho et al., simplifies the LSTM architecture by combining the forget and input gates into a single update gate and merging the cell state and hidden state. The reset gate controls how much past information to forget, while the update gate controls the balance between previous hidden state and candidate activation. Chung et al. conducted an empirical evaluation and found that GRU achieves comparable or superior performance to LSTM on many sequence modeling tasks while using approximately 25% fewer parameters. @mondal2023toward specifically evaluated both architectures for Kubernetes workload prediction and confirmed similar accuracy with significant computational savings.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto),
    [Aspect], [LSTM], [GRU],
    [Gates], [3 (forget, input, output)], [2 (reset, update)],
    [State vectors], [2 (cell + hidden)], [1 (hidden only)],
    [Parameters per cell], [$4h(h+x) + 4h$], [$3h(h+x) + 3h$],
    [Training speed], [Baseline], [~25% faster],
    [Prediction accuracy], [Reference], [Comparable],
    [Real-time suitability], [Moderate], [High],
  ),
  caption: [LSTM vs GRU comparison],
) <table-lstm-gru>

For the workload prediction task in this research—short-horizon (135 s, 9 × 15 s) HTTP traffic forecasting with a real-time latency constraint (under 50ms inference)—GRU's lower computational cost and comparable accuracy make it the preferred architecture. The reduced parameter count also mitigates overfitting risk given the limited training data available from synthetic workload patterns.

== Kubernetes Scaling and the ElaX Algorithm

Kubernetes provides built-in autoscaling mechanisms at two granularity levels @ren2023research. The Horizontal Pod Autoscaler (HPA) scales the number of pod replicas within a deployment based on observed resource utilization metrics. HPA operates on a control loop with a default period of 15 seconds, querying the metrics API, computing the desired replica count as the ratio of current to desired metric value, and scaling subject to min/max bounds and stabilization windows. Serracanta et al. @serracanta2025hpa formally proved that the HPA control loop is globally asymptotically stable at any utilization target between 30 and 80%, justifying threshold tuning as a sound design choice. However, reactive threshold controllers can still oscillate under volatile load; Tiny Autoscalers @tinyautoscalers2022 introduced a bottoming mechanism that prevents rapid resource swings, informing the consolidation idle-timer design used in this thesis. The Cluster Autoscaler operates at the node level, adding nodes when pods cannot be scheduled and removing underutilized nodes after a configurable cool-down period.

Both HPA and Cluster Autoscaler are fundamentally reactive—they respond to observed metric thresholds rather than anticipating future demand @zhang2021zeus. This reactive gap between demand onset and scaling completion is the core problem addressed by predictive approaches.

ElaX (Elastic Execution), proposed by @yang2019elax, is an algorithm for provisioning resource elasticity in containerized online cloud services. ElaX introduces a two-layer decision architecture that separates workload prediction from resource management. The Workload Predictor forecasts future traffic volume using a recurrent neural network (LSTM or GRU). The Resource Allocation Model maps predicted traffic to required compute resources using a linear model $R = alpha dot.op x + beta$, where R is CPU resources required, x is traffic volume (requests per second), alpha is the slope coefficient representing resource cost per request, and beta is base resource overhead. The Online Controller monitors real-time SLO compliance and adjusts resources based on the gap between target and observed tail latency using a slack-based scaling algorithm.

This research extends ElaX in three significant ways. First, GRU substitution replaces LSTM with GRU as the workload predictor, reducing inference latency from approximately 100ms to approximately 40ms while maintaining comparable prediction accuracy. Second, capacity-driven decision logic extends the original resource allocation adjustment to route traffic between platforms—Kubernetes and serverless—adding a cross-platform dimension to the elasticity decision while using observed load and ready capacity for routing. Third, a priority-based action hierarchy (SCALE_OUT, PREDICTIVE, OPTIMIZE_COST, MAINTAIN) integrates reactive SLO monitoring with confidence-gated predictive replica scaling, ensuring that SLO recovery always takes precedence over cost optimization.

The combination of ElaX's resource allocation model with cross-platform routing and GRU prediction forms the theoretical foundation for the hybrid system evaluated in this thesis.

#figure(
  image("../figures/image6.png", width: 80%),
  caption: [ElaX system architecture @yang2019elax],
) <fig:elax-architecture>
