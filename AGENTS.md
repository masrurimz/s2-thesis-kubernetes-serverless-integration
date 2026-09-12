# AGENTS.md

Agent instructions for this repository.

## Project Overview

This is a **completed** Master's thesis research project implementing a hybrid k3s-serverless architecture with intelligent traffic routing based on GRU workload prediction and SLO monitoring.

**Thesis Title**: "Decision Making and Elastic Scalability Management in Heterogeneous Cloud Environments Based on Workload Prediction"

**Current Status**: All 5 sprints complete. Experiments ran. Writing thesis document.

---

## Repository Map

| Directory | Purpose | Rule |
|-----------|---------|------|
| `libs/shared/` | **Foundation package** — Pydantic models, config, scenarios, protocols, storage | Never import from `apps/`. Every other package depends on this. |
| `libs/infra/` | **Infrastructure clients** — K8sScaler, K3dAutoscaler, Prometheus client, HAProxy adapter | Shared by routing and experiment packages |
| `libs/analysis/` | **Domain analysis library** — data loaders, pairwise comparison, cold-start decomposition, cost model, report gen | Depends on `shared` only. Consumed by `apps/analysis`, `apps/experiment`, `apps/dashboard`. |
| `apps/prediction/` | **GRU prediction service** — FastAPI server, model loader, training | Deployable service (port 8090) |
| `apps/routing/` | **Routing daemon** — V1/V2/V3 controllers (Algorithm 1), Algorithm 2 (ClusterController), daemon, SLO monitor, weight adjuster | Deployable service (port 9104) |
| `apps/experiment/` | **Experiment orchestration** — pipeline stages, CLI, calibration, dynamic, trace-replay, realtime validation | CLI tool for running experiments |
| `apps/analysis/` | **Analysis CLI** — post-hoc statistics, cost model, cold-start, plots, hypothesis validation | Typer sub-app (`thesis analysis <cmd>`); thin orchestration over `libs/analysis` |
| `results/` | **Single source of truth for ALL experiment evidence** | Evidence system: typed registry, journals, claims. See `results/AGENTS.md` and `results/evidence/README.md` before adding experiments. |
| `thesis/` | **Narrative only** — thesis text, protocol, appendices | Links INTO `results/` for evidence |
| `thesis-typst/` | **Canonical thesis book (Typst)** — English-first body + dual abstracts + ITS ITS-IF formatting | `typst compile`; see thesis-typst/README.md for preview |
| `thesis-latex/` | (archived) previous LaTeX version | read-only snapshot under `archived/thesis-latex/` |
| `data/` | Datasets (ClarkNet, Calgary traces, synthetic) | Large files tracked via `.gitattributes` |
| `data/trace-replay/` | k6 stage JSONs (ClarkNet + 4 synthetic archetypes) | Workload traces for experiment replay |
| `infrastructure/` | k3d configs, HAProxy, load testing, cluster setup scripts | Deployment configs and ops tooling |
| `docs/` | Setup guides, specs, architecture docs | Points to `results/` for evidence |
| `archived/` | Legacy sprint artifacts, deprecated code | **Read-only. Never add new work here.** |

**Package-level AGENTS.md files** exist in every `libs/` and `apps/` package. Read the nearest one before editing files in that directory.

---

## Module Dependency Graph

```
libs/shared              (models, protocols, config, scenarios, storage)
  ↑
  ├── libs/infra         (K8sScaler, K3dAutoscaler, Prometheus client, k6 client)
  │     ↑
  │     ├── apps/prediction   (GRU server, FastAPI port 8090)
  │     ├── apps/routing      (V1/V2/V3 controllers, Algorithm 2, daemon port 9104)
  │     └── apps/experiment   (pipeline stages, CLI, calibration, dynamic, trace-replay)
  │
  └── libs/analysis          (data loaders, comparison, cold-start, cost, report — depends on shared)
        ↑
        ├── apps/analysis    (Typer CLI: thesis analysis <cmd> — post-hoc statistics + plots)
        ├── apps/experiment  (analyze stage delegates to shared.stats + libs/analysis)
        └── apps/dashboard   (panels import constants from shared.scenarios)
```

No circular dependencies. `libs/` never imports from `apps/`.


## Experiment Architecture

