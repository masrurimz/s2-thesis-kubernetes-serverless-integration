# Chapter 3: Methodology (Metodologi)

## Research Flow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      RESEARCH METHODOLOGY                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────┐                                                 │
│  │ 3.1        │                                                 │
│  │ Literature │                                                 │
│  │ Study      │                                                 │
│  └─────┬──────┘                                                 │
│        │                                                         │
│        ▼                                                         │
│  ┌────────────┐                                                 │
│  │ 3.2        │                                                 │
│  │ Data       │                                                 │
│  │ Collection │                                                 │
│  └─────┬──────┘                                                 │
│        │                                                         │
│        ▼                                                         │
│  ┌────────────┐                                                 │
│  │ 3.3        │                                                 │
│  │ Method     │                                                 │
│  │ Design     │                                                 │
│  └─────┬──────┘                                                 │
│        │                                                         │
│        ▼                                                         │
│  ┌────────────┐                                                 │
│  │ 3.4        │                                                 │
│  │ Implement- │                                                 │
│  │ ation      │                                                 │
│  └─────┬──────┘                                                 │
│        │                                                         │
│        ▼                                                         │
│  ┌────────────┐                                                 │
│  │ 3.5        │                                                 │
│  │ Evaluation │                                                 │
│  └─────┬──────┘                                                 │
│        │                                                         │
│        ▼                                                         │
│  ┌────────────┐                                                 │
│  │ 3.6        │                                                 │
│  │ Report     │                                                 │
│  │ Writing    │                                                 │
│  └────────────┘                                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3.1 Literature Study (Studi Literatur)

The literature study phase focuses on understanding:

1. **Cloud Computing Fundamentals**
   - Container orchestration (Kubernetes)
   - Serverless computing (FaaS)
   - Hybrid cloud architectures

2. **Workload Prediction**
   - Time-series forecasting methods
   - Deep learning approaches (LSTM, GRU)
   - Accuracy evaluation metrics

3. **Elastic Scaling Algorithms**
   - ElaX algorithm and modifications
   - SLO-aware resource management
   - Proactive vs. reactive scaling

4. **Performance Metrics**
   - Latency measurement (tail latency)
   - Resource utilization
   - Cost modeling

---

## 3.2 Data Collection (Pengumpulan Data)

### Datasets

Two real HTTP trace datasets are used for training and evaluation:

**Table 3-1: Dataset Request Examples**

| Dataset | Request Example |
|---------|-----------------|
| University of Calgary | `local - - [24/Oct/1994:13:41:41 -0600] "GET index.html HTTP/1.0" 200 150` |
| ClarkNet | `204.249.225.59 - - [28/Aug/1995:00:00:34 -0400] "GET /pub/rmharris/catalogs/dawsocat/intro.html HTTP/1.0" 200 3542` |

### Dataset Characteristics

| Dataset | Requests | Time Period | Source |
|---------|----------|-------------|--------|
| ClarkNet | ~2M | Aug-Sep 1995 | ClarkNet WWW Server |
| Calgary | ~2M | Oct 1994 | University of Calgary CS |

### Data Processing Pipeline

```
Raw HTTP Logs → CLF Parsing → Timestamp Extraction → RPS Aggregation → Time Series
```

**Processing Steps:**
1. Parse Combined Log Format (CLF) entries
2. Extract timestamp for each request
3. Aggregate to requests-per-second (RPS)
4. Create sliding window sequences for GRU training
5. Split into train/validation/test sets (70/15/15)

---

## 3.3 Method Design (Perancangan Metode)

