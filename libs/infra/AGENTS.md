# libs/infra

Domain-driven infrastructure package: k3d cluster lifecycle, node shaping and residue clearing, Knative installation, HAProxy routing, Prometheus scrape configuration, test-app deployment, and cluster diagnostics. Owns the `thesis infra` CLI.

## Module map

Package source lives under `libs/infra/infra/` (nested package layout).

| Path | Responsibility |
|---|---|
| `infra/cli.py` | Typer app registering all `thesis infra` commands; thin handlers importing domain modules |
| `infra/config.py` | `PlatformConfig`: port/host definitions (replaces the former `deploy/config.env`) |
| `infra/commands.py` | `run()`: subprocess wrapper with Rich logging and dry-run support |
| `infra/readiness.py` | Testbed convergence: `ensure_testbed`, `inspect_testbed`, `rebuild_testbed`, `cluster_nodes_ready`, `app_endpoints_serving`. Backs `ensure`/`rebuild`; also imported by `apps/experiment` (`experiment/conditions.py`, `experiment/cli.py`) |
| `infra/cluster/k3d/manager.py` | `K3dManager`: create/delete clusters, `apply_node_resources` / `apply_serverless_node_resources` (Docker CPU/memory limits from `CALIBRATION`) |
| `infra/cluster/k3d/shaping.py` | Node inventory and convergence: `list_nodes`, `remove_node`, `converge_agent_count`, `is_live_k8s_node`. Backs `shape-nodes` |
| `infra/cluster/k3d/residue.py` | Clear what an earlier run leaves: `prune_dynamic_nodes`, `settle_workload`, `prune_orphaned_pods`. Consumed by `readiness.py` |
| `infra/cluster/k3d/autoscaler.py` | `K3dAutoscaler`: standalone k3d-backed dynamic node autoscaler for experiment orchestration |
| `infra/cluster/k8s/scaler.py` | `K8sScaler`: kubectl subprocess wrapper (cordon/uncordon); used by `apps/routing` (`routing/daemon/service.py`) |
| `infra/serverless/knative/installer.py` | `KnativeInstaller`: applies the Knative manifests in the same directory |
| `infra/serverless/activator/` | Go cold-start activator (`main.go`) + `ActivatorManager` + deployment/rbac/service manifests |
| `infra/networking/haproxy/manager.py`, `client.py` | `HAProxyManager` (docker compose lifecycle), `HAProxyClient` (stats) |
| `infra/networking/haproxy/render.py` | Renders the shipped HAProxy config against the live cluster (substitutes the sslip.io domain embedding the Kourier service IP) into a runtime path |
| `infra/observability/prometheus/manager.py`, `client.py` | `PrometheusManager` (compose lifecycle), `PrometheusClient` implementing `shared.protocols.metrics.MetricsClient` |
| `infra/observability/prometheus/config.py` | Scrape configuration via the Kubernetes API proxy: renders kubeconfig credentials into the container, validates with promtool in a throwaway container, reloads (never restarts), reports per-series counts. Backs `monitoring` |
| `infra/workloads/deploy.py` | `deploy_test_app`: build/import image, deploy to both clusters, endpoint and Knative-webhook readiness probes. Backs `deploy-app` and the rebuild path |
| `infra/workloads/test_app/` | Go HTTP test app (`main.go`) + `TestAppManager` + k8s/knative/hpa/nodeport manifests |
| `infra/diagnostics/checker.py` | `HealthChecker`: HTTP health checks across components. Backs `health` |
| `infra/diagnostics/verifier.py` | `ClusterVerifier`: node CPU allocation fairness and node-label/capacity checks. Backs `verify` |

## Module direction

- **May import:** `shared.*` (protocols, models, calibration, output) and third-party (typer, rich, requests, structlog). Currently: `shared.protocols.metrics`, `shared.output`.
- **Access rule:** apps reach this package through the `thesis infra` CLI or a `shared.protocols` contract, not by importing internals. Current direct importers (named in the map above): `apps/experiment` (`infra.readiness`) and `apps/routing` (`infra.cluster.k8s.K8sScaler`).
- **Where new code goes:**
  - A new CLI command: handler in `cli.py` (thin), logic in the owning domain module.
  - A new cluster operation: `cluster/<tool>/<module>.py` beside its siblings.
  - A new config asset (YAML, Dockerfile, Go source): the same directory as its Python owner, shipped as package data, read via `importlib.resources`.
  - A new test: `libs/infra/tests/`, monkeypatching `infra.commands.run`.

## Design principle: domain-driven

Directories are organized by domain (what it does), not by tool (what it uses): `cluster/` (k3d, k8s), `serverless/` (knative, activator), `networking/` (haproxy), `observability/` (prometheus), `workloads/` (test_app), `diagnostics/` (checker, verifier). Each tool directory contains both Python code and config assets as package data.

## Tests

`libs/infra/tests/`: prometheus config, readiness, deploy, haproxy render, commands, shaping. All hermetic: the subprocess layer (`infra.commands.run`) is monkeypatched with stateful fakes (`FakeK3d`, `CompletedProcess` stubs); no cluster, docker, or network is required.

```bash
uv run python -m pytest libs/infra/tests -q
```

Live/opt-in tier: none in this package. Tests that need a real cluster live in the apps (e.g. `apps/experiment/tests/test_cpu_fairness_e2e.py`, skipped unless `thesis-hybrid` is running).

## Commands it contributes

```bash
uv run thesis infra setup             # Full setup: cluster, serverless, networking, monitoring
uv run thesis infra teardown          # Tear down all infrastructure components
uv run thesis infra health            # Health check all components
uv run thesis infra verify            # Node CPU allocation fairness and configuration
uv run thesis infra apply-resources   # Apply Docker CPU/memory limits to existing nodes
uv run thesis infra status            # Show infrastructure status
uv run thesis infra cluster <action>  # Manage the k3d cluster (create, delete, status)
uv run thesis infra ensure            # Converge testbed: clusters, HAProxy, Prometheus, node count
uv run thesis infra shape-nodes       # Converge the number of static agent nodes
uv run thesis infra monitoring        # Make app and kubelet metrics scrapable
uv run thesis infra deploy-app        # Build and deploy test-app to both clusters
uv run thesis infra rebuild           # Tear down, bring back up, then converge
```

## Invariants

- Convergence commands (`ensure`, `shape-nodes`, `apply-resources`, `deploy-app`) are idempotent: a second run with the same arguments takes no actions.
- `rebuild` exists to remove inherited state (dynamic nodes, warm pods, months of objects). It costs minutes; it belongs before an experiment, not between its runs.
- The static agent count decides whether the node tier is exercised at all: with spare agents the autoscaler never fires, which changes what a predictive-scheduling comparison measures.
- `monitoring` reloads Prometheus, never restarts it, so it is safe while experiments run. Credentials are rendered from the kubeconfig at runtime and never committed.
- HAProxy configs in the package are templates: the live sslip.io domain embeds the Kourier service IP, so `render.py` substitutes it into a runtime path rather than editing tracked files.
- Docker node CPU/memory limits are hardcoded per-node tuples in `cluster/k3d/manager.py` (`apply_node_resources`, `apply_serverless_node_resources`), sized so a 1.0-CPU agent fits about three 300m pods. The 300m request itself is hardcoded in the warm/knative manifests (`workloads/test_app/`); `CALIBRATION.pod_cpu_request` in shared mirrors it so analysis math agrees. The `apply-resources` help text says "Enforces CalibrationConfig values", but the node numbers do not read it.
