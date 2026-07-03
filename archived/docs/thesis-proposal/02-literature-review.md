# Chapter 2: Literature Review (Kajian Pustaka)

## 2.1 Cloud Computing

Cloud computing is a model for enabling ubiquitous, convenient, on-demand network access to a shared pool of configurable computing resources (e.g., networks, servers, storage, applications, and services) that can be rapidly provisioned and released with minimal management effort or service provider interaction.

### Cloud Service Models

| Model | Description | User Responsibility | Provider Responsibility |
|-------|-------------|---------------------|------------------------|
| **IaaS** | Infrastructure as a Service | Applications, Data, Runtime, Middleware, OS | Virtualization, Servers, Storage, Networking |
| **PaaS** | Platform as a Service | Applications, Data | Runtime, Middleware, OS, Virtualization, Servers, Storage, Networking |
| **SaaS** | Software as a Service | Data | Everything else |
| **FaaS** | Function as a Service | Function Code | Everything else including execution |

### Cloud Deployment Models

1. **Public Cloud**: Services offered over the public internet (AWS, GCP, Azure)
2. **Private Cloud**: Cloud infrastructure operated solely for a single organization
3. **Hybrid Cloud**: Combination of public and private clouds
4. **Multi-Cloud**: Use of multiple cloud providers

---

## 2.1.1 Container & Kubernetes

### Containers

Containers are lightweight, standalone, executable packages that include everything needed to run a piece of software:
- Code
- Runtime
- System tools
- System libraries
- Settings

**Advantages over Virtual Machines:**
- Faster startup time (seconds vs. minutes)
- Lower resource overhead
- Higher density (more containers per host)
- Consistent environment across development and production

### Kubernetes Architecture

Kubernetes (K8s) is an open-source container orchestration platform that automates deployment, scaling, and management of containerized applications.

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

**Key Components:**
- **API Server**: Entry point for all REST commands
- **Scheduler**: Assigns pods to nodes
- **Controller Manager**: Manages cluster state
- **etcd**: Stores cluster configuration and state
- **Kubelet**: Agent running on each node
- **Kube-proxy**: Network proxy on each node

---

## 2.1.2 Function as a Service and Serverless

### Serverless Computing

Serverless computing is a cloud execution model where:
- Cloud provider dynamically manages machine allocation
- Pricing is based on actual compute time consumed
- No server management required from the developer

### Serverless Architecture

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

**Characteristics:**
- **Event-driven**: Functions triggered by events
- **Stateless**: No persistent state between invocations
- **Auto-scaling**: Automatic scale from 0 to N
- **Pay-per-use**: Charged only for execution time

### Cold Start Problem

Cold start occurs when a function instance needs to be initialized:
1. Container provisioning
2. Runtime initialization
3. Function code loading
4. Dependency loading

**Typical cold start latencies:**
| Platform | Cold Start (ms) |
|----------|----------------|
| AWS Lambda | 100-500 |
| Google Cloud Functions | 200-600 |
| Azure Functions | 500-1000 |
| Knative | 1000-3000 |

---

## 2.2 Integration between Kubernetes and Serverless

### Hybrid Architecture Benefits

Integrating Kubernetes and serverless provides:

1. **Cost Optimization**: Use K8s for baseline, serverless for bursts
2. **Performance**: Warm K8s instances avoid cold starts
3. **Flexibility**: Choose best platform for each workload
4. **Reliability**: Fallback between platforms

### Integration Patterns

**Pattern 1: Overflow Model**
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

**Pattern 2: Predictive Routing**
```
     Traffic ──► Predictor ──► Router ──┬──► Kubernetes
                                        │
                                        └──► Serverless
```

---

## 2.3 Cloud Application Performance

### 2.3.1 SLA Violations

A Service Level Agreement (SLA) defines performance targets:
- **Availability**: 99.9%, 99.99%, etc.
- **Latency**: p50, p95, p99 thresholds
- **Error Rate**: Maximum acceptable error percentage

**SLO (Service Level Objective)**: Specific measurable target within an SLA

