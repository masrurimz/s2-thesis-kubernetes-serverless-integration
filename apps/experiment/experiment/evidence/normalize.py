"""Convert the legacy utilization JSON series to the shared Parquet path.

The two per-run time series (``resource_utilization.json``,
``node_utilization.json``) moved to Parquet. This module is the one-shot
migration for the files history already wrote: parse each JSON row into the
typed model, write through the same shared writer the pipeline uses, verify by
reading back through the same shared reader, and only then delete the JSON.
The pipeline writer is exercised by the conversion, so the 663 real files are
the writer's strongest test.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from shared.artifacts import (
    read_node_utilization,
    read_resource_utilization,
    write_node_utilization,
    write_resource_utilization,
)
from shared.models.metrics import NodeSample, ResourceSample


_TIMESTAMP_TOLERANCE = 1e-6


@dataclass(frozen=True)
class _SeriesSpec:
    """One series: its legacy JSON name, model, and the shared writer/reader."""

    legacy_file: str
    name: str
    model: type[ResourceSample] | type[NodeSample]
    writer: Callable[[Path, Sequence[Any]], Path]
    reader: Callable[[Path], list[Any]]


_SERIES = (
    _SeriesSpec(
        legacy_file="resource_utilization.json",
        name="resource",
        model=ResourceSample,
        writer=write_resource_utilization,
        reader=read_resource_utilization,
    ),
    _SeriesSpec(
        legacy_file="node_utilization.json",
        name="node",
        model=NodeSample,
        writer=write_node_utilization,
        reader=read_node_utilization,
    ),
)


@dataclass
class SeriesConversion:
    """One file's conversion outcome, as the CLI report carries it."""

    run: str
    series: str
    status: str  # converted | would-convert | failed
    rows: int = 0
    bytes_before: int = 0
    bytes_after: int = 0
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "run": self.run,
            "series": self.series,
            "status": self.status,
            "rows": self.rows,
            "bytes_before": self.bytes_before,
            "bytes_after": self.bytes_after,
            "error": self.error,
        }


def _parse_source(model: type, json_path: Path) -> tuple[list[Any], str | None]:
    """The file's samples, or the reason it cannot be converted."""
    try:
        rows = json.loads(json_path.read_text())
        if not isinstance(rows, list):
            raise ValueError("not a JSON array")
        return [model(**row) for row in rows], None
    except (OSError, ValueError, TypeError, ValidationError) as exc:
        return [], f"unreadable source: {exc}"


def _verification_error(restored: Sequence[Any], source: Sequence[Any]) -> str | None:
    """Why the read-back differs from the source, or None when it matches.

    The writer sorts by timestamp, so the source is compared in sorted order.
    Values must match exactly; timestamps round-trip through microseconds and
    are compared to within 1e-6.
    """
    if len(restored) != len(source):
        return f"row count {len(restored)} != {len(source)}"
    timestamps = [sample.timestamp for sample in restored]
    if any(later < earlier for earlier, later in zip(timestamps, timestamps[1:], strict=False)):
        return "timestamps are not non-decreasing"
    for restored_sample, source_sample in zip(restored, source, strict=True):
        if abs(restored_sample.timestamp - source_sample.timestamp) > _TIMESTAMP_TOLERANCE:
            return f"timestamp drift near {source_sample.timestamp}"
        if restored_sample.model_dump(exclude={"timestamp"}) != source_sample.model_dump(exclude={"timestamp"}):
            return f"value mismatch near {source_sample.timestamp}"
    return None


def _convert_one(run_dir: Path, run_label: str, spec: _SeriesSpec, *, apply: bool) -> SeriesConversion:
    json_path = run_dir / spec.legacy_file
    source, error = _parse_source(spec.model, json_path)
    if error is not None:
        # Both files stay; a corrupt source is reported, never deleted.
        return SeriesConversion(run=run_label, series=spec.name, status="failed", rows=len(source), error=error)

    bytes_before = json_path.stat().st_size
    if not apply:
        return SeriesConversion(
            run=run_label,
            series=spec.name,
            status="would-convert",
            rows=len(source),
            bytes_before=bytes_before,
        )

    try:
        parquet_path = spec.writer(run_dir, source)
        restored = spec.reader(run_dir)
    except Exception as exc:  # noqa: BLE003 - any failure leaves both files in place
        return SeriesConversion(run=run_label, series=spec.name, status="failed", rows=len(source), error=str(exc))

    mismatch = _verification_error(restored, sorted(source, key=lambda sample: sample.timestamp))
    if mismatch is not None:
        return SeriesConversion(
            run=run_label,
            series=spec.name,
            status="failed",
            rows=len(source),
            bytes_before=bytes_before,
            bytes_after=parquet_path.stat().st_size if parquet_path.is_file() else 0,
            error=f"verification failed: {mismatch}",
        )

    json_path.unlink()
    return SeriesConversion(
        run=run_label,
        series=spec.name,
        status="converted",
        rows=len(restored),
        bytes_before=bytes_before,
        bytes_after=parquet_path.stat().st_size,
    )


def normalize_series_artifacts(results_root: Path, *, apply: bool = False) -> dict[str, Any]:
    """Convert the legacy utilization JSON series under ``results_root``.

    A run directory that already has the Parquet and no JSON never appears:
    the walk is over the JSON names, so a second run is a no-op. With
    ``apply=False`` nothing is written; the report says what a conversion
    would do.
    """
    experiments_root = results_root / "experiments"
    conversions: list[SeriesConversion] = []
    for spec in _SERIES:
        for json_path in sorted(experiments_root.glob(f"**/{spec.legacy_file}")):
            run_dir = json_path.parent
            conversions.append(_convert_one(run_dir, str(run_dir.relative_to(results_root)), spec, apply=apply))

    converted = [c for c in conversions if c.status == "converted"]
    return {
        "apply": apply,
        "files": [c.as_dict() for c in conversions],
        "converted": len(converted),
        "would_convert": sum(c.status == "would-convert" for c in conversions),
        "failed": sum(c.status == "failed" for c in conversions),
        "rows": sum(c.rows for c in conversions if c.status in {"converted", "would-convert"}),
        "bytes_before": sum(c.bytes_before for c in conversions),
        "bytes_after": sum(c.bytes_after for c in converted),
    }
