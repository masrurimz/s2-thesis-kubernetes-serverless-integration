"""Artifact scanner and per-run JSON loaders for the experiment dashboard.

Reads ``results/experiments/<phase>/<batch>/<scenario>_run<N>/`` and exposes
each artifact as a plain Python object (dict / list). The core scanner and
loaders are cache-free so they can be unit-tested without Streamlit; a
module-level :func:`cached_scan` wrapper is provided for the Streamlit app.

All loaders are defensive: missing files return ``None`` (or ``[]`` for
provision events), and non-finite floats (``NaN``/``Infinity`` produced by
``json.load``) are sanitized to ``None`` so downstream Plotly/pandas rendering
cannot choke.
"""

from __future__ import annotations

import functools
import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

__all__ = [
    "scan_experiments",
    "cached_scan",
    "load_result",
    "load_manifest",
    "load_prom",
    "load_resource",
    "load_provision",
    "load_k6",
    "RunArtifacts",
]

# results/experiments/<phase>/<batch>/<scenario>_run<N>/
_RUN_DIR_RE = re.compile(r"^(?P<scenario>.+)_run(?P<run_id>\d+)$")
_BATCH_DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_")


def _mtime(path: Path) -> float:
    """Return file mtime, or 0.0 if missing (so cache key stays hashable)."""
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _sanitize(obj: Any) -> Any:
    """Recursively replace non-finite floats (NaN/Infinity) with None.

    ``json.load`` accepts the bare tokens ``NaN``/``Infinity`` (a Python
    extension), but Plotly/pandas and strict JSON consumers choke on them.
    """
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_sanitize(v) for v in obj)
    return obj


@functools.lru_cache(maxsize=256)
def _read_json(path_str: str, mtime: float) -> Any | None:
    """Cached JSON reader keyed on (absolute path, mtime). None if missing."""
    path = Path(path_str)
    if not path.is_file():
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def scan_experiments(root: Path) -> pd.DataFrame:
    """Walk ``results/experiments/`` and return one row per run directory.

    Columns: phase, batch, batch_date, scenario, run_id, run_dir, plus boolean
    artifact-coverage flags has_result/has_prom/has_resource/has_provision/
    has_daemon_log/has_k6, and ``era`` ("era2" if has_prom else "era1").
    """
    exp_root = root / "results" / "experiments"
    rows: list[dict[str, Any]] = []
    if not exp_root.is_dir():
        return pd.DataFrame(
            columns=[
                "phase",
                "batch",
                "batch_date",
                "scenario",
                "run_id",
                "run_dir",
                "has_result",
                "has_prom",
                "has_resource",
                "has_provision",
                "has_daemon_log",
                "has_k6",
                "era",
            ]
        )

    for run_dir in sorted(exp_root.glob("*/*/*_run*")):
        if not run_dir.is_dir():
            continue
        name = run_dir.name
        m = _RUN_DIR_RE.match(name)
        if not m:
            continue
        scenario = m.group("scenario")
        run_id = int(m.group("run_id"))
        batch = run_dir.parent.name
        phase = run_dir.parent.parent.name
        date_match = _BATCH_DATE_RE.match(batch)
        batch_date = date_match.group(1) if date_match else ""

        has_result = (run_dir / "result.json").is_file()
        has_prom = (run_dir / "prometheus" / "prometheus_export.json").is_file()
        has_resource = (run_dir / "resource_utilization.json").is_file()
        has_provision = (run_dir / "provision_events.json").is_file()
        has_daemon_log = (run_dir / "daemon.log").is_file()
        has_k6 = bool(list((run_dir / "k6").glob("*.json"))) if (run_dir / "k6").is_dir() else False

        rows.append(
            {
                "phase": phase,
                "batch": batch,
                "batch_date": batch_date,
                "scenario": scenario,
                "run_id": run_id,
                "run_dir": str(run_dir.resolve()),
                "has_result": has_result,
                "has_prom": has_prom,
                "has_resource": has_resource,
                "has_provision": has_provision,
                "has_daemon_log": has_daemon_log,
                "has_k6": has_k6,
                "era": "era2" if has_prom else "era1",
            }
        )

    return pd.DataFrame(rows)


