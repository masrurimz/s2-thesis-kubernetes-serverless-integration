# SLO Definition

## Primary SLO

The primary service-level objective is **p99 request latency < 200 ms** during each governed workload run. The threshold is evaluated over the experiment's measurement window and reported with p50, p95, p99, throughput, errors, and SLO-violation count.

| Percentile | Target | Purpose |
|---|---:|---|
| p50 | < 50 ms | Typical request experience |
| p95 | < 100 ms | High-percentile experience |
| **p99** | **< 200 ms** | **Primary control and evaluation SLO** |

Secondary indicators are HTTP error rate, availability, throughput degradation, and backend request distribution. They are reported descriptively unless a pre-registered hypothesis explicitly uses them.

## Measurement and monitor

The SLO monitor derives latency from HAProxy `rtime` (raw response time), including the backend response path seen by the traffic proxy. This is the Bug 1 fix: HAProxy rtime, rather than an obsolete stats column or a client-side approximation, is the control signal used to detect p99 violations.

Algorithm 1 samples the monitor every 15 seconds. A sustained violation enters the routing decision flow; cooldowns and hysteresis prevent oscillation. Application and k6 metrics remain useful for reporting and cross-checks, but do not replace the HAProxy rtime control signal.

## Violation handling

```text
read HAProxy rtime-derived p99
if p99 >= 200 ms for the configured violation window:
    mark an SLO violation
    Algorithm 1 evaluates SCALE_OUT first
    increase serverless capacity/weight only after health and cooldown checks
if p99 < 200 ms with capacity margin:
    Algorithm 1 may optimize cost gradually
```

Prediction is not a routing SLO signal. The GRU forecast is confidence-gated and feeds Algorithm 2's Kubernetes replica target; routing uses observed load, observed ready capacity, and observed trend extrapolation.

## Scenario reporting

Use the final four scenarios:

- **S1:** Kubernetes + HPA baseline
- **S2:** serverless-only
- **S3:** hybrid-reactive
- **S4:** hybrid-predictive

The definitive paired H2 comparison is S3 versus S4 on ClarkNet replay. Report p99 and the SLO threshold together; do not replace the p99 SLO with proposal-era availability or scaling-speed targets.
