"""Health checker for all infrastructure components.

Replaces deploy/scripts/check-health.sh.
"""

import time

import requests
import structlog

from infra.commands import console
from infra.config import PlatformConfig

logger = structlog.get_logger(__name__)


class HealthChecker:
    """Check health of infrastructure components via HTTP."""

    def __init__(self, config: PlatformConfig | None = None) -> None:
        self.config = config or PlatformConfig()
        self._session = requests.Session()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_all(self) -> dict[str, bool]:
        """Run health checks on all known components. Returns component→healthy mapping."""
        results: dict[str, bool] = {}

        checks = [
            ("k3s_backend", f"{self.config.k3s_warm_url}/health"),
            ("serverless_activator", f"{self.config.k3s_activator_url}/health"),
            ("haproxy_router", f"{self.config.haproxy_url}/health"),
            ("haproxy_stats", self.config.haproxy_stats_url),
            ("prometheus", f"{self.config.prometheus_url}/-/healthy"),
        ]

        for name, url in checks:
            results[name] = self.check_component(name, url)

        return results

    def check_component(self, name: str, url: str, timeout: float = 5.0) -> bool:
        """Check a single component endpoint. Returns True if healthy."""
        try:
            resp = self._session.get(url, timeout=timeout)
            healthy = resp.status_code < 400
        except requests.RequestException:
            healthy = False

        status = "[green]✓[/green]" if healthy else "[red]✗[/red]"
        console.print(f"  {status} {name}: {url}")
        return healthy

    def check_response_time(self, url: str | None = None, samples: int = 5) -> dict[str, float]:
        """Measure response time statistics for an endpoint."""
        target = url or self.config.haproxy_url
        times: list[float] = []

        for _ in range(samples):
            try:
                start = time.monotonic()
                self._session.get(target, timeout=10)
                elapsed = time.monotonic() - start
                times.append(elapsed)
            except requests.RequestException:
                pass

        if not times:
            return {"min_ms": 0, "max_ms": 0, "avg_ms": 0}

        return {
            "min_ms": min(times) * 1000,
            "max_ms": max(times) * 1000,
            "avg_ms": (sum(times) / len(times)) * 1000,
        }
