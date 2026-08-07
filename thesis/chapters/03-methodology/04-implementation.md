## 3.4 Implementation Method (Metode Implementasi)

### 3.4.1 Workload Predictor (GRU Architecture)

The workload prediction model uses a Gated Recurrent Unit (GRU), chosen for its balance of accuracy, parameter count, and inference cost. The final model emits a direct multi-horizon forecast:

```text
Input: 30 samples of RPS at 15-second resolution
                    │
                    ▼
        ┌───────────────────────┐
        │   GRU layers +        │
        │   dropout regularizer  │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ Dense output: 9 steps │
        │ (9 × 15 s = 135 s)    │
        └───────────┬───────────┘
                    │
                    ▼
Output: forecast RPS for the next 135 seconds
```

The model uses stacked recurrent layers and dropout regularization. The prediction server returns the forecast and a confidence score. Confidence gating prevents low-confidence forecasts from driving proactive scaling. Synthetic test RMSE is 4.75% after HPO (6.01% before HPO); real ClarkNet RMSE is 17.78%.

**Training configuration:** Adam optimizer, MSE loss, batch size 32, up to 100 epochs with early stopping, and a 15% temporally ordered validation split. Inference is designed to fit comfortably within the 15-second control cycle.

### 3.4.2 Resource Allocation Model (Model Alokasi Sumber Daya)

The resource model translates a traffic signal into a Kubernetes replica target:

$$R = \alpha \cdot x + \beta$$

where $R$ is the target replica count, $x$ is either observed RPS or forecast RPS, $\alpha$ is the calibrated replicas-per-RPS coefficient, and $\beta$ is the base overhead. The code-verified final calibration uses `fib_n=33`, $r_{saturation}=33.3$ RPS per replica, target CPU utilization 0.5, and therefore $r_{effective}=16.65$ and $\alpha=1/r_{effective}\approx0.0601$. Bounds and a safety clamp prevent extreme replica targets.

The coefficient is calibrated from sustainable-throughput measurements at known replica counts, using p99 ≤ 200 ms as the SLO guardrail. In S3, $x=x_{obs}$ (observed RPS); in S4, $x=x_{pred}$ (the confidence-gated GRU forecast). The scaling model is the same in both modes; only the signal source differs.

### 3.4.3 Online Controllers

The online control plane consists of two coordinated algorithms. Algorithm 1 controls traffic distribution; Algorithm 2 controls Kubernetes replica capacity. They run in a 15-second loop.

#### 3.4.3.1 Algorithm 1: Routing Controller (V3)

Algorithm 1 is the V3 capacity-driven routing controller. It uses observed load, ready Kubernetes capacity, and p99 state to adjust HAProxy weights. It does **not** use `GRUClient.predict()` to increase routing weights. A prediction can mark the PREDICTIVE priority and is consumed by Algorithm 2 for proactive scaling; routing remains grounded in observed capacity and tail latency. Observed-load trend extrapolation may gate a proactive routing shift.

**Algorithm 1: V3 SLO- and Capacity-Aware Routing Controller**

