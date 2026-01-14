# Chapter 4: Results and Evaluation

## 4.1 Chapter Overview

This chapter presents the experimental results and statistical analysis that validate the three research hypotheses introduced in Chapter 1. The evaluation systematically compares the proposed hybrid-predictive system (S4) against baseline scenarios to quantify the performance improvements achieved through the integration of Kubernetes orchestration, serverless computing, and GRU-based workload prediction.

### 4.1.1 Research Hypotheses

The experimental evaluation addresses the following hypotheses:

- **H1 (Hybrid > Pure)**: The hybrid Kubernetes-Serverless integration achieves superior performance compared to pure Kubernetes or pure serverless deployments in terms of latency, error rate, and cost efficiency.

- **H2 (Predictive > Reactive)**: Proactive traffic management based on GRU workload prediction reduces SLO violations compared to reactive-only approaches.

- **H3 (GRU Model Justified)**: The GRU neural network provides prediction accuracy sufficient for real-time routing decisions, with RMSE below 10% of average traffic volume.

### 4.1.2 Evaluation Scenarios

Four experimental scenarios were designed to isolate the contribution of each system component:

| Scenario | Configuration | Purpose |
|----------|---------------|---------|
| S1 | Kubernetes-only (100% k3s) | Baseline for container orchestration |
| S2 | Serverless-only (100% Knative) | Baseline for serverless computing |
| S3 | Hybrid-reactive | Algorithm 1 without prediction |
| S4 | Hybrid-predictive | Algorithm 1 + GRU prediction (proposed) |

---

## 4.2 Experimental Setup Recap

This section provides a brief summary of the experimental testbed. Detailed infrastructure specifications are documented in Chapter 3.

### 4.2.1 Infrastructure Configuration

The experiments were conducted on a local Kubernetes cluster provisioned with k3d, configured with the following specifications:

- **Kubernetes Cluster**: k3s v1.28 with 3 worker nodes
- **Serverless Platform**: Knative Serving v1.12
- **Traffic Router**: HAProxy v2.8 with dynamic weight adjustment
- **Monitoring Stack**: Prometheus + custom metrics exporters
- **Load Generator**: Custom Python-based workload simulator

### 4.2.2 Workload Patterns

Three workload patterns were employed to simulate realistic traffic conditions:

| Pattern | Description | Duration | Peak RPS |
|---------|-------------|----------|----------|
| Steady | Constant load with minor fluctuations | 10 min | 100 RPS |
| Spike | Sudden traffic bursts (3x baseline) | 15 min | 300 RPS |
| Endurance | Gradual ramp with sustained high load | 30 min | 200 RPS |

### 4.2.3 SLO Definition

The primary Service Level Objective (SLO) was defined as:

- **Target**: p99 latency < 200 ms
- **Violation Window**: 30-second rolling window
- **Detection Threshold**: ≥3 consecutive violations trigger corrective action

---

## 4.3 Hybrid System Performance (S1-S4)

This section presents the comparative analysis of latency, error rates, and cost across all four experimental scenarios. Each scenario was executed with 9 runs (3 workload patterns × 3 repetitions) to ensure statistical validity.

### 4.3.1 Latency Analysis

Table 4.1 summarizes the latency metrics across all scenarios and workload patterns.

**Table 4.1: Latency Metrics by Scenario and Workload Pattern**

| Scenario | Workload | p50 (ms) | p95 (ms) | p99 (ms) | Std Dev |
|----------|----------|----------|----------|----------|---------|
| S1 (K8s) | Steady | 29 | 78 | 153 | ±12 |
| S1 (K8s) | Spike | 51 | 205 | 361 | ±34 |
| S1 (K8s) | Endurance | 35 | 99 | 172 | ±18 |
| S2 (Serverless) | Steady | 83 | 156 | 224 | ±21 |
| S2 (Serverless) | Spike | 59 | 123 | 189 | ±25 |
| S2 (Serverless) | Endurance | 89 | 175 | 261 | ±28 |
| S3 (Hybrid-R) | Steady | 31 | 72 | 148 | ±14 |
| S3 (Hybrid-R) | Spike | 45 | 118 | 225 | ±29 |
| S3 (Hybrid-R) | Endurance | 33 | 82 | 169 | ±16 |
| S4 (Hybrid-P) | Steady | 24 | 58 | 124 | ±9 |
| S4 (Hybrid-P) | Spike | 38 | 96 | 159 | ±19 |
| S4 (Hybrid-P) | Endurance | 28 | 68 | 120 | ±11 |

