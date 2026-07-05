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
| `apps/prediction/` | **GRU prediction service** — FastAPI server, model loader, training | Deployable service (port 8090) |
| `apps/routing/` | **Routing daemon** — V1/V2/V3 controllers (Algorithm 1), Algorithm 2 (ClusterController), daemon, SLO monitor, weight adjuster | Deployable service (port 9104) |
| `apps/experiment/` | **Experiment orchestration** — pipeline stages, CLI, NodeProvisioner, cost analyzer | CLI tool for running experiments |
| `apps/scripts/` | **Analysis tools** — cost analyzer, statistical analysis | CLI tools for post-experiment analysis |
| `results/` | **Single source of truth for ALL experiment evidence** | If it's experiment output, it lives here |
| `thesis/` | **Narrative only** — thesis text, protocol, appendices | Links INTO `results/` for evidence |
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
  │     └── apps/experiment   (pipeline stages, CLI, NodeProvisioner, cost analyzer)
  │
  └── apps/scripts        (cost analyzer, analysis — depends on shared, experiment)
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

```bash
# Full 4-scenario experiment
uv run thesis-experiment run --controller v3 --runs 5 \
  --scenarios s1-k8s-only,s2-serverless-only,s3-hybrid-reactive,s4-hybrid-predictive

# Cost analysis
uv run python apps/scripts/scripts/cost_analyzer.py \
  --experiment-dir results/experiments/phase-b/<experiment-folder>
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

