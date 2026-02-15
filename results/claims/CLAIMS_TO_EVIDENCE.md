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

### Claim 3 (Performance): S4 vs S1 latency comparison
- **Evidence (attempt 1):** `results/experiments/phase-b/2026-02-12_replicated-20runs/report.md` — INVALIDATED (bugs 1-3)
- **Evidence (attempt 2):** `results/experiments/phase-b/2026-02-14_clarknet-replay/report.md` — INVALIDATED (bugs 4-7)
- **Evidence (attempt 3 — VALID):** `results/experiments/phase-b/2026-02-15_clarknet-replay/reanalysis_report.md`
- **Raw Data:** `results/experiments/phase-b/2026-02-15_clarknet-replay/results_final.json` (20 runs)
- **Result:** S4 p99 = 2821.69 ± 424.33 ms vs S1 p99 = 5.89 ± 0.01 ms. S4 is significantly worse (p<0.001 Welch corrected, d=9.384). Hybrid routing with partial serverless engagement causes severe tail-latency inflation from cold-start/queueing effects.
- **Reproduce:** `cd controller && uv run python ../thesis/scripts/reanalyze_phase_b.py --results-dir ../results/experiments/phase-b/2026-02-15_clarknet-replay`
- **Status:** ❌ H1 not supported for performance superiority — hybrid is worse than baselines on p99. This is a **valid negative result** with design implications (see Claim 3a).

### Claim 3a (Design Insight): Hybrid tail-latency caused by serverless cold-start interaction
- **Evidence:** `results/experiments/phase-b/2026-02-15_clarknet-replay/reanalysis_report.md` — S2 (serverless-only) p99 = 9.31ms (warm), but S3 (5% serverless share) p99 = 3280ms. Low serverless share causes intermittent cold-starts/queueing.
- **Raw Data:** Same as Claim 3
- **Result:** Partial serverless engagement (5-25% traffic) triggers repeated scale-from-zero penalties. S4 (25% share) performs better than S3 (5% share) because higher traffic keeps serverless warm.
- **Status:** ✅ Validated — important design implication for hybrid architectures

---

## H2: Predictive Scaling Mechanism

### Claim 4 (Mechanism): PREDICTIVE action triggers before violation
- **Evidence:** `results/experiments/phase-a1/2026-02-12_predictive-trigger/report.md`
- **Raw Data:** Decision log — action=PREDICTIVE at p99=146ms, predicted 47% load increase, confidence 72%
- **Status:** ✅ Validated (in Phase A1 ramp test only)