```pseudocode
Algorithm 1: V3 Routing Controller
────────────────────────────────────────────────────────────────
Constants:
  SLO_THRESHOLD ← 200ms
  HEALTHY_MARGIN ← 0.7
  WEIGHT_STEP ← 10
  CONTROL_INTERVAL ← 15 seconds
  MAX_SERVERLESS ← 50
  CONFIDENCE_THRESHOLD ← 0.5

State:
  weights ← {k8s: 100, knative: 0}
  serverless_enabled ← false

repeat every CONTROL_INTERVAL:
  p99 ← SLOMonitor.p99()
  observed_load ← HAProxy.current_rps()
  ready_capacity ← K8s.ready_replica_capacity()
  trend ← extrapolate_observed_load(window=30s)
  forecast, confidence ← GRUClient.predict() if available

  // Priority 1: SCALE_OUT responds to observed overload/tail latency.
  if p99 > SLO_THRESHOLD or observed_load > ready_capacity:
    action ← SCALE_OUT
    enable_serverless_and_prewarm_if_needed()
    weights.knative ← min(MAX_SERVERLESS,
                           weights.knative + WEIGHT_STEP)

  // Priority 2: PREDICTIVE marks forecast-assisted scaling only.
  else if forecast is valid and confidence ≥ CONFIDENCE_THRESHOLD
          and forecast indicates a future replica increase:
    action ← PREDICTIVE
    // Do not derive HAProxy weights from the forecast.
    Algorithm2.submit_forecast(forecast, confidence)
    // Routing remains based on observed trend/capacity.
    if trend indicates observed capacity risk:
      enable_serverless_and_prewarm_if_needed()
      weights.knative ← min(MAX_SERVERLESS,
                             weights.knative + WEIGHT_STEP)

  // Priority 3: reclaim serverless capacity in a healthy state.
  else if p99 < SLO_THRESHOLD × HEALTHY_MARGIN:
    action ← OPTIMIZE_COST
    weights.knative ← max(0, weights.knative - WEIGHT_STEP / 2)
    if weights.knative = 0:
      serverless_enabled ← false

  // Priority 4: no change.
  else:
    action ← MAINTAIN

  HAProxy.set_weights(100 - weights.knative, weights.knative)
  record(action, observed_load, ready_capacity, weights)

until shutdown
```

The final priority order is **SCALE_OUT > PREDICTIVE > OPTIMIZE_COST > MAINTAIN**. There is no separate SCALE_IN action: reducing serverless weight and consolidation are part of `OPTIMIZE_COST`. The graduated weight sequence is 100/0 → 90/10 → 80/20 → 70/30 → 60/40 → 50/50.

#### 3.4.3.2 Algorithm 2: Cluster Controller (Integrated in the Routing Daemon)

Algorithm 2 performs real Kubernetes scaling. It consumes observed load in S3 and the confidence-gated 9-step forecast in S4. This is the only algorithmic path through which GRU prediction affects scaling.

```pseudocode
Algorithm 2: Integrated Kubernetes Replica Scaling
────────────────────────────────────────────────────────────────
Constants:
  CONTROL_INTERVAL ← 15 seconds
  MIN_REPLICAS ← 3
  MAX_REPLICAS ← 6 (default final cap)
  SCALE_DOWN_HYSTERESIS ← 0.8
  SCALE_UP_COOLDOWN ← 30 seconds
  SCALE_DOWN_COOLDOWN ← 60 seconds

Configuration:
  mode ∈ {REACTIVE, PREDICTIVE}       // S3 / S4

repeat every CONTROL_INTERVAL:
  R_current ← K8s.deployment_replicas()
  p99 ← SLOMonitor.p99()

  if mode = REACTIVE:
    x ← HAProxy.mean_rps(window=30s)
  else:
    forecast, confidence ← GRU.latest_forecast(horizon=9)
    if confidence ≥ CONFIDENCE_THRESHOLD:
      x ← forecast.upper_capacity_signal
    else:
      x ← HAProxy.mean_rps(window=30s)

  R_raw ← α × x + β
  R_target ← clamp(ceil(R_raw), MIN_REPLICAS, MAX_REPLICAS)

  if R_target > R_current and scale_up_cooldown_passed():
    kubectl scale deployment/app --replicas=R_target
  else if R_target < R_current × SCALE_DOWN_HYSTERESIS
          and p99 < SLO_THRESHOLD × HEALTHY_MARGIN
          and scale_down_cooldown_passed():
    kubectl scale deployment/app --replicas=R_target

until shutdown
```

The same $R=\alpha x+\beta$ model and safety rules apply in both modes. Only the source of $x$ differs: observed load for S3 and GRU forecast for S4. This clean separation makes the paired comparison a test of predictive scaling rather than prediction-driven routing.

**Coordination:** serverless absorbs an observed burst while Algorithm 2 restores Kubernetes capacity. Once replicas are ready and endpoints are healthy, Algorithm 1 reduces serverless weight through `OPTIMIZE_COST`; traffic is not returned based on a GRU-derived routing weight.
