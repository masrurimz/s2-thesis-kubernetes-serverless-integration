# Thesis Logbook

Owner: zahid | Thesis: *Decision Making and Elastic Scalability Management in Heterogeneous Cloud Environments Based on Workload Prediction* | Last worked: 2026-08-07

This is an append-only record of experiments, advisor communication, publication work, and defense preparation. **It is not the source of experiment facts** — every number points to the evidence system.

## Files

- [experiments](experiments.md) — experiment events and decisions (links only, no copied metrics)
- [advisor WhatsApp](advisor-whatsapp.md) — professor chat: drafts, sent/received texts verbatim
- [bimbingan](bimbingan.md) — supervision sessions + action items
- [publications](publications.md) — publication pipeline tracker
- [venue communications](venue-communications.md) — journal/editor/reviewer correspondence
- [professor Q&A](professor-qa.md) — anticipated questions, bilingual answers
- [progress summary](progress-summary.md) — shareable handout; a snapshot, not a log or source of truth

## Evidence hierarchy (what is canonical)

- **Experiment facts**: the bundle under `../../results/experiments/phase-b/<bundle>/` (meta.yaml/report.md/raw artifacts) and the typed registry `../../results/evidence/registry.yaml`.
- **Thesis numbers**: `../../results/claims/FINAL_NUMBERS.md` and `../../results/claims/CLAIMS_TO_EVIDENCE.md`.
- **Proposal-to-delivered rationale**: `../DRIFT_ANALYSIS.md` (D1–D13, §6b).
- `../../results/EXPERIMENT_JOURNAL.md` is **generated/read-only**; `catalog.duckdb` is a local cache. Neither is hand-edited.

**Evidence roles** (from the registry): `final` = the thesis claim (currently only `2026-07-14_clarknet-tuned-paired-n5`, H2 p=0.0304); `diagnostic` = supporting/replication (all 2026-08-* bundles; pooled p=0.0030 is replication-tier); `archived` = superseded. A draft may cite diagnostic bundles only as *replication*, never as the thesis result.

## Entry rules

1. Append a dated entry at the end; never delete or rewrite old message text or outcomes.
2. IDs per stream: `EXP-YYYY-MM-DD-NN`, `WA-YYYY-MM-DD-NN`, `BIM-YYYY-MM-DD-NN`, `PUB-NN`, `VEN-YYYY-MM-DD-NN`, `QA-NNN`.
3. Every entry has `status: pending | sent | replied | actioned`. `pending` = unfinished; `sent` = outbound delivered; `replied` = response arrived; `actioned` = resulting task done.
4. Messages stay verbatim in their original language (normally Bahasa Indonesia). Notes, interpretations, and defense answers are English.
5. Every factual claim has an Evidence block; if not yet evidenced, label it `unverified`.
6. The latest event for an ID is its current state — never edit an earlier status, append a follow-up event.

## How the agent maintains this logbook

- On request ("log this exchange"), the agent appends `WA-`/`BIM-`/`EXP-`/`VEN-` events verbatim and updates statuses; it never rewrites history.
- Before any outbound message, the agent verifies every factual claim against the evidence hierarchy and tags each with its bundle + role.
- When the professor asks a real question, the agent appends an "actual question event" under the matching `QA-NNN` and files new questions as new IDs.
- The agent keeps `progress-summary.md` in sync with `FINAL_NUMBERS.md` and the registry before it is shared.
