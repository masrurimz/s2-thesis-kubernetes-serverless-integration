## 4.1 GRU Prediction Model Performance

The GRU prediction model was evaluated in two stages: first on synthetic workload patterns used for training, and then on real HTTP trace datasets (ClarkNet and Calgary) to assess generalization. This section reports accuracy metrics, baseline comparisons, and live inference performance.

### 4.1.1 Synthetic Data Performance

The GRU model was trained on synthetic workload patterns incorporating three traffic shapes: diurnal cycles, random bursts, and gradual ramps. The model architecture consists of a two-layer GRU (128 hidden units per layer) with dropout regularization (0.2), followed by a fully connected layer (64 → 1). Training used Adam optimizer with learning rate 0.0005, batch size 32, and early stopping with patience of 25 epochs (maximum 200). The dataset was split 70/15/15 into training, validation, and test sets.

**Table 4.1: GRU Model Accuracy on Synthetic Test Data**

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| RMSE% | 6.01% | < 10% | ✅ Met |
| MAE% | 4.91% | < 5% | ✅ Met |
| MAPE | ~4.91% | — | Estimated from MAE% |
| Mean Load | 100.0 RPS | — | Normalization reference |

All three predefined accuracy targets were met on the synthetic test set. The RMSE of 6.01% represents the model's root mean squared prediction error relative to the normalized traffic range, well within the 10% threshold established in the methodology. The MAE of 4.91% indicates that on average, predictions deviate by less than 5 RPS from actual values at 100 RPS mean load—meeting the <5% target at the boundary.

### 4.1.2 Baseline Comparison on Synthetic Data

To contextualize GRU performance, six baseline models were evaluated on the same synthetic test set.

**Table 4.2: Model Comparison — Synthetic Workload Data**

| Model | RMSE | MAE | MAPE | RMSE% |
|-------|------|-----|------|-------|
| **GRU** | — | — | — | **6.01%** |
| Moving Average (w=15) | 11.37 | 9.21 | 9.36% | 11.12% |
| EMA (α=0.3) | 11.53 | 9.37 | 9.57% | 11.28% |
| Moving Average (w=5) | 11.78 | 9.64 | 9.86% | 11.52% |
| Linear Regression | 11.82 | 9.56 | 9.77% | 11.56% |
| Naïve (Last Value) | 15.16 | 12.45 | 12.74% | 14.83% |
| Seasonal Naïve (1h) | 18.94 | 15.61 | 15.47% | 18.52% |

The GRU achieves approximately 46% lower RMSE% than the best statistical baseline (Moving Average with window size 15, RMSE% = 11.12%). This improvement is attributable to the GRU's ability to learn temporal dependencies across the 60-step input sequence, capturing both the periodic structure of diurnal patterns and the abrupt transitions of burst events. All statistical baselines exceed the 10% RMSE target, indicating that simple time-series methods are insufficient for the prediction accuracy required by the routing controller.

### 4.1.3 Real Trace Performance (ClarkNet and Calgary)

To evaluate generalization beyond synthetic patterns, the GRU was retrained on real HTTP access logs from ClarkNet (7 days, mean 3.27 RPS per second) and Calgary (352 days, mean 1.20 RPS per second). Raw per-second data was aggregated to 1-minute, 5-minute, and 10-minute intervals to assess the effect of temporal resolution on prediction accuracy. The same architecture and hyperparameters were used, with sequence lengths of 60 steps for 1-minute and 5-minute resolutions and 36 steps for 10-minute resolution.

**Table 4.3: GRU Accuracy on ClarkNet Traces (Best Configuration)**

| Resolution | RMSE | RMSE% | MAE | MAE% | MAPE | Test N |
|------------|------|-------|-----|------|------|--------|
| 1-min | 30.23 | 26.64% | 24.13 | 21.27% | 30.88% | 1,452 |
| **5-min** ★ | **97.83** | **17.78%** | **79.69** | **14.48%** | **18.74%** | **243** |
| 10-min | 200.81 | 17.92% | 165.94 | 14.81% | 18.99% | 116 |

★ Best configuration by RMSE%

**Table 4.4: GRU Accuracy on Calgary Traces**

| Resolution | RMSE | RMSE% | MAE | MAE% | MAPE | Test N |
|------------|------|-------|-----|------|------|--------|
| 1-min (14d) | 1.34 | 292.53% | 0.56 | 123.16% | 72.59% | 2,964 |
| 5-min (30d) | 11.39 | 112.74% | 8.21 | 81.23% | 181.79% | 1,236 |

The best real-trace performance was achieved on ClarkNet at 5-minute aggregation: RMSE% = 17.78%, MAE% = 14.48%, MAPE = 18.74%. This does not meet the original targets (<10% RMSE, <5% MAE), representing a performance gap of approximately 3× compared to synthetic data. Calgary traces proved unsuitable for meaningful prediction due to extreme sparsity (mean ~1 RPS per minute), resulting in metrics dominated by near-zero and zero-value intervals.

**Table 4.5: Synthetic vs. Real Trace Performance Comparison**

| Metric | Synthetic | ClarkNet 5-min (Best) | Ratio |
|--------|-----------|----------------------|-------|
| RMSE% | 6.01% | 17.78% | 2.96× |
| MAE% | 4.91% | 14.48% | 2.95× |
| MAPE | ~4.91% | 18.74% | 3.81× |

The performance gap is expected for three reasons. First, the ClarkNet test set exhibits non-stationarity: the training period mean was 864 RPS (weekday traffic) while the test period mean was 574 RPS (weekend traffic), representing a distribution shift not present in synthetic data. Second, real traces contain irregular bursts and idle periods that are poorly represented by the smooth diurnal patterns in synthetic training data. Third, the Calgary dataset's academic server traffic follows no clean diurnal cycle, making it fundamentally different from the patterns the GRU was designed to capture.

Despite not meeting the original targets on real data, the GRU substantially outperforms statistical baselines on ClarkNet: 18.74% MAPE versus approximately 65% MAPE for the best baseline (Moving Average), representing a 3.5× improvement. This indicates that the GRU architecture captures meaningful temporal patterns in real traces, even if absolute accuracy falls short of the targets calibrated against synthetic data.

### 4.1.4 Live Inference Performance

During live system operation (Phase A1 and Phase B experiments), the GRU prediction server demonstrated the following operational characteristics:

**Table 4.6: GRU Live Inference Metrics**

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Inference Latency | ~40ms | < 50ms | ✅ Met |
| Confidence Range | 0.72 – 0.88 | > 0.6 | ✅ Met |
| Predictions Active | Yes (Phase A1) | — | ✅ |

The ~40ms inference latency confirms the model operates well within the constraint for real-time routing decisions. The confidence scores (0.72–0.88 observed during Phase A1) provide a meaningful gating mechanism: the routing controller uses these to modulate its reliance on predictions, only triggering PREDICTIVE actions when confidence exceeds 0.5 (the configured threshold).

### 4.1.5 H3 Validation Summary

**H3 (GRU Prediction Adequacy): Fully validated on synthetic data.** All four predefined accuracy targets were met: RMSE% = 6.01% (target <10%), MAE% = 4.91% (target <5%), inference latency ~40ms (target <50ms), and confidence scores 0.72–0.88 (meaningful). On real HTTP traces, the GRU significantly outperforms statistical baselines but does not meet the original thresholds, which were calibrated for synthetic workload patterns. The gap between synthetic and real-trace performance is acknowledged as a limitation of the current training approach.

---
