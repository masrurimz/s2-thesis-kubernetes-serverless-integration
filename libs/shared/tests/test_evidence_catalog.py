"""Tests for EvidenceCatalog DuckDB view creation and querying."""

import pytest

from shared.evidence.catalog import EvidenceCatalog
from shared.models.experiment import ExperimentResult
from shared.storage.journal import ExperimentJournal
from shared.storage.parquet import write_table_parquet


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------


@pytest.fixture()
def two_bundle_repo(tmp_path):
    """Create a results tree with two experiment bundles (s3, s4)."""
    experiments = tmp_path / "results" / "experiments"
    evidence = tmp_path / "results" / "evidence"
    evidence.mkdir(parents=True)
    bundle_dir = experiments / "phase-b" / "2026-07-12_h2"

    for scenario in ("s3", "s4"):
        run_dir = bundle_dir / "raw" / f"{scenario}_run1"
        run_dir.mkdir(parents=True)

        # events.jsonl via typed journal
        journal = ExperimentJournal(
            path=run_dir / "events.jsonl",
            experiment_id="phase-b/2026-07-12_h2",
            bundle_path=str(bundle_dir),
        )
        journal.record(journal.new_event("run_started", scenario=scenario, run_id=1))
        journal.record(journal.new_event("run_completed", scenario=scenario, run_id=1))

        # result.json
        result = ExperimentResult(
            scenario=scenario,
            run_id=1,
            p50_latency_ms=12.0 if scenario == "s4" else 15.0,
        )
        (run_dir / "result.json").write_text(result.model_dump_json())

    return tmp_path


@pytest.fixture()
def parquet_repo(two_bundle_repo):
    """Add a Parquet timeseries file to the s4 run."""
    import pyarrow as pa

    run_dir = two_bundle_repo / "results" / "experiments" / "phase-b" / "2026-07-12_h2" / "raw" / "s4_run1"
    table = pa.table(
        {
            "timestamp": pa.array([1.0, 2.0], type=pa.float64()),
            "latency_ms": pa.array([10.0, 12.0], type=pa.float64()),
        }
    )
    write_table_parquet(
        table,
        run_dir / "metrics.parquet",
        schema_version=2,
        metadata={
            "experiment_id": "phase-b/2026-07-12_h2",
            "scenario": "s4",
            "run_id": "1",
            "producer_git_commit": "abc1234",
            "generated_at": "2026-07-12T10:00:00+00:00",
        },
    )
    return two_bundle_repo


@pytest.fixture()
def empty_repo(tmp_path):
    """Create a results tree with no experiment data."""
    (tmp_path / "results" / "evidence").mkdir(parents=True)
    return tmp_path


# -----------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------


class TestCatalogRefresh:
    """refresh() creates all expected views."""

    def test_refresh_creates_all_views(self, two_bundle_repo):
        catalog = EvidenceCatalog(two_bundle_repo)
        catalog.refresh()

        for view in [
            "registry_entries",
            "registry_events",
            "run_events",
            "run_results",
            "timeseries",
            "artifact_index",
        ]:
            rows = catalog.query(f"SELECT * FROM {view}")
            assert isinstance(rows, list)

    def test_refresh_creates_db_file(self, two_bundle_repo):
        catalog = EvidenceCatalog(two_bundle_repo)
        catalog.refresh()
        assert catalog.db_path.exists()


class TestRunEventsView:
    """run_events from events.jsonl files."""

    def test_run_events_returns_all_events(self, two_bundle_repo):
        catalog = EvidenceCatalog(two_bundle_repo)
        catalog.refresh()

        rows = catalog.query("SELECT * FROM run_events")
        # 2 bundles × 2 events each = 4 events
        assert len(rows) == 4
        events = [r["event"] for r in rows]
        assert "run_started" in events
        assert "run_completed" in events

    def test_run_events_have_experiment_id(self, two_bundle_repo):
        catalog = EvidenceCatalog(two_bundle_repo)
        catalog.refresh()

        rows = catalog.query("SELECT * FROM run_events")
        for row in rows:
            assert row["experiment_id"] == "phase-b/2026-07-12_h2"


class TestRunResultsView:
    """run_results from result.json files."""

    def test_run_results_returns_both_scenarios(self, two_bundle_repo):
        catalog = EvidenceCatalog(two_bundle_repo)
        catalog.refresh()

        rows = catalog.query("SELECT * FROM run_results")
        assert len(rows) == 2
        scenarios = {r["scenario"] for r in rows}
        assert scenarios == {"s3", "s4"}

    def test_run_results_preserve_metrics(self, two_bundle_repo):
        catalog = EvidenceCatalog(two_bundle_repo)
        catalog.refresh()

        rows = catalog.query("SELECT scenario, p50_latency_ms FROM run_results ORDER BY scenario")
        assert rows[0]["scenario"] == "s3"
        assert rows[1]["scenario"] == "s4"


class TestArtifactIndexView:
    """artifact_index scans all artifacts."""

    def test_artifact_index_finds_json_and_jsonl(self, two_bundle_repo):
        catalog = EvidenceCatalog(two_bundle_repo)
        catalog.refresh()

        rows = catalog.query("SELECT * FROM artifact_index")
        formats = {r["format"] for r in rows}
        assert "json" in formats
        assert "jsonl" in formats

    def test_artifact_index_has_sha256(self, two_bundle_repo):
        catalog = EvidenceCatalog(two_bundle_repo)
        catalog.refresh()

        rows = catalog.query("SELECT * FROM artifact_index")
        for row in rows:
            assert len(row["sha256"]) == 64
            assert row["byte_size"] > 0


class TestTimeseriesView:
    """timeseries from Parquet files."""

    def test_timeseries_with_parquet(self, parquet_repo):
        catalog = EvidenceCatalog(parquet_repo)
        catalog.refresh()

        rows = catalog.query("SELECT * FROM timeseries")
        assert len(rows) == 2
        assert all("latency_ms" in r for r in rows)


class TestEmptyCorpus:
    """Empty corpus produces queryable views."""

    def test_all_views_queryable_when_empty(self, empty_repo):
        catalog = EvidenceCatalog(empty_repo)
        catalog.refresh()

        for view in [
            "registry_entries",
            "registry_events",
            "run_events",
            "run_results",
            "timeseries",
            "artifact_index",
        ]:
            rows = catalog.query(f"SELECT * FROM {view}")
            assert rows == [], f"{view} should be empty"


class TestRegistryEntriesView:
    """registry_entries from registry.yaml."""

    def test_registry_entries_from_yaml(self, tmp_path):
        import yaml

        evidence = tmp_path / "results" / "evidence"
        evidence.mkdir(parents=True)

        entry = {
            "id": "phase-b/2026-07-12_h2",
            "root": str(tmp_path),
            "path": "results/experiments/phase-b/2026-07-12_h2",
            "date": "2026-07-12",
            "role": "intermediate",
            "status": "current",
            "scenarios": ["s3", "s4"],
            "n_runs_total": 10,
            "n_runs_valid": 8,
            "has_meta": True,
            "has_report": True,
            "has_paired_analysis": True,
        }
        (evidence / "registry.yaml").write_text(yaml.dump({"phase-b/2026-07-12_h2": entry}))

        catalog = EvidenceCatalog(tmp_path)
        catalog.refresh()

        rows = catalog.query("SELECT * FROM registry_entries")
        assert len(rows) == 1
        assert rows[0]["id"] == "phase-b/2026-07-12_h2"
        assert rows[0]["role"] == "intermediate"
