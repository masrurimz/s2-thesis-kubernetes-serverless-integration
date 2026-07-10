"""Surrogate-assisted HPO for cloud routing controllers.

Uses a Gaussian Process surrogate trained on existing experiment data to
screen thousands of parameter combinations in seconds, avoiding expensive
20-minute real experiments. Based on multi-fidelity optimization concepts
from BOHB (Falkner et al., 2018) and digital twin approaches from
KAPETÁNIOS (2022).

Two-stage pipeline:
  1. Surrogate screening (seconds): GP predicts SLO + p99 for 10K samples
  2. Real validation (~20 min each): Top-K candidates validated on live system

The surrogate naturally handles the overfitting problem identified in
controller_hpo.py — by learning from ALL available data points (including
repeated runs), it captures the noise structure and avoids selecting
single-run outliers.

Usage::

    from experiment.tuning.surrogate_hpo import run_surrogate_hpo
    result = run_surrogate_hpo(validate_top=3)

References:
  - BOHB: Falkner et al. (2018), "BOHB: Robust and Efficient Hyperparameter
    Optimization at Scale", PMLR 80.
  - KAPETÁNIOS: kptns/kapetanios (2022), digital twin for K8s HPA tuning.
  - Cawley & Talbot (2010), "On Over-fitting in Model Selection and
    Subsequent Selection Bias in Performance Evaluation", JMLR 11.
"""

import json
import logging
import pickle
from typing import Any, Optional

from datetime import datetime
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

# Project root (parent of apps/experiment/)
PROJECT_ROOT = Path(__file__).resolve().parents[4]
RESULTS_DIR = PROJECT_ROOT / "results" / "experiments" / "tuning"

# Controller parameter search space (from controller_hpo.py)
PARAM_BOUNDS = {
    "target_cpu_util": (0.3, 0.9),
    "kp_burn": (0.1, 2.0),
    "proactive_trend_threshold": (1.0, 10.0),
    "proactive_approach_ratio": (0.3, 0.9),
}

# Default CalibrationConfig values (for comparison)
DEFAULTS = {
    "target_cpu_util": 0.5,
    "kp_burn": 0.5,
    "proactive_trend_threshold": 3.0,
    "proactive_approach_ratio": 0.6,
}


def collect_experiment_data() -> dict:
    """Collect all (params, SLO, p99) data points from existing experiments.

    Sources:
      - Controller HPO screening trials (ctrl_trial_*)
      - Holdout validation runs
      - Original S4 proactive experiments (default params)

    Returns:
        Dict with keys 'X' (n×4 array), 'y_slo', 'y_p99', 'sources'.
    """
    data_points = []

    # 1. Controller HPO screening
    screening_dir = RESULTS_DIR / "trials"
    if screening_dir.exists():
        for trial_dir in sorted(screening_dir.glob("ctrl_trial_*")):
            config_path = trial_dir / "config.json"
            if not config_path.exists():
                continue
            with open(config_path) as f:
                config = json.load(f)
            results = list(trial_dir.rglob("result.json"))
            if not results:
                continue
            with open(results[0]) as f:
                result = json.load(f)
            data_points.append(
                {
                    "target_cpu_util": config["target_cpu_util"],
                    "kp_burn": config["kp_burn"],
                    "proactive_trend_threshold": config["proactive_trend_threshold"],
                    "proactive_approach_ratio": config["proactive_approach_ratio"],
                    "slo": result["slo_violations_k6"],
                    "p99": result["p99_latency_ms"],
                    "source": f"screening_{trial_dir.name}",
                }
            )

    # 2. Holdout validation (uses trial-0 params: cpu=0.659, kp=1.49)
    holdout_dir = PROJECT_ROOT / "results/experiments/phase-b/2026-07-10_tuned_holdout"
    if holdout_dir.exists():
        for rj in sorted(holdout_dir.rglob("result.json")):
            with open(rj) as f:
                result = json.load(f)
            data_points.append(
                {
                    "target_cpu_util": 0.659,
                    "kp_burn": 1.49,
                    "proactive_trend_threshold": 4.37,
                    "proactive_approach_ratio": 0.87,
                    "slo": result["slo_violations_k6"],
                    "p99": result["p99_latency_ms"],
                    "source": f"holdout_run{result['run_id']}",
                }
            )

    # 3. Original S4 experiments (default params)
    proactive_dir = PROJECT_ROOT / "results/experiments/phase-b/2026-07-08_fib33_proactive"
    if proactive_dir.exists():
        for rj in sorted(proactive_dir.glob("s4-hybrid-predictive_run*/result.json")):
            with open(rj) as f:
                result = json.load(f)
            data_points.append(
                {
                    **DEFAULTS,
                    "slo": result["slo_violations_k6"],
                    "p99": result["p99_latency_ms"],
                    "source": f"original_s4_run{result['run_id']}",
                }
            )

    param_keys = list(PARAM_BOUNDS.keys())
    X = np.array([[d[k] for k in param_keys] for d in data_points])
    y_slo = np.array([d["slo"] for d in data_points])
    y_p99 = np.array([d["p99"] for d in data_points])

    logger.info(
        "surrogate_data_collected",
        n_points=len(data_points),
        n_unique_combos=len(np.unique(X, axis=0)),
    )

    return {
        "X": X,
        "y_slo": y_slo,
        "y_p99": y_p99,
        "sources": [d["source"] for d in data_points],
        "param_keys": param_keys,
    }


