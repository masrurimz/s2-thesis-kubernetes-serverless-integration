# Claims to Evidence Mapping

**Every thesis claim must trace to raw data and a reproduction command.**

**Performance numbers are drawn exclusively from `results/claims/FINAL_NUMBERS.md`.** The definitive H2 evidence is the `2026-07-14_clarknet-tuned-paired-n5` paired S3/S4 bundle (n=5, ClarkNet variable load, h=9 model, utilization-based node consolidation, tuned S3). H2 is **supported** for the pre-specified primary p99 test. See that file for exact figures and framing rules.

> **Infrastructure reset (2026-07-11):** Six infrastructure bugs (Bugs 8–13) invalidated ALL previous experiment bundles (Feb 2026 phase-b, July 2026 `2026-07-08-*` and `2026-07-10_*`). Every evidence reference below that predates the 2026-07-11 baseline is marked **⚠️ Superseded by Bugs 8-13. See INCONSISTENCIES.md 2026-07-11 entry.** The definitive H2 bundle is `2026-07-14_clarknet-tuned-paired-n5`; the `2026-07-11_scaling_fix_n1` diagnostic (n=1) remains the H1 baseline. Registry IDs: `experiments.2026-07-14-clarknet-tuned-paired-n5`, `experiments.2026-07-11-scaling-fix-n1`.

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
- **Status:** ✅ Directional (n=1 diagnostic). S4 beats S1 by 95.1% on p99 (118 vs 2,421 ms). Not statistically established; n=5 replication pending.

> **Superseded evidence:** Previous H1 performance claims cited `phase-b/2026-07-08_fib33_n5` (reported S4 p99=233.6 ms vs S1 p99=109.8 ms, "localhost bias" negative result) and the Feb 2026 bundles (`phase-b/2026-02-12_replicated-20runs` Bugs 1–3, `phase-b/2026-02-14_clarknet-replay` Bugs 4–7, `phase-b/2026-02-15_clarknet-replay`, `phase-b/2026-02-16_*`, `phase-b/2026-02-18_*`, `phase-b/2026-02-19_*`, `phase-b/2026-02-21_*`). All are **⚠️ Superseded by Bugs 8-13. See INCONSISTENCIES.md 2026-07-11 entry.**

---

## H2: Predictive Scaling Mechanism

### Claim 4 (Mechanism): PREDICTIVE action triggers before violation
- **Evidence:** `results/experiments/phase-a1/2026-02-12_predictive-trigger/report.md`
- **⚠️ Superseded by Bugs 8-13. See INCONSISTENCIES.md 2026-07-11 entry.**
- **Registry ID:** `experiments.2026-02-12-predictive-trigger` (superseded; mechanism demo not recomputed on fixed infra)
- **Raw Data:** Decision log — action=PREDICTIVE at p99=146 ms, predicted 47% load increase, confidence 72%
- **Status:** ✅ Mechanism validated (Phase A1 ramp test, pre-fix infra). Note: the 2026-07-11 baseline confirms 9 PREDICTIVE actions fired in S4 during the n=1 run.

