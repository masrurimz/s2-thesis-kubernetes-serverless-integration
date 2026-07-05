"""Cold-start decomposition analysis.

Quantifies the cold-start penalty in hybrid scenarios (S3, S4) and its
contribution to p99 latency variance. Extracted from cold_start_analysis.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from analysis.constants import (
    COLD_START_MS_S3,
    COLD_START_MS_S4,
    COLD_START_RANGE,
    PHASE_A1_DECISIONS,
)
from shared.scenarios import SLO_THRESHOLD_MS


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


def compute_scenario_stats(scenario: str, runs: list[dict]) -> ScenarioStats:
    """Compute descriptive statistics for one scenario across its runs."""
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


def correlation_scale_out_p99(runs: list[dict]) -> Optional[float]:
    """Pearson correlation between scale_out_count and p99 for hybrid runs.

    Returns None when there are fewer than 3 runs or either series has zero
    variance (correlation is undefined).
    """
    if len(runs) < 3:
        return None
    so = [r["scale_out_count"] for r in runs]
    p99 = [r["p99_latency_ms"] for r in runs]
    if np.std(so) == 0 or np.std(p99) == 0:
        return None
    return float(np.corrcoef(so, p99)[0, 1])


def analyze_phase_a1_transition() -> dict:
    """Analyze the weight transition in Phase A1 to estimate cold start penalty.

    Key transition: Decision 2→3 (MAINTAIN 100/0 → SCALE_OUT 90/10) — when
    Knative first receives traffic and a cold start occurs.
    """
    first_scale_out = PHASE_A1_DECISIONS[2]  # decision 3
    warm_decisions = [d for d in PHASE_A1_DECISIONS if d["p99_ms"] and d["p99_ms"] < SLO_THRESHOLD_MS]

    p99_at_first_scale_out = first_scale_out["p99_ms"]  # 3648ms
    p99_before_scale_out = PHASE_A1_DECISIONS[1]["p99_ms"]  # 6516ms
    warm_p99s = [d["p99_ms"] for d in warm_decisions]
    p99_warm_mean = float(np.mean(warm_p99s))
    cold_start_estimate = float(np.mean(COLD_START_RANGE))  # ~958ms average

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


def variance_decomposition(stats: dict[str, ScenarioStats]) -> Optional[dict]:
    """Decompose p99 variance: σ²_total = σ²_base + σ²_cold + σ²_load.

    Uses S1 (K8s-only, no cold starts) and S2 (serverless-only) as the base
    variance reference. The excess variance in S3/S4 is attributable to cold
    start + routing overhead.
    """
    s1 = stats.get("s1-k8s-only")
    s2 = stats.get("s2-serverless-only")
    s3 = stats.get("s3-hybrid-reactive")
    s4 = stats.get("s4-hybrid-predictive")

    if not all([s1, s2, s3, s4]):
        return None

    base_var = (s1.p99_std**2 + s2.p99_std**2) / 2
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


def theoretical_cold_start_impact(
    rps: int = 100,
    duration_sec: int = 300,
    cold_start_ms: float = 958.0,
    weight_at_transition: int = 10,
    n_scale_out_events: int = 1,
    cold_start_duration_sec: float = 5.0,
) -> dict:
    """Model cold-start impact on p99 latency.

    When weight shifts from 0→10%, 10% of requests hit Knative. During the
    cold-start window (~1-5s), these requests experience high latency and
    dominate the p99 tail.
    """
    total_requests = rps * duration_sec
    cold_requests = int(rps * (weight_at_transition / 100.0) * cold_start_duration_sec * n_scale_out_events)
    p99_threshold_count = int(total_requests * 0.01)
    cold_start_dominates_p99 = cold_requests >= p99_threshold_count

    return {
        "total_requests": total_requests,
        "cold_start_requests": cold_requests,
        "p99_threshold_count": p99_threshold_count,
        "cold_start_dominates_p99": cold_start_dominates_p99,
        "cold_start_ms": cold_start_ms,
        "weight_at_transition": weight_at_transition,
    }
