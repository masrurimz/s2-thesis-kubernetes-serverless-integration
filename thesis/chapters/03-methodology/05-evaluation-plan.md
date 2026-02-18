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

Four scenarios are defined to compare platform-native autoscaling baselines against the custom hybrid control plane, and to isolate the value of GRU prediction within the hybrid architecture. All scenarios route traffic through HAProxy to eliminate data-path confounds. S1 and S2 use platform-native autoscaling (HPA and KPA respectively); S3 and S4 use the custom control plane (Algorithms 1+2).

**Table 3-3: Evaluation Scenarios**

| Scenario | Name | Routing | Autoscaling | Scaling Signal | GRU |
|----------|------|---------|-------------|----------------|-----|
| S1 | K8s + HPA Baseline | 100% K8s, Knative weight=0 | HPA (native CPU-based) | CPU utilization | Off |
| S2 | Knative-Only (KPA) | 100% Knative via HAProxy | KPA (concurrency-based, scale-to-zero) | Request concurrency | Off |
| S3 | Hybrid Reactive | Dynamic K8s↔Knative | Algorithm 1 (routing) + Algorithm 2 (replicas, reactive) | $x_{obs}$ | Off |
| S4 | Hybrid Predictive | Dynamic K8s↔Knative | Algorithm 1 (routing) + Algorithm 2 (replicas, predictive) | $x_{pred}$ | On |

Where $x_{obs}$ = mean observed RPS over the last 30 seconds and $x_{pred}$ = GRU 30-second-ahead forecast.

**Scenario Comparisons:**

- **S1 vs S2**: Compares **platform-native autoscaling baselines** — Kubernetes HPA (CPU-based, persistent pods) versus Knative KPA (concurrency-based, scale-to-zero). This establishes the performance envelope of each platform operating independently.
- **S3 vs S1/S2**: Evaluates whether the **hybrid reactive control plane** (Algorithm 1 routing + Algorithm 2 scaling) improves over either baseline alone, by combining Kubernetes steady-state capacity with serverless burst absorption.
- **S3 vs S4**: Isolates the **value of GRU prediction** — both use hybrid routing and Algorithm 2 scaling; the only difference is the scaling signal: reactive ($x_{obs}$) versus predictive ($x_{pred}$) and the PREDICTIVE trigger in Algorithm 1.

**Autoscaler Mutual Exclusion Constraint:** Infrastructure validation (Section 3.5.3, Phase A0) confirmed that Kubernetes HPA and direct replica scaling via `kubectl scale` conflict: HPA overrides manual replica changes after its stabilization window (~5 minutes). Therefore, S3 and S4 require HPA to be deleted before Algorithm 2 can safely control replicas. This constraint is enforced in the per-run reset procedure (Section 3.5.4).

### 3.5.3 Evaluation Phases

#### Phase A0: Infrastructure and Autoscaler Validation (Validasi Infrastruktur)

Pre-experiment validation tests to confirm that testbed mechanisms function correctly and to inform scenario design decisions:

- **T0 (Cluster Health):** Verify all nodes Ready, metrics-server operational, Prometheus targets active, data-plane reachable to both K8s and Knative backends.
- **T1 (Load Generation):** Confirm k6 `constant-arrival-rate` and `ramping-arrival-rate` executors reach target rates with <2% errors.
- **T2 (HPA Validation):** Create HPA for the test application, drive CPU load, observe scale-up and scale-down. Validates that HPA functions correctly on k3d for the S1 baseline.
- **T3 (HPA vs kubectl scale):** Test whether HPA and manual `kubectl scale` coexist or conflict on the same Deployment. This test directly determines the scaling architecture for S3/S4.
- **T4 (KPA Validation):** Verify Knative KPA scales from zero under load and returns to zero after idle. Measure cold start latency. Validates the S2 baseline.

**Key validated findings:**
- HPA scales 2→10 replicas in ~45 seconds under CPU load; scales down in ~7.5 minutes (T2).
- HPA overrides `kubectl scale` after its 5-minute stabilization window (T3). **This mandates that S3/S4 delete HPA before Algorithm 2 can operate.**
- KPA cold start: ~1.2 seconds. Scale-up 1→7 pods under concurrent load; scale-to-zero ~60 seconds after idle (T4).
- KPA uses concurrency-based scaling, requiring workloads with meaningful processing time (not just lightweight health checks) to trigger scaling (T4).
- All system evaluation experiments (Phases A1, B, C) use the `/fib?n=32` endpoint, which computes recursive Fibonacci numbers as a CPU-intensive workload. Unlike a busy-loop (`/work`), recursive Fibonacci yields to the Go runtime scheduler between function calls, allowing health checks, metrics reporting, and Prometheus scraping to operate correctly even under full CPU saturation. Combined with `GOMAXPROCS=1` (single Go runtime thread), this creates predictable per-replica capacity (~60 RPS) and linear queuing under overload.

