# Infrastructure

Hybrid K8s-Serverless platform infrastructure for thesis evaluation.

## Components

| Directory | Purpose | Technology |
|-----------|---------|------------|
| `k3s/` | Kubernetes cluster configuration | K3s (lightweight K8s) |
| `haproxy/` | Traffic router configuration | HAProxy |
| `serverless/` | Serverless function deployment | Knative |
| `monitoring/` | Metrics and observability | Prometheus |
| `load-tests/` | Performance testing scripts | k6 |
| `scripts/` | Automation and management | Bash |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TRAFFIC ROUTER (HAProxy)                  │
│                    infrastructure/haproxy/                   │
└─────────────┬───────────────────────────┬───────────────────┘
              │                           │
              ▼                           ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│   KUBERNETES (K3s)      │   │     SERVERLESS          │
│   infrastructure/k3s/   │   │   infrastructure/       │
│   • Cost-effective      │   │   serverless/           │
│   • Always warm         │   │   • Instant scale       │
│   • Baseline load       │   │   • Burst handling      │
└─────────────────────────┘   └─────────────────────────┘
```

## Quick Start

```bash
cd infrastructure

# Deploy full stack
./scripts/setup.sh

# Check health
./scripts/check-health.sh

# Teardown
./scripts/teardown.sh
```

## Load Testing

```bash
# Run steady load test (50 RPS, 3 min)
./load-tests/run-load-tests.sh steady

# Run spike test (50→200→50 RPS)
./load-tests/run-load-tests.sh spike

# Run endurance test (25 RPS, 30 min)
./load-tests/run-load-tests.sh endurance
```

## Validated Performance (Baseline)

| Metric | Value | Target |
|--------|-------|--------|
| p95 Latency | 23.41ms | < 150ms ✅ |
| Error Rate | 0% | < 0.1% ✅ |
| Distribution | 80/20 K8s/Knative | As configured ✅ |
| Resource Usage | 43% | < 80% ✅ |

## Thesis Mapping

This infrastructure supports the 4 evaluation scenarios:

| Scenario | Configuration |
|----------|---------------|
| S1: K8s-Only | HAProxy 100% → K8s |
| S2: Serverless-Only | HAProxy 100% → Knative |
| S3: Hybrid Reactive | HAProxy → both, no prediction |
| S4: Hybrid Predictive | HAProxy → both, with controller |
