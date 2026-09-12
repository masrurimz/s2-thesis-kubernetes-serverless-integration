# Summary — 2026-09-11_clarknet-leakfree-paired-n5

- Date: 2026-09-11
- Git commit: ae5e1a1, bdc0cdf
- Scenarios: s3-hybrid-reactive, s4-hybrid-predictive
- Runs per scenario: 5 (status: in_progress)

## What ran

### s3-hybrid-reactive

- Runs: 5, passed the validity gate: 5
- Model artifact: n/a
- nodes_provisioned: 0
- first_provision_delay_sec: 0.0

### s4-hybrid-predictive

- Runs: 5, passed the validity gate: 5
- Model artifact: data/models/gru_model.pt (pytorch)
- nodes_provisioned: 0
- first_provision_delay_sec: 0.0

## Headline

Aggregates are means over gate-passing runs.

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | error rate | throughput (rps) | SLO violations | replica-seconds | serverless share (%) | valid |
|---|---|---|---|---|---|---|---|---|---|---|
| s3-hybrid-reactive | 5 | 69.1 | 87.9 | 103.7 | 0.0000 | 73.2 | 9.2 | 6154.5 | 33.2 | 5/5 |
| s4-hybrid-predictive | 5 | 69.4 | 91.9 | 120.5 | 0.0000 | 73.2 | 79.0 | 6823.5 | 28.9 | 5/5 |

## Paired comparison — s4-hybrid-predictive vs s3-hybrid-reactive

Pairs are matched by run id, in run order. 5 of 5 pairs passed the validity gate on both sides.

| Pair | s3-hybrid-reactive p99 (ms) | s4-hybrid-predictive p99 (ms) | Δ p99 (ms) | s3-hybrid-reactive SLO | s4-hybrid-predictive SLO | Δ SLO |
|---|---|---|---|---|---|---|
| run 1 | 98.7 | 127.8 | +29.1 | 1.0 | 98.0 | +97.0 |
| run 2 | 110.5 | 110.7 | +0.2 | 26.0 | 41.0 | +15.0 |
| run 3 | 101.3 | 108.8 | +7.5 | 2.0 | 5.0 | +3.0 |
| run 4 | 106.9 | 146.0 | +39.1 | 0.0 | 211.0 | +211.0 |
| run 5 | 101.2 | 109.3 | +8.0 | 17.0 | 40.0 | +23.0 |

- Mean Δp99 latency: +16.8 ms, paired Cohen's d: 1.02, exact one-sided permutation p: 0.0312 (clears 0.05).
- Mean ΔSLO violations: +69.8, paired Cohen's d: 0.80, exact one-sided permutation p: 0.0312 (clears 0.05).

## Forecast fidelity

| Scenario | eligible cycles | successful predictions | delivery rate | delivered |
|---|---|---|---|---|
| s3-hybrid-reactive | 0 | 0 | n/a | yes |
| s4-hybrid-predictive | 275 | 275 | 1.000 | yes |

## Node tier

| Scenario | node tier exercised | pending events | nodes provisioned | mean provisioning delay (s) |
|---|---|---|---|---|
| s3-hybrid-reactive | no | 0 | 0 | n/a |
| s4-hybrid-predictive | no | 0 | 0 | n/a |

## Caveats

- s3-hybrid-reactive run 1 never exercised the node tier.
- s3-hybrid-reactive run 2 never exercised the node tier.
- s3-hybrid-reactive run 3 never exercised the node tier.
- s3-hybrid-reactive run 4 never exercised the node tier.
- s3-hybrid-reactive run 5 never exercised the node tier.
- s4-hybrid-predictive run 1 never exercised the node tier.
- s4-hybrid-predictive run 2 never exercised the node tier.
- s4-hybrid-predictive run 3 never exercised the node tier.
- s4-hybrid-predictive run 4 never exercised the node tier.
- s4-hybrid-predictive run 5 never exercised the node tier.
