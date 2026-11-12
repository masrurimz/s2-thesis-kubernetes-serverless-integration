#import "ch02-figures.typ": *
#import "headings.typ": H, cap

= #H("ch2")

This chapter reviews the theoretical foundations and prior work that support this research. It covers cloud computing service models, container orchestration with Kubernetes, and serverless computing with the cold start problem. It also covers hybrid integration patterns, cloud application performance metrics, workload prediction with recurrent neural networks, and Kubernetes scaling strategies including the ElaX algorithm that this research extends.

== #H("ch2-cloud")

Cloud computing is a model for ubiquitous, convenient, on-demand network access to a shared pool of configurable computing resources @mell2011nist. These resources are networks, servers, storage, applications, and services. A provider can provision and release them rapidly with minimal management effort or service provider interaction. The model is now the dominant way to deploy and operate software systems at scale. In a 2023 industry survey, 87% of respondents reported multi-cloud use @flexera2023.

Cloud computing services fall into four models. Each model defines a different boundary of responsibility between the provider and the consumer:

- IaaS (Infrastructure as a Service) provides raw compute, storage, and networking. The user manages applications, data, runtime, middleware, and the OS. The provider manages virtualization, servers, storage, and networking.

- PaaS (Platform as a Service) adds managed runtime and middleware. The user manages only applications and data.

- SaaS (Software as a Service) delivers complete applications. The user manages only their data.

- FaaS (Function as a Service) is the most granular model. Developers deploy single functions and leave the operation of the underlying infrastructure to the cloud provider @wurster2018modeling.

This research operates at the intersection of IaaS/PaaS (Kubernetes container orchestration) and FaaS (Knative serverless functions).

The hybrid cloud model is relevant to this research. The proposed architecture routes traffic between a Kubernetes cluster and a serverless platform. The Kubernetes cluster is analogous to a managed private environment. The serverless platform is analogous to a public elastic service. The system selects the right backend from real-time performance and predicted workload conditions.

== #H("ch2-containers")

Containers are lightweight, standalone executable packages. They package the parts of an application together with the middleware, binaries and libraries needed to run it @pahl2019cloud. A virtual machine runs a full guest operating system. A container shares the host kernel. Containers share the kernel of their host, and the host operating system isolates them from one another @yadav2019docker. This design difference gives three practical advantages. Startup time drops from minutes to seconds. Resource overhead drops to the shared kernel footprint. Deployment density increases from tens to hundreds of instances per host.

Kubernetes (K8s) is an open-source container orchestration platform. Google designed it from over a decade of experience with the Borg and Omega cluster management systems. It automates deployment, scaling, and management of containerized applications across clusters of machines. It uses declarative configuration and a reconciliation control loop.

The architecture has two planes. The Control Plane manages cluster-wide state and scheduling decisions. It uses four components. The API Server is the central management entity. It exposes the Kubernetes REST API. The Scheduler selects the right nodes for new pods from resource requirements and constraint policies. The Controller Manager runs reconciliation processes. These processes watch and drive cluster state toward the desired state. etcd is a consistent, highly available distributed key-value store. It is the backing store for all cluster state data.

The Data Plane consists of Worker Nodes. These nodes run application workloads. Each node runs a Kubelet and a Kube-proxy. The Kubelet is an agent that ensures the containers in pod specifications run and stay healthy. The Kube-proxy is a network proxy. It maintains the rules that allow communication to pods. K3s is the lightweight Kubernetes distribution used in this research. It keeps full API compatibility and reduces the memory footprint to about 512MB RAM. This makes it suitable for resource-constrained environments.

#figure(
  fig-k8s-architecture(),
  caption: [Architecture of a Kubernetes cluster @kubernetes2024components],
) <fig:k8s-architecture>

== #H("ch2-serverless")

Serverless computing is a cloud execution model. The provider takes over the provisioning, scaling and maintenance of servers @sadaqat2018serverless. Servers still exist despite the name. The abstraction removes server management from the developer's responsibility @savage2018going. Key characteristics include event-driven execution, stateless processing, automatic scaling, and pay-per-use pricing. Functions run when events trigger them, not continuously. No persistent state remains between invocations. Scaling runs from zero to thousands based on the event rate. Billing covers only the resources a function uses while it runs. AWS Lambda, for example, rounds the duration up to the nearest 1 ms @mampage2022holistic.

Major commercial platforms include AWS Lambda, Google Cloud Functions, and Azure Functions. In the open-source ecosystem, Knative provides a Kubernetes-native serverless runtime. OpenFaaS offers a simpler function deployment model. This research uses Knative Serving as the serverless backend. It runs on the same Kubernetes cluster. This enables a fair comparison and simple traffic routing through a shared network namespace.

