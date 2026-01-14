#!/usr/bin/env python3
"""
GRU Model Loader.

Handles loading PyTorch GRU models and making predictions.
Supports both PyTorch (.pt) and sklearn fallback (.joblib) formats.
"""

import sys
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

import numpy as np
import structlog

logger = structlog.get_logger(__name__)

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available")


@dataclass
class GRUConfig:
    """GRU model configuration."""
    input_size: int = 1
    hidden_size: int = 64
    num_layers: int = 2
    dropout: float = 0.2
    sequence_length: int = 30
    prediction_horizon: int = 1
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 100
    early_stopping_patience: int = 10


if TORCH_AVAILABLE:
    class GRUNetwork(nn.Module):
        """GRU neural network for time series prediction."""
        
        def __init__(self, config: GRUConfig):
            super().__init__()
            self.config = config
            
            self.gru = nn.GRU(
                input_size=config.input_size,
                hidden_size=config.hidden_size,
                num_layers=config.num_layers,
                dropout=config.dropout if config.num_layers > 1 else 0,
                batch_first=True
            )
            
            self.fc = nn.Sequential(
                nn.Linear(config.hidden_size, config.hidden_size // 2),
                nn.ReLU(),
                nn.Dropout(config.dropout),
                nn.Linear(config.hidden_size // 2, 1)
            )
        
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            gru_out, _ = self.gru(x)
            last_hidden = gru_out[:, -1, :]
            output = self.fc(last_hidden)
            return output.squeeze(-1)


class GRUModelLoader:
    """
    Loads and manages GRU prediction models.
    
    Supports loading from PyTorch checkpoint or sklearn joblib format.
    """
    
    DEFAULT_MODEL_PATHS = [
        Path("data/models/gru_model.pt"),
        Path("controller/data/models/gru_model.pt"),
        Path(__file__).parent.parent / "data/models/gru_model.pt",
    ]
    
    def __init__(self, model_path: Optional[Path] = None):
        self.model = None
        self.config: Optional[GRUConfig] = None
        self.scaler_mean: float = 0.0
        self.scaler_std: float = 1.0
        self.rmse: Optional[float] = None
        self.mae: Optional[float] = None
        self.is_loaded: bool = False
        self.model_path: Optional[Path] = None
        self.model_type: str = "unknown"
        
        if TORCH_AVAILABLE:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = None
        
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
        """
        Load model from file.
        
        Args:
            path: Path to model file (.pt for PyTorch, .joblib for sklearn)
            
        Returns:
            True if loading succeeded
        """
        path = Path(path)
        if not path.exists():
            logger.error("Model file not found", path=str(path))
            return False
        
        try:
            if TORCH_AVAILABLE and str(path).endswith('.pt'):
                return self._load_pytorch(path)
            else:
                return self._load_sklearn(path)
        except Exception as e:
            logger.error("Failed to load model", path=str(path), error=str(e))
            return False
    
    def _load_pytorch(self, path: Path) -> bool:
        """Load PyTorch model."""
        import torch
        
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        metadata = checkpoint['metadata']
        
        self.config = GRUConfig(**metadata['config'])
        self.model = GRUNetwork(self.config).to(self.device)
        self.model.load_state_dict(checkpoint['model_state'])
        self.model.eval()
        
        self.scaler_mean = metadata['scaler_mean']
        self.scaler_std = metadata['scaler_std']
        self.rmse = metadata.get('rmse')
        self.mae = metadata.get('mae')
        self.is_loaded = True
        self.model_path = path
        self.model_type = "pytorch"
        
        logger.info("PyTorch model loaded", 
                   path=str(path),
                   hidden_size=self.config.hidden_size,
                   sequence_length=self.config.sequence_length)
        return True
    
    def _load_sklearn(self, path: Path) -> bool:
        """Load sklearn model (fallback)."""
        import joblib
        
        data = joblib.load(path)
        metadata = data['metadata']
        
        self.config = GRUConfig(**metadata['config'])
        self.model = data['model']
        self.scaler_mean = metadata['scaler_mean']
        self.scaler_std = metadata['scaler_std']
        self.rmse = metadata.get('rmse')
        self.mae = metadata.get('mae')
        self.is_loaded = True
        self.model_path = path
        self.model_type = "sklearn"
        
        logger.info("sklearn model loaded", path=str(path))
        return True
    
    def _normalize(self, data: np.ndarray) -> np.ndarray:
        """Normalize data using stored statistics."""
        return (data - self.scaler_mean) / (self.scaler_std + 1e-8)
    
    def _denormalize(self, data: np.ndarray) -> np.ndarray:
        """Denormalize data using stored statistics."""
        return data * self.scaler_std + self.scaler_mean
    
    def predict(self, history: List[float], horizon: int = 1) -> dict:
        """
        Predict future request counts.
        
        Args:
            history: List of recent request counts
            horizon: Number of steps ahead to predict
            
        Returns:
            Dictionary with predictions and confidence
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")
        
        if len(history) < self.config.sequence_length:
            padding_size = self.config.sequence_length - len(history)
            padding = [self.scaler_mean] * padding_size
            history = padding + list(history)
        
        values = np.array(history[-self.config.sequence_length:], dtype=np.float32)
        normalized = self._normalize(values)
        
        predictions = []
        current_seq = normalized.copy()
        
        for _ in range(horizon):
            if TORCH_AVAILABLE and isinstance(self.model, nn.Module):
                self.model.eval()
                with torch.no_grad():
                    X = torch.FloatTensor(current_seq).reshape(1, -1, 1).to(self.device)
                    pred_norm = self.model(X).cpu().numpy()[0]
            else:
                X = current_seq.reshape(1, -1)
                pred_norm = self.model.predict(X)[0]
            
            pred_denorm = float(self._denormalize(pred_norm))
            predictions.append(max(0, pred_denorm))
            
            current_seq = np.roll(current_seq, -1)
            current_seq[-1] = pred_norm
        
        avg_prediction = np.mean(predictions)
        confidence = self._calculate_confidence(history, predictions)
        
        return {
            "predicted_requests": predictions[-1] if horizon == 1 else int(avg_prediction),
            "confidence": confidence,
            "horizon_values": [int(p) for p in predictions],
            "model_rmse": self.rmse,
        }
    
    def _calculate_confidence(self, history: List[float], predictions: List[float]) -> float:
        """Calculate prediction confidence based on model performance and input stability."""
        base_confidence = 0.7
        
        if self.rmse and self.scaler_mean > 0:
            rmse_ratio = self.rmse / self.scaler_mean
            if rmse_ratio < 0.1:
                base_confidence = 0.9
            elif rmse_ratio < 0.15:
                base_confidence = 0.8
            elif rmse_ratio < 0.2:
                base_confidence = 0.7
            else:
                base_confidence = 0.6
        
        if len(history) >= 5:
            recent_std = np.std(history[-5:])
            recent_mean = np.mean(history[-5:])
            if recent_mean > 0:
                cv = recent_std / recent_mean
                stability_factor = max(0.8, 1.0 - cv)
                base_confidence *= stability_factor
        
        return round(min(0.95, max(0.5, base_confidence)), 2)
    
    def get_status(self) -> dict:
        """Get model status information."""
        return {
            "loaded": self.is_loaded,
            "model_type": self.model_type,
            "model_path": str(self.model_path) if self.model_path else None,
            "sequence_length": self.config.sequence_length if self.config else None,
            "hidden_size": self.config.hidden_size if self.config else None,
            "rmse": self.rmse,
            "mae": self.mae,
            "scaler_mean": self.scaler_mean,
            "scaler_std": self.scaler_std,
        }
