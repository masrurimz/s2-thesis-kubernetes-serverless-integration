#!/usr/bin/env python3
"""
Moving Average Predictor.

Simple baseline: predict next value as average of last N values.
"""

import numpy as np
from typing import Optional


class MovingAveragePredictor:
    """Predicts next value as moving average of recent values."""
    
    def __init__(self, window_size: int = 5):
        """
        Args:
            window_size: Number of past values to average
        """
        self.name = f"Moving Average (window={window_size})"
        self.window_size = window_size
        self.history = []
        
    def fit(self, X: np.ndarray, y: np.ndarray) -> "MovingAveragePredictor":
        """Store recent history for MA calculation."""
        self.history = list(y[-self.window_size:])
        return self
        
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict as average of stored history."""
        if not self.history:
            return np.zeros(len(X))
        return np.full(len(X), np.mean(self.history))
    
    def predict_from_series(self, series: np.ndarray) -> np.ndarray:
        """Predict each value as MA of previous window."""
        predictions = np.zeros(len(series))
        
        for i in range(len(series)):
            if i < self.window_size:
                predictions[i] = np.mean(series[:max(1, i)])
            else:
                predictions[i] = np.mean(series[i-self.window_size:i])
                
        return predictions


class ExponentialMovingAveragePredictor:
    """Predicts next value as exponential moving average."""
    
    def __init__(self, alpha: float = 0.3):
        """
        Args:
            alpha: Smoothing factor (0-1). Higher = more weight on recent values.
        """
        self.name = f"EMA (alpha={alpha})"
        self.alpha = alpha
        self.ema = None
        
    def fit(self, X: np.ndarray, y: np.ndarray) -> "ExponentialMovingAveragePredictor":
        """Calculate initial EMA from training data."""
        if len(y) == 0:
            self.ema = 0
            return self
            
        self.ema = y[0]
        for val in y[1:]:
            self.ema = self.alpha * val + (1 - self.alpha) * self.ema
        return self
        
    def predict_from_series(self, series: np.ndarray) -> np.ndarray:
        """Predict each value as EMA of previous values."""
        predictions = np.zeros(len(series))
        ema = series[0]
        
        for i in range(len(series)):
            predictions[i] = ema
            ema = self.alpha * series[i] + (1 - self.alpha) * ema
                
        return predictions
