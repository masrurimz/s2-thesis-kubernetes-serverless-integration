# Summary — 2026-09-12_h2-pair

- Date: 2026-09-12
- Git commit: cb373df
- Scenarios: s3-hybrid-reactive, s4-hybrid-predictive
- Runs per scenario: 2 (status: in_progress)

## What ran

### s3-hybrid-reactive

- Runs: 5, passed the validity gate: 5
- Model artifact: n/a
- nodes_provisioned: 1
- first_provision_delay_sec: run1=80.93711352348328, run2=113.7761344909668, run3=110.03297758102417, run4=55.85480093955994, run5=65.72047209739685

### s4-hybrid-predictive

- Runs: 5, passed the validity gate: 5
- Model artifact: data/models/gru_model.pt (pytorch)
- nodes_provisioned: 1
- first_provision_delay_sec: run1=89.85191059112549, run2=90.77882814407349, run3=68.68648314476013, run4=63.7775936126709, run5=111.78250861167908

## Headline

Aggregates are means over gate-passing runs.

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | error rate | throughput (rps) | SLO violations | replica-seconds | serverless share (%) | valid |
|---|---|---|---|---|---|---|---|---|---|---|
| s3-hybrid-reactive | 5 | 64.5 | 106.6 | 201.8 | 0.0000 | 73.2 | 857.0 | 6097.5 | 34.1 | 5/5 |
| s4-hybrid-predictive | 5 | 64.3 | 93.0 | 196.6 | 0.0000 | 73.2 | 707.6 | 6859.5 | 29.2 | 5/5 |

## Paired comparison — s4-hybrid-predictive vs s3-hybrid-reactive

Pairs are matched by run id, in run order. 5 of 5 pairs passed the validity gate on both sides.

| Pair | s3-hybrid-reactive p99 (ms) | s4-hybrid-predictive p99 (ms) | Δ p99 (ms) | s3-hybrid-reactive SLO | s4-hybrid-predictive SLO | Δ SLO |
|---|---|---|---|---|---|---|
| run 1 | 215.0 | 275.3 | +60.3 | 990.0 | 1239.0 | +249.0 |
| run 2 | 277.6 | 130.2 | -147.4 | 1679.0 | 108.0 | -1571.0 |
| run 3 | 156.9 | 241.8 | +84.9 | 392.0 | 1150.0 | +758.0 |
| run 4 | 132.0 | 186.0 | +54.0 | 165.0 | 748.0 | +583.0 |
| run 5 | 227.6 | 149.8 | -77.9 | 1059.0 | 293.0 | -766.0 |

- Mean Δp99 latency: -5.2 ms, paired Cohen's d: -0.05, exact one-sided permutation p (H1: S4 faster): 0.4375 (does not clear 0.05).
- Mean ΔSLO violations: -149.4, paired Cohen's d: -0.15, exact one-sided permutation p (H1: S4 faster): 0.4062 (does not clear 0.05).

## Forecast fidelity

| Scenario | eligible cycles | successful predictions | delivery rate | delivered |
|---|---|---|---|---|
| s3-hybrid-reactive | 0 | 0 | n/a | yes |
| s4-hybrid-predictive | 280 | 280 | 1.000 | yes |

## Node tier

| Scenario | node tier exercised | pending events | nodes provisioned | mean provisioning delay (s) |
|---|---|---|---|---|
| s3-hybrid-reactive | yes | 5 | 5 | 85.3 |
| s4-hybrid-predictive | yes | 5 | 5 | 85.0 |

## Caveats

None.