#figure(
  fig-serverless-architecture(),
  caption: [Serverless computing architecture @mampage2022holistic],
) <fig:serverless-architecture>

The cloud service model and division of responsibilities are shown below @kavis2014.

#figure(
  fig-cloud-services(),
  caption: [Cloud services and division of responsibilities @kavis2014],
) <fig:cloud-services>

The cold start problem is one of the most important performance challenges of serverless computing @golec2023cold. A cold start occurs when a function invocation arrives but no warm (pre-initialized) function instance exists to handle it. The platform must then do several sequential initialization steps. These steps are container provisioning, runtime initialization, function code loading, and dependency initialization. Typical cold start latencies range from 100–500 ms for AWS Lambda, 200–600 ms for Google Cloud Functions, and 1000–3000 ms for Knative on Kubernetes. Knative must provision a full Kubernetes pod, not a lightweight container sandbox. Beni et al. @beni2021reducing showed that sharing libraries between containers, pre-creating network containers and creating containers in parallel reduce the startup delay during elastic scaling in Kubernetes. This finding motivates the predictive pre-warming approach used in this research. Serverless benchmarks measure cold-start latency @yu2020characterizing @sebs2020, and SeBS shows that billing granularity charges for unused time and memory @sebs2020. Forecasts have been used to start serverless functions before requests arrive @jegannathan2022time, and reinforcement learning to decide how long to keep them warm @vahidinia2023mitigating.

The cold start penalty is large for latency-sensitive applications with strict SLO targets. If p99 latency must stay below 200 ms, one cold start invocation can cause an SLO violation. This trade-off between serverless elasticity and cold start latency motivates the hybrid architecture proposed in this thesis. Kubernetes provides always-warm pods for baseline traffic. Serverless absorbs overflow, but only when prediction shows enough lead time for warm-up.

== #H("ch2-integration")

Kubernetes and serverless have complementary strengths and weaknesses. Kubernetes gives consistent low latency and is cost-efficient for sustained loads, but it requires capacity planning. Serverless gives instant elasticity and zero idle cost, but it has a cold start penalty. These differences motivate combining the two into hybrid architectures @dehigama2024. Dehigama et al. @dehigama2024 showed that a hybrid VM-serverless deployment can cut total cost by 7.5% compared to optimally provisioned VM-only setups. It also keeps SLO compliance. PulseNet @pulsenet2025 proposed a dual-track control plane. It separates sustainable traffic from excessive traffic. It gives 35% better performance than Dirigent, a FaaS-only system, at the same cost. MArk provisions virtual machines from a load forecast and serves bursts on AWS Lambda @zhang2019mark. Spock uses serverless functions to cover the scale-out lag of virtual machines @gunasekaran2019spock.

Combining Kubernetes and serverless gives four key advantages:

- Cost optimization: Kubernetes serves predictable baseline load and avoids per-invocation serverless costs; serverless serves burst traffic and avoids over-provisioning.

- Performance: warm Kubernetes pods avoid cold start latency for most requests; serverless handles overflow.

- Flexibility: each workload component runs on the most suitable platform.

- Reliability: cross-platform routing gives a fallback.

LA-IMR @laimr2026 showed up to 20.7% P99 latency reduction in hybrid cloud-edge environments. It used predictive in-memory routing and proactive autoscaling.

The literature describes two primary patterns. The Overflow Model routes all traffic to Kubernetes until saturation appears in CPU, memory, or latency metrics. Then excess traffic overflows to the serverless backend. This pattern is reactive. It responds to saturation after it occurs. The latency between detection and the availability of serverless capacity creates a window. SLO violations may occur in this window. The Predictive Scaling pattern uses a forecasting model to anticipate demand. It adjusts Kubernetes capacity before limits are reached. This pattern motivates the architecture proposed in this research. Its routing controller still uses observed load and ready capacity. In simulation, AAPA @aapa2025 reduced SLO violations against the Kubernetes HPA by scaling per workload archetype and widening its margins when classifier confidence is low.

Earlier studies cover parts of this problem. @table-prior-work shows what each study covers, and what it does not.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, left, left),
    [*Thread*], [*Representative work*], [*Covered*], [*Not covered*],
    [Hybrid deployment cost], [@dehigama2024], [VM-serverless cost comparison], [No dynamic traffic routing],
    [Dual-track serverless control], [@pulsenet2025], [Overflow routing and trend prediction on Knative], [No Kubernetes-FaaS routing],
    [Predictive autoscaling with confidence], [@aapa2025], [Archetype-specific scaling with confidence-based margins], [Single platform, no cross-platform routing],
    [Predictive cloud-edge routing], [@laimr2026], [Predictive routing and proactive autoscaling], [No separation of scaling and routing],
    [GRU prediction for Kubernetes], [@mondal2023toward], [GRU forecasting of cluster CPU usage], [No routing, no serverless backend],
    [Unified prediction and allocation], [@yang2019elax], [Predictor, resource model, online controller], [Single platform, no SLO-aware routing],
  ),
  caption: [Partial prior work on each thread],
) <table-prior-work>

