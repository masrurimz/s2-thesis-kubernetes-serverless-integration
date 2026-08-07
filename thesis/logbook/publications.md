# Publication Pipeline

`stage` is the pipeline position: `idea | outline | draft | internal review | submitted | revision | accepted | rejected | published`. `status` describes the latest event; the latest event for a `PUB` ID is current. Venue correspondence (emails, portal messages) is logged verbatim in [venue-communications.md](venue-communications.md) and referenced here via `VEN-...`.

## PUB-001 — Hybrid Kubernetes–Serverless Autoscaling with GRU Workload Prediction

- First logged: 2026-08-07
- Status: pending
- Stage: idea
- Target venue: *[to be decided]* — candidates: IEEE Access (Q1, APCs waived for some countries), Journal of Cloud Computing (Springer, Q2), FGCS (Elsevier, Q1, strong autoscaling fit), or an Indonesian Scopus-indexed venue for a national requirement. Track + URL to be filled before submission.
- Manuscript/artifact: `thesis-typst/build/thesis.pdf` (chapter adaptation needed — paper is a compressed version, not a cut-down thesis)
- Contribution claim: hybrid K8s+serverless autoscaling where GRU forecasts drive scaling (not routing), with explicit autoscaler fairness (node CPU bounding, r_saturation calibration) and an evidence-governed, replicated experiment (paired n=5, p=0.0304, independent replication 9/10 pairs). Evidence: [../../results/claims/FINAL_NUMBERS.md](../../results/claims/FINAL_NUMBERS.md), bundles in [experiments.md](experiments.md).
- Current next action: decide venue + co-authors (advisor) — due: after defense
- Evidence: thesis ch01 (hypotheses), ch04 `sec:replication`, [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md) §6

### YYYY-MM-DD — <stage event>
- Status: pending | sent | replied | actioned
- What changed: [stage, decision, or requested revision]
- Evidence / related venue record: `VEN-...` and links
- Next action: [owner + due date]

---

*Conventions: append events per PUB ID; statuses per [README.md](README.md).*
