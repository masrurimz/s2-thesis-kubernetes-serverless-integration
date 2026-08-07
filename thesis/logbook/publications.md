---
# Publication Pipeline

`stage`: `idea | outline | draft | internal review | submitted | revision | accepted | rejected | published`. `status`: latest event per `PUB` ID. Venue correspondence logged verbatim in [venue-communications.md](venue-communications.md) via `VEN-...`.

## ITS S2 publication requirement (verified 2026-08-07)

**Author context:** S2 Informatics, ITS Surabaya — Muhammad Zahid Masruri, NRP 6025222041; supervisors Prof. Tohari Ahmad & Royyana Muslim Ijtihadie.

**Controlling rules (both reported; cohort/program confirmation recommended):**

1. **Peraturan Rektor ITS No.33/2025** (Peraturan Akademik ITS, effective 2025-11-24, repeals 18/2023 & 10/2024) — official DPSP page https://www.its.ac.id/pendidikan/2026/01/23/peraturan-akademik-tahun-2025/ · PDF https://www.its.ac.id/pendidikan/wp-content/uploads/sites/112/2026/01/SALINAN_Peraturan-Rektor-Nomor-33-Tahun-2025-Peraturan-Akademik-ITS_organized.pdf. Pasal 69(3)(b)(3): S2 graduation requires a dissemination condition governed by a separate guideline; 36 SKS, IPK >=3, C <=20%; max 8 semesters; yudisium required.

2. **Keputusan Rektor T/2086/IT2/HK.00.01/2020 (Baku Mutu Pascasarjana)** — still the operational standard posted by the graduate school; PDF https://www.its.ac.id/pascasarjana/wp-content/uploads/sites/115/2020/08/SK-REKTOR-BAKU-MUTU-PASCASARJANA-2020-PUBLISHED.pdf · download index https://www.its.ac.id/pascasarjana/download/. Section 2.4.1 — S2 publication alternatives:
   - Regular route: published accredited national journal OR accepted international journal OR oral presentation at a reputable indexed international seminar (>5 countries; Scopus/WoS proceedings).
   - Research route (requires more): one seminar presentation PLUS accepted Scopus Q3/WoS journal, OR published Sinta 1-4 journal, OR registered patent. No mere submission.

3. **PMTIF (S2 Informatics) SOP** — SOP Tesis-Publikasi S2 PDF https://www.its.ac.id/informatika/wp-content/uploads/sites/44/2022/09/SOP-Tesis-Publikasi-S2.pdf (2022-09-23): national journal LoA + proof of publication; international seminar proceedings + presenter certificate + poster; international journal minimum LoA; grading by admin/Kaprodi. Current S2 Informatics program page https://www.its.ac.id/informatika/id/akademik/program-studi/program-studi-s2/ lists 36 SKS incl. 3-SKS "Tesis-Publikasi Ilmiah".

4. **Timing:** Baku Mutu 4.2.1 — write journal article, then thesis exam >=2 months before ITS yudisium, article copy attached to exam report; prodi checks publication in SIM Yudisium before proposing yudisium. No explicit submission deadline relative to sidang; PMTIF's sidang checklist https://www.its.ac.id/informatika/id/syarat-maju-sidang-tesis/ does not list publication (so it gates yudisium, not sidang).

