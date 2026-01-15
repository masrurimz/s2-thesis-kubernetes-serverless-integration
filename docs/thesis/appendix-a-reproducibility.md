# Appendix A: Reproducibility Guide

This appendix provides step-by-step instructions to reproduce all experiments and results presented in this thesis. The guide covers environment setup, dataset preparation, model training, infrastructure deployment, and experiment execution.

---

## A.0 System Components Overview

This section provides a quick reference to all components involved in the experiment infrastructure.

### A.0.1 Core Components

| Component | Location | Port | Description |
|-----------|----------|------|-------------|
| **routing_daemon** | `controller/daemon/routing_daemon.py` | 9104 | Main daemon running Algorithm 1 with scenario configs |
| **GRU prediction server** | `controller/prediction/prediction_server.py` | 8090 | Serves load predictions from trained GRU model |
| **Algorithm1Controller** | `controller/intelligent_router/algorithm1_controller.py` | - | Core SLO-aware routing logic |
| **SLOMonitor** | `controller/monitoring_v2/slo_monitor.py` | - | Monitors p99 latency and detects violations |
| **HAProxy weight adjuster** | `controller/intelligent_router/weight_adjuster.py` | 9999 (socket) | Adjusts HAProxy backend weights |
| **k6_runner** | `controller/workloads/k6_runner.py` | - | Executes k6 load tests programmatically |

### A.0.2 Evaluation Scripts

| Script | Location | Purpose |
|--------|----------|---------|
| **H1 Evaluator** | `experiments/evaluations/h1_evaluation.py` | Tests Hybrid > Pure hypothesis |
| **H2 Evaluator** | `experiments/evaluations/h2_evaluation.py` | Tests Predictive > Reactive hypothesis |
| **Experiment Logger** | `experiments/experiment_logger.py` | Logs experiment runs and metrics |

### A.0.3 Infrastructure Services

| Service | Port | Purpose |
|---------|------|---------|
| HAProxy | 8082 (traffic), 8404 (stats), 9999 (admin) | Traffic routing between K8s and Knative |
| Prometheus | 9090 | Metrics collection and queries |
| Grafana | 3000 | Metrics visualization |
| k3d cluster | 8080 (K8s), 8081 (Knative/Kourier) | Container orchestration |

### A.0.4 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_URL` | `http://localhost:9090` | Prometheus server URL |
| `ROUTING_DAEMON_URL` | `http://localhost:9104` | Routing daemon API URL |
| `GRU_SERVER_URL` | `http://localhost:8090` | GRU prediction server URL |
| `HAPROXY_STATS_URL` | `http://localhost:8404/stats;csv` | HAProxy stats endpoint |
| `HAPROXY_SOCKET_HOST` | `localhost` | HAProxy admin socket host |
| `HAPROXY_SOCKET_PORT` | `9999` | HAProxy admin socket port |

### A.0.5 Expected Output Locations

| Output | Location | Format |
|--------|----------|--------|
| H1 results | `results/evaluations/h1/` | CSV, JSON, Markdown |
| H2 results | `results/evaluations/h2/` | CSV, JSON, Markdown |
| Trained models | `controller/data/models/` | PyTorch `.pt` files |
| Experiment logs | `logs/` | Structured JSON logs |

---

## A.1 Prerequisites

### A.1.1 Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16-32 GB |
| Storage | 20 GB SSD | 50 GB SSD |
| GPU | Not required | CUDA-capable (for faster GRU training) |

**Resource Allocation by Phase:**

| Phase | Memory | CPU | Duration |
|-------|--------|-----|----------|
| Model Training (GRU) | 4-8 GB | 2+ cores | 10-30 min |
| K3s Cluster | 4 GB | 2 cores | Continuous |
| Full Evaluation (S1-S4) | 8-16 GB | 4+ cores | 2-4 hours |

### A.1.2 Software Requirements

| Software | Version | Purpose |
|----------|---------|---------|
| Python | ≥3.11 | Controller, ML models |
| UV | ≥0.4.0 | Python package manager |
| Docker | ≥24.0 | Container runtime |
| K3d | ≥5.6.0 | K3s in Docker |
| kubectl | ≥1.28 | Kubernetes CLI |
| curl | Any | HTTP testing |
| git | Any | Repository cloning |

