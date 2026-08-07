# Defense Communications Log

**Purpose:** a durable, versioned log of *every* communication with the thesis
advisor and the defense committee around the defense of
*"Decision Making and Elastic Scalability Management in Heterogeneous Cloud
Environments Based on Workload Prediction"* — WhatsApp threads, bimbingan
sessions, emails, and the progress materials shared with them.

This folder is the **hub**: it points to (and is backed by) the evidence system
(`results/evidence/`, `results/EXPERIMENT_JOURNAL.md`) and the defense documents
(`thesis/DRIFT_ANALYSIS.md`, `thesis-typst/`).

## Folder map

| File | Contents |
|---|---|
| `README.md` | This file — purpose, conventions |
| `advisor-whatsapp.md` | Live WhatsApp thread log with the advisor: drafts, sent texts (verbatim), replies, bimbingan session records |
| `progress-summary.md` | The 1-page progress overview shared with the advisor (source of truth for what was sent) |

## Logging conventions

1. **One file per channel/contact.** A new thread (e.g., committee email) gets a
   new file here.
2. **One dated entry per event.** Append, never rewrite history — corrections
   are new entries.
3. **Record verbatim text.** Store the *exact* message sent and the *exact*
   reply received, not a summary. Future-you and the committee may need it.
4. **Track status.** Every entry carries a status: `pending` / `sent` /
   `replied` / `actioned`. Update the entry when the state changes.
5. **Link evidence.** When a message references a number, link the bundle or
   document it came from (e.g., `results/experiments/phase-b/2026-08-07_paired-h2_104918`).
6. **Bimbingan sessions** get a section in the thread file: date, who attended,
   topics, advisor feedback (verbatim where possible), action items, next session.

## Related documents

- `thesis/DRIFT_ANALYSIS.md` — the defense script (drift items, citations, replication story)
- `results/claims/FINAL_NUMBERS.md` — definitive numbers quoted in all communications
- `results/EXPERIMENT_JOURNAL.md` — experiment ledger (139 bundles)
- `results/evidence/registry.yaml` — evidence registry (bundle roles)
- `thesis-typst/build/thesis.pdf` — the thesis PDF to share with the advisor
