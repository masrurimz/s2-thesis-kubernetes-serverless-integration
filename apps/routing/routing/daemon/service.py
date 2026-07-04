#!/usr/bin/env python3
"""
Routing Daemon for Experiment Orchestration.

Main daemon that runs Algorithm1Controller with scenario-specific configs.

Scenarios:
- s1-k8s-only: HAProxy weights 100/0, no algorithm (static)
- s2-serverless-only: HAProxy weights 0/100, no algorithm (static)
- s3-hybrid-reactive: Algorithm1 without GRU predictions
- s4-hybrid-predictive: Algorithm1 + GRU predictions
"""

import asyncio
import os
import threading
import time
from collections import deque
from typing import Dict, Optional

import structlog
import uvicorn

from routing.monitoring.slo_monitor import SLOMonitor, SLOConfig
from routing.algorithm.algorithm1_v1 import Algorithm1Controller, Algorithm1Config
from routing.algorithm.algorithm1_v2 import Algorithm1ControllerV2, Algorithm1ConfigV2
from routing.algorithm.algorithm1_v3 import Algorithm1ControllerV3, Algorithm1ConfigV3
from routing.algorithm.weight_adjuster import HAProxyWeightAdjuster
from routing.clients.gru_client import GRUClient
from routing.scaling.cluster_controller import ClusterController, ScalingConfig
from infra.cluster.k8s import K8sScaler
from shared.scenarios import Scenario, SCENARIO_CONFIGS
from routing.daemon.metrics import (
    daemon_decision_total,
    daemon_current_weight,
    daemon_prediction_used,
    daemon_prediction_failed,
    daemon_decision_latency,
    k8s_scaling_events_total,
    k8s_desired_replicas,
    k8s_available_replicas,
)
from routing.daemon.app import create_app

logger = structlog.get_logger(__name__)


