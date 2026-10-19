//=============================================================================
// ITS Informatics Department Thesis (Typst)
//
// This is your main entry point. Edit the content below and
// customize the configuration variables at the top of this file
// for your thesis metadata.
//
// Department of Informatics
// Faculty of Intelligent Electrical and Informatics Technology
// Institut Teknologi Sepuluh Nopember (ITS)
// Surabaya, Indonesia
//=============================================================================

//=============================================================================
// THESIS CONFIGURATION
// Edit the variables below to customize your thesis metadata.
// All variables are available directly (without prefix) throughout
// this file and are also passed to the template as named arguments.
//=============================================================================

// --- Author Information ---
#let author = "Muhammad Zahid Masruri"
#let nrp = "6025221041"
#let sign = "resources/fake-sign.svg"  // replace when real signature available

// --- Supervisor Information ---
#let supervisors = (
  (name: "Prof. Tohari Ahmad, S.Kom., M.IT., Ph.D.", nip: "197708242006041001", sign: "resources/fake-sign.svg"),
  (name: "Royyana Muslim Ijtihadie, S.Kom., M.Kom., Ph.D.", nip: "197505252003121002", sign: "resources/fake-sign.svg"),
)

// --- Examiner Information ---
#let examiners = (
  (name: "Dosen Penguji ke-1 (Lengkap)", nip: "20xxxxxxxx", sign: "resources/fake-sign.svg"),
  (name: "Dosen Penguji ke-2 (Lengkap)", nip: "20xxxxxxxx", sign: "resources/fake-sign.svg"),
  (name: "Dosen Penguji ke-3 (Lengkap)", nip: "20xxxxxxxx", sign: "resources/fake-sign.svg"),
)

// --- Head of Department ---
#let chief = (name: "Kepala Departemen Informatika", nip: "20xxxxxxxx", sign: "resources/fake-sign.svg")

// --- Dates ---
#let dates = (
  writing: "27 Juni 2024",
  exam: (day: "Rabu", date: "10 Juli 2024", place: "Ruang 217B"),
  graduationPeriod: "September 2024",
)

// --- Academic Program ---
#let program = (
  type: "Program Magister",
  title: "Magister Komputer (M.Kom.)",
  concentration: "Teknik Informatika",
  courseClass: "Teknologi Jaringan dan Keamanan Siber Cerdas",
  courseClassShort: "NETICS",
  degree: "S2",
  department: "Departemen Teknik Informatika",
  faculty: "Fakultas Teknologi Elektro dan Informatika Cerdas",
  university: "Institut Teknologi Sepuluh Nopember",
  city: "Surabaya",
  year: 2026,
)

// --- Essay Code ---
#let essay = "Tesis Sidang Akhir - EF235401"

// --- Thesis Titles ---
#let title = (
  id: "Pengambilan Keputusan dan Pengaturan Skalabilitas Elastis pada Lingkungan Cloud yang Heterogen dengan Berbasiskan pada Prediksi Workload",
  en: "Decision Making and Elastic Scalability Management in Heterogeneous Cloud Environments Based on Workload Prediction",
)

// --- Resource Paths (relative to src/) ---
#let paths = (
  logo: "resources/its-logo.png",
  coverBackground: "resources/its-thesis-cover-without-logo.svg",
  coverBackgroundSecondary: "resources/its-thesis-cover-without-logo-2.svg",
  validationBackground: "resources/its-thesis-validation.png",
  bibliography: "bibliography.bib",
)

// HELPER
#let tab-to(target-width, body) = context {
  let current-width = measure(body).width
  if current-width < target-width {
    h(target-width - current-width)
  } else {
    h(0pt)
  }
}

//=============================================================================
// TEMPLATE SETUP
// Each config variable is passed directly as a named argument to the
// template — no `cfg` wrapper needed. Use them directly in your content.
//=============================================================================

#import "template.typ": thesis
#import "content/headings.typ": H

