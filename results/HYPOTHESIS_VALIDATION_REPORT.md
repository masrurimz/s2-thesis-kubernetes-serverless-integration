# Thesis Hypothesis Validation Report - Mechanism Validation

**Date:** 2026-02-11 (Updated: 2026-02-13)  
**Validation Method:** Automated testing with historical experiment data + Phase B controlled experiments  
**Status:** ✅ H3 Fully Validated | ⚠️ H1/H2 Mechanisms Validated (statistical superiority not established)

> **Canonical honest assessment:** See [`thesis/appendices/PHASE_B_HONEST_ASSESSMENT.md`](../thesis/appendices/PHASE_B_HONEST_ASSESSMENT.md)

---

## Executive Summary

| Hypothesis | Description | Status | Key Evidence |
|------------|-------------|--------|--------------|
| **H3** | GRU provides adequate prediction | ✅ VALIDATED | 6.01% RMSE < 10% target |
| **H1** | Hybrid > Pure approaches | ⚠️ MECHANISM VALIDATED | Statistical superiority not established (p=0.0677) |
| **H2** | Predictive > Reactive | ⚠️ MECHANISM VALIDATED | No difference at tested load; both S3/S4 had 0 violations |

---

## H3: GRU Prediction Adequacy ✅

### Hypothesis Statement
> "GRU provides adequate prediction for the controller (RMSE < 10%)"

### Validation Results

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **RMSE** | **6.01%** | < 10% | ✅ PASS |
| Model Type | PyTorch GRU | - | ✅ Valid |
| Test Confidence | 0.90 | > 0.7 | ✅ High |
| Live Confidence | 0.72 | > 0.6 | ✅ Valid |
| Prediction Latency | ~40ms | < 50ms | ✅ Valid |

### Evidence

```python
# Model Configuration
GRUConfig(
    hidden_size=128,
    num_layers=2,
    sequence_length=60,
    epochs=100,
    learning_rate=0.0005
)

# Test Prediction
Input: [100.0] * 30  # 30 seconds history
Output: 101.59 RPS, Confidence: 0.90
```

### Comparison with Baselines

| Model | RMSE % | vs GRU |
|-------|--------|--------|
| **GRU (Ours)** | **6.01%** | ✅ Best |
| Linear Regression | 11.56% | +92% worse |
| Moving Average | 11.12% | +85% worse |
| Naive (Last Value) | 14.83% | +147% worse |

### Conclusion
✅ **H3 VALIDATED** - GRU achieves 6.01% RMSE, significantly better than the 10% target and all baseline methods.

---

## H1: Hybrid vs Pure Approaches ⚠️

### Hypothesis Statement
> "Hybrid Kubernetes-Serverless routing achieves superior SLO compliance compared to pure Kubernetes or pure serverless deployments"

### Phase B Controlled Experiment (100 RPS, 20 replicated runs)

| Metric | S1 (K8s-Only) | S4 (Hybrid-Predictive) | Result |
|--------|---------------|------------------------|--------|
| Mean p99 | 400.9 ± 103.3 ms | 558.0 ± 228.8 ms | S4 higher (not better) |
| Welch t-test p-value | - | **0.0677** | **NOT significant (p > 0.05)** |
| Cohen's d | - | -0.874 | Large effect, but negative |

**Interpretation:** At 100 RPS in the controlled Phase B experiment, the hybrid system did **not** show statistically significant improvement over K8s-only. S1 actually had lower latency, likely due to localhost routing bias in k3d (see Caveats).

### Stress Test Results (NOT a controlled comparison)

| Scenario | Throughput (RPS) | Error Rate | p95 Latency |
|----------|-----------------|------------|-------------|
| **S1: K8s-Only** | 348 | 79.2% | 5001 ms |
| **S2: Serverless-Only** | 586 | 0.0% | 1.2 ms |
| **S4: Hybrid-Predictive** | 536 | 96.9% | 5000 ms |

> ⚠️ **These stress test numbers used different configurations and load levels across scenarios.** The S4 v4 (536 RPS) vs S1 (348 RPS) comparison is **NOT a valid controlled experiment** — different concurrency levels, durations, and system states were used. These numbers should not be cited as evidence of superiority.

### What WAS Validated (Mechanism)

| Mechanism | Evidence | Status |
|-----------|----------|--------|
| Weight shifting | 100/0 → 50/50 during spikes | ✅ Working |
| Hybrid routing | Traffic split between K8s and serverless | ✅ Working |
| SLO monitoring | Violations detected correctly | ✅ Working |
| Algorithm logic | Priority: SCALE_OUT > PREDICTIVE > OPTIMIZE | ✅ Correct |

### Conclusion
⚠️ **H1 MECHANISM VALIDATED** - The hybrid routing mechanism (weight shifting, traffic splitting, SLO-based decisions) works as designed. However, statistical superiority over K8s-only was **not established** in the controlled Phase B experiment (p=0.0677, not significant at α=0.05).

---

## H2: Predictive vs Reactive ⚠️

### Hypothesis Statement
> "GRU-based predictive routing enables proactive scaling decisions before reactive thresholds trigger, improving SLO compliance"

### Phase B Controlled Experiment (100 RPS, 20 replicated runs)

| Metric | S3 (Hybrid-Reactive) | S4 (Hybrid-Predictive) | Result |
|--------|----------------------|------------------------|--------|
| Mean SLO violations | 0.00 | 0.00 | **No difference** |
| Both scenarios | Zero violations | Zero violations | System handled 100 RPS easily |

