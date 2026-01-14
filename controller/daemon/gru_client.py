#!/usr/bin/env python3
"""
GRU Prediction Client.

HTTP client for querying GRU prediction server at localhost:8090.
"""

import time
from dataclasses import dataclass
from typing import List, Optional

import requests
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class PredictionResult:
    """Result from GRU prediction service."""
    predicted_requests: int
    confidence: float
    horizon_values: List[int]
    latency_ms: float
    success: bool = True
    error: Optional[str] = None


class GRUClient:
    """HTTP client for GRU prediction server."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8090",
        timeout: float = 5.0,
        retry_count: int = 2,
    ):
        """
        Initialize GRU client.
        
        Args:
            base_url: GRU prediction server URL
            timeout: Request timeout in seconds
            retry_count: Number of retries on failure
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retry_count = retry_count
        self._is_available = False
        self._last_check_time: Optional[float] = None
        self._check_interval = 30.0  # Re-check availability every 30s
        
        logger.info("GRUClient initialized", base_url=self.base_url)
    
    def is_healthy(self) -> bool:
        """Check if GRU server is healthy."""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=self.timeout,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "healthy" and data.get("model_loaded", False)
            return False
        except Exception as e:
            logger.debug("GRU health check failed", error=str(e))
            return False
    
    def check_availability(self) -> bool:
        """
        Check server availability with caching.
        
        Returns:
            True if server is available and model loaded
        """
        current_time = time.time()
        
        if (self._last_check_time is not None and 
            current_time - self._last_check_time < self._check_interval):
            return self._is_available
        
        self._is_available = self.is_healthy()
        self._last_check_time = current_time
        
        return self._is_available
    
    def predict(
        self,
        history: List[float],
        horizon: int = 5,
    ) -> PredictionResult:
        """
        Get prediction from GRU server.
        
        Args:
            history: Recent request counts
            horizon: Number of steps ahead to predict
            
        Returns:
            PredictionResult with prediction data or error
        """
        if not history:
            return PredictionResult(
                predicted_requests=0,
                confidence=0.0,
                horizon_values=[],
                latency_ms=0.0,
                success=False,
                error="Empty history provided",
            )
        
        start_time = time.perf_counter()
        last_error: Optional[str] = None
        
        for attempt in range(self.retry_count + 1):
            try:
                response = requests.post(
                    f"{self.base_url}/predict",
                    json={"history": history, "horizon": horizon},
                    timeout=self.timeout,
                )
                
                latency_ms = (time.perf_counter() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    
                    logger.debug(
                        "GRU prediction received",
                        predicted=data.get("predicted_requests"),
                        confidence=data.get("confidence"),
                        latency_ms=round(latency_ms, 2),
                    )
                    
                    return PredictionResult(
                        predicted_requests=data.get("predicted_requests", 0),
                        confidence=data.get("confidence", 0.0),
                        horizon_values=data.get("horizon_values", []),
                        latency_ms=latency_ms,
                        success=True,
                    )
                else:
                    last_error = f"HTTP {response.status_code}: {response.text[:100]}"
                    
            except requests.exceptions.Timeout:
                last_error = "Request timeout"
            except requests.exceptions.ConnectionError:
                last_error = "Connection refused"
            except Exception as e:
                last_error = str(e)
            
            if attempt < self.retry_count:
                time.sleep(0.1 * (attempt + 1))
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        logger.warning(
            "GRU prediction failed",
            error=last_error,
            attempts=self.retry_count + 1,
        )
        
        return PredictionResult(
            predicted_requests=0,
            confidence=0.0,
            horizon_values=[],
            latency_ms=latency_ms,
            success=False,
            error=last_error,
        )
    
    def get_model_status(self) -> dict:
        """Get detailed model status from server."""
        try:
            response = requests.get(
                f"{self.base_url}/model/status",
                timeout=self.timeout,
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
