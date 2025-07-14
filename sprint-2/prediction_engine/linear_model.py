#!/usr/bin/env python3
"""
Sprint 2: Linear Regression Model for Load Prediction

This module implements a linear regression model to predict traffic patterns
for intelligent routing decisions in the hybrid k3s-serverless system.
"""

import joblib
import numpy as np
import pandas as pd
import structlog
from datetime import datetime, timedelta
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Optional, Tuple

logger = structlog.get_logger(__name__)


class TrafficPredictor:
    """Linear regression model for traffic pattern prediction."""
    
    def __init__(self, model_path: str = "data/model-artifacts/traffic_model.joblib"):
        """
        Initialize traffic prediction model.
        
        Args:
            model_path: Path to save/load trained model
        """
        self.model_path = Path(model_path)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Model components
        self.model = LinearRegression()
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Model performance metrics
        self.rmse = None
        self.r2_score = None
        self.training_samples = 0
        
        # Prediction parameters
        self.prediction_window = 30  # seconds
        self.feature_window = 300    # 5 minutes of historical features
        
        logger.info("TrafficPredictor initialized", model_path=str(self.model_path))
        
    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare features and targets from historical data.
        
        Args:
            df: DataFrame with historical traffic patterns
            
        Returns:
            Tuple of (features, targets) arrays
        """
        if len(df) < 10:
            raise ValueError("Insufficient data for feature preparation")
            
        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        features = []
        targets = []
        
        # Create sliding window features
        window_size = self.feature_window // 30  # Number of 30-second intervals
        
        for i in range(window_size, len(df)):
            # Historical features (past 5 minutes)
            window_data = df.iloc[i-window_size:i]
            
            feature_vector = [
                # Traffic volume features
                window_data['total_requests'].mean(),
                window_data['total_requests'].std(),
                window_data['total_requests'].iloc[-1],  # Most recent
                
                # Backend distribution features
                window_data['k3s_requests'].mean(),
                window_data['knative_requests'].mean(),
                (window_data['k3s_requests'] / window_data['total_requests']).mean(),
                
                # Performance features
                window_data['avg_response_time'].mean(),
                window_data['error_rate'].mean(),
                
                # Temporal features
                *self._extract_temporal_features(df.iloc[i]['timestamp']),
                
                # Trend features
                self._calculate_trend(window_data['total_requests']),
                self._calculate_trend(window_data['avg_response_time'])
            ]
            
            # Target: next period's total requests
            target = df.iloc[i]['total_requests']
            
            features.append(feature_vector)
            targets.append(target)
            
        features_array = np.array(features)
        targets_array = np.array(targets)
        
        logger.debug("Features prepared", 
                    features_shape=features_array.shape,
                    targets_shape=targets_array.shape)
        
        return features_array, targets_array
        
    def _extract_temporal_features(self, timestamp: int) -> List[float]:
        """
        Extract temporal features from timestamp.
        
        Args:
            timestamp: Unix timestamp
            
        Returns:
            List of temporal feature values
        """
        dt = datetime.fromtimestamp(timestamp)
        
        # Hour of day (normalized)
        hour_norm = dt.hour / 23.0
        
        # Day of week (normalized) 
        day_norm = dt.weekday() / 6.0
        
        # Sinusoidal encoding for cyclical features
        hour_sin = np.sin(2 * np.pi * dt.hour / 24)
        hour_cos = np.cos(2 * np.pi * dt.hour / 24)
        
        return [hour_norm, day_norm, hour_sin, hour_cos]
        
    def _calculate_trend(self, series: pd.Series) -> float:
        """
        Calculate trend direction in time series.
        
        Args:
            series: Time series data
            
        Returns:
            Trend coefficient (-1 to 1)
        """
        if len(series) < 2:
            return 0.0
            
        x = np.arange(len(series))
        coefficients = np.polyfit(x, series.values, 1)
        
        # Normalize trend coefficient
        trend = coefficients[0] / (series.std() + 1e-8)
        return np.clip(trend, -1.0, 1.0)
        
    def train(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Train the linear regression model on historical data.
        
        Args:
            df: DataFrame with historical traffic patterns
            
        Returns:
            Dictionary with training metrics
        """
        try:
            # Prepare features and targets
            X, y = self.prepare_features(df)
            
            if len(X) < 5:
                raise ValueError("Insufficient data for training")
                
            # Split data for validation (80/20)
            split_idx = int(len(X) * 0.8)
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_val_scaled = self.scaler.transform(X_val)
            
            # Train model
            self.model.fit(X_train_scaled, y_train)
            
            # Validate model
            y_pred = self.model.predict(X_val_scaled)
            
            # Calculate metrics
            self.rmse = np.sqrt(mean_squared_error(y_val, y_pred))
            self.r2_score = r2_score(y_val, y_pred)
            self.training_samples = len(X)
            self.is_trained = True
            
            # Calculate RMSE as percentage of mean
            rmse_percent = (self.rmse / np.mean(y_val)) * 100
            
            metrics = {
                'rmse': self.rmse,
                'rmse_percent': rmse_percent,
                'r2_score': self.r2_score,
                'training_samples': self.training_samples,
                'validation_samples': len(X_val)
            }
            
            logger.info("Model training complete", **metrics)
            
            # Save trained model
            self.save_model()
            
            return metrics
            
        except Exception as e:
            logger.error("Model training failed", error=str(e))
            raise
            
    def predict(self, current_data: Dict) -> Dict[str, float]:
        """
        Make prediction for next period traffic.
        
        Args:
            current_data: Current traffic statistics
            
        Returns:
            Dictionary with prediction and confidence metrics
        """
        if not self.is_trained:
            self.load_model()
            
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
            
        try:
            # Create feature vector from current data
            feature_vector = [
                # Current traffic (as historical mean/std/recent)
                current_data.get('total_requests', 1000),
                50,  # Default std
                current_data.get('total_requests', 1000),
                
                # Backend distribution
                current_data.get('k3s_requests', 800),
                current_data.get('knative_requests', 200),
                0.8,  # Default ratio
                
                # Performance
                current_data.get('avg_response_time', 25.0),
                current_data.get('error_rate', 0.0),
                
                # Temporal features
                *self._extract_temporal_features(current_data.get('timestamp', int(time.time()))),
                
                # Default trends
                0.0, 0.0
            ]
            
            # Scale features and predict
            X = np.array([feature_vector])
            X_scaled = self.scaler.transform(X)
            
            prediction = self.model.predict(X_scaled)[0]
            
            # Calculate confidence based on model performance
            confidence = max(0.5, 1.0 - (self.rmse / 1000))  # Simplified confidence
            
            result = {
                'predicted_requests': max(0, prediction),
                'confidence': confidence,
                'model_rmse': self.rmse,
                'model_r2': self.r2_score,
                'prediction_timestamp': current_data.get('timestamp', int(time.time()))
            }
            
            logger.debug("Prediction made", **result)
            return result
            
        except Exception as e:
            logger.error("Prediction failed", error=str(e))
            raise
            
    def save_model(self) -> bool:
        """
        Save trained model to disk.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'is_trained': self.is_trained,
                'rmse': self.rmse,
                'r2_score': self.r2_score,
                'training_samples': self.training_samples,
                'prediction_window': self.prediction_window,
                'feature_window': self.feature_window
            }
            
            joblib.dump(model_data, self.model_path)
            logger.info("Model saved", path=str(self.model_path))
            return True
            
        except Exception as e:
            logger.error("Model save failed", error=str(e))
            return False
            
    def load_model(self) -> bool:
        """
        Load trained model from disk.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if not self.model_path.exists():
                logger.warning("Model file not found", path=str(self.model_path))
                return False
                
            model_data = joblib.load(self.model_path)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.is_trained = model_data['is_trained']
            self.rmse = model_data['rmse']
            self.r2_score = model_data['r2_score']
            self.training_samples = model_data['training_samples']
            
            logger.info("Model loaded", 
                       path=str(self.model_path),
                       rmse=self.rmse,
                       r2_score=self.r2_score)
            return True
            
        except Exception as e:
            logger.error("Model load failed", error=str(e))
            return False
            
    def retrain_if_needed(self, df: pd.DataFrame, max_age_hours: int = 24) -> bool:
        """
        Retrain model if performance degrades or data is stale.
        
        Args:
            df: Current historical data
            max_age_hours: Maximum age before retraining
            
        Returns:
            True if retrained, False if not needed
        """
        should_retrain = False
        
        # Check if model exists and is trained
        if not self.is_trained:
            should_retrain = True
            reason = "Model not trained"
        
        # Check data freshness
        elif len(df) > self.training_samples * 1.5:
            should_retrain = True
            reason = "Significant new data available"
            
        # Check model age (simplified check)
        elif self.rmse and self.rmse > 200:  # RMSE threshold
            should_retrain = True
            reason = "Model performance degraded"
            
        if should_retrain:
            logger.info("Retraining model", reason=reason)
            metrics = self.train(df)
            return True
        else:
            logger.debug("Model retaining not needed")
            return False


# Import time for temporal features
import time


def main():
    """Test the traffic prediction model."""
    from .data_collector import DataCollector
    
    # Initialize components
    collector = DataCollector()
    predictor = TrafficPredictor()
    
    # Get historical data
    df = collector.get_historical_data(hours=1)
    print(f"Training data: {len(df)} points")
    
    if len(df) >= 10:
        # Train model
        metrics = predictor.train(df)
        print(f"Training metrics: {metrics}")
        
        # Make prediction
        current_stats = collector.collect_current_stats()
        if current_stats:
            prediction = predictor.predict(current_stats)
            print(f"Prediction: {prediction}")
    else:
        print("Insufficient data for training")


if __name__ == "__main__":
    main()