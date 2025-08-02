# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Kubernetes & Serverless Integration thesis research project that implements a **hybrid k3s-serverless architecture** with intelligent traffic routing based on workload prediction and SLO monitoring.

### Research Focus

**Thesis Title**: "Decision Making and Elastic Scalability Management in Heterogeneous Cloud Environments Based on Workload Prediction"

The project implements a novel hybrid approach that intelligently routes traffic between cost-effective Kubernetes clusters and infinitely-scalable serverless functions using GRU neural networks and formal SLO monitoring.

### Architecture Evolution

The project follows an **incremental 5-sprint methodology** optimized for LLM-assisted development:

- **Sprint 1**: Basic hybrid foundation (k3s + Knative serverless) - _1 day with LLM_
- **Sprint 2**: Automated load prediction with linear regression - _1-2 days with LLM_
- **Sprint 3**: SLO-aware routing with 99th percentile latency monitoring - _2-3 days with LLM_
- **Sprint 4**: GRU neural network integration with real HTTP trace data - _3-5 days (ML training)_
- **Sprint 5**: Complete ElaX algorithm implementation with formal evaluation - _2-3 days with LLM_

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
- **LLM-AWARE DEVELOPMENT** – Use burst implementation + validation cycles, not human time estimates.

---

## 📋 Task Management

- Use `TodoWrite` / `TodoRead` _aggressively_ for complex or multi-step tasks.
- Break tasks into concrete, actionable items.
- Mark todos as done immediately after completion.
- Use todos as your battle plan – always structure complex ops around them.
- **LLM Planning**: Estimate in "execution blocks" (15-30 min) not hours/days.
- **Context Batching**: Group related tasks by domain/component for parallel execution.

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

- Commit at _logical checkpoints_ with clear commit messages.
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
- **LLM Optimization**: Create 5-10 related files simultaneously in burst implementation.
- **Validation Cycles**: Plan explicit human testing phases between implementation bursts.

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
- ❌ Don't use human time estimates (hours/days) for LLM-capable tasks
- ❌ Don't plan sequential tasks that can be executed in parallel batches

---

## 🚀 LLM Development Guidelines

**Reference**: See `CLAUDE-LLM-METHODOLOGY.md` for complete methodology

### Core LLM Approach

- **Execution Blocks**: 15-30 minute focused implementation bursts
- **Context Batching**: Group related tasks (configs, docs, scripts) together
- **Burst + Validate**: Implementation → Human Testing → Feedback → Next Burst
- **Parallel Creation**: Generate 5-10 related files simultaneously

### LLM Strengths (Leverage)

- Configuration generation (YAML, JSON, configs)
- Pattern-based implementation following existing conventions
- Documentation created simultaneously with code
- Parallel execution of related tasks

### LLM Limitations (Account For)

- Complex multi-system debugging requires human feedback
- Integration validation needs real-world testing
- Performance optimization requires iterative measurement
- Domain expertise and business logic validation

### Estimation Framework

- **Simple**: 1 execution block (single component, docs, scripts)
- **Medium**: 2-3 execution blocks (multi-component integration)
- **Complex**: Multiple burst + validation cycles (system-wide changes)

Always plan with LLM reality: Sprint 1 = 1 day actual (not 5 days traditional)

---

## 🤝 User-LLM Validation Collaboration

### Role Separation

**LLM Role**:
- Code validation, syntax checking, import testing
- Analysis of user feedback and error messages
- Configuration generation and pattern implementation
- Documentation updates and logic verification

**User Role**:
- Execute long-running services (servers, monitoring, prediction engines)
- Integration testing and performance measurement
- Manual verification of system behavior
- Resource management and process monitoring

### Handoff Protocol

**Phase 1 (LLM Implementation)**:
- LLM provides specific commands for user execution
- Clear step-by-step instructions with expected outputs
- Error handling guidance and troubleshooting steps

**Phase 2 (User Execution)**:
- User executes services and reports results
- Captures logs, error messages, and performance metrics
- Tests integration points and validates behavior

**Phase 3 (Collaborative Analysis)**:
- User reports findings back to LLM with specific details
- LLM analyzes feedback and provides next steps
- Iterative refinement based on real-world testing

### Example Workflow

```bash
# LLM provides commands like:
uv run prediction-server --debug
# User executes and reports: "Server started on port 8000, logs show..."

# LLM analyzes feedback:
# "Based on your logs, the prediction accuracy is 85%. Let's optimize..."
```

---

## 📦 UV Package Management Usage

### Core UV Commands

```bash
# Project setup and dependency management
uv sync                    # Install dependencies from pyproject.toml
uv lock                    # Update dependency lock file
uv add package-name        # Add new dependency
uv remove package-name     # Remove dependency

# Script execution patterns
uv run script.py                    # Run Python script
uv run -m module.name              # Run module directly
uv run prediction-server           # Run defined script from pyproject.toml
uv run --script training-pipeline  # Run specific project script
```

