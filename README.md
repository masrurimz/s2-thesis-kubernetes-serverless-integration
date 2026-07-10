# Hybrid K3s-Serverless Architecture with GRU Workload Prediction

Master's thesis: *"Decision Making and Elastic Scalability Management in Heterogeneous Cloud Environments Based on Workload Prediction"*

## Directory Map

| Directory | Purpose |
|-----------|---------|
| `controller/` | Active Python system: routing daemon, GRU prediction, SLO monitoring, autoscaler |
| `scripts/` | Reproduction + analysis scripts (experiment runners, statistics, plotting) |
| `results/` | **Single source of truth** for all experiment evidence (bundles with raw data + reports) |
| `thesis/` | Narrative only: chapters, protocol, appendices |
| `thesis-typst/` | Canonical thesis book (Typst ITS-IF): English-first + dual abstracts |
| `archived/thesis-latex/` | Previous LaTeX (read-only) |
| `infrastructure/` | K3s/K3d, HAProxy, Knative, Prometheus, k6 load tests |
| `data/` | Input datasets: ClarkNet/Calgary HTTP traces, processed parquet |
| `docs/` | Setup guides, specs, deployment docs |
| `archived/` | Curated historical context (read-only) |

## Entry Points

- **Evidence** → [`results/README.md`](results/README.md) — experiment registry, hypothesis coverage
- **Reproduce** → [`scripts/README.md`](scripts/README.md) — all reproduction + analysis scripts
- **Read thesis** → [`thesis-typst/`](thesis-typst/) (Typst, canonical) or markdown under `thesis/chapters/`
- **Claims audit** → [`results/claims/CLAIMS_TO_EVIDENCE.md`](results/claims/CLAIMS_TO_EVIDENCE.md)

## Quick Start

```bash
# Install all dependencies (uv workspace)
uv sync

# Run Phase B experiments
HSA_OVERRIDE_GFX_VERSION=11.0.0 \
  uv run python scripts/run_phase_b_experiments.py --phase full --runs 5 --duration 300

# Start prediction server + routing daemon
HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python -m prediction.prediction_server &
HSA_OVERRIDE_GFX_VERSION=11.0.0 PREDICTION_CONFIDENCE_THRESHOLD=0.6 \
  uv run python -m daemon.routing_daemon --scenario s4-hybrid-predictive

# Run tests
uv run python -m pytest controller/tests/
```

## Tech Stack

- **Python 3.12** (uv workspace, ROCm PyTorch)
- **K3s/K3d** (lightweight Kubernetes)
- **Knative** (serverless functions)
- **HAProxy** (traffic routing)
- **Prometheus** (metrics)
- **k6** (load testing)
