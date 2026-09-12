"""PredictionClient Protocol for dependency injection.

The protocol describes what a consumer of a prediction service needs. The routing
daemon asks three questions of it: whether the service is reachable at all
(``check_availability``, which a caller may cache), what model it is serving
(``get_model_status``, used to refuse a run against the wrong or stale artifact), and
the forecast itself. A protocol narrower than its consumer would silently exclude
substitutes that do not happen to be the one implementation in the tree.
"""

from typing import Any, Protocol, Sequence

from shared.models.prediction import PredictionResult


class PredictionClient(Protocol):
    """Contract for a prediction service client."""

    def predict(self, history: Sequence[float], horizon: int = 5) -> PredictionResult:
        """Get a workload prediction from the prediction service."""
        ...

    def is_healthy(self) -> bool:
        """Check if the prediction service is available."""
        ...

    def check_availability(self) -> bool:
        """Whether the service is reachable and its model loaded; may be cached."""
        ...

    def get_model_status(self) -> dict[str, Any]:
        """The served model's status, including the artifact it loaded."""
        ...
