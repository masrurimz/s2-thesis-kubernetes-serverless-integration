# Documentation

What each document is for. New to the repository? Read the [README](../README.md) first, then run the [quick start](getting-started/02-quick-start.md).

Every entry names its mode, so you know what you are opening: a **tutorial** teaches by doing, a **how-to** solves one task, a **reference** states facts, an **explanation** gives the why.

## Getting started

| Document | Mode | What it is for |
|---|---|---|
| [Overview](getting-started/00-overview.md) | Explanation | The research question, the final configuration, and what is measured |
| [Prerequisites](getting-started/01-prerequisites.md) | Reference | Tool versions, hardware, and installation for the testbed |
| [Quick start](getting-started/02-quick-start.md) | Tutorial | Bring the testbed up, run one smoke pair, read the bundle |
| [Understanding the architecture](getting-started/03-understanding-architecture.md) | Explanation | The control loop, Algorithm 1 and 2, calibration, runtime topology |

## Running experiments

| Document | Mode | What it is for |
|---|---|---|
| [Experiment runbook](experiments/RUNNING_EXPERIMENTS.md) | How-to | Profiles, series, evidence commands, run conditions, validity gates, troubleshooting |
| [Experiment plan](thesis-implementation/01-experiment-plan.md) | Explanation | The design: hypotheses, scenarios, paired counterbalancing, sampling |
| [Methodology and implementation](thesis-implementation/02-methodology-implementation.md) | Explanation | How each stage is implemented and why |
| [Running experiments](thesis-implementation/03-running-experiments.md) | How-to | The protocol walkthrough per phase |
| [Real-time validation](REALTIME_VALIDATION_GUIDE.md) | How-to | The H3 check and the live H1 and H2 runs |

## Specifications and operations

| Document | Mode | What it is for |
|---|---|---|
| [Algorithm 1 specification](specs/algorithm-1-spec.md) | Reference | States, priority order, thresholds, weight rules |
| [SLO definition](specs/slo-definition.md) | Reference | What the SLO is and how it is measured |
| [Calibration guide](CALIBRATION_GUIDE.md) | Reference | Every controller constant and where it comes from |
| [S4 integration guide](S4_INTEGRATION_GUIDE.md) | Reference | How the GRU service and the daemon fit together |
| [Deployment](deployment/VPS_DEPLOYMENT.md) | How-to | Deploying to a VPS, with helpers in `deployment/scripts/` |

## Evidence and results

| Document | Mode | What it is for |
|---|---|---|
| [`results/README.md`](../results/README.md) | Reference | The evidence tree and the bundle schema |
| [`results/claims/CLAIMS_TO_EVIDENCE.md`](../results/claims/CLAIMS_TO_EVIDENCE.md) | Reference | Every thesis claim, and the bundle that supports it |
| [`results/claims/FINAL_NUMBERS.md`](../results/claims/FINAL_NUMBERS.md) | Reference | The numbers that may appear in the thesis, with framing rules |
| [`results/claims/INCONSISTENCIES.md`](../results/claims/INCONSISTENCIES.md) | Reference | Known contradictions and superseded evidence |
| [Experiment results log](EXPERIMENT_RESULTS.md) | Explanation | Historical results narrative, superseded where the claims map says so |

## Thesis and references

| Document | Mode | What it is for |
|---|---|---|
| [`thesis-typst/`](../thesis-typst/) | Explanation | The canonical thesis book |
| [`thesis/chapters/`](../thesis/chapters/) | Explanation | The markdown draft |
| [References](references/REFERENCES.md) | Reference | Archived cited papers; the PDFs are Git LFS objects |
| [Plans](plans/) | Explanation | Dated implementation plans, including the [2026-09-10 GRU leak-free retrain](plans/2026-09-10-gru-leakfree-retrain.md) |

## Historical

| Document | What it is for |
|---|---|
| [`archived/docs-historical/`](../archived/docs-historical/) | Superseded setup guides, the pre-refactor codebase inventory, and the implementation cross-check. Each file carries a banner naming its replacement |
| [Archived methodology](archived/experimental-methodology.md) | Early protocol, not current |
| [Initial hybrid plan](archived/initial-hybrid-plan.md) | Early plan, not current |
| [STRATEGIC-PLAN.md](STRATEGIC-PLAN.md) | Early planning artifact; current claims follow the claims map |

## Conventions

- Conventions for agents and contributors: [`AGENTS.md`](../AGENTS.md), with a package-level `AGENTS.md` in every workspace package.
- Test tiers: `uv run python -m pytest` runs the hermetic tier; `uv run python -m pytest -m live` runs the tests that touch real clusters.
- Commands in these documents are checked: `apps/cli/tests/test_docs_commands.py` fails when a documented command no longer exists.
