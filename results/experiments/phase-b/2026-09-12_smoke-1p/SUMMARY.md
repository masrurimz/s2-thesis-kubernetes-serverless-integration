# Summary — 2026-09-12_smoke-1p

- Date: 2026-09-12
- Git commit: 7ff529a
- Scenarios: s3-hybrid-reactive, s4-hybrid-predictive
- Runs per scenario: 2 (status: in_progress)

## What ran

### s3-hybrid-reactive

- Runs: 1, passed the validity gate: 1
- Model artifact: n/a
- nodes_provisioned: 1
- first_provision_delay_sec: 120.06962275505066

### s4-hybrid-predictive

- Runs: 1, passed the validity gate: 1
- Model artifact: data/models/gru_model.pt (pytorch)
- nodes_provisioned: 1
- first_provision_delay_sec: 74.88822722434998

## Headline

Aggregates are means over gate-passing runs.

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | error rate | throughput (rps) | SLO violations | replica-seconds | serverless share (%) | valid |
|---|---|---|---|---|---|---|---|---|---|---|
| s3-hybrid-reactive | 1 | 64.6 | 409.9 | 1785.0 | 0.0000 | 73.2 | 5868.0 | 6187.5 | 25.9 | 1/1 |
| s4-hybrid-predictive | 1 | 64.4 | 626.6 | 2706.3 | 0.0000 | 73.0 | 5963.0 | 6772.5 | 25.9 | 1/1 |

## Paired comparison — s4-hybrid-predictive vs s3-hybrid-reactive

Pairs are matched by run id, in run order. 1 of 1 pairs passed the validity gate on both sides.

| Pair | s3-hybrid-reactive p99 (ms) | s4-hybrid-predictive p99 (ms) | Δ p99 (ms) | s3-hybrid-reactive SLO | s4-hybrid-predictive SLO | Δ SLO |
|---|---|---|---|---|---|---|
| run 1 | 1785.0 | 2706.3 | +921.3 | 5868.0 | 5963.0 | +95.0 |

- Mean Δp99 latency: +921.3 ms, paired Cohen's d: n/a, exact one-sided permutation p (H1: S4 faster): 1.0000 (does not clear 0.05).
- Mean ΔSLO violations: +95.0, paired Cohen's d: n/a, exact one-sided permutation p (H1: S4 faster): 1.0000 (does not clear 0.05).

## Forecast fidelity

| Scenario | eligible cycles | successful predictions | delivery rate | delivered |
|---|---|---|---|---|
| s3-hybrid-reactive | 0 | 0 | n/a | yes |
| s4-hybrid-predictive | 57 | 57 | 1.000 | yes |

## Node tier

| Scenario | node tier exercised | pending events | nodes provisioned | mean provisioning delay (s) |
|---|---|---|---|---|
| s3-hybrid-reactive | yes | 1 | 1 | 120.1 |
| s4-hybrid-predictive | yes | 1 | 1 | 74.9 |

## Caveats

None.