**Confirm before relying:** DPSP pasca-its@its.ac.id / WhatsApp +62 811-3050-0022; PMTIF tinformatika@its.ac.id — ask which applies to cohort 2025-2026 (2020 Baku Mutu vs 2025 rule's separate dissemination guideline).

---

## PUB-001 — Hybrid Kubernetes-Serverless Autoscaling with GRU Workload Prediction

- First logged: 2026-08-07
- Status: pending
- Stage: idea
- Target venue: [to be decided — see shortlist below]
- Manuscript/artifact: `thesis-typst/build/thesis.pdf` (chapter adaptation needed — paper is a compressed version, not a cut-down thesis)
- Contribution claim: hybrid K8s+serverless autoscaling where GRU forecasts drive scaling (not routing), with explicit autoscaler fairness (node CPU bounding, r_saturation calibration) and an evidence-governed, replicated experiment (paired n=5, p=0.0304, independent replication 9/10 pairs). Evidence: ../../results/claims/FINAL_NUMBERS.md, bundles in experiments.md.
- Current next action: decide venue + co-authors (advisor) — due: after defense; then draft paper (8-page conference or ~12-page journal)
- Evidence: thesis ch01 (hypotheses), ch04 sec:replication, ../DRIFT_ANALYSIS.md §6

### 2026-08-07 — ITS requirement + venue shortlist verified
- Status: pending
- What changed: ITS requirement verified (research route needs accepted Scopus Q3/WoS journal OR published Sinta 1-4 OR seminar+journal). Venue shortlist below.
- Evidence: ITS rules above; venue facts researched with URLs
- Next action: pick venue, confirm with advisor, start paper draft

---

## Venue shortlist (2026-08-07, researched)

### International journals
|Journal|Rank|APC|Fit|Notes|
|---|---|---|---|---|
|Journal of Cloud Computing (Springer OA)|SCImago Q1 (verify year)|GBP 1340 / USD 1890 / EUR 1490|Direct fit: autoscaling, serverless, K8s|Official median first decision 40 days — fastest realistic path|
|Cluster Computing (Springer)|Q1 (verify year)|GBP 2390 / USD 3290 / EUR 2690 or subscription (no fee)|Parallel/distributed/cloud|Median first decision 25 days; hybrid OA|
|IEEE Trans. Cloud Computing|Q1 (verify year)|USD 2800 OA or subscription|Exact cloud scope|Slower review; prestige fit|
|IEEE Access|broad Q1 (verify)|USD 2160 (full OA)|Broad|4-6 wk submission-to-publication; realistic fallback|

### International conferences (Scopus-indexed proceedings; verify)
|Conference|Deadline cycle|Fit|Notes|
|---|---|---|---|
|IEEE/ACM UCC 2026|paper Aug 19 2026, notif Sep 30, camera Oct 15, meeting Dec 1-4 (Florianopolis)|serverless, cloud-edge elasticity, AI scheduling|Strong fit; fee TBA|
|IEEE CCGrid 2027|paper Dec 1 2026, notif Feb 1 2027, meeting May 24-27 (Dallas)|containers/serverless/autoscaling, learning-assisted|CORE B|
|IEEE CLOUD / CloudCom / ACM SoCC|cycle-dependent|cloud|Alternatives; check current CFP|

### Indonesian national journals (SINTA)
|Journal|SINTA|APC|Fit|Notes|
|---|---|---|---|---|
|Register (Unipdu)|S1 + Scopus|USD 500 (from Jul 2026)|Cloud/Virtualization/Parallel + AI/ML/Forecasting|5-10-day first decision; direct topic fit|
|JTIIK (Univ. Brawijaya)|S2|Rp 2M (after acceptance, from Apr 2026)|Smart Cloud Technology scope|Explicit cloud scope, lower APC|
|RESTI (IAII)|S2 + Scopus|IDR 5M then 7.5M (from Aug 2026)|AI/Computer Science Applications|Review 2-10 mo|
|JUTI (ITS)|S3|free|General IT/network|ITS's own journal; 60d to acceptance|
|Lontar Komputer (Unud)|S2|IDR 1.5M|Neural-network/network|1-3 mo review|

### Recommended plan (best 3)
1. **Journal of Cloud Computing** — submit ~Sep 2026 → first decision Oct → acceptance Nov-Jan. Meets "accepted international journal" (regular route) or Q1 (research route if Scopus Q1 confirmed).
2. **Register** (S1+Scopus) — for a guaranteed SINTA 1-4 publication path (research route); fast decision.
3. **UCC 2026** (oral) — pairs with the journal for the research route's seminar requirement; deadline Aug 19 2026.

**Reality check:** no acceptance guaranteed; ranks/APCs need edition verification before submission. The research route needs an accepted Q3+/WoS journal OR published SINTA 1-4, plus the seminar requirement — plan for both a journal AND an oral presentation.

---

*Conventions: append events per PUB ID; statuses per README.md.*
---
