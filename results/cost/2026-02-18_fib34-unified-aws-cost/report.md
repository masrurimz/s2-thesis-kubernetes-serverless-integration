# Unified AWS Cost Analysis — fib(34) Validation

**Date:** 2026-02-18
**Source experiment:** `results/experiments/phase-b/2026-02-18_fib34-validation/`
**Analyzer:** `scripts/cost_analyzer.py` v5 → `cost_results.json`

## Unified AWS Cost per 1200s Run

| Component | S1 (K8s-only) | S2 (Serverless-only) | S3 (Hybrid Reactive) | S4 (Hybrid Predictive) |
|-----------|---:|---:|---:|---:|
| EKS control plane | $0.0333 | $0.0000 | $0.0333 | $0.0333 |
| EC2 compute | $0.0277 | $0.0000 | $0.0277 | $0.0277 |
| Lambda capacity | $0.0000 | $0.0017 | $0.0035 | $0.0035 |
| Lambda execution | $0.0000 | $0.0030 | $0.0076 | $0.0065 |
| Lambda requests | $0.0000 | $0.0176 | $0.0083 | $0.0112 |
| **Total** | **$0.0611** | **$0.0223** | **$0.0804** | **$0.0822** |

## Per-Million Request Costs

| Scenario | $/1M Requests | $/1M Successful |
|----------|--------------:|----------------:|
| S1 | $0.86 | $0.97 |
| S2 | $0.25 | $0.25 |
| S3 | $1.92 | $3.61 |
| S4 | $1.45 | $1.99 |

## Monthly Projection (30d Continuous)

| Scenario | AWS Total |
|----------|----------:|
| S1 | $132 |
| S2 | $48 |
| S3 | $174 |
| S4 | $178 |

## Crossover Points (S1 vs S2)

- fib(32): ~97.9 RPS
- fib(34): ~65.9 RPS
- fib(35): ~36.0 RPS

Graph: `results/cost/cost_crossover_rps.png`

## Evidence

- `results/cost/2026-02-18_fib34-unified-aws-cost/cost_results.json`
- `results/experiments/phase-b/2026-02-18_fib34-validation/`
