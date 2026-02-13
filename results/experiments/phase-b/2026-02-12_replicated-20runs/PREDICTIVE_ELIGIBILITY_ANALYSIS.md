# PREDICTIVE Eligibility Analysis — Phase B

**Date**: 2026-02-13  
**Analysis of**: 20 replicated runs (5 runs × 4 scenarios)  
**Question**: Why did `PREDICTIVE=0` in **all** Phase B runs?  
**Bead**: s2-51z

---

## Executive Summary

**ROOT CAUSE CHAIN** (3 compounding blockers):

| Level | Blocker | Impact |
|-------|---------|--------|
| **PRIMARY** | GRU server not running | prediction=None → PREDICTIVE never evaluated |
| **SECONDARY** | Steady 100 RPS workload | Even with GRU: 0% load change << 30% threshold |
| **TERTIARY** | Decision priority preemption | SCALE_OUT (83%) and OPTIMIZE_COST (3%) checked first |

**PREDICTIVE=0 is an expected and correct result** for Phase B's experimental conditions. The mechanism was validated in Phase A1 with appropriate workload (ramp 20→100 RPS).

---

## Decision Logic Trace

Source: `controller/intelligent_router/algorithm1_controller.py` lines 97-145

```
Algorithm1Controller.make_decision() priority order:
  1. SCALE_OUT:      violation_duration ≥ 30s AND can_adjust    ← checked FIRST
  2. OPTIMIZE_COST:  p99 < 140ms AND can_adjust                 ← checked SECOND
  3. PREDICTIVE:     prediction available AND can_adjust         ← checked THIRD
     └─ _apply_prediction() (lines 245-303):
        a. confidence ≥ 0.5     (prediction_confidence_threshold)
        b. current_load > 0
        c. (predicted - current) / current > 0.3  (30% increase)
  4. MAINTAIN:       default fallback
```

### PREDICTIVE requires ALL of:

| # | Condition | Code Reference | Threshold |
|---|-----------|---------------|-----------|
| 1 | No sustained SLO violation | `make_decision` line 129 | violation_duration < 30s |
| 2 | Not in healthy zone | `make_decision` line 135 | p99 ≥ 140ms |
| 3 | GRU server available | `routing_daemon.py` line 362 | `check_availability() == True` |
| 4 | Load history ≥ 5 points | `routing_daemon.py` line 364 | `len(history) >= 5` |
| 5 | GRU prediction succeeds | `routing_daemon.py` line 366 | `pred_result.success == True` |
| 6 | Confidence ≥ 0.5 | `algorithm1_controller.py` line 256 | `config.prediction_confidence_threshold` |
| 7 | Current load valid | `algorithm1_controller.py` line 259 | `current_load > 0` |
| 8 | Load increase > 30% | `algorithm1_controller.py` line 264 | `config.load_change_threshold` |

**Configuration values** (from `algorithm1_controller.py` lines 28-36 and `slo_monitor.py` lines 21-22):
- `p99_threshold_ms = 200.0`
- `violation_window_sec = 30`
- `healthy_margin = 0.7` → healthy threshold = 140ms
- `prediction_confidence_threshold = 0.5`
- `load_change_threshold = 0.3`
- `cooldown_sec = 15`

---

## Quantitative Condition Analysis

### Per-Condition Eligibility (across ~103 S4 decision ticks)

```
┌─────────────────────────────────┬─────────────┬──────────────────────┐
│ Condition                       │ % Ticks Met │ Blocker Level        │
├─────────────────────────────────┼─────────────┼──────────────────────┤
│ GRU server available            │     0%      │ PRIMARY (fatal)      │
│ Load history ≥ 5 points         │    80%      │ Minor (transient)    │
│ GRU prediction success          │     0%      │ Consequence of above │
│ Confidence ≥ 0.5                │     0%*     │ Consequence of above │
│ Load increase > 30%             │     0%**    │ SECONDARY (design)   │
│ Not preempted by SCALE_OUT      │   ~15%      │ TERTIARY (timing)    │
│ Not preempted by OPTIMIZE_COST  │   ~85%      │ Minor                │
│ ALL conditions met              │     0%      │ TOTAL BLOCK          │
└─────────────────────────────────┴─────────────┴──────────────────────┘

* Would be ~80% if GRU were running (high confidence on steady data)
** Would be 0% even with GRU: steady load → 0% change << 30% threshold
```

### S4 Decision Distribution (5 runs, 103 total ticks)

| Action | Count | % | Meaning |
|--------|-------|---|---------|
| SCALE_OUT | 85 | 83% | SLO violations (cold-start period) |
| MAINTAIN | 15 | 15% | Within range, no action needed |
| OPTIMIZE_COST | 3 | 3% | Healthy state, reduce serverless |
| PREDICTIVE | 0 | 0% | GRU unavailable + no load increase |

---

## Blocker Deep Dive

### PRIMARY: GRU Server Not Running

**Evidence**: `gru_predictions_used=0` and `gru_avg_confidence=0.00` in ALL 20 runs.

| S4 Run | gru_predictions_used | gru_avg_confidence | predictive_count |
|--------|---------------------|-------------------|-----------------|
| 1 | 0 | 0.00 | 0 |
| 2 | 0 | 0.00 | 0 |
| 3 | 0 | 0.00 | 0 |
| 4 | 0 | 0.00 | 0 |
| 5 | 0 | 0.00 | 0 |

**Code path** (`routing_daemon.py` lines 359-378):
```python
prediction = None  # Default
if self.scenario_config.use_predictions and self.gru_client.check_availability():
    # ← check_availability() returned False (GRU server not running)
    # prediction stays None → make_decision() skips _apply_prediction()
    history = list(self._load_history)
    if len(history) >= 5:
        pred_result = self.gru_client.predict(history, horizon=5)
        # Never reached
```

