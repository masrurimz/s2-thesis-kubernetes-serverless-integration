# apps/routing

Deployable routing control plane. Runs the SLO-aware routing controller (Algorithm 1 V1/V2/V3, with V3 current) and prediction-based cluster scaling (Algorithm 2). Exposes a FastAPI API on port 9104.

## Module map

| Path | Responsibility |
|---|---|
| `routing/daemon/service.py` | `RoutingDaemon`: main decision loop, scenario management |
| `routing/daemon/app.py` | `create_app(daemon)`: FastAPI API routes |
| `routing/daemon/cli.py` | Typer CLI entry point (`daemon` command) |
| `routing/daemon/metrics.py` | Daemon-level Prometheus metric registration (`daemon_decision_total` etc.) |
| `routing/algorithm/registry.py` | Controller registry: selects the Algorithm 1 version per scenario |
| `routing/algorithm/algorithm1_v1.py` | Algorithm 1 V1 (S3 reactive): bang-bang priority cascade |
| `routing/algorithm/algorithm1_v2.py` | Algorithm 1 V2 (S4 predictive): PID + feedforward controller |
| `routing/algorithm/algorithm1_v3.py` | Algorithm 1 V3 (current): capacity-driven routing, one-sided burn-rate PI, proactive hold, `last_predicted_upper` for Algorithm 2 |
| `routing/algorithm/weight_adjuster.py` | `HAProxyWeightAdjuster`: HAProxy socket weight management |
| `routing/algorithm/fallback_handler.py` | `FallbackHandler`: tiered fallback routing |
| `routing/algorithm/decision_logger.py` | `DecisionLogger`: SQLite audit trail |
| `routing/algorithm/metrics.py` | Algorithm-level Prometheus metric definitions (`slo_violation_total` etc.) |
| `routing/monitoring/slo_monitor.py` | `SLOMonitor`: p99 latency tracking, SLO violation detection |
| `routing/scaling/cluster_controller.py` | `ClusterController` (Algorithm 2): R=αx+β replica scaling |
| `routing/clients/gru_client.py` | `GRUClient`: HTTP client for the prediction server |

## Module direction

- **May import:** `shared` (models, config, scenarios, protocols) and `infra` (`K8sScaler` in `daemon/service.py`), plus fastapi, uvicorn, prometheus-client, structlog.
- **Must never import:** `experiment`, `analysis_cli`, `dashboard`, `cli` (same or higher layer), and the `prediction` package itself. The daemon talks to the prediction service over HTTP through the `PredictionClient` protocol from `shared.protocols.prediction`; never import `prediction.*` directly.
- **Where new code goes:**
  - New controller variant → `routing/algorithm/`, registered in `algorithm/registry.py`
  - New daemon API route → `routing/daemon/app.py`
  - New daemon-level Prometheus metric → `routing/daemon/metrics.py`; algorithm-level → `routing/algorithm/metrics.py`
  - New client for an external service → `routing/clients/`
  - New test → `apps/routing/tests/`

## Tests

`apps/routing/tests/`; hermetic, no live tier. 179 tests covering controllers (V1/V2/V3), the registry, SLO monitor, cluster controller, weight adjuster, fallback handler, decision logger, metrics, prediction counters, prediction seam, and predictive shrink. k3d/kubectl/HAProxy interactions are mocked. Run with:

```bash
uv run python -m pytest apps/routing/tests -q
```

## Commands it contributes

- `thesis-routing-daemon` entry point → `routing.daemon.cli:app` (`daemon` command).
- `thesis routing daemon` registers that same app through `apps/cli`.

```bash
uv run thesis-routing-daemon --scenario s4-hybrid-predictive
uv run thesis routing daemon --scenario s4-hybrid-predictive
```

## Invariants

- `GRUClient` implements the `PredictionClient` protocol from `shared.protocols.prediction`.
- V3 is the current controller; V1/V2 are legacy. V3 routes by observed load capacity and stores `last_predicted_upper` for Algorithm 2 scaling.
- V3 burn-rate is one-sided: zero when healthy, positive-only intervention. `proactive_hold_sec` prevents premature rollback.
- S4 treatment delivery: the daemon counts `_prediction_eligible_cycles` and `_prediction_delivery_failures`; `get_status()` exposes both for the experiment validity gate.
- Routing decisions are logged to SQLite via `DecisionLogger`.
