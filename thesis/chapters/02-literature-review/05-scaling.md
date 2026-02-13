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
