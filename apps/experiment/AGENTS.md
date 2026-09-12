# apps/experiment

Experiment orchestration: composable pipeline stages, the run-conditions gate, named profiles, series supervision, tuning studies, and the evidence sub-app. Its stages were extracted from a former 2164-line `scripts/run_phase_b_experiments.py` monolith, since deleted.

## Pipeline architecture

```
plan → preflight → reset → daemon → workload → collect → validate → analyze → report
```

Each stage implements the `Stage` protocol (`stages/base.py`) and emits lifecycle events to a per-run `events.jsonl` journal. Stages share a `PipelineContext`; the pipeline fails fast if any stage fails. Prediction readiness is not a separate stage: it is the daemon stage's `require_prediction_service()` plus the conditions gate.

## Module map

| Path | Responsibility |
|---|---|
| `experiment/pipeline.py` | `Pipeline`: threads `PipelineContext` through ordered stages, dry-run support |
| `experiment/cli.py` | Typer app with all 15 commands (list under Commands) |
| `experiment/conditions.py` | `RunConditions`, `apply()`, `ConditionsUnmet`: the one conditioning gate every entry point funnels through |
| `experiment/profiles.py` | Named experiment profiles (`get_profile`, `profile_names`): scenarios, design, static agent count, prediction-server need, controller env |
| `experiment/series.py` | Series runner (`parse_stage`, `run_series`, `summarise`): a chain of profiles as one supervised command |
| `experiment/summary.py` | `write_summary()`: per-bundle `SUMMARY.md` |
| `experiment/calibration.py` | Workload calibration: sweeps scenarios x RPS to find the Goldilocks load level |
| `experiment/dynamic.py` | Phase C dynamic ramp/burst experiment (S3 vs S4) |
| `experiment/services.py` | `ensure_prediction_server()`: converges the operator-managed prediction server to a known state |
| `experiment/validation.py` | Real-time hypothesis validation; H3 checks the trained GRU via `prediction.model_loader`, no cluster needed |
| `experiment/trace_replay.py` | Generates k6 trace-replay artifacts (stages JSON + JS) from ClarkNet parquet |
| `experiment/clients/daemon.py` | Typed HTTP client for the routing daemon, using `shared.models.routing` contracts |
| `experiment/infrastructure/node_provisioner.py` | `NodeProvisioner`: simulates cloud node provisioning via k3d cordon/uncordon |
| `experiment/stages/base.py` | `Stage` protocol + `BaseStage` |
| `experiment/stages/plan.py` | `PlanStage`: run order, seeds, batch manifest |
| `experiment/stages/preflight.py` | `PreflightStage`: infrastructure readiness checks |
| `experiment/stages/reset.py` | `ResetStage`: per-run scenario reset |
| `experiment/stages/daemon.py` | `DaemonStage`: daemon lifecycle + `require_prediction_service()` for S4 |
| `experiment/stages/workload.py` | `WorkloadStage`: k6 ClarkNet trace replay |
| `experiment/stages/collect.py` | `CollectStage`: Prometheus metrics + node/resource polling |
| `experiment/stages/validate.py` | `evaluate_run_validity()` S4 treatment-fidelity gate (`TreatmentFidelity` DTO) + node-engagement evaluation |
| `experiment/stages/analyze.py` | `AnalyzeStage`: Welch, Mann-Whitney, bootstrap CI, Cohen's d |
| `experiment/stages/report.py` | `ReportStage`: Markdown report + `generate_paired_report()` for paired H2 |
| `experiment/tuning/gru_hpo.py` | GRU hyperparameter optimization: gap-aware expanding-window temporal CV, production-aligned multi-horizon objective |
| `experiment/tuning/gru_study.py` | Leak-free GRU/LSTM horizon-9 study on ClarkNet (primary) and synthetic arms; frozen protocol |
| `experiment/tuning/gru_probe.py` | One-lever-at-a-time GRU probe against OLS autoregression; frozen measurement contract |
| `experiment/tuning/controller_hpo.py` | Controller tuning: deterministic V3 replay screening + paired live runs |
| `experiment/tuning/surrogate_hpo.py` | Gaussian-process surrogate screening of controller parameters |
| `experiment/tuning/workload_analysis.py` | Demand Complexity Index workload characterization (retraining trigger) |
| `experiment/evidence/registry.py` | `scan_bundles`, `reconcile_registry`, `legacy_backfill`: merge-safe typed registry |
| `experiment/evidence/renderer.py` | `render_experiment_journal()`: deterministic `EXPERIMENT_JOURNAL.md` |
| `experiment/evidence/catalog.py` | `EvidenceCatalogAdapter`: DuckDB query adapter + `derive_legacy_parquet()` |
| `experiment/evidence/cli_adapter.py` | Evidence Typer sub-app: audit, reconcile, query, journal, backfill-legacy, derive-parquet, catalog |
| `experiment/load_tests/` | k6 scripts in `legacy/`, `canonical/`, `calibration/` + README |