Earlier work covers each thread. No single thread is new. The contribution combines three parts. Cross-platform routing moves traffic between Kubernetes and an independent serverless platform. GRU prediction drives replica scaling through an extension of ElaX's largest-value scaling decision. Routing reads observed load and ready capacity and does not read the forecast. No earlier system combines these parts. Built on ElaX's resource allocation model, this combination closes the research gap.

== #H("ch2-metrics")

Measuring and managing cloud application performance requires a structured framework of metrics, targets, and monitoring approaches.

A Service Level Agreement (SLA) is a contract between a service provider and a consumer. It defines expected performance levels and the consequences of failing to meet them. A Service Level Indicator (SLI) is a quantitative measure of a service aspect, such as request latency, error rate, or throughput. A Service Level Objective (SLO) is a target value or range for an SLI, such as "p99 latency under 200ms." An SLA is expressed through SLIs and SLOs.

This research uses p99 (99th percentile) latency as the primary SLO indicator. It follows the tail-at-scale principle @dean2013tail. In distributed systems, the slowest component in the request path determines overall user-perceived latency. Therefore, optimizing tail latency, rather than mean or median latency, is essential to keep a consistent user experience.

Response time splits into three components. Network latency covers routing overhead and backend selection. Queue time is the wait in the Kubernetes or serverless request queue. Processing time is the actual application computation. Cold start latency in serverless adds to the processing time for the first invocation. Tail latency is the upper end of the response-time distribution, reported as a high percentile such as p99 or p99.9 @dean2013tail. It captures degradation before that degradation affects most users.

Scalability is the ability of a system to handle more workload by adding resources. Elasticity adds the ability to acquire and release resources automatically when demand changes. Kubernetes achieves elasticity through the Horizontal Pod Autoscaler (HPA). The HPA reacts to observed CPU or custom metrics. Serverless platforms offer inherent elasticity. They provision function instances per invocation.

== #H("ch2-prediction")

Workload prediction turns reactive scaling into proactive scaling. Reactive scaling responds to current metrics. Proactive scaling prepares for anticipated demand. Recurrent neural networks have forecast CPU usage in a cluster trace slightly more accurately than ARIMA @mondal2023toward. Forecast-based scalers for Kubernetes use time-series models of resource use or request rate @mondal2023toward @yuan2024time.

LSTM (Long Short-Term Memory) is a recurrent neural network architecture. Hochreiter and Schmidhuber introduced it. It learns long-term dependencies in sequential data. The key innovation is the cell state. The cell state holds information and is regulated by three gates: the forget gate, the input gate, and the output gate. LSTM is a common method in studies of load prediction for autoscaling @mondal2023toward. However, its three-gate architecture introduces large computational overhead. For a hidden state of size h, each LSTM cell requires $4h(h + x) + 4h$ parameters, where x is the input dimension. This overhead causes slower training and a higher parameter count.

GRU (Gated Recurrent Unit) is simpler than LSTM. Cho et al. proposed it @cho2014learning. GRU combines the forget and input gates into a single update gate. It also merges the cell state and hidden state. The reset gate controls how much past information to forget. The update gate controls the balance between the previous hidden state and the candidate activation. Chung et al. ran an empirical evaluation @chung2014empirical. They found the GRU comparable to the LSTM on music and speech modeling. The GRU cell needs about 25% fewer parameters than the LSTM cell, from three instead of four gate parameter sets. @mondal2023toward trained LSTM, BiLSTM, and GRU under one protocol on real Google clusterdata-2011-2 sequences. The protocol used TensorFlow 2, Adam, 200 epochs, batch 512, and MSE loss. @mondal2023toward held out ten sequences for testing. LSTM and GRU used the same capacity of 50 hidden units. GRU was best on all three accuracy metrics: MSE 0.00194 against 0.00195, RMSE 0.04360 against 0.04367, and MAE 0.03057 against 0.03274. Training took 0.75 s against 1.44 s. Inference time was effectively identical, 0.0651 s against 0.0661 s. The paper does not state the hardware it measured on, so only the comparison within that paper is meaningful. Each model is also reported at its own best step size, 24 for GRU against 47 for LSTM. This research therefore measures its own latency on the testbed (median 4.0 ms in the September bundle, against a 50 ms target, Chapter 4) rather than borrowing theirs.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto),
    [Aspect], [LSTM], [GRU],
    [Gates], [3 (forget, input, output)], [2 (reset, update)],
    [State vectors], [2 (cell + hidden)], [1 (hidden only)],
    [Parameters per cell], [$4h(h+x) + 4h$], [$3h(h+x) + 3h$],
    [Training speed], [Baseline], [Slightly faster],
    [Prediction accuracy], [Reference], [Comparable],
    [Real-time suitability], [Moderate], [High],
  ),
  caption: [LSTM vs GRU comparison],
) <table-lstm-gru>

