"""GRU hyperparameter optimization using Optuna TPE.

Search space (from literature consensus — Optuna KDD 2019, TPE-GRNN arXiv:2406.02604):
  - hidden_size: {32, 64, 128, 256}
  - num_layers: {1, 2, 3}
  - learning_rate: log-uniform [1e-4, 1e-2]
  - sequence_length: {15, 30, 60, 120}
  - dropout: uniform [0.0, 0.5]

Objective: minimize validation RMSE%.
Uses time-ordered train/val/test splits (70/15/15).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Callable

import numpy as np
import optuna
import structlog

logger = structlog.get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "results" / "experiments" / "tuning"


def _generate_synthetic_data(duration_hours: int = 72) -> np.ndarray:
    """Generate synthetic traffic data for HPO (same as train_gru.py)."""
    from prediction.training.train_gru import generate_realistic_traffic

    np.random.seed(42)
    df = generate_realistic_traffic(duration_hours=duration_hours)
    return df["total_requests"].values.astype(np.float64)


def _load_real_data(dataset: str = "clarknet", resample: str = "5min") -> np.ndarray:
    """Load real ClarkNet/Calgary trace data."""
    data_dir = PROJECT_ROOT / "apps" / "prediction" / "prediction" / "data" / "processed"
    fname = f"{dataset}_real_rps.parquet"
    import pandas as pd

    df = pd.read_parquet(data_dir / fname)
    df = df.resample(resample).sum().fillna(0)
    return df.iloc[:, 0].values.astype(np.float64)


def create_gru_objective(data: np.ndarray) -> Callable[[optuna.Trial], float]:
    """Return Optuna objective function for GRU HPO.

    Args:
        data: 1D array of RPS values (time-ordered).

    Returns:
        Objective function that returns validation RMSE%.
    """

    def objective(trial: optuna.Trial) -> float:
        from prediction.gru_predictor import GRUConfig, GRUPredictor

        # Suggest hyperparameters
        hidden_size = trial.suggest_categorical("hidden_size", [32, 64, 128, 256])
        num_layers = trial.suggest_int("num_layers", 1, 3)
        learning_rate = trial.suggest_float("learning_rate", 1e-4, 1e-2, log=True)
        sequence_length = trial.suggest_categorical("sequence_length", [15, 30, 60, 120])
        dropout = trial.suggest_float("dropout", 0.0, 0.5)

        config = GRUConfig(
            hidden_size=hidden_size,
            num_layers=num_layers,
            learning_rate=learning_rate,
            sequence_length=sequence_length,
            dropout=dropout,
            epochs=100,
            early_stopping_patience=15,
        )

        predictor = GRUPredictor(config=config)

        try:
            result = predictor.train(data, val_ratio=0.15)
        except Exception as e:
            logger.warning("gru_train_failed", error=str(e), trial=trial.number)
            return 1000.0  # Return large value for failed trials

        rmse_pct = result.get("val_rmse_percent", 1000.0)
        logger.info(
            "gru_hpo_trial",
            trial=trial.number,
            rmse_pct=round(rmse_pct, 2),
            hidden_size=hidden_size,
            num_layers=num_layers,
            lr=learning_rate,
            seq_len=sequence_length,
            dropout=round(dropout, 2),
        )

        return rmse_pct

    return objective


def run_gru_hpo(
    n_trials: int = 30,
    data_source: str = "synthetic",
    study_name: str | None = None,
) -> dict:
    """Run Optuna study for GRU hyperparameter optimization.

    Args:
        n_trials: Number of Optuna trials (30 recommended by literature).
        data_source: "synthetic" or "clarknet" or "calgary".
        study_name: Optional name for the Optuna study.

    Returns:
        Dict with best params, best RMSE%, study statistics, and output paths.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    study_name = study_name or f"gru_hpo_{timestamp}"
    output_dir = RESULTS_DIR / f"gru_hpo_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    if data_source == "synthetic":
        data = _generate_synthetic_data()
    elif data_source in ("clarknet", "calgary"):
        data = _load_real_data(dataset=data_source)
    else:
        raise ValueError(f"Unknown data_source: {data_source}")

    logger.info("gru_hpo_start", n_trials=n_trials, data_source=data_source, n_samples=len(data))

    # Create study
    storage = f"sqlite:///{output_dir / 'study.db'}"
    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=42),
        pruner=optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=30),
        study_name=study_name,
        storage=storage,
    )

    objective = create_gru_objective(data)
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    # Save results
    best = study.best_trial
    result = {
        "timestamp": timestamp,
        "data_source": data_source,
        "n_trials": n_trials,
        "best_trial": best.number,
        "best_params": best.params,
        "best_rmse_pct": best.value,
        "all_trials": [
            {
                "number": t.number,
                "params": t.params,
                "value": t.value if t.value is not None else float("inf"),
                "state": str(t.state),
            }
            for t in study.trials
        ],
        "output_dir": str(output_dir),
    }

    with open(output_dir / "study.json", "w") as f:
        json.dump(result, f, indent=2)

    logger.info(
        "gru_hpo_complete",
        best_trial=best.number,
        best_rmse_pct=round(best.value, 2),
        best_params=best.params,
    )

    return result