### A.1.3 Operating System Compatibility

| OS | Status | Notes |
|----|--------|-------|
| Ubuntu 22.04+ | ✅ Tested | Primary development platform |
| macOS 13+ (ARM/Intel) | ✅ Tested | Full support |
| Windows 11 + WSL2 | ⚠️ Partial | Docker Desktop required |

**Estimated Setup Time: 30-45 minutes**

---

## A.2 Environment Setup

### A.2.1 Clone the Repository

```bash
# Clone the repository
git clone https://github.com/masrurimz/s2-thesis-kubernetes-serverless-integration.git
cd s2-thesis-kubernetes-serverless-integration

# Verify repository structure
ls -la
# Expected: controller/ data/ experiments/ infrastructure/ ml_models/ results/
```

**Success Criteria:** All directories present, no git errors.

### A.2.2 Install UV Package Manager

```bash
# Install UV (cross-platform)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
# Expected: uv 0.4.x or higher
```

### A.2.3 Install Python Dependencies

```bash
# Navigate to controller directory
cd controller

# Install all dependencies
uv sync

# Verify installation
uv run python -c "import torch; import pandas; import sklearn; print('Dependencies OK')"
# Expected: "Dependencies OK"
```

**Estimated Time: 5-10 minutes** (depends on network speed)

### A.2.4 Install Container Tools

**Ubuntu/Debian:**
```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Install K3d
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

**macOS:**
```bash
# Using Homebrew
brew install docker k3d kubectl

# Start Docker Desktop (required for macOS)
open -a Docker
```

**Verify installations:**
```bash
docker --version    # Expected: Docker version 24.x+
k3d --version       # Expected: k3d version v5.x+
kubectl version --client  # Expected: Client Version: v1.28+
```

**Success Criteria:** All version commands return expected versions.

---

## A.3 Dataset Preparation

### A.3.1 Dataset Overview

This research uses two real-world HTTP trace datasets for training and evaluation:

| Dataset | Requests | Time Period | Source |
|---------|----------|-------------|--------|
| ClarkNet | ~2M | Aug-Sep 1995 | ClarkNet WWW Server |
| Calgary | ~2M | Oct 1994 | University of Calgary CS |

### A.3.2 Download Raw Datasets

```bash
# Navigate to data directory
cd data/scripts

# Make download script executable
chmod +x download_datasets.sh

# Download datasets
./download_datasets.sh
```

**Alternative (if FTP unavailable):**
```bash
# ClarkNet from Internet Archive
curl -L -o ../raw/clarknet/clarknet-http.gz \
  "https://web.archive.org/web/2023/ftp://ita.ee.lbl.gov/traces/clarknet-http.gz"

# Calgary from Internet Archive
curl -L -o ../raw/calgary/calgary-http.gz \
  "https://web.archive.org/web/2023/ftp://ita.ee.lbl.gov/traces/calgary-http.gz"
```

**Estimated Time: 10-20 minutes** (depending on network)

### A.3.3 Process Datasets

```bash
# Navigate to controller directory
cd ../../controller

# Process ClarkNet dataset to RPS time series
uv run python -m data.scripts.clf_parser --input ../data/raw/clarknet/ --output ../data/processed/clarknet_rps.parquet

# Process Calgary dataset
uv run python -m data.scripts.clf_parser --input ../data/raw/calgary/ --output ../data/processed/calgary_rps.parquet

# Verify processed data
ls -la ../data/processed/
# Expected: clarknet_rps.parquet, calgary_rps.parquet
```

### A.3.4 Generate Synthetic Data (Alternative)

If real datasets are unavailable, generate synthetic data with realistic patterns:

```bash
cd controller

# Generate synthetic training data (72 hours)
uv run python -c "
import sys
sys.path.insert(0, 'ml_models')
from train_gru import generate_realistic_traffic
import pandas as pd

df = generate_realistic_traffic(duration_hours=72)
df.to_parquet('../data/processed/synthetic_rps.parquet')
print(f'Generated {len(df)} samples')
"
```

**Success Criteria:** Parquet files exist in `data/processed/` with non-zero size.

---

## A.4 Model Training

### A.4.1 GRU Model Training

The GRU neural network is trained on the processed RPS time series data.

```bash
cd controller

