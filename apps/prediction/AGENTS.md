# apps/prediction — GRU Prediction Service

## What This Is

Deployable prediction service. FastAPI server serving GRU workload predictions on port 8090. Also contains training scripts and baseline models.

## Module Map

| Module | Purpose |
|--------|---------|
| `server.py` | FastAPI app + Typer CLI entry point (`/health`, `/predict`, `/model/status`, `/model/reload`) |
| `model_loader.py` | `GRUModelLoader` — loads PyTorch/sklearn models, handles padding, confidence |
| `gru_predictor.py` | `GRUPredictor` + `GRUNetwork` — model definition and training loop |
| `training/train_gru.py` | Synthetic data training (RMSE < 10%) |
| `training/train_gru_real.py` | Real ClarkNet/Calgary training (1/5/10-min resolutions) |
| `training/model_comparison.py` | GRU vs baselines comparison |
| `training/baselines/` | Naive, Seasonal Naive, Moving Average, EMA predictors |

## Commands

```bash
uv run thesis-prediction-server --port 8090
uv run thesis prediction serve --port 8090
uv run thesis prediction train --data synthetic
uv run thesis prediction train --data real
```

## Dependencies

- `shared` (models, config)
- FastAPI, uvicorn, torch (ROCm), numpy, pandas, scikit-learn

## Boundaries

- ROCm: set `HSA_OVERRIDE_GFX_VERSION=11.0.0` for GPU training
- Model artifacts (.pt/.joblib) are gitignored, referenced by path
- API models come from `shared.models.prediction`
