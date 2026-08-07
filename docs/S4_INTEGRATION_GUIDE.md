# S4 Hybrid-Predictive Integration Guide

## Final S4 behavior

S4 is the hybrid-predictive scenario in the current experiment pipeline. The GRU is trained on synthetic workload patterns and emits a direct **9-step × 15-second = 135-second** forecast. The forecast is confidence-gated and feeds Algorithm 2 Kubernetes replica scaling. Algorithm 1 V3 routes with observed load, observed ready capacity, HAProxy `rtime` p99, and confidence-gated observed-load trend extrapolation; the raw forecast does not directly set HAProxy weights.

The primary SLO is p99 < 200 ms. The canonical request is `/fib?n=33` through HAProxy HTTP on port 18082.

```text
synthetic GRU forecast + confidence
                 |
                 v
Algorithm 2: Kubernetes replica target [3, 6]
                 |
observed load + ready capacity + rtime p99
                 |
                 v
Algorithm 1 V3 -> graduated HAProxy weights -> K8s / Knative
```

## Services

Start the current services with the installed entry points:

```bash
uv run thesis-prediction-server --port 8090
uv run thesis-routing-daemon --port 9104
```

Verify health and metrics:

```bash
curl http://localhost:8090/health
curl http://localhost:9104/metrics
curl http://localhost:18082/fib?n=33
curl http://localhost:9090/-/healthy
curl http://localhost:18404/stats
```

The prediction service exposes health and prediction endpoints according to its running API. The experiment manager owns daemon startup and teardown during governed runs, so manual startup is mainly for service diagnostics.

## Infrastructure and S4 run

```bash
uv run thesis infra apply-resources
uv run thesis infra deploy-app
uv run thesis infra health
uv run thesis-experiment preflight
uv run thesis-experiment run --phase full --runs 5 --duration 300 \
  --scenarios s4-hybrid-predictive
```

For the definitive comparison, use the counterbalanced paired command:

```bash
uv run thesis-experiment paired-run --pairs 5
```

S3 and S4 use the same ClarkNet replay and calibration; only the predictive control treatment differs. S4 is admitted to the definitive result only when predictions are delivered and the forecast horizon is sufficient.

## What to inspect

- Prediction delivery, confidence, and forecast horizon in the S4 run bundle.
- Algorithm 2 target replicas and proactive scale decisions.
- Algorithm 1 observed-load decisions and HAProxy weight transitions.
- HAProxy `rtime`-derived p99 and SLO violations.
- Backend request distribution and directional proxy cost.

The definitive H2 result is S3 mean p99 188.5 ms versus S4 126.0 ms (p=0.0304, d=-1.26), with identical USD 163 proxy cost. H1 remains a directional n=1 diagnostic: S4 118.2 ms versus S1 2,421.3 ms.

## Troubleshooting

```bash
# Service reachability
curl http://localhost:8090/health
curl http://localhost:9104/metrics

# Infrastructure readiness
uv run thesis infra health
uv run thesis-experiment preflight

# Evidence lifecycle
uv run thesis-experiment evidence audit
uv run thesis-experiment evidence reconcile --apply
uv run thesis-experiment evidence catalog refresh
uv run thesis-experiment evidence journal
```

Do not substitute a deleted standalone controller or a proposal-era fixed weight for the current CLI-managed V3 pipeline.
