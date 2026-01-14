# Appendix B: Algorithm Pseudocode

This appendix presents the formal pseudocode for the algorithms implemented in this research. Each algorithm includes detailed comments, complexity analysis, and implementation notes.

---

## B.1 Algorithm 1: SLO-Aware Routing Controller

Algorithm 1 implements the core routing logic that adjusts traffic distribution between Kubernetes and serverless backends based on real-time SLO monitoring and optional workload predictions.

### B.1.1 Formal Specification

```
Algorithm 1: SLO-Aware Routing Controller
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INPUT:
  p99_current      : float    // Current p99 latency in milliseconds
  slo_threshold    : float    // SLO target (default: 200.0 ms)
  weights_current  : {k3s: int, knative: int}  // Current traffic weights (sum = 100)
  prediction       : Optional[Prediction]       // From Algorithm 2 (may be null)
  current_load     : float    // Current requests per second

OUTPUT:
  weights_new      : {k3s: int, knative: int}   // Updated traffic weights

STATE (persistent across invocations):
  violation_start  : Timestamp | null  // When SLO violation began
  last_adjustment  : Timestamp         // Last weight modification time

CONSTANTS:
  WEIGHT_STEP      : 10       // Weight adjustment increment (percentage points)
  COOLDOWN_SEC     : 15       // Minimum seconds between adjustments
  VIOLATION_WINDOW : 30       // Seconds of sustained violation before action
  HEALTHY_MARGIN   : 0.7      // Multiplier for "healthy" threshold
  MIN_K3S_WEIGHT   : 5        // Minimum K8s weight (always maintain baseline)
  MAX_K3S_WEIGHT   : 95       // Maximum K8s weight (keep serverless warm)
  PREDICTION_CONF  : 0.7      // Minimum prediction confidence for proactive action
  LOAD_CHANGE_THRESH: 0.3     // Predicted load increase threshold for preemption

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROCEDURE RouteTraffic():

01:   // ═══════════════════════════════════════════════════════════════════
02:   // PHASE 1: SLO Violation Detection
03:   // Track whether p99 latency exceeds threshold and for how long
04:   // ═══════════════════════════════════════════════════════════════════
05:   
06:   IF p99_current > slo_threshold THEN
07:       // Violation detected - start or continue tracking
08:       IF violation_start IS NULL THEN
09:           violation_start ← NOW()
10:           LOG("SLO violation started", p99=p99_current, threshold=slo_threshold)
11:       END IF
12:       violation_duration ← NOW() - violation_start
13:   ELSE
14:       // No violation - reset tracking
15:       IF violation_start IS NOT NULL THEN
16:           LOG("SLO violation ended", duration=NOW() - violation_start)
17:       END IF
18:       violation_start ← NULL
19:       violation_duration ← 0
20:   END IF

21:   // ═══════════════════════════════════════════════════════════════════
22:   // PHASE 2: Sustained Violation Response
23:   // If violation persists beyond window, shift traffic to serverless
24:   // ═══════════════════════════════════════════════════════════════════
25:   
26:   IF violation_duration ≥ VIOLATION_WINDOW THEN
27:       IF NOW() - last_adjustment ≥ COOLDOWN_SEC THEN
28:           // Scale out to serverless to reduce K8s load
29:           knative_new ← MIN(100 - MIN_K3S_WEIGHT, 
30:                             weights_current.knative + WEIGHT_STEP)
31:           k3s_new ← 100 - knative_new
32:           last_adjustment ← NOW()
33:           LOG("Scaling to serverless", reason="sustained_violation",
34:               old_weights=weights_current, new_weights={k3s_new, knative_new})
35:           RETURN {k3s: k3s_new, knative: knative_new}
36:       END IF
37:   END IF

38:   // ═══════════════════════════════════════════════════════════════════
39:   // PHASE 3: Healthy State Optimization
40:   // When well below SLO, optimize for cost by increasing K8s usage
41:   // ═══════════════════════════════════════════════════════════════════
42:   
43:   healthy_threshold ← slo_threshold × HEALTHY_MARGIN
44:   
45:   IF p99_current < healthy_threshold THEN
46:       IF NOW() - last_adjustment ≥ COOLDOWN_SEC THEN
47:           IF weights_current.knative > (100 - MAX_K3S_WEIGHT) THEN
48:               // Shift traffic back to K8s (more cost-effective)
49:               k3s_new ← MIN(MAX_K3S_WEIGHT, 
50:                             weights_current.k3s + (WEIGHT_STEP / 2))
51:               knative_new ← 100 - k3s_new
52:               last_adjustment ← NOW()
53:               LOG("Optimizing for cost", reason="healthy_state",
54:                   old_weights=weights_current, new_weights={k3s_new, knative_new})
55:               RETURN {k3s: k3s_new, knative: knative_new}
56:           END IF
57:       END IF
58:   END IF

59:   // ═══════════════════════════════════════════════════════════════════
60:   // PHASE 4: Proactive Adjustment (Prediction-Based)
61:   // If significant load increase predicted, preemptively scale
62:   // ═══════════════════════════════════════════════════════════════════
63:   
64:   IF prediction IS NOT NULL THEN
65:       IF prediction.confidence ≥ PREDICTION_CONF THEN
66:           predicted_load ← prediction.value
67:           load_change ← (predicted_load - current_load) / current_load
68:           
69:           IF load_change > LOAD_CHANGE_THRESH THEN
70:               // Significant increase predicted - preemptively scale
71:               IF NOW() - last_adjustment ≥ COOLDOWN_SEC THEN
72:                   knative_new ← MIN(50, weights_current.knative + WEIGHT_STEP)
73:                   k3s_new ← 100 - knative_new
74:                   last_adjustment ← NOW()
75:                   LOG("Proactive scaling", reason="prediction",
76:                       predicted_change=load_change, confidence=prediction.confidence)
77:                   RETURN {k3s: k3s_new, knative: knative_new}
78:               END IF
79:           END IF
80:       END IF
81:   END IF

82:   // ═══════════════════════════════════════════════════════════════════
83:   // PHASE 5: No Action Required
84:   // Current configuration is acceptable
85:   // ═══════════════════════════════════════════════════════════════════
86:   
87:   RETURN weights_current

END PROCEDURE
```