// ---------------------------------------------------------------------------
// LANGUAGE MODE / EDITION SWITCH
// Canonical edition is the English body (default, no input flag needed).
// Compile the Indonesian edition with:
//     typst compile --input lang=id src/thesis.typ build/thesis-id.pdf
//   or: make master-id
// Structural headings flip with the edition (CHAPTER I INTRODUCTION vs
// BAB I PENDAHULUAN) via content/headings.typ. Always rendered in BOTH
// editions: the administrative chrome (cover, approval, KATA PENGANTAR)
// and the dual abstracts (ABSTRAK id + ABSTRACT en).
// text(lang:, region:) drives hyphenation, smart quotes, figure supplement
// localization (when supplement: auto), and the CSL bibliography locale:
// with lang "id"/"ID", Typst 0.13's hayagriva uses locales-id-ID for APA
// terms (et al. -> dkk., and -> dan, in -> dalam).
// ---------------------------------------------------------------------------
#let edition = sys.inputs.at("lang", default: "en")
#let body-lang = if edition == "id" { "id" } else { "en" }
#let body-region = if body-lang == "id" { "ID" } else { none }

#show: thesis.with(
  author: author,
  nrp: nrp,
  sign: sign,
  supervisors: supervisors,
  examiners: examiners,
  chief: chief,
  dates: dates,
  program: program,
  essay: essay,
  title: title,
  paths: paths,
  proposal: false, // full thesis (not proposal)
  edition: edition,
)

#set text(lang: body-lang, region: body-region)

// Fallback for any residual English citation tokens the CSL locale misses.
// Inert in the English edition.
#show: body => {
  if body-lang == "id" {
    show "et al.": "dkk."
    body
  } else {
    body
  }
}

//=============================================================================
// 1. DEDICATION
//=============================================================================

#v(1fr)
#align(center)[
  Karya ini kupersembahkan kepada: \
  istriku tercinta, anak-anakku tersayang, dan kedua orang tuaku yang selalu mendukungku dan mendoakanku.
]
#v(1fr)

#pagebreak()

//=============================================================================
// 2. FOREWORD  (Kata Pengantar)
//=============================================================================

// Typst 0.13+ removed par(indent: ...)
// Use explicit first-line indentation if needed: #indent[content]

#align(center, text(size: 13pt, weight: "bold")[#upper("KATA PENGANTAR")])

#v(1.5em)

Puji syukur penulis panjatkan ke hadirat Allah SWT yang telah memberikan rahmat serta kemudahan sehingga peneliti dapat menyelesaikan penelitian tesis dengan judul "Pengambilan Keputusan dan Pengaturan Skalabilitas Elastis pada Lingkungan Cloud yang Heterogen dengan Berbasiskan pada Prediksi Workload" ini dapat terselesaikan.

Peneliti menyadari bahwa tesis ini tidak akan berhasil tanpa adanya bantuan dari beberapa pihak. Oleh karena itu, penulis ingin mengucapkan terima kasih kepada:

+ Bapak Prof. Tohari Ahmad, S.Kom., M.IT., Ph.D. selaku dosen pembimbing tesis 1 yang telah sabar dalam membimbing dan mengarahkan peneliti sehingga dapat menyelesaikan tesis ini.
+ Bapak Royyana Muslim Ijtihadie, S.Kom., M.Kom., Ph.D. selaku dosen pembimbing tesis 2 yang telah sabar dalam membimbing dan mengarahkan peneliti sehingga dapat menyelesaikan tesis ini.
+ Orang tua dari peneliti yang telah memberikan dukungan, nasihat, kasih sayang, dan perhatian dalam mendidik dan membantu penulis, sehingga dapat menyelesaikan tesis ini.
+ Semua pihak lainnya yang secara langsung maupun tidak langsung dalam membantu peneliti menyelesaikan tesis ini.

Peneliti menyadari bahwa dalam penyusunan laporan tesis ini masih terdapat banyak kekurangan, sehingga kritik dan saran sangat diharapkan. Akhir kata peneliti berharap tesis ini dapat membawa manfaat bagi semua pihak yang menggunakannya.

#v(2em)
#align(right)[
  Surabaya, Juli 2026 \
  \
  \
  \
  Muhammad Zahid Masruri \
  NRP: 6025221041
]

#pagebreak()

//=============================================================================
// 3. INDONESIAN ABSTRACT  (Abstrak)
//=============================================================================

// Typst 0.13+ doesn't support par(indent: ...)
// For abstracts, we can leave paragraphs without indent or use #par.leading

#align(center, text(size: 12pt, weight: "bold")[
  #upper(title.id)
])

#v(1em)
#par(first-line-indent: 0pt)[
  Nama Mahasiswa#tab-to(3.5cm, [Nama Mahasiswa]): #author \
  NRP#tab-to(3.5cm, [NRP]): #nrp \
  Pembimbing 1#tab-to(3.5cm, [Pembimbing 1]): #supervisors.at(0).name \
  Pembimbing 2#tab-to(3.5cm, [Pembimbing 2]): #supervisors.at(1).name
]

