# apps/experiment — Experiment Orchestration

## What This Is

Experiment runner using composable pipeline stages. Decomposes the former 2164-line monolith (`scripts/run_phase_b_experiments.py`) into independently testable stages.

## Pipeline Architecture

```
plan → preflight → reset → daemon → [prediction_preflight for S4] → workload → collect → validate → analyze → report

Each stage implements the `Stage` Protocol and emits lifecycle events to a per-run `events.jsonl` journal.

Stages read from and write to a shared `PipelineContext`. Pipeline fails fast if any stage fails.

## Module Map

| Module | Purpose |
|--------|---------|
| `pipeline.py` | `Pipeline` — orchestrator that threads context through stages |
| `cli.py` | Typer app: `run`, `paired-run`, `dynamic`, `preflight`, `analyze`, `evidence` sub-app |
| `stages/base.py` | `Stage` Protocol + `BaseStage` abstract class |
| `stages/plan.py` | `PlanStage` — run order, seeds, batch manifest |
| `stages/preflight.py` | `PreflightStage` — infrastructure readiness checks |
| `stages/reset.py` | `ResetStage` — per-run scenario reset |
| `stages/daemon.py` | `DaemonStage` — daemon lifecycle + `require_prediction_service()` S4 preflight |
| `stages/workload.py` | `WorkloadStage` — k6 ClarkNet trace replay |
| `stages/collect.py` | `CollectStage` — Prometheus metrics + resource polling |
| `stages/validate.py` | `evaluate_run_validity()` — S4 treatment-fidelity gate (TreatmentFidelity DTO) |
| `stages/analyze.py` | `AnalyzeStage` — Welch, Mann-Whitney, bootstrap CI, Cohen's d |
| `stages/report.py` | `ReportStage` — Markdown report + `generate_paired_report()` for paired H2 |
| `evidence/registry.py` | `scan_bundles`, `reconcile_registry`, `legacy_backfill` — merge-safe registry |
| `evidence/renderer.py` | `render_experiment_journal()` — deterministic EXPERIMENT_JOURNAL.md |
| `evidence/catalog.py` | `EvidenceCatalogAdapter` — DuckDB query + `derive_legacy_parquet()` |
| `evidence/cli_adapter.py` | Evidence Typer sub-app: audit, reconcile, query, journal, backfill-legacy, derive-parquet, catalog refresh |
| `tuning/gru_hpo.py` | GRU hyperparameter optimization with temporal CV + baseline promotion gate |
| `tuning/controller_hpo.py` | Controller tuning: deterministic replay + paired live screening |
| `infrastructure/node_provisioner.py` | `NodeProvisioner` — k3d node cordon/uncordon |
```bash
uv run thesis-experiment run --phase full --runs 5 --duration 300
uv run thesis-experiment preflight
uv run thesis-experiment run --phase calibration --runs 1 --dry-run
uv run thesis-experiment analyze --results-file results/experiments/phase-b/.../results.csv
```

## Result Storage

- Tabular results → CSV (git-friendly, line-per-record)
- Event logs → JSONL (append-only, one-line-per-event)
- Metadata → YAML (meta.yaml)
- Reports → Markdown

## Dependencies

- `shared` (models, pipeline contracts)
- `infra` (Prometheus, k6, k8s clients)
- scipy, rich, typer
