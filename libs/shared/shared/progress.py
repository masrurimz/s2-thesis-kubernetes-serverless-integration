"""Rich-based progress, ETA, and countdown utilities for experiment CLIs.

Provides reusable helpers for batch progress bars, phase spinners, countdown
timers, and compact result summaries. All functions take an explicit Console —
no global state.

Usage:
    from rich.console import Console
    from shared.progress import create_progress, countdown, run_phase

    console = Console()
    with create_progress(console) as progress:
        task = progress.add_task("Batch", total=20)
        for i in range(20):
            with countdown(console, 30, "Warmup"):
                ...
            progress.advance(task)
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import TYPE_CHECKING, Generator

from rich.console import Console
from rich.live import Live
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.text import Text

if TYPE_CHECKING:
    from shared.models.experiment import ExperimentResult


def create_progress(console: Console) -> Progress:
    """Pre-configured Progress with experiment-appropriate columns.

    Layout: [spinner] description [bar] M/N • ETA • elapsed
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
        TextColumn("•"),
        TimeElapsedColumn(),
        console=console,
    )


@contextmanager
def run_phase(console: Console, description: str) -> Generator[Progress, None, None]:
    """Context manager for a timed phase (warmup/cooldown/k6/daemon-start).

    Shows a spinner with elapsed time; on exit, the duration is left visible.
    Yields the inner Progress so callers can update the task description.
    """
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[cyan]{task.description}[/cyan]"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    )
    task = progress.add_task(description, total=None)  # noqa: F841 — reserved for future per-task control
    t0 = time.time()
    try:
        with progress:
            yield progress
    finally:
        elapsed = time.time() - t0
        console.print(f"  [green]✓[/green] {description} — {elapsed_str(elapsed)}")


@contextmanager
def countdown(console: Console, seconds: int, label: str) -> Generator[None, None, None]:
    """Live countdown timer for sleep/wait phases.

    Shows '⏳ Label: 23s remaining' updating every second.
    Degrades to a single print on non-TTY (no flicker).
    """
    if not console.is_terminal:
        console.print(f"  [dim]⏳ {label}: {seconds}s[/dim]")
        time.sleep(seconds)
    else:
        text = Text()
        remaining = seconds
        with Live(text, console=console, refresh_per_second=1, transient=True):
            while remaining > 0:
                text.plain = f"  ⏳ {label}: {remaining}s remaining"
                time.sleep(1)
                remaining -= 1
    yield
    console.print(f"  [green]✓[/green] {label}: {seconds}s done")


def print_run_header(console: Console, idx: int, total: int, scenario: str, run_id: int) -> None:
    """Print a run header with box-drawing separators."""
    console.print()
    console.rule(f"[bold]Run {idx}/{total} — {scenario} run {run_id}[/bold]", style="cyan")


def print_run_result(console: Console, result: "ExperimentResult", duration: float) -> None:
    """Print a compact one-line result summary.

    Layout: ✓ 45.2s • p99=142ms • rps=98.3 • errors=0.02% • SLO=0
    """
    console.print(
        f"  [green]✓[/green] [bold]{elapsed_str(duration)}[/bold] • "
        f"p99=[magenta]{result.p99_latency_ms:.0f}ms[/magenta] • "
        f"rps=[blue]{result.throughput_rps:.1f}[/blue] • "
        f"errors=[red]{result.error_rate:.4%}[/red]"
    )


def print_run_failure(console: Console, scenario: str, error: str) -> None:
    """Print a compact one-line failure summary."""
    console.print(f"  [red]✗ {scenario}[/red] — {error[:120]}")


def elapsed_str(seconds: float) -> str:
    """Format seconds as a human-readable duration.

    >>> elapsed_str(45.2)
    '45.2s'
    >>> elapsed_str(135)
    '2m 15s'
    >>> elapsed_str(7935)
    '2h 12m'
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"
