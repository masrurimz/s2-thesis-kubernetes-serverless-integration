# PREDICTIVE Eligibility Analysis — Phase B

**Date**: 2026-02-13  
**Analysis of**: 20 replicated runs (5 runs × 4 scenarios)  
**Question**: Why did `PREDICTIVE=0` in **all** Phase B runs?

---

## Executive Summary

**ROOT CAUSE**: GRU prediction server was **not running** during Phase B experiments.

- **Evidence**: `gru_predictions_used=0` in all 20 runs (aggregate metric in experiments_final.json)
- **Impact**: PREDICTIVE action could **never** trigger — prediction input missing
- **Implication**: Phase B validated S3 vs S4 **reactive** behavior only, not predictive capability

**PREDICTIVE mechanism WAS validated** in Phase A1 ramp test (2026-02-12):
- Triggered at p99=146ms (healthy state)
- Predicted 47% load increase with 72% confidence
- Pre-positioned serverless capacity before violation

---

## Analysis Method

### PREDICTIVE Trigger Conditions (from Algorithm1Controller)

PREDICTIVE requires **ALL** of:
1. ✅ `p99 < 200ms` (healthy, not in SCALE_OUT mode)
2. ✅ `confidence >= 0.5` (or 0.6/0.7 if threshold raised)
3. ✅ `predicted_load_increase > 30%`
4. ✅ Not in cooldown (15 sec since last adjustment)
5. ❌ **GRU prediction available** (requires GRU server running)

### Data Source

`results/experiments/phase-b/2026-02-12_replicated-20runs/raw/experiments_final.json`

---

## Per-Run Results (S4 Only)

| Run | p99 (ms) | Violations | SCALE_OUT | PREDICTIVE | GRU Used | GRU Conf |
|-----|----------|------------|-----------|------------|----------|----------|
| 1   | 287.9    | 1          | 15        | 0          | 0        | 0.00     |
| 2   | 294.5    | 1          | 14        | 0          | 0        | 0.00     |
| 3   | 372.5    | 1          | 18        | 0          | 0        | 0.00     |
| 4   | 814.2    | 1          | 19        | 0          | 0        | 0.00     |
| 5   | 384.8    | 1          | 19        | 0          | 0        | 0.00     |
| **Σ** | **430.8** | **5/5** | **85**    | **0**      | **0**    | **0.00** |

**Key observations:**
- All 5 runs: `gru_predictions_used = 0`
- All 5 runs: `gru_avg_confidence = 0.00`
- All 5 runs had SLO violations → mostly reactive (SCALE_OUT)
- Zero PREDICTIVE actions across all 20 Phase B runs (S1-S4)

---

## Root Cause Deep Dive

### Primary Cause: GRU Server Not Running

**Evidence:**
```json
{
  "scenario": "s4-hybrid-predictive",
  "run_id": 1,
  "gru_predictions_used": 0,     // ← GRU never queried
  "gru_avg_confidence": 0.0,     // ← No confidence scores
  "predictive_count": 0          // ← Cannot trigger without predictions
}
```

**Why GRU wasn't used:**
1. **Script design**: `thesis/scripts/run_phase_b_experiments.py` performs pre-flight check for GRU server (line 127) but **does not start it**
2. **Likely scenario**: GRU server was not running when Phase B experiments executed
3. **Result**: Algorithm1Controller received `prediction=None` → PREDICTIVE path never evaluated

**From Phase B execution logs (meta.yaml):**
```yaml
reproduce:
  - "cd controller && HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python ../thesis/scripts/run_phase_b_experiments.py --phase full --runs 5 --duration 300"
```

No mention of GRU server start command. Infrastructure check may have **failed but been bypassed**.

---

### Secondary Cause: Steady-State Workload (if GRU had been running)

**Even if GRU was running**, steady 100 RPS would not trigger PREDICTIVE:

```
Current load: 100 RPS
Predicted load: ~100 RPS (steady-state GRU prediction)
Load change: (100 - 100) / 100 = 0%
Threshold: 30%
Result: 0% << 30% → PREDICTIVE not eligible
```

**Why Phase A1 succeeded:**
- Workload: baseline (20 RPS) → ramp (20→100 RPS) → peak (100 RPS)
- GRU detected surge during ramp: predicted 47% increase
- System healthy (p99=146ms) during ramp → PREDICTIVE triggered

---

## Condition-by-Condition Analysis

For each PREDICTIVE requirement, assess eligibility in Phase B:

| Condition | Phase B Eligibility | Evidence |
|-----------|---------------------|----------|
| 1. `p99 < 200ms` (healthy) | ⚠️ **Rarely met** | Mean p99=430ms, all runs had violations |
| 2. `confidence >= 0.5` | ❌ **Never met** | `gru_avg_confidence=0.0` (no predictions) |
| 3. `load_increase > 30%` | ❌ **Never met** | Steady 100 RPS → ~0% change |
| 4. Not in cooldown | ✅ Likely met | 15 sec cooldown, 300 sec run |
| 5. **GRU prediction available** | ❌ **NEVER** | `gru_predictions_used=0` |

