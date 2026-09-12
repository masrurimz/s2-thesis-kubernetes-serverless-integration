"""One read path for the artifacts a run writes.

Every artifact here is written by exactly one producer and read by several
consumers: the run summary, the evidence registry, the experiment CLI, the analysis
CLI and the cost model. Each of them used to open the files itself, which is how a
manifest gained a key one reader never learned, how a cost model came to read fields
no producer wrote, and how a provisioner stream got three different parsers while a
typed model for it sat unused. Readers and writers now live here, and the models are
the shape.

Two rules the functions keep, because they are what a bundle read back from disk
needs rather than what a happy path wants:

* A missing or corrupt file yields the empty value, never a raise. A bundle half
  copied between machines is a normal state, and crashing on it hides the rest.
* A field that carries no reading stays absent. Nothing is defaulted into a number
  a later average would treat as measured.
"""

from __future__ import annotations

import functools
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence, TypeVar

import pyarrow as pa
from pydantic import TypeAdapter, ValidationError

from shared.models.experiment import ExperimentResult, RunManifest
from shared.models.metrics import NodeSample, ResourceSample
from shared.models.provisioning import ProvisionEvent
from shared.storage.parquet import read_table_parquet, write_table_parquet

RESULT_FILE = "result.json"
MANIFEST_FILE = "manifest.json"
PROVISION_EVENTS_FILE = "provision_events.json"
RESOURCE_UTILIZATION_FILE = "resource_utilization.parquet"
NODE_UTILIZATION_FILE = "node_utilization.parquet"
PROMETHEUS_EXPORT_FILE = "prometheus_export.json"

_RESOURCE_SAMPLES = TypeAdapter(list[ResourceSample])
_NODE_SAMPLES = TypeAdapter(list[NodeSample])


def _read_json(path: Path) -> Any | None:
    """Parse a JSON file, or None when it is absent or unreadable."""
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    return path


# ---------------------------------------------------------------------------
# result.json — the typed outcome of one run
# ---------------------------------------------------------------------------


def read_result(run_dir: Path) -> ExperimentResult | None:
    """The run's result, or None when it is missing or does not validate."""
    raw = _read_json(run_dir / RESULT_FILE)
    if not isinstance(raw, dict):
        return None
    try:
        return ExperimentResult(**raw)
    except ValidationError:
        return None


def read_result_dict(run_dir: Path) -> dict:
    """The result as a plain dict, validated through the model. {} when absent.

    The summary renders from a dict; going through the model means a field the
    summary reads is a field the model declares, so a renamed field cannot leave a
    silent gap in the table. Only fields the file actually carries are returned:
    a measurement that was never taken must stay absent rather than becoming the
    model's default zero, which the table reports differently.
    """
    result = read_result(run_dir)
    return result.model_dump(exclude_unset=True) if result is not None else {}


def write_result(run_dir: Path, result: ExperimentResult) -> Path:
    return _write_json(run_dir / RESULT_FILE, result.model_dump())


def result_validation_error(run_dir: Path) -> str | None:
    """Why this run's result was rejected, for a caller that reports it.

    The reader returns None for both "no file" and "bad file"; a validate command
    that swallowed the difference would tell an operator nothing about a broken run.
    """
    raw = _read_json(run_dir / RESULT_FILE)
    if not isinstance(raw, dict):
        return None
    try:
        ExperimentResult(**raw)
    except ValidationError as exc:
        return str(exc)
    return None


# ---------------------------------------------------------------------------
# manifest.json — the conditions a run started from
# ---------------------------------------------------------------------------


def read_manifest(run_dir: Path) -> RunManifest | None:
    raw = _read_json(run_dir / MANIFEST_FILE)
    if not isinstance(raw, dict):
        return None
    try:
        return RunManifest(**raw)
    except ValidationError:
        return None


def write_manifest(run_dir: Path, manifest: RunManifest) -> Path:
    return _write_json(run_dir / MANIFEST_FILE, manifest.model_dump())


def read_manifest_git_commit(run_dir: Path) -> str:
    """The commit a run ran from, or "" when it cannot be read.

    A manifest written by an older version may not satisfy today's model; the
    commit is the one field every run records and every reader of a bundle needs,
    so it is recovered from the raw document when validation refuses the rest.
    """
    manifest = read_manifest(run_dir)
    if manifest is not None:
        return manifest.git_commit
    raw = _read_json(run_dir / MANIFEST_FILE)
    if isinstance(raw, dict):
        commit = raw.get("git_commit")
        if isinstance(commit, str):
            return commit
    return ""


