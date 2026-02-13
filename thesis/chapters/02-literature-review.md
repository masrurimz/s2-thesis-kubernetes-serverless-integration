# BAB 2: TINJAUAN PUSTAKA (Literature Review)

This chapter reviews the theoretical foundations and prior work underpinning this research. It covers cloud computing service models, container orchestration with Kubernetes, serverless computing and the cold start problem, hybrid integration patterns, cloud application performance metrics, workload prediction using recurrent neural networks, and Kubernetes scaling strategies including the ElaX algorithm that this research extends.

---

## 2.1 Cloud Computing (Komputasi Awan)

Cloud computing is a model for enabling ubiquitous, convenient, on-demand network access to a shared pool of configurable computing resources—networks, servers, storage, applications, and services—that can be rapidly provisioned and released with minimal management effort or service provider interaction [1]. The model has become the dominant paradigm for deploying and operating software systems at scale, with 87% of enterprises adopting multi-cloud strategies as of 2023 [17].

### Cloud Service Models

Cloud computing services are typically categorized into four models, each defining a different boundary of responsibility between the provider and the consumer:

**Table 2-1: Cloud Service Models**

| Model | Description | User Responsibility | Provider Responsibility |
|-------|-------------|---------------------|------------------------|
| **IaaS** | Infrastructure as a Service | Applications, Data, Runtime, Middleware, OS | Virtualization, Servers, Storage, Networking |
| **PaaS** | Platform as a Service | Applications, Data | Runtime, Middleware, OS, Virtualization, Servers |
| **SaaS** | Software as a Service | Data | Everything else |
| **FaaS** | Function as a Service | Function Code | Everything else including execution |

Each ascending layer abstracts away more operational complexity. IaaS provides raw compute, storage, and networking; PaaS adds managed runtime and middleware; SaaS delivers complete applications; and FaaS—the most granular model—allows developers to deploy individual functions without awareness of the underlying execution environment [1]. This research operates at the intersection of IaaS/PaaS (Kubernetes container orchestration) and FaaS (Knative serverless functions).

### Cloud Deployment Models

Cloud infrastructure can be deployed in several configurations [1]:

1. **Public Cloud**: Services offered over the public internet by providers such as AWS, GCP, and Azure. Offers economies of scale but limited control over data locality and security posture.
2. **Private Cloud**: Infrastructure operated exclusively for a single organization, providing greater control at higher cost.
3. **Hybrid Cloud**: Combination of public and private clouds, allowing workloads to move between environments based on cost, compliance, or performance requirements.
4. **Multi-Cloud**: Use of multiple cloud providers to avoid vendor lock-in, improve resilience, or leverage specialized services.

The hybrid cloud model is particularly relevant to this research, as the proposed architecture routes traffic between a Kubernetes cluster (analogous to a managed private environment) and a serverless platform (analogous to a public elastic service), selecting the appropriate backend based on real-time performance and predicted workload conditions.

---

## 2.1.1 Container dan Kubernetes (Containers and Kubernetes)

### Containers

Containers are lightweight, standalone executable packages that encapsulate application code, runtime, system tools, libraries, and configuration [2]. Unlike virtual machines, which each run a full guest operating system, containers share the host kernel and isolate processes through Linux namespaces and control groups. This architectural difference yields significant practical advantages:

**Table 2-2: Containers vs Virtual Machines**

| Aspect | Containers | Virtual Machines |
|--------|-----------|-----------------|
| Startup time | Seconds | Minutes |
| Resource overhead | Low (shared kernel) | High (full guest OS) |
| Density | Hundreds per host | Tens per host |
| Isolation | Process-level | Hardware-level |
| Image size | Megabytes | Gigabytes |

Containers enable consistent environments across development and production, reducing the "works on my machine" problem and facilitating continuous integration and deployment pipelines.

### Kubernetes Architecture

Kubernetes (K8s) is an open-source container orchestration platform originally designed at Google, drawing on over a decade of experience with the Borg and Omega cluster management systems [2]. It automates deployment, scaling, and management of containerized applications across clusters of machines through declarative configuration and a reconciliation control loop.

