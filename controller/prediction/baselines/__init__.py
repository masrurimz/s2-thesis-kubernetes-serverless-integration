"""Baseline prediction models for comparison."""
from .naive import NaivePredictor
from .moving_avg import MovingAveragePredictor

__all__ = ["NaivePredictor", "MovingAveragePredictor"]
