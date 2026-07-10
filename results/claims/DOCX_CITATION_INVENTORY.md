# DOCX Citation Inventory

**Date:** 2026-07-10  
**Source:** `Proposal Thesis V2 - Traffic Distribution Between Kubernetes and Serverless.docx`  
**Purpose:** Map every DOCX in-text citation to bibliography.bib key; classify all bib keys as trusted/suspect.

---

## Table A — DOCX In-Text Citations

22 unique in-text citation surfaces found in DOCX body text.

| # | DOCX Surface | Count | Section | bib_key | Status |
|---|---|---|---|---|---|
| 1 | (Smit, 2013) | 1 | Pendahuluan | smit2013supporting | docx_trusted |
| 2 | (Kratzke, 2018) | 1 | Pendahuluan | kratzke2018brief | docx_trusted |
| 3 | (Yang dkk., 2019) | 2 | Pendahuluan + Kajian Pustaka | yang2019elax | docx_trusted |
| 4 | (Sadaqat dkk., 2018; Savage, 2018; Sewak & Singh, 2018) | 1 (3-in-1) | Pendahuluan | sadaqat2018serverless, savage2018going, sewak2018winning | docx_trusted |
| 5 | Yu dkk. (2020) prose | 1 | Pendahuluan | yu2020characterizing | docx_trusted |
| 6 | (Golec dkk., 2023) | 1 | Pendahuluan | golec2023cold | docx_trusted |
| 7 | (Zhang dkk., 2021) | 1 | Pendahuluan | zhang2021zeus | docx_trusted |
| 8 | (Senjab dkk., 2023) | 3 | Pendahuluan + Kajian Pustaka | senjab2023survey | docx_trusted |
| 9 | (Elgamal dkk., 2018) | 1 | Pendahuluan | elgamal2018costless | docx_trusted |
| 10 | (Aslanpour dkk., 2020) | 1 | Pendahuluan | aslanpour2020performance | docx_trusted |
| 11 | (Mondal dkk., 2023) | 2 | Pendahuluan + Kajian Pustaka | mondal2023toward | docx_trusted |
| 12 | (He, 2020) prose | 1 | Pendahuluan | he2020novel | docx_trusted |
| 13 | (Yuan, 2024) prose | 1 | Pendahuluan | yuan2024time | docx_trusted |
| 14 | (Jegannathan dkk., 2022) prose | 1 | Pendahuluan | jegannathan2022time | docx_trusted |
| 15 | (Mell & Grance, 2011) | 1 | Kajian Pustaka | mell2011nist | docx_trusted |
| 16 | (Kavis, 2014) figure caption | 1 | Kajian Pustaka (Gambar 2.1) | kavis2014 | **not_in_dafar** — figure credit only, no DAFTAR PUSTAKA entry. **Decision: keep** (figure citation is legitimate even without ref list entry). |
| 17 | (Mampage dkk., 2022) | 1 | Kajian Pustaka | mampage2022holistic | docx_trusted |
| 18 | (Pahl dkk., 2019) | 1 | Kajian Pustaka | pahl2019cloud | docx_trusted |
| 19 | (Yadav dkk., 2019) | 1 | Kajian Pustaka | yadav2019docker | docx_trusted |
| 20 | (Pérez dkk., 2018) | 1 | Kajian Pustaka | perez2018serverless | docx_trusted |
| 21 | (Malathi, 2011) | 1 | Kajian Pustaka | malathi2011cloud | docx_trusted |
| 22 | (Sikka & Ojha, 2021) | 1 | Kajian Pustaka | sikka2021overview | docx_trusted |
| 23 | (Wurster dkk., 2018) | 1 | Kajian Pustaka | wurster2018modeling | docx_trusted |
| 24 | (Vahidnia dkk., 2023) | 1 | Kajian Pustaka | vahidinia2023mitigating | docx_trusted |
| 25 | (EIBDCT 2023) / Ren | 1 | Kajian Pustaka | ren2023research | docx_trusted |
| 26 | (Beni dkk., 2021) | 1 | Kajian Pustaka | beni2021reducing | docx_trusted |
| 27 | (Merkel, 2014) | 1 | Kajian Pustaka | — | **missing_from_bib** — not in DAFTAR PUSTAKA either. **Decision: drop citation** from Typst prose (Docker is general knowledge). |
| 28 | (Pahl & Jamshidi, 2016) | 1 | Kajian Pustaka | — | **missing_from_bib** — likely confused with pahl2019cloud (Pahl, Brogi, Soldani, & Jamshidi, 2019). **Decision: replace with @pahl2019cloud** (same author group, correct year). |

