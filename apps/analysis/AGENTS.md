# apps/analysis

Typer sub-app exposing post-hoc analysis and visualization as `thesis analysis <command>`. Each command is a thin orchestration layer that delegates reusable logic to `libs/analysis` (domain) and `libs/shared` (stats primitives, scenario constants).

## Module map

| Path | Responsibility |
|---|---|
| `analysis_cli/cli.py` | Typer sub-app with all 12 commands (list under Commands); `runs`/`mechanism`/`variance` delegate to `analysis.bundle_evidence` (libs/analysis) |
| `analysis_cli/plots.py` | matplotlib figure builders (decision timeline, boxplots, dashboard) |
| `analysis_cli/timeseries.py` | Phase B time-series plots (scenario summary, decisions, outlier impact) |
| `analysis_cli/hypotheses.py` | `validate_all()`: H1/H2/H3 validation glue with hardcoded historical data; imports `prediction.model_loader` |
| `analysis_cli/gru_metrics.py` | GRU MAE%/MAPE from training metrics |
| `analysis_cli/crossover.py` | S1-vs-S2 cost-crossover helpers + multi-cloud (GCP/CF) projection constants |
| `analysis_cli/thesis_figures.py` | H2 forest plot for the thesis book; run as `uv run python -m analysis_cli.thesis_figures`, not a typer command |

## Module direction

- **May import:** `analysis` (the libs/analysis domain library), `shared` (stats, scenarios, artifacts), and `prediction` (`model_loader` in `hypotheses.py`). Plus typer, rich, matplotlib.
- **Must never import:** `experiment`, `routing`, `dashboard`, `cli` (same or higher layer).
- **Where new code goes:**
  - New CLI command → `analysis_cli/cli.py` as a thin handler; the domain logic it calls belongs in `libs/analysis`
  - Thesis-specific glue with no reusable home → a sibling module in `analysis_cli/` (the pattern of `hypotheses.py`, `crossover.py`)
  - New matplotlib figure builder → `analysis_cli/plots.py` or `analysis_cli/timeseries.py`

## Tests

`apps/analysis/tests/` holds the CLI-surface tier: `test_evidence_tables.py` pins what `runs`/`mechanism`/`variance` print by default, their `--json` contract, and their `--fields` validation (Typer `CliRunner`, mocked `analysis.bundle_evidence` rows). Domain logic is covered by `libs/analysis/tests/` (`test_bundle_evidence.py`, `test_data_loaders.py`). Both hermetic; no live tier. Run with:

```bash
uv run python -m pytest apps/analysis/tests -q
uv run python -m pytest libs/analysis/tests -q
```

## Commands it contributes

`thesis analysis` (12 commands, verified against `--help`): `reanalyze`, `results-final`, `robust-stats`, `cost`, `cold-start`, `hypotheses`, `plots`, `timeseries`, `gru-metrics`, `runs`, `mechanism`, `variance`. Entry point: `thesis-analysis` → `analysis_cli.cli:app`; also registered as the `analysis` sub-app of `thesis`.

```bash
uv run thesis analysis --help
uv run thesis analysis robust-stats
uv run thesis analysis reanalyze --results-dir results/experiments/phase-b/2026-02-15_clarknet-replay
uv run thesis analysis cost --experiment-dir results/experiments/phase-b/2026-02-16_validation-metrics-fixes
uv run thesis analysis cold-start
uv run thesis analysis hypotheses
uv run thesis analysis plots
uv run thesis analysis timeseries
uv run thesis analysis gru-metrics
uv run thesis analysis results-final --results-dir <bundle>
uv run thesis analysis runs <bundle>
uv run thesis analysis mechanism <bundle>
uv run thesis analysis variance <bundle>
```

## Conventions

- **No domain logic here.** Every command delegates to `analysis.*` (libs/analysis) or `shared.*`. This package only wires CLI args, prints output, and writes result files. The only inline code is thesis-specific glue with no reusable home (`HypothesisValidator` historical data; crossover graph math).
- **Import root is `analysis_cli`**: the package dir is `analysis_cli/` (not `analysis/`) to avoid colliding with `libs/analysis`, which owns the `analysis.*` import root. Distribution name is `analysis-cli`; helpers import as `analysis_cli.plots`, domain calls stay `analysis.comparison`, `analysis.cost`.
- **matplotlib is isolated here**, like streamlit/plotly in `apps/dashboard`; it lives in this package's `pyproject.toml`, not in root.
- **Constants come from `shared.scenarios`**: never redefine `SCENARIO_LABELS`, `SCENARIO_COLORS`, `SCENARIO_ORDER`, `SLO_THRESHOLD_MS`.
- **Lazy registration.** Added via `_register_analysis()` in `apps/cli/cli/main.py`, silently skipped on `ImportError` (same pattern as the other sub-apps).