```
┌─────────────────────────────────────────────────────────────────┐
│                      KUBERNETES CLUSTER                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    CONTROL PLANE                         │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐ │   │
│  │  │ API Server   │ │ Scheduler    │ │ Controller       │ │   │
│  │  │              │ │              │ │ Manager          │ │   │
│  │  └──────────────┘ └──────────────┘ └──────────────────┘ │   │
│  │  ┌──────────────────────────────────────────────────────┐│   │
│  │  │ etcd (Distributed Key-Value Store)                   ││   │
│  │  └──────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    WORKER NODES                          │   │
│  │  ┌─────────────────┐  ┌─────────────────┐               │   │
│  │  │ Node 1          │  │ Node 2          │  ...          │   │
│  │  │ ┌─────┐ ┌─────┐ │  │ ┌─────┐ ┌─────┐ │               │   │
│  │  │ │Pod 1│ │Pod 2│ │  │ │Pod 3│ │Pod 4│ │               │   │
│  │  │ └─────┘ └─────┘ │  │ └─────┘ └─────┘ │               │   │
│  │  │ ┌─────────────┐ │  │ ┌─────────────┐ │               │   │
│  │  │ │ Kubelet     │ │  │ │ Kubelet     │ │               │   │
│  │  │ │ Kube-proxy  │ │  │ │ Kube-proxy  │ │               │   │
│  │  │ └─────────────┘ │  │ └─────────────┘ │               │   │
│  │  └─────────────────┘  └─────────────────┘               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Figure 2-1: Kubernetes Cluster Architecture**

The architecture consists of two planes:

**Control Plane** components manage cluster-wide state and scheduling decisions:
- **API Server**: The central management entity that exposes the Kubernetes REST API. All administrative operations—including those from kubectl, the scheduler, and controllers—pass through the API server [12].
- **Scheduler**: Monitors newly created pods with no assigned node and selects an appropriate node based on resource requirements, affinity rules, and constraint policies [4].
- **Controller Manager**: Runs controller processes (e.g., ReplicaSet controller, Deployment controller) that watch the cluster state via the API server and reconcile the actual state toward the desired state [2].
- **etcd**: A consistent and highly available distributed key-value store used as the backing store for all cluster state data.

**Data Plane** (Worker Nodes) run application workloads:
- **Kubelet**: An agent on each node that ensures containers described in pod specifications are running and healthy.
- **Kube-proxy**: A network proxy that maintains network rules allowing communication to pods from inside or outside the cluster.

K3s, the lightweight Kubernetes distribution used in this research, maintains full API compatibility while reducing the memory footprint to approximately 512MB RAM, making it suitable for resource-constrained environments [12].

---

## 2.1.2 Function as a Service dan Serverless (FaaS and Serverless Computing)

### Serverless Computing

Serverless computing is a cloud execution model in which the provider dynamically manages the allocation and provisioning of servers [3]. Despite the name, servers still exist—the abstraction simply removes server management from the developer's responsibility. Key characteristics include:

- **Event-driven execution**: Functions are triggered by events (HTTP requests, message queue events, timers) rather than running continuously.
- **Stateless processing**: No persistent state is maintained between invocations; each function execution is independent.
- **Automatic scaling**: The platform scales function instances from zero to thousands based on incoming event rate, with no configuration required.
- **Pay-per-use pricing**: Billing is based on actual compute time consumed (typically per 100ms of execution), eliminating cost for idle capacity.

```
┌─────────────────────────────────────────────────────────────────┐
│                    SERVERLESS PLATFORM                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────┐    ┌───────────────────────────────────────┐    │
│  │  Event    │───►│         Function Runtime               │    │
│  │  Source   │    │  ┌─────────┐ ┌─────────┐ ┌─────────┐  │    │
│  │ (HTTP,    │    │  │ Func A  │ │ Func B  │ │ Func C  │  │    │
│  │  Queue,   │    │  │ (warm)  │ │ (cold)  │ │ (warm)  │  │    │
│  │  Timer)   │    │  └─────────┘ └─────────┘ └─────────┘  │    │
│  └───────────┘    └───────────────────────────────────────┘    │
│                              │                                  │
│                    ┌─────────▼─────────┐                       │
│                    │ Auto-Scaling      │                       │
│                    │ (0 to N instances)│                       │
│                    └───────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

