# Running Experiments (Current Pipeline)

This runbook covers the governed `thesis-experiment` pipeline. It intentionally does not describe superseded standalone controllers or load generators.

## Prerequisites and services

Apply the final resource limits and deploy the test application before starting a run:

```bash
uv run thesis infra apply-resources
uv run thesis infra deploy-app
uv run thesis infra health
```

The experiment pipeline expects:

| Service | Port | Check |
|---|---:|---|
| Prediction server | 8090 | `curl http://localhost:8090/health` |
| Routing daemon | 9104 | `curl http://localhost:9104/health` |
| Prometheus | 9090 | `curl http://localhost:9090/-/healthy` |
| HAProxy HTTP | 18082 | `curl http://localhost:18082/fib?n=33` |
| HAProxy stats | 18404 | `curl http://localhost:18404/stats` |

The canonical workload endpoint is `/fib?n=33`. The SLO monitor reads HAProxy `rtime`; p99 must remain below 200 ms for a run to meet the primary SLO.

Start the services when running them outside the experiment manager:

```bash
uv run thesis-prediction-server --port 8090
uv run thesis-routing-daemon --port 9104
```

## Preflight

```bash
uv run thesis-experiment preflight
```

Preflight verifies cluster/application health, metrics reachability, backend readiness, and the prediction path before changing traffic. Fix a failed check rather than admitting its run to the evidence set.

## Full four-scenario evaluation

```bash
uv run thesis-experiment run --phase full --runs 5 --duration 300
```

The default scenario set is:

- `s1-k8s-only` (Kubernetes + HPA)
- `s2-serverless-only` (Knative)
- `s3-hybrid-reactive`
- `s4-hybrid-predictive`

To select a subset, pass a comma-separated list, for example:

```bash
uv run thesis-experiment run --phase full --runs 5 --duration 300 \
  --scenarios s3-hybrid-reactive,s4-hybrid-predictive
```

Each run performs reset, daemon freshness checks, warmup, k6 measurement, cooldown, collection, and validity evaluation. Do not interpret an excluded or invalid bundle as a successful replicate.

## Definitive paired H2

```bash
uv run thesis-experiment paired-run --pairs 5
```

The paired command counterbalances S3/S4 order and uses the same ClarkNet workload and V3 controller for both members of each pair. The primary endpoint is paired p99. The final evidence is S3 188.5 ms versus S4 126.0 ms, p=0.0304, d=-1.26; both scenarios have the same USD 163 proxy cost.

## Other current pipeline phases

```bash
# Dynamic S3/S4 diagnostic
uv run thesis-experiment dynamic --runs 3

# Capacity calibration
uv run thesis-experiment calibrate

# Generate trace-replay stages and k6 artifacts
uv run thesis-experiment trace-replay
```

Calibration measures the `/fib?n=33` capacity envelope against the p99 < 200 ms SLO. The final shared values are `r_saturation_per_replica=33.3` and `max_k8s_replicas=6`; see [../../CALIBRATION_GUIDE.md](../CALIBRATION_GUIDE.md).

## Evidence lifecycle

Run the read-only audit before reconciliation, then apply the merge-safe update and regenerate derived views:

```bash
uv run thesis-experiment evidence audit
uv run thesis-experiment evidence reconcile --apply
uv run thesis-experiment evidence catalog refresh
uv run thesis-experiment evidence journal
```

`audit` is read-only. `reconcile --apply` writes the typed registry. Catalog refresh rebuilds the local query cache, and journal renders the deterministic experiment journal. Evidence files under `results/` are the source of claims.

## Interpretation guardrails

- H1 is a directional n=1 diagnostic: S4 118.2 ms versus S1 2,421.3 ms; do not call it statistically established.
- H2 is the definitive paired n=5 result stated above.
- GRU training is synthetic; ClarkNet/Calgary are validation data, and ClarkNet is replayed for evaluation.
- The forecast is 135 seconds (9 × 15 seconds), drives Algorithm 2 replica scaling, and does not directly set routing weights.
- Cost values are directional proxy estimates, not cloud invoices.
