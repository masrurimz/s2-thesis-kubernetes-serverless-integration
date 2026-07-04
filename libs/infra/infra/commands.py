"""Subprocess wrapper with Rich logging and dry-run support."""

import shutil
import subprocess

from rich.console import Console

console = Console()


def run(
    cmd: list[str],
    dry_run: bool = False,
    cwd: str | None = None,
    check: bool = False,
    **kwargs: object,
) -> subprocess.CompletedProcess[str]:
    """Run a command with Rich logging and optional dry-run.

    Args:
        cmd: Command and arguments.
        dry_run: If True, log the command but don't execute it.
        cwd: Working directory for the subprocess.
        check: If True, raise on non-zero exit.
        **kwargs: Extra args passed to subprocess.run.
    """
    console.print(f"[dim]$ {' '.join(cmd)}[/dim]")
    if dry_run:
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, **kwargs)  # noqa: S603
    if check and result.returncode != 0:
        console.print(f"[red]Command failed (rc={result.returncode}): {result.stderr.strip()}[/red]")
        result.check_returncode()
    return result


def check_command(cmd: str) -> bool:
    """Check if a command is available on PATH."""
    return shutil.which(cmd) is not None
