"""Prometheus HTTP API client for experiment metrics collection."""

from typing import Optional

import requests
import structlog

logger = structlog.get_logger(__name__)


class PrometheusClient:
    """Client for querying Prometheus HTTP API."""

    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        self.prometheus_url = prometheus_url.rstrip("/")
        self._session = requests.Session()

    def query_instant(self, expr: str, timestamp: Optional[int] = None) -> Optional[float]:
        """Query Prometheus instant query API.

        Args:
            expr: PromQL expression
            timestamp: Unix timestamp for evaluation (optional)

        Returns:
            Float value or None on error/no data
        """
        params: dict[str, str | int] = {"query": expr}
        if timestamp is not None:
            params["time"] = timestamp

        try:
            response = self._session.get(
                f"{self.prometheus_url}/api/v1/query",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "success":
                logger.warning("prometheus_query_failed", expr=expr, response=data)
                return None

            results = data.get("data", {}).get("result", [])
            if not results:
                return None

            value = results[0].get("value", [])
            if len(value) < 2:
                return None

            return float(value[1])

        except requests.RequestException as e:
            logger.error("prometheus_connection_error", expr=expr, error=str(e))
            return None
        except (ValueError, KeyError, IndexError) as e:
            logger.error("prometheus_parse_error", expr=expr, error=str(e))
            return None

    def query_range(self, expr: str, start: int, end: int, step: int = 15) -> list[tuple[int, float]]:
        """Query Prometheus range query API.

        Args:
            expr: PromQL expression
            start: Start timestamp (Unix seconds)
            end: End timestamp (Unix seconds)
            step: Query resolution step in seconds

        Returns:
            List of (timestamp, value) tuples
        """
        params = {
            "query": expr,
            "start": start,
            "end": end,
            "step": step,
        }

        try:
            response = self._session.get(
                f"{self.prometheus_url}/api/v1/query_range",
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "success":
                logger.warning("prometheus_range_query_failed", expr=expr, response=data)
                return []

            results = data.get("data", {}).get("result", [])
            if not results:
                return []

            values = results[0].get("values", [])
            return [(int(ts), float(val)) for ts, val in values]

        except requests.RequestException as e:
            logger.error("prometheus_connection_error", expr=expr, error=str(e))
            return []
        except (ValueError, KeyError, IndexError) as e:
            logger.error("prometheus_parse_error", expr=expr, error=str(e))
            return []

    def get_latency_percentiles(self, window: str = "30s") -> dict[str, float]:
        """Get latency percentiles (p50, p95, p99) in milliseconds.

        Args:
            window: Time window for rate calculation (e.g., "30s", "1m")

        Returns:
            Dict with keys 'p50', 'p95', 'p99' containing latency in ms.
            Missing percentiles have value 0.0
        """
        percentiles = {"p50": 0.50, "p95": 0.95, "p99": 0.99}
        result: dict[str, float] = {}

        for name, quantile in percentiles.items():
            expr = (
                f"histogram_quantile({quantile}, "
                f"sum(rate(http_request_duration_seconds_bucket[{window}])) by (le)) * 1000"
            )
            value = self.query_instant(expr)
            result[name] = value if value is not None else 0.0

        return result

    def get_error_rate(self, window: str = "1m") -> float:
        """Get error rate as fraction (0-1).

        Args:
            window: Time window for rate calculation

        Returns:
            Error rate as float between 0 and 1
        """
        expr = f'sum(rate(http_requests_total{{status=~"5.."}}[{window}])) / sum(rate(http_requests_total[{window}]))'
        value = self.query_instant(expr)
        if value is None or value != value:  # NaN check
            return 0.0
        return max(0.0, min(1.0, value))

    def get_throughput(self, window: str = "1m") -> float:
        """Get request throughput (requests per second).

        Args:
            window: Time window for rate calculation

        Returns:
            Requests per second
        """
        expr = f"sum(rate(http_requests_total[{window}]))"
        value = self.query_instant(expr)
        return value if value is not None else 0.0

    def get_slo_violations(self, threshold_ms: float = 200) -> int:
        """Get count of SLO violations.

        Counts requests where latency exceeded the threshold.

        Args:
            threshold_ms: Latency threshold in milliseconds

        Returns:
            Count of violations as integer
        """
        _ = threshold_ms / 1000.0  # noqa: F841 — threshold in seconds (for future Prometheus queries)
        expr = "sum(increase(slo_violation_total[1h]))"
        value = self.query_instant(expr)

        if value is not None:
            return int(value)

        latencies = self.get_latency_percentiles()
        p99 = latencies.get("p99", 0.0)
        return 1 if p99 > threshold_ms else 0

    def parse_haproxy_stats_weights(self, url: str) -> Optional[dict[str, int]]:
        """Parse HAProxy stats CSV to get current k3s/knative weights.

        Args:
            url: HAProxy stats CSV endpoint URL

        Returns:
            Dict with 'k3s' and 'knative' weight values, or None on failure
        """
        try:
            r = self._session.get(url, timeout=5)
            if r.status_code != 200:
                return None

            weights: dict[str, int] = {}
            for line in r.text.strip().split("\n"):
                if line.startswith("#") or not line.strip():
                    continue
                fields = line.split(",")
                if len(fields) < 19 or fields[0] != "servers":
                    continue
                svname = fields[1]
                if svname in ("k3s", "k3s-cluster"):
                    weights["k3s"] = int(fields[18])
                elif svname in ("knative", "serverless-sim"):
                    weights["knative"] = int(fields[18])

            return weights if weights else None

        except Exception as e:
            logger.debug("haproxy_stats_parse_failed", error=str(e))
            return None
