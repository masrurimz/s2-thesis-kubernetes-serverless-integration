"""Typer sub-app for the dashboard.

Mirrors ``experiment.cli`` (``app = typer.Typer(...)`` + ``@app.command()``).
The ``start`` command shells out to ``streamlit run`` because Streamlit must
own its own server process.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import typer

app = typer.Typer(help="Interactive experiment-results dashboard")

DEFAULT_PORT = 28555  # 28188/28199 taken by Hindsight; 28555 verified free


@app.command()
def start(
    port: int = typer.Option(DEFAULT_PORT, "--port", "-p", help="Port to bind (default 28555)"),
    host: str = typer.Option("0.0.0.0", "--host", help="Bind address"),
) -> None:
    """Start the Streamlit dashboard (reachable over Tailscale)."""
    # app.py is a sibling module in this package.
    script = Path(__file__).resolve().parent / "app.py"
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(script),
        "--server.address",
        host,
        "--server.port",
        str(port),
        "--server.headless",
        "true",
        "--server.fileWatcherType",
        "none",
    ]
    typer.echo(f"Starting dashboard: http://{host}:{port}")
    typer.echo("  (from m5-space over Tailscale: http://100.122.177.43:%d)" % port)
    subprocess.run(cmd, check=False)


if __name__ == "__main__":
    app()
