# Thesis Results Package

Canonical results directory for the thesis: *"Decision Making and Elastic Scalability Management in Heterogeneous Cloud Environments Based on Workload Prediction"*.

All raw experimental data, processed tables, and validation reports are indexed below.

---

## Directory Structure

```
thesis/results/
├── raw/                        # Unprocessed experimental outputs
│   ├── phase_a1/               # Sprint 3-4 load test results (reactive + predictive)
│   ├── phase_b/                # Sprint 5 hypothesis validation & cost analysis
│   ├── gru_training/           # GRU model training artifacts & comparison data
│   └── stress_tests/           # Stress test logs & summaries
├── processed/                  # Publication-ready tables & summaries
├── reports/                    # Analysis reports & inconsistency tracking
└── README.md                   # This file
```

---

## Raw Data Index

### `raw/phase_a1/` — Load Test Results (Sprints 3–4)

| File | Description | Date |
|------|-------------|------|
| `s3_daemon_20260211_023705.log` | Daemon log from S3 hybrid reactive stress test | 2026-02-11 |
| `stress-s3-hybrid-reactive-summary.json` | k6 summary — S3 hybrid reactive scenario | 2026-02-11 |
| `stress-s4-hybrid-predictive-summary.json` | k6 summary — S4 hybrid predictive scenario | 2026-02-11 |

### `raw/phase_b/` — Hypothesis Validation & Cost Analysis (Sprint 5)

| File | Description | Date |
|------|-------------|------|
| `validation_20260211_232450.json` | Full hypothesis validation results (H1–H4) | 2026-02-11 |
| `cost_analysis_20260211_234542.json` | Cost optimization analysis (hybrid vs pure k3s vs serverless) | 2026-02-11 |

### `raw/gru_training/` — GRU Neural Network Training

| File | Description |
|------|-------------|
| `GRU_TRAINING_RESULTS.md` | Summary of GRU training outcomes and metrics |
| `model_comparison.csv` | Model comparison table (linear regression vs GRU) |
| `model_comparison_REAL.csv` | Model comparison with real ClarkNet/Calgary trace data |
| `README_REAL_RESULTS.md` | Documentation of real-data training methodology & results |

### `raw/stress_tests/` — Stress Test Artifacts

| File | Description | Date |
|------|-------------|------|
| `STRESS_TEST_SUMMARY.md` | Human-readable stress test summary across all scenarios | 2026-02-11 |
| `s4_hybrid_predictive_20260211_024117.log` | Full daemon log from S4 hybrid predictive test | 2026-02-11 |

---

## Processed Data Index

### `processed/` — Publication-Ready Tables

| File | Format | Description |
|------|--------|-------------|
| `model_comparison.csv` | CSV | Model comparison data for programmatic use |
| `model_comparison.md` | Markdown | Model comparison table for documentation |
| `model_comparison.tex` | LaTeX | Model comparison table for thesis document |
| `GRU_TRAINING_RESULTS.md` | Markdown | GRU training results summary |
| `PHASE_A1_VALIDATION_SUMMARY.md` | Markdown | Phase A1 validation summary |

---

## Reports

### `reports/`

| File | Description |
|------|-------------|
| `INCONSISTENCIES.md` | Tracked data inconsistencies and resolution status |

---

## Data Provenance

All raw data originates from experiments run on 2026-02-11. Source locations before consolidation:

| Canonical Path | Original Source |
|----------------|-----------------|
| `raw/phase_b/*` | `results/hypothesis_validation/`, `results/cost_analysis/` |
| `raw/phase_a1/*` | `results/load-tests/` |
| `raw/gru_training/*` | `results/`, `results/tables/`, `data/processed/` |
| `raw/stress_tests/*` | `results/`, `results/load-tests/` |
| `processed/*` | `results/tables/`, `results/processed/` |

---

## Key Metrics (Quick Reference)

- **GRU Prediction RMSE**: <10% target on ClarkNet traces
- **SLO Compliance**: 99th percentile latency <200ms
- **Cost Optimization**: Hybrid routing vs pure k3s vs pure serverless
- **Algorithm 1 Reaction Time**: 5-second SLO violation detection window