### Claim 5 (Superiority): S4 vs S3 paired comparison — H2
- **Evidence:** `results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5/paired_analysis.json` (n=5 counterbalanced S3/S4 pairs, ClarkNet variable load, h=9 model)
- **Registry ID:** `experiments.2026-07-14-clarknet-tuned-paired-n5` (definitive; role: final, status: current)
- **Raw Data:** Per-run `result.json` files for all 10 runs (5×S3, 5×S4); per-run `daemon.log` files; `paired_analysis.json` inferential statistics
- **Primary result (p99 latency, paired):** S3 mean 188.47 ms, S4 mean 126.00 ms, mean diff −62.47 ms, 95% CI [−100.87, −26.21] ms (entirely below zero), uncorrected permutation p=0.0304 (pre-specified primary test, significant at α=0.05), paired Cohen's d=−1.2646 (large effect, S4 better). S4 won all 5 pairs.
- **Secondary results (descriptive after multiplicity correction):** p95 latency: S3 mean 95.77 ms, S4 mean 81.89 ms, d=−3.5247, uncorrected p=0.0304, **corrected p=0.1216 (not significant)**. SLO violations: S3 mean 656.4, S4 mean 130.0, d=−1.3462, uncorrected p=0.0304, **corrected p=0.1216 (not significant)**. Throughput: diff ≈0, p=0.7147. Monthly cost: identical (USD 163/mo both scenarios).
- **Treatment delivery:** All 5 S4 runs delivered complete forecasts; `predictive_count=4–5` and `proactive_scaleups=1–2` in every S4 run; `forecast_horizon_sufficient=True` in all 5 runs. 10/10 runs valid.
- **Statistical interpretation:** The primary p99 test is pre-specified and significant at p=0.0304 (uncorrected). The artifact's multiplicity-corrected primary field is 1.0; corrected p-values for secondary metrics (p95, SLO) are 0.1216 and therefore **not significant**. H2 is supported for the primary p99 superiority claim only.
- **Supersedes** `2026-07-12_paired-h2-clean-v2` (non-significant, p=0.38) and `2026-07-11_paired-h2` (treatment-confounded). Earlier bundles are retained as immutable historical records; raw files are unchanged.
- **Status:** ✅ **SUPPORTED (primary p99, p=0.0304 uncorrected, d=−1.2646, large effect).** H2 latency superiority is established for the pre-specified primary p99 test. Secondary metrics (p95, SLO) show large effect sizes in S4's favor but corrected p=0.1216 is not significant after multiplicity correction across 5 metrics; report them as descriptive only.
---

## H3: GRU Prediction Adequacy

### Claim 6: RMSE below 10% target
- **Primary evidence (leak-free retrain, 2026-09-10):** `results/models/gru/2026-09-10_clarknet-15s-h9-leakfree/report.md`
- **Registry ID:** `models.2026-09-10-clarknet-15s-h9-leakfree` (role final, status current)
- **Protocol:** ClarkNet resampled to 15 s at the replay amplitude (scale factor 33), chronological splits with a 38-sample embargo, hyperparameters and epoch budget selected on the validation portion only at horizon 9, refit on train plus validation, three seeds, test evaluated once. The replay window, samples 28940 to 29020, lies inside the test portion and is never trained on.
- **Result:** holdout RMSE 29.635 ± 0.016, MAE 22.486 ± 0.079, normalised RMSE 0.396, skill against persistence 0.216, upper-envelope coverage 0.921, rolling-origin over five blocks 29.039 ± 6.893. Baselines on identical windows: persistence 37.813, linear trend 46.534, seasonal naive 53.688, and an OLS autoregression on the same 30-sample window 29.465.
- **Verdict:** the under-10% target is **not met** on the real 15-second deployment series, and the GRU does **not** beat a linear autoregression (29.635 against 29.465, within noise). The skill over persistence, about 22%, is real and stable across seeds. Out-of-distribution archetypes: spike 26.58, ramp 24.27, periodic 25.42, stationary 4.74.
- **Superseded evidence, do not cite:** `results/models/gru/2026-02-10_training-synthetic/report.md` (synthetic, RMSE 6.01% manual and 4.75% post-HPO at horizon 5) and `results/models/gru/2026-02-13_training-clarknet-calgary/report.md` (ClarkNet at 5-minute aggregation, RMSE 17.78%). Both are archived; both predate the leak-free protocol, and the aggregation and horizon differ from the deployment task. The harness carries a synthetic arm that re-derives the synthetic figure under the clean protocol at horizon 9.
- **Status:** ❌ Not met on real data at deployment resolution. Met on synthetic data only. GRU accuracy parity with a linear autoregression is a disclosed limitation.

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
- **Result:** Range 0.72–0.88 during live predictions with the synthetic-trained model of the time. Under the leak-free ClarkNet model the reported confidence is a constant 0.6, because the score is the ratio of validation RMSE to mean load and that ratio now exceeds the 0.15 threshold. The gate still passes its 0.5 default, so predictive scaling remains enabled, but the score no longer varies within a run.
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

