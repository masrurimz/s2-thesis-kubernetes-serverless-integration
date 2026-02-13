## 3.5 Evaluation Plan (Rencana Evaluasi)

### 3.5.1 Traffic Predictor Evaluation

The GRU prediction model is evaluated using three standard regression metrics, computed on the held-out test set:

**Root Mean Square Error (RMSE):**

$$RMSE = \sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i - \hat{y}_i)^2}$$

**Mean Absolute Error (MAE):**

$$MAE = \frac{1}{n}\sum_{i=1}^{n}|y_i - \hat{y}_i|$$

**Mean Absolute Percentage Error (MAPE):**

$$MAPE = \frac{100\%}{n}\sum_{i=1}^{n}\left|\frac{y_i - \hat{y}_i}{y_i}\right|$$

To facilitate comparison across different traffic scales, percentage-normalized variants are also computed:

- **RMSE%** = (RMSE / mean(y)) × 100%
- **MAE%** = (MAE / mean(y)) × 100%

**Target Performance:**

| Metric | Target | Rationale |
|--------|--------|-----------|
| RMSE% | < 10% of average traffic | Sufficient accuracy for proactive routing |
| MAE% | < 5% of average traffic | Low average error for stable predictions |
| Inference latency | < 50ms | Real-time constraint for 15-second decision cycle |

The model is evaluated on both synthetic test data (primary accuracy assessment) and real HTTP trace data from ClarkNet and Calgary (generalization assessment). Performance on real traces is reported separately with the expectation that accuracy may be lower due to non-stationarity and irregular patterns absent in synthetic training data.

### 3.5.2 Router and Scaling Evaluation

#### Evaluation Scenarios

Four scenarios are defined to isolate the contribution of each system component:

**Table 3-3: Evaluation Scenarios**

| Scenario | Name | Routing | Algorithm | GRU Prediction |
|----------|------|---------|-----------|----------------|
| S1 | K8s-Only | 100% K8s, 0% Serverless | None (static) | No |
| S2 | Serverless-Only | 0% K8s, 100% Serverless | None (static) | No |
| S3 | Hybrid Reactive | Initial 80/20, dynamic | Algorithm 1 | No |
| S4 | Hybrid Predictive | Initial 80/20, dynamic | Algorithm 1 | Yes |

- **S1 vs S4** tests H1: whether the hybrid architecture outperforms pure K8s.
- **S3 vs S4** tests H2: whether predictive routing outperforms reactive-only.
- **S1 and S2** serve as baselines for cost and performance comparison.

#### Performance Metrics

**Table 3-4: Performance Metrics**

| Metric | Description | Target |
|--------|-------------|--------|
| p50 Latency | Median response time | < 50ms |
| p95 Latency | 95th percentile response time | < 100ms |
| p99 Latency | 99th percentile (tail latency) | < 200ms |
| Error Rate | Percentage of failed requests (HTTP 5xx) | < 0.1% |
| Throughput | Sustained requests per second | No degradation |

**Table 3-5: Resource Metrics**

| Metric | Description | Target |
|--------|-------------|--------|
| CPU Utilization | Average CPU usage across pods | 60–80% |
| Memory Utilization | Average memory usage | < 80% |
| Scale Events | Number of weight adjustment decisions | Minimize unnecessary changes |

**Table 3-6: Cost Metrics**

| Metric | Description | Computation |
|--------|-------------|-------------|
| K8s Cost | Resource-hours × unit price | Based on public cloud pricing |
| Serverless Cost | Invocations × execution time × unit price | Per-invocation billing model |
| Total Cost | K8s Cost + Serverless Cost | Sum of both components |

Cost analysis uses proxy estimation based on published pricing from AWS, GCP, and Azure, rather than actual cloud billing data, due to the local testbed deployment.

#### Experiment Design

**Phase A1: Mechanism Validation**

A controlled ramp-load experiment to validate that individual system mechanisms function correctly:

- **Workload profile:** Baseline (60s @ 20 RPS) → Ramp (60s @ 20→100 RPS) → Peak (120s @ 100 RPS)
- **Purpose:** Confirm that weight shifting, serverless engagement, SLO monitoring, and PREDICTIVE action triggering operate as designed.
- **Success criteria:** PREDICTIVE triggers before SLO violation during the ramp phase; weight progression follows the expected 100/0 → 50/50 path.

**Phase B: Replicated Comparison**

The primary comparative evaluation with statistical rigor:

- **Workload:** Steady-state at 100 RPS for 300 seconds per run.
- **Replication:** 5 runs per scenario × 4 scenarios = 20 total runs.
- **Randomization:** Run order randomized using `random.shuffle()` to control for temporal confounds (e.g., system warm-up, background processes).
- **Cool-down:** 30-second pause between consecutive runs to allow system state to reset.

**Statistical Analysis:**

The following statistical tests are applied to compare scenario pairs:

| Test | Purpose | Assumptions |
|------|---------|-------------|
| Welch's t-test | Mean comparison with unequal variances | Approximate normality |
| Mann-Whitney U | Non-parametric rank comparison | No distributional assumptions |
| Bootstrap CI | Confidence intervals via resampling | No distributional assumptions |
| Cohen's d | Effect size quantification | — |

Significance threshold is set at α = 0.05. Both parametric (Welch's t-test) and non-parametric (Mann-Whitney U) tests are reported to provide robustness against small-sample normality violations. Effect sizes (Cohen's d) are reported alongside p-values to quantify practical significance regardless of statistical significance.

**Data Quality:**

- Outlier detection using the criterion p99 < 15ms (indicating measurement artifact rather than genuine system behavior).
- Excluded runs are documented with explicit justification.
- Statistics are recomputed on the clean dataset.

### 3.5.3 Threats to Validity

The experimental evaluation is subject to the following known threats, documented proactively:

1. **Localhost routing bias (Critical):** The k3d single-node testbed runs all components (HAProxy, K3s, Knative) on localhost, creating an artificial advantage for the K8s-only scenario (S1) where traffic never traverses a real network. This limits the interpretability of absolute performance comparisons between scenarios.

2. **GRU server availability:** The prediction server must be confirmed running before S4 experiments to ensure the predictive mechanism is active. Infrastructure health checks are performed at experiment start.

3. **Workload representativeness:** Steady-state load (100 RPS constant) does not create the dynamic workload conditions (ramps, bursts) needed to exercise the PREDICTIVE mechanism. Mechanism validation (Phase A1) uses dynamic workload separately to address this limitation.

4. **Synthetic training data:** The GRU model is trained on synthetic patterns that may not capture all characteristics of real production workloads. Generalization to real traces is assessed but not guaranteed.

5. **Sample size:** With n = 5 runs per scenario, statistical power is limited for detecting moderate effect sizes. Results are interpreted as mechanism validation rather than definitive superiority claims.
