# Claims to Evidence Mapping

**Every thesis claim must trace to raw data and a reproduction command.**

---

## H1: Hybrid Routing Mechanism

### Claim 1 (Mechanism): Dynamic weight shifting works
- **Evidence:** `results/experiments/phase-a1/2026-02-12_predictive-trigger/report.md` — Weight table: 100/0 → 90/10 → ... → 50/50
- **Raw Data:** Decision log in report (captured from daemon at runtime)
- **Reproduce:** See meta.yaml in same bundle
- **Status:** ✅ Validated

### Claim 2 (Mechanism): Serverless backend engages under load
- **Evidence:** `results/experiments/phase-a1/2026-02-12_predictive-trigger/report.md` — Knative weight > 0 during high load
- **Raw Data:** Same as Claim 1
- **Status:** ✅ Validated

### Claim 3 (Superiority): S4 outperforms S1
- **Evidence:** `results/experiments/phase-b/2026-02-12_replicated-20runs/report.md`
- **Raw Data:** `results/experiments/phase-b/2026-02-12_replicated-20runs/raw/experiments_final.json`
- **Result:** S1 mean p99=519.8ms, S4 mean p99=430.8ms — S4 actually LOWER but high variance
- **Threat:** k3d localhost routing bias, some runs have stale Prometheus metrics
- **Status:** ⚠️ Not established (high variance, data quality issues)

---

## H2: Predictive Scaling Mechanism

### Claim 4 (Mechanism): PREDICTIVE action triggers before violation
- **Evidence:** `results/experiments/phase-a1/2026-02-12_predictive-trigger/report.md`
- **Raw Data:** Decision log — action=PREDICTIVE at p99=146ms, predicted 47% load increase, confidence 72%
- **Status:** ✅ Validated (in Phase A1 ramp test only)

### Claim 5 (Superiority): S4 reduces violations vs S3
- **Evidence:** `results/experiments/phase-b/2026-02-12_replicated-20runs/report.md`
- **Raw Data:** `results/experiments/phase-b/2026-02-12_replicated-20runs/raw/experiments_final.json`
- **Result:** S3: 4/5 runs violated, S4: 5/5 runs violated. S4 is WORSE.
- **Root Cause:** GRU server was NOT running during Phase B (gru_predictions_used=0 in all runs). Phase B inadvertently compared reactive-only behaviors (S3 vs S4 both used SCALE_OUT, no PREDICTIVE).
- **Analysis:** `results/experiments/phase-b/2026-02-12_replicated-20runs/PREDICTIVE_ELIGIBILITY_ANALYSIS.md`
- **Status:** ⚠️ Not demonstrated (Phase B = reactive comparison, not predictive vs reactive)

---

## H3: GRU Prediction Adequacy

### Claim 6: RMSE below 10% target
- **Evidence:** `results/models/gru/2026-02-10_training-synthetic/report.md`
- **Raw Data:** Training logs, model artifact at `controller/data/models/gru_model.pt`
- **Results:**
  - Test RMSE = 6.01% (target <10%) ✅
  - Test MAE% = 4.91% (target <5%) ✅
  - MAPE ≈ 4.91% (estimated) ✅
- **Reproduce:** `cd controller && HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python -m prediction.train_gru`
- **Note:** Trained on synthetic data, validated against ClarkNet/Calgary baselines
- **Status:** ✅ Fully Validated

### Claim 7: Live prediction latency acceptable
- **Evidence:** `results/experiments/phase-a1/2026-02-12_predictive-trigger/report.md`
- **Result:** ~40ms (target <50ms)
- **Status:** ✅ Validated

### Claim 8: Confidence scores meaningful
- **Evidence:** `results/experiments/phase-a1/2026-02-12_predictive-trigger/report.md`
- **Result:** Range 0.72-0.88 during live predictions
- **Status:** ✅ Validated

---

## Summary

| Type | Claim | Bundle | Status |
|------|-------|--------|--------|
| Mechanism | Weight shifting | phase-a1/predictive-trigger | ✅ |
| Mechanism | Serverless engagement | phase-a1/predictive-trigger | ✅ |
| Mechanism | PREDICTIVE trigger | phase-a1/predictive-trigger | ✅ |
| Mechanism | GRU inference | models/gru/training-synthetic | ✅ |
| Superiority | S4 outperforms S1 | phase-b/replicated-20runs | ⚠️ Not established |
| Superiority | S4 fewer violations than S3 | phase-b/replicated-20runs | ⚠️ Not demonstrated |

---

## Reproduction Commands

### H3 (GRU)
```bash
cd controller
HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python -c "
from prediction.model_loader import GRUModelLoader
loader = GRUModelLoader()
print(f'RMSE: {loader.rmse}')
"
```

### H1/H2 Mechanisms
```bash
cd controller
HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python -m prediction.prediction_server
HSA_OVERRIDE_GFX_VERSION=11.0.0 PREDICTION_CONFIDENCE_THRESHOLD=0.6 \
  uv run python -m daemon.routing_daemon --scenario s4-hybrid-predictive
```

### Full Phase B
```bash
cd controller
HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python ../thesis/scripts/run_phase_b_experiments.py \
  --phase full --runs 5 --duration 300
```

---

## Training Data Note

- GRU trained on **synthetic data** (generated traffic patterns)
- NOT on ClarkNet/Calgary as proposed in thesis methodology Section 3.2
- ClarkNet/Calgary parquets in `data/processed/` used for **baseline model comparison only**

**Last Updated:** 2026-02-13
