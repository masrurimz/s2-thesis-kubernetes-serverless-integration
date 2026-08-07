# Advisor WhatsApp Log

## Contact

| Field | Value |
|---|---|
| Advisor | [Nama Dosen] |
| Program / NIM | [Prodi] / [NIM] |
| Channel | WhatsApp |
| Thesis | Decision Making and Elastic Scalability Management in Heterogeneous Cloud Environments Based on Workload Prediction |

## Thread status

- **Current state:** initial outreach drafted, **not yet sent** (2026-08-07)
- **Next action:** send WA-2026-08-07-01 during office hours (Tue–Fri 09:00–15:00)
- **Fallback:** no reply within 2–3 working days → WA follow-up; then email as second channel

## Timeline

| Date | Event | Status |
|---|---|---|
| 2026-08-07 | Initial outreach drafted (evidence-tiered) | pending |

---

## WA-2026-08-07-01 — Initial outreach

### 2026-08-07 14:00 — draft
- Direction: out
- Status: pending
- Message (verbatim, Bahasa Indonesia):
> Selamat pagi, Pak/Bu [Nama Dosen]. Saya [Nama], mahasiswa [Prodi], NIM [NIM], bimbingan Bapak/Ibu. Mohon maaf mengganggu.
>
> Saya ingin melaporkan perkembangan tesis saya yang berjudul *"Decision Making and Elastic Scalability Management in Heterogeneous Cloud Environments Based on Workload Prediction"*:
> 1. Kelima sprint penelitian telah selesai — eksperimen 4 skenario (S1–S4) selesai dijalankan. Hasil definitif: skenario hibrida-prediktif (S4) mengungguli hibrida-reaktif (S3) pada p99 (126.0 vs 188.5 ms; p=0.0304), dan **arah ini dikonfirmasi replikasi independen** (S4 menang 9/10 pasangan, pooled p=0.003).
> 2. Naskah tesis selesai disusun ulang dan siap direview (PDF), termasuk **analisis drift proposal→pelaksanaan** dengan 17 sitasi terarsip.
> 3. Target pendaftaran sidang: [tanggal/minggu].
>
> Boleh saya meminta waktu bimbingan minggu ini/pekan depan untuk memaparkan ringkasan dan meminta masukan? Saya bisa hadir [Senin 09.00 / Selasa 13.00 / Rabu 10.00], atau menyesuaikan jadwal Bapak/Ibu. Sebelumnya, boleh saya kirim ringkasan 1 halaman + PDF naskahnya?
>
> Terima kasih, Pak/Bu. Salam hormat,
> [Nama] — [NIM] — [No. HP]

- English note: Intent = report completion, bridge the 1.5-year gap with evidence, request bimbingan with concrete slots. Draft was **evidence-tiered on 2026-08-07**: the definitive claim (p=0.0304) is attributed to the final bundle; the pooled p=0.003 is explicitly labeled replication (diagnostic tier). Earlier draft version headlined p=0.003 without the tier — corrected before sending.
- Attachments: none (offer 1-page summary + PDF in the message)
- Evidence for factual claims in the message:
  - Definitive H2 (p=0.0304, 126.0 vs 188.5 ms): `results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5/` (role=**final**)
  - Replication (9/10 pairs, pooled p=0.003): `results/experiments/phase-b/2026-08-07_paired-h2_060200/` + `2026-08-07_paired-h2_104918/` (role=**diagnostic**) — [../../results/claims/FINAL_NUMBERS.md](../../results/claims/FINAL_NUMBERS.md)
  - Drift analysis with 17 citations: [../DRIFT_ANALYSIS.md](../DRIFT_ANALYSIS.md)

### [pending events: sent / received / actioned]

- When sent: append "sent" event here with the exact delivered text (even if identical to the draft), status `sent`.
- On reply: append "received" event with the verbatim incoming text, status `replied`, plus English interpretation and requested action/due date.
- After the follow-up is done: append "actioned" event linking `BIM-...`/`PUB-...`.

---

## WA-2026-08-07-02 — Follow-up template (no reply in 2–3 working days)

### 2026-08-07 14:00 — draft
- Direction: out
- Status: pending
- Message (verbatim, Bahasa Indonesia):
> Selamat pagi, Pak/Bu [Nama]. Mohon maaf mengganggu lagi — saya menanyakan ulang kesediaan waktu bimbingan untuk tesis saya (ringkasan progres sudah saya siapkan, tinggal kirim). Terima kasih.
- English note: single gentle nudge; do not repeat the full report.
- Attachments: none
- Evidence: none (no factual claims)

---

## WA-2026-08-07-03 — Confirmation + materials (after advisor agrees)

### 2026-08-07 14:00 — draft
- Direction: out
- Status: pending
- Message (verbatim, Bahasa Indonesia):
> Terima kasih, Pak/Bu. Saya kirim ringkasan 1 halaman (lampiran) — PDF naskah lengkap bisa saya kirim juga atau saya bawa saat bimbingan. Saya hadir [hari, jam, tempat]. Terima kasih.
- English note: attachments = the shareable handout only; the full thesis PDF is offered, not dumped.
- Attachments:
  - `progress-summary.md` exported to PDF — [progress-summary.md](progress-summary.md) (keep in sync with FINAL_NUMBERS before sending)
  - `thesis-typst/build/thesis.pdf` (offer only)
- Evidence: handout numbers verified against [../../results/claims/FINAL_NUMBERS.md](../../results/claims/FINAL_NUMBERS.md)

---

*Conventions: append events, never rewrite. Statuses: pending → sent → replied → actioned. See [README.md](README.md).*
