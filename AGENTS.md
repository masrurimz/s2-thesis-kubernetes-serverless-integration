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
| `results/` | **Single source of truth for ALL experiment evidence** — raw data, processed outputs, figures, claims, reports | If it's experiment output, it lives here. Nowhere else. |
| `results/claims/` | Claims-to-evidence mapping + inconsistency tracking | Every thesis claim must trace to raw data here |
| `results/experiments/` | Experiment bundles (one folder per experiment run/batch) | Each bundle: `meta.yaml` + `raw/` + `report.md` |
| `results/models/` | ML model training results | Same bundle convention |
| `results/cost/` | Cost analysis results | Same bundle convention |
| `thesis/` | **Narrative only** — thesis text, protocol, appendices | Links INTO `results/` for evidence. Never stores raw data. No scripts. |
| `thesis/protocol/` | Preregistered experiment design + threats to validity | Update only to document new limitations |
| `controller/` | Active Python system (workspace member): prediction, routing, daemon, monitoring, ML models | `uv sync` from repo root |
| `controller/prediction/` | GRU serving + training + baselines (merged from `ml_models/`) | ML code lives here, not in a separate top-level dir |
| `scripts/` | Canonical reproduction + analysis scripts (experiment runners, statistics, plotting) | Run from repo root: `uv run python scripts/<name>.py` |
| `data/` | Datasets (ClarkNet, Calgary traces, synthetic) | Large files tracked via `.gitattributes` |
| `infrastructure/` | k3d configs, HAProxy, load testing | Deployment configs |
| `infrastructure/load-tests/` | k6 load test suite (canonical/calibration/legacy subdirs) | See `load-tests/README.md` for manifest |
| `docs/` | Current docs: setup guides, specs, deployment | Points to `results/` for evidence |
| `archived/` | Curated historical context (experiments-framework, legacy docs) | **Read-only. Never add new work here.** |
**Package-level AGENTS.md files** exist in `controller/`, `scripts/`, `infrastructure/`, and `data/`. Read the nearest one before editing files in that directory.

**Key documents to read first:**
- `results/README.md` — Evidence registry and experiment index
- `results/claims/CLAIMS_TO_EVIDENCE.md` — Every claim mapped to raw data
- `results/claims/INCONSISTENCIES.md` — Tracked inconsistencies
- `thesis/protocol/THREATS_TO_VALIDITY.md` — Known limitations

---

## Results Structure (Experiment Bundle Convention)

Every experiment is a **self-contained folder** under `results/experiments/`, `results/models/`, or `results/cost/`. This is the core organizational pattern.

### Bundle Structure

```
results/experiments/<phase>/<YYYY-MM-DD_short-slug>/
  meta.yaml       # REQUIRED: id, date, scenarios, workload, claims, reproduce, status
  raw/            # REQUIRED: unmodified experiment outputs (JSON, CSV, logs)
  processed/      # OPTIONAL: aggregated tables, statistics
  figures/        # OPTIONAL: generated plots
  report.md       # REQUIRED: one interpretation doc per experiment (no spin)
```

### meta.yaml Required Fields

```yaml
id: phase-b.replicated.2026-02-12      # Unique, never changes
date: 2026-02-12                        # When experiment ran
phase: phase-b                          # Which thesis phase
scenarios: [s1-k8s-only, s4-hybrid-predictive]  # Which scenarios
workload: {rps: 100, duration_sec: 300} # Load parameters
claims: {supports: [H1, H2]}           # Which hypotheses this relates to
reproduce: ["uv run python ..."]        # Exact reproduction command(s)
status: complete                        # complete | partial | failed
```

### Adding a New Experiment

1. Create folder: `results/experiments/<phase>/<YYYY-MM-DD_slug>/`
2. Add `meta.yaml` + `raw/` data + `report.md`
3. Add row to registry table in `results/README.md`
4. Update `results/claims/CLAIMS_TO_EVIDENCE.md` if it supports a thesis claim
5. That's it. No other files to edit.

---

## Repository Invariants

### 1. Single Source of Truth

- **All experiment evidence lives in `results/` only.** No raw data, reports, or summaries in `thesis/`, `docs/`, `controller/results/`, or anywhere else.
- **`thesis/` is narrative.** It links to `results/` paths for evidence. It never stores data.
- **One report per experiment.** Each experiment bundle has exactly one `report.md`. Don't create parallel summaries elsewhere.
- **Before creating a new doc, search for an existing one.** Update in-place; don't create a parallel version.

### 2. Evidence Integrity

- **No summary claims without evidence mapping.** Any statement containing "validated", "significant", "outperforms", or "all hypotheses" MUST be backed by a corresponding entry in `results/claims/CLAIMS_TO_EVIDENCE.md` with raw-data path + reproduction command.
- **Distinguish mechanism validation from performance superiority.** This project validates mechanisms (✅) but could not demonstrate performance superiority due to environment constraints (⚠️). Never conflate these.
- **If evidence conflicts, log it.** Add entry to `results/claims/INCONSISTENCIES.md` and correct the claim. Don't silently fix.
- **Claims language**: Use "mechanism validated" (correct) not "hypothesis proven" (overclaim).

