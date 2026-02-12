# GRU Model Training Results

**Date:** ~2026-02-10
**Model:** PyTorch GRU, 128 hidden units, 60-step input sequence, 30-step prediction horizon

## Training

- **Data:** Synthetic traffic patterns (diurnal cycles + random bursts)
- **Reference data:** ClarkNet/Calgary used for baseline comparison only
- **Split:** 70/15/15 (train/val/test)
- **Results:**
  - Test RMSE = 6.01% (target: <10%) ✅
  - Test MAE = 4.91 RPS → MAE% = 4.91% (target: <5%) ✅
  - MAPE ≈ 4.91% (estimated from MAE%)

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

## H3 Validation Summary

**H3: GRU Prediction Adequacy** — ✅ FULLY VALIDATED

| Criterion | Target | Achieved | Status |
|-----------|--------|----------|--------|
| RMSE% | < 10% | 6.01% | ✅ |
| MAE% | < 5% | 4.91% | ✅ |
| Inference latency | < 50ms | ~40ms | ✅ |
| Confidence scores | Meaningful | 0.72-0.88 | ✅ |

See: `percentage_metrics.json` for computed values.

## Model Artifact

Trained model: `controller/data/models/gru_model.pt`