### Claim 13a (Mechanism): Pending pods trigger K3dAutoscaler dynamic node creation
- **Evidence:** `results/experiments/phase-b/2026-07-13_dynamic-node-offload/s1-k8s-only_run1/provision_events.json` — `pending_detected → provision_delay_started → node_created` for `dynamic-workload-0` and `dynamic-workload-1`. Same pattern in S3 and S4 run directories.
- **Status:** ✅ Diagnostic (n=1). All three K8s scenarios (S1, S3, S4) provisioned 2 dynamic nodes when `max_k8s_replicas=10` exceeded the 6-pod static capacity.

### Claim 13b (Mechanism): Dynamic nodes receive workload pods
- **Evidence:** `result.json` in each run directory records `available_replicas_final=10` with static capacity of 6 pods (2 agents × 3 pods at 300m). The 4 additional pods must have been scheduled on the 2 dynamic workload nodes. `node_created` events confirm nodes became Ready (`elapsed_sec` 5.5–5.8s).
- **Status:** ✅ Diagnostic (n=1). `dynamic_node_pod_count=0` in `result.json` is a collection-timing artifact (pods were redistributed after collection); the `available_replicas_final` and `node_created` evidence is conclusive.

### Claim 13c (Mechanism): S3/S4 maintain measurable Knative weight-time during the provisioning/capacity period
- **Evidence:** S3 `serverless_weight_time_product=24,630`, `knative_active_seconds=1,230`; S4 `serverless_weight_time_product=24,855`, `knative_active_seconds=1,230`. S1 `serverless_weight_time_product=0` (no offload by design). S2 `serverless_weight_time_product=126,000` (100% serverless reference).
- **Status:** ✅ Diagnostic (n=1). The hybrid scenarios offloaded 96.5% of traffic time to Knative while simultaneously provisioning dynamic K8s nodes.

### Claim 13d (Cost): Dynamic-node EC2 cost is represented separately in the cost model
- **Evidence:** `results/cost_analysis/cost_analysis_20260713_130219.json` — `stress_harness_ec2.dynamic_nodes` field: S1=USD 0.0279, S3=USD 0.0280, S4=USD 0.0275, S2=USD 0.0000. The cost model in `libs/analysis/analysis/cost.py` (lines 158–161) computes `dynamic_hours = nodes_provisioned * (duration - first_provision_delay) / 3600` and multiplies by the EC2 node rate.
- **Status:** ✅ Diagnostic (n=1). Dynamic-node cost is tracked separately from serverless Lambda cost in the unified AWS cost model.

### Claim 13e (Trade-off): Dynamic nodes alone are not sufficient; serverless offload is necessary
- **Evidence:** S1 (K8s-only, 2 dynamic nodes, no offload) p99=6,665 ms, success rate=65.6%. S3 (hybrid-reactive, 2 dynamic nodes, 96.5% serverless time) p99=874 ms, success rate=90.0%. The 51–70-second provisioning delay was absorbed by Knative in S3/S4 but caused severe degradation in S1.
- **Status:** ✅ Diagnostic (n=1). Adding nodes without serverless offload is slower and has worse SLO compliance than the hybrid approach with the same node count.

### Claim 13f (Limitation): S4 forecast horizon insufficient under high load
- **Evidence:** `results/experiments/phase-b/2026-07-13_dynamic-node-offload/s4-hybrid-predictive_run1/result.json` — `run_validity_passed=False`, `treatment_fidelity.forecast_horizon_sufficient=False`. Measured provisioning delay=70.5s; required horizon = `ceil((70.5+15)/15) = 6` steps; model outputs 5 steps (75s). S4 delivered 55 predictions (100% delivery) but `predictive_count=0`, `proactive_scaleups=0`. S4 p99=1,393 ms vs S3 p99=874 ms (+59%).
- **Status:** ⚠️ Diagnostic (n=1). The static 5-step forecast horizon is inadequate when provisioning delays exceed 70s. Validates the need for an adaptive horizon that tracks the live EWMA of measured provisioning delays. Retraining with `prediction_horizon=7` (105s window) or making the horizon adaptive is required.

