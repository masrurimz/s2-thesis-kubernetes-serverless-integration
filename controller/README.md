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

## Components

| Package | Purpose | Status |
|---------|---------|--------|
| `prediction_engine/` | Traffic prediction with linear regression | 🔧 Needs validation |
| `intelligent_router/` | HAProxy weight adjustment + decision logging | 🔧 Needs validation |
| `monitoring_v2/` | Enhanced monitoring (stub) | 🔴 Not implemented |

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Prediction      │    │ Intelligent     │    │   HAProxy       │
│ Engine          │───►│ Router          │───►│   (weights)     │
│ (Linear/GRU)    │    │ (Algorithm 1)   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

```bash
cd controller

# Install dependencies
uv sync

# Start prediction server
uv run prediction-server

# Start routing controller
uv run routing-controller
```

## Scripts

| Command | Description |
|---------|-------------|
| `uv run prediction-server` | Start FastAPI prediction API |
| `uv run routing-controller` | Start intelligent routing loop |
| `uv run data-collector` | Collect HAProxy stats |
| `uv run weight-adjuster` | Adjust HAProxy weights |

## Thesis Mapping

- **Algorithm 1** (Routing Controller): `intelligent_router/routing_controller.py`
- **Algorithm 2** (Cluster Controller): Integrated into prediction + routing flow
- **Resource Model** (R = αx + β): `prediction_engine/linear_model.py`
