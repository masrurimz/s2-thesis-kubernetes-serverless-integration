#!/usr/bin/env python3
"""
Cold Start vs Warm Start Latency Decomposition Analysis

Analyzes Phase B experiment data and Phase A1 decision logs to quantify
the cold start penalty in hybrid scenarios (S3, S4) and its contribution
to p99 latency variance.

Data sources:
- Phase B: results/experiments/phase-b/2026-02-12_replicated-20runs/raw/experiments_final.json
- Phase A1: results/experiments/phase-a1/2026-02-12_predictive-trigger/report.md (decision log)
- Infrastructure: Knative cold start measurements (682ms-1235ms from infra tests)
- Knative config: minScale=0, scale-to-zero-grace-period=30s

Usage:
    uv run python scripts/cold_start_analysis.py
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

# ---------------------------------------------------------------------------
# Constants from infrastructure measurements and Knative config
# ---------------------------------------------------------------------------

# Measured cold start times from infrastructure/results/knative-real/RESULTS-SUMMARY.md
COLD_START_MS_S3 = 682.0  # Pre-warm cold start for S3 reactive
COLD_START_MS_S4 = 1235.0  # Pre-warm cold start for S4 predictive
COLD_START_RANGE = (682.0, 1235.0)  # Range across measurements

# Knative autoscaler config from infrastructure/k3d/knative-install.sh
KNATIVE_SCALE_TO_ZERO_GRACE = 30  # seconds
KNATIVE_STABLE_WINDOW = 60  # seconds
KNATIVE_MIN_SCALE = 0  # minScale annotation

# Algorithm 1 config from controller/intelligent_router/algorithm1_controller.py
WEIGHT_STEP = 10  # +10% per SCALE_OUT
COOLDOWN_SEC = 15  # seconds between adjustments
MAX_KNATIVE_WEIGHT = 50  # max serverless weight
SLO_THRESHOLD_MS = 200  # p99 threshold

# Phase A1 decision log (from report.md)
PHASE_A1_DECISIONS = [
    {"decision": 1, "action": "MAINTAIN", "p99_ms": None, "weights": (100, 0)},
    {"decision": 2, "action": "MAINTAIN", "p99_ms": 6516.0, "weights": (100, 0)},
    {"decision": 3, "action": "SCALE_OUT", "p99_ms": 3648.0, "weights": (90, 10)},
    {"decision": 4, "action": "SCALE_OUT", "p99_ms": 2060.0, "weights": (80, 20)},
    {"decision": 5, "action": "SCALE_OUT", "p99_ms": 1120.0, "weights": (70, 30)},
    {"decision": 6, "action": "SCALE_OUT", "p99_ms": 632.0, "weights": (60, 40)},
    {"decision": 7, "action": "SCALE_OUT", "p99_ms": 278.0, "weights": (50, 50)},
    {"decision": 8, "action": "OPTIMIZE_COST", "p99_ms": 110.0, "weights": (55, 45)},
    {"decision": 9, "action": "PREDICTIVE", "p99_ms": 146.0, "weights": (50, 50)},
    {"decision": 10, "action": "MAINTAIN", "p99_ms": 158.0, "weights": (50, 50)},
    {"decision": 11, "action": "MAINTAIN", "p99_ms": 266.0, "weights": (50, 50)},
    {"decision": 18, "action": "OPTIMIZE_COST", "p99_ms": 118.0, "weights": (55, 45)},
]

# Outlier run IDs to exclude (from outliers.json)
OUTLIER_RUNS = {
    "s1-k8s-only": [2],
    "s2-serverless-only": [5],
    "s3-hybrid-reactive": [5],
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_phase_b_data(base_path: Path) -> List[Dict]:
    """Load Phase B experiment data, excluding outlier runs."""
    data_path = base_path / "results/experiments/phase-b/2026-02-12_replicated-20runs/raw/experiments_final.json"
    with open(data_path) as f:
        raw = json.load(f)

    # Filter outliers
    clean = []
    for run in raw:
        scenario = run["scenario"]
        run_id = run["run_id"]
        if run_id in OUTLIER_RUNS.get(scenario, []):
            continue
        clean.append(run)
    return clean


def group_by_scenario(data: List[Dict]) -> Dict[str, List[Dict]]:
    """Group experiment runs by scenario."""
    grouped: Dict[str, List[Dict]] = {}
    for run in data:
        s = run["scenario"]
        grouped.setdefault(s, []).append(run)
    return grouped


# ---------------------------------------------------------------------------
# Phase B analysis
# ---------------------------------------------------------------------------


@dataclass
class ScenarioStats:
    scenario: str
    n_runs: int
    p99_mean: float
    p99_std: float
    p99_median: float
    p99_min: float
    p99_max: float
    p99_cov: float  # coefficient of variation
    p95_mean: float
    p50_mean: float
    throughput_mean: float
    avg_scale_out_count: float
    avg_total_decisions: float


def compute_scenario_stats(scenario: str, runs: List[Dict]) -> ScenarioStats:
    p99s = [r["p99_latency_ms"] for r in runs]
    p95s = [r["p95_latency_ms"] for r in runs]
    p50s = [r["p50_latency_ms"] for r in runs]
    throughputs = [r["throughput_rps"] for r in runs]
    scale_outs = [r["scale_out_count"] for r in runs]
    total_decisions = [
        r["maintain_count"] + r["scale_out_count"] + r["predictive_count"] + r["optimize_cost_count"] for r in runs
    ]

    p99_arr = np.array(p99s)
    mean = float(np.mean(p99_arr))
    std = float(np.std(p99_arr, ddof=1)) if len(p99_arr) > 1 else 0.0

    return ScenarioStats(
        scenario=scenario,
        n_runs=len(runs),
        p99_mean=mean,
        p99_std=std,
        p99_median=float(np.median(p99_arr)),
        p99_min=float(np.min(p99_arr)),
        p99_max=float(np.max(p99_arr)),
        p99_cov=(std / mean * 100) if mean > 0 else 0.0,
        p95_mean=float(np.mean(p95s)),
        p50_mean=float(np.mean(p50s)),
        throughput_mean=float(np.mean(throughputs)),
        avg_scale_out_count=float(np.mean(scale_outs)),
        avg_total_decisions=float(np.mean(total_decisions)),
    )


def correlation_scale_out_p99(runs: List[Dict]) -> Optional[float]:
    """Pearson correlation between scale_out_count and p99 for hybrid runs."""
    if len(runs) < 3:
        return None
    so = [r["scale_out_count"] for r in runs]
    p99 = [r["p99_latency_ms"] for r in runs]
    if np.std(so) == 0 or np.std(p99) == 0:
        return None
    return float(np.corrcoef(so, p99)[0, 1])


# ---------------------------------------------------------------------------
# Phase A1 cold start decomposition
# ---------------------------------------------------------------------------


def analyze_phase_a1_transition():
    """Analyze the weight transition in Phase A1 to estimate cold start penalty.

    Key transition: Decision 2→3 (MAINTAIN 100/0 → SCALE_OUT 90/10)
    This is when Knative first receives traffic → cold start occurs.

    Returns dict with analysis results.
    """
    # First SCALE_OUT (decision 3): knative goes from 0→10%
    first_scale_out = PHASE_A1_DECISIONS[2]  # decision 3
    # Warm steady state (decisions 8-10 after stabilization)
    warm_decisions = [d for d in PHASE_A1_DECISIONS if d["p99_ms"] and d["p99_ms"] < SLO_THRESHOLD_MS]

    p99_at_first_scale_out = first_scale_out["p99_ms"]  # 3648ms

    # Before SCALE_OUT (decision 2): 6516ms - but this is SLO violation pre-serverless
    p99_before_scale_out = PHASE_A1_DECISIONS[1]["p99_ms"]  # 6516ms

    # Warm state p99 (after system stabilizes)
    warm_p99s = [d["p99_ms"] for d in warm_decisions]
    p99_warm_mean = float(np.mean(warm_p99s))

    # The p99 drop from decision 2→7 tracks both:
    # 1. Cold start penalty being absorbed during ramp-up
    # 2. Load distribution improving as more weight shifts to knative

    # Estimate cold start penalty from infrastructure measurements
    # Cold start = time for first request to knative to complete
    cold_start_estimate = np.mean(COLD_START_RANGE)  # ~958ms average

    # p99 during first SCALE_OUT includes cold start + SLO violation load
    # Warm state p99 is ~130ms (average of stable decisions)
    # Cold start penalty on p99 ≈ measured cold start time (affects 10% of traffic)
    #
    # At 10% weight, 10% of requests hit knative. If cold start = 958ms,
    # these requests contribute to tail latency.
    # p99 sees the slowest 1% → cold start requests dominate p99 at transition.

    return {
        "p99_before_serverless": p99_before_scale_out,
        "p99_at_first_scale_out": p99_at_first_scale_out,
        "p99_warm_state_mean": p99_warm_mean,
        "cold_start_measured_s3": COLD_START_MS_S3,
        "cold_start_measured_s4": COLD_START_MS_S4,
        "cold_start_average": cold_start_estimate,
        "warm_decisions": warm_decisions,
        "transition_decisions": PHASE_A1_DECISIONS[2:7],  # decisions 3-7 (ramp)
    }


# ---------------------------------------------------------------------------
# Variance decomposition model
# ---------------------------------------------------------------------------


def variance_decomposition(stats: Dict[str, ScenarioStats]):
    """Decompose p99 variance into components.

    Model: σ²_total = σ²_base + σ²_cold + σ²_load

    We use S1 (k8s-only, no cold starts) as base variance reference.
    The excess variance in S3/S4 is attributable to cold start + routing overhead.
    """
    s1 = stats.get("s1-k8s-only")
    s2 = stats.get("s2-serverless-only")
    s3 = stats.get("s3-hybrid-reactive")
    s4 = stats.get("s4-hybrid-predictive")

    if not all([s1, s2, s3, s4]):
        return None

    # Base variance = average of S1 and S2 (no routing decisions)
    base_var = (s1.p99_std**2 + s2.p99_std**2) / 2

    # S3 excess = total - base → cold start + routing overhead
    s3_excess_var = max(0, s3.p99_std**2 - base_var)
    s4_excess_var = max(0, s4.p99_std**2 - base_var)

    return {
        "base_variance": base_var,
        "base_std": base_var**0.5,
        "s1_variance": s1.p99_std**2,
        "s2_variance": s2.p99_std**2,
        "s3_total_variance": s3.p99_std**2,
        "s3_excess_variance": s3_excess_var,
        "s3_excess_std": s3_excess_var**0.5,
        "s4_total_variance": s4.p99_std**2,
        "s4_excess_variance": s4_excess_var,
        "s4_excess_std": s4_excess_var**0.5,
        "s3_pct_from_cold_start": (s3_excess_var / s3.p99_std**2 * 100) if s3.p99_std > 0 else 0,
        "s4_pct_from_cold_start": (s4_excess_var / s4.p99_std**2 * 100) if s4.p99_std > 0 else 0,
    }


# ---------------------------------------------------------------------------
# Theoretical cold start impact model
# ---------------------------------------------------------------------------


def theoretical_cold_start_impact(
    rps: int = 100,
    duration_sec: int = 300,
    cold_start_ms: float = 958.0,
    weight_at_transition: int = 10,
    n_scale_out_events: int = 1,
    cold_start_duration_sec: float = 5.0,
):
    """Model cold start impact on p99 latency.

    When weight shifts from 0→10%, 10% of requests hit Knative.
    During cold start (~1-5s), these requests experience high latency.

    Args:
        rps: Requests per second
        duration_sec: Total test duration
        cold_start_ms: Cold start latency per request
        weight_at_transition: % weight on Knative at first engagement
        n_scale_out_events: Number of cold start events per run
        cold_start_duration_sec: How long cold start affects requests
    """
    total_requests = rps * duration_sec

    # Requests during cold start window
    cold_requests = int(rps * (weight_at_transition / 100.0) * cold_start_duration_sec * n_scale_out_events)

    # These requests experience cold_start_ms latency
    # Normal requests: ~5ms
    # Cold start requests: ~cold_start_ms

    # p99 = 99th percentile → top 1% of requests
    p99_threshold_count = int(total_requests * 0.01)

    # If cold_requests > p99_threshold_count, cold start dominates p99
    cold_start_dominates_p99 = cold_requests >= p99_threshold_count

    return {
        "total_requests": total_requests,
        "cold_start_requests": cold_requests,
        "p99_threshold_count": p99_threshold_count,
        "cold_start_dominates_p99": cold_start_dominates_p99,
        "cold_start_fraction": cold_requests / total_requests if total_requests > 0 else 0,
        "cold_start_ms": cold_start_ms,
        "estimated_p99_with_cold_start": cold_start_ms if cold_start_dominates_p99 else None,
    }


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------


def main():
    base_path = Path(__file__).parent.parent.parent  # thesis-kubernetes-serverless-integration/

    print("=" * 80)
    print("COLD START vs WARM START LATENCY DECOMPOSITION")
    print("=" * 80)

    # 1. Load and analyze Phase B data
    print("\n## Phase B: Per-Scenario Statistics (excluding outliers)")
    print("-" * 60)

    data = load_phase_b_data(base_path)
    grouped = group_by_scenario(data)

    stats = {}
    for scenario in ["s1-k8s-only", "s2-serverless-only", "s3-hybrid-reactive", "s4-hybrid-predictive"]:
        runs = grouped.get(scenario, [])
        s = compute_scenario_stats(scenario, runs)
        stats[scenario] = s
        print(f"\n### {scenario} (n={s.n_runs})")
        print(f"  p99: mean={s.p99_mean:.1f}ms, std={s.p99_std:.1f}ms, CoV={s.p99_cov:.1f}%")
        print(f"  p99: min={s.p99_min:.1f}ms, max={s.p99_max:.1f}ms, median={s.p99_median:.1f}ms")
        print(f"  p95: mean={s.p95_mean:.1f}ms, p50: mean={s.p50_mean:.1f}ms")
        print(f"  throughput: {s.throughput_mean:.1f} RPS")
        print(f"  avg scale_out: {s.avg_scale_out_count:.1f}, avg total decisions: {s.avg_total_decisions:.1f}")

    # 2. Correlation: scale_out_count vs p99
    print("\n\n## Correlation: scale_out_count vs p99 (hybrid scenarios)")
    print("-" * 60)

    for scenario in ["s3-hybrid-reactive", "s4-hybrid-predictive"]:
        runs = grouped.get(scenario, [])
        r = correlation_scale_out_p99(runs)
        if r is not None:
            print(f"  {scenario}: r={r:.3f} (n={len(runs)})")
            if abs(r) > 0.5:
                print("    → Moderate-to-strong correlation: more scale-outs ↔ higher p99")
            elif abs(r) > 0.3:
                print("    → Weak correlation")
            else:
                print("    → No meaningful correlation")
        else:
            print(f"  {scenario}: insufficient data")

    # 3. Variance decomposition
    print("\n\n## Variance Decomposition")
    print("-" * 60)

    decomp = variance_decomposition(stats)
    if decomp:
        print(f"  Base variance (avg S1+S2): σ²={decomp['base_variance']:.0f}, σ={decomp['base_std']:.1f}ms")
        print(f"  S1 variance: σ²={decomp['s1_variance']:.0f}, σ={stats['s1-k8s-only'].p99_std:.1f}ms")
        print(f"  S2 variance: σ²={decomp['s2_variance']:.0f}, σ={stats['s2-serverless-only'].p99_std:.1f}ms")
        print(
            f"  S3 total variance: σ²={decomp['s3_total_variance']:.0f}, σ={stats['s3-hybrid-reactive'].p99_std:.1f}ms"
        )
        print(
            f"  S3 excess (cold start + routing): σ²={decomp['s3_excess_variance']:.0f}, σ={decomp['s3_excess_std']:.1f}ms"
        )
        print(f"  S3 % from cold start/routing: {decomp['s3_pct_from_cold_start']:.1f}%")
        print(
            f"  S4 total variance: σ²={decomp['s4_total_variance']:.0f}, σ={stats['s4-hybrid-predictive'].p99_std:.1f}ms"
        )
        print(
            f"  S4 excess (cold start + routing): σ²={decomp['s4_excess_variance']:.0f}, σ={decomp['s4_excess_std']:.1f}ms"
        )
        print(f"  S4 % from cold start/routing: {decomp['s4_pct_from_cold_start']:.1f}%")

    # 4. Phase A1 transition analysis
    print("\n\n## Phase A1: Weight Transition Cold Start Analysis")
    print("-" * 60)

    a1 = analyze_phase_a1_transition()
    print(f"  p99 before serverless (100/0): {a1['p99_before_serverless']:.0f}ms")
    print(f"  p99 at first SCALE_OUT (90/10): {a1['p99_at_first_scale_out']:.0f}ms")
    print(f"  p99 warm state mean: {a1['p99_warm_state_mean']:.0f}ms")
    print(f"  Measured cold start S3: {a1['cold_start_measured_s3']:.0f}ms")
    print(f"  Measured cold start S4: {a1['cold_start_measured_s4']:.0f}ms")
    print(f"  Average cold start: {a1['cold_start_average']:.0f}ms")

    print("\n  Weight ramp trajectory (decisions 3-7):")
    for d in a1["transition_decisions"]:
        k3s, kn = d["weights"]
        print(f"    Decision {d['decision']}: {d['action']:15s} p99={d['p99_ms']:.0f}ms  weights={k3s}/{kn}")

    print("\n  Warm state decisions:")
    for d in a1["warm_decisions"]:
        k3s, kn = d["weights"]
        print(f"    Decision {d['decision']}: {d['action']:15s} p99={d['p99_ms']:.0f}ms  weights={k3s}/{kn}")

    # 5. Theoretical cold start impact
    print("\n\n## Theoretical Cold Start Impact Model")
    print("-" * 60)

    for cs_ms, label in [
        (COLD_START_MS_S3, "S3 (682ms)"),
        (COLD_START_MS_S4, "S4 (1235ms)"),
        (958.0, "Average (958ms)"),
    ]:
        impact = theoretical_cold_start_impact(
            rps=100,
            duration_sec=300,
            cold_start_ms=cs_ms,
            weight_at_transition=10,
            n_scale_out_events=1,
            cold_start_duration_sec=5.0,
        )
        print(f"\n  ### {label}:")
        print(f"    Total requests: {impact['total_requests']}")
        print(f"    Cold-start affected requests: {impact['cold_start_requests']}")
        print(f"    p99 threshold (top 1%): {impact['p99_threshold_count']} requests")
        print(f"    Cold start fraction: {impact['cold_start_fraction']:.3%}")
        print(f"    Cold start dominates p99: {impact['cold_start_dominates_p99']}")
        if impact["estimated_p99_with_cold_start"]:
            print(f"    → Estimated p99 ≈ {impact['estimated_p99_with_cold_start']:.0f}ms (cold start latency)")

    # 6. Summary
    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    cs_penalty = a1["cold_start_average"]
    warm_p99 = a1["p99_warm_state_mean"]

    print(f"""
  Cold Start Penalty Estimate:
    Measured range: {COLD_START_MS_S3:.0f}-{COLD_START_MS_S4:.0f}ms (avg {cs_penalty:.0f}ms)
    Warm state p99: {warm_p99:.0f}ms
    Cold start overhead: {cs_penalty - warm_p99:.0f}ms above warm state

  Variance Attribution (S3 reactive):
    Total p99 std: {stats["s3-hybrid-reactive"].p99_std:.0f}ms
    Base std (no routing): {decomp["base_std"]:.0f}ms
    Excess std (cold start + routing): {decomp["s3_excess_std"]:.0f}ms
    → {decomp["s3_pct_from_cold_start"]:.0f}% of S3 variance attributable to cold start/routing

  Correlation (scale_out ↔ p99):""")

    for scenario in ["s3-hybrid-reactive", "s4-hybrid-predictive"]:
        r = correlation_scale_out_p99(grouped.get(scenario, []))
        print(f"    {scenario}: r={r:.3f}" if r else f"    {scenario}: N/A")

    print(f"""
  Data Limitations:
    ⚠ No per-request latency data (only run-level aggregates)
    ⚠ No per-backend tagging (cannot separate k3s vs knative latency)
    ⚠ GRU was not running in Phase B (S4 fell back to reactive)
    ⚠ Cold start measurements from infra tests, not Phase B runs
    ⚠ Phase A1 had ramp load profile; Phase B used constant load

  Recommendations:
    1. Set minScale=1 to avoid cold starts (eliminates ~{cs_penalty:.0f}ms penalty)
    2. Keep pre-warming in SCALE_OUT path (already implemented)
    3. Collect per-request latency with backend tags in future experiments
    4. Run Phase B with GRU enabled to validate S4 predictive advantage
""")

    # Write JSON output for further analysis
    output = {
        "cold_start_penalty": {
            "measured_s3_ms": COLD_START_MS_S3,
            "measured_s4_ms": COLD_START_MS_S4,
            "average_ms": cs_penalty,
            "warm_state_p99_ms": warm_p99,
            "overhead_ms": cs_penalty - warm_p99,
        },
        "scenario_stats": {
            k: {
                "n_runs": v.n_runs,
                "p99_mean": round(v.p99_mean, 1),
                "p99_std": round(v.p99_std, 1),
                "p99_cov": round(v.p99_cov, 1),
                "avg_scale_out": round(v.avg_scale_out_count, 1),
            }
            for k, v in stats.items()
        },
        "variance_decomposition": {k: round(v, 1) if isinstance(v, float) else v for k, v in (decomp or {}).items()},
        "correlations": {
            scenario: round(correlation_scale_out_p99(grouped.get(scenario, [])) or 0, 3)
            for scenario in ["s3-hybrid-reactive", "s4-hybrid-predictive"]
        },
    }

    output_path = base_path / "results/experiments/phase-b/2026-02-12_replicated-20runs/cold_start_decomposition.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  JSON output written to: {output_path.relative_to(base_path)}")


if __name__ == "__main__":
    main()
