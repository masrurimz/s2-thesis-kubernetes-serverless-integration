# ICAIIC 2027 submission packet (PUB-001)

Everything needed to submit `PUB-001` to ICAIIC 2027. Events stay in [publications.md](publications.md) and
[venue-communications.md](venue-communications.md) (`VEN-2026-11-12-01`). Checked 2026-11-12.

## 1. Venue facts

| Item | Value | Source |
|---|---|---|
| Conference | The 9th International Conference on Artificial Intelligence in Information and Communication, 2027-02-22 to 2027-02-25, Nakanoshima Center, Osaka University, Japan, and virtual | [CFP v7](https://icaiic.org/wp-content/uploads/2026/10/ICAIIC-2027-CFP-v7.pdf) |
| Submission deadline | 2026-11-15, time zone not stated | [icaiic.org](https://icaiic.org/), [submission page](https://icaiic.org/submission/) |
| Acceptance notification | 2026-12-15 | same |
| Camera-ready, copyright form | 2027-01-01 | same |
| Author registration | on or before 2027-01-05; virtual author USD 550, onsite author USD 650 | [registration page](https://icaiic.org/registration/) |
| Format | PDF, IEEE conference style, two columns, single-spaced, at least 10 pt, A4 or letter | submission page |
| Length | full paper 3 to 6 pages; extra pages USD 50 each, at most 2 | submission and registration pages |
| Submission system | EDAS, https://edas.info/N35066 | submission page |
| Sponsors | organized by KICS, Osaka University, Kookmin University; technical co-sponsorship IEEE ComSoc and IEICE NOLTA Society | CFP v7; site news of 2026-10-14 |
| Indexing | "published in the ICAIIC Conference Proceedings with an assigned ISBN number and submitted to IEEE Xplore, Scopus, and EI Compendex" | CFP v7 |
| Review anonymity | not stated on the site or in the CFP | see section 3, step 4 |
| Refund | 70% until 2027-01-31, none after | registration page |

Open venue facts:

- Scopus. The CFP promises submission to Scopus. A web search on 2026-11-12 returned a SCImago source page titled
  "International Conference on Artificial Intelligence in Information and Communication, ICAIIC" (source id
  21101299653), and SCImago lists Scopus sources only. The page itself refused a scripted read (HTTP 403), so open
  https://www.scimagojr.com/journalsearch.php?q=21101299653&tip=sid&clean=0 or https://www.scopus.com/sources once.
- ITS grade. ICAIIC is not in CORE (portal search 2026-10-20, [publication-targets.md](publication-targets.md)), so
  the seminar row grades it B. CCGrid 2027 is CORE B and grades A, but needs a 10-page paper and travel to Dallas.
- ITS also asks for more than 5 countries. Not checked for ICAIIC 2027; the 2026 program book would show it.

## 2. Files to upload

| File | Use | Verified 2026-11-12 |
|---|---|---|
| `paper/conference-named.pdf` | upload when EDAS does not ask for an anonymous manuscript; also the base for the camera-ready | 6 pages, A4, 10 pt body, 7 fonts all embedded, author block present (rewritten 2026-11-12) |
| `paper/conference.pdf` | upload when EDAS says the review is double-blind | 6 pages, A4, 10 pt body, 7 fonts all embedded, 0 lines matching author or institution strings (rewritten 2026-11-12) |

Both come from the same body. `make check` in `paper/` passed: `numbers.json` matches the bundles and the prose
types no measured number. Rebuild with `cd paper && make`. Page 6 has about six reference lines spare, so
recheck the page count after any edit to the text or to `thesis-typst/src/bibliography.bib`.

## 3. EDAS steps

1. Log in or create an account at https://edas.info. Use the name and affiliation exactly as in section 4.
2. Open https://edas.info/N35066 and register the paper as a full paper.
3. Paste the title, abstract, keywords and topic from section 4. Add every author in the order of section 4.
   Each co-author needs an EDAS account; EDAS can create one from name, email and affiliation.
4. Read what the registration page says about anonymity. If it says double-blind or forbids author names in the
   manuscript, upload `paper/conference.pdf`. Otherwise upload `paper/conference-named.pdf`.
5. Upload the PDF, then open the stored file from "My Papers" and check the page count is 6.
6. Paste the EDAS paper number into `VEN-2026-11-12-01` and `PUB-001`.

Submit on 2026-11-14 WIB. The deadline has no stated time zone, and a manuscript can usually be replaced on EDAS
until the deadline closes. Many IEEE-sponsored conferences freeze the author list at the deadline, so settle
section 4's author list before submitting.

## 4. Text to paste

**Title**

Scaling Kubernetes Replicas with GRU Forecasts and Routing Overflow to Serverless

**Authors, in order** (from `paper/authors.typ`; the EDAS list must match the PDF)

1. Muhammad Zahid Masruri, Department of Informatics, Institut Teknologi Sepuluh Nopember, Surabaya, Indonesia, masruri03@gmail.com
2. Royyana Muslim Ijtihadie, Department of Informatics, Institut Teknologi Sepuluh Nopember, Surabaya, Indonesia, roy@if.its.ac.id

Open: the thesis lists two supervisors, and Prof. Tohari Ahmad is not in this list. ITS requires the adviser as
a co-author. Ask Pak Roy (draft `WA-2026-11-12-01`). Adding an author is one entry in `paper/authors.typ`.

**Topic** (pick the closest one EDAS offers)

1. AI for Data Analysis, Big Data and Cloud
2. AI for Control, Decision and Autonomous Intelligence

**Keywords**

Kubernetes, serverless computing, autoscaling, workload prediction, gated recurrent unit, traffic routing

**Abstract** (233 words, plain text, same as the PDF)

Kubernetes adds pods only after the load has risen, so requests wait while new pods and nodes start. A serverless platform adds instances within seconds but costs more per request. A hybrid uses both. Kubernetes serves the base load, and the serverless platform takes the overflow. We ask whether a load forecast still helps in such a hybrid. Every 15 s, our control loop sends to Knative only the load that the ready Kubernetes pods cannot serve, and a scaler derived from ElaX sets the number of pods. In the predictive hybrid, the scaler also reads a 135 s forecast from a gated recurrent unit (GRU), plus a safety margin, and adds pods before the load arrives. The reactive hybrid has no forecast. We replayed the ClarkNet web trace against both hybrids, Kubernetes with the Horizontal Pod Autoscaler (HPA), and Knative alone. Both hybrids matched the projected cost of Kubernetes with the HPA, but the reactive hybrid had a higher 99th-percentile latency (p99). In ten pairs of runs planned in advance, the forecast changed p99 by -13.6 ms (95% CI [-63.5, +35.6], p = 0.307) and used 45% more pod-seconds. This design detects differences above about 72 ms. The GRU was also no more accurate than a linear autoregression. One explanation that fits these results is that Knative already serves the load during the start-up delay that the forecast was meant to cover.

**Short abstract** (199 words; paste this one if EDAS caps the field at 200 words. The PDF keeps the longer abstract; IEEE allows up to 250 words.)

Kubernetes adds pods only after the load has risen, so requests wait while new pods and nodes start. A serverless platform adds instances within seconds but costs more per request. A hybrid serves the base load on Kubernetes and sends the overflow to serverless. We ask whether a load forecast still helps in such a hybrid. Every 15 s, our control loop sends to Knative only the load that ready Kubernetes pods cannot serve, and a scaler derived from ElaX sets the number of pods. In the predictive hybrid, the scaler reads a 135 s forecast from a gated recurrent unit (GRU) and adds pods before the load arrives. We replayed the ClarkNet trace against both hybrids and Kubernetes with the Horizontal Pod Autoscaler (HPA). Both hybrids matched the projected cost of Kubernetes with the HPA, but the reactive hybrid had a higher 99th-percentile latency (p99). In ten planned pairs, the forecast changed p99 by -13.6 ms (95% CI [-63.5, +35.6], p = 0.307) and used 45% more pod-seconds. The GRU was no more accurate than a linear autoregression. One explanation is that Knative already serves the load during the start-up delay that the forecast was meant to cover.

## 5. After acceptance (2026-12-15 onward)

1. Apply the reviewers' comments to `paper/sections/body.typ`, rebuild, keep 6 pages.
2. Validate `paper/conference-named.pdf` at https://ieee-pdf-express.org/ with conference ID `68212X`. The site
   asks for embedded fonts, no bookmarks and no links. Fonts are embedded. The Typst PDF carries link
   annotations on reference URLs, so expect to strip them if the check fails.
3. Upload the validated PDF as "Final Manuscript" on EDAS and sign the IEEE copyright form from the EDAS paper
   page. Both are due 2027-01-01.
4. Pay the author registration by 2027-01-05 (virtual USD 550, onsite USD 650; card or bank transfer).
5. Present on 2027-02-22 to 2027-02-25. Keep the presenter certificate and a photo or recording of the talk.
6. ITS documents (section 1a of [publication-targets.md](publication-targets.md)): article file, presentation
   documentation, presenter certificate, form "Pernyataan Telah Melakukan Publikasi Ilmiah" signed by student,
   adviser and Kaprodi. Submit at https://its.id/PublikasiIlmiahS2IF.