### B.1.2 Complexity Analysis

| Aspect | Complexity | Notes |
|--------|------------|-------|
| Time | O(1) | All operations are constant-time comparisons |
| Space | O(1) | Fixed state variables regardless of traffic volume |
| Invocation Frequency | Every 1 second | Configurable via controller loop |

### B.1.3 Implementation Mapping

| Pseudocode Element | Python Implementation |
|--------------------|----------------------|
| `p99_current` | `SLOMonitor.check_slo().p99_latency_ms` |
| `slo_threshold` | `SLOConfig.p99_threshold_ms` |
| `weights_current` | `IntelligentRoutingController.current_weights` |
| `prediction` | `PredictionServer.predict()` response |
| `LOG()` | `structlog.get_logger().info()` |

---

## B.2 Algorithm 2: GRU Workload Predictor

Algorithm 2 implements the Gated Recurrent Unit neural network for time-series workload prediction.

### B.2.1 Architecture Specification

```
Algorithm 2: GRU Workload Predictor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ARCHITECTURE:
  Input Shape      : (batch_size, sequence_length, features)
                   : (32, 60, 1)  // 60 seconds of RPS data
  
  Layer 1: GRU
    - Units        : 64
    - Activation   : tanh (hidden), sigmoid (gates)
    - Dropout      : 0.2
    - Return Seq.  : True (for stacking)
  
  Layer 2: GRU
    - Units        : 32
    - Activation   : tanh (hidden), sigmoid (gates)
    - Dropout      : 0.2
    - Return Seq.  : False (final hidden state only)
  
  Layer 3: Dense
    - Units        : prediction_horizon (30)
    - Activation   : linear
  
  Output Shape     : (batch_size, prediction_horizon)
                   : (32, 30)  // 30-second forecast

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TRAINING CONFIGURATION:
  Optimizer        : Adam
    - Learning Rate: 0.001
    - Beta1        : 0.9
    - Beta2        : 0.999
  
  Loss Function    : Mean Squared Error (MSE)
  
  Batch Size       : 32
  Epochs           : 100 (with early stopping)
  
  Early Stopping:
    - Monitor      : validation_loss
    - Patience     : 10 epochs
    - Min Delta    : 0.0001
  
  Data Split:
    - Training     : 70%
    - Validation   : 15%
    - Test         : 15%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PREPROCESSING:
  1. Parse HTTP trace logs (CLF format)
  2. Aggregate to requests-per-second (RPS)
  3. Apply Min-Max normalization: x_norm = (x - x_min) / (x_max - x_min)
  4. Create sliding windows: (input[t:t+60], target[t+60:t+90])
  5. Shuffle and batch
```

