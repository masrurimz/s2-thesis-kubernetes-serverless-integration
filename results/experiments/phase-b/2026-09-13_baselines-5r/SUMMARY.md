# Summary — 2026-09-13_baselines-5r

- Date: 2026-09-13
- Git commit: 7ff529a
- Scenarios: s1-k8s-only, s2-serverless-only
- Runs per scenario: 5 (status: in_progress)

## What ran

### s1-k8s-only

- Runs: 5, passed the validity gate: 5
- Model artifact: n/a
- nodes_provisioned: 2
- first_provision_delay_sec: run1=117.98789739608765, run2=64.05605387687683, run3=59.03817129135132, run4=52.0613214969635, run5=109.84609198570251

### s2-serverless-only

- Runs: 5, passed the validity gate: 5
- Model artifact: n/a
- nodes_provisioned: 0
- first_provision_delay_sec: 0.0

## Headline

Aggregates are means over gate-passing runs.

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | ramp p99 (ms) | error rate | throughput (rps) | SLO violations | replica-seconds | serverless share (%) | valid |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s1-k8s-only | 5 | 64.0 | 80.6 | 124.6 | 139.1 | 0.0000 | 73.2 | 91.4 | 11083.5 | 0.0 | 5/5 |
| s2-serverless-only | 5 | 65.2 | 75.5 | 77.8 | 78.5 | 0.0000 | 73.2 | 4.6 | 0.0 | 100.0 | 5/5 |

ramp p99 (co-primary): the trace's ramp stages; mean over the 10/10 run(s) whose k6 summary recorded stages.

## Paired comparison — s2-serverless-only vs s1-k8s-only

Pairs are matched by run id, in run order. 5 of 5 pairs passed the validity gate on both sides.

| Pair | s1-k8s-only p99 (ms) | s2-serverless-only p99 (ms) | Δ p99 (ms) | s1-k8s-only SLO | s2-serverless-only SLO | Δ SLO |
|---|---|---|---|---|---|---|
| run 1 | 118.9 | 77.5 | -41.5 | 58.0 | 3.0 | -55.0 |
| run 2 | 110.8 | 77.5 | -33.3 | 91.0 | 13.0 | -78.0 |
| run 3 | 148.6 | 79.2 | -69.4 | 185.0 | 1.0 | -184.0 |
| run 4 | 119.6 | 77.6 | -42.1 | 57.0 | 3.0 | -54.0 |
| run 5 | 125.3 | 77.4 | -47.9 | 66.0 | 3.0 | -63.0 |

- Mean Δp99 latency: -46.8 ms, paired Cohen's d: -3.44, exact one-sided permutation p (H1: S4 faster): 0.0312 (clears 0.05).
- Mean ΔSLO violations: -86.8, paired Cohen's d: -1.57, exact one-sided permutation p (H1: S4 faster): 0.0312 (clears 0.05).

## Forecast fidelity

| Scenario | eligible cycles | successful predictions | delivery rate | delivered |
|---|---|---|---|---|
| s1-k8s-only | 0 | 0 | n/a | yes |
| s2-serverless-only | 0 | 0 | n/a | yes |

## Node tier

| Scenario | node tier exercised | pending events | nodes provisioned | mean provisioning delay (s) |
|---|---|---|---|---|
| s1-k8s-only | yes | 2075 | 10 | 80.6 |
| s2-serverless-only | not required | 0 | 0 | n/a |

## Caveats

None.
