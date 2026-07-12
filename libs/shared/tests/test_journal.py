"""Tests for ExperimentJournal typed JSONL round-trip, ordering, concurrency, and guards."""

import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from shared.models.evidence import ExperimentJournalEvent
from shared.storage.journal import ExperimentJournal


@pytest.fixture()
def journal(tmp_path):
    return ExperimentJournal(
        path=tmp_path / "events.jsonl",
        experiment_id="phase-b/2026-07-12_h2",
        bundle_path="/results/experiments/phase-b/2026-07-12_h2",
        git_commit="abc1234",
    )


class TestJournalRoundTrip:
    """Typed JSONL round-trip through ExperimentJournal."""

    def test_record_and_read_all_round_trips_typed_fields(self, journal):
        ev = journal.new_event(
            "run_started",
            scenario="s4",
            run_id=1,
            payload={"seed": 42, "order": 0},
        )
        journal.record(ev)

        events = journal.read_all()
        assert len(events) == 1

        result = events[0]
        assert isinstance(result, ExperimentJournalEvent)
        assert result.event == "run_started"
        assert result.experiment_id == "phase-b/2026-07-12_h2"
        assert result.bundle_path == "/results/experiments/phase-b/2026-07-12_h2"
        assert result.scenario == "s4"
        assert result.run_id == 1
        assert result.git_commit == "abc1234"
        assert result.payload == {"seed": 42, "order": 0}
        # UUID and timestamp survived the round-trip
        assert str(result.event_id) == str(ev.event_id)
        assert result.timestamp == ev.timestamp

    def test_multiple_event_types_round_trip(self, journal):
        for event_name in [
            "run_started",
            "daemon_started",
            "prediction_preflight_passed",
            "workload_completed",
            "run_completed",
        ]:
            journal.record(journal.new_event(event_name, run_id=1))

        events = journal.read_all()
        assert len(events) == 5
        assert [e.event for e in events] == [
            "run_started",
            "daemon_started",
            "prediction_preflight_passed",
            "workload_completed",
            "run_completed",
        ]

    def test_pair_excluded_event(self, journal):
        journal.record(
            journal.new_event(
                "pair_excluded",
                pair_id="s3_run1-s4_run1",
                payload={"reason": "s4 delivery_rate=0.6 < 1.0"},
            )
        )
        events = journal.read_all()
        assert events[0].pair_id == "s3_run1-s4_run1"
        assert events[0].payload["reason"] == "s4 delivery_rate=0.6 < 1.0"


class TestJournalOrdering:
    """Strict append ordering."""

    def test_events_preserve_insertion_order(self, journal):
        for i in range(10):
            journal.record(journal.new_event("run_started", run_id=i, payload={"order": i}))

        events = journal.read_all()
        assert [e.run_id for e in events] == list(range(10))
        assert [e.payload["order"] for e in events] == list(range(10))


class TestJournalConcurrency:
    """Concurrent writes produce intact, non-corrupted records."""

    def test_concurrent_appends_all_records_intact(self, tmp_path):
        journal_path = tmp_path / "events.jsonl"
        journal = ExperimentJournal(journal_path, "concurrent", "/bundle")

        n_threads = 4
        n_per_thread = 25

        def writer(thread_id: int) -> None:
            for i in range(n_per_thread):
                journal.record(
                    journal.new_event(
                        "run_started",
                        run_id=thread_id,
                        payload={"thread": thread_id, "i": i},
                    )
                )

        with ThreadPoolExecutor(max_workers=n_threads) as pool:
            futures = [pool.submit(writer, t) for t in range(n_threads)]
            for f in futures:
                f.result()

        # Every line must be valid JSON (no interleaving corruption)
        with open(journal_path) as f:
            lines = [line.strip() for line in f if line.strip()]
        for line in lines:
            json.loads(line)  # raises on corruption

        # All records survived and are typed
        events = journal.read_all()
        assert len(events) == n_threads * n_per_thread
        assert all(e.experiment_id == "concurrent" for e in events)

    def test_concurrent_appends_no_duplicate_event_ids(self, tmp_path):
        journal_path = tmp_path / "events.jsonl"
        journal = ExperimentJournal(journal_path, "dup-test", "/bundle")

        def writer(_thread_id: int) -> None:
            for _ in range(15):
                journal.record(journal.new_event("run_started"))

        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(writer, t) for t in range(3)]
            for f in futures:
                f.result()

        events = journal.read_all()
        ids = [str(e.event_id) for e in events]
        assert len(ids) == len(set(ids))  # no duplicates


class TestJournalGuards:
    """record() rejects mismatched identifiers."""

    def test_record_rejects_mismatched_experiment_id(self, journal):
        ev = journal.new_event("run_started")
        # Tamper with experiment_id
        ev = ev.model_copy(update={"experiment_id": "different-experiment"})
        with pytest.raises(ValueError, match="experiment_id mismatch"):
            journal.record(ev)

    def test_record_rejects_mismatched_bundle_path(self, journal):
        ev = journal.new_event("run_started")
        ev = ev.model_copy(update={"bundle_path": "/different/bundle"})
        with pytest.raises(ValueError, match="bundle_path mismatch"):
            journal.record(ev)

    def test_record_accepts_matching_identifiers(self, journal):
        ev = journal.new_event("run_completed")
        journal.record(ev)  # should not raise
        assert len(journal.read_all()) == 1
