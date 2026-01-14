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

| Thesis Component | Implementation |
|-----------------|----------------|
| p99_current | SLOMonitor.check_slo().p99_latency_ms |
| slo_threshold | SLOConfig.p99_threshold_ms (200.0) |
| window_size | SLOConfig.violation_window_sec (30) |
| weights_current | IntelligentRoutingController.current_weights |
| prediction | PredictionServer.predict() response |
| WEIGHT_STEP | Algorithm1Controller.weight_step (10) |
| COOLDOWN | Algorithm1Controller.cooldown_sec (15) |

## Integration Points

1. **SLO Monitor** → Algorithm 1 (p99 metrics)
2. **Prediction Server** → Algorithm 1 (load forecasts)
3. **Algorithm 1** → HAProxy Weight Adjuster (weight commands)
4. **Decision Logger** ← Algorithm 1 (audit trail)
