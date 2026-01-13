# Results

Final thesis results - tables, figures, and raw data.

## Structure

```
results/
├── tables/            # LaTeX-ready tables
│   ├── h1-comparison.tex    # S4 vs S1/S2 comparison
│   ├── h2-comparison.tex    # S4 vs S3 comparison
│   └── prediction-accuracy.tex  # RMSE/MAE/MAPE
├── figures/           # Publication-quality figures
│   ├── latency-distribution.pdf
│   ├── cost-comparison.pdf
│   └── prediction-timeseries.pdf
└── raw/               # Raw experiment data
    └── YYYYMMDD-HHMM_scenario_workload.json
```

## Key Tables (Mapping to Thesis Chapters)

| Table | Chapter | Content |
|-------|---------|---------|
| `prediction-accuracy.tex` | 4.1 | GRU vs LR vs baselines (H3) |
| `h1-comparison.tex` | 4.2 | Hybrid vs Pure approaches (H1) |
| `h2-comparison.tex` | 4.3 | Predictive vs Reactive (H2) |

## Target Metrics (Thesis 3.5.2)

### Performance Targets

| Metric | Target |
|--------|--------|
| p50 Latency | < 50ms |
| p95 Latency | < 100ms |
| p99 Latency | < 200ms (SLO) |
| Error Rate | < 0.1% |

### Prediction Targets

| Metric | Target |
|--------|--------|
| RMSE | < 10% of avg traffic |
| MAE | < 5% of avg traffic |

## Generating Results

```bash
# Generate all thesis tables
python scripts/generate_tables.py

# Generate all figures
python scripts/generate_figures.py
```
