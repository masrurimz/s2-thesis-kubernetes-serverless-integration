"""Window-driven boundary derivation for the leak-free GRU study.

Window 30 (and any window the frozen 38-sample gaps can host) must reproduce
the frozen ClarkNet literals exactly so existing bundles stay reproducible.
Larger windows derive boundaries with embargo = window + horizon - 1 at both
gaps, preserving the train and validation spans, and must keep the replay
window strictly inside the test portion.
"""

import pytest
from experiment.tuning.gru_study import CLARKNET_TOTAL, DEFAULT_HORIZON, build_splits

REPLAY_START, REPLAY_END = 28940, 29020  # ticket-frozen replay window, series index space


def test_window_derives_boundaries_and_window30_is_frozen() -> None:
    """Window 30 reproduces the frozen set; window 120 derives embargo ≥ 128."""
    w30 = build_splits(CLARKNET_TOTAL, 30, DEFAULT_HORIZON, "clarknet")
    assert (w30.train_end, w30.val_start, w30.val_end, w30.test_start) == (22500, 22539, 26205, 26243)

    # 20 also fits the frozen gaps — it must stay on the frozen literals too.
    w20 = build_splits(CLARKNET_TOTAL, 20, DEFAULT_HORIZON, "clarknet")
    assert (w20.train_end, w20.val_start, w20.val_end, w20.test_start) == (22500, 22539, 26205, 26243)

    w120 = build_splits(CLARKNET_TOTAL, 120, DEFAULT_HORIZON, "clarknet")
    assert w120.embargo == 128  # 120 + 9 - 1, the minimum the ticket requires
    assert w120.val_start - w120.train_end >= w120.embargo
    assert w120.test_start - w120.val_end >= w120.embargo
    # Train and validation spans are preserved from the frozen protocol.
    assert w120.train_end == 22500
    assert w120.val_end - w120.val_start == 26205 - 22539
    # The replay window stays strictly inside the derived test portion.
    assert w120.test_start == 26422
    assert w120.test_start <= REPLAY_START
    assert REPLAY_END < CLARKNET_TOTAL

    # A window that cannot leave a test region fails loudly.
    with pytest.raises(ValueError, match="leave no test region"):
        build_splits(CLARKNET_TOTAL, 40000, DEFAULT_HORIZON, "clarknet")
