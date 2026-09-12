"""Local DuckDB evidence catalog — read-only views over canonical artifacts.

The catalog at ``results/evidence/catalog.duckdb`` is a local cache, never an
evidence source. ``refresh()`` drops/recreates only views; it never mutates
canonical JSONL, YAML, JSON, CSV, or Parquet files.

duckdb is imported lazily inside methods so the module loads even when the
dependency is absent (e.g. in a minimal install).
"""

import glob
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from shared.models.evidence import ExperimentRegistryEntry

#: File extensions indexed by ``artifact_index``.
_ARTIFACT_EXTENSIONS: dict[str, str] = {
    ".csv": "csv",
    ".jsonl": "jsonl",
    ".json": "json",
    ".parquet": "parquet",
}


def _duckdb_path_list(paths: list[str]) -> str:
    """Build a SQL list literal for DuckDB read_parquet/read_json_auto."""
    escaped = [p.replace("'", "''") for p in paths]
    return "[" + ", ".join(f"'{p}'" for p in escaped) + "]"


def _duckdb_str(value: str) -> str:
    """Single-quote-escape a string for DuckDB SQL."""
    return "'" + value.replace("'", "''") + "'"


class EvidenceCatalog:
    """Local DuckDB catalog of experiment evidence.

    Args:
        root: Repository root (the directory containing ``results/``).
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.db_path = self.root / "results" / "evidence" / "catalog.duckdb"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Drop and recreate all views from canonical artifacts.

        Creates/replaces only the ``catalog.duckdb`` file and its views.
        Never writes to any canonical source artifact.
        """
        import duckdb

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        wal = self.db_path.with_suffix(".duckdb.wal")
        wal.unlink(missing_ok=True)

        con = duckdb.connect(str(self.db_path))
        try:
            self._refresh_registry_entries(con)
            self._refresh_registry_events(con)
            self._refresh_run_events(con)
            self._refresh_run_results(con)
            self._refresh_timeseries(con)
            self._refresh_artifact_index(con)
            con.close()  # checkpoint to the main db file
        except BaseException:
            con.close()
            raise

    def query(self, sql: str) -> list[dict[str, Any]]:
        """Execute a read-only SQL query against the catalog and return rows as dicts."""
        import duckdb

        con = duckdb.connect(str(self.db_path), read_only=True)
        try:
            result = con.execute(sql)
            columns = [d[0] for d in result.description]
            return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]
        finally:
            con.close()

    # ------------------------------------------------------------------
    # View builders
    # ------------------------------------------------------------------

    def _refresh_registry_entries(self, con: Any) -> None:
        """View ``registry_entries`` from ``results/evidence/registry.yaml``."""
        yaml_path = self.root / "results" / "evidence" / "registry.yaml"
        entries = self._load_registry_yaml(yaml_path)
        tmp = self.db_path.parent / "_registry_entries.jsonl"
        if entries:
            tmp.write_text("\n".join(json.dumps(e, default=str) for e in entries) + "\n")
            con.execute(
                f"CREATE OR REPLACE VIEW registry_entries AS SELECT * FROM read_json_auto({_duckdb_str(str(tmp))})"
            )
        else:
            tmp.unlink(missing_ok=True)
            con.execute("CREATE OR REPLACE VIEW registry_entries AS SELECT * FROM (VALUES (NULL)) t(dummy) WHERE 1=0")

    def _refresh_registry_events(self, con: Any) -> None:
        """View ``registry_events`` from ``results/evidence/registry-events.jsonl``."""
        jsonl_path = self.root / "results" / "evidence" / "registry-events.jsonl"
        if jsonl_path.exists():
            con.execute(
                f"CREATE OR REPLACE VIEW registry_events AS "
                f"SELECT * FROM read_json_auto({_duckdb_str(str(jsonl_path))}, "
                f"format='newline_delimited')"
            )
        else:
            con.execute("CREATE OR REPLACE VIEW registry_events AS SELECT * FROM (VALUES (NULL)) t(dummy) WHERE 1=0")

    def _refresh_run_events(self, con: Any) -> None:
        """View ``run_events`` from ``results/experiments/**/events.jsonl``."""
        pattern = str(self.root / "results" / "experiments" / "**" / "events.jsonl")
        matches = sorted(glob.glob(pattern, recursive=True))
        if matches:
            con.execute(
                f"CREATE OR REPLACE VIEW run_events AS "
                f"SELECT * FROM read_json_auto({_duckdb_path_list(matches)}, "
                f"format='newline_delimited', union_by_name=true)"
            )
        else:
            con.execute("CREATE OR REPLACE VIEW run_events AS SELECT * FROM (VALUES (NULL)) t(dummy) WHERE 1=0")

    def _refresh_run_results(self, con: Any) -> None:
        """View ``run_results`` from ``results/experiments/**/result.json``."""
        pattern = str(self.root / "results" / "experiments" / "**" / "result.json")
        matches = sorted(glob.glob(pattern, recursive=True))
        if matches:
            con.execute(
                f"CREATE OR REPLACE VIEW run_results AS "
                f"SELECT * FROM read_json_auto({_duckdb_path_list(matches)}, "
                f"union_by_name=true)"
            )
        else:
            con.execute("CREATE OR REPLACE VIEW run_results AS SELECT * FROM (VALUES (NULL)) t(dummy) WHERE 1=0")

    def _refresh_timeseries(self, con: Any) -> None:
        """View ``timeseries`` from every Parquet a run directory holds.

        Two homes: the ``raw/`` dumps (``results/experiments/**/raw/**/*.parquet``)
        and the per-run series written beside ``result.json``
        (``results/experiments/**/*_run*/*.parquet``).

        The files hold three different shapes (pod samples, node readings, k6 points),
        so every row also carries ``filename``. Without it a consumer sees a table of
        mostly NULL columns and cannot tell which series a row belongs to.
        """
        # DuckDB doesn't support multiple '**' in one glob, so use Python glob and
        # pass an explicit file list. One pattern covers the whole experiments tree: the
        # ``raw/`` dumps and the per-run series, at any depth. It does not depend on a
        # directory being called ``*_run*``, so a series file written somewhere new is
        # included without editing this list.
        experiments = self.root / "results" / "experiments"
        matches = sorted(glob.glob(str(experiments / "**" / "*.parquet"), recursive=True))
        if matches:
            con.execute(
                f"CREATE OR REPLACE VIEW timeseries AS "
                f"SELECT * FROM read_parquet({_duckdb_path_list(matches)}, "
                f"union_by_name=true, filename=true)"
            )
        else:
            con.execute("CREATE OR REPLACE VIEW timeseries AS SELECT * FROM (VALUES (NULL)) t(dummy) WHERE 1=0")

    def _refresh_artifact_index(self, con: Any) -> None:
        """View ``artifact_index`` from scanning all artifacts under ``results/experiments/``."""
        experiments_root = self.root / "results" / "experiments"
        records = self._scan_artifacts(experiments_root)
        tmp = self.db_path.parent / "_artifact_index.jsonl"
        if records:
            tmp.write_text("\n".join(json.dumps(r) for r in records) + "\n")
            con.execute(
                f"CREATE OR REPLACE VIEW artifact_index AS SELECT * FROM read_json_auto({_duckdb_str(str(tmp))})"
            )
        else:
            tmp.unlink(missing_ok=True)
            con.execute("CREATE OR REPLACE VIEW artifact_index AS SELECT * FROM (VALUES (NULL)) t(dummy) WHERE 1=0")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_registry_yaml(yaml_path: Path) -> list[dict[str, Any]]:
        """Load registry.yaml and normalize to a list of flat dicts.

        Handles common shapes: ``{id: {entry}}``, ``{entries: [...]}``,
        or a bare list. Each entry is validated through ExperimentRegistryEntry
        then re-dumped to a JSON-safe dict for DuckDB.
        """
        if not yaml_path.exists():
            return []

        data: Any = yaml.safe_load(yaml_path.read_text())
        raw_entries: list[dict[str, Any]] = []

        if isinstance(data, dict):
            if "entries" in data and isinstance(data["entries"], list):
                for item in data["entries"]:
                    if isinstance(item, dict):
                        raw_entries.append(item)
            else:
                for key, val in data.items():
                    if isinstance(val, dict):
                        entry = dict(val)
                        entry.setdefault("id", key)
                        raw_entries.append(entry)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    raw_entries.append(item)

        result: list[dict[str, Any]] = []
        for raw in raw_entries:
            try:
                entry = ExperimentRegistryEntry.model_validate(raw)
                result.append(entry.model_dump(mode="json"))
            except Exception:
                result.append(raw)
        return result

    @staticmethod
    def _scan_artifacts(experiments_root: Path) -> list[dict[str, Any]]:
        """Scan all CSV/JSONL/JSON/Parquet files under experiments_root."""
        records: list[dict[str, Any]] = []
        if not experiments_root.exists():
            return records

        for file_path in sorted(experiments_root.rglob("*")):
            if not file_path.is_file():
                continue
            fmt = _ARTIFACT_EXTENSIONS.get(file_path.suffix.lower())
            if fmt is None:
                continue

            rel = file_path.relative_to(experiments_root)
            parts = list(rel.parts)
            if len(parts) > 2:
                bundle_id = str(Path(*parts[:2]))
            elif parts:
                bundle_id = parts[0]
            else:
                bundle_id = ""

            run_path = str(rel.parent) if len(parts) > 1 else ""
            is_derived = "derived" in parts

            sha256 = hashlib.sha256(file_path.read_bytes()).hexdigest()

            records.append(
                {
                    "bundle_id": bundle_id,
                    "run_path": run_path,
                    "format": fmt,
                    "byte_size": file_path.stat().st_size,
                    "sha256": sha256,
                    "is_derived": is_derived,
                }
            )
        return records
