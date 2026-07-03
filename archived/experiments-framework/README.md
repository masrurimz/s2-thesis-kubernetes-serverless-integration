# Experiments

This directory contains all experiment configurations, runs, and tracking for thesis evaluation.

## Structure

```
experiments/
├── scenarios/           # 4 evaluation scenarios (from thesis 3.5.2)
│   ├── s1-k8s-only/    # Baseline: all traffic → Kubernetes
│   ├── s2-serverless-only/  # Baseline: all traffic → Serverless
│   ├── s3-hybrid-reactive/  # Control: Algorithm 1, no prediction
│   └── s4-hybrid-predictive/  # Proposed: Algorithm 1 + GRU prediction
├── workloads/          # Load test configurations
│   ├── steady.yaml     # Constant load pattern
│   ├── spike.yaml      # Burst traffic pattern
│   └── endurance.yaml  # Long-running stability test
├── runs/               # Timestamped experiment outputs
└── experiments.db      # SQLite tracking database
```

## Hypothesis Mapping

| Comparison | Proves | Expected Outcome |
|------------|--------|------------------|
| S4 vs S1 | H1: Hybrid > K8s | Lower p99 during spikes |
| S4 vs S2 | H1: Hybrid > Serverless | Lower cost at steady load |
| S4 vs S3 | H2: Predictive > Reactive | Fewer SLO violations |

## Running Experiments

```bash
# Run single scenario
./run-scenario.sh s1 steady

# Run full comparison
./run-experiment.sh --scenarios s1,s2,s3,s4 --workloads steady,spike --reps 3
```

## Metrics Collected

- **Latency**: p50, p95, p99 (ms)
- **Errors**: Error rate (%)
- **Throughput**: Requests/second
- **Resources**: CPU/Memory utilization
- **Cost**: Resource-hours proxy
