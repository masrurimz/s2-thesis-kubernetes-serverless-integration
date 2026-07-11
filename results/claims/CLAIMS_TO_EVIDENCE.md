# Claims to Evidence Mapping

**Every thesis claim must trace to raw data and a reproduction command.**

**Performance numbers are drawn exclusively from `results/claims/FINAL_NUMBERS.md`, which cites the current baseline `results/experiments/phase-b/2026-07-11_scaling_fix_n1` (n=1 diagnostic).** See that file for exact figures and framing rules.

> **Infrastructure reset (2026-07-11):** Six infrastructure bugs (Bugs 8–13) invalidated ALL previous experiment bundles (Feb 2026 phase-b, July 2026 `2026-07-08-*` and `2026-07-10_*`). Every evidence reference below that predates the 2026-07-11 baseline is marked **⚠️ Superseded by Bugs 8-13. See INCONSISTENCIES.md 2026-07-11 entry.** The only current performance baseline is `2026-07-11_scaling_fix_n1` (n=1 diagnostic; n=5 replication pending for statistical significance). Registry ID (pending audit): `experiments.2026-07-11-scaling-fix-n1`.

---

## H1: Hybrid Routing Mechanism

### Claim 1 (Mechanism): Dynamic weight shifting works
- **Evidence:** `results/experiments/phase-a1/2026-02-12_predictive-trigger/report.md` — Weight table: 100/0 → 90/10 → ... → 50/50
- **⚠️ Superseded by Bugs 8-13. See INCONSISTENCIES.md 2026-07-11 entry.**
- **Registry ID:** `experiments.2026-02-12-predictive-trigger` (superseded; mechanism demo not recomputed on fixed infra)
- **Raw Data:** Decision log in report (captured from daemon at runtime)
- **Status:** ✅ Mechanism validated (pre-fix infra)

### Claim 2 (Mechanism): Serverless backend engages under load
- **Evidence:** `results/experiments/phase-a1/2026-02-12_predictive-trigger/report.md` — Knative weight > 0 during high load
- **⚠️ Superseded by Bugs 8-13. See INCONSISTENCIES.md 2026-07-11 entry.**
- **Registry ID:** `experiments.2026-02-12-predictive-trigger` (superseded; mechanism demo not recomputed on fixed infra)
- **Raw Data:** Same as Claim 1
- **Status:** ✅ Mechanism validated (pre-fix infra)

### Claim 3 (Performance): S4 vs S1 latency comparison
- **Evidence:** `results/experiments/phase-b/2026-07-11_scaling_fix_n1/report.md` (n=1 diagnostic, current baseline)
- **Registry ID:** `experiments.2026-07-11-scaling-fix-n1` (current baseline; n=5 replication pending)
- **Raw Data:** Per-run HAProxy p99 latency and SLO violation counts in report tables
- **Result (p99 latency):** S4 p99 = 118 ms vs S1 p99 = 2,421 ms → **−95.1%** improvement.
- **Result (SLO violations):** S4 = 104 vs S1 = 6,717 → **−98.5%** reduction (0.12% vs 7.66% SLO rate).
- **Why this differs from the old "localhost bias" negative result:** the previous H1 finding (S4 worse than S1) was an artifact of Bugs 8 and 11 — node CPU limits were never enforced (pods got the full 16-core host) and S1's HPA provisioned dynamic nodes (4.0 CPU vs S3/S4's 2.0 CPU), so S1 never saturated. With `--cpus=1.0` per node enforced and `max_k8s_replicas=6` capped to schedulable capacity, S1 saturates as designed and hybrid routing (S4) provides a clear performance benefit.
- **Status:** ✅ CONFIRMED (n=1). S4 beats S1 by 95.1% on p99 and 98.5% on SLO violations. n=5 replication pending for statistical significance.

> **Superseded evidence:** Previous H1 performance claims cited `phase-b/2026-07-08_fib33_n5` (reported S4 p99=233.6 ms vs S1 p99=109.8 ms, "localhost bias" negative result) and the Feb 2026 bundles (`phase-b/2026-02-12_replicated-20runs` Bugs 1–3, `phase-b/2026-02-14_clarknet-replay` Bugs 4–7, `phase-b/2026-02-15_clarknet-replay`, `phase-b/2026-02-16_*`, `phase-b/2026-02-18_*`, `phase-b/2026-02-19_*`, `phase-b/2026-02-21_*`). All are **⚠️ Superseded by Bugs 8-13. See INCONSISTENCIES.md 2026-07-11 entry.**