### 3. Artifact Hygiene

- **No empty placeholder directories.** Don't create dirs without content. No `.keep` or `.gitkeep` files.
- **No large binaries in git** unless explicitly whitelisted in `.gitattributes`. Models (`.pt`), large datasets, PDFs — prefer generated artifacts + pointer stubs.
- **No ephemeral outputs in git.** Logs, `/tmp/` files, daemon outputs → excerpt relevant parts into reports, don't commit raw.
- **`.gitignore` must cover**: `*.log`, `__pycache__/`, `.venv/`, `/tmp/`, `*.pyc`, large generated outputs.
- **No duplicate reports.** If you find yourself writing a second summary of the same experiment, you're doing it wrong. Update the existing `report.md` in the experiment bundle.

### 4. Results Flow

1. Run experiment → script outputs to `controller/results/` or similar working dir
2. Create experiment bundle folder under `results/experiments/<phase>/`
3. Move raw outputs into `raw/`, write `meta.yaml` and `report.md`
4. Update `results/claims/CLAIMS_TO_EVIDENCE.md` with path + reproduction command
5. If discrepancy found → update `results/claims/INCONSISTENCIES.md`
6. Never skip steps 4-5

### Lesson Learned: What Went Wrong Before

> Previous structure used `thesis/results/` as canonical + `results/` as working space + `thesis/appendices/` for reports. This caused:
> - 15+ duplicate .md files saying the same thing differently
> - Real per-run data hidden in `controller/results/phase_b/` never promoted
> - Old stress test data mislabeled as Phase B results in `thesis/results/raw/phase_b/`
> - Reports contradicting each other (one said "ALL HYPOTHESES VALIDATED", another said "not significant")
> - Nobody could answer "what data do we actually have?" without reading every file
>
> **The fix:** One canonical location (`results/`), one doc per experiment (bundle convention), no narrative in evidence directories.

---

## Development Commands

### Controller (uv workspace — run from repo root)

```bash
uv sync                                                    # Install all deps (workspace)
uv run python -m prediction.prediction_server &            # Start prediction API
uv run python -m daemon.routing_daemon --scenario s4 &     # Start routing daemon
uv run python -m pytest controller/tests/                  # Run tests
```

### Infrastructure

```bash
k3d cluster create demo-hybrid --agents 1 --port "8080:80@loadbalancer"
kubectl create deployment test-app --image=nginx:alpine
kubectl expose deployment test-app --port=80 --target-port=80
```

### Reproduction (see `scripts/README.md` for full details)

```bash
HSA_OVERRIDE_GFX_VERSION=11.0.0 \
  uv run python scripts/run_phase_b_experiments.py --phase full --runs 5 --duration 300
```

---

## Issue Tracking

This project uses **bd (beads)** for issue tracking.

```bash
bd prime          # Workflow context
bd ready          # Find unblocked work
bd create "Title" --type task --priority 2   # Create issue
bd close <id>     # Complete work
bd sync           # Sync with git (run at session end)
```

---

## LLM Workflow Standards

### Core Principles

- **Terse, expert-level communication.** Lead with solution.
- **Burst + validate cycles.** Implementation → human testing → feedback → next burst.
- **Surgical edits only.** Don't touch unrelated files. Match existing patterns.

### Task Management

- `bd` for multi-session work with dependencies
- `TodoWrite` for single-session linear tasks
- Estimate in execution blocks (15-30 min), not hours/days

### Git Workflow

- Commit at logical checkpoints: `feat:`, `fix:`, `refactor:`, `chore:` prefix
- Do not squash — user squashes later
- Never push unless explicitly told to

### What NOT to Do

- ❌ Create duplicate reports/docs (search first, update in-place)
- ❌ Commit large binaries without `.gitattributes` entry
- ❌ Make summary claims without evidence mapping
- ❌ Add files to `archived/` (it's read-only legacy)
- ❌ Create empty placeholder directories
- ❌ Push to remote unless told to
- ❌ Deploy unless told to

---

## Hardware Constraints

- **Full Development**: 8+ cores, 32GB RAM
- **Resource-Constrained Testing**: 4+ cores, 8GB RAM (6GB usable)
- **AMD GPU**: Set `HSA_OVERRIDE_GFX_VERSION=11.0.0` for ROCm

---

## Session Completion

When ending a work session:

1. File issues for remaining work (`bd create`)
2. Run quality gates if code changed (`uv run -m pytest`)
3. Update issue status (`bd close`, `bd update`)
4. Push: `git pull --rebase && bd sync && git push`
5. Verify: `git status` shows up-to-date with origin

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:7510c1e2 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->