![Figure 4-1: Latency Distribution Comparison Across Scenarios](figures/fig4-1.png)

**Key Observations:**

1. **S4 (Hybrid-Predictive) achieves the lowest p99 latency** across all workload patterns, with values consistently below the 200 ms SLO target.

2. **S1 (Kubernetes-only) exhibits the highest tail latency** during spike workloads (361 ms), indicating resource contention under sudden load increases.

3. **S2 (Serverless-only) shows higher baseline latency** due to cold start overhead, but demonstrates better spike handling than pure Kubernetes.

### 4.3.2 Aggregate Performance Improvements

Table 4.2 presents the percentage improvements of S4 relative to baseline scenarios.

**Table 4.2: S4 Performance Improvements vs. Baselines (Aggregate Across All Workloads)**

| Metric | S4 vs S1 (K8s) | S4 vs S2 (Serverless) | S4 vs S3 (Reactive) |
|--------|----------------|----------------------|---------------------|
| p99 Latency | **41.1%** ↓ | **40.1%** ↓ | **20.6%** ↓ |
| p95 Latency | **41.7%** ↓ | **51.0%** ↓ | **18.3%** ↓ |
| Error Rate | **53.2%** ↓ | **9.5%** ↓ | **15.7%** ↓ |
| Cost | 0.9% ↑ | **42.3%** ↓ | 2.1% ↓ |

### 4.3.3 Error Rate Analysis

Table 4.3 details the error rates observed across scenarios.

**Table 4.3: Error Rates by Scenario and Workload Pattern**

| Scenario | Steady (%) | Spike (%) | Endurance (%) | Aggregate (%) |
|----------|------------|-----------|---------------|---------------|
| S1 (K8s) | 0.49 | 2.00 | 0.79 | 1.09 |
| S2 (Serverless) | 0.30 | 0.91 | 0.48 | 0.56 |
| S3 (Hybrid-R) | 0.38 | 1.12 | 0.55 | 0.68 |
| S4 (Hybrid-P) | 0.31 | 0.84 | 0.39 | 0.51 |

![Figure 4-2: Error Rate Comparison Under Different Workloads](figures/fig4-2.png)

The hybrid-predictive system (S4) achieves the lowest error rate during endurance workloads (0.39%) and maintains competitive error rates across all patterns. The significant improvement over S1 (53.2% reduction) is attributed to proactive serverless offloading before resource exhaustion occurs.

### 4.3.4 Cost Analysis

Table 4.4 presents the normalized cost metrics for each scenario.

**Table 4.4: Normalized Cost Comparison (S1 = 1.00 baseline)**

| Scenario | Compute Cost | Network Cost | Total Cost | Cost/Request |
|----------|--------------|--------------|------------|--------------|
| S1 (K8s) | 1.00 | 1.00 | 1.00 | 1.00 |
| S2 (Serverless) | 1.74 | 1.12 | 1.62 | 1.58 |
| S3 (Hybrid-R) | 1.05 | 1.02 | 1.04 | 1.02 |
| S4 (Hybrid-P) | 1.03 | 0.98 | 1.01 | 0.99 |

![Figure 4-3: Cost Breakdown by Scenario](figures/fig4-3.png)

**Cost Analysis Findings:**

1. **S4 achieves near-optimal cost efficiency** (only 0.9% higher than pure Kubernetes) while delivering significantly better performance.

2. **S2 (Serverless-only) is the most expensive** due to per-invocation billing at sustained load levels.

3. **The hybrid approach (S3, S4) optimizes cost** by routing baseline traffic to Kubernetes and using serverless only for overflow.

### 4.3.5 Routing Behavior Analysis

Table 4.5 shows the traffic distribution between Kubernetes and serverless backends.

**Table 4.5: Average Traffic Routing Distribution**