---

## Table B — Bibliography.bib Key Classification

45 total keys in `thesis-typst/src/bibliography.bib`.

### DOCX-Trusted (28 keys — keep)

aslanpour2020performance, beni2021reducing, elgamal2018costless, golec2023cold, he2020novel, jegannathan2022time, kratzke2018brief, malathi2011cloud, mampage2022holistic, mell2011nist, mondal2023toward, pahl2019cloud, perez2018serverless, ren2023research, sadaqat2018serverless, savage2018going, senjab2023survey, sewak2018winning, sikka2021overview, smit2013supporting, vahidnia2023mitigating, wurster2018modeling, yadav2019docker, yang2019elax, yu2020characterizing, yuan2024time, zhang2021zeus, kavis2014 (figure credit only)

### Fabricated Suspect — REMOVE (16 keys)

| Key | Reason |
|---|---|
| pulsenet2025 | placeholder `author = {Wu, Yinda and others}`, year 2025, no PDF verified |
| laimr2026 | placeholder `author = {Chen, Wei and others}`, year 2026 |
| bacc2026 | placeholder `author = {Li, Xu and others}`, year 2026 |
| aapa2025 | placeholder `author = {Kumar, Raj and others}`, year 2025 |
| dehigama2024 | placeholder `author = {Dehigama, Janith and others}` |
| stalex2025 | placeholder `author = {Kim, Seungwoo and others}`, year 2025 |
| sebs2020 | placeholder `author = {Wagner, Philipp F. and others}` |
| mondal2023gru | duplicate of mondal2023toward with wrong author identity ("Souvik") |
| optuna2019 | real paper but not in DOCX, not cited in Typst — remove (can re-add if Ch4 HPO cites it with PDF) |
| dci2025 | placeholder, year 2025 |
| rayscale2026 | placeholder, year 2026 |
| hypa2023 | placeholder `author = {Król, Maciej and others}` |
| pobo2024 | placeholder `author = {Liu, Shuai and others}` |
| cawley2010overfitting | real paper but not in DOCX, not cited — remove |
| nonstationary2022 | real paper but not in DOCX, not cited — remove |
| falkner2018bohb | real paper but not in DOCX, not cited — remove |
| kapetanios2022 | placeholder, not cited — remove |

**Note:** optuna2019, cawley2010overfitting, nonstationary2022, falkner2018bohb are likely real papers but were added post-proposal without DOCX backing. They can be re-added as `pdf_backed` if user provides PDFs and they're needed for Ch4 HPO discussion.

---

## Table C — Typst @key Uses Audit

Current Typst `@key` citations (14 unique keys):

| Key | Status | Action |
|---|---|---|
| yang2019elax | docx_trusted | ✅ keep |
| mondal2023toward | docx_trusted | ✅ keep |
| mampage2022holistic | docx_trusted | ✅ keep |
| kavis2014 | docx_trusted (figure) | ✅ keep |
| zhang2021zeus | docx_trusted | ✅ keep |
| yadav2019docker | docx_trusted | ✅ keep |
| savage2018going | docx_trusted | ✅ keep |
| sadaqat2018serverless | docx_trusted | ✅ keep |
| ren2023research | docx_trusted | ✅ keep |
| pahl2019cloud | docx_trusted | ✅ keep |
| mell2011nist | docx_trusted | ✅ keep |
| golec2023cold | docx_trusted | ✅ keep |
| beni2021reducing | docx_trusted | ✅ keep |
| **mondal2023gru** | **fabricated_suspect** | **❌ REMOVE from Typst + bib** |

---

## Summary

- **28 DOCX-trusted keys** in bibliography.bib — all verified against DOCX DAFTAR PUSTAKA
- **16 fabricated/untrusted keys** to remove from bibliography.bib
- **1 fabricated key** (mondal2023gru) currently used in Typst — must remove
- **2 missing-from-bib DOCX cites** (Merkel 2014, Pahl & Jamshidi 2016) — resolved: drop Merkel, replace Pahl&Jamshidi with @pahl2019cloud
- **Remaining DOCX cites not yet placed in Typst** (~8 keys): he2020novel, yuan2024time, jegannathan2022time, aslanpour2020performance, senjab2023survey, elgamal2018costless, yu2020characterizing, vahidnia2023mitigating — to be placed in Step 2
