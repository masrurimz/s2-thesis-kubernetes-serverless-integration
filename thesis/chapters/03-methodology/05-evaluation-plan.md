## 3.5 Evaluation Plan (Rencana Evaluasi)

This evaluation plan is designed to (i) validate the mechanisms of the hybrid routing and scaling control plane, (ii) compare system behavior under realistic **trace-driven replay** workloads, and (iii) measure dynamic response to bursts and ramps. The plan specifies exact procedures, metrics, data collection, and post-processing steps for reproducibility.

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

### 3.5.2 System Evaluation: Scenarios and Phases

#### Evaluation Scenarios

Four scenarios are defined with strict variable isolation: each consecutive pair differs by exactly one mechanism, enabling clean attribution of performance differences. All scenarios route traffic through HAProxy to eliminate data-path confounds. Algorithm 2 (replica scaling) operates in two modes: **reactive** (using observed load $x_{obs}$) and **predictive** (using GRU-predicted load $x_{pred}$), with identical parameters ($\alpha, \beta, \gamma, R_{min}, R_{max}$, cooldowns) in both modes.

**Table 3-3: Evaluation Scenarios**

| Scenario | Name | Routing | Algorithm 1 | Algorithm 2 (Scaling) | Scaling Signal | GRU |
|----------|------|---------|-------------|----------------------|----------------|-----|
| S1 | K8s-Only Static | 100% K8s, Knative weight=0 | Off | Off (fixed replicas) | — | Off |
| S2 | K8s Reactive Scaling | 100% K8s, Knative weight=0 | Off | On (reactive mode) | $x_{obs}$ | Off |
| S3 | Hybrid Reactive | Dynamic K8s↔Knative | On (reactive only) | On (reactive mode) | $x_{obs}$ | Off |
| S4 | Hybrid Predictive | Dynamic K8s↔Knative | On (predictive enabled) | On (predictive mode) | $x_{pred}$ | On |

Where $x_{obs}$ = mean observed RPS over the last 30 seconds (matching the GRU prediction horizon), and $x_{pred}$ = GRU 30-second-ahead forecast.

**Scenario Comparisons (One Variable per Pair):**

- **S1 vs S2**: Isolates the **value of autoscaling** — both are K8s-only; only difference is Algorithm 2 reactive scaling ON vs OFF.
- **S2 vs S3**: Isolates the **value of hybrid routing** — both use reactive replica scaling; only difference is Algorithm 1 + Knative overflow ON vs OFF.
- **S3 vs S4**: Isolates the **value of GRU prediction** — both use hybrid routing and replica scaling; only difference is reactive signal ($x_{obs}$) vs predictive signal ($x_{pred}$) and the PREDICTIVE trigger in Algorithm 1.

**Configuration Lock (ensuring S3 vs S4 isolation):** S3 and S4 use identical Algorithm 2 parameters, weight step sizes, SLO thresholds, cooldowns, and control intervals. The only configuration change is the prediction source and the PREDICTIVE branch enable flag in Algorithm 1.

### 3.5.3 Evaluation Phases

#### Phase A1: Mechanism Validation (Validasi Mekanisme)

A controlled ramp-load experiment to validate that individual system mechanisms function correctly:

- **Workload profile (k6 synthetic):** Baseline (60s @ 20 RPS) → Ramp (60s @ 20→100 RPS) → Peak (120s @ 100 RPS)
- **Purpose:** Confirm that weight shifting, serverless engagement, SLO monitoring, PREDICTIVE action triggering, Kubernetes replica scaling via Algorithm 2, and traffic return to Kubernetes all operate as designed.
- **Success criteria:**
  1. In S4, Algorithm 1 engages Knative before sustained SLO violation during the ramp (predictive trigger).
  2. Algorithm 2 issues a scale-up toward the computed $R_{target}$.
  3. After replicas are ready and healthy, traffic shifts back toward Kubernetes and Knative usage decreases.

#### Phase B: Replicated Comparison with Trace-Driven Workload (Perbandingan dengan Beban Trace)

The primary comparative evaluation with statistical rigor, using realistic time-varying workload derived from ClarkNet trace replay:

