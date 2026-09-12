# libs/shared

Foundation package: Pydantic models, configuration, protocols, statistical primitives, storage writers, and the evidence catalog cache. Every other package in the workspace imports this one; it imports none of them.

## Module map

Package source lives under `libs/shared/shared/` (nested package layout).

| Path | Responsibility |
|---|---|
| `shared/config.py` | `PlatformConfig` (Pydantic BaseSettings): all service endpoints (HAProxy, GRU, Prometheus, daemon) |
| `shared/logging.py` | structlog setup: `configure_logging(mode="dev"\|"json"\|"cli")` |
| `shared/scenarios.py` | `Scenario` enum, `ScenarioConfig`, `SCENARIO_CONFIGS` (S1-S4), scenario labels/colors/order, `SLO_THRESHOLD_MS` |
| `shared/output.py` | Machine-readable CLI output: `json_line`/`print_json` (one-line JSON, plain print, never rich), `print_next` |
| `shared/progress.py` | Rich progress bars, phase spinners, countdowns for experiment CLIs; explicit `Console`, no global state |
| `shared/artifacts.py` | The one read path for run artifacts: `read_result`, `read_manifest`, `read_provision_events`, the Parquet utilization series (`read/write_resource_utilization`, `read/write_node_utilization`, `series_provenance`), `write_*` counterparts, `result_validation_error` |
| `shared/stats.py` | Statistical primitives: Welch t, Mann-Whitney U, bootstrap CI, Holm-Bonferroni, paired bootstrap CI, paired permutation test, paired Cohen's d, effect-size labels |
| `shared/models/experiment.py` | `ExperimentResult` (nested `TreatmentFidelity`), `RunManifest`, `BatchManifest`, `ExperimentConfig`, `StatisticalComparison`, `PairedComparison` |
| `shared/models/evidence.py` | Evidence DTOs: `TreatmentFidelity`, `NodeEngagement`, `ExperimentJournalEvent`, `ExperimentRegistryEntry`, `JournalEventName` |
| `shared/models/prediction.py` | `PredictRequest`, `PredictResponse` (multi-horizon), `PredictionResult`, `HealthResponse`, `ModelStatus` |
| `shared/models/routing.py` | `StatusResponse`, `SetScenarioRequest`, `HealthResponse`, `RoutingDecision` |
| `shared/models/metrics.py` | `MetricSample`, `MetricSeries`, `ResourceSample`, `NodeSample`, `MetricsExport` |
| `shared/models/pipeline.py` | `PipelineContext`, `StageResult`, `PreflightResult`, `WorkloadResult` |
| `shared/models/calibration.py` | `CalibrationConfig` + module `CALIBRATION` singleton + `get_calibration()` (resolves `CALIBRATION_OVERRIDE`) |
| `shared/models/provisioning.py` | `ProvisionEvent` (node autoscaler wire shape `{"ts","event","data"}`) |
| `shared/protocols/` | Inter-module contracts: `MetricsClient`, `PredictionClient`, `ProvisionerClient`, `RoutingDaemonClient` (exported from `__init__`) |
| `shared/storage/csv_writer.py` | `save_csv(rows, path)`: Pydantic models to CSV |
| `shared/storage/jsonl_writer.py` | `JSONLWriter`: append-only event stream, fcntl.flock-hardened |
| `shared/storage/journal.py` | `ExperimentJournal`: typed append-only lifecycle/governance journal over `JSONLWriter` |
| `shared/storage/parquet.py` | `write_table_parquet()`, `read_table_parquet()`: atomic Parquet with provenance metadata |
| `shared/storage/artifacts.py` | `save_yaml(model, path)`: meta.yaml configs |
| `shared/evidence/catalog.py` | `EvidenceCatalog`: read-only DuckDB views (registry_entries, registry_events, run_events, run_results, timeseries, artifact_index) over `results/evidence/`; lazy duckdb import |

## Module direction

- **May import:** stdlib and third-party only (pydantic, structlog, rich, duckdb lazily). No workspace package.
- **Must never import:** `apps/*`, `libs/infra`, `libs/analysis`, or any other workspace package. This is the bottom of the dependency graph; everything else depends on it.
- **Where new code goes:**
  - Rule of thumb: it belongs here when two packages need it; a helper only one package uses stays in that package.
  - A new cross-package DTO or result shape: `models/<domain>.py` (one module per domain).
  - A new inter-module client contract: `protocols/<domain>.py`, re-exported in `protocols/__init__.py`.
  - A new artifact read/write path: `shared/artifacts.py` (readers and writers live together).
  - A new persistence format or writer: `storage/<format>.py`.
  - A new statistical primitive: `stats.py`.
  - A new test: `libs/shared/tests/`.

Consumers (verified by import): `apps/analysis`, `apps/dashboard`, `apps/experiment`, `apps/prediction`, `libs/analysis`, `libs/infra`.

## Tests

`libs/shared/tests/`: architecture boundaries, artifacts round-trip, metrics parsing, stats (unpaired and paired), calibration load, journal, parquet, evidence catalog. All hermetic (tmp_path fixtures, no cluster, no network).

```bash
uv run python -m pytest libs/shared/tests -q
```

Live/opt-in tier: none.

## Commands it contributes

None: library only.

## Invariants

- Models are Pydantic v2 `BaseModel`s; the wire shape is the file shape (no aliases between disk and code).
- `artifacts.py` readers return the empty value on a missing or corrupt file, never raise: a half-copied bundle is a normal state, and absence must never read as a measured zero.
- The journal is write-once: no record is edited or deleted after append.
- `EvidenceCatalog` is a local cache, never an evidence source. `refresh()` drops and recreates views only; it never mutates canonical JSONL/YAML/JSON/CSV/Parquet. Its staging files (`_registry_entries.jsonl`, `_artifact_index.jsonl` beside the catalog) are regenerated scratch.
- The module-level `CALIBRATION` singleton is never mutated by env at import. Overrides resolve at call time via `get_calibration()` or `CalibrationConfig.load(path=...)`.
- Storage format strategy: CSV for tabular results (git-diffable), JSONL for append-only event logs, YAML for experiment metadata, Markdown for reports, Parquet for high-volume time series.
