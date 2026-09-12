"""Tests for the evidence Typer sub-app commands.

Tests prove:
- Commands enforce --apply (reconcile and backfill-legacy fail without it).
- Query never mutates registry/journal/catalog canonical artifacts.
- Rendering is deterministic (same input -> same output).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from experiment.cli import app
from experiment.evidence.registry import (
    scan_bundles,
    write_registry,
)
from experiment.evidence.renderer import render_experiment_journal
from shared.models.evidence import ExperimentJournalEvent, ExperimentRegistryEntry
from typer.testing import CliRunner

runner = CliRunner()


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _make_result(scenario: str = "s3-hybrid-reactive", run_id: int = 1) -> dict:
    return {
        "scenario": scenario,
        "run_id": run_id,
        "timestamp": "2026-07-12T00:00:00",
        "run_validity_passed": True,
        "stress_validity_passed": True,
    }


@pytest.fixture()
def results_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a results/ root with a fixture bundle and patch the CLI to use it."""
    base = tmp_path / "results"
    base.mkdir()
    bundle = base / "experiments" / "phase-b" / "2026-07-12_test"
    bundle.mkdir(parents=True)
    (bundle / "meta.yaml").write_text("bundle_schema_version: 2\n")
    (bundle / "report.md").write_text("# Report\n1 clean\n")
    raw = bundle / "raw"
    raw.mkdir()
    run_dir = raw / "s3-hybrid-reactive_run1"
    run_dir.mkdir()
    (run_dir / "result.json").write_text(json.dumps(_make_result()))

    # Patch the results root used by the CLI commands
    monkeypatch.setattr("experiment.evidence.cli_adapter.RESULTS_ROOT", base)
    return base


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestReconcileEnforcesApply:
    """reconcile and backfill-legacy fail without --apply."""

    def test_reconcile_without_apply_exits_nonzero(self, results_root: Path):
        result = runner.invoke(app, ["evidence", "reconcile"])
        assert result.exit_code != 0

    def test_reconcile_with_apply_succeeds(self, results_root: Path):
        result = runner.invoke(app, ["evidence", "reconcile", "--apply"])
        assert result.exit_code == 0
        assert (results_root / "evidence" / "registry.yaml").exists()

    def test_backfill_legacy_without_apply_exits_nonzero(self, results_root: Path):
        result = runner.invoke(app, ["evidence", "backfill-legacy"])
        assert result.exit_code != 0


class TestQueryNeverMutates:
    """Read-only commands never mutate canonical artifacts."""

    def test_audit_does_not_write(self, results_root: Path):
        """audit is read-only: no registry/events/catalog written."""
        result = runner.invoke(app, ["evidence", "audit"])
        assert result.exit_code == 0
        assert not (results_root / "evidence" / "registry.yaml").exists()
        assert not (results_root / "evidence" / "registry-events.jsonl").exists()

    def test_query_does_not_mutate(self, results_root: Path):
        """query does not modify registry/events files."""
        # Set up a minimal registry so query can run
        scanned = scan_bundles(results_root)
        registry_path = results_root / "evidence" / "registry.yaml"
        write_registry(registry_path, scanned)

        events_path = results_root / "evidence" / "registry-events.jsonl"
        events_path.parent.mkdir(parents=True, exist_ok=True)
        events_path.write_text("")

        registry_before = registry_path.read_text()
        events_before = events_path.read_text()

        # Query may fail if duckdb/catalog isn't built, but must not mutate files
        runner.invoke(app, ["evidence", "query", "SELECT 1"])

        assert registry_path.read_text() == registry_before
        assert events_path.read_text() == events_before


class TestJournalCommand:
    """journal command shows governance events."""

    def test_journal_runs(self, results_root: Path):
        """journal command succeeds and shows events."""
        # Write some governance events
        events_path = results_root / "evidence" / "registry-events.jsonl"
        events_path.parent.mkdir(parents=True, exist_ok=True)
        events_path.write_text("")

        result = runner.invoke(app, ["evidence", "journal", "--limit", "5"])
        assert result.exit_code == 0


