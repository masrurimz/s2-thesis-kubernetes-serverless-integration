# Claims to Evidence Mapping

**Thesis Audit Trail** - Every claim maps to raw data and reproduction command.

---

## H1: Hybrid Routing Mechanism

### Claim 1 (Mechanism): Dynamic weight shifting works
- **Metric:** Weight progression over time
- **Raw Data:** `thesis/results/raw/phase_b/` (decision logs and validation results)
- **Evidence:** `results/PREDICTIVE_ACTION_VALIDATION.md` (weight table: 100/0 → 90/10 → ... → 50/50)
- **Reproduce:** `scripts/run_phase_b_experiments.py --scenario s4`
- **Status:** ✅ Validated

### Claim 2 (Mechanism): Serverless backend engages under load
- **Metric:** knative weight > 0 during high load
- **Raw Data:** Daemon Prometheus metrics `routing_daemon_current_weight{backend="knative"}`
- **Evidence:** `results/PHASE_A1_VALIDATION_SUMMARY.md` Section "Weight Progression"
- **Reproduce:** See Claim 1
- **Status:** ✅ Validated

### Claim 3 (Superiority): S4 outperforms S1
- **Metric:** p99 latency S4 vs S1
- **Raw Data:** `thesis/results/raw/phase_b/validation_20260211_232450.json`
- **Evidence:** S1 mean=400.9ms, S4 mean=558.0ms (not significant, p=0.0677)
- **Threat:** S1 uses localhost routing (artificially fast)
- **Status:** ⚠️ Not established (p=0.0677, environment-limited)

---

## H2: Predictive Scaling Mechanism

### Claim 4 (Mechanism): PREDICTIVE action triggers before violation
- **Metric:** PREDICTIVE count > 0 when p99 < 200ms
- **Raw Data:** Excerpted in `results/PREDICTIVE_ACTION_VALIDATION.md` (captured from daemon logs at runtime)
- **Evidence:** `results/PREDICTIVE_ACTION_VALIDATION.md`
  - Timestamp: 2026-02-12 18:15:54
  - action=PREDICTIVE, p99=146ms (healthy)
  - reason='Predicted 47% load increase (confidence: 72%)'
- **Reproduce:** `scripts/run_phase_b_experiments.py --scenario s4` with ramp load
- **Status:** ✅ Validated

### Claim 5 (Superiority): S4 reduces violations vs S3
- **Metric:** SLO violation count comparison
- **Raw Data:** `thesis/results/raw/phase_b/validation_20260211_232450.json`
- **Evidence:** Both S3 and S4 had 0 violations at 100 RPS
- **Threat:** Load too low to create conditions where prediction matters
- **Status:** ⚠️ Not demonstrated (both had 0 violations at 100 RPS)

---

## H3: GRU Prediction Adequacy

### Claim 6: RMSE below 10% target
- **Metric:** Test RMSE percentage
- **Raw Data:** `controller/data/models/gru_model.pt` + training logs
- **Evidence:** `results/GRU_TRAINING_RESULTS.md`
  - Test RMSE: 6.01%
  - Target: < 10%
  - Baseline: Linear Regression 11.56%, Moving Average 11.12%
- **Reproduce:** `scripts/train_gru.py` (if retraining) or load existing model
- **Status:** ✅ Validated

### Claim 7: Live prediction latency acceptable
- **Metric:** Prediction response time
- **Raw Data:** Daemon logs showing `latency_ms` for GRU predictions
- **Evidence:** `results/PHASE_A1_VALIDATION_SUMMARY.md`
  - Latency: ~40ms
  - Target: < 50ms
- **Status:** ✅ Validated

### Claim 8: Confidence scores meaningful
- **Metric:** Confidence values and correlation with accuracy
- **Raw Data:** Captured in daemon logs at runtime (no persistent log file)
- **Evidence:** Range 0.72-0.88 during live predictions
- **Status:** ✅ Validated

---

## Mechanism Validation Summary

