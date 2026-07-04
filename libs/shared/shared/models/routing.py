"""Routing daemon API models.

Shared between routing daemon and experiment runner.
"""

from typing import Dict, Optional

from pydantic import BaseModel


class StatusResponse(BaseModel):
    """Status response from the routing daemon."""

    scenario: str
    scenario_description: str
    weights: Dict[str, int]
    decision_count: int
    scale_out_count: int
    optimize_cost_count: int
    predictive_count: int
    maintain_count: int
    uptime_seconds: float
    gru_available: bool
    last_decision_time: Optional[float] = None


class SetScenarioRequest(BaseModel):
    """Request to change the daemon's active scenario."""

    scenario: str


class HealthResponse(BaseModel):
    """Health check response from the routing daemon."""

    status: str
    scenario: str
    haproxy_connected: bool
    gru_available: bool


class RoutingDecision(BaseModel):
    """Output of Algorithm 1 routing decision."""

    action: str  # MAINTAIN, SCALE_OUT, OPTIMIZE_COST, PREDICTIVE
    k3s_weight: int
    knative_weight: int
    reason: str
    backend_state_changed: bool = False
