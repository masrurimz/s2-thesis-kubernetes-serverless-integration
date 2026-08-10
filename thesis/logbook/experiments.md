# Experiment Log

Experiment entries record research events, decisions, and communications about runs. They **do not reproduce result tables** — numbers live in the bundles and `FINAL_NUMBERS.md`; the logbook links them.

Seed entries below cover the runs that define the current evidence state (July definitive + August replication). New runs get appended by the agent on request or after evidence commands.

## EXP-2026-07-14-01 — Definitive paired H2 experiment (role: final)
- Date/time: 2026-07-14
- Status: actioned
- Evidence role: **final** (the thesis claim; EVID-003)
- Phase/scenario: Phase B / S3–S4 paired, n=5, ClarkNet, counterbalanced, seed 42
- What happened: the pre-registered paired comparison ran; S4 won all 5 pairs; p99 188.5 vs 126.0 ms; permutation p=0.0304, d=−1.26; SLO violations 656→130 (−80%); cost identical $163; 280/280 predictions delivered (fidelity gate passed).
- Decision or interpretation: H2 supported on the pre-specified primary metric. Bundle promoted to `role: final` in the registry on 2026-08-07 (EVID-003, `bundle_promoted` event).
- Follow-up: none
- Evidence:
  - Bundle: [../../results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5/](../../results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5/)
  - Registry: [../../results/evidence/registry.yaml](../../results/evidence/registry.yaml), role=final/current
  - Claim/number: [../../results/claims/FINAL_NUMBERS.md](../../results/claims/FINAL_NUMBERS.md)
  - Drift/protocol: [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) §6, D6/D7/D13
- Related: QA-005, QA-011

## EXP-2026-08-06-01 — Bare-minimum pipeline test (diagnostic)
- Date/time: 2026-08-06
- Status: actioned
- Evidence role: diagnostic
- Phase/scenario: Phase B / 1 pair, preflight + pipeline green test
- What happened: idempotency verification — same trigger, new bundle, no state pollution; both runs valid, S4 fidelity delivered.
- Decision or interpretation: pipeline repeatable; baseline for the replication series.
- Follow-up: none
- Evidence:
  - Bundle: [../../results/experiments/phase-b/2026-08-06_paired-h2_225818/](../../results/experiments/phase-b/2026-08-06_paired-h2_225818/)
  - Registry: role=diagnostic/current
  - Drift/protocol: [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) §6b
- Related: —

## EXP-2026-08-06-02 — n=3 default-cap run (diagnostic, config-drift finding)
- Date/time: 2026-08-06
- Status: actioned
- Evidence role: diagnostic (misconfigured reproduction — NOT evidence for H2)
- Phase/scenario: Phase B / 3 pairs, default calibration (`max_k8s_replicas=6`)
- What happened: S3 appeared faster (96.8 vs 117.5 ms) — root cause: default cap ≠ definitive cap; S3 overflowed to serverless, making the reactive baseline artificially fast.
- Decision or interpretation: documented as a config-drift diagnostic in DRIFT §6b; definitive config recorded in `results/calibration/2026-08-06_definitive-repro.json` so re-triggers match the definitive evidence.
- Follow-up: none (finding disclosed in thesis ch03/appendix A + calibration docs)
- Evidence:
  - Bundle: [../../results/experiments/phase-b/2026-08-06_paired-h2_234256/](../../results/experiments/phase-b/2026-08-06_paired-h2_234256/)
  - Calibration: [../../results/calibration/2026-08-06_definitive-repro.json](../../results/calibration/2026-08-06_definitive-repro.json)
  - Drift/protocol: [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) §6b
- Related: QA-015

## EXP-2026-08-07-01 — n=3 with definitive override (diagnostic)
- Date/time: 2026-08-07
- Status: actioned
- Evidence role: diagnostic
- Phase/scenario: Phase B / 3 pairs, `max_k8s_replicas=10` override + h=9
- What happened: S4 won 3/3 pairs (Δ −16.4 ms, d=−2.90; p at the n=3 floor).
- Decision or interpretation: directional confirmation; small-n floor noted.
- Follow-up: none
- Evidence:
  - Bundle: [../../results/experiments/phase-b/2026-08-07_paired-h2_034648/](../../results/experiments/phase-b/2026-08-07_paired-h2_034648/)
  - Registry: role=diagnostic/current
