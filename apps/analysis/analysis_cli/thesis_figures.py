"""Generate the single matplotlib thesis figure (Chapter 4).

Five of the six figures are rendered natively in Typst via
``thesis-typst/src/content/figures.typ`` (cetz/cetz-plot + primaviz). Only the
H2 effect-size forest plot, which has no first-class native primitive, is
generated here as a matplotlib PNG, once per edition (English and Indonesian).

Every number is read from the experiment bundles under
``results/experiments/phase-b/``. The pre-registered 2026-09-20 batch is the H2
result; the other batches are history, named as in the Chapter 4 history table.

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
# Bundles (single source of truth). The four-scenario replication is unpaired
# and has no paired_analysis.json; its Welch estimate is typed below.
# ---------------------------------------------------------------------------
PRIMARY = "2026-09-20_h2-confirmatory-10p"
JULY = "2026-07-14_clarknet-tuned-paired-n5"
AUGUST_A = "2026-08-08_paired-h2_195150"
AUGUST_B = "2026-08-08_paired-h2_233726"
SEPTEMBER_PAIR = "2026-09-13_h2-pair-5p"
FIRST_CONFIRMATORY = "2026-09-13_h2-confirmatory-10p"

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
# fig04_6: H2 forest plot. Point = S4-S3 mean p99 difference (ms), whiskers =
# 95% CI, negative favours S4. The pre-registered batch sits on top in its own
# colour; history batches follow in date order.
# ---------------------------------------------------------------------------
LABELS: dict[str, list[str]] = {
    "en": [
        "Pre-registered (09-20, n=10)",
        "July (07-14, n=5)",
        "August A (08-08, n=5)",
        "August B (08-08, n=5)",
        "Four-scenario replication\n(08-09, 5 runs per arm)",
        "September pair (09-13, n=5)",
        "First confirmatory (09-13, n=10)",
    ],
    "id": [
        "Pra-registrasi (20-09, n=10)",
        "Juli (14-07, n=5)",
        "Agustus A (08-08, n=5)",
        "Agustus B (08-08, n=5)",
        "Replikasi empat skenario\n(09-08, 5 run per lengan)",
        "Pasangan September (13-09, n=5)",
        "Konfirmatori pertama (13-09, n=10)",
    ],
}
TEXT: dict[str, dict[str, str]] = {
    "en": {
        "xlabel": "S4 - S3 mean p99 difference (ms), negative favours S4",
        "primary": "H2 result",
        "history": "History",
        "file": "fig04_6_replication_batches.png",
    },
    "id": {
        "xlabel": "Selisih rata-rata p99 S4 - S3 (ms), negatif berarti S4 lebih baik",
        "primary": "Hasil H2",
        "history": "Sejarah",
        "file": "fig04_6_replication_batches_id.png",
    },
}


def _fig_replication_batches(repo_root: Path, out_dir: Path, lang: str) -> Path:
    # Four-scenario replication, S4 vs S3 from its report.md: Welch mean
    # difference -52.50 ms, 95% CI [-102.60, -11.81], Cohen's d -1.300.
    four_scenario = {"mean_diff": -52.50, "ci_lower": -102.60, "ci_upper": -11.81, "d": -1.300}
    stats = [
        _paired_stats(repo_root, PRIMARY),
        _paired_stats(repo_root, JULY),
        _paired_stats(repo_root, AUGUST_A),
        _paired_stats(repo_root, AUGUST_B),
        four_scenario,
        _paired_stats(repo_root, SEPTEMBER_PAIR),
        _paired_stats(repo_root, FIRST_CONFIRMATORY),
    ]
    text = TEXT[lang]
    sep = 1.0  # extra gap below the primary row
    ypos = np.array([len(stats) + sep - 1] + list(range(len(stats) - 2, -1, -1)), dtype=float)

    fig, ax = plt.subplots(figsize=(8, 6.2))
    ax.axvline(0, color="#999999", linewidth=1.0, zorder=1)
    ax.axhline(ypos[0] - (1 + sep) / 2, color="#cccccc", linewidth=0.8, zorder=1)

    for i, (y, s) in enumerate(zip(ypos, stats)):
        color = "#1f77b4" if i == 0 else "#bdbdbd"
        xerr = [[s["mean_diff"] - s["ci_lower"]], [s["ci_upper"] - s["mean_diff"]]]
        ax.errorbar(
            s["mean_diff"],
            y,
            xerr=xerr,
            fmt="D" if i == 0 else "o",
            markersize=11,
            markerfacecolor=color,
            markeredgecolor="#222222",
            markeredgewidth=0.8,
            elinewidth=2.2 if i == 0 else 1.6,
            capsize=4,
            capthick=1.2,
            ecolor="#1f77b4" if i == 0 else "#555555",
            zorder=3,
        )
        diff = f"{s['mean_diff']:+.1f} ms"
        if lang == "id":
            diff = diff.replace(".", ",")
        ax.text(s["mean_diff"] + 12, y + 0.3, diff, va="center", ha="left", fontsize=9, color="#222222")

    ax.text(-640, ypos[0] + 0.55, text["primary"], fontsize=9, fontweight="bold", color="#1f77b4")
    ax.text(-640, ypos[1] + 0.55, text["history"], fontsize=9, fontweight="bold", color="#555555")
    ax.set_yticks(ypos)
    ax.set_yticklabels(LABELS[lang])
    ax.set_xlabel(text["xlabel"])
    ax.set_xlim(-650, 1150)
    ax.set_ylim(-0.7, ypos[0] + 1.0)
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    fig.tight_layout()

    out = out_dir / text["file"]
    fig.savefig(out)
    plt.close(fig)
    return out


def generate_thesis_figures(repo_root: str | Path, output_dir: str | Path) -> list[Path]:
    """Generate the H2 forest plot, one PNG per edition.

    The other five figures are native Typst (cetz/cetz-plot/primaviz) and live
    in ``thesis-typst/src/content/figures.typ``; they are not produced here.

    Returns the list of PNG paths written.
    """
    repo_root = Path(repo_root)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    return [_fig_replication_batches(repo_root, out_dir, lang) for lang in TEXT]


if __name__ == "__main__":
    import sys

    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else repo / "thesis-typst" / "src" / "figures"
    written = generate_thesis_figures(repo, out)
    for p in written:
        print(f"{p}  ({p.stat().st_size} bytes)")
