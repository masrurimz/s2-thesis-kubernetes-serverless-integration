"""Daemon.log parser — extracts structured events from the structlog text log.

The daemon log is richer than ``prometheus_export.json`` for routing decisions,
GRU predictions, HAProxy observed latency, and weight-change reasons. This
module parses the log line-by-line into a tidy DataFrame.

Parsing is fail-soft: unparseable lines are skipped silently, never raised.
The leading wall-clock timestamp is captured as ``ts_str`` (naive local); the
caller (``normalize.daemon_to_df``) converts to relative seconds anchored on
the run's ``t_start``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

__all__ = ["parse_daemon_log", "PARSER_COLUMNS"]

# Leading timestamp: 2026-02-18 17:39:17
_TS_RE = re.compile(r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")

# Algorithm 1 routing decision (line 37/53/69 in sample):
#   Algorithm 1: SCALE_OUT new_weights={'k3s': 90, 'knative': 10} p99=28594.0 serverless_enabled=True violation_sec=30
_ROUTING_RE = re.compile(
    r"Algorithm 1: (?P<action>SCALE_OUT|SCALE_DOWN|MAINTAIN|PREDICTIVE|OPTIMIZE_COST)\s+"
    r"new_weights=\{'k3s':\s*(?P<k3s>\d+),\s*'knative':\s*(?P<knative>\d+)\}"
    r"(?:\s+p99=(?P<p99>[\d.]+))?"
    r"(?:\s+serverless_enabled=(?P<serverless>\w+))?"
    r"(?:\s+violation_sec=(?P<violation>\d+))?"
)

# Algorithm 2 k8s scaling decision (line 81/100/118):
#   algorithm2_scaling_decision action=SCALE_UP alpha=... current_replicas=1 predicted_load=25.03 ... target_replicas=2
_SCALING_RE = re.compile(
    r"algorithm2_scaling_decision\s+action=(?P<action>\w+)"
    r".*?current_replicas=(?P<current>\d+)"
    r".*?predicted_load=(?P<predicted_load>[\d.]+)"
    r".*?target_replicas=(?P<target>\d+)"
)

# k8s_scale_executed deployment=test-app-warm replicas=2
_SCALE_EXECUTED_RE = re.compile(r"k8s_scale_executed\s+deployment=(?P<deployment>\S+)\s+replicas=(?P<replicas>\d+)")

# GRU prediction received confidence=0.72 latency_ms=222.9 predicted=65
_GRU_RE = re.compile(
    r"GRU prediction received\s+confidence=(?P<confidence>[\d.]+)\s+"
    r"latency_ms=(?P<latency_ms>[\d.]+)\s+predicted=(?P<predicted>\d+)"
)

# HAProxy latency avg_rtime=14297 max_rtime=44765 p99_est=28594
_HAPROXY_RE = re.compile(
    r"HAProxy latency\s+avg_rtime=(?P<avg_rtime>\d+)\s+"
    r"max_rtime=(?P<max_rtime>\d+)\s+p99_est=(?P<p99_est>\d+)"
)

# Weights updated action=SCALE_OUT reason='SLO violation (28594ms > 200ms) for 30s' weights={'k3s': 90, 'knative': 10}
_WEIGHTS_RE = re.compile(
    r"Weights updated\s+action=(?P<action>\w+)\s+reason='(?P<reason>[^']*)'\s+"
    r"weights=\{'k3s':\s*(?P<k3s_w>\d+),\s*'knative':\s*(?P<knative_w>\d+)\}"
)

# Knative cold start events (warning lines)
_KNATIVE_COLD_RE = re.compile(
    r"Knative pre-warm returned non-200\s+cold_start_ms=(?P<cold_start>[\d.]+)\s+status=(?P<status>\d+)"
)


PARSER_COLUMNS = [
    "ts_str",
    "event_type",
    "action",
    "p99_est",
    "k3s_weight",
    "knative_weight",
    "current_replicas",
    "target_replicas",
    "predicted_load",
    "gru_confidence",
    "gru_predicted",
    "reason",
    "cold_start_ms",
    "raw",
]


def _empty_row(ts_str: str, raw: str) -> dict:
    """Build a row with all columns defaulted to None."""
    row = {col: None for col in PARSER_COLUMNS}
    row["ts_str"] = ts_str
    row["raw"] = raw
    return row


def _try_match(line: str) -> dict | None:
    """Attempt every pattern against one log line; return a row or None."""
    ts_match = _TS_RE.match(line)
    if not ts_match:
        return None
    ts_str = ts_match.group("ts")

    # Routing decision (Algorithm 1)
    m = _ROUTING_RE.search(line)
    if m:
        row = _empty_row(ts_str, line)
        row["event_type"] = "routing_decision"
        row["action"] = m.group("action")
        row["k3s_weight"] = int(m.group("k3s"))
        row["knative_weight"] = int(m.group("knative"))
        row["p99_est"] = float(m.group("p99")) if m.group("p99") else None
        return row

    # k8s scaling decision (Algorithm 2)
    m = _SCALING_RE.search(line)
    if m:
        row = _empty_row(ts_str, line)
        row["event_type"] = "scaling_decision"
        row["action"] = m.group("action")
        row["current_replicas"] = int(m.group("current"))
        row["target_replicas"] = int(m.group("target"))
        row["predicted_load"] = float(m.group("predicted_load"))
        return row

    # scale executed
    m = _SCALE_EXECUTED_RE.search(line)
    if m:
        row = _empty_row(ts_str, line)
        row["event_type"] = "scale_executed"
        row["action"] = m.group("replicas")
        row["reason"] = f"deployment={m.group('deployment')}"
        return row

    # GRU prediction
    m = _GRU_RE.search(line)
    if m:
        row = _empty_row(ts_str, line)
        row["event_type"] = "gru_prediction"
        row["gru_confidence"] = float(m.group("confidence"))
        row["gru_predicted"] = int(m.group("predicted"))
        row["p99_est"] = float(m.group("latency_ms"))  # reuse column for latency_ms
        return row

    # HAProxy latency
    m = _HAPROXY_RE.search(line)
    if m:
        row = _empty_row(ts_str, line)
        row["event_type"] = "haproxy_latency"
        row["p99_est"] = float(m.group("p99_est"))
        return row

    # Weights updated
    m = _WEIGHTS_RE.search(line)
    if m:
        row = _empty_row(ts_str, line)
        row["event_type"] = "weight_change"
        row["action"] = m.group("action")
        row["reason"] = m.group("reason")
        row["k3s_weight"] = int(m.group("k3s_w"))
        row["knative_weight"] = int(m.group("knative_w"))
        return row

    # Knative cold start
    m = _KNATIVE_COLD_RE.search(line)
    if m:
        row = _empty_row(ts_str, line)
        row["event_type"] = "knative_cold_start"
        row["cold_start_ms"] = float(m.group("cold_start"))
        row["p99_est"] = float(m.group("status"))
        return row

    return None


def parse_daemon_log(path: Path | str) -> pd.DataFrame:
    """Parse a daemon.log into a DataFrame of structured events.

    Returns an empty DataFrame (with the canonical columns) if the file is
    missing. Never raises on malformed lines — they are skipped.
    """
    path = Path(path)
    if not path.is_file():
        return pd.DataFrame(columns=PARSER_COLUMNS)

    rows: list[dict] = []
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                row = _try_match(line.rstrip("\n"))
                if row is not None:
                    rows.append(row)
    except OSError:
        return pd.DataFrame(columns=PARSER_COLUMNS)

    return pd.DataFrame(rows, columns=PARSER_COLUMNS)
