"""Metrics-related models for Prometheus exports and resource sampling."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


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
    """A single resource utilization sample from metrics-server.

    Field names are the persisted wire keys, so the artifact and the model cannot
    disagree about what a sample is.
    """

    model_config = ConfigDict(extra="ignore")

    timestamp: float
    pod: str
    backend: str = ""
    cpu_millicores: float
    memory_mib: float


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


# Tokens metrics-server prints when it has no reading for a node or pod yet. They
# are a missing measurement, not a zero, and must never be coerced into one.
_UNREADABLE = frozenset({"<unknown>", "unknown", "n/a", "nan", ""})


def _is_unreadable(text: str) -> bool:
    return text.strip().lower() in _UNREADABLE


def _parse_percent(value: str) -> Optional[float]:
    """`6%` to 6.0; None when there is no reading."""
    text = value.strip().rstrip("%")
    if _is_unreadable(value):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_cpu_to_cores(value: str) -> Optional[float]:
    """A Kubernetes CPU quantity to cores: `250m` to 0.25, `2` to 2.0.

    Returns None when the value carries no reading, so callers decide whether a
    missing measurement is skipped or reported; it is never silently zero.
    """
    text = value.strip()
    if _is_unreadable(text):
        return None
    try:
        if text.endswith("n"):
            return int(text[:-1]) / 1_000_000_000
        if text.endswith("u"):
            return int(text[:-1]) / 1_000_000
        if text.endswith("m"):
            return int(text[:-1]) / 1000
        return float(text)
    except ValueError:
        return None


def parse_memory_to_mib(value: str) -> Optional[float]:
    """A Kubernetes memory quantity to MiB: `1024Ki` to 1.0, `2Gi` to 2048.0."""
    text = value.strip()
    if _is_unreadable(text):
        return None
    try:
        for suffix, factor in (("Ki", 1 / 1024), ("Mi", 1.0), ("Gi", 1024.0), ("Ti", 1024.0 * 1024)):
            if text.endswith(suffix):
                return int(text[: -len(suffix)]) * factor
        return int(text) / (1024 * 1024)  # plain bytes
    except ValueError:
        return None


class NodeSample(BaseModel):
    """One node's utilization reading from `kubectl top nodes`.

    Fields are optional because a node metrics-server has not scraped yet reports
    `<unknown>`: the sample then records what exists and leaves the rest absent.
    """

    model_config = ConfigDict(frozen=True)

    timestamp: float
    node: str
    cpu_cores: Optional[float] = None
    cpu_pct: Optional[float] = None
    memory_mib: Optional[float] = None
    memory_pct: Optional[float] = None

    @classmethod
    def from_kubectl_top_row(cls, row: str, timestamp: float) -> Optional["NodeSample"]:
        """Parse one `kubectl top nodes --no-headers` row, or None if it holds nothing.

        Columns: NAME CPU(cores) CPU% MEM(bytes) MEM%. A brand-new node prints
        `<unknown>` in all four, which is the normal state during the provisioning
        window; such a row yields None instead of a zero-filled sample.
        """
        parts = row.split()
        if len(parts) < 5:
            return None
        cpu_cores = parse_cpu_to_cores(parts[1])
        memory_mib = parse_memory_to_mib(parts[3])
        if cpu_cores is None and memory_mib is None:
            return None
        return cls(
            timestamp=timestamp,
            node=parts[0],
            cpu_cores=cpu_cores,
            cpu_pct=_parse_percent(parts[2]),
            memory_mib=memory_mib,
            memory_pct=_parse_percent(parts[4]),
        )
