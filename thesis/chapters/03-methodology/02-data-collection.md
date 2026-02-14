## 3.2 Data Collection (Pengumpulan Data)

This section describes (i) how training and validation datasets are constructed for the GRU workload predictor and (ii) how real HTTP traces (ClarkNet and Calgary) are transformed into **trace-driven replay workloads** for the evaluation of the hybrid Kubernetes–serverless system. The objective is full reproducibility: all transformations are deterministic, parameterized, and can be re-executed from raw inputs.

### 3.2.1 Primary Training Data: Synthetic Workload Patterns

The GRU prediction model is trained on synthetically generated traffic patterns designed to represent common cloud workload characteristics. Four pattern types are combined to produce the training dataset:

- **Diurnal cycles**: Sinusoidal traffic patterns simulating daily usage peaks and troughs.
- **Bursty spikes**: Short-duration traffic surges injected at random intervals.
- **Gradual ramps**: Linearly increasing traffic segments representing organic growth or planned load increases.
- **Baseline noise**: Gaussian random fluctuations added to all patterns to simulate measurement variability.

These components are superimposed and scaled to produce time-series sequences of requests per second (RPS). Synthetic training is selected because it (1) provides controlled labels for supervised learning, (2) enables arbitrary dataset sizes, and (3) allows explicit inclusion of ramps and spikes that are not consistently present in historical traces.

**Data Processing Pipeline (Synthetic Training):**

```text
Pattern Definition → Traffic Simulation → 1s RPS Time Series → Sliding Windows → Train/Val/Test Split
```

**Processing steps (reproducible):**
1. **Generate 1-second RPS series** by combining the four components with a fixed random seed to ensure reproducibility.
2. **Windowing:** Construct sliding-window samples using an input window length of **60 seconds** (last 60 RPS points) and a prediction horizon of **30 seconds** ahead (target label).
3. **Split:** Use temporally ordered split to prevent leakage: Training = 70%, Validation = 15%, Test = 15%.

All generator parameters (amplitudes, spike probability, ramp slope range, noise variance, seed) are stored as a configuration file committed alongside the experiment code.

### 3.2.2 Reference Data: Real HTTP Traces (ClarkNet and Calgary)

ClarkNet and Calgary HTTP trace datasets serve two roles:

1. **Baseline comparison for predictor generalization** (offline evaluation of prediction accuracy).
2. **Trace-driven replay** (online system evaluation under realistic, non-synthetic temporal patterns).

These datasets are **not used for training** to avoid learning historical idiosyncrasies and to preserve a strict separation between training data (synthetic) and external validation data (real traces).

**Table 3-1: Reference Dataset Characteristics**

| Dataset | Requests | Time Period | Source | Usage in This Thesis |
|---------|----------|-------------|--------|----------------------|
| ClarkNet | ~2M | Aug–Sep 1995 | ClarkNet WWW Server | (i) Predictor baseline comparison, (ii) Trace-driven replay workload |
| Calgary | ~2M | Oct 1994 | University of Calgary CS | Predictor baseline comparison; optional secondary replay workload |

**Table 3-2: Dataset Request Examples**

| Dataset | Request Example |
|---------|-----------------|
| University of Calgary | `local - - [24/Oct/1994:13:41:41 -0600] "GET index.html HTTP/1.0" 200 150` |
| ClarkNet | `204.249.225.59 - - [28/Aug/1995:00:00:34 -0400] "GET /pub/... HTTP/1.0" 200 3542` |

### 3.2.3 Real Trace Processing for Predictor Baseline Comparison (Offline)

For offline predictor comparison (Section 3.5.1), the traces are converted into an RPS time series and then passed through the same windowing pipeline as the synthetic dataset. This provides a direct comparison of GRU accuracy on out-of-distribution workloads.

**Offline Trace Pipeline (baseline comparison):**

```text
Raw HTTP Logs → CLF Parsing → Timestamp Extraction → Aggregation → RPS Time Series → Sliding Windows
```

