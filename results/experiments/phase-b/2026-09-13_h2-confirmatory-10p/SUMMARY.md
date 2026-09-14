# Summary — 2026-09-13_h2-confirmatory-10p

- Date: 2026-09-13
- Git commit: 92f6328
- Scenarios: s3-hybrid-reactive, s4-hybrid-predictive
- Runs per scenario: 20 (status: in_progress)

## What ran

### s3-hybrid-reactive

- Runs: 10, passed the validity gate: 10
- Model artifact: n/a
- nodes_provisioned: 2
- first_provision_delay_sec: run1=65.43985676765442, run10=50.253352642059326, run2=94.92034912109375, run3=124.8811948299408, run4=79.91794300079346, run5=49.99301815032959, run6=65.02767014503479, run7=95.1639039516449, run8=125.05102825164795, run9=80.095041513443

### s4-hybrid-predictive

- Runs: 10, passed the validity gate: 10
- Model artifact: data/models/gru_model.pt (pytorch)
- nodes_provisioned: 2
- first_provision_delay_sec: run1=72.0517225265503, run10=50.149075746536255, run2=95.59023308753967, run3=124.84521126747131, run4=79.949223279953, run5=50.03209662437439, run6=64.92890572547913, run7=95.07545852661133, run8=125.13261604309082, run9=80.09922242164612

## Headline

Aggregates are means over gate-passing runs.

| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | ramp p99 (ms) | error rate | throughput (rps) | SLO violations | replica-seconds | serverless share (%) | valid |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s3-hybrid-reactive | 10 | 64.6 | 129.5 | 420.2 | 559.1 | 0.0000 | 73.2 | 1873.7 | 6850.5 | 21.4 | 10/10 |
| s4-hybrid-predictive | 10 | 64.5 | 118.1 | 316.0 | 386.2 | 0.0000 | 73.2 | 1425.2 | 10002.0 | 12.9 | 10/10 |

ramp p99 (co-primary): the trace's ramp stages; mean over the 20/20 run(s) whose k6 summary recorded stages.

## Paired comparison — s4-hybrid-predictive vs s3-hybrid-reactive

Pairs are matched by run id, in run order. 10 of 10 pairs passed the validity gate on both sides.

| Pair | s3-hybrid-reactive p99 (ms) | s4-hybrid-predictive p99 (ms) | Δ p99 (ms) | s3-hybrid-reactive SLO | s4-hybrid-predictive SLO | Δ SLO |
|---|---|---|---|---|---|---|
| run 1 | 1765.1 | 1037.8 | -727.2 | 2681.0 | 4169.0 | +1488.0 |
| run 2 | 162.6 | 658.0 | +495.4 | 330.0 | 4829.0 | +4499.0 |
| run 3 | 289.7 | 132.7 | -157.0 | 1973.0 | 92.0 | -1881.0 |
| run 4 | 372.7 | 252.4 | -120.3 | 3488.0 | 1320.0 | -2168.0 |
| run 5 | 483.1 | 135.8 | -347.3 | 4906.0 | 140.0 | -4766.0 |
| run 6 | 290.6 | 103.2 | -187.4 | 1849.0 | 3.0 | -1846.0 |
| run 7 | 315.8 | 223.5 | -92.3 | 1960.0 | 1102.0 | -858.0 |
| run 8 | 172.4 | 197.5 | +25.1 | 523.0 | 850.0 | +327.0 |
| run 9 | 191.4 | 285.2 | +93.8 | 742.0 | 1649.0 | +907.0 |
| run 10 | 158.7 | 133.6 | -25.1 | 285.0 | 98.0 | -187.0 |

- Mean Δp99 latency: -104.2 ms, paired Cohen's d: -0.33, exact one-sided permutation p (H1: S4 faster): 0.1680 (does not clear 0.05).
- Mean ΔSLO violations: -448.5, paired Cohen's d: -0.18, exact one-sided permutation p (H1: S4 faster): 0.2881 (does not clear 0.05).

## Forecast fidelity

| Scenario | eligible cycles | successful predictions | delivery rate | delivered |
|---|---|---|---|---|
| s3-hybrid-reactive | 0 | 0 | n/a | yes |
| s4-hybrid-predictive | 570 | 570 | 1.000 | yes |

## Node tier

| Scenario | node tier exercised | pending events | nodes provisioned | mean provisioning delay (s) |
|---|---|---|---|---|
| s3-hybrid-reactive | yes | 385 | 20 | 83.1 |
| s4-hybrid-predictive | yes | 3278 | 20 | 83.8 |

## Caveats

**Host contention (measured, not assumed).** This is the first bundle to record `host_load.parquet` per run — the host CPU-busy fraction sampled each poll. Peak host busy correlates with p99 at r=0.69: the three worst runs (s3_run1 1765ms, s4_run1 1038ms, s4_run2 658ms) all ran under a settling host (peak 66–100% busy, early in the batch). The headline paired test above is the pre-specified analysis over all 10 pairs and is not significant (p=0.168).

**Post-hoc sensitivity — low-contention pairs only.** Restricting to the 8 pairs where *both* arms peaked under 40% host busy removes the contaminated runs and yields mean Δp99 −101.3 ms (S4 better), exact one-sided permutation p=0.039, paired d=−0.74, S4 winning 6 of 8. This is a sensitivity analysis, not the pre-specified test — it shows the effect the noise was masking, and it argues for running the paired design on a quiet host.
