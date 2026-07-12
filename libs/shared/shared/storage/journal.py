"""Append-only experiment lifecycle journal backed by hardened JSONLWriter.

Each event is a self-contained ExperimentJournalEvent serialized as one JSON line.
The journal is write-once: no record is ever edited or deleted.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from shared.models.evidence import ExperimentJournalEvent, JournalEventName
from shared.storage.jsonl_writer import JSONLWriter


class ExperimentJournal:
    """Typed append-only journal for experiment lifecycle events.

    Wraps JSONLWriter (fcntl.flock-protected on Linux) to provide typed
    ExperimentJournalEvent round-tripping.

    Usage::

        journal = ExperimentJournal(
            path=run_dir / "events.jsonl",
            experiment_id="phase-b/2026-07-12_h2",
            bundle_path=str(bundle_dir),
            git_commit=commit_sha,
        )
        ev = journal.new_event("run_started", scenario="s4", run_id=1,
                               payload={"seed": 42})
        journal.record(ev)
        all_events = journal.read_all()
    """

    def __init__(
        self,
        path: Path,
        experiment_id: str,
        bundle_path: str,
        git_commit: str = "",
    ) -> None:
        self._writer = JSONLWriter(path)
        self.experiment_id = experiment_id
        self.bundle_path = bundle_path
        self.git_commit = git_commit

    def new_event(
        self,
        event: JournalEventName,
        *,
        scenario: str | None = None,
        run_id: int | None = None,
        pair_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> ExperimentJournalEvent:
        """Create a new ExperimentJournalEvent with generated UUID4 and UTC timestamp."""
        return ExperimentJournalEvent(
            event_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            event=event,
            experiment_id=self.experiment_id,
            bundle_path=self.bundle_path,
            scenario=scenario,
            run_id=run_id,
            pair_id=pair_id,
            git_commit=self.git_commit,
            payload=payload or {},
        )

    def record(self, event: ExperimentJournalEvent) -> None:
        """Append an event to the journal file.

        Raises:
            ValueError: If the event's experiment_id or bundle_path differs
                from this journal instance.
        """
        if event.experiment_id != self.experiment_id:
            raise ValueError(f"event experiment_id mismatch: {event.experiment_id!r} != {self.experiment_id!r}")
        if event.bundle_path != self.bundle_path:
            raise ValueError(f"event bundle_path mismatch: {event.bundle_path!r} != {self.bundle_path!r}")
        self._writer.append(event)

    def read_all(self) -> list[ExperimentJournalEvent]:
        """Read and validate all events from the journal file."""
        raw_lines = self._writer.read_all()
        return [ExperimentJournalEvent.model_validate(line) for line in raw_lines]
