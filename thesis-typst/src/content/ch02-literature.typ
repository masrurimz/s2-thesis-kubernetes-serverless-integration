= LITERATURE REVIEW

This chapter reviews the theoretical foundations and prior work that support this research. It covers cloud computing service models, container orchestration with Kubernetes, and serverless computing with the cold start problem. It also covers hybrid integration patterns, cloud application performance metrics, workload prediction with recurrent neural networks, and Kubernetes scaling strategies including the ElaX algorithm that this research extends.

== Cloud Computing

Cloud computing is a model for ubiquitous, convenient, on-demand network access to a shared pool of configurable computing resources @mell2011nist. These resources are networks, servers, storage, applications, and services. A provider can provision and release them rapidly with minimal management effort or service provider interaction. The model is now the dominant way to deploy and operate software systems at scale. By 2023, 87% of enterprises had adopted multi-cloud strategies.

Cloud computing services fall into four models. Each model defines a different boundary of responsibility between the provider and the consumer:

IaaS (Infrastructure as a Service) provides raw compute, storage, and networking. The user manages applications, data, runtime, middleware, and the OS. The provider manages virtualization, servers, storage, and networking. PaaS (Platform as a Service) adds managed runtime and middleware. The user manages only applications and data. SaaS (Software as a Service) delivers complete applications. The user manages only their data. FaaS (Function as a Service) is the most granular model. Developers deploy single functions without knowledge of the underlying execution environment. This research operates at the intersection of IaaS/PaaS (Kubernetes container orchestration) and FaaS (Knative serverless functions).

The hybrid cloud model is relevant to this research. The proposed architecture routes traffic between a Kubernetes cluster and a serverless platform. The Kubernetes cluster is analogous to a managed private environment. The serverless platform is analogous to a public elastic service. The system selects the right backend from real-time performance and predicted workload conditions.

== Containers and Kubernetes

Containers are lightweight, standalone executable packages. They encapsulate application code, runtime, system tools, libraries, and configuration @pahl2019cloud. A virtual machine runs a full guest operating system. A container shares the host kernel. Containers isolate processes through Linux namespaces and control groups @yadav2019docker. This design difference gives three practical advantages. Startup time drops from minutes to seconds. Resource overhead drops to the shared kernel footprint. Deployment density increases from tens to hundreds of instances per host.

Kubernetes (K8s) is an open-source container orchestration platform. Google designed it from over a decade of experience with the Borg and Omega cluster management systems. It automates deployment, scaling, and management of containerized applications across clusters of machines. It uses declarative configuration and a reconciliation control loop.

The architecture has two planes. The Control Plane manages cluster-wide state and scheduling decisions. It uses four components. The API Server is the central management entity. It exposes the Kubernetes REST API. The Scheduler selects the right nodes for new pods from resource requirements and constraint policies. The Controller Manager runs reconciliation processes. These processes watch and drive cluster state toward the desired state. etcd is a consistent, highly available distributed key-value store. It is the backing store for all cluster state data.

The Data Plane consists of Worker Nodes. These nodes run application workloads. Each node runs a Kubelet and a Kube-proxy. The Kubelet is an agent that ensures the containers in pod specifications run and stay healthy. The Kube-proxy is a network proxy. It maintains the rules that allow communication to pods. K3s is the lightweight Kubernetes distribution used in this research. It keeps full API compatibility and reduces the memory footprint to about 512MB RAM. This makes it suitable for resource-constrained environments.

#figure(
  image("../figures/image6.png", width: 80%),
  caption: [Architecture of a Kubernetes cluster],
) <fig:k8s-architecture>

== Serverless Computing and Cold Start

Serverless computing is a cloud execution model. The provider manages the allocation and provisioning of servers dynamically @sadaqat2018serverless. Servers still exist despite the name. The abstraction removes server management from the developer's responsibility @savage2018going. Key characteristics include event-driven execution, stateless processing, automatic scaling, and pay-per-use pricing. Functions run when events trigger them, not continuously. No persistent state remains between invocations. Scaling runs from zero to thousands based on the event rate. Billing uses the actual compute time consumed, typically per 100ms of execution @mampage2022holistic.

Major commercial platforms include AWS Lambda, Google Cloud Functions, and Azure Functions. In the open-source ecosystem, Knative provides a Kubernetes-native serverless runtime. OpenFaaS offers a simpler function deployment model. This research uses Knative Serving as the serverless backend. It runs on the same Kubernetes cluster. This enables a fair comparison and simple traffic routing through a shared network namespace.

#figure(
  image("../figures/image8.png", width: 70%),
  caption: [Serverless computing architecture @mampage2022holistic],
) <fig:serverless-architecture>

