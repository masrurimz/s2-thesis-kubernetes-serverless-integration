# Sprint 1: Basic Hybrid Foundation

**Goal**: Build fundamental hybrid k3s-serverless architecture with manual traffic control and basic monitoring.

## Quick Start

### Prerequisites

- Docker running with 6GB+ RAM allocated
- kubectl and k3d installed
- k6 installed for load testing

### Setup (5 minutes)

```bash
# Deploy entire hybrid system
./scripts/setup.sh

# Verify deployment
./scripts/check-health.sh

# Test traffic distribution
./scripts/test-traffic.sh
```

### Usage

```bash
# Access hybrid endpoint
curl http://localhost:8082

# View HAProxy stats
open http://localhost:8404/stats

# View Prometheus metrics
open http://localhost:9090

# Adjust traffic weights manually
./scripts/adjust-weights.sh 60 40  # 60% k3s, 40% serverless
```

### Load Testing

```bash
# Run all load tests
./scripts/run-load-tests.sh

# Individual tests
k6 run load-testing/steady-load.js
k6 run load-testing/spike-load.js
k6 run load-testing/endurance-test.js
```

### Cleanup

```bash
# Remove all components
./scripts/teardown.sh
```

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Testing  │    │ Traffic Router  │    │   K3s Cluster   │
│   (k6 scripts)  │───►│   (HAProxy)     │───►│   (nginx app)   │
│   Port: N/A     │    │   Port: 8082    │    │   Port: 8080    │
└─────────────────┘    │                 │    └─────────────────┘
                       │                 │           │
                       │                 │    ┌─────────────────┐
                       │                 │───►│ Serverless Sim  │
                       │                 │    │(Knative Service)│
                       └─────────────────┘    │ Port: 8081      │
                              │               └─────────────────┘
                       ┌─────────────────┐           │
                       │   Monitoring    │◄──────────┘
                       │  (Prometheus)   │
                       │   Port: 9090    │
                       └─────────────────┘
```

## Components

### Core Infrastructure

- **K3s Cluster** (`infrastructure/k3s/`): Cost-effective primary backend
- **Knative Serverless** (`infrastructure/serverless/`): Authentic serverless with scale-to-zero
- **HAProxy Router** (`infrastructure/haproxy/`): Intelligent traffic distribution
- **Prometheus Monitoring** (`infrastructure/monitoring/`): Metrics collection

### Automation Scripts

- **Setup/Teardown** (`scripts/`): System lifecycle management
- **Testing** (`scripts/`): Health checks and traffic validation
- **Operations** (`scripts/`): Manual weight adjustment and monitoring

### Load Testing

- **Steady Load** (`load-testing/steady-load.js`): Constant 50 RPS test
- **Traffic Spike** (`load-testing/spike-load.js`): 50→200→50 RPS simulation
- **Endurance** (`load-testing/endurance-test.js`): 30-minute stability test

## Resource Requirements

### Constrained Environment (6GB Usable RAM)

| Component       | RAM       | CPU      | Port |
| --------------- | --------- | -------- | ---- |
| K3s Cluster     | 2GB       | 1.0      | 8080 |
| Knative Serving | 200MB     | 0.25     | -    |
| Knative Pods    | 128MB     | 0.1      | 8081 |
| HAProxy         | 256MB     | 0.25     | 8082 |
| Prometheus      | 1GB       | 0.25     | 9090 |
| **Total**       | **4.1GB** | **1.85** | -    |

## Success Criteria

- ✅ Traffic routes between k3s cluster and serverless simulation
- ✅ Manual traffic weight adjustment works under load
- ✅ System stable for 30+ minute test periods
- ✅ Resource usage within 6GB RAM constraints
- ✅ Response times: p95 < 150ms (normal), p95 < 300ms (spike)
- ✅ Error rate < 2% under all load conditions

## Documentation

- **[PRD](../docs/sprint-1/PRD-basic-hybrid-foundation.md)**: Product requirements and business goals
- **[TDD](../docs/sprint-1/TDD-basic-hybrid-architecture.md)**: Technical design and architecture
- **[Progress Tracker](../docs/sprint-1/implementation-progress.md)**: Day-by-day implementation progress
- **Setup Guide** (`docs/setup-guide.md`): Detailed setup instructions
- **Operations Manual** (`docs/operations-manual.md`): Day-to-day operations
- **Troubleshooting** (`docs/troubleshooting.md`): Common issues and solutions

## Results and Analysis

- **Performance Baseline** (`results/performance-baseline.md`): Load testing results
- **Resource Utilization** (`results/resource-utilization.md`): Resource usage analysis
- **Cost Analysis** (`results/cost-analysis.md`): Cost calculation baseline
- **Lessons Learned** (`results/lessons-learned.md`): Sprint retrospective

## Implementation Status

**Current Phase**: Documentation Complete - Ready for Implementation

See [implementation-progress.md](../docs/sprint-1/implementation-progress.md) for detailed day-by-day progress tracking.

## Next Steps

1. **Day 1**: Setup k3s cluster and serverless simulation
2. **Day 2**: Implement HAProxy traffic router with manual control
3. **Day 3**: Add Prometheus monitoring and basic metrics
4. **Day 4**: Create load testing framework and validate performance
5. **Day 5**: Complete documentation and stability testing

**Sprint 2 Preview**: Add automated load prediction and intelligent routing decisions based on historical patterns.
