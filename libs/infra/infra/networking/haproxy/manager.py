"""HAProxy deployment manager — docker-compose lifecycle.

Replaces deploy/haproxy/ shell logic.
"""

import importlib.resources
import os

import structlog

from infra.networking.haproxy.render import render_config

from infra.commands import console, run

logger = structlog.get_logger(__name__)


class HAProxyManager:
    """Manage HAProxy via docker-compose."""

    def __init__(self, mode: str = "default") -> None:
        """Initialize with a compose mode ('default', 'knative', 'coldstart')."""
        self.mode = mode
        self._compose_file = self._resolve_compose_file(mode)

    @staticmethod
    def _resolve_compose_file(mode: str) -> str:
        mapping = {
            "default": "docker-compose.yml",
            "knative": "docker-compose-knative.yml",
            "coldstart": "docker-compose-coldstart.yml",
        }
        filename = mapping.get(mode, mapping["default"])
        return str(importlib.resources.files("infra").joinpath("networking", "haproxy", filename))

    def start(self) -> bool:
        """Start HAProxy via docker-compose against a freshly rendered config.

        The config names the Knative host, and that host changes with the cluster, so
        it is rendered from the running cluster before every start.
        """
        console.print(f"[bold]Starting HAProxy (mode={self.mode})...[/bold]")
        rendered = render_config(self.mode)
        env = dict(os.environ, HAPROXY_CFG=str(rendered))
        result = run(["docker", "compose", "-f", self._compose_file, "up", "-d"], env=env)
        if result.returncode != 0:
            logger.error("haproxy_start_failed", stderr=result.stderr)
            return False
        logger.info("haproxy_start_ok", mode=self.mode)
        console.print("[green]✓ HAProxy started.[/green]")
        return True

    def stop(self) -> bool:
        """Stop HAProxy via docker-compose."""
        console.print("[bold]Stopping HAProxy...[/bold]")
        result = run(["docker", "compose", "-f", self._compose_file, "down"])
        if result.returncode != 0:
            logger.error("haproxy_stop_failed", stderr=result.stderr)
            return False
        logger.info("haproxy_stop_ok")
        console.print("[green]✓ HAProxy stopped.[/green]")
        return True

    def is_running(self) -> bool:
        """Check if HAProxy containers are running."""
        result = run(["docker", "compose", "-f", self._compose_file, "ps", "--services", "--filter", "status=running"])
        return bool(result.stdout.strip())
