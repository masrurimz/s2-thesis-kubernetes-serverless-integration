# Project Overview: Hybrid K8s-Serverless Integration

## What This Project Does

This research implements a hybrid architecture that combines:
- **Kubernetes clusters** for baseline warm operations
- **Serverless computing** for infinite scaling during traffic spikes  
- **Intelligent routing** using machine learning-based workload prediction

## Thesis Research Focus

**Title**: Decision Making and Elastic Scalability Management in Heterogeneous Cloud Environments Based on Workload Prediction

**Key Innovation**: ElaX algorithm enhanced with GRU-based prediction for tail latency optimization

## Quick Understanding (5 minutes)

### The Problem
- Traditional Kubernetes: Slow to scale, wastes resources during low load
- Pure Serverless: Expensive for sustained workloads, cold start latency
- **Solution**: Hybrid system that intelligently routes traffic based on real-time conditions

### How It Works
```
Normal Load (100 RPS)     →  Kubernetes Cluster (baseline capacity)
Traffic Spike (1000 RPS)  →  Serverless Functions (instant scale)  
Sustained High (800 RPS)  →  Back to Kubernetes (cost optimization)
```

### Key Components
1. **GRU Workload Predictor**: Predicts traffic 30 seconds ahead using real HTTP trace data
2. **Routing Controller**: Routes traffic based on SLO violations (tail latency >200ms)
3. **Resource Allocator**: Uses formal model R = α·x + β with OLS coefficient tuning
4. **Cost Optimizer**: Minimizes total cost while maintaining performance guarantees

## Implementation Approach

We follow an **incremental, agile methodology**:

### Sprint 1: Basic Hybrid (Week 1)
- Simple k3s + simulated serverless
- Manual traffic switching
- Basic monitoring

### Sprint 2: Automation (Week 2) 
- Simple load prediction
- Automated routing decisions
- Historical data collection

### Sprint 3: SLO Management (Week 3)
- Tail latency monitoring
- 5-second SLO violation detection
- Cost tracking

### Sprint 4: ML Integration (Week 4)
- GRU model training on real data
- 30-second prediction horizon
- Real-time inference

### Sprint 5: Full Thesis (Week 5)
- Complete ElaX implementation
- Formal evaluation
- Comparative analysis

## Expected Results

- **Workload-dependent cost ranking** (validated from measured run artifacts)
- **<200ms p95 latency** under normal load
- **<30 second scaling** response time
- **RMSE <10%** prediction accuracy

## Getting Started

1. **[Prerequisites](01-prerequisites.md)** - Install required tools
2. **[Quick Demo](02-quick-start.md)** - 15-minute working demo
3. **[Architecture Deep Dive](03-understanding-architecture.md)** - Technical details

## For Thesis Work

See **[thesis-implementation/](../thesis-implementation/)** for formal research documentation.

## For Development

See **[incremental-development/](../incremental-development/)** for sprint-by-sprint implementation guides.