**Common SLO Targets:**
| Metric | Typical Target |
|--------|---------------|
| p50 Latency | < 50ms |
| p95 Latency | < 100ms |
| p99 Latency | < 200ms |
| Error Rate | < 0.1% |
| Availability | > 99.9% |

### 2.3.2 Request Response Time

Response time components:
```
Total Response Time = Network Latency + Queue Time + Processing Time
```

**Tail Latency**: The latency experienced by the slowest requests (p99, p99.9)

### 2.3.3 Resource Utilization

Key metrics:
- **CPU Utilization**: Percentage of CPU capacity used
- **Memory Utilization**: Percentage of memory used
- **Network I/O**: Bytes sent/received
- **Disk I/O**: Read/write operations

### 2.3.4 Scalability and Elasticity

**Scalability Types:**
- **Vertical Scaling**: Adding resources to existing instances
- **Horizontal Scaling**: Adding more instances

**Elasticity**: The ability to automatically scale resources up/down based on demand

---

## 2.4 Prediction Algorithms and Models

### 2.4.1 LSTM (Long Short-Term Memory)

LSTM is a type of recurrent neural network (RNN) designed to learn long-term dependencies:

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

**Advantages:**
- Captures long-term dependencies
- Mitigates vanishing gradient problem

**Disadvantages:**
- Computationally expensive
- Slower training and inference

### 2.4.2 GRU (Gated Recurrent Unit)

GRU is a simplified version of LSTM with fewer parameters:

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

**Advantages over LSTM:**
- Fewer parameters (faster training)
- Lower memory usage
- Similar accuracy for many tasks
- Better for resource-constrained environments

**GRU vs LSTM Comparison (Mondal et al., 2023):**
| Aspect | LSTM | GRU |
|--------|------|-----|
| Parameters | 4 gates | 2 gates |
| Training Speed | Slower | Faster |
| Memory Usage | Higher | Lower |
| Accuracy | Similar | Similar |
| Recommended | Complex sequences | Simpler patterns |

---

## 2.5 Kubernetes Scaling Strategies

### 2.5.1 Cluster & Pod Autoscaler

**Horizontal Pod Autoscaler (HPA):**
- Scales pods based on CPU/memory utilization
- Reactive (responds to current metrics)
- Configurable target utilization

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

**Cluster Autoscaler:**
- Scales the number of nodes in a cluster
- Adds nodes when pods can't be scheduled
- Removes underutilized nodes

### 2.5.2 ElaX Method in Cluster Scaling

ElaX (Elastic Execution) by Yang et al. (2019) is an algorithm for provisioning resource elasticity in containerized online cloud services.

**ElaX Architecture:**

```
┌──────────────────────────────────────────────────────────────┐
│                       ElaX System                             │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐    ┌─────────────────┐                  │
│  │ Workload        │───►│ Resource        │                  │
│  │ Predictor       │    │ Allocation      │                  │
│  │ (LSTM/GRU)      │    │ (R = αx + β)    │                  │
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

**Key Components:**

1. **Workload Predictor**: Forecasts future traffic using ML models
2. **Resource Allocation**: Maps predicted load to resources
3. **Online Controller**: Real-time SLO monitoring and adjustment

**Resource Allocation Formula:**

$$R = \alpha \cdot x + \beta$$

Where:
- $R$: CPU resources required
- $x$: Traffic volume (requests/second)
- $\alpha$: Slope coefficient (resource per request)
- $\beta$: Base resource overhead

**Algorithm 1: ElaX Online Control**

```pseudocode
Variables:
  SLO_target ← False
  slack ← 0
  cur_resource

repeat:
  slack ← (SLO_target - GetTailLatency()) / SLO_target
  
  if slack > 0 then
    IncrResource(cur_resource * 10%)
  else if 0 < slack < 0.05 then
    IncrResource(cur_resource * 5%)
  else
    extra_resource ← cur_resource - pre_resource
    if extra_resource > 0 then
      RemoveResource(extra_resource * 50%)
  end if
  
  wait(2)  // Delay for 2 seconds
until forever
```
