# apps/experiment — Experiment Orchestration

## What This Is

Experiment runner using composable pipeline stages. Decomposes the former 2164-line monolith (`scripts/run_phase_b_experiments.py`) into independently testable stages.

## Pipeline Architecture

```
plan → preflight → reset → daemon → workload → collect → analyze → report
```

Each stage implements the `Stage` Protocol:
- `name: str`
- `execute(ctx: PipelineContext) → StageResult`
- `dry_run(ctx: PipelineContext) → StageResult`

Stages read from and write to a shared `PipelineContext`. Pipeline fails fast if any stage fails.

## Module Map

| Module | Purpose |
|--------|---------|
| `pipeline.py` | `Pipeline` — orchestrator that threads context through stages |
| `cli.py` | Typer app: `run`, `analyze`, `preflight`, `validate` |
| `stages/base.py` | `Stage` Protocol + `BaseStage` abstract class |
| `stages/plan.py` | `PlanStage` — run order, seeds, batch manifest |
| `stages/preflight.py` | `PreflightStage` — infrastructure readiness checks |
| `stages/reset.py` | `ResetStage` — per-run scenario reset |
| `stages/daemon.py` | `DaemonStage` — daemon process lifecycle |
| `stages/workload.py` | `WorkloadStage` — k6 ClarkNet trace replay |
| `stages/collect.py` | `CollectStage` — Prometheus metrics + resource polling |
| `stages/analyze.py` | `AnalyzeStage` — Welch, Mann-Whitney, bootstrap CI, Cohen's d |
| `stages/report.py` | `ReportStage` — Markdown report generation |
| `infrastructure/node_provisioner.py` | `NodeProvisioner` — k3d node cordon/uncordon |
| `clients/daemon.py` | Typed daemon HTTP client |

## Commands

```bash
uv run thesis-experiment run --phase full --runs 5 --duration 300
uv run thesis-experiment preflight
uv run thesis-experiment run --phase calibration --runs 1 --dry-run
uv run thesis-experiment analyze --results-file results/experiments/phase-b/.../results.csv
```

## Result Storage

- Tabular results → CSV (git-friendly, line-per-record)
- Event logs → JSONL (append-only, one-line-per-event)
- Metadata → YAML (meta.yaml)
- Reports → Markdown

## Dependencies

- `shared` (models, pipeline contracts)
- `infra` (Prometheus, k6, k8s clients)
- scipy, rich, typer
