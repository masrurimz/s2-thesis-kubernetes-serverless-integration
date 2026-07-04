# Scripts — Reproduction and Analysis Tools

All scripts run from the repo root via `uv run python scripts/<name>.py`.

## Experiment Runners

| Script | Purpose | Usage |
|--------|---------|-------|
| `run_phase_b_experiments.py` | Canonical Phase B experiment runner (k6 + Prometheus + daemon lifecycle) | `uv run python scripts/run_phase_b_experiments.py --phase full --runs 5 --duration 300` |
| `run_calibration.py` | Workload calibration — finds Goldilocks RPS via curl + Prometheus | `uv run python scripts/run_calibration.py` |
| `run_dynamic_experiment.py` | Phase C dynamic burst experiments (S3 vs S4) | `uv run python scripts/run_dynamic_experiment.py` |
| `realtime_validation.py` | Live H1/H2/H3 validation with real infrastructure | `uv run python scripts/realtime_validation.py` |

## Analysis

| Script | Purpose | Usage |
|--------|---------|-------|
| `validate_all_hypotheses.py` | H1/H2/H3 validation from historical data + GRU model | `uv run python scripts/validate_all_hypotheses.py` |
| `robust_statistics_phase_b.py` | Welch/Mann-Whitney/bootstrap CI on Phase B data | `uv run python scripts/robust_statistics_phase_b.py` |
| `reanalyze_phase_b.py` | Re-analysis of all Phase B runs with Holm-Bonferroni correction | `uv run python scripts/reanalyze_phase_b.py` |
| `cold_start_analysis.py` | Cold start penalty decomposition from Phase A1 + Phase B | `uv run python scripts/cold_start_analysis.py` |
| `cost_analyzer.py` | AWS cloud cost model (EKS/Lambda/EC2) from experiment data | `uv run python scripts/cost_analyzer.py` |
| `analyze_predictive_eligibility.py` | Root-cause analysis for PREDICTIVE=0 in Phase B runs | `uv run python scripts/analyze_predictive_eligibility.py` |
| `identify_outlier_runs.py` | Detects stale-Prometheus outlier runs | `uv run python scripts/identify_outlier_runs.py` |

## Metrics and Visualization

| Script | Purpose | Usage |
|--------|---------|-------|
| `compute_gru_percentage_metrics.py` | Derives MAE%/MAPE from training results, validates H3 | `uv run python scripts/compute_gru_percentage_metrics.py` |
| `generate_plots.py` | Thesis-quality figures (A1 timeline, B boxplots, dashboard) | `uv run python scripts/generate_plots.py` |
| `plot_phase_b_timeseries.py` | Matplotlib bar charts + decision comparison plots | `uv run python scripts/plot_phase_b_timeseries.py` |
| `generate_trace_replay.py` | Parquet → k6 stages JSON + JS script via pandas | `uv run python scripts/generate_trace_replay.py` |

## Shell

| Script | Purpose |
|--------|---------|
| `run-scenario.sh` | Run a single experiment scenario |

## Environment

Set `HSA_OVERRIDE_GFX_VERSION=11.0.0` for AMD GPU (ROCm) support.