### B.2.2 GRU Cell Equations

The GRU cell implements the following operations:

```
GRU Cell Update Equations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For each timestep t:

  Update Gate:
    z_t = σ(W_z · [h_{t-1}, x_t] + b_z)

  Reset Gate:
    r_t = σ(W_r · [h_{t-1}, x_t] + b_r)

  Candidate Hidden State:
    h̃_t = tanh(W_h · [r_t ⊙ h_{t-1}, x_t] + b_h)

  Final Hidden State:
    h_t = (1 - z_t) ⊙ h_{t-1} + z_t ⊙ h̃_t

Where:
  σ     : Sigmoid activation function
  tanh  : Hyperbolic tangent activation
  ⊙     : Element-wise multiplication (Hadamard product)
  [·,·] : Concatenation
  W_*   : Weight matrices
  b_*   : Bias vectors
```

### B.2.3 Inference Procedure

```
PROCEDURE Predict(history: float[60]):

01:   // Normalize input using training statistics
02:   normalized ← (history - train_min) / (train_max - train_min)
03:   
04:   // Reshape for model input: (1, 60, 1)
05:   input_tensor ← RESHAPE(normalized, [1, 60, 1])
06:   
07:   // Forward pass through GRU layers
08:   WITH torch.no_grad():
09:       output ← model(input_tensor)
10:   
11:   // Denormalize predictions
12:   predictions ← output × (train_max - train_min) + train_min
13:   
14:   // Calculate confidence based on recent prediction accuracy
15:   confidence ← 1.0 - (recent_mae / mean_traffic)
16:   
17:   RETURN Prediction(
18:       values: predictions[0],      // 30-element array
19:       confidence: confidence,
20:       timestamp: NOW()
21:   )

END PROCEDURE
```

### B.2.4 Complexity Analysis

| Aspect | Complexity | Notes |
|--------|------------|-------|
| Training Time | O(E × N × S × H²) | E=epochs, N=samples, S=sequence, H=hidden |
| Inference Time | O(S × H²) | Single forward pass |
| Space (Model) | O(H² × L) | H=hidden size, L=layers |
| Space (Inference) | O(S × H) | Hidden states per sequence |

---

## B.3 Resource Allocation Model

The resource allocation model maps predicted traffic to required CPU resources, based on the ElaX algorithm modification.

### B.3.1 Linear Resource Model

```
Resource Allocation Formula (ElaX Modification)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  R = α · x + β

Where:
  R : Required CPU resources (millicores)
  x : Traffic volume (requests per second)
  α : Slope coefficient (millicores per request)
  β : Base resource overhead (millicores)

Coefficient Derivation (OLS):
  Given historical data points: {(x_i, R_i)}
  
  α = Σ(x_i - x̄)(R_i - R̄) / Σ(x_i - x̄)²
  β = R̄ - α · x̄

Online Coefficient Update:
  α_new = α_old + η · error · x
  β_new = β_old + η · error

  Where:
    η     : Learning rate (0.01)
    error : R_actual - R_predicted
```

