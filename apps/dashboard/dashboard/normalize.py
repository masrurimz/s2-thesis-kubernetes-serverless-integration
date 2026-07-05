"""Time alignment and aggregation helpers.

Bridges the raw loaded artifacts into tidy DataFrames sharing a common
relative-seconds axis (``t_rel_sec = ts - t_start``) so that prometheus
series, daemon events, and resource samples can be overlaid in one chart.

``t_start`` resolution priority:
1. ``result.json["t_start"]`` (unix_ts UTC, authoritative)
2. first daemon.log timestamp (naive local, assumed same clock)
3. first prometheus_export series timestamp
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

__all__ = [
    "run_t_start",
    "daemon_to_df",
    "prom_to_long",
    "resource_to_agg",
    "provision_to_df",
]


def _first_prom_ts(prom: dict | None) -> float | None:
    """Return the earliest unix timestamp across all prom series, or None."""
    if not prom:
        return None
    earliest: float | None = None
    for series in prom.values():
        if not isinstance(series, list):
            continue
        for point in series:
            if isinstance(point, (list, tuple)) and len(point) >= 1:
                try:
                    ts = float(point[0])
                except (TypeError, ValueError):
                    continue
                if earliest is None or ts < earliest:
                    earliest = ts
    return earliest


def run_t_start(
    result: dict | None,
    daemon_first_ts_str: str | None,
    prom: dict | None,
) -> float | None:
    """Resolve the run's t_start (unix_ts) using the documented priority."""
    if result and result.get("t_start") is not None:
        try:
            return float(result["t_start"])
        except (TypeError, ValueError):
            pass
    if daemon_first_ts_str:
        try:
            return datetime.fromisoformat(daemon_first_ts_str).timestamp()
        except (ValueError, TypeError):
            pass
    return _first_prom_ts(prom)