#v(2em)
#align(center, text(size: 13pt, weight: "bold")[#upper("ABSTRAK")])

#v(1em)
Arsitektur *cloud* modern harus menjaga latensi rendah dengan biaya terkendali. *Kubernetes* memberi kontrol yang stabil tetapi lambat merespons lonjakan lalu lintas. Komputasi *serverless* menskala dengan cepat tetapi lebih mahal per *request*. Penelitian ini membangun dan mengevaluasi arsitektur *hybrid* dari keduanya, dengan prakiraan GRU (*gated recurrent unit*) sebagai masukan penskalaan replika Kubernetes.

Sistem mengalihkan lalu lintas dari *Kubernetes* ke *serverless* ketika beban teramati melebihi kapasitas replika Kubernetes yang siap. Prakiraan GRU merencanakan replika Kubernetes melalui Algoritma 2. Algoritma 1 merutekan berdasarkan beban saat ini dan kapasitas replika yang siap, tanpa membaca prakiraan. Pengujian memasangkan kontrol reaktif dan prediktif dalam empat batch (5, 5, 10, dan 10 pasang; tiga terakhir memakai prediktor ClarkNet) pada beban *trace* ClarkNet, ditambah uji tunggal empat skenario dan uji mekanisme bertahap. Beban *replay* terdiri dari 40 tahap × 30 detik = 20 menit dengan RPS (*requests per second*) 22--164.

Untuk beban ClarkNet, tidak ada pemenang yang jelas. Semua batch yang dapat diatribusikan ke ClarkNet menunjukkan hasil yang sama: selisihnya masih dalam batas kebetulan (+153,3 ms p = 0,656, n = 5; -104,2 ms p = 0,168, n = 10; -13,6 ms p = 0,307, d = -0,16, n = 10 pada ulangan dengan beban *host* tercatat per *run*). Dalam 25 pasang, S4 lebih cepat 16,5 ms secara rata-rata. Rentang kepercayaan 95% untuk selisih rata-rata adalah dari 188,6 ms lebih cepat sampai 184,5 ms lebih lambat ([-188,6, +184,5] ms, p satu sisi = 0,448), sehingga data tidak menunjukkan keunggulan prediksi. Batch Juli dilaporkan sebagai sejarah. Pada n = 5 dengan beban ClarkNet yang naik turun, S4 mencapai rata-rata p99 (persentil ke-99) 126,0 ms vs 188,5 ms untuk S3 (selisih -62,5 ms, CI 95% [-100,9, -26,2] ms, p = 0,0312, Cohen's d = -1,26). Nilai p tersebut adalah nilai terkecil yang mungkin pada n = 5 (1/32), karena kelima pasangan jatuh searah. S4 juga menunjukkan 80,2% lebih sedikit pelanggaran SLO (*service level objective*) (130 vs 656) dengan biaya bulanan yang identik. Setiap *run* S4 memuat 4-5 label PREDICTIVE; label ini berasal dari tren beban teramati, bukan dari prakiraan GRU. Ukuran sekunder seperti p95 tidak signifikan setelah koreksi (p terkoreksi = 0,1248). *Manifest* batch itu tidak mencatat prediktor; artefak yang terpasang pada periode itu adalah model yang dilatih dengan data sintetis, sehingga batch ini tidak dapat diatribusikan ke prediktor ClarkNet. Model GRU mencapai RMSE 5,2% pada data sintetis. Akurasi pada *trace* ClarkNet berada di bawah target karena beban kerja tidak stasioner.

#v(1em)
#par(first-line-indent: 0pt)[
  #text(weight: "bold")[Kata Kunci:] Cloud Computing, Kubernetes, Serverless, Prediksi Beban Kerja, GRU, Distribusi Lalu Lintas, Arsitektur Hybrid.
]

#pagebreak()

//=============================================================================
// 4. ENGLISH ABSTRACT
//=============================================================================

#align(center, text(size: 12pt, weight: "bold")[
  #upper(title.en)
])

#v(1em)
#par(first-line-indent: 0pt)[
  Name#tab-to(4.3cm, [Name]): #author \
  Student Identity Number#tab-to(4.3cm, [Student Identity Number]): #nrp \
  Supervisor 1#tab-to(4.3cm, [Supervisor 1]): #supervisors.at(0).name \
  Supervisor 2#tab-to(4.3cm, [Supervisor 2]): #supervisors.at(1).name
]

