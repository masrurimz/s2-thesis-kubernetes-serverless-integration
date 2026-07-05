#!/usr/bin/env python3
"""
Algorithm 1 V2: PID + Feedforward Routing Controller.

This controller replaces the bang-bang priority-cascade of V1 with a unified
PID feedback loop augmented by GRU-based feedforward. The feedforward signal
modulates the reactive response in ALL controller states — not just when the
system is healthy — which fixes the core defect of V1 where PREDICTIVE could
never fire because the system was permanently in SLO violation.

Design informed by:
    - AAPA (Zhang et al., arXiv:2507.05653, 2025): confidence-weighted scaling
    - ADAPT (Baghel, arXiv:2605.15788, 2026): cold-start EWMA estimation
    - STaleX (arXiv:2501.18734, 2025): weighted PID with dead-zone hysteresis
    - ARIMA-PID (MTAP 2023): hybrid prediction + PID control
    - ElaX (Yang et al., HPCC 2019): the thesis base algorithm

Control architecture::

    GRU prediction ──→ Feedforward ──→ adjustment_ff
                                          │
    p99 measurement ─→ PID (error) ──→ adjustment_fb ──→ Combine ──→ new_weight
    SLO target ───────↗                                    ff + fb

The PID controller produces a proportional response to SLO violations:
    - P term: immediate error response (larger violation → larger shift)
    - I term: accumulated persistent error (prevents steady-state offset)
    - D term: rate of change (dampens oscillation, faster response to spikes)

The feedforward term anticipates future load changes from GRU predictions:
    - Positive load change → shift toward serverless (proactive)
    - Negative load change → shift toward K8s (anticipate recovery)
    - Confidence modulates magnitude (AAPA pattern)
"""

import time
import uuid
from dataclasses import dataclass
from typing import Optional, Dict, List

import requests
import structlog

from routing.monitoring.slo_monitor import SLOMonitor, SLOStatus
from routing.algorithm.metrics import (
    slo_violation_total,
    routing_decision_total,
    reaction_time_ms,
)
from routing.algorithm.algorithm1_v1 import RoutingDecision

logger = structlog.get_logger(__name__)


@dataclass
class Algorithm1ConfigV2:
    """Configuration for Algorithm 1 V2 (PID + Feedforward).

    Attributes:
        kp: Proportional gain — weight adjustment per unit normalized error.
        ki: Integral gain — accumulated persistent error (anti-windup clamped).
        kd: Derivative gain — rate of error change, dampens oscillation.
        kff: Feedforward gain — weight given to GRU-predicted load change.
        slo_target_p99_ms: Base SLO target for p99 latency in milliseconds.
        hysteresis_factor: Dead-zone width as fraction of target (e.g. 0.2 = ±20%).
        adaptive_target: If True, compute target from warmup baseline p99.
        max_serverless_weight: Maximum serverless (Knative) weight percentage.
        min_serverless_weight: Minimum serverless weight percentage.
        default_serverless_weight: Baseline serverless weight for S4 (e.g. 20).
        recovery_step: Weight reduction per cycle when healthy (toward baseline).
        recovery_delay_sec: Seconds of sustained health before recovery begins.
        prediction_confidence_threshold: Minimum GRU confidence to act on.
        min_load_change_threshold: Minimum |load_change| to trigger feedforward.
        cold_start_alpha: EWMA smoothing factor for cold-start estimation.
        cold_start_safety: Safety multiplier on EWMA for pre-warm horizon.
        cooldown_sec: Minimum seconds between weight adjustments.
        integral_min: Anti-windup lower clamp for integral term.
        integral_max: Anti-windup upper clamp for integral term.
    """

    # PID gains
    kp: float = 0.15
    ki: float = 0.005
    kd: float = 0.08

    # Feedforward gain
    kff: float = 0.1

    # Thresholds
    slo_target_p99_ms: float = 200.0
    hysteresis_factor: float = 0.2  # 20% dead zone
    adaptive_target: bool = True

    # Weight limits
    max_serverless_weight: int = 70
    min_serverless_weight: int = 0
    default_serverless_weight: int = 20

    # Recovery
    recovery_step: int = 3
    recovery_delay_sec: int = 30

    # Prediction
    prediction_confidence_threshold: float = 0.5
    min_load_change_threshold: float = 0.1  # 10% change to act

    # Cold-start estimation (ADAPT)
    cold_start_alpha: float = 0.3
    cold_start_safety: float = 1.2

    # Cooldown
    cooldown_sec: int = 15
    max_weight_delta_per_step: int = 15  # Max weight change per decision cycle

    # Anti-windup
    integral_min: float = -10.0
    integral_max: float = 10.0

    # Knative integration (same as V1)
    healthy_margin: float = 0.7  # For daemon compatibility (Algorithm 2 readiness gate)
    knative_host: str = "test-app.default.127.0.0.1.sslip.io"
    knative_url: str = "http://localhost:8083"
    prewarm_timeout_sec: int = 30