### Project Scripts Integration

**Defined in pyproject.toml**:
```toml
[project.scripts]
prediction-server = "intelligent_router.prediction_server:main"
routing-controller = "intelligent_router.routing_controller:main"
load-generator = "scripts.load_generator:main"
```

**Usage**:
```bash
# Development testing
uv run prediction-server --port 8000 --debug
uv run routing-controller --config config/routing.yml
uv run load-generator --duration 300 --rps 50

# Module imports and testing
uv run -m intelligent_router.prediction_engine
uv run -m pytest tests/
```

### Common Patterns

- **Development**: `uv run` for all script execution
- **Testing**: `uv run -m pytest` or `uv run test-script`
- **Services**: Use project scripts for long-running services
- **Environment**: `uv sync` before each development session

---

## 🔄 Subagent Context Management

### When to Use Subagents

**Large File Updates**:
- Multi-file documentation updates
- Extensive codebase refactoring
- Complex configuration changes across multiple files

**Extensive Research**:
- Multi-round analysis of system architecture
- Deep investigation of performance issues
- Comprehensive pattern analysis across codebase

**Context-Heavy Tasks**:
- When main conversation context approaches limits
- Complex debugging requiring multiple tool iterations
- Large-scale code review and optimization

### Delegation Patterns

**Research Subagents**:
```
Task: "Analyze prediction accuracy patterns in Sprint 2 results"
Scope: Limited to /sprint-2/results/ and related metrics
Output: Summary report for main conversation
```

**Implementation Subagents**:
```
Task: "Update all configuration files for Sprint 3 SLO monitoring"
Scope: Config files, documentation, setup scripts
Output: Ready-to-execute implementation plan
```

**Analysis Subagents**:
```
Task: "Review HAProxy routing logic and suggest optimizations"
Scope: Routing components and performance data
Output: Specific optimization recommendations
```

### Integration Protocol

1. **Delegation**: Main conversation creates focused subagent task
2. **Execution**: Subagent performs deep analysis/implementation
3. **Integration**: Subagent provides summary and actionable items
4. **Continuation**: Main conversation proceeds with subagent findings

### Context Preservation

- Subagents maintain focus on specific domains/components
- Main conversation preserves overall project context
- Integration points clearly defined for knowledge transfer
- Prevents main conversation context exhaustion

---

## ✅ Sprint Validation Workflow

### Sprint 1 + Sprint 2 Integration

**Foundation (Sprint 1)**:
- Basic hybrid k3s + serverless architecture
- HAProxy traffic routing with static weights
- Container orchestration and basic monitoring

**Intelligence Layer (Sprint 2)**:
- Linear regression prediction engine
- Automated weight adjustment based on predictions
- Performance metrics collection and analysis

### Validation Phase Structure

**Phase 1: Code Validation (LLM)**
```bash
# LLM validates syntax and logic
uv run -m intelligent_router.prediction_engine  # Import test
uv run --check routing_controller.py            # Syntax validation
uv run -m pytest tests/test_prediction.py       # Unit tests
```

**Phase 2: Service Execution (User)**
```bash
# User executes long-running services
uv run prediction-server --port 8000 &
uv run routing-controller --interval 30 &
docker-compose up -d monitoring-stack

# User monitors and reports
curl http://localhost:8000/predict
tail -f logs/prediction-server.log
```

**Phase 3: Performance Analysis (Collaborative)**
```bash
# User collects metrics
curl http://localhost:9090/api/v1/query?query=prediction_accuracy
kubectl top pods
docker stats

# LLM analyzes user feedback
# "Prediction accuracy: 87%, latency: 45ms, memory usage: 120MB"
# "Routing decisions: 73% k3s, 27% serverless"
```

### Commands for User Execution

**Sprint 1 Validation**:
```bash
# Verify hybrid system is operational
kubectl get pods -A
curl http://localhost:8080/health    # k3s endpoint
curl http://localhost:8081/health    # serverless endpoint
curl http://localhost:8082/stats     # HAProxy stats
```

**Sprint 2 Validation**:
```bash
# Start prediction services
uv run prediction-server --config config/prediction.yml
uv run routing-controller --log-level debug

# Generate test load
uv run load-generator --pattern increasing --duration 600

# Monitor prediction accuracy
watch "curl -s http://localhost:8000/metrics | grep accuracy"
```

### Expected Outputs for LLM Analysis

**Performance Metrics**:
- Prediction accuracy percentage
- Response latency measurements
- Resource utilization (CPU, memory)
- Routing decision distribution

**Error Patterns**:
- Service startup logs
- Prediction engine error messages
- Routing controller decisions
- System resource constraints

**Integration Status**:
- Service communication health
- Data flow between components
- Configuration validation results
- End-to-end system behavior
