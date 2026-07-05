"""Tests for dashboard.normalize — time alignment + aggregation.

Run from repo root: ``uv run pytest apps/dashboard/tests/test_normalize.py -v``
"""

from __future__ import annotations

import pandas as pd

from dashboard.normalize import (
    daemon_to_df,
    prom_to_long,
    provision_to_df,
    resource_to_agg,
    run_t_start,
)


def test_prom_to_long_basic() -> None:
    prom = {"k8s_available_replicas": [[1771411187.8, 1.0], [1771411202.8, 2.0]]}
    df = prom_to_long(prom, t_start=1771411187.8)
    assert list(df.columns) == ["metric", "ts", "dt", "t_rel_sec", "value"]
    assert len(df) == 2
    first = df.iloc[0]
    assert first["metric"] == "k8s_available_replicas"
    assert first["t_rel_sec"] == 0.0
    assert first["value"] == 1.0
    assert df.iloc[1]["t_rel_sec"] == 15.0


def test_prom_to_long_empty() -> None:
    df = prom_to_long(None, t_start=1.0)
    assert df.empty
    assert "t_rel_sec" in df.columns


def test_resource_to_agg_groups_by_backend() -> None:
    records = [
        {"timestamp": 1000.0, "pod": "a", "backend": "k8s", "cpu_millicores": 10.0, "memory_mib": 5.0},
        {"timestamp": 1000.0, "pod": "b", "backend": "k8s", "cpu_millicores": 20.0, "memory_mib": 7.0},
        {"timestamp": 1000.0, "pod": "c", "backend": "knative", "cpu_millicores": 1.0, "memory_mib": 2.0},
    ]
    agg = resource_to_agg(records, t_start=1000.0)
    assert len(agg) == 2
    k8s = agg[agg["backend"] == "k8s"].iloc[0]
    assert k8s["cpu_total"] == 30.0
    assert k8s["mem_total"] == 12.0
    assert k8s["pod_count"] == 2
    assert k8s["t_rel_sec"] == 0.0


def test_run_t_start_prefers_result() -> None:
    assert run_t_start({"t_start": 1771411187.8}, None, None) == 1771411187.8


def test_run_t_start_falls_back_to_daemon() -> None:
    ts = run_t_start(None, "2026-02-18 17:39:17", None)
    assert ts is not None and ts > 1.7e9


def test_provision_to_df() -> None:
    events = [
        [1771411251.6, "pending_detected", {"count": 2}],
        [1771411311.1, "node_created", {"node": "dynamic-workload-2"}],
    ]
    df = provision_to_df(events, t_start=1771411187.8)
    assert len(df) == 2
    assert df.iloc[0]["event"] == "pending_detected"
    assert "count" in df.iloc[0]["detail_json"]


def test_daemon_to_df_adds_relative_seconds() -> None:
    parsed = pd.DataFrame([{"ts_str": "2026-02-18 17:39:17", "event_type": "routing_decision", "action": "SCALE_OUT"}])
    df = daemon_to_df(parsed, t_start=1771411187.8)
    assert "t_rel_sec" in df.columns
    assert len(df) == 1
