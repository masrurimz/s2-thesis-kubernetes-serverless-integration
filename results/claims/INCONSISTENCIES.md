# Known Inconsistencies & Resolutions

**Date:** 2026-02-13
**Purpose:** Audit trail of inconsistencies found during thesis evidence validation.

---

## Resolved Inconsistencies

### 1. Hypothesis Validation Report vs Honest Assessment
- **Issue:** `results/HYPOTHESIS_VALIDATION_REPORT.md` claimed "ALL HYPOTHESES VALIDATED" using cherry-picked stress test throughput numbers, while honest assessment shows H1 p=0.0677 (not significant) and H2 had no difference.
- **Resolution:** Report rewritten. Old file deleted during repo restructuring.

### 2. GRU Training Data: Synthetic vs Real
- **Issue:** Thesis proposal (Section 3.2) specifies ClarkNet and Calgary HTTP traces for training. Actual GRU training used synthetic data.
- **Resolution:** Documented in claims mapping. ClarkNet/Calgary used for baseline comparison only.

### 3. Mislabeled Phase B Data
- **Issue:** `thesis/results/raw/phase_b/validation_20260211_232450.json` contained OLD stress test data (79-97% error rates) but was stored as Phase B results.
- **Resolution:** Moved to `results/experiments/phase-a1/2026-02-11_stress-tests/raw/`. Correctly labeled as stress test data.

### 4. Real Phase B Data Hidden
- **Issue:** The actual 20-run per-run experiment data (`experiments_final.json`) was in `controller/results/phase_b/` — never promoted to thesis evidence directories.
- **Resolution:** Promoted to `results/experiments/phase-b/2026-02-12_replicated-20runs/raw/`.

### 5. Statistics Don't Match Raw Data
- **Issue:** `PHASE_B_HONEST_ASSESSMENT.md` reports "S1 mean=400.9±103.3ms, S4 mean=558.0±228.8ms" but computing from experiments_final.json gives S1 mean=519.8ms, S4 mean=430.8ms (different values, different direction).
- **Resolution:** Acknowledged. Old stats may have excluded outlier runs or used different methodology. The raw per-run data in `experiments_final.json` is the source of truth.

### 6. PREDICTIVE Count Discrepancy
- **Issue:** PHASE_B_HONEST_ASSESSMENT.md says "PREDICTIVE actions triggered (P0)" but experiments_final.json shows PREDICTIVE=0 in ALL 20 Phase B runs. The PREDICTIVE trigger was from Phase A1 ramp test, not Phase B.
- **Resolution:** Correctly attributed. PREDICTIVE validated in Phase A1 only.

### 7. Violation Count Error
- **Issue:** PHASE_B_HONEST_ASSESSMENT.md claims "S3: 0 violations, S4: 0 violations" at 100 RPS. Raw data shows S3: 4/5 runs had violations, S4: 5/5 runs had violations.
- **Resolution:** Old report was wrong. Updated in consolidated report.

### 8. Outlier Runs (Stale Prometheus Data)
- **Issue:** S1-run2 (p99=9.9ms, 190 RPS), S2-run5 (p99=9.9ms, 201 RPS), S3-run5 (p99=10.0ms, 84 RPS) have impossibly low p99 latency.
- **Root Cause:** Prometheus metrics likely reset/stale during these runs. Normal HAProxy p99 range: 200-900ms.
- **Resolution:** Exclusion criteria defined (p99<15ms OR throughput>150RPS). Statistics recomputed with clean data (n=4/4/4/5). Both versions reported transparently.
- **Impact:** Excluding outliers increases S1/S2/S3 mean p99 (more honest baselines), reduces variance, but doesn't change statistical significance outcomes.
- **Documentation:** `results/experiments/phase-b/2026-02-12_replicated-20runs/EXCLUSION_CRITERIA.md`

---

## Acknowledged Limitations (Not Resolved)

### 1. k3d Localhost Bias
S1 (K8s-only) benefits from localhost routing, making it artificially fast. Cannot be resolved without multi-node or cloud deployment.

### 2. Load Insufficiency
100 RPS insufficient to demonstrate predictive advantage. Higher load or real cloud deployment needed.

### 3. Missing MAE Evaluation
Proposal targets MAE < 5% but MAE was not reported as percentage in results. Raw MAE=4.91 exists but percentage was not computed against average.

### 4. Cost Analysis is Proxy-Based
Proposal asks for real cost comparison. Only proxy/estimated costs were computed, not actual billing data.

