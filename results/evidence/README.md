# Evidence Storage and Query Rules

This directory holds the canonical evidence registry, governance event log, deferred-evidence backlog, and the local DuckDB query catalog for the thesis.

## Canonical storage tiers

| Tier | Formats | Git handling | Role |
|------|---------|--------------|------|
| **Normal Git text** | YAML, JSON, JSONL, Markdown, CSV | Tracked normally | Configuration, lifecycle provenance, summaries, reports |
| **Git LFS** | `results/experiments/**/*.parquet` | `filter=lfs diff=lfs merge=lfs -text` | Per-run high-volume time-series artifacts |
| **Ignored / rebuilt** | `catalog.duckdb`, `catalog.duckdb.wal`, `catalog.duckdb.tmp` | `.gitignore` | Local DuckDB query cache — never a source of truth |

Parquet files under `results/experiments/` are tracked by Git LFS via a single rule in `.gitattributes`. YAML, JSON, JSONL, CSV, and Markdown remain normal Git text files. The DuckDB catalog is regenerated from canonical artifacts and is never committed.

## Canonical files

| File | Purpose | Mutability |
|------|---------|------------|
| `registry.yaml` | Typed registry of all experiment bundles | Merge-safe: scanner replaces scanner-owned fields; human fields preserved |
| `registry-events.jsonl` | Append-only governance event log | Immutable: append only, never edited or deleted |
| `BACKLOG.md` | Human-maintained deferred-evidence queue (`EVID-NNN`) | Human-maintained |
| `README.md` | This file | Human-maintained |
| `catalog.duckdb` | Local DuckDB query cache | Ignored, rebuilt on demand |

## Legacy v1 bundles

Historical bundles use the original direct-child layout (`<scenario>_run<N>/` as direct children of the bundle root). The registry scanner reads both v1 and v2 layouts:

- **Logical backfill only:** `uv run thesis experiment evidence backfill-legacy --apply` registers every v1 bundle in `registry.yaml` and appends one `legacy_backfilled` event per bundle.
- **Raw files preserved:** no historical bundle file is moved, rewritten, or deleted.
- **Per-artifact Parquet derivation:** `uv run thesis experiment evidence derive-parquet` creates a provenance-preserving Parquet copy of a specific legacy CSV or JSONL artifact under `derived/legacy-parquet/`. This is deliberate and per-artifact — never a bulk conversion.
- **No fabricated lifecycle:** historical runs never receive reconstructed `run_started`/`run_completed` events. The lifecycle journal begins with v2 bundles.

## Bundle schema v2

```
results/experiments/<phase>/<YYYY-MM-DD_slug>/
  meta.yaml                          # Immutable planned configuration
  report.md                          # Sole human interpretation
  events.jsonl                       # Immutable bundle-level execution record
  derived/
    paired_analysis.json             # Computed analysis
    legacy-parquet/<artifact>.parquet  # Derived copies of legacy measurements
  raw/
    <scenario>_run<N>/
      manifest.json                  # Per-run reproducibility snapshot
      events.jsonl                   # Immutable per-run execution record
      result.json                    # Typed ExperimentResult
      daemon.log                     # Raw diagnostic text log
      k6-summary.json                # k6 summary
      metrics.parquet                # Queried high-volume metrics (LFS)
      prediction-actual.parquet      # Prediction vs actual (LFS)
      system-events.parquet          # Normalized system event projection (LFS)
```

`meta.yaml` must set `bundle_schema_version: 2` for v2 bundles. The `daemon.log` remains the raw diagnostic source; `system-events.parquet` is a normalized query projection — never a replacement for the raw text log.

## Query examples

After building the catalog:

```bash
uv run thesis experiment evidence catalog refresh
```

Query against the typed views:

```sql
-- Per-run results
SELECT experiment_id, scenario, run_id, p99_latency_ms, run_validity_passed
FROM run_results
ORDER BY experiment_id, run_id
LIMIT 20;

-- Execution lifecycle events
SELECT event, experiment_id, run_id, timestamp
FROM run_events
WHERE event = 'run_failed'
ORDER BY timestamp DESC;

-- Time-series (v2 Parquet; empty if no v2 Parquet exists)
SELECT scenario, count(*) FROM timeseries GROUP BY scenario;

-- Artifact index (all legacy + v2 artifacts)
SELECT format, count(*) FROM artifact_index GROUP BY format ORDER BY format;

-- Treatment fidelity per bundle
SELECT id, treatment_fidelity
FROM registry_entries
WHERE treatment_fidelity IS NOT NULL;
```

The catalog exposes empty typed views (not errors) when no v2 Parquet exists. Use `artifact_index` to discover legacy CSV/JSON/JSONL data by path.
