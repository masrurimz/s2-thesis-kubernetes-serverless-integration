"""Run a chain of profiles as one supervised series.

A series is not a shell loop: each stage changes the testbed, so a stage that fails has
to be retried on its own terms, the chain has to stop rather than run later stages
against a broken stack, and the indexer that watches this work tree has to be out of
the way for the whole measurement window. Those rules belong in the tool that runs the
experiments, not in a script beside it — the script could not be reused for a longer
night, could not be tested, and left the rules in one operator's head.

The runner is injectable so the rules are tested without launching anything.
"""

from __future__ import annotations

from shared.output import json_line
import shutil
import subprocess
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

INDEXER_UNIT = "graphify-watcher.service"
STAGE_KEYS = ("pairs", "runs", "output", "duration", "controller", "workload", "seed")


@dataclass(frozen=True)
class StageSpec:
    """One profile invocation: the profile and the overrides this series gives it."""

    profile: str
    overrides: dict[str, str] = field(default_factory=dict)

    def command(self) -> list[str]:
        parts = ["uv", "run", "thesis", "experiment", "reproduce", "--profile", self.profile]
        for key, value in self.overrides.items():
            parts += [f"--{key}", value]
        return parts

    def describe(self) -> str:
        suffix = " ".join(f"{key}={value}" for key, value in self.overrides.items())
        return f"{self.profile} ({suffix})" if suffix else self.profile


def parse_stage(spec: str) -> StageSpec:
    """Parse ``profile[:key=value,key=value]`` into a stage.

    Raises ValueError on an unknown key or a malformed pair, so a typo in a series
    definition fails before hours of measurement rather than silently dropping an
    override.
    """
    profile, _, options = spec.partition(":")
    if not profile:
        raise ValueError(f"stage {spec!r} names no profile")
    overrides: dict[str, str] = {}
    if options:
        for item in options.split(","):
            key, sep, value = item.partition("=")
            if not sep or not key or not value:
                raise ValueError(f"stage {spec!r}: expected key=value, got {item!r}")
            if key not in STAGE_KEYS:
                raise ValueError(f"stage {spec!r}: unknown key {key!r}; known: {', '.join(STAGE_KEYS)}")
            overrides[key] = value
    return StageSpec(profile=profile, overrides=overrides)


@dataclass
class StageOutcome:
    """What one stage did, and how long it took."""

    stage: str
    attempts: int
    ok: bool
    seconds: float
    returncode: int = 0

    def as_dict(self) -> dict:
        return {
            "stage": self.stage,
            "attempts": self.attempts,
            "ok": self.ok,
            "seconds": round(self.seconds, 1),
            "returncode": self.returncode,
        }


def _default_runner(command: Sequence[str], log_path: Path) -> int:
    with log_path.open("a") as log:
        log.write(f"\n$ {' '.join(command)}\n")
        log.flush()
        completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=False)
    return completed.returncode


def _default_indexer(action: str) -> bool:
    """Pause or restore the work-tree indexer; best effort, never fatal."""
    if shutil.which("systemctl") is None:
        return False
    return subprocess.run(["systemctl", "--user", action, INDEXER_UNIT], check=False).returncode == 0


def run_series(
    stages: Sequence[StageSpec],
    *,
    max_attempts: int = 2,
    log_path: Path | None = None,
    runner: Callable[[Sequence[str], Path], int] = _default_runner,
    indexer: Callable[[str], bool] = _default_indexer,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], datetime] = datetime.now,
) -> list[StageOutcome]:
    """Run each stage in order, retrying a failure, stopping the chain if it repeats.

    Returns one outcome per stage that ran. A stage that fails every attempt stops the
    series: later stages assume the stack the earlier ones left behind.
    """
    log_path = log_path or Path.home() / ".local" / "state" / "thesis-run" / f"series-{now():%Y%m%d-%H%M%S}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    outcomes: list[StageOutcome] = []

    def note(message: str) -> None:
        with log_path.open("a") as log:
            log.write(f"{now():%Y-%m-%d %H:%M:%S} {message}\n")

    note(f"series start: {len(stages)} stage(s), log {log_path}")
    indexer_paused = indexer("stop")
    note(f"indexer {'paused' if indexer_paused else 'not paused'} for the series")

    try:
        for stage in stages:
            started = time.monotonic()
            returncode = 0
            for attempt in range(1, max_attempts + 1):
                note(f"stage {stage.describe()}: attempt {attempt}")
                returncode = runner(stage.command(), log_path)
                if returncode == 0:
                    break
                note(f"stage {stage.describe()}: attempt {attempt} failed with {returncode}")
                if attempt < max_attempts:
                    sleep(60)
            ok = returncode == 0
            outcomes.append(
                StageOutcome(
                    stage=stage.profile,
                    attempts=attempt,
                    ok=ok,
                    seconds=time.monotonic() - started,
                    returncode=returncode,
                )
            )
            note(f"stage {stage.describe()}: {'ok' if ok else 'FAILED'}")
            if not ok:
                note("series stopping: a stage failed every attempt")
                break
    finally:
        if indexer_paused:
            indexer("start")
            note("indexer restored")

    return outcomes


def summarise(outcomes: Sequence[StageOutcome]) -> str:
    lines = [f"{'stage':24} {'attempts':>8} {'ok':>4} {'minutes':>8}"]
    for outcome in outcomes:
        lines.append(f"{outcome.stage:24} {outcome.attempts:8} {str(outcome.ok):>4} {outcome.seconds / 60:8.1f}")
    return "\n".join(lines)


def as_payload(outcomes: Sequence[StageOutcome]) -> list[dict]:
    return [outcome.as_dict() for outcome in outcomes]


def json_payload(outcomes: Sequence[StageOutcome]) -> str:
    """The stage outcomes as one line of JSON — the form every --json here prints."""
    return json_line(as_payload(outcomes))
