# apps/prediction

Deployable GRU workload prediction service: FastAPI server on port 8090, model loading, training scripts, and baseline predictors.

## Module map

Paths relative to `apps/prediction/`. `data/` sits beside the import package, not inside it.

| Path | Responsibility |
|---|---|
| `prediction/server.py` | FastAPI app (`/health`, `/predict`, `/model/status`, `/model/reload`) plus `cli_app` Typer entry (`serve`) |
| `prediction/model_loader.py` | `GRUModelLoader`: locates and loads model artifacts, input padding, confidence |
| `prediction/gru_predictor.py` | `GRUConfig`, `GRUNetwork`, `GRUPredictor`: model definition, training loop, torch/joblib save and load with JSON sidecar |
| `prediction/training/train_gru.py` | Synthetic-data training entry point |
| `prediction/training/train_gru_real.py` | Real-trace training on ClarkNet/Calgary parquet (15 s default, matching the daemon control loop; sweeps 1/5/10-min resolutions) |
| `prediction/training/model_comparison.py` | Linear Regression vs naive baselines comparison; writes LaTeX and Markdown tables |
| `prediction/training/baselines/naive.py` | `NaivePredictor`, `SeasonalNaivePredictor` |
| `prediction/training/baselines/moving_avg.py` | `MovingAveragePredictor`, `ExponentialMovingAveragePredictor` |
| `data/models/` | Model artifacts referenced by path: `gru_model.json` sidecar is tracked; `gru_model.pt` is gitignored by the `*.pt` rule |

## Module direction

- **May import:** `shared` (API models, calibration constants) and third-party deps (fastapi, torch, scikit-learn, typer, joblib). The importlinter layer also permits `infra` and `analysis`, but this package declares no dependency on either.
- **Must never import:** `routing`, `experiment`, `analysis_cli`, `dashboard`, `cli`. They sit above this package in the layer contract (`pyproject.toml` `[tool.importlinter]`); importing them is a boundary violation.
- **Where new code goes:**
  - Serving or model-loading concern → `prediction/server.py` or `prediction/model_loader.py`
  - New training script or baseline predictor → `prediction/training/` (baselines in `training/baselines/`)
  - New model artifact → `apps/prediction/data/models/`, referenced by path, never imported
  - New test → `apps/prediction/tests/`

## Tests

`apps/prediction/tests/`; hermetic, no live tier. 46 tests in `test_gru.py`, `test_baselines.py`, `test_gru_splits.py`, `test_gru_refit_isolation.py`. Run with:

```bash
uv run python -m pytest apps/prediction/tests -q
```

## Commands it contributes

- `thesis-prediction-server` entry point → `prediction.server:cli_app` (`serve` command).
- `thesis prediction serve` and `thesis prediction train` are defined inline in `apps/cli/cli/main.py::_register_prediction`, not in this package. `train` dispatches to `training/train_gru.py` (synthetic) or `training/train_gru_real.py` (real).

## Invariants

- ROCm training on the Radeon 780M iGPU needs `HSA_OVERRIDE_GFX_VERSION=11.0.0`.
- Model artifacts (`.pt`, `.joblib`) are gitignored and referenced by path; the JSON sidecar is tracked.
- API request/response models come from `shared.models.prediction`; never redefine them here.
- Training and serving share one contract: `GRUConfig.cell` selects `gru` or `lstm`, and both cells must keep the same training/serving shape (`test_gru_splits.py::TestCellSelector` enforces this).
