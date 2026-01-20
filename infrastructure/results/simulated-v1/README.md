# Simulated Serverless Experiments (v1)

**Date:** 2026-01-18  
**Status:** Archived - Simulation-based validation

## Experiment Configuration

### Serverless Simulation

These experiments used a **custom serverless-activator** (Go proxy) instead of real Knative:

| Aspect | This Experiment | Real Knative |
|--------|-----------------|--------------|
| Cold start | Deterministic 5s | Variable 100ms-10s |
| Scale-to-zero | Custom idle checker (30s TTL) | Native Knative activator |
| Activation | K8s Deployment scale 0→1 | Knative Pod Autoscaler |
| Reproducibility | High | Cluster-state dependent |

### Weight Configuration

- **Default weights:** 80% K8s / 20% Serverless (not 100/0 as intended)
- **Impact:** Serverless always received traffic, even during baseline

### Infrastructure

- `test-app-warm`: K8s steady-state backend (50m-200m CPU)
- `test-app-cold`: Serverless workload (5s init delay simulates cold start)
- `serverless-activator`: Go proxy that scales test-app-cold 0↔1
- HAProxy: Traffic routing with dynamic weight adjustment

## Results Summary

| Scenario | Error Rate | p95 Latency | Throughput |
|----------|------------|-------------|------------|
| S1 (K8s Only) | 72.62% | 60,002ms | 13.7 req/s |
| S2 (Serverless Only) | 92.83% | 23,158ms | 45.8 req/s |
| S3 (Hybrid Reactive) | 0% | 5.7ms | 65.7 req/s |
| S4 (Hybrid Predictive) | 0% | 5.7ms | 65.8 req/s |

## Hypothesis Validation

- **H1 Validated:** Hybrid routing (S3/S4) dramatically outperformed pure backends (S1/S2)
- **H2 Validated:** GRU prediction enabled 4 preemptive SCALE_OUT decisions

## Files

| File | Description |
|------|-------------|
| `s1-k8s-only/` | Pure K8s scenario results |
| `s2-serverless-only/` | Pure serverless scenario results |
| `s3-spike-summary.json` | Hybrid reactive (Algorithm 1 only) |
| `s4-spike-summary.json` | Hybrid predictive (Algorithm 1 + GRU) |
| `stress-test/` | Extended stress test with daemon logs |

## Validity Statement

These results are valid for **simulation-based validation** of the hybrid routing hypothesis. The custom activator provides:

1. **Reproducibility:** Deterministic 5s cold start enables consistent comparison
2. **Controlled variables:** Isolates routing algorithm behavior from Knative variability
3. **Proof of concept:** Demonstrates Algorithm 1/2 effectiveness

### Limitations

1. Cold start timing doesn't reflect real cloud function behavior
2. Single-pod K8s backend limits scalability validation
3. 80/20 default means serverless was always warm

### Recommended Follow-up

Run `knative-real` experiments with:
- Real Knative Service with native scale-to-zero
- 100% K8s / 0% serverless default weights
- Algorithm 1 SCALE_OUT enables serverless dynamically
