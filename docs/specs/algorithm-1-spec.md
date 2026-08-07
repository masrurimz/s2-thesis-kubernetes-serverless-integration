# Algorithm 1: V3 Capacity-Driven Routing Controller

## Purpose

Algorithm 1 is the 15-second routing loop for the hybrid Kubernetes/Knative testbed. It maintains the p99 < 200 ms SLO by shifting HAProxy weights between Kubernetes and serverless backends. It reads observed request load, observed ready replicas, observed HAProxy latency, and current weights. It does not use a GRU forecast as a direct routing-weight input.

The GRU forecast is consumed by Algorithm 2, which computes a Kubernetes replica target. Algorithm 1 may use observed-load trend extrapolation for a proactive routing decision when GRU confidence is sufficient; this post-Bug-13 behavior prevents an under-predicting forecast from directly over-routing to serverless.

## Inputs and outputs

| Input | Meaning |
|---|---|
| `current_load` | Observed requests per second from Prometheus |
| `ready_replicas` | Ready Kubernetes workload replicas |
| `current_p99` | Tail latency observed by the SLO monitor |
| `k8s_weight`, `knative_weight` | Current HAProxy percentages |
| `trend` | Observed-load trend extrapolation |
| `gru_confidence` | Confidence gate supplied by the prediction path |
| `slo_threshold_ms` | 200 ms |

The output is a graduated HAProxy weight update. Weights always sum to 100 and are changed only after cooldown, hysteresis, and backend-health checks pass.

## Decision priority

The decision flow is strictly ordered (Bug 2 fix):

```text
SCALE_OUT > PREDICTIVE > OPTIMIZE_COST > MAINTAIN
```

1. **SCALE_OUT:** sustained observed SLO violation or insufficient observed ready capacity. Increase serverless weight and let Algorithm 2 raise the Kubernetes replica target.
2. **PREDICTIVE:** the observed trend approaches the capacity boundary and the GRU confidence gate is met. Algorithm 2 has already received the forecast; Algorithm 1 can shift routing using the observed trend, not the raw forecast value.
3. **OPTIMIZE_COST:** the observed system is healthy with capacity headroom. Gradually restore Kubernetes weight.
4. **MAINTAIN:** no threshold, cooldown, or health condition requires a change.

## Pseudocode

```text
loop every 15 seconds:
    load        <- observed Prometheus request rate
    ready       <- observed ready Kubernetes replicas
    p99         <- HAProxy rtime-derived p99
    trend       <- extrapolate observed load
    capacity    <- ready * r_effective

    if sustained(p99 > 200 ms) or load > capacity:
        decision <- SCALE_OUT
        increase Knative weight by WEIGHT_STEP
        request Algorithm 2 to reconcile its observed-load replica target
    else if trend approaches capacity and gru_confidence >= confidence_threshold:
        decision <- PREDICTIVE
        allow Algorithm 2's forecast-informed replica target
        shift weights only according to observed trend and backend capacity
    else if healthy(p99 < 200 ms) and load is below capacity margin:
        decision <- OPTIMIZE_COST
        restore Kubernetes weight gradually
    else:
        decision <- MAINTAIN

    apply only after cooldown/hysteresis and verify weights sum to 100
```

The forecast value is never copied directly into a routing weight. Algorithm 2 consumes the confidence-gated forecast for replica scaling; Algorithm 1 uses observed load, observed capacity, and confidence-gated trend extrapolation.

## Weight policy

Use graduated 10-percentage-point changes, bounded by 0/100 and the configured serverless safety limit. S3 and S4 begin with the configured three warm replicas; runtime routing decisions are driven by the observed signals above.

## Algorithm 2 integration

Algorithm 2 receives the GRU upper forecast and confidence, computes a target using the effective capacity model, and reconciles Kubernetes replicas in `[3, 6]` under the default calibration (the definitive paired H2 bundle used the experiment-local override `max_k8s_replicas = 10`; see `results/calibration/2026-08-06_definitive-repro.json`). Prediction therefore drives Kubernetes scaling. Algorithm 1 consumes the resulting ready capacity and observed load when deciding distribution.

## Metrics

The routing daemon exposes counters and gauges for decision type, SLO violations, current weights, observed load, ready replicas, and reaction time. The SLO monitor uses HAProxy `rtime` (raw response time) to derive p99; application request timing is not substituted for this control signal.

## Operational entry points

```bash
uv run thesis-routing-daemon --port 9104
curl http://localhost:9104/metrics
```

The experiment CLI starts and stops the daemon as part of the governed pipeline. Prometheus is expected at `http://localhost:9090`, HAProxy HTTP at `http://localhost:18082`, and HAProxy stats at `http://localhost:18404`.
