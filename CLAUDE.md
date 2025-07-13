# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Kubernetes & Serverless Integration thesis research project that implements a **hybrid k3s-serverless architecture** with intelligent traffic routing based on workload prediction and SLO monitoring.

### Research Focus

**Thesis Title**: "Decision Making and Elastic Scalability Management in Heterogeneous Cloud Environments Based on Workload Prediction"

The project implements a novel hybrid approach that intelligently routes traffic between cost-effective Kubernetes clusters and infinitely-scalable serverless functions using GRU neural networks and formal SLO monitoring.

### Architecture Evolution

The project follows an **incremental 5-sprint methodology**:

- **Sprint 1**: Basic hybrid foundation (k3s + Docker serverless simulation)
- **Sprint 2**: Automated load prediction with linear regression  
- **Sprint 3**: SLO-aware routing with 99th percentile latency monitoring
- **Sprint 4**: GRU neural network integration with real HTTP trace data
- **Sprint 5**: Complete ElaX algorithm implementation with formal evaluation

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

### Sprint Development

```bash
# Sprint 1: Basic Hybrid Foundation
cd docs/incremental-development/phase-1-basic-hybrid.md
# Follow day-by-day implementation plan

# Sprint 2: Load Prediction  
cd docs/incremental-development/phase-2-prediction.md
# Add linear regression and automated routing

# Sprint 3: SLO Monitoring
cd docs/incremental-development/phase-3-slo-monitoring.md  
# Implement Algorithm 1 and tail latency monitoring

# Sprint 4: GRU Integration
cd docs/incremental-development/phase-4-gru-integration.md
# Real dataset processing and neural networks

# Sprint 5: Full ElaX System
cd docs/incremental-development/phase-5-full-thesis.md
# Complete thesis implementation
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

# Check SLO compliance
python scripts/check_slo_compliance.py --threshold 200ms
```

### Resource Management

```bash
# Resource-constrained setup (8GB RAM)
docker run --memory="1g" --cpus="0.5" prometheus/prometheus
k3d cluster create constrained --agents 0 --resources.limits.memory=2Gi

# Full environment setup (16GB+ RAM)
docker-compose -f docker-compose-full.yml up -d
k3d cluster create full --agents 2 --resources.limits.memory=4Gi
```

## Documentation Structure

### Getting Started
- `docs/getting-started/01-prerequisites.md`: System requirements and installation
- `docs/getting-started/02-quick-start.md`: 15-minute hybrid demo
- `docs/getting-started/03-understanding-architecture.md`: Deep dive into components

### Incremental Development (5 Sprints)
- `docs/incremental-development/README.md`: Agile sprint methodology overview
- `docs/incremental-development/phase-1-basic-hybrid.md`: Foundation week
- `docs/incremental-development/phase-2-prediction.md`: Linear regression automation  
- `docs/incremental-development/phase-3-slo-monitoring.md`: Algorithm 1 + SLO monitoring
- `docs/incremental-development/phase-4-gru-integration.md`: Neural networks + real data
- `docs/incremental-development/phase-5-full-thesis.md`: Complete ElaX implementation

### Thesis Implementation
- `docs/thesis-implementation/`: Formal research documentation
- `docs/reference/`: Background materials and algorithm specifications
- `docs/archived/`: Historical documentation from previous approaches

### Code Components

- `apps/rust-app/v2-prometheus/`: Simple HTTP server with Prometheus metrics
- `monitoring/prometheus-v2-separate-cluster-client-server/`: Monitoring stack
- `autoscaler/experiment-6-odhi-scaler/`: Latest autoscaling experiments  
- `scripts/`: Utility scripts for setup, testing, and evaluation

## Hardware Constraints

### Minimum Requirements
- **Full Development**: 8+ cores, 32GB RAM
- **Resource-Constrained Testing**: 4+ cores, 8GB RAM (6GB usable)

### Sprint Resource Requirements
- **Sprint 1-2**: 4-6GB RAM (basic hybrid + prediction)
- **Sprint 3**: 6-8GB RAM (SLO monitoring stack)
- **Sprint 4-5**: 8-16GB RAM (GRU training + real datasets)

Resource-constrained configurations available for all sprints with reduced monitoring frequency and data retention.

## Development Workflow

1. **Choose Sprint**: Start with [Sprint 1](docs/incremental-development/phase-1-basic-hybrid.md)
2. **Check Prerequisites**: Verify system requirements and install dependencies
3. **Follow Daily Plans**: Each sprint has 5-day implementation schedule
4. **Validate at Each Step**: Ensure working system before proceeding
5. **Complete Sprint**: Mark todos as done, document learnings
6. **Proceed to Next**: Build on previous sprint's foundation

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

---

# 🧠 Claude Code Workflow

## 🔑 Core Principles

- **NO HIGH-LEVEL BULLSHIT** – Show real code, not vague suggestions.
- **Terse, expert-level, casual communication** – Get to the point.
- **Anticipate needs** – Offer solutions they haven't asked for yet.

---

## 📋 Task Management

- Use `TodoWrite` / `TodoRead` *aggressively* for complex or multi-step tasks.
- Break tasks into concrete, actionable items.
- Mark todos as done immediately after completion.
- Use todos as your battle plan – always structure complex ops around them.

---

## 🔍 Search & Analysis

- Use `Task` tool for multi-round open-ended investigation.
- **Batch** search operations (esp. Bash) to minimize latency.
- Prefer `rg` (ripgrep) over `grep`, `fd` over `find`, etc.
- Read and diff multiple files at once where analysis demands it.

---

## 🧬 Code Changes

- Always check `@nimbly-technologies/*` modules for internal libs/utilities.
- Match existing code patterns – review similar files before adding new logic.
- Add comments only where the logic isn't self-evident.
- Don't touch unrelated files – surgical edits only.

---

## 🗃️ Git Workflow

- Commit at *logical checkpoints* with clear commit messages.
- Format commit messages:
  - `feat:`, `fix:`, `refactor:`, `chore:`, etc. + short summary
- Do **not** squash – user will squash and rename commits later.
- Never push unless explicitly instructed.
- Don't run deployment scripts unless told to.

---

## 📁 File Ops

- CREATE markdown files to document implemented logic. 
- ALWAYS edit existing files if possible.
- NEVER delete MongoDB data without explicit confirmation.

---

## 🛠️ Tool Usage

- Batch all independent operations into single calls.
- Use absolute paths.
- Parallelize wherever possible:
  - e.g., `&` in Bash, `xargs -P`, background jobs.
- Use optimized tools (`rg`, `fd`, etc.) over slower legacy ones.

---

## 💬 Response Style

- Lead with the solution. Explain later, only if necessary.
- Show only relevant code (a few lines before/after).
- Reference files with this format:
  - `path/to/file.ts:42`
- Split large responses cleanly.
- No fluff. No filler.

---

## 🚫 What NOT to Do

- ❌ Don't update Git config
- ❌ Don't push to remote unless told to
- ❌ Don't deploy unless told to
- ❌ Don't touch unrelated DB entries
