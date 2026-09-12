"""Demand Complexity Index (DCI) workload characterization.

Computes DCI from workload data to detect distributional shifts that may
warrant GRU model retraining. Based on DCI Meta-Learning paper
(Nature Scientific Reports 2025, doi:10.1038/s41598-025-31508-x).

DCI is used as a REPORTING metric — retraining triggers require DCI shift
AND forecast degradation (HyPA pattern, IEEE NFV-SDN 2023).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import numpy as np
import structlog

from shared.artifacts import read_prometheus_export, read_result

logger = structlog.get_logger(__name__)


def compute_dci(values: np.ndarray) -> Dict[str, float]:
    """Compute Demand Complexity Index and its components.

    Args:
        values: 1D array of demand values (e.g., RPS per interval).

    Returns:
        Dict with cv, zero_ratio, spikiness, and dci_composite.
    """
    values = np.asarray(values, dtype=np.float64)
    n = len(values)

    if n == 0:
        return {"cv": 0.0, "zero_ratio": 1.0, "spikiness": 0.0, "dci_composite": 0.0}

    mean = float(np.mean(values))
    std = float(np.std(values))

    # Coefficient of variation (most influential DCI feature per Nature 2025)
    cv = std / mean if mean > 0 else 0.0

    # Zero-demand ratio (fraction of intervals with zero or near-zero demand)
    zero_ratio = float(np.mean(values < 0.01 * max(mean, 1.0)))

    # Spike severity: ratio of 95th percentile to median
    median = float(np.median(values))
    p95 = float(np.percentile(values, 95))
    spikiness = (p95 / median) if median > 0 else 0.0

    # DCI composite: weighted average (CV has highest weight per paper)
    dci_composite = 0.5 * min(cv, 3.0) + 0.3 * zero_ratio + 0.2 * min(spikiness / 5.0, 1.0)

    return {
        "cv": round(cv, 4),
        "zero_ratio": round(zero_ratio, 4),
        "spikiness": round(spikiness, 4),
        "dci_composite": round(dci_composite, 4),
        "mean": round(mean, 2),
        "n_samples": n,
    }


def detect_workload_shift(
    baseline_dci: Dict[str, float],
    current_dci: Dict[str, float],
    threshold: float = 0.3,
) -> Dict:
    """Check if workload has shifted enough to warrant investigation.

    Shift = |current_dci - baseline_dci| / max(baseline_dci, epsilon).

    Args:
        baseline_dci: DCI from reference period.
        current_dci: DCI from current period.
        threshold: Relative shift threshold (0.3 = 30% change).

    Returns:
        Dict with shift_detected, shift_magnitude, reason.
    """
    base = baseline_dci.get("dci_composite", 0)
    curr = current_dci.get("dci_composite", 0)

    shift = abs(curr - base) / max(base, 0.01)
    detected = shift > threshold

    # Also check individual components
    cv_shift = abs(current_dci.get("cv", 0) - baseline_dci.get("cv", 0)) / max(baseline_dci.get("cv", 0.01), 0.01)

    reason = "stable"
    if detected:
        reason = f"DCI shifted {shift:.1%} (threshold {threshold:.0%})"
    elif cv_shift > threshold:
        reason = f"CV shifted {cv_shift:.1%} (variability change)"

    return {
        "shift_detected": detected or cv_shift > threshold,
        "shift_magnitude": round(shift, 4),
        "cv_shift": round(cv_shift, 4),
        "threshold": threshold,
        "reason": reason,
    }


def analyze_workload_from_experiment(experiment_dir: str) -> Dict:
    """Analyze workload characteristics from experiment results.

    DCI needs a demand series, and the demand series this repo records is the
    exported ``prom_rps`` query — requests per second over the run window. The
    utilization samples are capacity, not demand, and reading them here once
    produced a zero DCI for every run whose resource file existed, because the keys
    it looked for are not written by any producer.
    """
    exp_path = Path(experiment_dir)

    series = read_prometheus_export(exp_path)
    demand = [value for _, value in series.get("prom_rps", [])]
    if demand:
        return compute_dci(np.array(demand))

    # Fallback: the run summary carries a single throughput figure, not a series.
    result = read_result(exp_path)
    if result is not None:
        return {
            "cv": 0.0,
            "zero_ratio": 0.0,
            "spikiness": 0.0,
            "dci_composite": 0.0,
            "mean": round(result.throughput_rps, 2),
            "n_samples": 0,
            "note": "Estimated from summary metrics — no per-interval data available",
        }

    return {"error": f"No data found in {experiment_dir}"}


def compare_experiments(experiment_dirs: List[str], threshold: float = 0.3) -> Dict:
    """Compare DCI across multiple experiment runs.

    Args:
        experiment_dirs: List of experiment directory paths.
        threshold: Shift detection threshold.

    Returns:
        Dict with per-experiment DCI, baseline, and shift analysis.
    """
    results = []
    for d in experiment_dirs:
        dci = analyze_workload_from_experiment(d)
        dci["experiment_dir"] = d
        results.append(dci)

    # Use first experiment as baseline
    baseline = results[0] if results else {}
    shifts = []
    for r in results[1:]:
        shift = detect_workload_shift(baseline, r, threshold)
        shift["experiment_dir"] = r["experiment_dir"]
        shifts.append(shift)

    return {
        "baseline": baseline,
        "experiments": results,
        "shifts": shifts,
        "threshold": threshold,
    }