def fit_gp_surrogate(
    X: np.ndarray,
    y: np.ndarray,
    use_log: bool = False,
) -> Any:
    """Fit a 2D Gaussian Process surrogate on (target_cpu_util, kp_burn).

    Only 2 of the 4 controller params showed signal in screening.
    The other 2 (proactive_trend_threshold, proactive_approach_ratio) are
    fixed at defaults — their GP length scales hit the upper bound,
    indicating no meaningful relationship with performance.

    Args:
        X: n×4 array of controller params (only first 2 columns used).
        y: n array of target values (SLO or p99).
        use_log: If True, log-transform y before fitting (for SLO).

    Returns:
        Fitted GaussianProcessRegressor.
    """
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import ConstantKernel, RBF, WhiteKernel

    # Use only 2D (target_cpu_util, kp_burn)
    X_2d = X[:, :2].copy()

    # Aggregate repeated measurements
    unique = np.unique(X_2d, axis=0)
    X_agg = []
    y_agg = []
    for u in unique:
        mask = np.all(X_2d == u, axis=1)
        X_agg.append(u)
        y_agg.append(np.mean(y[mask]))
    X_agg = np.array(X_agg)
    y_agg = np.array(y_agg)

    if use_log:
        y_agg = np.log(y_agg)

    # Normalize inputs to [0, 1]
    bounds_2d = np.array([PARAM_BOUNDS["target_cpu_util"], PARAM_BOUNDS["kp_burn"]])
    X_norm = (X_agg - bounds_2d[:, 0]) / (bounds_2d[:, 1] - bounds_2d[:, 0])

    # RBF kernel with moderate length scale + noise
    kernel = ConstantKernel(1.0) * RBF(length_scale=0.3, length_scale_bounds=(0.1, 2.0)) + WhiteKernel(
        noise_level=0.3, noise_level_bounds=(0.01, 1.0)
    )
    gp = GaussianProcessRegressor(kernel=kernel, normalize_y=True, random_state=42)
    gp.fit(X_norm, y_agg)

    logger.info(
        "gp_fitted",
        kernel=str(gp.kernel_),
        log_marginal_likelihood=round(gp.log_marginal_likelihood(), 2),
        n_training=len(X_agg),
        use_log=use_log,
    )
    return gp


def run_surrogate_screening(
    gp_slo: Any,
    gp_p99: Any,
    n_samples: int = 10000,
    p99_threshold: float = 200.0,
    slo_log_transformed: bool = True,
) -> list[dict]:
    """Monte Carlo screening of parameter space using GP surrogates.

    Samples n_samples random parameter combinations, predicts SLO and p99
    using the GPs, filters by p99 constraint, and ranks by predicted SLO.

    Args:
        gp_slo: Fitted GP for SLO prediction.
        gp_p99: Fitted GP for p99 prediction.
        n_samples: Number of Monte Carlo samples.
        p99_threshold: Hard constraint on predicted p99 (ms).
        slo_log_transformed: Whether gp_slo was trained on log(SLO).

    Returns:
        List of candidate dicts, sorted by predicted SLO ascending.
    """
    bounds_2d = np.array([PARAM_BOUNDS["target_cpu_util"], PARAM_BOUNDS["kp_burn"]])
    np.random.seed(42)

    # Sample uniformly from 2D search space
    X_samp = np.random.uniform(bounds_2d[:, 0], bounds_2d[:, 1], size=(n_samples, 2))
    X_norm = (X_samp - bounds_2d[:, 0]) / (bounds_2d[:, 1] - bounds_2d[:, 0])

    # GP predictions
    slo_pred, slo_std = gp_slo.predict(X_norm, return_std=True)
    if slo_log_transformed:
        slo_pred = np.exp(slo_pred)
        slo_std = slo_pred * slo_std  # Approximate error propagation

    p99_pred, p99_std = gp_p99.predict(X_norm, return_std=True)

    # Filter by p99 constraint
    mask = p99_pred < p99_threshold
    safe_idx = np.where(mask)[0]
    ranked = np.argsort(slo_pred[safe_idx])

    candidates = []
    for rank, i in enumerate(ranked):
        oi = safe_idx[i]
        candidates.append(
            {
                "rank": rank + 1,
                "target_cpu_util": float(X_samp[oi, 0]),
                "kp_burn": float(X_samp[oi, 1]),
                "proactive_trend_threshold": DEFAULTS["proactive_trend_threshold"],
                "proactive_approach_ratio": DEFAULTS["proactive_approach_ratio"],
                "pred_slo": float(slo_pred[oi]),
                "pred_slo_std": float(slo_std[oi]),
                "pred_p99": float(p99_pred[oi]),
                "pred_p99_std": float(p99_std[oi]),
            }
        )

    logger.info(
        "surrogate_screening_complete",
        n_samples=n_samples,
        n_safe=int(mask.sum()),
        pct_safe=round(100 * mask.sum() / n_samples, 1),
        best_pred_slo=round(candidates[0]["pred_slo"], 0) if candidates else None,
        best_pred_p99=round(candidates[0]["pred_p99"], 1) if candidates else None,
    )
    return candidates