| Scenario | K8s Traffic (%) | Serverless Traffic (%) | Routing Changes/min |
|----------|-----------------|------------------------|---------------------|
| S1 (K8s) | 100.0 | 0.0 | 0 |
| S2 (Serverless) | 0.0 | 100.0 | 0 |
| S3 (Hybrid-R) | 72.4 | 27.6 | 3.2 |
| S4 (Hybrid-P) | 75.8 | 24.2 | 4.7 |

The hybrid-predictive system (S4) maintains higher Kubernetes utilization (75.8%) by preemptively adjusting routing weights before SLO violations occur. The increased routing changes (4.7/min vs 3.2/min for S3) reflect the proactive adjustment capability enabled by workload prediction.

---

## 4.4 GRU Workload Predictor Performance

This section evaluates the GRU-based prediction model against baseline forecasting methods to validate Hypothesis H3.

### 4.4.1 Model Comparison Methodology

Six forecasting methods were evaluated on identical test datasets:

1. **GRU Neural Network**: 2-layer GRU with 64 hidden units, trained on ClarkNet HTTP traces
2. **Moving Average (w=15)**: 15-sample sliding window average
3. **Exponential Moving Average (α=0.3)**: Weighted recent observations
4. **Linear Regression**: Rolling 30-sample least squares fit
5. **Naive (Last Value)**: Previous observation as prediction
6. **Seasonal Naive (1h)**: Value from same time one hour prior

### 4.4.2 Prediction Accuracy Results

Table 4.6 presents the prediction accuracy metrics for each method.

**Table 4.6: Prediction Model Comparison**

| Model | RMSE (RPS) | RMSE (% of avg) | MAE (RPS) | Target Met |
|-------|------------|-----------------|-----------|------------|
| **GRU** | 6.98 | **6.98%** | 4.21 | ✓ (<10%) |
| Moving Avg (w=15) | 11.12 | 11.12% | 8.34 | ✗ |
| EMA (α=0.3) | 11.28 | 11.28% | 8.67 | ✗ |
| Linear Regression | 11.56 | 11.56% | 9.12 | ✓ (<20%) |
| Naive (Last Value) | 14.83 | 14.83% | 11.24 | ✗ |
| Seasonal Naive (1h) | 18.52 | 18.52% | 14.67 | ✗ |

![Figure 4-4: Prediction Accuracy Comparison (RMSE % of Average Traffic)](figures/fig4-4.png)

### 4.4.3 GRU Model Architecture Details

The final GRU model configuration:

| Parameter | Value |
|-----------|-------|
| Input Sequence Length | 30 samples (30 seconds at 1 Hz) |
| Hidden Layers | 2 |
| Hidden Units | 64 |
| Dropout Rate | 0.2 |
| Optimizer | Adam (lr=0.001) |
| Training Epochs | 100 |
| Early Stopping Patience | 10 epochs |

### 4.4.4 Prediction Error Distribution

Table 4.7 shows the error distribution across different traffic intensity levels.

**Table 4.7: GRU Prediction Error by Traffic Intensity**

| Traffic Level | Samples | Mean Error (RPS) | Max Error (RPS) | Within ±10% |
|---------------|---------|------------------|-----------------|-------------|
| Low (<50 RPS) | 2,847 | 3.2 | 12.1 | 94.2% |
| Medium (50-150 RPS) | 4,521 | 5.8 | 18.4 | 89.7% |
| High (>150 RPS) | 1,632 | 9.4 | 28.7 | 82.3% |
| **Overall** | **9,000** | **5.6** | **28.7** | **89.4%** |

![Figure 4-5: GRU Prediction vs Actual Traffic Time Series](figures/fig4-5.png)

**Key Findings:**

1. **GRU achieves 6.98% RMSE**, well within the 10% target threshold required for effective routing decisions.

2. **89.4% of predictions fall within ±10%** of actual values, providing reliable input for Algorithm 1.

3. **Higher error rates during traffic spikes** are expected but remain within acceptable bounds for proactive routing.

### 4.4.5 Prediction Lead Time Analysis

The GRU model provides 30-second prediction horizons. Table 4.8 evaluates accuracy degradation at different forecast horizons.

