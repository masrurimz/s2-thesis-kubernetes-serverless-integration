#!/usr/bin/env python3
"""
GRU Model Loader — thin wrapper around the canonical GRUPredictor.

All model architecture (GRUConfig, GRUNetwork) lives in gru_predictor.py.
This module provides the loader/predict interface consumed by the FastAPI
server, with auto-discovery of model artifacts from standard paths.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import structlog

from prediction.gru_predictor import GRUPredictor, GRUConfig, ARTIFACT_SCHEMA_VERSION

logger = structlog.get_logger(__name__)


class GRUModelLoader:
    """
    Loads and manages GRU prediction models.

    Delegates all architecture and inference to the canonical
    :class:`~prediction.gru_predictor.GRUPredictor`.
    """

    DEFAULT_MODEL_PATHS = [
        Path("data/models/gru_model.pt"),
        Path("controller/data/models/gru_model.pt"),
        Path(__file__).parent.parent / "data/models/gru_model.pt",
        Path(__file__).parent.parent / "controller/data/models/gru_model.pt",
    ]

    def __init__(self, model_path: Optional[Path] = None):
        self._predictor = GRUPredictor()
        self.is_loaded: bool = False
        self.model_path: Optional[Path] = None
        self.model_type: str = "unknown"

        if model_path:
            self.load(model_path)
        else:
            self._auto_load()

    def _auto_load(self) -> bool:
        """Try loading from default paths."""
        for path in self.DEFAULT_MODEL_PATHS:
            if path.exists():
                if self.load(path):
                    return True
        logger.warning("No model found in default paths")
        return False

    def load(self, path: Path) -> bool:
        """Load model artifact via the canonical predictor."""
        path = Path(path)
        if not path.exists():
            logger.error("Model file not found", path=str(path))
            return False

        if self._predictor.load_model(path):
            self.is_loaded = True
            self.model_path = path
            self.model_type = "pytorch" if str(path).endswith(".pt") else "sklearn"
            logger.info(
                "Model loaded via canonical predictor",
                path=str(path),
                horizon=self._predictor.config.prediction_horizon,
                sample_interval_sec=self._predictor.config.sample_interval_sec,
            )
            return True

        logger.error("Failed to load model", path=str(path))
        return False

    # ------------------------------------------------------------------
    # Delegate properties
    # ------------------------------------------------------------------

    @property
    def config(self) -> Optional[GRUConfig]:
        return self._predictor.config if self.is_loaded else None

    @property
    def scaler_mean(self) -> float:
        return self._predictor.scaler_mean

    @property
    def scaler_std(self) -> float:
        return self._predictor.scaler_std

    @property
    def rmse(self) -> Optional[float]:
        return self._predictor.rmse

    @property
    def mae(self) -> Optional[float]:
        return self._predictor.mae

    @property
    def upper_offsets(self) -> np.ndarray:
        return self._predictor.upper_offsets

    @property
    def val_coverage(self) -> float:
        return self._predictor.val_coverage

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict(self, history: List[float], horizon: int = 1) -> Dict[str, Any]:
        """Predict future request counts using the canonical predictor.

        The ``horizon`` parameter is accepted for API compatibility but the
        model always outputs ``config.prediction_horizon`` direct forecasts.
        If ``horizon`` differs from the model's native horizon, the response
        still contains all native-horizon values.
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")

        values = np.array(history, dtype=np.float32)
        result = self._predictor.predict(values)

        # Map to the server-response contract
        point_forecasts = result.get("point_forecasts", [])
        upper_forecasts = result.get("upper_forecasts", [])
        horizon_values = [int(round(p)) for p in point_forecasts]

        return {
            "predicted_requests": int(round(result["predicted_requests"])),
            "confidence": result["confidence"],
            "horizon_values": horizon_values,
            "point_forecasts": [float(f) for f in point_forecasts],
            "upper_forecasts": [float(f) for f in upper_forecasts],
            "model_rmse": result.get("model_rmse"),
        }

    def get_status(self) -> Dict[str, Any]:
        """Get model status information."""
        cfg = self.config
        return {
            "loaded": self.is_loaded,
            "model_type": self.model_type,
            "model_path": str(self.model_path) if self.model_path else None,
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            "sequence_length": cfg.sequence_length if cfg else None,
            "prediction_horizon": cfg.prediction_horizon if cfg else None,
            "sample_interval_sec": cfg.sample_interval_sec if cfg else None,
            "hidden_size": cfg.hidden_size if cfg else None,
            "num_layers": cfg.num_layers if cfg else None,
            "rmse": self.rmse,
            "mae": self.mae,
            "scaler_mean": self.scaler_mean,
            "scaler_std": self.scaler_std,
            "val_coverage": self.val_coverage,
        }
