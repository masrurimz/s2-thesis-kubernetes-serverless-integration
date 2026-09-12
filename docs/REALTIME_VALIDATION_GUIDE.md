# Real-Time Hypothesis Validation Guide

This document explains how to perform actual experiments with real Prometheus metrics to validate H1, H2, and H3.

## Overview

The `thesis experiment validate-realtime` command validates H3 (GRU prediction adequacy) offline by loading the trained model; it needs no cluster. H1 and H2 require live experiments:
- Live runs use the experiment CLI (`run`, `paired-run`, `reproduce`) with k6 load against each scenario
- Metrics are collected from Prometheus and HAProxy during and after each run
- Post-hoc analysis runs through the analysis CLI (`hypotheses`, `cost`, `runs`, `mechanism`, `variance`)

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REAL-TIME VALIDATION FLOW                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. CHECK INFRASTRUCTURE                                                    │
│     ├── Prometheus: curl http://localhost:9090/-/healthy                     │
│     ├── K3s: kubectl get nodes                                               │
│     └── HAProxy: curl http://localhost:18404/stats                         │
│                                                                              │
│  2. RUN EXPERIMENT (per scenario, per run)                                   │
│     ├── Configure routing daemon for scenario (S1/S2/S3/S4)                  │
│     ├── Start k6 load test (steady/spike/endurance)                        │
│     ├── Collect Prometheus metrics every 15 seconds                       │
│     └── Stop after duration (default: 300 seconds)                         │
│                                                                              │
│  3. COLLECT METRICS                                                          │
│     ├── Latency: histogram_quantile(0.95, http_request_duration_seconds)    │
│     ├── Error Rate: rate(http_requests_total{status=~"5.."})               │
│     ├── Throughput: rate(http_requests_total)                                │
│     ├── K8s Pods: kube_pod_status_ready                                        │
│     └── Decisions: routing_decisions_total                                     │
│                                                                              │
│  4. STATISTICAL ANALYSIS                                                     │
│     ├── Run each scenario N times (default: 3)                               │
│     ├── Calculate mean, stddev, confidence intervals                         │
│     └── Perform significance testing (H1/H2 comparisons)                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

### 1. Infrastructure Running

```bash
# Converge the whole stack (clusters, HAProxy, Prometheus, node count), then check it
uv run thesis infra ensure
uv run thesis infra health

# Check Prometheus (deployed in the monitoring namespace, NodePort 30090)
kubectl port-forward svc/prometheus 9090:9090 -n monitoring

# Check the K3s cluster
kubectl get nodes
# Should show: k3d-thesis-hybrid-server-0 Ready

# Check HAProxy stats
curl http://localhost:18404/stats
```

### 2. Scenarios Configured

Each scenario requires different routing daemon configuration:

| Scenario | Routing Daemon Config | HAProxy Weights | Prediction |
|----------|----------------------|-----------------|------------|
| S1 | Static K8s only | 100/0 | No |
| S2 | Static Serverless only | 0/100 | No |
| S3 | Algorithm 1 reactive | 80/20 → 50/50 | No |
| S4 | Algorithm 1 + 2 | 80/20 → 50/50 | Yes |

### 3. GRU Model (for S4)

```bash
# Ensure the artifact exists (loaded by apps/prediction/prediction/model_loader.py)
ls -la data/models/gru_model.pt

# Start the prediction server, then check health
uv run thesis-prediction-server --port 8090
curl http://localhost:8090/health
```

## Running Validation

### Quick Check (No Experiments)

```bash
uv run thesis experiment validate-realtime
```

This validates H3 only. The GRU check loads the model artifact directly, so no cluster is needed. The command writes a timestamped JSON report under `results/realtime_validation/` and prints the path.

### Full Live Validation (60+ minutes)

```bash
# All four scenarios, 3 runs each, 300 s per run
uv run thesis experiment run --phase full --runs 3 --duration 300

# Or all four arms under one named profile
uv run thesis experiment reproduce --profile quad

# Definitive H2 comparison
uv run thesis experiment paired-run --pairs 5
```