### B.3.2 Implementation

```python
from sklearn.linear_model import LinearRegression

class ResourceAllocator:
    def __init__(self):
        self.model = LinearRegression()
        self.alpha = None
        self.beta = None
    
    def fit(self, traffic_history, resource_history):
        """Fit OLS model to historical data."""
        X = traffic_history.reshape(-1, 1)
        y = resource_history
        self.model.fit(X, y)
        self.alpha = self.model.coef_[0]
        self.beta = self.model.intercept_
    
    def predict(self, traffic):
        """Predict required resources for given traffic."""
        return self.alpha * traffic + self.beta
    
    def update_online(self, traffic, actual_resource, learning_rate=0.01):
        """Online coefficient correction based on prediction error."""
        predicted = self.predict(traffic)
        error = actual_resource - predicted
        self.alpha += learning_rate * error * traffic
        self.beta += learning_rate * error
```

---

## B.4 Integration: Combined Control Loop

The following diagram illustrates how Algorithms 1 and 2 integrate in the production control loop:

```
Combined Control Loop Architecture
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                    ┌─────────────────────────────────────┐
                    │         OFFLINE TRAINING            │
                    │  ┌─────────────┐  ┌──────────────┐  │
                    │  │ HTTP Trace  │──│ GRU Training │  │
                    │  │  Datasets   │  │  Pipeline    │  │
                    │  └─────────────┘  └──────┬───────┘  │
                    └──────────────────────────┼──────────┘
                                               │
                                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          ONLINE CONTROL LOOP                              │
│                                                                          │
│  ┌─────────────────┐                                                     │
│  │  Prometheus     │◄───────────────────────────────────────────────┐    │
│  │  Metrics        │                                                │    │
│  └────────┬────────┘                                                │    │
│           │                                                         │    │
│           ▼                                                         │    │
│  ┌─────────────────┐      ┌─────────────────┐                      │    │
│  │  SLO Monitor    │      │  Algorithm 2:   │                      │    │
│  │  (p99 check)    │      │  GRU Predictor  │                      │    │
│  └────────┬────────┘      └────────┬────────┘                      │    │
│           │                        │                                │    │
│           │    p99_current         │    prediction                  │    │
│           │                        │                                │    │
│           └───────────┬────────────┘                                │    │
│                       │                                              │    │
│                       ▼                                              │    │
│           ┌─────────────────────┐                                   │    │
│           │    Algorithm 1:     │                                   │    │
│           │  Routing Controller │                                   │    │
│           └──────────┬──────────┘                                   │    │
│                      │                                               │    │
│                      │    weights_new                                │    │
│                      ▼                                               │    │
│           ┌─────────────────────┐                                   │    │
│           │  HAProxy Runtime    │                                   │    │
│           │  Weight Adjuster    │                                   │    │
│           └──────────┬──────────┘                                   │    │
│                      │                                               │    │
│         ┌────────────┴────────────┐                                 │    │
│         │                         │                                  │    │
│         ▼                         ▼                                  │    │
│  ┌─────────────┐          ┌─────────────┐                           │    │
│  │ Kubernetes  │          │  Knative    │                           │    │
│  │  (K3s)      │          │ Serverless  │───────────────────────────┘    │
│  └─────────────┘          └─────────────┘                                │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

Control Loop Timing:
  - Metrics collection : Every 1 second
  - SLO evaluation     : Every 1 second
  - GRU prediction     : Every 30 seconds
  - Weight adjustment  : Minimum 15 seconds apart (cooldown)
```

### B.4.1 Control Loop Pseudocode

