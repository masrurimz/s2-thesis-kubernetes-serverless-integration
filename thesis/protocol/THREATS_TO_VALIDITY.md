# Threats to Validity

**Explicit acknowledgment of limitations and biases in the thesis validation.**

---

## Critical Threat: Environment Bias (S1 Baseline)

### The Problem

The k3d single-node cluster creates an **artificial advantage for S1 (K8s-only)**:

```
S1 (K8s-only) routing path:
  HAProxy → 172.19.0.3:30080 (k3d node) → test-app pod
  
  Actual: Both HAProxy and k3d node run on localhost
          Effectively: localhost → localhost (loopback)
          Latency: ~1-2ms base

S4 (Hybrid-Predictive) routing path:
  HAProxy → k3s backend OR knative backend
  
  When serverless engaged: 
    → Knative → Kourier proxy → cold start penalty
    Latency: +50-100ms (cold start) or +5-10ms (warm)
```

### Impact on Results

| Metric | S1 (Artificial) | S4 (Real) | Effect |
|--------|-----------------|-----------|--------|
| Base p99 | ~100-200ms | ~150-300ms | S1 biased low |
| Under load | ~400ms | ~500-800ms | S1 biased low |
| Demonstrated | S1 "faster" | S4 "slower" | Misleading |

**This is NOT a design flaw in the hybrid system.** It is a testbed artifact.

### Mitigation

1. **Explicit documentation** (this file)
2. **Renamed baseline** in thesis: "K8s-only (local loopback, best-case baseline)"
3. **Honest framing**: Performance comparison environment-limited, not system-limited
4. **Mechanism focus**: Emphasize validated mechanisms over biased performance numbers

---

## Secondary Threat: GRU Server Unavailability in Phase B

### The Problem

**GRU prediction server was not running during Phase B replicated experiments** (2026-02-12, 20 runs).

### Evidence

**Quantitative proof** from `experiments_final.json`:
```json
{
  "scenario": "s4-hybrid-predictive",
  "run_id": 1-5,
  "gru_predictions_used": 0,     // ← Zero GRU queries in ALL runs
  "gru_avg_confidence": 0.0,     // ← No confidence scores
  "predictive_count": 0          // ← Cannot trigger without predictions
}
```

**All 20 Phase B runs**: `gru_predictions_used = 0`

### Impact

Phase B experiments inadvertently compared **reactive-only** behaviors:
- S3 (reactive): Used SCALE_OUT based on SLO violations
- S4 (predictive): Also used SCALE_OUT only (no predictions available)
- **Result**: S3 vs S4 comparison tested weight adjustment speed, not predictive vs reactive

**What this means**:
- ✅ H1 (hybrid mechanism): Still validated (weight shifting works)
- ⚠️ H2 (predictive superiority): Not tested in Phase B
- ✅ H2 mechanism: Validated separately in Phase A1 ramp test

### Root Cause

`thesis/scripts/run_phase_b_experiments.py` performs GRU server health check (line 127) but **does not start the server**. Infrastructure check may have been bypassed or failed silently.

### Mitigation

1. **Documented**: Full analysis in `results/experiments/phase-b/.../PREDICTIVE_ELIGIBILITY_ANALYSIS.md`
2. **Claims updated**: Phase B cited for reactive comparison only
3. **H2 evidence**: Phase A1 ramp test validates PREDICTIVE mechanism (p99=146ms, 47% surge predicted, pre-violation trigger)
4. **Recommended follow-up**: Re-run S3 vs S4 with GRU confirmed running + dynamic workload

---

## Tertiary Threat: Load Insufficiency

### The Problem

100 RPS steady-state was insufficient to create conditions where:
- S1 would violate SLOs consistently
- Predictive scaling would demonstrate advantage over reactive

### Evidence

| Scenario | SLO Violations at 100 RPS |
|----------|---------------------------|
| S1 | 4/5 runs (corrected from old claim) |
| S2 | 4/5 runs |
| S3 | 4/5 runs |
| S4 | 5/5 runs |

**Result:** Most runs had violations, but steady-state load → predicted load change ~0% → PREDICTIVE never eligible (requires >30% predicted increase).

**Note**: This threat is **secondary** to GRU unavailability. Even if GRU was running, steady load wouldn't trigger PREDICTIVE.

### Root Cause

1. Single-node local cluster with loopback routing (S1 artificially fast)
2. Steady-state workload (no load variation for GRU to predict)
3. Local testbed oversized for the chosen load

### Mitigation

1. Acknowledged in honest assessment
2. Framed as "mechanism validation" not "performance superiority"
3. Phase A1 used **dynamic workload** (ramp) to validate PREDICTIVE
4. Outline cloud deployment + dynamic workload plan for future work

---

## Quaternary Threat: Synthetic Training Data

### The Problem

GRU model trained on synthetic traffic patterns:
- Diurnal cycles + bursty spikes (hand-crafted)
- Not real-world production traces

### Impact

- May not generalize to production traffic shapes
- Model could overfit to synthetic patterns

### Mitigation

1. Clearly labeled in thesis
2. Validated on held-out synthetic test set (not training data)
3. Live predictions showed good confidence (0.72-0.88)
4. Future work: retrain on production traces

---

