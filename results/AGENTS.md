# results/

Single source of truth for all experiment evidence: raw data, processed outputs, figures, claims, reports. Every thesis claim must trace to raw data here. This tree is data only; the code that governs it lives in `apps/experiment` and `libs/shared`.

## Module map

| Path | Responsibility |
|---|---|
| `experiments/<phase>/<bundle>/` | Experiment bundles (schema v2 layout below; legacy v1 bundles remain in place) |
| `evidence/registry.yaml` | Typed registry of all bundles; scanner-owned facts merged, human fields preserved |
| `evidence/registry-events.jsonl` | Immutable governance event log (canonical for governance) |
| `evidence/_registry_entries.jsonl`, `evidence/_artifact_index.jsonl` | Staging files the DuckDB catalog regenerates on refresh; scratch, never canonical |
| `evidence/catalog.duckdb` | Local DuckDB query cache; ignored by git, rebuilt locally |
| `evidence/README.md`, `evidence/BACKLOG.md` | Storage tiers and query rules; deferred-evidence queue (`EVID-NNN`) |
| `claims/` | Claim ledger: `CLAIMS_TO_EVIDENCE.md`, `INCONSISTENCIES.md`, `TRUTH_ALIGNED_CLAIMS.md`, `FINAL_NUMBERS.md`, `DOCX_CITATION_INVENTORY.md` |
| `EXPERIMENT_JOURNAL.md` | Generated Markdown summary of the registry and recent governance events; read-only, never hand-edited |
| `calibration/` | Capacity/calibration run artifacts (JSON) |
| `cost/`, `cost_analysis/` | Cost model figures and per-run cost analysis JSON |
| `models/gru/` | Model study outputs |
| `figures/`, `hypothesis_validation/`, `phase_b_run.log` | Figure candidates, validation JSON, run logs |

## Data versus implementation

The registry implementation is not in this tree:

- `apps/experiment/experiment/evidence/registry.py`: typed scanner, merge-safe reconciler, legacy backfill (scanner-owned vs human-owned field split).
- `apps/experiment/experiment/evidence/cli_adapter.py`: the Typer sub-app registered as `thesis experiment evidence ...`.
- `apps/experiment/experiment/evidence/catalog.py`: adapter bridging bundles into `shared.evidence.catalog.EvidenceCatalog` (Parquet writes, sha256 indexing).
- `apps/experiment/experiment/evidence/renderer.py`: renders `EXPERIMENT_JOURNAL.md` from the registry.
- `libs/shared/shared/evidence/catalog.py`: `EvidenceCatalog`, the DuckDB view layer.

Edits to registry behavior go there; edits to registry *content* go through the CLI below or, for human-owned fields, directly in `registry.yaml`.

## Module direction

- **Where new code goes:** nowhere under `results/`. New evidence-handling code belongs in `apps/experiment/experiment/evidence/`; new catalog views in `libs/shared/shared/evidence/catalog.py`.
- **Where new data goes:** a new experiment bundle under `experiments/<phase>/<YYYY-MM-DD_slug>/` (schema v2); a new claim mapping in `claims/`; deferred evidence gets a `BACKLOG.md` entry first.

## Mandatory discovery sequence (for agents)

Before creating a new experiment or analysis, read these in order:

1. **[`evidence/README.md`](evidence/README.md)**: canonical storage tiers (Git text / LFS / ignored) and query rules.
2. **[`evidence/BACKLOG.md`](evidence/BACKLOG.md)**: deferred-evidence queue (`EVID-NNN`); check whether your task is already tracked or blocked.
3. **Query the registry/catalog**: `uv run thesis experiment evidence audit` (read-only bundle scan), then `uv run thesis experiment evidence query` or `journal` to see what bundles exist and their treatment-fidelity status.
4. Only then create a new experiment or analysis.

## The evidence CLI

`uv run thesis experiment evidence ...` (contributed by `apps/experiment`; operates on this tree):

| Subcommand | Effect |
|---|---|
| `audit` | Read-only scan of experiment bundles; prints a summary |
| `reconcile [--apply]` | Merge-safe registry reconciliation; without `--apply` it reports drift and exits non-zero, with `--apply` it writes `registry.yaml` + governance events |
| `query` | Read-only SQL against the DuckDB catalog |
| `journal` | Read-only view of recent governance events from `registry-events.jsonl` |
| `backfill-legacy [--apply]` | Logically backfill legacy v1 bundles into the typed registry; same `--apply` gate as `reconcile` |
| `derive-parquet` | Writes a provenance-preserving Parquet from a legacy CSV/JSONL source to the explicit `--output` path (no fixed location) |
| `catalog refresh` | Rebuilds `catalog.duckdb` (ignored, noncanonical); never touches canonical files |

No tests live under `results/`. Registry and catalog behavior is tested where the code lives:

```bash
uv run python -m pytest apps/experiment/tests/test_evidence_registry.py apps/experiment/tests/test_evidence_cli.py libs/shared/tests/test_evidence_catalog.py -q
```

All hermetic (tmp_path repos; no cluster, no network).

## Bundle schema v2

New experiments use schema v2 (`meta.yaml` sets `bundle_schema_version: 2`):

