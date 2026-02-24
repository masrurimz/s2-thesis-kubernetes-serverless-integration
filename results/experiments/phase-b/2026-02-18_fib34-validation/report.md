# Phase B Fib(34) Validation — Unified AWS Cost Mapping

**Date:** 2026-02-18
**Experiment:** `results/experiments/phase-b/2026-02-18_fib34-validation/`
**Workload:** ClarkNet trace replay, `fib(34)`, 1200s per scenario
**Analyzer:** `thesis/scripts/cost_analyzer.py` v5 → `controller/results/cost_analysis/cost_analysis_20260218_182512.json`

## Scenario Metrics

| Scenario | Total Req | Successful | Success Rate | p99 (ms) | SLO Violations | Serverless % |
|----------|----------:|-----------:|-------------:|---------:|---------------:|-------------:|
| s1-k8s-only | 70,599 | 62,751 | 88.9% | 23,138.8 | 7,848 | 0.0% |
| s2-serverless-only | 87,840 | 87,840 | 100.0% | 0.6 | 0 | 100.0% |
| s3-hybrid-reactive | 41,902 | 22,236 | 53.1% | 28,659.1 | 19,666 | 98.8% |
| s4-hybrid-predictive | 56,898 | 41,360 | 72.7% | 24,898.7 | 15,538 | 98.8% |

## Unified AWS Cost per 1200s Run

| Component | S1 | S2 | S3 | S4 |
|-----------|---:|---:|---:|---:|
| EKS control plane | $0.0333 | $0.0000 | $0.0333 | $0.0333 |
| EC2 compute | $0.0277 | $0.0000 | $0.0277 | $0.0277 |
| Lambda capacity | $0.0000 | $0.0017 | $0.0035 | $0.0035 |
| Lambda execution | $0.0000 | $0.0030 | $0.0076 | $0.0065 |
| Lambda requests | $0.0000 | $0.0176 | $0.0083 | $0.0112 |
| **Total** | **$0.0611** | **$0.0223** | **$0.0804** | **$0.0822** |

## Crossover Evidence

- **fib(34) crossover:** ~65.9 RPS (within experiment range ~50–73 RPS)
- **fib(32) crossover:** ~97.9 RPS (outside experiment range)
- **fib(35) crossover:** ~36.0 RPS

Graph: `results/cost/cost_crossover_rps.png`

## Comparison vs fib(32) Baseline

Baseline (fib32) totals from `results/cost/2026-02-17_three-model-cost-comparison/report.md`:
- S1 $0.0611, S2 $0.0451, S3 $0.0970, S4 $0.1044 (per 1200s)

fib(34) shifts the crossover into the measured RPS band and reduces S2 cost due to lower CPU-seconds per request under the fib(34) profile.

## Evidence Files

- `results/experiments/phase-b/2026-02-18_fib34-validation/s1-k8s-only_run1/result.json`
- `results/experiments/phase-b/2026-02-18_fib34-validation/s2-serverless-only_run1/result.json`
- `results/experiments/phase-b/2026-02-18_fib34-validation/s3-hybrid-reactive_run1/result.json`
- `results/experiments/phase-b/2026-02-18_fib34-validation/s4-hybrid-predictive_run1/result.json`
- `controller/results/cost_analysis/cost_analysis_20260218_182512.json`
