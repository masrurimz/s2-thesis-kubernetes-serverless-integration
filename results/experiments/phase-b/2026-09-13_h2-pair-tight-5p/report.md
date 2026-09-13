# 2026-09-13 h2-pair-tight — aborted, design withdrawn

**Status: aborted mid-run; the design it tested is withdrawn.** This bundle is
kept as the measured basis for the `capacity_headroom` condition and as a
negative result, not as evidence for or against H2.

## What it was

`h2-pair-tight` declared `max_k8s_replicas: 6` (199.8 RPS at 33.3 RPS/replica)
to make the forecast exceed capacity more often than the ten-replica
`h2-pair` ceiling (333.0 RPS). The reasoning was that a lower ceiling raises
the proactive margin. It does the opposite.

## Why it is invalid

Algorithm 2 sizes from the reactively required target,
`ceil(alpha * buffer * load)` with alpha 0.0601 (~16.65 RPS per replica). A
forecast can only exceed capacity when the load leaves headroom under the
ceiling. At six replicas the ClarkNet replay (peak 164 RPS) saturates the
ceiling on **11 of 40 stages (27.5%)**, so the sizing law is already at the
ceiling and no forecast can exceed it — the predictive arm has nothing to
pre-empt. The run measures a reactive arm under a predictive label.

Measured here: `predictive_count` was 4, 3, 6 across the three S4 runs (the
daemon *issued* scale-ups), but `prediction_usage_rate` was 0.00 — the
predictions never translated into capacity the load could not already claim.
All 57 eligible cycles were non-actionable, against 3–5 actionable at ten
replicas.

## What it measured anyway

| run | p99 (ms) | error_rate | predictive_count |
|---|---|---|---|
| s3-hybrid-reactive_run1 | 3562.8 | 0.000 | 0 |
| s3-hybrid-reactive_run2 | 1151.8 | 0.000 | 0 |
| s3-hybrid-reactive_run3 | 1573.3 | 0.000 | 0 |
| s4-hybrid-predictive_run1 | 3902.4 | 0.000 | 4 |
| s4-hybrid-predictive_run2 | 4694.5 | 0.002 | 3 |
| s4-hybrid-predictive_run3 | 1885.4 | 0.000 | 6 |

S4's p99 (1885–4694 ms) is ~4× the cap-10 runs' — the tight ceiling starved
both arms, and the predictive arm could not recover it. That is the mechanism
the `capacity_headroom` condition now refuses: `apply()` rejects a run that
needs a predictor and declares a ceiling when more than 5% of replay stages
saturate it.

## Disposition

Aborted after 6 of 10 runs (s4 run4 has no `result.json`). Do not re-analyse
as an H2 pair; the treatment was never actionable. The paired experiment that
tests H2 is `h2-pair` (cap 10), whose ceiling the replay sits under.
