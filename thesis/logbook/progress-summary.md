# Progress Summary — 1 Page (for the Advisor)

This is the source of truth for the progress overview shared with the advisor
(WhatsApp message 3 attachment). All numbers link to the evidence system;
nothing here is newer than the referenced bundles.

## Status: research complete, thesis written, defense-ready

**Architecture.** Hybrid platform combining k3s (Kubernetes) and serverless
(Knative), with a GRU workload predictor driving elastic scaling decisions.
Four scenarios compared: S1 pure Kubernetes, S2 pure serverless, S3 hybrid
reactive (observed-load scaling), S4 hybrid predictive (GRU-forecast scaling).

**Primary result (H2 — predictive vs reactive hybrid).** S4 beats S3:

| Metric | S3 (reactive) | S4 (predictive) | Δ |
|---|---|---|---|
| p99 latency (ms) | 188.5 | 126.0 | −62.5 (−33%) |
| One-sided permutation p | — | — | **0.0304** |
| Cohen's d (paired) | — | — | −1.26 |
| SLO violations (p99 < 200 ms) | 656 | 130 | **−80%** |
| Cost | $163 | $163 | identical |

*Evidence: `results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5` (definitive, role: final).*

**Independent replication (August 2026, role: diagnostic — supporting evidence, not the thesis claim).** The full experiment was re-triggered twice with the same recorded configuration:

| Run | Pairs won | S3 p99 (ms) | S4 p99 (ms) | p | d |
|---|---|---|---|---|---|
| Batch 1 (n=5) | 4/5 | 131.7 | 109.9 | 0.0958 | −0.71 |
| Batch 2 (n=5) | **5/5** | 175.3 | 94.6 | **0.0304** | −1.00 |
| **Pooled (n=10)** | **9/10** | 153.5 | 102.3 | **0.0030** | −0.78 |

The direction is stable across three independent batches; batch 2 reproduces
the July result almost exactly (identical p = 0.0304). Pooled replication is
reported as repeatability evidence; the thesis's inferential claim remains the
final July bundle (p = 0.0304).

*Evidence: `2026-08-07_paired-h2_060200`, `2026-08-07_paired-h2_104918` (both role: diagnostic).*

**Supporting results.** GRU predictor: synthetic RMSE 4.75% (post-HPO),
ClarkNet 5-min-ahead 17.78%; cost model shows identical spend between hybrids;
paired n=5 counterbalanced design with full treatment-fidelity gating.

**Deliverables.**
- Thesis manuscript (Typst → PDF, compiles clean) — `thesis-typst/build/thesis.pdf`
- Drift analysis proposal→implementation, 13 items, 17 archived citations — `thesis/DRIFT_ANALYSIS.md`
- Governed evidence registry: 139 experiment bundles, catalog + journal — `results/evidence/`

**Next steps (needs advisor input).** Review of the drift analysis (especially
the D5 prediction-for-scaling drift and D9 GRU accuracy honesty), confirmation
of the defense timeline, sidang registration.
