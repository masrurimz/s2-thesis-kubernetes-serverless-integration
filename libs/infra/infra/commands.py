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
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command with Rich logging and optional dry-run.

    stdin is closed unless input_text is given. A tool invoked as `... -f -` reads
    stdin, and a child that inherits an interactive or open stdin waits forever for
    input nobody will send — which is exactly how a rebuild hangs mid-install.

    Args:
        cmd: Command and arguments.
        dry_run: If True, log the command but don't execute it.
        cwd: Working directory for the subprocess.
        check: If True, raise on non-zero exit.
        input_text: Text to feed the command's stdin.
    """
    console.print(f"[dim]$ {' '.join(cmd)}[/dim]")
    if dry_run:
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd,
        input=input_text,
        stdin=subprocess.DEVNULL if input_text is None else None,
        check=False,  # noqa: S603 — cmd is always a list, never shell=True
    )
    if check and result.returncode != 0:
        console.print(f"[red]Command failed (rc={result.returncode}): {result.stderr.strip()}[/red]")
        result.check_returncode()
    return result


def check_command(cmd: str) -> bool:
    """Check if a command is available on PATH."""
    return shutil.which(cmd) is not None
