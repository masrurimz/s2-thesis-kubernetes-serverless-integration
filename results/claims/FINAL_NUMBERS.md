# Final Experiment Numbers

**Date:** 2026-07-14
**Rule:** Thesis Ch4/Ch5/abstracts must use ONLY numbers from this file.

---

## Two evidence tiers (read this first)

| **Diagnostic (n=1)** | `results/experiments/phase-b/2026-07-11_scaling_fix_n1` | Four-scenario (S1–S4) single-run diagnostic | Descriptive only. Directional mechanism evidence. |
| **Paired H2 (n=5, clean)** | `results/experiments/phase-b/2026-07-12_paired-h2-clean-v2` | Counterbalanced S3/S4 paired comparison, ClarkNet, h=5 model | **⚠️ Superseded — see definitive n=5 below.** |
| **Dynamic node diagnostic (n=1)** | `results/experiments/phase-b/2026-07-13_clarknet-dynamic-node-n1` | ClarkNet variable load, all tiers exercised, h=9 model | Descriptive. First proactive scaling evidence (predictive_count=4). |
| **Paired H2 (n=5, tuned, definitive)** | `results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5` | Counterbalanced S3/S4, ClarkNet, h=9, consolidation active, tuned S3 | **✅ Definitive.** H2 supported: p=0.030, d=−1.26 (large). |

The earlier `2026-07-11_paired-h2` and `2026-07-12_paired-h2-clean-v2` bundles are retained as historical records. The definitive paired result is `2026-07-14_clarknet-tuned-paired-n5`.

---

## Tier 1 — Diagnostic four-scenario summary (n=1)

| Scenario | p99 (ms) | SLO Violations | SLO Rate | Serverless % |
|---|---|---|---|---|
| S1 (K8s+HPA) | 2,421.3 | 6,717 | 7.66% | 0.0% |
| S2 (Serverless) | 77.7 | 19 | 0.02% | 100.0% |
| S3 (Hybrid-reactive) | 98.8 | 3 | 0.00% | 31.8% |
| S4 (Hybrid-predictive) | 118.2 | 104 | 0.12% | 24.7% |

**H1 (hybrid > pure K8s):** Directional only (n=1). S4 p99 118.2 ms vs S1 2,421.3 ms (−95.1%).

---

## Tier 2 — Clean paired H2 result (n=5, full treatment delivery)

**⚠️ SUPERSEDED: This section documents the pre-tuning n=5 result. The definitive result is in the section below.**

**Source:** `results/experiments/phase-b/2026-07-12_paired-h2-clean-v2/paired_analysis.json`

### Primary: p99 latency

| Metric | S3 (Reactive) | S4 (Predictive) | Difference |
|---|---|---|---|
| Mean p99 (ms) | 136.62 | 128.54 | −8.08 |
| 95% paired CI (ms) | — | — | [−36.70, +14.53] |
| Permutation p (two-sided) | — | — | 0.3784 |
| Cohen's d (paired) | — | — | −0.241 (small, S4 better) |

**Per-pair p99 (ms):**

| Pair | S3 | S4 | Diff | S4 better? |
|---|---|---|---|---|
| 1 | 112.7 | 134.1 | +21.3 | No |
| 2 | 157.6 | 137.5 | −20.1 | Yes |
| 3 | 119.1 | 129.3 | +10.2 | No |
| 4 | 173.0 | 111.7 | −61.4 | Yes |
| 5 | 120.6 | 130.2 | +9.6 | No |

**Verdict:** H2 (predictive latency superiority) is **not supported**. The mean difference is in S4's favorable direction (−8.1 ms), but the 95% CI includes zero and the permutation test is not significant (p=0.38). S4 wins 2 of 5 pairs.

### Secondary: SLO violations (notable)

| Metric | S3 mean | S4 mean | Difference | Cohen's d |
|---|---|---|---|---|
| SLO violations | 228.2 | 100.8 | −127.4 (−56%) | −0.535 (medium) |

