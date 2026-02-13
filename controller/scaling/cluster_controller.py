#!/usr/bin/env python3
"""
Algorithm 2: Cluster Controller (Prediction-Based Resource Scaling)

Implements the proposed cluster controller from thesis section 3.4.3.2.
Uses the linear model R = α·x + β to compute required resources from
GRU-predicted workload, then produces scaling decisions.

This is a proof-of-concept that:
- Reads predicted load from the GRU prediction server
- Computes required replicas via R = α·x + β
- Logs scaling decisions with full audit trail
- Does NOT execute kubectl commands (mechanism validation only)
"""

import math
from dataclasses import dataclass, field
from typing import Optional, List

import structlog

from config import settings

logger = structlog.get_logger(__name__)


@dataclass
class ScalingConfig:
    """Configuration for Algorithm 2 cluster controller."""
    alpha: float = 0.01          # Linear coefficient: replicas per request/s
    beta: float = 1.0            # Base replicas (minimum even at zero load)
    buffer: float = 1.2          # 20% capacity buffer above computed requirement
    min_replicas: int = 1        # Floor
    max_replicas: int = 10       # Ceiling
    scale_down_threshold: float = 0.8  # Scale down when target < current * threshold
    prediction_interval_sec: int = 30  # How often to re-evaluate


@dataclass
class ScalingDecision:
    """Output of a single Algorithm 2 evaluation cycle."""
    predicted_load: float
    required_resources: float    # R = α·x + β (raw)
    target_replicas: int         # After buffer + clamp
    current_replicas: int
    action: str                  # SCALE_UP, SCALE_DOWN, MAINTAIN
    reason: str

    def __str__(self) -> str:
        return (
            f"[{self.action}] predicted_load={self.predicted_load:.1f} "
            f"R={self.required_resources:.2f} target={self.target_replicas} "
            f"current={self.current_replicas} — {self.reason}"
        )


class ClusterController:
    """
    Algorithm 2: Prediction-based Kubernetes resource scaling.

    Consumes GRU predictions and translates them into replica counts
    using the linear model R = α·x + β with a configurable buffer.
    """

    def __init__(
        self,
        config: Optional[ScalingConfig] = None,
        prediction_url: Optional[str] = None,
        initial_replicas: int = 1,
    ):
        self.config = config or ScalingConfig()
        self.prediction_url = prediction_url or f"{settings.GRU_SERVICE_URL}/predict"
        self.current_replicas = initial_replicas
        self.history: List[ScalingDecision] = []

    def compute_required_resources(self, predicted_load: float) -> float:
        """Compute R = α·x + β."""
        return self.config.alpha * predicted_load + self.config.beta

    def compute_target_replicas(self, predicted_load: float) -> int:
        """Compute target replicas: ceil(R * buffer), clamped to [min, max]."""
        raw = self.compute_required_resources(predicted_load)
        buffered = raw * self.config.buffer
        clamped = max(self.config.min_replicas, min(self.config.max_replicas, math.ceil(buffered)))
        return clamped

    def evaluate(self, predicted_load: float, current_replicas: Optional[int] = None) -> ScalingDecision:
        """
        Run one Algorithm 2 cycle given a predicted load value.

        Args:
            predicted_load: Predicted (or observed) request rate.
            current_replicas: Actual replica count from K8s. Falls back to
                internal state if not provided (backward compat).

        Returns a ScalingDecision (logged, not executed).
        """
        if current_replicas is None:
            current_replicas = self.current_replicas

        required = self.compute_required_resources(predicted_load)
        target = self.compute_target_replicas(predicted_load)

        if target > current_replicas:
            action = "SCALE_UP"
            reason = (
                f"Predicted load {predicted_load:.0f} req/s requires "
                f"{target} replicas (currently {current_replicas})"
            )
        elif target < current_replicas * self.config.scale_down_threshold:
            action = "SCALE_DOWN"
            reason = (
                f"Predicted load {predicted_load:.0f} req/s needs only "
                f"{target} replicas (currently {current_replicas})"
            )
        else:
            action = "MAINTAIN"
            reason = (
                f"Target {target} within threshold of "
                f"current {current_replicas}"
            )

        decision = ScalingDecision(
            predicted_load=predicted_load,
            required_resources=required,
            target_replicas=target,
            current_replicas=current_replicas,
            action=action,
            reason=reason,
        )

        logger.info(
            "algorithm2_scaling_decision",
            action=decision.action,
            predicted_load=predicted_load,
            required_resources=round(required, 3),
            target_replicas=target,
            current_replicas=current_replicas,
            alpha=self.config.alpha,
            beta=self.config.beta,
            buffer=self.config.buffer,
        )

        self.history.append(decision)
        return decision
