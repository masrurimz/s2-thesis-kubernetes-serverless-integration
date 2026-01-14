"""
GRU Prediction Service Package.

Provides HTTP API for workload prediction using trained GRU models.
"""

__version__ = "1.0.0"

from .model_loader import GRUModelLoader
from .prediction_server import app

__all__ = ["GRUModelLoader", "app"]