- **Workload:** ClarkNet trace-driven replay using 30-second buckets and k6 `ramping-arrival-rate` stages (Section 3.2.4). Replay duration per run is fixed (e.g., 20 minutes) and recorded in the run manifest. A replay scaling factor $g$ is applied to fit testbed capacity and kept constant across all scenarios.
- **Replication:** $n = 5$ runs per scenario × 4 scenarios = 20 total runs.
- **Randomization:** Run order randomized using `random.shuffle()` to control for temporal confounds (e.g., system warm-up, background processes).
- **Cool-down:** 60-second pause between consecutive runs plus explicit system reset (see Section 3.5.4).

**Statistical Analysis:**

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

#### Phase C: Dynamic Burst Validation (Validasi Lonjakan Dinamis)

Stress the system with controlled, repeatable bursts to quantify responsiveness and stability beyond historical traces:

- **Workload profiles:**
  1. **Single burst:** 60s @ 30 RPS → 30s @ 200 RPS → 180s @ 30 RPS
  2. **Burst train:** repeated 15s spikes every 60s for 10 minutes
- **Purpose:** Stress the system with controlled bursts to measure scale-up responsiveness, oscillation behavior, and recovery time.
- **Success criteria:**
  - p99 remains below the SLO threshold more frequently in S4 than S3/S1.
  - Scale-up occurs quickly enough to reduce sustained reliance on Knative.
  - Minimal oscillation in replicas and traffic weights after stabilization.

### 3.5.4 Detailed Experiment Procedure (Prosedur Eksperimen Terperinci)

#### (A) Infrastructure Setup (One-Time per Machine)

1. **Start k3d/k3s cluster** with fixed resource limits (CPU/memory) and fixed versions recorded in an experiment manifest.
2. **Deploy components:**
   - Application (Kubernetes Deployment + Service)
   - Knative Serving (Kourier ingress) and Knative Service for the same application image
   - HAProxy configured with two backends (K8s and Knative) and runtime socket enabled
   - Prometheus configured to scrape: HAProxy stats endpoint, routing daemon metrics endpoint, Kubernetes metrics
3. **Start GRU prediction server** (FastAPI) and confirm health endpoint responds.
4. **Start routing daemon** with: control interval = 15s, logging enabled (structured JSON), Prometheus exporter enabled.

#### (B) Per-Run Reset Procedure

Before each run:

1. **Reset HAProxy weights** to baseline (e.g., 100/0 for S1; scenario-defined initial weights for S3/S4).
2. **Reset Kubernetes replicas:** scale to fixed baseline (e.g., 1 replica for S1/S3; 1 replica for S4 with Algorithm 2 active).
3. **Reset Knative:** ensure minScale = 0 and no active requests; wait until Knative pods scale to zero.
4. **Clear/rotate logs:** routing daemon log, prediction server log, HAProxy log, k6 output path.
5. **Warm-up period:** 30 seconds idle to stabilize Prometheus scraping and avoid initialization noise.

#### (C) Run Execution

1. Record start timestamp $t_{start}$.
2. Execute k6 with the appropriate workload:
   - Phase A1/C: synthetic script with defined stages.
   - Phase B: generated trace-driven stages from `k6_stages.json`.
3. After k6 completion, wait 60 seconds cooldown to capture delayed scaling effects.
4. Record end timestamp $t_{end}$.
5. Export all metrics for $[t_{start}, t_{end}]$.

#### (D) Data Export (Per Run)

For each run, store:
- `k6_summary.json` and full k6 output
- Routing daemon log (JSONL)
- Prediction server log
- Prometheus exports via `query_range` for all metrics listed in Section 3.5.5
- Configuration snapshot: HAProxy config, routing daemon config, resource model coefficients ($\alpha, \beta, \gamma$), k6 script + stages JSON, git commit hash

### 3.5.5 Metrics

#### (A) User-Perceived Performance Metrics

**Table 3-4: Performance Metrics**

| Metric | Description | Target / Interpretation |
|--------|-------------|------------------------|
| p50 Latency | Median response time | Descriptive |
| p95 Latency | 95th percentile response time | Descriptive |
| p99 Latency | Tail latency (SLO metric) | ≤ 200ms |
| Error Rate | Fraction of HTTP 5xx / failed requests | < 0.1% |
| Achieved Throughput | Delivered RPS vs target RPS | Diagnose overload or generator limits |

#### (B) Routing and Control-Plane Metrics

**Table 3-5: Routing/Controller Metrics**

