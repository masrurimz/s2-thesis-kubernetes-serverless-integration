"""Tests for dashboard.parser — daemon.log regex extraction.

Run from repo root: ``uv run pytest apps/dashboard/tests/test_parser.py -v``
"""

from __future__ import annotations

from pathlib import Path

from dashboard.parser import parse_daemon_log

REPO_ROOT = Path(__file__).resolve().parents[3]
KNOWN_LOG = (
    REPO_ROOT
    / "results"
    / "experiments"
    / "phase-b"
    / "2026-02-18_fib34-validation"
    / "s4-hybrid-predictive_run1"
    / "daemon.log"
)


def test_parse_scale_out_line() -> None:
    """A fixture SCALE_OUT line must yield action, weights, and p99_est."""
    line = (
        "2026-02-18 17:39:47 [info     ] Algorithm 1: SCALE_OUT         "
        "new_weights={'k3s': 90, 'knative': 10} p99=28594.0 "
        "serverless_enabled=True violation_sec=30\n"
    )
    tmp = Path(__file__).parent / "_fixture_scale.log"
    tmp.write_text(line, encoding="utf-8")
    try:
        df = parse_daemon_log(tmp)
    finally:
        tmp.unlink(missing_ok=True)

    assert not df.empty
    row = df.iloc[0]
    assert row["event_type"] == "routing_decision"
    assert row["action"] == "SCALE_OUT"
    assert int(row["k3s_weight"]) == 90
    assert int(row["knative_weight"]) == 10
    assert float(row["p99_est"]) == 28594.0


def test_parse_weight_change_line() -> None:
    line = (
        "2026-02-18 17:39:48 [info     ] Weights updated                "
        "action=SCALE_OUT reason='SLO violation (28594ms > 200ms) for 30s' "
        "weights={'k3s': 90, 'knative': 10}\n"
    )
    tmp = Path(__file__).parent / "_fixture_weight.log"
    tmp.write_text(line, encoding="utf-8")
    try:
        df = parse_daemon_log(tmp)
    finally:
        tmp.unlink(missing_ok=True)

    assert not df.empty
    row = df.iloc[0]
    assert row["event_type"] == "weight_change"
    assert row["action"] == "SCALE_OUT"
    assert "SLO violation" in str(row["reason"])
    assert int(row["k3s_weight"]) == 90


def test_parse_real_log_has_events() -> None:
    """The known ERA-2 daemon.log must yield many parsed events."""
    if not KNOWN_LOG.is_file():
        import pytest

        pytest.skip(f"missing fixture log: {KNOWN_LOG}")
    df = parse_daemon_log(KNOWN_LOG)
    assert not df.empty
    types = set(df["event_type"].dropna().unique())
    # At least routing decisions and HAProxy latency should be present.
    assert "routing_decision" in types
    assert "haproxy_latency" in types


def test_parse_missing_file_returns_empty() -> None:
    df = parse_daemon_log(Path("/nonexistent/daemon.log"))
    assert df.empty
    assert "ts_str" in df.columns


def test_parse_skips_garbage() -> None:
    tmp = Path(__file__).parent / "_fixture_garbage.log"
    tmp.write_text("this is not a log line\nneither is this\n", encoding="utf-8")
    try:
        df = parse_daemon_log(tmp)
    finally:
        tmp.unlink(missing_ok=True)
    assert df.empty
