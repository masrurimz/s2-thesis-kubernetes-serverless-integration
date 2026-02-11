#!/usr/bin/env python3
"""
GRU Prediction HTTP Server.

FastAPI server exposing trained GRU model for workload prediction.
Port: 8090, Response target: <50ms.
"""

import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .model_loader import GRUModelLoader

logger = structlog.get_logger(__name__)

model_loader: Optional[GRUModelLoader] = None
server_start_time: float = 0.0


class PredictRequest(BaseModel):
    """Request model for prediction endpoint."""
    history: List[float] = Field(
        ...,
        description="Recent request counts (last N values)",
        min_length=1,
    )
    horizon: int = Field(
        default=5,
        ge=1,
        le=30,
        description="Number of steps ahead to predict",
    )


class PredictResponse(BaseModel):
    """Response model for prediction endpoint."""
    predicted_requests: int = Field(description="Primary prediction value")
    confidence: float = Field(ge=0, le=1, description="Prediction confidence (0-1)")
    horizon_values: List[int] = Field(description="Predictions for each horizon step")
    latency_ms: float = Field(description="Prediction latency in milliseconds")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str
    model_loaded: bool
    model_type: Optional[str]
    uptime_seconds: float
    sequence_length: Optional[int]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - load model on startup."""
    global model_loader, server_start_time
    
    server_start_time = time.time()
    
    model_paths = [
        Path("data/models/gru_model.pt"),
        Path(__file__).parent.parent / "data/models/gru_model.pt",
        Path("/app/models/gru_model.pt"),
        Path("data/models/gru_model.joblib"),
        Path(__file__).parent.parent / "data/models/gru_model.joblib",
        Path("/app/models/gru_model.joblib"),
    ]
    
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


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns server status and model information.
    """
    is_loaded = model_loader is not None and model_loader.is_loaded
    
    return HealthResponse(
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
        "prediction.prediction_server:app",
        host="0.0.0.0",
        port=8090,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