---

## H2: Predictive Scaling Mechanism

### Claim 4 (Mechanism): PREDICTIVE action triggers before violation
- **Evidence:** `results/experiments/phase-a1/2026-02-12_predictive-trigger/report.md`
- **⚠️ Superseded by Bugs 8-13. See INCONSISTENCIES.md 2026-07-11 entry.**
- **Registry ID:** `experiments.2026-02-12-predictive-trigger` (superseded; mechanism demo not recomputed on fixed infra)
- **Raw Data:** Decision log — action=PREDICTIVE at p99=146 ms, predicted 47% load increase, confidence 72%
- **Status:** ✅ Mechanism validated (Phase A1 ramp test, pre-fix infra). Note: the 2026-07-11 baseline confirms 9 PREDICTIVE actions fired in S4 during the n=1 run.

### Claim 5 (Superiority): S4 reduces SLO violations vs S3
- **Evidence:** `results/experiments/phase-b/2026-07-11_scaling_fix_n1/report.md` (n=1 diagnostic, current baseline)
- **Registry ID:** `experiments.2026-07-11-scaling-fix-n1` (current baseline; n=5 replication pending)
- **Raw Data:** Per-run p99 latency, SLO violation counts, serverless request counts, and monthly cost projection in report tables
- **Result (p99 latency):** S4 p99 = 118 ms vs S3 p99 = 99 ms → +19.7% (S4 worse).
- **Result (SLO violations):** S4 = 104 vs S3 = 3 (S4 worse; both near-zero SLO rate: 0.12% vs 0.00%).
- **Result (serverless dependency):** S4 = 2,666 serverless requests vs S3 = 5,354 → **−50.2%** (S4 better).
- **Result (monthly cost):** S4 = $142/mo vs S3 = $147/mo → **−3.4%** (~$5/mo cheaper; S4 better).
- **Reproduce:** See the canonical reproduction command in "Reproduction Commands" below.
- **Status:** ⚠️ PARTIAL (n=1). S4 provides a **cost advantage** (50% less serverless dependency, ~$5/mo cheaper) but **not a latency advantage** (p99 19% higher than S3). Both scenarios keep the SLO violation rate near zero. n=5 replication pending.
- **Architecture change (Bug 13 fix):** Prediction now drives **K8s SCALING** (Algorithm 2 proactive replicas via trend extrapolation), **not serverless ROUTING**. Routing weight uses ACTUAL load only. This separation ensures S4 never routes more to serverless than S3 (eliminating unnecessary Knative overhead), while still benefiting from prediction via earlier K8s scaling — which is why S4's serverless share (24.7%) is lower than S3's (31.8%).

> **Superseded evidence:** Previous H2 claims cited `phase-b/2026-07-08_fib33_proactive` (reported d=−1.21, p=0.12; prediction-for-routing architecture) and `phase-b/2026-02-15_clarknet-replay` (reported p=0.0037, d=−2.96; different controller/workload, metric contamination). All are **⚠️ Superseded by Bugs 8-13. See INCONSISTENCIES.md 2026-07-11 entry.**

---

## H3: GRU Prediction Adequacy

### Claim 6: RMSE below 10% target
- **Evidence (synthetic):** `results/models/gru/2026-02-10_training-synthetic/report.md`
- **⚠️ Superseded by Bugs 8-13. See INCONSISTENCIES.md 2026-07-11 entry.** (Model training itself is infra-independent; flagged because live prediction behavior was not re-validated on the fixed experiment stack.)
- **Registry ID:** `models.2026-02-10-training-synthetic` (superseded)
- **Evidence (real traces):** `results/models/gru/2026-02-13_training-clarknet-calgary/report.md`
- **⚠️ Superseded by Bugs 8-13. See INCONSISTENCIES.md 2026-07-11 entry.**
- **Registry ID:** `models.2026-02-13-training-clarknet-calgary` (superseded)
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
- **⚠️ Superseded by Bugs 8-13. See INCONSISTENCIES.md 2026-07-11 entry.**
- **Registry ID:** `experiments.2026-02-12-predictive-trigger` (superseded; mechanism demo not recomputed on fixed infra)
- **Result:** ~40 ms (target <50 ms)
- **Status:** ✅ Validated (pre-fix infra)

