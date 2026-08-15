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


def _paired(repo_root: Path, bundle: str) -> tuple[float, float]:
    """Return (cohens_d_paired, permutation_p_value) from a paired_analysis.json."""
    p = _phase_b_dir(repo_root, bundle) / "paired_analysis.json"
    prim = _read_json(p)["primary"]
    return float(prim["cohens_d_paired"]), float(prim["permutation_p_value"])


# ---------------------------------------------------------------------------
# fig04_6 — H2 effect-size forest plot across replication batches
# ---------------------------------------------------------------------------
def _fig_replication_batches(repo_root: Path, out_dir: Path) -> Path:
    # Effect sizes (Cohen's d paired, S4 vs S3; negative = S4 better).
    d_def, p_def = _paired(repo_root, DEFINITIVE_PAIRED)
    d_run1, p_run1 = _paired(repo_root, PAIRED_RUN1)
    d_run2, p_run2 = _paired(repo_root, PAIRED_RUN2)

    # n=5 RUN3 S4-vs-S3: report.md — Cohen's d -1.300, Mann-Whitney p 0.0317.
    d_run3, p_run3 = -1.300, 0.0317

    labels = [
        "Definitive\n(07-14, n=5)",
        "RUN1\n(08-08 19:51, n=5)",
        "RUN2\n(08-08 23:37, n=5)",
        "RUN3\n(08-09 replay, n=5)",
    ]
    d_values = [d_def, d_run1, d_run2, d_run3]
    p_values = [p_def, p_run1, p_run2, p_run3]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ypos = np.arange(len(labels))[::-1]

    ax.axvline(0, color="#999999", linewidth=1.0, zorder=1)

    for y, d, p in zip(ypos, d_values, p_values):
        color = "#2ca02c" if p < 0.05 else "#bdbdbd"
        ax.errorbar(
            d,
            y,
            xerr=0.0,
            fmt="o",
            markersize=11,
            markerfacecolor=color,
            markeredgecolor="#222222",
            markeredgewidth=0.8,
            zorder=3,
        )
        ax.text(
            d + 0.06,
            y,
            f"d = {d:.2f}\np = {p:.3f}",
            va="center",
            ha="left",
            fontsize=9,
            color="#222222",
        )

    ax.set_yticks(ypos)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Cohen's d (paired, S4 vs S3) — negative favours S4")
    ax.set_title("H2 effect size across replication batches")
    ax.set_xlim(-1.7, 0.7)
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    ax.axvspan(-1.7, 0, color="#2ca02c", alpha=0.05, zorder=0)
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