| Scenario | Pod Autoscaler | Node Autoscaler | Traffic Routing | HPA |
|----------|---------------|-----------------|-----------------|-----|
| S1 (K8s-only) | HPA (CPU 50%, 1-10) | K3dAutoscaler (min=0, max=2) | 100% K8s | Enabled |
| S2 (Serverless) | KPA (Knative) | N/A | 100% Serverless | Disabled |
| S3 (Hybrid-reactive) | Algorithm 2 (observed-only) | K3dAutoscaler | V3 capacity-driven | Disabled |
| S4 (Hybrid-predictive) | Algorithm 2 (GRU) | K3dAutoscaler | V3 capacity-driven | Disabled |

Key patterns:
- **HAProxy weight-time product**: Traffic split = `serverless_weight_time / (k8s_weight_time + serverless_weight_time)`. NOT `time_in_serverless_pct`.
- **Prometheus Gauge pre-init**: Labeled Gauge children need `.labels(value).set(0)` at import or Prometheus sees nothing on first scrape.
- **Node utilization**: `kubectl top nodes` polled alongside pods. Stored in `node_utilization.json`.
- **Provisioning delay**: 45-120s simulated VM boot before k3d node creation.
- **Inter-module contracts**: Protocols in `libs/shared/shared/protocols/` (PredictionClient, RoutingDaemonClient, MetricsClient, ProvisionerClient). Pydantic models in `libs/shared/shared/models/`.
---

## Development Commands

### Workspace (run from repo root)

```bash
uv sync                              # Install all workspace packages
uv run python -m pytest              # Run all tests
uv run thesis --help                 # Unified CLI help
uv run thesis experiment preflight   # Validate infrastructure
uv run thesis routing daemon --scenario s4-hybrid-predictive  # Start daemon
uv run thesis prediction serve --port 8090                    # Start prediction server
```

### Service-specific entry points

```bash
uv run thesis-prediction-server      # Prediction server
uv run thesis-routing-daemon         # Routing daemon
uv run thesis-experiment             # Experiment runner
```

### Reproduction

An experiment is only repeatable if the conditions it ran under are part of it. Two runs of the same scenarios differ in result when the cluster happens to carry a spare node that absorbs the ramp, or when the prediction server is missing or serving a different artifact. `reproduce` makes those conditions explicit, converges the testbed to them, runs the design, and writes a summary a person can read.

```bash
# Counterbalanced S3/S4 pairs with one static agent node: the regime H2 is about.
uv run thesis experiment reproduce --profile h2-pair

# What would happen, changing nothing.
uv run thesis experiment reproduce --profile h2-pair --dry-run

# One pair, to check the testbed before a long run.
uv run thesis experiment reproduce --profile smoke

# Read a finished bundle without touching it.
uv run thesis experiment summary results/experiments/phase-b/<bundle>

# Converge the testbed alone (clusters, HAProxy, Prometheus, node count).
uv run thesis infra ensure --agents 1
uv run thesis infra shape-nodes --agents 1 --dry-run
```

Profiles live in `apps/experiment/experiment/profiles.py`: `h2-pair`, `h2-pair-abundant`, `s4-point-sizing`, `s4-point-sizing-shrink`, `baselines`, `quad`, `smoke`. Each names its scenarios, design, static agent count, whether it needs the prediction server, and any controller environment it sets.

Guarantees:

- **Idempotent.** A bundle that already holds every requested pair or run is left alone and only re-analysed. A partial bundle continues from where it stopped, appending rather than overwriting. `--resume` is the default; `--force` replaces the bundle.
- **Scriptable.** Non-interactive, with exit code 1 when a run or pair fails its gate, so a wrapper can chain profiles.
- **Conditions recorded.** The profile, the testbed convergence result, and the prediction server's artifact hash land in the bundle's `events.jsonl` as a `profile_applied` event.
- **Readable.** Every bundle gets `SUMMARY.md`: what ran, the headline table per arm, the paired verdict, forecast fidelity, and the reasons any run was rejected.

The agent count is not decoration. On 2026-09-11 a pair ran against a cluster with two static agents, no node was provisioned, the reactive arm paid no provisioning penalty, and the predictive arm's over-provisioning showed up as pure cost. The same design with one static agent on 2026-07-14 provisioned two nodes per run, each costing 59 to 122 seconds, and the predictive arm won. Same code, different regime, opposite answer.