# ---------------------------------------------------------------------------
# paired_analysis.json — the verdict a bundle's pairs produced
# ---------------------------------------------------------------------------

PAIRED_ANALYSIS_FILE = "paired_analysis.json"


def paired_analysis_path(bundle_dir: Path) -> Path | None:
    """Where this bundle's paired analysis is, whichever layout wrote it.

    The schema puts it under `derived/`, and the paired-run commands write it at the
    bundle root. Both shapes are on disk in `results/experiments/`, so a reader looks
    in both places rather than believing one of them.
    """
    for candidate in (bundle_dir / PAIRED_ANALYSIS_FILE, bundle_dir / "derived" / PAIRED_ANALYSIS_FILE):
        if candidate.exists():
            return candidate
    return None


def read_paired_analysis(bundle_dir: Path) -> dict[str, Any] | None:
    """The bundle's paired analysis, or None when it has none or cannot be read."""
    path = paired_analysis_path(bundle_dir)
    if path is None:
        return None
    payload = _read_json(path)
    return payload if isinstance(payload, dict) else None


# ---------------------------------------------------------------------------
# provision_events.json — the node autoscaler's lifecycle stream
# ---------------------------------------------------------------------------


def read_provision_events(run_dir: Path) -> list[ProvisionEvent]:
    """The run's provisioner events, tolerating the older key spelling.

    Older bundles spell the keys `et` and `d`; both spellings mean the same event,
    and a reader that only knew the new one would silently report an empty node
    lifecycle for those runs.
    """
    raw = _read_json(run_dir / PROVISION_EVENTS_FILE)
    if not isinstance(raw, list):
        return []
    events: list[ProvisionEvent] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        normalised = {
            "ts": item.get("ts", 0.0),
            "event": item.get("event") or item.get("et", ""),
            "data": item.get("data", item.get("d", {})),
        }
        try:
            events.append(ProvisionEvent(**normalised))
        except ValidationError:
            continue
    return events


def write_provision_events(run_dir: Path, log: Sequence[tuple[float, str, dict]]) -> Path:
    return _write_json(
        run_dir / PROVISION_EVENTS_FILE,
        [{"ts": ts, "event": event, "data": data} for ts, event, data in log],
    )


def provision_event_names(events: Sequence[ProvisionEvent]) -> list[str]:
    """Event names in order, the input the engagement rule classifies."""
    return [event.event for event in events]


# ---------------------------------------------------------------------------
# utilization samples — what the pollers saw
#
# Both series are Parquet: a typed UTC-microsecond timestamp column the table
# is sorted by, dictionary-encoded labels, and provenance metadata derived from
# the run directory. The round-trip keeps the models' float epoch-second
# timestamps to within a microsecond.
# ---------------------------------------------------------------------------

_SERIES_SCHEMA_VERSION = 1
_TIMESTAMP_TYPE = pa.timestamp("us", tz="UTC")
_LABEL_COLUMNS = frozenset({"pod", "backend", "node"})
_RESOURCE_COLUMNS = ("timestamp", "pod", "backend", "cpu_millicores", "memory_mib")
_NODE_COLUMNS = ("timestamp", "node", "cpu_cores", "cpu_pct", "memory_mib", "memory_pct")
_RUN_NAME_RE = re.compile(r"^(?P<scenario>.+)_run(?P<run_id>\d+)$")

_SampleT = TypeVar("_SampleT", ResourceSample, NodeSample)


@functools.lru_cache(maxsize=1)
def _repo_head_commit() -> str:
    """The repository HEAD commit, or "unknown" when run outside a work tree."""
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _experiment_id(run_dir: Path) -> str:
    """The bundle directory relative to ``results/experiments/``.

    ``results/experiments/<phase>/<batch>/<run>`` yields ``<phase>/<batch>``;
    a ``raw/`` layout hop (schema v2) is skipped. A run outside that tree (a
    tmp dir in tests) falls back to the parent directory name.
    """
    parts: list[str] = []
    node = run_dir.parent
    while node.name and node.name != "experiments" and node != node.parent:
        parts.append(node.name)
        node = node.parent
    if node.name != "experiments":
        return run_dir.parent.name
    if parts and parts[0] == "raw":
        parts.pop(0)
    return "/".join(reversed(parts))


