# data/ — Input Datasets

## What This Is

HTTP trace datasets (ClarkNet, Calgary) for GRU model training and experiment evaluation. Not experiment outputs — those live in `../results/`.

## Structure

| Directory | Contents |
|-----------|----------|
| `raw/` | Original HTTP log archives (ClarkNet Aug-Sep 1995, Calgary Oct 1994) — gitignored |
| `processed/` | RPS time series parquet, train/val/test splits, model artifacts |
| `trace-replay/` | Generated k6 artifacts (stages JSON, RPS CSV) for trace-driven load tests |
| `scripts/` | CLF log parser (`clf_parser.py`) — data pipeline, not analysis scripts |

## Conventions

- **Large files** are tracked via `.gitattributes` — don't add new large binaries without a gitattributes entry.
- **Don't commit raw data** — `raw/` is gitignored. Use `scripts/download_datasets.sh` to fetch.
- **CLF parser** is a standalone package (`data/scripts/`) — import via `from data.scripts import clf_to_rps`.
- **Processed parquet** is the canonical training input — `scripts/generate_trace_replay.py` reads from here.