### Conditioning — one gate, every path

A run starts from the conditions `RunConditions` declares or it does not start. `_run_single` calls `experiment/conditions.py::apply` before anything else, and every entry point funnels through `_run_single`, so no command can skip it:

1. **Converge and clean.** `infra.readiness.ensure_testbed` sets the static agent count, deletes leftover dynamic nodes, deletes pods whose node is gone, and waits for the Kubernetes node objects to agree with the containers.
2. **Check.** Nodes Ready; both arms serving (only the arms the scenario uses — S2 drains K8s on purpose); a prediction port when the design needs one; the host quiet enough to measure on.
3. **Refuse, loudly.** A failed check raises `ConditionsUnmet`, records `run_refused` in the run's journal, and returns no result, which the pair loop already treats as a failed pair.

```bash
# The same battery, before committing hours to a run.
uv run thesis experiment preflight --profile h2-pair
uv run thesis experiment preflight --profile h2-pair --no-converge   # report only

# Teardown, recreate both clusters, reinstall Knative, redeploy, converge.
# Minutes, so it belongs before an experiment, not between its runs.
uv run thesis experiment reproduce --profile h2-pair --fresh-stack
```

**When an experiment changes, its conditions change with it.** A new profile or scenario set must declare what it needs — static agents, the prediction server, controller environment — and `apps/experiment/tests/test_profiles.py` fails when a hybrid profile leaves no capacity to bind or a predictive one serves no predictor. A new check belongs in `conditions.apply`, next to the others, so both `preflight` and the runner get it.

**Host hygiene is part of the measurement.** The gate reports CPU busy from `/proc/stat` and refuses above full occupancy, naming the processes responsible. Indexers count: `graphify-watcher.service` holds most of a core while it watches the work tree, and any experiment run on the same machine waits for it.

```bash
systemctl --user stop graphify-watcher.service    # before a measurement window
systemctl --user start graphify-watcher.service   # after
```

### Reading a finished bundle

A bundle is evidence other people and agents have to read. Three commands answer the
questions it exists to answer, each with a table for a person and `--json` for a
program; nothing about a bundle should need a script written beside it.

```bash
# What each run measured, and the conditions it was measured under.
uv run thesis analysis runs results/experiments/phase-b/<bundle>
# When the node tier arrived relative to the load, beside the tail it explains.
uv run thesis analysis mechanism results/experiments/phase-b/<bundle>
# How far each arm moved run to run, and the smallest p the design can attain (2^-n).
uv run thesis analysis variance results/experiments/phase-b/<bundle>

# Recompute the paired verdict from the bundle's own runs (--write updates the
# artifacts; the runner's verdict is written once and can go stale against a fix).
uv run thesis experiment analyze results/experiments/phase-b/<bundle> --json
```

A series of stages is a command too, rather than a shell loop beside the repo:

```bash
uv run thesis experiment series \
  --stage h2-pair:pairs=5 --stage s4-point-sizing --stage baselines:runs=5 \
  --json
```

It retries a failed stage once, stops the chain when a stage fails every attempt, and
pauses the work-tree indexer for the whole window, restoring it even if a stage dies.

Older invocations remain available for ad-hoc work:

```bash
# Full 4-scenario experiment
uv run thesis-experiment run --controller v3 --runs 5 \
  --scenarios s1-k8s-only,s2-serverless-only,s3-hybrid-reactive,s4-hybrid-predictive

# Cost analysis (post-hoc, on experiment results)
uv run thesis analysis cost --experiment-dir results/experiments/phase-b/<experiment-folder>
uv run thesis analysis reanalyze --results-dir results/experiments/phase-b/<experiment-folder>
```

---

## Code Quality — Mandatory

Every change MUST pass `ruff` and `ty` before it is considered done. Config lives in `pyproject.toml` (`[tool.ruff]` — target py312, line-length 120, excludes `archived/.venv/results`). Run from repo root:

```bash
uv run ruff check            # lint — MUST be 0 errors
uv run ruff format           # format in place
uv run ruff format --check   # CI / hook verification
uv run ty check              # type-check — do not add NEW errors
```

