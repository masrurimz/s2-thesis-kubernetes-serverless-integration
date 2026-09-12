"""Application adapter around ``shared.evidence.catalog.EvidenceCatalog``.

Resolves the repository ``results/evidence/catalog.duckdb`` location and exposes
read-only query results. Also provides per-artifact legacy Parquet derivation.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
from shared.evidence.catalog import EvidenceCatalog
from shared.storage.parquet import write_table_parquet


def _sha256_file(path: Path) -> str:
    """Compute SHA-256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_commit() -> str:
    """Get the current git commit hash (best-effort)."""
    import subprocess

    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


class EvidenceCatalogAdapter:
    """Application-layer adapter for the DuckDB evidence catalog.

    The catalog at ``results/evidence/catalog.duckdb`` is a local query cache
    rebuilt from canonical artifacts — never a source of truth.
    """

    def __init__(self, results_root: Path) -> None:
        self.results_root = results_root
        self.catalog_path = results_root / "evidence" / "catalog.duckdb"
        # EvidenceCatalog expects the repository root (parent of results/)
        self._catalog = EvidenceCatalog(results_root.parent)

    def refresh(self) -> None:
        """Rebuild the local DuckDB catalog from canonical artifacts."""
        self._catalog.refresh()

    def query(self, sql: str) -> list[dict[str, Any]]:
        """Execute a read-only SQL query against the catalog.

        Returns rows as a list of dicts.
        """
        import duckdb

        con = duckdb.connect(str(self.catalog_path), read_only=True)
        try:
            result = con.execute(sql)
            columns = [d[0] for d in result.description] if result.description else []
            rows = result.fetchall()
            return [dict(zip(columns, row, strict=False)) for row in rows]
        finally:
            con.close()

    def derive_legacy_parquet(
        self,
        source: Path,
        output: Path,
        *,
        artifact_name: str,
    ) -> Path:
        """Derive a provenance-preserving Parquet from a legacy CSV or JSONL.

        Args:
            source: Path to the legacy CSV or JSONL file.
            output: Output Parquet path (must be under results/experiments).
            artifact_name: Name of the artifact for metadata.

        Returns:
            The output Parquet path.

        Raises:
            ValueError: If source is outside results/experiments or unsupported format.
        """
        source = source.resolve()
        output = output.resolve()
        experiments_root = (self.results_root / "experiments").resolve()

        # Security: reject paths outside results/experiments
        try:
            output.relative_to(experiments_root)
        except ValueError:
            raise ValueError(f"Output path must be under results/experiments, got: {output}") from None
        try:
            source.relative_to(experiments_root)
        except ValueError:
            raise ValueError(f"Source path must be under results/experiments, got: {source}") from None

        suffix = source.suffix.lower()
        if suffix == ".csv":
            df = pd.read_csv(source)
        elif suffix == ".jsonl":
            df = pd.read_json(source, lines=True)
        else:
            raise ValueError(f"Unsupported source format: {suffix}. Only CSV and JSONL are accepted.")

        table = pa.Table.from_pandas(df)

        source_sha = _sha256_file(source)
        output.parent.mkdir(parents=True, exist_ok=True)

        write_table_parquet(
            table,
            output,
            schema_version=1,
            metadata={
                "evidence_schema_version": "1",
                "experiment_id": str(output.parent.parent.name),
                "scenario": "",
                "run_id": "",
                "producer_git_commit": _git_commit(),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "source_path": str(source),
                "source_sha256": source_sha,
                "conversion_version": "1",
                "artifact_name": artifact_name,
            },
        )

        return output