**Why GRU wasn't running**: `run_phase_b_experiments.py` performs a pre-flight check but does not start the GRU server. The server was likely not started manually before the experiment batch.

### SECONDARY: Steady Workload (No Predicted Increase)

**Even if GRU had been running**, steady 100 RPS produces no load increase signal:

```
current_load  = ~100 RPS (steady)
predicted_load = ~100 RPS (GRU learns steady pattern)
load_change   = (100 - 100) / 100 = 0.0
threshold     = 0.3 (30%)
result        = 0.0 << 0.3 → PREDICTIVE NOT eligible
```

Per-tick analysis (hypothetical with GRU running):
- 20 ticks per run × 5 runs = ~100 ticks
- Ticks with valid prediction: ~80 (after 5-tick warmup)
- Ticks with load_increase > 30%: **0** (steady load = 0% change)

### TERTIARY: Decision Priority Preemption

PREDICTIVE is checked **third** in the priority chain. Even in the narrow p99 band where it could fire (140-200ms), it must compete with:

- **SCALE_OUT** (83% of ticks): Fires during cold-start spike when p99 > 200ms
- **OPTIMIZE_COST** (3% of ticks): Fires when p99 < 140ms (healthy)
- **MAINTAIN** (15% of ticks): Default when neither fires but still no prediction

The "PREDICTIVE window" (140ms ≤ p99 < 200ms) is narrow and transient with steady load.

---

## Per-Run S4 Results

| Run | p99 (ms) | Violations | SCALE_OUT | OPTIMIZE_COST | MAINTAIN | PREDICTIVE | GRU Used |
|-----|----------|------------|-----------|---------------|----------|------------|----------|
| 1 | 287.9 | 1 | 15 | 1 | 4 | 0 | 0 |
| 2 | 294.5 | 1 | 14 | 1 | 5 | 0 | 0 |
| 3 | 372.5 | 1 | 18 | 1 | 2 | 0 | 0 |
| 4 | 814.2 | 1 | 19 | 0 | 2 | 0 | 0 |
| 5 | 384.8 | 1 | 19 | 0 | 2 | 0 | 0 |
| **Σ** | **430.8 avg** | **5/5** | **85** | **3** | **15** | **0** | **0** |

---

## What Workload WOULD Trigger PREDICTIVE?

PREDICTIVE requires:
1. **Warning zone**: 140ms ≤ p99 < 200ms (not violating, not healthy)
2. **Predicted surge**: load_change > 30% (e.g., 60 RPS → 80+ RPS)
3. **GRU confidence**: ≥ 0.5
4. **GRU server running**: prediction available

**Workloads that would trigger it:**

| Pattern | Current RPS | Predicted RPS | Change | Triggers? |
|---------|------------|--------------|--------|-----------|
| Steady 100 | 100 | ~100 | 0% | ❌ |
| Ramp 20→100 | 60 | 90 | +50% | ✅ |
| Burst (spike) | 50 | 80 | +60% | ✅ |
| Sawtooth | 70 | 100 | +43% | ✅ |
| Diurnal rise | 80 | 110 | +38% | ✅ |

**Phase A1 validation** (successful trigger):
- Workload: 20 → 100 RPS ramp
- Trigger point: p99=146ms, predicted 47% increase, confidence 0.72
- Result: PREDICTIVE fired, pre-positioned serverless capacity before violation

---

## Comparison: Phase A1 vs Phase B

| Aspect | Phase A1 (ramp test) | Phase B (replicated) |
|--------|---------------------|---------------------|
| **Workload** | Dynamic ramp (20→100 RPS) | Steady 100 RPS |
| **GRU Server** | ✅ Running | ❌ Not running |
| **GRU Used** | Yes (conf 0.72-0.88) | No (gru_predictions_used=0) |
| **PREDICTIVE** | ✅ 1 action triggered | ❌ 0 actions |
| **Purpose** | Mechanism validation | Statistical comparison |
| **H2 Status** | Mechanism validated | Reactive-only comparison |

---

## Thesis Implications

### What Phase B Actually Validated

✅ **S3 vs S4 reactive behavior** — both used SCALE_OUT, no predictions  
✅ **Weight adjustment mechanism** — gradual shifts 100/0 → 50/50  
✅ **SLO monitoring accuracy** — violations correctly detected  
❌ **Predictive superiority** — requires GRU + dynamic workload

### Defensible Thesis Framing

> "H2 mechanism validated (Phase A1 ramp test: PREDICTIVE triggered at p99=146ms with 47% predicted load increase). Phase B experiments compared reactive behaviors only—GRU server was unavailable (gru_predictions_used=0 across all 20 runs) and steady 100 RPS workload would produce 0% predicted increase regardless (threshold: 30%). To demonstrate statistical predictive superiority, follow-up experiments with dynamic workload and active GRU are recommended."

### Recommendations

1. **Update CLAIMS_TO_EVIDENCE.md**: Phase A1 for H2 mechanism, Phase B for reactive comparison
2. **Add to THREATS_TO_VALIDITY.md**: GRU server unavailability + steady workload design
3. **If time permits**: Re-run S3 vs S4 with GRU server + ramp workload (3-5 replicates)

---

## Reproduction

```bash
cd controller
uv run python ../results/experiments/phase-b/2026-02-12_replicated-20runs/scripts/predictive_eligibility_analysis.py
```

Machine-readable summary: `predictive_eligibility_summary.json`

---

**Last updated**: 2026-02-13  
**Analysis script**: `scripts/predictive_eligibility_analysis.py`
