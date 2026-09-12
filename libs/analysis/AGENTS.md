# libs/analysis

Domain analysis library for thesis experiment results: data loaders over result bundles, pairwise and paired statistical comparison, cold-start decomposition, cloud cost model, report generation, and typed evidence tables over a single bundle. Consumed by `apps/analysis` (the `analysis_cli` Typer app imports `analysis.*`; see `apps/analysis/analysis_cli/cli.py`, `plots.py`, `timeseries.py`, `crossover.py`).

## Module map

Package source lives under `libs/analysis/analysis/` (nested package layout).

| Path | Responsibility |
|---|---|
| `analysis/constants.py` | `OUTLIER_RUNS`, `BETA_VALUES`, `H1/H2_COMPARISONS`, cold-start measurements, AWS pricing constants, `PHASE_A1_DECISIONS`; pod resource requests derived from `CALIBRATION` |
| `analysis/data_loaders.py` | `load_phase_b_data(path, exclude_outliers)`, `load_outliers`, `is_outlier`, `group_by_scenario`, `build_results_final`, `ScenarioMetrics`, `load_experiment_metrics` |
| `analysis/comparison.py` | `run_pairwise_comparison(...)` and `apply_holm_bonferroni(family)` for unpaired scenario comparisons; `run_paired_comparison(...)` and `apply_holm_paired(family)` for paired designs; both produce `shared.models.experiment` comparison models |
| `analysis/bundle_evidence.py` | Typed evidence tables over one bundle directory: `run_evidence` (`RunEvidence`), `mechanism_rows` (`MechanismRow`), `variance_summary` (`ArmSpread`, `VarianceSummary`), `as_payload` for machine output |
| `analysis/cold_start.py` | `ScenarioStats`, `compute_scenario_stats`, `correlation_scale_out_p99`, `analyze_phase_a1_transition`, `variance_decomposition`, `theoretical_cold_start_impact` |
| `analysis/cost.py` | `CloudPricing`, `CostBreakdown`, `analyze_from_experiment(metrics)`, `compute_cost_proxy(results)` |
| `analysis/report.py` | `generate_report(results, h1, h2, cost)`, `render_comparisons(lines, comps)` |

## Module direction

- **May import:** `shared.*` (stats primitives, models, scenario constants, artifact readers) and third-party (numpy, scipy, pandas, pydantic).
- **Must never import:** `apps/*`, `libs/infra`, or any CLI module. Statistical math lives in `shared.stats`; this package composes those primitives into domain-specific comparisons and tables.
- **Where new code goes:**
  - A new analysis concern (one domain question): one new module `analysis/<concern>.py`, imported by `apps/analysis` CLI code.
  - A new statistical procedure: `shared.stats`, not here.
  - A new bundle-level question: a builder in `analysis/bundle_evidence.py` returning typed rows.
  - A new test: `libs/analysis/tests/`.

## Tests

`libs/analysis/tests/`: `test_bundle_evidence.py`, `test_data_loaders.py`. Hermetic (tmp_path bundle fixtures; no cluster, no network).

```bash
uv run python -m pytest libs/analysis/tests -q
```

Live/opt-in tier: none.

## Commands it contributes

None: library only. The CLI that drives it is `apps/analysis` (`uv run thesis analysis ...`).

## Invariants

- One module per domain concern; the module's public names are what `apps/analysis` imports.
- `bundle_evidence` builders take a bundle directory and return typed rows over the artifacts read through `shared.artifacts`; a question about a bundle is a function call, never hand-opened files.
- Outlier handling is centralized: `OUTLIER_RUNS` in `constants.py`, applied by `data_loaders` (`exclude_outliers`, `is_outlier`), never re-listed by callers.
- Costs derive from `CALIBRATION` (shared calibration single source of truth); pricing constants stay in `constants.py`.