### 5. Stale Prometheus Metrics
Some Phase B runs (S1-run2, S2-run5, S3-run5) show p99~10ms and anomalously high throughput (~190-200 RPS). These are likely stale/reset Prometheus data, not real measurements.

### 6. 15+ Duplicate Report Files
Previous documentation had the same results reported in 3-5 different files with different numbers. Resolved by consolidating into experiment bundle convention (one report.md per experiment).

## 2026-02-14: Three Critical Bugs Invalidate Previous Phase B Data

### Bug 1: SLO Monitor Using Wrong HAProxy Column (ttime vs rtime)
- **Discovery**: Session 2026-02-14, investigating constant SCALE_OUT in Phase B runs
- **Root Cause**: `slo_monitor.py` read `fields[61]` (ttime = total connection time including keepalive) instead of `fields[60]` (rtime = backend response time)
- **Impact**: p99 estimates 7000-10000ms when actual response time was 1-2ms. ALL S3/S4 runs in previous Phase B showed 84+ SCALE_OUT decisions regardless of actual system health.
- **Fix**: Commit `18558ff` — changed to rtime (fields[60]) and rtime_max (fields[92])
- **Affected Data**: `results/experiments/phase-b/2026-02-12_replicated-20runs/` and Phase C data

### Bug 2: Algorithm 1 Priority Order Reversed
- **Discovery**: Same session, after fixing Bug 1, PREDICTIVE still unreachable
- **Root Cause**: Code checked OPTIMIZE_COST (Priority 3) before PREDICTIVE (Priority 2), so when system was healthy, OPTIMIZE_COST always fired first, preventing PREDICTIVE evaluation
- **Impact**: PREDICTIVE could never trigger in healthy state — which is exactly when it should trigger
- **Fix**: Commit `c6f3e0b` — swapped priority order to match thesis (SCALE_OUT → PREDICTIVE → OPTIMIZE_COST → MAINTAIN)
- **Affected Data**: Same as Bug 1

### Bug 3: Prometheus Not Scraping Routing Daemon
- **Discovery**: Same session, daemon metrics empty in Prometheus export
- **Root Cause**: Prometheus (inside k3d) had no scrape target for daemon at port 9104
- **Fix**: Commit `e6c4506` — added routing-daemon scrape job targeting 172.19.0.1:9104
- **Affected Data**: All previous experiments missing daemon Prometheus metrics

### Resolution
Previous Phase B (2026-02-12) and Phase C data should be treated as **invalidated** for Algorithm 1 decision analysis. k6 latency metrics remain valid (they measure end-to-end, not affected by daemon bugs). New Phase B experiments running 2026-02-14 with all three bugs fixed.

### Resolution (continued)

**New experimental baseline established 2026-02-14:**
- Workload endpoint: `/work?duration_ms=5` (deterministic CPU busy-loop)
- Runtime: `GOMAXPROCS=1` (single-threaded Go)
- Resources: 500m CPU / 128Mi memory / 1 replica baseline
- Saturation: ~145 RPS per replica (calibrated)
- Scaling model: α=0.0069, β=0.0 (derived from saturation point)
- Trace replay: ClarkNet g=33 (peak 164 RPS, mean 73 RPS)
- Calibration bundle: `results/experiments/phase-b/2026-02-14_calibration-work-5ms/`

**Phase A1 also affected:** Phase A1 mechanism validation (2026-02-12) was run before all three bug fixes. While the PREDICTIVE trigger evidence (p99=146ms, 47% surge predicted) demonstrates the mechanism conceptually, the SLO monitor was reading wrong values. Phase A1 should be re-validated post-fix.

## 2026-02-14: Four Experiment Design Bugs Invalidate Phase B Rerun (ClarkNet Replay)

**Discovery:** Session 2026-02-14, investigating contaminated metrics in 20-run ClarkNet replay experiment.

**Context:** After fixing Bugs 1-3 (above), a new 20-run Phase B experiment was conducted with the `/work?duration_ms=5` endpoint and ClarkNet trace replay. All 20 runs completed but post-hoc analysis revealed 4 additional bugs that invalidate all daemon/routing metrics.

**Affected Data:** `results/experiments/phase-b/2026-02-14_clarknet-replay/` (all 20 runs)

