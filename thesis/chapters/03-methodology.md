# Chapter 3: Research Methodology (Metodologi Penelitian)

This chapter describes the research design, data collection strategy, system architecture, implementation methods, evaluation plan, and research schedule. Each section details the actual methodology employed, including scope adjustments made during the research process.

## 3.1 Research Flow (Alur Penelitian)

The research follows a six-phase methodology, progressing from theoretical foundations through system design, implementation, and experimental evaluation:

1. **Literature Study** — Survey of cloud computing architectures, workload prediction methods, and elastic scaling algorithms to establish the theoretical foundation and identify the research gap.
2. **Data Collection** — Generation of synthetic workload patterns for GRU model training, supplemented by real HTTP trace datasets (ClarkNet and Calgary) for baseline comparison and validation.
3. **Method Design** — Architecture design of the hybrid Kubernetes-serverless system, specification of routing and scaling algorithms, and definition of the SLO-based decision framework.
4. **Implementation** — Development of the GRU prediction server, routing controller (Algorithm 1), proof-of-concept cluster controller (Algorithm 2), monitoring infrastructure, and traffic routing layer.
5. **Evaluation** — Systematic experimental evaluation across four deployment scenarios with mechanism validation, replicated comparison experiments, and statistical analysis.
6. **Report Writing** — Documentation of findings with truth-aligned claims that distinguish validated mechanisms from unestablished superiority claims.

Each phase produces artifacts that feed into subsequent phases: the literature study informs the system design, the collected data trains the prediction model, the implemented system undergoes experimental evaluation, and the evaluation results inform the thesis conclusions.

---

## 3.2 Data Collection (Pengumpulan Data)

### 3.2.1 Primary Training Data: Synthetic Workload Patterns

The GRU prediction model is trained on synthetically generated traffic patterns designed to represent common cloud workload characteristics. Four pattern types are combined to produce the training dataset:

- **Diurnal cycles**: Sinusoidal traffic patterns simulating daily usage peaks and troughs, representing the most common workload shape in web applications.
- **Bursty spikes**: Short-duration traffic surges injected at random intervals, simulating flash crowd events and viral content scenarios.
- **Gradual ramps**: Linearly increasing traffic segments representing organic growth or planned load increases.
- **Baseline noise**: Gaussian random fluctuations added to all patterns to simulate real-world measurement variability.

These four components are superimposed and scaled to produce time-series sequences of requests per second (RPS). The synthetic approach was chosen for three reasons: (1) it provides controlled ground-truth labels for supervised training, (2) it enables generation of arbitrary quantities of training data, and (3) it allows systematic inclusion of specific pattern types (particularly bursty spikes and ramps) that are underrepresented in historical trace datasets.

**Data Processing Pipeline:**

```
Pattern Definition → Traffic Simulation → RPS Time Series → Sliding Windows → Train/Val/Test Split
```

Processing steps:

1. Generate synthetic traffic patterns by combining the four component types with configurable amplitudes and frequencies.
2. Construct sliding window sequences using a 60-second input window to capture short-term temporal dependencies.
3. Split the resulting sequences into training (70%), validation (15%), and test (15%) sets with temporal ordering preserved to prevent data leakage.

### 3.2.2 Reference Data: Real HTTP Traces

ClarkNet and Calgary HTTP trace datasets are used for baseline model comparison and validation of the GRU model's generalization capability. These datasets are **not** used for training.

**Table 3-1: Reference Dataset Characteristics**

| Dataset | Requests | Time Period | Source | Usage |
|---------|----------|-------------|--------|-------|
| ClarkNet | ~2M | Aug–Sep 1995 | ClarkNet WWW Server | Baseline comparison |
| Calgary | ~2M | Oct 1994 | University of Calgary CS | Pattern validation |

**Table 3-2: Dataset Request Examples**

| Dataset | Request Example |
|---------|-----------------|
| University of Calgary | `local - - [24/Oct/1994:13:41:41 -0600] "GET index.html HTTP/1.0" 200 150` |
| ClarkNet | `204.249.225.59 - - [28/Aug/1995:00:00:34 -0400] "GET /pub/rmharris/catalogs/dawsocat/intro.html HTTP/1.0" 200 3542` |

**Real Trace Processing Pipeline (for baseline comparison):**

