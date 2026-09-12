# apps/dashboard

Interactive Streamlit + Plotly dashboard for archival analysis of thesis experiment results. Reads `results/experiments/` directly: no live monitoring, no Prometheus, no Grafana. Read-only.

## Module map

| Path | Responsibility |
|---|---|
| `dashboard/loader.py` | Artifact scanner (`scan_experiments`) + per-run JSON loaders (`load_result`/`load_prom`/...). NaN/Inf sanitized. Cached via `functools.lru_cache`. |
| `dashboard/parser.py` | `parse_daemon_log`: regex extraction of routing/scaling/GRU/HAProxy/weight-change events. Fail-soft. |
| `dashboard/normalize.py` | Time alignment (`run_t_start`, `prom_to_long`, `resource_to_agg`, `daemon_to_df`, `provision_to_df`). All series share `t_rel_sec`. |
| `dashboard/panels.py` | 8 `render_panelN` functions + `RunData` dataclass. Constants imported from `shared.scenarios`. |
| `dashboard/app.py` | Streamlit entrypoint (`main()`): sidebar selectors + 8 tabs. |
| `dashboard/cli.py` | Typer sub-app; `start` shells out to `streamlit run` (Streamlit must own its process). |

## Module direction

- **May import:** `shared` (scenario constants in `panels.py`), streamlit, plotly, pandas, numpy.
- **Must never import:** `shared.artifacts` (the importlinter protected contract allows only `experiment`, `analysis`, `analysis_cli` to import it; `loader.py` reads run files directly, a known piece of deferred work), and never `experiment`, `routing`, `prediction`, `infra`, `analysis`, `analysis_cli`, `cli`.
- **Where new code goes:**
  - New panel → `render_panelN` in `dashboard/panels.py` + its tab in `app.py`
  - New artifact format to read → loader in `dashboard/loader.py`, alignment in `dashboard/normalize.py`
  - New daemon-log event type → regex in `dashboard/parser.py`
  - New test → `apps/dashboard/tests/`

## Tests

`apps/dashboard/tests/`; hermetic, no live tier (the package is read-only over archived results). 16 tests in `test_loader.py`, `test_normalize.py`, `test_parser.py`. Run with:

```bash
uv run python -m pytest apps/dashboard/tests -q
```

## Commands it contributes

`thesis dashboard start` (default port 28555, host `0.0.0.0`). Entry point: `thesis-dashboard` → `dashboard.cli:app`.

```bash
uv run thesis dashboard start
uv run thesis dashboard start --port 28666 --host 0.0.0.0
```

Bind `0.0.0.0` so the dashboard is reachable over Tailscale. Auth relies on Tailscale ACL only. For tighter exposure, firewall port 28555 to the `tailscale0` interface.

## Data eras

- **ERA 2** (2026-07-03+): full JSON bundles. Time-series timelines, scaling storyboards, and the correlation explorer all work.
- **ERA 1** (pre-2026-07-03): `daemon.log` + `meta.yaml` only. Panels 3-6 degrade to "no time-series data"; KPIs come from `results_final.json`; the Decision Inspector still parses `daemon.log`.

## Invariants

- No live monitoring: read-only archival analysis. Prometheus (1 h retention) remains the live tool.
- streamlit/plotly are isolated here; their deps live in this package's `pyproject.toml`, not in root.
- `result.json` is loaded as a plain dict (`.get()`), not validated against `shared.models.experiment.ExperimentResult`, because the shape varies across eras and the dashboard is read-only.
