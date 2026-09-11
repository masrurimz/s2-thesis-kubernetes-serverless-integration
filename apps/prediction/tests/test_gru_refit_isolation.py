"""Final-refit blindness for GRUPredictor: ``val_ratio=0.0`` sees nothing past ``train_end``.

The study's final refit calls ``train(full_df, val_ratio=0.0, train_end=val_end)``
with the *whole* series, so the region past the embargo is the untouched test
region. The refit contract promises: fixed epoch budget, no early stopping, no
validation metrics, and no dependence on any slice after ``train_end``. These
tests prove that contract by mutating the post-train region with wild values
and asserting the fit is bit-identical.
"""

import numpy as np
import pandas as pd
import torch

from prediction.gru_predictor import GRUConfig, GRUPredictor

SEQ_LEN, HORIZON = 10, 3
N = 300
TRAIN_END = 260
EMBARGO = SEQ_LEN + HORIZON - 1  # 12


def _series(n: int, seed: int = 0) -> np.ndarray:
    rng = np.random.RandomState(seed)
    return (100.0 + rng.uniform(-10, 10, n).cumsum()).astype(np.float32)


def _fit(values: np.ndarray) -> GRUPredictor:
    torch.manual_seed(0)
    predictor = GRUPredictor(
        GRUConfig(
            epochs=3,
            sequence_length=SEQ_LEN,
            prediction_horizon=HORIZON,
            head_dropout=0.0,
            batch_size=16,
        )
    )
    predictor.train(pd.DataFrame({"total_requests": values}), val_ratio=0.0, train_end=TRAIN_END)
    return predictor


def test_final_refit_cannot_see_post_train_region() -> None:
    """Mutating everything past the embargo leaves the refit bit-identical."""
    base = _series(N)
    mutated = base.copy()
    mutated[TRAIN_END + EMBARGO :] = (
        np.random.RandomState(7).uniform(0.0, 1_000_000.0, N - TRAIN_END - EMBARGO).astype(np.float32)
    )

    p_base = _fit(base)
    p_mut = _fit(mutated)

    # Fixed budget, no early stopping, and no validation metrics from any
    # slice: every recorded val_loss is nan and no val_rmse was produced.
    assert len(p_base.training_history) == 3
    assert all(np.isnan(h["val_loss"]) for h in p_base.training_history)
    assert p_base.rmse is None and p_base.mae is None

    # No epoch's training loss depends on post-train-end values.
    assert [h["train_loss"] for h in p_base.training_history] == [h["train_loss"] for h in p_mut.training_history]

    # Scaler and split bookkeeping come from the training portion only.
    assert p_mut.scaler_mean == p_base.scaler_mean
    assert p_mut.scaler_std == p_base.scaler_std
    assert p_base.split_indices is not None
    assert p_base.split_indices["train_end"] == TRAIN_END
