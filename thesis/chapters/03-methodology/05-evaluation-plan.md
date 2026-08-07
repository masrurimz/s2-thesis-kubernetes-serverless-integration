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

Four scenarios compare platform-native baselines with the custom hybrid controller. S1 and S2 use HPA and KPA; S3 and S4 use Algorithms 1+2. In S3/S4, routing uses observed capacity and tail latency, while the scaling signal differs: observed load for S3 and the confidence-gated GRU forecast for S4.

**Table 3-3: Evaluation Scenarios**

| Scenario | Name | Routing | Autoscaling | Scaling Signal | GRU |
|----------|------|---------|-------------|----------------|-----|
| S1 | K8s + HPA Baseline | 100% K8s, Knative weight=0 | HPA (native CPU-based) | CPU utilization | Off |
| S2 | Knative-Only (KPA) | 100% Knative via HAProxy | KPA (concurrency-based, scale-to-zero) | Request concurrency | Off |
| S3 | Hybrid Reactive | Dynamic K8s↔Knative | Algorithm 1 (routing) + Algorithm 2 (replicas, reactive) | $x_{obs}$ | Off |
| S4 | Hybrid Predictive | Dynamic K8s↔Knative | Algorithm 1 (routing) + Algorithm 2 (replicas, predictive) | $x_{pred}$ | On |

Where $x_{obs}$ is mean observed RPS over the last 30 seconds and $x_{pred}$ is the final 9-step GRU forecast (9 × 15 seconds = 135 seconds) used by Algorithm 2 for replica scaling. GRU output does not directly set HAProxy routing weights.

**Scenario Comparisons:**

- **S1 vs S2**: Compares **platform-native autoscaling baselines** — Kubernetes HPA (CPU-based, persistent pods) versus Knative KPA (concurrency-based, scale-to-zero). This establishes the performance envelope of each platform operating independently.
- **S3 vs S1/S2**: Evaluates whether the **hybrid reactive control plane** (Algorithm 1 routing + Algorithm 2 scaling) improves over either baseline alone, by combining Kubernetes steady-state capacity with serverless burst absorption.
- **S3 vs S4**: Isolates the value of GRU-assisted scaling—both use hybrid routing and Algorithm 2; the only difference is the scaling signal, reactive ($x_{obs}$) versus predictive ($x_{pred}$). Routing remains observed-load/capacity-driven in both.

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
- All system evaluation experiments use the code-verified `/fib?n=33` endpoint, which computes recursive Fibonacci as scheduler-cooperative CPU work. Combined with `GOMAXPROCS=1`, this produces approximately 60 RPS measured saturation per replica. The final calibration uses $r_{saturation}=33.3$, target CPU utilization 0.5, $r_{effective}=16.65$, and $\alpha=1/r_{effective}\approx0.0601$ for Algorithm 2.

> **Workload recalibration note:** Earlier `/work?duration_ms=5` (~145 RPS) and `/work?duration_ms=10` (~50 RPS) busy-loop parameterizations are invalidated. The final `/fib?n=33` endpoint yields scheduler-cooperative processing and stable health checks. Code-verified calibration uses $r_{saturation}=33.3$, $r_{effective}=16.65$, and $\alpha=1/r_{effective}$; the measured endpoint saturation is approximately 60 RPS per replica.

#### Phase A1: Mechanism Validation (Validasi Mekanisme)

A controlled ramp-load experiment to validate that individual system mechanisms function correctly:

- **Workload profile (k6 synthetic):** Baseline (60s @ 20 RPS) → Ramp (60s @ 20→100 RPS) → Peak (120s @ 100 RPS). Requests target `/fib?n=33` to ensure non-trivial, scheduler-cooperative CPU processing.
- **Purpose:** Confirm weight shifting, serverless engagement, SLO monitoring, PREDICTIVE action logging, Algorithm 2 replica scaling, and traffic return to Kubernetes.
- **Success criteria:**
  1. In S4, Algorithm 1 engages Knative before sustained SLO violation during the ramp (predictive trigger).
  2. Algorithm 2 issues a scale-up toward the computed $R_{target}$.
  3. After replicas are ready and healthy, traffic shifts back toward Kubernetes and Knative usage decreases.

#### Phase B: Replicated Comparison with Trace-Driven Workload (Perbandingan dengan Beban Trace)

The primary comparative evaluation with statistical rigor, using realistic time-varying workload derived from ClarkNet trace replay:

