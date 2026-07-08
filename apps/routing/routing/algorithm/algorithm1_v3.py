#!/usr/bin/env python3
"""
Algorithm 1 V3: Capacity-Driven Baseline+Burst Routing Controller.

Replaces V2's error-driven PID+Feedforward with capacity-driven routing.
K8s always handles baseline load (up to its effective capacity). Knative
handles only the burst above K8s capacity. This is the architecture pattern
described by PulseNet (dual-track), LA-IMR (capacity-driven), and
Dehigama et al. (VMs baseline + serverless burst).

Key design decisions (oracle-reviewed):
    1. Route on AVAILABLE replicas (readyReplicas), not desired replicas.
    2. Total load = max(observed, predicted upper bound).
    3. Burst ratio = (total_load - k8s_capacity) / total_load.
    4. Budget-aware pacing via BACC-style burn-rate PI controller.
    5. Capacity-deficit mode when Knative cap binds.

References:
    - PulseNet: arxiv:2505.24551 — dual-track routing
    - LA-IMR: arxiv:2505.07417 — capacity-driven latency model
    - BACC: arxiv:2606.20575 — budget-aware burn-rate pacing
    - AAPA: arxiv:2507.05653 — confidence-weighted scaling
    - Dehigama et al.: HotInfra 2024 — VMs baseline + serverless burst
    - ElaX: Yang et al., HPCC 2019 — thesis base algorithm
"""

import math
import time
import uuid
from dataclasses import dataclass
from typing import Optional, Dict, Tuple

import requests
import structlog

from routing.monitoring.slo_monitor import SLOMonitor, SLOStatus
from routing.algorithm.metrics import (
    routing_decision_total,
)
from routing.algorithm.algorithm1_v1 import RoutingDecision

logger = structlog.get_logger(__name__)


@dataclass
class Algorithm1ConfigV3:
    """Configuration for Algorithm 1 V3 (Capacity-Driven).

    Attributes:
        r_saturation_per_replica: RPS per pod at which p99 reaches SLO threshold.
            Must be calibrated from actual testbed measurements.
        target_cpu_util: Safety margin on K8s capacity (0.7 = use 70% of saturation).
        min_k8s_replicas: Minimum K8s replicas (never scale below this).
        max_k8s_replicas: Maximum K8s replicas.
        max_knative_weight: Maximum serverless weight percentage.
        min_knative_weight: Minimum serverless weight (0 = fully K8s).
        prediction_confidence_threshold: Minimum GRU confidence to use prediction.
        total_budget_violations: Max SLO violations allowed per experiment run.
        experiment_duration_sec: Duration of a single experiment run in seconds.
        kp_burn: Proportional gain for burn-rate PI controller.
        ki_burn: Integral gain for burn-rate PI controller.
        slo_target_p99_ms: Base SLO target for p99 latency.
        knative_host: Knative service host header for pre-warm.
        knative_url: Kourier gateway URL for pre-warm.
        prewarm_timeout_sec: Timeout for Knative pre-warm request.
    """

    # K8s capacity model — values from CalibrationConfig (libs/shared/shared/models/calibration.py)
    r_saturation_per_replica: float = 35.0
    target_cpu_util: float = 0.8  # r_effective = 35 * 0.8 = 28 RPS/pod
    min_k8s_replicas: int = 3  # 3 pods × 28 = 84 RPS (covers mean 73 RPS)
    max_k8s_replicas: int = 10

    # Routing limits
    max_knative_weight: int = 50  # Lower cap — K8s should handle majority
    min_knative_weight: int = 0

    # Prediction
    prediction_confidence_threshold: float = 0.5

    # Proactive routing — trend-based amplification (S4 only; S3 has no prediction)
    # When GRU trend is rising AND load approaching cap, extrapolate forward
    # to trigger Knative routing BEFORE saturation hits.
    proactive_trend_threshold: float = 3.0  # Min per-step RPS rise to trigger
    proactive_approach_ratio: float = 0.6  # Start proactive at 60% of K8s capacity
    proactive_lookahead_steps: int = 5  # Extrapolation horizon (5 × 15s = 75s ahead)

    # Budget-aware pacing (BACC-inspired burn-rate PI)
    total_budget_violations: int = 1000
    experiment_duration_sec: int = 1200  # 20 min per run
    kp_burn: float = 0.5
    ki_burn: float = 0.05

    # SLO
    slo_target_p99_ms: float = 200.0

    # Knative integration
    knative_host: str = "test-app.default.192.168.0.2.sslip.io"
    knative_url: str = "http://localhost:8083"
    prewarm_timeout_sec: int = 30

    # Daemon compat
    healthy_margin: float = 0.7
    cooldown_sec: int = 15


