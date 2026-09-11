# Advisor WhatsApp Log

## Contact

| Field | Value |
|---|---|
| Advisor | Royyana Muslim Ijtihadie (Pak Roy) — dosen wali & pembimbing; co-pembimbing: Prof. Tohari Ahmad |
| Program / NRP | Magister Komputer (M.Kom), Teknik Informatika / 6025221041 (user-confirmed 2026-09-10) |
| Channel | WhatsApp |
| Thesis | Decision Making and Elastic Scalability Management in Heterogeneous Cloud Environments Based on Workload Prediction |

## Thread status

- **Current state:** replied. The adviser approved the FRS on 2026-09-10 and issued two directives: an Indonesian summary in a fixed order, and a 6–7 page conference paper from existing results with submission before January.
- **Next action:** send `ringkasan-penelitian.md` for review, confirm the venue (CCGrid 2027 proposed), then draft the paper. Bimbingan slot still open: the adviser has not fixed a day yet.
- **Fallback:** if the slot stays unset after the summary is read, propose Monday or Tuesday again in the same thread.

## Timeline

| Date | Event | Status |
|---|---|---|
| 2026-08-07 | Initial outreach drafted (evidence-tiered) | superseded |
| 2026-09-10 | FRS + bimbingan outreach sent | sent |
| 2026-09-10 | Adviser replied: FRS approved; Indonesian summary and conference paper directed | replied |

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

## WA-2026-09-10-01 — Combined FRS request + bimbingan outreach

### 2026-09-10 — draft
- Direction: out
- Status: pending
- Supersedes: WA-2026-08-07-01 (unsent; its 3-bullet report content moves to the follow-up handout `progress-summary.md`)
- Message (verbatim, Bahasa Indonesia):
> Assalamu'alaikum warahmatullahi wabarakatuh, Pak Roy.
>
> Mohon maaf mengganggu waktu Bapak. Saya Zahid (Muhammad Zahid Masruri, NRP 6025221041), mahasiswa pewalian sekaligus bimbingan tesis Bapak. Saya ingin meminta bantuan Bapak untuk dua hal:
> 1. Pengambilan FRS mata kuliah Publikasi Ilmiah dan Sidang Akhir Tesis. Saya tidak dapat mengambilnya sendiri di My ITS Academica, dan pihak akademik menyarankan lewat dosen wali langsung.
> 2. Waktu bimbingan. Senin atau Selasa saya biasanya lebih bebas. Saat ini saya berada di luar Surabaya karena pekerjaan, jadi jika berkenan, bimbingan dapat dilakukan secara online.
>
> Sekadar laporan, mohon maaf sudah lama tidak menghubungi Bapak. Alhamdulillah penelitian tesis sudah berjalan jauh. Empat skenario sudah diuji dan diulang untuk memastikan hasilnya konsisten, dan naskah sudah saya susun. Naskah ini masih perlu masukan dan review Bapak. Ringkasan 1 halaman dan PDF naskah siap saya kirim setelah ini.
>
> Terima kasih banyak, Pak. Wassalamu'alaikum warahmatullahi wabarakatuh.

- English note: first actual contact after the ~1.5-year gap. Revisions 2026-09-10: FRS ask first (urgent), report paragraph second; progress framing, never "research done" (user instruction; experiments done, manuscript drafted, review still needed). Technical-writing pass: no em dashes, one apology, one thought per sentence, no "pendaftaran sidang" phrasing, slots Monday/Tuesday, online stated (user outside Surabaya, working). NRP 6025221041 (label NRP, not NIM).
- Attachments: none (offer handout + PDF in-message)
- Evidence for factual claims:
  - "empat skenario dijalankan dan diulang, hasil konsisten": final bundle `results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5/` (p=0.0304) + replication bundles `2026-08-07_paired-h2_060200/` & `2026-08-07_paired-h2_104918/` (9/10 pairs, pooled p=0.003) — [../../results/claims/FINAL_NUMBERS.md](../../results/claims/FINAL_NUMBERS.md)
  - Correction 2026-09-10: the earlier note cited `2026-08-07_paired-h2_060200` and `2026-08-07_paired-h2_104918` (9/10 pairs, pooled p=0.003). Those two batches were deleted before commit and are excluded from the evidence record (thesis ch04 sec:replication). Retained replication is the 2026-08-08 batches (RUN1 p=0.436, RUN2 p=0.062, both S4-favorable) and the 2026-08-09 four-scenario replication (paired analysis p=0.032; per-scenario mean p99 S1 110.3, S2 79.7, S3 151.6, S4 99.1 ms). The sent message text above is unchanged history.
  - FRS blocked in My ITS Academica: user-reported (no repo evidence) — `unverified`
  - `progress-summary.md` finalized 2026-09-10; PDF `thesis-typst/build/thesis.pdf` (4.1 MB) present

