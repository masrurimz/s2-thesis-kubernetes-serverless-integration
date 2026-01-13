# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Note**: LLM workflow standards have been moved to [AGENTS.md](./AGENTS.md). This file contains project-specific context only.

## Project Overview

This is a Kubernetes & Serverless Integration thesis research project that implements a **hybrid k3s-serverless architecture** with intelligent traffic routing based on workload prediction and SLO monitoring.

### Research Focus

**Thesis Title**: "Decision Making and Elastic Scalability Management in Heterogeneous Cloud Environments Based on Workload Prediction"

The project implements a novel hybrid approach that intelligently routes traffic between cost-effective Kubernetes clusters and infinitely-scalable serverless functions using GRU neural networks and formal SLO monitoring.

### Architecture Evolution

The project follows an **incremental 5-sprint methodology** optimized for LLM-assisted development:

| Sprint | Focus | Status | Duration |
|--------|-------|--------|----------|
| **Sprint 1** | Basic hybrid foundation (k3s + Knative serverless) | ✅ Complete | 1 day |
| **Sprint 2** | Automated load prediction with linear regression | 🔧 Validation needed | 1-2 days |
| **Sprint 3** | SLO-aware routing with 99th percentile latency monitoring | ⏳ Pending | 2-3 days |
| **Sprint 4** | GRU neural network integration with real HTTP trace data | ⏳ Pending | 3-5 days |
| **Sprint 5** | Complete ElaX algorithm implementation with formal evaluation | ⏳ Pending | 2-3 days |

**Total Project Duration**: 2-3 weeks (not months) with LLM assistance

### Key Components

- **Hybrid Traffic Router**: HAProxy with intelligent weight adjustment
- **Workload Predictor**: Evolution from linear regression → GRU neural networks
- **SLO Monitor**: Algorithm 1 implementation with tail latency tracking
- **Cost Optimizer**: Real-time cost analysis and optimization
- **Evaluation Framework**: RMSE accuracy and formal thesis validation

## Development Commands

### Quick Start (15 minutes)

```bash
# Get hybrid system running quickly
# See: docs/getting-started/02-quick-start.md

# Create k3s cluster
k3d cluster create demo-hybrid --agents 1 --port "8080:80@loadbalancer"

# Deploy test application
kubectl create deployment test-app --image=nginx:alpine
kubectl expose deployment test-app --port=80 --target-port=80

# Create serverless simulation
docker run -d --name serverless-sim -p 8081:80 nginx:alpine

# Setup traffic router (HAProxy)
docker run -d --name traffic-router -p 8082:8082 -v /tmp/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg haproxy:alpine
```

### Sprint-Specific Commands

**Sprint 1** (Basic Hybrid):
```bash
cd sprint-1
./scripts/setup.sh           # Deploy full stack
./scripts/check-health.sh    # Verify all components
./scripts/teardown.sh        # Clean up
```

**Sprint 2** (Intelligent Routing):
```bash
cd sprint-2
uv sync                                                    # Install deps
uv run python -m prediction_engine.prediction_server &     # Start prediction API
uv run python -m intelligent_router.routing_controller &   # Start routing
```

### Monitoring & Metrics

```bash
# Prometheus metrics
curl http://localhost:9090/api/v1/query?query=http_requests_total

# HAProxy stats
curl http://localhost:8404/stats

# System monitoring
kubectl top nodes
kubectl top pods
```

## Documentation Structure

### Getting Started
- `docs/getting-started/01-prerequisites.md`: System requirements
- `docs/getting-started/02-quick-start.md`: 15-minute hybrid demo
- `docs/getting-started/03-understanding-architecture.md`: Component deep dive

### Incremental Development (5 Sprints)
- `docs/incremental-development/README.md`: Agile sprint methodology
- `docs/incremental-development/phase-1-basic-hybrid.md`: Foundation week
- `docs/incremental-development/phase-2-prediction.md`: Linear regression automation
- `docs/incremental-development/phase-3-slo-monitoring.md`: Algorithm 1 + SLO monitoring

### Sprint Directories
- `sprint-1/`: Complete - Basic hybrid infrastructure
- `sprint-2/`: Validation needed - Intelligent routing + prediction engine

## Hardware Constraints

### Minimum Requirements
- **Full Development**: 8+ cores, 32GB RAM
- **Resource-Constrained Testing**: 4+ cores, 8GB RAM (6GB usable)

### Sprint Resource Requirements
- **Sprint 1-2**: 4-6GB RAM (basic hybrid + prediction)
- **Sprint 3**: 6-8GB RAM (SLO monitoring stack)
- **Sprint 4-5**: 8-16GB RAM (GRU training + real datasets)

## Key Research Elements

### Datasets
- **ClarkNet HTTP Traces**: 4M+ requests for real workload patterns
- **Calgary HTTP Traces**: Complementary dataset for validation
- **Synthetic Load**: Generated patterns for controlled testing

### Algorithms
- **Algorithm 1**: Thesis routing controller with 5-second SLO violation detection
- **ElaX Algorithm**: Base algorithm modified for hybrid environments
- **GRU Neural Networks**: 30-second workload prediction with RMSE <10%

### Evaluation Metrics
- **Prediction Accuracy**: RMSE measurement on real HTTP trace data
- **SLO Compliance**: 99th percentile latency <200ms target
- **Cost Optimization**: Hybrid vs pure k3s vs pure serverless analysis
- **Response Time**: Algorithm 1 detection and reaction speed