### Bug 4: HAProxy Server Name Mismatch in ScenarioResetter
- **Root Cause**: `run_phase_b_experiments.py` ScenarioResetter uses HAProxy Runtime API with server name `k3s-cluster` but actual backend server is named `k3s`. The `set server` command silently fails (HAProxy returns no error for nonexistent servers).
- **Impact**: Weight resets between runs silently failed. S1 never got 100/0 weights (K8s-only), S2 never got 0/100 (serverless-only). All scenarios started with stale weights from the previous run.
- **Evidence**: S1 (K8s-only) shows `time_in_serverless=70-96%` — impossible if weights were correctly set to 100/0.
- **Fix Bead**: s2-1xu

### Bug 5: Stale Daemon Process Leaking Metrics Across Scenarios
- **Root Cause**: Routing daemon binds Prometheus metrics endpoint on port 9104. Between runs, the old daemon process is not killed. New daemon fails to bind the port, and Prometheus continues scraping the old daemon's metrics from the previous scenario.
- **Impact**: Complete metric contamination. S1 (K8s-only, no daemon needed) shows PREDICTIVE=165-786 actions because Prometheus was scraping a stale S4 daemon. S3 (reactive, no GRU) also shows PREDICTIVE actions.
- **Evidence**: S1 should have PREDICTIVE=0 (no daemon runs for S1). Instead, every S1 run shows hundreds of PREDICTIVE decisions.
- **Fix Bead**: s2-jrc

### Bug 6: Prometheus Counter Query Missing `_total` Suffix
- **Root Cause**: Metrics collection code queries `routing_daemon_prediction_used` but Prometheus stores counter metrics with `_total` suffix as `routing_daemon_prediction_used_total`. Query returns empty result.
- **Impact**: `gru_predictions_used=0` for ALL 20 runs including S4 where GRU prediction server was healthy and responding. Makes it impossible to verify GRU integration worked.
- **Evidence**: GRU prediction server logs show successful predictions, but metric collection reports 0 for every run.
- **Fix Bead**: s2-nxq

### Bug 7: No Pre-Run Invariant Checks
- **Root Cause**: Experiment runner had no pre-run validation to check: (a) HAProxy weight reset succeeded, (b) no stale daemon on metrics port, (c) Prometheus queries return non-empty data, (d) correct scenario isolation.
- **Impact**: All 4 bugs went undetected for 20 runs (~2 hours of experiment time). Without invariant checks, silent failures are invisible.
- **Fix Bead**: s2-9w2

### Resolution
- k6 latency data remains valid (measures end-to-end HTTP, not affected by daemon bugs): p95 ranges 535-3408ms, ~87K requests per run at ~73 RPS mean.
- ALL daemon metrics (routing decisions, weight distributions, GRU predictions used, time in serverless) are garbage and must not be cited.
- New Phase B experiment required with all 7 bugs (1-3 from earlier + 4-7 from this batch) fixed.
- Bundle marked `status: invalidated` in meta.yaml.

---

## Resolved Inconsistencies (continued)

### 9. Cost Chapter Mixed Stress-Harness Node Capacity with Production Projection

- **Issue:** Original cost analysis (2026-02-17) derived EC2 node counts from k3d stress-harness observation (nodes_provisioned from experiment, constrained to 400m allocatable per node via `system-reserved=15600m`). This produced cost figures that reflected the artificial constraint — not representative of real cloud node capacity.
- **Root Cause:** `cost_analyzer.py` Model 3 used observed `nodes_provisioned` from experiment, which reflected the artificial k3d constraint (2 pods/node). Real t3.medium has ~1.8 vCPU allocatable → 9 pods/node. S1's 9 desired replicas fit on 1–2 real nodes, not 6.
- **Impact:**
  - K8s execution time was hardcoded at 10ms (actual: 105ms via Little's Law with 200m CPU limit)
  - EC2 model undercounted production nodes for serverless-heavy scenarios
  - Missing EKS control plane cost ($72/month)
  - Corrected numbers change the cost story: S1 $162/mo, S2 $192/mo, S3 $192/mo, S4 $222/mo (EC2 Production)
- **Resolution:**
  - `cost_analyzer.py` split into Model 3a (observed/stress) and Model 3b (production projection using real t3.medium capacity)
  - K8s service time now derived from Little's Law (avg_replicas / k8s_rps)
  - Added EKS control plane $0.10/hr
  - Report rewritten with two-world framing
  - Cross-ref: `thesis/protocol/THREATS_TO_VALIDITY.md` (new construct validity threat)
