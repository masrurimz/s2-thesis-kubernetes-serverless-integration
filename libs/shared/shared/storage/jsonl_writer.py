"""JSONL writer for append-only structured event streams.

Each line is a self-contained JSON object. Git shows one-line-per-event diffs.
All writes are protected by an exclusive ``fcntl.flock`` and ``os.fsync`` so
concurrent processes cannot interleave or lose events.
"""

import fcntl
import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class JSONLWriter:
    """Append-only writer for newline-delimited JSON events.

    Usage:
        writer = JSONLWriter("results/experiment/events.jsonl")
        writer.append({"event": "run_started", "timestamp": 1234567890})
        writer.append({"event": "k6_completed", "duration_sec": 300})
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: BaseModel | dict[str, Any]) -> None:
        """Append a single event to the JSONL file.

        Args:
            event: A Pydantic model (serialized via model_dump) or a dict
        """
        if isinstance(event, BaseModel):
            data = event.model_dump(mode="json")
        else:
            data = event

        with open(self.path, "a") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.write(json.dumps(data, default=str) + "\n")
                f.flush()
                os.fsync(f.fileno())
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def append_batch(self, events: list[BaseModel | dict[str, Any]]) -> None:
        """Append multiple events at once."""
        with open(self.path, "a") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                for event in events:
                    if isinstance(event, BaseModel):
                        data = event.model_dump(mode="json")
                    else:
                        data = event
                    f.write(json.dumps(data, default=str) + "\n")
                f.flush()
                os.fsync(f.fileno())
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def read_all(self) -> list[dict[str, Any]]:
        """Read all events from the JSONL file."""
        if not self.path.exists():
            return []

        results = []
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if line:
                    results.append(json.loads(line))
        return results
