#!/usr/bin/env python3
"""
Train linear regression model and validate RMSE.

Target: RMSE < 20% of average traffic (thesis requirement)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from prediction_engine.linear_model import TrafficPredictor


def generate_synthetic_traffic(
    duration_hours: int = 24,
    base_rps: float = 100,
    noise_std: float = 10
) -> pd.DataFrame:
    """
    Generate synthetic traffic data with daily patterns.
    
    Simulates realistic patterns:
    - Daily cycle (peak at noon, low at night)
    - Random noise
    - Occasional spikes
    """
    samples_per_hour = 60  # 1 sample per minute
    total_samples = duration_hours * samples_per_hour
    
    base_time = datetime.now() - timedelta(hours=duration_hours)
    
    data = []
    for i in range(total_samples):
        timestamp = base_time + timedelta(minutes=i)
        hour = timestamp.hour
        minute = timestamp.minute
        
        # Daily pattern: peak at 12:00, low at 3:00
        hour_factor = np.sin((hour - 6) * np.pi / 12) * 0.4 + 1.0
        
        # Add some minute-level variation
        minute_factor = 1.0 + 0.05 * np.sin(minute * np.pi / 30)
        
        # Base traffic with patterns
        requests = base_rps * hour_factor * minute_factor
        
        # Add noise
        requests += np.random.normal(0, noise_std)
        
        # Occasional spike (1% chance)
        if np.random.random() < 0.01:
            requests *= np.random.uniform(1.5, 2.5)
        
        # Ensure positive
        requests = max(10, requests)
        
        data.append({
            'timestamp': int(timestamp.timestamp()),
            'total_requests': int(requests),
            'avg_response_time': 25 + np.random.normal(0, 5),
            'error_rate': 0.01 + np.random.uniform(0, 0.02),
            'k3s_requests': int(requests * 0.8),
            'knative_requests': int(requests * 0.2)
        })
    
    return pd.DataFrame(data)


def validate_model(predictor: TrafficPredictor, test_data: pd.DataFrame) -> dict:
    """
    Validate model against test data.
    
    Returns metrics including RMSE and whether it meets thesis target.
    """
    predictions = []
    actuals = []
    
    for i in range(len(test_data) - 1):
        row = test_data.iloc[i]
        stats = {
            'timestamp': int(row['timestamp']),
            'total_requests': row['total_requests'],
            'avg_response_time': row.get('avg_response_time', 25),
            'k3s_requests': row.get('k3s_requests', int(row['total_requests'] * 0.8)),
            'knative_requests': row.get('knative_requests', int(row['total_requests'] * 0.2))
        }
        
        try:
            result = predictor.predict(stats)
            predictions.append(result['predicted_requests'])
            actuals.append(test_data.iloc[i + 1]['total_requests'])
        except Exception as e:
            print(f"Prediction error at index {i}: {e}")
    
    predictions = np.array(predictions)
    actuals = np.array(actuals)
    
    # Calculate metrics
    rmse = np.sqrt(np.mean((predictions - actuals) ** 2))
    mae = np.mean(np.abs(predictions - actuals))
    mape = np.mean(np.abs((actuals - predictions) / (actuals + 1e-8))) * 100
    avg_traffic = np.mean(actuals)
    rmse_percent = (rmse / avg_traffic) * 100
    
    return {
        'rmse': rmse,
        'mae': mae,
        'mape': mape,
        'avg_traffic': avg_traffic,
        'rmse_percent': rmse_percent,
        'meets_target': rmse_percent < 20,
        'num_predictions': len(predictions)
    }


def main():
    """Train model and validate RMSE."""
    print("=" * 60)
    print("Model Training and RMSE Validation")
    print("=" * 60)
    print()
    
    # Set seed for reproducibility
    np.random.seed(42)
    
    # Generate synthetic training data
    print("[1/4] Generating synthetic traffic data...")
    train_data = generate_synthetic_traffic(duration_hours=48, base_rps=100)
    test_data = generate_synthetic_traffic(duration_hours=6, base_rps=100)
    print(f"  Training samples: {len(train_data)}")
    print(f"  Test samples: {len(test_data)}")
    print()
    
    # Initialize and train model
    print("[2/4] Training linear regression model...")
    model_path = Path(__file__).parent.parent / "data" / "models" / "linear_model.joblib"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    
    predictor = TrafficPredictor(model_path=str(model_path))
    train_metrics = predictor.train(train_data)
    print(f"  Training RMSE: {train_metrics['rmse']:.2f}")
    print(f"  Training RMSE %: {train_metrics['rmse_percent']:.2f}%")
    print(f"  Training R²: {train_metrics['r2_score']:.4f}")
    print(f"  Samples used: {train_metrics['training_samples']}")
    print()
    
    # Validate on test data
    print("[3/4] Validating on test data...")
    val_metrics = validate_model(predictor, test_data)
    print(f"  Test RMSE: {val_metrics['rmse']:.2f}")
    print(f"  Test MAE: {val_metrics['mae']:.2f}")
    print(f"  Test MAPE: {val_metrics['mape']:.2f}%")
    print(f"  Average traffic: {val_metrics['avg_traffic']:.2f} RPS")
    print(f"  RMSE as % of avg: {val_metrics['rmse_percent']:.2f}%")
    print()
    
    # Model already saved by train() method
    print("[4/4] Model saved...")
    print(f"  Model saved to: {model_path}")
    print()
    
    # Summary
    print("=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    print(f"  Target: RMSE < 20% of average traffic")
    print(f"  Actual: RMSE = {val_metrics['rmse_percent']:.2f}% of average traffic")
    print()
    
    if val_metrics['meets_target']:
        print("✓ MODEL MEETS THESIS REQUIREMENT")
        return 0
    else:
        print("✗ MODEL DOES NOT MEET REQUIREMENT")
        print("  Consider: more training data, feature engineering, or different model")
        return 1


if __name__ == "__main__":
    sys.exit(main())
