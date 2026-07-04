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
| `libs/clients/` | **Infrastructure clients** — Prometheus, HAProxy, k8s, k6 Python clients | Shared by routing and experiment packages |
| `apps/prediction/` | **GRU prediction service** — FastAPI server, model loader, training | Deployable service (port 8090) |
| `apps/routing/` | **Routing daemon** — Algorithm 1 V1/V2, SLO monitor, scaling | Deployable service (port 9104) |
| `apps/experiment/` | **Experiment orchestration** — composable pipeline stages | CLI tool for running experiments |
| `apps/cli/` | **Unified CLI** — `thesis` command aggregating all subcommands | Entry point: `uv run thesis` |
| `results/` | **Single source of truth for ALL experiment evidence** | If it's experiment output, it lives here |
| `thesis/` | **Narrative only** — thesis text, protocol, appendices | Links INTO `results/` for evidence |
| `data/` | Datasets (ClarkNet, Calgary traces, synthetic) | Large files tracked via `.gitattributes` |
| `deploy/` | k3d configs, HAProxy, load testing, cluster setup scripts | Deployment configs and ops tooling |
| `docs/` | Setup guides, specs, architecture docs | Points to `results/` for evidence |
| `archived/` | Legacy sprint artifacts, deprecated code | **Read-only. Never add new work here.** |

**Package-level AGENTS.md files** exist in every `libs/` and `apps/` package. Read the nearest one before editing files in that directory.

---

## Module Dependency Graph

```
libs/shared              (no internal deps; pydantic, structlog)
  ↑
  ├── libs/clients       (depends on shared; requests)
  │     ↑
  │     ├── apps/prediction   (depends on shared; fastapi, torch, numpy)
  │     ├── apps/routing      (depends on shared, clients; fastapi, prometheus-client)
  │     └── apps/experiment   (depends on shared, clients; scipy, rich, typer)
  │
  └── apps/cli           (depends on shared; typer, rich; lazily imports other apps)
```

No circular dependencies. `libs/` never imports from `apps/`.

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

```bash
HSA_OVERRIDE_GFX_VERSION=11.0.0 \
  uv run thesis experiment run --phase full --runs 5 --duration 300
```

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

Every experiment is a self-contained folder under `results/experiments/`:

```
results/experiments/<phase>/<YYYY-MM-DD_slug>/
  meta.yaml                       # YAML — experiment metadata
  report.md                       # Markdown — interpretation
  raw/<scenario>_run<N>/
    k6_summary.csv                # CSV — k6 metrics
    prometheus.csv                # CSV — time-series
    daemon_events.jsonl           # JSONL — decision log
    resource.csv                  # CSV — CPU/memory
  processed/
    aggregate.csv                 # CSV — per-scenario summary
    comparisons.csv               # CSV — statistical comparisons
  figures/*.png
```

---

## Repository Invariants

### 1. Single Source of Truth
- All experiment evidence lives in `results/` only
- `thesis/` is narrative — links to `results/` for evidence
- One report per experiment — no duplicate summaries

### 2. Package Boundaries
- `libs/shared` never imports from `apps/` or `libs/clients/`
- `libs/clients` depends on `shared` only
- `apps/` packages can import from `libs/`
- Inter-module communication via HTTP (services) or Protocols (in-process)

### 3. Artifact Hygiene
- No empty placeholder directories
- No large binaries in git (models, datasets — gitignored)
- `.gitignore` covers: `*.log`, `__pycache__/`, `.venv/`, `*.pyc`

---

## Hardware Constraints

- **Full Development**: 8+ cores, 32GB RAM
- **AMD GPU**: Set `HSA_OVERRIDE_GFX_VERSION=11.0.0` for ROCm
- **Python**: 3.12 (pinned across all workspace members)

---

## Issue Tracking

This project uses **bd (beads)** for issue tracking.

```bash
bd prime          # Workflow context
bd ready          # Find unblocked work
bd create "Title" --type task --priority 2
bd close <id>
```