```
Raw HTTP Logs → CLF Parsing → Timestamp Extraction → RPS Aggregation → Time Series
```

The real trace data undergoes the same sliding window transformation as the synthetic data to enable direct comparison of prediction accuracy across data sources. The key difference is aggregation granularity: synthetic data uses 1-second intervals (matching the live prediction server), while real traces are aggregated at 5-minute intervals due to the lower temporal resolution of historical access logs.

---

## 3.3 Method Design: System Architecture (Perancangan Arsitektur Sistem)

### 3.3.1 Hybrid Architecture Overview

The proposed system integrates three subsystems: an offline training pipeline, an online prediction and control plane, and a hybrid execution infrastructure. The architecture follows a two-layer design inspired by the ElaX algorithm framework (Yang et al., 2019), where Algorithm 1 governs traffic routing between execution platforms and Algorithm 2 manages cluster-level resource scaling.

```
┌──────────────────────────────────────────────────────────────────────┐
│                       PROPOSED HYBRID SYSTEM                         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────────────────────────────────────────────────┐       │
│   │                    OFFLINE TRAINING                      │       │
│   │  ┌──────────────┐         ┌──────────────────────────┐  │       │
│   │  │ Synthetic    │────────►│ GRU Training Pipeline    │  │       │
│   │  │ Workload     │         │ • Feature engineering    │  │       │
│   │  │ Patterns     │         │ • Model training         │  │       │
│   │  │              │         │ • Hyperparameter tuning   │  │       │
│   │  └──────────────┘         └───────────┬──────────────┘  │       │
│   │                                       │                  │       │
│   │                                       ▼                  │       │
│   │                           ┌──────────────────────┐      │       │
│   │                           │ Trained GRU Model    │      │       │
│   │                           └───────────┬──────────┘      │       │
│   └───────────────────────────────────────┼──────────────────┘       │
│                                           │                          │
│   ┌───────────────────────────────────────┼──────────────────┐       │
│   │                    ONLINE PREDICTION   │                  │       │
│   │                                       ▼                  │       │
│   │  ┌──────────────┐         ┌──────────────────────────┐  │       │
│   │  │ Real-time    │────────►│ GRU Predictor            │  │       │
│   │  │ Traffic      │         │ (30-sec ahead forecast)  │  │       │
│   │  │ Metrics      │         └───────────┬──────────────┘  │       │
│   │  └──────────────┘                     │                  │       │
│   │                                       ▼                  │       │
│   │                      ┌────────────────────────────┐     │       │
│   │                      │ Resource Allocation Model  │     │       │
│   │                      │      R = α·x + β           │     │       │
│   │                      └────────────┬───────────────┘     │       │
│   │                                   │                      │       │
│   │                                   ▼                      │       │
│   │               ┌───────────────────────────────────┐     │       │
│   │               │      ONLINE CONTROLLERS            │     │       │
│   │               │  ┌─────────────┐ ┌─────────────┐  │     │       │
│   │               │  │ Algorithm 1 │ │ Algorithm 2 │  │     │       │
│   │               │  │ Routing     │ │ Cluster     │  │     │       │
│   │               │  │ Controller  │ │ Controller  │  │     │       │
│   │               │  │ (Impl.)     │ │ (PoC)       │  │     │       │
│   │               │  └──────┬──────┘ └──────┬──────┘  │     │       │
│   │               └─────────┼───────────────┼─────────┘     │       │
│   │                         │               │                │       │
│   └─────────────────────────┼───────────────┼────────────────┘       │
│                             │               │                        │
│   ┌─────────────────────────┼───────────────┼────────────────┐       │
│   │            INFRASTRUCTURE               │                │       │
│   │                         ▼               ▼                │       │
│   │   ┌─────────────────────────────────────────────────┐   │       │
│   │   │              TRAFFIC ROUTER (HAProxy)            │   │       │
│   │   └─────────────┬───────────────────────┬───────────┘   │       │
│   │                 │                       │                │       │
│   │                 ▼                       ▼                │       │
│   │   ┌─────────────────────┐   ┌─────────────────────┐    │       │
│   │   │   KUBERNETES (K3s)  │   │     SERVERLESS      │    │       │
│   │   │   • Cost-effective  │   │     (Knative)       │    │       │
│   │   │   • Always warm     │   │   • Instant scale   │    │       │
│   │   │   • Baseline load   │   │   • Burst handling  │    │       │
│   │   └─────────────────────┘   └─────────────────────┘    │       │
│   │                                                          │       │
│   └──────────────────────────────────────────────────────────┘       │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.3.2 Infrastructure Components

The infrastructure layer consists of three components:

**HAProxy (Traffic Router):** Serves as the entry point for all HTTP traffic, distributing requests between the Kubernetes and serverless backends according to weighted routing rules. Weights are dynamically adjusted by Algorithm 1 through the HAProxy Runtime API (TCP socket interface). HAProxy also exposes a statistics endpoint that provides real-time throughput and latency metrics consumed by the monitoring subsystem.

**K3s (Kubernetes Backend):** A lightweight, certified Kubernetes distribution deployed via k3d (k3s-in-Docker). K3s runs the primary application workload as always-warm pods, providing consistent low-latency responses for baseline traffic. The K3s backend is cost-effective for sustained load because its resources are pre-provisioned and shared across requests.

**Knative Serving (Serverless Backend):** Deployed on the same K3s cluster using Kourier as the ingress controller. Knative provides scale-to-zero capability and rapid autoscaling for burst traffic. When the routing controller enables the serverless backend, Knative automatically manages pod lifecycle including cold start initialization. The serverless backend is engaged only when SLO violations occur or when the GRU model predicts an imminent load surge.

### 3.3.3 Monitoring and Metrics Collection

The system uses Prometheus for metrics collection and the SLO monitor component for real-time compliance checking:

- **Prometheus** scrapes HAProxy statistics at 1-second intervals, collecting request counts, response times, and backend health status.
- **SLO Monitor** computes the 99th percentile (p99) tail latency from Prometheus time-series data and maintains a rolling violation window to detect sustained SLO breaches.
- **Prometheus metrics** from the routing daemon itself (decision counts, weight changes, prediction usage) enable post-experiment analysis and debugging.

---

## 3.4 Implementation Method (Metode Implementasi)

### 3.4.1 Workload Predictor (GRU Architecture)

The workload prediction model uses a Gated Recurrent Unit (GRU) neural network, chosen for its favorable trade-off between prediction accuracy and computational efficiency compared to LSTM networks. GRU achieves comparable performance with fewer parameters, resulting in faster training and lower inference latency.

**Architecture:**

```
Input: Time-series window (60 seconds of RPS data)
                    │
                    ▼
        ┌───────────────────────┐
        │   Input Layer         │
        │   (sequence_length,   │
        │    features)          │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   GRU Layer 1         │
        │   (64 units)          │
        │   + Dropout (0.2)     │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   GRU Layer 2         │
        │   (32 units)          │
        │   + Dropout (0.2)     │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   Dense Layer         │
        │   (prediction_horizon)│
        └───────────┬───────────┘
                    │
                    ▼