def cached_scan(root: Path) -> pd.DataFrame:
    """Streamlit-friendly cached scan wrapper.

    Uses ``root``'s mtime as the cache key so newly-added runs are picked up on
    a manual refresh. Importing streamlit lazily keeps unit tests import-free.
    """
    try:
        import streamlit as st
    except ImportError:
        return scan_experiments(root)

    mtime = _mtime(root / "results" / "experiments")

    @st.cache_data(ttl=60, max_entries=4)
    def _scan(_root_str: str, _mtime: float) -> pd.DataFrame:
        return scan_experiments(root)

    return _scan(str(root), mtime)


# --- per-run loaders -------------------------------------------------------


def load_result(run_dir: Path | str) -> dict | None:
    """Load ``result.json`` (per-run scalar summary)."""
    run_dir = Path(run_dir)
    path = run_dir / "result.json"
    raw = _read_json(str(path), _mtime(path))
    return _sanitize(raw) if raw is not None else None


def load_manifest(run_dir: Path | str) -> dict | None:
    """Load ``manifest.json`` (experiment configuration)."""
    run_dir = Path(run_dir)
    path = run_dir / "manifest.json"
    raw = _read_json(str(path), _mtime(path))
    return _sanitize(raw) if raw is not None else None


def load_prom(run_dir: Path | str) -> dict | None:
    """Load ``prometheus/prometheus_export.json`` (dict of [ts, value] arrays)."""
    run_dir = Path(run_dir)
    path = run_dir / "prometheus" / "prometheus_export.json"
    raw = _read_json(str(path), _mtime(path))
    return _sanitize(raw) if raw is not None else None


def load_resource(run_dir: Path | str) -> list[dict] | None:
    """Load ``resource_utilization.json`` (per-pod samples)."""
    run_dir = Path(run_dir)
    path = run_dir / "resource_utilization.json"
    raw = _read_json(str(path), _mtime(path))
    return _sanitize(raw) if raw is not None else None


def load_provision(run_dir: Path | str) -> list:
    """Load ``provision_events.json`` (sparse [ts, event, details] tuples).

    Returns ``[]`` for empty/missing files so callers can always iterate.
    """
    run_dir = Path(run_dir)
    path = run_dir / "provision_events.json"
    raw = _read_json(str(path), _mtime(path))
    if raw is None:
        return []
    sanitized = _sanitize(raw)
    return sanitized if isinstance(sanitized, list) else []


def load_k6(run_dir: Path | str) -> dict | None:
    """Load the single k6 handleSummary JSON under ``k6/``."""
    run_dir = Path(run_dir)
    k6_dir = run_dir / "k6"
    if not k6_dir.is_dir():
        return None
    candidates = sorted(k6_dir.glob("*.json"))
    if not candidates:
        return None
    path = candidates[0]
    raw = _read_json(str(path), _mtime(path))
    return _sanitize(raw) if raw is not None else None


# --- batch-level loaders (optional, for ERA1 fallback) --------------------


def load_batch_results(batch_dir: Path | str) -> list[dict] | None:
    """Load ``results_final.json`` at the batch level (ERA 1 fallback)."""
    batch_dir = Path(batch_dir)
    path = batch_dir / "results_final.json"
    raw = _read_json(str(path), _mtime(path))
    return _sanitize(raw) if raw is not None else None


@functools.lru_cache(maxsize=64)
def _parse_daemon_ts(ts_str: str) -> float | None:
    """Parse a daemon.log leading timestamp ``YYYY-MM-DD HH:MM:SS`` to unix.

    Treated as naive local; relative-second alignment handles the rest. Returns
    None if the string does not parse.
    """
    try:
        return datetime.fromisoformat(ts_str).timestamp()
    except (ValueError, TypeError):
        return None


class RunArtifacts:
    """Lazy container bundling all loaded artifacts for one run.

    Provided as a convenience for the app layer; each attribute loads on first
    access so unused artifacts cost nothing.
    """

    def __init__(self, run_dir: Path | str) -> None:
        self.run_dir = Path(run_dir)

    @property
    def result(self) -> dict | None:
        return load_result(self.run_dir)

    @property
    def manifest(self) -> dict | None:
        return load_manifest(self.run_dir)

    @property
    def prom(self) -> dict | None:
        return load_prom(self.run_dir)

    @property
    def resource(self) -> list[dict] | None:
        return load_resource(self.run_dir)

    @property
    def provision(self) -> list:
        return load_provision(self.run_dir)

    @property
    def k6(self) -> dict | None:
        return load_k6(self.run_dir)
