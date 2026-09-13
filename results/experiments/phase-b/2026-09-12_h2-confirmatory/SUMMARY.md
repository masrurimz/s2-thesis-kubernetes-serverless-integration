# Summary — 2026-09-12_h2-confirmatory

- Date: 2026-09-12
- Git commit: 7ff529a
- Scenarios: s3-hybrid-reactive, s4-hybrid-predictive
- Runs per scenario: 10 (status: in_progress)

## What ran

### s3-hybrid-reactive

- Runs: 5, passed the validity gate: 5
- Model artifact: n/a
- nodes_provisioned: 2
- first_provision_delay_sec: run1=65.00991725921631, run2=97.65908813476562, run3=125.19051599502563, run4=79.83233618736267, run5=50.14050340652466

### s4-hybrid-predictive

- Runs: 5, passed the validity gate: 5
- Model artifact: data/models/gru_model.pt (pytorch)
- nodes_provisioned: run1=2, run2=2, run3=3, run4=2, run5=2
- first_provision_delay_sec: run1=65.12639498710632, run2=95.04459595680237, run3=125.21927452087402, run4=80.30920457839966, run5=50.0053927898407

## Headline

Aggregates are means over gate-passing runs.

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | ramp p99 (ms) | error rate | throughput (rps) | SLO violations | replica-seconds | serverless share (%) | valid |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s3-hybrid-reactive | 5 | 64.8 | 131.3 | 342.7 | 484.7 | 0.0000 | 73.2 | 1527.4 | 6892.5 | 22.8 | 5/5 |
| s4-hybrid-predictive | 5 | 64.4 | 126.0 | 498.7 | 689.4 | 0.0000 | 73.2 | 1682.8 | 7455.0 | 18.8 | 5/5 |

ramp p99 (co-primary): the trace's ramp stages; mean over the 10/10 run(s) whose k6 summary recorded stages.

## Paired comparison — s4-hybrid-predictive vs s3-hybrid-reactive

Pairs are matched by run id, in run order. 5 of 5 pairs passed the validity gate on both sides.

| Pair | s3-hybrid-reactive p99 (ms) | s4-hybrid-predictive p99 (ms) | Δ p99 (ms) | s3-hybrid-reactive SLO | s4-hybrid-predictive SLO | Δ SLO |
|---|---|---|---|---|---|---|
| run 1 | 227.6 | 191.5 | -36.1 | 1085.0 | 775.0 | -310.0 |
| run 2 | 116.7 | 341.4 | +224.7 | 69.0 | 2530.0 | +2461.0 |
| run 3 | 253.1 | 217.6 | -35.5 | 1485.0 | 1008.0 | -477.0 |
| run 4 | 977.9 | 1609.5 | +631.6 | 4862.0 | 3950.0 | -912.0 |
| run 5 | 138.0 | 133.7 | -4.4 | 136.0 | 151.0 | +15.0 |

- Mean Δp99 latency: +156.1 ms, paired Cohen's d: 0.54, exact one-sided permutation p (H1: S4 faster): 0.7812 (does not clear 0.05).
- Mean ΔSLO violations: +155.4, paired Cohen's d: 0.12, exact one-sided permutation p (H1: S4 faster): 0.5625 (does not clear 0.05).

## Forecast fidelity

| Scenario | eligible cycles | successful predictions | delivery rate | delivered |
|---|---|---|---|---|
| s3-hybrid-reactive | 0 | 0 | n/a | yes |
| s4-hybrid-predictive | 285 | 285 | 1.000 | yes |

## Node tier

| Scenario | node tier exercised | pending events | nodes provisioned | mean provisioning delay (s) |
|---|---|---|---|---|
| s3-hybrid-reactive | yes | 260 | 10 | 83.6 |
| s4-hybrid-predictive | yes | 196 | 11 | 83.1 |

## Caveats

None.