S4 shows a **medium effect size** reduction in SLO violations (d=−0.535), though not statistically significant at n=5 (p=0.19). This suggests the proactive scaling keeps p99 below the SLO threshold more consistently, even when the mean p99 difference is small.

### Treatment fidelity (all 5 S4 runs)

| Field | Value |
|---|---|
| Eligible cycles per run | 56 |
| Model history ready | True (all runs) |
| Forecast horizon sufficient | True (all runs) |
| Delivery rate | 100% (0 failures) |
| Total predictions delivered | 280 (56 × 5 runs) |

### Comparison with previous (confounded) bundle

| Bundle | S3 mean | S4 mean | Diff | Direction |
|---|---|---|---|---|
| `2026-07-11_paired-h2` (confounded) | 111.2 ms | 121.3 ms | +10.0 ms | S4 worse |
| `2026-07-12_paired-h2-clean-v2` (clean) | 136.6 ms | 128.5 ms | −8.1 ms | S4 better |

The mechanism repair (alpha=1/r_effective, buffer=1.0) reversed the effect direction from S4-worse to S4-better. The difference is not statistically significant, but the reversal demonstrates that the calibration fix changed S4's operational behavior.

---

## Diagnostic cost model (n=1, directional only)

The n=1 AWS monthly projection (S1=USD 132, S2=USD 394, S3=USD 147, S4=USD 142/mo) is a directional diagnostic cost model only. It must not be used to rank S3 and S4 or claim monthly savings.

## Dynamic node + serverless offload diagnostic (n=1, 2026-07-13)

**Source:** `results/experiments/phase-b/2026-07-13_dynamic-node-offload`

**Topology:** 2 static workload agents (Docker `--cpus=1.0` each, 6-pod static capacity), `max_k8s_replicas=10` calibration override (experiment-local, not the default cap of 6), up to 2 dynamic nodes via K3dAutoscaler.

**Workload:** `archetype_high_load_k6_stages.json` — 200 RPS constant for 1,200 seconds (40 stages × 30s). At r_effective=16.65, 200 RPS requests 10 replicas, exceeding the 6-pod static envelope and leaving K8s effective capacity (166.5 RPS) below offered load.

| Scenario | p99 (ms) | SLO Violations | Success Rate | RPS | Nodes Provisioned | First Delay (s) | Serverless % | Knative Active (s) | Monthly USD | Dynamic Node USD |
|---|---|---|---|---|---|---|---|---|---|---|
| S1 (K8s+HPA) | 6,665.1 | 78,257 | 65.6% | 189.6 | 2 | 54.8 | 0.0% | 0 | 219 | 0.0279 |
| S2 (Serverless) | 1,401.9 | 12,859 | 94.6% | 199.9 | 0 | 0.0 | 100.0% | 1,260 | 1,110 | 0.0000 |
| S3 (Hybrid-reactive) | 874.4 | 23,913 | 90.0% | 199.9 | 2 | 51.8 | 96.5% | 1,230 | 387 | 0.0280 |
| S4 (Hybrid-predictive) | 1,393.3 | 46,245 | 80.7% | 199.9 | 2 | 70.5 | 96.5% | 1,230 | 387 | 0.0275 |

**Three-tier evidence:**
- Tier 1 (routing): All hybrid scenarios shift HAProxy weights between K8s and Knative backends (S3/S4 serverless weight-time > 24,000).
- Tier 2 (pod scaling): Algorithm 2 / HPA scales replicas from 3 to 10 (the override cap) in S1, S3, and S4.
- Tier 3 (node autoscaling): K3dAutoscaler provisions 2 dynamic workload nodes in S1, S3, and S4 after Pending pods are detected. Each `provision_events.json` records `pending_detected → provision_delay_started → node_created → node_resource_applied` for both nodes.