### System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                       PROPOSED HYBRID SYSTEM                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   ┌─────────────────────────────────────────────────────────┐        │
│   │                    OFFLINE TRAINING                      │        │
│   │  ┌──────────────┐         ┌──────────────────────────┐  │        │
│   │  │ HTTP Trace   │────────►│ GRU Training Pipeline    │  │        │
│   │  │ Datasets     │         │ • Feature engineering    │  │        │
│   │  │ (ClarkNet,   │         │ • Model training        │  │        │
│   │  │  Calgary)    │         │ • Hyperparameter tuning │  │        │
│   │  └──────────────┘         └───────────┬──────────────┘  │        │
│   │                                       │                  │        │
│   │                                       ▼                  │        │
│   │                           ┌──────────────────────┐      │        │
│   │                           │ Trained GRU Model    │      │        │
│   │                           └───────────┬──────────┘      │        │
│   └───────────────────────────────────────┼──────────────────┘        │
│                                           │                           │
│   ┌───────────────────────────────────────┼──────────────────┐        │
│   │                    ONLINE PREDICTION   │                  │        │
│   │                                       ▼                  │        │
│   │  ┌──────────────┐         ┌──────────────────────────┐  │        │
│   │  │ Real-time    │────────►│ GRU Predictor            │  │        │
│   │  │ Traffic      │         │ (30-sec ahead forecast)  │  │        │
│   │  │ Metrics      │         └───────────┬──────────────┘  │        │
│   │  └──────────────┘                     │                  │        │
│   │                                       ▼                  │        │
│   │                      ┌────────────────────────────┐     │        │
│   │                      │ Resource Allocation Model  │     │        │
│   │                      │      R = α·x + β           │     │        │
│   │                      └────────────┬───────────────┘     │        │
│   │                                   │                      │        │
│   │                                   ▼                      │        │
│   │               ┌───────────────────────────────────┐     │        │
│   │               │      ONLINE CONTROLLERS            │     │        │
│   │               │  ┌─────────────┐ ┌─────────────┐  │     │        │
│   │               │  │ Routing     │ │ Cluster     │  │     │        │
│   │               │  │ Controller  │ │ Controller  │  │     │        │
│   │               │  └──────┬──────┘ └──────┬──────┘  │     │        │
│   │               └─────────┼───────────────┼─────────┘     │        │
│   │                         │               │                │        │
│   └─────────────────────────┼───────────────┼────────────────┘        │
│                             │               │                         │
│   ┌─────────────────────────┼───────────────┼────────────────┐        │
│   │            INFRASTRUCTURE               │                │        │
│   │                         ▼               ▼                │        │
│   │   ┌─────────────────────────────────────────────────┐   │        │
│   │   │              TRAFFIC ROUTER (HAProxy)            │   │        │
│   │   └─────────────┬───────────────────────┬───────────┘   │        │
│   │                 │                       │                │        │
│   │                 ▼                       ▼                │        │
│   │   ┌─────────────────────┐   ┌─────────────────────┐     │        │
│   │   │   KUBERNETES (K3s)  │   │     SERVERLESS      │     │        │
│   │   │   • Cost-effective  │   │     (Knative)       │     │        │
│   │   │   • Always warm     │   │   • Instant scale   │     │        │
│   │   │   • Baseline load   │   │   • Burst handling  │     │        │
│   │   └─────────────────────┘   └─────────────────────┘     │        │
│   │                                                          │        │
│   └──────────────────────────────────────────────────────────┘        │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 3.4 Implementation Method (Metode Implementasi)

### 3.4.1 Workload Predictor

**GRU Architecture:**

```
Input: Time-series window (e.g., 60 seconds of RPS data)
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

**Training Configuration:**
- **Optimizer**: Adam
- **Loss Function**: Mean Squared Error (MSE)
- **Batch Size**: 32
- **Epochs**: 100 (with early stopping)
- **Validation Split**: 15%

### 3.4.2 Resource Allocation

**Linear Resource Model:**

$$R = \alpha \cdot x + \beta$$

Where:
- $R$: Required CPU resources (millicores)
- $x$: Predicted traffic (requests/second)
- $\alpha$: Resource per request coefficient
- $\beta$: Base resource overhead

**OLS (Ordinary Least Squares) Tuning:**

The coefficients $\alpha$ and $\beta$ are derived using linear regression on historical data:

```python
from sklearn.linear_model import LinearRegression

# X: Historical traffic data
# y: Historical resource usage

model = LinearRegression()
model.fit(X, y)

alpha = model.coef_[0]
beta = model.intercept_
```

**Online Coefficient Correction:**

Based on prediction error feedback:
```
α_new = α_old + learning_rate * error
β_new = β_old + learning_rate * error
```

### 3.4.3 Online Controller

The online controller consists of two components:

#### 3.4.3.1 Routing Controller

**Algorithm 1: Routing Controller (Proposed)**

```pseudocode
Algorithm 1: Routing Controller
────────────────────────────────────────────────────────────────

Variables:
  reroute_traffic ← False
  violation_timer ← 0
  compliance_timer ← 0

repeat:
  // Get current metrics
  tail_latency ← GetTailLatency()      // p99 latency
  CPU_usage ← GetCPUUsage()
  
  // Check SLO compliance
  if tail_latency > SLO then
    violation_timer ← violation_timer + 1
    compliance_timer ← 0
  else
    compliance_timer ← compliance_timer + 1
    violation_timer ← 0
  end if
  
  // Make routing decision
  if violation_timer >= 5 AND not reroute_traffic then
    RerouteToServerless()              // Start using serverless
    reroute_traffic ← True
  else if compliance_timer >= 5 AND reroute_traffic then
    RerouteToKubernetes()              // Return to K8s only
    reroute_traffic ← False
  end if
  
  wait(1)  // Delay for 1 second