Output: Predicted RPS for next 30 seconds
```

The model consists of two stacked GRU layers with decreasing hidden dimensions (64 → 32 units), each followed by dropout regularization (rate 0.2) to prevent overfitting. The final dense layer outputs the predicted RPS value for the 30-second prediction horizon. This multi-step prediction enables the routing controller to anticipate workload changes and take proactive action.

**Training Configuration:**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Optimizer | Adam | Adaptive learning rate, standard for RNN training |
| Loss function | Mean Squared Error (MSE) | Direct optimization of prediction accuracy |
| Batch size | 32 | Balance between gradient stability and memory usage |
| Epochs | 100 (with early stopping) | Early stopping prevents overfitting on validation loss |
| Validation split | 15% | Sufficient for monitoring generalization |
| Learning rate | Default (0.001) | Adam default, no manual scheduling needed |

**Prediction Server:** The trained model is served via a FastAPI prediction server that accepts recent RPS history as input and returns both the predicted load value and a confidence score. The confidence score is computed from prediction variance and serves as a gating mechanism—the routing controller only acts on predictions exceeding a configurable confidence threshold (default: 0.5).

### 3.4.2 Resource Allocation Model

A linear resource allocation model translates predicted workload into required compute resources:

$$R = \alpha \cdot x + \beta$$

Where:

- $R$: Required resources (expressed as replica count or CPU millicores)
- $x$: Predicted traffic (requests per second)
- $\alpha$: Resource-per-request coefficient (how many additional resources each RPS requires)
- $\beta$: Base resource overhead (minimum resources needed at zero load)

**Coefficient Derivation (OLS):**

The coefficients $\alpha$ and $\beta$ are derived using Ordinary Least Squares (OLS) regression on historical workload-to-resource mapping data:

```python
from sklearn.linear_model import LinearRegression

