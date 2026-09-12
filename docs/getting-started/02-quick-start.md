# Quick Start: One Honest Experiment

## Goal

Bring the governed testbed up, converge it to a known shape, run one smoke pair, and read the bundle it produces. Everything goes through the `thesis` CLI.

## Prerequisites

- Docker running, `kubectl` and `k3d` installed, `k6` on PATH
- 8 GB+ RAM free (the testbed runs two k3d clusters plus Knative)
- Repo installed: `git lfs install` once per clone, then `uv sync`

See [Prerequisites](01-prerequisites.md) for details.

## Step 1: Bring the testbed up

```bash
# Full setup: clusters (thesis-hybrid + thesis-serverless), Knative, networking, monitoring.
uv run thesis infra setup

# Converge to a runnable state: clusters, HAProxy, Prometheus, node count.
# Idempotent; prints only the actions it had to take.
uv run thesis infra ensure --agents 1

# Deploy the deterministic test app (/fib?n=33) to both clusters.
uv run thesis infra deploy-app

# Check the result.
uv run thesis infra status
```

The static agent count matters. With spare agent nodes the node autoscaler never fires, and a predictive-scheduling comparison measures nothing. One static agent is the shape the H2 experiments run under. `uv run thesis infra shape-nodes --agents 1 --dry-run` reports the change without making it.

## Step 2: Check the conditions

```bash
uv run thesis experiment preflight --profile smoke
```

This is the same battery the runner applies before every run: testbed converged and residue cleared, nodes ready, both arms serving, prediction server present when the design needs it, host quiet enough to measure on. Add `--no-converge` to report only.

## Step 3: Run one smoke pair

```bash
uv run thesis experiment reproduce --profile smoke
```

One S3/S4 pair, end to end: the testbed is re-converged before each run, the design runs, the analysis and a `SUMMARY.md` are written, and the command exits nonzero if a run or pair fails its gate. The bundle lands in `results/experiments/phase-b/` under a dated name like `2026-09-12_smoke-1p`.

A dry run reports what would happen without changing anything:

```bash
uv run thesis experiment reproduce --profile smoke --dry-run
```

## Step 4: Read the bundle

```bash
BUNDLE=results/experiments/phase-b/<your-dated-bundle>

# What each run measured, and the conditions it was measured under.
uv run thesis analysis runs "$BUNDLE"

# When the node tier arrived relative to the load, beside the tail it explains.
uv run thesis analysis mechanism "$BUNDLE"

# How far each arm moved run to run, and what n pairs can resolve.
uv run thesis analysis variance "$BUNDLE"

# The human-readable summary: what ran, headline table, pair verdict.
uv run thesis experiment summary "$BUNDLE"
```

Each analysis command takes `--json` for program use. Open `$BUNDLE/SUMMARY.md` for the written verdict; `raw/<scenario>_run<N>/` holds the per-run evidence.

## What you just ran

- **S3 (hybrid-reactive)**: Algorithm 2 scales replicas from observed load only; Algorithm 1 (V3) routes by capacity.
- **S4 (hybrid-predictive)**: same controllers, but a GRU forecast (9 × 15 s = 135 s ahead) gates proactive scaling.
- Workload: ClarkNet trace replay against `/fib?n=33`, calibrated so p99 lands near the 200 ms SLO.
- Primary SLO: p99 < 200 ms. A run that fails its treatment-fidelity gate is invalid and excluded.

## Next steps

- The real H2 regime: `uv run thesis experiment reproduce --profile h2-pair` (five counterbalanced S3/S4 pairs).
- [Understanding Architecture](03-understanding-architecture.md) for the component map.
- [Running experiments](../experiments/RUNNING_EXPERIMENTS.md) for the full runbook, profiles, and evidence lifecycle.
- Root [README](../../README.md) for test tiers and evidence rules.

## Teardown

```bash
uv run thesis infra teardown
```