**Timeline:**
- S1: 3 runs × 5 min = 15 min
- S2: 3 runs × 5 min = 15 min
- S3: 3 runs × 5 min = 15 min
- S4: 3 runs × 5 min = 15 min
- Total: ~60 minutes + setup/teardown

## Metrics Collected

### Core SLO Metrics

| Metric | PromQL Query | Unit |
|--------|-------------|------|
| p50 Latency | `histogram_quantile(0.50, ...)` | milliseconds |
| p95 Latency | `histogram_quantile(0.95, ...)` | milliseconds |
| p99 Latency | `histogram_quantile(0.99, ...)` | milliseconds |
| Error Rate | `rate(http_requests_total{status=~"5.."}) / rate(http_requests_total)` | percent |
| Throughput | `rate(http_requests_total)` | RPS |

### Resource Metrics

| Metric | PromQL Query | Unit |
|--------|-------------|------|
| K8s Pod Count | `count(kube_pod_status_ready)` | pods |
| Serverless Invocations | `knative_service_request_count` | count |
| CPU Utilization | `rate(container_cpu_usage_seconds_total)` | cores |
| Memory Usage | `container_memory_working_set_bytes` | bytes |

### Decision Metrics

| Metric | Source | Description |
|--------|--------|-------------|
| SCALE_OUT Count | `routing_decisions_total{decision="SCALE_OUT"}` | Reactive scaling |
| PREDICTIVE Count | `routing_decisions_total{decision="PREDICTIVE"}` | Predictive scaling |
| Weight Changes | `haproxy_weight_changes_total` | Routing adjustments |

## Validation Criteria

### H1: Hybrid > Pure

**Acceptance Criteria:**
1. S4 throughput > S1 throughput (statistically significant, p < 0.05)
2. S4 error rate < S1 error rate OR within margin
3. Cost analysis reports both whole-run totals and fairness-normalized metrics (`$/1M requests`, `$/1M successful`) without assuming fixed scenario ordering

**Measurements Needed:**
- S1: 3+ runs with metrics
- S2: 3+ runs with metrics
- S4: 3+ runs with metrics

### H2: Predictive > Reactive

**Acceptance Criteria:**
1. PREDICTIVE decisions > 0 in S4 (pipeline actually triggers)
2. S4 p99 latency < S3 p99 latency (statistically significant)
3. S4 SCALE_OUT count < S3 SCALE_OUT count (fewer reactive emergencies)

**Measurements Needed:**
- S3: 3+ runs with metrics
- S4: 3+ runs with metrics
- GRU predictions with confidence > 0.70

### H3: GRU Adequate

**Acceptance Criteria:**
1. Model RMSE < 10% of mean traffic
2. Predictions complete within < 50ms
3. Model loads successfully

**Measurements:**
- From training data (already validated)
- From prediction server health endpoint

## Statistical Analysis

### Significance Testing

```python
# Example: Compare S4 vs S1 throughput
from scipy import stats

s1_throughputs = [348, 352, 345]  # 3 runs
s4_throughputs = [536, 542, 528]  # 3 runs

t_stat, p_value = stats.ttest_ind(s4_throughputs, s1_throughputs)
# p_value < 0.05 => statistically significant
```

### Effect Size

```python
# Cohen's d for effect size
def cohens_d(group1, group2):
    n1, n2 = len(group1), len(group2)
    s1, s2 = statistics.stdev(group1), statistics.stdev(group2)
    pooled_std = sqrt(((n1-1)*s1**2 + (n2-1)*s2**2) / (n1+n2-2))
    return (statistics.mean(group1) - statistics.mean(group2)) / pooled_std

# d > 0.8 => large effect
# d > 0.5 => medium effect
# d > 0.2 => small effect
```

## Expected Results

Based on stress test history, we expect:

