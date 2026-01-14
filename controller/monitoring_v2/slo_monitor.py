#!/usr/bin/env python3
"""
SLO Monitor for Algorithm 1.

Monitors p99 latency and tracks SLO violations for the routing controller.
"""

import time
from dataclasses import dataclass
from typing import Optional, Dict

import requests
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class SLOConfig:
    """SLO configuration parameters."""
    p99_threshold_ms: float = 200.0  # SLO target: 200ms p99 latency
    violation_window_sec: int = 30  # Window for sustained violation detection
    healthy_margin: float = 0.7  # Multiplier for healthy threshold
    prometheus_url: str = "http://localhost:9090"
    scrape_interval_sec: int = 15


@dataclass
class SLOStatus:
    """Current SLO status."""
    p99_latency_ms: float
    is_violating: bool
    violation_duration_sec: int
    timestamp: int
    recommendation: str = "MAINTAIN"  # SCALE_OUT, OPTIMIZE_COST, MAINTAIN


class SLOMonitor:
    """
    Monitors SLO compliance for Algorithm 1.
    
    Tracks p99 latency from Prometheus and detects sustained violations.
    """
    
    def __init__(self, config: Optional[SLOConfig] = None):
        """Initialize SLO monitor."""
        self.config = config or SLOConfig()
        self.violation_start_time: Optional[int] = None
        self._last_p99: float = 0.0
        self._total_checks: int = 0
        self._violations: int = 0
        
        logger.info("SLOMonitor initialized",
                   threshold_ms=self.config.p99_threshold_ms,
                   violation_window=self.config.violation_window_sec)
    
    def check_slo(self) -> SLOStatus:
        """
        Check current SLO status.
        
        Returns:
            SLOStatus with current p99 latency and violation info
        """
        current_time = int(time.time())
        p99 = self._get_p99_latency()
        self._total_checks += 1
        
        is_violating = p99 > self.config.p99_threshold_ms
        
        if is_violating:
            self._violations += 1
            if self.violation_start_time is None:
                self.violation_start_time = current_time
            violation_duration = current_time - self.violation_start_time
        else:
            self.violation_start_time = None
            violation_duration = 0
        
        self._last_p99 = p99
        
        recommendation = self._get_recommendation(p99, violation_duration)
        
        return SLOStatus(
            p99_latency_ms=p99,
            is_violating=is_violating,
            violation_duration_sec=violation_duration,
            timestamp=current_time,
            recommendation=recommendation
        )
    
    def _get_recommendation(self, p99: float, violation_duration: int) -> str:
        """Determine recommendation based on current state."""
        healthy_threshold = self.config.p99_threshold_ms * self.config.healthy_margin
        
        if violation_duration >= self.config.violation_window_sec:
            return "SCALE_OUT"
        elif p99 < healthy_threshold:
            return "OPTIMIZE_COST"
        else:
            return "MAINTAIN"
    
    def _get_p99_latency(self) -> float:
        """Query Prometheus for p99 latency."""
        try:
            query = 'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[1m])) by (le)) * 1000'
            response = requests.get(
                f"{self.config.prometheus_url}/api/v1/query",
                params={"query": query},
                timeout=5
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("status") == "success" and result.get("data", {}).get("result"):
                value = float(result["data"]["result"][0]["value"][1])
                return value if value > 0 else self._last_p99
            
            return self._last_p99
            
        except Exception as e:
            logger.warning("Failed to query p99 latency", error=str(e))
            return self._last_p99
    
    def get_statistics(self) -> Dict:
        """Get monitor statistics."""
        return {
            "total_checks": self._total_checks,
            "violations": self._violations,
            "last_p99": self._last_p99,
            "violation_start_time": self.violation_start_time
        }
    
    def reset(self) -> None:
        """Reset violation tracking state."""
        self.violation_start_time = None
        self._last_p99 = 0.0
        self._total_checks = 0
        self._violations = 0


class MockSLOMonitor(SLOMonitor):
    """Mock SLO monitor for testing."""
    
    def __init__(self, config: Optional[SLOConfig] = None):
        super().__init__(config)
        self._mock_p99: float = 150.0
    
    def set_mock_metrics(self, p99: float) -> None:
        """Set mock p99 latency value."""
        self._mock_p99 = p99
    
    def _get_p99_latency(self) -> float:
        """Return mock p99 value."""
        return self._mock_p99