**Figure 2-2: Serverless Platform Architecture**

Major commercial platforms include AWS Lambda, Google Cloud Functions [18], and Azure Functions. In the open-source ecosystem, Knative [19] provides a Kubernetes-native serverless runtime, while OpenFaaS [20] offers a simpler function deployment model. This research uses Knative Serving as the serverless backend because it runs on the same Kubernetes cluster, enabling fair comparison and simplified traffic routing through a shared network namespace.

### Cold Start Problem (Masalah Cold Start)

The cold start problem is the primary performance limitation of serverless computing [3], [8]. A cold start occurs when a function invocation arrives but no warm (pre-initialized) function instance exists to handle it. The platform must then perform several sequential initialization steps:

1. **Container provisioning**: Allocating compute resources and creating a container sandbox.
2. **Runtime initialization**: Starting the language runtime (JVM, Node.js, Python interpreter).
3. **Function code loading**: Downloading and loading the function deployment package.
4. **Dependency initialization**: Loading libraries and establishing connections.

**Table 2-3: Typical Cold Start Latencies by Platform**

| Platform | Cold Start Range (ms) | Source |
|----------|----------------------|--------|
| AWS Lambda | 100–500 | [3] |
| Google Cloud Functions | 200–600 | [18] |
| Azure Functions | 500–1000 | [3] |
| Knative (on Kubernetes) | 1000–3000 | [19] |

Knative exhibits the highest cold start latency because it must provision a full Kubernetes pod (including Istio/Kourier sidecar injection) rather than a lightweight container sandbox. Beni et al. [8] demonstrated that maintaining warm containers during elastic scaling of Kubernetes-based serverless platforms can reduce cold start latency by 50–80%, motivating the predictive pre-warming approach implemented in this research.

The cold start penalty is particularly significant for latency-sensitive applications with strict SLO targets. If p99 latency must remain below 200ms, even a single cold start invocation can cause an SLO violation. This trade-off between serverless elasticity and cold start latency is a central motivation for the hybrid architecture proposed in this thesis: Kubernetes provides always-warm pods for baseline traffic, while serverless absorbs overflow—but only when prediction indicates sufficient lead time for warm-up.

---

## 2.2 Integrasi Kubernetes dan Serverless (Kubernetes-Serverless Integration)

The complementary strengths and weaknesses of Kubernetes (consistent low latency, cost-efficient for sustained loads, requires capacity planning) and serverless (instant elasticity, zero idle cost, cold start penalty) motivate their integration into hybrid architectures [3], [7].

### Hybrid Architecture Benefits

Integrating Kubernetes and serverless provides four key advantages:

1. **Cost optimization**: Use Kubernetes for predictable baseline load (avoiding per-invocation serverless costs) and serverless for burst traffic (avoiding over-provisioning Kubernetes resources).
2. **Performance**: Warm Kubernetes pods avoid cold start latency for the majority of requests, while serverless handles overflow that would otherwise queue behind a saturated K8s backend.
3. **Flexibility**: Different workload components can be assigned to the most appropriate execution platform based on their characteristics.
4. **Reliability**: Cross-platform routing provides fallback capability if either backend experiences degradation.

### Integration Patterns

Two primary patterns have been identified in the literature for integrating container orchestration with serverless platforms:

**Pattern 1: Overflow Model**

In the overflow pattern, Kubernetes handles all traffic up to its provisioned capacity. When Kubernetes reaches saturation (as detected by CPU, memory, or latency metrics), excess traffic overflows to the serverless backend.

