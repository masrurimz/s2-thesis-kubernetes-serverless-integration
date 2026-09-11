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
  - State: **reopened 2026-09-11, then superseded by EVID-006**
  - Scope: `results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5/`
  - Prerequisite: real 15-second ClarkNet-trained GRU artifact loaded and passing health preflight; hard prediction-delivery gate (preflight + per-eligible-cycle delivery) active in the experiment runner
  - Done when: 5 valid S3/S4 pairs complete with `treatment_fidelity.delivery_rate == 1.0` for every S4 run; `paired_analysis.json` reports inferential statistics; the bundle is promoted toward `role: final` by a human evidence decision.
  - **Resolution claimed:** Resolved by `2026-07-14-clarknet-tuned-paired-n5`. All 5 S4 runs delivered complete forecasts (predictive_count=4–5, forecast_horizon_sufficient=True). H2 supported: primary p99 p=0.0304, d=−1.2646.
  - **Correction 2026-09-11:** the stated prerequisite was not met. The model behind that bundle is `data/models/gru_model.pt`, trained on synthetic data in 18 seconds on 2026-07-13 with `prediction_horizon=9`; its scaler mean is 86.62 from synthetic training at `base_rps` 100. No 15-second ClarkNet-trained artifact existed at the time. The delivery gate part of the definition was met, the artifact part was not.
  - **Status now:** a genuine 15-second ClarkNet-trained, leak-free artifact exists as of 2026-09-11, `results/models/gru/2026-09-10_clarknet-15s-h9-leakfree` (registry `role: final`, `status: current`, GRU holdout RMSE 29.635 ± 0.016, replay window held out). The remaining work is the paired rerun against that artifact, tracked as EVID-006.

- [ ] EVID-006 — Paired S3/S4 rerun against the leak-free ClarkNet artifact
  - Priority: high
  - State: ready, blocked on infrastructure
  - Scope: `results/experiments/phase-b/<new-date>_clarknet-leakfree-paired-n5/`
  - Prerequisite: promote `results/models/gru/2026-09-10_clarknet-15s-h9-leakfree/artifacts/clarknet_gru_s44.pt` to `data/models/gru_model.pt`, then bring up the testbed. Both k3d clusters are down as of 2026-09-11 (`thesis-hybrid` 0/1 servers, `thesis-serverless` 0/1 servers, API connection refused) and HAProxy is stopped, so this needs a full `thesis infra setup` plus `thesis infra deploy-app` before the runs.
  - Done when: five counterbalanced S3/S4 pairs complete with full prediction delivery, `paired_analysis.json` reports the paired statistics, and the result is compared against the 2026-07-14 bundle to show whether the leak-free, ClarkNet-trained model changes the H2 conclusion.
  - Why it matters: the current H2 result (p = 0.030, d = −1.26, S4 winning all five pairs) rests on a model trained on synthetic data for 18 seconds and never evaluated on the trace it served. The paired rerun is what makes the headline claim rest on an artifact the thesis can defend.

- [ ] EVID-007 — Symmetric GRU/LSTM study with both cells in one invocation
  - Priority: medium
  - State: ready, deferred until the box is free (external load held it at ~30 for four hours)
  - Scope: `results/models/gru/<date>_clarknet-15s-h9-symmetric/`
  - Command: `ROCR_VISIBLE_DEVICES= HIP_VISIBLE_DEVICES= CUDA_VISIBLE_DEVICES= uv run thesis-experiment gru-hpo --data-sources clarknet --cells gru,lstm --seeds 42,43,44 --n-trials 6 --horizon 9 --output-dir <new dir> --no-promote`. A partial run already exists at `results/models/gru/2026-09-11_clarknet-15s-h9-final` (one GRU seed); resuming into that directory skips the completed selections.
  - Prerequisite: none beyond CPU. Run it on an idle machine.
  - Done when: three seeds per cell complete under the identical refit call, `paired_tests` is non-empty in `metrics.json`, and the asymmetry note in the predictor section of `FINAL_NUMBERS.md` can be deleted.
  - Why it matters: the two published arms were produced by different revisions of the refit call. Both are leak-free and the difference is disclosed, and it works against the GRU claim, but a comparison should not rest on an asymmetry the reader has to reason about. This run removes the caveat and gives the paired test committed provenance inside the bundle rather than only in `scripts/gru_predictor_analysis.py`.


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
