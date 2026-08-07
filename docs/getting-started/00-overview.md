# Project Overview

This project evaluates a hybrid Kubernetes + serverless control plane for tail-latency-sensitive workloads.

- Kubernetes provides warm, capacity-limited replicas.
- Knative provides elastic overflow.
- Algorithm 1 V3 routes using observed load, observed ready capacity, and HAProxy rtime-derived p99.
- A GRU forecast is confidence-gated and feeds Algorithm 2 Kubernetes replica scaling; it does not directly set routing weights.

## Final research configuration

- Workload: deterministic `/fib?n=33` CPU endpoint.
- GRU training: synthetic diurnal, burst, and ramp series.
- ClarkNet and Calgary: validation corpora; ClarkNet is also replayed for evaluation.
- Forecast: 9 samples × 15 seconds = **135 seconds**.
- Primary SLO: **p99 < 200 ms**.
- Scenarios: S1 K8s + HPA, S2 serverless-only, S3 hybrid-reactive, S4 hybrid-predictive.

## How the control loop works

```text
observed RPS -> Algorithm 1 V3 -> HAProxy K8s/Knative weights
      |
      +-> GRU confidence-gated forecast -> Algorithm 2 replica target
```

The forecast enables proactive Kubernetes capacity. Routing reacts to observed capacity and trend, so a forecast error cannot directly force an expensive serverless weight.

## Final evidence snapshot

- H2 definitive paired n=5: S3 mean p99 188.5 ms; S4 126.0 ms; p=0.0304; d=-1.26; both USD 163 proxy cost.
- H1 directional n=1: S4 118.2 ms versus S1 2,421.3 ms.

These results support the stated testbed comparison only. H1 is not inferential, and cost is a directional proxy.

## Current entry points

```bash
uv run thesis infra apply-resources
uv run thesis infra deploy-app
uv run thesis infra health
uv run thesis-experiment preflight
uv run thesis-experiment run --phase full --runs 5 --duration 300
```

Services use prediction port 8090, routing port 9104, Prometheus 9090, HAProxy HTTP 18082, and HAProxy stats 18404. See [Architecture](03-understanding-architecture.md) and [Running Experiments](../thesis-implementation/03-running-experiments.md) for the complete flow.
