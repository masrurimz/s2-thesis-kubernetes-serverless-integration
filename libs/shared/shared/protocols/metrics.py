"""MetricsClient Protocol for dependency injection."""

from typing import Optional, Protocol


class MetricsClient(Protocol):
    """Contract for a Prometheus metrics client."""

    def query_instant(self, expr: str, timestamp: Optional[int] = None) -> Optional[float]:
        """Query a Prometheus instant metric."""
        ...

    def query_range(self, expr: str, start: int, end: int, step: int = 15) -> list[tuple[int, float]]:
        """Query a Prometheus range metric."""
        ...