# Train GRU model with default configuration
uv run python -m ml_models.train_gru

# Expected output:
# ======================================================================
# GRU Model Training and Evaluation
# ======================================================================
# [1/3] Generating training data (72 hours)...
# [2/3] Training GRU model...
#   GRU Validation RMSE: X.XX (Y.YY%)
# [3/3] Evaluating on test set...
# ✓ GRU meets thesis target (RMSE < 10%)
# Model saved to: controller/data/models/gru_model.pt
```

**Model Configuration (default):**

| Parameter | Value | Description |
|-----------|-------|-------------|
| `hidden_size` | 128 | GRU hidden units |
| `num_layers` | 2 | Stacked GRU layers |
| `sequence_length` | 60 | Look-back window (minutes) |
| `epochs` | 100 | Maximum training epochs |
| `learning_rate` | 0.0005 | Adam optimizer LR |
| `early_stopping_patience` | 15 | Early stopping epochs |

**Estimated Time: 10-30 minutes** (CPU) / 2-5 minutes (GPU)

### A.4.2 Model Comparison (GRU vs Baselines)

Compare GRU against baseline models for thesis H3 justification:

```bash
cd controller

# Run model comparison
uv run python -m ml_models.model_comparison

# Expected output: Table comparing RMSE across models
```

### A.4.3 Verify Model Output

```bash
# Check trained model exists
ls -la data/models/gru_model.pt
# Expected: File with size > 100KB

# Test model prediction
uv run python -c "
import torch
from ml_models.gru_predictor import GRUPredictor, GRUConfig
import numpy as np

config = GRUConfig()
predictor = GRUPredictor(config)
predictor.load_model('data/models/gru_model.pt')

# Test prediction with sample data
sample = np.random.uniform(80, 120, size=60)
result = predictor.predict(sample)
print(f'Predicted RPS: {result[\"predicted_requests\"]:.2f}')
print('Model loaded and predicting successfully!')
"
```

**Success Criteria:**
- Model file saved at `controller/data/models/gru_model.pt`
- Validation RMSE < 10% (thesis target)
- Model loads and predicts without errors

---

## A.5 Infrastructure Deployment

### A.5.1 Create K3s Cluster

```bash
# Navigate to infrastructure directory
cd infrastructure/k3s

# Create K3s cluster using k3d
k3d cluster create hybrid-thesis \
  --config cluster-config.yaml \
  --port "8080:80@loadbalancer"

# Verify cluster is running
kubectl cluster-info
# Expected: Kubernetes control plane is running at https://...

# Check nodes
kubectl get nodes
# Expected: One node in "Ready" status
```

**Estimated Time: 2-5 minutes**

### A.5.2 Deploy Knative Serving

```bash
# Install Knative Serving CRDs
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.12.0/serving-crds.yaml

# Install Knative Serving core
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.12.0/serving-core.yaml

# Install Kourier (lightweight ingress)
kubectl apply -f https://github.com/knative/net-kourier/releases/download/knative-v1.12.0/kourier.yaml

# Configure Knative to use Kourier
kubectl patch configmap/config-network \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'

# Verify Knative installation
kubectl get pods -n knative-serving
# Expected: All pods in "Running" status
```

**Estimated Time: 3-5 minutes**

### A.5.3 Deploy Test Application (K8s Backend)

```bash
cd infrastructure/k3s

# Deploy nginx test application
kubectl apply -f nginx-deployment.yaml
kubectl apply -f nginx-service.yaml

# Verify deployment
kubectl get pods -l app=nginx
# Expected: Pod in "Running" status

# Test K8s backend
curl http://localhost:8080/
# Expected: nginx welcome page or custom response
```

### A.5.4 Deploy Serverless Backend (Knative)

```bash
cd infrastructure/serverless

# Deploy Knative service
kubectl apply -f knative-service.yaml

# Wait for service to be ready
kubectl get ksvc serverless-sim
# Expected: URL column shows service URL, READY=True

# Get Kourier external IP/port
kubectl get svc kourier -n kourier-system
```

### A.5.5 Deploy HAProxy Traffic Router

```bash
cd infrastructure/haproxy

# Start HAProxy using docker-compose
docker-compose up -d

# Verify HAProxy is running
docker ps | grep haproxy
# Expected: haproxy container running

