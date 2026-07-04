# diagnostics/

Health checking and system diagnostics.

## What this does

`HealthChecker` verifies that all platform components are running and responding correctly. It checks:

- HAProxy — is the traffic router up? Is it distributing traffic?
- Prometheus — is the metrics scraper running? Is it collecting data?
- GRU Prediction Server — is the prediction API healthy?
- Routing Daemon — is the control plane responding?
- K8s test app — is the test application serving requests?
- Knative services — are serverless functions ready?

## Why "diagnostics" not "health"?

Health checking is operational diagnosis — it answers "what's broken?" across all domains (cluster, networking, observability, workloads). It's not a single domain like cluster or networking; it's a cross-cutting concern that checks everything.

If a component is unhealthy, the checker reports which one and why, helping operators quickly identify and fix issues.

## Related packages

- `infra/cli.py` — `thesis infra health` command uses `HealthChecker`
- `apps/experiment/experiment/stages/preflight.py` — Experiment preflight uses similar checks before running experiments