class RoutingDaemon:
    """
    Main routing daemon for experiment orchestration.

    Runs Algorithm1Controller with scenario-specific configs.
    """

    def __init__(
        self,
        scenario: str,
        decision_interval: int = 15,
        prometheus_url: str = "http://localhost:9090",
        haproxy_socket_host: str = "localhost",
        haproxy_socket_port: int = 9999,
        haproxy_stats_url: str = "http://localhost:8404/stats;csv",
        gru_server_url: str = "http://localhost:8090",
        api_port: int = 9104,
    ):
        """
        Initialize the routing daemon.

        Args:
            scenario: Scenario name (s1-k8s-only, s2-serverless-only, etc.)
            decision_interval: Seconds between decisions
            prometheus_url: Prometheus server URL
            haproxy_socket_host: HAProxy admin socket host
            haproxy_socket_port: HAProxy admin socket port
            haproxy_stats_url: HAProxy stats URL
            gru_server_url: GRU prediction server URL
            api_port: HTTP API port
        """
        try:
            self.scenario = Scenario(scenario)
        except ValueError:
            raise ValueError(f"Invalid scenario: {scenario}. Valid: {[s.value for s in Scenario]}")

        self.scenario_config = SCENARIO_CONFIGS[self.scenario]
        self.decision_interval = decision_interval
        self.api_port = api_port

        self.slo_monitor = SLOMonitor(
            config=SLOConfig(
                prometheus_url=prometheus_url,
                haproxy_stats_url=haproxy_stats_url,
            )
        )

        controller_version = os.environ.get("CONTROLLER_VERSION", "v3")

        if self.scenario == Scenario.S4_HYBRID_PREDICTIVE and controller_version == "v3":
            self.algorithm_controller = Algorithm1ControllerV3(
                slo_monitor=self.slo_monitor,
                config=Algorithm1ConfigV3(cooldown_sec=decision_interval),
            )
            logger.info("Using V3 controller (Capacity-Driven) for S4", scenario=scenario, version=controller_version)
        elif self.scenario == Scenario.S4_HYBRID_PREDICTIVE and controller_version == "v2":
            self.algorithm_controller = Algorithm1ControllerV2(
                slo_monitor=self.slo_monitor,
                config=Algorithm1ConfigV2(
                    cooldown_sec=decision_interval,
                    default_serverless_weight=self.scenario_config.knative_weight,
                ),
            )
            logger.info("Using V2 controller (PID + Feedforward) for S4", scenario=scenario, version=controller_version)
        else:
            self.algorithm_controller = Algorithm1Controller(
                slo_monitor=self.slo_monitor,
                config=Algorithm1Config(
                    cooldown_sec=decision_interval,
                    default_k3s_weight=self.scenario_config.k3s_weight,
                    default_knative_weight=self.scenario_config.knative_weight,
                    load_change_threshold=0.15 if self.scenario_config.use_predictions else 0.3,
                ),
            )

        self.weight_adjuster = HAProxyWeightAdjuster(
            tcp_socket_host=haproxy_socket_host,
            tcp_socket_port=haproxy_socket_port,
            stats_url=haproxy_stats_url,
        )

        self.gru_client = GRUClient(base_url=gru_server_url)

        self.current_weights = {
            "k3s": self.scenario_config.k3s_weight,
            "knative": self.scenario_config.knative_weight,
        }

        self.algorithm_controller.current_weights = self.current_weights.copy()
        self.algorithm_controller.serverless_enabled = self.current_weights["knative"] > 0
        self._running = False
        self._shutdown_event = threading.Event()
        self._start_time = time.time()
        self._last_decision_time: Optional[float] = None
        self._decision_count = 0

        self._load_history: deque = deque(maxlen=60)
        self._last_total_requests: Optional[int] = None
        self._last_total_requests_ts: Optional[float] = None

        # K8s scaler: always instantiate for replica gauge emission;
        # Algorithm 2 scaling logic only runs when use_algorithm=True.
        self.k8s_scaler = K8sScaler()
        if self.scenario_config.use_algorithm:
            controller_ver = os.environ.get("CONTROLLER_VERSION", "v3")
            if controller_ver == "v3" and self.scenario == Scenario.S4_HYBRID_PREDICTIVE:
                self.cluster_controller = ClusterController(
                    config=ScalingConfig(
                        alpha=0.03,  # 300m CPU: ~35 RPS/pod → 1/35 ≈ 0.029
                        beta=0.0,
                        buffer=1.2,
                        min_replicas=3,
                        max_replicas=10,
                        scale_down_threshold=0.5,
                    )
                )
            else:
                self.cluster_controller = ClusterController(config=ScalingConfig())
        else:
            self.cluster_controller = None
        self._last_scale_up_ts: Optional[float] = None
        self._last_scale_down_ts: Optional[float] = None

        logger.info(
            "RoutingDaemon initialized",
            scenario=self.scenario.value,
            description=self.scenario_config.description,
            use_algorithm=self.scenario_config.use_algorithm,
            use_predictions=self.scenario_config.use_predictions,
            decision_interval=decision_interval,
        )

    def _apply_initial_weights(self) -> bool:
        """Apply initial weights for the scenario."""
        success = self.weight_adjuster.set_weights_with_retry(
            self.current_weights["k3s"],
            self.current_weights["knative"],
        )

        if success:
            daemon_current_weight.labels(backend="k3s").set(self.current_weights["k3s"])
            daemon_current_weight.labels(backend="knative").set(self.current_weights["knative"])
            logger.info(
                "Initial weights applied",
                k3s=self.current_weights["k3s"],
                knative=self.current_weights["knative"],
            )
        else:
            logger.warning("Failed to apply initial weights")

        return success

    def _get_current_load(self) -> Optional[float]:
        """Get current request load from history."""
        if self._load_history:
            return float(self._load_history[-1])
        return None

    def _update_load_history(self) -> None:
        """Update load history from Prometheus (simplified)."""
        # Primary source: Prometheus request rate query.
        try:
            import requests

            query = "sum(rate(http_requests_total[1m]))"
            response = requests.get(
                f"{self.slo_monitor.config.prometheus_url}/api/v1/query",
                params={"query": query},
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success" and data.get("data", {}).get("result"):
                    value = float(data["data"]["result"][0]["value"][1])
                    self._load_history.append(value)
                    return
        except Exception as e:
            logger.debug("Failed to update load history", error=str(e))

        # Fallback source: HAProxy cumulative request counter converted to req/s.
        # This keeps predictive mode functional when Prometheus is unreachable.
        try:
            response = self.weight_adjuster._send_command("show stat")
            if not response:
                return

            total_requests: Optional[int] = None
            for line in response.strip().split("\n"):
                if not line or line.startswith("#"):
                    continue

                fields = line.split(",")
                if len(fields) < 8:
                    continue

                if fields[0] == self.weight_adjuster.backend_name and fields[1] == "BACKEND":
                    if fields[7].isdigit():
                        total_requests = int(fields[7])
                        break

            if total_requests is None:
                return

            now = time.time()
            if self._last_total_requests is not None and self._last_total_requests_ts is not None:
                delta_reqs = total_requests - self._last_total_requests
                delta_t = max(0.001, now - self._last_total_requests_ts)
                if delta_reqs >= 0:
                    self._load_history.append(delta_reqs / delta_t)

            self._last_total_requests = total_requests
            self._last_total_requests_ts = now
        except Exception as e:
            logger.debug("Failed HAProxy fallback load history update", error=str(e))

    def _update_k8s_replica_gauges(self) -> None:
        """Emit Prometheus replica gauges for all scenarios (including static S1/S2)."""
        try:
            dep_status = self.k8s_scaler.get_deployment_status()
            if dep_status is not None:
                k8s_desired_replicas.set(dep_status.spec_replicas or 0)
                k8s_available_replicas.set(dep_status.available_replicas or 0)
        except Exception:
            pass

    def _execute_decision_loop(self) -> None:
        """Execute single decision loop iteration."""
        start_time = time.perf_counter()

        self._update_load_history()
        self._update_k8s_replica_gauges()

        if not self.scenario_config.use_algorithm:
            self._last_decision_time = time.time()
            self._decision_count += 1
            daemon_decision_total.labels(
                scenario=self.scenario.value,
                action="STATIC",
            ).inc()

            logger.debug(
                "Static scenario - no decision needed",
                scenario=self.scenario.value,
                weights=self.current_weights,
            )
            return

        slo_status = self.slo_monitor.check_slo()

        prediction = None
        current_load = self._get_current_load()

        if self.scenario_config.use_predictions and self.gru_client.check_availability():
            history = list(self._load_history)
            if len(history) >= 5:
                pred_result = self.gru_client.predict(history, horizon=5)
                if pred_result.success:
                    prediction = {
                        "predicted_requests": pred_result.predicted_requests,
                        "confidence": pred_result.confidence,
                    }
                    daemon_prediction_used.inc()
                    logger.debug(
                        "Using GRU prediction",
                        predicted=pred_result.predicted_requests,
                        confidence=pred_result.confidence,
                    )
                else:
                    daemon_prediction_failed.inc()
                    logger.debug("GRU prediction failed", error=pred_result.error)
        # Get available replicas for V3 capacity-driven routing
        available_replicas = 1
        if self.k8s_scaler is not None:
            dep_status = self.k8s_scaler.get_deployment_status()
            if dep_status is not None:
                available_replicas = max(1, dep_status.available_replicas)

        # V3 controller takes available_replicas; V1/V2 ignore it via default
        if isinstance(self.algorithm_controller, Algorithm1ControllerV3):
            decision = self.algorithm_controller.make_decision(
                slo_status=slo_status,
                prediction=prediction,
                current_load=current_load,
                available_replicas=available_replicas,
            )
        else:
            decision = self.algorithm_controller.make_decision(
                slo_status=slo_status,
                prediction=prediction,
                current_load=current_load,
            )

        self._decision_count += 1
        self._last_decision_time = time.time()

        daemon_decision_total.labels(
            scenario=self.scenario.value,
            action=decision.action,
        ).inc()

        # Readiness gate: block RECOVERY only if fewer than 2 K8s pods ready.
        # Previous version blocked when available != desired — too strict for V3.
        should_block = False
        if decision.action in ("OPTIMIZE_COST", "RECOVERY") and self.k8s_scaler is not None:
            dep_status = self.k8s_scaler.get_deployment_status()
            if dep_status is not None:
                should_block = dep_status.available_replicas < 2
            else:
                should_block = not self.k8s_scaler.is_ready()
        if should_block:
            logger.warning("Blocking traffic return: K8s not ready", original_action=decision.action)
            from routing.algorithm.algorithm1_v1 import RoutingDecision as _RD

            decision = _RD(
                weights=self.current_weights.copy(),
                reason="Blocked: K8s not ready for traffic return",
                action="MAINTAIN",
                metrics={"p99": slo_status.p99_latency_ms},
            )

        if decision.weights != self.current_weights:
            success = self.weight_adjuster.set_weights_with_retry(
                decision.weights["k3s"],
                decision.weights["knative"],
            )

            if success:
                self.current_weights = decision.weights.copy()
                self.algorithm_controller.commit_applied_decision(
                    decision,
                    current_time=int(time.time()),
                )
                daemon_current_weight.labels(backend="k3s").set(self.current_weights["k3s"])
                daemon_current_weight.labels(backend="knative").set(self.current_weights["knative"])

                logger.info(
                    "Weights updated",
                    action=decision.action,
                    reason=decision.reason,
                    weights=self.current_weights,
                )
            else:
                logger.error("Failed to apply weight update", weights=decision.weights)

        # Algorithm 2: K8s replica scaling (S3/S4 only)
        self._execute_algorithm2(slo_status, prediction, current_load)

        latency_ms = (time.perf_counter() - start_time) * 1000
        daemon_decision_latency.observe(latency_ms)

        logger.debug(
            "Decision loop completed",
            action=decision.action,
            p99=slo_status.p99_latency_ms,
            latency_ms=round(latency_ms, 2),
        )

    def _execute_algorithm2(
        self,
        slo_status,
        prediction: Optional[Dict],
        current_load: Optional[float],
    ) -> None:
        """Run Algorithm 2 K8s replica scaling (S3/S4 only)."""
        if self.k8s_scaler is None or self.cluster_controller is None:
            return

        dep_status = self.k8s_scaler.get_deployment_status()
        if dep_status is None:
            return

        k8s_desired_replicas.set(dep_status.spec_replicas)
        k8s_available_replicas.set(dep_status.available_replicas)

        # Determine scaling signal:
        # V3: use max(observed, predicted) — ensures we never under-provision
        # S3: use observed load only
        n_samples = max(1, min(len(self._load_history), -(-30 // self.decision_interval)))
        recent = list(self._load_history)[-n_samples:]
        x_obs = float(sum(recent) / len(recent)) if recent else 0.0
        scaling_signal = x_obs

        if self.scenario_config.use_predictions and prediction is not None and prediction.get("confidence", 0) >= 0.5:
            x_pred = float(prediction["predicted_requests"])
            if isinstance(self.algorithm_controller, Algorithm1ControllerV3):
                # V3: use max(observed, predicted) — never under-provision
                scaling_signal = max(x_obs, x_pred)
            else:
                scaling_signal = x_pred

        scaling_decision = self.cluster_controller.evaluate(scaling_signal, dep_status.spec_replicas)

        now = time.time()
        healthy_threshold = self.slo_monitor.config.p99_threshold_ms * self.algorithm_controller.config.healthy_margin

        if scaling_decision.action == "SCALE_UP":
            scale_up_cooldown = 15
            if self._last_scale_up_ts is None or (now - self._last_scale_up_ts) >= scale_up_cooldown:
                success = self.k8s_scaler.scale(scaling_decision.target_replicas)
                k8s_scaling_events_total.labels(direction="up", result="success" if success else "fail").inc()
                if success:
                    self._last_scale_up_ts = now

        elif scaling_decision.action == "SCALE_DOWN":
            # V3: min 3 replicas, 300s cooldown (don't scale down frequently)
            is_v3 = isinstance(self.algorithm_controller, Algorithm1ControllerV3)
            min_replicas = 3 if is_v3 else 1
            scale_down_cooldown = 300 if is_v3 else 60
            target = max(min_replicas, scaling_decision.target_replicas)
            if (
                (self._last_scale_down_ts is None or (now - self._last_scale_down_ts) >= scale_down_cooldown)
                and slo_status.p99_latency_ms < healthy_threshold
                and target < dep_status.spec_replicas
            ):
                success = self.k8s_scaler.scale(target)
                k8s_scaling_events_total.labels(direction="down", result="success" if success else "fail").inc()
                if success:
                    self._last_scale_down_ts = now

    def run(self) -> None:
        """Main loop - runs until shutdown."""
        self._running = True
        self._start_time = time.time()

        logger.info(
            "Starting routing daemon",
            scenario=self.scenario.value,
            interval=self.decision_interval,
        )

        self._apply_initial_weights()

        # HPA guard: warn if HPA exists for target deployment (S3/S4 only)
        if self.k8s_scaler is not None and self.k8s_scaler.check_hpa_conflict():
            logger.error("HPA detected — Algorithm 2 scaling may conflict with HPA")

        api_thread = threading.Thread(target=self._run_api_server, daemon=True)
        api_thread.start()

        while not self._shutdown_event.is_set():
            try:
                self._execute_decision_loop()
            except Exception as e:
                logger.error("Decision loop error", error=str(e))

            self._shutdown_event.wait(timeout=self.decision_interval)

        self._running = False
        logger.info("Routing daemon stopped")

    def stop(self) -> None:
        """Graceful shutdown."""
        logger.info("Stopping routing daemon...")
        self._shutdown_event.set()

    def get_status(self) -> Dict:
        """Return current status, weights, metrics."""
        stats = self.algorithm_controller.get_statistics()

        return {
            "scenario": self.scenario.value,
            "scenario_description": self.scenario_config.description,
            "weights": self.current_weights.copy(),
            "decision_count": self._decision_count,
            "scale_out_count": stats["scale_out_count"],
            "optimize_cost_count": stats["optimize_cost_count"],
            "predictive_count": stats["predictive_count"],
            "maintain_count": stats["maintain_count"],
            "uptime_seconds": round(time.time() - self._start_time, 2),
            "gru_available": self.gru_client.check_availability(),
            "last_decision_time": self._last_decision_time,
        }

    def set_scenario(self, scenario: str) -> None:
        """Change scenario (for testing)."""
        try:
            new_scenario = Scenario(scenario)
        except ValueError:
            raise ValueError(f"Invalid scenario: {scenario}")

        self.scenario = new_scenario
        self.scenario_config = SCENARIO_CONFIGS[new_scenario]

        self.current_weights = {
            "k3s": self.scenario_config.k3s_weight,
            "knative": self.scenario_config.knative_weight,
        }

        self._apply_initial_weights()

        if self.scenario_config.use_algorithm:
            self.algorithm_controller.current_weights = self.current_weights.copy()

        logger.info(
            "Scenario changed",
            scenario=self.scenario.value,
            weights=self.current_weights,
        )

    def _run_api_server(self) -> None:
        """Run FastAPI server in background thread."""
        app = create_app(self)

        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=self.api_port,
            log_level="warning",
        )
        server = uvicorn.Server(config)

        asyncio.run(server.serve())
