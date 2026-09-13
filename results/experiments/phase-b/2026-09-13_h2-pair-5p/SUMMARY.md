# Summary — 2026-09-13_h2-pair-5p

- Date: 2026-09-13
- Git commit: fe8da48, dd20841, bd889ad
- Scenarios: s3-hybrid-reactive, s4-hybrid-predictive
- Runs per scenario: 10 (status: in_progress)

## What ran

### s3-hybrid-reactive

- Runs: 5, passed the validity gate: 5
- Model artifact: n/a
- nodes_provisioned: 2
- first_provision_delay_sec: run1=65.17637038230896, run2=95.1897120475769, run3=125.01822972297668, run4=80.28823494911194, run5=50.15654110908508

### s4-hybrid-predictive

- Runs: 5, passed the validity gate: 5
- Model artifact: data/models/gru_model.pt (pytorch)
- nodes_provisioned: 2
- first_provision_delay_sec: run1=65.01746940612793, run2=94.94538950920105, run3=124.89470553398132, run4=79.91395306587219, run5=50.081778049468994

## Headline

Aggregates are means over gate-passing runs.

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | ramp p99 (ms) | error rate | throughput (rps) | SLO violations | replica-seconds | serverless share (%) | valid |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s3-hybrid-reactive | 5 | 66.3 | 238.8 | 503.0 | 596.6 | 0.0000 | 73.2 | 4360.2 | 6871.5 | 21.2 | 5/5 |
| s4-hybrid-predictive | 5 | 64.8 | 181.9 | 656.3 | 908.7 | 0.0000 | 73.2 | 2741.0 | 9975.0 | 12.7 | 5/5 |

ramp p99 (co-primary): the trace's ramp stages; mean over the 10/10 run(s) whose k6 summary recorded stages.

## Paired comparison — s4-hybrid-predictive vs s3-hybrid-reactive

Pairs are matched by run id, in run order. 5 of 5 pairs passed the validity gate on both sides.

| Pair | s3-hybrid-reactive p99 (ms) | s4-hybrid-predictive p99 (ms) | Δ p99 (ms) | s3-hybrid-reactive SLO | s4-hybrid-predictive SLO | Δ SLO |
|---|---|---|---|---|---|---|
| run 1 | 1275.2 | 226.0 | -1049.2 | 13296.0 | 1048.0 | -12248.0 |
| run 2 | 120.8 | 1837.5 | +1716.7 | 46.0 | 6398.0 | +6352.0 |
| run 3 | 197.6 | 817.3 | +619.6 | 853.0 | 4549.0 | +3696.0 |
| run 4 | 551.7 | 187.2 | -364.4 | 4860.0 | 703.0 | -4157.0 |
| run 5 | 369.7 | 213.4 | -156.3 | 2746.0 | 1007.0 | -1739.0 |

- Mean Δp99 latency: +153.3 ms, paired Cohen's d: 0.14, exact one-sided permutation p (H1: S4 faster): 0.6562 (does not clear 0.05).
- Mean ΔSLO violations: -1619.2, paired Cohen's d: -0.22, exact one-sided permutation p (H1: S4 faster): 0.3438 (does not clear 0.05).

## Forecast fidelity

| Scenario | eligible cycles | successful predictions | delivery rate | delivered |
|---|---|---|---|---|
| s3-hybrid-reactive | 0 | 0 | n/a | yes |
| s4-hybrid-predictive | 285 | 285 | 1.000 | yes |

## Node tier

| Scenario | node tier exercised | pending events | nodes provisioned | mean provisioning delay (s) |
|---|---|---|---|---|
| s3-hybrid-reactive | yes | 198 | 10 | 83.2 |
| s4-hybrid-predictive | yes | 1631 | 10 | 83.0 |

## Caveats

None.
