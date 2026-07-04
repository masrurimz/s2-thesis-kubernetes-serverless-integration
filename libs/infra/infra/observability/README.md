# observability/

Monitoring and metrics collection.

## prometheus/

Prometheus scrapes metrics from all services: HAProxy stats, routing daemon decisions, k6 test results, Kubernetes resource usage. The experiment runner queries Prometheus to collect time-series data for analysis.

Files:
- `prometheus.yml` — Scrape config (targets, intervals)
- `rules.yml` — Recording and alerting rules
- `prometheus-k8s.yaml` — Kubernetes deployment manifest
- `prometheus.yaml` — VPS deployment config
- `docker-compose.yml` — Local docker-compose (Prometheus + node-exporter)

**What's the difference between the two config files?**
- `prometheus.yml` — used by local docker-compose (Sprint 1 era, short retention)
- `prometheus.yaml` — used for VPS/k8s deployment (7-day retention, more scrape targets)

## Related packages

- `infra/observability/prometheus/client.py` — `PrometheusClient` for querying Prometheus HTTP API
- `apps/experiment/experiment/stages/collect.py` — Uses PrometheusClient to export metrics during experiments
