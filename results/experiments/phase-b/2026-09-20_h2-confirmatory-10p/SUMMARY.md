# Summary — 2026-09-20_h2-confirmatory-10p

- Date: 2026-09-20
- Git commit: 837e8a8
- Scenarios: s3-hybrid-reactive, s4-hybrid-predictive
- Runs per scenario: 20 (status: in_progress)

## What ran

### s3-hybrid-reactive

- Runs: 10, passed the validity gate: 10
- Model artifact: n/a
- nodes_provisioned: run1=2, run10=3, run2=2, run3=2, run4=2, run5=2, run6=2, run7=2, run8=2, run9=2
- first_provision_delay_sec: run1=64.91055512428284, run10=50.16583490371704, run2=94.78786849975586, run3=124.90386295318604, run4=79.6814112663269, run5=51.43682265281677, run6=64.70965266227722, run7=94.6259663105011, run8=124.68531847000122, run9=79.94163036346436

### s4-hybrid-predictive

- Runs: 10, passed the validity gate: 10
- Model artifact: data/models/gru_model.pt (pytorch)
- nodes_provisioned: run1=2, run10=2, run2=2, run3=2, run4=2, run5=3, run6=2, run7=2, run8=2, run9=2
- first_provision_delay_sec: run1=64.93551421165466, run10=50.2166211605072, run2=95.1151134967804, run3=124.89654517173767, run4=79.99056100845337, run5=50.04024028778076, run6=64.65884041786194, run7=94.67349672317505, run8=124.75197458267212, run9=80.10688161849976

## Headline

Aggregates are means over gate-passing runs.

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | ramp p99 (ms) | error rate | throughput (rps) | SLO violations | replica-seconds | serverless share (%) | valid |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s3-hybrid-reactive | 10 | 64.3 | 88.6 | 160.4 | 222.0 | 0.0000 | 73.2 | 394.7 | 6887.2 | 25.8 | 10/10 |
| s4-hybrid-predictive | 10 | 64.2 | 87.6 | 146.8 | 177.9 | 0.0000 | 73.2 | 398.3 | 9986.2 | 18.6 | 10/10 |

ramp p99 (co-primary): the trace's ramp stages; mean over the 20/20 run(s) whose k6 summary recorded stages.

## Paired comparison — s4-hybrid-predictive vs s3-hybrid-reactive

Pairs are matched by run id, in run order. 10 of 10 pairs passed the validity gate on both sides.

| Pair | s3-hybrid-reactive p99 (ms) | s4-hybrid-predictive p99 (ms) | Δ p99 (ms) | s3-hybrid-reactive SLO | s4-hybrid-predictive SLO | Δ SLO |
|---|---|---|---|---|---|---|
| run 1 | 101.2 | 113.7 | +12.5 | 15.0 | 29.0 | +14.0 |
| run 2 | 301.3 | 123.0 | -178.3 | 1367.0 | 105.0 | -1262.0 |
| run 3 | 166.9 | 169.5 | +2.6 | 555.0 | 627.0 | +72.0 |
| run 4 | 158.3 | 299.8 | +141.5 | 268.0 | 2214.0 | +1946.0 |
| run 5 | 127.0 | 119.6 | -7.4 | 73.0 | 47.0 | -26.0 |
| run 6 | 154.9 | 96.0 | -59.0 | 427.0 | 10.0 | -417.0 |
| run 7 | 158.3 | 102.4 | -55.9 | 303.0 | 9.0 | -294.0 |
| run 8 | 110.6 | 150.2 | +39.5 | 20.0 | 167.0 | +147.0 |
| run 9 | 158.0 | 187.8 | +29.7 | 284.0 | 751.0 | +467.0 |
| run 10 | 167.1 | 106.1 | -61.0 | 635.0 | 24.0 | -611.0 |

- Mean Δp99 latency: -13.6 ms, paired Cohen's d: -0.16, exact one-sided permutation p (H1: S4 faster): 0.3066 (does not clear 0.05).
- Mean ΔSLO violations: +3.6, paired Cohen's d: 0.00, exact one-sided permutation p (H1: S4 faster): 0.5049 (does not clear 0.05).

## Forecast fidelity

| Scenario | eligible cycles | successful predictions | delivery rate | delivered |
|---|---|---|---|---|
| s3-hybrid-reactive | 0 | 0 | n/a | yes |
| s4-hybrid-predictive | 570 | 570 | 1.000 | yes |

## Node tier

| Scenario | node tier exercised | pending events | nodes provisioned | mean provisioning delay (s) |
|---|---|---|---|---|
| s3-hybrid-reactive | yes | 555 | 21 | 83.0 |
| s4-hybrid-predictive | yes | 3792 | 21 | 82.9 |

## Caveats

None.
