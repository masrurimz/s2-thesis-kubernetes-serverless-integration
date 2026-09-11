"""Artifact-metadata guarantee for the final refit: validation RMSE, never holdout.

The final refit trains with ``val_ratio=0.0`` and produces no validation
metrics of its own, so ``refit_and_evaluate`` carries the selection fit's
validation RMSE/MAE into the final predictor before saving. The saved artifact
must therefore record the selection fit's validation RMSE — not null (the
regression this defends against) and not the test-region RMSE (the historical
leak surfacing in metadata).
"""

from __future__ import annotations

import json

import numpy as np

from experiment.tuning.gru_study import build_splits, refit_and_evaluate


def test_refit_artifact_records_selection_validation_rmse_not_holdout(tmp_path) -> None:
    rng = np.random.RandomState(3)
    values = (100.0 + rng.uniform(-8, 8, 2200).cumsum()).astype(np.float32)
    splits = build_splits(len(values), 20, 5, "synthetic")
    params = {
        "hidden_size": 16,
        "num_layers": 1,
        "dropout": 0.0,
        "head_dropout": 0.0,
        "learning_rate": 3.8e-4,
        "sequence_length": 20,
    }
    artifact_path = tmp_path / "synthetic_gru_s42.pt"

    record = refit_and_evaluate(
        cell="gru",
        params=params,
        epochs_selected=2,
        values=values,
        splits=splits,
        horizon=5,
        seed=42,
        artifact_path=artifact_path,
        season=5760,
        n_rolling_blocks=1,
    )

    # The sidecar JSON carries the same metadata dict save_model wrote into the .pt.
    meta = json.loads(artifact_path.with_suffix(".json").read_text())

    assert meta["rmse"] is not None, "artifact must not record a null rmse"
    assert meta["mae"] is not None, "artifact must not record a null mae"
    assert meta["rmse"] == record["selection_val_rmse"], "artifact rmse must be the selection fit's validation RMSE"
    assert meta["rmse"] != record["overall"]["rmse"], "artifact rmse must not be the test-region RMSE"