# Check HAProxy stats
curl http://localhost:8404/stats
# Expected: HAProxy stats page

# Test traffic routing
curl http://localhost:8082/
# Expected: Response from either K8s or serverless backend
```

### A.5.6 Deploy Prometheus Monitoring

```bash
cd infrastructure/monitoring

# Start Prometheus
docker-compose up -d

# Verify Prometheus is running
curl http://localhost:9090/-/healthy
# Expected: "Prometheus is Healthy."

# Test metrics query
curl "http://localhost:9090/api/v1/query?query=up"
# Expected: JSON response with metric data
```

### A.5.7 Verify Full Infrastructure

```bash
# Check all components
echo "=== K3s Cluster ==="
kubectl get nodes

echo "=== K8s Pods ==="
kubectl get pods --all-namespaces | grep -E "(nginx|serverless)"

echo "=== Knative Services ==="
kubectl get ksvc

echo "=== HAProxy ==="
curl -s http://localhost:8404/stats | head -5

echo "=== Prometheus ==="
curl -s http://localhost:9090/-/healthy

echo "=== Traffic Test ==="
for i in {1..5}; do curl -s http://localhost:8082/health; done
```

**Success Criteria:**
- K3s cluster running with 1 node
- Nginx pod running in K8s
- Knative service deployed and ready
- HAProxy routing traffic
- Prometheus collecting metrics

---

## A.6 Running Experiments

### A.6.1 Experiment Scenarios

| Scenario | Description | HAProxy Config |
|----------|-------------|----------------|
| S1: K8s-only | 100% traffic to Kubernetes | weight 100:0 |
| S2: Serverless-only | 100% traffic to Knative | weight 0:100 |
| S3: Hybrid-reactive | Algorithm 1, no prediction | Dynamic weights |
| S4: Hybrid-predictive | Algorithm 1 + GRU | Dynamic weights |

### A.6.2 Configure Scenario S1 (K8s-only)

```bash
# Update HAProxy weights via runtime socket
echo "set server servers/k3s-cluster weight 100" | nc -U /tmp/haproxy.sock
echo "set server servers/serverless-sim weight 0" | nc -U /tmp/haproxy.sock

# Alternative: Update haproxy.cfg directly
# server k3s-cluster host.docker.internal:8080 weight 100
# server serverless-sim host.docker.internal:8081 weight 0
```

### A.6.3 Configure Scenario S2 (Serverless-only)

```bash
echo "set server servers/k3s-cluster weight 0" | nc -U /tmp/haproxy.sock
echo "set server servers/serverless-sim weight 100" | nc -U /tmp/haproxy.sock
```

### A.6.4 Run Scenario S3 (Hybrid-Reactive)

```bash
cd controller

# Start routing daemon in reactive mode (Algorithm 1 without predictions)
uv run python -m daemon.routing_daemon \
  --scenario s3-hybrid-reactive \
  --interval 15 \
  --prometheus-url http://localhost:9090 \
  --haproxy-host localhost \
  --haproxy-port 9999 \
  --api-port 9104

# In another terminal, verify daemon is running
curl http://localhost:9104/health
# Expected: {"status": "healthy", "scenario": "s3-hybrid-reactive", ...}

# Monitor routing decisions
curl http://localhost:9104/status
```

**Routing Daemon API Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/status` | GET | Current weights, decision counts |
| `/set_scenario` | POST | Change scenario |
| `/health` | GET | Health check |
| `/metrics` | GET | Prometheus metrics |

### A.6.5 Run Scenario S4 (Hybrid-Predictive)

```bash
cd controller

# First, start the GRU prediction server (port 8090)
uv run python -m prediction_engine.server --port 8090 &

# Verify prediction server is running
curl http://localhost:8090/health
# Expected: {"status": "healthy", "model_loaded": true}

# Start routing daemon in predictive mode
uv run python -m daemon.routing_daemon \
  --scenario s4-hybrid-predictive \
  --interval 15 \
  --prometheus-url http://localhost:9090 \
  --haproxy-host localhost \
  --haproxy-port 9999 \
  --gru-url http://localhost:8090 \
  --api-port 9104

# Verify GRU integration
curl http://localhost:9104/health
# Expected: {"gru_available": true, ...}
```

