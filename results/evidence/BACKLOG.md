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
- [x] EVID-006a — n=1 paired S3/S4 run against the leak-free artifact (2026-09-11)
  - Bundle: `results/experiments/phase-b/2026-09-11_clarknet-leakfree-paired-n1`
  - Valid: both arms zero request failures, S4 delivered 55 of 55 eligible forecasts, both arms passed the run-validity gate.
  - Result at n=1: reactive p99 120.4 ms and 117 SLO violations against predictive 152.6 ms and 254, with three scale-ups against six and higher k8s replica-seconds. The predictor delivered every forecast but only one cycle was actionable, so the proactive arm scaled up less and carried the same load on fewer replicas.
  - Two attempts were rejected first and are kept beside it as `-invalid` (HAProxy exited mid-run, so the load history never filled the model's input window) and `-aborted` (the prediction server hung on the integrated GPU and failed every eligible cycle). Both failures were caught by the gates the bundle records, not by inspection.

  - **Status now:** a genuine 15-second ClarkNet-trained, leak-free artifact exists as of 2026-09-11, `results/models/gru/2026-09-10_clarknet-15s-h9-leakfree` (registry `role: final`, `status: current`, GRU holdout RMSE 29.635 ± 0.016, replay window held out). The remaining work is the paired rerun against that artifact, tracked as EVID-006.

- [x] EVID-006 — Paired S3/S4 rerun against the leak-free ClarkNet artifact
  - Priority: high
  - State: complete, 2026-09-13
  - Scope: `results/experiments/phase-b/2026-09-12_h2-confirmatory/`
  - Outcome: five valid counterbalanced pairs, all ten runs passed the validity gate, the node tier engaged (two nodes per reactive run, eleven on the predictive arm), provisioning delays were paired arm-to-arm within a fraction of a second, and forecast delivery was 285 of 285. The paired verdict does not support H2 and leans the other way: reactive 342.7 ms against predictive 498.7 ms, difference +156.1 ms, 95 percent CI [-29.5, +416.7], exact permutation p = 0.7812, d = 0.54.
  - Cause: every actionable forecast cycle converted into a proactive scaleup, but only 3 to 5 of 57 eligible cycles were actionable (0.053 to 0.088), and the node-arrival lead was approximately zero on four of five pairs. The cap is the qualification rule — a point forecast must exceed the capacity threshold inside the lead window — not the controller's willingness to act. Forecasting the crossing directly is the refinement that targets this rate.
  - Artifact: the predictor was pinned on 2026-09-12 (commit 98e17d1), but the promotion swapped the files — the deployed `data/models/gru_model.pt` is the synthetic-arm leak-free winner (`7f8244bc...3099d`), and the ClarkNet winner (`20623c19...32e5`) was written to `gru_model.pre-leakfree-bak.pt`. Both the confirmatory and quiet batches loaded `7f8244bc...` from their `prediction_preflight` events, so their verdicts describe the synthetic-arm predictor. See EVID-009. The 2026-07-14 manifest carries an empty predictor block, so that batch's weights remain unverifiable.
  - Variance: the paired standard deviation was 287 ms against 49 ms in the July batch, with per-run p99 from 116 to 1610 ms while probe training ran on the same box. The quiet re-run `results/experiments/phase-b/2026-09-13_h2-quiet/` repeats the profile on an idle machine to separate intrinsic hybrid variance from co-running load.
  - Why it matters: the answer to this item's question is that the leak-free ClarkNet-trained artifact does not reproduce the July significance. The headline H2 claim now rests on one significant batch under an unpinned artifact plus this fair pre-registered null, and the thesis must say so in those terms.

- [ ] EVID-007 — Symmetric GRU/LSTM study with both cells in one invocation
  - Priority: medium
  - State: ready, deferred until the box is free (external load held it at ~30 for four hours)
  - Scope: `results/models/gru/<date>_clarknet-15s-h9-symmetric/`
  - Command: `ROCR_VISIBLE_DEVICES= HIP_VISIBLE_DEVICES= CUDA_VISIBLE_DEVICES= uv run thesis-experiment gru-hpo --data-sources clarknet --cells gru,lstm --seeds 42,43,44 --n-trials 6 --horizon 9 --output-dir <new dir> --no-promote`. A partial run already exists at `results/models/gru/2026-09-11_clarknet-15s-h9-final` (one GRU seed); resuming into that directory skips the completed selections.
  - Prerequisite: none beyond CPU. Run it on an idle machine.
  - Done when: three seeds per cell complete under the identical refit call, `paired_tests` is non-empty in `metrics.json`, and the asymmetry note in the predictor section of `FINAL_NUMBERS.md` can be deleted.
  - Why it matters: the two published arms were produced by different revisions of the refit call. Both are leak-free and the difference is disclosed, and it works against the GRU claim, but a comparison should not rest on an asymmetry the reader has to reason about. This run removes the caveat and gives the paired test committed provenance inside the bundle rather than only in `scripts/gru_predictor_analysis.py`.

- [ ] EVID-008 — Extend the evidence scanner to the models root
  - Priority: low
  - State: ready, deliberately not done during a measurement window
  - Scope: `apps/experiment/experiment/evidence/registry.py::scan_bundles` plus `_bundle_id`'s `root_name`
  - Gap: `scan_bundles` walks `results/experiments/` only, so the model bundles under `results/models/gru/` are never reconciled. The four 2026-09-13 bundles (two EDAs, representation search, crossing target) carry `meta.yaml` and `report.md` and still do not appear in `registry.yaml`; the `models.*` entries that do exist were written outside the current CLI.
  - Done when: `thesis experiment evidence reconcile --apply` creates entries for every `results/models/gru/<date>_*` bundle that has a `meta.yaml`, and the four 2026-09-13 bundles appear with the human-owned role and status set.

- [ ] EVID-009 — Promotion swapped the deployed predictor for the synthetic-arm artifact
  - Priority: high
  - State: **swap done 2026-09-13** — `data/models/gru_model.pt` now carries the ClarkNet winner `20623c19c8407b116dcbcffe12a79a58fbedf24c4e731b8659206b5cb77032e5`, sidecar replaced with the champion's (2-layer, scaler 98.41/52.18), predictor restarted and `/predict` verified; the synthetic artifact is backed up as `gru_model.pt.pre-evid009`. Remaining: the pair batch against the correct artifact, and the provenance naming in the write-up.
  - Evidence: `data/models/gru_model.pt` hashed `7f8244bcc403c59a3e2be5d31b1ee5586f01c0052416c2705c0a325d1cc3099d` (the synthetic-arm artifact, LFS object of `2026-09-11_synthetic-15s-h9-leakfree/artifacts/synthetic_gru_s42.pt`) was served for the confirmatory and quiet batches while the chapter attributed them to the leak-free ClarkNet artifact. Runtime-reported scaler (107.66/23.98), layer count and val coverage matched the synthetic sidecar to the last digit.
  - Consequence: the confirmatory and quiet pair batches measured the synthetic-arm predictor. The quiet batch was stopped 2026-09-13 (user decision: fix the model first); its S4 half was void either way.
  - Done when: a pair batch runs against `20623c19c840…` and the predictor provenance in `FINAL_NUMBERS.md`, `CLAIMS_TO_EVIDENCE.md` and the thesis book names the artifact each batch actually loaded.

- [ ] EVID-010 — Spend the remaining predictor-training levers
  - Priority: high
  - State: ready, box-bound; every item below is implemented or a small change, none is blocked on design
  - Context: the split protocol delivered honesty rather than accuracy — it replaced leak-inflated synthetic numbers with the real 29.635 against OLS 29.465 — and the data explains why RMSE cannot move: 30-minute autocorrelation 0.54, so a 135-second horizon is level and slope. **Quantified 2026-09-13** (`2026-09-13_eda-clarknet/eda.json` `forecastability`): permutation entropy at the modeling unit is 0.9876 (m=5; white-noise reference 0.9996), and the residuals of a one-step level+slope fit carry 43.6% of the variance at PE 0.9946 — the linear-unexplained part of ClarkNet is ordinally indistinguishable from noise, so the RMSE ceiling is a measured property of the corpus (Bandt-Pompe; forecastability-measures-2025). Contrast: Calgary reads PE 0.374 with an 86.1% linear-unexplained variance share — sparse/bursty structure linear cannot capture, which is real headroom for a nonlinear model (Kourentzes 2013: the right target there is a demand rate, not the raw level).
  - Unspent, ranked:
    1. HPO budget. The deployed winner's study passed `--n-trials 6`; the CLI default is 30 and the space now carries weight decay (1e-6 to 1e-2 log), gradient clipping (0, 1, 5) and input dropout (0 to 0.3) on top of the original six knobs. The calendar variant falling 42% behind persistence (`skill_vs_ols` −0.378, worse than naive) is a training-pathology signature — overfitting or a feature-scaling failure, and it predates the canonical normalisation — so both the regularisation space and the input contract are under-searched. Target 50 or more trials per cell. Driver: `~/.local/state/thesis-run/evid010.sh` block 1.
    2. More training days. The ClarkNet parquet holds exactly 7 days. Named source now: **NASA-HTTP** (ita.ee.lbl.gov/html/contrib/NASA-HTTP.html) — two months of full HTTP logs from the KSC server in the same format, ~8x the span, enough for the 7-day-block CV ClarkNet cannot support. Acquisition + the existing parquet pipeline; a data job, not a modelling one.
    3. Calgary pretrain → ClarkNet fine-tune, **retargeted**: pretrain on crossing/rate labels (84.1% of Calgary buckets are zero; point-RPS pretraining would mostly teach "predict zero"), fine-tune on ClarkNet crossing labels. Module exists (`experiment/tuning/calgary_pretrain.py`, uncommitted).
    4. Multi-scale input. `window120` (2 h look-back) was the least-bad variant at −0.0035 with a derived test start; concatenating short and long windows is untested.
    5. The four within-day feature variants (queued, wave-2 driver) plus a genuine ensemble — `ensemble.json` in the 2026-09-10 probe set records n/a, so no ensemble was ever measured.
    6. Wrapper strategies: recursive one-step, per-horizon heads, and seq2seq against the current direct 9-step head.
    7. Objective: the crossing head already beats the linear arm's 0.8 to 4.2% recall with 0.988. Calibration + validation-only threshold sweep **running 2026-09-13** (`2026-09-13_t-cross-calibration`, record pending); asymmetric loss penalising under-prediction is the untested extension.


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
