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

import json
from pathlib import Path
from typing import Any, Sequence

from pydantic import TypeAdapter, ValidationError

from shared.models.experiment import ExperimentResult, RunManifest
from shared.models.metrics import NodeSample, ResourceSample
from shared.models.provisioning import ProvisionEvent

RESULT_FILE = "result.json"
MANIFEST_FILE = "manifest.json"
PROVISION_EVENTS_FILE = "provision_events.json"
RESOURCE_UTILIZATION_FILE = "resource_utilization.json"
NODE_UTILIZATION_FILE = "node_utilization.json"
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
            "ts": item.get("ts", item.get("et", 0.0)),
            "event": item.get("event", ""),
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
# ---------------------------------------------------------------------------


def read_resource_utilization(run_dir: Path) -> list[ResourceSample]:
    return _RESOURCE_SAMPLES.validate_python(_read_json(run_dir / RESOURCE_UTILIZATION_FILE) or [])


def write_resource_utilization(run_dir: Path, samples: Sequence[ResourceSample]) -> Path:
    return _write_json(run_dir / RESOURCE_UTILIZATION_FILE, [s.model_dump() for s in samples])


def read_node_utilization(run_dir: Path) -> list[NodeSample]:
    return _NODE_SAMPLES.validate_python(_read_json(run_dir / NODE_UTILIZATION_FILE) or [])


def write_node_utilization(run_dir: Path, samples: Sequence[NodeSample]) -> Path:
    return _write_json(run_dir / NODE_UTILIZATION_FILE, [s.model_dump() for s in samples])


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
