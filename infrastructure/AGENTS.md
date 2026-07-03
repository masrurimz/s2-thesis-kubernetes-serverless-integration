# infrastructure/ — Platform and Traffic Generation

## What This Is

K3s/K3d cluster configs, HAProxy routing, Knative serverless, Prometheus monitoring, and k6 load test scripts. Not Python — mostly YAML (K8s), JS (k6), shell scripts, and config files.

## Quick Commands

```bash
# Cluster setup
cd infrastructure && ./scripts/setup.sh

# Run load tests
./load-tests/run-load-tests.sh steady

# Check health
./scripts/check-health.sh

# Teardown
./scripts/teardown.sh
```

## k6 Load Tests

Organized into three subdirectories under `load-tests/`:

| Directory | Purpose | Files |
|-----------|---------|-------|
| `canonical/` | Scripts used by final thesis evidence | clarknet_replay.js, spike.js, stress.js, endurance.js, steady.js, dynamic_burst.js, clarknet_replay_fib34.js |
| `calibration/` | Calibration and SLO finder scripts | calibration.js, calibrate_work.js, t7-*.js |
| `legacy/` | Historical variants (git history is backup) | *-legacy.js, spike-stress.js, ramp.js, etc. |

See `load-tests/README.md` for the full manifest with used-by references.

## Conventions

- **Shell scripts** at `load-tests/` root are the runners — don't move them into subdirs.
- **`scripts/`** here is infra setup/teardown (not analysis scripts — those are in top-level `scripts/`).
- **`config.env`** + `load-config.sh` centralize port/host configuration.
- **Don't edit k6 scripts in legacy/** unless fixing a bug that affects historical bundle interpretation.

## What NOT to Edit

- `test-app/` — Go test application, stable. Only change for infrastructure changes.
- `serverless-activator/` — Knative activator, rarely touched.
