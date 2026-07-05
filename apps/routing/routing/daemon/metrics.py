"""Prometheus metrics registration for the routing daemon.

Extracted from controller/daemon/routing_daemon.py lines 101-166.
"""

from prometheus_client import Counter, Gauge, Histogram, REGISTRY


def _get_or_create_metric(metric_class, name, description, labelnames=None, buckets=None):
    """Get existing metric or create new one (handles re-import)."""
    try:
        if labelnames:
            if buckets:
                return metric_class(name, description, labelnames, buckets=buckets)
            return metric_class(name, description, labelnames)
        else:
            if buckets:
                return metric_class(name, description, buckets=buckets)
            return metric_class(name, description)
    except ValueError:
        return REGISTRY._names_to_collectors.get(name)


daemon_decision_total = _get_or_create_metric(
    Counter,
    "routing_daemon_decision_total",
    "Total routing decisions by daemon",
    ["scenario", "action"],
)

daemon_current_weight = _get_or_create_metric(
    Gauge,
    "routing_daemon_current_weight",
    "Current routing weight",
    ["backend"],
)

daemon_prediction_used = _get_or_create_metric(
    Counter,
    "routing_daemon_prediction_used",
    "Predictions from GRU used in decisions",
)

daemon_prediction_failed = _get_or_create_metric(
    Counter,
    "routing_daemon_prediction_failed",
    "Failed prediction requests",
)

daemon_decision_latency = _get_or_create_metric(
    Histogram,
    "routing_daemon_decision_latency_ms",
    "Decision loop latency in milliseconds",
    buckets=[5, 10, 25, 50, 100, 250, 500, 1000],
)

k8s_scaling_events_total = _get_or_create_metric(
    Counter,
    "k8s_scaling_events_total",
    "K8s replica scaling events",
    ["direction", "result"],
)

k8s_desired_replicas = _get_or_create_metric(
    Gauge,
    "k8s_deployment_desired_replicas",
    "Desired replica count for K8s deployment",
)

k8s_available_replicas = _get_or_create_metric(
    Gauge,
    "k8s_deployment_available_replicas",
    "Available replica count for K8s deployment",
)
# Pre-create labeled children so Prometheus sees them from the first scrape.
# Without this, the labeled gauge series don't exist until the daemon calls
# .labels(backend="...").set(...) during init, and early scrapes see nothing.
daemon_current_weight.labels(backend="k3s").set(0)
daemon_current_weight.labels(backend="knative").set(0)
