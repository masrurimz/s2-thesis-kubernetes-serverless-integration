"""Prometheus deployment manager — docker-compose lifecycle.

Merged from deploy/monitoring/ and deploy/prometheus/.
"""

import importlib.resources

import structlog

from infra.commands import console, run

logger = structlog.get_logger(__name__)


class PrometheusManager:
    """Manage Prometheus via docker-compose."""

    def __init__(self) -> None:
        self._compose_file = str(
            importlib.resources.files("infra").joinpath("observability", "prometheus", "docker-compose.yml")
        )

    def start(self) -> bool:
        """Start Prometheus via docker-compose."""
        console.print("[bold]Starting Prometheus...[/bold]")
        result = run(["docker-compose", "-f", self._compose_file, "up", "-d"])
        if result.returncode != 0:
            logger.error("prometheus_start_failed", stderr=result.stderr)
            return False
        logger.info("prometheus_start_ok")
        console.print("[green]✓ Prometheus started.[/green]")
        return True

    def stop(self) -> bool:
        """Stop Prometheus via docker-compose."""
        console.print("[bold]Stopping Prometheus...[/bold]")
        result = run(["docker-compose", "-f", self._compose_file, "down"])
        if result.returncode != 0:
            logger.error("prometheus_stop_failed", stderr=result.stderr)
            return False
        logger.info("prometheus_stop_ok")
        console.print("[green]✓ Prometheus stopped.[/green]")
        return True

    def is_running(self) -> bool:
        """Check if Prometheus container is running."""
        result = run(["docker-compose", "-f", self._compose_file, "ps", "--services", "--filter", "status=running"])
        return bool(result.stdout.strip())
