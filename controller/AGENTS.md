# controller/ — Active Python System

## What This Is

The intelligent routing controller for the hybrid k3s-serverless architecture. A uv workspace member — dependencies are in the root `pyproject.toml`, not here.

## Quick Commands

```bash
# Run from repo root (uv workspace)
uv sync
uv run python -m pytest controller/tests/
uv run routing-daemon --scenario s4-hybrid-predictive
uv run gru-prediction-server
```

## Module Map

| Package | Purpose |
|---------|---------|
| `prediction/` | GRU serving, model loading, training, baselines (merged from former `ml_models/`) |
| `prediction/baselines/` | Naive + moving average baselines (H3 comparison) |
| `daemon/` | Routing daemon — experiment orchestration |
| `intelligent_router/` | Algorithm 1: HAProxy weight adjustment + decision logging |
| `scaling/` | Cluster controller + K8s scaler |
| `autoscaler/` | K3d autoscaler |
| `monitoring_v2/` | SLO monitoring (Prometheus queries) |
| `workloads/` | k6 runner integration |

## Conventions

- **No `cd controller`** — all commands run from repo root via `uv run`.
- **ROCm torch**: `HSA_OVERRIDE_GFX_VERSION=11.0.0` needed for GPU scripts (`train_gru.py`, `train_gru_real.py`).
- **Entry points** are defined in `pyproject.toml` `[project.scripts]` — use `uv run <name>` not `uv run python -m <module>`.
- **Imports**: use `prediction.gru_predictor`, not `gru_predictor` or `ml_models.gru_predictor`.
- **Tests**: `controller/tests/test_*.py` — some reference archived modules (`prediction_engine`, `experiment_logger`). These are pre-existing failures, not regressions.

## Boundaries

- `pyproject.toml` here is a **workspace member** — deps come from root. Don't add deps here.
- `data/models/` holds trained `.pt` model artifacts — gitignored, not committed.
- Results go in `../results/`, never in `controller/results/` (that directory was deleted).

## What NOT to Edit

- `archived/` — read-only historical context, never modify.
- `results/` — evidence is immutable once created. Only add new bundles.
