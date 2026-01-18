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

import argparse
import asyncio
import signal
import threading
import time
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from pydantic import BaseModel

from monitoring_v2.slo_monitor import SLOMonitor, SLOConfig
from intelligent_router.algorithm1_controller import Algorithm1Controller, Algorithm1Config
from intelligent_router.weight_adjuster import HAProxyWeightAdjuster
from daemon.gru_client import GRUClient

from config import settings

logger = structlog.get_logger(__name__)


class Scenario(str, Enum):
    """Experiment scenarios."""
    S1_K8S_ONLY = "s1-k8s-only"
    S2_SERVERLESS_ONLY = "s2-serverless-only"
    S3_HYBRID_REACTIVE = "s3-hybrid-reactive"
    S4_HYBRID_PREDICTIVE = "s4-hybrid-predictive"


@dataclass
class ScenarioConfig:
    """Configuration for each scenario."""
    name: str
    k3s_weight: int
    knative_weight: int
    use_algorithm: bool
    use_predictions: bool
    description: str


SCENARIO_CONFIGS: Dict[Scenario, ScenarioConfig] = {
    Scenario.S1_K8S_ONLY: ScenarioConfig(
        name="S1: K8s Only",
        k3s_weight=100,
        knative_weight=0,
        use_algorithm=False,
        use_predictions=False,
        description="Static routing to K8s cluster only",
    ),
    Scenario.S2_SERVERLESS_ONLY: ScenarioConfig(
        name="S2: Serverless Only",
        k3s_weight=0,
        knative_weight=100,
        use_algorithm=False,
        use_predictions=False,
        description="Static routing to serverless only",
    ),
    Scenario.S3_HYBRID_REACTIVE: ScenarioConfig(
        name="S3: Hybrid Reactive",
        k3s_weight=80,
        knative_weight=20,
        use_algorithm=True,
        use_predictions=False,
        description="Algorithm 1 reactive routing without predictions",
    ),
    Scenario.S4_HYBRID_PREDICTIVE: ScenarioConfig(
        name="S4: Hybrid Predictive",
        k3s_weight=80,
        knative_weight=20,
        use_algorithm=True,
        use_predictions=True,
        description="Algorithm 1 with GRU predictions (Algorithm 2)",
    ),
}


daemon_decision_total = Counter(
    "routing_daemon_decision_total",
    "Total routing decisions by daemon",
    ["scenario", "action"],
)

daemon_current_weight = Gauge(
    "routing_daemon_current_weight",
    "Current routing weight",
    ["backend"],
)

daemon_prediction_used = Counter(
    "routing_daemon_prediction_used",
    "Predictions from GRU used in decisions",
)

daemon_prediction_failed = Counter(
    "routing_daemon_prediction_failed",
    "Failed prediction requests",
)

daemon_decision_latency = Histogram(
    "routing_daemon_decision_latency_ms",
    "Decision loop latency in milliseconds",
    buckets=[5, 10, 25, 50, 100, 250, 500, 1000],
)


class StatusResponse(BaseModel):
    """Status response model."""
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
    last_decision_time: Optional[float]


