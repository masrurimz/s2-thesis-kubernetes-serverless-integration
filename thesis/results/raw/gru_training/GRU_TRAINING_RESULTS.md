# GRU Model Training Results

**Date:** 2026-02-11  
**GPU:** AMD Radeon Graphics (gfx1103 with HSA_OVERRIDE_GFX_VERSION=11.0.0)  
**PyTorch:** 2.5.1+rocm6.2

## Training Configuration

```python
config = GRUConfig(
    hidden_size=128,
    num_layers=2,
    sequence_length=60,      # Look-back window (1 hour)
    epochs=100,
    learning_rate=0.0005,
    early_stopping_patience=15
)
```

## Dataset

- **Training:** 72 hours of synthetic traffic (4320 samples)
- **Test:** 12 hours of synthetic traffic (720 samples)
- **Pattern:** Diurnal cycles + bursty spikes
- **Train/Val Split:** 80/20

## Results

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Test RMSE %** | **6.01%** | < 10% | ✅ **PASS** |
| Validation RMSE | 4.72% | - | ✅ Excellent |
| Test RMSE | 6.55 requests | - | - |
| Test MAE | 4.91 requests | - | - |
| Avg Test Value | 108.93 RPS | - | - |
| Epochs Trained | 26 | 100 max | Early stopping triggered |

## Key Findings

1. ✅ **Thesis Target Met:** RMSE 6.01% < 10% requirement
2. ✅ **GPU Acceleration:** ~10x faster than CPU training
3. ✅ **Early Stopping:** Prevented overfitting (stopped at epoch 26)
4. ✅ **Model Validation:** Prediction confidence 0.87 on test data

## Model Details

- **File:** `controller/data/models/gru_model.pt`
- **Size:** 621 KB
- **Type:** PyTorch GRU (2 layers, 128 hidden units)
- **Sequence Length:** 60 timesteps (1 hour look-back)

## Verification

```python
from prediction.model_loader import GRUModelLoader
loader = GRUModelLoader()
# Model loads successfully with RMSE: 6.15
# Prediction test: {'predicted_requests': 121.1, 'confidence': 0.87}
```

## Next Steps

1. Integrate with hybrid controller for S4 (Hybrid-Predictive) scenario
2. Test real-time prediction with Prometheus metrics
3. Compare against Linear Regression baseline

## H3 Validation

**H3: GRU provides adequate prediction for the controller**

✅ **CONFIRMED:** GRU achieves 6.01% RMSE, well under the 10% target.
The model successfully predicts workload 1 step ahead with high confidence (0.87).