```
                 Normal Load           High Load
                     │                     │
                     ▼                     ▼
              ┌─────────────┐       ┌─────────────┐
              │ Kubernetes  │       │ Kubernetes  │
              │ (handles    │       │ (at max)    │───┐
              │  100%)      │       │             │   │ Overflow
              └─────────────┘       └─────────────┘   │
                                                      ▼
                                           ┌─────────────────┐
                                           │   Serverless    │
                                           │   (handles      │
                                           │    overflow)    │
                                           └─────────────────┘
```

**Figure 2-3: Overflow Integration Pattern**

This pattern is reactive—it responds to saturation after it occurs. The latency between detecting saturation and serverless capacity becoming available (including potential cold starts) creates a window during which SLO violations may occur.

**Pattern 2: Predictive Routing**

The predictive routing pattern uses a forecasting model to anticipate traffic changes and proactively adjust the traffic distribution between backends before capacity limits are reached:

```
     Traffic ──► Predictor ──► Router ──┬──► Kubernetes
                                        │
                                        └──► Serverless
```

**Figure 2-4: Predictive Routing Pattern**

This pattern is the basis for the architecture proposed in this research. By forecasting workload 30 seconds ahead using a GRU neural network and combining the prediction with real-time SLO monitoring, the system can pre-warm serverless capacity and shift traffic proactively. The ElaX algorithm [7] provides the algorithmic framework for implementing this pattern, as detailed in Section 2.5.2.

---

## 2.3 Performa Aplikasi Cloud (Cloud Application Performance)

Measuring and managing cloud application performance requires a structured framework of metrics, targets, and monitoring approaches [9], [10].

### 2.3.1 SLA, SLO, dan SLI (Service Level Agreements)

A **Service Level Agreement (SLA)** is a contractual commitment between a service provider and consumer that defines expected performance levels and the consequences of failing to meet them [9].

An SLA is operationalized through:
- **SLI (Service Level Indicator)**: A quantitative measure of a service aspect (e.g., request latency, error rate, throughput).
- **SLO (Service Level Objective)**: A target value or range for an SLI (e.g., "p99 latency < 200ms").

**Table 2-4: Common SLO Targets**

| Metric | Typical Target | This Research |
|--------|---------------|---------------|
| p50 Latency | < 50ms | Measured |
| p95 Latency | < 100ms | Measured |
| p99 Latency | < 200ms | **Primary SLO** |
| Error Rate | < 0.1% | Measured |
| Availability | > 99.9% | Not evaluated |

This research uses p99 (99th percentile) latency as the primary SLO indicator, following the tail-at-scale principle articulated by Dean and Barroso [10]: in distributed systems, overall user-perceived latency is determined by the slowest component in the request path. Optimizing tail latency—rather than mean or median—is therefore essential for maintaining consistent user experience.

### 2.3.2 Waktu Respons Permintaan (Request Response Time)

Response time is the total duration from when a client sends a request to when it receives the complete response. It decomposes into:

$$\text{Total Response Time} = \text{Network Latency} + \text{Queue Time} + \text{Processing Time}$$

In a hybrid architecture, network latency includes routing overhead (HAProxy decision + backend selection), queue time includes any waiting in the Kubernetes or serverless request queue, and processing time is the actual application computation. Cold start latency in serverless adds to the processing time component for the first invocation.

**Tail latency** (p99, p99.9) represents the response time experienced by the slowest 1% or 0.1% of requests. Dean and Barroso [10] demonstrate that at scale, tail latency has outsized impact on user experience because any single slow backend can delay an entire aggregated request. The routing controller in this research monitors p99 latency specifically because it captures degradation before it affects the majority of users.

### 2.3.3 Utilisasi Sumber Daya (Resource Utilization)

Key resource metrics for evaluating cloud application efficiency include:

- **CPU Utilization**: Percentage of allocated CPU capacity consumed. Over-provisioning (low utilization) wastes cost; under-provisioning (high utilization) risks latency degradation.
- **Memory Utilization**: Percentage of allocated memory consumed. Memory pressure can trigger OOM (Out of Memory) kills, causing pod restarts.
- **Network I/O**: Bytes sent and received, relevant for detecting bandwidth saturation.

