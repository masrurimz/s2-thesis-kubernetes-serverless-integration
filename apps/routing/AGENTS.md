# apps/routing — Routing Daemon + Algorithm + Scaling

## What This Is

Deployable routing control-plane. Runs the SLO-aware routing controller (Algorithm 1 V1/V2/V3) and prediction-based cluster scaling (Algorithm 2). V3 is the current controller: capacity-driven routing from observed load, with GRU-confidence-gated upper forecast for proactive Algorithm 2 scaling. S4 treatment delivery is tracked via `_prediction_eligible_cycles` and `_prediction_delivery_failures` counters. Exposes a FastAPI API on port 9104.

## Module Map

| Module | Purpose |
|--------|---------|
| `daemon/service.py` | `RoutingDaemon` — main decision loop, scenario management |
| `daemon/app.py` | `create_app(daemon) → FastAPI` — API routes |
| `daemon/cli.py` | Typer CLI entry point |
| `daemon/metrics.py` | Prometheus metric registration (daemon_decision_total, etc.) |
| `algorithm/algorithm1_v1.py` | Algorithm 1 V1 (S3 reactive) — bang-bang priority cascade |
| `algorithm/algorithm1_v2.py` | Algorithm 1 V2 (S4 predictive) — PID + feedforward controller |
| `algorithm/algorithm1_v3.py` | Algorithm 1 V3 (current) — capacity-driven routing, one-sided burn-rate PI, proactive hold, `last_predicted_upper` for Algorithm 2 |
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
- V3 is the current controller (V1/V2 are legacy). V3 routes by observed load capacity; stores `last_predicted_upper` for Algorithm 2 scaling.
- V3 burn-rate is one-sided: zero when healthy, positive-only intervention. `proactive_hold_sec` prevents premature rollback.
- S4 treatment delivery: daemon counts `_prediction_eligible_cycles` and `_prediction_delivery_failures`; `get_status()` exposes them for the experiment validity gate.
- Routing decisions logged to SQLite via `DecisionLogger`
