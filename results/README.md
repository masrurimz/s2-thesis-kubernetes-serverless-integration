# Results — Evidence Registry

**Single source of truth for all experiment evidence.**

Rules:
1. Every experiment is a self-contained bundle: `meta.yaml` + `raw/` + `report.md`
2. Every thesis claim traces to raw data via `claims/CLAIMS_TO_EVIDENCE.md`
3. One report per experiment. No duplicate summaries.
4. Raw data is never edited.

---

## Hypothesis Coverage

| Hypothesis | Mechanism Validated? | Superiority Demonstrated? | Stats Done? | Notes |
|------------|---------------------|--------------------------|-------------|-------|
| **H1** (Hybrid > Pure) | ✅ Weight shifting, serverless engagement | ⚠️ Not established | ✅ Welch t-test | k3d localhost bias; high p99 variance |
| **H2** (Predictive > Reactive) | ✅ PREDICTIVE triggered pre-violation | ⚠️ Not demonstrated | ✅ | GRU server not running in Phase B (gru_predictions_used=0); mechanism validated in A1 ramp |
| **H3** (GRU adequate) | ✅ 6.01% RMSE, 40ms latency | N/A | ✅ | Trained on synthetic, not real traces |

---

## Experiment Registry

| ID | Phase | Category | Date | Scenarios | Bundle Path |
|----|-------|----------|------|-----------|-------------|
| `phase-a1.stress-tests.2026-02-11` | A1 | Stress Tests | 2026-02-11 | S3, S4 | `experiments/phase-a1/2026-02-11_stress-tests/` |
| `phase-a1.predictive-trigger.2026-02-12` | A1 | Mechanism Validation | 2026-02-12 | S4 | `experiments/phase-a1/2026-02-12_predictive-trigger/` |
| `phase-b.calibration.2026-02-12` | B | Calibration | 2026-02-12 | S1, S3 | `experiments/phase-b/2026-02-12_calibration/` |
| `phase-b.replicated.2026-02-12` | B | Replicated Runs | 2026-02-12 | S1-S4 | `experiments/phase-b/2026-02-12_replicated-20runs/` |
| `gru.training-synthetic.2026-02-10` | — | Model Training | 2026-02-10 | — | `models/gru/2026-02-10_training-synthetic/` |
| `cost.proxy-analysis.2026-02-11` | B | Cost Analysis | 2026-02-11 | S1-S4 | `cost/2026-02-11_proxy-analysis/` |

---

## Quick Links

- **Claims audit trail:** [`claims/CLAIMS_TO_EVIDENCE.md`](claims/CLAIMS_TO_EVIDENCE.md)
- **Known issues:** [`claims/INCONSISTENCIES.md`](claims/INCONSISTENCIES.md)
- **Experiment protocol:** [`../thesis/protocol/EXPERIMENT_PROTOCOL.md`](../thesis/protocol/EXPERIMENT_PROTOCOL.md)
- **Threats to validity:** [`../thesis/protocol/THREATS_TO_VALIDITY.md`](../thesis/protocol/THREATS_TO_VALIDITY.md)

---

## How to Add a New Experiment

1. Create folder: `experiments/<phase>/<YYYY-MM-DD_slug>/`
2. Add `meta.yaml` (see any existing bundle for template)
3. Put raw outputs in `raw/`
4. Write `report.md` (raw artifacts first, then interpretation)
5. Add a row to the registry table above
6. Update `claims/CLAIMS_TO_EVIDENCE.md` if it supports a hypothesis

---

## Reproduction

### Full Phase B
```bash
cd controller
HSA_OVERRIDE_GFX_VERSION=11.0.0 \
  uv run python ../thesis/scripts/run_phase_b_experiments.py --phase full --runs 5 --duration 300
```

### GRU Training
```bash
cd controller
HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python -m prediction.train_gru
```

### Live Validation
```bash
cd controller
HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python -m prediction.prediction_server &
HSA_OVERRIDE_GFX_VERSION=11.0.0 PREDICTION_CONFIDENCE_THRESHOLD=0.6 \
  uv run python -m daemon.routing_daemon --scenario s4-hybrid-predictive
```