Aslanpour et al. [9] provide a comprehensive taxonomy of performance evaluation metrics for cloud, fog, and edge computing, noting that the most informative metrics depend on the deployment model and workload characteristics.

### 2.3.4 Skalabilitas dan Elastisitas (Scalability and Elasticity)

**Scalability** is the ability of a system to handle increasing workload by adding resources. Two types exist:
- **Vertical scaling** (scale-up): Adding CPU, memory, or storage to existing instances.
- **Horizontal scaling** (scale-out): Adding more instances to distribute load.

**Elasticity** extends scalability with the ability to both acquire and release resources automatically in response to demand changes. An elastic system scales out during traffic surges and scales in during lulls, matching resource allocation to actual demand over time [9].

Kubernetes achieves elasticity through the Horizontal Pod Autoscaler (HPA), which reacts to observed CPU or custom metrics. Serverless platforms offer inherent elasticity by provisioning function instances per invocation. The distinction between scalability (can the system grow?) and elasticity (does it grow and shrink automatically?) is central to this research, as the hybrid system combines Kubernetes's controlled scalability with serverless's rapid elasticity.

---

## 2.4 Algoritma dan Model Prediksi (Prediction Algorithms and Models)

Workload prediction transforms reactive scaling (responding to current metrics) into proactive scaling (preparing for anticipated demand). Time-series forecasting using recurrent neural networks has demonstrated effectiveness for cloud workload prediction tasks [5], [6].

### 2.4.1 LSTM (Long Short-Term Memory)

LSTM, introduced by Hochreiter and Schmidhuber [15], is a recurrent neural network architecture designed to learn long-term dependencies in sequential data. The key innovation is the **cell state**—a conveyor belt of information that runs through the entire sequence—regulated by three gating mechanisms:

```
           ┌───────────────────────────────────────────┐
           │              LSTM Cell                     │
           │  ┌─────────┐ ┌─────────┐ ┌─────────┐      │
    x_t ───┼─►│ Forget  │ │ Input   │ │ Output  │      │
           │  │ Gate    │ │ Gate    │ │ Gate    │      │
           │  └────┬────┘ └────┬────┘ └────┬────┘      │
           │       │           │           │            │
           │       ▼           ▼           ▼            │
           │  ┌────────────────────────────────────┐   │
h_{t-1} ───┼─►│         Cell State (C_t)           │───┼──► h_t
           │  └────────────────────────────────────┘   │
           └───────────────────────────────────────────┘
```

**Figure 2-5: LSTM Cell Architecture**

- **Forget Gate**: Decides what information to discard from the cell state.
- **Input Gate**: Decides what new information to store in the cell state.
- **Output Gate**: Decides what to output based on the cell state.

LSTM has been widely applied to cloud workload prediction [5], [16]. However, its three-gate architecture introduces substantial computational overhead: for a hidden state of size $h$, each LSTM cell requires $4h(h + x) + 4h$ parameters (where $x$ is the input dimension), resulting in slower training and higher inference latency compared to simpler alternatives.

### 2.4.2 GRU (Gated Recurrent Unit)

GRU, proposed by Cho et al. [6], simplifies the LSTM architecture by combining the forget and input gates into a single **update gate** and merging the cell state and hidden state:

```
           ┌───────────────────────────────────────────┐
           │              GRU Cell                      │
           │  ┌─────────┐ ┌─────────┐                  │
    x_t ───┼─►│ Reset   │ │ Update  │                  │
           │  │ Gate    │ │ Gate    │                  │
           │  └────┬────┘ └────┬────┘                  │
           │       │           │                        │
           │       ▼           ▼                        │
           │  ┌────────────────────────────────────┐   │
h_{t-1} ───┼─►│      Hidden State (h_t)            │───┼──► h_t
           │  └────────────────────────────────────┘   │
           └───────────────────────────────────────────┘
```

**Figure 2-6: GRU Cell Architecture**

- **Reset Gate**: Controls how much past information to forget.
- **Update Gate**: Controls the balance between previous hidden state and candidate activation, serving the combined role of LSTM's forget and input gates.

### LSTM vs GRU Comparison

