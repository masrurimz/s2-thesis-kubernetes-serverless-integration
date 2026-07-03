# Thesis — Narrative Only

**Master's Thesis:** Decision Making and Elastic Scalability Management in Heterogeneous Cloud Environments Based on Workload Prediction

This directory contains thesis **narrative** (text, protocol, appendices). All experiment evidence lives in [`../results/`](../results/README.md).

---

## Key Documents

| Document | Purpose |
|----------|---------|
| [`../results/README.md`](../results/README.md) | **Start here** — Evidence registry and experiment index |
| [`../results/claims/CLAIMS_TO_EVIDENCE.md`](../results/claims/CLAIMS_TO_EVIDENCE.md) | Every claim mapped to raw data |
| `protocol/EXPERIMENT_PROTOCOL.md` | Preregistered experimental design |
| `protocol/THREATS_TO_VALIDITY.md` | Explicit limitations and biases |
| [`../results/claims/INCONSISTENCIES.md`](../results/claims/INCONSISTENCIES.md) | Known data inconsistencies |

---

## Directory Structure

```
thesis/
├── README.md                  # This file
├── protocol/
│   ├── EXPERIMENT_PROTOCOL.md # Preregistered design
│   └── THREATS_TO_VALIDITY.md # Explicit limitations
└── appendices/
    └── EXPERIMENT_TIMELINE.md # Timeline context
```

**Evidence lives in `../results/`, NOT here.** See [`../results/README.md`](../results/README.md).

---

## Reproduction

```bash
HSA_OVERRIDE_GFX_VERSION=11.0.0 \
  uv run python scripts/run_phase_b_experiments.py --phase full --runs 5 --duration 300
```