### Claim 5 (Superiority): S4 reduces SLO violations vs S3
- **Evidence (attempt 1):** `results/experiments/phase-b/2026-02-12_replicated-20runs/report.md` — INVALIDATED (bugs 1-3)
- **Evidence (attempt 2):** `results/experiments/phase-b/2026-02-14_clarknet-replay/report.md` — INVALIDATED (bugs 4-7)
- **Evidence (attempt 3 — VALID):** `results/experiments/phase-b/2026-02-15_clarknet-replay/reanalysis_report.md`
- **Raw Data:** `results/experiments/phase-b/2026-02-15_clarknet-replay/results_final.json`
- **Result:** S4 SLO violations = 11302 ± 1974 vs S3 = 16519 ± 1521 → **31.6% reduction** (Welch p=0.0037 Holm-corrected, Cohen's d=-2.961 large effect). S4 gru_predictions_used=80/run, S3=0. S4 p99 14% lower but not significant (p=0.073).
- **Reproduce:** `cd controller && uv run python ../thesis/scripts/reanalyze_phase_b.py --results-dir ../results/experiments/phase-b/2026-02-15_clarknet-replay`
- **Status:** ✅ H2 supported — GRU prediction significantly reduces SLO violations (mechanism + superiority validated)

---

## H3: GRU Prediction Adequacy

### Claim 6: RMSE below 10% target
- **Evidence (synthetic):** `results/models/gru/2026-02-10_training-synthetic/report.md`
- **Evidence (real traces):** `results/models/gru/2026-02-13_training-clarknet-calgary/report.md`
- **Raw Data (synthetic):** Training logs, model artifact at `controller/data/models/gru_model.pt`
- **Raw Data (real):** `results/models/gru/2026-02-13_training-clarknet-calgary/raw/training_results.json`, model at `controller/data/models/gru_model_real.pt`
- **Results (synthetic):**
  - Test RMSE% = 6.01% (target <10%) ✅
  - Test MAE% = 4.91% (target <5%) ✅
  - MAPE ≈ 4.91% (estimated) ✅
- **Results (real — ClarkNet 5-min, best):**
  - Test RMSE% = 17.78% (target <10%) ❌
  - Test MAE% = 14.48% (target <5%) ❌
  - MAPE = 18.74% ❌
- **Reproduce (real):** `cd controller && HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python -c "import sys; sys.path.insert(0,'../ml_models'); from train_gru_real import main; main()"`
- **Note:** GRU outperforms baselines on real data (baseline MAPE ~65% vs GRU 18.74%) but does not meet original thresholds. Gap is expected: real traces have non-stationarity and irregular bursts absent in synthetic data.
- **Status:** ⚠️ Partially validated — mechanism works, thresholds not met on real data

### Claim 7: Live prediction latency acceptable
- **Evidence:** `results/experiments/phase-a1/2026-02-12_predictive-trigger/report.md`
- **Result:** ~40ms (target <50ms)
- **Status:** ✅ Validated

### Claim 8: Confidence scores meaningful
- **Evidence:** `results/experiments/phase-a1/2026-02-12_predictive-trigger/report.md`
- **Result:** Range 0.72-0.88 during live predictions
- **Status:** ✅ Validated

---

## Testbed Validity & Scenario Design Decisions

### Claim 9 (Testbed): HPA works correctly on k3d
- **Evidence:** `results/experiments/validation/2026-02-13_infrastructure-validation/report.md` — T2: scale 2→10 under load, 10→2 after cooldown
- **Reproduce:** See Commands Used in report.md (T2 section)
- **Status:** ✅ Validated — S1 can use native HPA as baseline

### Claim 10 (Design Decision): HPA and kubectl scale are mutually exclusive
- **Evidence:** `results/experiments/validation/2026-02-13_infrastructure-validation/report.md` — T3: HPA reverts kubectl scale changes
- **Reproduce:** See Commands Used in report.md (T3 section)
- **Status:** ✅ Validated — S3/S4 must delete HPA; Algorithm 2 owns replicas via kubectl scale

### Claim 11 (Testbed): Knative KPA autoscaling works on k3d
- **Evidence:** `results/experiments/validation/2026-02-13_infrastructure-validation/report.md` — T4: scale 1→7 under CPU-heavy load, scale-to-zero after 60s
- **Reproduce:** See Commands Used in report.md (T4 section)
- **Status:** ✅ Validated — S2 viable as Knative-only baseline

---

## Summary

| Type | Claim | Bundle | Status |
|------|-------|--------|--------|
| Mechanism | Weight shifting | phase-a1/predictive-trigger | ✅ |
| Mechanism | Serverless engagement | phase-a1/predictive-trigger | ✅ |
| Mechanism | PREDICTIVE trigger | phase-a1/predictive-trigger | ✅ |
| Mechanism | GRU inference (synthetic) | models/gru/training-synthetic | ✅ |
| Mechanism | GRU inference (real traces) | models/gru/training-clarknet-calgary | ⚠️ Mechanism works, targets not met |
| Performance | S4 vs S1 latency | phase-b/2026-02-15_clarknet-replay | ❌ H1 not supported (hybrid p99 >> baseline) |
| Design Insight | Hybrid cold-start tail-latency | phase-b/2026-02-15_clarknet-replay | ✅ Validated |
| Superiority | S4 fewer violations than S3 | phase-b/2026-02-15_clarknet-replay | ✅ H2 supported (p=0.0037, d=-2.96) |
| Testbed | HPA works on k3d | validation/infrastructure-validation | ✅ |
| Design Decision | HPA vs kubectl scale exclusive | validation/infrastructure-validation | ✅ |
| Testbed | Knative KPA works on k3d | validation/infrastructure-validation | ✅ |

---

## Invalidated Evidence (Audit Trail)

### Round 1 (2026-02-12): Bugs 1-3
Previous Phase B data (`phase-b/2026-02-12_replicated-20runs`) and Phase C data (`phase-c/2026-02-13_dynamic-workload`) are invalidated due to three critical bugs fixed 2026-02-14:
1. SLO monitor used HAProxy ttime (total time) instead of rtime (response time) → false p99 readings
2. Algorithm 1 priority order reversed (OPTIMIZE_COST before PREDICTIVE) → PREDICTIVE never reachable
3. Prometheus not scraping routing daemon → missing controller metrics

Additionally, previous experiments used `/health` endpoint (near-zero CPU), making autoscaler and capacity results non-comparable to post-fix `/work` endpoint experiments.

### Round 2 (2026-02-14): Bugs 4-7
Phase B rerun (`phase-b/2026-02-14_clarknet-replay`) with /work endpoint also invalidated due to four experiment design bugs:
4. HAProxy server name mismatch: ScenarioResetter uses 'k3s-cluster' but actual server is 'k3s' → weight resets silently failed
5. Stale daemon process on port 9104 not killed between runs → Prometheus scrapes old daemon metrics across scenarios
6. Prometheus counter query missing `_total` suffix → gru_predictions_used=0 for all scenarios
7. No pre-run invariant checks to catch any of these

k6 latency data from round 2 remains valid; all daemon/routing metrics are garbage.

See `results/claims/INCONSISTENCIES.md` for full details.

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

- GRU originally trained on **synthetic data** → RMSE% 6.01%, MAE% 4.91% ✅
- GRU retrained on **real ClarkNet/Calgary traces** (2026-02-13) → best RMSE% 17.78%, MAE% 14.48% ❌
- ClarkNet provides usable signal at 5-min+ aggregation; Calgary too sparse for GRU
- Real-data results are a known limitation to acknowledge in thesis

**Last Updated:** 2026-02-15 (Phase B attempt 3 complete — H2 supported, H1 not supported, design insight validated)
