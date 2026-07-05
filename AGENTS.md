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

## Code Quality — Mandatory

Every change MUST pass `ruff` and `ty` before it is considered done. Config lives in `pyproject.toml` (`[tool.ruff]` — target py312, line-length 120, excludes `archived/.venv/results`). Run from repo root:

```bash
uv run ruff check            # lint — MUST be 0 errors
uv run ruff format           # format in place
uv run ruff format --check   # CI / hook verification
uv run ty check              # type-check — do not add NEW errors
```

* Baseline: `ruff check` is clean; `ty check` reports ~80 pre-existing diagnostics, almost all in `archived/` legacy code. Do not regress `ty`'s count; fix any `ty` error in code you touch.
* Enforcement: a `prek` git hook (`.pre-commit-config.yaml`) runs `ruff check` and `ruff format --check` automatically on commit. Install once after cloning: `uv run prek install`.
* `ty check` is wired as a **manual-stage** hook — it does NOT block commits (the `archived/` diagnostics otherwise would). Run it manually for type-sensitive changes: `uv run prek run --hook-stage manual ty-check`.
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