### Claim 8: Confidence scores meaningful
- **Evidence:** `results/experiments/phase-a1/2026-02-12_predictive-trigger/report.md`
- **⚠️ Superseded by Bugs 8-13. See INCONSISTENCIES.md 2026-07-11 entry.**
- **Registry ID:** `experiments.2026-02-12-predictive-trigger` (superseded; mechanism demo not recomputed on fixed infra)
- **Result:** Range 0.72–0.82 during live predictions
- **Status:** ✅ Validated (pre-fix infra)

---

## Testbed Validity & Scenario Design Decisions

### Claim 9 (Testbed): HPA works correctly on k3d
- **Evidence:** `results/experiments/validation/2026-02-13_infrastructure-validation/report.md` — T2: scale 2→10 under load, 10→2 after cooldown
- **⚠️ Superseded by Bugs 8-13. See INCONSISTENCIES.md 2026-07-11 entry.** (Validated on unlimited-CPU nodes pre-Bug-8 fix.)
- **Status:** ⚠️ Mechanism behavior still holds, but the scale-2→10 range is no longer reachable — `max_k8s_replicas=6` (Bug 11 fix) caps HPA at schedulable capacity.

### Claim 10 (Design Decision): HPA and kubectl scale are mutually exclusive
- **Evidence:** `results/experiments/validation/2026-02-13_infrastructure-validation/report.md` — T3: HPA reverts kubectl scale changes
- **⚠️ Superseded by Bugs 8-13. See INCONSISTENCIES.md 2026-07-11 entry.**
- **Status:** ✅ Validated — S3/S4 must delete HPA; Algorithm 2 owns replicas via kubectl scale

### Claim 11 (Testbed): Knative KPA autoscaling works on k3d
- **Evidence:** `results/experiments/validation/2026-02-13_infrastructure-validation/report.md` — T4: scale 1→7 under CPU-heavy load, scale-to-zero after 60s
- **⚠️ Superseded by Bugs 8-13. See INCONSISTENCIES.md 2026-07-11 entry.**
- **Status:** ✅ Validated — S2 viable as Knative-only baseline

---

## Cost Analysis

> **Updated (2026-07-11):** Production cost projections now come from `FINAL_NUMBERS.md` (n=1 baseline `2026-07-11_scaling_fix_n1`): S1=$132/mo, S2=$394/mo, S3=$147/mo, S4=$142/mo. The Feb 2026 cost bundles below remain directional only (different controller version/workload) and are superseded for thesis Ch4/Ch5 figures.

### Claim 12a (Cost Mechanism): CPU throttling + concurrency creates hidden serverless cost multiplier
- **Evidence:** `results/cost/2026-02-17_three-model-cost-comparison/report.md` §Key Finding: CPU Throttling and Little's Law
- **⚠️ Superseded by Bugs 8-13. See INCONSISTENCIES.md 2026-07-11 entry.**
- **Status:** ⚠️ Directional mechanism insight (Feb controller version); not recomputed on July fixed-infra data.

### Claim 12b (Cost Projection): Production cost comparison under t3.medium sizing
- **Evidence:** `results/cost/2026-02-17_three-model-cost-comparison/report.md` §Model 3b
- **⚠️ Superseded by Bugs 8-13. See INCONSISTENCIES.md 2026-07-11 entry.**
- **Status:** ⚠️ Directional analysis (Feb controller version). Use the `2026-07-11_scaling_fix_n1` cost figures in `FINAL_NUMBERS.md` for thesis numbers.

### Claim 12c (Cost Crossover): fib(34) crossover occurs within experiment RPS band
- **Evidence:** `results/cost/2026-02-18_fib34-unified-aws-cost/report.md` §Crossover Points
- **⚠️ Superseded by Bugs 8-13. See INCONSISTENCIES.md 2026-07-11 entry.**
- **Status:** ⚠️ Directional analysis (Feb controller version). Not recomputed on July fixed-infra data.

---

## Summary