until forever
```

**Key Parameters:**
- **SLO Threshold**: 200ms (p99 latency target)
- **Violation Timer**: 5 seconds (consecutive violations before rerouting)
- **Compliance Timer**: 5 seconds (consecutive compliance before returning to K8s)

#### 3.4.3.2 Cluster Controller

The cluster controller manages Kubernetes resource scaling based on predicted workload:

```pseudocode
Algorithm 2: Cluster Controller
────────────────────────────────────────────────────────────────

Variables:
  current_resources
  prediction_interval ← 30 seconds

repeat:
  // Get prediction
  predicted_load ← GetGRUPrediction()
  
  // Calculate required resources
  required_resources ← α * predicted_load + β
  
  // Apply scaling with buffer
  target_resources ← required_resources * 1.2  // 20% buffer
  
  // Scale cluster
  if target_resources > current_resources then
    ScaleUp(target_resources - current_resources)
  else if target_resources < current_resources * 0.8 then
    ScaleDown(current_resources - target_resources)
  end if
  
  current_resources ← GetCurrentResources()
  
  wait(prediction_interval)

until forever
```

---

## 3.5 Evaluation Plan (Rencana Evaluasi)

### 3.5.1 Traffic Predictor Evaluation

**Metrics:**

1. **RMSE (Root Mean Square Error)**
   $$RMSE = \sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i - \hat{y}_i)^2}$$

2. **MAE (Mean Absolute Error)**
   $$MAE = \frac{1}{n}\sum_{i=1}^{n}|y_i - \hat{y}_i|$$

3. **MAPE (Mean Absolute Percentage Error)**
   $$MAPE = \frac{100\%}{n}\sum_{i=1}^{n}\left|\frac{y_i - \hat{y}_i}{y_i}\right|$$

**Target Performance:**
- RMSE < 10% of average traffic
- MAE < 5% of average traffic

### 3.5.2 Router and Scaling Evaluation

**Performance Metrics:**

| Metric | Description | Target |
|--------|-------------|--------|
| p50 Latency | Median response time | < 50ms |
| p95 Latency | 95th percentile | < 100ms |
| p99 Latency | 99th percentile (tail) | < 200ms |
| Error Rate | Failed requests | < 0.1% |
| Throughput | Requests per second | No degradation |

**Resource Metrics:**

| Metric | Description | Target |
|--------|-------------|--------|
| CPU Utilization | Average CPU usage | 60-80% |
| Memory Utilization | Average memory usage | < 80% |
| Scale Events | Number of scaling operations | Minimize |

**Cost Metrics:**

| Metric | Description |
|--------|-------------|
| K8s Cost | Resource hours × unit cost |
| Serverless Cost | Invocations × execution time × unit cost |
| Total Cost | K8s Cost + Serverless Cost |

**Evaluation Scenarios:**

1. **Baseline (K8s Only)**: All traffic to Kubernetes
2. **Baseline (Serverless Only)**: All traffic to serverless
3. **Hybrid (Proposed)**: Intelligent routing with prediction
4. **Hybrid (No Prediction)**: Reactive routing only

---

## 3.6 Report Writing (Penulisan Laporan)

The thesis report will include:

1. **Introduction**: Problem background and motivation
2. **Literature Review**: Related work and theoretical foundation
3. **Methodology**: Detailed system design and implementation
4. **Results**: Experimental evaluation and analysis
5. **Discussion**: Findings interpretation and limitations
6. **Conclusion**: Summary and future work

---

## 3.7 Research Schedule (Jadwal Penelitian)

**Table 3-2: Research Timeline**

| No | Activity | M1 | M2 | M3 | M4 | M5 | M6 |
|----|----------|:--:|:--:|:--:|:--:|:--:|:--:|
| 1 | Literature Study | ■ | ■ | | | | |
| 2 | Data Collection | | ■ | | | | |
| 3 | System Design | | ■ | ■ | ■ | | |
| 4 | Implementation and Testing | | | ■ | ■ | ■ | |
| 5 | Journal Writing | | | | | ■ | |
| 6 | Report Writing | | ■ | ■ | ■ | ■ | ■ |

**Legend:**
- M1-M6: Month 1 through Month 6
- ■: Activity scheduled for that month

**Milestones:**
- **Month 2**: Data collection complete, system design started
- **Month 3**: Prototype implementation
- **Month 4**: Core system complete
- **Month 5**: Evaluation and journal submission
- **Month 6**: Final thesis report
