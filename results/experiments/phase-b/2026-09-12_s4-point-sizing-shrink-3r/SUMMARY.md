# Summary — 2026-09-12_s4-point-sizing-shrink-3r

- Date: 2026-09-12
- Git commit: 0618d80
- Scenarios: s4-hybrid-predictive
- Runs per scenario: 3 (status: in_progress)

## What ran

### s4-hybrid-predictive

- Runs: 3, passed the validity gate: 3
- Model artifact: data/models/gru_model.pt (pytorch)
- nodes_provisioned: 1
- first_provision_delay_sec: run1=96.6713433265686, run2=93.68661284446716, run3=118.55681920051575

## Headline

Aggregates are means over gate-passing runs.

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | error rate | throughput (rps) | SLO violations | replica-seconds | serverless share (%) | valid |
|---|---|---|---|---|---|---|---|---|---|---|
| s4-hybrid-predictive | 3 | 64.4 | 549.9 | 2174.4 | 0.0000 | 73.1 | 7280.3 | 6407.5 | 31.4 | 3/3 |

## Forecast fidelity

| Scenario | eligible cycles | successful predictions | delivery rate | delivered |
|---|---|---|---|---|
| s4-hybrid-predictive | 171 | 171 | 1.000 | yes |

## Node tier

| Scenario | node tier exercised | pending events | nodes provisioned | mean provisioning delay (s) |
|---|---|---|---|---|
| s4-hybrid-predictive | yes | 3 | 3 | 103.0 |

## Caveats

None.