| Type | Claim | Registry ID | Status |
|------|-------|-------------|--------|
| Mechanism | Weight shifting | `experiments.2026-02-12-predictive-trigger` | ✅ Mechanism validated (superseded — pre-fix infra) |
| Mechanism | Serverless engagement | `experiments.2026-02-12-predictive-trigger` | ✅ Mechanism validated (superseded — pre-fix infra) |
| Mechanism | PREDICTIVE trigger | `experiments.2026-02-12-predictive-trigger` | ✅ Mechanism validated (superseded — pre-fix infra) |
| Mechanism | GRU inference (synthetic) | `models.2026-02-10-training-synthetic` | ⚠️ Mechanism works, real-trace targets not met (superseded) |
| Mechanism | GRU inference (real traces) | `models.2026-02-13-training-clarknet-calgary` | ⚠️ Mechanism works, targets not met (superseded) |
| Performance (H1) | S4 vs S1 latency | `experiments.2026-07-11-scaling-fix-n1` | ✅ CONFIRMED (n=1): S4 beats S1 by 95.1% on p99 (118 vs 2,421 ms); n=5 pending |
| Performance (H2) | S4 vs S3 (cost/serverless) | `experiments.2026-07-11-scaling-fix-n1` | ⚠️ PARTIAL (n=1): S4 cheaper ($142 vs $147, −50% serverless) but p99 +19.7% vs S3; n=5 pending |
| Testbed | HPA works on k3d | validation/infrastructure-validation | ⚠️ Superseded (scale range now capped at 6) |
| Design Decision | HPA vs kubectl scale exclusive | validation/infrastructure-validation | ✅ (superseded — pre-fix infra) |
| Testbed | Knative KPA works on k3d | validation/infrastructure-validation | ✅ (superseded — pre-fix infra) |
| Cost Mechanism | Throttling cost multiplier | cost/2026-02-17 (Feb directional) | ⚠️ Superseded (Feb directional) |
| Cost Projection | Production comparison | cost/2026-02-17 (Feb directional) | ⚠️ Superseded (Feb directional; use 2026-07-11 figures) |
| Cost Crossover | fib(34) crossover in observed band | cost/2026-02-18 (Feb directional) | ⚠️ Superseded (Feb directional) |

---

## Superseded Evidence (Audit Trail)

> **All pre-2026-07-11 experiment bundles are superseded by Bugs 8–13.** The current baseline is `2026-07-11_scaling_fix_n1` (n=1 diagnostic; n=5 replication pending). Numbers from superseded bundles must NOT appear in thesis Ch4/Ch5/abstracts. See `INCONSISTENCIES.md` 2026-07-11 entry for the six bugs and their fixes.

### July 2026 Phase B bundles — superseded by the 2026-07-11 scaling-fix baseline (Bugs 8-13)

These bundles were previously designated `role: final` but are invalidated by the six infrastructure bugs (node CPU limits never applied, r_saturation miscalibrated, calibration tooling broken, S1 dynamic-node unfairness, GRU server died mid-run, prediction used for routing instead of scaling).

| Superseded bundle | Registry ID | Reason |
|---|---|---|
| `phase-b/2026-07-08_fib33_n5` | `experiments.2026-07-08-fib33-n5` | Bugs 8, 11 — unlimited CPU + S1 dynamic nodes → "localhost bias" negative result was an artifact |
| `phase-b/2026-07-08_fib33_proactive` | `experiments.2026-07-08-fib33-proactive` | Bugs 8, 13 — prediction-for-routing architecture over-routed to serverless; numbers invalidated |
| `phase-b/2026-07-08_fib33`, `2026-07-08_fib33_v2`, `2026-07-08_pipefix`, `2026-07-08_s2-pipefix` | `experiments.2026-07-08-*` | Bugs 8–13 — pre-fix infrastructure |
| `phase-b/2026-07-10_*` | `experiments.2026-07-10-*` | Bugs 8–13 — pre-fix infrastructure |
| All `phase-b/2026-07-03` through `2026-07-07_*` intermediate/smoke bundles | `experiments.2026-07-0[3-7]-*` | Bugs 8–13 — pre-fix infrastructure |

### Feb 2026 Phase B bundles — superseded (Bugs 1-7, then again by Bugs 8-13)

| Superseded bundle | Reason | Superseded by |
|---|---|---|
| `phase-b/2026-02-12_replicated-20runs` | Bugs 1–3 (SLO monitor wrong HAProxy column, priority order reversed, Prometheus not scraping daemon) | `2026-07-11_scaling_fix_n1` |
| `phase-b/2026-02-14_clarknet-replay` | Bugs 4–7 (HAProxy server name mismatch, stale daemon, missing `_total` suffix, no invariant checks) | `2026-07-11_scaling_fix_n1` |
| `phase-b/2026-02-15_clarknet-replay` | Different controller/workload version; metric contamination | `2026-07-11_scaling_fix_n1` |
| `phase-b/2026-02-16_validation-metrics-fixes` | Pre-V3 controller | `2026-07-11_scaling_fix_n1` |
| `phase-b/2026-02-18_fib34-validation` | Pre-V3 controller, different workload | `2026-07-11_scaling_fix_n1` |
| `phase-b/2026-02-19_pilot-n2-validity-gates-rerun` | Pilot n=2, pre-V3 controller | `2026-07-11_scaling_fix_n1` |
| `phase-b/2026-02-21_all-scenarios-rerun-v2` | Pre-V3 controller, n=1 per scenario | `2026-07-11_scaling_fix_n1` |

