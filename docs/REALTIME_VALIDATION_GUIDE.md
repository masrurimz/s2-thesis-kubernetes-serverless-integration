# Real-Time Hypothesis Validation Guide

This document explains how to perform actual experiments with real Prometheus metrics to validate H1, H2, and H3.

## Overview

The `realtime_validation.py` script performs **live experiments** with actual infrastructure:
- Runs k6 load tests against each scenario
- Collects real metrics from Prometheus
- Performs statistical analysis across multiple runs
- Produces honest validation results

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REAL-TIME VALIDATION FLOW                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. CHECK INFRASTRUCTURE                                                    │
│     ├── Prometheus: curl http://localhost:9090/-/healthy                     │
│     ├── K3s: kubectl get nodes                                               │
│     └── HAProxy: curl http://localhost:8404/stats                            │
│                                                                              │
│  2. RUN EXPERIMENT (per scenario, per run)                                   │
│     ├── Configure routing daemon for scenario (S1/S2/S3/S4)                  │
│     ├── Start k6 load test (steady/spike/endurance)                        │
│     ├── Collect Prometheus metrics every 10 seconds                        │
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
# Check Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n monitoring

# Check K3s
kubectl get nodes
# Should show: k3d-thesis-hybrid-server-0 Ready

# Check HAProxy (if using systemd)
sudo systemctl start haproxy
# Or check manually:
curl http://localhost:8404/stats
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
# Ensure model exists
ls -la controller/data/models/gru_model.pt

# Test prediction server
curl http://localhost:8090/health
```

## Running Validation

### Quick Check (No Experiments)

```bash
cd controller
HSA_OVERRIDE_GFX_VERSION=11.0.0 sg render -c \
  "uv run python ../scripts/realtime_validation.py"
```

This checks infrastructure and validates H3 only (no live experiments needed).

### Full Live Validation (30+ minutes)

```bash
cd controller
HSA_OVERRIDE_GFX_VERSION=11.0.0 sg render -c \
  "uv run python ../scripts/realtime_validation.py --live --duration 300 --runs 3"
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
3. S4 cost < S2 cost (hybrid cheaper than pure serverless)

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
curl http://localhost:8404/metrics

# Check if apps are exposing metrics
curl http://test-app/metrics
```

### Routing Daemon Not Making Decisions

```bash
# Check daemon logs
kubectl logs -f deployment/routing-daemon

# Check if metrics are flowing
curl http://localhost:9104/metrics
```

## Outputs

### JSON Results

```json
{
  "timestamp": "2026-02-12T10:00:00",
  "h1": {
    "proven": true,
    "confidence": "medium",
    "evidence": {
      "s1_throughput_mean": 348.5,
      "s4_throughput_mean": 536.2,
      "improvement_percent": 53.9,
      "p_value": 0.03,
      "significant": true
    }
  },
  "h2": {
    "proven": false,
    "confidence": "low",
    "evidence": {
      "predictive_decisions": 0,
      "reason": "No predictive actions triggered"
    }
  },
  "h3": {
    "proven": true,
    "confidence": "high",
    "evidence": {
      "rmse_percent": 6.01
    }
  }
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
   ./scripts/start-infrastructure.sh
   ```

2. **Run validation:**
   ```bash
   cd controller
   HSA_OVERRIDE_GFX_VERSION=11.0.0 sg render -c \
     "uv run python ../scripts/realtime_validation.py --live"
   ```

3. **Analyze results:**
   ```bash
   python scripts/analyze_results.py results/realtime_validation/
   ```

4. **Generate report:**
   ```bash
   python scripts/generate_report.py --input results/realtime_validation/
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

For quick iteration, use simulation mode with historical data:

```bash
# Fast validation using stress test results
python scripts/validate_all_hypotheses.py
```

This provides approximate validation without running live experiments.

---

**Last Updated:** 2026-02-12  
**Status:** Implementation ready, requires infrastructure setup