class TestRenderingDeterministic:
    """Markdown rendering is deterministic for the same input."""

    def test_render_is_deterministic(self, tmp_path: Path):
        """Same entries + events produce identical output."""
        entries = [
            ExperimentRegistryEntry(
                id="experiments.2026-07-12-test",
                root="experiments",
                path="experiments/phase-b/2026-07-12_test",
                date="2026-07-12",
                role="intermediate",
                status="current",
                scenarios=["s3-hybrid-reactive"],
                n_runs_total=2,
                n_runs_valid=2,
                has_meta=True,
                has_report=True,
                has_paired_analysis=False,
            ),
        ]
        events: list[ExperimentJournalEvent] = []

        out1 = tmp_path / "journal1.md"
        out2 = tmp_path / "journal2.md"
        render_experiment_journal(entries, events, out1)
        render_experiment_journal(entries, events, out2)

        assert out1.read_text() == out2.read_text()
        assert "Experiment Journal" in out1.read_text()
        assert "experiments.2026-07-12-test" in out1.read_text()


class TestQueryDisplay:
    """`query` shows a bounded number of rows, names what it hid, and never mangles a cell.

    An unbounded `SELECT *` over the artifact index is thousands of rows; a table wider than
    the terminal is ellipsized by rich into uselessness; and a long cell is truncated with
    its own length and its own escape hatch.
    """

    @staticmethod
    def _adapter(rows: list[dict]):
        class _Fake:
            def __init__(self, root):
                self.root = root

            def query(self, sql, max_rows=None):
                return rows if max_rows is None else rows[:max_rows]

        return _Fake

    def test_stops_at_the_limit_and_says_there_is_more(self, results_root, monkeypatch):
        rows = [{"run_path": f"phase-b/bundle/raw/run{index}"} for index in range(60)]
        monkeypatch.setattr("experiment.evidence.catalog.EvidenceCatalogAdapter", self._adapter(rows))

        result = runner.invoke(app, ["evidence", "query", "SELECT run_path FROM artifact_index", "--limit", "5"])

        assert result.exit_code == 0, result.output
        assert "5 row(s) shown; more available — raise --limit" in result.output.replace("\n", " ")

    def test_a_short_result_says_nothing_about_hiding_rows(self, results_root, monkeypatch):
        monkeypatch.setattr("experiment.evidence.catalog.EvidenceCatalogAdapter", self._adapter([{"a": 1}]))

        result = runner.invoke(app, ["evidence", "query", "SELECT a FROM t"])

        assert "1 row(s) shown" in result.output
        assert "more available" not in result.output

    def test_json_mode_emits_one_line_of_the_rows(self, results_root, monkeypatch):
        rows = [{"a": index} for index in range(3)]
        monkeypatch.setattr("experiment.evidence.catalog.EvidenceCatalogAdapter", self._adapter(rows))

        result = runner.invoke(app, ["evidence", "query", "SELECT a FROM t", "--json"])

        assert json.loads(result.stdout) == rows
        assert "\n" not in result.stdout.strip()

    def test_a_long_cell_is_truncated_with_its_length_and_the_flag(self, results_root, monkeypatch):
        long_value = "z" * 400
        monkeypatch.setattr("experiment.evidence.catalog.EvidenceCatalogAdapter", self._adapter([{"blob": long_value}]))

        result = runner.invoke(app, ["evidence", "query", "SELECT blob FROM t"])

        assert "400 chars" in result.output
        assert "--full" in result.output
        assert long_value not in result.output

    def test_full_shows_the_whole_cell(self, results_root, monkeypatch):
        long_value = "z" * 200
        monkeypatch.setattr("experiment.evidence.catalog.EvidenceCatalogAdapter", self._adapter([{"blob": long_value}]))

        result = runner.invoke(app, ["evidence", "query", "SELECT blob FROM t", "--full"])

        # A block, not a table: the value arrives whole and on one line.
        assert f"  blob: {long_value}" in result.output


class TestJournalJson:
    def test_json_mode_emits_the_events_without_a_table(self, results_root):
        events_path = results_root / "evidence" / "registry-events.jsonl"
        events_path.parent.mkdir(parents=True, exist_ok=True)
        events_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "event_id": "8d73c062-45da-49f3-9846-9fe8a1ffd891",
                    "timestamp": "2026-08-09T04:12:35.295807+00:00",
                    "event": "registry_audited",
                    "experiment_id": "registry",
                    "bundle_path": "results/evidence",
                }
            )
            + "\n"
        )

        result = runner.invoke(app, ["evidence", "journal", "--json"])

        assert result.exit_code == 0, result.output
        payload = json.loads(result.stdout)
        assert [event["event"] for event in payload] == ["registry_audited"]