| Type | Claim | Evidence Location | Status |
|------|-------|-------------------|--------|
| Mechanism | Weight shifting | `PREDICTIVE_ACTION_VALIDATION.md` | ✅ Validated |
| Mechanism | Serverless engagement | `PHASE_A1_VALIDATION_SUMMARY.md` | ✅ Validated |
| Mechanism | SLO monitoring | `PHASE_A1_VALIDATION_SUMMARY.md` | ✅ Validated |
| Mechanism | Reactive scaling | `PHASE_A1_VALIDATION_SUMMARY.md` | ✅ Validated |
| Mechanism | Predictive trigger | `PREDICTIVE_ACTION_VALIDATION.md` | ✅ Validated |
| Mechanism | GRU inference | `GRU_TRAINING_RESULTS.md` | ✅ Validated |
| Mechanism | Algorithm priority | `PHASE_B_HONEST_ASSESSMENT.md` | ✅ Validated |
| Superiority | S4 outperforms S1 | `PHASE_B_HONEST_ASSESSMENT.md` | ⚠️ Not established (p=0.0677) |
| Superiority | S4 fewer violations than S3 | `PHASE_B_HONEST_ASSESSMENT.md` | ⚠️ Not demonstrated (0 vs 0) |

---

## Performance Comparison Summary

| Comparison | Metric | Result | Significance | Limitation |
|------------|--------|--------|--------------|------------|
| S4 vs S1 | p99 latency | 558ms vs 401ms | p=0.0677, Cohen's d=-0.874 | S1 localhost routing bias |
| S4 vs S3 | Violations | 0 vs 0 | N/A | Insufficient load |
| S2 vs S1 | p99 latency | ~782ms vs ~401ms | Significant | Expected (cold start) |

---

## Reproduction Commands

### H3 (GRU)
```bash
cd controller
HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python -c "
from prediction.model_loader import GRUModelLoader
loader = GRUModelLoader()
print(f'RMSE: {loader.rmse}')
"
```

### H1/H2 Mechanisms
```bash
cd controller
# Terminal 1: Prediction server
HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python -m prediction.prediction_server

# Terminal 2: Routing daemon
HSA_OVERRIDE_GFX_VERSION=11.0.0 PREDICTION_CONFIDENCE_THRESHOLD=0.6 \
  uv run python -m daemon.routing_daemon --scenario s4-hybrid-predictive

# Terminal 3: Generate load
curl -H "Host: test-app.default.127.0.0.1.sslip.io" http://localhost:18082/health
```

### Full Phase B
```bash
cd controller
HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python ../scripts/run_phase_b_experiments.py \
  --phase full --runs 5 --duration 300
```

---

## Threats to Validity

### Environment Bias (Critical)
- **Issue:** k3d single-node cluster means S1 traffic is localhost loopback
- **Impact:** S1 baseline artificially fast; cannot demonstrate hybrid superiority
- **Mitigation:** Documented as environment limitation, not design flaw

### Load Insufficiency
- **Issue:** 100 RPS insufficient to stress system
- **Impact:** Both S3 and S4 maintained SLOs; no room to show predictive benefit
- **Mitigation:** Acknowledged in honest assessment

### Synthetic Training Data
- **Issue:** GRU trained on synthetic traffic patterns, not real ClarkNet/Calgary traces as originally proposed
- **Impact:** May not generalize to real-world traces
- **Mitigation:** Clearly labeled; model validated on held-out synthetic test set. ClarkNet/Calgary parquets in `data/processed/` were used for model comparison evaluation (RMSE benchmarking), not GRU training

---

## Files by Category

### Raw Evidence
- `controller/data/models/gru_model.pt` - Trained model
- `thesis/results/raw/phase_b/validation_20260211_232450.json` - Phase B validation results
- `thesis/results/raw/phase_a1/` - Phase A1 validation results
- `/tmp/routing_daemon.log` - Decision logs (ephemeral; excerpted in `PREDICTIVE_ACTION_VALIDATION.md`)

### Processed Results
- `thesis/results/processed/` - Tables, statistics
- `thesis/figures/` - Thesis-ready plots

### Training Data Note
- GRU was trained on **synthetic data** (generated traffic patterns), not real ClarkNet/Calgary traces as originally proposed in the thesis methodology
- Processed ClarkNet/Calgary parquets exist in `data/processed/` but were used for **model comparison evaluation** (RMSE benchmarking against linear regression / moving average), not for GRU training

### Protocol Documentation
- `thesis/protocol/EXPERIMENT_PROTOCOL.md` - Preregistered design
- `thesis/protocol/THREATS_TO_VALIDITY.md` - Explicit limitations

---

**Last Updated:** 2026-02-13
