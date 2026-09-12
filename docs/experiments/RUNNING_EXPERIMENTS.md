# Running Experiments (Current Layout)

This is the current command and file map for the thesis experiment pipeline. Results and evidence remain under `results/`; this document does not duplicate raw or derived artifacts.

## Source layout

```text
apps/experiment/experiment/
  cli.py                 # thesis-experiment commands
  calibration.py         # capacity sweep and analysis
  dynamic.py             # dynamic S3/S4 workload
  trace_replay.py        # ClarkNet/Calgary replay generation
  evidence/              # registry, catalog, journal adapters
  stages/                # preflight, reset, workload, collect, validate, report
libs/infra/              # cluster, app, node, and health lifecycle
libs/shared/             # calibration and experiment models
```

The GRU training entry point is `python -m prediction.training.train_gru`. The running inference service is `thesis-prediction-server`, and the routing service is `thesis-routing-daemon`.

## Infrastructure and service checks

```bash
uv run thesis infra apply-resources
uv run thesis infra deploy-app
uv run thesis infra health

uv run thesis-prediction-server --port 8090
uv run thesis-routing-daemon --port 9104
```

Runtime ports:

| Service | Port |
|---|---:|
| Prediction server | 8090 |
| Routing daemon | 9104 |
| Prometheus | 9090 |
| HAProxy HTTP | 18082 |
| HAProxy stats | 18404 |

The workload request is `http://localhost:18082/fib?n=33`. The SLO monitor derives p99 from HAProxy `rtime`; the primary target is p99 < 200 ms.

## Canonical CLI commands

```bash
# Readiness
uv run thesis-experiment preflight

# Full S1-S4 evaluation
uv run thesis-experiment run --phase full --runs 5 --duration 300
# Optional subset
uv run thesis-experiment run --phase full --runs 5 --duration 300 \
  --scenarios s3-hybrid-reactive,s4-hybrid-predictive

# Definitive counterbalanced H2
uv run thesis-experiment paired-run --pairs 5

# Additional diagnostics and calibration
uv run thesis-experiment dynamic --runs 3
uv run thesis-experiment calibrate
uv run thesis-experiment trace-replay

# Evidence governance
uv run thesis-experiment evidence audit
uv run thesis-experiment evidence reconcile --apply
uv run thesis-experiment evidence catalog refresh
uv run thesis-experiment evidence journal
```

## Profiles and reproduce

`reproduce` runs an experiment end to end under a named profile: it converges the testbed to the profile's shape, ensures the prediction server is the right artifact, runs the design, and writes the analysis plus `SUMMARY.md`. A bundle that already holds every requested pair or run is only re-analysed; a partial bundle resumes.

Profiles are declared in `apps/experiment/experiment/profiles.py`:

| Profile | Design | Static agents | Prediction server |
|---|---|---|---|
| `h2-pair` | 5 counterbalanced S3/S4 pairs; node provisioning in the path (the H2 regime) | 1 | yes |
| `h2-pair-abundant` | 5 pairs; two agent nodes, so the autoscaler does not fire | 2 | yes |
| `s4-point-sizing` | S4 only, 3 runs; sizing from the central forecast (`ROUTING_SIZING_SIGNAL=point`) | 1 | yes |
| `s4-point-sizing-shrink` | S4 only, 3 runs; point sizing with a deliberate 0.85 under-forecast | 1 | yes |
| `baselines` | S1 and S2, 5 runs each; the H1 comparison | 1 | no |
| `quad` | all four arms, 5 runs each | 1 | yes |
| `smoke` | one S3/S4 pair, to check the testbed before a long run | 1 | yes |

```bash
uv run thesis-experiment reproduce --profile h2-pair
uv run thesis-experiment reproduce --profile quad --fresh-stack
uv run thesis-experiment reproduce --profile smoke --dry-run
```

`--pairs N` and `--runs N` override the profile's counts. `--output PATH` names the bundle (default `results/experiments/phase-b/<date>_<profile>-<suffix>`). `--fresh-stack` rebuilds both clusters and redeploys the app first. `--resume` (default) continues a partial bundle; `--force` replaces an existing one.

## Series

`series` chains profiles as stages in one invocation. A failing stage is retried up to `--max-attempts` (default 2); a stage that fails every attempt stops the chain, because the next stage assumes the stack the last one left. The work-tree indexer is paused for the window and restored afterwards.

```bash
uv run thesis-experiment series --stage smoke --stage h2-pair
uv run thesis-experiment series --stage smoke --dry-run
```

Stage syntax is `profile[:pairs=N,output=PATH,...]`; repeat `--stage` for a chain.

## Bundle analysis

