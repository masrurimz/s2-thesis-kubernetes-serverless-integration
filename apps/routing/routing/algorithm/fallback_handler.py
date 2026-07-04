#!/usr/bin/env python3
"""
Sprint 2: Fallback Handler for Intelligent Routing

Provides safe fallback strategies when predictions fail or confidence is low.
"""

import time
from typing import Dict, Optional

import structlog

logger = structlog.get_logger(__name__)


class FallbackHandler:
    """Handles fallback routing strategies when intelligent routing fails."""

    def __init__(
        self,
        fallback_timeout_sec: int = 120,
        recovery_threshold: int = 3,
        emergency_k3s_weight: int = 100,
        emergency_knative_weight: int = 0,
        safe_k3s_weight: int = 80,
        safe_knative_weight: int = 20,
    ):
        """
        Initialize fallback handler.

        Args:
            fallback_timeout_sec: Seconds before attempting recovery
            recovery_threshold: Successful checks needed for recovery
            emergency_k3s_weight: K3s weight in emergency mode
            emergency_knative_weight: Knative weight in emergency mode
            safe_k3s_weight: K3s weight in safe mode
            safe_knative_weight: Knative weight in safe mode
        """
        self.fallback_timeout_sec = fallback_timeout_sec
        self.recovery_threshold = recovery_threshold
        self.emergency_k3s_weight = emergency_k3s_weight
        self.emergency_knative_weight = emergency_knative_weight
        self.safe_k3s_weight = safe_k3s_weight
        self.safe_knative_weight = safe_knative_weight

        # State tracking
        self._fallback_start_time: Optional[float] = None
        self._recovery_count: int = 0
        self._in_fallback: bool = False

        logger.info(
            "FallbackHandler initialized",
            timeout_sec=fallback_timeout_sec,
            recovery_threshold=recovery_threshold,
        )

    def get_fallback_weights(self, current_stats: Dict) -> Dict[str, int]:
        """
        Get appropriate fallback weights based on current system state.

        Args:
            current_stats: Current system statistics

        Returns:
            Dict with 'k3s' and 'knative' weights
        """
        if self._is_emergency_condition(current_stats):
            return self._get_emergency_weights(current_stats)

        if self._is_high_load_condition(current_stats):
            return self._get_high_load_weights(current_stats)

        if self._is_low_load_condition(current_stats):
            return self._get_low_load_weights(current_stats)

        return {"k3s": self.safe_k3s_weight, "knative": self.safe_knative_weight}

    def _is_emergency_condition(self, stats: Dict) -> bool:
        """Check if system is in emergency condition."""
        try:
            p99 = stats.get("p99_latency_ms", 0)
            error_rate = stats.get("error_rate", 0)

            # Emergency if p99 > 1000ms or error rate > 10%
            if p99 > 1000 or error_rate > 0.1:
                logger.warning("Emergency condition detected", p99=p99, error_rate=error_rate)
                return True

            return False
        except Exception:
            return True  # Assume emergency if we can't evaluate

    def _is_high_load_condition(self, stats: Dict) -> bool:
        """Check if system is under high load."""
        try:
            current_rps = stats.get("current_rps", 0)
            cpu_usage = stats.get("cpu_usage", 0)

            # High load if RPS > 500 or CPU > 80%
            if current_rps > 500 or cpu_usage > 0.8:
                return True

            return False
        except Exception:
            return False

    def _is_low_load_condition(self, stats: Dict) -> bool:
        """Check if system is under low load."""
        try:
            current_rps = stats.get("current_rps", 0)

            # Low load if RPS < 10
            if current_rps < 10:
                return True

            return False
        except Exception:
            return False

    def _get_emergency_weights(self, stats: Dict) -> Dict[str, int]:
        """Get weights for emergency conditions."""
        logger.warning("Using emergency weights")
        return {"k3s": self.emergency_k3s_weight, "knative": self.emergency_knative_weight}

    def _get_high_load_weights(self, stats: Dict) -> Dict[str, int]:
        """Get weights for high load conditions."""
        return {
            "k3s": self.safe_k3s_weight,
            "knative": self.safe_knative_weight,
        }

    def _get_low_load_weights(self, stats: Dict) -> Dict[str, int]:
        """Get weights for low load conditions."""
        return {
            "k3s": self.safe_k3s_weight,
            "knative": self.safe_knative_weight,
        }

    def should_enable_intelligent_routing(self) -> bool:
        """
        Check if intelligent routing should be enabled.

        Returns:
            True if intelligent routing is safe to use
        """
        if not self._in_fallback:
            return True

        if self._fallback_start_time is None:
            return False

        elapsed = time.time() - self._fallback_start_time
        if elapsed < self.fallback_timeout_sec:
            return False

        if self._recovery_count >= self.recovery_threshold:
            self.reset_fallback_state()
            return True

        return False

    def reset_fallback_state(self) -> None:
        """Reset fallback state after successful recovery."""
        self._in_fallback = False
        self._fallback_start_time = None
        self._recovery_count = 0
        logger.info("Fallback state reset - intelligent routing restored")

    def get_status(self) -> Dict:
        """Get current fallback handler status."""
        return {
            "in_fallback": self._in_fallback,
            "fallback_start_time": self._fallback_start_time,
            "recovery_count": self._recovery_count,
            "timeout_sec": self.fallback_timeout_sec,
        }

    def get_recovery_weights(self, target_weights: Dict[str, int]) -> Dict[str, int]:
        """
        Get gradual recovery weights.

        Args:
            target_weights: Target weights to recover toward

        Returns:
            Intermediate weights for gradual recovery
        """
        if not self._in_fallback:
            return target_weights

        # Gradually increase confidence in intelligent routing
        self._recovery_count += 1
        recovery_factor = min(1.0, self._recovery_count / self.recovery_threshold)

        # Blend between safe weights and target weights
        k3s_weight = int(self.safe_k3s_weight + (target_weights["k3s"] - self.safe_k3s_weight) * recovery_factor)
        knative_weight = int(
            self.safe_knative_weight + (target_weights["knative"] - self.safe_knative_weight) * recovery_factor
        )

        logger.debug(
            "Recovery weights computed",
            recovery_count=self._recovery_count,
            recovery_factor=recovery_factor,
            weights={"k3s": k3s_weight, "knative": knative_weight},
        )

        return {"k3s": self.safe_k3s_weight, "knative": self.safe_knative_weight}


def main():
    """Test the fallback handler."""
    handler = FallbackHandler()

    # Test with normal stats
    normal_stats = {"p99_latency_ms": 150, "error_rate": 0.01, "current_rps": 100}
    weights = handler.get_fallback_weights(normal_stats)
    print(f"Normal weights: {weights}")

    # Test with emergency stats
    emergency_stats = {"p99_latency_ms": 1500, "error_rate": 0.15}
    weights = handler.get_fallback_weights(emergency_stats)
    print(f"Emergency weights: {weights}")

    # Test status
    status = handler.get_status()
    print(f"Handler status: {status}")


if __name__ == "__main__":
    main()