def series_provenance(run_dir: Path) -> dict[str, str]:
    """Provenance key-value metadata for a run's series Parquet.

    The same stamp fits any artifact written inside a run directory:
    ``experiment_id`` names the bundle (relative to ``results/experiments/``),
    ``scenario`` and ``run_id`` parse out of the run directory name
    (``s1-k8s-only_run1``), ``producer_git_commit`` prefers the run's own
    manifest snapshot and falls back to the repository HEAD, and
    ``generated_at`` is UTC now in ISO 8601.
    """
    match = _RUN_NAME_RE.match(run_dir.name)
    return {
        "experiment_id": _experiment_id(run_dir),
        "scenario": match.group("scenario") if match else run_dir.name,
        "run_id": match.group("run_id") if match else "",
        "producer_git_commit": read_manifest_git_commit(run_dir) or _repo_head_commit(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _series_table(samples: Sequence[_SampleT], columns: tuple[str, ...]) -> pa.Table:
    rows = [sample.model_dump() for sample in samples]
    arrays: list[pa.Array] = []
    for column in columns:
        values = [row[column] for row in rows]
        if column == "timestamp":
            # float64 epoch seconds carry sub-microsecond residue (.75) that a
            # cast refuses to truncate; rounding to integer microseconds first
            # is exact, and reading back divides to within 1e-6 of the source.
            micros = pa.array([round(value * 1_000_000) for value in values], type=pa.int64())
            arrays.append(micros.cast(_TIMESTAMP_TYPE))
        else:
            arrays.append(pa.array(values, type=pa.string() if column in _LABEL_COLUMNS else pa.float64()))
    return pa.Table.from_arrays(arrays, names=list(columns)).sort_by("timestamp")


def _write_series_parquet(run_dir: Path, samples: Sequence[_SampleT], filename: str, columns: tuple[str, ...]) -> Path:
    path = run_dir / filename
    write_table_parquet(
        _series_table(samples, columns),
        path,
        schema_version=_SERIES_SCHEMA_VERSION,
        metadata=series_provenance(run_dir),
    )
    return path


def _read_series_parquet(run_dir: Path, filename: str, adapter: TypeAdapter) -> list[Any]:
    path = run_dir / filename
    if not path.is_file():
        return []
    try:
        table = read_table_parquet(path)
        micros = table.column("timestamp").cast(pa.int64()).to_pylist()
        rows = table.to_pylist()
        for row, micro in zip(rows, micros, strict=True):
            row["timestamp"] = micro / 1_000_000
        return adapter.validate_python(rows)
    except (OSError, ValueError, KeyError, ValidationError):
        return []


def read_resource_utilization(run_dir: Path) -> list[ResourceSample]:
    """The polled samples, or [] when the file is absent or does not validate."""
    return _read_series_parquet(run_dir, RESOURCE_UTILIZATION_FILE, _RESOURCE_SAMPLES)


def write_resource_utilization(run_dir: Path, samples: Sequence[ResourceSample]) -> Path:
    return _write_series_parquet(run_dir, samples, RESOURCE_UTILIZATION_FILE, _RESOURCE_COLUMNS)


def read_node_utilization(run_dir: Path) -> list[NodeSample]:
    """The node readings, or [] when the file is absent or does not validate."""
    return _read_series_parquet(run_dir, NODE_UTILIZATION_FILE, _NODE_SAMPLES)


def write_node_utilization(run_dir: Path, samples: Sequence[NodeSample]) -> Path:
    return _write_series_parquet(run_dir, samples, NODE_UTILIZATION_FILE, _NODE_COLUMNS)


# ---------------------------------------------------------------------------
# prometheus/prometheus_export.json — the raw series a run exported
# ---------------------------------------------------------------------------


def read_prometheus_export(run_dir: Path) -> dict[str, list[tuple[float, float]]]:
    """Each exported query as (timestamp, value) pairs. {} when absent."""
    raw = _read_json(run_dir / "prometheus" / PROMETHEUS_EXPORT_FILE)
    if not isinstance(raw, dict):
        return {}
    series: dict[str, list[tuple[float, float]]] = {}
    for name, points in raw.items():
        if not isinstance(points, list):
            continue
        pairs: list[tuple[float, float]] = []
        for point in points:
            if isinstance(point, (list, tuple)) and len(point) == 2:
                pairs.append((float(point[0]), float(point[1])))
        series[name] = pairs
    return series
