"""Leak-free split guarantees and cell selector for GRUPredictor.

These tests defend the training-protocol invariants added for the horizon-9
study: no window crosses a split boundary (embargo = sequence_length +
horizon - 1 between segments), the fitted scaler depends only on the training
portion, and artifacts record the trained cell while old artifacts default to
"gru".
"""

import numpy as np
import pandas as pd
import pytest

from prediction.gru_predictor import GRUConfig, GRUPredictor

SEQ_LEN = 10
HORIZON = 3
N = 300
TRAIN_END = 200
EMBARGO = SEQ_LEN + HORIZON - 1  # 12
VAL_START = TRAIN_END + EMBARGO
VAL_END = 260


def _series(n: int, seed: int = 0) -> pd.DataFrame:
    rng = np.random.RandomState(seed)
    return pd.DataFrame({"total_requests": 100.0 + rng.uniform(-10, 10, n).cumsum()})


def _window_indices(start: int, end: int) -> set[int]:
    """Every sample index touched by inputs or targets of windows in [start, end)."""
    touched: set[int] = set()
    for i in range(start, end - SEQ_LEN - HORIZON + 1):
        touched.update(range(i, i + SEQ_LEN))
        touched.update(range(i + SEQ_LEN, i + SEQ_LEN + HORIZON))
    return touched


class TestLeakFreeSplits:
    def test_no_train_window_overlaps_val_or_test(self):
        predictor = GRUPredictor(GRUConfig(epochs=1, sequence_length=SEQ_LEN, prediction_horizon=HORIZON))
        df = _series(N)
        predictor.train(df, train_end=TRAIN_END, val_start=VAL_START, val_end=VAL_END)

        split = predictor.split_indices
        assert split is not None
        assert split["embargo"] == EMBARGO
        assert split["val_start"] - split["train_end"] >= EMBARGO

        train_idx = _window_indices(0, split["train_end"])
        val_idx = _window_indices(split["val_start"], split["val_end"])
        test_idx = set(range(split["val_end"], N))

        assert train_idx & val_idx == set() and train_idx & test_idx == set()

    def test_train_rejects_embargo_violation(self):
        predictor = GRUPredictor(GRUConfig(epochs=1, sequence_length=SEQ_LEN, prediction_horizon=HORIZON))
        df = _series(N)
        with pytest.raises(ValueError, match="Embargo violation"):
            predictor.train(df, train_end=TRAIN_END, val_start=TRAIN_END + EMBARGO - 1)

    def test_scaler_ignores_validation_perturbation(self):
        config = GRUConfig(epochs=1, sequence_length=SEQ_LEN, prediction_horizon=HORIZON)

        base = _series(N, seed=7)["total_requests"].to_numpy().astype(np.float32)
        perturbed = base.copy()
        perturbed[TRAIN_END:] *= 100.0

        p1 = GRUPredictor(config)
        p1.train(pd.DataFrame({"total_requests": base}), train_end=TRAIN_END, val_start=VAL_START, val_end=VAL_END)
        p2 = GRUPredictor(config)
        p2.train(pd.DataFrame({"total_requests": perturbed}), train_end=TRAIN_END, val_start=VAL_START, val_end=VAL_END)

        assert p2.scaler_mean == p1.scaler_mean and p2.scaler_std == p1.scaler_std


class TestCellSelector:
    def test_default_is_gru(self):
        assert GRUConfig().cell == "gru"

    def test_rejects_unknown_cell(self):
        with pytest.raises(ValueError, match="cell must be"):
            GRUConfig(cell="rnn")

    @pytest.mark.parametrize("cell", ["gru", "lstm"])
    def test_lstm_shares_training_and_serving_contract(self, cell, tmp_path):
        predictor = GRUPredictor(
            GRUConfig(cell=cell, hidden_size=8, epochs=1, sequence_length=SEQ_LEN, prediction_horizon=HORIZON)
        )
        df = _series(80)
        metrics = predictor.train(df)

        assert predictor.is_trained is True
        assert "val_rmse" in metrics

        recent = df["total_requests"].values[-15:]
        result = predictor.predict(recent)
        assert len(result["point_forecasts"]) == HORIZON

        path = tmp_path / f"model_{cell}.pt"
        predictor.save_model(path)
        loaded = GRUPredictor()
        assert loaded.load_model(path) is True
        assert loaded.config.cell == cell

    def test_legacy_artifact_without_cell_defaults_to_gru(self, tmp_path):
        import torch

        from prediction.gru_predictor import ARTIFACT_SCHEMA_VERSION

        config = GRUConfig(hidden_size=8, epochs=1, sequence_length=SEQ_LEN, prediction_horizon=HORIZON)
        predictor = GRUPredictor(config)
        predictor.train(_series(80))
        path = tmp_path / "legacy.pt"
        predictor.save_model(path)

        checkpoint = torch.load(path, weights_only=False)
        checkpoint["metadata"].pop("cell")
        checkpoint["metadata"]["config"].pop("cell")
        checkpoint["metadata"]["schema_version"] = ARTIFACT_SCHEMA_VERSION
        torch.save(checkpoint, path)

        loaded = GRUPredictor()
        assert loaded.load_model(path) is True
        assert loaded.config.cell == "gru"