- Related: QA-011

## EXP-2026-08-07-02 — Replication batch 1, n=5 (diagnostic)
- Date/time: 2026-08-07
- Status: actioned
- Evidence role: diagnostic
- Phase/scenario: Phase B / 5 pairs, definitive config
- What happened: S4 won 4/5 pairs; Δ −21.8 ms, p=0.0958, d=−0.71; SLO 172→101 (−41%). Baseline S3 ran faster than July (131.7 vs 188.5 ms).
- Decision or interpretation: directional but not significant — between-batch variance, reported honestly (DRIFT §6b, ch04 sec:replication).
- Follow-up: none (superseded in interpretation by the pooled n=10)
- Evidence:
  - Bundle: [../../results/experiments/phase-b/2026-08-07_paired-h2_060200/](../../results/experiments/phase-b/2026-08-07_paired-h2_060200/)
  - Registry: role=diagnostic/current
- Related: QA-011

## EXP-2026-08-07-03 — Replication batch 2, n=5 (diagnostic)
- Date/time: 2026-08-07
- Status: actioned
- Evidence role: diagnostic
- Phase/scenario: Phase B / 5 pairs, definitive config
- What happened: S4 won **5/5** pairs; Δ −80.8 ms (CI [−152.0, −33.0]), **p=0.0304 — identical to July**, d=−1.00; SLO 626→8.
- Decision or interpretation: independent significant replication of the definitive result.
- Follow-up: none
- Evidence:
  - Bundle: [../../results/experiments/phase-b/2026-08-07_paired-h2_104918/](../../results/experiments/phase-b/2026-08-07_paired-h2_104918/)
  - Registry: role=diagnostic/current
- Related: QA-011

## EXP-2026-08-07-04 — Evidence governance (registry + journal)
- Date/time: 2026-08-07
- Status: actioned
- Evidence role: governance event (all roles)
- What happened: definitive bundle promoted to `role: final`; all August bundles registered `role: diagnostic`; reconcile → catalog refresh → journal regenerated (139 bundles total).
- Decision or interpretation: registry is the single source of truth for bundle roles; `EXPERIMENT_JOURNAL.md` regenerated, never hand-edited.
- Follow-up: none
- Evidence:
  - Registry: [../../results/evidence/registry.yaml](../../results/evidence/registry.yaml)
  - Journal: [../../results/EXPERIMENT_JOURNAL.md](../../results/EXPERIMENT_JOURNAL.md)
  - Commands: `uv run thesis-experiment evidence reconcile --apply` → `catalog refresh` → `journal`
- Related: —

---

## Historical series index (Feb–Jul 2026)

The complete machine list of all 139 bundles is the generated ledger: [../../results/EXPERIMENT_JOURNAL.md](../../results/EXPERIMENT_JOURNAL.md) (regenerate with `uv run thesis-experiment evidence journal`). Below is the **curated series index** — the runs that shaped the current evidence state, grouped by research arc. Roles per [../../results/evidence/registry.yaml](../../results/evidence/registry.yaml).

