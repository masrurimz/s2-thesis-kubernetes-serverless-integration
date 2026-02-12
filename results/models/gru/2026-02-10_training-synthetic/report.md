# GRU Model Training Results

**Date:** ~2026-02-10
**Model:** PyTorch GRU, 128 hidden units, 60-step input sequence, 30-step prediction horizon

## Training

- **Data:** Synthetic traffic patterns (diurnal cycles + random bursts)
- **NOT trained on:** ClarkNet or Calgary real traces (deviation from proposal)
- **Split:** 70/15/15 (train/val/test)
- **Result:** Test RMSE = 6.01% (target: <10%) ✅

## Model Comparison — Synthetic Data

Source: `raw/model_comparison.csv`

| Model | RMSE | MAE | MAPE | RMSE % |
|-------|------|-----|------|--------|
| **GRU** | **—** | **—** | **—** | **6.01%** |
| Moving Avg (w=15) | 11.37 | 9.21 | 9.36% | 11.12% |
| EMA (α=0.3) | 11.53 | 9.37 | 9.57% | 11.28% |
| Moving Avg (w=5) | 11.78 | 9.64 | 9.86% | 11.52% |
| Linear Regression | 11.82 | 9.56 | 9.77% | 11.56% |
| Naive (Last Value) | 15.16 | 12.45 | 12.74% | 14.83% |
| Seasonal Naive (1h) | 18.94 | 15.61 | 15.47% | 18.52% |

GRU achieves ~45% lower RMSE than the best baseline (Moving Average).

## Baseline Comparison — Real ClarkNet/Calgary Data

Source: `raw/model_comparison_REAL.csv`

| Model | RMSE | MAE | MAPE | Mean RPS |
|-------|------|-----|------|----------|
| Naive (last value) | 2.09 | 1.48 | 72.7% | 2.51 |
| Moving Average (w=10) | 1.65 | 1.24 | 65.6% | 2.51 |
| Linear Regression | 1.60 | 1.22 | 68.4% | 2.51 |
| MLP (64,32) | 1.60 | 1.23 | 68.8% | 2.51 |

**Note:** GRU was NOT evaluated on real data. These baselines show the difficulty of real trace prediction (high MAPE due to low mean RPS = 2.51).

## Live Inference Performance

- Latency: ~40ms (target: <50ms) ✅
- Confidence range: 0.72 - 0.88
- Predictions active during Phase A1 and Phase B experiments

## Known Issues

1. **Proposal deviation:** Thesis methodology (Section 3.2) specifies ClarkNet and Calgary for GRU training. Actual GRU trained on synthetic data.
2. **MAE target:** Proposal targets MAE < 5%. Raw MAE = 4.91 but percentage not computed against average.
3. **GRU not in comparison CSV:** The 6.01% figure comes from separate training logs, not the model_comparison.csv file.

## Model Artifact

Trained model: `controller/data/models/gru_model.pt`