class SetScenarioRequest(BaseModel):
    """Request to change scenario."""
    scenario: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    scenario: str
    haproxy_connected: bool
    gru_available: bool


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
            config=SLOConfig(prometheus_url=prometheus_url)
        )
        
        self.algorithm_controller = Algorithm1Controller(
            slo_monitor=self.slo_monitor,
            config=Algorithm1Config(cooldown_sec=decision_interval),
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
        
        self._running = False
        self._shutdown_event = threading.Event()
        self._start_time = time.time()
        self._last_decision_time: Optional[float] = None
        self._decision_count = 0
        
        self._load_history: deque = deque(maxlen=60)
        
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
        try:
            import requests
            query = 'sum(rate(http_requests_total[1m]))'
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
        except Exception as e:
            logger.debug("Failed to update load history", error=str(e))
    
    def _execute_decision_loop(self) -> None:
        """Execute single decision loop iteration."""
        start_time = time.perf_counter()
        
        self._update_load_history()
        
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
        
        if decision.weights != self.current_weights:
            success = self.weight_adjuster.set_weights_with_retry(
                decision.weights["k3s"],
                decision.weights["knative"],
            )
            
            if success:
                self.current_weights = decision.weights.copy()
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
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        daemon_decision_latency.observe(latency_ms)
        
        logger.debug(
            "Decision loop completed",
            action=decision.action,
            p99=slo_status.p99_latency_ms,
            latency_ms=round(latency_ms, 2),
        )
    
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
        app = self._create_app()
        
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=self.api_port,
            log_level="warning",
        )
        server = uvicorn.Server(config)
        
        asyncio.run(server.serve())
    
    def _create_app(self) -> FastAPI:
        """Create FastAPI application."""
        daemon = self
        
        app = FastAPI(
            title="Routing Daemon API",
            description="HTTP API for routing daemon control and monitoring",
            version="1.0.0",
        )
        
        @app.get("/status", response_model=StatusResponse)
        async def get_status():
            """Get current daemon status."""
            status = daemon.get_status()
            return StatusResponse(**status)
        
        @app.post("/set_scenario")
        async def set_scenario(request: SetScenarioRequest):
            """Change scenario (for testing)."""
            try:
                daemon.set_scenario(request.scenario)
                return {"status": "ok", "scenario": daemon.scenario.value}
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint."""
            return HealthResponse(
                status="healthy" if daemon._running else "starting",
                scenario=daemon.scenario.value,
                haproxy_connected=daemon.weight_adjuster.socket_available,
                gru_available=daemon.gru_client.check_availability() if daemon.scenario_config.use_predictions else False,
            )
        
        @app.get("/metrics")
        async def metrics():
            """Prometheus metrics endpoint."""
            return Response(
                content=generate_latest(),
                media_type=CONTENT_TYPE_LATEST,
            )
        
        return app


def main():
    """Entry point for routing daemon."""
    parser = argparse.ArgumentParser(description="Routing Daemon for experiment orchestration")
    parser.add_argument(
        "--scenario",
        type=str,
        default=settings.DEFAULT_SCENARIO,
        help=f"Scenario (default: {settings.DEFAULT_SCENARIO})",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=settings.DAEMON_DECISION_INTERVAL,
        help=f"Decision interval in seconds (default: {settings.DAEMON_DECISION_INTERVAL})",
    )
    parser.add_argument(
        "--prometheus-url",
        type=str,
        default=settings.PROMETHEUS_URL,
        help=f"Prometheus server URL (default: {settings.PROMETHEUS_URL})",
    )
    parser.add_argument(
        "--haproxy-host",
        type=str,
        default=settings.HAPROXY_HOST,
        help=f"HAProxy admin socket host (default: {settings.HAPROXY_HOST})",
    )
    parser.add_argument(
        "--haproxy-port",
        type=int,
        default=settings.HAPROXY_SOCKET_PORT,
        help=f"HAProxy admin socket port (default: {settings.HAPROXY_SOCKET_PORT})",
    )
    parser.add_argument(
        "--haproxy-stats",
        type=str,
        default=settings.HAPROXY_STATS_URL,
        help=f"HAProxy stats URL (default: {settings.HAPROXY_STATS_URL})",
    )
    parser.add_argument(
        "--gru-url",
        type=str,
        default=settings.GRU_SERVICE_URL,
        help=f"GRU prediction server URL (default: {settings.GRU_SERVICE_URL})",
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=settings.DAEMON_API_PORT,
        help=f"HTTP API port (default: {settings.DAEMON_API_PORT})",
    )
    
    args = parser.parse_args()
    
    daemon = RoutingDaemon(
        scenario=args.scenario,
        decision_interval=args.interval,
        prometheus_url=args.prometheus_url,
        haproxy_socket_host=args.haproxy_host,
        haproxy_socket_port=args.haproxy_port,
        haproxy_stats_url=args.haproxy_stats,
        gru_server_url=args.gru_url,
        api_port=args.api_port,
    )
    
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        daemon.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    daemon.run()


if __name__ == "__main__":
    main()