| Series | Key bundles | Role | Established |
|---|---|---|---|
| Phase B pipeline builds (Feb) | `2026-02-12_calibration`, `2026-02-14_clarknet-replay`, `2026-02-16_s1-hpa-validation`, `2026-02-20_s2-serverless-validation`, `2026-02-22_full-phase-b-canonical-r5`, `2026-02-25_s3s4-post-p0p2-fixes` | diagnostic / archived | Canonical Phase B pipeline + validity gates |
| V3 & S2 bring-up (Jul 4–7) | `2026-07-04_v3-tuned-full`, `2026-07-05_final-all-fixes`, `2026-07-07_s2-final`, `2026-07-07_s3-consistent` | diagnostic | Controller correctness (V3 + KPA path) |
| Fairness calibration (Jul 5–11) | `2026-07-05_clarknet-cpu-limit`, `2026-07-06_s1-s4-fair-calibrated`, `2026-07-10_cpulimit_n1`, `2026-07-11_fair_tuned_n1`, `2026-07-11_nolimit_n1` | diagnostic | Node CPU bounding + r_saturation calibration (the fairness methodology) |
| GRU holdout / HPO (Jul 10) | `2026-07-10_gp_holdout_n5`, `2026-07-10_tuned_holdout` | diagnostic | Post-HPO synthetic RMSE 4.75% |
| H2 paired evolution (Jul 11–14) | `2026-07-11_paired-h2`, `2026-07-12_paired-h2-clean`, `2026-07-12_paired-h2-clean-v2` → `2026-07-14_clarknet-tuned-paired-n5` | diagnostic → **final** | The definitive H2 result (p=0.0304, role=final) |
| H1 architecture diagnostics (Jul 13–14) | `2026-07-13_clarknet-dynamic-node-n1`, `2026-07-13_clarknet-scaledown-n1`, `2026-07-14_clarknet-tuned-s3-n1`, `2026-07-14_clarknet-util-scaledown-n1` | diagnostic | S1–S4 trade-off map (S2 fastest, 2.8× cost) |
| Horizon tuning (Jul 13) | `2026-07-13_s4-horizon7-test`, `2026-07-13_s4-horizon9-test` | diagnostic | `prediction_horizon=9` (135 s) chosen |
| Replication series (Aug 6–7) | `2026-08-06_paired-h2_225818/234256`, `2026-08-07_paired-h2_034648/060200/104918` | diagnostic | Reproducibility + config-drift finding (EXP-2026-08-06-02) |

Also present (not indexed above): `phase-a1/`, `phase-c/`, `tuning/`, `validation/` bundles — see the journal for the exhaustive list.

---

## Append convention

New entry template (copy when the agent logs a run):

```markdown
## EXP-YYYY-MM-DD-NN — <run, review, invalidation, or decision>
- Date/time: YYYY-MM-DD HH:MM
- Status: pending | actioned
- Evidence role: planned | diagnostic | final | superseded
- Phase/scenario: [e.g. Phase B / S3-S4]
- What happened: [1-3 sentences; no copied metrics]
- Decision or interpretation: [...]
- Follow-up: [owner, due date, or none]
- Evidence:
  - Bundle: [../../results/experiments/phase-b/<bundle>/](...)
  - Registry: [../../results/evidence/registry.yaml](../../results/evidence/registry.yaml)
  - Claim/number: [../../results/claims/FINAL_NUMBERS.md](../../results/claims/FINAL_NUMBERS.md)
  - Drift/protocol: [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md), section <D#>
- Related: `WA-...`, `BIM-...`, `QA-...`
```

## EXP-2026-08-08-01 — Replikasi paired H2 batch 1 (diagnostic, replication tier)
- Date/time: 2026-08-08
- Status: actioned
- Evidence role: **diagnostic** (replication tier; bukan klaim final)
- Phase/scenario: Phase B / S3–S4 paired, RUN1, 5 pairs, definitive config
- What happened: Batch replikasi terdiri atas 10 run (5 pasangan S3/S4), dengan treatment fidelity 280/280, delivery 1.0, dan 0 prediksi gagal. Hasilnya menunjukkan S3 136.89 ms dan S4 132.93 ms pada p99, selisih −3.96 ms, permutation p=0.4363, dan d≈−0.05; S4 pada pasangan ke-5 mengalami keterlambatan provisioning sebesar 117 s.
- Decision or interpretation: H2 **tidak didukung** pada batch ini. Sebagai bukti replication tier, hasil ini merupakan batch null yang harus dipertahankan dalam pelaporan variasi antar-batch; klaim H2 final tetap hanya berasal dari bundle definitif Juli.
- Follow-up: none
- Evidence:
  - Bundle: [../../results/experiments/phase-b/2026-08-08_paired-h2_195150/](../../results/experiments/phase-b/2026-08-08_paired-h2_195150/)
  - Registry: [../../results/evidence/registry.yaml](../../results/evidence/registry.yaml), role=diagnostic/current
  - Drift/protocol: [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) §6b