def run_surrogate_hpo(
    validate_top: int = 0,
    output_dir: Optional[Path] = None,
) -> dict:
    """Full surrogate-assisted HPO pipeline.

    1. Collect experiment data from existing results
    2. Fit GP surrogates for SLO and p99
    3. Run Monte Carlo screening (10K samples in seconds)
    4. Optionally validate top-K candidates on real system

    Args:
        validate_top: Number of top candidates to validate (0 = skip).
        output_dir: Where to save results. Defaults to tuning/ dir.

    Returns:
        Dict with surrogate predictions, top candidates, and validation results.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_dir = output_dir or (RESULTS_DIR / f"surrogate_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Stage 1: Collect data
    data = collect_experiment_data()
    logger.info("surrogate_hpo_start", n_points=len(data["X"]), output_dir=str(output_dir))

    # Stage 2: Fit GPs
    gp_slo = fit_gp_surrogate(data["X"], data["y_slo"], use_log=True)
    gp_p99 = fit_gp_surrogate(data["X"], data["y_p99"], use_log=False)

    # Save GP models
    with open(output_dir / "gp_models.pkl", "wb") as f:
        pickle.dump({"gp_slo": gp_slo, "gp_p99": gp_p99}, f)

    # Stage 3: Monte Carlo screening
    candidates = run_surrogate_screening(gp_slo, gp_p99, n_samples=10000)

    # Predict defaults for comparison
    bounds_2d = np.array([PARAM_BOUNDS["target_cpu_util"], PARAM_BOUNDS["kp_burn"]])
    d_norm = (np.array([[0.5, 0.5]]) - bounds_2d[:, 0]) / (bounds_2d[:, 1] - bounds_2d[:, 0])
    d_slo, d_slo_std = gp_slo.predict(d_norm, return_std=True)
    d_p99, d_p99_std = gp_p99.predict(d_norm, return_std=True)
    default_pred = {
        "pred_slo": float(np.exp(d_slo[0])),
        "pred_slo_std": float(np.exp(d_slo[0]) * d_slo_std[0]),
        "pred_p99": float(d_p99[0]),
        "pred_p99_std": float(d_p99_std[0]),
    }

    # Stage 4: Optional real validation
    validation_results = []
    if validate_top > 0:
        from experiment.tuning.controller_hpo import run_single_experiment

        for i, candidate in enumerate(candidates[:validate_top]):
            trial_id = f"surrogate_val_{i:03d}"
            config_path = output_dir / f"{trial_id}_config.json"
            params = {k: candidate[k] for k in PARAM_BOUNDS}
            with open(config_path, "w") as f:
                json.dump(params, f, indent=2)

            exp_dir = str(output_dir / trial_id)
            result = run_single_experiment(
                config_path,
                scenario="s4-hybrid-predictive",
                output_dir=exp_dir,
            )

            validation_results.append(
                {
                    "candidate_rank": candidate["rank"],
                    "params": params,
                    "gp_pred_slo": candidate["pred_slo"],
                    "real_slo": result.get("slo_violations_k6"),
                    "gp_pred_p99": candidate["pred_p99"],
                    "real_p99": result.get("p99_latency_ms"),
                }
            )
            logger.info(
                "surrogate_validation",
                rank=candidate["rank"],
                gp_pred_slo=candidate["pred_slo"],
                real_slo=result.get("slo_violations_k6"),
                gp_pred_p99=candidate["pred_p99"],
                real_p99=result.get("p99_latency_ms"),
            )

    # Save full results
    result = {
        "timestamp": timestamp,
        "n_data_points": len(data["X"]),
        "n_unique_combos": len(np.unique(data["X"], axis=0)),
        "gp_slo_kernel": str(gp_slo.kernel_),
        "gp_p99_kernel": str(gp_p99.kernel_),
        "default_prediction": default_pred,
        "real_default": {"slo": 702, "p99": 188},
        "top_candidates": candidates[:10],
        "validation_results": validation_results,
        "output_dir": str(output_dir),
    }

    with open(output_dir / "surrogate_results.json", "w") as f:
        json.dump(result, f, indent=2, default=str)

    logger.info(
        "surrogate_hpo_complete",
        n_candidates=len(candidates),
        n_validated=len(validation_results),
        best_pred_slo=candidates[0]["pred_slo"] if candidates else None,
        default_pred_slo=default_pred["pred_slo"],
    )

    return result