## Module direction

- **May import:** `shared`, `infra` (readiness, k3d autoscaler, Prometheus, k6), `analysis` (libs/analysis, e.g. `analysis.comparison` in `cli.py`), and `prediction` (model loader in `validation.py`, `GRUConfig`/`GRUPredictor` in tuning). Plus scipy, optuna, rich, typer.
- **Must never import:** `routing` (talk to the daemon over HTTP via `experiment/clients/daemon.py` and `shared.models.routing` contracts), `analysis_cli`, `dashboard`, `cli`.
- **Where new code goes:**
  - New pipeline stage → `experiment/stages/`, wired into the pipeline sequence where it belongs
  - New run-condition check → `experiment/conditions.py::apply`, so preflight and the runner both get it
  - New named profile → `experiment/profiles.py` (declare static agents, prediction-server need, controller env)
  - New series/profile chain concern → `experiment/series.py`
  - New bundle output format → `experiment/summary.py` or `stages/report.py`
  - New tuning study → `experiment/tuning/`
  - New evidence operation → `experiment/evidence/` with a thin handler in `evidence/cli_adapter.py`
  - New k6 script → `experiment/load_tests/` (correct era folder)
  - New test → `apps/experiment/tests/`

## Tests

`apps/experiment/tests/`; hermetic by default, live tier opt-in. 182 tests total; the 5 in `test_cpu_fairness_e2e.py` carry `pytest.mark.live`, drive the real k3d cluster and Docker, and are deselected by the repo default (`-m 'not live'` in root `pyproject.toml`). Run with:

```bash
uv run python -m pytest apps/experiment/tests -q          # hermetic (177)
uv run python -m pytest apps/experiment/tests -m live -q  # live tier (5); never while an experiment runs
```

## Commands it contributes

`thesis experiment` (15 commands, verified against `--help`): `run`, `analyze`, `preflight`, `validate`, `calibrate`, `dynamic`, `validate-realtime`, `trace-replay`, `summary`, `series`, `reproduce`, `paired-run`, `gru-hpo`, `gru-probe`, and the `evidence` sub-app. Entry point: `thesis-experiment` → `experiment.cli:app`.

`analyze` recomputes a bundle's paired verdict from its per-run `result.json` files (`--write` updates the artifacts).

## Invariants

- The conditions gate is unconditional: `_run_single` calls `experiment/conditions.py::apply` before anything else, and every entry point funnels through `_run_single`. A new command that runs experiments must go through it too.
- A profile declares its needs (scenarios, design, static agents, prediction server, controller env); `tests/test_profiles.py` fails when a hybrid profile leaves no capacity to bind or a predictive one serves no predictor.
- Result storage: tabular results as CSV, event logs as JSONL (append-only), metadata as YAML (`meta.yaml`), reports as Markdown. Bundles follow the schema in `results/AGENTS.md`.
- `tuning/gru_study.py` and `tuning/gru_probe.py` implement frozen protocols; do not redesign them.
- k6 load scripts live in `experiment/load_tests/`, not in `infrastructure/`.
