---
# Publication Pipeline

`stage`: `idea | outline | draft | internal review | submitted | revision | accepted | rejected | published`. `status`: latest event per `PUB` ID. Venue correspondence logged verbatim in [venue-communications.md](venue-communications.md) via `VEN-...`.

## ITS S2 publication requirement (verified 2026-08-07)

**Author context:** S2 Informatics, ITS Surabaya — Muhammad Zahid Masruri, NRP 6025221041 (user-confirmed 2026-09-10; earlier entry had wrong 6025222041); supervisors Prof. Tohari Ahmad & Royyana Muslim Ijtihadie.

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
- Stage: outline
- Target venue: CCGrid 2027 (proposed 2026-09-10; abstract 2026-11-24, paper 2026-12-01, notification 2027-02-01, Dallas-Fort Worth 2027-05-24/27) — adviser confirms
- Manuscript/artifact: new 6–7 page conference paper (separate from the thesis; existing results only)
- Contribution claim: hybrid K8s+serverless autoscaling where GRU forecasts drive scaling (not routing), with explicit autoscaler fairness (node CPU bounding, r_saturation calibration) and an evidence-governed, replicated experiment (paired n=5, p=0.0304, independent replication 9/10 pairs). Evidence: ../../results/claims/FINAL_NUMBERS.md, bundles in experiments.md.
- Current next action: draft the paper from the outline below — due: 2026-09-24; submit before 2026-12-01
- Evidence: thesis ch01 (hypotheses), ch04 sec:replication, ../DRIFT_ANALYSIS.md §6

### 2026-08-07 — ITS requirement + venue shortlist verified
- Status: pending
- What changed: ITS requirement verified (research route needs accepted Scopus Q3/WoS journal OR published Sinta 1-4 OR seminar+journal). Venue shortlist below.
- Evidence: ITS rules above; venue facts researched with URLs
- Next action: pick venue, confirm with advisor, start paper draft

### 2026-09-10 — adviser directive: short conference paper, venue before January
- Status: pending
- What changed: the adviser approved the FRS request and redirected the publication. Write a 6–7 page conference paper using only results that already exist, from scenarios S1–S4 and the paired S3/S4 comparison. The paper does not need to cover the whole thesis. It must state the context clearly and why the work matters. Submission must fall before January 2027. A conference paper of this length also serves the ITS regular route, which accepts an oral presentation in an indexed international seminar.
- Evidence: adviser message [advisor-whatsapp.md](advisor-whatsapp.md) WA-2026-09-10-01; numbers from [../../results/claims/FINAL_NUMBERS.md](../../results/claims/FINAL_NUMBERS.md)
- Next action: confirm the venue with the adviser, then draft the paper from the outline below

### 2026-10-13 — TIME-E 2026 not registered; Scopus conference search reopened
- Status: pending
- What changed: the conference was never registered. TIME-E 2026 (paper deadline 2026-09-20) has passed, so it cannot take this paper. The adviser asked for a Scopus-indexed conference. CCGrid 2027 is the candidate already in this log (paper deadline 2026-12-01, abstract 2026-11-24, per wikicfp). Its Scopus indexing is `[INFERENCE]`; the CCGrid site was not checked in this session.
- Title mismatch: three titles exist. `paper/conference.typ` says "Hybrid Kubernetes-Serverless Routing: A Test of Guessing Against Reacting". `paper/journal.typ` says "Hybrid Kubernetes-Serverless Routing: Design, Paired Evaluation, and Host-Load Instrumentation". The outline above proposes "GRU-Based Predictive Autoscaling for Hybrid Kubernetes and Serverless Clusters". Pick one before submission.
- Contribution wording applied 2026-10-13 to `paper/sections/content.typ` (abstract, introduction, contribution list), thesis ch01, ch02 and ch03, and `ringkasan-penelitian.md`. The "confidence-gated" wording is removed. The scaling path has no confidence check: `apps/routing/routing/daemon/service.py` lines 607–662 use the forecast without one, and `apps/prediction/prediction/gru_predictor.py` lines 628–636 give confidence 0.8 or 0.6 against a 0.5 threshold, so no gate would ever close.
- Open, not changed in this event: `thesis-typst/src/content/ch03-methodology.typ` Algorithm 1 pseudocode (PREDICTIVE branch, lines 125–129) and the PREDICTIVE bullet (line 103) still say the forecast can move routing weights. The v3 routing code, which the daemon imports, does not do that. `ch02-literature.typ` line 90 (PulseNet row) still names "confidence-gated prediction".
- Next action: user finds a Scopus-indexed conference and confirms CCGrid or an alternative before 2026-11-24 — owner: user — `pending`.
- Evidence: `results/claims/FINAL_NUMBERS.md`; code references above; `WA-2026-10-13-01`; `VEN-2026-10-13-01`.