### 2026-09-10 15:28–15:32 — reply received; FRS approved
- Direction: out and in
- Status: replied (FRS: actioned)
- Outcome: the adviser approved the FRS request the same day and redirected the work. First an Indonesian summary in a fixed structure, then a 6–7 page conference paper built from existing results.

Received (verbatim, 10/09/26):
> [15.28.05] Pak Royyana Muslim Ijtihadie, S.Kom.,M.Kom.,Ph.D.: ayaknya perlu segera dipercepat kalau sudah ada skenario
> [15.29.41] Pak Royyana Muslim Ijtihadie, S.Kom.,M.Kom.,Ph.D.: tolong dituliskan lagi
> • rumusan masalah apa saja
> • pembahasan metodologi yang disesuaikan rumusan masalah
> • pembahasan evaluasi dengan menyebutkan skenario skenario yang sudah didapatkan  (sesuaikan dengan metodologi)
> • kesimpulan (sesuaikan point-pointnya dengan rumusan masalah)
> • pakai bahasa indonesia saja
> [15.30.53] Pak Royyana Muslim Ijtihadie, S.Kom.,M.Kom.,Ph.D.: sekalian segera nulis publikasi dan cari  conference  di periode sebelum januari (6-7 halaman, gunakan skenario-2 yang sudah ada saja)
> [15.31.53] Pak Royyana Muslim Ijtihadie, S.Kom.,M.Kom.,Ph.D.: iya skenario-skenario yang sudah ada hasilnya, itu saja dijadikan publikasi
> [15.32.01] Pak Royyana Muslim Ijtihadie, S.Kom.,M.Kom.,Ph.D.: tidak perlu komplit ke thesis
> [15.32.38] Pak Royyana Muslim Ijtihadie, S.Kom.,M.Kom.,Ph.D.: yang penting
> • context jelas
> • why importance
> • rumusan masalah
> • metodologi
> • evaluasi
> • kesimpulan

Sent (verbatim, user's side, 10/09/26):
> [15.28.54] Muhammad Zahid Masruri: kalo berkenan apa boleh saya kirim seluruh bukunya pak ?
> [15.29.26] Muhammad Zahid Masruri: sementara masih dalam bahas inggris untuk penulisannya, atau bapak ada saran lebih bagus untuk nya
> [15.30.26] Muhammad Zahid Masruri: baik pak roy akan saya buatkan ringkasannya terlebih dahulu
> [15.31.29] Muhammad Zahid Masruri: untuk skenario 2 ini skenario hasil penelitian kah pak ?
> [15.32.01] Muhammad Zahid Masruri: ohh baik bapak

- English note: two directives. First, write the summary in Indonesian only, ordered as rumusan masalah, metodologi, evaluasi, kesimpulan. The evaluation section must name the scenarios that already have results, and the conclusion must answer each rumusan masalah point by point. Second, write the conference paper of 6–7 pages from existing results only. The paper does not need to cover the whole thesis, and its submission must fall before January. The adviser also asked for the paper to state the context and why the work matters.
- Language note: the thesis body is English. The adviser asked for Indonesian for the summary, so the summary is Indonesian and the paper language follows the chosen venue.
- Action items:
  - `ringkasan-penelitian.md` written 2026-09-10 (Indonesian, fixed structure) — owner: user, due: before the next bimbingan.
  - `PUB-001` redirected to a conference paper of 6–7 pages with submission before January 2027 — owner: user and adviser, due: venue chosen this week.
  - FRS: approved 2026-09-10 (user report) — `actioned`.
- Evidence: summary numbers come from [../../results/claims/FINAL_NUMBERS.md](../../results/claims/FINAL_NUMBERS.md). The FRS approval is user-reported and `unverified` in the repo.

---

*Conventions: append events, never rewrite. Statuses: pending → sent → replied → actioned. See [README.md](README.md).*