class Algorithm1ControllerV2:
    """PID + Feedforward routing controller for hybrid K8s-serverless architecture.

    Replaces V1's bang-bang priority cascade with a unified control loop. The
    PID feedback reacts to current SLO error; the GRU feedforward anticipates
    future load changes. Both signals combine into a single weight adjustment.

    This controller is used for S4 (hybrid-predictive). S3 uses V1 (reactive only).

    Attributes:
        slo_monitor: SLO monitor instance for p99 measurement.
        config: Controller configuration (PID gains, thresholds, limits).
        current_weights: Current {'k3s': int, 'knative': int} weights.
        serverless_enabled: Whether Knative backend is currently active.
    """

    def __init__(
        self,
        slo_monitor: Optional[SLOMonitor] = None,
        config: Optional[Algorithm1ConfigV2] = None,
    ):
        """Initialize the V2 controller.

        Args:
            slo_monitor: SLO monitor for p99 latency measurement.
                If None, a default SLOMonitor is created.
            config: Controller configuration. If None, uses defaults.
        """
        self.slo_monitor = slo_monitor or SLOMonitor()
        self.config = config or Algorithm1ConfigV2()

        # State tracking
        self.last_adjustment_time: Optional[int] = int(time.time())
        self.current_weights: Dict[str, int] = {
            "k3s": 100 - self.config.default_serverless_weight,
            "knative": self.config.default_serverless_weight,
        }
        self.serverless_enabled: bool = self.current_weights["knative"] > 0

        # PID state
        self._integral: float = 0.0
        self._prev_error: float = 0.0

        # Adaptive target state
        self._baseline_p99_values: List[float] = []
        self._adaptive_target: Optional[float] = None
        self._warmup_end_time: Optional[float] = None

        # Cold-start EWMA (ADAPT)
        self._cold_start_ewma: float = 0.0
        self._cold_start_initialized: bool = False

        # Recovery state
        self._healthy_since: Optional[float] = None

        # Pre-warm state
        self.prewarm_in_progress: bool = False

        # Metrics counters (same interface as V1)
        self.total_decisions: int = 0
        self.scale_out_count: int = 0
        self.optimize_cost_count: int = 0
        self.predictive_count: int = 0
        self.maintain_count: int = 0

        # Violation tracking (same as V1)
        self.violation_detected_time: Optional[float] = None

        logger.info(
            "Algorithm1ControllerV2 initialized",
            kp=self.config.kp,
            ki=self.config.ki,
            kd=self.config.kd,
            kff=self.config.kff,
            max_serverless=self.config.max_serverless_weight,
            adaptive_target=self.config.adaptive_target,
        )

    def make_decision(
        self,
        slo_status: Optional[SLOStatus] = None,
        prediction: Optional[Dict] = None,
        current_load: Optional[float] = None,
    ) -> RoutingDecision:
        """Execute the PID + feedforward control loop.

        This is the main entry point called by the routing daemon every
        ``config.cooldown_sec`` seconds. It combines PID feedback on current
        SLO error with GRU feedforward on predicted load change.

        Args:
            slo_status: Current SLO status. If None, queries the SLO monitor.
            prediction: Optional GRU prediction dict with keys
                'predicted_requests' and 'confidence'.
            current_load: Current observed load in requests per second.

        Returns:
            RoutingDecision with new weights and action label.
        """
        self.total_decisions += 1
        current_time = int(time.time())
        decision_id = str(uuid.uuid4())[:8]

        # Get SLO status if not provided
        if slo_status is None:
            slo_status = self.slo_monitor.check_slo()

        p99 = slo_status.p99_latency_ms
        # No-traffic guard: if p99=0 (no requests), don't adjust weights
        # This prevents the controller from drifting during warmup/idle periods
        if p99 <= 0:
            return self._maintain(0.0, self._compute_adaptive_target(), 0.0, str(uuid.uuid4())[:8])

        # Track warmup baseline for adaptive target
        self._track_warmup(p99, current_time)

        # Compute adaptive target
        target_p99 = self._compute_adaptive_target()

        # Track violation detection time for reaction metric
        if slo_status.violation_duration_sec > 0 and self.violation_detected_time is None:
            self.violation_detected_time = time.time()
        elif slo_status.violation_duration_sec == 0:
            self.violation_detected_time = None

        # Check cooldown
        can_adjust = self._can_adjust(current_time)

        # Normalized error: positive = violation, negative = healthy
        if target_p99 > 0:
            error = (p99 - target_p99) / target_p99
        else:
            error = 0.0

        # --- Hysteresis dead zone ---
        in_dead_zone = abs(error) < self.config.hysteresis_factor

        # --- GRU feedforward (works in ALL states) ---
        feedforward = self._compute_feedforward(prediction, current_load)

        # --- Dead zone: only feedforward can act ---
        if in_dead_zone and can_adjust:
            if abs(feedforward) > 0.05:  # Significant enough to produce ~5 weight points
                # Significant prediction — act proactively
                return self._apply_adjustment(
                    feedforward,
                    p99,
                    target_p99,
                    error,
                    prediction,
                    current_load,
                    current_time,
                    decision_id,
                    action="PREDICTIVE",
                )
            # No prediction in dead zone — maintain
            return self._maintain(p99, target_p99, error, decision_id)

        elif not can_adjust:
            # Cooldown active — maintain
            return self._maintain(p99, target_p99, error, decision_id)

        # --- Outside dead zone: PID feedback + feedforward ---

        # PID feedback
        pid_p, pid_i, pid_d = self._compute_pid(error, dt=self.config.cooldown_sec)
        feedback = pid_p + pid_i + pid_d

        # Combined adjustment
        total_adjustment = feedback + feedforward

        # Determine action label for metrics
        if abs(feedforward) > abs(feedback) and abs(feedforward) > 0.5:
            action = "PREDICTIVE"
        elif error > 0:
            action = "REACTIVE"  # SCALE_OUT equivalent
        else:
            action = "RECOVERY"  # OPTIMIZE_COST equivalent

        # Compute new weights
        weight_delta = int(round(total_adjustment * 100))
        # Clamp per-step delta to prevent extreme jumps
        max_delta = self.config.max_weight_delta_per_step
        weight_delta = max(-max_delta, min(max_delta, weight_delta))
        new_serverless = self.current_weights["knative"] + weight_delta
        new_serverless = max(
            self.config.min_serverless_weight,
            min(self.config.max_serverless_weight, new_serverless),
        )
        new_k3s = 100 - new_serverless
        proposed_weights = {"k3s": new_k3s, "knative": new_serverless}

        # If no effective change, maintain
        if proposed_weights == self.current_weights:
            return self._maintain(p99, target_p99, error, decision_id)

        # Count action
        if action == "PREDICTIVE":
            self.predictive_count += 1
        elif action == "REACTIVE":
            self.scale_out_count += 1
        elif action == "RECOVERY":
            self.optimize_cost_count += 1

        routing_decision_total.labels(decision_type=action).inc()

        # Pre-warm Knative if shifting toward serverless and not enabled
        backend_state_changed = False
        if total_adjustment > 0 and not self.serverless_enabled:
            self.serverless_enabled = True
            backend_state_changed = True
            self._prewarm_knative()

        # Disable serverless if weight reaches 0
        if new_serverless == 0 and self.serverless_enabled:
            backend_state_changed = True

        # Reaction time metric
        if self.violation_detected_time is not None and action == "REACTIVE":
            reaction_ms = (time.time() - self.violation_detected_time) * 1000
            reaction_time_ms.observe(reaction_ms)
            self.violation_detected_time = None

        if action == "REACTIVE":
            slo_violation_total.labels(slo_name="p99_latency").inc()

        weights_before = self.current_weights.copy()

        logger.info(
            "controller_decision",
            decision_id=decision_id,
            action=action,
            p99=round(p99, 1),
            target_p99=round(target_p99, 1),
            error=round(error, 4),
            pid_p=round(pid_p, 4),
            pid_i=round(pid_i, 4),
            pid_d=round(pid_d, 4),
            feedforward=round(feedforward, 4),
            total_adjustment=round(total_adjustment, 4),
            weight_delta=weight_delta,
            weights_before=weights_before,
            weights_after=proposed_weights,
            confidence=prediction.get("confidence", 0) if prediction else 0,
            predicted_load=prediction.get("predicted_requests", 0) if prediction else 0,
            current_load=current_load or 0,
            serverless_enabled=self.serverless_enabled,
            backend_state_changed=backend_state_changed,
        )

        reason = self._build_reason(action, p99, target_p99, error, prediction, current_load)

        return RoutingDecision(
            weights=proposed_weights,
            reason=reason,
            action=action,
            metrics={
                "p99": p99,
                "target_p99": target_p99,
                "error": error,
                "pid_p": pid_p,
                "pid_i": pid_i,
                "pid_d": pid_d,
                "feedforward": feedforward,
                "total_adjustment": total_adjustment,
            },
            backend_state_changed=backend_state_changed,
        )

    def _compute_pid(self, error: float, dt: int) -> tuple[float, float, float]:
        """Compute PID feedback terms.

        The PID controller produces a proportional response to SLO violations.
        Inspired by STaleX (arXiv:2501.18734) weighted PID controllers and
        ARIMA-PID (MTAP 2023) hybrid prediction+control approach.

        Terms:
            - P (Proportional): Immediate error response. Larger violation →
              larger weight shift. This replaces V1's fixed weight_step.
            - I (Integral): Accumulated persistent error. Prevents steady-state
              offset where the controller settles at a suboptimal weight.
              Anti-windup clamping prevents runaway accumulation.
            - D (Derivative): Rate of error change. Dampens oscillation by
              detecting rapid changes and responding faster to spikes.

        Args:
            error: Normalized SLO error (p99 - target) / target.
                Positive = violation, negative = healthy.
            dt: Time delta in seconds since last decision.

        Returns:
            Tuple of (P_term, I_term, D_term) — individual PID contributions.
        """
        # P term: proportional to current error
        p_term = self.config.kp * error

        # I term: accumulate error, clamp to prevent windup
        self._integral += error * dt
        self._integral = max(
            self.config.integral_min,
            min(self.config.integral_max, self._integral),
        )
        i_term = self.config.ki * self._integral

        # D term: rate of error change
        d_term = self.config.kd * (error - self._prev_error) / max(dt, 1)
        self._prev_error = error

        logger.debug(
            "pid_computation",
            error=round(error, 4),
            p_term=round(p_term, 4),
            i_term=round(i_term, 4),
            d_term=round(d_term, 4),
            integral=round(self._integral, 4),
        )

        return p_term, i_term, d_term

    def _compute_feedforward(
        self,
        prediction: Optional[Dict],
        current_load: Optional[float],
    ) -> float:
        """Compute GRU-based feedforward adjustment.

        The feedforward term anticipates future load changes from GRU
        predictions. Unlike V1's PREDICTIVE mode, this fires in ALL controller
        states — during violation, it augments the reactive response; during
        health, it provides proactive pre-warming.

        Inspired by AAPA (arXiv:2507.05653) confidence-weighted scaling:
        the prediction confidence modulates the magnitude of the adjustment.
        Lower confidence → smaller shift, hedging against prediction errors.

        Args:
            prediction: GRU prediction dict with keys 'predicted_requests'
                and 'confidence'. None if no prediction available.
            current_load: Current observed load in RPS. None if unavailable.

        Returns:
            Feedforward adjustment value. Positive = shift toward serverless,
            negative = shift toward K8s, 0 = no action.
        """
        if prediction is None:
            return 0.0

        confidence = prediction.get("confidence", 0)
        predicted_load = prediction.get("predicted_requests", 0)

        # Gate on confidence
        if confidence < self.config.prediction_confidence_threshold:
            return 0.0

        # Need current load to compute change ratio
        if current_load is None or current_load <= 0:
            return 0.0

        # Normalized load change: positive = increase, negative = decrease
        load_change = (predicted_load - current_load) / current_load

        # Gate on minimum change threshold
        if abs(load_change) < self.config.min_load_change_threshold:
            return 0.0

        # Feedforward: proportional to predicted load change, weighted by confidence
        # Kff * load_change * confidence
        # Positive load_change → positive ff → shift toward serverless
        # Negative load_change → negative ff → shift toward K8s
        ff = self.config.kff * load_change * confidence

        logger.debug(
            "feedforward_computation",
            confidence=round(confidence, 3),
            predicted_load=predicted_load,
            current_load=round(current_load, 1),
            load_change=round(load_change, 4),
            feedforward=round(ff, 4),
        )

        return ff

    def _track_warmup(self, p99: float, current_time: int) -> None:
        """Track p99 values during warmup period for adaptive target computation.

        During the first 60 seconds, collects p99 samples to compute a baseline.
        After warmup, the adaptive target is fixed for the rest of the run.

        Args:
            p99: Current p99 latency in milliseconds.
            current_time: Current Unix timestamp.
        """
        if not self.config.adaptive_target:
            return

        if self._warmup_end_time is None:
            # First call — set warmup end time
            self._warmup_end_time = current_time + 60

        if self._adaptive_target is not None:
            return  # Already computed

        if current_time < self._warmup_end_time and p99 > 0:
            self._baseline_p99_values.append(p99)
        elif current_time >= self._warmup_end_time and self._baseline_p99_values:
            # Warmup complete — compute adaptive target
            import statistics

            baseline = statistics.median(self._baseline_p99_values)
            self._adaptive_target = max(
                self.config.slo_target_p99_ms,
                baseline * 1.5,
            )
            logger.info(
                "adaptive_target_computed",
                baseline_p99=round(baseline, 1),
                target_p99=round(self._adaptive_target, 1),
                samples=len(self._baseline_p99_values),
            )

    def _compute_adaptive_target(self) -> float:
        """Compute the SLO target for the current state.

        If adaptive target is enabled and warmup is complete, returns the
        baseline-derived target. Otherwise falls back to the fixed config target.

        Inspired by ADAPT (arXiv:2605.15788) dynamic horizon estimation:
        the target adapts to observed baseline rather than using a fixed value
        that may be unrealistic for the testbed.

        Returns:
            Target p99 latency in milliseconds.
        """
        if self._adaptive_target is not None:
            return self._adaptive_target
        return self.config.slo_target_p99_ms

    def _update_cold_start_ewma(self, observed_delay: float) -> None:
        """Update cold-start EWMA estimator.

        Tracks observed provisioning delays using exponentially weighted moving
        average. This informs the pre-warming horizon — how far ahead to trigger
        Knative pre-warming before predicted load arrives.

        From ADAPT (arXiv:2605.15788): the EWMA replaces a static cold-start
        constant with a live estimate that adapts to runtime conditions.

        Args:
            observed_delay: Observed cold-start duration in seconds.
        """
        if not self._cold_start_initialized:
            self._cold_start_ewma = observed_delay
            self._cold_start_initialized = True
        else:
            alpha = self.config.cold_start_alpha
            self._cold_start_ewma = alpha * observed_delay + (1 - alpha) * self._cold_start_ewma

        logger.debug(
            "cold_start_ewma_updated",
            observed_delay=round(observed_delay, 2),
            ewma=round(self._cold_start_ewma, 2),
        )

    def _apply_adjustment(
        self,
        adjustment: float,
        p99: float,
        target_p99: float,
        error: float,
        prediction: Optional[Dict],
        current_load: Optional[float],
        current_time: int,
        decision_id: str,
        action: str = "PREDICTIVE",
    ) -> RoutingDecision:
        """Apply a single feedforward-only adjustment (used in dead zone).

        Args:
            adjustment: Feedforward adjustment value.
            p99: Current p99 latency.
            target_p99: Current SLO target.
            error: Normalized error.
            prediction: GRU prediction dict (if available).
            current_load: Current load in RPS.
            current_time: Current timestamp.
            decision_id: Unique decision identifier for logging.
            action: Action label (default 'PREDICTIVE').

        Returns:
            RoutingDecision with adjusted weights.
        """
        weight_delta = int(round(adjustment * 100))
        # Clamp per-step delta
        max_delta = self.config.max_weight_delta_per_step
        weight_delta = max(-max_delta, min(max_delta, weight_delta))
        new_serverless = self.current_weights["knative"] + weight_delta
        new_serverless = max(
            self.config.min_serverless_weight,
            min(self.config.max_serverless_weight, new_serverless),
        )
        new_k3s = 100 - new_serverless
        proposed_weights = {"k3s": new_k3s, "knative": new_serverless}

        if proposed_weights == self.current_weights:
            return self._maintain(p99, target_p99, error, decision_id)

        self.predictive_count += 1
        routing_decision_total.labels(decision_type="PREDICTIVE").inc()

        backend_state_changed = False
        if adjustment > 0 and not self.serverless_enabled:
            self.serverless_enabled = True
            backend_state_changed = True
            self._prewarm_knative()

        ff = adjustment
        logger.info(
            "controller_decision",
            decision_id=decision_id,
            action=action,
            p99=round(p99, 1),
            target_p99=round(target_p99, 1),
            error=round(error, 4),
            pid_p=0.0,
            pid_i=0.0,
            pid_d=0.0,
            feedforward=round(ff, 4),
            total_adjustment=round(ff, 4),
            weight_delta=weight_delta,
            weights_before=self.current_weights.copy(),
            weights_after=proposed_weights,
            confidence=prediction.get("confidence", 0) if prediction else 0,
            predicted_load=prediction.get("predicted_requests", 0) if prediction else 0,
            current_load=current_load or 0,
            serverless_enabled=self.serverless_enabled,
            backend_state_changed=backend_state_changed,
            note="dead_zone_feedforward",
        )

        return RoutingDecision(
            weights=proposed_weights,
            reason=f"Predictive adjustment in dead zone (ff={ff:.3f})",
            action=action,
            metrics={"p99": p99, "target_p99": target_p99, "error": error, "feedforward": ff},
            backend_state_changed=backend_state_changed,
        )

    def _maintain(self, p99: float, target_p99: float, error: float, decision_id: str) -> RoutingDecision:
        """Return a MAINTAIN decision (no weight change).

        Args:
            p99: Current p99 latency.
            target_p99: Current SLO target.
            error: Normalized error.
            decision_id: Unique decision identifier.

        Returns:
            RoutingDecision with action='MAINTAIN' and current weights.
        """
        self.maintain_count += 1
        routing_decision_total.labels(decision_type="MAINTAIN").inc()

        return RoutingDecision(
            weights=self.current_weights.copy(),
            reason=f"Maintain (p99={p99:.0f}ms, target={target_p99:.0f}ms, error={error:.3f})",
            action="MAINTAIN",
            metrics={"p99": p99, "target_p99": target_p99, "error": error},
        )

    def _build_reason(
        self,
        action: str,
        p99: float,
        target_p99: float,
        error: float,
        prediction: Optional[Dict],
        current_load: Optional[float],
    ) -> str:
        """Build a human-readable reason string for the decision.

        Args:
            action: Action label.
            p99: Current p99 latency.
            target_p99: Current SLO target.
            error: Normalized error.
            prediction: GRU prediction dict.
            current_load: Current load.

        Returns:
            Reason string.
        """
        if action == "REACTIVE":
            return f"SLO violation (p99={p99:.0f}ms > target={target_p99:.0f}ms)"
        elif action == "PREDICTIVE":
            conf = prediction.get("confidence", 0) if prediction else 0
            pred = prediction.get("predicted_requests", 0) if prediction else 0
            return f"Predictive (predicted={pred:.0f} RPS, confidence={conf:.0%})"
        elif action == "RECOVERY":
            return f"Recovery (p99={p99:.0f}ms < target={target_p99:.0f}ms)"
        return f"Maintenance (p99={p99:.0f}ms)"

    def _can_adjust(self, current_time: int) -> bool:
        """Check if cooldown period has passed since last adjustment.

        Args:
            current_time: Current Unix timestamp.

        Returns:
            True if enough time has passed for a new adjustment.
        """
        if self.last_adjustment_time is None:
            return True
        return current_time - self.last_adjustment_time >= self.config.cooldown_sec

    def commit_applied_decision(self, decision: RoutingDecision, current_time: Optional[int] = None) -> None:
        """Commit decision effects after daemon successfully applies weights.

        This method is called by the daemon AFTER weights have been written to
        HAProxy. It updates internal controller state to match the applied
        decision. This prevents stale decisions from corrupting state if the
        HAProxy weight application fails.

        Args:
            decision: The RoutingDecision that was successfully applied.
            current_time: Current timestamp. If None, uses time.time().
        """
        self.current_weights = decision.weights.copy()
        now = current_time if current_time is not None else int(time.time())

        if decision.action in {"REACTIVE", "PREDICTIVE", "RECOVERY"}:
            self.last_adjustment_time = now

        if decision.action in {"REACTIVE", "PREDICTIVE"} and decision.weights["knative"] > 0:
            self.serverless_enabled = True
        elif decision.action == "RECOVERY" and decision.weights["knative"] == 0:
            self.serverless_enabled = False

    def get_statistics(self) -> Dict:
        """Get decision statistics for monitoring and reporting.

        Returns:
            Dict with counts, current weights, and controller state.
        """
        return {
            "total_decisions": self.total_decisions,
            "scale_out_count": self.scale_out_count,
            "optimize_cost_count": self.optimize_cost_count,
            "predictive_count": self.predictive_count,
            "maintain_count": self.maintain_count,
            "current_weights": self.current_weights,
            "last_adjustment": self.last_adjustment_time,
            "serverless_enabled": self.serverless_enabled,
            "controller_version": "v2",
            "integral": round(self._integral, 4),
            "adaptive_target": round(self._adaptive_target, 1) if self._adaptive_target else None,
            "cold_start_ewma": round(self._cold_start_ewma, 2) if self._cold_start_initialized else None,
        }

    def _prewarm_knative(self) -> bool:
        """Send a synthetic request to trigger Knative cold start.

        This ensures the serverless backend is ready before traffic is routed
        to it. Called proactively when shifting weight toward serverless.

        Returns:
            True if pre-warm succeeded, False otherwise.
        """
        if self.prewarm_in_progress:
            logger.debug("Pre-warm already in progress, skipping")
            return True

        self.prewarm_in_progress = True
        start_time = time.time()
        try:
            logger.info(
                "Pre-warming Knative service",
                url=self.config.knative_url,
                host=self.config.knative_host,
            )

            response = requests.get(
                f"{self.config.knative_url}/health",
                headers={"Host": self.config.knative_host},
                timeout=self.config.prewarm_timeout_sec,
            )

            cold_start_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                # Update cold-start EWMA
                self._update_cold_start_ewma(cold_start_ms / 1000.0)
                logger.info(
                    "Knative pre-warm successful",
                    cold_start_ms=round(cold_start_ms, 1),
                    status=response.status_code,
                )
                return True
            else:
                logger.warning(
                    "Knative pre-warm returned non-200",
                    status=response.status_code,
                    cold_start_ms=round(cold_start_ms, 1),
                )
                return False

        except requests.Timeout:
            logger.warning("Knative pre-warm timed out", timeout_sec=self.config.prewarm_timeout_sec)
            return False
        except Exception as e:
            logger.error("Knative pre-warm failed", error=str(e))
            return False
        finally:
            self.prewarm_in_progress = False

    def is_serverless_enabled(self) -> bool:
        """Check if serverless backend is currently enabled.

        Returns:
            True if serverless is enabled.
        """
        return self.serverless_enabled

    def force_enable_serverless(self) -> bool:
        """Force enable serverless backend (for testing/manual control).

        Returns:
            True if serverless is enabled after this call.
        """
        if not self.serverless_enabled:
            self.serverless_enabled = True
            self._prewarm_knative()
            logger.info("Serverless backend force-enabled")
        return self.serverless_enabled

    def force_disable_serverless(self) -> bool:
        """Force disable serverless backend (for testing/manual control).

        Returns:
            True if serverless is disabled after this call.
        """
        if self.serverless_enabled:
            self.serverless_enabled = False
            self.current_weights = {"k3s": 100, "knative": 0}
            logger.info("Serverless backend force-disabled")
        return not self.serverless_enabled