| Scenario | Expected Throughput | Expected Error Rate | Expected p95 |
|----------|--------------------|--------------------|--------------|
| S1 | 300-400 RPS | 70-85% | 4000-6000ms |
| S2 | 550-650 RPS | 0-5% | 1-5ms |
| S3 | 350-450 RPS | 85-95% | 4000-5500ms |
| S4 | 500-600 RPS | 90-98% | 4000-5500ms |

**Note:** These are rough estimates. Real experiments may vary based on:
- Load test intensity
- Infrastructure state
- Network conditions
- CPU throttling settings

Cost rankings may also change materially with workload profile and execution-time signal selection (for example, app-duration-informed vs CPU-derived sizing), so treat any single run as directional unless replicated.

## Troubleshooting

### Prometheus Not Available

```bash
# Check if Prometheus pod is running
kubectl get pods -n monitoring | grep prometheus

# Port forward if needed
kubectl port-forward svc/prometheus 9090:9090 -n monitoring &
```

### No Metrics in Prometheus

```bash
# Check if HAProxy exporter is working
curl http://localhost:18404/metrics

# Make the application and kubelet metrics scrapable
uv run thesis infra monitoring
```

### Routing Daemon Not Making Decisions

```bash
# The daemon runs as a local process; check its health and metrics
curl http://localhost:9104/health
curl http://localhost:9104/metrics
```

## Outputs

### JSON Results

`validate-realtime` writes this shape (values illustrative):

```json
{
  "timestamp": "2026-09-12T10:00:00",
  "h3": {
    "hypothesis": "H3",
    "proven": true,
    "confidence": "high",
    "evidence": {
      "model_type": "gru",
      "training_rmse_requests": 6.01,
      "training_rmse_percent": 6.01,
      "target_rmse_percent": 10.0,
      "test_prediction": 742,
      "test_confidence": 0.83
    }
  },
  "h1": {"status": "pending_live_experiments"},
  "h2": {"status": "pending_live_experiments"},
  "report_path": "results/realtime_validation/validation_20260912_100000.json"
}
```

### Visualization

Results can be visualized with:

```python
import matplotlib.pyplot as plt

# Plot latency comparison
scenarios = ['S1', 'S2', 'S3', 'S4']
p95_latencies = [5001, 1.2, 5001, 5000]

plt.bar(scenarios, p95_latencies)
plt.ylabel('p95 Latency (ms)')
plt.title('Latency by Scenario')
plt.savefig('results/latency_comparison.png')
```

## Next Steps

1. **Start infrastructure:**
   ```bash
   uv run thesis infra setup      # first time
   uv run thesis infra ensure     # converge an existing stack
   ```

2. **Run the offline H3 check:**
   ```bash
   uv run thesis experiment validate-realtime
   ```

3. **Run live experiments:**
   ```bash
   uv run thesis experiment reproduce --profile quad
   uv run thesis experiment paired-run --pairs 5
   ```

4. **Analyze results:**
   ```bash
   uv run thesis analysis hypotheses
   uv run thesis analysis cost --experiment-dir results/experiments/phase-b/<bundle>
   uv run thesis analysis runs results/experiments/phase-b/<bundle>
   ```

5. **Write the bundle summary:**
   ```bash
   uv run thesis experiment summary results/experiments/phase-b/<bundle>
   uv run thesis experiment analyze results/experiments/phase-b/<bundle>
   ```

## Limitations

Current limitations of real-time validation:

1. **Time consuming:** Full validation takes 60+ minutes
2. **Infrastructure dependency:** Requires all services running
3. **Cost:** Running on real cloud would incur charges
4. **Repeatability:** Results may vary between runs due to:
   - Network conditions
   - CPU scheduling
   - Background load

## Alternative: Simulation Mode

For quick iteration, use the offline checks with stored results:

```bash
# All three hypotheses from stored results, no live experiments
uv run thesis analysis hypotheses
```

---

**Last Updated:** 2026-09-12  
**Status:** Commands verified against the current `thesis` CLI
