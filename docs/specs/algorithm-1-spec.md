# Algorithm 1: SLO-Aware Routing Controller

## Thesis Reference

Per thesis section 3.4.3.1, Algorithm 1 is the core routing controller that:
1. Monitors p99 latency against SLO threshold
2. Detects sustained violations
3. Adjusts traffic weights to maintain SLO compliance
4. Optimizes for cost when healthy

## Pseudocode (from thesis)

```
Algorithm 1: SLO-Aware Routing Controller
───────────────────────────────────────────

Input:
  p99_current     : Current p99 latency (ms)
  slo_threshold   : SLO target (200ms)
  window_size     : Violation detection window (30s)
  weights_current : Current {k3s, knative} weights
  prediction      : Optional predicted load (from Algorithm 2)

Output:
  weights_new     : Adjusted traffic weights

State:
  violation_start : Timestamp of violation start (or null)
  last_adjustment : Timestamp of last weight change

Constants:
  WEIGHT_STEP     : 10  (weight adjustment step)
  COOLDOWN        : 15s (minimum time between adjustments)
  HEALTHY_MARGIN  : 0.7 (threshold multiplier for "healthy" state)

Procedure:
1. IF p99_current > slo_threshold:
     IF violation_start IS NULL:
       violation_start ← now()
     violation_duration ← now() - violation_start
   ELSE:
     violation_start ← NULL
     violation_duration ← 0

2. IF violation_duration ≥ window_size:
     # Sustained violation - scale out to serverless
     IF now() - last_adjustment ≥ COOLDOWN:
       knative_new ← min(100, knative_current + WEIGHT_STEP)
       k3s_new ← 100 - knative_new
       last_adjustment ← now()
       RETURN {k3s: k3s_new, knative: knative_new}

3. IF p99_current < slo_threshold × HEALTHY_MARGIN:
     # Healthy - optimize for cost by increasing k3s
     IF now() - last_adjustment ≥ COOLDOWN:
       k3s_new ← min(95, k3s_current + WEIGHT_STEP // 2)
       knative_new ← 100 - k3s_new
       last_adjustment ← now()
       RETURN {k3s: k3s_new, knative: knative_new}

4. # Use prediction if available (Algorithm 2 integration)
   IF prediction IS NOT NULL AND prediction.confidence > 0.7:
     load_change ← (prediction.value - current_load) / current_load
     IF load_change > 0.3:  # Significant increase predicted
       knative_new ← min(50, knative_current + WEIGHT_STEP)
       k3s_new ← 100 - knative_new
       RETURN {k3s: k3s_new, knative: knative_new}

5. RETURN weights_current  # No change
```

## Implementation Mapping

| Thesis Component | Implementation File | Class/Function |
|-----------------|---------------------|----------------|
| p99_current | `controller/monitoring_v2/slo_monitor.py` | `SLOMonitor.check_slo().p99_latency_ms` |
| slo_threshold | `controller/monitoring_v2/slo_monitor.py` | `SLOConfig.p99_threshold_ms` (200.0) |
| window_size | `controller/monitoring_v2/slo_monitor.py` | `SLOConfig.violation_window_sec` (30) |
| weights_current | `controller/intelligent_router/algorithm1_controller.py` | `Algorithm1Controller.current_weights` |
| prediction | `controller/prediction_engine/server.py` | `PredictionServer.predict()` response |
| WEIGHT_STEP | `controller/intelligent_router/algorithm1_controller.py` | `Algorithm1Config.weight_step` (10) |
| COOLDOWN | `controller/intelligent_router/algorithm1_controller.py` | `Algorithm1Config.cooldown_sec` (15) |
| HEALTHY_MARGIN | `controller/intelligent_router/algorithm1_controller.py` | `Algorithm1Config.healthy_margin` (0.7) |

## Core Implementation Files

