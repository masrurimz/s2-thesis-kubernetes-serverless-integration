#!/usr/bin/env python3
"""
Algorithm 1: SLO-Aware Routing Controller

Implements the core routing logic from thesis section 3.4.3.1.
"""

import time
from dataclasses import dataclass
from typing import Optional, Dict

import structlog

from monitoring_v2.slo_monitor import SLOMonitor, SLOConfig, SLOStatus

logger = structlog.get_logger(__name__)


@dataclass
class Algorithm1Config:
    """Configuration for Algorithm 1."""
    weight_step: int = 10  # Weight adjustment step
    cooldown_sec: int = 15  # Minimum time between adjustments
    healthy_margin: float = 0.7  # Multiplier for healthy threshold
    max_knative_weight: int = 50  # Maximum serverless weight
    min_k3s_weight: int = 50  # Minimum k8s weight
    prediction_confidence_threshold: float = 0.7
    load_change_threshold: float = 0.3  # Significant load change


@dataclass
class RoutingDecision:
    """Output of Algorithm 1 routing decision."""
    weights: Dict[str, int]
    reason: str
    action: str  # SCALE_OUT, OPTIMIZE_COST, PREDICTIVE, MAINTAIN
    metrics: Dict[str, float]


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
        
        # State tracking
        self.last_adjustment_time: Optional[int] = None
        self.current_weights = {"k3s": 80, "knative": 20}
        
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
        
        # Step 2: Check for sustained SLO violation
        if (slo_status.violation_duration_sec >= self.slo_monitor.config.violation_window_sec
            and can_adjust):
            return self._scale_out(current_time, slo_status)
        
        # Step 3: Check for healthy state (optimize cost)
        healthy_threshold = self.slo_monitor.config.p99_threshold_ms * self.config.healthy_margin
        if slo_status.p99_latency_ms < healthy_threshold and can_adjust:
            return self._optimize_cost(current_time, slo_status)
        
        # Step 4: Use prediction if available
        if prediction and can_adjust:
            decision = self._apply_prediction(current_time, prediction, current_load)
            if decision:
                return decision
        
        # Step 5: No change
        return self._maintain(slo_status)
    
    def _can_adjust(self, current_time: int) -> bool:
        """Check if cooldown period has passed."""
        if self.last_adjustment_time is None:
            return True
        return current_time - self.last_adjustment_time >= self.config.cooldown_sec
    
    def _scale_out(self, current_time: int, slo_status: SLOStatus) -> RoutingDecision:
        """Scale out to serverless due to SLO violation."""
        self.scale_out_count += 1
        
        new_knative = min(
            self.config.max_knative_weight,
            self.current_weights["knative"] + self.config.weight_step
        )
        new_k3s = 100 - new_knative
        
        self.current_weights = {"k3s": new_k3s, "knative": new_knative}
        self.last_adjustment_time = current_time
        
        logger.info("Algorithm 1: SCALE_OUT",
                   p99=slo_status.p99_latency_ms,
                   violation_sec=slo_status.violation_duration_sec,
                   new_weights=self.current_weights)
        
        return RoutingDecision(
            weights=self.current_weights.copy(),
            reason=f"SLO violation ({slo_status.p99_latency_ms:.0f}ms > 200ms) for {slo_status.violation_duration_sec}s",
            action="SCALE_OUT",
            metrics={"p99": slo_status.p99_latency_ms, "violation_sec": slo_status.violation_duration_sec}
        )
    
    def _optimize_cost(self, current_time: int, slo_status: SLOStatus) -> RoutingDecision:
        """Increase k3s weight for cost optimization."""
        self.optimize_cost_count += 1
        
        # Use smaller step for cost optimization
        step = self.config.weight_step // 2
        new_k3s = min(95, self.current_weights["k3s"] + step)
        new_knative = 100 - new_k3s
        
        self.current_weights = {"k3s": new_k3s, "knative": new_knative}
        self.last_adjustment_time = current_time
        
        logger.info("Algorithm 1: OPTIMIZE_COST",
                   p99=slo_status.p99_latency_ms,
                   new_weights=self.current_weights)
        
        return RoutingDecision(
            weights=self.current_weights.copy(),
            reason=f"Healthy state ({slo_status.p99_latency_ms:.0f}ms < {200 * self.config.healthy_margin:.0f}ms), optimizing cost",
            action="OPTIMIZE_COST",
            metrics={"p99": slo_status.p99_latency_ms}
        )
    
    def _apply_prediction(self, current_time: int, 
                         prediction: Dict,
                         current_load: Optional[float]) -> Optional[RoutingDecision]:
        """Apply predictive adjustment based on Algorithm 2 output."""
        confidence = prediction.get("confidence", 0)
        predicted_load = prediction.get("predicted_requests", 0)
        
        if confidence < self.config.prediction_confidence_threshold:
            return None
        
        if current_load is None or current_load <= 0:
            return None
        
        load_change = (predicted_load - current_load) / current_load
        
        if load_change > self.config.load_change_threshold:
            # Significant increase predicted - proactively scale out
            self.predictive_count += 1
            
            new_knative = min(
                self.config.max_knative_weight,
                self.current_weights["knative"] + self.config.weight_step
            )
            new_k3s = 100 - new_knative
            
            self.current_weights = {"k3s": new_k3s, "knative": new_knative}
            self.last_adjustment_time = current_time
            
            logger.info("Algorithm 1: PREDICTIVE scale out",
                       predicted_load=predicted_load,
                       current_load=current_load,
                       load_change=load_change,
                       new_weights=self.current_weights)
            
            return RoutingDecision(
                weights=self.current_weights.copy(),
                reason=f"Predicted {load_change*100:.0f}% load increase (confidence: {confidence:.0%})",
                action="PREDICTIVE",
                metrics={"predicted_load": predicted_load, "load_change": load_change, "confidence": confidence}
            )
        
        return None
    
    def _maintain(self, slo_status: SLOStatus) -> RoutingDecision:
        """Maintain current weights."""
        self.maintain_count += 1
        
        return RoutingDecision(
            weights=self.current_weights.copy(),
            reason="Within acceptable range, maintaining current weights",
            action="MAINTAIN",
            metrics={"p99": slo_status.p99_latency_ms}
        )
    
    def get_statistics(self) -> Dict:
        """Get decision statistics."""
        return {
            "total_decisions": self.total_decisions,
            "scale_out_count": self.scale_out_count,
            "optimize_cost_count": self.optimize_cost_count,
            "predictive_count": self.predictive_count,
            "maintain_count": self.maintain_count,
            "current_weights": self.current_weights,
            "last_adjustment": self.last_adjustment_time
        }
