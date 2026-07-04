"""RoutingDaemonClient Protocol for dependency injection."""

from typing import Protocol

from shared.models.routing import StatusResponse


class RoutingDaemonClient(Protocol):
    """Contract for a routing daemon HTTP client."""

    def get_status(self) -> StatusResponse:
        """Get the current daemon status."""
        ...

    def set_scenario(self, scenario: str) -> bool:
        """Change the active scenario."""
        ...

    def is_healthy(self) -> bool:
        """Check if the daemon is running."""
        ...