The cloud service model and division of responsibilities are shown below @kavis2014.

#figure(
  image("../figures/image3.png", width: 80%),
  caption: [Cloud services and division of responsibilities @kavis2014],
) <fig:cloud-services>

The cold start problem is the primary performance limitation of serverless computing @golec2023cold. A cold start occurs when a function invocation arrives but no warm (pre-initialized) function instance exists to handle it. The platform must then do several sequential initialization steps. These steps are container provisioning, runtime initialization, function code loading, and dependency initialization. Typical cold start latencies range from 100–500 ms for AWS Lambda, 200–600 ms for Google Cloud Functions, and 1000–3000 ms for Knative on Kubernetes. Knative must provision a full Kubernetes pod, not a lightweight container sandbox. Beni et al. @beni2021reducing showed that keeping warm containers during elastic scaling of Kubernetes-based serverless platforms can reduce cold start latency by 50–80%. This finding motivates the predictive pre-warming approach used in this research.

The cold start penalty is large for latency-sensitive applications with strict SLO targets. If p99 latency must stay below 200 ms, one cold start invocation can cause an SLO violation. This trade-off between serverless elasticity and cold start latency motivates the hybrid architecture proposed in this thesis. Kubernetes provides always-warm pods for baseline traffic. Serverless absorbs overflow, but only when prediction shows enough lead time for warm-up.

== Kubernetes-Serverless Integration

Kubernetes and serverless have complementary strengths and weaknesses. Kubernetes gives consistent low latency and is cost-efficient for sustained loads, but it requires capacity planning. Serverless gives instant elasticity and zero idle cost, but it has a cold start penalty. These differences motivate combining the two into hybrid architectures @dehigama2024. Dehigama et al. @dehigama2024 showed that a hybrid VM-serverless deployment can cut total cost by 7.5% compared to optimally provisioned VM-only setups. It also keeps SLO compliance. PulseNet @pulsenet2025 proposed a dual-track control plane. It separates sustainable traffic from excessive traffic. It gives 35% better performance than FaaS-only systems at cost parity.

Combining Kubernetes and serverless gives four key advantages. Cost optimization: Kubernetes serves predictable baseline load and avoids per-invocation serverless costs; serverless serves burst traffic and avoids over-provisioning. Performance: warm Kubernetes pods avoid cold start latency for most requests; serverless handles overflow. Flexibility: each workload component runs on the most suitable platform. Reliability: cross-platform routing gives a fallback. LA-IMR @laimr2026 showed up to 20.7% P99 latency reduction in hybrid cloud-edge environments. It used predictive in-memory routing and proactive autoscaling.

The literature describes two primary patterns. The Overflow Model routes all traffic to Kubernetes until saturation appears in CPU, memory, or latency metrics. Then excess traffic overflows to the serverless backend. This pattern is reactive. It responds to saturation after it occurs. The latency between detection and the availability of serverless capacity creates a window. SLO violations may occur in this window. The Predictive Scaling pattern uses a forecasting model to anticipate demand. It adjusts Kubernetes capacity before limits are reached. This pattern motivates the architecture proposed in this research. Its routing controller still uses observed load and ready capacity. AAPA @aapa2025 showed that archetype-aware confidence weighting reduces SLO violations.

== Cloud Application Performance Metrics

Measuring and managing cloud application performance requires a structured framework of metrics, targets, and monitoring approaches.

A Service Level Agreement (SLA) is a contract between a service provider and a consumer. It defines expected performance levels and the consequences of failing to meet them. A Service Level Indicator (SLI) is a quantitative measure of a service aspect, such as request latency, error rate, or throughput. A Service Level Objective (SLO) is a target value or range for an SLI, such as "p99 latency under 200ms." An SLA is expressed through SLIs and SLOs.

This research uses p99 (99th percentile) latency as the primary SLO indicator. It follows the tail-at-scale principle. In distributed systems, the slowest component in the request path determines overall user-perceived latency. Therefore, optimizing tail latency, rather than mean or median latency, is essential to keep a consistent user experience.

Response time splits into three components. Network latency covers routing overhead and backend selection. Queue time is the wait in the Kubernetes or serverless request queue. Processing time is the actual application computation. Cold start latency in serverless adds to the processing time for the first invocation. Tail latency (p99, p99.9) is the response time that the slowest fraction of requests experiences. It captures degradation before that degradation affects most users.

Scalability is the ability of a system to handle more workload by adding resources. Elasticity adds the ability to acquire and release resources automatically when demand changes. Kubernetes achieves elasticity through the Horizontal Pod Autoscaler (HPA). The HPA reacts to observed CPU or custom metrics. Serverless platforms offer inherent elasticity. They provision function instances per invocation.

