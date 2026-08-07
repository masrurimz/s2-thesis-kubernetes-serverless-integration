# Thesis Validation Plan: Two-Phase Approach

**Goal:** Validate H1 (Hybrid), H2 (Predictive), H3 (GRU) with honest, defensible evidence

**Timeline:** Phase A (2-6 hours) → Phase B (1-2 days if needed)

---

## Phase A: Quick Wins (Easy First)

### A0: Evidence Packaging (1 hour, no new experiments)
Document what we *can* claim today:

| Hypothesis | Current Evidence | What We Can Claim |
|------------|------------------|-------------------|
| **H3** | 6.01% RMSE measured | ✅ "GRU achieves 6.01% RMSE, meeting <10% target" |
| **H2** | Pipeline works, PREDICTIVE=0 | ⚠️ "Pipeline operational; conservative threshold prevented actions" |
| **H1** | Historical stress test | ⚠️ "Mechanism validated (weight shifting); SLO recovery limited under extreme load" |

**Deliverable:** `docs/CURRENT_EVIDENCE_PACKAGE.md` ✅ Done

---

### A1: Minimal Live Validation (2-4 hours)
**Goal:** Trigger at least 1 PREDICTIVE action + collect live metrics

**Setup:**
```bash
# Terminal 1: Start prediction server
cd controller
HSA_OVERRIDE_GFX_VERSION=11.0.0 sg render -c \
  "uv run python -m prediction.prediction_server"

# Terminal 2: Run with lowered threshold (experiment)
HSA_OVERRIDE_GFX_VERSION=11.0.0 \
  PREDICTION_CONFIDENCE_THRESHOLD=0.5 \
  sg render -c "uv run python -m daemon.routing_daemon --scenario s4"
```

**Experiment:**
- Duration: 3 minutes (180 seconds)
- Workload: `infrastructure/load-tests/steady.js` (100 RPS)
- Scenarios: S3 (reactive) vs S4-low-threshold (predictive)
- Runs: 2 per scenario

**Metrics to collect:**
1. Throughput (RPS)
2. p95 latency
3. Error rate
4. Decision counts (SCALE_OUT, PREDICTIVE)
5. GRU confidence scores

**Success criteria:**
- PREDICTIVE > 0 in at least one run
- Metrics saved to JSON
- Comparison table generated

---

## Phase B: Correct Way (Full Scientific Validation)

### B0: Pre-register Design (1 hour)
Write experimental protocol BEFORE running:

**Hypotheses:**
- H1: S4 achieves better throughput than S1 at acceptable error rates
- H2: S4 with predictive enabled reduces p99 vs S3 reactive
- H3: GRU confidence correlates with prediction accuracy

**Metrics:**
- Primary: throughput, p99 latency, error rate
- Secondary: decision counts, GRU confidence, cost proxy

**Scenarios:**
- S1: K8s-only
- S2: Serverless-only
- S3: Hybrid reactive
- S4: Hybrid predictive (threshold 0.7)
- S4-low: Hybrid predictive (threshold 0.5) - sensitivity test

**Acceptance criteria:**
- ≥3 replicates per scenario
- Randomized run order
- 5-minute duration per run
- 95% confidence intervals reported

---

### B1: Workload Calibration (1-2 hours)
Find "Goldilocks" load where differences are visible:

```bash
# Test different RPS levels
for rps in 50 100 200 500; do
  k6 run --env RPS=$rps infrastructure/load-tests/calibration.js
done
```

**Target:** Load where:
- S1 shows stress but not total collapse
- S2 handles easily
- Hybrid has room to demonstrate benefit

---

### B2: Proper Experiment Execution (4-8 hours)
```bash
# Run full experiment
python scripts/realtime_validation.py \
  --live \
  --scenarios s1,s2,s3,s4,s4-low \
  --runs 5 \
  --duration 300 \
  --output results/final_validation/
```

**Features:**
- Randomized scenario order
- Prometheus metrics collection
- Automated result aggregation
- Statistical analysis (t-test, confidence intervals)

---

### B3: Analysis & Report (2-3 hours)
Generate thesis-ready results:

```python
# Statistical analysis
from scipy import stats

# Per-run aggregates
s3_throughput = [536, 542, 528, 550, 538]  # example
s4_throughput = [586, 592, 578, 595, 588]  # example

# Welch's t-test
t_stat, p_value = stats.ttest_ind(s4_throughput, s3_throughput, equal_var=False)

# Confidence interval
import numpy as np
diff = np.mean(s4_throughput) - np.mean(s3_throughput)
ci_low, ci_high = np.percentile(..., [2.5, 97.5])
```

