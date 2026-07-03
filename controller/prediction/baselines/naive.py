#!/usr/bin/env python3
"""
Naive Last-Value Predictor.

Simplest baseline: predict next value = current value.
Used to establish minimum performance threshold.
"""

import numpy as np
from typing import List, Dict


class NaivePredictor:
    """Predicts next value as current value (persistence model)."""
    
    def __init__(self):
        self.name = "Naive Last-Value"
        self.last_value = None
        
    def fit(self, X: np.ndarray, y: np.ndarray) -> "NaivePredictor":
        """Fit is a no-op for naive predictor."""
        if len(y) > 0:
            self.last_value = y[-1]
        return self
        
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict next value as last known value."""
        if self.last_value is None:
            return np.zeros(len(X))
        return np.full(len(X), self.last_value)
    
    def predict_from_series(self, series: np.ndarray) -> np.ndarray:
        """Predict each next value as current value (shift by 1)."""
        predictions = np.zeros(len(series))
        predictions[1:] = series[:-1]
        predictions[0] = series[0]  # No prediction for first point
        return predictions


class SeasonalNaivePredictor:
    """Predicts next value as value from same time period ago."""
    
    def __init__(self, period: int = 60):
        """
        Args:
            period: Seasonal period (e.g., 60 for hourly patterns with minute data)
        """
        self.name = f"Seasonal Naive (period={period})"
        self.period = period
        self.history = None
        
    def fit(self, X: np.ndarray, y: np.ndarray) -> "SeasonalNaivePredictor":
        """Store history for seasonal prediction."""
        self.history = y.copy()
        return self
        
    def predict_from_series(self, series: np.ndarray) -> np.ndarray:
        """Predict each value as value from one period ago."""
        predictions = np.zeros(len(series))
        for i in range(len(series)):
            if i >= self.period:
                predictions[i] = series[i - self.period]
            else:
                predictions[i] = series[0]  # Fallback
        return predictions