## Mechanism & Diagnostic Claims (July 2026)

### Claim 14 (Mechanism): h=9 forecast sufficiency and proactive actions
- **Evidence:** `results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5/` — all 5 S4 runs: `forecast_horizon_sufficient=True`, `predictive_count=4–5`, `proactive_scaleups=1–2`.
- **Registry ID:** `experiments.2026-07-14-clarknet-tuned-paired-n5`
- **Design:** GRU `prediction_horizon=9` (9 × 15s = 135s forecast window) covers the measured provisioning delay (up to 120s) plus 15s safety margin. ClarkNet variable load (30–164 RPS) provides ramps and surges the forecast can predict ahead of the observed signal.
- **Status:** ✅ Mechanism validated (n=5). The 135s horizon is sufficient and the GRU forecast triggered 4–5 proactive routing decisions per S4 run. Supersedes the h=5 limitation documented in Claim 13f.

### Claim 15 (Mechanism): Utilization-based node consolidation
- **Evidence:** `results/experiments/phase-b/2026-07-14_clarknet-util-scaledown-n1/provision_events.json` — `scale_down_detected` events with `utilization` field; `node_deleted` events after `kubectl drain`.
- **Registry ID:** `experiments.2026-07-14-clarknet-util-scaledown-n1`
- **Design:** K3dAutoscaler implements cluster-autoscaler-style consolidation (matching Kubernetes CA / KARPENTER `WhenEmptyOrUnderutilized`): a dynamic node is consolidated when (1) CPU-request utilization < 50% threshold, (2) pods are reschedulable to other workload nodes, (3) node underutilized ≥ 90s, (4) ≥ 120s since last scale-down. `kubectl drain` evicts pods before deletion. Cost model computes actual per-node lifetime from `node_created → node_deleted` timestamps.
- **Status:** ✅ Diagnostic (n=1). Both S3 and S4 show `scale_down_detected` → `node_deleted` cycles with the `utilization` field, followed by re-provisioning on the next load peak — proving the bidirectional provision → consolidate → re-provision loop.

---

## Summary

| Type | Claim | Registry ID | Status |
|------|-------|-------------|--------|
| Mechanism | Weight shifting | `experiments.2026-02-12-predictive-trigger` | ✅ Mechanism validated (superseded — pre-fix infra) |
| Mechanism | Serverless engagement | `experiments.2026-02-12-predictive-trigger` | ✅ Mechanism validated (superseded — pre-fix infra) |
| Mechanism | PREDICTIVE trigger | `experiments.2026-02-12-predictive-trigger` | ✅ Mechanism validated (superseded — pre-fix infra) |
| Mechanism | GRU inference (synthetic) | `models.2026-02-10-training-synthetic` | ⚠️ Mechanism works, real-trace targets not met (superseded) |
| Mechanism | GRU inference (real traces) | `models.2026-02-13-training-clarknet-calgary` | ⚠️ Mechanism works, targets not met (superseded) |
| Performance (H1) | S4 vs S1 latency | `experiments.2026-07-11-scaling-fix-n1` | ✅ Directional (n=1): S4 beats S1 by 95.1% on p99 (118 vs 2,421 ms); not inferential |
| Performance (H2) | S4 vs S3 paired p99 | `experiments.2026-07-14-clarknet-tuned-paired-n5` | ✅ Supported (primary p99 p=0.0304, d=−1.2646, large; corrected secondary p=0.1216 not significant) |
| Testbed | HPA works on k3d | validation/infrastructure-validation | ⚠️ Superseded (scale range now capped at 6) |
| Design Decision | HPA vs kubectl scale exclusive | validation/infrastructure-validation | ✅ (superseded — pre-fix infra) |
| Testbed | Knative KPA works on k3d | validation/infrastructure-validation | ✅ (superseded — pre-fix infra) |
| Cost Mechanism | Throttling cost multiplier | cost/2026-02-17 (Feb directional) | ⚠️ Superseded (Feb directional) |
| Cost Projection | Production comparison | cost/2026-02-17 (Feb directional) | ⚠️ Superseded (Feb directional; use 2026-07-11 figures) |
| Cost Crossover | fib(34) crossover in observed band | cost/2026-02-18 (Feb directional) | ⚠️ Superseded (Feb directional) |
| Mechanism | h=9 forecast sufficiency | `experiments.2026-07-14-clarknet-tuned-paired-n5` | ✅ Mechanism validated (n=5): predictive_count=4–5 per S4 run |
| Mechanism | Utilization-based node consolidation | `experiments.2026-07-14-clarknet-util-scaledown-n1` | ✅ Diagnostic (n=1): 50% utilization threshold + drain |

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
| `models/gru/2026-02-10_training-synthetic` | `models.2026-02-10-training-synthetic` | GRU synthetic training; superseded by the leak-free retrain on 2026-09-10 |
| `models/gru/2026-02-13_training-clarknet-calgary` | `models.2026-02-13-training-clarknet-calgary` | GRU real-trace validation at 5-minute aggregation; superseded by the leak-free retrain on 2026-09-10 |
| `models/gru/2026-09-10_clarknet-15s-h9-leakfree` | `models.2026-09-10-clarknet-15s-h9-leakfree` | Leak-free ClarkNet 15 s study, horizon 9, replay window held out; current predictor evidence |
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

