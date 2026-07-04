"""PredictionClient Protocol for dependency injection."""

from typing import Protocol, Sequence

from shared.models.prediction import PredictionResult


class PredictionClient(Protocol):
    """Contract for a prediction service client."""

    def predict(self, history: Sequence[float], horizon: int = 5) -> PredictionResult:
        """Get a workload prediction from the prediction service."""
        ...

    def is_healthy(self) -> bool:
        """Check if the prediction service is available."""
        ...