class Algorithm1ControllerV3:
    """Capacity-driven baseline+burst routing controller.

    Routes traffic based on K8s effective capacity (available replicas × R_effective),
    not on SLO error. K8s handles baseline load; Knative handles only the burst.

    Used for S4 (hybrid-predictive). S3 uses V1 (reactive only).

    Attributes:
        slo_monitor: SLO monitor for p99 measurement.
        config: Controller configuration.
        current_weights: Current {'k3s': int, 'knative': int} weights.
        serverless_enabled: Whether Knative backend is active.
    """

    def __init__(
        self,
        slo_monitor: Optional[SLOMonitor] = None,
        config: Optional[Algorithm1ConfigV3] = None,
    ):
        """Initialize V3 controller.

        Args:
            slo_monitor: SLO monitor instance. If None, creates default.
            config: Controller configuration. If None, uses defaults.
        """
        self.slo_monitor = slo_monitor or SLOMonitor()
        self.config = config or Algorithm1ConfigV3()

        # State
        self.current_weights: Dict[str, int] = {"k3s": 80, "knative": 20}
        self.serverless_enabled: bool = True
        self.last_adjustment_time: Optional[int] = int(time.time())
        self.prewarm_in_progress: bool = False
        self.capacity_deficit: bool = False

        # Budget tracking (BACC-inspired)
        self.cumulative_violations: int = 0
        self._experiment_start_time: Optional[float] = None
        self._burn_integral: float = 0.0

        # Metrics counters
        self.total_decisions: int = 0
        self.scale_out_count: int = 0
        self.optimize_cost_count: int = 0
        self.predictive_count: int = 0
        self.maintain_count: int = 0

        # Violation tracking
        self.violation_detected_time: Optional[float] = None
        # Proactive routing — trend tracking (S4 only; S3 has no prediction)
        self._prediction_history: list[float] = []
        self._load_history: list[float] = []

        logger.info(
            "Algorithm1ControllerV3 initialized",
            r_saturation=self.config.r_saturation_per_replica,
            target_cpu_util=self.config.target_cpu_util,
            max_knative=self.config.max_knative_weight,
            total_budget=self.config.total_budget_violations,
        )

    @property
    def r_effective_per_replica(self) -> float:
        """Effective RPS capacity per K8s replica after safety margin."""
        return self.config.r_saturation_per_replica * self.config.target_cpu_util

    def make_decision(
        self,
        slo_status: Optional[SLOStatus] = None,
        prediction: Optional[Dict] = None,
        current_load: Optional[float] = None,
        available_replicas: int = 1,
    ) -> RoutingDecision:
        """Execute capacity-driven routing decision.

        Args:
            slo_status: Current SLO status. If None, queries monitor.
            prediction: Optional GRU prediction dict.
            current_load: Current observed load in RPS.
            available_replicas: Number of READY K8s replicas (not desired).

        Returns:
            RoutingDecision with capacity-driven weight split.
        """
        self.total_decisions += 1
        decision_id = str(uuid.uuid4())[:8]

        if self._experiment_start_time is None:
            self._experiment_start_time = time.time()

        if slo_status is None:
            slo_status = self.slo_monitor.check_slo()

        p99 = slo_status.p99_latency_ms

        # Track violations for budget
        if p99 > self.config.slo_target_p99_ms:
            self.cumulative_violations += 1
            if self.violation_detected_time is None:
                self.violation_detected_time = time.time()
        else:
            self.violation_detected_time = None

        # No-traffic guard
        if p99 <= 0 and (current_load is None or current_load <= 0):
            return self._maintain(p99, decision_id)

        # Step 1: Compute effective K8s capacity from READY replicas
        k8s_capacity = self._compute_k8s_capacity(available_replicas)

        # Step 2: Total load = max(observed, predicted upper bound)
        # S4 proactive routing: extrapolate ACTUAL load trend forward to trigger
        # Knative routing BEFORE saturation. GRU confidence gates the decision
        # (S3 sends prediction=None → skipped entirely).
        predicted_upper = 0.0

        # Track actual load for real-time trend detection
        self._load_history.append(current_load or 0)
        if len(self._load_history) > 5:
            self._load_history.pop(0)

        if prediction and prediction.get("confidence", 0) >= self.config.prediction_confidence_threshold:
            raw_pred = prediction.get("predicted_requests", 0)

            # Proactive amplification: use ACTUAL load trend (responsive) gated by
            # GRU confidence (confirms model expects sustained load).
            # GRU predictions alone lag 2+ min behind real load changes.
            if len(self._load_history) >= 3:
                n = len(self._load_history)
                load_trend = (self._load_history[-1] - self._load_history[0]) / (n - 1)
                approach_ratio = (current_load or 0) / k8s_capacity if k8s_capacity > 0 else 0

                if (
                    load_trend > self.config.proactive_trend_threshold
                    and approach_ratio > self.config.proactive_approach_ratio
                ):
                    # Extrapolate: current load + trend × lookahead horizon
                    amplified = (current_load or 0) + load_trend * self.config.proactive_lookahead_steps
                    predicted_upper = max(raw_pred, amplified)
                    logger.debug(
                        "Proactive amplification",
                        raw_pred=raw_pred,
                        amplified=round(predicted_upper, 1),
                        load_trend=round(load_trend, 1),
                        approach_ratio=round(approach_ratio, 2),
                    )
                else:
                    predicted_upper = raw_pred
            else:
                predicted_upper = raw_pred

        total_load = max(current_load or 0, predicted_upper)

        if total_load <= 0:
            return self._maintain(p99, decision_id)

        # Step 3: Compute routing split
        k8s_weight, knative_weight, capacity_deficit = self._compute_routing_split(total_load, k8s_capacity)
        self.capacity_deficit = capacity_deficit

        # Step 4: Budget-aware burn-rate pacing (BACC-inspired)
        burn_adjustment = self._burn_rate_adjustment()
        knative_weight = max(0, min(self.config.max_knative_weight, knative_weight + burn_adjustment))
        k8s_weight = 100 - knative_weight

        # Determine action label
        if knative_weight > self.current_weights.get("knative", 0):
            if predicted_upper > (current_load or 0):
                action = "PREDICTIVE"
            else:
                action = "REACTIVE"
        elif knative_weight < self.current_weights.get("knative", 0):
            action = "RECOVERY"
        else:
            action = "MAINTAIN"

        proposed_weights = {"k3s": k8s_weight, "knative": knative_weight}

        if proposed_weights == self.current_weights:
            return self._maintain(p99, decision_id)

        # Count action
        if action == "PREDICTIVE":
            self.predictive_count += 1
        elif action == "REACTIVE":
            self.scale_out_count += 1
        elif action == "RECOVERY":
            self.optimize_cost_count += 1

        routing_decision_total.labels(decision_type=action).inc()

        # Pre-warm if enabling serverless
        backend_state_changed = False
        if knative_weight > 0 and not self.serverless_enabled:
            self.serverless_enabled = True
            backend_state_changed = True
            self._prewarm_knative()
        elif knative_weight == 0 and self.serverless_enabled:
            self.serverless_enabled = False
            backend_state_changed = True

        weights_before = self.current_weights.copy()

        logger.info(
            "controller_decision_v3",
            decision_id=decision_id,
            action=action,
            p99=round(p99, 1),
            total_load=round(total_load, 1),
            k8s_capacity=round(k8s_capacity, 1),
            available_replicas=available_replicas,
            r_effective=round(self.r_effective_per_replica, 1),
            burst_ratio=round(max(0, (total_load - k8s_capacity) / total_load), 4),
            knative_weight=knative_weight,
            k8s_weight=k8s_weight,
            capacity_deficit=capacity_deficit,
            budget_remaining=self.config.total_budget_violations - self.cumulative_violations,
            burn_adjustment=burn_adjustment,
            confidence=prediction.get("confidence", 0) if prediction else 0,
            predicted_load=prediction.get("predicted_requests", 0) if prediction else 0,
            current_load=current_load or 0,
            weights_before=weights_before,
            weights_after=proposed_weights,
            serverless_enabled=self.serverless_enabled,
        )

        reason = self._build_reason(action, total_load, k8s_capacity, capacity_deficit)

        return RoutingDecision(
            weights=proposed_weights,
            reason=reason,
            action=action,
            metrics={
                "p99": p99,
                "total_load": total_load,
                "k8s_capacity": k8s_capacity,
                "available_replicas": available_replicas,
                "burst_ratio": max(0, (total_load - k8s_capacity) / total_load),
                "capacity_deficit": int(capacity_deficit),
                "budget_remaining": self.config.total_budget_violations - self.cumulative_violations,
            },
            backend_state_changed=backend_state_changed,
        )

    def _compute_k8s_capacity(self, available_replicas: int) -> float:
        """Compute effective K8s capacity from ready replicas.

        Uses available_replicas (readyReplicas) not desired_replicas.
        Applies target_cpu_util safety margin.

        Args:
            available_replicas: Number of READY K8s pods.

        Returns:
            Effective K8s capacity in RPS.
        """
        return max(0, available_replicas) * self.r_effective_per_replica

    def _compute_routing_split(self, total_load: float, k8s_capacity: float) -> Tuple[int, int, bool]:
        """Compute K8s/Knative weight split based on capacity vs load.

        K8s handles up to its effective capacity. Burst above capacity
        goes to Knative. If burst exceeds max_knative_weight, enter
        capacity-deficit mode.

        Args:
            total_load: Total traffic load in RPS.
            k8s_capacity: Effective K8s capacity in RPS.

        Returns:
            Tuple of (k8s_weight, knative_weight, capacity_deficit).
        """
        if total_load <= k8s_capacity:
            return 100, 0, False

        burst_ratio = (total_load - k8s_capacity) / total_load
        knative_pct = burst_ratio * 100

        if knative_pct > self.config.max_knative_weight:
            knative_weight = self.config.max_knative_weight
            k8s_weight = 100 - knative_weight
            return k8s_weight, knative_weight, True

        knative_weight = int(math.ceil(knative_pct))
        knative_weight = max(self.config.min_knative_weight, knative_weight)
        k8s_weight = 100 - knative_weight
        return k8s_weight, knative_weight, False

    def _burn_rate_adjustment(self) -> int:
        """Compute BACC-inspired burn-rate adjustment to Knative weight.

        Compares actual violation burn-rate against allowed budget burn-rate.
        If burning too fast, increases Knative weight. If burning slow,
        prefers K8s.

        Returns:
            Weight adjustment (positive = more Knative, negative = more K8s).
        """
        elapsed = time.time() - (self._experiment_start_time or time.time())
        if elapsed < 1:
            return 0

        actual_burn = self.cumulative_violations / elapsed
        allowed_burn = self.config.total_budget_violations / self.config.experiment_duration_sec

        if allowed_burn <= 0:
            return 0

        burn_ratio = actual_burn / allowed_burn
        burn_error = burn_ratio - 1.0  # Positive = overspending budget

        self._burn_integral += burn_error
        self._burn_integral = max(-5.0, min(5.0, self._burn_integral))  # Anti-windup

        adjustment = int((self.config.kp_burn * burn_error + self.config.ki_burn * self._burn_integral) * 10)

        logger.debug(
            "burn_rate_adjustment",
            actual_burn=round(actual_burn, 2),
            allowed_burn=round(allowed_burn, 2),
            burn_ratio=round(burn_ratio, 3),
            burn_error=round(burn_error, 3),
            adjustment=adjustment,
            budget_remaining=self.config.total_budget_violations - self.cumulative_violations,
        )

        return adjustment

    def _build_reason(self, action: str, total_load: float, k8s_capacity: float, deficit: bool) -> str:
        """Build human-readable reason string."""
        parts = [f"load={total_load:.0f}RPS", f"k8s_cap={k8s_capacity:.0f}RPS"]
        if deficit:
            parts.append("CAPACITY-DEFICIT")
        if action == "PREDICTIVE":
            parts.append("(prediction-driven)")
        elif action == "REACTIVE":
            parts.append("(burst-routing)")
        elif action == "RECOVERY":
            parts.append("(reducing-serverless)")
        return " | ".join(parts)

    def _maintain(self, p99: float, decision_id: str) -> RoutingDecision:
        """Return MAINTAIN decision."""
        self.maintain_count += 1
        routing_decision_total.labels(decision_type="MAINTAIN").inc()
        return RoutingDecision(
            weights=self.current_weights.copy(),
            reason=f"Maintain (p99={p99:.0f}ms)",
            action="MAINTAIN",
            metrics={"p99": p99},
        )

    def commit_applied_decision(self, decision: RoutingDecision, current_time: Optional[int] = None) -> None:
        """Commit decision state after daemon successfully applies weights."""
        self.current_weights = decision.weights.copy()
        now = current_time if current_time is not None else int(time.time())
        if decision.action in {"REACTIVE", "PREDICTIVE", "RECOVERY"}:
            self.last_adjustment_time = now
        if decision.action in {"REACTIVE", "PREDICTIVE"} and decision.weights["knative"] > 0:
            self.serverless_enabled = True
        elif decision.action == "RECOVERY" and decision.weights["knative"] == 0:
            self.serverless_enabled = False

    def get_statistics(self) -> Dict:
        """Get decision statistics."""
        return {
            "total_decisions": self.total_decisions,
            "scale_out_count": self.scale_out_count,
            "optimize_cost_count": self.optimize_cost_count,
            "predictive_count": self.predictive_count,
            "maintain_count": self.maintain_count,
            "current_weights": self.current_weights,
            "serverless_enabled": self.serverless_enabled,
            "controller_version": "v3",
            "cumulative_violations": self.cumulative_violations,
            "budget_remaining": self.config.total_budget_violations - self.cumulative_violations,
            "capacity_deficit": self.capacity_deficit,
            "r_effective_per_replica": round(self.r_effective_per_replica, 1),
        }

    def _prewarm_knative(self) -> bool:
        """Pre-warm Knative service to eliminate cold start."""
        if self.prewarm_in_progress:
            return True
        self.prewarm_in_progress = True
        try:
            start = time.time()
            response = requests.get(
                f"{self.config.knative_url}/health",
                headers={"Host": self.config.knative_host},
                timeout=self.config.prewarm_timeout_sec,
            )
            cold_ms = (time.time() - start) * 1000
            if response.status_code == 200:
                logger.info("Knative pre-warm OK", cold_start_ms=round(cold_ms, 1))
                return True
            logger.warning("Knative pre-warm non-200", status=response.status_code)
            return False
        except Exception as e:
            logger.error("Knative pre-warm failed", error=str(e))
            return False
        finally:
            self.prewarm_in_progress = False

    def is_serverless_enabled(self) -> bool:
        return self.serverless_enabled

    def force_enable_serverless(self) -> bool:
        if not self.serverless_enabled:
            self.serverless_enabled = True
            self._prewarm_knative()
        return self.serverless_enabled

    def force_disable_serverless(self) -> bool:
        if self.serverless_enabled:
            self.serverless_enabled = False
            self.current_weights = {"k3s": 100, "knative": 0}
        return not self.serverless_enabled