| File | Purpose |
|------|---------|
| [`controller/intelligent_router/algorithm1_controller.py`](../../controller/intelligent_router/algorithm1_controller.py) | Main Algorithm 1 logic |
| [`controller/daemon/routing_daemon.py`](../../controller/daemon/routing_daemon.py) | Daemon that runs Algorithm 1 with scenario configs |
| [`controller/intelligent_router/weight_adjuster.py`](../../controller/intelligent_router/weight_adjuster.py) | HAProxy weight adjustment via admin socket |
| [`controller/intelligent_router/metrics.py`](../../controller/intelligent_router/metrics.py) | Prometheus metrics for H2 evaluation |
| [`controller/monitoring_v2/slo_monitor.py`](../../controller/monitoring_v2/slo_monitor.py) | SLO monitoring and violation detection |

## Integration Points

1. **SLO Monitor** → Algorithm 1 (p99 metrics)
2. **Prediction Server** → Algorithm 1 (load forecasts)
3. **Algorithm 1** → HAProxy Weight Adjuster (weight commands)
4. **Decision Logger** ← Algorithm 1 (audit trail)

## Prometheus Metrics Exposed

Metrics defined in `controller/intelligent_router/metrics.py`:

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `slo_violation_total` | Counter | `slo_name` | Total SLO violations detected |
| `routing_decision_total` | Counter | `decision_type` | Decisions by type (SCALE_OUT, OPTIMIZE_COST, PREDICTIVE, MAINTAIN) |
| `reaction_time_ms` | Histogram | - | Time from violation detection to weight adjustment |

Metrics exposed by routing daemon (`controller/daemon/routing_daemon.py`):

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `routing_daemon_decision_total` | Counter | `scenario`, `action` | Decisions by scenario and action |
| `routing_daemon_current_weight` | Gauge | `backend` | Current weight per backend (k3s, knative) |
| `routing_daemon_prediction_used` | Counter | - | GRU predictions used in decisions |
| `routing_daemon_decision_latency_ms` | Histogram | - | Decision loop latency |

## Routing Daemon Integration

The routing daemon (`controller/daemon/routing_daemon.py`) orchestrates Algorithm 1:

### Scenario Configurations

```python
SCENARIO_CONFIGS = {
    "s1-k8s-only": ScenarioConfig(k3s=100, knative=0, algorithm=False, predictions=False),
    "s2-serverless-only": ScenarioConfig(k3s=0, knative=100, algorithm=False, predictions=False),
    "s3-hybrid-reactive": ScenarioConfig(k3s=80, knative=20, algorithm=True, predictions=False),
    "s4-hybrid-predictive": ScenarioConfig(k3s=80, knative=20, algorithm=True, predictions=True),
}
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/status` | GET | Current daemon status, weights, decision counts |
| `/set_scenario` | POST | Change scenario (for H1/H2 evaluations) |
| `/health` | GET | Health check (HAProxy, GRU connectivity) |
| `/metrics` | GET | Prometheus metrics |

### Running the Daemon

```bash
cd controller
uv run python -m daemon.routing_daemon \
  --scenario s4-hybrid-predictive \
  --interval 15 \
  --prometheus-url http://localhost:9090 \
  --haproxy-host localhost \
  --haproxy-port 9999 \
  --gru-url http://localhost:8090 \
  --api-port 9104
```

## Decision Flow

```
┌─────────────────┐
│ Decision Loop   │ (every 15s)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SLOMonitor      │ → Query Prometheus for p99 latency
│ .check_slo()    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ Algorithm1Controller.make_decision()                    │
│                                                         │
│  1. Check sustained violation → SCALE_OUT              │
│  2. Check healthy state → OPTIMIZE_COST                │
│  3. Check prediction (if S4) → PREDICTIVE              │
│  4. Otherwise → MAINTAIN                               │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ WeightAdjuster  │ → Send weight command to HAProxy admin socket
│ .set_weights()  │
└─────────────────┘
```
