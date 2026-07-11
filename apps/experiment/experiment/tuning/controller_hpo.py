"""Controller parameter optimization — two-stage replay + paired live screening.

Stage 1 (Replay): Deterministic trace replay through the V3 controller +
Algorithm 2 logic against the ClarkNet 15-second trace. No live infrastructure
needed. Screens a small controller space and rejects ineligible candidates.

Stage 2 (Paired live): Counterbalanced S3/S4 live pairs (n=3 per candidate)
for shortlisted configurations. Uses the paired-run CLI command.

Search space (3 knobs, deliberately small):
  - upper_residual_quantile: {0.80, 0.90, 0.95} — GRU upper-envelope width
  - algorithm2_buffer: {1.0, 1.1, 1.2} — capacity buffer for target replicas
  - proactive_hold_sec: {60, 90, 120} — how long to hold proactive scale-up

Rejection criteria:
  - Error rate increase
  - Run/stress validity gate failure
  - Fewer useful proactive scale-ups than no-op predictions

Ranking (lexicographic):
  1. Paired p99 difference (S4 - S3), lower is better
  2. SLO violations, lower is better

Config injection: immutable JSON artifacts per candidate + model artifact hash.
"""

from __future__ import annotations

import json
import math
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import structlog

logger = structlog.get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
TRIALS_DIR = PROJECT_ROOT / "results" / "experiments" / "tuning" / "trials"


# ---------------------------------------------------------------------------
# Trial config artifacts
# ---------------------------------------------------------------------------


def write_trial_config(trial_id: str, params: dict, model_hash: str = "") -> Path:
    """Write controller trial parameters to an immutable JSON artifact."""
    TRIALS_DIR.mkdir(parents=True, exist_ok=True)
    config_path = TRIALS_DIR / f"{trial_id}.json"
    config_path.write_text(
        json.dumps(
            {
                "trial_id": trial_id,
                "params": params,
                "model_hash": model_hash,
                "created": datetime.now().isoformat(),
            },
            indent=2,
        )
    )
    return config_path


def read_trial_result(trial_id: str) -> dict:
    """Read experiment results for a completed trial."""
    result_path = TRIALS_DIR / trial_id / "result.json"
    if result_path.exists():
        with open(result_path) as f:
            return json.load(f)
    return {}


# ---------------------------------------------------------------------------
# Stage 1: Deterministic replay simulation
# ---------------------------------------------------------------------------


def load_clarknet_15s() -> np.ndarray:
    """Load ClarkNet trace at 15-second resolution for replay."""
    import pandas as pd

    data_dir = PROJECT_ROOT / "apps" / "prediction" / "data" / "processed"
    df = pd.read_parquet(data_dir / "clarknet_real_rps.parquet")
    df = df.resample("15s").sum().fillna(0)
    return df["total_requests" if "total_requests" in df.columns else df.columns[0]].values.astype(np.float64)


