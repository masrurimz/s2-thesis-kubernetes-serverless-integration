# apps/dashboard/ — Experiment Results Dashboard

## What This Is

Interactive **Streamlit + Plotly** dashboard for **archival analysis** of thesis
experiment JSON results. Reads `results/experiments/` directly — no live
monitoring, no Prometheus, no Grafana.

## Run

```bash
# From repo root (on x1-dev):
uv run thesis dashboard start
# → http://0.0.0.0:28555  (Tailscale URL from m5-space: http://100.122.177.43:28555)

# Custom port/host:
uv run thesis dashboard start --port 28666 --host 0.0.0.0
```

Bind `0.0.0.0` so the dashboard is reachable over Tailscale. Auth relies on
**Tailscale ACL** only (same pattern as Hindsight on 28188/28199). For tighter
exposure, firewall port 28555 to the `tailscale0` interface.

## Data Eras

- **ERA 2** (2026-07-03+): full JSON bundles — time-series timelines, scaling
  storyboards, correlation explorer all work.
- **ERA 1** (pre-2026-07-03): `daemon.log` + `meta.yaml` only — Panels 3-6
  degrade to "no time-series data"; KPIs come from `results_final.json`; the
  Decision Inspector still parses `daemon.log`.

## Package Layout

| Module | Responsibility |
|---|---|
| `loader.py` | Artifact scanner (`scan_experiments`) + per-run JSON loaders (`load_result`/`load_prom`/…). NaN/Inf sanitized. Cached via `functools.lru_cache`. |
| `parser.py` | `parse_daemon_log` — regex extraction of routing/scaling/GRU/HAProxy/weight-change events. Fail-soft. |
| `normalize.py` | Time alignment (`run_t_start`, `prom_to_long`, `resource_to_agg`, `daemon_to_df`, `provision_to_df`). All series share `t_rel_sec`. |
| `panels.py` | 8 `render_panelN` functions + `RunData` dataclass. Constants imported from `shared.scenarios` (single source of truth). |
| `app.py` | Streamlit entrypoint (`main()`). Sidebar selectors + 8 tabs. |
| `cli.py` | Typer sub-app; `start` shells out to `streamlit run`. |

## Conventions

- **No live monitoring** — this is read-only archival analysis. Prometheus
  (1h retention) remains the live tool.
- **streamlit/plotly isolated here** — deps live in this package's
  `pyproject.toml`, not in root.
- **result.json loaded as plain dict** (`.get()`), not validated against
  `shared.models.experiment.ExperimentResult`, because the shape varies across
  eras and the dashboard is read-only.

## Tests

```bash
uv run pytest apps/dashboard/tests/ -v
```
