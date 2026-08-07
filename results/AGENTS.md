# results/ — Evidence Registry

## What This Is

**Single source of truth for ALL experiment evidence.** Raw data, processed outputs, figures, claims, reports. Every thesis claim must trace to raw data here.

## Mandatory Discovery Sequence (for agents)

Before creating a new experiment or analysis, read these in order:

1. **[`evidence/README.md`](evidence/README.md)** — canonical storage tiers (Git text / LFS / ignored) and query rules.
2. **[`evidence/BACKLOG.md`](evidence/BACKLOG.md)** — deferred-evidence queue (`EVID-NNN`); check whether your task is already tracked or blocked.
3. **Query the registry/catalog** — run `uv run thesis experiment evidence audit` and `uv run thesis experiment evidence catalog refresh` to see what bundles exist and their treatment-fidelity status.
4. Only then create a new experiment or analysis.

Canonical evidence sources:
- **[`evidence/registry.yaml`](evidence/registry.yaml)** — typed registry of all bundles (scanner-owned facts merged; human fields preserved).
- **[`evidence/registry-events.jsonl`](evidence/registry-events.jsonl)** — immutable governance event log (canonical for governance).
- Per-run **`events.jsonl`** — immutable execution record (canonical for execution).
- **[`EXPERIMENT_JOURNAL.md`](EXPERIMENT_JOURNAL.md)** — generated Markdown summary of the registry and recent governance events (read-only; never hand-edited).
- **`catalog.duckdb`** — local DuckDB query cache; never a source of truth.

## Bundle Schema v2

New experiments use schema v2 (`meta.yaml` sets `bundle_schema_version: 2`):

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

**Immutability rules:**
- `meta.yaml` is immutable planned configuration.
- Root and per-run `events.jsonl` are immutable execution records — append only, never edited or deleted.
- `raw/` contains raw text logs plus Parquet tables; raw artifacts are never edited.
- `derived/` contains computed analysis; it may be regenerated from raw data.
- `report.md` is the sole interpretation.

**Git handling:**
- `.parquet` files are Git LFS (`results/experiments/**/*.parquet`).
- JSON, YAML, JSONL, CSV, and Markdown are normal Git text.
- `catalog.duckdb` is ignored (rebuilt locally).

Legacy bundles (schema v1, direct-child `<scenario>_run<N>/` layout) remain in place. The registry/catalog adapters read them; no raw file is moved or rewritten.

## Storage Formats

- **YAML** for metadata (`meta.yaml`) — human-authored
- **JSONL** for event logs — append-only, one-line-per-event diffs
- **JSON** for structured results and manifests
- **CSV** for legacy tabular results — git-friendly, pandas-native
- **Parquet** for high-volume time-series (Git LFS)
- **Markdown** for reports — embeddable in thesis
- **PNG** for figures — small, git-trackable

## Rules

1. Raw data is never edited after creation
2. One report per experiment — no duplicate summaries
3. Every claim traces to raw data via `claims/CLAIMS_TO_EVIDENCE.md`
4. If evidence conflicts, log in `claims/INCONSISTENCIES.md`
5. `.parquet` is Git LFS; `catalog.duckdb` is ignored and rebuilt

## Key Documents

- `README.md` — Evidence registry and experiment index
- `evidence/README.md` — Canonical storage and query rules
- `evidence/BACKLOG.md` — Deferred-evidence work queue
- `evidence/registry.yaml` — Typed registry of all bundles
- `evidence/registry-events.jsonl` — Immutable governance log
- `EXPERIMENT_JOURNAL.md` — Generated registry summary (read-only)
- `claims/CLAIMS_TO_EVIDENCE.md` — Every claim mapped to raw data
- `claims/INCONSISTENCIES.md` — Tracked inconsistencies

## Experiment Data Storage Policy

**Where each experiment artifact lives — three tiers. Decided by size, meaning, and
regenerability; **never** by file extension alone.**

| Tier | Storage | What goes there | Examples |
|---|---|---|---|
| **(a) PLAIN GIT** | tracked in git, normal diffable text | small, human-meaningful, evidence-critical, must survive | `meta.yaml`, `events.jsonl`, `result.json`, `paired_analysis.json`, `k6-summary.json`, `daemon.log`, `provision_events.json`, `node_utilization.json`, `resource_utilization.json` |
| **(b) GIT LFS** | Git LFS (`.gitattributes` filter) | large binary, regenerable | `*.parquet` metrics tables, `prometheus/` raw exports, model weights `*.pt` / `*.pth` |
| **(c) DISK-ONLY** | untracked, ignored, documented in `results/evidence/registry.yaml` | very large, regenerable | phase-c raw k6 blobs (`k6-results.json`, ~160 MB each, ~1 GB total), `data/raw/*.gz` |

**Rules**

1. Small + human-meaningful + diffable + must-survive → **plain git**. Commit it.
2. Large binary / raw exports → **Git LFS** (parquet, prometheus, weights). Wire the LFS filter
   when the artifact first appears; never fall back to disk-only for something a reviewer needs.
3. Huge + regenerable → **disk-only**, but register the bundle and its raw location in
   `results/evidence/` so the data path is documented.
4. **Never blanket-ignore `*.json`.** JSON is the evidence format of this repo; a blanket rule
   silently hides every analysis artifact.
5. **Bundle JSON is evidence-critical and MUST be tracked** in plain git: `result.json`,
   `paired_analysis.json`, `k6-summary.json`, and per-run `result.json`/`manifest.json` are
   committed, never ignored.
6. `.gitignore` only names the large/derived exceptions
   (`results/experiments/**/raw/*.json`, `raw/**/k6-results.json`, `**/prometheus/*.json`,
   `**/k6/*.json`). Everything else under `results/experiments/` is addable by default.
7. `results/evidence/` (registry + catalog) is the source of truth for bundle roles; a bundle's
   storage tier must match its registry entry.

**Incident note (Aug 2026) — why rule 4 exists.** A blanket `*.json` ignore line caused
`paired_analysis.json` / `result.json` to be silently uncommitted across bundles; when a worktree
was deleted, those analysis artifacts were **irrecoverable** — they existed on disk but never in
git. Fix: scoped ignore rules + backfill of every on-disk `result.json` / `paired_analysis.json`
(334 files, ~1.4 MB) so thesis-claim backing is versioned. Never reintroduce a blanket
extension ignore.
