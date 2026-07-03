#!/usr/bin/env python3
"""
Sprint 2: Intelligent Routing Controller

This module implements the main routing controller that uses prediction data
to automatically adjust HAProxy traffic weights for optimal hybrid routing.
"""

import asyncio
import time
from typing import Dict, Optional

import requests
import structlog

from .weight_adjuster import HAProxyWeightAdjuster
from .decision_logger import DecisionLogger
from .fallback_handler import FallbackHandler

logger = structlog.get_logger(__name__)


class IntelligentRoutingController:
    """Main controller for intelligent traffic routing."""

    def __init__(
        self,
        prediction_api_url: str = "http://localhost:8003",
        haproxy_stats_url: str = "http://localhost:8404/stats;csv",
        haproxy_socket_path: str = "/tmp/haproxy.sock",
        routing_interval: int = 30,
        enable_intelligent_routing: bool = True,
    ):
        """
        Initialize intelligent routing controller.

        Args:
            prediction_api_url: Prediction server API endpoint
            haproxy_stats_url: HAProxy stats CSV endpoint
            haproxy_socket_path: HAProxy admin socket path
            routing_interval: Routing decision interval in seconds
            enable_intelligent_routing: Enable intelligent routing (fallback to manual if False)
        """
        self.prediction_api_url = prediction_api_url
        self.haproxy_stats_url = haproxy_stats_url
        self.routing_interval = routing_interval
        self.enable_intelligent_routing = enable_intelligent_routing

        # Initialize components
        self.weight_adjuster = HAProxyWeightAdjuster(haproxy_socket_path)
        self.decision_logger = DecisionLogger()
        self.fallback_handler = FallbackHandler()

        # Controller state
        self.is_running = False
        self.last_decision_time = None
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3

        # Current weights tracking
        self.current_weights = {"k3s": 80, "knative": 20}
        self.target_weights = {"k3s": 80, "knative": 20}

        logger.info(
            "IntelligentRoutingController initialized",
            prediction_api=prediction_api_url,
            intelligent_routing=enable_intelligent_routing,
        )

    async def start(self) -> None:
        """Start the intelligent routing controller."""
        if self.is_running:
            logger.warning("Controller already running")
            return

        self.is_running = True
        logger.info("Starting intelligent routing controller")

        try:
            # Initial health check
            await self._health_check()

            # Start main control loop
            await self._control_loop()

        except KeyboardInterrupt:
            logger.info("Controller stopped by user")
        except Exception as e:
            logger.error("Controller failed", error=str(e))
        finally:
            self.is_running = False

    async def stop(self) -> None:
        """Stop the intelligent routing controller."""
        self.is_running = False
        logger.info("Intelligent routing controller stopped")

    async def _control_loop(self) -> None:
        """Main control loop for intelligent routing decisions."""
        while self.is_running:
            try:
                start_time = time.time()

                # Make routing decision
                await self._make_routing_decision()

                # Calculate sleep time to maintain consistent interval
                elapsed = time.time() - start_time
                sleep_time = max(0, self.routing_interval - elapsed)

                logger.debug("Control loop cycle complete", elapsed=elapsed, sleep_time=sleep_time)

                await asyncio.sleep(sleep_time)

            except Exception as e:
                logger.error("Control loop cycle failed", error=str(e))
                self.consecutive_failures += 1

                if self.consecutive_failures >= self.max_consecutive_failures:
                    logger.error("Too many consecutive failures, entering fallback mode")
                    await self._enter_fallback_mode()

                await asyncio.sleep(self.routing_interval)

    async def _make_routing_decision(self) -> None:
        """Make an intelligent routing decision based on predictions."""
        try:
            decision_start = time.time()

            # Get current system state
            current_stats = await self._get_current_stats()
            if not current_stats:
                raise Exception("Failed to get current system stats")

            # Get prediction if intelligent routing is enabled
            prediction = None
            if self.enable_intelligent_routing:
                prediction = await self._get_prediction()

            # Calculate target weights
            if prediction and self.enable_intelligent_routing:
                target_weights = self._calculate_intelligent_weights(current_stats, prediction)
                decision_type = "intelligent"
            else:
                target_weights = self.fallback_handler.get_fallback_weights(current_stats)
                decision_type = "fallback"

            # Apply weight changes if needed
            if hasattr(self, "weight_adjuster"):
                weights_changed = await self._apply_weight_changes(target_weights)
            else:
                weights_changed = False

            # Log decision
            decision = {
                "timestamp": int(time.time()),
                "decision_type": decision_type,
                "current_stats": current_stats,
                "prediction": prediction,
                "previous_weights": self.current_weights.copy(),
                "target_weights": target_weights,
                "weights_changed": weights_changed,
                "decision_latency": time.time() - decision_start,
            }

            if hasattr(self, "decision_logger"):
                self.decision_logger.log_decision(decision)

            # Update tracking
            self.last_decision_time = int(time.time())
            self.consecutive_failures = 0  # Reset on success

            logger.debug(
                "Routing decision complete", type=decision_type, weights=target_weights, changed=weights_changed
            )

        except Exception as e:
            logger.error("Routing decision failed", error=str(e))
            raise

    async def _get_current_stats(self) -> Optional[Dict]:
        """Get current traffic statistics from HAProxy."""
        try:
            response = requests.get(self.haproxy_stats_url, timeout=5)
            response.raise_for_status()

            # Parse HAProxy CSV stats
            lines = response.text.strip().split("\n")
            headers = lines[0].split(",")

            stats = {
                "timestamp": int(time.time()),
                "total_requests": 0,
                "k3s_requests": 0,
                "knative_requests": 0,
                "avg_response_time": 25.0,
                "error_rate": 0.0,
            }

            for line in lines[1:]:
                if not line.strip():
                    continue

                fields = line.split(",")
                if len(fields) < len(headers):
                    continue

                row = dict(zip(headers, fields))

                # Extract backend server stats
                if row.get("svname") == "k3s-backend":
                    stats["k3s_requests"] = int(row.get("stot", 0) or 0)
                elif row.get("svname") == "knative-backend":
                    stats["knative_requests"] = int(row.get("stot", 0) or 0)
                elif row.get("pxname") == "hybrid-backend" and row.get("svname") == "BACKEND":
                    stats["total_requests"] = int(row.get("stot", 0) or 0)

            return stats

        except Exception as e:
            logger.error("Failed to get current stats", error=str(e))
            return None

    async def _get_prediction(self) -> Optional[Dict]:
        """Get traffic prediction from prediction server."""
        try:
            response = requests.post(f"{self.prediction_api_url}/predict", json={}, timeout=5)
            response.raise_for_status()

            prediction = response.json()
            logger.debug(
                "Prediction received",
                predicted=prediction.get("predicted_requests"),
                confidence=prediction.get("confidence"),
            )

            return prediction

        except requests.exceptions.RequestException as e:
            logger.warning("Prediction API unavailable", error=str(e))
            return None
        except Exception as e:
            logger.error("Failed to get prediction", error=str(e))
            return None

    def _calculate_intelligent_weights(self, current_stats: Dict, prediction: Dict) -> Dict[str, int]:
        """
        Calculate intelligent traffic weights based on prediction.

        Args:
            current_stats: Current system statistics
            prediction: Traffic prediction data

        Returns:
            Dictionary with target k3s and knative weights
        """
        try:
            predicted_requests = prediction.get("predicted_requests", 1000)
            confidence = prediction.get("confidence", 0.5)
            current_requests = current_stats.get("total_requests", 1000)

            # Calculate load change
            if current_requests > 0:
                load_change = (predicted_requests - current_requests) / current_requests
            else:
                load_change = 0

            # Base weights (Sprint 1 optimal)
            k3s_weight = 80
            knative_weight = 20

            # Adjust weights based on prediction and confidence
            if confidence > 0.7:  # High confidence predictions
                if load_change > 0.3:  # Significant increase predicted
                    # Increase serverless for better scaling
                    adjustment = min(20, int(load_change * 50))
                    knative_weight = min(50, knative_weight + adjustment)
                    k3s_weight = 100 - knative_weight

                elif load_change < -0.3:  # Significant decrease predicted
                    # Increase k3s for cost efficiency
                    adjustment = min(15, int(abs(load_change) * 40))
                    k3s_weight = min(95, k3s_weight + adjustment)
                    knative_weight = 100 - k3s_weight

            # Apply conservative adjustments for medium confidence
            elif confidence > 0.5:
                if load_change > 0.5:  # Very significant increase
                    knative_weight = min(35, knative_weight + 10)
                    k3s_weight = 100 - knative_weight
                elif load_change < -0.5:  # Very significant decrease
                    k3s_weight = min(90, k3s_weight + 5)
                    knative_weight = 100 - k3s_weight

            # Use recommendation from prediction if available
            if "recommendation" in prediction:
                rec_k3s = prediction["recommendation"].get("k3s_weight", k3s_weight)
                _ = prediction["recommendation"].get("knative_weight", knative_weight)  # noqa: F841 — available for future use

                # Blend with our calculation based on confidence
                blend_factor = confidence
                k3s_weight = int(k3s_weight * (1 - blend_factor) + rec_k3s * blend_factor)
                knative_weight = 100 - k3s_weight

            logger.debug(
                "Intelligent weights calculated",
                load_change=load_change,
                confidence=confidence,
                k3s_weight=k3s_weight,
                knative_weight=knative_weight,
            )

            return {"k3s": k3s_weight, "knative": knative_weight}

        except Exception as e:
            logger.error("Weight calculation failed", error=str(e))
            # Return safe defaults
            return {"k3s": 80, "knative": 20}

    async def _apply_weight_changes(self, target_weights: Dict[str, int]) -> bool:
        """
        Apply weight changes to HAProxy if needed.

        Args:
            target_weights: Target weights for k3s and knative

        Returns:
            True if weights were changed, False otherwise
        """
        try:
            # Check if weights need to change (avoid unnecessary adjustments)
            if (
                abs(target_weights["k3s"] - self.current_weights["k3s"]) < 5
                and abs(target_weights["knative"] - self.current_weights["knative"]) < 5
            ):
                logger.debug("Weight change too small, skipping")
                return False

            # Apply weight changes
            success = self.weight_adjuster.set_weights_with_retry(target_weights["k3s"], target_weights["knative"])

            if success:
                self.current_weights = target_weights.copy()
                logger.info("Weights updated successfully", weights=target_weights)
                return True
            else:
                logger.error("Failed to update weights")
                return False

        except Exception as e:
            logger.error("Weight application failed", error=str(e))
            return False

    async def _health_check(self) -> None:
        """Perform initial health check of all components."""
        try:
            # Check prediction API
            response = requests.get(f"{self.prediction_api_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("Prediction API healthy")
            else:
                logger.warning("Prediction API not healthy", status=response.status_code)

        except Exception as e:
            logger.warning("Prediction API health check failed", error=str(e))

        # Check HAProxy stats
        stats = await self._get_current_stats()
        if stats:
            logger.info("HAProxy stats accessible")
        else:
            logger.warning("HAProxy stats not accessible")

        # Check weight adjustment capability
        if hasattr(self, "weight_adjuster"):
            test_success = self.weight_adjuster.test_connection()
            if test_success:
                logger.info("HAProxy weight adjustment working")
            else:
                logger.warning("HAProxy weight adjustment not working")

    async def _enter_fallback_mode(self) -> None:
        """Enter fallback mode due to consecutive failures."""
        logger.warning("Entering fallback mode")

        # Disable intelligent routing temporarily
        original_setting = self.enable_intelligent_routing
        self.enable_intelligent_routing = False

        try:
            # Apply safe fallback weights
            fallback_weights = {"k3s": 80, "knative": 20}
            await self._apply_weight_changes(fallback_weights)

            # Wait for system to stabilize
            await asyncio.sleep(60)

            # Reset failure counter and re-enable if possible
            self.consecutive_failures = 0
            self.enable_intelligent_routing = original_setting

            logger.info("Exited fallback mode")

        except Exception as e:
            logger.error("Fallback mode failed", error=str(e))

    def get_status(self) -> Dict:
        """Get current controller status."""
        return {
            "is_running": self.is_running,
            "intelligent_routing_enabled": self.enable_intelligent_routing,
            "current_weights": self.current_weights,
            "last_decision_time": self.last_decision_time,
            "consecutive_failures": self.consecutive_failures,
        }


async def main_async():
    """Async main function for the intelligent router."""
    controller = IntelligentRoutingController()

    try:
        await controller.start()
    except KeyboardInterrupt:
        await controller.stop()


def main():
    """Entry point for the intelligent router script."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
