# Thesis Evidence Package

**Master's Thesis:** Decision Making and Elastic Scalability Management in Heterogeneous Cloud Environments Based on Workload Prediction

**Repository:** https://github.com/masrurimz/s2-thesis-kubernetes-serverless-integration

---

## Quick Start

### What This Package Contains

This directory contains all evidence, raw data, and reproduction scripts for the thesis validation.

### Key Documents

| Document | Purpose |
|----------|---------|
| `CLAIMS_TO_EVIDENCE.md` | **Start here** - Every claim mapped to raw data |
| `protocol/EXPERIMENT_PROTOCOL.md` | Preregistered experimental design |
| `protocol/THREATS_TO_VALIDITY.md` | Explicit limitations and biases |
| `results/processed/` | Tables, statistics, figures |
| `appendices/` | Detailed logs and excerpts |

---

## Validation Summary

### ✅ Mechanisms Validated

| Mechanism | Status | Evidence |
|-----------|--------|----------|
| GRU Prediction | ✅ | 6.01% RMSE < 10% target |
| Weight Shifting | ✅ | 100/0 → 50/50 documented |
| SLO Monitoring | ✅ | Violations detected correctly |
| PREDICTIVE Action | ✅ | Triggered before violation |
| Hybrid Routing | ✅ | Serverless engages under load |

### ⚠️ Performance Superiority (Environment-Limited)

| Comparison | Result | Reason |
|------------|--------|--------|
| S4 vs S1 (p99) | Not significant | S1 localhost routing bias |
| S4 vs S3 (violations) | No difference | Insufficient load |

**Important:** The lack of statistical significance is an **environment limitation**, not a design flaw. The k3d single-node cluster's localhost routing gives S1 an artificial advantage.

---

## Reproduction

### Prerequisites
- AMD GPU with ROCm support (or CPU fallback)
- k3d cluster running
- HAProxy, Prometheus running
- Python 3.12 with uv

### One-Command Validation

```bash
cd controller
HSA_OVERRIDE_GFX_VERSION=11.0.0 \
  uv run python ../scripts/run_phase_b_experiments.py \
  --phase full --runs 5 --duration 300
```

### H3 (GRU) Only

```bash
cd controller
HSA_OVERRIDE_GFX_VERSION=11.0.0 \
  uv run python -c "from prediction.model_loader import GRUModelLoader; \
  loader=GRUModelLoader(); print(f'RMSE: {loader.rmse}')"
```

### H1/H2 Mechanisms

```bash
# Terminal 1
HSA_OVERRIDE_GFX_VERSION=11.0.0 \
  uv run python -m prediction.prediction_server

# Terminal 2
HSA_OVERRIDE_GFX_VERSION=11.0.0 \
  PREDICTION_CONFIDENCE_THRESHOLD=0.6 \
  uv run python -m daemon.routing_daemon --scenario s4

# Terminal 3 - Generate load
curl -H "Host: test-app.default.127.0.0.1.sslip.io" \
  http://localhost:18082/health
```

---

## Directory Structure

```
thesis/
├── CLAIMS_TO_EVIDENCE.md      # Audit trail (START HERE)
├── README.md                  # This file
├── protocol/
│   ├── EXPERIMENT_PROTOCOL.md # Preregistered design
│   └── THREATS_TO_VALIDITY.md # Explicit limitations
├── results/
│   ├── raw/                   # Unmodified logs
│   │   ├── phase_a1/
│   │   ├── phase_b/
│   │   └── gru_training/
│   ├── processed/             # Tables, statistics
│   └── figures/               # Thesis-ready plots
├── scripts/                   # Reproduction scripts
├── config/                    # Environment configs
└── appendices/                # Detailed excerpts
```

---

## Honest Assessment

See `protocol/THREATS_TO_VALIDITY.md` for explicit acknowledgment of:

1. **k3d single-node limitation** - S1 uses localhost routing (artificially fast)
2. **Load insufficiency** - 100 RPS couldn't stress the system
3. **Synthetic training data** - GRU trained on synthetic traffic

These limitations do **not** invalidate the mechanism validation, but they do limit the performance comparison conclusions.

---

## Contact

For thesis defense questions, refer to `CLAIMS_TO_EVIDENCE.md` for complete audit trail.
