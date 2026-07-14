# Evidence Backlog

Deferred evidence work items. Each item uses a stable `EVID-NNN` ID.

This is a work queue — not an interpretation or duplicate experiment report. Update State and Done-when as work progresses.

---

- [ ] EVID-001 — Backfill legacy v1 bundles into the typed registry
  - Priority: high
  - State: ready
  - Scope: `results/evidence/registry.yaml`, `results/evidence/registry-events.jsonl`
  - Prerequisite: none
  - Done when: `uv run thesis experiment evidence backfill-legacy --apply` registers every v1 bundle; every v1 bundle has exactly one `legacy_backfilled` registry event; `uv run thesis experiment evidence audit` lists zero unregistered bundles.

- [ ] EVID-002 — Paired-H2 prediction-actual derived Parquet
  - Priority: medium
  - State: ready
  - Scope: `results/experiments/phase-b/2026-07-11_paired-h2/derived/legacy-parquet/`
  - Prerequisite: source telemetry (Prometheus prediction vs actual) available for the paired-H2 bundle
  - Done when: `uv run thesis experiment evidence derive-parquet` produces a provenance-preserving Parquet with source SHA-256 metadata under `derived/legacy-parquet/`; the artifact is queryable through `artifact_index` in the DuckDB catalog.

- [x] EVID-003 — Clean n=5 S3/S4 paired rerun with full treatment delivery
  - Priority: high
  - State: resolved
  - Scope: `results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5/`
  - Prerequisite: real 15-second ClarkNet-trained GRU artifact loaded and passing health preflight; hard prediction-delivery gate (preflight + per-eligible-cycle delivery) active in the experiment runner
  - Done when: 5 valid S3/S4 pairs complete with `treatment_fidelity.delivery_rate == 1.0` for every S4 run; `paired_analysis.json` reports inferential statistics; the bundle is promoted toward `role: final` by a human evidence decision.
  - **Resolution:** Resolved by `2026-07-14-clarknet-tuned-paired-n5`. All 5 S4 runs delivered complete forecasts (predictive_count=4–5, forecast_horizon_sufficient=True). H2 supported: primary p99 p=0.0304, d=−1.2646.

- [ ] EVID-004 — Apply treatment-fidelity gate to DynamicExperimentRunner (Phase C)
  - Priority: medium
  - State: ready
  - Scope: `apps/experiment/experiment/dynamic.py::DynamicExperimentRunner.run_single_experiment`
  - Prerequisite: none
  - Done when: S4 dynamic experiments use the same preflight + per-cycle delivery gate as Phase B; lifecycle events written to per-run `events.jsonl`; `evaluate_run_validity()` called after collection.

- [ ] EVID-005 — Migrate new experiment runs to v2 raw/ bundle layout
  - Priority: medium
  - State: ready
  - Scope: `apps/experiment/experiment/cli.py::_run_single` run_dir builder + path consumers
  - Prerequisite: none (legacy bundles remain v1; only new runs change)
  - Done when: new runs write under `raw/<scenario>_run<N>/` with Parquet metrics; v1 adapter still reads historical bundles; `meta.yaml` sets `bundle_schema_version: 2`.
