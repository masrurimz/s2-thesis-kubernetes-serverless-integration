# workloads/

Test applications and load generators used in experiments.

## Why both test_app and k6?

| Subdirectory | What it does | Technology |
|-------------|-------------|------------|
| `test_app/` | HTTP test application with `/work` and `/fib` endpoints | Go |
| `k6/` | Load test runner that generates traffic against the test app | JavaScript (k6) |

**test_app** is the **target** — the application being load-tested. It simulates CPU-bound work (`/fib?n=34`) and configurable-duration work (`/work?duration_ms=5`).

**k6** is the **load generator** — it sends HTTP requests to the test app at controlled rates, simulating real traffic patterns (ClarkNet trace replay, spike tests, steady load).

Both are needed for experiments: k6 generates the traffic, test_app handles it. The experiment runner (`apps/experiment/`) orchestrates both.

## test_app (Go application)

Standalone Go module with `go.mod`. Built via `docker build`, deployed as both K8s Deployment (warm) and Knative Service (cold). Configs:
- `k8s-deployment.yaml` — K8s deployment
- `knative-service.yaml` — Knative service
- `hpa.yaml` — Horizontal Pod Autoscaler
- `test-app-warm-deployment.yaml` — Warm (always-running) variant
- `test-app-cold-deployment.yaml` — Cold (scale-to-zero) variant

## k6

The k6 JavaScript load test scripts are NOT here — they live in `apps/experiment/experiment/load_tests/` because they're experiment-specific workloads (ClarkNet replay, calibration, etc.). This package only contains the `K6Runner` Python class that executes k6 as a subprocess.

## Related packages

- `apps/experiment/experiment/stages/workload.py` — Uses `K6Runner` to run experiments
- `apps/experiment/experiment/load_tests/` — k6 JavaScript scripts (canonical, calibration, legacy)