**Scenario Configuration Reference:**

| Scenario | Weights (K8s/Knative) | Algorithm 1 | GRU Predictions |
|----------|----------------------|-------------|-----------------|
| `s1-k8s-only` | 100/0 | No (static) | No |
| `s2-serverless-only` | 0/100 | No (static) | No |
| `s3-hybrid-reactive` | 80/20 initial | Yes | No |
| `s4-hybrid-predictive` | 80/20 initial | Yes | Yes |

### A.6.6 Run Load Tests

```bash
# Using the run-scenario.sh script
./run-scenario.sh s4 steady    # S4 with steady load
./run-scenario.sh s4 spike     # S4 with spike load
./run-scenario.sh s4 endurance # S4 with endurance test

# Manual load test with curl (simple)
for i in {1..1000}; do
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8082/
  sleep 0.01
done

# Using k6 (if installed)
k6 run infrastructure/load-tests/steady.js
```

### A.6.7 Collect Metrics

```bash
# Query Prometheus for latency percentiles
curl "http://localhost:9090/api/v1/query?query=histogram_quantile(0.99,rate(http_request_duration_seconds_bucket[5m]))"

# Export metrics to CSV
uv run python -c "
import requests
import pandas as pd

query = 'http_requests_total'
response = requests.get(f'http://localhost:9090/api/v1/query?query={query}')
data = response.json()
print(data)
"
```

---

## A.7 Reproducing Results

### A.7.1 Run H1 Evaluation (Hybrid > Pure)

```bash
cd experiments

# Run H1 evaluation in SIMULATED mode (for development/verification)
python -m evaluations.h1_evaluation

# Run H1 evaluation on REAL INFRASTRUCTURE
# Prerequisites:
# - k3d cluster running with test apps deployed
# - HAProxy running with weight adjustment enabled
# - Prometheus scraping all targets
# - GRU prediction server running (port 8090)
# - Routing daemon running (port 9104)
python -m evaluations.h1_evaluation --simulate=False

# Expected output:
# ======================================================================
# H1 Hypothesis Evaluation: Hybrid > Pure
# ======================================================================
# ...
# VERDICT: H1 PROVEN ✓

# Results saved to:
# - results/evaluations/h1/h1_raw_data_YYYYMMDD_HHMMSS.csv
# - results/evaluations/h1/h1_summary_YYYYMMDD_HHMMSS.json
# - results/evaluations/h1/h1_report_YYYYMMDD_HHMMSS.md
```

**H1 Programmatic Configuration:**

```python
from experiments.evaluations.h1_evaluation import H1Evaluator
from pathlib import Path

evaluator = H1Evaluator(
    results_dir=Path("results/evaluations/h1"),
    routing_daemon_url="http://localhost:9104",
    prometheus_url="http://localhost:9090",
)

result = evaluator.run_evaluation(
    scenarios=["s1-k8s-only", "s2-serverless-only", "s4-hybrid-predictive"],
    workloads=["steady", "spike", "endurance"],
    repetitions=3,
    simulate=False,  # Set to True for simulated mode
)

print(result.summary)
print(f"H1 Proven: {result.hypothesis_proven}")
```

**Estimated Time: 5-10 minutes** (simulated) / 2-4 hours (real infrastructure)

### A.7.2 Run H2 Evaluation (Predictive > Reactive)

```bash
cd experiments

# Run H2 evaluation in SIMULATED mode (for development/verification)
python -m evaluations.h2_evaluation

# Run H2 evaluation on REAL INFRASTRUCTURE
python -m evaluations.h2_evaluation --simulate=False

# Expected output:
# ======================================================================
# H2 Hypothesis Evaluation: Predictive > Reactive
# ======================================================================
# ...
# VERDICT: H2 PROVEN ✓

# Results saved to:
# - results/evaluations/h2/h2_raw_data_YYYYMMDD_HHMMSS.csv
# - results/evaluations/h2/h2_summary_YYYYMMDD_HHMMSS.json
# - results/evaluations/h2/h2_report_YYYYMMDD_HHMMSS.md
```

**H2 Programmatic Configuration:**

