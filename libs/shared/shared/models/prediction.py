"""Prediction-related Pydantic models.

Shared between prediction server and routing daemon.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """Request to the GRU prediction endpoint."""

    history: List[float] = Field(
        ...,
        description="Recent request counts (last N values)",
        min_length=1,
    )
    horizon: int = Field(
        default=5,
        ge=1,
        le=30,
        description="Number of steps ahead to predict",
    )


class PredictResponse(BaseModel):
    """Response from the GRU prediction endpoint."""

    predicted_requests: int = Field(description="Primary prediction value (max of upper forecasts)")
    confidence: float = Field(ge=0, le=1, description="Prediction confidence (0-1)")
    horizon_values: List[int] = Field(description="Point forecasts for each horizon step")
    latency_ms: float = Field(description="Prediction latency in milliseconds")
    point_forecasts: Optional[List[float]] = Field(default=None, description="Raw point forecasts per horizon")
    upper_forecasts: Optional[List[float]] = Field(default=None, description="Upper envelope forecasts per horizon")


class PredictionResult(BaseModel):
    """Result from GRU prediction service (used by routing daemon client)."""

    predicted_requests: int
    confidence: float
    horizon_values: List[int]
    latency_ms: float
    success: bool = True
    error: Optional[str] = None
    point_forecasts: Optional[List[float]] = None
    upper_forecasts: Optional[List[float]] = None


class HealthResponse(BaseModel):
    """Health check response from prediction server."""

    status: str
    model_loaded: bool
    model_type: Optional[str] = None
    uptime_seconds: float
    sequence_length: Optional[int] = None


class ModelStatus(BaseModel):
    """Detailed model status from prediction server."""

    model_loaded: bool
    model_type: Optional[str] = None
    model_path: Optional[str] = None
    sequence_length: Optional[int] = None
    input_size: Optional[int] = None
    hidden_size: Optional[int] = None
    num_layers: Optional[int] = None
    last_prediction_latency_ms: Optional[float] = None