```bash
# Recompute a bundle's paired verdict from its own runs;
# --write rewrites paired_analysis.json and SUMMARY.md, --json emits the verdict
uv run thesis-experiment analyze results/experiments/phase-b/<bundle>
uv run thesis-experiment summary results/experiments/phase-b/<bundle>

# Cloud cost analysis over per-scenario result.json subdirs
uv run thesis analysis cost --experiment-dir results/experiments/phase-b/<bundle>

# What each run measured, and the conditions it was measured under
uv run thesis analysis runs results/experiments/phase-b/<bundle>

# When the node tier arrived relative to the load, beside the tail it explains
uv run thesis analysis mechanism results/experiments/phase-b/<bundle>

# Run-to-run spread per arm, and what n pairs can resolve
uv run thesis analysis variance results/experiments/phase-b/<bundle>
```

## Evidence governance (full set)

| Command | Mode | Effect |
|---|---|---|
| `evidence audit` | read-only | Scan bundles; print valid/total and treatment fidelity |
| `evidence query "<sql>"` | read-only | SQL against the local DuckDB catalog; run `catalog refresh` first |
| `evidence journal` | read-only | Recent governance events from `registry-events.jsonl` |
| `evidence catalog refresh` | rebuilds local cache | Rebuild `catalog.duckdb` (git-ignored, never canonical) |
| `evidence reconcile --apply` | writes | Merge scanner facts into `results/evidence/registry.yaml`, append a governance event, regenerate `EXPERIMENT_JOURNAL.md` |
| `evidence backfill-legacy --apply` | writes | Backfill legacy v1 bundles into the typed registry; without `--apply` it prints a preview and exits nonzero |
| `evidence derive-parquet --source F --output P` | writes | Derive a provenance-preserving Parquet from a legacy CSV or JSONL artifact |

`reconcile` and `backfill-legacy` refuse to write without `--apply`.

## Scenario contract

| ID | Scenario | Expected control |
|---|---|---|
| S1 | K8s + HPA | Kubernetes baseline |
| S2 | Serverless-only | Knative only |
| S3 | Hybrid-reactive | Algorithm 1 on observed load |
| S4 | Hybrid-predictive | Algorithm 2 consumes GRU forecast; Algorithm 1 still routes on observed load/trend |

The GRU is trained on synthetic patterns, validated on ClarkNet and Calgary, and ClarkNet is replayed for evaluation. The direct forecast horizon is 9 × 15 s = 135 s.

## Run conditions and validity gates

Every entry point that executes a run passes through `apply` in `apps/experiment/experiment/conditions.py`: the testbed is converged, its residue cleared, and the checks run. A run whose checks fail does not start.

Checks: the expected agent nodes are present and ready; HAProxy and Prometheus are up; the scenario-appropriate endpoints are serving; the prediction port answers when the profile needs one; host load is below 1.0x the core count (above that the run is refused, above 0.5x a caveat is recorded).

What a bundle records about its conditions:

- `profile_applied` in the bundle's `events.jsonl`: the profile, the testbed shape, the prediction server status, and the full conditions report.
- `run_refused` in a run's `events.jsonl` when the gate refuses that run.
- The per-run conditions report in that run's `manifest.json`.
- The typed event vocabulary, including `run_conditioned` and `run_refused`, is `JournalEventName` in `libs/shared/shared/models/evidence.py`.

Check a profile's conditions without running it:

```bash
uv run thesis-experiment preflight --profile h2-pair
```

Validity gates applied after a run (`apps/experiment/experiment/stages/validate.py`):

- S4 treatment fidelity: the prediction service must have delivered on every prediction-eligible control cycle, or the run is not valid.
- Node engagement: when the scenario's design requires the node tier, a run where no pod went pending and no node was provisioned is marked invalid (`run_validity_passed=false`, reasons recorded).
- Request failures above 0.10, the k6 `http_req_failed` threshold, fail validity.

Invalid runs stay recorded as invalid; use the evidence audit and reconcile flow rather than editing result data.

## Final result references

- H2 definitive paired n=5: S3 mean p99 188.5 ms vs S4 126.0 ms, p=0.0304, d=-1.26; proxy cost USD 163 for each.
- H1 directional n=1: S4 p99 118.2 ms vs S1 2,421.3 ms.
- Calibration: `r_saturation_per_replica=33.3`, `max_k8s_replicas=6`, deterministic `/fib?n=33` endpoint.

These are evidence-aligned summaries, not new measurements. H1 is directional and the cost model is a proxy.

## Troubleshooting by pipeline stage

1. If preflight fails, use `uv run thesis infra health` and correct the infrastructure before running workloads.
2. If the prediction health check fails for S4, start `thesis-prediction-server` on 8090 and verify the model artifact expected by the service.
3. If routing metrics are absent, verify `thesis-routing-daemon` on 9104 and Prometheus on 9090.
4. If p99 is missing, inspect HAProxy stats on 18404 and confirm the rtime-derived monitor stream.
5. If a bundle is invalid, keep it recorded as invalid and use the evidence audit/reconcile flow; do not hand-edit result data.
