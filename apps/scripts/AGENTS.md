# scripts/ — Reproduction and Analysis Scripts

## What This Is

Canonical reproduction and analysis scripts for thesis experiments. Standalone Python files — not a package. Uses the root `.venv` via `uv run python scripts/<name>.py`.

## Quick Commands

```bash
# Run from repo root
uv run python scripts/run_phase_b_experiments.py --phase full --runs 5 --duration 300
uv run python scripts/validate_all_hypotheses.py
uv run python scripts/generate_plots.py
```

## Conventions

- **Always run from repo root** — scripts use `Path(__file__).resolve().parent.parent` to find project root.
- **ROCm GPU**: set `HSA_OVERRIDE_GFX_VERSION=11.0.0` before any script that loads GRU models.
- **No imports from controller** — scripts are standalone analysis tools. They read data files directly, not via controller modules. If a script needs controller code, it subprocesses `uv run python -m ...`.
- **ruff**: F841 (unused-variable) is per-file-ignored here — matplotlib `bars = ax.bar(...)` assignments are standard patterns.

## Script Categories

| Category | Scripts |
|----------|---------|
| **Runners** | `run_phase_b_experiments.py`, `run_calibration.py`, `run_dynamic_experiment.py`, `realtime_validation.py` |
| **Analysis** | `validate_all_hypotheses.py`, `robust_statistics_phase_b.py`, `reanalyze_phase_b.py`, `cold_start_analysis.py`, `cost_analyzer.py`, `analyze_predictive_eligibility.py`, `identify_outlier_runs.py` |
| **Visualization** | `generate_plots.py`, `plot_phase_b_timeseries.py`, `compute_gru_percentage_metrics.py`, `generate_trace_replay.py` |

See `scripts/README.md` for per-script documentation.