```python
from experiments.evaluations.h2_evaluation import H2Evaluator
from pathlib import Path

evaluator = H2Evaluator(
    results_dir=Path("results/evaluations/h2"),
    routing_daemon_url="http://localhost:9104",
    prometheus_url="http://localhost:9090",
    controller_metrics_url="http://localhost:9104/metrics",
    k6_duration_sec=300,
)

result = evaluator.run_evaluation(
    scenarios=["s3-hybrid-reactive", "s4-hybrid-predictive"],
    workloads=["spike", "endurance"],  # Focus on dynamic workloads
    repetitions=3,
    simulate=False,
)

print(result.summary)
print(f"H2 Proven: {result.hypothesis_proven}")
print(f"Violation Reduction: {result.violation_reduction:.1f}%")
print(f"Proactive Ratio: {result.proactive_ratio:.1%}")
```

**H2 Metrics Collected:**

| Metric | Source | Description |
|--------|--------|-------------|
| `slo_violations` | Prometheus counter | Count of p99 > 200ms events |
| `slo_violation_duration_sec` | Prometheus range query | Total time in violation |
| `proactive_adjustments` | Prometheus counter | PREDICTIVE decisions |
| `reactive_adjustments` | Prometheus counter | SCALE_OUT decisions |
| `avg_reaction_time_ms` | Prometheus histogram | Time from violation to adjustment |

**H2 Success Criteria:**
- SLO violations: >50% reduction (S4 vs S3)
- Proactive ratio: >50% of total adjustments

### A.7.3 Run Full Evaluation Suite

```bash
cd controller

# Run all evaluations
uv run python -m experiments.run_all_evaluations

# This runs:
# 1. H1 Evaluation (Hybrid vs Pure)
# 2. H2 Evaluation (Predictive vs Reactive)
# 3. Model comparison (GRU vs baselines)
# 4. Statistical significance tests
```

### A.7.4 Validate Model Comparison Results

```bash
# Check model comparison table
cat results/tables/model_comparison.csv

# Expected columns:
# Model,RMSE,RMSE_Percent,MAE,R2
# GRU,X.XX,Y.YY%,Z.ZZ,0.XX
# Linear,XX.XX,YY.YY%,ZZ.ZZ,0.XX
# ARIMA,XX.XX,YY.YY%,ZZ.ZZ,0.XX
```

### A.7.5 Reproduce Thesis Figures

```bash
cd controller

# Generate all figures for thesis
uv run python -m experiments.generate_figures

# Output:
# - results/figures/latency_comparison.png
# - results/figures/slo_violations.png
# - results/figures/cost_analysis.png
# - results/figures/prediction_accuracy.png
```

### A.7.6 Success Criteria

| Metric | Target | How to Verify |
|--------|--------|---------------|
| GRU RMSE | < 10% | Check `train_gru.py` output |
| H1: S4 vs S1 latency | > 15% improvement | Check `h1_summary.json` |
| H1: S4 vs S2 cost | > 20% improvement | Check `h1_summary.json` |
| H2: SLO violations | > 50% reduction | Check `h2_summary.json` |
| H2: Proactive ratio | > 50% | Check `h2_summary.json` |

---

## A.8 Troubleshooting

### A.8.1 Common Issues

#### Issue: UV sync fails

```bash
# Clear UV cache and retry
uv cache clean
uv sync --force

# If Python version mismatch
uv python install 3.11
uv sync
```

#### Issue: K3d cluster creation fails

```bash
# Delete existing cluster
k3d cluster delete hybrid-thesis

# Check Docker is running
docker ps

# Create cluster with verbose output
k3d cluster create hybrid-thesis --verbose
```

#### Issue: Knative pods not starting

```bash
# Check pod status
kubectl get pods -n knative-serving

# Check events for errors
kubectl describe pod <pod-name> -n knative-serving

# Check resource constraints
kubectl top nodes
```

#### Issue: HAProxy connection refused

```bash
# Check HAProxy logs
docker logs haproxy

# Verify config syntax
docker run --rm -v $(pwd)/haproxy.cfg:/etc/haproxy/haproxy.cfg:ro haproxy:alpine haproxy -c -f /etc/haproxy/haproxy.cfg

# Restart HAProxy
docker-compose restart haproxy
```

#### Issue: Prometheus not scraping targets