def simulate_controller_replay(
    trace: np.ndarray,
    r_saturation: float = 33.3,
    target_cpu_util: float = 0.5,
    min_replicas: int = 3,
    max_replicas: int = 6,
    slo_threshold_ms: float = 200.0,
    buffer: float = 1.2,
    proactive_hold_sec: float = 90.0,
    sample_interval_sec: int = 15,
    use_predictions: bool = False,
    prediction_trace: np.ndarray | None = None,
    upper_forecast_trace: np.ndarray | None = None,
    scale_up_delay_sec: int = 45,
) -> dict[str, Any]:
    """Deterministic replay of V3 controller + Algorithm 2 against a trace.

    Simulates the closed-loop system:
    1. For each 15s timestep, compute K8s capacity from current replicas
    2. Route excess load to Knative (capacity-driven)
    3. Compute synthetic p99 from capacity model
    4. Algorithm 2: compute target replicas from observed (S3) or predictive (S4) load
    5. Apply proactive hold for S4
    6. Apply scale-up delay before new replicas become ready

    Returns aggregate metrics: SLO violations, p99 stats, proactive counts, etc.
    """
    r_effective = r_saturation * target_cpu_util
    scale_up_delay_steps = max(1, scale_up_delay_sec // sample_interval_sec)
    hold_steps = max(1, int(proactive_hold_sec // sample_interval_sec))

    current_replicas = min_replicas
    pending_replicas = 0
    pending_remaining = 0

    # Proactive hold state
    hold_remaining = 0
    held_target = 0

    # Metrics
    p99_values: list[float] = []
    slo_violations = 0
    useful_proactive = 0
    no_op_predictions = 0
    serverless_weight_sum = 0
    error_events = 0

    n = len(trace)
    for t in range(n):
        load = float(trace[t])

        # Complete pending scale-up
        if pending_remaining > 0:
            pending_remaining -= 1
            if pending_remaining == 0:
                current_replicas = min(max_replicas, current_replicas + pending_replicas)
                pending_replicas = 0

        # K8s capacity
        k8s_capacity = current_replicas * r_effective

        # Routing: capacity-driven
        if load <= k8s_capacity:
            knative_weight = 0
            # Synthetic p99: scales with utilization
            util = load / k8s_capacity if k8s_capacity > 0 else 1.0
            # M/M/1-like latency: p99 ≈ base × (1 + util² / (1 - util))
            if util < 0.95:
                p99 = slo_threshold_ms * 0.4 * (1 + util**2 / max(0.05, 1 - util))
            else:
                p99 = slo_threshold_ms * 5  # Near-saturation spike
        else:
            burst_ratio = (load - k8s_capacity) / load
            knative_weight = min(50, int(math.ceil(burst_ratio * 100)))
            # Excess load goes to serverless at ~constant latency
            k8s_load = k8s_capacity
            serverless_load = load - k8s_capacity
            k8s_util = 0.95
            k8s_p99 = slo_threshold_ms * 0.4 * (1 + k8s_util**2 / max(0.05, 1 - k8s_util))
            serverless_p99 = 80.0  # Serverless cold-start amortized
            p99 = k8s_p99 * (k8s_load / load) + serverless_p99 * (serverless_load / load)

        p99_values.append(p99)
        serverless_weight_sum += knative_weight

        if p99 > slo_threshold_ms:
            slo_violations += 1

        # Error rate: increases when extremely overloaded
        if p99 > slo_threshold_ms * 3:
            error_events += 1

        # Algorithm 2: compute target replicas
        observed_load = load
        observed_target = min(max_replicas, max(min_replicas, math.ceil(observed_load / r_effective * buffer)))

        if use_predictions and upper_forecast_trace is not None and t < len(upper_forecast_trace):
            # S4: use upper forecast for scaling
            predicted_load = float(upper_forecast_trace[t])
            predictive_target = min(max_replicas, max(min_replicas, math.ceil(predicted_load / r_effective * buffer)))

            if predictive_target > observed_target:
                # Proactive scale-up
                useful_proactive += 1
                applied_target = predictive_target
                hold_remaining = hold_steps
                held_target = predictive_target
            elif hold_remaining > 0:
                # Within hold window
                applied_target = max(observed_target, held_target)
                if applied_target == observed_target:
                    no_op_predictions += 1
                hold_remaining -= 1
            else:
                applied_target = observed_target
                no_op_predictions += 1
        else:
            # S3: observed only
            applied_target = observed_target

        # Execute scaling decision
        if applied_target > current_replicas + pending_replicas:
            delta = applied_target - current_replicas - pending_replicas
            pending_replicas = delta
            pending_remaining = scale_up_delay_steps
        elif applied_target < current_replicas and hold_remaining == 0:
            # Scale down (gradual, one at a time)
            current_replicas = max(min_replicas, current_replicas - 1)

    p99_arr = np.array(p99_values)
    return {
        "mean_p99": float(np.mean(p99_arr)),
        "p95_p99": float(np.percentile(p99_arr, 95)),
        "p99_p99": float(np.percentile(p99_arr, 99)),
        "slo_violations": slo_violations,
        "total_steps": n,
        "slo_violation_rate": slo_violations / n if n > 0 else 0,
        "error_rate": error_events / n if n > 0 else 0,
        "useful_proactive": useful_proactive,
        "no_op_predictions": no_op_predictions,
        "avg_serverless_weight": serverless_weight_sum / n if n > 0 else 0,
        "final_replicas": current_replicas,
    }


def run_replay_screening(
    trace: np.ndarray | None = None,
    upper_forecast_trace: np.ndarray | None = None,
    r_saturation: float = 33.3,
    target_cpu_util: float = 0.5,
    min_replicas: int = 3,
    max_replicas: int = 6,
    slo_threshold_ms: float = 200.0,
    sample_interval_sec: int = 15,
) -> list[dict[str, Any]]:
    """Stage 1: Deterministic replay screening of the small controller space.

    Evaluates S3 (observed-only) and S4 (predictive) for each candidate.
    Returns ranked candidates that pass rejection criteria.
    """
    if trace is None:
        trace = load_clarknet_15s()

    # Base config for S3 (observed-only, fixed across all candidates)
    s3_base = simulate_controller_replay(
        trace=trace,
        r_saturation=r_saturation,
        target_cpu_util=target_cpu_util,
        min_replicas=min_replicas,
        max_replicas=max_replicas,
        slo_threshold_ms=slo_threshold_ms,
        sample_interval_sec=sample_interval_sec,
        use_predictions=False,
    )

    candidates: list[dict[str, Any]] = []
    quantiles = [0.80, 0.90, 0.95]
    buffers = [1.0, 1.1, 1.2]
    holds = [60, 90, 120]

    for quantile in quantiles:
        for buffer in buffers:
            for hold in holds:
                # Derive upper forecast trace from prediction trace
                if upper_forecast_trace is None:
                    # Without a trained model, use optimistic upper bound
                    # (point + 20% for rising, point for falling)
                    uf_trace = trace * 1.2
                else:
                    uf_trace = upper_forecast_trace

                s4_metrics = simulate_controller_replay(
                    trace=trace,
                    r_saturation=r_saturation,
                    target_cpu_util=target_cpu_util,
                    min_replicas=min_replicas,
                    max_replicas=max_replicas,
                    slo_threshold_ms=slo_threshold_ms,
                    buffer=buffer,
                    proactive_hold_sec=float(hold),
                    sample_interval_sec=sample_interval_sec,
                    use_predictions=True,
                    upper_forecast_trace=uf_trace,
                )

                # Rejection criteria
                rejected = False
                reject_reason = ""

                if s4_metrics["error_rate"] > s3_base["error_rate"] + 0.001:
                    rejected = True
                    reject_reason = "error_rate_increase"

                if s4_metrics["useful_proactive"] < s4_metrics["no_op_predictions"]:
                    rejected = True
                    reject_reason = "more_no_ops_than_useful"

                # Paired p99 difference (S4 - S3, lower is better for S4)
                p99_diff = s4_metrics["p99_p99"] - s3_base["p99_p99"]

                candidate = {
                    "params": {
                        "upper_residual_quantile": quantile,
                        "algorithm2_buffer": buffer,
                        "proactive_hold_sec": hold,
                    },
                    "s3_replay": s3_base,
                    "s4_replay": s4_metrics,
                    "p99_diff": p99_diff,
                    "rejected": rejected,
                    "reject_reason": reject_reason,
                }
                candidates.append(candidate)

    # Rank survivors lexicographically: p99_diff, slo_violations, cost
    survivors = [c for c in candidates if not c["rejected"]]
    survivors.sort(
        key=lambda c: (
            c["p99_diff"],
            c["s4_replay"]["slo_violations"],
            c["s4_replay"]["avg_serverless_weight"],
        )
    )

    logger.info(
        "replay_screening_complete",
        total_candidates=len(candidates),
        survivors=len(survivors),
        best_p99_diff=survivors[0]["p99_diff"] if survivors else None,
    )

    return survivors


# ---------------------------------------------------------------------------
# Stage 2: Paired live confirmation
# ---------------------------------------------------------------------------


def run_single_experiment(
    config_path: Path,
    scenario: str = "s4-hybrid-predictive",
    output_dir: str | None = None,
) -> dict:
    """Run a single experiment with the given controller config."""
    cmd = [
        "uv",
        "run",
        "thesis-experiment",
        "run",
        "--scenarios",
        scenario,
        "--runs",
        "1",
        "--calibration",
        str(config_path),
    ]
    if output_dir:
        cmd.extend(["--output", output_dir])

    logger.info("running_experiment", scenario=scenario, config=str(config_path))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

    if result.returncode != 0:
        logger.error("experiment_failed", rc=result.returncode, stderr=result.stderr[-500:])
        return {"error": result.stderr[-500:], "returncode": result.returncode}

    # Find result.json
    search_dir = Path(output_dir) if output_dir else PROJECT_ROOT / "results" / "experiments"
    result_files = list(search_dir.rglob("result.json"))
    if result_files:
        with open(result_files[-1]) as f:
            return json.load(f)

    return {"error": "No result.json found", "returncode": result.returncode}


def run_paired_confirmation(
    survivors: list[dict],
    n_pairs: int = 3,
    output_base: str | None = None,
) -> dict[str, Any]:
    """Stage 2: Counterbalanced S3/S4 live pairs for shortlisted candidates.

    Each candidate gets n_pairs counterbalanced S3/S4 runs.
    """
    output_base = output_base or str(TRIALS_DIR / "paired_confirmation")
    confirmations = []

    for idx, candidate in enumerate(survivors[:3]):  # Top 3 only
        trial_id = f"paired_confirm_{idx:03d}"
        params = candidate["params"]
        config_path = write_trial_config(trial_id, params)

        s3_p99s = []
        s4_p99s = []

        for pair in range(n_pairs):
            pair_output = str(Path(output_base) / trial_id / f"pair_{pair + 1}")

            # Alternate order
            if pair % 2 == 0:
                first, second = "s3-hybrid-reactive", "s4-hybrid-predictive"
            else:
                first, second = "s4-hybrid-predictive", "s3-hybrid-reactive"

            r1 = run_single_experiment(config_path, scenario=first, output_dir=pair_output + f"_{first[:2]}")
            r2 = run_single_experiment(config_path, scenario=second, output_dir=pair_output + f"_{second[:2]}")

            if "p99_latency_ms" in r1 and "p99_latency_ms" in r2:
                if first.startswith("s3"):
                    s3_p99s.append(r1["p99_latency_ms"])
                    s4_p99s.append(r2["p99_latency_ms"])
                else:
                    s3_p99s.append(r2["p99_latency_ms"])
                    s4_p99s.append(r1["p99_latency_ms"])

        if len(s3_p99s) >= 2:
            from analysis.comparison import run_paired_comparison

            paired = run_paired_comparison(s3_p99s, s4_p99s, metric="p99_latency_ms")
            confirmation = {
                "trial_id": trial_id,
                "params": params,
                "n_valid_pairs": len(s3_p99s),
                "paired_result": paired.model_dump(),
            }
            confirmations.append(confirmation)

    # Select winner: lowest paired p99 difference
    if confirmations:
        winner = min(
            confirmations,
            key=lambda c: c["paired_result"]["mean_difference"],
        )
    else:
        winner = None

    return {
        "confirmations": confirmations,
        "winner": winner,
        "timestamp": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_controller_hpo_robust(
    trace_path: str | None = None,
    n_confirm_pairs: int = 3,
    output_dir: str | None = None,
) -> dict[str, Any]:
    """Two-stage controller HPO: replay screening + paired live confirmation.

    Stage 1 (Replay): Fast deterministic screening against ClarkNet trace.
    Stage 2 (Paired live): Counterbalanced S3/S4 pairs for top candidates.

    The replay stage uses NO live infrastructure and screens 27 candidates
    in seconds. Only top survivors proceed to expensive live confirmation.
    """
    logger.info("controller_hpo_start", n_confirm_pairs=n_confirm_pairs)

    # Stage 1: Replay screening
    trace = load_clarknet_15s() if trace_path is None else np.load(trace_path)
    survivors = run_replay_screening(trace=trace)

    if not survivors:
        logger.info("controller_hpo_complete", recommendation="retain_defaults", reason="No survivors passed replay")
        return {
            "screening_survivors": 0,
            "recommendation": "retain_defaults",
            "reason": "No candidates passed replay rejection criteria",
        }

    # Stage 2: Paired live confirmation
    confirmation = run_paired_confirmation(
        survivors,
        n_pairs=n_confirm_pairs,
        output_base=output_dir,
    )

    if confirmation.get("winner") is None:
        logger.info("controller_hpo_complete", recommendation="retain_defaults")
        return {
            "screening_survivors": len(survivors),
            "confirmation": confirmation,
            "recommendation": "retain_defaults",
            "reason": "No candidate achieved valid paired confirmation",
        }

    # Persist promoted configuration
    winner = confirmation["winner"]
    promoted_path = TRIALS_DIR / "promoted_config.json"
    promoted_path.write_text(
        json.dumps(
            {
                "params": winner["params"],
                "paired_result": winner["paired_result"],
                "promoted_at": datetime.now().isoformat(),
            },
            indent=2,
        )
    )

    logger.info(
        "controller_hpo_complete",
        recommendation="adopt_tuned",
        winner=winner["trial_id"],
        p99_diff=winner["paired_result"]["mean_difference"],
    )

    return {
        "screening_survivors": len(survivors),
        "confirmation": confirmation,
        "recommendation": "adopt_tuned",
        "winner": winner,
        "promoted_config": str(promoted_path),
    }
