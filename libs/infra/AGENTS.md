# libs/infra — Infrastructure Management

## What This Is

Domain-driven infrastructure package. Manages cluster lifecycle, serverless infrastructure, networking, observability, test workloads, and diagnostics. Replaces the former `deploy/` directory with Python code and package data.

## Module Map

| Module | Purpose |
|--------|---------|
| `cli.py` | Typer CLI: `thesis infra setup`, `teardown`, `health`, `status`, `cluster` |
| `config.py` | `PlatformConfig` — port/host definitions (replaces `deploy/config.env`) |
| `commands.py` | Subprocess wrapper with Rich logging + dry-run |
| `cluster/k3d/` | `K3dManager` — create/delete k3d cluster + `cluster.yaml` |
| `cluster/k8s/` | `K8sScaler` — kubectl subprocess wrapper |
| `serverless/knative/` | `KnativeInstaller` + Knative manifests |
| `serverless/activator/` | Go module: Knative cold-start activator + `ActivatorManager` |
| `networking/haproxy/` | `HAProxyClient` + `HAProxyManager` + HAProxy configs |
| `observability/prometheus/` | `PrometheusClient` + `PrometheusManager` + Prometheus configs |
| `workloads/test_app/` | Go module: HTTP test app + `TestAppManager` |
| `workloads/k6/` | `K6Runner` — k6 load test runner |
| `diagnostics/` | `HealthChecker` — HTTP health checks |

## Design Principle: Domain-Driven

Directories organized by domain (what it does), not by tool (what it uses):
- `cluster/` = Kubernetes cluster lifecycle (k3d, k8s)
- `serverless/` = Serverless infrastructure (knative, activator)
- `networking/` = Traffic routing (haproxy)
- `observability/` = Monitoring (prometheus)
- `workloads/` = Test applications (test_app, k6)
- `diagnostics/` = Health checking

Each tool directory contains both Python code AND config assets (YAML, Dockerfiles, Go source) as package data.

## Dependencies

- `shared` (config, models)
- `requests`, `rich`, `typer`

## CLI Commands

```bash
uv run thesis infra setup              # Full infrastructure setup
uv run thesis infra teardown           # Tear down everything
uv run thesis infra health             # Health check all components
uv run thesis infra status             # Show infrastructure status
```