```
PROCEDURE MainControlLoop():

01:   // Initialize components
02:   slo_monitor ← SLOMonitor(threshold=200.0)
03:   gru_predictor ← GRUPredictor(model_path="models/gru.pt")
04:   router ← RoutingController(initial_weights={k3s: 80, knative: 20})
05:   haproxy ← HAProxyClient(socket="/var/run/haproxy.sock")
06:   
07:   prediction_interval ← 30  // seconds
08:   last_prediction_time ← 0
09:   current_prediction ← NULL

10:   // Main loop
11:   WHILE True DO
12:       // Collect current metrics
13:       metrics ← prometheus.query_instant([
14:           "histogram_quantile(0.99, http_request_duration_seconds_bucket)",
15:           "sum(rate(http_requests_total[30s]))"
16:       ])
17:       
18:       p99_current ← metrics.p99_latency × 1000  // Convert to ms
19:       current_load ← metrics.request_rate

20:       // Update prediction periodically
21:       IF NOW() - last_prediction_time ≥ prediction_interval THEN
22:           history ← prometheus.query_range("http_requests_total", last_60s)
23:           current_prediction ← gru_predictor.predict(history)
24:           last_prediction_time ← NOW()
25:       END IF

26:       // Execute Algorithm 1
27:       new_weights ← router.RouteTraffic(
28:           p99_current,
29:           current_prediction,
30:           current_load
31:       )

32:       // Apply weight changes if different
33:       IF new_weights ≠ router.current_weights THEN
34:           haproxy.set_weights(new_weights)
35:           router.current_weights ← new_weights
36:           log_decision(new_weights, p99_current, current_prediction)
37:       END IF

38:       // Sleep until next iteration
39:       SLEEP(1)  // 1-second control loop
40:   END WHILE

END PROCEDURE
```

---

## B.5 Implementation Notes

### B.5.1 Python Module Structure

```
controller/
├── src/
│   └── intelligent_router/
│       ├── algorithm1/
│       │   ├── routing_controller.py    # Algorithm 1 implementation
│       │   ├── slo_monitor.py           # SLO metrics collection
│       │   └── weight_adjuster.py       # HAProxy integration
│       ├── algorithm2/
│       │   ├── gru_model.py             # GRU architecture (PyTorch)
│       │   ├── predictor.py             # Inference wrapper
│       │   └── data_processor.py        # Preprocessing pipeline
│       └── integration/
│           ├── control_loop.py          # Main control loop
│           └── prometheus_client.py     # Metrics queries
```

### B.5.2 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| 15-second cooldown | Prevents oscillation; allows HAProxy to stabilize |
| 30-second prediction interval | Balances responsiveness with compute cost |
| 70% healthy margin | Conservative threshold avoids premature cost optimization |
| 30% load change threshold | Filters noise; triggers only for significant changes |
| Min 5% serverless weight | Keeps serverless instances warm, reduces cold starts |

### B.5.3 Error Handling

```python
class RoutingController:
    def route_traffic(self, p99_current, prediction, current_load):
        try:
            # Main routing logic (Algorithm 1)
            return self._execute_routing(p99_current, prediction, current_load)
        except PrometheusConnectionError:
            logger.warning("Prometheus unavailable, using last known state")
            return self.current_weights
        except PredictionError:
            logger.warning("Prediction failed, falling back to reactive mode")
            return self._execute_routing(p99_current, None, current_load)
        except HAProxyError as e:
            logger.error("HAProxy update failed", error=str(e))
            raise  # Critical error - alert operator
```

---

## B.6 Validation Checklist

Before deploying the algorithms, verify:

- [ ] GRU model achieves RMSE < 10% on test set
- [ ] Algorithm 1 responds within 100ms per invocation
- [ ] HAProxy weight changes apply within 1 second
- [ ] Prometheus queries return within 500ms
- [ ] Cooldown prevents more than 4 adjustments per minute
- [ ] Logs capture all routing decisions with timestamps
- [ ] Graceful degradation works when prediction unavailable
