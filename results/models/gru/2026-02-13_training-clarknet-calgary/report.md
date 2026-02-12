# GRU Training on Real HTTP Traces (ClarkNet + Calgary)

**Date:** 2026-02-13
**Model:** PyTorch GRU, 128 hidden units, 2 layers, dropout 0.2
**Previous:** Synthetic training achieved RMSE% 6.01%, MAE% 4.91%

## Motivation

The thesis proposal specifies training on real ClarkNet/Calgary HTTP traces.
Previous GRU training used synthetic data (diurnal cycles + random bursts).
This experiment retrains on real traces to assess real-world prediction accuracy.

## Data

| Dataset | Source | Duration | Resolution | Mean RPS | Samples |
|---------|--------|----------|------------|----------|---------|
| ClarkNet | `data/processed/clarknet_real_rps.parquet` | 7 days | per-second | 3.27/s | 505,966 |
| Calgary | `data/processed/calgary_real_rps.parquet` | 352 days | per-second | 1.20/s | 603,872 |

Raw per-second data was aggregated to 1-min, 5-min, and 10-min buckets (sum of requests per interval).

## Configuration

- Architecture: GRU 128 hidden × 2 layers, dropout 0.2, FC(64→1)
- Learning rate: 0.0005 (Adam)
- Batch size: 32
- Early stopping patience: 25 epochs (max 200)
- Split: 85% train (with internal 80/20 train/val), 15% test (temporal)
- Seed: 42

Sequence lengths tuned per resolution:
- 1-min, 5-min: 60 steps
- 10-min: 36 steps (~6h lookback)

## Results

### ClarkNet

| Resolution | RMSE | RMSE% | MAE | MAE% | MAPE | Test N |
|------------|------|-------|-----|------|------|--------|
| **1-min** | 30.23 | 26.64% | 24.13 | 21.27% | 30.88% | 1,452 |
| **5-min** ★ | 97.83 | **17.78%** | 79.69 | **14.48%** | **18.74%** | 243 |
| **10-min** | 200.81 | 17.92% | 165.94 | 14.81% | 18.99% | 116 |

★ Best configuration by RMSE%

### Calgary

| Resolution | RMSE | RMSE% | MAE | MAE% | MAPE | Test N |
|------------|------|-------|-----|------|------|--------|
| **1-min** (14d) | 1.34 | 292.53% | 0.56 | 123.16% | 72.59% | 2,964 |
| **5-min** (30d) | 11.39 | 112.74% | 8.21 | 81.23% | 181.79% | 1,236 |

Calgary traces are too sparse (mean ~1 RPS/min) for meaningful GRU prediction.
High MAPE is caused by many near-zero and zero-value intervals.

## Comparison with Synthetic Training

| Metric | Synthetic | ClarkNet 5-min (best) | Ratio |
|--------|-----------|----------------------|-------|
| RMSE% | 6.01% | 17.78% | 2.96× |
| MAE% | 4.91% | 14.48% | 2.95× |
| MAPE | ~4.91% | 18.74% | 3.81× |

## Analysis

1. **Performance gap is expected.** Synthetic data has smooth diurnal patterns with controlled noise (σ=5). Real traces exhibit:
   - Non-stationary traffic (train mean 864 vs test mean 574 for 5-min ClarkNet — weekday vs weekend shift)
   - Irregular bursts and idle periods
   - No clean diurnal cycle in Calgary (academic server)

2. **RMSE% targets not met on real data.** The original targets (RMSE <10%, MAE <5%) were calibrated against synthetic data. On real ClarkNet traces, best RMSE% = 17.78%.

3. **GRU still outperforms baselines on real data.** The baseline comparison from the synthetic report shows Moving Average at ~65% MAPE on real data. GRU achieves 18.74% MAPE on ClarkNet 5-min — a substantial improvement.

4. **Calgary is unsuitable for per-minute prediction.** Mean ~1 RPS means most minutes have 0-2 requests — effectively Poisson noise, not a learnable pattern.

5. **Resolution matters.** Coarser aggregation (5-min, 10-min) smooths noise and improves RMSE%, but the improvement plateaus at 5-min → 10-min.

## Impact on H3 Validation

**H3 (GRU Prediction Adequacy):** Partially validated on real data.
- ✅ GRU mechanism works on real traces and outperforms baselines
- ⚠️ Does not meet the <10% RMSE / <5% MAE thresholds on real data
- ✅ Meets thresholds on synthetic data (as previously reported)
- The gap between synthetic and real performance should be acknowledged as a limitation

## Model Artifacts

- Best model (ClarkNet 5-min): `controller/data/models/gru_model_real.pt`
- Training script: `ml_models/train_gru_real.py`
- Raw results: `raw/training_results.json`
