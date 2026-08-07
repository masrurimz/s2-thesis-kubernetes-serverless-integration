# Understanding the Final Architecture

## Why hybrid control

Kubernetes replicas are warm and economical but have a finite, calibrated capacity. Knative can absorb overflow but has a different cost and startup profile. The experiment therefore compares a K8s baseline, serverless-only baseline, reactive hybrid control, and predictive hybrid control under one deterministic workload.

## Data and control flow

```text
synthetic training series
          |
          v
   GRU: 9 x 15 s = 135 s
          |
          v
Algorithm 2: forecast-informed K8s replica target
          |
observed RPS + ready capacity + HAProxy rtime p99
          |
          v
Algorithm 1 V3: capacity-driven routing
          |
          v
      HAProxy weights
       /          \
 Kubernetes      Knative
```

The GRU is trained on synthetic workload patterns. ClarkNet and Calgary are used for validation; ClarkNet is replayed as the variable evaluation trace. The prediction path drives **scaling**, not a direct traffic-weight decision. Algorithm 1 uses observed load and observed-load trend extrapolation gated by GRU confidence.

## Algorithm 1 priority

```text
SCALE_OUT > PREDICTIVE > OPTIMIZE_COST > MAINTAIN
```

- `SCALE_OUT`: observed SLO violation or insufficient ready capacity.
- `PREDICTIVE`: observed trend approaches capacity and the confidence gate is open; Algorithm 2 can pre-scale replicas.
- `OPTIMIZE_COST`: observed healthy headroom permits gradual return toward Kubernetes.
- `MAINTAIN`: no action passes thresholds and cooldowns.

The routing SLO monitor derives p99 from HAProxy `rtime` and uses a 200 ms threshold.

## Calibration and workload

The canonical endpoint is `/fib?n=33`. The final shared capacity values are `r_saturation_per_replica=33.3`, minimum 3 replicas, and maximum 6 replicas. Node CPU limits are applied by `uv run thesis infra apply-resources` before experiments.

## Scenarios and evidence

| Scenario | Description |
|---|---|
| S1 | K8s + HPA baseline |
| S2 | Serverless-only |
| S3 | Hybrid-reactive |
| S4 | Hybrid-predictive |

The definitive H2 paired n=5 result is S3 p99 188.5 ms versus S4 126.0 ms (p=0.0304, d=-1.26), with identical USD 163 proxy cost. H1 is directional n=1: S4 118.2 ms versus S1 2,421.3 ms.

## Runtime topology

| Component | Port | Role |
|---|---:|---|
| Prediction server | 8090 | GRU inference and confidence |
| Routing daemon | 9104 | Algorithm 1 V3 loop |
| Prometheus | 9090 | Observed load and readiness metrics |
| HAProxy HTTP | 18082 | Experiment request path |
| HAProxy stats | 18404 | Proxy statistics |

Run through the governed CLI rather than ad hoc controllers:

```bash
uv run thesis-experiment preflight
uv run thesis-experiment run --phase full --runs 5 --duration 300
uv run thesis-experiment paired-run --pairs 5
```

There is no final claim of a universal scaling activation time. The measurable target is the p99 < 200 ms SLO, with the controller's scale and routing behavior reported from the evidence bundles.