**Deliverables:**
1. Results table with CIs
2. p-values for hypothesis tests
3. Effect sizes (Cohen's d)
4. Visualization (box plots, time series)

---

## Decision Tree

```
Start
│
├─► Can you run experiments now?
│   ├─► YES → Phase A1 (minimal live validation)
│   │         └─► PREDICTIVE > 0 triggered?
│   │             ├─► YES → Continue to Phase B
│   │             └─► NO → Document conservative behavior as finding
│   └─► NO → Phase A0 only (document current state)
│
└─► Phase B (full validation if time permits)
    ├─► Workload calibration
    ├─► 5 replicates × 5 scenarios
    └─► Statistical analysis
```

---

## Resource Requirements

### Phase A (Quick)
- Time: 2-6 hours
- Compute: Current k3d cluster
- Storage: ~100 MB for metrics
- Risk: Low (uses existing infrastructure)

### Phase B (Correct)
- Time: 1-2 days
- Compute: Current k3d cluster + monitoring
- Storage: ~1 GB for full metrics
- Risk: Medium (requires stable cluster)

---

## Exit Criteria by Phase

### Phase A Complete When:
- [x] H3 evidence documented
- [x] At least 1 live experiment run
- [x] Prometheus metrics successfully collected
- [x] Comparison table generated (even if preliminary)

### Phase B Complete When:
- [x] 3+ replicates per scenario (20 runs executed)
- [x] Statistical tests performed (Welch's t-test, Mann-Whitney U)
- [x] 95% CIs reported
- [ ] Thesis-ready results chapter written

---

## Historical Status Snapshot (superseded)

| Phase | Status | Next Action |
|-------|--------|-------------|
| A0 | ✅ Complete | Evidence documented |
| A1 | ✅ Complete | PREDICTIVE triggered, metrics collected |
| B0-B4 (v1) | ⚠️ Invalidated | Workload parameterization insufficient — `duration_ms=5` (~145 RPS saturation) meant trace peak only 1.13× capacity; scaling mechanisms not exercised |
| B (v2) | ⚠️ Invalidated | `duration_ms=10` busy-loop blocked Go scheduler — health checks failed, HPA saw ~1% CPU under full load |
| B (v3) | 🔄 Redesigned | Switched to `/fib?n=32` (~60 RPS saturation); cooperative scheduling enables correct HPA/CPU reporting. α=0.0167. Awaiting re-execution. |

---

**Plan created:** 2026-02-12  
**Phase B v1 completed:** 2026-02-13 (invalidated due to workload parameterization — see THREATS_TO_VALIDITY.md)  
**Phase B v2 invalidated:** 2026-02-15 (busy-loop blocked Go scheduler)  
**Phase B v3 redesign:** 2026-02-15 (switched to /fib?n=32)  
**Next milestone:** Re-run Phase B with corrected parameterization, then thesis results chapter write-up

---

## Final Design Addendum (2026-07-14)

The earlier Phase B plan and status table above are retained as historical planning records. The delivered design is the v4 multi-node testbed described in `PHASE_B_V4_DESIGN.md`: two bounded workload nodes plus dynamically provisioned workload nodes, Docker `--cpus` node bounds, workload/serverless placement isolation, and explicit node-provisioning and treatment-fidelity gates. The old single-node and unlimited-capacity assumptions must not be used for final claims.

The definitive H2 execution used a **counterbalanced paired n=5 design (10 runs total)**, not five independent runs per scenario and not the earlier n=10–15-per-scenario target. Each pair ran S3 (reactive) and S4 (predictive) under the same ClarkNet variable-load replay, with pair order counterbalanced. The final GRU model supplied a 9-step horizon at 15 seconds per step (**h=9, 135 seconds**), sufficient for the measured provisioning-delay regime. Prediction drove Algorithm 2 replica scaling; routing remained observed-load/capacity-driven. The separate `2026-07-11_scaling_fix_n1` four-scenario run was retained as a diagnostic for directional H1 evidence.

The final primary comparison is paired p99: S3 mean 188.5 ms versus S4 126.0 ms, 95% CI [−100.9, −26.2], p=0.030 (unrounded 0.0304), d=−1.26. Secondary p95 and SLO results are descriptive after corrected p=0.1216. See `results/claims/FINAL_NUMBERS.md` for the canonical values.
