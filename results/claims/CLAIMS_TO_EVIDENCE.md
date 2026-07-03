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
- **Reproduce (real):** `HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python -m prediction.train_gru_real`
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

### Claim 11a (Pipeline): Two-tier validity gates are emitted end-to-end
- **Evidence:** `results/experiments/phase-b/2026-02-19_pilot-n2-validity-gates-rerun/report.md` — Run Validity, Stress Validity, and Analysis Set sections
- **Raw Data:** `results/experiments/phase-b/2026-02-19_pilot-n2-validity-gates-rerun/results_final.json` (`run_validity_passed`, `stress_validity_passed`, `validity_gate_passed`)
- **Reproduce:** `cd controller && HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python ../thesis/scripts/run_phase_b_experiments.py --phase full --runs 2 --output /home/zahid/work/master-s2-study/thesis-kubernetes-serverless-integration/results/experiments/phase-b/2026-02-19_pilot-n2-validity-gates-rerun`
- **Status:** ✅ Validated — all scenarios 2/2 run-valid and 2/2 stress-valid in pilot

---

## Cost Analysis

### Claim 12a (Cost Mechanism): CPU throttling + concurrency creates hidden serverless cost multiplier
- **Evidence:** `results/cost/2026-02-17_three-model-cost-comparison/report.md` §Key Finding: CPU Throttling and Little's Law
- **Raw Data:** `controller/results/cost_analysis/cost_analysis_20260217_144437.json`
- **Result:** Knative pod (200m CPU, target-concurrency=10) creates 50× CPU slowdown per request. Lambda bills wall-clock (2.515s for S2) not CPU time (9.77ms), creating ~364× cost multiplier. K8s pods also throttled: Little's Law service time S1=105ms, S3=262ms, S4=1.309s (not the naive 10ms hardcode).
- **Status:** ✅ Validated — mechanism insight about serverless cost drivers

### Claim 12b (Cost Projection): Production cost comparison under t3.medium sizing
- **Evidence:** `results/cost/2026-02-17_three-model-cost-comparison/report.md` §Model 3b, §Thesis Implications
- **Raw Data:** `controller/results/cost_analysis/cost_analysis_20260217_144437.json`
- **Source Experiment:** `results/experiments/phase-b/2026-02-16_validation-metrics-fixes/`
- **Reproduce:** `cd controller && uv run python ../thesis/scripts/cost_analyzer.py --experiment-dir ../results/experiments/phase-b/2026-02-16_validation-metrics-fixes`
- **Production Assumptions:** t3.medium ($0.0416/hr), 1.8 vCPU allocatable, +1 HA headroom node, EKS $0.10/hr
- **Results (Model 3b EC2 Production — monthly):** S1 $162, S2 $192, S3 $192, S4 $222
- **Results (Model 1 Lambda PC — monthly):** S1 $162, S2 $2,326, S3 $636, S4 $897
- **Results ($/1M successful — EC2 Production):** S1 $2.91, S2 $1.13, S3 $1.33, S4 $1.52
- **Interpretation Constraint:** These are analytical projections using experiment throughput/pod-count inputs mapped to production node sizing. NOT direct measurements from the stress harness (which used 400m allocatable per node).
- **Status:** ✅ Analysis complete — supports H3 cost discussion

### Claim 12c (Cost Crossover): fib(34) crossover occurs within experiment RPS band
- **Evidence:** `results/cost/2026-02-18_fib34-unified-aws-cost/report.md` §Crossover Points
- **Raw Data:** `results/cost/2026-02-18_fib34-unified-aws-cost/cost_results.json`, `results/cost/cost_crossover_rps.png`
- **Source Experiment:** `results/experiments/phase-b/2026-02-18_fib34-validation/`
- **Reproduce:**
  - `cd controller && HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python ../thesis/scripts/cost_analyzer.py --experiment-dir ../results/experiments/phase-b/2026-02-18_fib34-validation`
  - `cd controller && HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python ../thesis/scripts/cost_analyzer.py --crossover-graph`
- **Result:** S1 vs S2 crossover at ~65.9 RPS for fib(34), inside the observed ~50–73 RPS range; fib(32) crossover at ~97.9 RPS remains outside the band.
- **Status:** ✅ Validated — workload sensitivity shifts crossover into measurable range

### Claim 12d (Cost Fairness): Fairness-normalized metrics produced on updated pilot pipeline
- **Evidence:** `results/cost/2026-02-19_pilot-n2-unified-aws-cost/report.md`
- **Raw Data:** `results/cost/2026-02-19_pilot-n2-unified-aws-cost/cost_results.json`
- **Source Experiment:** `results/experiments/phase-b/2026-02-19_pilot-n2-validity-gates-rerun/`
- **Reproduce:** `cd controller && HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python ../thesis/scripts/cost_analyzer.py --experiment-dir /home/zahid/work/master-s2-study/thesis-kubernetes-serverless-integration/results/experiments/phase-b/2026-02-19_pilot-n2-validity-gates-rerun`
- **Result:** `$ / 1M requests` and `$ / 1M successful` are populated for all scenarios; pilot directional result shows S4 better than S3 on `$ / 1M successful`.
- **Status:** ✅ Validated for pipeline output (pilot n=2; not final inferential evidence)

### Claim 12e (Cost Model Correction): Serverless-specific execution-time sizing is applied to hybrid/serverless scenarios
- **Evidence:** `results/cost/2026-02-21_all-scenarios-rerun-v2-unified-aws-cost/report.md`
- **Raw Data:**
  - `results/cost/2026-02-21_all-scenarios-rerun-v2-unified-aws-cost/cost_results.json`
  - `results/experiments/phase-b/2026-02-21_all-scenarios-rerun-v2/results_final.json`
- **Source Experiment:** `results/experiments/phase-b/2026-02-21_all-scenarios-rerun-v2/`
- **Reproduce:** `cd controller && HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python ../thesis/scripts/cost_analyzer.py --experiment-dir /home/zahid/work/master-s2-study/thesis-kubernetes-serverless-integration/results/experiments/phase-b/2026-02-21_all-scenarios-rerun-v2`
- **Result:** Analyzer uses app-duration-informed execution sizing (`execution_time_source=app_duration_avg`) for S2/S3/S4. Reported totals per 1200s run: S1=$0.061, S2=$0.169, S3=$0.486, S4=$0.432; S4 < S3 after correction.
- **Interpretation Constraint:** n=1 per scenario; directional/pipeline-validating evidence, not final inferential ranking.
- **Status:** ✅ Validated for model behavior and reporting pipeline

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
| Cost Mechanism | Throttling cost multiplier | cost/2026-02-17_three-model-cost-comparison | ✅ Validated |
| Cost Projection | Production 3-model comparison | cost/2026-02-17_three-model-cost-comparison | ✅ Analysis complete |
| Cost Crossover | fib(34) crossover in observed band | cost/2026-02-18_fib34-unified-aws-cost | ✅ Validated |
| Cost Fairness Pipeline | Fairness-normalized outputs emitted | cost/2026-02-19_pilot-n2-unified-aws-cost | ✅ Validated (pilot) |
| Cost Model Correction | Serverless-specific execution sizing | cost/2026-02-21_all-scenarios-rerun-v2-unified-aws-cost | ✅ Validated (directional n=1) |

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

**Last Updated:** 2026-02-21 (cost-model correction + all-scenarios rerun-v2 evidence mapped)
