# Publication plan — advisor constraints, venue research, paper state

**Date:** 2026-09-18
**Mode:** Explanation — why TIME-E 2026 is the venue, and what is built.

## Advisor comms (WhatsApp, 2026-09-10)

Pak Royyana Muslim Ijtihadie asked for:

- A ringkasan (Bahasa Indonesia): rumusan masalah, metodologi matched to the
  rumusan masalah, evaluasi of the scenarios already obtained (matched to the
  methodology), kesimpulan (points matched to the rumusan masalah).
- A publication plus a conference **before January**, 6–7 pages, using **only
  the S2 scenarios that already have results** — the paper does not need the
  full thesis.
- Structure: context, why importance, rumusan masalah, metodologi, evaluasi,
  kesimpulan.
- Then: find a conference that is **hybrid (online presentation possible)**
  with a presentation or deadline that fits this semester.
- On the "international only, no SINTA?" question: no SINTA requirement,
  **international Scopus**.

**Note:** the last advisor message (international Scopus) has no reply sent
yet. Draft reply is at the end of this file.

## Venue research (2026-09-17)

Closed or unusable: IEEE CloudCom 2026 (deadline passed Aug 15), ICICoS 2026
(ran Aug 12–13), ICITACEE 2026 (ran Sep 9–11), ICEECIT 2026 (final deadline
Sep 15), COMNETSAT 2026 (site down, deadline passed), ICIMCIS 2026 (site is
a stub with no dates — skipped as unreliable).

**Selected: TIME-E 2026** (https://tim2e.org) — the only venue that meets
every advisor constraint:

- 7th IEEE International Conference on Technology, Informatics, Management,
  Engineering and Environment; IEEE Indonesia sponsored; past proceedings in
  IEEE Xplore and indexed by Scopus.
- **Hybrid**: presenters choose in-person or virtual.
- **This semester**: held 2026-11-11 to 2026-11-13, Bali.
- **Deadline 2026-09-20**, acceptance notification 2026-09-30, camera-ready
  2026-10-30.
- **6 pages max**, IEEE two-column A4, **double-blind** (no author names in
  the manuscript), PDF via EDAS: https://edas.info/N35430. All authors must
  be registered in EDAS before review; the list cannot change after.
- Scope fits: "Computing & Processing" and "Communication, Networking".

Backup (journal track): **Kinetik** (https://kinetik.umm.ac.id) — SINTA 2 +
Scopus, scope covers Computer Network + Computing, 4-week review, 4–8 weeks
submission-to-publication. A submission this week can be published in
November. Not what the advisor asked for, but it covers the "accepted
counts" reading of the graduation rule.

## Paper state (`paper/`)

Two builds from one shared source (`paper/sections/content.typ`; an
`extended` flag drives both):

- `paper/conference.pdf` — the TIME-E version. 5 pages, A4, **anonymous**
  (verified: no author or affiliation string in the text). Five figures,
  two tables.
- `paper/journal.pdf` — the extended version with real authors: Muhammad
  Zahid Masruri and Royyana Muslim Ijtihadie, Department of Informatics,
  ITS, Surabaya. Adds the Calibration, node-consolidation, and
  generalization sections.
- Rebuild with `make` in `paper/` (needs `typst` on PATH). The IEEE template
  is vendored as `paper/ieee.typ` with fonts fixed to Liberation Serif/Mono
  (Times-metric, no download needed).

Content policy: the paper reports the ClarkNet-attributable result
truthfully — hybrid routing beats saturated Kubernetes by up to 95% p99;
predictive-vs-reactive is conditional (ten pairs, mean −104.2 ms,
$p = 0.168$ on the pre-specified test; clean-host subset $p = 0.039$
disclosed as sensitivity analysis). Numbers come from
`results/claims/FINAL_NUMBERS.md`; figures reuse
`thesis-typst/src/figures/paper/`.

Still owed: the Bahasa Indonesia ringkasan the advisor asked for
(context, why, rumusan masalah, metodologi, evaluasi skenario, kesimpulan),
and the EDAS submission itself.

## Draft reply to Pak Roy (not sent)

> Baik Pak, update: saya sudah menemukan conference yang memenuhi kriteria —
> TIME-E 2026 (IEEE, Scopus), 11–13 November di Bali, hybrid (boleh
> presentasi online), deadline paper 20 September, 6 halaman. Paper saya
> susun dari skenario-skenario yang sudah ada saja. Draft segera saya
> bagikan. Terima kasih Pak.
