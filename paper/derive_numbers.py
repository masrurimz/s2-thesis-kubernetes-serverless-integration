"""Derive every number the papers quote from the evidence bundles.

Writes ``paper/numbers.json``, which ``paper/sections/*.typ`` reads. ``--check`` fails
when the committed file no longer matches the bundles, or when the prose in
``paper/sections/body.typ`` types a number that is neither interpolated from
numbers.json nor a configuration constant listed in ``CONSTANTS``.

    uv run python paper/derive_numbers.py
    uv run python paper/derive_numbers.py --check
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

import yaml
from scipy import stats as scipy_stats
from shared.stats import (
    cohens_d_paired,
    mann_whitney_u,
    paired_bootstrap_ci,
    paired_permutation_p_from_diffs,
)

ROOT = Path(__file__).resolve().parents[1]
PHASE_B = ROOT / "results/experiments/phase-b"
MODELS = ROOT / "results/models/gru"
COST_DIR = ROOT / "results/cost_analysis"
OUT = Path(__file__).with_name("numbers.json")

FOUR = "2026-08-09_clarknet-replay_032257"
BATCHES = {
    "b5": "2026-09-13_h2-pair-5p",
    "b10a": "2026-09-13_h2-confirmatory-10p",
    "b10b": "2026-09-20_h2-confirmatory-10p",
}
SCENARIOS = {
    "s1": "s1-k8s-only",
    "s2": "s2-serverless-only",
    "s3": "s3-hybrid-reactive",
    "s4": "s4-hybrid-predictive",
}

# Numbers the prose may type literally: configuration and protocol constants, not
# measurements. Each names where the value is set.
CONSTANTS = {
    "0": "zero weight / zero RPS in the routing rule",
    "0.4": "post-hoc quiet-host threshold, peak CPU-busy (2026-09-13 bundle SUMMARY.md)",
    "0.5": "target CPU utilization u (calibration)",
    "0.75": "scale-down threshold (cluster_controller.py)",
    "0.90": "upper-envelope coverage target (90th percentile offsets)",
    "1": "one-CPU worker (k3d node bound)",
    "2": "the name Algorithm 2",
    "3": "replica floor R_min and Knative KPA min (knative-service.yaml)",
    "5": "pair count of batch A (meta.yaml)",
    "9": "forecast steps",
    "10": "replica ceiling R_max, Knative KPA max, pair count of batches B and C",
    "15": "control period and sample interval (service.py)",
    "16.65": "r_eff = 33.3 x 0.5",
    "20": "replay length in minutes; initial 80/20 hybrid weight (scenarios.py)",
    "30": "input length, x_obs window, replay step (s), 30-day month",
    "33": "replay amplification factor; /fib?n=33",
    "33.3": "measured single-pod saturation r_sat (calibration)",
    "38": "embargo = 30 + 9 - 1 (study report)",
    "40": "replay steps",
    "45": "lower provisioning delay (s)",
    "50": "serverless weight cap (%); node consolidation utilization (%)",
    "60": "ElaX one-hour horizon in minutes",
    "73": "replay mean RPS (trace manifest)",
    "80": "statistical power (%)",
    "90": "proactive hold (s); 90th percentile",
    "95": "confidence level (%)",
    "75": "provisioning delay in the paired sequence (profiles.py _DELAY_SEQ)",
    "100": "percentage scale in the routing rule",
    "120": "upper provisioning delay; scale-down cooldown (s)",
    "133.2": "C with eight ready pods = 8 x 16.65",
    "135": "forecast horizon 9 x 15 s",
    "140": "healthy p99 threshold 0.7 x 200 ms (slo_monitor.py)",
    "164": "replay peak RPS (trace manifest)",
    "200": "p99 SLO (ms)",
    "266": "load at which the 50% cap binds with eight pods = 2 x 133.2",
    "404": "HTTP status of the Knative warm-up request (paired-batch daemon.log)",
}
BODY = Path(__file__).with_name("sections") / "body.typ"


def literal_numbers(text: str) -> list[tuple[int, str]]:
    """Numbers typed in prose, after removing interpolations, references and identifiers."""
    found = []
    for lineno, line in enumerate(text.splitlines(), 1):
        line = line.split("//", 1)[0]
        line = re.sub(r"#[A-Za-z][\w.\-]*", "", line)  # numbers.json interpolations, function calls
        line = re.sub(r"[@<][\w:\-]+>?", "", line)  # citations and labels
        line = re.sub(r"\b[A-Za-z][A-Za-z\-]*\d+\w*", "", line)  # p99, S4, t3, k3d, N-BEATS-like ids
        line = re.sub(r"`[^`]*`", "", line)  # inline code
        found += [
            (lineno, m) for m in re.findall(r"(?<![\w.,])\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\w.,])\d+(?:\.\d+)?", line)
        ]
    return found


MONTH_SEC = 30 * 24 * 3600
MINUS = "\u2212"


def num(value: float, digits: int = 1, sign: bool = False) -> str:
    text = f"{value:+,.{digits}f}" if sign else f"{value:,.{digits}f}"
    return text.replace("-", MINUS)


def pval(value: float) -> str:
    return f"{value:.3f}" if value >= 0.001 else "<0.001"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def runs(bundle: str, scenario: str) -> list[dict]:
    root = PHASE_B / bundle
    dirs = [d for d in root.iterdir() if d.name.startswith(f"{scenario}_run") and (d / "result.json").exists()]
    dirs.sort(key=lambda d: int(d.name.rsplit("run", 1)[1]))
    return [load(d / "result.json") for d in dirs]


def traffic_share(run: dict) -> float:
    k8s, sls = run["k8s_weight_time_product"], run["serverless_weight_time_product"]
    return 100.0 * sls / (k8s + sls) if k8s + sls else 0.0


def latest_cost(bundle: str) -> dict:
    matches = [p for p in sorted(COST_DIR.glob("cost_analysis_*.json")) if load(p)["experiment_dir"].endswith(bundle)]
    if not matches:
        sys.exit(f"no cost analysis for {bundle}; run `uv run thesis analysis cost --experiment-dir ...`")
    return load(matches[-1])


def monthly_cost(cost: dict, scenario: str) -> list[float]:
    rows = [r for r in cost["scenarios"] if r["scenario"] == scenario]
    return [r["aws_cost"]["total"] * MONTH_SEC / r["duration_sec"] for r in rows]


def mean(values: list[float]) -> float:
    return statistics.fmean(values)


def four_scenario() -> dict:
    cost = latest_cost(FOUR)
    out: dict = {"bundle": FOUR}
    p99: dict[str, list[float]] = {}
    for key, name in SCENARIOS.items():
        rs = runs(FOUR, name)
        p99[key] = [r["p99_latency_ms"] for r in rs]
        out[key] = {
            "n": len(rs),
            "p99": num(mean(p99[key])),
            "p99_sd": num(statistics.stdev(p99[key])),
            "slo": num(mean([r["slo_violations_k6"] for r in rs])),
            "share": num(mean([traffic_share(r) for r in rs])),
            "replica_s": num(mean([r["k8s_replica_seconds"] for r in rs]), 0),
            "cost": num(mean(monthly_cost(cost, name)), 0),
        }
    for other in ("s1", "s2", "s3"):
        _, p = mann_whitney_u(p99[other], p99["s4"])
        change = 100.0 * (mean(p99["s4"]) - mean(p99[other])) / mean(p99[other])
        out[f"s4_vs_{other}"] = {"p": pval(p), "pct": num(change, 1, sign=True), "abs_pct": num(abs(change), 1)}
    replicas = {key: mean([r["k8s_replica_seconds"] for r in runs(FOUR, name)]) for key, name in SCENARIOS.items()}
    for key in ("s3", "s4"):
        out[f"{key}_pods_below_s1"] = num(100.0 * (1 - replicas[key] / replicas["s1"]), 0)
    return out


def batch(bundle: str) -> tuple[dict, list[float], list[float]]:
    pa = load(PHASE_B / bundle / "paired_analysis.json")["primary"]
    s3, s4 = runs(bundle, SCENARIOS["s3"]), runs(bundle, SCENARIOS["s4"])
    base, comp = pa["baseline_values"], pa["comparison_values"]
    assert base == [r["p99_latency_ms"] for r in s3], f"{bundle}: S3 order differs from paired_analysis"
    assert comp == [r["p99_latency_ms"] for r in s4], f"{bundle}: S4 order differs from paired_analysis"
    cost = latest_cost(bundle)
    delays = [r["first_provision_delay_sec"] for r in s3 + s4 if r["first_provision_delay_sec"]]
    fid = [r["treatment_fidelity"] for r in s4]
    out = {
        "bundle": bundle,
        "n": pa["n_pairs"],
        "s3": num(pa["baseline_mean"]),
        "s4": num(pa["comparison_mean"]),
        "diff": num(pa["mean_difference"], 1, sign=True),
        "ci_lo": num(pa["paired_ci_lower"], 1, sign=True),
        "ci_hi": num(pa["paired_ci_upper"], 1, sign=True),
        "p": pval(pa["permutation_p_value"]),
        "d": num(pa["cohens_d_paired"], 2, sign=True),
        "wins": sum(c < b for b, c in zip(base, comp, strict=True)),
        "slo_s3": num(mean([r["slo_violations_k6"] for r in s3]), 0),
        "slo_s4": num(mean([r["slo_violations_k6"] for r in s4]), 0),
        "share_s3": num(mean([traffic_share(r) for r in s3])),
        "share_s4": num(mean([traffic_share(r) for r in s4])),
        "active_s3": num(mean([r["time_in_serverless_pct"] for r in s3])),
        "active_s4": num(mean([r["time_in_serverless_pct"] for r in s4])),
        "replica_s3": num(mean([r["k8s_replica_seconds"] for r in s3]), 0),
        "replica_s4": num(mean([r["k8s_replica_seconds"] for r in s4]), 0),
        "cost_s3": num(mean(monthly_cost(cost, SCENARIOS["s3"])), 0),
        "cost_s4": num(mean(monthly_cost(cost, SCENARIOS["s4"])), 0),
        "valid": sum(r["run_validity_passed"] for r in s3 + s4),
        "runs": len(s3) + len(s4),
        "delivered": sum(f["successful_predictions"] for f in fid),
        "eligible": sum(f["eligible_cycles"] for f in fid),
        "proactive": sum(f["proactive_scaleups"] for f in fid),
        "delay_min": num(min(delays), 0),
        "delay_max": num(max(delays), 0),
        "nodes": num(mean([r["nodes_provisioned"] for r in s3 + s4]), 1),
        "plot": [round(pa["mean_difference"], 1), round(pa["paired_ci_lower"], 1), round(pa["paired_ci_upper"], 1)],
        "replica_pct": num(
            100 * (mean([r["k8s_replica_seconds"] for r in s4]) / mean([r["k8s_replica_seconds"] for r in s3]) - 1),
            0,
        ),
    }
    busy = [r.get("avg_host_busy_ratio") for r in s3 + s4]
    if all(b is not None for b in busy):
        peak = [r["peak_host_busy_ratio"] for r in s3 + s4]
        out["busy_avg_min"], out["busy_avg_max"] = num(min(busy), 2), num(max(busy), 2)
        out["busy_peak_max"] = num(max(peak), 2)
        out["busy_peak_over_half"] = sum(p > 0.5 for p in peak)
        out["busy_p99_r"] = num(statistics.correlation(peak, [r["p99_latency_ms"] for r in s3 + s4]), 2)
        # Post-hoc sensitivity subset recorded in the bundle's SUMMARY.md: pairs whose two
        # runs both peaked under 0.4 host CPU-busy.
        quiet = [
            c["p99_latency_ms"] - b["p99_latency_ms"]
            for b, c in zip(s3, s4, strict=True)
            if b["peak_host_busy_ratio"] < 0.4 and c["peak_host_busy_ratio"] < 0.4
        ]
        out["quiet"] = {
            "n": len(quiet),
            "diff": num(mean(quiet), 1, sign=True),
            "p": pval(paired_permutation_p_from_diffs(quiet)),
            "wins": sum(d < 0 for d in quiet),
        }
    sd = statistics.stdev([c - b for b, c in zip(base, comp, strict=True)])
    out["diff_sd"] = num(sd, 0)
    # Paired t approximation, one-sided alpha 0.05, power 0.80.
    df = len(base) - 1
    out["mde"] = num((scipy_stats.t.ppf(0.95, df) + scipy_stats.t.ppf(0.80, df)) * sd / len(base) ** 0.5, 0)
    return out, base, comp


def predictor_latency(bundle: str) -> dict:
    pattern = re.compile(r"GRU prediction received .*latency_ms=([0-9.]+)")
    values: list[float] = []
    for log in sorted((PHASE_B / bundle).glob(f"{SCENARIOS['s4']}_run*/daemon.log")):
        found = [float(m.group(1)) for m in pattern.finditer(log.read_text())]
        values.extend(found[1:])  # the first request of a run includes model warm-up
    values.sort()
    return {
        "median": num(statistics.median(values), 1),
        "p95": num(values[int(0.95 * (len(values) - 1))], 1),
        "n": len(values),
    }


def predictor() -> dict:
    gru = load(MODELS / "2026-09-10_clarknet-15s-h9-leakfree/metrics.json")["arms"]["clarknet"]["gru"]
    lstm = load(MODELS / "2026-09-10_clarknet-15s-h9-lstm/metrics.json")["arms"]["clarknet"]["lstm"]
    syn = load(MODELS / "2026-09-11_synthetic-15s-h9-leakfree/metrics.json")["arms"]["synthetic"]["gru"]
    ols = load(MODELS / "2026-09-10_predictor-probes/baseline.json")["ols"]
    art = load(MODELS / "2026-09-10_clarknet-15s-h9-leakfree/artifacts/clarknet_gru_s44.json")
    report = (MODELS / "2026-09-10_clarknet-15s-h9-leakfree/report.md").read_text()
    base = re.search(r"persistence RMSE ([0-9.]+), linear trend ([0-9.]+), seasonal naive ([0-9.]+)", report)
    assert base, "baseline line missing from the GRU report"
    probes = sorted((MODELS / "2026-09-13_probes-representation").glob("*.json"))
    verdicts = {p.stem: load(p)["aggregate"]["beats_ols_on_selection_folds"] for p in probes}
    levers = {k: v for k, v in verdicts.items() if k != "calendar"}
    cfg = art.get("config", art)
    meta = yaml.safe_load((MODELS / "2026-09-10_clarknet-15s-h9-leakfree/meta.yaml").read_text())
    gru_h, ols_h = gru["per_horizon_mean"]["rmse"], ols["per_horizon_rmse_steps_1_to_9"]

    def arm(m: dict) -> dict:
        o = m["overall"]
        return {
            "rmse": num(o["rmse"]["mean"], 2),
            "rmse_sd": num(o["rmse"]["std"], 3),
            "mae": num(o["mae"]["mean"], 2),
            "nrmse": num(100 * o["nrmse"]["mean"], 1),
            "skill": num(o["skill_vs_persistence"]["mean"], 3),
            "skill_pct": num(100 * o["skill_vs_persistence"]["mean"], 0),
            "coverage": num(m["coverage_mean"], 3),
            "spike": num(m["archetype_rmse_mean"]["spike"], 2),
        }

    offsets = art.get("upper_offsets") or cfg.get("upper_offsets")
    return {
        "gru": arm(gru),
        "lstm": arm(lstm),
        "ols_rmse": num(ols["rmse"], 2),
        "ols_mae": num(ols["mae"], 2),
        "persistence": num(float(base.group(1)), 2),
        "trend": num(float(base.group(2)), 2),
        "seasonal": num(float(base.group(3)), 2),
        "synthetic_nrmse": num(100 * syn["overall"]["nrmse"]["mean"], 1),
        "hidden": cfg["hidden_size"],
        "layers": cfg["num_layers"],
        "dropout": num(cfg["dropout"], 2),
        "lr": f"{cfg['learning_rate']:.2e}",
        "epochs": cfg["epochs"],
        "offset_min": num(min(offsets), 0),
        "offset_max": num(max(offsets), 0),
        "levers": len(levers),
        "levers_beating_ols": sum(levers.values()),
        "latency": predictor_latency(BATCHES["b10b"]),
        "trials": meta["n_trials"],
        "seq_searched": " and ".join(str(s) for s in meta["sequence_lengths_searched"]),
        "seeds": len(meta["seeds"]),
        "gru_h1": num(gru_h[0], 2),
        "gru_h9": num(gru_h[-1], 2),
        "ols_h1": num(ols_h[0], 2),
        "ols_h9": num(ols_h[-1], 2),
    }


def derive() -> dict:
    batches: dict = {}
    pooled_base: list[float] = []
    pooled_comp: list[float] = []
    for key, bundle in BATCHES.items():
        batches[key], base, comp = batch(bundle)
        pooled_base += base
        pooled_comp += comp
    diffs = [c - b for b, c in zip(pooled_base, pooled_comp, strict=True)]
    lo, hi = paired_bootstrap_ci(pooled_base, pooled_comp)
    batches["pooled"] = {
        "n": len(diffs),
        "diff": num(mean(diffs), 1, sign=True),
        "ci_lo": num(lo, 1, sign=True),
        "ci_hi": num(hi, 1, sign=True),
        "p": pval(paired_permutation_p_from_diffs(diffs)),
        "d": num(cohens_d_paired(pooled_base, pooled_comp), 2, sign=True),
        "wins": sum(d < 0 for d in diffs),
        "plot": [round(mean(diffs), 1), round(lo, 1), round(hi, 1)],
    }
    return {"four": four_scenario(), "h2": batches, "gru": predictor()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="fail if numbers.json is stale")
    args = parser.parse_args()
    text = json.dumps(derive(), indent=1, ensure_ascii=False) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            sys.exit(f"{OUT.name} is stale: run `uv run python paper/derive_numbers.py`")
        stray = [(n, v) for n, v in literal_numbers(BODY.read_text()) if v not in CONSTANTS]
        if stray:
            lines = "\n".join(f"  body.typ:{n}: {v}" for n, v in stray)
            sys.exit(f"numbers typed in prose that are not in CONSTANTS or numbers.json:\n{lines}")
        print(f"{OUT.name} matches the bundles; every number in body.typ is derived or a listed constant")
        return
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
