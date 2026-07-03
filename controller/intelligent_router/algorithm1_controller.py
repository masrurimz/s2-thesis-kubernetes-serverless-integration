#!/usr/bin/env python3
"""
Algorithm 1: SLO-Aware Routing Controller

Implements the core routing logic from thesis section 3.4.3.1.
Updated for real Knative integration with ENABLE/DISABLE backend state management.
"""

import time
from dataclasses import dataclass
from typing import Optional, Dict, Callable

import requests
import structlog

from monitoring_v2.slo_monitor import SLOMonitor, SLOConfig, SLOStatus
from intelligent_router.metrics import (
    slo_violation_total,
    routing_decision_total,
    reaction_time_ms,
)
from config import settings

logger = structlog.get_logger(__name__)


@dataclass
class Algorithm1Config:
    """Configuration for Algorithm 1."""
    weight_step: int = 10  # Weight adjustment step
    cooldown_sec: int = 15  # Minimum time between adjustments
    healthy_margin: float = 0.7  # Multiplier for healthy threshold
    max_knative_weight: int = 50  # Maximum serverless weight
    min_k3s_weight: int = 50  # Minimum k8s weight
    prediction_confidence_threshold: float = 0.5  # Lowered from 0.7 to enable PREDICTIVE actions for H2 validation
    load_change_threshold: float = 0.3  # Significant load change
    # Real Knative integration settings
    default_k3s_weight: int = 100  # Default: 100% K8s
    default_knative_weight: int = 0  # Default: 0% serverless (disabled)
    knative_host: str = "test-app.default.127.0.0.1.sslip.io"  # Knative service host header
    knative_url: str = "http://localhost:8081"  # Kourier gateway URL (k3d mapped port)
    prewarm_timeout_sec: int = 30  # Timeout for Knative pre-warm request


@dataclass
class RoutingDecision:
    """Output of Algorithm 1 routing decision."""
    weights: Dict[str, int]
    reason: str
    action: str  # SCALE_OUT, OPTIMIZE_COST, PREDICTIVE, MAINTAIN, ENABLE, DISABLE
    metrics: Dict[str, float]
    backend_state_changed: bool = False  # True if backend was enabled/disabled


