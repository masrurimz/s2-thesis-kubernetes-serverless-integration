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
| `results/reports/INCONSISTENCIES.md` | Known data inconsistencies and explanations |

---

## Validation Summary

### ✅ Mechanisms Validated (H1, H2 — Mechanism-Level)

| Mechanism | Status | Evidence |
|-----------|--------|----------|
| GRU Prediction (H3) | ✅ | 6.01% RMSE < 10% target |
| Weight Shifting (H1) | ✅ | 100/0 → 50/50 documented |
| SLO Monitoring (H1) | ✅ | Violations detected correctly |
| PREDICTIVE Action (H2) | ✅ | Triggered before violation |
| Hybrid Routing (H1) | ✅ | Serverless engages under load |

**Note:** H1 and H2 are validated at the **mechanism level** — each component behaves correctly in isolation and integration. Performance superiority over baselines was not demonstrated due to environment constraints (see below).

### ⚠️ Performance Superiority — Honest Limitation

| Comparison | Result | Reason |
|------------|--------|--------|
| S4 vs S1 (p99) | Not significant | S1 localhost routing bias |
| S4 vs S3 (violations) | No difference | Insufficient load |

**This is a genuine limitation, not a hedged claim.** The k3d single-node cluster routes S1 traffic via localhost, giving it an artificial latency advantage that a real multi-node deployment would not have. At 100 RPS the system was never stressed enough for predictive routing to show measurable benefit over reactive. These results are reported transparently; they do **not** invalidate the mechanism validation above but they do mean we cannot claim performance superiority from this experimental environment.

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
│   ├── figures/               # Thesis-ready plots
│   └── reports/               # Analysis reports & inconsistency notes
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
