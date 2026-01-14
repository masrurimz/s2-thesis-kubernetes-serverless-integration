# Model Training Results

## Linear Regression Model

**Training Date**: 2026-01-14
**Dataset**: Synthetic traffic (48 hours training, 6 hours test)
**Model File**: `linear_model.joblib`

### Performance Metrics

| Metric | Training | Test | Target |
|--------|----------|------|--------|
| RMSE | 12.25 | 16.26 | - |
| RMSE % of avg | 12.25% | **15.83%** | < 20% |
| MAE | - | 11.05 | - |
| MAPE | - | 10.39% | < 15% |
| R² | 0.7821 | - | > 0.7 |

### Thesis Requirement

| Requirement | Target | Actual | Status |
|-------------|--------|--------|--------|
| RMSE < 20% of average traffic | < 20% | 15.83% | ✅ PASS |

### Model Details

- **Algorithm**: Linear Regression (sklearn)
- **Features**: 14 (traffic volume, backend distribution, performance, temporal, trend)
- **Feature Window**: 5 minutes (10 samples @ 30s intervals)
- **Prediction Window**: 30 seconds ahead

### Feature Engineering

1. **Traffic Volume Features**:
   - Mean/std/recent total requests
   
2. **Backend Distribution**:
   - K3s/Knative request means
   - K3s ratio

3. **Performance Features**:
   - Average response time
   - Error rate

4. **Temporal Features**:
   - Hour normalized
   - Day of week normalized
   - Sinusoidal hour encoding (sin/cos)

5. **Trend Features**:
   - Traffic trend coefficient
   - Response time trend coefficient

### Reproducing Results

```bash
cd controller
uv run python scripts/train_and_validate_model.py
```

### Running Tests

```bash
cd controller
uv run python -m pytest tests/test_model_training.py -v
```