== Workload Prediction with Recurrent Neural Networks

Workload prediction turns reactive scaling into proactive scaling. Reactive scaling responds to current metrics. Proactive scaling prepares for anticipated demand. Time-series forecasting with recurrent neural networks has shown effectiveness for cloud workload prediction tasks @mondal2023toward.

LSTM (Long Short-Term Memory) is a recurrent neural network architecture. Hochreiter and Schmidhuber introduced it. It learns long-term dependencies in sequential data. The key innovation is the cell state. The cell state holds information and is regulated by three gates: the forget gate, the input gate, and the output gate. LSTM has been widely applied to cloud workload prediction @mondal2023toward. However, its three-gate architecture introduces large computational overhead. For a hidden state of size h, each LSTM cell requires $4h(h + x) + 4h$ parameters, where x is the input dimension. This overhead causes slower training and higher inference latency.

GRU (Gated Recurrent Unit) is simpler than LSTM. Cho et al. proposed it. GRU combines the forget and input gates into a single update gate. It also merges the cell state and hidden state. The reset gate controls how much past information to forget. The update gate controls the balance between the previous hidden state and the candidate activation. Chung et al. ran an empirical evaluation. They found that GRU achieves comparable or superior performance to LSTM on many sequence modeling tasks. GRU uses about 25% fewer parameters. @mondal2023toward evaluated both architectures for Kubernetes workload prediction. It confirmed similar accuracy with significant computational savings.

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

For the workload prediction task in this research, GRU is the preferred architecture. The task is short-horizon (135 s, 9 × 15 s) HTTP traffic forecasting with a real-time latency constraint (under 50ms inference). GRU has a lower computational cost and comparable accuracy. The reduced parameter count also lowers overfitting risk. The synthetic workload patterns provide limited training data.

== Kubernetes Scaling and the ElaX Algorithm

Kubernetes provides built-in autoscaling mechanisms at two granularity levels @ren2023research. The Horizontal Pod Autoscaler (HPA) scales the number of pod replicas within a deployment. It uses observed resource utilization metrics. HPA runs a control loop with a default period of 15 seconds. It queries the metrics API. It computes the desired replica count as the ratio of current to desired metric value. It scales subject to min/max bounds and stabilization windows. Serracanta et al. @serracanta2025hpa formally proved that the HPA control loop is globally asymptotically stable at any utilization target between 30 and 80%. This finding justifies threshold tuning as a sound design choice. However, reactive threshold controllers can still oscillate under volatile load. Tiny Autoscalers @tinyautoscalers2022 introduced a bottoming mechanism that prevents rapid resource swings. This mechanism informs the consolidation idle-timer design used in this thesis. The Cluster Autoscaler operates at the node level. It adds nodes when pods cannot be scheduled. It removes underutilized nodes after a configurable cool-down period.

Both HPA and Cluster Autoscaler are reactive. They respond to observed metric thresholds. They do not anticipate future demand @zhang2021zeus. This reactive gap between demand onset and scaling completion is the core problem that predictive approaches address.

ElaX (Elastic Execution) is an algorithm that provisions resource elasticity in containerized online cloud services. @yang2019elax proposed it. ElaX uses a two-layer decision architecture. It separates workload prediction from resource management. The Workload Predictor forecasts future traffic volume. It uses a recurrent neural network (LSTM or GRU). The Resource Allocation Model maps predicted traffic to required compute resources. It uses the linear model $R = alpha dot.op x + beta$, where R is CPU resources required, x is traffic volume (requests per second), alpha is the slope coefficient representing resource cost per request, and beta is base resource overhead. The Online Controller monitors real-time SLO compliance. It adjusts resources from the gap between target and observed tail latency. It uses a slack-based scaling algorithm.

This research extends ElaX in three ways. First, GRU substitution replaces LSTM with GRU as the workload predictor. This change reduces inference latency from about 100ms to about 40ms. It keeps comparable prediction accuracy. Second, capacity-driven decision logic extends the original resource allocation adjustment. It routes traffic between two platforms, Kubernetes and serverless. This change adds a cross-platform dimension to the elasticity decision. It uses observed load and ready capacity for routing. Third, a priority-based action hierarchy (SCALE_OUT, PREDICTIVE, OPTIMIZE_COST, MAINTAIN) integrates reactive SLO monitoring with confidence-gated predictive replica scaling. This hierarchy ensures that SLO recovery always takes precedence over cost optimization.

The combination of ElaX's resource allocation model with cross-platform routing and GRU prediction forms the theoretical foundation for the hybrid system evaluated in this thesis.

#figure(
  image("../figures/image6.png", width: 80%),
  caption: [ElaX system architecture @yang2019elax],
) <fig:elax-architecture>