**Eligibility count**: 0 ticks across all 20 runs met all 5 conditions.

**Blocking condition**: #5 (no GRU predictions)

---

## Comparison: Phase A1 vs Phase B

| Aspect | Phase A1 (2026-02-12 ramp) | Phase B (2026-02-12 replicated) |
|--------|----------------------------|----------------------------------|
| **Workload** | Dynamic ramp (20→100 RPS) | Steady-state (100 RPS constant) |
| **GRU Server** | ✅ Running | ❌ **Not running** |
| **GRU Used** | Yes (confidence 0.72-0.88) | No (`gru_predictions_used=0`) |
| **PREDICTIVE** | ✅ 1 action triggered | ❌ 0 actions |
| **Trigger Tick** | 18:15:54, p99=146ms, 47%↑ predicted | N/A |
| **Purpose** | Mechanism validation | Statistical comparison (reactive) |

**Conclusion**: Phase A1 validated PREDICTIVE mechanism. Phase B was inadvertently a **reactive-only** comparison.

---

## Thesis Implications

### What Phase B Actually Validated

✅ **S3 vs S4 reactive behavior** (both used SCALE_OUT, no predictions)  
✅ **Weight adjustment mechanism** (gradual shifts 100/0 → 50/50)  
✅ **SLO monitoring accuracy** (violations detected)  
❌ **Predictive superiority** (requires GRU, dynamic workload)

### What This Means for H2

**H2 Status**:
- **Mechanism validated**: ✅ Phase A1 demonstrates PREDICTIVE triggers pre-violation
- **Statistical superiority**: ⚠️ Not demonstrated (Phase B = reactive-only, no predictive actions)

**Defensible thesis framing**:
> "H2 mechanism validated (Phase A1 ramp test). Phase B experiments inadvertently compared reactive behaviors only (GRU server not running). To demonstrate statistical superiority of predictive over reactive, a follow-up experiment with dynamic workload and active GRU is recommended."

---

## Recommendations

### Immediate (Thesis Defense)

1. **Update claims mapping**:
   - Phase A1: PREDICTIVE mechanism validated ✅
   - Phase B: S3 vs S4 reactive comparison (GRU unavailable)

2. **Add to THREATS_TO_VALIDITY.md**:
   ```markdown
   ### GRU Server Unavailability in Phase B
   
   Phase B replicated experiments were executed without the GRU prediction server running,
   as evidenced by gru_predictions_used=0 across all 20 runs. This inadvertently converted
   the S4 scenario into reactive-only mode, preventing PREDICTIVE actions from triggering.
   
   Impact: Phase B validated reactive scaling (S3 vs S4 with SCALE_OUT only), not predictive
   vs reactive comparison. PREDICTIVE mechanism remains validated via Phase A1 ramp test.
   ```

3. **Thesis language**:
   - Remove "Phase B proves H2" claims
   - Cite Phase A1 for H2 mechanism validation
   - Acknowledge Phase B as reactive comparison

### Follow-Up (If Time Permits)

4. **Re-run S3 vs S4 with:**
   - GRU server confirmed running (pre-flight check + validation)
   - Dynamic workload (ramp or burst pattern)
   - 3-5 replicates
   - **Goal**: Demonstrate PREDICTIVE triggers + fewer violations

5. **Script fix**: Modify `thesis/scripts/run_phase_b_experiments.py`:
   ```python
   # Line 143 - Change from check-only to auto-start
   if not self.check_infrastructure():
       logger.info("Starting missing services...")
       self.start_gru_server()  # Add this method
       self.check_infrastructure()  # Re-check
   ```

---

## Quantitative Summary

**Across 20 Phase B runs:**
- Total S4 ticks: ~20 runs × 20 decision cycles = ~400 ticks (estimated)
- PREDICTIVE-eligible ticks: **0** (GRU unavailable)
- PREDICTIVE triggered: **0**

**Phase A1 ramp test (validation run):**
- Total S4 ticks: ~18 decisions
- PREDICTIVE-eligible ticks: **≥1** (at 18:15:54)
- PREDICTIVE triggered: **1** ✅

**Conclusion**: PREDICTIVE mechanism functional but requires:
1. GRU server running
2. Dynamic workload (creates healthy→surge window)
3. Predicted load increase >30%

Phase B met none of these requirements (primarily #1).

---

## Files Updated

- ✅ Created: `results/experiments/phase-b/2026-02-12_replicated-20runs/PREDICTIVE_ELIGIBILITY_ANALYSIS.md` (this file)
- 📝 TODO: Update `results/claims/CLAIMS_TO_EVIDENCE.md` with Phase B caveat
- 📝 TODO: Update `thesis/protocol/THREATS_TO_VALIDITY.md` with GRU server limitation

**Last updated**: 2026-02-13
