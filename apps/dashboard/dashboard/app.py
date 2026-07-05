"""Streamlit entrypoint for the experiment results dashboard.

Run via the CLI (``uv run thesis dashboard start``) or directly:
``streamlit run apps/dashboard/dashboard/app.py``.

Builds a :class:`dashboard.panels.RunData` from the selected run and renders
the 8 panels in tabs. All heavy loading is cached inside ``loader.py`` via
``functools.lru_cache`` keyed on file mtime, so switching tabs is fast.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from dashboard.loader import (
    cached_scan,
    load_k6,
    load_manifest,
    load_provision,
    load_prom,
    load_result,
    load_resource,
)
from dashboard.normalize import (
    daemon_to_df,
    prom_to_long,
    provision_to_df,
    resource_to_agg,
    run_t_start,
)
from dashboard.parser import parse_daemon_log
from dashboard.panels import (
    RunData,
    render_panel1,
    render_panel2,
    render_panel3,
    render_panel4,
    render_panel5,
    render_panel6,
    render_panel7,
    render_panel8,
)


def _repo_root() -> Path:
    """Resolve the repo root as the dashboard package's parent.parent.parent.

    apps/dashboard/dashboard/app.py → dashboard/ → dashboard/ → apps/ → root.
    """
    return Path(__file__).resolve().parents[3]


def build_run_data(run_row: pd.Series, all_runs: pd.DataFrame) -> RunData:
    """Assemble a RunData for one row of the scan table."""
    run_dir = Path(run_row["run_dir"])
    result = load_result(run_dir)
    manifest = load_manifest(run_dir)
    k6 = load_k6(run_dir)
    prom = load_prom(run_dir)
    resource = load_resource(run_dir)
    provision = load_provision(run_dir)

    daemon_parsed = parse_daemon_log(run_dir / "daemon.log")
    daemon_first_ts = daemon_parsed["ts_str"].iloc[0] if not daemon_parsed.empty else None
    t_start = run_t_start(result, daemon_first_ts, prom)

    return RunData(
        run_dir=str(run_dir),
        phase=run_row["phase"],
        batch=run_row["batch"],
        scenario=run_row["scenario"],
        run_id=int(run_row["run_id"]),
        era=run_row["era"],
        result=result,
        manifest=manifest,
        k6=k6,
        t_start=t_start,
        prom_long=prom_to_long(prom, t_start),
        resource_agg=resource_to_agg(resource, t_start),
        provision_df=provision_to_df(provision, t_start),
        daemon_df=daemon_to_df(daemon_parsed, t_start),
        all_runs=all_runs,
    )


def main() -> None:
    st.set_page_config(page_title="Thesis Experiment Dashboard", page_icon="📊", layout="wide")
    st.title("Thesis Experiment Results Dashboard")

    root = _repo_root()

    # --- Sidebar: refresh + selectors ---------------------------------------
    with st.sidebar:
        if st.button("🔄 Refresh experiments", help="Re-scan results/experiments/ for new runs"):
            st.cache_data.clear()
        all_runs = cached_scan(root)
        if all_runs.empty:
            st.warning(f"No runs found under {root / 'results' / 'experiments'}")
            return

        phases = sorted(all_runs["phase"].unique().tolist())
        sel_phase = st.multiselect("Phase", phases, default=phases)
        runs_in_phases = all_runs[all_runs["phase"].isin(sel_phase)] if sel_phase else all_runs

        batches = sorted(runs_in_phases["batch"].unique().tolist())
        sel_batch = st.selectbox("Batch", batches)

        batch_runs = runs_in_phases[runs_in_phases["batch"] == sel_batch]
        scenarios = [s for s in pd.Series(batch_runs["scenario"]).unique().tolist()]
        sel_scenario = st.selectbox("Scenario", scenarios)

        scenario_runs = batch_runs[batch_runs["scenario"] == sel_scenario].sort_values("run_id")
        run_labels = [f"run {int(r)}" for r in scenario_runs["run_id"]]
        sel_run_idx = st.selectbox("Run", range(len(run_labels)), format_func=lambda i: run_labels[i])

    if scenario_runs.empty:
        st.warning("No runs match the selected phase/batch/scenario.")
        return

    run_row = scenario_runs.iloc[sel_run_idx]

    # --- Header -------------------------------------------------------------
    st.caption(
        f"`{run_row['phase']}` · `{run_row['batch']}` · "
        f"`{run_row['scenario']}` · run {int(run_row['run_id'])} · "
        f"**{run_row['era'].upper()}**"
    )

    coverage_cols = ["has_result", "has_prom", "has_resource", "has_provision", "has_daemon_log", "has_k6"]
    coverage = {c.replace("has_", ""): ("✅" if run_row.get(c) else "—") for c in coverage_cols}
    st.caption("Artifacts: " + "  ".join(f"`{k}` {v}" for k, v in coverage.items()))

    # --- Build RunData (cached per run_dir+mtime via loader lru_cache) ------
    ctx = build_run_data(run_row, all_runs)

    # --- Tabs ----------------------------------------------------------------
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
        [
            "1 · Run Browser",
            "2 · KPI Matrix",
            "3 · Timeline",
            "4 · Scaling & Provisioning",
            "5 · Traffic & Weights",
            "6 · Resources",
            "7 · Decisions",
            "8 · Correlation",
        ]
    )
    with tab1:
        render_panel1(st, ctx)
    with tab2:
        render_panel2(st, ctx)
    with tab3:
        render_panel3(st, ctx)
    with tab4:
        render_panel4(st, ctx)
    with tab5:
        render_panel5(st, ctx)
    with tab6:
        render_panel6(st, ctx)
    with tab7:
        render_panel7(st, ctx)
    with tab8:
        render_panel8(st, ctx)


if __name__ == "__main__":
    main()
