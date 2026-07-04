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
    haproxy_stats_url: str = "http://localhost:18404/stats;csv"
    scrape_interval_sec: int = 15
    use_haproxy_fallback: bool = True  # Use HAProxy stats if Prometheus fails


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
        self._last_haproxy_total_requests: Optional[int] = None
        self._last_haproxy_total_rtime_ms: Optional[float] = None

        logger.info(
            "SLOMonitor initialized",
            threshold_ms=self.config.p99_threshold_ms,
            violation_window=self.config.violation_window_sec,
        )

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
            recommendation=recommendation,
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
        """Query Prometheus first, then HAProxy fallback if enabled."""
        p99 = self._get_p99_from_prometheus()
        if p99 > 0:
            return p99

        if self.config.use_haproxy_fallback:
            p99 = self._get_latency_from_haproxy()
            if p99 > 0:
                return p99

        return self._last_p99

    def _get_p99_from_prometheus(self) -> float:
        """Query Prometheus for p99 latency."""
        try:
            query = "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[30s])) by (le)) * 1000"
            response = requests.get(f"{self.config.prometheus_url}/api/v1/query", params={"query": query}, timeout=5)
            response.raise_for_status()

            result = response.json()
            if result.get("status") == "success" and result.get("data", {}).get("result"):
                value = float(result["data"]["result"][0]["value"][1])
                return value if value > 0 else 0.0

            return 0.0

        except Exception as e:
            logger.debug("Prometheus query failed", error=str(e))
            return 0.0

    def _get_latency_from_haproxy(self) -> float:
        """Estimate recent latency from HAProxy cumulative counters per interval."""
        try:
            response = requests.get(self.config.haproxy_stats_url, timeout=5)
            response.raise_for_status()

            lines = response.text.strip().split("\n")
            for line in lines:
                fields = line.split(",")
                if len(fields) <= 92:
                    continue
                if fields[0] != "servers" or fields[1] != "BACKEND":
                    continue
                if not fields[7].isdigit() or not fields[60].isdigit():
                    continue

                total_requests = int(fields[7])
                avg_rtime_ms = float(fields[60])
                max_rtime_ms = float(fields[92]) if fields[92].isdigit() else avg_rtime_ms
                total_rtime_ms = total_requests * avg_rtime_ms

                if self._last_haproxy_total_requests is None or self._last_haproxy_total_rtime_ms is None:
                    self._last_haproxy_total_requests = total_requests
                    self._last_haproxy_total_rtime_ms = total_rtime_ms
                    logger.debug("HAProxy fallback primed", total_requests=total_requests)
                    return 0.0

                delta_requests = total_requests - self._last_haproxy_total_requests
                delta_rtime_ms = total_rtime_ms - self._last_haproxy_total_rtime_ms
                self._last_haproxy_total_requests = total_requests
                self._last_haproxy_total_rtime_ms = total_rtime_ms

                if delta_requests <= 0 or delta_rtime_ms <= 0:
                    return 0.0

                interval_avg_ms = delta_rtime_ms / delta_requests
                estimated_p99 = min(interval_avg_ms * 2.0, max_rtime_ms)
                logger.debug(
                    "HAProxy fallback latency",
                    delta_requests=delta_requests,
                    interval_avg_ms=round(interval_avg_ms, 2),
                    max_rtime_ms=max_rtime_ms,
                    p99_est=round(estimated_p99, 2),
                )
                return float(max(0.0, estimated_p99))

            return 0.0

        except Exception as e:
            logger.warning("HAProxy stats query failed", error=str(e))
            return 0.0

    def get_statistics(self) -> Dict:
        """Get monitor statistics."""
        return {
            "total_checks": self._total_checks,
            "violations": self._violations,
            "last_p99": self._last_p99,
            "violation_start_time": self.violation_start_time,
        }

    def reset(self) -> None:
        """Reset violation tracking state."""
        self.violation_start_time = None
        self._last_p99 = 0.0
        self._total_checks = 0
        self._violations = 0
        self._last_haproxy_total_requests = None
        self._last_haproxy_total_rtime_ms = None


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
