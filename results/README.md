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
| **H1** (Hybrid > Pure) | ✅ Weight shifting, serverless engagement | ❌ Not supported in valid replicated set (`2026-02-15_clarknet-replay`); rerun-v2 (`n=1`) directional only | ✅ Welch t-test | Hybrid p99 worse than S1 in valid replicated set; no superiority claim |
| **H2** (Predictive > Reactive) | ✅ PREDICTIVE triggered pre-violation | ✅ Supported in valid replicated set (`2026-02-15_clarknet-replay`); rerun-v2 (`n=1`) non-inferential | ✅ | Keep A1 mechanism evidence + valid replicated evidence; treat rerun-v2 as pipeline/directional |
| **H3** (GRU adequate) | ✅ 6.01% RMSE (synthetic), ⚠️ 17.78% RMSE (real ClarkNet) | N/A | ✅ | Synthetic meets targets; real traces do not (<10% RMSE). GRU still outperforms baselines on real data. |

---

## Experiment Registry

| ID | Phase | Category | Date | Scenarios | Bundle Path |
|----|-------|----------|------|-----------|-------------|
| `phase-a1.stress-tests.2026-02-11` | A1 | Stress Tests | 2026-02-11 | S3, S4 | `experiments/phase-a1/2026-02-11_stress-tests/` |
| `phase-a1.predictive-trigger.2026-02-12` | A1 | Mechanism Validation | 2026-02-12 | S4 | `experiments/phase-a1/2026-02-12_predictive-trigger/` |
| `phase-b.calibration.2026-02-12 (INVALIDATED)` | B | Calibration | 2026-02-12 | S1, S3 | `experiments/phase-b/2026-02-12_calibration/` |
| `phase-b.replicated.2026-02-12 (INVALIDATED)` | B | Replicated Runs | 2026-02-12 | S1-S4 | `experiments/phase-b/2026-02-12_replicated-20runs/` |
| `phase-b.calibration.2026-02-14` | B | Calibration | 2026-02-14 | S1 | `experiments/phase-b/2026-02-14_calibration-work-5ms/` |
| `gru.training-synthetic.2026-02-10` | — | Model Training | 2026-02-10 | — | `models/gru/2026-02-10_training-synthetic/` |
| `gru.training-clarknet-calgary.2026-02-13` | — | Model Training | 2026-02-13 | — | `models/gru/2026-02-13_training-clarknet-calgary/` |
| `cost.proxy-analysis.2026-02-11` | B | Cost Analysis | 2026-02-11 | S1-S4 | `cost/2026-02-11_proxy-analysis/` |
| `phase-c.dynamic-workload.2026-02-13` | C | Dynamic Workload | 2026-02-13 | S3, S4 | `experiments/phase-c/2026-02-13_dynamic-workload/` |
| `phase-b.clarknet-replay.2026-02-14 (INVALIDATED)` | B | Replicated Runs (ClarkNet) | 2026-02-14 | S1-S4 | `experiments/phase-b/2026-02-14_clarknet-replay/` |
| `phase-b.clarknet-replay-aborted.2026-02-14` | B | Aborted Run | 2026-02-14 | S2, S4 | `experiments/phase-b/2026-02-14_clarknet-replay-ABORTED/` |
| `phase-b.fib34-validation.2026-02-18` | B | Validation (fib34) | 2026-02-18 | S1-S4 | `experiments/phase-b/2026-02-18_fib34-validation/` |
| `phase-b.pilot-validity-gates-rerun.2026-02-19` | B | Pilot Validation (n=2) | 2026-02-19 | S1-S4 | `experiments/phase-b/2026-02-19_pilot-n2-validity-gates-rerun/` |
| `phase-b.s2-serverless-validation.2026-02-20` | B | Validation (S2 only) | 2026-02-20 | S2 | `experiments/phase-b/2026-02-20_s2-serverless-validation/` |
| `phase-b.s2-serverless-validation-v2.2026-02-20` | B | Validation (S2 only, app-duration) | 2026-02-20 | S2 | `experiments/phase-b/2026-02-20_s2-serverless-validation-v2/` |
| `phase-b.all-scenarios-rerun-v2.2026-02-21` | B | Full Rerun (n=1 each, app-duration) | 2026-02-21 | S1-S4 | `experiments/phase-b/2026-02-21_all-scenarios-rerun-v2/` |
| `validation.infrastructure.2026-02-13` | Validation | Infrastructure Validation | 2026-02-13 | T0–T4 | `experiments/validation/2026-02-13_infrastructure-validation/` |
| `cost.unified-aws-fib34.2026-02-18` | B | Cost Analysis | 2026-02-18 | S1-S4 | `cost/2026-02-18_fib34-unified-aws-cost/` |
| `cost.unified-aws-pilot-n2.2026-02-19` | B | Cost Analysis (Pilot n=2) | 2026-02-19 | S1-S4 | `cost/2026-02-19_pilot-n2-unified-aws-cost/` |
| `cost.unified-aws-s2-validation.2026-02-20` | B | Cost Analysis (S2 validation) | 2026-02-20 | S2 | `cost/2026-02-20_s2-validation-unified-aws-cost/` |
| `cost.unified-aws-s2-validation-v2.2026-02-21` | B | Cost Analysis (S2 validation v2) | 2026-02-21 | S2 | `cost/2026-02-21_s2-validation-v2-unified-aws-cost/` |
| `cost.unified-aws-all-scenarios-rerun-v2.2026-02-21` | B | Cost Analysis (all scenarios rerun v2) | 2026-02-21 | S1-S4 | `cost/2026-02-21_all-scenarios-rerun-v2-unified-aws-cost/` |

---

## Quick Links

- **Claims audit trail:** [`claims/CLAIMS_TO_EVIDENCE.md`](claims/CLAIMS_TO_EVIDENCE.md)
- **Known issues:** [`claims/INCONSISTENCIES.md`](claims/INCONSISTENCIES.md)
- **Experiment protocol:** [`../thesis/protocol/EXPERIMENT_PROTOCOL.md`](../thesis/protocol/EXPERIMENT_PROTOCOL.md)
- **Threats to validity:** [`../thesis/protocol/THREATS_TO_VALIDITY.md`](../thesis/protocol/THREATS_TO_VALIDITY.md)
- **Experiment registry (SSOT):** [`experiments/REGISTRY.yaml`](experiments/REGISTRY.yaml) — machine-readable classification of all experiment bundles
- **Scanner:** `uv run python scripts/audit_experiment_registry.py --write` (run after every experiment)
- **Citation inventory:** [`claims/DOCX_CITATION_INVENTORY.md`](claims/DOCX_CITATION_INVENTORY.md) — DOCX-first citation audit

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
HSA_OVERRIDE_GFX_VERSION=11.0.0 \
  uv run python scripts/run_phase_b_experiments.py --phase full --runs 5 --duration 300
```

### GRU Training
```bash
HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python -m prediction.train_gru
```

### Live Validation
```bash
HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python -m prediction.prediction_server &
HSA_OVERRIDE_GFX_VERSION=11.0.0 PREDICTION_CONFIDENCE_THRESHOLD=0.6 \
  uv run python -m daemon.routing_daemon --scenario s4-hybrid-predictive
```
