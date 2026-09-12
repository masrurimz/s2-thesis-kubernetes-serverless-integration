"""Tests for dashboard.loader — scanner + per-run loaders.

Run from repo root: ``uv run pytest apps/dashboard/tests/test_loader.py -v``
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from dashboard.loader import (
    _sanitize,
    load_result,
    scan_experiments,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
KNOWN_RUN = (
    REPO_ROOT / "results" / "experiments" / "phase-b" / "2026-02-18_fib34-validation" / "s4-hybrid-predictive_run1"
)


requires_uncommitted_artifacts = pytest.mark.skipif(
    not (KNOWN_RUN / "prometheus").is_dir(),
    reason="the fib34 bundle's prometheus/ export is untracked, so a fresh git worktree does not have it",
)


@requires_uncommitted_artifacts
def test_scan_finds_fib34_run() -> None:
    runs = scan_experiments(REPO_ROOT)
    assert not runs.empty, "scanner returned no runs"
    # The known ERA-2 run must appear with full artifact coverage.
    mask = (runs["batch"] == "2026-02-18_fib34-validation") & (runs["scenario"] == "s4-hybrid-predictive")
    matched = runs[mask]
    assert len(matched) == 1
    row = matched.iloc[0]
    assert row["run_id"] == 1
    assert row["has_result"] is True or row["has_result"] == 1
    assert row["has_prom"] is True or row["has_prom"] == 1
    assert row["era"] == "era2"


def test_load_result_has_p99() -> None:
    result = load_result(KNOWN_RUN)
    assert result is not None
    assert "p99_latency_ms" in result
    # Verified value from the actual file.
    assert math.isclose(result["p99_latency_ms"], 24898.73, rel_tol=1e-4)


def test_load_result_missing_returns_none(tmp_path: Path) -> None:
    assert load_result(tmp_path / "nope") is None


def test_sanitize_replaces_nan_inf() -> None:
    assert _sanitize(float("nan")) is None
    assert _sanitize(float("inf")) is None
    assert _sanitize(float("-inf")) is None
    assert _sanitize(1.5) == 1.5
    assert _sanitize({"a": float("nan"), "b": [float("inf"), 2]}) == {"a": None, "b": [None, 2]}
    assert _sanitize("x") == "x"
