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
    # Actuator-fidelity fields (S4 treatment gate)
    prediction_eligible_cycles: int = 0
    prediction_delivery_failures: int = 0
    model_history_ready: bool = False
    model_sequence_length: int = 0
    forecast_horizon_sufficient: bool = False
    forecast_actionable_cycles: int = 0
    forecast_capacity_signal: float = 0.0
    provisioning_delay_estimate_sec: float = 0.0
    provisioning_delay_samples: int = 0
    forecast_horizon_steps: int = 0
    proactive_scaleups: int = 0
    no_op_predictions: int = 0
    useful_proactive_scaleups: int = 0
    model_config = {"extra": "allow"}


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