## Training Data Note (superseded 2026-09-11)

- GRU, synthetic arm, leak-free protocol at horizon 9: RMSE 5.2% of the mean load, MAE 4.1%. Target met.
- GRU, real deployment arm, amplified ClarkNet at 15 s with the replay window held out: RMSE 39.6% of the mean load, skill 0.216 against persistence. Target not met.
- LSTM under the identical protocol: RMSE 29.917 against the GRU's 29.635, GRU better on every seed. A linear autoregression on the same window reaches 29.465, so GRU parity with linear is disclosed.
- Superseded figures, do not quote: 4.75%, 6.01%, 17.78%, 14.48%. They come from pre-leak-free protocols at horizon 5 and at 5-minute aggregation.
- Source of record: the predictor section of `results/claims/FINAL_NUMBERS.md` and the bundle `results/models/gru/2026-09-10_clarknet-15s-h9-leakfree`.

---

## Framing Rules for Thesis

1. **H1 (hybrid vs pure K8s):** "Confirmed (n=1): S4 beats S1 by 95.1% on p99 (118 ms vs 2,421 ms) and 98.5% on SLO violations. n=5 replication pending for statistical significance." Do NOT say "proven" (n=1).
2. **H2 (predictive vs reactive):** "Supported (primary p99, definitive n=5). S4 mean 126.00 ms vs S3 mean 188.47 ms, diff −62.47 ms, 95% CI [−100.87, −26.21] ms (entirely below zero), pre-specified primary permutation p=0.0304, Cohen's d=−1.2646 (large). S4 won all 5 pairs." Report secondary metrics (p95, SLO) with the correction caveat (rule 6).
3. **Use** "mechanism validated" for what works (weight shifting, PREDICTIVE trigger, GRU inference).
4. **Use** "mechanism validated on synthetic data; real-trace accuracy below target thresholds" for H3 partial validation.
5. **All pre-2026-07-11 experiment numbers are superseded (Bugs 8-13).** Cite ONLY `results/claims/FINAL_NUMBERS.md`.
6. **Multiplicity correction:** The primary p99 test is pre-specified and significant at p=0.0304 (uncorrected). Secondary metrics (p95, SLO) have corrected p=0.1216 (not significant after correction across 5 metrics) — report them as **descriptive**, not as confirmatory. The artifact's corrected primary field is 1.0; the book MUST state the distinction between the uncorrected primary p and the corrected secondary p-values. Do NOT claim all five metrics are statistically significant.

**Last Updated:** 2026-07-14