### 2026-10-13 (later) — follow-up: Algorithm 1 and ElaX wording corrected
- Status: pending
- What changed: the "Open" items in the event above are closed. The thesis Algorithm 1 table and the PREDICTIVE bullet in ch03 described the earlier priority-ladder controller (SCALE_OUT, OPTIMIZE_COST, ten-point steps). Every S3 and S4 run in `results/experiments/phase-b/2026-09-20_h2-confirmatory-10p/` records `controller_version` v3 in its manifest, and its `daemon.log` shows `controller_decision_v3` with direct capacity splits (for example 100/0 to 70/30 in one cycle). Ch03 now describes V3: capacity split, 50% cap, pacing term, labels. The same fix reached ch01, ch02, ch04 (Phase A1 labelled as the earlier controller), ch05, the paper design section and `ringkasan-penelitian.md`. The ch02 PulseNet row no longer says "no confidence-gated prediction".
- ElaX wording, checked against `docs/references/elax-elastic-provisioning-containerized-2019.pdf` section III: ElaX predicts 60 per-minute points once an hour with an LSTM and reserves for the largest predicted value. So multi-step forecasting is inherited, not new. The thesis now states what changed: GRU, 135 s horizon refreshed every 15 s, the larger of the observed and forecast replica targets with a 90 s hold, and routing between two backends. It states that ElaX's slack-based feedback controller and vertical scale-up are not reimplemented.
- Still open, not changed: (a) the pacing term looks unable to fire at a 15 s cadence. Allowed burn is 1000/1200 = 0.83 cycles per second and the largest possible burn is one violating cycle per 15 s = 0.067. This arithmetic is `[INFERENCE]`. In the one run inspected (S4 run 10 of the bundle above) `burn_adjustment` stayed 0 and `budget_remaining` stayed 1000. (b) The Knative pre-warm request returned HTTP 404 in that run's log, so the claim that pre-warming reduces cold-start latency is unverified. (c) ch04 lines about the n = 1 ClarkNet diagnostic still mention OPTIMIZE_COST and "the confidence gate". The controller version of those older diagnostics is unverified. (d) The V3 module docstring still says S3 uses V1 and that total load is max(observed, predicted). The code does neither.
- Evidence: `apps/routing/routing/algorithm/algorithm1_v3.py` lines 217–294; `apps/routing/routing/algorithm/registry.py` lines 83–94; run manifests and `daemon.log` named above.

### 2026-10-19 — conference paper rewritten from the evidence; venue shortlist renewed
- Status: pending
- What changed: the paper was rewritten from scratch around the three contributions agreed on 2026-10-13. One title replaces the three in the event of 2026-10-13: "Forecast-Driven Replica Scaling in a Hybrid Kubernetes–Knative Deployment: Architecture and Paired Evaluation". Structure: Introduction (ElaX gap, three contributions), Related work (with a table of what Algorithm 2 keeps from ElaX and what it changes), Control architecture (Algorithm 1 and Algorithm 2 as pseudocode, node tier), GRU forecaster (leak-free protocol, accuracy against persistence, LSTM and linear autoregression), Experimental setup, Results (four scenarios; three paired batches and the pooled 25 pairs; why the forecast did not help), Discussion, Conclusion. The conference build is 5 A4 pages, anonymous.
- Evidence pipeline: `paper/derive_numbers.py` derives every measured value from the bundles into `paper/numbers.json`; the prose interpolates it. `make check` in `paper/` fails when the JSON is stale or when the prose types a number that is not a listed configuration constant.
- Corrections against the old paper: Algorithm 1 no longer reads the forecast; the S3/S4 "serverless share" is the weight-time share, not a request share; the 102 ms paired sd is replaced by the measured sd per batch (84 ms in batch C); the July batch is described as unattributable history, not evidence.
- Venue: TIME-E 2026 is closed. Ranked shortlist (VEN-2026-10-19-01): ICAIIC 2027 (deadline 2026-11-15, 6 pages, virtual author fee USD 550, IEEE technical co-sponsorship; Scopus unverified), IEEE CCGrid 2027 (abstract 2026-11-24, paper 2026-12-01, 10 pages, double-blind, no online option found), TECHNOVA-GRACE 2027 (online, deadline window from 2026-12-15; indexing unproven).
- Next action: adviser picks the conference; submit `paper/conference.pdf` before its deadline — owner: user — `pending`.
- Evidence: `paper/numbers.json`; bundles named in `paper/derive_numbers.py`; `thesis/logbook/decisions-2026-10-19-paper-rewrite.tsv`.

