# Running Thesis Experiments

This guide provides step-by-step instructions to run the H1 and H2 hypothesis evaluations on real infrastructure.

---

## Prerequisites

Before running experiments, ensure all components are operational:

### Infrastructure Checklist

| Component | Command to Verify | Expected Output |
|-----------|------------------|-----------------|
| k3d cluster | `kubectl get nodes` | 2+ nodes Ready |
| Test app (K8s) | `curl http://localhost:8080/health` | 200 OK |
| Test app (Knative) | `curl -H "Host: test-app.default.example.com" http://localhost:8081/health` | 200 OK |
| HAProxy | `curl http://localhost:8404/stats` | Stats page |
| Prometheus | `curl http://localhost:9090/-/healthy` | "Prometheus is Healthy" |
| GRU prediction server | `curl http://localhost:8090/health` | `{"status": "healthy"}` |
| Routing daemon | `curl http://localhost:9104/health` | `{"status": "healthy"}` |

### Quick Setup

```bash
# 1. Create k3d cluster with all components
cd infrastructure/k3d
./create-cluster.sh
./knative-install.sh

# 2. Deploy test application
kubectl apply -f infrastructure/k8s/test-app.yaml
kubectl apply -f infrastructure/serverless/test-app-knative.yaml

# 3. Start HAProxy
cd infrastructure/haproxy
docker-compose up -d

# 4. Start Prometheus/Grafana
cd infrastructure/monitoring
docker-compose up -d

# 5. Train and start GRU prediction server
cd controller
uv run python -m ml_models.train_gru  # If model not trained
uv run python -m prediction_engine.server --port 8090

# 6. Start routing daemon
cd controller
uv run python -m daemon.routing_daemon --scenario s4-hybrid-predictive
```

---

## Running H1 Evaluation (Hybrid > Pure)

H1 tests whether hybrid routing (S4) outperforms pure K8s (S1) and pure Serverless (S2).

### Simulated Mode (Development)

```bash
cd experiments
python -m evaluations.h1_evaluation
```

### Real Infrastructure Mode

```bash
cd experiments
python -m evaluations.h1_evaluation --simulate=False
```

### What It Does

1. Runs scenarios S1, S2, S4 sequentially
2. For each scenario:
   - Configures routing daemon via `POST /set_scenario`
   - Runs k6 load tests (steady, spike, endurance)
   - Collects metrics from Prometheus
3. Compares performance across scenarios
4. Generates statistical analysis

### Configuration Options

```python
evaluator = H1Evaluator(
    results_dir=Path("results/evaluations/h1"),
    routing_daemon_url="http://localhost:9104",
    prometheus_url="http://localhost:9090",
)

result = evaluator.run_evaluation(
    scenarios=["s1-k8s-only", "s2-serverless-only", "s4-hybrid-predictive"],
    workloads=["steady", "spike", "endurance"],
    repetitions=3,
    simulate=False,  # Set to False for real infrastructure
)
```

---

## Running H2 Evaluation (Predictive > Reactive)

H2 tests whether predictive routing (S4) reduces SLO violations compared to reactive routing (S3).

### Simulated Mode (Development)

```bash
cd experiments
python -m evaluations.h2_evaluation
```

### Real Infrastructure Mode

```bash
cd experiments
python -m evaluations.h2_evaluation --simulate=False
```

### What It Does

1. Runs scenarios S3 and S4
2. Measures:
   - SLO violations count
   - Violation duration
   - Proactive vs reactive adjustments
   - Average reaction time
3. Calculates improvement percentages
4. Determines if hypothesis is proven

### Configuration Options

```python
evaluator = H2Evaluator(
    results_dir=Path("results/evaluations/h2"),
    routing_daemon_url="http://localhost:9104",
    prometheus_url="http://localhost:9090",
    controller_metrics_url="http://localhost:9104/metrics",
    k6_duration_sec=300,
)

result = evaluator.run_evaluation(
    scenarios=["s3-hybrid-reactive", "s4-hybrid-predictive"],
    workloads=["spike", "endurance"],
    repetitions=3,
    simulate=False,
)
```

---

## Scenarios Reference

| Scenario | Code | Weights (K8s/Knative) | Algorithm | GRU Predictions |
|----------|------|----------------------|-----------|-----------------|
| S1: K8s Only | `s1-k8s-only` | 100/0 | Static | No |
| S2: Serverless Only | `s2-serverless-only` | 0/100 | Static | No |
| S3: Hybrid Reactive | `s3-hybrid-reactive` | 80/20 initial | Algorithm 1 | No |
| S4: Hybrid Predictive | `s4-hybrid-predictive` | 80/20 initial | Algorithm 1 | Yes |

---

## Workload Profiles

| Workload | Description | Pattern |
|----------|-------------|---------|
| `steady` | Constant load | 50 VUs for 5 minutes |
| `spike` | Traffic bursts | Ramps from 10→100→10 VUs |
| `endurance` | Extended test | 30 VUs for 30 minutes |