#v(2em)
#align(center, text(size: 13pt, weight: "bold")[#upper("ABSTRACT")])

#v(1em)
Modern cloud systems must keep tail latency low at controlled cost. Kubernetes offers stable control but responds slowly to traffic surges. Serverless scales quickly but costs more per request. This thesis builds and evaluates a hybrid of the two in which a GRU (gated recurrent unit) forecast informs Kubernetes replica scaling.

The system shifts traffic from Kubernetes to serverless when observed load exceeds the capacity of the ready Kubernetes replicas. The forecast plans Kubernetes replicas in Algorithm 2. Algorithm 1 routes by current load and ready capacity and does not read the forecast. Tests pair reactive and predictive control in four batches on ClarkNet traffic (5, 5, 10 and 10 pairs; the last three use the ClarkNet-trained predictor), plus a single-run comparison of four scenarios and staged mechanism checks. The replay runs 40 stages × 30 seconds = 20 minutes, with RPS (requests per second) 22--164.

On ClarkNet load, there is no clear winner. Every ClarkNet-attributable batch tells the same story: the difference is within chance (+153.3 ms p = 0.656, n = 5; -104.2 ms p = 0.168, n = 10; -13.6 ms p = 0.307, d = -0.16, n = 10 on a repeat with host load recorded per run). Across 25 pairs, S4 ran 16.5 ms faster on average. The 95% confidence interval of the mean difference runs from 188.6 ms faster to 184.5 ms slower ([-188.6, +184.5] ms, one-sided p = 0.448), so the data show no advantage for prediction. The July batch is reported as history. At n = 5 with rolling ClarkNet load, S4 reaches mean p99 (99th percentile) 126.0 ms versus 188.5 ms for S3 (mean difference -62.5 ms, 95% CI [-100.9, -26.2] ms, p = 0.0312, Cohen's d = -1.26). That p is the smallest value possible at n = 5 (1/32), because all five pairs fell the same way. S4 also shows 80.2% fewer SLO (service level objective) violations (130 vs 656) at identical monthly cost. Each S4 run carried 4-5 PREDICTIVE labels; these came from the observed-load trend, not from the GRU forecast. Secondary measures such as p95 are not significant after correction (corrected p = 0.1248). The batch manifest records no predictor; the artifact deployed in that period was the synthetic-trained model, so the batch cannot be attributed to the ClarkNet predictor. The GRU model reaches 5.2% RMSE on synthetic data. On the ClarkNet trace, accuracy falls below target because the load is non-stationary.

#v(1em)
#par(first-line-indent: 0pt)[
  #text(weight: "bold")[Keywords:] Cloud Computing, Kubernetes, Serverless, Workload Prediction, GRU, Traffic Distribution, Hybrid Architecture.
]

#pagebreak()

//=============================================================================
// 5. TABLE OF CONTENTS
//=============================================================================

#outline(
  title: [#align(center, text(size: 14pt, weight: "bold")[#upper(H("toc"))])],
  indent: auto,
  depth: 3,
)

#pagebreak()

//=============================================================================
// 6. LIST OF TABLES
//=============================================================================

#outline(
  title: [#align(center, text(size: 14pt, weight: "bold")[#upper(H("lot"))])],
  target: figure.where(kind: table),
)

#pagebreak()

//=============================================================================
// 7. LIST OF FIGURES
//=============================================================================

#outline(
  title: [#align(center, text(size: 14pt, weight: "bold")[#upper(H("lof"))])],
  target: figure.where(kind: image),
)

#pagebreak()

#counter(page).update(1)
#set page(numbering: "1")

#include "content/ch01-introduction.typ"
#include "content/ch02-literature.typ"
#include "content/ch03-methodology.typ"
#include "content/ch04-results.typ"
#include "content/ch05-conclusion.typ"

//=============================================================================
// BIBLIOGRAPHY
//=============================================================================

#set heading(numbering: none)

= #H("bib")
#bibliography(
  "bibliography.bib",
  title: none,
  style: "apa",
  full: false,
)

#pagebreak()

//=============================================================================
// APPENDICES
//=============================================================================

#include "content/appendices.typ"

#pagebreak()

//=============================================================================
// BIOGRAPHY
//=============================================================================

#set heading(numbering: none)
#include "content/biography.typ"