* Baseline: `ruff check` and `ty check` are both clean. `archived/` is excluded from every tool (`pyproject.toml` `[tool.ty.src]`, ruff's `extend-exclude`, pytest's `norecursedirs`): it is a frozen pre-refactor snapshot, so its diagnostics are history rather than work.
* Enforcement: a `prek` git hook (`.pre-commit-config.yaml`) runs `ruff check`, `ruff format --check` and `ty check` on commit. Install once after cloning: `uv run prek install`.
* Import boundaries are enforced by `lint-imports` contracts in `pyproject.toml` (`[tool.importlinter]`), asserted by `libs/shared/tests/test_architecture.py` so the normal test run catches a boundary crossed. The protected contract bounds *importers* of `shared.artifacts`; it cannot see a module that opens the files directly, and `apps/dashboard/dashboard/loader.py` still does (deferred work, listed in the refactor design).
* `prek` is a Rust drop-in for `pre-commit`, added as a dev dependency; `uv sync` installs it. Docs: https://prek.j178.dev

---

## Storage Format Strategy

| Data type | Format | Why |
|-----------|--------|-----|
| Per-run tabular results (latency, throughput) | **CSV** | Git-friendly, line-per-record, pandas-native |
| Structured event logs (daemon decisions) | **JSONL** | Append-only, one-line-per-event diffs |
| Experiment metadata | **YAML** | Human-authored, already used for meta.yaml |
| Summary reports | **Markdown** | Already used for report.md |
| Time-series exports | **CSV** | Compact, diffable |
| Model artifacts | **Gitignored** | Large binaries, referenced by path |

---

## Results Bundle Convention

Every experiment is a self-contained folder under `results/experiments/`. New experiments use schema v2 (see `results/AGENTS.md` for the full specification); existing bundles remain in the legacy direct-child layout and are read by registry/catalog adapters.

```
results/experiments/<phase>/<YYYY-MM-DD_slug>/
  meta.yaml                       # YAML — experiment metadata (bundle_schema_version: 2)
  report.md                       # Markdown — sole interpretation
  events.jsonl                    # JSONL — immutable bundle-level lifecycle events
  derived/
    paired_analysis.json           # Computed statistical analysis
  raw/<scenario>_run<N>/
    manifest.json                  # Per-run reproducibility snapshot
    events.jsonl                   # JSONL — immutable per-run lifecycle events
    result.json                    # Typed ExperimentResult with TreatmentFidelity
    daemon.log                     # Raw diagnostic text log
    k6-summary.json                # k6 summary
    metrics.parquet                # Parquet — time-series (Git LFS)
    prediction-actual.parquet      # Parquet — GRU forecast vs actual (Git LFS)
    system-events.parquet          # Parquet — normalized daemon events (Git LFS)
```

**Evidence workflow:** `uv run thesis experiment evidence audit` → `reconcile --apply` → `catalog refresh` → `journal --limit 20`. See `results/evidence/README.md` and `results/evidence/BACKLOG.md` for deferred evidence work.

**S4 treatment-fidelity gate:** S4 runs require GRU preflight + 100% prediction delivery on all eligible cycles. A run with `treatment_fidelity.delivered=False` is invalid and excluded from paired analysis.
## Repository Invariants

### 1. Single Source of Truth
- All experiment evidence lives in `results/` only
- `thesis/` is narrative — links to `results/` for evidence
- One report per experiment — no duplicate summaries

### 2. Package Boundaries
- `libs/shared` imports nothing from `libs/` or `apps/` — it is the floor
- `libs/analysis` and `libs/infra` depend on `shared` only
- `apps/` packages may import from `libs/`; `libs/` never imports from `apps/`
- Inter-module communication via HTTP (services) or Protocols (in-process)
- The importer side is enforced by `lint-imports` contracts in `pyproject.toml` and asserted by `libs/shared/tests/test_architecture.py` in the normal test run

### 3. Artifact Hygiene
- No empty placeholder directories
- No large binaries in git (models, datasets — gitignored)
- `.gitignore` covers: `*.log`, `__pycache__/`, `.venv/`, `*.pyc`

