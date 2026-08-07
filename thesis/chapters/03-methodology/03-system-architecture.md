## 3.3 Method Design: System Architecture (Perancangan Arsitektur Sistem)

### 3.3.1 Hybrid Architecture Overview

The proposed system integrates three subsystems: an offline training pipeline, an online prediction and control plane, and a hybrid execution infrastructure. The architecture follows a two-layer design inspired by the ElaX algorithm framework (Yang et al., 2019), where Algorithm 1 governs traffic routing between execution platforms and Algorithm 2 manages cluster-level resource scaling. Both algorithms are integrated into a single routing daemon that executes them in a coordinated 15-second control loop: Algorithm 1 provides immediate traffic shedding to serverless, while Algorithm 2 scales Kubernetes replicas to restore capacity, after which Algorithm 1 returns traffic to Kubernetes.

```
┌──────────────────────────────────────────────────────────────────────┐
│                       PROPOSED HYBRID SYSTEM                         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────────────────────────────────────────────────┐       │
│   │                    OFFLINE TRAINING                      │       │
│   │  ┌──────────────┐         ┌──────────────────────────┐  │       │
│   │  │ Synthetic    │────────►│ GRU Training Pipeline    │  │       │
│   │  │ Workload     │         │ • Feature engineering    │  │       │
│   │  │ Patterns     │         │ • Model training         │  │       │
│   │  │              │         │ • Hyperparameter tuning   │  │       │
│   │  └──────────────┘         └───────────┬──────────────┘  │       │
│   │                                       │                  │       │
│   │                                       ▼                  │       │
│   │                           ┌──────────────────────┐      │       │
│   │                           │ Trained GRU Model    │      │       │
│   │                           └───────────┬──────────┘      │       │
│   └───────────────────────────────────────┼──────────────────┘       │
│                                           │                          │
│   ┌───────────────────────────────────────┼──────────────────┐       │
│   │                    ONLINE PREDICTION   │                  │       │
│   │                                       ▼                  │       │
│   │  ┌──────────────┐         ┌──────────────────────────┐  │       │
│   │  │ Real-time    │────────►│ GRU Predictor             │  │       │
│   │  │ Traffic      │         │ (9-step / 135-sec forecast)│  │       │
│   │  │ Metrics      │         └──────────────────────────┘  │       │
│   │  └──────────────┘                     │                  │       │
│   │                                       ▼                  │       │
│   │                      ┌────────────────────────────┐     │       │
│   │                      │ Resource Allocation Model  │     │       │
│   │                      │      R = α·x + β           │     │       │
│   │                      └────────────┬───────────────┘     │       │
│   │                                   │                      │       │
│   │                                   ▼                      │       │
│   │               ┌───────────────────────────────────┐     │       │
│   │               │      ONLINE CONTROLLERS            │     │       │
│   │               │  ┌─────────────┐ ┌─────────────┐  │     │       │
│   │               │  │ Algorithm 1 │ │ Algorithm 2 │  │     │       │
│   │               │  │ Routing     │ │ Cluster     │  │     │       │
│   │               │  │ Controller  │ │ Controller  │  │     │       │
│   │               │  │ (Impl.)     │ │ (Integrated)│  │     │       │
│   │               │  └──────┬──────┘ └──────┬──────┘  │     │       │
│   │               └─────────┼───────────────┼─────────┘     │       │
│   │                         │               │                │       │
│   └─────────────────────────┼───────────────┼────────────────┘       │
│                             │               │                        │
│   ┌─────────────────────────┼───────────────┼────────────────┐       │
│   │            INFRASTRUCTURE               │                │       │
│   │                         ▼               ▼                │       │
│   │   ┌─────────────────────────────────────────────────┐   │       │
│   │   │              TRAFFIC ROUTER (HAProxy)            │   │       │
│   │   └─────────────┬───────────────────────┬───────────┘   │       │
│   │                 │                       │                │       │
│   │                 ▼                       ▼                │       │
│   │   ┌─────────────────────┐   ┌─────────────────────┐    │       │
│   │   │   KUBERNETES (K3s)  │   │     SERVERLESS      │    │       │
│   │   │   • Baseline warm   │   │     (Knative)       │    │       │
│   │   │   • Predictable cap │   │   • Elastic scale   │    │       │
│   │   │   • Steady traffic  │   │   • Burst handling  │    │       │
│   │   └─────────────────────┘   └─────────────────────┘    │       │
│   │                                                          │       │
│   └──────────────────────────────────────────────────────────┘       │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.3.2 Infrastructure Components

The infrastructure layer consists of three components:

**HAProxy (Traffic Router):** Serves as the entry point for all HTTP traffic, distributing requests between the Kubernetes and serverless backends according to weighted routing rules. Weights are dynamically adjusted by Algorithm 1 through the HAProxy Runtime API (TCP socket interface). HAProxy also exposes a statistics endpoint that provides real-time throughput and latency metrics consumed by the monitoring subsystem.

**K3s (Kubernetes Backend):** A lightweight, certified Kubernetes distribution deployed via k3d (k3s-in-Docker). K3s runs the primary application workload as always-warm pods, providing consistent low-latency responses for baseline traffic. In this study, K3s serves as the baseline warm capacity; relative cost advantage is evaluated empirically per run rather than assumed a priori.

**Knative Serving (Serverless Backend):** Deployed on the same K3s cluster using Kourier as the ingress controller. Knative provides scale-to-zero capability and rapid autoscaling for burst traffic. Routing responds to observed capacity and tail latency in the V3 controller; the GRU forecast gates proactive **scaling** decisions in Algorithm 2. Trend extrapolation of observed load may gate proactive routing, but GRU prediction does not directly set HAProxy weights.

### 3.3.3 Monitoring and Metrics Collection

The system uses Prometheus for metrics collection and the SLO monitor component for real-time compliance checking:

- **Prometheus** scrapes HAProxy statistics at 1-second intervals, collecting request counts, response times, and backend health status.
- **SLO Monitor** computes the 99th percentile (p99) tail latency from Prometheus time-series data and maintains a rolling violation window to detect sustained SLO breaches.
- **Prometheus metrics** from the routing daemon itself (decision counts, weight changes, prediction usage) enable post-experiment analysis and debugging.
