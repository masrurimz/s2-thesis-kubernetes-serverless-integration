# libs/shared — Foundation Package

## What This Is

Shared Pydantic models, configuration, protocols, and storage utilities. Every other package depends on this. Zero internal dependencies — never imports from `apps/` or `libs/clients/`.

## Module Map

| Module | Purpose |
|--------|---------|
| `config.py` | Pydantic BaseSettings — all service endpoints (HAProxy, GRU, Prometheus, Daemon) |
| `logging.py` | structlog configuration: `configure_logging(mode="dev"|"json"|"cli")` |
| `scenarios.py` | `Scenario` enum + `ScenarioConfig` + `SCENARIO_CONFIGS` (S1-S4) |
| `models/experiment.py` | `ExperimentResult`, `RunManifest`, `BatchManifest`, `StatisticalComparison`, `ExperimentConfig` |
| `models/prediction.py` | `PredictRequest`, `PredictResponse`, `PredictionResult`, `HealthResponse`, `ModelStatus` |
| `models/routing.py` | `StatusResponse`, `SetScenarioRequest`, `HealthResponse`, `RoutingDecision` |
| `models/metrics.py` | `MetricSample`, `MetricSeries`, `ResourceSample`, `MetricsExport` |
| `models/pipeline.py` | `PipelineContext`, `StageResult`, `PreflightResult`, `WorkloadResult` |
| `protocols/prediction.py` | `PredictionClient` Protocol |
| `protocols/routing.py` | `RoutingDaemonClient` Protocol |
| `protocols/metrics.py` | `MetricsClient` Protocol |
| `storage/csv_writer.py` | `save_csv(rows, path)` — Pydantic models → CSV |
| `storage/jsonl_writer.py` | `JSONLWriter` — append-only event stream |
| `storage/artifacts.py` | `save_yaml(model, path)` — meta.yaml configs |

## Storage Format Strategy

- **CSV** for tabular results (latency, throughput, resources) — line-per-record, git-diffable
- **JSONL** for structured event logs — append-only, one-line-per-event diffs
- **YAML** for experiment metadata (meta.yaml) — human-authored
- **Markdown** for summary reports — embeddable in thesis

## Boundaries

- **Never import from `apps/`** — this is the foundation, apps depend on it
- **Never import from `libs/clients/`** — clients depends on shared, not the other way
- Models are Pydantic v2 BaseModels for schema validation and JSON serialization