Load test scripts are in `infrastructure/load-testing/`:
- `steady-load.js`
- `spike-load.js`
- `endurance-test.js`

---

## Interpreting Results

### H1 Results (results/evaluations/h1/)

```
h1_raw_data_YYYYMMDD_HHMMSS.csv    # Per-run metrics
h1_summary_YYYYMMDD_HHMMSS.json    # Aggregated improvements
h1_report_YYYYMMDD_HHMMSS.md       # Human-readable report
```

**Key metrics:**
- `s4_vs_s1.p99_latency`: % improvement over K8s-only
- `s4_vs_s2.cost`: % cost reduction over Serverless-only
- `significance`: Statistical significance (p < 0.05)

**Success criteria:**
- S4 vs S1 p99 latency: >15% improvement
- S4 vs S2 cost: >20% reduction

### H2 Results (results/evaluations/h2/)

```
h2_raw_data_YYYYMMDD_HHMMSS.csv
h2_summary_YYYYMMDD_HHMMSS.json
h2_report_YYYYMMDD_HHMMSS.md
```

**Key metrics:**
- `violation_reduction`: % fewer SLO violations
- `proactive_ratio`: Proactive / (Proactive + Reactive) adjustments

**Success criteria:**
- SLO violations: >50% reduction
- Proactive ratio: >50%

---

## Prometheus Metrics Reference

Metrics exposed by routing daemon (`localhost:9104/metrics`):

| Metric | Description |
|--------|-------------|
| `slo_violation_total` | Counter of SLO violations by type |
| `routing_decision_total` | Counter of decisions (SCALE_OUT, OPTIMIZE_COST, PREDICTIVE, MAINTAIN) |
| `reaction_time_ms` | Histogram of violation-to-adjustment latency |
| `routing_daemon_current_weight` | Current weights by backend |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_URL` | `http://localhost:9090` | Prometheus server |
| `ROUTING_DAEMON_URL` | `http://localhost:9104` | Routing daemon API |
| `GRU_SERVER_URL` | `http://localhost:8090` | GRU prediction server |
| `HAPROXY_STATS_URL` | `http://localhost:8404/stats;csv` | HAProxy stats |

---

## Troubleshooting

### "Failed to configure scenario"

```bash
# Check routing daemon is running
curl http://localhost:9104/health

# Restart routing daemon
cd controller
uv run python -m daemon.routing_daemon --scenario s3-hybrid-reactive
```

### "k6 not found"

```bash
# Install k6
# macOS
brew install k6

# Linux
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

### "Prometheus returns 0 for all metrics"

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify HAProxy metrics are being scraped
curl http://localhost:9090/api/v1/query?query=haproxy_backend_http_requests_total

# Check if test app is generating traffic
curl http://localhost:8082/  # HAProxy endpoint
```

### "GRU server not available"

```bash
# Check if model is trained
ls controller/data/models/gru_model.pt

# Train model if missing
cd controller
uv run python -m ml_models.train_gru

# Start prediction server
uv run python -m prediction_engine.server --port 8090
```

### Low proactive adjustment ratio

- Ensure GRU model is trained on representative data
- Verify prediction confidence threshold (default 0.7)
- Check load change threshold (default 0.3)

---

## Full Experiment Pipeline

```bash
#!/bin/bash
# Full experiment run script

set -e

echo "=== Setting up infrastructure ==="
cd infrastructure/k3d && ./create-cluster.sh && ./knative-install.sh
cd ../..

echo "=== Deploying test apps ==="
kubectl apply -f infrastructure/k8s/test-app.yaml
kubectl apply -f infrastructure/serverless/test-app-knative.yaml

echo "=== Starting support services ==="
docker-compose -f infrastructure/haproxy/docker-compose.yml up -d
docker-compose -f infrastructure/monitoring/docker-compose.yml up -d

echo "=== Training GRU model ==="
cd controller && uv run python -m ml_models.train_gru && cd ..

echo "=== Starting GRU server (background) ==="
cd controller && uv run python -m prediction_engine.server --port 8090 &
GRU_PID=$!
cd ..

echo "=== Starting routing daemon (background) ==="
cd controller && uv run python -m daemon.routing_daemon --scenario s4-hybrid-predictive &
DAEMON_PID=$!
cd ..

sleep 10  # Wait for services to start

echo "=== Running H1 evaluation ==="
cd experiments && python -m evaluations.h1_evaluation --simulate=False

echo "=== Running H2 evaluation ==="
python -m evaluations.h2_evaluation --simulate=False

echo "=== Cleaning up ==="
kill $GRU_PID $DAEMON_PID 2>/dev/null || true

echo "=== Results saved to results/evaluations/ ==="
```

---

## Related Documentation

- [Appendix A: Reproducibility Guide](../thesis/appendix-a-reproducibility.md) - Complete setup instructions
- [Algorithm 1 Spec](../specs/algorithm-1-spec.md) - Routing algorithm details
- [Infrastructure Setup](../../infrastructure/k3d/README.md) - k3d cluster configuration