```
results/experiments/<phase>/<YYYY-MM-DD_slug>/
  meta.yaml                          # Immutable planned configuration
  report.md                          # Sole human interpretation
  events.jsonl                       # Immutable bundle-level execution record
  paired_analysis.json               # Computed analysis (root: what the writers emit)
  SUMMARY.md                         # Generated verdict and headline table
  derived/
    paired_analysis.json             # Also read here; no bundle uses it today
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
- Root and per-run `events.jsonl` are immutable execution records. Append only, never edited or deleted.
- `raw/` contains raw text logs plus Parquet tables; raw artifacts are never edited.
- `derived/` contains computed analysis; it may be regenerated from raw data.
- `report.md` is the sole interpretation.

**Git handling:**
- `.parquet` files are Git LFS (`results/experiments/**/*.parquet`).
- JSON, YAML, JSONL, CSV, and Markdown are normal Git text.
- `catalog.duckdb` is ignored (rebuilt locally).

Canonical v2 layout is as above. What the current writers actually emit differs, and the scanner accepts both layouts (`_scan_run_dirs` in `apps/experiment/experiment/evidence/registry.py` handles v1 direct-child and v2 `raw/`):

- The paired-run commands (`apps/experiment/experiment/cli.py`) stamp `bundle_schema_version: 2` but create `<scenario>_run<N>/` as direct children of the bundle root and write `paired_analysis.json` and `SUMMARY.md` at the root, not under `derived/`. All nine bundles that carry a paired analysis have this shape; none uses `derived/`.
- The dynamic workload runner (`apps/experiment/experiment/dynamic.py`) writes runs under `raw/`.

When creating a new bundle by hand, match what the owning command writes (direct children for the paired-run commands, `raw/` for the dynamic runner). Readers take both layouts through `shared.artifacts.read_paired_analysis` and `registry._scan_run_dirs`, so a bundle is never invisible because of where its analysis landed.

## Storage formats

- **YAML** for metadata (`meta.yaml`): human-authored
- **JSONL** for event logs: append-only, one-line-per-event diffs
- **JSON** for structured results and manifests
- **CSV** for legacy tabular results: git-friendly, pandas-native
- **Parquet** for high-volume time series (Git LFS)
- **Markdown** for reports: embeddable in thesis
- **PNG** for figures: small, git-trackable

## Rules

1. Raw data is never edited after creation
2. One report per experiment; no duplicate summaries
3. Every claim traces to raw data via `claims/CLAIMS_TO_EVIDENCE.md`
4. If evidence conflicts, log it in `claims/INCONSISTENCIES.md`
5. `.parquet` is Git LFS; `catalog.duckdb` is ignored and rebuilt

## Key documents

- `README.md`: evidence registry and experiment index
- `evidence/README.md`: canonical storage and query rules
- `evidence/BACKLOG.md`: deferred-evidence work queue
- `evidence/registry.yaml`: typed registry of all bundles
- `evidence/registry-events.jsonl`: immutable governance log
- `EXPERIMENT_JOURNAL.md`: generated registry summary (read-only)
- `claims/CLAIMS_TO_EVIDENCE.md`: every claim mapped to raw data
- `claims/INCONSISTENCIES.md`: tracked inconsistencies

## Experiment data storage policy

Where each experiment artifact lives: three tiers, decided by size, meaning, and regenerability, never by file extension alone.

| Tier | Storage | What goes there | Examples |
|---|---|---|---|
| **(a) plain git** | tracked, normal diffable text | small, human-meaningful, evidence-critical, must survive | `meta.yaml`, `events.jsonl`, `result.json`, `paired_analysis.json`, `k6-summary.json`, `daemon.log`, `provision_events.json`, `node_utilization.json`, `resource_utilization.json` |
| **(b) git LFS** | Git LFS (`.gitattributes` filter) | large binary, regenerable | `*.parquet` metrics tables, `prometheus/` raw exports, model weights `*.pt` / `*.pth` |
| **(c) disk-only** | untracked, ignored, documented in `results/evidence/registry.yaml` | very large, regenerable | phase-c raw k6 blobs (`k6-results.json`, ~160 MB each, ~1 GB total), `data/raw/*.gz` |

**Tier rules**

1. Small + human-meaningful + diffable + must-survive goes in plain git. Commit it.
2. Large binary / raw exports go in Git LFS (parquet, prometheus, weights). Wire the LFS filter when the artifact first appears; never fall back to disk-only for something a reviewer needs.
3. Huge + regenerable is disk-only, but register the bundle and its raw location in `results/evidence/` so the data path is documented.
4. Never blanket-ignore `*.json`. JSON is the evidence format of this repo; a blanket rule silently hides every analysis artifact.
5. Bundle JSON is evidence-critical and must be tracked in plain git: `result.json`, `paired_analysis.json`, `k6-summary.json`, and per-run `result.json`/`manifest.json` are committed, never ignored.
6. `.gitignore` only names the large/derived exceptions (`results/experiments/**/raw/*.json`, `raw/**/k6-results.json`, `**/prometheus/*.json`, `**/k6/*.json`). Everything else under `results/experiments/` is addable by default.
7. `results/evidence/` (registry + catalog) is the source of truth for bundle roles; a bundle's storage tier must match its registry entry.

**Incident note (Aug 2026), why rule 4 exists.** A blanket `*.json` ignore line caused `paired_analysis.json` / `result.json` to be silently uncommitted across bundles. When a worktree was deleted, those analysis artifacts were irrecoverable: they existed on disk but never in git. Fix: scoped ignore rules plus backfill of every on-disk `result.json` / `paired_analysis.json` (334 files, ~1.4 MB) so thesis-claim backing is versioned. Never reintroduce a blanket extension ignore.

## Invariants

- The registry reconciler never overwrites human-owned fields (`role`, `status`, `config`, `results`, `claims_supported`, `supersedes`, `superseded_by`, `notes`); it replaces only scanner-owned facts (date, scenarios, flags, counts, treatment fidelity, git commits).
- `registry-events.jsonl` and per-run `events.jsonl` are append-only.
- `catalog.duckdb` and its `_*.jsonl` staging files are caches; deleting them loses nothing.
- `EXPERIMENT_JOURNAL.md` is generated; hand edits are overwritten on the next render.
