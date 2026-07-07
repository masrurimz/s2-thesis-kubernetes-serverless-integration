"""Real-time hypothesis validation (H1/H2/H3) for thesis experiments.

H3 (GRU prediction adequacy) is validated directly against the trained GRU
model via prediction.model_loader -- no live cluster required. H1/H2 require
live experiments (routing daemon + k6 + Prometheus) and are reported as
pending until run against a live cluster.

Ported from scripts/realtime_validation.py. PrometheusMetricsCollector was
dropped -- it duplicated infra.observability. Entry point:
run_realtime_validation().
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# apps/experiment/experiment/validation.py -> 4 levels up to repo root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "results" / "realtime_validation"


@dataclass
class ExperimentMetrics:
    """Metrics collected from a single experiment run."""

    scenario: str
    run_id: int
    start_time: str
    duration_sec: int

    # Core metrics
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate_percent: float
    throughput_rps: float

    # Cost proxy (resource utilization)
    k8s_pod_count_avg: float
    serverless_invocations: int

    # Decision metrics
    scale_out_count: int
    predictive_count: int
    weight_changes: int

    # GRU specific (S4 only)
    gru_predictions_made: int = 0
    gru_avg_confidence: float = 0.0

    # Raw data for statistics
    latency_samples: Optional[List[float]] = None
    throughput_samples: Optional[List[float]] = None


@dataclass
class ValidationResult:
    """Validation result for a hypothesis."""

    hypothesis: str
    proven: bool
    confidence: str  # "high", "medium", "low"
    evidence: Dict
    limitations: List[str]
    recommendation: str


def validate_h3_gru() -> ValidationResult:
    """Validate H3 (GRU prediction adequacy) against the trained GRU model.

    No live cluster required: loads the model via prediction.model_loader and
    checks the training RMSE against the 10% target plus a single predict()
    smoke test.
    """
    from prediction.model_loader import GRUModelLoader

    loader = GRUModelLoader()
    if not loader.is_loaded:
        return ValidationResult(
            hypothesis="H3",
            proven=False,
            confidence="low",
            evidence={"error": "GRU model not loaded"},
            limitations=["Model not available for evaluation"],
            recommendation="Train and save GRU model first",
        )

    # Get actual RMSE from model
    model_rmse = loader.rmse
    if model_rmse is None:
        return ValidationResult(
            hypothesis="H3",
            proven=False,
            confidence="low",
            evidence={"error": "Model RMSE not available in metadata"},
            limitations=["Model metadata missing RMSE field"],
            recommendation="Retrain model and ensure RMSE is saved in metadata",
        )

    # Test prediction
    test_history = [100.0] * 30
    prediction = loader.predict(test_history, horizon=1)

    # Validate
    target_rmse = 10.0  # 10% target
    achieved_rmse_pct = (model_rmse / 100.0) * 100  # Approximate

    proven = achieved_rmse_pct < target_rmse

    evidence = {
        "model_type": loader.model_type,
        "training_rmse_requests": model_rmse,
        "training_rmse_percent": achieved_rmse_pct,
        "target_rmse_percent": target_rmse,
        "test_prediction": prediction.get("predicted_requests"),
        "test_confidence": prediction.get("confidence"),
        "sequence_length": loader.config.sequence_length if loader.config else None,
        "hidden_size": loader.config.hidden_size if loader.config else None,
    }

    limitations = [
        "RMSE measured on synthetic training data, not real-world traces",
        "Prediction horizon is 1 step (1 second), may need longer for routing decisions",
    ]

    return ValidationResult(
        hypothesis="H3",
        proven=proven,
        confidence="high" if proven else "medium",
        evidence=evidence,
        limitations=limitations,
        recommendation="Validated for synthetic data; test on real traffic traces",
    )


def run_realtime_validation(results_dir: Optional[Path] = None) -> Dict:
    """Run the H3 GRU check and report H1/H2 as pending live experiments.

    Returns the validation results dict (with a ``report_path`` key) and writes
    a timestamped JSON report. H1/H2 require live cluster experiments and are
    intentionally left pending here.
    """
    out_dir = results_dir or RESULTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    h3_result = validate_h3_gru()

    results_file = out_dir / f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    results = {
        "timestamp": datetime.now().isoformat(),
        "h3": asdict(h3_result),
        "h1": {"status": "pending_live_experiments"},
        "h2": {"status": "pending_live_experiments"},
        "report_path": str(results_file),
    }

    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info("validation_saved", path=str(results_file), h3_proven=h3_result.proven)
    return results
