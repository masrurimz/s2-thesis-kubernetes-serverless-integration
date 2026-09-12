# Summary — 2026-09-12_s4-point-sizing-3r

- Date: 2026-09-12
- Git commit: 0618d80, e3ba3e0
- Scenarios: s4-hybrid-predictive
- Runs per scenario: 3 (status: in_progress)

## What ran

### s4-hybrid-predictive

- Runs: 3, passed the validity gate: 3
- Model artifact: data/models/gru_model.pt (pytorch)
- nodes_provisioned: 1
- first_provision_delay_sec: run1=89.72089219093323, run2=64.78858280181885, run3=122.80915570259094

## Headline

Aggregates are means over gate-passing runs.

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | error rate | throughput (rps) | SLO violations | replica-seconds | serverless share (%) | valid |
|---|---|---|---|---|---|---|---|---|---|---|
| s4-hybrid-predictive | 3 | 64.4 | 435.4 | 1536.0 | 0.0001 | 73.0 | 4239.0 | 6592.5 | 28.6 | 3/3 |

## Forecast fidelity

| Scenario | eligible cycles | successful predictions | delivery rate | delivered |
|---|---|---|---|---|
| s4-hybrid-predictive | 170 | 170 | 1.000 | yes |

## Node tier

| Scenario | node tier exercised | pending events | nodes provisioned | mean provisioning delay (s) |
|---|---|---|---|---|
| s4-hybrid-predictive | yes | 3 | 3 | 92.4 |

## Caveats

None.
