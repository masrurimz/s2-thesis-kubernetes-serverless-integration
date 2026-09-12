#!/usr/bin/env python3
"""
GRU Prediction HTTP Server.

FastAPI server exposing trained GRU model for workload prediction.
Port: 8090, Response target: <50ms.
"""

import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from shared.models.prediction import PredictRequest, PredictResponse, PredictionHealthResponse

from .model_loader import GRUModelLoader

logger = structlog.get_logger(__name__)

model_loader: Optional[GRUModelLoader] = None
server_start_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - load model on startup."""
    global model_loader, server_start_time

    server_start_time = time.time()

    model_paths = []
    # If a specific model path was set on app state (via create_app), try it first.
    explicit_path = getattr(app.state, "model_path", None)
    if explicit_path:
        model_paths.append(Path(explicit_path))
    model_paths.extend(
        [
            Path("data/models/gru_model.pt"),
            Path(__file__).parent.parent / "data/models/gru_model.pt",
            Path("/app/models/gru_model.pt"),
            Path("data/models/gru_model.joblib"),
            Path(__file__).parent.parent / "data/models/gru_model.joblib",
            Path("/app/models/gru_model.joblib"),
        ]
    )

    model_loader = None
    for path in model_paths:
        if path.exists():
            try:
                model_loader = GRUModelLoader(path)
                if model_loader.is_loaded:
                    logger.info("Model loaded at startup", path=str(path))
                    break
            except Exception as e:
                logger.warning("Failed to load model from path", path=str(path), error=str(e))

    if model_loader is None or not model_loader.is_loaded:
        model_loader = GRUModelLoader()
        if model_loader.is_loaded:
            logger.info("Model loaded from default path")
        else:
            logger.warning("No pre-trained model found - server will return errors until model is provided")

    logger.info("GRU Prediction Server started", port=8090)

    yield

    logger.info("GRU Prediction Server shutting down")


app = FastAPI(
    title="GRU Prediction Server",
    description="HTTP API for workload prediction using trained GRU models",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=PredictionHealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns server status and model information.
    """
    is_loaded = model_loader is not None and model_loader.is_loaded

    return PredictionHealthResponse(
        status="healthy" if is_loaded else "degraded",
        model_loaded=is_loaded,
        model_type=model_loader.model_type if model_loader else None,
        uptime_seconds=round(time.time() - server_start_time, 2),
        sequence_length=model_loader.config.sequence_length if model_loader and model_loader.config else None,
    )


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """
    Predict future request counts.

    Takes recent request history and returns prediction for specified horizon.
    Target response time: <50ms.
    """
    start_time = time.perf_counter()

    if model_loader is None or not model_loader.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please ensure a trained model is available.",
        )

    try:
        result = model_loader.predict(request.history, request.horizon)

        latency_ms = (time.perf_counter() - start_time) * 1000

        logger.debug(
            "Prediction completed",
            predicted=result["predicted_requests"],
            confidence=result["confidence"],
            horizon=request.horizon,
            latency_ms=round(latency_ms, 2),
        )

        return PredictResponse(
            predicted_requests=int(result["predicted_requests"]),
            confidence=result["confidence"],
            horizon_values=result["horizon_values"],
            latency_ms=round(latency_ms, 2),
            point_forecasts=result.get("point_forecasts"),
            upper_forecasts=result.get("upper_forecasts"),
        )

    except Exception as e:
        logger.error("Prediction failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.get("/model/status")
async def model_status():
    """Get detailed model status information."""
    if model_loader is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Model loader not initialized"},
        )

    return model_loader.get_status()


@app.post("/model/reload")
async def reload_model(model_path: Optional[str] = None):
    """
    Reload the model from disk.

    Args:
        model_path: Optional path to model file. Uses default paths if not provided.
    """
    global model_loader

    try:
        if model_path:
            path = Path(model_path)
            if not path.exists():
                raise HTTPException(status_code=404, detail=f"Model file not found: {model_path}")
            model_loader = GRUModelLoader(path)
        else:
            model_loader = GRUModelLoader()

        if model_loader.is_loaded:
            logger.info("Model reloaded", path=str(model_loader.model_path))
            return {"status": "reloaded", "path": str(model_loader.model_path)}
        else:
            raise HTTPException(status_code=503, detail="Failed to reload model")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Model reload failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Reload failed: {str(e)}")


def main():
    """Run the prediction server."""
    uvicorn.run(
        "prediction.server:app",
        host="0.0.0.0",
        port=8090,
        reload=False,
        log_level="info",
    )


# ---------------------------------------------------------------------------
# Typer CLI entry point (thesis-prediction-server)
# ---------------------------------------------------------------------------

import typer

cli_app = typer.Typer()


@cli_app.command()
def serve(host: str = "0.0.0.0", port: int = 8090, model_path: str | None = None):
    """Start the GRU prediction server."""
    uvicorn.run(create_app(model_path), host=host, port=port)


def create_app(model_path: str | None = None) -> FastAPI:
    """Create and return the FastAPI app, optionally pre-loading a model.

    If model_path is given, it is stored on app.state so that the lifespan
    handler loads it first (before falling back to default paths).
    """
    if model_path:
        app.state.model_path = model_path
    return app


if __name__ == "__main__":
    main()
