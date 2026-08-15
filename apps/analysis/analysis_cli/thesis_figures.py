"""Generate the single matplotlib thesis figure (Chapter 4).

Five of the six figures are rendered natively in Typst via
``thesis-typst/src/content/figures.typ`` (cetz/cetz-plot + primaviz). Only the
H2 effect-size forest plot — which has no first-class native primitive — is
generated here as a matplotlib PNG.

Every number is read from the real experiment bundles; nothing is fabricated.

Data sources (all under ``results/experiments/phase-b/``):

- ``2026-07-14_clarknet-tuned-paired-n5/paired_analysis.json`` — definitive
  paired H2 (d = -1.26, p = 0.030).
- ``2026-08-08_paired-h2_195150/paired_analysis.json`` — replication RUN1
  (d = -0.050, p = 0.436).
- ``2026-08-08_paired-h2_233726/paired_analysis.json`` — replication RUN2
  (d = -0.505, p = 0.062).
- ``2026-08-09_clarknet-replay_032257/report.md`` — n=5 RUN3 S4-vs-S3
  (d = -1.300, Mann-Whitney p = 0.032).

Run::

    uv run python -m analysis_cli.thesis_figures
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------------------
# Constants (bundle names — single source of truth)
# ---------------------------------------------------------------------------
DEFINITIVE_PAIRED = "2026-07-14_clarknet-tuned-paired-n5"
PAIRED_RUN1 = "2026-08-08_paired-h2_195150"
PAIRED_RUN2 = "2026-08-08_paired-h2_233726"

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


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _phase_b_dir(repo_root: Path, bundle: str) -> Path:
    return repo_root / "results" / "experiments" / "phase-b" / bundle


def _paired_stats(repo_root: Path, bundle: str) -> dict:
    """Return mean-difference + paired CI + d + p from a paired_analysis.json."""
    p = _phase_b_dir(repo_root, bundle) / "paired_analysis.json"
    prim = _read_json(p)["primary"]
    return {
        "mean_diff": float(prim["mean_difference"]),
        "ci_lower": float(prim["paired_ci_lower"]),
        "ci_upper": float(prim["paired_ci_upper"]),
        "d": float(prim["cohens_d_paired"]),
        "p": float(prim["permutation_p_value"]),
    }


# ---------------------------------------------------------------------------
# fig04_6 — H2 forest plot across replication batches.
# Point estimate = S4−S3 mean-difference (ms); whiskers = 95% CI. Negative = S4
# faster. CI is on the ms scale in every source (paired CI for the three paired
# bundles; Welch CI for the n=5 replay RUN3).
# ---------------------------------------------------------------------------
def _fig_replication_batches(repo_root: Path, out_dir: Path) -> Path:
    st_def = _paired_stats(repo_root, DEFINITIVE_PAIRED)
    st_run1 = _paired_stats(repo_root, PAIRED_RUN1)
    st_run2 = _paired_stats(repo_root, PAIRED_RUN2)

    # RUN3 (n=5 replay) S4-vs-S3 from report.md: Welch mean diff −52.50 ms,
    # 95% CI [−102.60, −11.81], Cohen's d −1.300, Mann-Whitney p 0.0317.
    st_run3 = {
        "mean_diff": -52.50,
        "ci_lower": -102.60,
        "ci_upper": -11.81,
        "d": -1.300,
        "p": 0.0317,
    }

    labels = [
        "Definitive\n(07-14, n=5)",
        "RUN1\n(08-08 19:51, n=5)",
        "RUN2\n(08-08 23:37, n=5)",
        "RUN3\n(08-09 replay, n=5)",
    ]
    stats = [st_def, st_run1, st_run2, st_run3]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ypos = np.arange(len(labels))[::-1]

    ax.axvline(0, color="#999999", linewidth=1.0, zorder=1)

    for y, s in zip(ypos, stats):
        color = "#2ca02c" if s["p"] < 0.05 else "#bdbdbd"
        # Asymmetric error: [mean−CI_lower, CI_upper−mean] in ms.
        xerr = [[s["mean_diff"] - s["ci_lower"]], [s["ci_upper"] - s["mean_diff"]]]
        ax.errorbar(
            s["mean_diff"],
            y,
            xerr=xerr,
            fmt="o",
            markersize=11,
            markerfacecolor=color,
            markeredgecolor="#222222",
            markeredgewidth=0.8,
            elinewidth=1.6,
            capsize=4,
            capthick=1.2,
            ecolor="#555555",
            zorder=3,
        )
        ax.text(
            s["mean_diff"] + 4,
            y,
            f"d = {s['d']:.2f}\np = {s['p']:.3f}",
            va="center",
            ha="left",
            fontsize=9,
            color="#222222",
        )

    ax.set_yticks(ypos)
    ax.set_yticklabels(labels)
    ax.set_xlabel("S4 − S3 mean p99 difference (ms) — negative favours S4")
    ax.set_title("H2 across replication batches (point = mean diff, whiskers = 95% CI)")
    ax.set_xlim(-190, 95)
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    ax.axvspan(-190, 0, color="#2ca02c", alpha=0.05, zorder=0)
    fig.tight_layout()

    out = out_dir / "fig04_6_replication_batches.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def generate_thesis_figures(repo_root: str | Path, output_dir: str | Path) -> list[Path]:
    """Generate the single matplotlib PNG figure (the H2 forest plot).

    The other five figures are native Typst (cetz/cetz-plot/primaviz) and live
    in ``thesis-typst/src/content/figures.typ``; they are not produced here.

    Returns the list of PNG paths written.
    """
    repo_root = Path(repo_root)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    return [
        _fig_replication_batches(repo_root, out_dir),
    ]


if __name__ == "__main__":
    import sys

    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else repo / "thesis-typst" / "src" / "figures"
    written = generate_thesis_figures(repo, out)
    for p in written:
        print(f"{p}  ({p.stat().st_size} bytes)")
