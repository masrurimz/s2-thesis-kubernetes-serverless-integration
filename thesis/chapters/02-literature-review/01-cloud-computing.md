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