### 4. Module Direction — where new code goes
| Kind of code | Owner | Rule |
|---|---|---|
| A model, protocol, statistic, storage or artifact reader | `libs/shared/shared/` | Put it here when two packages need it; a helper only one package uses stays in that package |
| Cluster lifecycle, readiness, residue, deploys, Prometheus config | `libs/infra/infra/`, one domain directory each | Apps reach it through the `thesis infra` CLI or a Protocol, not by importing internals |
| Reusable analysis: loaders, comparison, cost, cold start, the bundle views | `libs/analysis/analysis/` | Depends on `shared` only; `apps/analysis` is a thin CLI over it |
| A new experiment stage | `apps/experiment/experiment/stages/` | One file per stage, typed against `stages/base.py` |
| A new condition the testbed must meet | `apps/experiment/experiment/conditions.py` | One `RunConditions` field and one check in `apply`; every path funnels through it, so `preflight` and the runner both get it |
| A new named run recipe | `apps/experiment/experiment/profiles.py` | Declare scenarios, design, static agents, whether a predictor is needed, controller environment |
| A new `thesis` command | The app that owns the behaviour | Register it in `apps/cli/cli/main.py`; the command body calls the package, it does not reimplement it |
| A test | Beside its package (`apps/*/tests`, `libs/*/tests`) | Hermetic by default; a test that touches a live cluster is marked `live` and stays out of the default run |

### 5. Agent-Facing Output — the CLI contract
Every command may be read by a person or by a program, and both are designed for:
- **`--json` prints one line** (`shared.output.json_line`). The indented form costs 27–40% more tokens on this repository's own payloads and buys a parser nothing; `| jq .` is the readable version.
- **Never a `rich` console for machine output** — it soft-wraps at the terminal width and corrupts a payload mid-token. Use `print`/`typer.echo`, or `soft_wrap=True` where rich is unavoidable.
- **Lists default to four columns.** The rest are one `--fields` away (`--fields all` for everything); an unknown field names the valid ones and exits 2.
- **Long text is truncated with its length and a `--full` escape**, never silently cut.
- **An empty result says so** (`0 run(s)`, "no governance events recorded") — silence is indistinguishable from failure.
- **A command that answers a question prints `next:` lines** naming the command that follows, with real paths (`shared.output.print_next`).
- **`thesis` with no arguments prints live state** — path, testbed, predictor, latest bundle — not help text.
- `apps/cli/tests/test_docs_commands.py` fails when a command documented in the docs stops existing.

### 6. Documentation — where it lives, and what a change owes it
- **Package behaviour:** the nearest `AGENTS.md`. Root first, then `apps/<package>/` or `libs/<package>/`. Every package doc states its module map, module direction, tests and tiers, the commands it contributes, and its own invariants — that is what makes a stale claim visible.
- **Running an experiment:** `docs/experiments/RUNNING_EXPERIMENTS.md`. Protocol and method: `docs/thesis-implementation/`. Evidence and bundle rules: `results/AGENTS.md`.
- **Superseded docs move to `archived/docs-historical/`** with a banner saying what replaced them. A document describing a world that no longer exists is not left in place.
- **Change a command, a module's home, or a test tier and its doc is part of the change.** Two checks catch the drift: `apps/cli/tests/test_docs_commands.py` (every documented command resolves) and `apps/experiment/tests/test_profiles.py` (a profile that cannot run cannot ship).

---

## References & Cited Papers — Archive Rule

Every paper, dataset, or external work cited or relied upon MUST be archived locally so it is reusable and traceable — link rot is not an excuse for a missing source.

* **Location**: `docs/references/` (PDF is the canonical archive format).
* **Naming**: `<slug>-<short-title>-<year>.pdf` — lowercase, hyphenated, year-suffixed. Example: `aapa-archetype-aware-predictive-autoscaler-2025.pdf`.
* **Manifest**: every archived paper gets a row in `docs/references/REFERENCES.md` with columns `Paper | File | arxiv/DOI | Key Insight`. No PDF lands in the folder without a manifest row; no manifest row without its PDF.
* **Binary storage**: ALL PDFs under `docs/references/` are tracked via **Git LFS** (rule lives in `.gitattributes`). Run `git lfs install` once per clone. Do not commit a PDF > 100 MB without LFS.
* If a paper is only available behind a paywall, archive the arXiv preprint and record the published DOI in the manifest.

---

## Hardware Constraints

- **Full Development**: 8+ cores, 32GB RAM
- **AMD GPU**: Set `HSA_OVERRIDE_GFX_VERSION=11.0.0` for ROCm
- **Python**: 3.12 (pinned across all workspace members)

