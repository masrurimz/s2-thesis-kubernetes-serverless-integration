# libs/shared — Foundation Package

## What This Is

Shared Pydantic models, configuration, protocols, and storage utilities. Every other package depends on this. Zero internal dependencies — never imports from `apps/` or `libs/clients/`.

## Module Map

| Module | Purpose |
|--------|---------|
| `config.py` | Pydantic BaseSettings — all service endpoints (HAProxy, GRU, Prometheus, Daemon) |
| `logging.py` | structlog configuration: `configure_logging(mode="dev"|"json"|"cli")` |
| `scenarios.py` | `Scenario` enum + `ScenarioConfig` + `SCENARIO_CONFIGS` (S1-S4) |
| `models/experiment.py` | `ExperimentResult` (with nested `TreatmentFidelity`), `RunManifest`, `BatchManifest`, `StatisticalComparison`, `PairedComparison`, `ExperimentConfig` |
| `models/evidence.py` | Evidence DTOs: `TreatmentFidelity`, `ExperimentJournalEvent`, `ExperimentRegistryEntry`, `JournalEventName` literal |
| `models/prediction.py` | `PredictRequest`, `PredictResponse` (multi-horizon), `PredictionResult`, `HealthResponse`, `ModelStatus` |
| `models/routing.py` | `StatusResponse`, `SetScenarioRequest`, `HealthResponse`, `RoutingDecision` |
| `models/metrics.py` | `MetricSample`, `MetricSeries`, `ResourceSample`, `MetricsExport` |
| `models/pipeline.py` | `PipelineContext`, `StageResult`, `PreflightResult`, `WorkloadResult` |
| `models/calibration.py` | `CalibrationConfig` — single source of truth for tuning params |
| `stats.py` | Welch t-test, Mann-Whitney U, bootstrap CI, Holm-Bonferroni, paired bootstrap CI, paired permutation test, paired Cohen's d |
| `protocols/prediction.py` | `PredictionClient` Protocol |
| `protocols/routing.py` | `RoutingDaemonClient` Protocol |
| `protocols/metrics.py` | `MetricsClient` Protocol |
| `storage/csv_writer.py` | `save_csv(rows, path)` — Pydantic models → CSV |
| `storage/jsonl_writer.py` | `JSONLWriter` — append-only event stream (fcntl.flock-hardened) |
| `storage/journal.py` | `ExperimentJournal` — typed append-only lifecycle/governance journal over JSONLWriter |
| `storage/parquet.py` | `write_table_parquet()`, `read_table_parquet()` — atomic Parquet with provenance metadata |
| `storage/artifacts.py` | `save_yaml(model, path)` — meta.yaml configs |
| `evidence/catalog.py` | `EvidenceCatalog` — DuckDB query catalog (registry_entries, run_events, run_results, timeseries, artifact_index views) |

## Storage Format Strategy

- **CSV** for tabular results (latency, throughput, resources) — line-per-record, git-diffable
- **JSONL** for structured event logs — append-only, one-line-per-event diffs
- **YAML** for experiment metadata (meta.yaml) — human-authored
- **Markdown** for summary reports — embeddable in thesis

## Boundaries

- **Never import from `apps/`** — this is the foundation, apps depend on it
- **Never import from `libs/clients/`** — clients depends on shared, not the other way
- Models are Pydantic v2 BaseModels for schema validation and JSON serialization
