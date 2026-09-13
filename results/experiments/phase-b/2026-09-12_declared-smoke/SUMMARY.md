# Summary — 2026-09-12_declared-smoke

- Date: 2026-09-12
- Git commit: 7ff529a
- Scenarios: s3-hybrid-reactive, s4-hybrid-predictive
- Runs per scenario: 2 (status: in_progress)

## What ran

### s3-hybrid-reactive

- Runs: 1, passed the validity gate: 1
- Model artifact: n/a
- nodes_provisioned: 3
- first_provision_delay_sec: 65.01591348648071

### s4-hybrid-predictive

- Runs: 1, passed the validity gate: 1
- Model artifact: data/models/gru_model.pt (pytorch)
- nodes_provisioned: 2
- first_provision_delay_sec: 64.83525037765503

## Headline

Aggregates are means over gate-passing runs.

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | ramp p99 (ms) | error rate | throughput (rps) | SLO violations | replica-seconds | serverless share (%) | valid |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s3-hybrid-reactive | 1 | 64.4 | 104.7 | 517.6 | n/a | 0.0000 | 73.2 | 0.0 | 6810.0 | 27.1 | 1/1 |
| s4-hybrid-predictive | 1 | 64.3 | 127.4 | 254.3 | n/a | 0.0000 | 73.2 | 0.0 | 7455.0 | 16.5 | 1/1 |

ramp p99 (co-primary): unavailable — this bundle's k6 summaries predate per-stage recording.

## Paired comparison — s4-hybrid-predictive vs s3-hybrid-reactive

Pairs are matched by run id, in run order. 1 of 1 pairs passed the validity gate on both sides.

| Pair | s3-hybrid-reactive p99 (ms) | s4-hybrid-predictive p99 (ms) | Δ p99 (ms) | s3-hybrid-reactive SLO | s4-hybrid-predictive SLO | Δ SLO |
|---|---|---|---|---|---|---|
| run 1 | 517.6 | 254.3 | -263.3 | 0.0 | 0.0 | +0.0 |

- Mean Δp99 latency: -263.3 ms, paired Cohen's d: n/a, exact one-sided permutation p (H1: S4 faster): 0.5000 (does not clear 0.05).
- Mean ΔSLO violations: +0.0, paired Cohen's d: n/a, exact one-sided permutation p (H1: S4 faster): 1.0000 (does not clear 0.05).

## Forecast fidelity

| Scenario | eligible cycles | successful predictions | delivery rate | delivered |
|---|---|---|---|---|
| s3-hybrid-reactive | 0 | 0 | n/a | yes |
| s4-hybrid-predictive | 57 | 57 | 1.000 | yes |

## Node tier

| Scenario | node tier exercised | pending events | nodes provisioned | mean provisioning delay (s) |
|---|---|---|---|---|
| s3-hybrid-reactive | yes | 3 | 3 | 65.0 |
| s4-hybrid-predictive | yes | 52 | 2 | 64.8 |

## Caveats

None.
