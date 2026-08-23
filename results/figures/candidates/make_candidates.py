#!/usr/bin/env python
"""Generate candidate thesis figures from REAL experiment data only.

Sources (no fabricated numbers):
  - results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5/  (definitive paired H2 bundle, 5x S3 + 5x S4)
      * <run>/prometheus/prometheus_export.json   daemon_weight_k3s / daemon_weight_knative series [epoch, value]
      * <run>/daemon.log                          controller_decision_v3 / GRU prediction received lines
      * <run>/result.json                         t_start anchor + aggregate fields
      * <run>/events.jsonl                        daemon_started epoch (timezone-offset validation)
  - results/experiments/tuning/gru_hpo_2026-07-09_224736/study.json  (context: tuned GRU hyperparameters)

Outputs (this directory):
  fig_cand1_routing_weights.png     S3 vs S4 routing-weight timeline
  fig_cand2_gru_pred_vs_actual.png  S4 GRU forecast vs observed load
  spearman_correlations.csv         long-format rho/p for all varying field pairs

Run:  uv run python results/figures/candidates/make_candidates.py
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BUNDLE = REPO / "results" / "experiments" / "phase-b" / "2026-07-14_clarknet-tuned-paired-n5"
HPO = REPO / "results" / "experiments" / "tuning" / "gru_hpo_2026-07-09_224736" / "study.json"

# Same style block as apps/analysis/analysis_cli/thesis_figures.py
plt.rcParams.update(
    {
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.dpi": 150,
    }
)

C_K3S = "#1f77b4"
C_KNATIVE = "#d62728"
C_OBS = "#1f77b4"
C_PRED = "#d62728"
C_REACTIVE = "#ff7f0e"
C_PREDICTIVE = "#9467bd"

RE_CTRL = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[info\s*\] controller_decision_v3\s+"
    r"action=(?P<action>\w+).*?current_load=(?P<load>[\d.]+).*?predicted_load=(?P<pred>[\d.]+)"
)
RE_GRU = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[debug\s*\] GRU prediction received\s+"
    r"confidence=(?P<conf>[\d.]+) latency_ms=(?P<lat>[\d.]+) predicted=(?P<pred>[\d.]+)"
)
RE_WEIGHTS = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[info\s*\] Weights updated\s+k3s=(?P<k3s>\d+) knative=(?P<kn>\d+)\s*$"
)
RE_ALGO2 = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[info\s*\] algorithm2_decision\s+"
    r".*?observed_load=(?P<load>[\d.]+)"
)


def load_json(p: Path):
    return json.loads(p.read_text())


def parse_daemon_log(path: Path) -> dict[str, list[dict]]:
    """Extract controller decisions / GRU predictions / weight updates with naive local timestamps."""
    out: dict[str, list[dict]] = {"ctrl": [], "gru": [], "weights": [], "algo2": []}
    for line in path.read_text().splitlines():
        m = RE_CTRL.match(line)
        if m:
            out["ctrl"].append(
                {
                    "ts": datetime.strptime(m["ts"], "%Y-%m-%d %H:%M:%S"),
                    "action": m["action"],
                    "current_load": float(m["load"]),
                    "predicted_load": float(m["pred"]),
                }
            )
            continue
        m = RE_GRU.match(line)
        if m:
            out["gru"].append(
                {
                    "ts": datetime.strptime(m["ts"], "%Y-%m-%d %H:%M:%S"),
                    "predicted": float(m["pred"]),
                    "confidence": float(m["conf"]),
                }
            )
            continue
        m = RE_WEIGHTS.match(line)
        if m:
            out["weights"].append(
                {
                    "ts": datetime.strptime(m["ts"], "%Y-%m-%d %H:%M:%S"),
                    "k3s": int(m["k3s"]),
                    "knative": int(m["kn"]),
                }
            )
        m = RE_ALGO2.match(line)
        if m:
            out["algo2"].append(
                {
                    "ts": datetime.strptime(m["ts"], "%Y-%m-%d %H:%M:%S"),
                    "observed_load": float(m["load"]),
                }
            )
    return out


def tz_offset_seconds(run_dir: Path) -> float:
    """daemon.log timestamps are local; events.jsonl are UTC. Return local->UTC epoch offset.

    Validated against daemon_started event; asserts a whole-hour offset (TZ), not ad-hoc.
    """
    ev = {}
    for line in (run_dir / "events.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        ev[d["event"]] = d["timestamp"]
    started = datetime.fromisoformat(ev["daemon_started"]).timestamp()
    # first timestamped line of daemon.log
    first = None
    for line in (run_dir / "daemon.log").read_text().splitlines():
        m = re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
        if m:
            first = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
            break
    assert first is not None, f"no timestamped line in {run_dir}/daemon.log"
    off = started - first.replace(tzinfo=timezone.utc).timestamp()
    # first log line is 'Starting routing daemon' (~0.5 s after event); allow 2 s slop on a whole hour
    assert abs(off - round(off / 3600) * 3600) < 2.0, f"suspicious tz offset {off}s for {run_dir}"
    return round(off / 3600) * 3600


def series_xy(run_dir: Path, key: str, t0: float) -> tuple[np.ndarray, np.ndarray]:
    data = load_json(run_dir / "prometheus" / "prometheus_export.json")[key]
    arr = np.asarray(data, dtype=float)
    return arr[:, 0] - t0, arr[:, 1]


def events_rel(run: dict, off: float, t0: float) -> dict[str, list[dict]]:
    """Convert parsed log events to seconds-from-run-start."""
    # naive log timestamps are treated as UTC explicitly (machine-local .timestamp()
    # would silently shift by the analysis host's TZ, e.g. -7 h on this box)
    res: dict[str, list[dict]] = {}
    for kind in ("ctrl", "gru", "weights", "algo2"):
        res[kind] = [dict(e, t=e["ts"].replace(tzinfo=timezone.utc).timestamp() + off - t0) for e in run[kind]]
        if res[kind]:
            lo, hi = min(e["t"] for e in res[kind]), max(e["t"] for e in res[kind])
            assert -300 <= lo and hi <= 1800, f"{kind} events out of run window: [{lo:.0f}, {hi:.0f}] s"
    return res


# ---------------------------------------------------------------------------
# Figure 1 — routing-weight timeline (S3 run1 top, S4 run1 bottom)
# ---------------------------------------------------------------------------
def fig1() -> Path:
    panels = [
        ("s3-hybrid-reactive_run1", "S3 — hybrid-reactive, run 1 (definitive bundle)"),
        ("s4-hybrid-predictive_run1", "S4 — hybrid-predictive, run 1 (definitive bundle)"),
    ]
    fig, axes = plt.subplots(2, 1, figsize=(9.5, 6.2), sharex=True)
    summary = {}
    for ax, (run_name, title) in zip(axes, panels):
        rd = BUNDLE / run_name
        res = load_json(rd / "result.json")
        t0 = float(res["t_start"])
        off = tz_offset_seconds(rd)
        parsed = parse_daemon_log(rd / "daemon.log")
        ev = events_rel(parsed, off, t0)

        xk, yk = series_xy(rd, "daemon_weight_k3s", t0)
        xn, yn = series_xy(rd, "daemon_weight_knative", t0)
        assert len(xk) > 0 and len(xn) > 0, f"empty weight series in {run_name}"

        ax.step(xk, yk, where="post", color=C_K3S, linewidth=1.8, label=f"weight k3s (n={len(xk)} samples)")
        ax.step(xn, yn, where="post", color=C_KNATIVE, linewidth=1.8, label=f"weight Knative (n={len(xn)})")

        reactive = [e["t"] for e in ev["ctrl"] if e["action"] == "REACTIVE"]
        predictive = [e["t"] for e in ev["ctrl"] if e["action"] == "PREDICTIVE"]
        if reactive:
            ax.plot(
                reactive,
                [104] * len(reactive),
                linestyle="none",
                marker="v",
                markersize=6,
                color=C_REACTIVE,
                label=f"REACTIVE burst-routing decision (n={len(reactive)})",
            )
        if predictive:
            for t in predictive:
                ax.axvline(t, color=C_PREDICTIVE, linestyle="--", linewidth=1.2, alpha=0.85, zorder=1)
            ax.plot(
                [],
                [],
                color=C_PREDICTIVE,
                linestyle="--",
                linewidth=1.2,
                label=f"PREDICTIVE decision (n={len(predictive)})",
            )

        ax.set_ylim(-4, 112)
        ax.set_ylabel("routing weight (%)")
        ax.set_title(f"{title} — REACTIVE n={len(reactive)}, PREDICTIVE n={len(predictive)}")
        ax.grid(axis="y", linestyle=":", alpha=0.5)
        summary[run_name] = {
            "weight_samples": len(xk),
            "k3s_weight_min_max": [float(yk.min()), float(yk.max())],
            "knative_weight_min_max": [float(yn.min()), float(yn.max())],
            "reactive_n": len(reactive),
            "predictive_n": len(predictive),
            "weights_updated_lines": len(ev["weights"]),
            "t_end_sec": float(xk[-1]),
        }
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.005), ncol=2, frameon=False)
    out = HERE / "fig_cand1_routing_weights.png"
    fig.savefig(out)
    print("FIG1 summary:", json.dumps(summary, indent=1))
    return out


# ---------------------------------------------------------------------------
# Figure 2 — GRU predicted vs observed load (S4 run1)
# ---------------------------------------------------------------------------
def fig2() -> Path:
    run_name = "s4-hybrid-predictive_run1"
    rd = BUNDLE / run_name
    res = load_json(rd / "result.json")
    t0 = float(res["t_start"])
    off = tz_offset_seconds(rd)
    ev = events_rel(parse_daemon_log(rd / "daemon.log"), off, t0)

    a2_t = np.array([e["t"] for e in ev["algo2"]])
    a2_y = np.array([e["observed_load"] for e in ev["algo2"]])
    obs_t = np.array([e["t"] for e in ev["ctrl"]])
    obs_y = np.array([e["current_load"] for e in ev["ctrl"]])
    pred_t = np.array([e["t"] for e in ev["gru"]])
    pred_y = np.array([e["predicted"] for e in ev["gru"]])
    predictive_t = [e["t"] for e in ev["ctrl"] if e["action"] == "PREDICTIVE"]

    assert len(pred_t) > 0, "no GRU prediction lines found"
    print(
        f"FIG2 {run_name}: algo2 per-cycle observed={len(a2_t)} "
        f"range=[{a2_y.min():.1f},{a2_y.max():.1f}] RPS; controller current_load n={len(obs_t)} "
        f"range=[{obs_y.min():.1f},{obs_y.max():.1f}] RPS; "
        f"GRU preds={len(pred_t)} range=[{pred_y.min():.0f},{pred_y.max():.0f}] RPS; "
        f"PREDICTIVE decisions={len(predictive_t)} (result.json predictive_count={res['predictive_count']}, "
        f"gru_predictions_used={res['gru_predictions_used']})"
    )

    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    ax.plot(
        a2_t,
        a2_y,
        color=C_OBS,
        linewidth=1.6,
        label=f"observed load (algorithm2_decision observed_load, per 15 s cycle, n={len(a2_t)})",
    )
    ax.plot(
        obs_t,
        obs_y,
        color="#08306b",
        linewidth=0,
        marker="x",
        markersize=6,
        label=f"routing controller current_load (n={len(obs_t)})",
    )
    ax.plot(
        pred_t,
        pred_y,
        color=C_PRED,
        linewidth=0,
        marker="o",
        markersize=4,
        label=f"GRU point forecast received (n={len(pred_t)})",
    )
    for t in predictive_t:
        ax.axvline(t, color=C_PREDICTIVE, linestyle="--", linewidth=1.3, alpha=0.9)
    ax.plot(
        [], [], color=C_PREDICTIVE, linestyle="--", linewidth=1.3, label=f"PREDICTIVE decision (n={len(predictive_t)})"
    )
    ax.set_xlabel("seconds from run start (t_start of result.json)")
    ax.set_ylabel("load (RPS)")
    ax.set_title(f"{run_name} (definitive bundle) — GRU forecast vs observed load")
    ax.grid(linestyle=":", alpha=0.5)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, frameon=False)
    fig.tight_layout()
    out = HERE / "fig_cand2_gru_pred_vs_actual.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Analysis — Spearman correlations across the 10 definitive runs
# ---------------------------------------------------------------------------
FIELDS = [
    "throughput_rps",
    "p99_latency_ms",
    "slo_violations_k6",
    "time_in_serverless_pct",
    "knative_active_seconds",
    "k8s_replica_seconds",
    "scale_out_count",
    "predictive_count",
    "desired_replicas_final",
    "error_rate",
]


def spearman() -> Path:
    runs = sorted(p for p in BUNDLE.iterdir() if p.is_dir())
    rows = []
    for rd in runs:
        r = load_json(rd / "result.json")
        rows.append({"run": rd.name, **{f: r.get(f) for f in FIELDS}})
    assert len(rows) == 10, f"expected 10 runs, got {len(rows)}"

    data = {f: np.array([row[f] for row in rows], dtype=float) for f in FIELDS}
    varying = [f for f in FIELDS if np.ptp(data[f]) > 0]
    degenerate = [f for f in FIELDS if f not in varying]
    print(f"Varying fields ({len(varying)}): {varying}")
    print(f"Degenerate (zero variance, excluded): {degenerate}")
    for f in degenerate:
        print(f"  {f} = {data[f][0]} in all 10 runs")

    mat = np.column_stack([data[f] for f in varying])
    rho, p = spearmanr(mat)

    lines = ["var_i,var_j,n,rho,p"]
    print("\nSpearman (n=10, two-sided):")
    for i, fi in enumerate(varying):
        for j, fj in enumerate(varying):
            if j <= i:
                continue
            print(f"  {fi} ~ {fj}: rho={rho[i, j]:+.3f}  p={p[i, j]:.4f}")
            lines.append(f"{fi},{fj},10,{rho[i, j]:.4f},{p[i, j]:.5f}")
    out = HERE / "spearman_correlations.csv"
    out.write_text("\n".join(lines) + "\n")

    # per-scenario quick stats for the write-up
    for scen in ("s3-hybrid-reactive", "s4-hybrid-predictive"):
        sub = [row for row in rows if row["run"].startswith(scen)]
        print(
            f"{scen}: p99 median={np.median([r['p99_latency_ms'] for r in sub]):.1f} ms, "
            f"SLO viol median={np.median([r['slo_violations_k6'] for r in sub]):.0f}, "
            f"serverless% median={np.median([r['time_in_serverless_pct'] for r in sub]):.1f}, "
            f"scale_out median={np.median([r['scale_out_count'] for r in sub]):.0f}"
        )
    return out


def main() -> None:
    hpo = load_json(HPO)
    print(
        "GRU HPO context (study.json): best_trial={b} best_rmse_pct={r:.3f} data_source={s} best_params={p}".format(
            b=hpo["best_trial"], r=hpo["best_rmse_pct"], s=hpo["data_source"], p=hpo["best_params"]
        )
    )
    for fn in (fig1, fig2, spearman):
        out = fn()
        print(f"wrote {out.name}  ({out.stat().st_size} bytes)\n")


if __name__ == "__main__":
    main()