### 2026-10-19 (later) — adversarial review applied to both papers
- Status: pending
- What changed: a hostile review (6 must-fix, 16 should-fix, 14 nits) was applied. The largest fix: the four-scenario batch (2026-08-09) ran S4 with an earlier GRU (envelope about 10 RPS above the point forecast, against 55–60 RPS for the leak-free model), so the paper now claims the S1/S2 comparison for the architecture only. The headline is the pre-specified batch C (−13.6 ms, 95% CI [−63.5, +35.6], p = 0.307). The two hybrids used 30% (S4) and 36% (S3) fewer pod-seconds than HPA at the same projected cost. Other fixes: the router wording (the routing weight does not depend on the forecast), the testbed facts (Knative has one three-CPU worker and three to ten warm pods; each request computes fib(33) and then waits 50 ms), the gates, the delay design, the bibliography metadata, MArk and Spock added as the closest prior work, the post-hoc quiet-host subset labelled as such, and the margin-only ablation stated as untested. The n = 1 diagnostic with the non-scaling S1 arm was removed.
- Stats fix found on the way: `paired_permutation_p_from_diffs` dropped the observed arrangement through float rounding (9/256 instead of 10/256 for the quiet subset). Fixed in commit `44ef4db` with a regression test; the four stored H2 verdicts are unchanged.
- Build: `paper/conference.pdf` 6 pages A4, anonymous (no author strings), 29 references.
- Open: an S1/S2/S3/S4 rerun with the leak-free GRU would let the four-scenario table measure the described system; not run.
- Evidence: `thesis/logbook/decisions-2026-10-19-paper-rewrite.tsv`; `paper/numbers.json`; `results/claims/FINAL_NUMBERS.md` (Replication 2026-08-09, S4 predictor).

### PAPER-001 outline (6–7 pages, IEEE two-column)
- Title and abstract: proposed title "GRU-Based Predictive Autoscaling for Hybrid Kubernetes and Serverless Clusters". Keywords: Kubernetes, serverless, autoscaling, workload prediction, GRU. Abstract of 120–150 words, no citations.
- Framing note: serverless carries the paper's emphasis, because the study compares a Kubernetes backend against a serverless backend and then the two hybrid modes. State one caveat in the first paragraph of Section III, or a reviewer will read the platform claim as false: both backends run on a single k3d testbed, simulating a two-platform deployment, with separate namespaces, separate ingress paths, and separate workload instances (`ch03-method`, `ch03-infra`).
- Serverless evidence to use: at 200 RPS constant load, S1 with dynamic nodes but no offload held only 65,6 percent success at p99 6.665 ms, while S3 held 96,5 percent of time in serverless at p99 874 ms. Serverless offload absorbed the 51–70 s node provisioning delay. S2 (Knative-only) is the pure serverless baseline at n = 1.
- I. Introduction (about 1 page). Context: two deployment paradigms and their limits. Why it matters: node provisioning takes 45–120 s, reactive control reacts after the peak, and p99 violations carry service penalties. Contributions: (a) GRU horizon sized to measured provisioning delay, (b) two-mode cluster controller, (c) utilization-based node consolidation matching Cluster Autoscaler, (d) paired replication with published statistics.
- II. Related work (about 0.5 page). ElaX, predictive autoscaling, serverless offloading, hybrid cluster management.
- III. Method (about 1.5 pages). Figure 1: architecture (HAProxy entry, Algorithm 1 routing, Algorithm 2 scaling, Prometheus and SLO monitor, K3dAutoscaler). Figure 2: GRU design (30 samples at 15 s in, 9 steps / 135 s out). Subsection: scenario definitions S1–S4 and the counterbalanced paired design.
- IV. Evaluation (about 2 pages). Setup: ClarkNet window 1995-09-02 04:35:30–04:55:00 UTC, 40 stages of 30 s, 22–164 RPS, SLO p99 200 ms, permutation test with alpha 0.05. Table I: four-scenario n=5 replication (mean p99 S1 110.3; S2 79.7; S3 151.6; S4 99.1 ms; SLO violations S3 1,998 vs S4 92). Figure 3: GRU forecast against actual on ClarkNet. Table II: definitive paired n=5 (p99, SLO violations, cost, p values, effect sizes). Replication paragraph: retained batches only, 08-08 RUN1 p=0.436 (null) and RUN2 p=0.062 (marginal), 08-09 paired analysis p=0.032, all S4-favorable; the 08-07 batches were deleted and are excluded (ch04 sec:replication). Cost-model paragraph: state the mapping (EC2 t3.medium USD 0.0416/h times measured node lifetime from provision events, EKS control plane per hour, Lambda Provisioned Concurrency instances = RPS times execution time billed per 300 s), the node-based limitation (warm replicas invisible; S4 5 vs S3 3 replicas is about USD 2.2/mo at per-vCPU-second), and that S3=S4=USD 163/mo is model output, not a bill. Node-consolidation diagnostic paragraph. Threats-to-validity paragraph.
- V. Discussion (about 0.5 page). Three necessary conditions for the predictive gain, and where the result does not transfer.
- VI. Conclusion (about 0.3 page).
- References: 20–25 entries, drawn from the thesis bibliography.
- Assets to reuse: `results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5/raw/*/prediction-actual.parquet` for the forecast figure; `metrics.parquet` for latency series; thesis figures in `thesis-typst/src/content/figures.typ`.