model = LinearRegression()
model.fit(X_historical_traffic, y_historical_resources)

alpha = model.coef_[0]   # Resource per request coefficient
beta = model.intercept_   # Base resource overhead
```

This model is used by Algorithm 2 (Cluster Controller) to compute scaling targets from GRU predictions.

### 3.4.3 Online Controllers

The online control plane consists of two algorithms that operate at different layers of the system.

#### 3.4.3.1 Algorithm 1: Routing Controller (Primary Implementation)

Algorithm 1 is the primary decision engine, fully implemented and experimentally evaluated. It monitors SLO compliance and adjusts traffic routing weights between Kubernetes and serverless backends using a priority-based decision framework.

**Algorithm 1: SLO-Aware Routing Controller**

```pseudocode
Algorithm 1: SLO-Aware Routing Controller
────────────────────────────────────────────────────────────────

Constants:
  SLO_THRESHOLD ← 200ms            // p99 latency target
  HEALTHY_MARGIN ← 0.7             // healthy = p99 < SLO × 0.7
  WEIGHT_STEP ← 10                 // weight adjustment increment
  COOLDOWN ← 15 seconds            // minimum time between adjustments
  MAX_SERVERLESS ← 50              // maximum serverless weight (%)
  CONFIDENCE_THRESHOLD ← 0.5       // minimum prediction confidence
  LOAD_CHANGE_THRESHOLD ← 0.3      // significant load change (30%)

Variables:
  weights ← {k3s: 100, knative: 0}  // initial: all traffic to K8s
  serverless_enabled ← False
  last_adjustment_time ← null

repeat every COOLDOWN seconds:

  // Step 1: Get current metrics
  slo_status ← SLOMonitor.check()
  prediction ← GRUClient.predict() if available
  current_load ← get_current_rps()

  // Step 2: Priority-based decision
  if slo_status.violation_duration ≥ VIOLATION_WINDOW then
    // SCALE_OUT (Priority 1): SLO violated → shift to serverless
    if not serverless_enabled then
      enable_serverless_backend()
      prewarm_knative()
      serverless_enabled ← True
    end if
    knative_weight ← min(MAX_SERVERLESS, weights.knative + WEIGHT_STEP)
    weights ← {k3s: 100 - knative_weight, knative: knative_weight}

  else if slo_status.p99 < SLO_THRESHOLD × HEALTHY_MARGIN then
    // OPTIMIZE_COST (Priority 3): Healthy → reduce serverless usage
    step ← WEIGHT_STEP / 2
    k3s_weight ← min(100, weights.k3s + step)
    weights ← {k3s: k3s_weight, knative: 100 - k3s_weight}
    if weights.knative = 0 then
      serverless_enabled ← False
    end if

  else if prediction ≠ null
         AND prediction.confidence ≥ CONFIDENCE_THRESHOLD
         AND load_change(prediction, current_load) > LOAD_CHANGE_THRESHOLD then
    // PREDICTIVE (Priority 2): Predicted surge → preemptive scale out
    if not serverless_enabled then
      enable_serverless_backend()
      prewarm_knative()
      serverless_enabled ← True
    end if
    knative_weight ← min(MAX_SERVERLESS, weights.knative + WEIGHT_STEP)
    weights ← {k3s: 100 - knative_weight, knative: knative_weight}

  else
    // MAINTAIN (Priority 4): No change needed
    // Keep current weights
  end if

  // Step 3: Apply weights to HAProxy
  HAProxy.set_weights(weights.k3s, weights.knative)