Chung et al. [6] conducted an empirical evaluation of gated recurrent networks and found that GRU achieves comparable or superior performance to LSTM on many sequence modeling tasks while using approximately 25% fewer parameters. Mondal et al. [5] specifically evaluated both architectures for Kubernetes workload prediction and confirmed similar accuracy with significant computational savings.

**Table 2-5: LSTM vs GRU Comparison (based on [5], [6])**

| Aspect | LSTM | GRU |
|--------|------|-----|
| Gates | 3 (forget, input, output) | 2 (reset, update) |
| State vectors | 2 (cell state + hidden) | 1 (hidden only) |
| Parameters per cell | $4h(h+x) + 4h$ | $3h(h+x) + 3h$ |
| Training speed | Baseline | ~25% faster |
| Memory usage | Higher | Lower |
| Prediction accuracy | Reference | Comparable |
| Real-time suitability | Moderate | High |

For the workload prediction task in this research—short-horizon (30-second) HTTP traffic forecasting with a real-time latency constraint (<50ms inference)—GRU's lower computational cost and comparable accuracy make it the preferred architecture. The reduced parameter count also mitigates overfitting risk given the limited training data available from synthetic workload patterns [5], [16].

---

## 2.5 Strategi Penskalaan Kubernetes (Kubernetes Scaling Strategies)

### 2.5.1 Cluster dan Pod Autoscaler (Cluster and Pod Autoscaling)

Kubernetes provides built-in autoscaling mechanisms at two granularity levels [11], [12]:

**Horizontal Pod Autoscaler (HPA)** scales the number of pod replicas within a deployment based on observed resource utilization metrics:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: example-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: example-deployment
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

HPA operates on a control loop with a default period of 15 seconds. At each interval, it queries the metrics API, computes the desired replica count as:

$$\text{desiredReplicas} = \lceil \text{currentReplicas} \times \frac{\text{currentMetricValue}}{\text{desiredMetricValue}} \rceil$$

and scales toward that target, subject to min/max bounds and stabilization windows to prevent thrashing [12].

**Cluster Autoscaler** operates at the node level, adding nodes when pods cannot be scheduled (pending due to insufficient resources) and removing underutilized nodes after a configurable cool-down period.

**Limitation**: Both HPA and Cluster Autoscaler are fundamentally **reactive**—they respond to observed metric thresholds rather than anticipating future demand. Rzadca et al. [11] describe Google's Autopilot system, which incorporates historical workload analysis to recommend resource configurations, but still reacts to recent observations rather than forecasting. This reactive gap between demand onset and scaling completion is the core problem addressed by predictive approaches such as the one proposed in this research.

### 2.5.2 Metode ElaX dalam Penskalaan Kluster (ElaX Method in Cluster Scaling)

ElaX (Elastic Execution), proposed by Yang et al. [7], is an algorithm for provisioning resource elasticity in containerized online cloud services. ElaX introduces a two-layer decision architecture that separates workload prediction from resource management:

```
┌──────────────────────────────────────────────────────────────┐
│                       ElaX System                             │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐    ┌─────────────────┐                  │
│  │ Workload        │───►│ Resource        │                  │
│  │ Predictor       │    │ Allocation      │                  │
│  │ (LSTM/GRU)      │    │ (R = αx + β)   │                  │
│  └─────────────────┘    └────────┬────────┘                  │
│                                  │                            │
│                                  ▼                            │
│                    ┌─────────────────────────┐               │
│                    │    Online Controller     │               │
│                    │ (SLO Monitoring + Scaling)│              │
│                    └─────────────────────────┘               │
│                                  │                            │
│                    ┌─────────────┴─────────────┐             │
│                    ▼                           ▼              │
│           ┌─────────────┐            ┌─────────────┐         │
│           │ Kubernetes  │            │ Feedback    │         │
│           │ Cluster     │◄───────────│ Loop        │         │
│           └─────────────┘            └─────────────┘         │
└──────────────────────────────────────────────────────────────┘
```

**Figure 2-7: ElaX System Architecture [7]**

#### Key Components