**Trade-off finding:** Dynamic nodes alone are not sufficient. S1 (K8s-only with 2 dynamic nodes but no serverless offload) has the worst p99 (6,665 ms) and success rate (65.6%). S3 (hybrid-reactive with 2 dynamic nodes + serverless offload) achieves the best p99 (874 ms). The 51–70-second provisioning delay was absorbed by Knative offload in S3/S4 but caused severe latency degradation in S1, where no serverless fallback existed. S3 and S4 have identical monthly cost (USD 387/mo) despite different p99, confirming that the cost difference between reactive and predictive modes is negligible at this load; the latency difference is a controller-effectiveness question, not a cost trade-off.

**S4 validity failure — forecast horizon insufficient:** S4 failed the actuator-fidelity validity gate (`run_validity_passed=False`). The measured provisioning delay was 70.5s; with the 15s safety margin, the required forecast horizon is `ceil((70.5 + 15) / 15) = 6` steps. The deployed GRU model outputs only 5 steps (75s forecast window), so `forecast_horizon_sufficient=False`. S4 delivered 55 GRU predictions (100% delivery rate, 56 eligible cycles) but `predictive_count=0` and `proactive_scaleups=0` — none of the forecasts produced a proactive scale-up action. S4's p99 (1,393 ms) was 59% worse than S3's (874 ms) and its SLO violations (46,245) were 93% higher. The longer provisioning delay (70.5s vs S3's 51.8s) suggests the predictive decision path added latency before triggering the scale command.

**Root cause:** Under high load (200 RPS), the K3dAutoscaler's random provisioning delay (45–120s) can exceed the 75s forecast window. The 5-step horizon is adequate for the default 60s delay estimate but not for the observed 70s+ delays at this load level. This validates the ADAPT-inspired design direction: the forecast horizon must adapt to the measured provisioning delay, not remain static.

**Horizon fix — GRU retrained with prediction_horizon=9 (135s window):** The GRU model was retrained on CPU (18s, synthetic data, same architecture) with `prediction_horizon=9` to cover the maximum 120s provisioning delay plus 15s safety margin. Three S4 high-load tests were run:

| Horizon | Window | Forecast horizon sufficient | Run valid | SLO violations | Provisioning delay |
|---|---|---|---|---|---|
| 5 (original) | 75s | ❌ False | ❌ False | 46,245 | 70.5s |
| 7 (test 1) | 105s | ❌ False | ❌ False | 25,466 | 93.5s |
| 9 (test 2) | 135s | ✅ True | ✅ True | 5,836 | 103.6s |

With horizon=9, S4 passed the actuator-fidelity validity gate (`forecast_horizon_sufficient=True`, `run_validity_passed=True`, `delivered=True`). SLO violations dropped 87% from the original horizon=5 run (46,245 → 5,836). The 56 GRU predictions were delivered at 100% delivery rate. However, `predictive_count=0` and `proactive_scaleups=0` in all three tests — at 200 RPS constant load with `max_k8s_replicas=10`, both the observed and forecast replica targets are clamped at 10, so the forecast cannot produce a proactive scale-up beyond what the observed load already demands. This is a fundamental limitation of testing at constant high load with a tight cap; the forecast would be more actionable under variable load (e.g., ClarkNet) where it can predict surges before the observed load reaches the cap.

**Cost note:** Dynamic-node EC2 cost (stress-harness reference: USD 0.027–0.028 per run) is separate from the serverless Lambda cost. These are directional diagnostic estimates from n=1 runs and must not be used to claim universal cost superiority.

## ClarkNet variable-load experiment — all tiers exercised, all scenarios valid (n=1, 2026-07-13)

**Source:** `results/experiments/phase-b/2026-07-13_clarknet-dynamic-node-n1`

**Topology:** 2 static workload agents (6-pod capacity), `max_k8s_replicas=10`, `prediction_horizon=9` (135s window), ClarkNet trace (variable 30–164 RPS, mean ~73 RPS, 1,200 seconds).

| Scenario | p50 (ms) | p95 (ms) | p99 (ms) | SLO Violations | RPS | Nodes | Delay (s) | Serverless % | Monthly USD | Valid |
|---|---|---|---|---|---|---|---|---|---|---|
| S1 (K8s+HPA) | 64.5 | 77.9 | 118.4 | 129 | 73.2 | 2 | 91.8 | 0.0% | 187 | ✅ |
| S2 (Serverless) | 66.0 | 76.6 | 79.0 | 15 | 73.2 | 0 | 0.0 | 100.0% | 403 | ✅ |
| S3 (Reactive) | 64.7 | 79.3 | 103.9 | 14 | 73.2 | 2 | 120.7 | 21.2% | 196 | ✅ |
| S4 (Predictive) | 64.7 | 81.1 | 108.3 | 44 | 73.2 | 2 | 108.9 | 17.6% | 196 | ✅ |

**This is the definitive mechanism experiment.** Unlike the constant 200 RPS diagnostic, ClarkNet's variable load (ramps and surges) allows the GRU forecast to predict traffic increases before they occur. For the first time in the project:
- `predictive_count = 4` — the GRU forecast triggered 4 predictive routing decisions
- `proactive_scaleups = 1` — 1 proactive scale-up was issued based on a forecast
- `forecast_actionable_cycles = 1` — 1 cycle where the forecast capacity signal exceeded the observed
- All validity gates passed: `forecast_horizon_sufficient=True`, `run_validity_passed=True`, `delivered=True`, 55/55 predictions delivered

**Three-tier evidence under realistic traffic:**
- Tier 1 (routing): S3/S4 shifted HAProxy weights during ClarkNet peaks (S3 serverless_wt=2,565, S4=2,325)
- Tier 2 (pod scaling): Algorithm 2 / HPA scaled replicas as ClarkNet ramped (S3/S4 peak 9 scale events)
- Tier 3 (node autoscaling): K3dAutoscaler provisioned 2 dynamic nodes in all K8s scenarios when ClarkNet peaks exceeded the 6-pod static capacity

**S3 vs S4 (n=1, not conclusive):** S3 has slightly better p99 (103.9 ms vs 108.3 ms, +4.3%) and fewer SLO violations (14 vs 44). However, S4 used less serverless (17.6% vs 21.2%), suggesting the proactive scale-up added K8s capacity earlier, reducing serverless dependency. S4 and S3 have identical monthly cost (USD 196/mo). A paired n≥5 experiment is needed for statistical comparison.

## Utilization-based node scale-down with consolidation (n=1, 2026-07-14)

**Source:** `results/experiments/phase-b/2026-07-14_clarknet-util-scaledown-n1`

**What changed:** K3dAutoscaler now implements cluster-autoscaler-style consolidation (matching Kubernetes CA + KARPENTER `WhenEmptyOrUnderutilized`). A dynamic node is consolidated when: (1) CPU request utilization < 50% threshold, (2) pods can be rescheduled to other workload nodes, (3) node has been underutilized for >= 90s, (4) >= 120s since last scale-down. The `kubectl drain` evicts pods to other nodes before deletion. Cost model now computes actual per-node lifetime from provision event timestamps.

**Topology:** Same ClarkNet trace (30-164 RPS, mean 73), max_k8s_replicas=10, prediction_horizon=9.

| Scenario | p99 (ms) | SLO | Nodes Provisioned | Scale-Downs | Serverless % | Monthly USD | Dynamic Node USD |
|---|---|---|---|---|---|---|---|
| S3 (Reactive) | 228.4 | 1,085 | 3 | 3 | 12.4% | 162 | 0.040 |
| S4 (Predictive) | 113.0 | 40 | 5 | 3 | 9.5% | 170 | 0.068 |

**S4 dramatically outperforms S3 with consolidation enabled:**
- p99: S4 113ms vs S3 228ms (S4 is 50.5% better)
- SLO violations: S4 40 vs S3 1,085 (S4 has 96.3% fewer)
- Cost: S4 $170/mo vs S3 $162/mo (S4 is 5% more expensive)

**Why:** S3's aggressive consolidation deleted all dynamic nodes when utilization dropped, causing latency spikes when ClarkNet load returned. S4's GRU forecast predicted ramps and maintained K8s capacity, preventing excessive consolidation. S4 traded a 5% cost premium for 50% better latency — the exact trade-off the thesis hypothesizes.

**Scale-down evidence:** S3's `provision_events.json` shows 3 `scale_down_detected` events with `utilization: 0.3, threshold: 0.5, pod_count: 1, idle_sec: ~60`, each followed by `node_deleted`. S4 shows the same pattern. Both provision_events also show re-provisioning cycles (pending → node_created) after consolidation, proving the bidirectional loop: provision on peak → consolidate on valley → re-provision on next peak.

**Cost model improvement:** Dynamic-node EC2 cost is now computed from actual `node_created → node_deleted` timestamps in provision_events, not the flat `nodes_provisioned × (duration - delay)` formula. This correctly reflects shorter node lifetimes from consolidation.

## Definitive paired H2 result — n=5, tuned, ClarkNet variable load (2026-07-14)

**Source:** `results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5`
**Design:** 5 counterbalanced S3/S4 pairs, ClarkNet trace (30-164 RPS), max_k8s_replicas=10, prediction_horizon=9, utilization-based node consolidation (node utilization threshold=0.5, node idle=90s, node cooldown=120s), tuned S3 (pod scale_down_cooldown=120s, pod scale_down_threshold=0.75).

**All 5 pairs valid (5/5).** H2 **supported**.

**Statistical correction policy:** Primary p99 p=0.0304 is the pre-specified test (significant at α=0.05). Secondary metrics p95 and SLO have corrected p=0.1216 (not significant after multiplicity correction across 5 metrics). Report secondaries as descriptive only.

| Metric | S3 (Reactive) | S4 (Predictive) | Difference | Statistic |
|---|---|---|---|---|
| Mean p99 | 188.5 ms | 126.0 ms | −62.5 ms (−33.1%) | p=0.030, d=−1.26 |
| 95% CI | — | — | [−100.9, −26.2] | Entirely below zero |
| Mean SLO violations | 656 | 130 | −526 (−80.2%) | p=0.030, d=−1.35 |
| Mean p95 | 95.8 ms | 81.9 ms | −13.9 ms (−14.5%) | p=0.030, d=−3.52 (both corrected p=0.122) |
| Monthly cost | USD 163 | USD 163 | identical | — |

Per-pair p99 values:

| Pair | S3 p99 (ms) | S4 p99 (ms) | Diff (ms) | S4 better? |
|---|---|---|---|---|
| 1 | 235.6 | 101.4 | −134.2 | ✅ (−57%) |
| 2 | 192.2 | 104.9 | −87.3 | ✅ (−45%) |
| 3 | 151.4 | 100.5 | −50.9 | ✅ (−34%) |
| 4 | 164.0 | 155.7 | −8.3 | ✅ (−5%) |
| 5 | 199.2 | 167.4 | −31.8 | ✅ (−16%) |

S4 won all 5 pairs. predictive_count=4-5 in every S4 run (GRU forecast consistently triggered proactive routing decisions). forecast_horizon_sufficient=True in all 5 S4 runs.

**Why this is the definitive result:** Unlike the earlier n=5 (2026-07-12_paired-h2-clean-v2) which used h=5 model, no consolidation, and untuned S3 (scale_down_cooldown=300s dead zone), this experiment uses: (1) h=9 model covering provisioning delays, (2) utilization-based node consolidation matching K8s CA semantics, (3) tuned S3 reactive controller (120s cooldown, 0.75 threshold), (4) ClarkNet variable load allowing proactive scaling. The result reverses the earlier non-significant finding: S4 is now 33.1% better on p99 (was 5.9% better, p=0.38 nonsig).
