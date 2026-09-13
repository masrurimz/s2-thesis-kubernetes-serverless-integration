"""Exploratory data analysis for the ClarkNet and Calgary traces.

Purpose: characterise both corpora well enough to DESIGN the train/validation/test
protocol instead of inheriting proportional fractions. Findings are written to
results/models/gru/2026-09-13_eda-*/ as report.md plus eda.json.

Run: uv run python scripts/eda_timeseries.py
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "results" / "models" / "gru"
FIFTEEN = "15s"
DAY = 5760  # 15 s buckets in 24 h
WEEK = 40320
EMBARGO = 38  # sequence_length 30 + horizon 9 - 1
CORPORA = {
    "clarknet": ROOT / "data" / "processed" / "clarknet_real_rps.parquet",
    "calgary": ROOT / "data" / "processed" / "calgary_real_rps.parquet",
}
DAYNAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def load(path: Path) -> pd.Series:
    df = pd.read_parquet(path)
    return df[df.columns[0]].resample(FIFTEEN).sum().dropna().astype(float)


def _index(series: pd.Series) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(series.index)


def describe(series: pd.Series) -> dict[str, Any]:
    counts = series.to_numpy(dtype=float)
    q = np.percentile(counts, [1, 5, 25, 50, 75, 95, 99])
    idx = _index(series)
    expected = int((idx[-1] - idx[0]).total_seconds() / 15) + 1
    return {
        "units": "counts per 15 s bucket; divide by 15 for requests per second",
        "samples": int(len(series)),
        "span_start": str(idx[0]),
        "span_end": str(idx[-1]),
        "span_days": round((idx[-1] - idx[0]).total_seconds() / 86400, 3),
        "resolution_sec": 15,
        "expected_buckets_if_gapless": expected,
        "missing_buckets": expected - len(series),
        "mean": round(float(counts.mean()), 4),
        "std": round(float(counts.std()), 4),
        "cv": round(float(counts.std() / max(counts.mean(), 1e-9)), 4),
        "min": round(float(counts.min()), 4),
        "max": round(float(counts.max()), 4),
        "p01_p05_p25_p50_p75_p95_p99": [round(float(x), 4) for x in q],
        "zero_share": round(float((counts == 0).mean()), 4),
        "below_1_share": round(float((counts < 1).mean()), 4),
        "skew": round(float(pd.Series(counts).skew()), 4),
        "kurtosis": round(float(pd.Series(counts).kurtosis()), 4),
        "mean_to_max_ratio": round(float(counts.mean() / max(counts.max(), 1e-9)), 4),
    }


def daytype_profile(series: pd.Series) -> dict[str, dict[str, Any]]:
    dow = np.array([ts.weekday() for ts in series.index])
    out: dict[str, dict[str, Any]] = {}
    for code, name in enumerate(DAYNAMES):
        seg = series[dow == code]
        if len(seg) == 0:
            out[name] = {"buckets": 0}
            continue
        out[name] = {
            "buckets": int(len(seg)),
            "share": round(float(len(seg) / len(series)), 4),
            "mean": round(float(seg.mean()), 3),
            "p95": round(float(np.percentile(seg.to_numpy(dtype=float), 95)), 3),
            "max": round(float(seg.max()), 3),
        }
    return out


def hourly_profile(series: pd.Series) -> dict[str, Any]:
    idx = _index(series)
    if len(idx) < DAY:
        return {}
    first = series.iloc[:DAY]
    hours = np.array([ts.hour for ts in first.index])
    by_hour = first.groupby(hours).mean()
    return {
        "hourly_mean_first_day": {int(h): round(float(v), 3) for h, v in by_hour.items()},
        "peak_hour": int(by_hour.idxmax()),
        "trough_hour": int(by_hour.idxmin()),
        "peak_to_trough_ratio": round(float(by_hour.max() / max(by_hour.min(), 1e-9)), 3),
    }


def seasonal_structure(series: pd.Series) -> dict[str, Any]:
    x = series.to_numpy(dtype=float)
    x = x - x.mean()
    out: dict[str, Any] = {}
    for name, lag in (
        ("lag_1", 1),
        ("lag_4", 4),
        ("lag_120", 120),
        ("lag_480", 480),
        ("daily_5760", DAY),
        ("weekly_40320", WEEK),
    ):
        if len(x) > lag:
            denom = float(np.sqrt(np.sum(x**2) * np.sum(x[lag:] ** 2)))
            out[f"autocorr_{name}"] = round(float(np.sum(x[:-lag] * x[lag:]) / denom), 4) if denom else None
    try:
        stl_mod = importlib.import_module("statsmodels.tsa.seasonal")
        stl = stl_mod.STL(pd.Series(x), period=DAY, robust=True).fit()
        var = float(np.var(x))
        out["stl_variance_share"] = {
            "trend": round(float(np.var(stl.trend) / var), 4),
            "seasonal": round(float(np.var(stl.seasonal) / var), 4),
            "resid": round(float(np.var(stl.resid) / var), 4),
        }
    except Exception as exc:  # noqa: BLE001
        out["stl_variance_share"] = f"skipped: {exc.__class__.__name__}"
    return out


def stationarity(series: pd.Series) -> dict[str, Any]:
    out: dict[str, Any] = {}
    x = series.to_numpy(dtype=float)
    try:
        tools = importlib.import_module("statsmodels.tsa.stattools")
        stat, p, *_ = tools.adfuller(x, autolag="AIC")
        out["adf_stat"], out["adf_p"] = round(float(stat), 4), float(p)
        out["adf_verdict"] = "stationary" if p < 0.05 else "unit root not rejected"
        kstat, kp, *_ = tools.kpss(x, regression="c", nlags="auto")
        out["kpss_stat"], out["kpss_p"] = round(float(kstat), 4), float(kp)
        out["kpss_verdict"] = "stationary" if kp > 0.05 else "non-stationary"
    except Exception as exc:  # noqa: BLE001
        out["skipped"] = exc.__class__.__name__
    return out


def permutation_entropy(x: np.ndarray, m: int = 5, delay: int = 1) -> float:
    """Bandt-Pompe permutation entropy, normalised by log2(m!)."""
    import math

    n = len(x) - (m - 1) * delay
    patterns = np.argsort(np.stack([x[np.arange(n) + i * delay] for i in range(m)], axis=1), axis=1)
    codes = (patterns * (m ** np.arange(m))).sum(axis=1)
    _, counts = np.unique(codes, return_counts=True)
    p = counts / counts.sum()
    return float((-(p * np.log2(p)).sum()) / math.log2(math.factorial(m)))


def spectral_entropy(x: np.ndarray) -> float:
    """Shannon entropy of the normalised power spectrum, 0 (one tone) to 1 (flat)."""
    p = np.abs(np.fft.rfft(x - x.mean())) ** 2
    p = p / p.sum()
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum() / np.log2(len(p)))


def forecastability(series: pd.Series) -> dict[str, Any]:
    """Ordinal and spectral predictability, plus the level+slope residual share.

    PE near 1.0 means the ordinal structure is near-maximally random (white
    noise reference = 1.0). Computing PE on the residuals of a one-step
    level+slope (OLS-shaped) fit separates the part any linear autoregression
    captures from the innovation left for any model to learn.
    """
    y = series.to_numpy(dtype=float)
    design = np.stack([y[1:-1], np.diff(y)[:-1]], axis=1)
    coef, *_ = np.linalg.lstsq(np.c_[design, np.ones(len(design))], y[2:], rcond=None)
    resid = y[2:] - (design @ coef[:-1] + coef[-1])
    rng = np.random.default_rng(0)
    return {
        "permutation_entropy": {
            "m4": permutation_entropy(y, 4),
            "m5": permutation_entropy(y, 5),
            "m6": permutation_entropy(y, 6),
        },
        "spectral_entropy": spectral_entropy(y),
        "level_slope_fit": {
            "residual_std": float(resid.std()),
            "series_std": float(y.std()),
            "residual_variance_share": float(resid.var() / y.var()),
        },
        "permutation_entropy_of_level_slope_residuals_m5": permutation_entropy(resid, 5),
        "white_noise_reference_m5": permutation_entropy(rng.normal(size=len(y)), 5),
    }


def block_design(series: pd.Series, block_days: int = 1) -> dict[str, Any]:
    """Blocked evaluation proposal: consecutive held-out blocks, train = all prior data."""
    dow = np.array([ts.weekday() for ts in series.index])
    blocks: list[dict[str, Any]] = []
    for i, test_lo in enumerate(range(3 * DAY, len(series) - block_days * DAY, block_days * DAY), start=3):
        test_hi = min(test_lo + block_days * DAY, len(series))
        train_lo, train_hi = 0, test_lo - EMBARGO
        if train_hi - train_lo < 2 * DAY or test_hi - test_lo < 96:
            continue
        test_seg, train_seg = series.iloc[test_lo:test_hi], series.iloc[train_lo:train_hi]
        blocks.append(
            {
                "block": i,
                "train_span": [str(_index(train_seg)[0]), str(_index(train_seg)[-1])],
                "test_span": [str(_index(test_seg)[0]), str(_index(test_seg)[-1])],
                "train_daytypes": sorted({DAYNAMES[int(d)] for d in np.unique(dow[train_lo:train_hi])}),
                "test_daytypes": sorted({DAYNAMES[int(d)] for d in np.unique(dow[test_lo:test_hi])}),
                "train_mean": round(float(train_seg.mean()), 3),
                "test_mean": round(float(test_seg.mean()), 3),
                "level_shift": round(float(test_seg.mean() / max(train_seg.mean(), 1e-9)), 3),
            }
        )
    overlaps = sum(1 for b in blocks if set(b["train_daytypes"]) & set(b["test_daytypes"]))
    weekend_blocks = sum(1 for b in blocks if "Sat" in b["test_daytypes"] or "Sun" in b["test_daytypes"])
    return {
        "block_days": block_days,
        "blocks": blocks,
        "blocks_with_daytype_overlap": overlaps,
        "blocks_testing_weekend": weekend_blocks,
        "total_blocks": len(blocks),
    }


def main() -> int:
    for name, path in CORPORA.items():
        if not path.exists():
            print(f"missing: {path}")
            continue
        series = load(path)
        eda: dict[str, Any] = {
            "corpus": name,
            "source": str(path.relative_to(ROOT)),
            "shape": describe(series),
            "daytype_profile": daytype_profile(series),
            "hourly": hourly_profile(series),
            "seasonal": seasonal_structure(series),
            "stationarity": stationarity(series),
            "forecastability": forecastability(series),
            "blocked_design_1d": block_design(series, 1),
            "blocked_design_7d": block_design(series, 7),
        }
        out = OUT_ROOT / f"2026-09-13_eda-{name}"
        out.mkdir(parents=True, exist_ok=True)
        (out / "eda.json").write_text(json.dumps(eda, indent=2, default=str))
        lines = [
            f"# EDA - {name}",
            "",
            f"Source: `{eda['source']}`",
            "",
            "Units: counts per 15 s bucket. Divide by 15 for requests per second. The original series is the raw "
            "trace; the deployment arm serves that series multiplied by the manifest factor 33.0. Level-shift ratios, "
            "autocorrelations, skew, kurtosis and zero shares are unit-free.",
            "",
            "## Shape",
            "",
            "```json",
            json.dumps(eda["shape"], indent=2),
            "```",
            "",
            "## Day-type profile",
            "",
            "| day | buckets | share | mean | p95 | max |",
            "|---|---|---|---|---|---|",
        ]
        for d, v in eda["daytype_profile"].items():
            if v.get("buckets"):
                lines.append(f"| {d} | {v['buckets']} | {v['share']} | {v['mean']} | {v['p95']} | {v['max']} |")
        for title, key in (
            ("Hourly profile", "hourly"),
            ("Seasonal structure", "seasonal"),
            ("Stationarity", "stationarity"),
        ):
            lines += ["", f"## {title}", "", "```json", json.dumps(eda[key], indent=2), "```"]
        lines += ["", "## Forecastability", "", "```json", json.dumps(eda["forecastability"], indent=2), "```"]
        for key in ("blocked_design_1d", "blocked_design_7d"):
            b = eda[key]
            lines += [
                "",
                f"## Blocked design ({b['block_days']}d blocks)",
                "",
                f"{b['total_blocks']} blocks, {b['blocks_with_daytype_overlap']} with train/test day-type overlap, "
                f"{b['blocks_testing_weekend']} testing a weekend day.",
                "",
                "| block | train span | test span | train days | test days | train mean | test mean | shift |",
                "|---|---|---|---|---|---|---|---|",
            ]
            shown = b["blocks"][:10] + (b["blocks"][-3:] if len(b["blocks"]) > 13 else [])
            for row in shown:
                lines.append(
                    f"| {row['block']} | {row['train_span'][0]} to {row['train_span'][1]} | {row['test_span'][0]} to {row['test_span'][1]} | "
                    f"{','.join(row['train_daytypes'])} | {','.join(row['test_daytypes'])} | {row['train_mean']} | {row['test_mean']} | {row['level_shift']} |"
                )
            if len(b["blocks"]) > len(shown):
                lines.append(
                    f"| ... | {len(b['blocks']) - len(shown)} further blocks, full table in eda.json | | | | | | |"
                )
        (out / "report.md").write_text("\n".join(lines))
        print(f"{name}: wrote {out.relative_to(ROOT)}")
        print(f"   shape    : {json.dumps(eda['shape'])[:220]}")
        print(f"   seasonal : {json.dumps(eda['seasonal'])[:220]}")
        print(
            f"   blocks1d : n={eda['blocked_design_1d']['total_blocks']} overlap={eda['blocked_design_1d']['blocks_with_daytype_overlap']} weekend={eda['blocked_design_1d']['blocks_testing_weekend']}"
        )
        print(
            f"   blocks7d : n={eda['blocked_design_7d']['total_blocks']} overlap={eda['blocked_design_7d']['blocks_with_daytype_overlap']} weekend={eda['blocked_design_7d']['blocks_testing_weekend']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