1. **Workload Predictor**: Forecasts future traffic volume using a recurrent neural network (LSTM or GRU). The original ElaX paper uses LSTM; this research substitutes GRU for the computational efficiency reasons discussed in Section 2.4.2.

2. **Resource Allocation Model**: Maps predicted traffic to required compute resources using a linear model:

$$R = \alpha \cdot x + \beta$$

Where:
- $R$: CPU resources required (millicores)
- $x$: Traffic volume (requests per second)
- $\alpha$: Slope coefficient representing resource cost per request
- $\beta$: Base resource overhead (idle resource consumption)

The coefficients $\alpha$ and $\beta$ are derived through Ordinary Least Squares (OLS) regression on historical traffic-to-resource mappings and can be updated online through error feedback [7].

3. **Online Controller**: Monitors real-time SLO compliance and adjusts resources based on the gap between target and observed tail latency. The original ElaX online controller uses a slack-based scaling algorithm:

```
Algorithm: ElaX Online Control [7]
────────────────────────────────────────────────────────────────

Variables:
  SLO_target, slack ← 0, cur_resource

repeat:
  slack ← (SLO_target - GetTailLatency()) / SLO_target

  if slack < 0 then                    // SLO violated
    IncrResource(cur_resource * 10%)
  else if 0 < slack < 0.05 then        // Near violation
    IncrResource(cur_resource * 5%)
  else                                 // SLO comfortable
    extra_resource ← cur_resource - pre_resource
    if extra_resource > 0 then
      RemoveResource(extra_resource * 50%)
    end if
  end if

  wait(2)
until forever
```

**Figure 2-8: ElaX Online Control Algorithm (adapted from [7])**

#### Modifications in This Research

This research extends ElaX in three significant ways:

1. **GRU substitution**: Replacing LSTM with GRU as the workload predictor, reducing inference latency from ~100ms to ~40ms while maintaining comparable prediction accuracy [5], [6].

2. **Routing-first decision logic**: The original ElaX adjusts resource allocation within a single platform (scaling replicas up/down). This research extends the decision to **route traffic between platforms**—Kubernetes and serverless—adding a cross-platform dimension to the elasticity decision. This is implemented as Algorithm 1 (Routing Controller) in Section 3.4.3.1.

3. **Priority-based action hierarchy**: The original ElaX uses a single slack metric. This research introduces a priority-ordered action set (SCALE_OUT > PREDICTIVE > OPTIMIZE_COST > MAINTAIN) that integrates both reactive SLO monitoring and proactive GRU predictions into a unified decision framework, ensuring that SLO recovery always takes precedence over cost optimization.

The combination of ElaX's resource allocation model with cross-platform routing and GRU prediction forms the theoretical foundation for the hybrid system evaluated in this thesis.

---

## 2.6 Ringkasan Tinjauan Pustaka (Literature Review Summary)

This chapter has established the theoretical foundations for the proposed hybrid Kubernetes-serverless architecture. Table 2-6 summarizes the key concepts and their relevance to this research:

**Table 2-6: Literature Review Summary**

| Topic | Key References | Relevance to This Research |
|-------|---------------|---------------------------|
| Cloud computing models | [1], [17] | Motivates hybrid deployment strategy |
| Kubernetes orchestration | [2], [4], [12] | Baseline platform for container workloads |
| Serverless and cold starts | [3], [8], [19], [20] | Elastic overflow backend; cold start drives predictive pre-warming |
| SLO and tail latency | [9], [10] | Primary performance metric (p99 < 200ms) |
| GRU prediction | [5], [6], [15], [16] | Workload forecasting for proactive routing |
| ElaX elastic scaling | [7] | Algorithmic framework extended for hybrid routing |
| Kubernetes autoscaling | [11], [12] | Reactive baseline that prediction augments |

The identified research gap is the absence of an integrated system that combines: (a) GRU-based workload prediction with real-time SLO monitoring, (b) cross-platform traffic routing between Kubernetes and serverless, and (c) a priority-based decision framework that balances performance and cost. The methodology for addressing this gap is presented in Chapter 3.
