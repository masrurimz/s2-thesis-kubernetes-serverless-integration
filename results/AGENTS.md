# results/ — Evidence Registry

## What This Is

**Single source of truth for ALL experiment evidence.** Raw data, processed outputs, figures, claims, reports. Every thesis claim must trace to raw data here.

## Bundle Convention

Every experiment is a self-contained folder:

```
results/experiments/<phase>/<YYYY-MM-DD_slug>/
  meta.yaml                       # YAML — experiment metadata
  report.md                       # Markdown — interpretation
  raw/<scenario>_run<N>/
    k6_summary.csv                # CSV — k6 metrics
    prometheus.csv                # CSV — time-series exports
    daemon_events.jsonl           # JSONL — structured decision log
    resource.csv                  # CSV — CPU/memory samples
  processed/
    aggregate.csv                 # CSV — per-scenario summary
    comparisons.csv               # CSV — statistical comparisons
  figures/*.png
```

## Storage Formats

- **CSV** for tabular results — git-friendly, line-per-record, pandas-native
- **JSONL** for event logs — append-only, one-line-per-event diffs
- **YAML** for metadata (meta.yaml) — human-authored
- **Markdown** for reports — embeddable in thesis
- **PNG** for figures — small, git-trackable

## Rules

1. Raw data is never edited after creation
2. One report per experiment — no duplicate summaries
3. Every claim traces to raw data via `claims/CLAIMS_TO_EVIDENCE.md`
4. If evidence conflicts, log in `claims/INCONSISTENCIES.md`

## Key Documents

- `README.md` — Evidence registry and experiment index
- `claims/CLAIMS_TO_EVIDENCE.md` — Every claim mapped to raw data
- `claims/INCONSISTENCIES.md` — Tracked inconsistencies