def _ts_to_rel_df(ts_series: pd.Series, t_start: float | None) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Given a unix-ts Series and t_start, return (ts, dt_utc, t_rel_sec)."""
    if t_start is None:
        t_start = ts_series.min() if not ts_series.empty else 0.0
    t_rel = ts_series - t_start
    dt = pd.to_datetime(ts_series, unit="s", utc=True)
    return ts_series, dt, t_rel


def daemon_to_df(parsed: pd.DataFrame, t_start: float | None) -> pd.DataFrame:
    """Add ts/dt/t_rel_sec to a parsed daemon events DataFrame.

    The parser leaves ``ts_str`` as a naive local string; we convert it to a
    unix timestamp via ``datetime.fromisoformat`` (same convention as
    ``run_t_start``) so the resulting ``t_rel_sec`` shares the prom axis.
    """
    if parsed.empty:
        out = parsed.copy()
        out["ts"] = pd.Series(dtype="float64")
        out["dt"] = pd.Series(dtype="datetime64[ns, UTC]")
        out["t_rel_sec"] = pd.Series(dtype="float64")
        return out

    df = parsed.copy()
    ts = df["ts_str"].apply(lambda s: _parse_ts_str(s))
    df["ts"] = ts
    df["dt"] = pd.to_datetime(ts, unit="s", utc=True, errors="coerce")
    if t_start is None:
        t_start = ts.min()
    df["t_rel_sec"] = ts - t_start
    return df


def _parse_ts_str(ts_str: Any) -> float:
    """Parse a daemon ts_str to unix_ts; return NaN if unparseable."""
    if not isinstance(ts_str, str):
        return float("nan")
    try:
        return datetime.fromisoformat(ts_str).timestamp()
    except (ValueError, TypeError):
        return float("nan")


def prom_to_long(prom: dict | None, t_start: float | None) -> pd.DataFrame:
    """Melt a prometheus_export dict into a long DataFrame.

    Output columns: metric, ts, dt, t_rel_sec, value.
    Returns an empty DataFrame (with those columns) if prom is None/empty.
    """
    cols = ["metric", "ts", "dt", "t_rel_sec", "value"]
    if not prom:
        return pd.DataFrame(columns=cols)

    records: list[dict] = []
    for metric, series in prom.items():
        if not isinstance(series, list):
            continue
        for point in series:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue
            try:
                ts = float(point[0])
                value = point[1]
            except (TypeError, ValueError):
                continue
            records.append({"metric": metric, "ts": ts, "value": value})

    if not records:
        return pd.DataFrame(columns=cols)

    df = pd.DataFrame(records)
    df["dt"] = pd.to_datetime(df["ts"], unit="s", utc=True)
    if t_start is None:
        t_start = df["ts"].min()
    df["t_rel_sec"] = df["ts"] - t_start
    return df[cols]


def resource_to_agg(records: list[dict] | None, t_start: float | None) -> pd.DataFrame:
    """Aggregate per-pod resource samples by (timestamp, backend).

    Output columns: ts, dt, t_rel_sec, backend, cpu_total, mem_total, pod_count.
    """
    cols = ["ts", "dt", "t_rel_sec", "backend", "cpu_total", "mem_total", "pod_count"]
    if not records:
        return pd.DataFrame(columns=cols)

    df = pd.DataFrame(records)
    if df.empty:
        return pd.DataFrame(columns=cols)

    # Coerce numeric columns defensively.
    df["timestamp"] = pd.to_numeric(df.get("timestamp"), errors="coerce")
    df["cpu_millicores"] = pd.to_numeric(df.get("cpu_millicores"), errors="coerce").fillna(0.0)
    df["memory_mib"] = pd.to_numeric(df.get("memory_mib"), errors="coerce").fillna(0.0)
    df["backend"] = df.get("backend", "unknown").fillna("unknown")

    df = df.dropna(subset=["timestamp"])
    if df.empty:
        return pd.DataFrame(columns=cols)

    agg = (
        df.groupby(["timestamp", "backend"])
        .agg(
            cpu_total=("cpu_millicores", "sum"),
            mem_total=("memory_mib", "sum"),
            pod_count=("cpu_millicores", "size"),
        )
        .reset_index()
        .rename(columns={"timestamp": "ts"})
    )
    agg["dt"] = pd.to_datetime(agg["ts"], unit="s", utc=True)
    if t_start is None:
        t_start = agg["ts"].min()
    agg["t_rel_sec"] = agg["ts"] - t_start
    return agg[cols]


def provision_to_df(events: list | None, t_start: float | None) -> pd.DataFrame:
    """Normalize provision_events.json ([ts, event_name, details]) to a DataFrame.

    Output columns: ts, dt, t_rel_sec, event, detail_json.
    """
    cols = ["ts", "dt", "t_rel_sec", "event", "detail_json"]
    if not events:
        return pd.DataFrame(columns=cols)

    rows: list[dict] = []
    for entry in events:
        if not isinstance(entry, (list, tuple)) or len(entry) < 2:
            continue
        try:
            ts = float(entry[0])
        except (TypeError, ValueError):
            continue
        event = entry[1] if len(entry) > 1 else "unknown"
        detail = entry[2] if len(entry) > 2 else None
        rows.append(
            {
                "ts": ts,
                "event": str(event),
                "detail_json": _detail_to_str(detail),
            }
        )

    if not rows:
        return pd.DataFrame(columns=cols)

    df = pd.DataFrame(rows)
    df["dt"] = pd.to_datetime(df["ts"], unit="s", utc=True)
    if t_start is None:
        t_start = df["ts"].min()
    df["t_rel_sec"] = df["ts"] - t_start
    return df[cols]


def _detail_to_str(detail: Any) -> str:
    if detail is None:
        return ""
    if isinstance(detail, str):
        return detail
    import json

    try:
        return json.dumps(detail, sort_keys=True, default=str)
    except (TypeError, ValueError):
        return str(detail)