### Conference options with a deadline before January 2027 (researched 2026-09-10)
| Venue | Deadline | Notification | Where | Fit | Status |
|---|---|---|---|---|---|
| IEEE CCGrid 2027 | abstract 2026-11-24, paper 2026-12-01 | 2027-02-01 | Dallas-Fort Worth, 2027-05-24/27 | Best fit: cluster, cloud, and internet computing, serverless elasticity, learning-assisted scheduling | Proposed primary |
| IEEE ICC 2027 | 2026-10-02 | 2027-01-15 | to confirm | Weak fit: communications scope, cloud and edge symposium only | Backup |
| IEEE ICDCS 2027 | mid-January by series history | April | to confirm | Strong scope, but the deadline falls after January, so it fails the adviser's window | Not eligible |
| IEEE/ACM UCC 2026 | passed (2026-08-19) | passed | Florianopolis | Strong fit | Closed |

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

## PUB-002 — Hybrid Kubernetes-Serverless Routing (journal track)

- First logged: 2026-10-13
- Status: pending
- Stage: draft. `paper/journal.typ` builds at 5 pages from the same content source as the conference version.
- Target venue: Kinetik (Universitas Muhammadiyah Malang), the user's candidate. The adviser is still asking which journal fits. Not confirmed.
- Indexing check (2026-10-13): Kinetik's indexing page lists SINTA S2, BASE, ROAD, Google Scholar, Garuda, Dimensions, Ingenta Connect and EBSCOHost. It does not list Scopus. The adviser asked for a Scopus venue. The "SINTA 2 + Scopus" note in `docs/plans/2026-09-18-publication-venues.md` is `unverified`.
- Authors: `paper/journal.typ` lists Royyana Muslim Ijtihadie as co-author. The chat does not record the adviser agreeing to this. `unverified`.
- Next action: confirm the journal with the adviser, and check Kinetik's Scopus status before submitting — owner: user — `pending`.
- Evidence: `results/claims/FINAL_NUMBERS.md`; `WA-2026-10-13-01`; `VEN-2026-10-13-01`.

### 2026-10-19 — journal version rewritten; Kinetik is not Scopus-indexed
- Status: pending
- Stage: draft. `paper/journal.pdf` builds at 6 pages from the same body as the conference version, with journal-only blocks: a cold-start and scaling-control paragraph in related work, the design reasoning behind the decision factor, the GRU search result, envelope coverage and probe variants, run conditioning, the cost model, the per-run boxplot, the node-tier timing, and a data-availability statement.
- Indexing: Kinetik's About page lists "SINTA 2, Scholar Metrics, Google Scholar" (checked 2026-10-19). Kinetik meets a SINTA requirement, not a Scopus one. Scopus-indexed alternatives: Journal of Cloud Computing (Springer, Scopus and SCIE; collections close 2026-12-31) and Jurnal RESTI (self-reported Scopus source 21101288925; APC IDR 8,500,000). Neither was confirmed on scopus.com itself in this session.
- Format gap: Kinetik asks for 6–10 pages in its Word template with sections Introduction, Research Method, Results and Discussion, Conclusion, and at least 25 references, 20 of them journal papers. The journal build is in the IEEE layout and cites 31 works, many of them conference papers or preprints. Port to the chosen journal's template once the adviser decides.
- Next action: adviser chooses the journal; then port `paper/journal.pdf` to its template — owner: user — `pending`.
- Evidence: `VEN-2026-10-19-01`; `paper/journal.pdf`.

### 2026-10-19 (later) — journal version after the review
- Status: pending
- Stage: draft. `paper/journal.pdf` builds at 7 pages with 34 references, which replaces the 6 pages and 31 works stated above. New journal-only material: the search budget (6 trials per input length, input lengths 20 and 30), per-step error against the linear model, the warm-up request note, the delay sequence, the cost-model formula, and the S2 capacity asymmetry.
- Gap: a Scopus journal usually expects a longer manuscript (often 10 or more pages, and about 30% new material over a conference version). The extensions that would close it are the four-scenario rerun with the leak-free GRU, a constant-margin ablation, and a per-backend tail decomposition.
- Next action: adviser chooses the journal — owner: user — `pending`.
- Evidence: `paper/journal.pdf`; `thesis/logbook/decisions-2026-10-19-paper-rewrite.tsv`.

*Conventions: append events per PUB ID; statuses per README.md.*
---
