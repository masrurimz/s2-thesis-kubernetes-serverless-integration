"""The utilization-series JSON -> Parquet migration: verified, idempotent, safe on corrupt input.

The conversion reuses the pipeline's own writer and reader, so the migration is
also the writer's strongest test: every file history already wrote goes through
the same code a live run uses.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from experiment.cli import app
from shared.artifacts import (
    NODE_UTILIZATION_FILE,
    RESOURCE_UTILIZATION_FILE,
    read_node_utilization,
    read_resource_utilization,
)
from typer.testing import CliRunner

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = REPO_ROOT / "libs" / "shared" / "tests" / "fixtures"

runner = CliRunner()


@pytest.fixture()
def results_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A results root holding one run with both legacy series JSON files."""
    base = tmp_path / "results"
    run_dir = _run_dir(base)
    run_dir.mkdir(parents=True)
    (run_dir / "resource_utilization.json").write_bytes((FIXTURES / "resource_utilization.json").read_bytes())
    (run_dir / "node_utilization.json").write_bytes((FIXTURES / "node_utilization.json").read_bytes())
    monkeypatch.setattr("experiment.evidence.cli_adapter.RESULTS_ROOT", base)
    return base


def _run_dir(results_root: Path) -> Path:
    return results_root / "experiments" / "phase-b" / "2026-07-12_test" / "s3-hybrid-reactive_run1"


def _normalize(*args: str):
    return runner.invoke(app, ["evidence", "normalize", *args])


def test_converted_parquet_reads_back_the_source_values(results_root: Path):
    source = json.loads((_run_dir(results_root) / "resource_utilization.json").read_text())
    source_sorted = sorted(source, key=lambda row: row["timestamp"])

    result = _normalize("--apply")

    assert result.exit_code == 0
    run_dir = _run_dir(results_root)
    assert not (run_dir / "resource_utilization.json").exists()
    assert (run_dir / RESOURCE_UTILIZATION_FILE).is_file()
    assert (run_dir / NODE_UTILIZATION_FILE).is_file()
    restored = read_resource_utilization(run_dir)
    assert len(restored) == len(source_sorted)
    for sample, row in zip(restored, source_sorted, strict=True):
        assert abs(sample.timestamp - row["timestamp"]) <= 1e-6
        assert sample.model_dump(exclude={"timestamp"}) == {k: v for k, v in row.items() if k != "timestamp"}
    assert read_node_utilization(run_dir)


def test_a_second_run_is_a_no_op(results_root: Path):
    assert _normalize("--apply").exit_code == 0

    report = json.loads(_normalize("--apply", "--json").output)

    assert report["files"] == []
    assert report["converted"] == 0
    assert report["failed"] == 0


def test_dry_run_reports_without_touching_files(results_root: Path):
    result = _normalize("--json")

    assert result.exit_code == 0
    report = json.loads(result.output)
    assert report["apply"] is False
    assert report["would_convert"] == 2
    assert report["converted"] == 0
    assert {entry["status"] for entry in report["files"]} == {"would-convert"}
    run_dir = _run_dir(results_root)
    assert (run_dir / "resource_utilization.json").exists()
    assert not (run_dir / RESOURCE_UTILIZATION_FILE).exists()


def test_corrupt_json_is_reported_and_left_in_place(results_root: Path):
    (_run_dir(results_root) / "node_utilization.json").write_text("{corrupt")

    result = _normalize("--apply")

    assert result.exit_code == 1
    run_dir = _run_dir(results_root)
    assert (run_dir / "node_utilization.json").exists(), "a corrupt source is never deleted"
    assert not (run_dir / NODE_UTILIZATION_FILE).exists(), "no Parquet without a verified conversion"
    report = json.loads(_normalize("--apply", "--json").output)
    failed = [entry for entry in report["files"] if entry["series"] == "node"]
    assert failed[0]["status"] == "failed"
    assert failed[0]["error"]