until shutdown
```

**Decision Types and Priority:**

| Priority | Action | Trigger Condition | Effect |
|----------|--------|-------------------|--------|
| 1 | SCALE_OUT | p99 > SLO threshold for sustained period | Shift traffic toward serverless |
| 2 | PREDICTIVE | Healthy state + GRU predicts >30% load increase | Preemptive serverless engagement |
| 3 | OPTIMIZE_COST | p99 < SLO × healthy margin | Reduce serverless usage |
| 4 | MAINTAIN | None of the above | Keep current weights |

The priority ordering ensures that active SLO violations always take precedence over predictive optimization, which in turn takes precedence over cost optimization. This prevents the system from reducing serverless capacity during a predicted surge.

**Weight Progression:**

Traffic weights shift gradually in increments of WEIGHT_STEP (10%) to avoid oscillation:

```
100/0 (K8s only) → 90/10 → 80/20 → 70/30 → 60/40 → 50/50 (maximum serverless)
```

The maximum serverless weight is capped at 50% to ensure the Kubernetes backend always handles at least half of the traffic, maintaining cost efficiency for baseline load.

**Knative Pre-warming:** When serverless is first enabled (either by SCALE_OUT or PREDICTIVE), the controller sends a synthetic health-check request to the Knative service endpoint to trigger cold start initialization. This reduces the latency penalty when actual traffic begins routing to the serverless backend.

#### 3.4.3.2 Algorithm 2: Cluster Controller (Proof-of-Concept)

Algorithm 2 addresses cluster-level resource scaling by computing required Kubernetes replica counts from predicted workload using the linear resource model. This algorithm is implemented as a proof-of-concept to demonstrate architectural feasibility; it is not integrated into the live experiment pipeline and is not subjected to full experimental evaluation.

**Algorithm 2: Prediction-Based Cluster Controller (Proposed)**

```pseudocode
Algorithm 2: Cluster Controller (Proof-of-Concept)
────────────────────────────────────────────────────────────────

Constants:
  ALPHA ← 0.01           // replicas per request/s
  BETA ← 1.0             // base replicas (minimum)
  BUFFER ← 1.2           // 20% capacity buffer
  MIN_REPLICAS ← 1
  MAX_REPLICAS ← 10
  SCALE_DOWN_THRESHOLD ← 0.8
  PREDICTION_INTERVAL ← 30 seconds

Variables:
  current_replicas ← 1

repeat every PREDICTION_INTERVAL:

  // Step 1: Get prediction
  predicted_load ← GRUPredictor.predict()

  // Step 2: Calculate required resources
  required ← ALPHA × predicted_load + BETA

  // Step 3: Apply buffer and clamp
  target ← clamp(required × BUFFER, MIN_REPLICAS, MAX_REPLICAS)

  // Step 4: Scaling decision
  if target > current_replicas then
    action ← SCALE_UP
    // Would execute: kubectl scale deployment --replicas=target
  else if target < current_replicas × SCALE_DOWN_THRESHOLD then
    action ← SCALE_DOWN
  else
    action ← MAINTAIN
  end if

  current_replicas ← target  // Simulate applying decision

until shutdown
```

**Implementation scope:** The proof-of-concept implementation computes scaling decisions and logs them with a full audit trail, but does not execute actual `kubectl scale` commands. Integration with Kubernetes HPA (Horizontal Pod Autoscaler) or VPA (Vertical Pod Autoscaler) is left for future work. The implementation includes 14 unit tests validating the computation logic, scaling boundaries, and decision categorization.

---

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

---

## 3.6 Research Schedule (Jadwal Penelitian)

**Table 3-7: Research Timeline**

| No | Activity | M1 | M2 | M3 | M4 | M5 | M6 |
|----|----------|:--:|:--:|:--:|:--:|:--:|:--:|
| 1 | Literature Study | ■ | ■ | | | | |
| 2 | Data Collection | | ■ | | | | |
| 3 | System Design | | ■ | ■ | ■ | | |
| 4 | Implementation and Testing | | | ■ | ■ | ■ | |
| 5 | Journal Writing | | | | | ■ | |
| 6 | Report Writing | | ■ | ■ | ■ | ■ | ■ |

**Legend:**

- M1–M6: Month 1 through Month 6
- ■: Activity scheduled for that month

**Milestones:**

- **Month 2:** Data collection complete, system architecture finalized
- **Month 3:** GRU model trained, core controller prototype operational
- **Month 4:** Algorithm 1 fully implemented, Phase A1 mechanism validation complete
- **Month 5:** Phase B replicated experiments complete, statistical analysis finished, journal draft
- **Month 6:** Final thesis report with truth-aligned conclusions
