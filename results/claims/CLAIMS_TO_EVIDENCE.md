# Claims to Evidence Mapping

**Every thesis claim must trace to raw data and a reproduction command.**

**Performance numbers are drawn exclusively from `results/claims/FINAL_NUMBERS.md`, which cites only REGISTRY bundles with `role: final`.** See that file for exact figures and framing rules.

---

## H1: Hybrid Routing Mechanism

### Claim 1 (Mechanism): Dynamic weight shifting works
- **Evidence:** `results/experiments/phase-a1/2026-02-12_predictive-trigger/report.md` — Weight table: 100/0 → 90/10 → ... → 50/50
- **Registry ID:** `experiments.2026-02-12-predictive-trigger` (final)
- **Raw Data:** Decision log in report (captured from daemon at runtime)
- **Status:** ✅ Mechanism validated

### Claim 2 (Mechanism): Serverless backend engages under load
- **Evidence:** `results/experiments/phase-a1/2026-02-12_predictive-trigger/report.md` — Knative weight > 0 during high load
- **Registry ID:** `experiments.2026-02-12-predictive-trigger` (final)
- **Raw Data:** Same as Claim 1
- **Status:** ✅ Mechanism validated

### Claim 3 (Performance): S4 vs S1 latency comparison
- **Evidence:** `results/experiments/phase-b/2026-07-08_fib33_n5/report.md` (pre-proactive S1 and S4, n=5 each)
- **Registry ID:** `experiments.2026-07-08-fib33-n5` (final)
- **Raw Data:** Per-run HAProxy p99 latency in report tables
- **Result:** S1 mean p99 = 109.78 ms vs S4 mean p99 = 233.64 ms. S4 is significantly worse on p99 (Welch p = 0.0104, Cohen's d = 2.839, large effect). The +112.8% increase is attributable to localhost routing bias: on a single-node k3d testbed, hybrid routing adds overhead without the network-latency benefit of multi-node deployment.
- **Status:** ⚠️ Mechanism validated, superiority NOT established. This is a valid negative result with a clear confound (localhost bias). The routing mechanism shifts traffic as designed (Claims 1–2), but the localhost testbed cannot demonstrate a performance benefit for hybrid routing over pure K8s.

> **Superseded evidence:** Previous H1 performance claims cited `phase-b/2026-02-12_replicated-20runs` (Bugs 1–3), `phase-b/2026-02-14_clarknet-replay` (Bugs 4–7), and `phase-b/2026-02-15_clarknet-replay` (different controller/workload version). All are superseded by the July 2026 V3-controller fib33 runs. See "Superseded Evidence" section below.

---

## H2: Predictive Scaling Mechanism

### Claim 4 (Mechanism): PREDICTIVE action triggers before violation
- **Evidence:** `results/experiments/phase-a1/2026-02-12_predictive-trigger/report.md`
- **Registry ID:** `experiments.2026-02-12-predictive-trigger` (final)
- **Raw Data:** Decision log — action=PREDICTIVE at p99=146 ms, predicted 47% load increase, confidence 72%
- **Status:** ✅ Mechanism validated (Phase A1 ramp test)

### Claim 5 (Superiority): S4 reduces SLO violations vs S3
- **Evidence:** `results/experiments/phase-b/2026-07-08_fib33_proactive/report.md` (S3 and S4 with proactive routing, n=5 each)
- **Registry ID:** `experiments.2026-07-08-fib33-proactive` (final)
- **Raw Data:** Per-run p99 latency and SLO violation counts in report tables
- **Result (p99 latency):** S4 mean p99 = 187.90 ms vs S3 mean p99 = 309.54 ms → −39.3% reduction (Welch p = 0.1216, not significant at α=0.05; Cohen's d = −1.214, large effect).
- **Result (SLO violations):** S4 mean = 701.80 vs S3 mean = 2805.40 → −75.0% reduction (Welch p = 0.1247, not significant at α=0.05; Cohen's d = −1.215, large effect).
- **Reproduce:** See bundle meta and `scripts/run_phase_b_experiments.py` configuration for the proactive routing scenario set.
- **Status:** ⚠️ Mechanism validated, statistical superiority NOT established. The PREDICTIVE trigger fires (Claim 4), and the direction and magnitude of the effect are large (75% SLO reduction, d≈1.21), but with n=5 the difference is not statistically significant (p≈0.12). The thesis reports this as "large effect size (d=1.21) but not statistically significant (p=0.12, n=5)."

> **Superseded evidence:** Previous H2 claims cited `phase-b/2026-02-15_clarknet-replay` (reported p=0.0037, d=−2.96 for SLO reduction). That bundle used a different controller version, workload, and was discovered to have metric contamination issues. It is superseded by the July 2026 proactive bundle with the V3 controller.

---

## H3: GRU Prediction Adequacy

### Claim 6: RMSE below 10% target
- **Evidence (synthetic):** `results/models/gru/2026-02-10_training-synthetic/report.md`
- **Registry ID:** `models.2026-02-10-training-synthetic` (final)
- **Evidence (real traces):** `results/models/gru/2026-02-13_training-clarknet-calgary/report.md`
- **Registry ID:** `models.2026-02-13-training-clarknet-calgary` (final)
- **Results (synthetic):**
  - Test RMSE% = 6.01% manual tuning (target <10%) ✅
  - Test RMSE% = 4.75% post-HPO (target <10%) ✅
  - Test MAE% = 4.91% (target <5%) ✅
  - Inference latency ≈ 40 ms (target <50 ms) ✅
- **Results (real — ClarkNet 5-min, best):**
  - Test RMSE% = 17.78% (target <10%) ❌
  - Test MAE% = 14.48% (target <5%) ❌
  - MAPE = 18.74% ❌
- **Note:** GRU outperforms baselines on real data (baseline MAPE ~65% vs GRU 18.74%) but does not meet original thresholds. Gap is expected: real traces have non-stationarity and irregular bursts absent in synthetic data.
- **Status:** ⚠️ Partially validated — synthetic accuracy meets all targets; real-trace accuracy below target thresholds. Mechanism works on both; thresholds not met on real data.

### Claim 7: Live prediction latency acceptable
- **Evidence:** `results/experiments/phase-a1/2026-02-12_predictive-trigger/report.md`
- **Registry ID:** `experiments.2026-02-12-predictive-trigger` (final)
- **Result:** ~40 ms (target <50 ms)
- **Status:** ✅ Validated

### Claim 8: Confidence scores meaningful
- **Evidence:** `results/experiments/phase-a1/2026-02-12_predictive-trigger/report.md`
- **Registry ID:** `experiments.2026-02-12-predictive-trigger` (final)
- **Result:** Range 0.72–0.82 during live predictions
- **Status:** ✅ Validated

---

## Testbed Validity & Scenario Design Decisions

### Claim 9 (Testbed): HPA works correctly on k3d
- **Evidence:** `results/experiments/validation/2026-02-13_infrastructure-validation/report.md` — T2: scale 2→10 under load, 10→2 after cooldown
- **Status:** ✅ Validated — S1 can use native HPA as baseline

### Claim 10 (Design Decision): HPA and kubectl scale are mutually exclusive
- **Evidence:** `results/experiments/validation/2026-02-13_infrastructure-validation/report.md` — T3: HPA reverts kubectl scale changes
- **Status:** ✅ Validated — S3/S4 must delete HPA; Algorithm 2 owns replicas via kubectl scale

### Claim 11 (Testbed): Knative KPA autoscaling works on k3d
- **Evidence:** `results/experiments/validation/2026-02-13_infrastructure-validation/report.md` — T4: scale 1→7 under CPU-heavy load, scale-to-zero after 60s
- **Status:** ✅ Validated — S2 viable as Knative-only baseline

---

## Cost Analysis

> **Gap (2026-07-10 audit):** No cost bundle is marked `role: final` for the July 2026 fib33 experiments. The Feb 2026 cost bundles use a different controller version and workload profile; their numbers must not be mixed with July latency/SLO results. Cost discussion in Ch4 should note this gap or use Feb directional estimates with explicit caveats about controller-version mismatch.

### Claim 12a (Cost Mechanism): CPU throttling + concurrency creates hidden serverless cost multiplier
- **Evidence:** `results/cost/2026-02-17_three-model-cost-comparison/report.md` §Key Finding: CPU Throttling and Little's Law
- **Status:** ✅ Validated — mechanism insight about serverless cost drivers. Note: directional analysis from Feb controller version; not recomputed on July data.

### Claim 12b (Cost Projection): Production cost comparison under t3.medium sizing
- **Evidence:** `results/cost/2026-02-17_three-model-cost-comparison/report.md` §Model 3b
- **Status:** ⚠️ Directional analysis from Feb controller version. Not recomputed on July data. Use with explicit caveats.

### Claim 12c (Cost Crossover): fib(34) crossover occurs within experiment RPS band
- **Evidence:** `results/cost/2026-02-18_fib34-unified-aws-cost/report.md` §Crossover Points
- **Status:** ⚠️ Directional analysis from Feb controller version.

---

## Summary

| Type | Claim | Registry ID | Status |
|------|-------|-------------|--------|
| Mechanism | Weight shifting | `experiments.2026-02-12-predictive-trigger` | ✅ Mechanism validated |
| Mechanism | Serverless engagement | `experiments.2026-02-12-predictive-trigger` | ✅ Mechanism validated |
| Mechanism | PREDICTIVE trigger | `experiments.2026-02-12-predictive-trigger` | ✅ Mechanism validated |
| Mechanism | GRU inference (synthetic) | `models.2026-02-10-training-synthetic` | ✅ Validated (4.75% RMSE post-HPO) |
| Mechanism | GRU inference (real traces) | `models.2026-02-13-training-clarknet-calgary` | ⚠️ Mechanism works, targets not met |
| Performance (H1) | S4 vs S1 latency | `experiments.2026-07-08-fib33-n5` | ⚠️ Mechanism validated, superiority NOT established (S4 p99=233.6 vs S1 p99=109.8, localhost bias) |
| Performance (H2) | S4 fewer SLO violations than S3 | `experiments.2026-07-08-fib33-proactive` | ⚠️ Mechanism validated, large effect (d=1.21, −75% SLO) but NOT significant (p=0.12, n=5) |
| Performance (H2) | S4 p99 vs S3 p99 | `experiments.2026-07-08-fib33-proactive` | ⚠️ Large effect (d=1.21, −39.3%) but NOT significant (p=0.12, n=5) |
| Testbed | HPA works on k3d | validation/infrastructure-validation | ✅ |
| Design Decision | HPA vs kubectl scale exclusive | validation/infrastructure-validation | ✅ |
| Testbed | Knative KPA works on k3d | validation/infrastructure-validation | ✅ |
| Cost Mechanism | Throttling cost multiplier | cost/2026-02-17 (Feb directional) | ✅ Mechanism validated |
| Cost Projection | Production comparison | cost/2026-02-17 (Feb directional) | ⚠️ Not recomputed on July data |
| Cost Crossover | fib(34) crossover in observed band | cost/2026-02-18 (Feb directional) | ⚠️ Not recomputed on July data |

---

## Superseded Evidence (Audit Trail)

### Feb 2026 Phase B bundles — superseded by July 2026 finals

The following Feb 2026 experiment bundles were previously cited as primary performance evidence. They are **superseded** by the July 2026 V3-controller fib33 runs designated `role: final` in REGISTRY.yaml. Numbers from these bundles must NOT appear in thesis Ch4/Ch5/abstracts.

| Superseded bundle | Reason | Superseded by |
|---|---|---|
| `phase-b/2026-02-12_replicated-20runs` | Bugs 1–3 (SLO monitor wrong HAProxy column, priority order reversed, Prometheus not scraping daemon) | `experiments.2026-07-08-fib33-n5` |
| `phase-b/2026-02-14_clarknet-replay` | Bugs 4–7 (HAProxy server name mismatch, stale daemon, missing `_total` suffix, no invariant checks) | `experiments.2026-07-08-fib33-n5` |
| `phase-b/2026-02-15_clarknet-replay` | Different controller/workload version; metric contamination | `experiments.2026-07-08-fib33-n5` (H1) and `experiments.2026-07-08-fib33-proactive` (H2) |
| `phase-b/2026-02-16_validation-metrics-fixes` | Pre-V3 controller | `experiments.2026-07-08-fib33-n5` |
| `phase-b/2026-02-18_fib34-validation` | Pre-V3 controller, different workload | `experiments.2026-07-08-fib33-n5` |
| `phase-b/2026-02-19_pilot-n2-validity-gates-rerun` | Pilot n=2, pre-V3 controller | `experiments.2026-07-08-fib33-n5` |
| `phase-b/2026-02-21_all-scenarios-rerun-v2` | Pre-V3 controller, n=1 per scenario | `experiments.2026-07-08-fib33-n5` and `experiments.2026-07-08-fib33-proactive` |

### Feb 2026 bundles still final (different purpose, not superseded)

| Bundle | Registry ID | Why still final |
|---|---|---|
| `phase-a1/2026-02-12_predictive-trigger` | `experiments.2026-02-12-predictive-trigger` | Unique ramp test demonstrating PREDICTIVE mechanism; no July equivalent |
| `models/gru/2026-02-10_training-synthetic` | `models.2026-02-10-training-synthetic` | GRU synthetic training; no later retraining supersedes it |
| `models/gru/2026-02-13_training-clarknet-calgary` | `models.2026-02-13-training-clarknet-calgary` | GRU real-trace validation; no later retraining supersedes it |

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

### Full Phase B (July 2026 configuration)
```bash
HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python scripts/run_phase_b_experiments.py \
  --phase full --runs 5 --duration 300
```

---

## Training Data Note

- GRU trained on **synthetic data** → RMSE% 4.75% post-HPO, MAE% 4.91% ✅
- GRU retrained on **real ClarkNet/Calgary traces** (2026-02-13) → best RMSE% 17.78%, MAE% 14.48% ❌
- ClarkNet provides usable signal at 5-min+ aggregation; Calgary too sparse for GRU
- Real-data results are a known limitation to acknowledge in thesis

---

## Framing Rules for Thesis

1. **Never say** "proven", "hypothesis proven", "demonstrated superiority" for H1/H2.
2. **Use** "mechanism validated" for what works (weight shifting, PREDICTIVE trigger, GRU inference).
3. **Use** "large effect size (d=1.21) but not statistically significant (p=0.12, n=5)" for H2 SLO/p99 reduction.
4. **Use** "localhost routing bias limits interpretation" for H1 negative result.
5. **Use** "mechanism validated on synthetic data; real-trace accuracy below target thresholds" for H3 partial validation.

**Last Updated:** 2026-07-10