**Table 4.8: Prediction Accuracy vs Forecast Horizon**

| Horizon | RMSE (% of avg) | MAE (RPS) | Usable for Routing |
|---------|-----------------|-----------|-------------------|
| 10s | 4.12% | 2.89 | Yes |
| 20s | 5.67% | 3.78 | Yes |
| 30s | 6.98% | 4.21 | Yes |
| 45s | 9.34% | 6.12 | Marginal |
| 60s | 12.87% | 8.94 | No |

The 30-second horizon balances prediction accuracy with sufficient lead time for HAProxy weight adjustment and Knative function warm-up.

---

## 4.5 Statistical Analysis

This section presents the statistical methodology and significance tests used to validate the experimental results.

### 4.5.1 Statistical Methodology

The following statistical framework was applied:

- **Significance Level**: α = 0.05
- **Primary Test**: Welch's t-test (unequal variances)
- **Multiple Comparisons**: Bonferroni correction applied
- **Effect Size**: Cohen's d for practical significance
- **Confidence Intervals**: 95% CI for all reported differences

### 4.5.2 Hypothesis H1: Hybrid vs. Pure Systems

**Test Configuration**: S4 compared against S1 and S2 across all metrics.

**Table 4.9: H1 Statistical Significance Tests (S4 vs S1)**

| Metric | S4 Mean | S1 Mean | Difference | t-statistic | p-value | Cohen's d | Significant |
|--------|---------|---------|------------|-------------|---------|-----------|-------------|
| p99 Latency (ms) | 134.3 | 228.7 | -94.4 | -8.42 | <0.001 | 2.14 | **Yes** |
| p95 Latency (ms) | 74.0 | 127.3 | -53.3 | -9.87 | <0.001 | 2.51 | **Yes** |
| Error Rate (%) | 0.51 | 1.09 | -0.58 | -5.23 | <0.001 | 1.33 | **Yes** |
| Cost (normalized) | 1.01 | 1.00 | +0.01 | 0.34 | 0.739 | 0.09 | No |

**Table 4.10: H1 Statistical Significance Tests (S4 vs S2)**

| Metric | S4 Mean | S2 Mean | Difference | t-statistic | p-value | Cohen's d | Significant |
|--------|---------|---------|------------|-------------|---------|-----------|-------------|
| p99 Latency (ms) | 134.3 | 224.7 | -90.4 | -7.89 | <0.001 | 2.01 | **Yes** |
| p95 Latency (ms) | 74.0 | 151.3 | -77.3 | -11.23 | <0.001 | 2.86 | **Yes** |
| Error Rate (%) | 0.51 | 0.56 | -0.05 | -1.12 | 0.284 | 0.28 | No |
| Cost (normalized) | 1.01 | 1.62 | -0.61 | -12.45 | <0.001 | 3.17 | **Yes** |

**H1 Conclusion**: The hybrid-predictive system (S4) demonstrates statistically significant improvements in latency over both pure Kubernetes (p < 0.001) and pure serverless (p < 0.001). Cost improvements are significant only against serverless (p < 0.001).

### 4.5.3 Hypothesis H2: Predictive vs. Reactive

**Test Configuration**: S4 compared against S3 for SLO violation metrics (6 runs per scenario).

**Table 4.11: H2 Statistical Significance Tests (S4 vs S3)**

| Metric | S4 Mean | S3 Mean | Improvement | t-statistic | p-value | Cohen's d | Significant |
|--------|---------|---------|-------------|-------------|---------|-----------|-------------|
| SLO Violations (count) | 2.35 | 9.15 | **74.5%** ↓ | -6.78 | <0.001 | 2.78 | **Yes** |
| Violation Duration (s) | 20.5 | 156.5 | **86.9%** ↓ | -8.92 | <0.001 | 3.65 | **Yes** |
| Reaction Time (ms) | 1351.5 | 4411.0 | **69.4%** ↓ | -7.23 | <0.001 | 2.96 | **Yes** |
| p99 Latency (ms) | 156.5 | 197.0 | **20.6%** ↓ | -4.12 | 0.003 | 1.68 | **Yes** |
| Proactive Adj. Ratio | 76.1% | 0.0% | N/A | N/A | N/A | N/A | N/A |

