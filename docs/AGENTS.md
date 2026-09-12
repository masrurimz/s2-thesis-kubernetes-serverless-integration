# docs/ — Documentation Index

## What This Is

Current documentation: setup guides, specs, deployment, references. Points to `results/` for experiment evidence.

## Document Map

| Document | Purpose |
|----------|---------|
| `README.md` | Main doc index with research overview and evaluation snapshot |
| `getting-started/` | Step-by-step entry: overview, prerequisites, quick start, architecture |
| `experiments/RUNNING_EXPERIMENTS.md` | Current experiment runbook |
| `thesis-implementation/` | Experiment plan, methodology, running experiments |
| `specs/` | Technical specs: Algorithm 1 (`algorithm-1-spec.md`), SLO definition (`slo-definition.md`) |
| `CALIBRATION_GUIDE.md` | Workload calibration for experiments |
| `S4_INTEGRATION_GUIDE.md` | Wiring the GRU predictor into the S4 controller |
| `REALTIME_VALIDATION_GUIDE.md` | Real-time hypothesis validation (H3 GRU check) |
| `deployment/VPS_DEPLOYMENT.md` | VPS deployment guide (helpers in `deployment/scripts/`) |
| `plans/` | Dated implementation plans |
| `references/` | Cited papers, PDF via Git LFS, manifest in `references/REFERENCES.md` |
| `archived/` | Historical methodology docs |
| `../archived/docs-historical/` | Superseded setup guides and inventories, with banners |

The architecture walkthrough is `getting-started/03-understanding-architecture.md`. For module-level architecture, read the root `AGENTS.md` repository map and the per-package `AGENTS.md` under `libs/` and `apps/`.

## Rules

* Docs link INTO `results/` for evidence — never store raw data here
* Before creating a new doc, search for existing ones
* Update in-place — don't create parallel versions
* `references/` — cited papers (PDF via Git LFS). Every PDF needs a row in `references/REFERENCES.md` with `Paper | File | arxiv/DOI | Key Insight`; name files `<slug>-<title>-<year>.pdf`. See root `AGENTS.md` → "References & Cited Papers"