- **Workload:** ClarkNet trace-driven replay using 30-second buckets and k6 `ramping-arrival-rate` stages (Section 3.2.4). The final model horizon is 9 × 15 seconds = 135 seconds. The code-verified final endpoint is `/fib?n=33`; its measured saturation is approximately 60 RPS per replica, while calibration uses $r_{saturation}=33.3$, $r_{effective}=16.65$, and $\alpha=1/r_{effective}$.
- **Replication:** The definitive H2 study uses a **counterbalanced paired design with n=5 pairs (10 runs total)** comparing S3 and S4. Each pair runs both treatments in counterbalanced order; the primary metric is paired p99 latency. A separate n=1 diagnostic executes all four scenarios (S1–S4).
- **Randomization:** Pair order is counterbalanced to control temporal drift and node-state effects. Per-run reset and treatment-fidelity gates are recorded in each manifest.
- **Cool-down:** 60-second pause between consecutive runs plus explicit system reset (see Section 3.5.4).

**Statistical Analysis:**

| Test | Purpose | Interpretation |
|------|---------|----------------|
| Paired permutation test | Pre-specified primary p99 comparison for S3/S4 | p=0.0304, significant at α=0.05 |
| Paired 95% CI | Uncertainty for S4−S3 p99 difference | [−100.9, −26.2] ms |
| Paired Cohen's d | Effect size | d=−1.26 (large) |
| Corrected secondary p-values | p95 and SLO after multiplicity correction | p=0.1216; descriptive only |

The n=1 S1–S4 diagnostic is descriptive. The paired n=5 H2 result uses the pre-specified primary p99 test; secondary p95 and SLO results are reported with the correction caveat.

**Data Quality and Run Validity Gates:**

- Outlier detection using the criterion p99 < 15ms (indicating measurement artifact rather than genuine system behavior).
- Excluded runs are documented with explicit justification.
- Statistics are recomputed on the clean dataset.
- **Multi-node gate (S1/S3/S4):** run is marked invalid if no dynamic-node provisioning events are captured, if no workload pod is observed on dynamic nodes, or if workload pods do not span at least two nodes.
- **Serverless gate (S2/S3/S4):** run is marked invalid if no Knative pod placement evidence is captured.
- Gate outcomes are reported explicitly in the run report before inferential statistics.

#### Phase C: Dynamic Burst Validation (Validasi Lonjakan Dinamis)

Stress the system with controlled, repeatable bursts to quantify responsiveness and stability beyond historical traces:

- **Workload profiles:**
  1. **Single burst:** 60s @ 30 RPS → 30s @ 170 RPS → 180s @ 30 RPS. The final `/fib?n=33` endpoint has approximately 60 RPS measured saturation per replica; code calibration uses $r_{saturation}=33.3$ and $r_{effective}=16.65$, so the burst exercises multi-replica scaling.
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
3. **Start the GRU prediction server** (FastAPI) and confirm its health endpoint responds.
4. **Start the routing daemon** with control interval = 15s, structured JSON logging, and Prometheus exporter enabled. The application workload is `/fib?n=33` with `GOMAXPROCS=1`, 500m CPU limit, and 128Mi memory limit.

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
| $/1M successful requests | Total cost normalized by successful output | Fair cross-scenario cost metric |
| $/1M SLO-compliant requests | Total cost normalized by SLO-compliant output | Fairness metric for service quality |
| Successful requests per USD | Output efficiency per cost | Throughput-cost fairness |

Cost analysis uses the unified AWS model (EKS + EC2 for the Kubernetes share, Lambda Provisioned Concurrency for the serverless share) applied to measured resource consumption. Production cost projections use real cloud node capacity (t3.medium, 1.8 vCPU allocatable) rather than the bounded Docker `--cpus` stress-harness nodes. Raw total cost is reported with the evidence tier; proxy costs are projected, not billed.

For Lambda sizing, execution time uses an explicit signal hierarchy to avoid under- or over-estimation in hybrid scenarios: (1) serverless-specific application duration from Knative-served successful requests; (2) scenario-level app duration for S2-only runs when serverless-specific splits are not needed; (3) CPU-derived fallback (`cpu_per_request_ms / 0.2 + 10ms`) only when app-duration signals are unavailable. Hybrid scenarios (S3/S4) must not use blended whole-scenario execution duration when serverless-specific signal is available. The analyzer reports whole-run totals (per 1200s run) and fairness-normalized metrics together.

