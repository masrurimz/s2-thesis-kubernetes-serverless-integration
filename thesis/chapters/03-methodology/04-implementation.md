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

### 3.4.2 Resource Allocation Model (Model Alokasi Sumber Daya)

A linear resource allocation model translates predicted workload into required Kubernetes resources. This model is used **online** by the routing daemon to compute replica scaling targets that are applied to the Kubernetes deployment in real time.

$$R = \alpha \cdot x + \beta$$

Where:

- $R$: required Kubernetes capacity (expressed as **target replica count** for the primary deployment)
- $x$: predicted traffic intensity (requests per second), produced by the GRU predictor for the next 30 seconds
- $\alpha$: resource-per-request coefficient (replicas per RPS)
- $\beta$: base replica overhead (minimum replicas at near-zero traffic)

**Online Usage in the Live System:**

At each control interval (15 seconds), the daemon obtains: (1) current observed load from HAProxy/Prometheus, (2) predicted load 30 seconds ahead from the GRU server, and (3) current replica state from Kubernetes. Algorithm 2 then computes a target replica count:

$$R_{target} = \text{clamp}\left(\lceil (\alpha \cdot x_{pred} + \beta) \cdot \gamma \rceil, R_{min}, R_{max}\right)$$

where $\gamma$ is a safety buffer (e.g., 1.2 for +20% headroom), and $R_{min}$, $R_{max}$ are fixed bounds to prevent extreme scaling. The computed target is **enforced** by issuing Kubernetes scaling commands (Section 3.4.3.2).

**Coefficient Derivation (OLS):**

The coefficients $\alpha$ and $\beta$ are obtained using Ordinary Least Squares (OLS) regression on calibration data collected from the same application and testbed:

1. Fix replicas to known values $R \in \{1, 2, \ldots, k\}$.
2. For each $R$, run a short steady workload sweep and record the sustainable throughput before crossing a latency SLO guardrail (p99 ≤ 200 ms).
3. Fit a linear model: $R \approx \alpha x + \beta$.

```python
from sklearn.linear_model import LinearRegression

model = LinearRegression()
model.fit(X_historical_traffic, y_historical_resources)

alpha = model.coef_[0]   # Resource per request coefficient
beta = model.intercept_   # Base resource overhead
```

The calibration dataset, fitted coefficients, and chosen SLO guardrail are stored as experiment artifacts for reproducibility.

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

#### 3.4.3.2 Algorithm 2: Cluster Controller (Terintegrasi pada Routing Daemon)

Algorithm 2 is integrated into the live routing daemon and executes real Kubernetes scaling actions. The hybrid design uses **two coordinated control actions**:

1. **Algorithm 1 (Routing Controller)** performs **immediate traffic shedding** by shifting a portion of traffic to the serverless (Knative) backend when a surge is detected or an SLO violation occurs.
2. **Algorithm 2 (Cluster Controller)** performs **capacity restoration** by scaling Kubernetes replicas so that the Kubernetes backend can absorb the workload again.
3. Once Kubernetes is scaled, ready, and healthy, **Algorithm 1 gradually returns traffic** from serverless back to Kubernetes, allowing Knative to scale down to zero.

This design intentionally leverages the complementary strengths of the platforms: Knative provides rapid burst absorption (instant overflow), while Kubernetes provides cost-efficient steady capacity once replicas are ready.

This coordination is active only in hybrid scenarios (S3 and S4). In baseline scenarios, S1 relies on HPA for native Kubernetes autoscaling without routing changes, and S2 relies on Knative KPA for serverless autoscaling without Kubernetes involvement.

**Control-Loop Integration:**

The daemon runs a **15-second control loop**. Algorithm 2 is executed in the same loop after Algorithm 1's routing decision, using the latest prediction and system state:

```text
Observe metrics → Predict (GRU) → Algorithm 1: shift traffic immediately if needed
                               → Algorithm 2: scale K8s replicas toward predicted demand
                               → If K8s ready+healthy: Algorithm 1 shifts traffic back to K8s
```

**Reactive vs Predictive Modes:** Algorithm 2 operates in two modes depending on the scenario. In **reactive mode** (S3), the scaling signal is the mean observed RPS over the last 30 seconds ($x_{obs}$), computed from HAProxy request counters. In **predictive mode** (S4), the signal is the GRU 30-second-ahead forecast ($x_{pred}$). Both modes use the identical resource model ($R = \alpha \cdot x + \beta$) and identical parameters ($\alpha$, $\beta$, $\gamma$, $R_{min}$, $R_{max}$, cooldowns), ensuring that any performance difference between S3 and S4 is attributable solely to the prediction signal.