## Quinary Threat: Workload Parameterization Sensitivity

### The Problem

The per-request work duration (`duration_ms`) directly determines single-pod saturation capacity and therefore controls which scaling regimes the trace-driven workload exercises.

### Evidence

| Parameter | Initial (v1) | Corrected (v2) |
|-----------|--------------|-----------------|
| `duration_ms` | 5 | 10 |
| Single-pod R_sat | ~145 RPS | ~50 RPS |
| α (1/R_sat) | 0.0069 | 0.02 |
| Peak trace (164 RPS) | 1.13× saturation (1 replica) | 3.28× saturation (4 replicas) |
| Mean trace (73 RPS) | 0.50× saturation (1 replica) | 1.46× saturation (2 replicas) |
| Trace stages needing >1 replica | ~10% | ~85% |

### Impact

Phase B v1 (with `duration_ms=5`) produced a workload where 90% of trace stages fit within a single pod. This meant:
- Algorithm 2 (replica scaling) rarely triggered scale-up
- Algorithm 1 (routing) had no overload condition to route around
- S3 vs S4 comparison was effectively "all scenarios idle" — no differentiation possible

### Root Cause

Saturation calibration was performed but the replay scaling factor $g=33$ was set to match the old R_sat (~145 RPS). The combination of high single-pod capacity and moderate trace replay rates eliminated the multi-pod regime that the experiment was designed to test.

### Lesson Learned

**Always verify that the chosen parameterization places the workload trace in the target scaling regime.** A quick check: compute `max(trace_rps) / R_sat` and `mean(trace_rps) / R_sat`. If both ratios are ≤ 1, the workload will not exercise scaling mechanisms.

### Mitigation

1. **v2 attempt:** Recalibrated to `duration_ms=10` (~50 RPS saturation). However, the busy-loop in `/work` monopolized the single Go thread (`GOMAXPROCS=1`), preventing health checks from responding under overload. HPA saw ~1% CPU because the runtime could not schedule metrics collection. Pods restarted before HPA could react.
2. **v3 (final):** Switched to `/fib?n=32` (~60 RPS saturation). Recursive Fibonacci yields to the Go scheduler between function calls, enabling correct CPU reporting (400-500% under load), stable health checks, and proper HPA/Algorithm 2 scaling.
3. Verified that 85% of ClarkNet stages now exceed single-pod capacity (α=0.0167, peak→4 replicas, mean→2 replicas)
4. Phase B v1 and v2 data preserved as negative results (demonstrates threat)
5. Documented as explicit threat in evaluation plan (Section 3.5.7, threat #12)

---

## Methodological Threats

### Randomization

✅ **Addressed:** Run order randomized in Phase B using `random.shuffle()`

### Replicates

✅ **Addressed:** 5 runs per scenario (n=5), total 20 runs

### Stopping Rule

⚠️ **Fixed duration:** 5 minutes per run (not data-dependent)
- Could miss long-tail behaviors
- Mitigation: Documented as time-limited experiment

### Multiple Comparisons

⚠️ **Not adjusted:** Performed t-tests on multiple metrics (p99, violations, etc.)
- Risk: Family-wise error rate
- Mitigation: Primary metrics pre-registered (p99 for H1, violations for H2)

---

## Threat Summary Table

| Threat | Severity | Mitigation | Thesis Impact |
|--------|----------|------------|---------------|
| S1 localhost bias | **Critical** | Documented + honest framing | Limits performance claims |
| Workload parameterization | **High** | Recalibrated 5ms→10ms; documented | Invalidated Phase B v1; corrected in v2 |
| Load insufficiency | Medium | Acknowledged | Limits predictive advantage proof |
| Synthetic training data | Medium | Clearly labeled | Limits generalization claims |
| Fixed duration | Low | Documented | Minor - 5 min sufficient |
| Multiple comparisons | Low | Primary metrics pre-registered | Minor |

---

## Defensible Thesis Claims

Given these threats, the thesis makes these **validated** claims:

| Claim | Evidence | Status |
|-------|----------|--------|
| GRU achieves <10% RMSE | 6.01% measured | ✅ Strong |
| Predictions trigger in <50ms | ~40ms measured | ✅ Strong |
| PREDICTIVE triggers pre-violation | Logged at p99=146ms | ✅ Strong |
| Weight shifting works | 100/0 → 50/50 documented | ✅ Strong |
| Algorithm priority correct | SCALE_OUT > PREDICTIVE observed | ✅ Strong |
| Hybrid beats K8s-only | NOT claimed | ❌ Not established |
| Predictive beats reactive | NOT claimed | ❌ Not established |

---

## Recommended Thesis Framing

> **"We designed and validated a hybrid Kubernetes-Serverless autoscaling system with GRU-based workload prediction. In a constrained local testbed, we demonstrated that all mechanisms function correctly: the GRU model predicts with 6.01% RMSE and sub-50ms latency, routing decisions shift traffic appropriately, and PREDICTIVE actions trigger before SLO violations. However, due to testbed limitations (localhost routing bias and insufficient load), we could not establish statistically significant performance superiority over baseline approaches. We therefore report these results as environment-limited mechanism validation rather than system-limited performance evaluation."**

This framing is **defensible** for a master's thesis.
