# libs/infra — Infrastructure Adapters

## What This Is

Shared infrastructure clients used by both routing and experiment packages. Avoids duplicating Prometheus/HAProxy/k8s/k6 helpers.

## Module Map

| Module | Purpose |
|--------|---------|
| `prometheus.py` | `PrometheusClient` — HTTP API client (query_instant, query_range, latency percentiles) |
| `haproxy.py` | `HAProxyClient` — TCP socket + stats CSV client (weights, enable/disable) |
| `kubernetes.py` | `K8sScaler` — kubectl subprocess wrapper for replica scaling |
| `k6.py` | `K6Runner` — k6 load test runner with output parsing |

## Dependencies

- `shared` (config, models)
- `requests` (HTTP)

## Boundaries

- Depends on `shared` only — never imports from `apps/`
- Clients are stateless — create new instances per use
- All clients accept config via constructor params, not global state
