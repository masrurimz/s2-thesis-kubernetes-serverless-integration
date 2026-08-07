# Thesis — Narrative Only

**Master's Thesis:** Decision Making and Elastic Scalability Management in Heterogeneous Cloud Environments Based on Workload Prediction

This directory contains thesis **narrative** (text, protocol, appendices). All experiment evidence lives in [`../results/`](../results/README.md).

---

## Key Documents

| Document | Purpose |
|----------|---------|
| [`../results/README.md`](../results/README.md) | **Start here** — Evidence registry and experiment index |
| [`../results/claims/FINAL_NUMBERS.md`](../results/claims/FINAL_NUMBERS.md) | Canonical final numbers and evidence tiers |
| [`../results/claims/CLAIMS_TO_EVIDENCE.md`](../results/claims/CLAIMS_TO_EVIDENCE.md) | Every claim mapped to raw data |
| `protocol/EXPERIMENT_PROTOCOL.md` | Final and historical experimental designs |
| `protocol/THREATS_TO_VALIDITY.md` | Explicit limitations and July alignment addendum |
| [`DRIFT_ANALYSIS.md`](DRIFT_ANALYSIS.md) | Proposal-to-delivered defense alignment |
| [`../results/claims/INCONSISTENCIES.md`](../results/claims/INCONSISTENCIES.md) | Known data inconsistencies and superseded bundles |

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

The final lifecycle is staged so that infrastructure, treatment fidelity, and evidence governance are checked explicitly:

```bash
uv run thesis-experiment preflight
uv run thesis-experiment run
uv run thesis-experiment paired-run
uv run thesis-experiment dynamic
uv run thesis-experiment evidence audit
uv run thesis-experiment evidence reconcile --apply
uv run thesis-experiment evidence catalog refresh
uv run thesis-experiment evidence journal --limit 20
```

Use the final evidence files as the source of truth for claims and interpretation:
[`results/claims/FINAL_NUMBERS.md`](../results/claims/FINAL_NUMBERS.md) and
[`DRIFT_ANALYSIS.md`](DRIFT_ANALYSIS.md).
