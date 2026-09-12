"""Typed HTTP client for communication with the routing daemon.

Uses shared.models.routing for request/response contracts.
"""

from typing import Any, Dict, Optional

import requests
import structlog
from shared.config import settings
from shared.models.routing import RoutingHealthResponse, StatusResponse

logger = structlog.get_logger(__name__)


class DaemonClient:
    """HTTP client for the routing daemon API."""

    def __init__(self, base_url: Optional[str] = None):
        self._base_url = base_url or f"http://localhost:{settings.DAEMON_API_PORT}"
        self._session = requests.Session()

    def is_healthy(self) -> bool:
        """Check if the daemon is healthy and responsive."""
        try:
            r = self._session.get(f"{self._base_url}/health", timeout=5)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        return False

    def get_health(self) -> Optional[RoutingHealthResponse]:
        """Get the daemon health response."""
        try:
            r = self._session.get(f"{self._base_url}/health", timeout=5)
            if r.status_code == 200:
                return RoutingHealthResponse(**r.json())
        except Exception as e:
            logger.warning("daemon_health_failed", error=str(e))
        return None

    def get_status(self) -> Optional[StatusResponse]:
        """Get the daemon status response."""
        try:
            r = self._session.get(f"{self._base_url}/status", timeout=5)
            if r.status_code == 200:
                return StatusResponse(**r.json())
        except Exception as e:
            logger.warning("daemon_status_failed", error=str(e))
        return None

    def get_status_raw(self) -> Optional[Dict[str, Any]]:
        """Get raw daemon status as dict (for backward compatibility)."""
        try:
            r = self._session.get(f"{self._base_url}/status", timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    def set_scenario(self, scenario: str) -> bool:
        """Set the daemon's active scenario."""
        try:
            r = self._session.post(
                f"{self._base_url}/scenario",
                json={"scenario": scenario},
                timeout=5,
            )
            return r.status_code == 200
        except Exception as e:
            logger.warning("daemon_set_scenario_failed", scenario=scenario, error=str(e))
            return False