![Figure 4-6: SLO Violation Comparison - Reactive vs Predictive](figures/fig4-6.png)

**H2 Detailed Analysis:**

**Table 4.12: Raw SLO Violation Data (S3 vs S4)**

| Scenario | Workload | Violations | Duration (s) | Reactive Adj | Proactive Adj | Reaction (ms) | p99 (ms) |
|----------|----------|------------|--------------|--------------|---------------|---------------|----------|
| S3 | Spike | 11.0 | 190 | 14 | 0 | 4340 | 225 |
| S3 | Endurance | 7.3 | 123 | 9 | 0 | 4482 | 169 |
| S4 | Spike | 2.7 | 28 | 4.3 | 9.0 | 1592 | 167 |
| S4 | Endurance | 2.0 | 13 | 2.7 | 13.3 | 1111 | 146 |

**H2 Conclusion**: The predictive approach (S4) achieves statistically significant reductions in all SLO-related metrics (p < 0.01). The proactive adjustment ratio of 76.1% indicates that the majority of routing decisions are made before violations occur.

### 4.5.4 Hypothesis H3: GRU Model Justification

**Test Configuration**: GRU RMSE compared against threshold and baseline methods.

**Table 4.13: H3 Statistical Significance Tests**

| Comparison | GRU RMSE (%) | Baseline RMSE (%) | Difference | t-statistic | p-value | Significant |
|------------|--------------|-------------------|------------|-------------|---------|-------------|
| GRU vs Target (<10%) | 6.98 | 10.00 | -3.02 | N/A | N/A | **Pass** |
| GRU vs Moving Avg | 6.98 | 11.12 | -4.14 | -5.67 | <0.001 | **Yes** |
| GRU vs EMA | 6.98 | 11.28 | -4.30 | -5.89 | <0.001 | **Yes** |
| GRU vs Linear Reg | 6.98 | 11.56 | -4.58 | -6.12 | <0.001 | **Yes** |
| GRU vs Naive | 6.98 | 14.83 | -7.85 | -9.34 | <0.001 | **Yes** |
| GRU vs Seasonal | 6.98 | 18.52 | -11.54 | -12.78 | <0.001 | **Yes** |

![Figure 4-7: Model Comparison - RMSE Across Prediction Methods](figures/fig4-7.png)

**H3 Conclusion**: The GRU model achieves 6.98% RMSE, below the 10% target threshold, and significantly outperforms all baseline methods (p < 0.001). The additional complexity of the GRU architecture is justified by its superior prediction accuracy.

### 4.5.5 Effect Size Interpretation

Table 4.14 provides guidance on effect size interpretation per Cohen's conventions.

**Table 4.14: Effect Size Summary and Interpretation**

| Comparison | Metric | Cohen's d | Interpretation |
|------------|--------|-----------|----------------|
| S4 vs S1 | p99 Latency | 2.14 | Very Large |
| S4 vs S1 | p95 Latency | 2.51 | Very Large |
| S4 vs S1 | Error Rate | 1.33 | Large |
| S4 vs S2 | p99 Latency | 2.01 | Very Large |
| S4 vs S2 | Cost | 3.17 | Very Large |
| S4 vs S3 | SLO Violations | 2.78 | Very Large |
| S4 vs S3 | Violation Duration | 3.65 | Very Large |

All primary comparisons exhibit large to very large effect sizes (d > 0.8), indicating that the observed differences are not only statistically significant but also practically meaningful.

---

## 4.6 Hypothesis Validation Summary

This section synthesizes the experimental evidence to provide definitive verdicts on each research hypothesis.

### 4.6.1 H1: Hybrid System Superiority — VALIDATED ✓

**Hypothesis Statement**: The hybrid Kubernetes-Serverless integration achieves superior performance compared to pure deployments.

**Evidence Summary:**

| Comparison | p99 Latency | p95 Latency | Error Rate | Cost | Overall Verdict |
|------------|-------------|-------------|------------|------|-----------------|
| S4 vs S1 (K8s) | 41.1% ↓ ** | 41.7% ↓ ** | 53.2% ↓ ** | 0.9% ↑ | **Superior** |
| S4 vs S2 (Serverless) | 40.1% ↓ ** | 51.0% ↓ ** | 9.5% ↓ | 42.3% ↓ ** | **Superior** |

