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
- [research summary](ringkasan-penelitian.md) — Indonesian summary in the adviser's requested order (rumusan masalah, metodologi, evaluasi, kesimpulan); shareable handout.
- [progress summary](progress-summary.md) — shareable handout; a snapshot, not a log or source of truth. WhatsApp-ready PDF export (regenerate before each send; `*.pdf` is gitignored so the PDF is a local artifact): `pandoc progress-summary.md -o progress-summary.pdf --pdf-engine=xelatex -V geometry:margin=2cm -V fontsize=10pt`

## Evidence hierarchy (what is canonical)

- **Experiment facts**: the bundle under `../../results/experiments/phase-b/<bundle>/` (meta.yaml/report.md/raw artifacts) and the typed registry `../../results/evidence/registry.yaml`.
- **Thesis numbers**: `../../results/claims/FINAL_NUMBERS.md` and `../../results/claims/CLAIMS_TO_EVIDENCE.md`.
- **Proposal-to-delivered rationale**: `../DRIFT_ANALYSIS.md` (D1–D13, §6b).
- `../../results/EXPERIMENT_JOURNAL.md` is **generated/read-only**; `catalog.duckdb` is a local cache. Neither is hand-edited.

- **Evidence roles** (from the registry): `final` = the thesis claim (currently only `2026-07-14_clarknet-tuned-paired-n5`, H2 p=0.0304); `diagnostic` = supporting/replication. Retained replication is the 2026-08-08 paired batches (RUN1 p=0.436, RUN2 p=0.062) and the 2026-08-09 four-scenario replication (p=0.032). The two 2026-08-07 batches were deleted before commit and are excluded per thesis ch04 sec:replication — never cite them. `archived` = superseded. A draft may cite diagnostic bundles only as *replication*, never as the thesis result.

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

## Growth policy (unbounded logs stay usable)

Append-only logs grow forever by design. The split rule keeps every file readable without breaking references:

1. **Roll over by year, never mid-year.** When a stream file exceeds ~300 lines / ~100 events, split it at the year boundary: `experiments.md` → `experiments-2026.md` + `experiments-2027.md` (same for `venue-communications.md`, and `professor-qa.md` if it ever exceeds ~50 entries). The ID scheme makes this lossless — `EXP-YYYY-MM-DD-NN` already encodes the year, so an entry's home file is derivable from its ID.
2. **The split is a `git mv` + index update.** Old file renamed to `<name>-<year>.md`, new empty file created, README "Files" table updated with a `(current)` marker and an archive row. No history is rewritten, no links break (the new file is the stream's continuation).
3. **Never split by phase/topic/message.** A second parallel file for the same stream creates the "which file does this go in?" tax — the anti-pattern the flat layout exists to avoid.
4. **Bounded streams never split**: `advisor-whatsapp.md` (one thread per advisor), `bimbingan.md` (~10 sessions), `publications.md` (a handful of PUB IDs). If a second advisor/committee thread appears, give it its own file (`committee-comms.md`).
5. **The full experiment list never lives in the logbook.** `EXPERIMENT_JOURNAL.md` (generated) is the exhaustive machine ledger; `experiments.md` stays curated (series index + decision events). If the journal itself grows past a single file, that's an evidence-system concern, not a logbook one.