### Pre-fix bundles still referenced (mechanism / model only)

These remain the only demonstrations of their respective mechanisms, but their numbers were captured on pre-Bugs-8-13 infrastructure and are not recomputed on the fixed stack.

| Bundle | Registry ID | Why still referenced |
|---|---|---|
| `phase-a1/2026-02-12_predictive-trigger` | `experiments.2026-02-12-predictive-trigger` | Unique ramp test demonstrating PREDICTIVE mechanism; no post-fix equivalent yet |
| `models/gru/2026-02-10_training-synthetic` | `models.2026-02-10-training-synthetic` | GRU synthetic training; infra-independent, no later retraining |
| `models/gru/2026-02-13_training-clarknet-calgary` | `models.2026-02-13-training-clarknet-calgary` | GRU real-trace validation; no later retraining |
| `validation/2026-02-13_infrastructure-validation` | `validation/*` | HPA/KPA testbed validation; superseded by Bug 8/11 fixes but no post-fix re-validation exists |

---

## Reproduction Commands

All experiment scenarios (S1–S4) are reproduced with the unified `thesis` CLI:

```bash
thesis infra apply-resources && thesis infra deploy-app && thesis infra verify && thesis-experiment run --runs 5 --duration 300
```

- `thesis infra apply-resources` — enforces Docker `--cpus=1.0` per workload node (Bug 8 fix) and applies the HPA `max_k8s_replicas=6` capacity cap (Bug 11 fix).
- `thesis infra deploy-app` — deploys the controller, prediction (GRU) server, and Knative services.
- `thesis infra verify` — preflight readiness, including GRU server health (Bug 12 mitigation).
- `thesis-experiment run --runs 5 --duration 300` — runs the S1–S4 scenario suite at n=5 replication of the n=1 diagnostic baseline (`2026-07-11_scaling_fix_n1`).

This single command reproduces H1 (S4 vs S1), H2 (S4 vs S3), and the live-prediction evidence (H3 Claims 7–8, exercised by S4's PREDICTIVE actions). For standalone GRU model evaluation (H3 Claim 6), see the model training reports under `results/models/gru/`.

---

## Training Data Note

- GRU trained on **synthetic data** → RMSE% 4.75% post-HPO, MAE% 4.91% ✅
- GRU retrained on **real ClarkNet/Calgary traces** (2026-02-13) → best RMSE% 17.78%, MAE% 14.48% ❌
- ClarkNet provides usable signal at 5-min+ aggregation; Calgary too sparse for GRU
- Real-data results are a known limitation to acknowledge in thesis

---

## Framing Rules for Thesis

1. **H1 (hybrid vs pure K8s):** "Confirmed (n=1): S4 beats S1 by 95.1% on p99 (118 ms vs 2,421 ms) and 98.5% on SLO violations. n=5 replication pending for statistical significance." Do NOT say "proven" (n=1).
2. **H2 (predictive vs reactive):** "Partial (n=1): S4 provides a cost advantage (~50% fewer serverless requests, $142 vs $147/mo) but not a latency advantage (p99 +19.7% vs S3). Both keep SLO rate near zero. Architecture change: prediction drives K8s scaling, not serverless routing."
3. **Use** "mechanism validated" for what works (weight shifting, PREDICTIVE trigger, GRU inference).
4. **Use** "mechanism validated on synthetic data; real-trace accuracy below target thresholds" for H3 partial validation.
5. **All pre-2026-07-11 experiment numbers are superseded (Bugs 8-13).** Cite ONLY `results/claims/FINAL_NUMBERS.md`.
6. The old framings — "localhost routing bias limits interpretation" (H1) and "large effect size (d=1.21) but not statistically significant (p=0.12, n=5)" (H2) — referred to the now-superseded `2026-07-08` bundles and must NOT be used.

**Last Updated:** 2026-07-11
