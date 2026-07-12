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

- [ ] EVID-003 — Clean n=5 S3/S4 paired rerun with full treatment delivery
  - Priority: high
  - State: blocked
  - Scope: `results/experiments/phase-b/<new-date>_paired-h2-clean/`
  - Prerequisite: real 15-second ClarkNet-trained GRU artifact loaded and passing health preflight; hard prediction-delivery gate (preflight + per-eligible-cycle delivery) active in the experiment runner
  - Done when: 5 valid S3/S4 pairs complete with `treatment_fidelity.delivery_rate == 1.0` for every S4 run; `paired_analysis.json` reports inferential statistics; the bundle is promoted toward `role: final` by a human evidence decision.
