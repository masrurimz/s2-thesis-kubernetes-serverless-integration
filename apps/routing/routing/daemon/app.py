"""FastAPI application factory for the routing daemon.

Creates the HTTP API that exposes daemon status, health checks,
scenario switching, and Prometheus metrics.
"""

from typing import TYPE_CHECKING

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from shared.models.routing import StatusResponse, SetScenarioRequest, HealthResponse

if TYPE_CHECKING:
    from routing.daemon.service import RoutingDaemon


def create_app(daemon: "RoutingDaemon") -> FastAPI:
    """Create FastAPI application with routes for the routing daemon.

    Args:
        daemon: The RoutingDaemon instance to expose via API.

    Returns:
        Configured FastAPI application.
    """
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
