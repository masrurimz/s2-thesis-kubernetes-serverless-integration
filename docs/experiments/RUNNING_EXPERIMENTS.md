# Running Experiments (Current Layout)

This is the current command and file map for the thesis experiment pipeline. Results and evidence remain under `results/`; this document does not duplicate raw or derived artifacts.

## Source layout

```text
apps/experiment/experiment/
  cli.py                 # thesis-experiment commands
  calibration.py         # capacity sweep and analysis
  dynamic.py             # dynamic S3/S4 workload
  trace_replay.py        # ClarkNet/Calgary replay generation
  evidence/              # registry, catalog, journal adapters
  stages/                # preflight, reset, workload, collect, validate, report
libs/infra/              # cluster, app, node, and health lifecycle
libs/shared/             # calibration and experiment models
```

The GRU training entry point is `python -m prediction.training.train_gru`. The running inference service is `thesis-prediction-server`, and the routing service is `thesis-routing-daemon`.

## Infrastructure and service checks

```bash
uv run thesis infra apply-resources
uv run thesis infra deploy-app
uv run thesis infra health

uv run thesis-prediction-server --port 8090
uv run thesis-routing-daemon --port 9104
```

Runtime ports:

| Service | Port |
|---|---:|
| Prediction server | 8090 |
| Routing daemon | 9104 |
| Prometheus | 9090 |
| HAProxy HTTP | 18082 |
| HAProxy stats | 18404 |

The workload request is `http://localhost:18082/fib?n=33`. The SLO monitor derives p99 from HAProxy `rtime`; the primary target is p99 < 200 ms.

## Canonical CLI commands

```bash
# Readiness
uv run thesis-experiment preflight

# Full S1-S4 evaluation
uv run thesis-experiment run --phase full --runs 5 --duration 300
# Optional subset
uv run thesis-experiment run --phase full --runs 5 --duration 300 \
  --scenarios s3-hybrid-reactive,s4-hybrid-predictive

# Definitive counterbalanced H2
uv run thesis-experiment paired-run --pairs 5

# Additional diagnostics and calibration
uv run thesis-experiment dynamic --runs 3
uv run thesis-experiment calibrate
uv run thesis-experiment trace-replay

# Evidence governance
uv run thesis-experiment evidence audit
uv run thesis-experiment evidence reconcile --apply
uv run thesis-experiment evidence catalog refresh
uv run thesis-experiment evidence journal
```

The evidence commands are ordered deliberately: `audit` is read-only; `reconcile --apply` updates the typed registry; catalog refresh rebuilds the query cache; journal renders the lifecycle view.

## Scenario contract

| ID | Scenario | Expected control |
|---|---|---|
| S1 | K8s + HPA | Kubernetes baseline |
| S2 | Serverless-only | Knative only |
| S3 | Hybrid-reactive | Algorithm 1 on observed load |
| S4 | Hybrid-predictive | Algorithm 2 consumes GRU forecast; Algorithm 1 still routes on observed load/trend |

The GRU is trained on synthetic patterns, validated on ClarkNet and Calgary, and ClarkNet is replayed for evaluation. The direct forecast horizon is 9 × 15 s = 135 s.

## Final result references

- H2 definitive paired n=5: S3 mean p99 188.5 ms vs S4 126.0 ms, p=0.0304, d=-1.26; proxy cost USD 163 for each.
- H1 directional n=1: S4 p99 118.2 ms vs S1 2,421.3 ms.
- Calibration: `r_saturation_per_replica=33.3`, `max_k8s_replicas=6`, deterministic `/fib?n=33` endpoint.

These are evidence-aligned summaries, not new measurements. H1 is directional and the cost model is a proxy.

## Troubleshooting by pipeline stage

1. If preflight fails, use `uv run thesis infra health` and correct the infrastructure before running workloads.
2. If the prediction health check fails for S4, start `thesis-prediction-server` on 8090 and verify the model artifact expected by the service.
3. If routing metrics are absent, verify `thesis-routing-daemon` on 9104 and Prometheus on 9090.
4. If p99 is missing, inspect HAProxy stats on 18404 and confirm the rtime-derived monitor stream.
5. If a bundle is invalid, keep it recorded as invalid and use the evidence audit/reconcile flow; do not hand-edit result data.
