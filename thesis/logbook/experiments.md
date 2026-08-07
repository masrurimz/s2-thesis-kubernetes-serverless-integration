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
