## 3.4 Implementation Method (Metode Implementasi)

### 3.4.1 Workload Predictor (GRU Architecture)

The workload prediction model uses a Gated Recurrent Unit (GRU) neural network, chosen for its favorable trade-off between prediction accuracy and computational efficiency compared to LSTM networks. GRU achieves comparable performance with fewer parameters, resulting in faster training and lower inference latency.

**Architecture:**

```
Input: Time-series window (60 seconds of RPS data)
                    │
                    ▼
        ┌───────────────────────┐
        │   Input Layer         │
        │   (sequence_length,   │
        │    features)          │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   GRU Layer 1         │
        │   (64 units)          │
        │   + Dropout (0.2)     │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   GRU Layer 2         │
        │   (32 units)          │
        │   + Dropout (0.2)     │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   Dense Layer         │
        │   (prediction_horizon)│
        └───────────┬───────────┘
                    │
                    ▼
Output: Predicted RPS for next 30 seconds
```

The model consists of two stacked GRU layers with decreasing hidden dimensions (64 → 32 units), each followed by dropout regularization (rate 0.2) to prevent overfitting. The final dense layer outputs the predicted RPS value for the 30-second prediction horizon. This multi-step prediction enables the routing controller to anticipate workload changes and take proactive action.

**Training Configuration:**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Optimizer | Adam | Adaptive learning rate, standard for RNN training |
| Loss function | Mean Squared Error (MSE) | Direct optimization of prediction accuracy |
| Batch size | 32 | Balance between gradient stability and memory usage |
| Epochs | 100 (with early stopping) | Early stopping prevents overfitting on validation loss |
| Validation split | 15% | Sufficient for monitoring generalization |
| Learning rate | Default (0.001) | Adam default, no manual scheduling needed |

**Prediction Server:** The trained model is served via a FastAPI prediction server that accepts recent RPS history as input and returns both the predicted load value and a confidence score. The confidence score is computed from prediction variance and serves as a gating mechanism—the routing controller only acts on predictions exceeding a configurable confidence threshold (default: 0.5).

### 3.4.2 Resource Allocation Model

A linear resource allocation model translates predicted workload into required compute resources:

$$R = \alpha \cdot x + \beta$$

Where:

- $R$: Required resources (expressed as replica count or CPU millicores)
- $x$: Predicted traffic (requests per second)
- $\alpha$: Resource-per-request coefficient (how many additional resources each RPS requires)
- $\beta$: Base resource overhead (minimum resources needed at zero load)

**Coefficient Derivation (OLS):**

The coefficients $\alpha$ and $\beta$ are derived using Ordinary Least Squares (OLS) regression on historical workload-to-resource mapping data:

```python
from sklearn.linear_model import LinearRegression

model = LinearRegression()
model.fit(X_historical_traffic, y_historical_resources)

alpha = model.coef_[0]   # Resource per request coefficient
beta = model.intercept_   # Base resource overhead
```

This model is used by Algorithm 2 (Cluster Controller) to compute scaling targets from GRU predictions.

### 3.4.3 Online Controllers

The online control plane consists of two algorithms that operate at different layers of the system.

#### 3.4.3.1 Algorithm 1: Routing Controller (Primary Implementation)

Algorithm 1 is the primary decision engine, fully implemented and experimentally evaluated. It monitors SLO compliance and adjusts traffic routing weights between Kubernetes and serverless backends using a priority-based decision framework.

**Algorithm 1: SLO-Aware Routing Controller**

```pseudocode
Algorithm 1: SLO-Aware Routing Controller
────────────────────────────────────────────────────────────────

Constants:
  SLO_THRESHOLD ← 200ms            // p99 latency target
  HEALTHY_MARGIN ← 0.7             // healthy = p99 < SLO × 0.7
  WEIGHT_STEP ← 10                 // weight adjustment increment
  COOLDOWN ← 15 seconds            // minimum time between adjustments
  MAX_SERVERLESS ← 50              // maximum serverless weight (%)
  CONFIDENCE_THRESHOLD ← 0.5       // minimum prediction confidence
  LOAD_CHANGE_THRESHOLD ← 0.3      // significant load change (30%)

Variables:
  weights ← {k3s: 100, knative: 0}  // initial: all traffic to K8s
  serverless_enabled ← False
  last_adjustment_time ← null

repeat every COOLDOWN seconds:

  // Step 1: Get current metrics
  slo_status ← SLOMonitor.check()
  prediction ← GRUClient.predict() if available
  current_load ← get_current_rps()

  // Step 2: Priority-based decision
  if slo_status.violation_duration ≥ VIOLATION_WINDOW then
    // SCALE_OUT (Priority 1): SLO violated → shift to serverless
    if not serverless_enabled then
      enable_serverless_backend()
      prewarm_knative()
      serverless_enabled ← True
    end if
    knative_weight ← min(MAX_SERVERLESS, weights.knative + WEIGHT_STEP)
    weights ← {k3s: 100 - knative_weight, knative: knative_weight}

  else if slo_status.p99 < SLO_THRESHOLD × HEALTHY_MARGIN then
    // OPTIMIZE_COST (Priority 3): Healthy → reduce serverless usage
    step ← WEIGHT_STEP / 2
    k3s_weight ← min(100, weights.k3s + step)
    weights ← {k3s: k3s_weight, knative: 100 - k3s_weight}
    if weights.knative = 0 then
      serverless_enabled ← False
    end if

  else if prediction ≠ null
         AND prediction.confidence ≥ CONFIDENCE_THRESHOLD
         AND load_change(prediction, current_load) > LOAD_CHANGE_THRESHOLD then
    // PREDICTIVE (Priority 2): Predicted surge → preemptive scale out
    if not serverless_enabled then
      enable_serverless_backend()
      prewarm_knative()
      serverless_enabled ← True
    end if
    knative_weight ← min(MAX_SERVERLESS, weights.knative + WEIGHT_STEP)
    weights ← {k3s: 100 - knative_weight, knative: knative_weight}

  else
    // MAINTAIN (Priority 4): No change needed
    // Keep current weights
  end if

  // Step 3: Apply weights to HAProxy
  HAProxy.set_weights(weights.k3s, weights.knative)

until shutdown
```

