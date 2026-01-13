# ML Models

Machine learning models for workload prediction.

## Structure

```
ml_models/
├── baselines/
│   ├── naive.py        # Last-value baseline
│   └── moving_avg.py   # Moving average baseline
├── linear_model.py     # Linear regression (from Sprint 2)
└── gru_predictor.py    # GRU neural network (thesis 3.4.1)
```

## Model Comparison (H3)

| Model | Purpose | Complexity |
|-------|---------|------------|
| Naive (last value) | Lower bound baseline | O(1) |
| Moving Average | Simple smoothing | O(window) |
| Linear Regression | Sprint 2 implementation | O(features) |
| GRU | Thesis proposed model | O(seq × hidden²) |

## Target Metrics (Thesis 3.5.1)

- **RMSE**: < 10% of average traffic
- **MAE**: < 5% of average traffic
- **MAPE**: < 15%

## Training Configuration (Thesis 3.4.1)

```python
# GRU Architecture
GRU(
    input_size=features,
    hidden_size=[64, 32],  # 2 layers
    dropout=0.2
)

# Training
optimizer = Adam(lr=0.001)
loss = MSE
batch_size = 32
epochs = 100  # with early stopping
```

## Usage

```python
from ml_models.gru_predictor import GRUPredictor

model = GRUPredictor(sequence_length=60, prediction_horizon=30)
model.train(X_train, y_train)
predictions = model.predict(X_test)
```
