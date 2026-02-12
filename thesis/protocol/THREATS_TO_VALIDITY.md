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

## Secondary Threat: Load Insufficiency

### The Problem

100 RPS was insufficient to create conditions where:
- S1 would violate SLOs
- Predictive scaling would demonstrate advantage

### Evidence

| Scenario | SLO Violations at 100 RPS |
|----------|---------------------------|
| S1 | 0 |
| S2 | 0 |
| S3 | 0 |
| S4 | 0 |

**Result:** No room to demonstrate that predictive reduces violations (both had zero).

### Root Cause

Single-node local cluster with loopback routing can handle higher load than distributed cloud deployment. The local testbed is **oversized** for the chosen load.

### Mitigation

1. Acknowledged in honest assessment
2. Framed as "mechanism validation" not "performance superiority"
3. Outline cloud deployment plan for future work

---

## Tertiary Threat: Synthetic Training Data

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