> **Workload recalibration note:** Two iterations were required to reach the final parameterization:
> 1. **v1 (`/work?duration_ms=5`):** ~145 RPS single-pod saturation. ClarkNet peak (164 RPS) only reached 1.13× saturation — insufficient for multi-replica scaling.
> 2. **v2 (`/work?duration_ms=10`):** ~50 RPS saturation. However, the busy-loop monopolized the single Go thread (`GOMAXPROCS=1`), preventing health checks from responding under overload. Kubernetes restarted pods before HPA could react, and CPU utilization was reported as ~1% (the runtime could not schedule metrics collection).
> 3. **v3 (`/fib?n=32`, final):** ~60 RPS saturation. Recursive Fibonacci cooperates with the Go scheduler, enabling correct CPU reporting (~400-500% under load), stable health checks, and proper HPA/Algorithm 2 scaling. At this parameterization, 85% of ClarkNet trace stages exceed single-pod capacity (peak at 2.73× saturation requiring ~4 replicas, mean at 1.22× requiring ~2 replicas).

#### Phase A1: Mechanism Validation (Validasi Mekanisme)

A controlled ramp-load experiment to validate that individual system mechanisms function correctly:

- **Workload profile (k6 synthetic):** Baseline (60s @ 20 RPS) → Ramp (60s @ 20→100 RPS) → Peak (120s @ 100 RPS). All requests target `/fib?n=32` to ensure non-trivial, scheduler-cooperative CPU processing.
- **Purpose:** Confirm that weight shifting, serverless engagement, SLO monitoring, PREDICTIVE action triggering, Kubernetes replica scaling via Algorithm 2, and traffic return to Kubernetes all operate as designed.
- **Success criteria:**
  1. In S4, Algorithm 1 engages Knative before sustained SLO violation during the ramp (predictive trigger).
  2. Algorithm 2 issues a scale-up toward the computed $R_{target}$.
  3. After replicas are ready and healthy, traffic shifts back toward Kubernetes and Knative usage decreases.

#### Phase B: Replicated Comparison with Trace-Driven Workload (Perbandingan dengan Beban Trace)

The primary comparative evaluation with statistical rigor, using realistic time-varying workload derived from ClarkNet trace replay:

- **Workload:** ClarkNet trace-driven replay using 30-second buckets and k6 `ramping-arrival-rate` stages (Section 3.2.4). Replay duration per run is fixed (e.g., 20 minutes) and recorded in the run manifest. A replay scaling factor $g$ is applied to fit testbed capacity and kept constant across all scenarios. Based on single-replica saturation calibration (~60 RPS for `/fib?n=32` with `GOMAXPROCS=1`), the scaling factor is set to $g = 33$, producing a peak replay rate of ~164 RPS (2.73× saturation, requiring ~4 replicas) and mean of ~73 RPS (1.22× saturation, requiring ~2 replicas). At this parameterization, 85% of ClarkNet trace stages exceed single-pod capacity, ensuring that scaling and routing mechanisms are exercised throughout each run.
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
  1. **Single burst:** 60s @ 30 RPS → 30s @ 170 RPS → 180s @ 30 RPS. Burst peak chosen relative to calibrated single-replica saturation (~145 RPS) to stress the system without total collapse (1.17× saturation).
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
5. **Application workload configuration:** The test application exposes a `/fib?n=32` endpoint with `GOMAXPROCS=1` to create CPU-intensive, scheduler-cooperative processing (~8ms per call). CPU limit is 500m, memory limit 128Mi. Each replica saturates at approximately 60 RPS.

#### (B) Per-Run Reset Procedure

Before each run:

1. **Reset autoscaler state (scenario-dependent):**
   - **S1 (HPA):** Ensure HPA exists with target CPU utilization (50%), minReplicas=1, maxReplicas=10. Wait for HPA to report metrics (avoids `<unknown>` targets). Do not use `kubectl scale` — HPA controls replicas.
   - **S2 (Knative KPA):** Ensure Knative service has minScale=0, maxScale=10. Wait until Knative pods scale to zero (no active requests).
   - **S3/S4 (Algorithm 2):** **Delete HPA** for the target Deployment if present. Scale to baseline replicas via `kubectl scale` (1 replica). This ensures Algorithm 2 is the sole replica controller.
2. **Reset HAProxy weights** to scenario baseline (100/0 for S1; 0/100 for S2; scenario-defined for S3/S4).
3. **Reset routing daemon state:** restart with scenario-specific flags (Algorithm 1/2 enabled/disabled, GRU on/off).
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

Cost analysis uses three billing models (Lambda Provisioned Concurrency, Cloud Run Always-Allocated, EC2 Node-Hours) applied to actual measured resource consumption from experiments. Production cost projections use real cloud node capacity (t3.medium, 1.8 vCPU allocatable) rather than the stress-harness constraint (400m allocatable). See Section 4.4 for methodology details.

