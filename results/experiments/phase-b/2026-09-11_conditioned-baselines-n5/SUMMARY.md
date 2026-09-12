# Summary — 2026-09-11_conditioned-baselines-n5

- Date: 2026-09-11
- Git commit: 0618d80, 4d4b89c, 5ace762
- Scenarios: s1-k8s-only, s2-serverless-only
- Runs per scenario: 5 (status: in_progress)

## What ran

### s1-k8s-only

- Runs: 5, passed the validity gate: 5
- Model artifact: n/a
- nodes_provisioned: 1
- first_provision_delay_sec: run1=71.69249606132507, run2=118.60021495819092, run3=62.23188900947571, run4=77.97562789916992, run5=73.79616570472717

### s2-serverless-only

- Runs: 5, passed the validity gate: 5
- Model artifact: n/a
- nodes_provisioned: 0
- first_provision_delay_sec: 0.0

## Headline

Aggregates are means over gate-passing runs.

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | error rate | throughput (rps) | SLO violations | replica-seconds | serverless share (%) | valid |
|---|---|---|---|---|---|---|---|---|---|---|
| s1-k8s-only | 5 | 67.1 | 2324.7 | 4753.8 | 0.0005 | 72.4 | 13765.4 | 7345.5 | 0.0 | 5/5 |
| s2-serverless-only | 5 | 66.6 | 78.3 | 86.8 | 0.0000 | 73.2 | 16.4 | 0.0 | 100.0 | 5/5 |

## Paired comparison — s2-serverless-only vs s1-k8s-only

Pairs are matched by run id, in run order. 5 of 5 pairs passed the validity gate on both sides.

| Pair | s1-k8s-only p99 (ms) | s2-serverless-only p99 (ms) | Δ p99 (ms) | s1-k8s-only SLO | s2-serverless-only SLO | Δ SLO |
|---|---|---|---|---|---|---|
| run 1 | 4098.6 | 77.7 | -4020.9 | 13184.0 | 6.0 | -13178.0 |
| run 2 | 3105.0 | 77.7 | -3027.4 | 7579.0 | 5.0 | -7574.0 |
| run 3 | 3399.8 | 122.9 | -3276.9 | 8141.0 | 59.0 | -8082.0 |
| run 4 | 8682.2 | 77.7 | -8604.5 | 25880.0 | 6.0 | -25874.0 |
| run 5 | 4483.4 | 77.8 | -4405.6 | 14043.0 | 6.0 | -14037.0 |

- Mean Δp99 latency: -4667.0 ms, paired Cohen's d: -2.06, exact one-sided permutation p (H1: S4 faster): 0.0312 (clears 0.05).
- Mean ΔSLO violations: -13749.0, paired Cohen's d: -1.86, exact one-sided permutation p (H1: S4 faster): 0.0312 (clears 0.05).

## Forecast fidelity

| Scenario | eligible cycles | successful predictions | delivery rate | delivered |
|---|---|---|---|---|
| s1-k8s-only | 0 | 0 | n/a | yes |
| s2-serverless-only | 0 | 0 | n/a | yes |

## Node tier

| Scenario | node tier exercised | pending events | nodes provisioned | mean provisioning delay (s) |
|---|---|---|---|---|
| s1-k8s-only | yes | 5 | 5 | 80.9 |
| s2-serverless-only | not required | 0 | 0 | n/a |

## Caveats

None.