**Interpretation:** At 100 RPS, both reactive and predictive approaches achieved zero SLO violations. The load was **not sufficient** to create conditions where predictive routing would demonstrate an advantage over reactive routing.

### Predictive Mechanism Validation (Separate from comparison)

The PREDICTIVE mechanism itself was validated independently:

| Mechanism | Evidence | Status |
|-----------|----------|--------|
| GRU predictions received | Confidence = 0.72 (live) | ✅ Working |
| PREDICTIVE action triggered | At p99=146ms (healthy, before SLO breach) | ✅ Working |
| Preemptive scaling | Triggered before violations occurred | ✅ Working |
| Confidence thresholding | Correctly rejected low-confidence (0.56 < 0.70) | ✅ Working |

### Pipeline Status

```
Prometheus → Data Collector → GRU Server → Algorithm 1 → HAProxy
     ✅            ✅              ✅            ✅          ✅
```

### Conclusion
⚠️ **H2 MECHANISM VALIDATED** - The GRU prediction pipeline is fully operational end-to-end, and PREDICTIVE actions triggered preemptively at p99=146ms (before SLO breach). However, at the controlled 100 RPS load level, no difference between predictive and reactive was observed (both had 0 violations).

---

## Caveats

### 1. Stress Test Numbers Are NOT Controlled Experiments

The throughput numbers from stress tests (S4: 536 RPS, S1: 348 RPS, S3: 383 RPS) were collected under different configurations, concurrency levels, and system states. They should **not** be used as evidence of statistical superiority. Only the Phase B controlled experiment (20 replicated runs at 100 RPS) provides valid comparative data.

### 2. Localhost Routing Bias in k3d

```
S1 (K8s-only): HAProxy → K3s node (single backend on localhost)
               └── test-app pod = localhost loopback
               └── Extremely low latency, no real network hop
```

The local k3d architecture gives S1 an artificial latency advantage. In a real cloud deployment (EKS + Lambda, GKE + Cloud Run), network topology would be more representative and hybrid routing benefits more apparent.

### 3. Insufficient Load at 100 RPS

100 RPS was not enough to stress a single-node k3d cluster. At this load level:
- K8s-only handled everything comfortably
- No SLO violations occurred in any scenario
- The conditions where predictive routing provides advantage (load spikes, capacity saturation) were not reached

### 4. Serverless Cold Start Penalty

S3/S4 hybrid scenarios incur serverless cold start latency that S1 (pure K8s) does not, creating an inherent disadvantage for the hybrid approach in latency measurements at low load.

---

## Overall Validation Summary

### Hypotheses Status

```
┌────────────────────────────────────────────────────────────────────────┐
│              THESIS HYPOTHESIS VALIDATION STATUS                       │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  H3: GRU Adequate           ✅ VALIDATED (6.01% < 10%)               │
│  H1: Hybrid > Pure          ⚠️ MECHANISM VALIDATED (p=0.0677, n.s.)  │
│  H2: Predictive > Reactive  ⚠️ MECHANISM VALIDATED (0 vs 0 viols.)  │
│                                                                        │
│  OVERALL: H3 fully validated; H1/H2 mechanisms validated              │
│           but statistical superiority not established                  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Scientific Contributions Validated

1. **GRU-based Predictor**: Achieves 6.01% RMSE, outperforming all baselines ✅
2. **Hybrid Routing**: Successfully shifts traffic between K8s and serverless ✅
3. **Predictive Control**: Pipeline operational, PREDICTIVE actions trigger preemptively ✅
4. **SLO Awareness**: Algorithm 1 makes routing decisions based on p99 latency ✅

### Data Sources

- **H3**: GRU training on 72 hours synthetic traffic + live validation
- **H1**: Phase B controlled experiment (20 runs, 100 RPS) + stress tests (informational only)
- **H2**: Phase B controlled experiment (20 runs, 100 RPS) + mechanism validation (ramp test)

### Confidence Level

| Hypothesis | Confidence | Reason |
|------------|------------|--------|
| H3 | **High** | Quantitative RMSE measurement, clear pass |
| H1 | **Medium** | Mechanism works; statistical test p=0.0677 (not significant) |
| H2 | **Medium** | Mechanism works; insufficient load to differentiate |

---

## Appendix: Raw Validation Data

### Full JSON Results

**Location:** `results/hypothesis_validation/validation_20260211_232450.json`

Contains complete evidence including:
- All scenario metrics
- Comparison calculations
- Statistical improvements
- Validation timestamps

### Canonical Honest Assessment

**Location:** [`thesis/appendices/PHASE_B_HONEST_ASSESSMENT.md`](../thesis/appendices/PHASE_B_HONEST_ASSESSMENT.md)

Contains the full Phase B analysis including:
- Root cause analysis of why statistical significance was not achieved
- k3d cluster limitations
- Thesis framing recommendations
- Future work suggestions for real cloud validation

### Reproducibility

To reproduce this validation:

```bash
cd /home/zahid/work/master-s2-study/thesis-kubernetes-serverless-integration

# Set GPU environment
export HSA_OVERRIDE_GFX_VERSION=11.0.0

# Run validation
sg render -c "cd controller && uv run python ../scripts/validate_all_hypotheses.py"
```

---

**Report Generated:** 2026-02-11 (Updated: 2026-02-13)  
**Validator Version:** 1.0.0  
**Status:** H3 fully validated; H1/H2 mechanisms validated but statistical superiority not established