### 3.5.6 Post-Processing and Statistical Analysis (Pengolahan Data)

1. **Alignment:** All time-series metrics are aligned to the run window $[t_{start}, t_{end}]$ using UTC timestamps.
2. **Event derivation:** Routing event = change in HAProxy backend weights. Scaling event = change in deployment `.spec.replicas`.
3. **Latency aggregation:** k6 latency percentiles are computed per run; Prometheus latency (if collected from HAProxy) is used as secondary corroboration.
4. **Statistical tests (Phase B):** Welch's t-test and Mann-Whitney U for scenario comparisons, bootstrap confidence intervals for median/p99 differences, Cohen's d for effect size.
5. **Reporting:** All exclusions (e.g., failed runs) are documented with a reproducible reason.

### 3.5.7 Threats to Validity (Ancaman terhadap Validitas)

The experimental evaluation is subject to the following known threats, documented proactively:

1. **Localhost routing bias (Critical):** The k3d single-node testbed runs all components (HAProxy, K3s, Knative) on localhost, eliminating network latency between components. This limits the interpretability of absolute performance comparisons between scenarios, as production deployments would incur real network overhead. Additionally, the k3d environment uses Docker containers as cluster nodes, which may exhibit different resource scheduling behavior compared to bare-metal or cloud VM nodes.

2. **Trace age and representativeness:** ClarkNet and Calgary are historical traces (1994–1995). They represent realistic temporal variability but may not match modern application semantics (TLS, dynamic content, microservices).

3. **Replay fidelity limitations:** Trace-driven replay preserves request intensity over time but does not reproduce original client think times, cache behaviors, or request mix unless explicitly modeled.

4. **Load generator saturation:** k6 may become CPU-limited at high target rates, reducing achieved throughput and biasing results. Generator resource usage must be monitored and reported.

5. **Cold start variability in Knative:** Serverless cold starts may vary between runs due to image caching and node state. Run order randomization and explicit reset procedures mitigate but cannot fully eliminate this.

6. **Model coefficient drift:** The resource allocation coefficients ($\alpha, \beta$) are calibrated on the testbed; changes in container limits, application version, or node resources require recalibration to keep scaling behavior comparable.

7. **Single-threaded application constraint:** The test application is configured with `GOMAXPROCS=1`, restricting each pod to single-threaded request processing via recursive Fibonacci computation (`/fib?n=32`, ~8ms per call, ~60 RPS saturation). Unlike a busy-loop, Fibonacci yields to the Go scheduler, enabling correct CPU reporting and health check responsiveness. This creates reproducible saturation behavior but does not represent typical multi-threaded web applications. Results should be interpreted in the context of this controlled bottleneck.

8. **Implementation bug invalidation:** Early Phase B and Phase C experiment data (prior to 2026-02-14) were invalidated due to three implementation bugs in the SLO monitor, Algorithm 1 priority ordering, and Prometheus scraping configuration. All reported results are from post-fix experiments.

9. **GRU server availability:** The prediction server must be confirmed running before S4 experiments to ensure the predictive mechanism is active. Infrastructure health checks are performed at experiment start.

10. **Sample size:** With $n = 5$ runs per scenario, statistical power is limited for detecting moderate effect sizes. Results are interpreted as mechanism validation rather than definitive superiority claims.

11. **Autoscaler mutual exclusion:** HPA and Algorithm 2 cannot coexist on the same Deployment (validated in Phase A0). This means S1 (HPA) and S3/S4 (Algorithm 2) use fundamentally different scaling mechanisms, which may confound direct performance comparisons between native and custom autoscaling approaches.

13. **Artificial node capacity constraint (Critical).** Workload nodes use `system-reserved=15600m` (leaving ~400m allocatable) to force Cluster Autoscaler triggers within experiment durations. This is a deliberate stress-harness technique to exercise autoscaling mechanisms but means: (a) CA triggers at lower loads than production, (b) pod scheduling constraints create artificial resource starvation (S1 desired 9 replicas but only 6 schedulable), and (c) observed node counts do not represent production sizing. Cost projections are computed separately using production node capacity (t3.medium, 1.8 vCPU allocatable).

12. **Workload parameterization sensitivity:** The per-request computation directly determines single-pod capacity and thus the scaling behavior observed. Three iterations were required: (a) `/work?duration_ms=5` (~145 RPS) was too light for scaling; (b) `/work?duration_ms=10` (~50 RPS) blocked the Go scheduler, preventing health checks and CPU reporting; (c) `/fib?n=32` (~60 RPS) uses scheduler-cooperative CPU work that enables correct HPA and Algorithm 2 behavior. The final parameterization ensures the ClarkNet trace exercises multi-replica scaling across all scenarios (peak at 2.73× saturation requiring ~4 replicas, mean at 1.22× requiring ~2 replicas). Results are specific to this parameterization and may differ at other service times.