| Metric | Description | Interpretation |
|--------|-------------|----------------|
| Weight change count | Number of HAProxy weight updates | Oscillation/stability indicator |
| Time-in-serverless (%) | Fraction of time Knative weight > 0 | Proxy for serverless reliance |
| Prediction usage rate | Fraction of control cycles using GRU | Verifies S4 predictive behavior |
| Control-loop latency | Time to compute + apply decisions | Must fit in 15-second interval |

#### (C) Kubernetes Replica Scaling Metrics (Algorithm 2)

**Table 3-6: Replica Scaling Metrics**

| Metric | Description | Interpretation |
|--------|-------------|----------------|
| Desired replicas ($R_{target}$) | Computed by $R = \alpha x + \beta$ with buffer | Planning signal |
| Current replicas ($R_{current}$) | Deployment `.spec.replicas` | Control state |
| Ready replicas | Deployment `.status.readyReplicas` | Actual available capacity |
| Scale-up events | Count of replica increases | Responsiveness indicator |
| Scale-down events | Count of replica decreases | Cost optimization behavior |
| Scale-up latency | Time from scale command → ready replicas = target | Provisioning speed |
| Oscillation index | Number of direction changes (up→down→up) per run | Stability indicator |

#### (D) Resource and Cost Proxy Metrics

**Table 3-7: Resource and Cost Metrics**

| Metric | Description | Computation |
|--------|-------------|-------------|
| CPU Utilization | Average CPU usage across pods | From Prometheus/K8s metrics |
| Memory Utilization | Average memory usage | From Prometheus/K8s metrics |
| K8s Capacity Time | Σ(replicas × seconds) | Cost proxy for K8s usage |
| Knative Active Time | Time with ≥1 Knative pod | Serverless cost proxy |

Cost analysis uses proxy estimation based on published pricing from AWS, GCP, and Azure, rather than actual cloud billing data, due to the local testbed deployment.

### 3.5.6 Post-Processing and Statistical Analysis (Pengolahan Data)

1. **Alignment:** All time-series metrics are aligned to the run window $[t_{start}, t_{end}]$ using UTC timestamps.
2. **Event derivation:** Routing event = change in HAProxy backend weights. Scaling event = change in deployment `.spec.replicas`.
3. **Latency aggregation:** k6 latency percentiles are computed per run; Prometheus latency (if collected from HAProxy) is used as secondary corroboration.
4. **Statistical tests (Phase B):** Welch's t-test and Mann-Whitney U for scenario comparisons, bootstrap confidence intervals for median/p99 differences, Cohen's d for effect size.
5. **Reporting:** All exclusions (e.g., failed runs) are documented with a reproducible reason.

### 3.5.7 Threats to Validity (Ancaman terhadap Validitas)

The experimental evaluation is subject to the following known threats, documented proactively:

1. **Localhost routing bias (Critical):** The k3d single-node testbed runs all components (HAProxy, K3s, Knative) on localhost, creating an artificial advantage for the K8s-only scenario (S1) where traffic never traverses a real network. This limits the interpretability of absolute performance comparisons between scenarios.

2. **Trace age and representativeness:** ClarkNet and Calgary are historical traces (1994–1995). They represent realistic temporal variability but may not match modern application semantics (TLS, dynamic content, microservices).

3. **Replay fidelity limitations:** Trace-driven replay preserves request intensity over time but does not reproduce original client think times, cache behaviors, or request mix unless explicitly modeled.

4. **Load generator saturation:** k6 may become CPU-limited at high target rates, reducing achieved throughput and biasing results. Generator resource usage must be monitored and reported.

5. **Cold start variability in Knative:** Serverless cold starts may vary between runs due to image caching and node state. Run order randomization and explicit reset procedures mitigate but cannot fully eliminate this.

6. **Model coefficient drift:** The resource allocation coefficients ($\alpha, \beta$) are calibrated on the testbed; changes in container limits, application version, or node resources require recalibration to keep scaling behavior comparable.

7. **GRU server availability:** The prediction server must be confirmed running before S4 experiments to ensure the predictive mechanism is active. Infrastructure health checks are performed at experiment start.

8. **Sample size:** With $n = 5$ runs per scenario, statistical power is limited for detecting moderate effect sizes. Results are interpreted as mechanism validation rather than definitive superiority claims.
