#!/usr/bin/env python3
"""
Sprint 2: Prediction Server API

Real-time FastAPI server for traffic prediction and intelligent routing.
Provides REST endpoints for prediction requests and model management.
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .data_collector import DataCollector
from .linear_model import TrafficPredictor

# Configure structured logging
logger = structlog.get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sprint 2 Prediction Server",
    description="Real-time traffic prediction for intelligent hybrid routing",
    version="2.0.0"
)

# Global components
collector: Optional[DataCollector] = None
predictor: Optional[TrafficPredictor] = None

# Server configuration
PREDICTION_INTERVAL = 30  # seconds
MODEL_RETRAIN_INTERVAL = 3600  # 1 hour


class PredictionRequest(BaseModel):
    """Request model for traffic prediction."""
    timestamp: Optional[int] = Field(default=None, description="Unix timestamp (auto-generated if None)")
    current_requests: Optional[int] = Field(default=None, description="Current request count")
    include_confidence: bool = Field(default=True, description="Include confidence metrics")


class PredictionResponse(BaseModel):
    """Response model for traffic prediction."""
    predicted_requests: float = Field(description="Predicted request count for next period")
    confidence: float = Field(description="Prediction confidence (0-1)")
    timestamp: int = Field(description="Prediction timestamp")
    model_performance: Dict[str, float] = Field(description="Model accuracy metrics")
    recommendation: Dict[str, int] = Field(description="Recommended traffic weights")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(description="Service status")
    model_trained: bool = Field(description="Whether model is trained")
    data_points: int = Field(description="Available historical data points")
    last_prediction: Optional[int] = Field(description="Last prediction timestamp")
    uptime_seconds: float = Field(description="Server uptime")


# Server state
server_start_time = time.time()
last_prediction_time: Optional[int] = None


@app.on_event("startup")
async def startup_event():
    """Initialize server components on startup."""
    global collector, predictor
    
    try:
        # Initialize data collector
        collector = DataCollector()
        logger.info("Data collector initialized")
        
        # Initialize predictor
        predictor = TrafficPredictor()
        
        # Try to load existing model
        if predictor.load_model():
            logger.info("Existing model loaded")
        else:
            # Train initial model with available data
            df = collector.get_historical_data(hours=1)
            if len(df) >= 10:
                metrics = predictor.train(df)
                logger.info("Initial model trained", **metrics)
            else:
                logger.warning("Insufficient data for initial training")
        
        # Start background tasks
        asyncio.create_task(continuous_data_collection())
        asyncio.create_task(periodic_model_retraining())
        
        logger.info("Prediction server started successfully")
        
    except Exception as e:
        logger.error("Server startup failed", error=str(e))
        raise


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Get historical data count
        df = collector.get_historical_data(hours=24)
        data_points = len(df)
        
        return HealthResponse(
            status="healthy",
            model_trained=predictor.is_trained,
            data_points=data_points,
            last_prediction=last_prediction_time,
            uptime_seconds=time.time() - server_start_time
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.post("/predict", response_model=PredictionResponse)
async def predict_traffic(request: PredictionRequest):
    """
    Predict traffic for the next period.
    
    Args:
        request: Prediction request parameters
        
    Returns:
        Traffic prediction with confidence and recommendations
    """
    global last_prediction_time
    
    try:
        if not predictor.is_trained:
            raise HTTPException(
                status_code=503,
                detail="Model not trained. Please wait for initial training."
            )
        
        # Get current stats
        current_stats = collector.collect_current_stats()
        if not current_stats:
            raise HTTPException(
                status_code=503,
                detail="Unable to collect current traffic statistics"
            )
        
        # Override with request data if provided
        if request.timestamp:
            current_stats['timestamp'] = request.timestamp
        if request.current_requests:
            current_stats['total_requests'] = request.current_requests
            
        # Make prediction
        prediction = predictor.predict(current_stats)
        
        # Calculate recommended weights based on prediction
        recommendation = calculate_weight_recommendation(
            prediction['predicted_requests'],
            current_stats['total_requests']
        )
        
        # Update last prediction time
        last_prediction_time = int(time.time())
        
        response = PredictionResponse(
            predicted_requests=prediction['predicted_requests'],
            confidence=prediction['confidence'],
            timestamp=prediction['prediction_timestamp'],
            model_performance={
                'rmse': prediction['model_rmse'],
                'r2_score': prediction['model_r2']
            },
            recommendation=recommendation
        )
        
        logger.debug("Prediction served", 
                    predicted=prediction['predicted_requests'],
                    confidence=prediction['confidence'])
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Prediction failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/retrain")
async def retrain_model(background_tasks: BackgroundTasks):
    """Trigger model retraining."""
    try:
        background_tasks.add_task(retrain_model_task)
        return {"message": "Model retraining scheduled"}
    except Exception as e:
        logger.error("Retrain request failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    """Get model performance metrics."""
    try:
        if not predictor.is_trained:
            return {"error": "Model not trained"}
            
        return {
            "model_trained": predictor.is_trained,
            "rmse": predictor.rmse,
            "r2_score": predictor.r2_score,
            "training_samples": predictor.training_samples,
            "server_uptime": time.time() - server_start_time,
            "last_prediction": last_prediction_time
        }
    except Exception as e:
        logger.error("Metrics retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/export")
async def export_data(format: str = "csv", hours: int = 24):
    """Export historical data."""
    try:
        if format not in ["csv", "json"]:
            raise HTTPException(status_code=400, detail="Format must be 'csv' or 'json'")
            
        output_path = f"data/exports/export_{int(time.time())}.{format}"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        if collector.export_data(output_path, format):
            return {"message": f"Data exported to {output_path}"}
        else:
            raise HTTPException(status_code=500, detail="Export failed")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Data export failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


def calculate_weight_recommendation(predicted_requests: float, 
                                  current_requests: int) -> Dict[str, int]:
    """
    Calculate recommended traffic weights based on prediction.
    
    Args:
        predicted_requests: Predicted request count
        current_requests: Current request count
        
    Returns:
        Dictionary with recommended k3s and knative weights
    """
    # Simple heuristic: adjust weights based on predicted load change
    if current_requests > 0:
        load_change = (predicted_requests - current_requests) / current_requests
    else:
        load_change = 0.0 if predicted_requests == 0 else 1.0
    
    # Default weights
    k3s_weight = 80
    knative_weight = 20
    
    # Adjust weights based on load prediction
    if load_change > 0.2:  # Significant increase predicted
        # Increase serverless for better scaling
        knative_weight = min(40, knative_weight + 15)
        k3s_weight = 100 - knative_weight
    elif load_change < -0.2:  # Significant decrease predicted
        # Increase k3s for cost efficiency
        k3s_weight = min(90, k3s_weight + 10)
        knative_weight = 100 - k3s_weight
        
    return {
        "k3s_weight": k3s_weight,
        "knative_weight": knative_weight
    }


async def continuous_data_collection():
    """Background task for continuous data collection."""
    logger.info("Starting continuous data collection")
    
    while True:
        try:
            stats = collector.collect_current_stats()
            if stats:
                collector.store_stats(stats)
                
            await asyncio.sleep(PREDICTION_INTERVAL)
            
        except Exception as e:
            logger.error("Data collection cycle failed", error=str(e))
            await asyncio.sleep(PREDICTION_INTERVAL)


async def periodic_model_retraining():
    """Background task for periodic model retraining."""
    logger.info("Starting periodic model retraining")
    
    while True:
        try:
            await asyncio.sleep(MODEL_RETRAIN_INTERVAL)
            await retrain_model_task()
            
        except Exception as e:
            logger.error("Periodic retraining failed", error=str(e))


async def retrain_model_task():
    """Background task to retrain the model."""
    try:
        logger.info("Starting model retraining")
        
        # Get recent historical data
        df = collector.get_historical_data(hours=24)
        
        # Check if retraining is needed
        if predictor.retrain_if_needed(df):
            logger.info("Model retrained successfully")
        else:
            logger.debug("Model retraining not needed")
            
    except Exception as e:
        logger.error("Model retraining failed", error=str(e))


def main():
    """Run the prediction server."""
    uvicorn.run(
        "prediction_engine.prediction_server:app",
        host="0.0.0.0",
        port=8003,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()