- Related: QA-011

## EXP-2026-08-08-02 — Replikasi paired H2 batch 2 (diagnostic, replication tier)
- Date/time: 2026-08-08
- Status: actioned
- Evidence role: **diagnostic** (replication tier; bukan klaim final)
- Phase/scenario: Phase B / S3–S4 paired, RUN2, 5 pairs, definitive config
- What happened: Batch replikasi terdiri atas 10 run dengan fidelity 280/280. S3 menghasilkan 160.38 ms dan S4 102.34 ms pada p99, selisih −58.05 ms, 95% CI [−161.5, −2.8], p=0.0621, dan d=−0.505 (medium); S4 lebih cepat pada 4 dari 5 pasangan, sedangkan pasangan ke-4 memuat outlier S3 sebesar 353 ms akibat provisioning node.
- Decision or interpretation: H2 **marginal** pada batch ini. Hasilnya secara arah konsisten dengan hasil definitif, tetapi tetap merupakan bukti replication tier dan tidak menggantikan klaim H2 final dari bundle definitif Juli.
- Follow-up: none
- Evidence:
  - Bundle: [../../results/experiments/phase-b/2026-08-08_paired-h2_233726/](../../results/experiments/phase-b/2026-08-08_paired-h2_233726/)
  - Registry: [../../results/evidence/registry.yaml](../../results/evidence/registry.yaml), role=diagnostic/current
  - Drift/protocol: [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) §6b
- Related: QA-011

## EXP-2026-08-09-01 — Replikasi penuh ClarkNet n=5, empat skenario (intermediate, replication tier)
- Date/time: 2026-08-09
- Status: actioned
- Evidence role: **intermediate** (replication tier; bukan klaim final)
- Phase/scenario: Phase B / S1–S4, RUN3, 4 skenario × 5 run, ClarkNet
- What happened: Sebanyak 20 run bersih (4 skenario × 5) selesai dengan fidelity 280/280 per scenario-set. P99 dan pelanggaran SLO berturut-turut adalah: S1 K8s-only 110.3 ms / 253; S2 serverless-only 79.7 ms / 2; S3 hybrid-reactive 151.6 ms / 1998; S4 hybrid-predictive 99.1 ms / 92. Untuk H1, S2 dibandingkan dengan S1 menghasilkan Welch p=0.0004 dan d=−5.582 (MW p=0.0079). Untuk H2, S4 dibandingkan dengan S3 menurunkan p99 sebesar 34.6% dan pelanggaran SLO sebesar 95.4%, dengan MW p=0.0317, Welch p=0.0970, dan d=−1.300.
- Decision or interpretation: H1 memperoleh dukungan pada perbandingan S2–S1. H2 menunjukkan hasil signifikan menurut Mann–Whitney tetapi tidak menurut Welch; secara batch-dependent hasilnya tetap konsisten secara arah dengan hasil definitif, sehingga RUN3 dicatat sebagai replication tier intermediate dan bukan klaim H2 final. Klaim H2 final tetap hanya bundle definitif Juli (p=0.0304, d=−1.26).
- Follow-up: none
- Evidence:
  - Bundle: [../../results/experiments/phase-b/2026-08-09_clarknet-replay_032257/](../../results/experiments/phase-b/2026-08-09_clarknet-replay_032257/)
  - Registry: [../../results/evidence/registry.yaml](../../results/evidence/registry.yaml), role=intermediate/current
  - Claim/number: [../../results/claims/FINAL_NUMBERS.md](../../results/claims/FINAL_NUMBERS.md) (H2 final remains the July bundle)
  - Drift/protocol: [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) §6b
- Related: QA-011
