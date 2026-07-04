"""Metrics-related models for Prometheus exports and resource sampling."""

from typing import List, Optional

from pydantic import BaseModel


class MetricSample(BaseModel):
    """A single Prometheus metric sample."""

    timestamp: float
    value: float


class MetricSeries(BaseModel):
    """A time series of Prometheus metric samples."""

    metric_name: str
    samples: List[MetricSample]

    @property
    def values(self) -> List[float]:
        return [s.value for s in self.samples]

    @property
    def timestamps(self) -> List[float]:
        return [s.timestamp for s in self.samples]


class ResourceSample(BaseModel):
    """A single resource utilization sample from metrics-server."""

    timestamp: float
    cpu_millicores: float
    memory_mib: float
    pod_name: Optional[str] = None


class MetricsExport(BaseModel):
    """Exported metrics for a single experiment run."""

    p99_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    error_rate: float = 0.0
    throughput_rps: float = 0.0
    weight_timeline: List[MetricSample] = []
    replica_timeline: List[MetricSample] = []
    resource_samples: List[ResourceSample] = []