### 3.5.6 Post-Processing and Statistical Analysis (Pengolahan Data)

1. **Alignment:** All time-series metrics are aligned to the run window $[t_{start}, t_{end}]$ using UTC timestamps.
2. **Event derivation:** Routing event = change in HAProxy backend weights. Scaling event = change in deployment `.spec.replicas`.
3. **Latency aggregation:** k6 latency percentiles are computed per run; Prometheus latency (if collected from HAProxy) is used as secondary corroboration.
4. **Statistical tests (Phase B):** Welch's t-test and Mann-Whitney U for scenario comparisons, bootstrap confidence intervals for median/p99 differences, Cohen's d for effect size.
5. **Cost post-processing:** Compute AWS totals from measured run-level consumption using the execution-time signal hierarchy above; emit both raw totals and fairness-normalized metrics.
6. **Reporting:** All exclusions (e.g., failed runs) are documented with a reproducible reason.

### 3.5.7 Threats to Validity (Ancaman terhadap Validitas)

The experimental evaluation is subject to the following known threats, documented proactively:

1. **Multi-node testbed and topology (Critical):** Final experiments use a bounded multi-node k3d testbed rather than the superseded single-node layout. Two static workload nodes and dynamically provisioned nodes are bounded with Docker `--cpus`; this exercises pending pods and node provisioning but does not reproduce cloud networking, VM boot, or availability-zone behavior.

2. **Trace age and representativeness:** ClarkNet and Calgary are historical traces (1994–1995). They represent realistic temporal variability but may not match modern application semantics (TLS, dynamic content, microservices).

3. **Replay fidelity limitations:** Trace-driven replay preserves request intensity over time but does not reproduce original client think times, cache behaviors, or request mix unless explicitly modeled.

4. **Load generator saturation:** k6 may become CPU-limited at high target rates, reducing achieved throughput and biasing results. Generator resource usage must be monitored and reported.

5. **Cold start variability in Knative:** Serverless cold starts may vary between runs due to image caching and node state. Run order randomization and explicit reset procedures mitigate but cannot fully eliminate this.

6. **Model coefficient drift:** The resource allocation coefficients ($\alpha, \beta$) are calibrated on the testbed; changes in container limits, application version, or node resources require recalibration to keep scaling behavior comparable.

7. **Single-threaded application constraint:** The test application uses code-verified `/fib?n=33` with `GOMAXPROCS=1`, restricting each pod to single-threaded recursive Fibonacci processing. Measured endpoint saturation is approximately 60 RPS per replica; calibration uses $r_{saturation}=33.3$, $r_{effective}=16.65$, and $\alpha=1/r_{effective}$. This is reproducible but not representative of all multi-threaded web applications.

8. **Implementation bug invalidation:** Early Phase B and Phase C experiment data (prior to 2026-02-14) were invalidated due to three implementation bugs in the SLO monitor, Algorithm 1 priority ordering, and Prometheus scraping configuration. All reported results are from post-fix experiments.

9. **GRU server availability:** The prediction server must be confirmed running before S4 experiments to ensure the predictive mechanism is active. Infrastructure health checks are performed at experiment start.

10. **Sample size and power:** H2 uses a counterbalanced paired design with n=5 pairs (10 runs) and a pre-specified primary p99 test. The separate four-scenario diagnostic is n=1 and directional; H1 is not treated as inferential evidence.

11. **Autoscaler mutual exclusion:** HPA and Algorithm 2 cannot coexist on the same Deployment (validated in Phase A0). This means S1 (HPA) and S3/S4 (Algorithm 2) use fundamentally different scaling mechanisms, which may confound direct performance comparisons between native and custom autoscaling approaches.

13. **Artificial node capacity constraint (Critical):** Workload nodes use Docker `--cpus=1.0` bounds and the infra node uses a bounded CPU budget to emulate cloud VM capacity. This replaces the invalidated `system-reserved=15600m` hack. The bounded stress harness exercises pending pods, dynamic-node provisioning, and serverless offload; node counts and delay are not production capacity or billed cost.

12. **Workload parameterization sensitivity:** Earlier `/work?duration_ms=5` and `/work?duration_ms=10` busy-loop bundles are invalidated. The final code-verified `/fib?n=33` endpoint is scheduler-cooperative with approximately 60 RPS measured saturation per replica; the calibration uses $r_{saturation}=33.3$, $r_{effective}=16.65$, and $\alpha=1/r_{effective}$. Results remain specific to this controlled workload.
