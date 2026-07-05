"""Dashboard panels — 8 Plotly-backed render functions sharing one RunData.

Each ``render_panelN(st, ctx)`` writes Streamlit elements for one tab. They
share a :class:`RunData` dataclass (built by ``app.py``) holding all loaded +
normalized frames for the active run.
Constants (SCENARIO_*, SLO_THRESHOLD_MS) are imported from ``shared.scenarios``
— the single source of truth shared with ``apps/analysis`` and ``apps/experiment``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shared.scenarios import SCENARIO_LABELS, SLO_THRESHOLD_MS

# Provision event colors for Panel 4 annotations (dashboard-specific, not shared).

# Provision event colors for Panel 4 annotations.
PROVISION_COLORS = {
    "autoscaler_started": "#4C72B0",  # blue
    "provision_delay_started": "#E06600",  # orange
    "node_created": "#55A868",  # green
}


@dataclass
class RunData:
    """All loaded + normalized frames for one run, consumed by the panels."""

    run_dir: str
    phase: str
    batch: str
    scenario: str
    run_id: int
    era: str
    result: dict | None = None
    manifest: dict | None = None
    k6: dict | None = None
    t_start: float | None = None
    prom_long: pd.DataFrame = field(default_factory=pd.DataFrame)
    resource_agg: pd.DataFrame = field(default_factory=pd.DataFrame)
    provision_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    daemon_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    all_runs: pd.DataFrame = field(default_factory=pd.DataFrame)  # scan table for comparison


def _series(ctx: RunData, metric: str) -> pd.DataFrame:
    """Return the prom_long slice for one metric (may be empty)."""
    if ctx.prom_long.empty:
        return pd.DataFrame(columns=["t_rel_sec", "value"])
    sub = ctx.prom_long[ctx.prom_long["metric"] == metric]
    return sub[["t_rel_sec", "value"]].sort_values("t_rel_sec")


# ===========================================================================
# Panel 1 — Run Browser & Coverage
# ===========================================================================


def render_panel1(st_mod, ctx: RunData) -> None:
    """All runs with era tag + artifact coverage + key KPIs."""
    runs = ctx.all_runs
    if runs.empty:
        st_mod.warning("No experiment runs found under results/experiments/.")
        return

    display = runs.copy()
    # Merge a couple of headline KPIs from each run's result.json (best-effort).
    display["p99_ms"] = ""
    display["throughput_rps"] = ""
    for idx, row in display.iterrows():
        # Lazy import to avoid hard dep at module import time.
        from dashboard.loader import load_result

        result = load_result(row["run_dir"])
        if result:
            display.at[idx, "p99_ms"] = f"{result.get('p99_latency_ms', float('nan')):.1f}"
            display.at[idx, "throughput_rps"] = f"{result.get('throughput_rps', float('nan')):.1f}"

    cols = [
        "phase",
        "batch",
        "scenario",
        "run_id",
        "era",
        "has_result",
        "has_prom",
        "has_resource",
        "has_provision",
        "has_daemon_log",
        "has_k6",
        "p99_ms",
        "throughput_rps",
    ]
    present = [c for c in cols if c in display.columns]
    st_mod.dataframe(display[present], use_container_width=True, hide_index=True)
    st_mod.caption(
        f"{len(display)} runs total · "
        f"{(display['era'] == 'era2').sum()} ERA-2 (full time-series) · "
        f"{(display['era'] == 'era1').sum()} ERA-1 (log/summary only)"
    )


# ===========================================================================
# Panel 2 — KPI Matrix
# ===========================================================================


def _kpi(result: dict, key: str, fmt: str = "{:.2f}") -> str:
    val = result.get(key)
    if val is None:
        return "—"
    try:
        return fmt.format(float(val))
    except (TypeError, ValueError):
        return str(val)


def render_panel2(st_mod, ctx: RunData) -> None:
    """KPI metric cards + batch comparison table."""
    if not ctx.result:
        st_mod.warning("No result.json for this run — KPIs unavailable.")
        return

    r = ctx.result
    col1, col2, col3, col4 = st_mod.columns(4)
    with col1:
        st_mod.metric("p50 latency (ms)", _kpi(r, "p50_latency_ms", "{:.2f}"))
        st_mod.metric("p95 latency (ms)", _kpi(r, "p95_latency_ms", "{:.1f}"))
        st_mod.metric("p99 latency (ms)", _kpi(r, "p99_latency_ms", "{:.1f}"))
    with col2:
        st_mod.metric("Throughput (rps)", _kpi(r, "throughput_rps", "{:.1f}"))
        st_mod.metric("Error rate", _kpi(r, "error_rate", "{:.3f}"))
        st_mod.metric("SLO violations (k6)", _kpi(r, "slo_violations_k6", "{:.0f}"))
    with col3:
        st_mod.metric("Scale-up events", _kpi(r, "scale_up_events", "{:.0f}"))
        st_mod.metric("Scale-down events", _kpi(r, "scale_down_events", "{:.0f}"))
        st_mod.metric("Nodes provisioned", _kpi(r, "nodes_provisioned", "{:.0f}"))
    with col4:
        st_mod.metric("First provision delay (s)", _kpi(r, "first_provision_delay_sec", "{:.1f}"))
        st_mod.metric("Time in serverless (%)", _kpi(r, "time_in_serverless_pct", "{:.1f}"))
        st_mod.metric("Prediction usage (%)", _kpi(r, "prediction_usage_rate", "{:.1f}"))

    st_mod.divider()
    st_mod.subheader("Batch comparison")
    _batch_comparison(st_mod, ctx)


def _batch_comparison(st_mod, ctx: RunData) -> None:
    """Compare KPIs across all runs in the same batch."""
    from dashboard.loader import load_result

    batch_runs = ctx.all_runs[ctx.all_runs["batch"] == ctx.batch]
    if batch_runs.empty:
        return
    rows = []
    for _, run_row in batch_runs.iterrows():
        res = load_result(run_row["run_dir"])
        if not res:
            continue
        rows.append(
            {
                "scenario": SCENARIO_LABELS.get(run_row["scenario"], run_row["scenario"]),
                "run_id": run_row["run_id"],
                "p99_ms": res.get("p99_latency_ms"),
                "throughput_rps": res.get("throughput_rps"),
                "error_rate": res.get("error_rate"),
                "slo_violations": res.get("slo_violations_k6"),
                "scale_out_count": res.get("scale_out_count"),
                "time_in_serverless_pct": res.get("time_in_serverless_pct"),
            }
        )
    if not rows:
        st_mod.info("No run summaries in this batch.")
        return
    df = pd.DataFrame(rows)
    st_mod.dataframe(df, use_container_width=True, hide_index=True)


# ===========================================================================
# Panel 3 — Unified Timeline
# ===========================================================================


def render_panel3(st_mod, ctx: RunData) -> None:
    """Selectable prometheus_export metrics over time."""
    if ctx.prom_long.empty:
        st_mod.warning("No prometheus_export.json time-series for this run (ERA 1 run?).")
        return

    available = sorted(ctx.prom_long["metric"].unique().tolist())
    defaults = [
        m
        for m in (
            "k8s_available_replicas",
            "k8s_desired_replicas",
            "daemon_weight_knative",
            "daemon_decision_latency_ms",
        )
        if m in available
    ]
    selected = st_mod.multiselect("Metrics", available, default=defaults or available[:3])
    use_absolute = st_mod.checkbox("Use absolute UTC time on x-axis", value=False)

    if not selected:
        st_mod.info("Select at least one metric.")
        return

    fig = go.Figure()
    for metric in selected:
        sub = _series(ctx, metric)
        if sub.empty:
            st_mod.warning(f"`{metric}` not captured for this run.")
            continue
        fig.add_trace(
            go.Scatter(
                x=sub["t_rel_sec"] if not use_absolute else ctx.prom_long[ctx.prom_long["metric"] == metric]["dt"],
                y=sub["value"],
                mode="lines+markers",
                name=metric,
            )
        )
    fig.update_layout(
        xaxis_title="seconds since run start" if not use_absolute else "UTC time",
        yaxis_title="value",
        height=520,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st_mod.plotly_chart(fig, use_container_width=True)


# ===========================================================================
# Panel 4 — Scaling & Provisioning Storyboard
# ===========================================================================


def render_panel4(st_mod, ctx: RunData) -> None:
    """Replicas timeline + provision-event annotations + scale markers."""
    if ctx.prom_long.empty:
        st_mod.warning("No time-series for this run (ERA 1 run?).")
        return

    desired = _series(ctx, "k8s_desired_replicas")
    available = _series(ctx, "k8s_available_replicas")
    pending = _series(ctx, "pods_pending_count")

    if desired.empty and available.empty:
        st_mod.warning("No replica series captured for this run.")
        return

    fig = go.Figure()
    if not desired.empty:
        fig.add_trace(
            go.Scatter(
                x=desired["t_rel_sec"],
                y=desired["value"],
                name="desired replicas",
                mode="lines+markers",
                line=dict(dash="dash"),
            )
        )
    if not available.empty:
        fig.add_trace(
            go.Scatter(x=available["t_rel_sec"], y=available["value"], name="available replicas", mode="lines+markers")
        )

    if not pending.empty:
        fig.add_trace(
            go.Scatter(
                x=pending["t_rel_sec"],
                y=pending["value"],
                name="pending pods",
                yaxis="y2",
                mode="lines",
                line=dict(color="#FFB000", width=1),
            )
        )
        fig.update_layout(yaxis2=dict(title="pending pods", overlaying="y", side="right", showgrid=False))

    # Provision event annotations.
    shapes = []
    for _, ev in ctx.provision_df.iterrows():
        color = PROVISION_COLORS.get(ev["event"], "#888888")
        x = ev["t_rel_sec"]
        fig.add_vline(x=x, line=dict(color=color, width=1, dash="dot"))
        fig.add_annotation(
            x=x,
            y=1.0,
            yref="paper",
            text=ev["event"],
            showarrow=False,
            textangle=-90,
            font=dict(size=9, color=color),
        )

    # Shaded bands between pending_detected → node_created.
    pending_ts = ctx.provision_df[ctx.provision_df["event"] == "pending_detected"]["t_rel_sec"].tolist()
    node_ts = ctx.provision_df[ctx.provision_df["event"] == "node_created"]["t_rel_sec"].tolist()
    for i, (p_ts, n_ts) in enumerate(zip(pending_ts, node_ts)):
        shapes.append(
            dict(
                type="rect",
                xref="x",
                yref="paper",
                x0=p_ts,
                x1=n_ts,
                y0=0,
                y1=1,
                fillcolor="#FFB000",
                opacity=0.12,
                layer="below",
                line_width=0,
            )
        )

    # k8s_scale_executed markers from daemon log.
    if not ctx.daemon_df.empty:
        scale_ev = ctx.daemon_df[ctx.daemon_df["event_type"] == "scale_executed"]
        if not scale_ev.empty:
            fig.add_trace(
                go.Scatter(
                    x=scale_ev["t_rel_sec"],
                    y=[0.5] * len(scale_ev),
                    mode="markers",
                    marker=dict(symbol="triangle-up", size=12, color="#C44E52"),
                    name="scale executed",
                    text=scale_ev["reason"],
                )
            )

    fig.update_layout(
        shapes=shapes,
        xaxis_title="seconds since run start",
        yaxis_title="replicas",
        height=560,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st_mod.plotly_chart(fig, use_container_width=True)

    if not ctx.provision_df.empty:
        st_mod.caption(
            "Shaded bands = provision delay (pending_detected → node_created). Vertical lines = autoscaler events."
        )


# ===========================================================================
# Panel 5 — Traffic, Latency & Weights Overlay
# ===========================================================================


def render_panel5(st_mod, ctx: RunData) -> None:
    """RPS + p99 (prom or HAProxy-est fallback) vs k3s/knative weights."""
    rps = _series(ctx, "prom_rps")
    prom_p99 = _series(ctx, "prom_p99_ms")
    w_k3s = _series(ctx, "daemon_weight_k3s")
    w_knative = _series(ctx, "daemon_weight_knative")

    # HAProxy p99_est fallback from daemon log (usually the only latency source).
    haproxy = pd.DataFrame()
    if not ctx.daemon_df.empty:
        h = ctx.daemon_df[ctx.daemon_df["event_type"] == "haproxy_latency"]
        if not h.empty:
            haproxy = h[["t_rel_sec", "p99_est"]].rename(columns={"p99_est": "value"})

    has_latency = not prom_p99.empty or not haproxy.empty
    has_traffic = not rps.empty
    has_weights = not w_k3s.empty or not w_knative.empty

    if not (has_latency or has_traffic or has_weights):
        st_mod.warning("No traffic/latency/weight data for this run.")
        return

    fig = go.Figure()
    if has_traffic:
        fig.add_trace(go.Scatter(x=rps["t_rel_sec"], y=rps["value"], name="rps", mode="lines", yaxis="y"))
    if not prom_p99.empty:
        fig.add_trace(
            go.Scatter(x=prom_p99["t_rel_sec"], y=prom_p99["value"], name="prom p99 (ms)", mode="lines", yaxis="y")
        )
    if not haproxy.empty and prom_p99.empty:
        fig.add_trace(
            go.Scatter(
                x=haproxy["t_rel_sec"],
                y=haproxy["value"],
                name="HAProxy p99_est (ms)",
                mode="lines+markers",
                yaxis="y",
                line=dict(color="#C44E52"),
            )
        )
        st_mod.info("prom_p99_ms empty — using HAProxy p99_est from daemon.log.")

    # SLO threshold line.
    fig.add_hline(
        y=SLO_THRESHOLD_MS, line=dict(color="red", dash="dot", width=1), annotation_text=f"SLO {SLO_THRESHOLD_MS:.0f}ms"
    )

    if not w_k3s.empty:
        fig.add_trace(
            go.Scatter(
                x=w_k3s["t_rel_sec"],
                y=w_k3s["value"],
                name="weight k3s",
                mode="lines",
                yaxis="y2",
                line=dict(color="#4C72B0"),
            )
        )
    if not w_knative.empty:
        fig.add_trace(
            go.Scatter(
                x=w_knative["t_rel_sec"],
                y=w_knative["value"],
                name="weight knative",
                mode="lines",
                yaxis="y2",
                line=dict(color="#DD8452"),
            )
        )

    fig.update_layout(
        xaxis_title="seconds since run start",
        yaxis=dict(title="rps / latency ms"),
        yaxis2=dict(title="weight %", overlaying="y", side="right", showgrid=False, range=[-5, 105]),
        height=560,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st_mod.plotly_chart(fig, use_container_width=True)


# ===========================================================================
# Panel 6 — Resource Utilization by Backend
# ===========================================================================


def render_panel6(st_mod, ctx: RunData) -> None:
    """Aggregated CPU / memory / pod count by backend."""
    if ctx.resource_agg.empty:
        st_mod.warning("No resource_utilization.json for this run.")
        return

    agg = ctx.resource_agg
    for metric, title, ylab in [
        ("cpu_total", "CPU millicores by backend", "cpu (m)"),
        ("mem_total", "Memory MiB by backend", "memory (MiB)"),
        ("pod_count", "Pod count by backend", "pods"),
    ]:
        fig = px.area(
            agg,
            x="t_rel_sec",
            y=metric,
            color="backend",
            title=title,
            labels={"t_rel_sec": "seconds since run start"},
        )
        fig.update_layout(height=360, hovermode="x unified")
        st_mod.plotly_chart(fig, use_container_width=True)


# ===========================================================================
# Panel 7 — Decision & Prediction Inspector
# ===========================================================================


def render_panel7(st_mod, ctx: RunData) -> None:
    """Filterable table of parsed daemon events."""
    if ctx.daemon_df.empty:
        st_mod.warning("No daemon.log events parsed for this run.")
        return

    df = ctx.daemon_df.copy()
    event_types = ["All"] + sorted(df["event_type"].dropna().unique().tolist())
    sel = st_mod.selectbox("Event type", event_types, index=0)
    if sel != "All":
        df = df[df["event_type"] == sel]
    search = st_mod.text_input("Search (action/reason)")
    if search:
        mask = df.get("reason", "").astype(str).str.contains(search, case=False, na=False) | df.get(
            "action", ""
        ).astype(str).str.contains(search, case=False, na=False)
        df = df[mask]

    show_cols = [
        c
        for c in [
            "t_rel_sec",
            "event_type",
            "action",
            "k3s_weight",
            "knative_weight",
            "current_replicas",
            "target_replicas",
            "p99_est",
            "gru_confidence",
            "gru_predicted",
            "reason",
        ]
        if c in df.columns
    ]
    st_mod.dataframe(df[show_cols].sort_values("t_rel_sec"), use_container_width=True, hide_index=True)
    st_mod.caption(f"{len(df)} events")


# ===========================================================================
# Panel 8 — Correlation Explorer
# ===========================================================================


def _build_aligned_grid(ctx: RunData) -> pd.DataFrame:
    """Build a wide table of metrics indexed by rounded t_rel_sec (15s grid)."""
    grid = pd.DataFrame()
    if not ctx.prom_long.empty:
        wide = ctx.prom_long.pivot_table(index="t_rel_sec", columns="metric", values="value", aggfunc="last")
        wide.index = (wide.index // 15 * 15).astype(int)  # snap to 15s grid
        grid = wide.groupby(level=0).last()

    # Add HAProxy p99_est when prom_p99_ms is missing.
    if not ctx.daemon_df.empty and ("prom_p99_ms" not in grid.columns or grid["prom_p99_ms"].isna().all()):
        h = ctx.daemon_df[ctx.daemon_df["event_type"] == "haproxy_latency"][["t_rel_sec", "p99_est"]].copy()
        if not h.empty:
            h["bucket"] = (h["t_rel_sec"] // 15 * 15).astype(int)
            h_series = h.groupby("bucket")["p99_est"].last()
            grid["haproxy_p99_est"] = h_series
            grid["p99"] = grid.get("prom_p99_ms")
            grid["p99"] = grid["p99"].fillna(grid["haproxy_p99_est"])

    # Add resource aggregates.
    if not ctx.resource_agg.empty:
        res = ctx.resource_agg.copy()
        res["bucket"] = (res["t_rel_sec"] // 15 * 15).astype(int)
        res_wide = res.pivot_table(index="bucket", columns="backend", values=["cpu_total", "pod_count"], aggfunc="last")
        if not res_wide.empty:
            res_wide.columns = ["_".join(map(str, c)) for c in res_wide.columns]
            grid = grid.join(res_wide, how="outer")

    return grid.sort_index()


def render_panel8(st_mod, ctx: RunData) -> None:
    """Correlation heatmap + lagged scatter."""
    grid = _build_aligned_grid(ctx)
    if grid.empty or grid.shape[1] < 2:
        st_mod.warning("Not enough overlapping series to compute correlations for this run.")
        return

    st_mod.subheader("Correlation heatmap (aligned 15s samples)")
    corr_cols = [
        c
        for c in [
            "prom_rps",
            "p99",
            "haproxy_p99_est",
            "k8s_available_replicas",
            "daemon_weight_knative",
            "cpu_total_k8s",
            "cpu_total_knative",
            "pod_count_k8s",
            "pod_count_knative",
            "pods_pending_count",
            "daemon_decision_latency_ms",
        ]
        if c in grid.columns
    ]
    if len(corr_cols) < 2:
        st_mod.info(f"Only {len(corr_cols)} numeric series available — need ≥2 for correlation.")
        return

    corr = grid[corr_cols].corr(numeric_only=True)
    fig_heat = px.imshow(corr, color_continuous_scale="RdBu", zmin=-1, zmax=1, title="Pearson correlation")
    fig_heat.update_layout(height=520)
    st_mod.plotly_chart(fig_heat, use_container_width=True)

    st_mod.divider()
    st_mod.subheader("Lagged scatter")
    x_options = [c for c in corr_cols if c != "p99" and c != "haproxy_p99_est"]
    default_x = next(
        (c for c in ["prom_rps", "k8s_available_replicas", "daemon_weight_knative"] if c in x_options),
        x_options[0] if x_options else None,
    )
    x_metric = st_mod.selectbox("X metric", x_options, index=x_options.index(default_x) if default_x else 0)
    lag = st_mod.select_slider("Lag (s) — y = p99 at t+lag", options=[0, 15, 30, 45, 60], value=0)
    y_col = "p99" if "p99" in grid.columns else "haproxy_p99_est"

    if x_metric and y_col:
        lagged = grid[[x_metric]].join(grid[[y_col]].shift(-lag // 15)).dropna()
        if not lagged.empty:
            import importlib.util

            has_statsmodels = importlib.util.find_spec("statsmodels") is not None
            fig_scat = px.scatter(
                lagged,
                x=x_metric,
                y=y_col,
                trendline="ols" if has_statsmodels else None,
                labels={x_metric: x_metric, y_col: f"{y_col} (t+{lag}s)"},
                title=f"Association: {x_metric} vs {y_col} lagged {lag}s",
            )
            fig_scat.update_layout(height=420)
            st_mod.plotly_chart(fig_scat, use_container_width=True)
            st_mod.caption(
                "Label reads as 'association (lagged)', not causation — provisioning/routing effects are delayed and workload-confounded."
            )
        else:
            st_mod.info("No overlapping samples after applying the lag.")