**Aggregation rule (offline comparison):**
- Traces are aggregated at **5-minute** resolution for stability of the baseline comparison plots and error metrics due to the lower temporal resolution of historical access logs.
- The GRU windowing is applied consistently after aggregation.

### 3.2.4 Trace-Driven Replay Workload Generation (Beban Replikasi Berbasis Trace)

To evaluate the full hybrid system under realistic demand dynamics, the ClarkNet/Calgary traces are transformed into a **30-second RPS schedule** and then executed using **k6** with the `ramping-arrival-rate` executor. This produces a time-varying open-loop workload that approximates the trace's temporal intensity while remaining reproducible and controllable.

#### (a) Canonical Replay Representation: 30-Second RPS Buckets

The replay schedule is defined as a time series of (timestamp, RPS) pairs where each entry represents the start time of a **30-second bucket** and the average requests-per-second during that bucket.

**Why 30 seconds?**
- The GRU prediction horizon is **30 seconds** (Section 3.4.1).
- The routing daemon control loop runs every **15 seconds**, allowing two control decisions per replay bucket.
- 30-second buckets reduce noise while preserving burst and ramp structure.

#### (b) Processing Pipeline

The traces are stored as Parquet files (columnar format) for deterministic and fast reprocessing. The pipeline proceeds as follows:

1. **Parse CLF log lines** into a structured table with timestamps converted to UTC.
2. **Bucket by 30-second windows**: group timestamps into fixed-width 30-second windows and compute `RPS = request_count / 30` for each bucket.
3. **Fill missing buckets** with RPS = 0 to preserve original idle periods.
4. **Apply optional scaling factor** `g` to fit testbed capacity: `RPS_scaled = g × RPS_raw`. The scaling factor is recorded and kept constant across all scenarios within the same experimental phase.
5. **Trim to experiment duration**: select a contiguous time span (e.g., first 20 minutes), recorded in the experiment manifest.

#### (c) k6 Stage Generation

Each 30-second bucket becomes one k6 `ramping-arrival-rate` stage:

```javascript
// Example generated stages
stages: [
  { duration: "30s", target: 42 },
  { duration: "30s", target: 55 },
  { duration: "30s", target: 10 },
  // ...
]
```

**k6 executor configuration:**
- `executor`: `"ramping-arrival-rate"` (open arrival process: targets a request rate independent of server response time)
- `timeUnit`: `"1s"`
- `preAllocatedVUs`: fixed (e.g., 200) to avoid allocation overhead during replay
- `maxVUs`: fixed (e.g., 400) to prevent unbounded generator growth

All derived artifacts are stored for reproducibility: `trace_raw.parquet` (structured trace), `trace_30s_rps.csv` (bucketed schedule), and `k6_stages.json` (exact replay stages used).

**Trace-driven replay pipeline summary:**

```text
Raw HTTP Logs → Parse → Parquet → 30s Bucketing (RPS) → Scale → k6 Stages → Online Replay
```

#### (d) Workload Endpoint and Determinism Controls

All trace-driven replay and synthetic load tests target the `/work?duration_ms=5` endpoint rather than a lightweight health check. This endpoint performs a deterministic CPU busy-loop for 5 milliseconds per request, ensuring:

1. **Meaningful per-request processing time** that triggers autoscaler responses (both HPA CPU-based and KPA concurrency-based).
2. **Predictable saturation behavior** when combined with `GOMAXPROCS=1` (single Go runtime thread per pod), creating a theoretical maximum of 200 RPS per replica with practical saturation at ~145 RPS.
3. **Linear capacity scaling** where each additional replica adds approximately 145 RPS of capacity, enabling the resource allocation model ($R = \alpha \cdot x + \beta$) to operate with calibrated coefficients ($\alpha \approx 0.0069$, $\beta = 0$).

The `/health` endpoint is retained exclusively for Kubernetes liveness/readiness probes and HAProxy backend health checks.

Calgary dataset replay is excluded from online system experiments due to insufficient request density (mean 0.02 RPS at 30-second granularity). Calgary is used only for offline GRU prediction accuracy comparison (Section 3.5.1).