**Kubernetes Scaling Mechanism:**

Scaling is performed by invoking `kubectl scale deployment/<name> --replicas=<R_target>`. This approach is chosen because it is deterministic, directly reproducible, and provides an explicit audit trail in controller logs. Infrastructure validation (Phase A0, Section 3.5.3) confirmed that Kubernetes HPA overrides manual `kubectl scale` commands after its stabilization window (~5 minutes), making the two mechanisms mutually exclusive. Therefore, Algorithm 2 requires HPA to be deleted from the target Deployment before it can safely control replicas. This mutual exclusion is enforced in the per-run reset procedure: S1 uses HPA as the native baseline, while S3 and S4 delete HPA and rely exclusively on Algorithm 2 for replica scaling.

**Safety Checks and Anti-Oscillation Rules:**

- **Cooldown:** minimum 30 seconds between scale-up actions, 60 seconds for scale-down.
- **Bounds:** replicas clamped to $[R_{min}, R_{max}]$.
- **Scale-down hysteresis:** scale-down only if target is below 80% of current capacity for a sustained window.
- **Readiness verification:** traffic returns to Kubernetes only after `availableReplicas == desiredReplicas` and HAProxy backend health checks show Kubernetes endpoints as UP.

**Algorithm 2: Integrated Cluster Controller (Reactive and Predictive Modes)**

```pseudocode
Algorithm 2: Integrated Cluster Controller (K8s Replica Scaling)
────────────────────────────────────────────────────────────────

Constants:
  CONTROL_INTERVAL ← 15 seconds
  BUFFER γ ← 1.2
  MIN_REPLICAS ← 1
  MAX_REPLICAS ← 10
  SCALE_DOWN_HYSTERESIS ← 0.8
  SCALE_UP_COOLDOWN ← 30 seconds
  SCALE_DOWN_COOLDOWN ← 60 seconds

Configuration:
  mode ∈ {REACTIVE, PREDICTIVE}    // S3 = REACTIVE, S4 = PREDICTIVE

State:
  last_scale_up_time ← null
  last_scale_down_time ← null

repeat every CONTROL_INTERVAL:

  // Step 1: Determine scaling signal based on mode
  R_current ← K8s.get_deployment_replicas()
  p99 ← SLOMonitor.p99()

  if mode = REACTIVE:
    x ← HAProxy.mean_rps(window=30s)          // observed RPS over last 30s
  else if mode = PREDICTIVE:
    x_pred, conf ← GRU.predict_next_30s()
    if conf < CONFIDENCE_THRESHOLD:
      x ← HAProxy.mean_rps(window=30s)        // fallback to observed if low confidence
    else:
      x ← x_pred

  // Step 2: Compute target replicas (identical formula for both modes)
  R_raw ← α × x + β
  R_target ← clamp(ceil(R_raw × γ), MIN_REPLICAS, MAX_REPLICAS)

  // Step 3: Scale-up decision
  if R_target > R_current AND cooldown_passed(last_scale_up_time, SCALE_UP_COOLDOWN):
    kubectl scale deployment/app --replicas=R_target
    last_scale_up_time ← now

  // Step 4: Scale-down decision (conservative)
  else if R_target < R_current × SCALE_DOWN_HYSTERESIS
          AND cooldown_passed(last_scale_down_time, SCALE_DOWN_COOLDOWN)
          AND p99 < SLO_THRESHOLD × HEALTHY_MARGIN:
    kubectl scale deployment/app --replicas=R_target
    last_scale_down_time ← now

until shutdown
```

The only difference between S3 and S4 is the source of `x` in Step 1: S3 always uses observed RPS, while S4 uses the GRU forecast (with fallback to observed if confidence is below threshold). Steps 2–4 are identical, ensuring that any performance difference between S3 and S4 is attributable solely to the prediction signal.

**Coordination with Algorithm 1:**

When Kubernetes scaling completes (replicas ready and endpoints healthy) and p99 latency is within the healthy margin, Algorithm 1 enters OPTIMIZE_COST mode and gradually increases Kubernetes weight (10% steps) until Knative weight reaches 0%. This creates a closed-loop behavior: serverless absorbs bursts immediately → Kubernetes scales to meet predicted demand → traffic returns to Kubernetes once capacity is available → serverless returns to zero for cost efficiency.