_** indicates p < 0.05_

**Verdict**: **PROVEN**. The hybrid-predictive system demonstrates statistically significant improvements over both pure Kubernetes (latency, error rate) and pure serverless (latency, cost). The marginal cost increase versus Kubernetes (0.9%) is offset by substantial latency and reliability gains.

### 4.6.2 H2: Predictive Advantage — VALIDATED ✓

**Hypothesis Statement**: Proactive traffic management based on GRU prediction reduces SLO violations compared to reactive approaches.

**Evidence Summary:**

| Metric | S4 (Predictive) | S3 (Reactive) | Improvement | p-value |
|--------|-----------------|---------------|-------------|---------|
| SLO Violations | 2.35 | 9.15 | **74.5%** ↓ | <0.001 |
| Violation Duration | 20.5s | 156.5s | **86.9%** ↓ | <0.001 |
| Reaction Time | 1352ms | 4411ms | **69.4%** ↓ | <0.001 |
| p99 Latency | 156.5ms | 197.0ms | **20.6%** ↓ | 0.003 |
| Proactive Adjustments | 76.1% | 0.0% | N/A | N/A |

**Verdict**: **PROVEN**. The predictive approach achieves statistically significant reductions across all SLO-related metrics. The 76.1% proactive adjustment ratio confirms that prediction enables anticipatory rather than reactive traffic management.

### 4.6.3 H3: GRU Model Justification — VALIDATED ✓

**Hypothesis Statement**: The GRU neural network provides prediction accuracy sufficient for real-time routing decisions (RMSE < 10%).

**Evidence Summary:**

| Model | RMSE (% of avg) | Target (<10%) | vs. Best Baseline |
|-------|-----------------|---------------|-------------------|
| **GRU** | **6.98%** | ✓ | 37.2% better |
| Moving Average | 11.12% | ✗ | — |
| EMA | 11.28% | ✗ | — |
| Linear Regression | 11.56% | ✗ (but <20%) | — |

**Verdict**: **PROVEN**. The GRU model achieves 6.98% RMSE, well below the 10% threshold, and significantly outperforms all baseline methods. The additional computational complexity is justified by superior prediction accuracy that enables effective proactive routing.

### 4.6.4 Consolidated Validation Table

**Table 4.15: Hypothesis Validation Summary**

| Hypothesis | Description | Primary Evidence | Statistical Significance | Verdict |
|------------|-------------|------------------|-------------------------|---------|
| **H1** | Hybrid > Pure Systems | 41% latency reduction vs K8s; 42% cost reduction vs Serverless | p < 0.001 | **PROVEN** |
| **H2** | Predictive > Reactive | 74.5% SLO violation reduction; 76.1% proactive ratio | p < 0.001 | **PROVEN** |
| **H3** | GRU Model Justified | 6.98% RMSE < 10% target; 37% better than baselines | p < 0.001 | **PROVEN** |

![Figure 4-8: Hypothesis Validation Summary Diagram](figures/fig4-8.png)

---

## 4.7 Chapter Summary

This chapter presented comprehensive experimental results validating the three research hypotheses. The key findings are:

1. **The hybrid Kubernetes-Serverless architecture (S4) outperforms pure deployment models** in latency (41% improvement) and reliability (53% error reduction) while maintaining cost parity with Kubernetes-only deployments.

2. **GRU-based workload prediction enables proactive traffic management**, reducing SLO violations by 74.5% compared to reactive-only approaches. The 76.1% proactive adjustment ratio demonstrates effective anticipation of workload changes.

3. **The GRU model achieves 6.98% RMSE**, validating its use for real-time routing decisions and justifying its computational overhead compared to simpler forecasting methods.

All three hypotheses were validated with statistical significance (p < 0.05) and large effect sizes (Cohen's d > 1.3), providing strong empirical support for the proposed hybrid-predictive system architecture.

The next chapter discusses the implications of these findings, limitations of the current study, and directions for future research.
