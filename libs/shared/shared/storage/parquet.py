"""Atomic Parquet writer/reader with provenance key-value metadata.

Writes to a sibling temporary file, fsyncs, then atomically replaces the
destination via os.replace. Every generated table carries evidence provenance
key-value metadata in its Parquet schema metadata.
"""

import os
import tempfile
from pathlib import Path
from typing import Mapping

import pyarrow as pa
import pyarrow.parquet as pq

#: Required provenance keys written into every Parquet file schema metadata.
REQUIRED_METADATA_KEYS = (
    "evidence_schema_version",
    "experiment_id",
    "scenario",
    "run_id",
    "producer_git_commit",
    "generated_at",
)

#: Provenance the caller must supply. ``evidence_schema_version`` is derived from
#: ``schema_version``, so it is an output of this function rather than an input.
REQUIRED_CALLER_KEYS = (
    "experiment_id",
    "scenario",
    "run_id",
    "producer_git_commit",
    "generated_at",
)


def write_table_parquet(
    table: pa.Table,
    path: Path,
    *,
    schema_version: int,
    metadata: Mapping[str, str],
) -> None:
    """Write a pyarrow Table to Parquet atomically with provenance metadata.

    Merges the caller-supplied *metadata* mapping with ``evidence_schema_version``
    (derived from *schema_version*) and writes the combined key-value metadata
    into the Parquet file schema. The file is written to a sibling temporary
    file, fsynced, then atomically ``os.replace``'d to *path*.

    Args:
        table: pyarrow Table to persist.
        path: Destination file path.
        schema_version: Integer schema version (stored as ``evidence_schema_version``).
        metadata: Provenance key-value pairs (experiment_id, scenario, run_id,
            producer_git_commit, generated_at).

    Raises:
        ValueError: A required provenance key is missing. The keys are the
            reason a table can be traced to the run that produced it, and a
            file written without them looks complete while being unauditable.
    """
    missing = [key for key in REQUIRED_CALLER_KEYS if key not in metadata]
    if missing:
        raise ValueError(
            f"write_table_parquet requires provenance metadata {missing}; "
            f"a table without it cannot be traced to the run that produced it"
        )

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    combined_meta: dict[bytes, bytes] = {
        key.encode(): str(value).encode()
        for key, value in {
            "evidence_schema_version": str(schema_version),
            **metadata,
        }.items()
    }

    table_with_meta = table.replace_schema_metadata(combined_meta)

    # Write to a sibling temp file, fsync, then atomic replace.
    tmp_fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".parquet.tmp", prefix=f".{path.stem}_")
    os.close(tmp_fd)
    tmp_path = Path(tmp_name)
    try:
        with open(tmp_path, "wb") as f:
            pq.write_table(table_with_meta, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


def read_table_parquet(path: Path) -> pa.Table:
    """Read a Parquet file and return the pyarrow Table (including schema metadata)."""
    return pq.read_table(str(path))