For the workload prediction task in this research, GRU is the preferred architecture. The task is short-horizon (135 s, 9 × 15 s) HTTP traffic forecasting with a real-time latency constraint (under 50ms inference). GRU has a lower computational cost and comparable accuracy. The reduced parameter count also lowers overfitting risk. The synthetic workload patterns provide limited training data.

== #H("ch2-elax")

Kubernetes provides built-in autoscaling mechanisms, among them the Horizontal Pod Autoscaler and the Cluster Autoscaler @ren2023research. The Horizontal Pod Autoscaler (HPA) scales the number of pod replicas within a deployment. It uses observed resource utilization metrics. HPA runs a control loop with a default period of 15 seconds. It queries the metrics API. It computes the desired replica count as the ratio of current to desired metric value. It scales subject to min/max bounds and stabilization windows. Serracanta et al. @serracanta2025hpa formally proved that the HPA control loop of a single service is globally asymptotically stable under a step input, and verified it at an 80% CPU target. This finding justifies threshold tuning as a sound design choice. However, reactive threshold controllers can still oscillate under volatile load. Tiny Autoscalers @tinyautoscalers2022 introduced a bottoming mechanism that keeps the predicted CPU allocation of a serverless function from dropping rapidly. This mechanism informs the consolidation idle-timer design used in this thesis. The Cluster Autoscaler operates at the node level. It adds nodes when pods cannot be scheduled. It removes underutilized nodes after a configurable cool-down period.

Both HPA and Cluster Autoscaler are reactive. They respond to observed metric thresholds. Neither anticipates future demand. The HPA scales only after its control loop reacts to higher utilization @hypa2023. This reactive gap between demand onset and scaling completion is the core problem that predictive approaches address. Surveys of Kubernetes scheduling include autoscaling-enabled scheduling as one of their categories @senjab2023survey. HyPA combines reactive and model-based horizontal scaling and updates its model online @hypa2023. KAPETÁNIOS adapts Kubernetes through a digital twin @kapetanios2022. STaleX adapts microservice scaling to spatial and temporal load features @stalex2025. BACC paces horizontal autoscaling against an error budget @bacc2026.

@yang2019elax ElaX is an algorithm that provisions resource elasticity in containerized online cloud services. ElaX has three components: a workload predictor, a resource reservation model, and an online controller. This design separates workload prediction from resource management. The Workload Predictor forecasts future traffic volume. It uses a Long Short-Term Memory (LSTM) recurrent network. The Resource Allocation Model maps predicted traffic to required compute resources. It uses the linear model $R = alpha dot.op x + beta$. R is the CPU resources required. x is traffic volume in requests per second. alpha is the slope: resource cost per request. beta is the base overhead. The Online Controller monitors real-time SLO compliance. It adjusts resources from the gap between target and observed tail latency. It uses a slack-based scaling algorithm.

This research changes ElaX in three ways. First, a GRU replaces the LSTM. The forecast horizon shrinks from one hour to nine 15-second steps (135 s), which covers the node provisioning delays measured in the testbed (50--125 s). The forecast refreshes every 15-second control cycle instead of once an hour. Median GRU inference in the September bundle is 4.0 ms (Chapter 4). On three matched seeds the GRU scores slightly better than an LSTM, and it matches a linear autoregression (Chapter 4). Second, the decision factor changes. ElaX reserves resources for the largest predicted value over its horizon, and this research keeps that largest-value rule. It applies the rule to the GRU upper envelope over 135 s, refreshed every 15 s, and compares it with the target from the observed load. Algorithm 2 takes the larger of the two replica targets, and it holds a raised target for 90 seconds. Algorithm 2 scales replicas only. It does not reimplement the slack-based feedback controller or the vertical scale-up of ElaX. Third, Algorithm 1 adds a decision that ElaX does not make. It splits traffic between Kubernetes and serverless from observed load and ready capacity. It does not use the forecast.

The combination of ElaX's resource allocation model with cross-platform routing and GRU prediction forms the theoretical foundation for the hybrid system evaluated in this thesis.

#figure(
  fig-elax-architecture(),
  caption: [ElaX system architecture @yang2019elax],
) <fig:elax-architecture>
