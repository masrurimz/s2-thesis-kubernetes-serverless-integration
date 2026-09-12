# Legacy run artifacts (pre-refactor)

These are the runs from the nginx simulation era, before the governed testbed and the `thesis` CLI existed. They are **not evidence**: by the repository's first invariant, experiment evidence lives in `results/` only. Nothing imports this tree.

## What is in here

Seven files were per-request k6 streams — one JSON record per request, 319 MB to 505 MB each. They were converted on 2026-09-12 to `<name>-points.parquet`: sample rows only, `ts` as a real timestamp column, ordered by time, zstd compressed. The originals were removed after each conversion's row count matched its source. **2.8 GB to 32 MB**, and a five-minute window now reads as a window instead of a full-file string scan.

Small files (configurations, summaries, a few kilobytes) stayed JSON, because for those the format was already the right one.

## Reading one

```bash
uv run python -c "
import duckdb
con = duckdb.connect()
print(con.execute(\"SELECT count(*) FROM read_parquet('infrastructure/results/knative-real/stress-test/s4-hybrid-predictive-v4/results-points.parquet')\").fetchone())
print(con.execute(\"SELECT type, metric, count(*) FROM read_parquet('infrastructure/results/knative-real/stress-test/s4-hybrid-predictive-v4/results-points.parquet') GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 10\").fetchall())
print(con.execute(\"SELECT data.time, data.value FROM read_parquet('infrastructure/results/knative-real/stress-test/s4-hybrid-predictive-v4/results-points.parquet') WHERE metric = 'http_reqs' ORDER BY data.time LIMIT 5\").fetchall())
"
```

## Repeating the conversion for another stream

```bash
uv run python -c "
import duckdb
duckdb.connect().execute(\"\"\"
  COPY (SELECT * FROM read_json_auto('<stream>.json', sample_size=-1))
  TO '<stream>.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)
""")
# then, for a time series, project it: sample rows only, typed timestamp, sorted
uv run python -c """
import duckdb
duckdb.connect().execute("""
  COPY (
    SELECT CAST(data.time AS TIMESTAMP WITH TIME ZONE) AS ts, metric,
           CAST(data.value AS DOUBLE) AS value, data.tags AS tags
    FROM read_parquet('<stream>.parquet') WHERE type = 'Point' ORDER BY ts
  ) TO '<stream>-points.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)
\"\"\")
"
```

Verify the row count against the source before deleting anything. A 160 MB k6 stream becomes 2.9 MB, a factor of 55; the derived Parquet is gitignored, the same disk-only tier as the JSON it replaces.