**Decision Types and Priority:**

| Priority | Action | Trigger Condition | Effect |
|----------|--------|-------------------|--------|
| 1 | SCALE_OUT | p99 > SLO threshold for sustained period | Shift traffic toward serverless |
| 2 | PREDICTIVE | Healthy state + GRU predicts >30% load increase | Preemptive serverless engagement |
| 3 | OPTIMIZE_COST | p99 < SLO × healthy margin | Reduce serverless usage |
| 4 | MAINTAIN | None of the above | Keep current weights |

The priority ordering ensures that active SLO violations always take precedence over predictive optimization, which in turn takes precedence over cost optimization. This prevents the system from reducing serverless capacity during a predicted surge.

**Weight Progression:**

Traffic weights shift gradually in increments of WEIGHT_STEP (10%) to avoid oscillation:

```
100/0 (K8s only) → 90/10 → 80/20 → 70/30 → 60/40 → 50/50 (maximum serverless)
```

The maximum serverless weight is capped at 50% to ensure the Kubernetes backend always handles at least half of the traffic, maintaining cost efficiency for baseline load.

**Knative Pre-warming:** When serverless is first enabled (either by SCALE_OUT or PREDICTIVE), the controller sends a synthetic health-check request to the Knative service endpoint to trigger cold start initialization. This reduces the latency penalty when actual traffic begins routing to the serverless backend.

#### 3.4.3.2 Algorithm 2: Cluster Controller (Proof-of-Concept)

Algorithm 2 addresses cluster-level resource scaling by computing required Kubernetes replica counts from predicted workload using the linear resource model. This algorithm is implemented as a proof-of-concept to demonstrate architectural feasibility; it is not integrated into the live experiment pipeline and is not subjected to full experimental evaluation.

**Algorithm 2: Prediction-Based Cluster Controller (Proposed)**

```pseudocode
Algorithm 2: Cluster Controller (Proof-of-Concept)
────────────────────────────────────────────────────────────────

Constants:
  ALPHA ← 0.01           // replicas per request/s
  BETA ← 1.0             // base replicas (minimum)
  BUFFER ← 1.2           // 20% capacity buffer
  MIN_REPLICAS ← 1
  MAX_REPLICAS ← 10
  SCALE_DOWN_THRESHOLD ← 0.8
  PREDICTION_INTERVAL ← 30 seconds

Variables:
  current_replicas ← 1

repeat every PREDICTION_INTERVAL:

  // Step 1: Get prediction
  predicted_load ← GRUPredictor.predict()

  // Step 2: Calculate required resources
  required ← ALPHA × predicted_load + BETA

  // Step 3: Apply buffer and clamp
  target ← clamp(required × BUFFER, MIN_REPLICAS, MAX_REPLICAS)

  // Step 4: Scaling decision
  if target > current_replicas then
    action ← SCALE_UP
    // Would execute: kubectl scale deployment --replicas=target
  else if target < current_replicas × SCALE_DOWN_THRESHOLD then
    action ← SCALE_DOWN
  else
    action ← MAINTAIN
  end if

  current_replicas ← target  // Simulate applying decision

until shutdown
```

**Implementation scope:** The proof-of-concept implementation computes scaling decisions and logs them with a full audit trail, but does not execute actual `kubectl scale` commands. Integration with Kubernetes HPA (Horizontal Pod Autoscaler) or VPA (Vertical Pod Autoscaler) is left for future work. The implementation includes 14 unit tests validating the computation logic, scaling boundaries, and decision categorization.
