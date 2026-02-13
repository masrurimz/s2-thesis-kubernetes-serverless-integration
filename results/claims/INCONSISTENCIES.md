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
