"""
Sprint 2: Prediction Engine Package

Linear regression-based traffic prediction for intelligent hybrid routing.
Provides data collection, model training, and real-time prediction API.
"""

__version__ = "2.0.0"

from .data_collector import DataCollector
from .linear_model import TrafficPredictor
from .prediction_server import app

__all__ = ["DataCollector", "TrafficPredictor", "app"]