```bash
# Check targets status
curl http://localhost:9090/api/v1/targets

# Verify prometheus.yml configuration
cat infrastructure/monitoring/prometheus.yml

# Check network connectivity
docker network ls
docker network inspect sprint1-monitoring
```

#### Issue: Model training runs out of memory

```bash
# Reduce batch size in GRUConfig
# Edit ml_models/train_gru.py:
# config = GRUConfig(batch_size=16)  # Reduce from 32

# Or use smaller sequence length
# config = GRUConfig(sequence_length=30)  # Reduce from 60
```

### A.8.2 Verification Commands

```bash
# Full system health check
echo "=== Python Environment ==="
cd controller && uv run python --version

echo "=== Dependencies ==="
uv run python -c "import torch, pandas, sklearn; print('OK')"

echo "=== Kubernetes ==="
kubectl get nodes

echo "=== Docker ==="
docker ps

echo "=== HAProxy ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:8082/

echo "=== Prometheus ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:9090/-/healthy

echo "=== Model ==="
ls -la controller/data/models/gru_model.pt 2>/dev/null || echo "Model not trained"
```

### A.8.3 Resource Cleanup

```bash
# Stop all services
docker-compose -f infrastructure/haproxy/docker-compose.yml down
docker-compose -f infrastructure/monitoring/docker-compose.yml down

# Delete K3s cluster
k3d cluster delete hybrid-thesis

# Clean Docker resources
docker system prune -f

# Remove generated data (optional)
rm -rf results/evaluations/*/
rm -rf controller/data/models/*.pt
```

### A.8.4 Getting Help

If issues persist:

1. Check the [project README](../../README.md) for updates
2. Review [CLAUDE.md](../../CLAUDE.md) for architecture details
3. Search existing GitHub issues
4. Create a new issue with:
   - OS and version
   - Python version (`python --version`)
   - Docker version (`docker --version`)
   - Error message and stack trace
   - Steps to reproduce

---

## A.9 Quick Reference

### A.9.1 Key Commands

```bash
# Environment
uv sync                              # Install dependencies
uv run <script>                      # Run Python script

# Infrastructure
k3d cluster create hybrid-thesis     # Create K3s cluster
kubectl apply -f <file.yaml>         # Deploy K8s resources
docker-compose up -d                 # Start Docker services

# Experiments
./run-scenario.sh s4 steady          # Run scenario S4 with steady load
uv run -m experiments.evaluations.h1_evaluation  # Run H1 evaluation
uv run -m experiments.evaluations.h2_evaluation  # Run H2 evaluation

# Model Training
uv run -m ml_models.train_gru        # Train GRU model
uv run -m ml_models.model_comparison # Compare models
```

### A.9.2 Directory Structure

```
s2-thesis-kubernetes-serverless-integration/
├── controller/                  # Python routing controller
│   ├── intelligent_router/      # Algorithm 1 implementation
│   ├── prediction_engine/       # Prediction server
│   ├── monitoring_v2/           # SLO monitoring
│   └── data/models/             # Trained model files
├── data/                        # HTTP trace datasets
│   ├── raw/                     # Original log files
│   └── processed/               # Processed RPS parquet
├── experiments/                 # Evaluation scripts
│   └── evaluations/             # H1, H2 hypothesis tests
├── infrastructure/              # Deployment configs
│   ├── k3s/                     # K3s cluster config
│   ├── serverless/              # Knative manifests
│   ├── haproxy/                 # Traffic router config
│   └── monitoring/              # Prometheus setup
├── ml_models/                   # GRU and baseline models
└── results/                     # Evaluation outputs
    ├── evaluations/             # H1, H2 results
    ├── tables/                  # CSV result tables
    └── figures/                 # Generated charts
```

### A.9.3 Expected Results Summary

| Hypothesis | Metric | Expected Result |
|------------|--------|-----------------|
| H1 | S4 vs S1 p99 latency | 15-25% improvement |
| H1 | S4 vs S2 cost | 20-40% reduction |
| H2 | SLO violations | 50-75% reduction |
| H2 | Proactive ratio | >50% of adjustments |
| H3 | GRU RMSE | <10% |

---

**Document Version:** 1.0  
**Last Updated:** January 2026  
**Repository:** https://github.com/masrurimz/s2-thesis-kubernetes-serverless-integration
