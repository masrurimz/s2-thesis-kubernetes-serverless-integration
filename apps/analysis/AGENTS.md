# apps/analysis — Experiment Analysis CLI

## What This Is

Typer sub-app exposing the post-hoc analysis / visualization scripts that used
to live as standalone files under `apps/scripts/scripts/`. Each command is a
thin orchestration layer that delegates reusable logic to `libs/analysis`
(domain) and `libs/shared` (stats primitives, scenario constants) and
reproduces the original script's stdout + file output.

Registered as `thesis analysis <subcommand>` via `apps/cli/cli/main.py`.

## Run

```bash
uv run thesis analysis --help                       # list all subcommands
uv run thesis analysis robust-stats                 # Welch + MW + bootstrap
uv run thesis analysis reanalyze --results-dir results/experiments/phase-b/2026-02-15_clarknet-replay
uv run thesis analysis cost --experiment-dir results/experiments/phase-b/2026-02-16_validation-metrics-fixes
uv run thesis analysis cold-start
uv run thesis analysis hypotheses
uv run thesis analysis plots
uv run thesis analysis timeseries
uv run thesis analysis gru-metrics
```

## Package Layout

| Module | Responsibility | Source script |
|--------|----------------|---------------|
| `cli.py` | Typer sub-app + 8 `@app.command()` functions | (orchestration) |
| `plots.py` | matplotlib figure builders (decision timeline, boxplots, dashboard) | `generate_plots.py` |
| `timeseries.py` | Phase B time-series plots (scenario summary, decisions, outlier impact) | `plot_phase_b_timeseries.py` |
| `hypotheses.py` | `HypothesisValidator` + `HypothesisResult` + `ScenarioMetrics` (thesis glue w/ hardcoded historical data; imports `prediction.model_loader`) | `validate_all_hypotheses.py` |
| `gru_metrics.py` | GRU MAE% / MAPE from training metrics | `compute_gru_percentage_metrics.py` |
| `crossover.py` | S1-vs-S2 cost-crossover helpers + multi-cloud (GCP/CF) projection constants | `cost_analyzer.py` |

## Conventions

- **No domain logic here** — every command delegates to `analysis.*`
  (the `libs/analysis` domain lib) / `shared.*`. This package only wires CLI
  args, prints output, and writes result files. The only inline code is
  thesis-specific glue that has no reusable home (`HypothesisValidator`
  historical data; crossover graph math).
- **Import root is `analysis_cli`** — the package dir is `analysis_cli/` (not
  `analysis/`) to avoid colliding with `libs/analysis`, which already owns the
  `analysis.*` import root. Distribution name is `analysis-cli`; app-internal
  helpers import as `analysis_cli.plots`, `analysis_cli.crossover`, etc., while
  domain calls stay `analysis.comparison`, `analysis.cost`.
- **matplotlib isolated here** — like `apps/dashboard` isolates
  streamlit/plotly, matplotlib lives in this package's `pyproject.toml`, not
  in root.
- **Constants imported from `shared.scenarios`** — never redefine
  `SCENARIO_LABELS` / `SCENARIO_COLORS` / `SCENARIO_ORDER` / `SLO_THRESHOLD_MS`.
- **Lazy registration** — added via `_register_analysis()` in
  `apps/cli/cli/main.py`, silently skipped on `ImportError` (same pattern as
  `_register_dashboard()`).
