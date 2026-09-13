# t_cross calibration — 2026-09-13

Canonical record for the capacity-crossing lever under the blocked-CV selection
contract. Produced by `thesis-experiment gru-probe --variant t_cross` on CPU
(`THESIS_DEVICE=cpu`), seeds 42/43/44, epochs ≤200, patience 25. Supersedes
`2026-09-13_probe-t-cross` (same contract, GPU run, no calibration layer).

## What this bundle adds over the first t_cross record

1. **Isotonic calibration fitted on inner-val only** — per fold × seed, the
   isotonic map sees only that fold's inner-val per-step (prob, label) pairs.
   Eval windows are never touched by the calibrator.
2. **Threshold sweep on the selection folds** — 19-point curves, uncalibrated
   and calibrated, in `decision_rule.curve_*`.
3. **OOD report on b5** and a **frozen deployment fold** with per-seed artifacts
   (`artifacts/t_cross_s{42,43,44}.pt`, schema v2, `target_mode='t_cross'`).
4. **Per-window per-step probabilities persisted** (`probs/t_cross_s*.npz`) so
   every sweep is reconstructible without retraining.

## Headline

| metric | uncalibrated | isotonic-calibrated | OLS reference |
|---|---|---|---|
| Brier per step (b2/b3/b4, mean over seeds) | 0.2361 | **0.0428** | 0.0488 |

Calibration alone moves the lever from losing the Brier gate (0.236 > 0.049) to
clearing it (0.043 < 0.049). The gate's keep rule is recall at bounded FAR —
Brier is reported, not decisive — but the calibrated score is now honest.

## Operating points (selection folds, recall ≥ 0.80 target)

| | threshold | recall | precision | FAR | mean lead |
|---|---|---|---|---|---|
| uncalibrated | 0.95 | 0.970 | 0.405 | 0.439 | 4.0 steps |
| calibrated | 0.45 | 0.816 | 0.543 | 0.210 | 3.9 steps |

Calibration buys a real operating point: at the recall target the false-alarm
rate drops from 0.44 to 0.21 and precision rises from 0.40 to 0.54, at ~3.9
steps (≈58 s at the 15 s sample interval) of mean lead.

## Per-fold pattern (mean over seeds)

- b2/b3/b4 (selection): brier_per_step 0.20–0.30 uncalibrated; recall ≈0.99 at
  FAR ≈0.60 — the raw head fires often and early.
- b5 (OOD): brier 0.008–0.011, recall 0.61–0.72, FAR 0.11–0.23, lead ≈9 steps —
  the calm tail block: fewer crossings, lower FAR, longer lead.
- deployment-frozen: recall 1.00 on all seeds, FAR 0.17–0.26, lead ≈3 steps.

## Caveats

- `headline_finding.selection_crossing_base_rate` / `ols_crossing_recall_range`
  are null in this record — the OLS crossing-recall comparison is carried in
  `beats_ols_gate` and the reference-arms section instead.
- FAR is computed per-step against steps at/above capacity; the crossing base
  rate per window is ~0.25–0.45 (see `label_distribution`), so per-step FAR
  overstates window-level false alarms.
- CPU vs GPU RNG shifts fold-level numbers slightly vs the first record; the
  qualitative pattern (b5 calm, deployment saturated) is identical.