class Algorithm1Controller:
    """
    SLO-Aware Routing Controller per thesis Algorithm 1.
    
    Monitors SLO compliance and adjusts traffic weights to maintain
    performance while optimizing cost.
    """
    
    def __init__(self,
                 slo_monitor: Optional[SLOMonitor] = None,
                 config: Optional[Algorithm1Config] = None):
        """
        Initialize Algorithm 1 controller.
        
        Args:
            slo_monitor: SLO monitor instance
            config: Algorithm configuration
        """
        self.slo_monitor = slo_monitor or SLOMonitor()
        self.config = config or Algorithm1Config()
        
        # State tracking - default 100% K8s, 0% Knative (serverless disabled)
        self.last_adjustment_time: Optional[int] = int(time.time())
        self.current_weights = {
            "k3s": self.config.default_k3s_weight,
            "knative": self.config.default_knative_weight
        }
        self.violation_detected_time: Optional[float] = None
        self.serverless_enabled: bool = self.current_weights["knative"] > 0
        self.prewarm_in_progress: bool = False
        
        # Metrics
        self.total_decisions = 0
        self.scale_out_count = 0
        self.optimize_cost_count = 0
        self.predictive_count = 0
        self.maintain_count = 0
        
        logger.info("Algorithm1Controller initialized",
                   weight_step=self.config.weight_step,
                   cooldown=self.config.cooldown_sec)
    
    def make_decision(self,
                     slo_status: Optional[SLOStatus] = None,
                     prediction: Optional[Dict] = None,
                     current_load: Optional[float] = None) -> RoutingDecision:
        """
        Execute Algorithm 1 routing decision.
        
        Args:
            slo_status: Current SLO status (or will query monitor)
            prediction: Optional prediction from Algorithm 2
            current_load: Current request load
            
        Returns:
            RoutingDecision with new weights and reasoning
        """
        self.total_decisions += 1
        current_time = int(time.time())
        
        # Get SLO status if not provided
        if slo_status is None:
            slo_status = self.slo_monitor.check_slo()
        
        # Check cooldown
        can_adjust = self._can_adjust(current_time)
        
        # Track violation detection time for reaction_time metric
        if slo_status.violation_duration_sec > 0 and self.violation_detected_time is None:
            self.violation_detected_time = time.time()
        elif slo_status.violation_duration_sec == 0:
            self.violation_detected_time = None
        
        # Priority 1: Check for sustained SLO violation
        if (slo_status.violation_duration_sec >= self.slo_monitor.config.violation_window_sec
            and can_adjust):
            return self._scale_out(current_time, slo_status)
        
        healthy_threshold = self.slo_monitor.config.p99_threshold_ms * self.config.healthy_margin

        # Priority 2: Early-warning predictive window before sustained violation lock-in
        warning_low = healthy_threshold
        warning_high = self.slo_monitor.config.p99_threshold_ms
        if (prediction and can_adjust and warning_low <= slo_status.p99_latency_ms < warning_high):
            decision = self._apply_prediction(current_time, prediction, current_load)
            if decision:
                return decision

        # Priority 3: Check for healthy state (optimize cost)
        if (slo_status.p99_latency_ms < healthy_threshold and can_adjust
            and current_load is not None and current_load > 0):
            return self._optimize_cost(current_time, slo_status)
        
        # Priority 4: No change
        return self._maintain(slo_status)
    
    def _can_adjust(self, current_time: int) -> bool:
        """Check if cooldown period has passed."""
        if self.last_adjustment_time is None:
            return True
        return current_time - self.last_adjustment_time >= self.config.cooldown_sec
    
    def _scale_out(self, current_time: int, slo_status: SLOStatus) -> RoutingDecision:
        """Scale out to serverless due to SLO violation.
        
        For real Knative integration:
        1. If serverless disabled: ENABLE backend + pre-warm
        2. Then ramp up weight
        """
        self.scale_out_count += 1
        backend_state_changed = False
        
        # Record Prometheus metrics
        slo_violation_total.labels(slo_name="p99_latency").inc()
        routing_decision_total.labels(decision_type="SCALE_OUT").inc()
        
        # Track reaction time (time from violation detection to adjustment)
        if self.violation_detected_time is not None:
            reaction_ms = (time.time() - self.violation_detected_time) * 1000
            reaction_time_ms.observe(reaction_ms)
            self.violation_detected_time = None
        
        # Step 1: Enable serverless backend if disabled
        if not self.serverless_enabled:
            logger.info("Algorithm 1: Enabling serverless backend for SCALE_OUT")
            self.serverless_enabled = True
            backend_state_changed = True
            # Pre-warm Knative (trigger cold start)
            self._prewarm_knative()
        
        # Step 2: Ramp up serverless weight
        new_knative = min(
            self.config.max_knative_weight,
            self.current_weights["knative"] + self.config.weight_step
        )
        new_k3s = 100 - new_knative
        
        logger.info("Algorithm 1: SCALE_OUT",
                   p99=slo_status.p99_latency_ms,
                   violation_sec=slo_status.violation_duration_sec,
                   new_weights={"k3s": new_k3s, "knative": new_knative},
                   serverless_enabled=self.serverless_enabled)
        
        return RoutingDecision(
            weights={"k3s": new_k3s, "knative": new_knative},
            reason=f"SLO violation ({slo_status.p99_latency_ms:.0f}ms > 200ms) for {slo_status.violation_duration_sec}s",
            action="SCALE_OUT",
            metrics={"p99": slo_status.p99_latency_ms, "violation_sec": slo_status.violation_duration_sec},
            backend_state_changed=backend_state_changed
        )
    
    def _optimize_cost(self, current_time: int, slo_status: SLOStatus) -> RoutingDecision:
        """Increase k3s weight for cost optimization.
        
        For real Knative integration:
        - Ramp down serverless weight
        - When weight reaches 0, DISABLE backend (allows scale-to-zero)
        """
        self.optimize_cost_count += 1
        backend_state_changed = False
        
        # Record Prometheus metrics
        routing_decision_total.labels(decision_type="OPTIMIZE_COST").inc()
        
        # Use smaller step for cost optimization
        step = self.config.weight_step // 2
        new_k3s = min(100, self.current_weights["k3s"] + step)  # Can go to 100%
        new_knative = 100 - new_k3s
        
        
        # If knative weight is 0, backend should be disabled after successful apply
        if new_knative == 0 and self.serverless_enabled:
            logger.info("Algorithm 1: Disabling serverless backend (weight=0, allow scale-to-zero)")
            backend_state_changed = True
        
        logger.info("Algorithm 1: OPTIMIZE_COST",
                   p99=slo_status.p99_latency_ms,
                   new_weights={"k3s": new_k3s, "knative": new_knative},
                   serverless_enabled=self.serverless_enabled)
        
        return RoutingDecision(
            weights={"k3s": new_k3s, "knative": new_knative},
            reason=f"Healthy state ({slo_status.p99_latency_ms:.0f}ms < {200 * self.config.healthy_margin:.0f}ms), optimizing cost",
            action="OPTIMIZE_COST",
            metrics={"p99": slo_status.p99_latency_ms},
            backend_state_changed=backend_state_changed
        )
    
    def _apply_prediction(self, current_time: int, 
                         prediction: Dict,
                         current_load: Optional[float]) -> Optional[RoutingDecision]:
        """Apply predictive adjustment based on Algorithm 2 output.
        
        For real Knative integration:
        - Enable serverless backend + pre-warm if predicting load spike
        """
        confidence = prediction.get("confidence", 0)
        predicted_load = prediction.get("predicted_requests", 0)
        
        if confidence < self.config.prediction_confidence_threshold:
            return None
        
        if current_load is None or current_load <= 0:
            return None
        
        load_change = (predicted_load - current_load) / current_load
        
        if load_change > self.config.load_change_threshold:
            # Significant increase predicted - proactively scale out
            backend_state_changed = False

            new_knative = min(
                self.config.max_knative_weight,
                self.current_weights["knative"] + self.config.weight_step
            )
            new_k3s = 100 - new_knative
            proposed_weights = {"k3s": new_k3s, "knative": new_knative}

            # Count predictive decisions only when they produce an effective weight change.
            if proposed_weights == self.current_weights:
                return None

            self.predictive_count += 1
            routing_decision_total.labels(decision_type="PREDICTIVE").inc()
            
            # Enable serverless backend if disabled (preemptive)
            if not self.serverless_enabled:
                logger.info("Algorithm 1: Enabling serverless backend for PREDICTIVE scale out")
                self.serverless_enabled = True
                backend_state_changed = True
                self._prewarm_knative()
            
            
            logger.info("Algorithm 1: PREDICTIVE scale out",
                       predicted_load=predicted_load,
                       current_load=current_load,
                       load_change=load_change,
                       new_weights=proposed_weights,
                       serverless_enabled=self.serverless_enabled)
            
            return RoutingDecision(
                weights=proposed_weights,
                reason=f"Predicted {load_change*100:.0f}% load increase (confidence: {confidence:.0%})",
                action="PREDICTIVE",
                metrics={"predicted_load": predicted_load, "load_change": load_change, "confidence": confidence},
                backend_state_changed=backend_state_changed
            )
        
        return None
    
    def _maintain(self, slo_status: SLOStatus) -> RoutingDecision:
        """Maintain current weights."""
        self.maintain_count += 1
        
        # Record Prometheus metrics
        routing_decision_total.labels(decision_type="MAINTAIN").inc()
        
        return RoutingDecision(
            weights=self.current_weights.copy(),
            reason="Within acceptable range, maintaining current weights",
            action="MAINTAIN",
            metrics={"p99": slo_status.p99_latency_ms}
        )
    
    def commit_applied_decision(self, decision: RoutingDecision, current_time: Optional[int] = None) -> None:
        """Commit decision effects only after daemon successfully applies weights."""
        self.current_weights = decision.weights.copy()
        if decision.action in {"SCALE_OUT", "OPTIMIZE_COST", "PREDICTIVE"}:
            now = current_time if current_time is not None else int(time.time())
            self.last_adjustment_time = now

        if decision.action in {"SCALE_OUT", "PREDICTIVE"} and decision.weights["knative"] > 0:
            self.serverless_enabled = True
        elif decision.action == "OPTIMIZE_COST" and decision.weights["knative"] == 0:
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
            "last_adjustment": self.last_adjustment_time,
            "serverless_enabled": self.serverless_enabled
        }
    
    def _prewarm_knative(self) -> bool:
        """Send synthetic request to trigger Knative cold start.
        
        This ensures the serverless backend is ready before traffic is routed to it.
        """
        if self.prewarm_in_progress:
            logger.debug("Pre-warm already in progress, skipping")
            return True
            
        self.prewarm_in_progress = True
        try:
            logger.info("Pre-warming Knative service",
                       url=self.config.knative_url,
                       host=self.config.knative_host)
            
            start_time = time.time()
            response = requests.get(
                f"{self.config.knative_url}/health",
                headers={"Host": self.config.knative_host},
                timeout=self.config.prewarm_timeout_sec
            )
            
            cold_start_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                logger.info("Knative pre-warm successful",
                           cold_start_ms=cold_start_ms,
                           status=response.status_code)
                return True
            else:
                logger.warning("Knative pre-warm returned non-200",
                              status=response.status_code,
                              cold_start_ms=cold_start_ms)
                return False
                
        except requests.Timeout:
            logger.warning("Knative pre-warm timed out",
                          timeout_sec=self.config.prewarm_timeout_sec)
            return False
        except Exception as e:
            logger.error("Knative pre-warm failed", error=str(e))
            return False
        finally:
            self.prewarm_in_progress = False
    
    def is_serverless_enabled(self) -> bool:
        """Check if serverless backend is currently enabled."""
        return self.serverless_enabled
    
    def force_enable_serverless(self) -> bool:
        """Force enable serverless backend (for testing/manual control)."""
        if not self.serverless_enabled:
            self.serverless_enabled = True
            self._prewarm_knative()
            logger.info("Serverless backend force-enabled")
        return self.serverless_enabled
    
    def force_disable_serverless(self) -> bool:
        """Force disable serverless backend (for testing/manual control)."""
        if self.serverless_enabled:
            self.serverless_enabled = False
            self.current_weights = {"k3s": 100, "knative": 0}
            logger.info("Serverless backend force-disabled")
        return not self.serverless_enabled
