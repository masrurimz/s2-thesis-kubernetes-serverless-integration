# Controller

Intelligent routing controller for hybrid K8s-Serverless system with workload prediction.

## Configuration

Configuration is managed via `config.py` and `.env`. 

Environment variables in `.env` override defaults:

```bash
# HAProxy Configuration
HAPROXY_HOST=localhost
HAPROXY_SOCKET_PORT=19999
HAPROXY_STATS_PORT=18404
HAPROXY_HTTP_PORT=18082

# GRU Prediction Service
GRU_HOST=localhost
GRU_PORT=8090
```

| Package | Purpose | Status |
|---------|---------|--------|
| `prediction/` | GRU serving, model loading, training, baselines | ✅ Active |
| `prediction/baselines/` | Naive + moving average baselines (H3 comparison) | ✅ Active |
| `intelligent_router/` | HAProxy weight adjustment + decision logging | ✅ Active |
| `daemon/` | Routing daemon (experiment orchestration) | ✅ Active |
| `scaling/` | Cluster controller + K8s scaler | ✅ Active |
| `autoscaler/` | K3d autoscaler | ✅ Active |
| `monitoring_v2/` | SLO monitoring | ✅ Active |
| `workloads/` | k6 runner | ✅ Active |

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Prediction      │    │ Intelligent     │    │   HAProxy       │
│ Engine          │───►│ Router          │───►│   (weights)     │
│ (Linear/GRU)    │    │ (Algorithm 1)   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start (uv workspace — run from repo root)

```bash
uv sync                                    # Install all deps (workspace)

# Start prediction server
uv run gru-prediction-server

# Start routing controller
uv run routing-controller

# Start routing daemon
uv run routing-daemon --scenario s4-hybrid-predictive
```

## Entry Points

| Command | Description |
|---------|-------------|
| `uv run gru-prediction-server` | Start FastAPI GRU prediction API |
| `uv run routing-controller` | Start intelligent routing loop |
| `uv run routing-daemon` | Start routing daemon for experiment scenarios |
| `uv run weight-adjuster` | Adjust HAProxy weights manually |

## ML Models (merged from `ml_models/`)

| Model | Purpose | Location |
|-------|---------|----------|
| GRU | Thesis proposed model (PyTorch, 128 hidden, 2 layers, dropout 0.2) | `prediction/gru_predictor.py` |
| Linear Regression | Sprint 2 baseline | `prediction/model_loader.py` |
| Naive (last value) | Lower bound baseline | `prediction/baselines/naive.py` |
| Moving Average | Simple smoothing baseline | `prediction/baselines/moving_avg.py` |

### Training

```bash
# Train on synthetic data
HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python -m prediction.train_gru

# Train on real ClarkNet/Calgary traces
HSA_OVERRIDE_GFX_VERSION=11.0.0 uv run python -m prediction.train_gru_real
```

## Thesis Mapping

- **Algorithm 1** (Routing Controller): `intelligent_router/routing_controller.py`
- **Algorithm 2** (Cluster Controller): Integrated into prediction + routing flow
- **Resource Model** (R = αx + β): `prediction/model_loader.py`
