# apps/routing — Routing Daemon + Algorithm + Scaling

## What This Is

Deployable routing control-plane. Runs the SLO-aware routing controller (Algorithm 1 V1/V2) and prediction-based cluster scaling (Algorithm 2). Exposes a FastAPI API on port 9104.

## Module Map

| Module | Purpose |
|--------|---------|
| `daemon/service.py` | `RoutingDaemon` — main decision loop, scenario management |
| `daemon/app.py` | `create_app(daemon) → FastAPI` — API routes |
| `daemon/cli.py` | Typer CLI entry point |
| `daemon/metrics.py` | Prometheus metric registration (daemon_decision_total, etc.) |
| `algorithm/algorithm1_v1.py` | Algorithm 1 V1 (S3 reactive) — bang-bang priority cascade |
| `algorithm/algorithm1_v2.py` | Algorithm 1 V2 (S4 predictive) — PID + feedforward controller |
| `algorithm/weight_adjuster.py` | `HAProxyWeightAdjuster` — HAProxy socket weight management |
| `algorithm/fallback_handler.py` | `FallbackHandler` — tiered fallback routing |
| `algorithm/decision_logger.py` | `DecisionLogger` — SQLite audit trail |
| `algorithm/metrics.py` | Prometheus metric definitions (slo_violation_total, etc.) |
| `monitoring/slo_monitor.py` | `SLOMonitor` — p99 latency tracking, SLO violation detection |
| `scaling/cluster_controller.py` | `ClusterController` (Algorithm 2) — R=αx+β replica scaling |
| `clients/gru_client.py` | `GRUClient` — HTTP client for prediction server |

## Commands

```bash
uv run thesis-routing-daemon --scenario s4-hybrid-predictive
uv run thesis routing daemon --scenario s4-hybrid-predictive
```

## Dependencies

- `shared` (models, config, scenarios, protocols)
- `infra` (HAProxy, k8s clients)
- FastAPI, uvicorn, prometheus-client

## Boundaries

- `GRUClient` implements `PredictionClient` Protocol from `shared.protocols.prediction`
- Algorithm 1 V1 is for S3 (reactive), V2 is for S4 (predictive with PID)
- Routing decisions logged to SQLite via `DecisionLogger`
