# libs/analysis — Domain Analysis Library

## What This Is

Domain analysis library for thesis experiment results: data loaders, pairwise
statistical comparison, cold-start decomposition, cloud cost model, and report
generation. Consumed by `apps/analysis` (CLI), `apps/experiment` (pipeline),
and `apps/dashboard` (read-only archival).

## Module Map

| Module | Purpose |
|--------|---------|
| `constants.py` | `OUTLIER_RUNS`, `BETA_VALUES`, `H1/H2_COMPARISONS`, cold-start measurements, AWS pricing constants, `PHASE_A1_DECISIONS` |
| `data_loaders.py` | `load_phase_b_data(path, exclude_outliers)`, `load_outliers`, `is_outlier`, `group_by_scenario`, `ScenarioMetrics`, `load_experiment_metrics`, `_compute_actual_serverless_pct` |
| `comparison.py` | `run_pairwise_comparison(results, baseline, comp, metric, label) → StatisticalComparison`, `apply_holm_bonferroni(family)` |
| `cold_start.py` | `ScenarioStats`, `compute_scenario_stats`, `correlation_scale_out_p99`, `analyze_phase_a1_transition`, `variance_decomposition`, `theoretical_cold_start_impact` |
| `cost.py` | `CloudPricing`, `CostBreakdown`, `analyze_from_experiment(metrics)`, `compute_cost_proxy(results)` |
| `report.py` | `generate_report(results, h1, h2, cost)`, `render_comparisons(lines, comps)` |

## Boundaries

- Depends on `shared` only (stats primitives, models, scenario constants).
- Never imports from `apps/`.
- Statistical math lives in `shared.stats`, not here — this package composes
  those primitives into domain-specific comparisons.

## Tests

```bash
uv run pytest libs/analysis/tests/ -v
```
