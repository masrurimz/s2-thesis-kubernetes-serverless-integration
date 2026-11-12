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
// The body is one file per chapter and edition: content/<name>.typ is the
// English text and content/<name>.id.typ its Indonesian translation. Headings
// flip through content/headings.typ. `make check-id` fails when a translation
// drops a citation, label, figure, table or number of its English source.
// Always rendered in BOTH editions: the administrative chrome (cover,
// approval, KATA PENGANTAR) and the dual abstracts (ABSTRAK id + ABSTRACT en).
// text(lang:, region:) drives hyphenation, smart quotes, figure supplement
// localization (when supplement: auto), and the CSL bibliography locale:
// with lang "id"/"ID", Typst 0.13's hayagriva uses locales-id-ID for APA
// terms (et al. -> dkk., and -> dan, in -> dalam).
// ---------------------------------------------------------------------------
#let edition = sys.inputs.at("lang", default: "en")
#let body-lang = if edition == "id" { "id" } else { "en" }
#let body-region = if body-lang == "id" { "ID" } else { none }
#let chapter(name) = "content/" + name + (if edition == "id" { ".id" } else { "" }) + ".typ"

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

Puji syukur penulis panjatkan ke hadirat Allah SWT atas rahmat dan kemudahan yang diberikan, sehingga penulis dapat menyelesaikan penelitian tesis berjudul "Pengambilan Keputusan dan Pengaturan Skalabilitas Elastis pada Lingkungan Cloud yang Heterogen dengan Berbasiskan pada Prediksi Workload".

Penulis menyadari bahwa tesis ini tidak akan selesai tanpa bantuan banyak pihak. Oleh karena itu, penulis mengucapkan terima kasih kepada:

+ Bapak Prof. Tohari Ahmad, S.Kom., M.IT., Ph.D. selaku dosen pembimbing tesis 1, yang dengan sabar membimbing dan mengarahkan penulis sampai tesis ini selesai.
+ Bapak Royyana Muslim Ijtihadie, S.Kom., M.Kom., Ph.D. selaku dosen pembimbing tesis 2, yang dengan sabar membimbing dan mengarahkan penulis sampai tesis ini selesai.
+ Orang tua penulis, yang telah memberikan dukungan, nasihat, kasih sayang, dan perhatian dalam mendidik dan membantu penulis sampai tesis ini selesai.
+ Semua pihak lain yang secara langsung maupun tidak langsung membantu penulis menyelesaikan tesis ini.

Penulis menyadari bahwa laporan tesis ini masih memiliki banyak kekurangan, sehingga penulis mengharapkan kritik dan saran. Akhir kata, penulis berharap tesis ini bermanfaat bagi semua pihak yang menggunakannya.

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
Sistem _cloud_ modern harus menjaga _tail latency_ tetap rendah dengan biaya terkendali. Kubernetes memberi kontrol yang stabil, tetapi lambat merespons lonjakan lalu lintas. Komputasi _serverless_ menskalakan dengan cepat, tetapi biayanya lebih mahal per _request_. Tesis ini membangun dan mengevaluasi arsitektur _hybrid_ dari keduanya. Dalam arsitektur itu, prakiraan GRU (_gated recurrent unit_) menjadi masukan bagi penskalaan replika Kubernetes.

Sistem mengalihkan lalu lintas dari Kubernetes ke _serverless_ ketika beban teramati melebihi kapasitas replika Kubernetes yang siap. Prakiraan GRU merencanakan replika Kubernetes dalam Algoritma 2. Algoritma 1 merutekan lalu lintas berdasarkan beban saat ini dan kapasitas replika yang siap, tanpa membaca prakiraan. Pengujian utama adalah satu _batch_ pra-registrasi berisi 10 pasang kontrol reaktif dan prediktif pada lalu lintas ClarkNet, dengan prediktor yang dilatih dengan ClarkNet. _Batch_ sebelumnya dilaporkan sebagai sejarah. Pengujian juga mencakup perbandingan empat skenario dengan satu _run_ per skenario dan pemeriksaan mekanisme bertahap. Beban _replay_ terdiri dari 40 tahap × 30 detik = 20 menit, dengan RPS (_requests per second_) 22 sampai 164.

Pada beban ClarkNet, prediksi tidak memberi keuntungan yang jelas. Pada _batch_ pra-registrasi, S4 mencapai rata-rata p99 (persentil ke-99) 146,8 ms, sedangkan S3 mencapai 160,4 ms (selisih rata-rata -13,6 ms, rentang kepercayaan 95% [-63,5; +35,6] ms, p = 0,307, Cohen's d = -0,16). S4 menang pada 5 dari 10 pasangan. Latensi p95 dan pelanggaran SLO (_service level objective_) juga tidak berbeda. Pada seluruh 25 pasangan yang memakai prediktor ClarkNet, S4 rata-rata 16,5 ms lebih cepat. Rentang kepercayaan 95%-nya berkisar dari 188,6 ms lebih cepat sampai 184,5 ms lebih lambat (p satu sisi = 0,448). _Batch_ Juli sebelumnya mencapai p = 0,0312, tetapi manifesnya tidak mencatat prediktor, sehingga _batch_ itu dilaporkan sebagai sejarah. Model GRU mencapai RMSE 5,2% pada data sintetis. Pada _trace_ ClarkNet, akurasinya di bawah target karena beban tidak stasioner.

#v(1em)
#par(first-line-indent: 0pt)[
  #text(weight: "bold")[Kata Kunci:] Komputasi Awan, Kubernetes, _Serverless_, Prediksi Beban Kerja, GRU, Distribusi Lalu Lintas, Arsitektur _Hybrid_.
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

The system shifts traffic from Kubernetes to serverless when observed load exceeds the capacity of the ready Kubernetes replicas. The forecast plans Kubernetes replicas in Algorithm 2. Algorithm 1 routes by current load and ready capacity and does not read the forecast. The main test is a pre-registered batch of 10 counterbalanced pairs of reactive and predictive control on ClarkNet traffic, using the ClarkNet-trained predictor; earlier batches are reported as history. The evaluation also includes a single-run comparison of four scenarios and staged mechanism checks. The replay runs 40 stages × 30 seconds = 20 minutes, with RPS (requests per second) 22--164.

On ClarkNet load, prediction gave no clear gain. In the pre-registered batch, S4 reached mean p99 (99th percentile) 146.8 ms versus 160.4 ms for S3 (mean difference -13.6 ms, 95% CI [-63.5, +35.6] ms, p = 0.307, Cohen's d = -0.16). S4 won 5 of 10 pairs, and p95 latency and SLO (service level objective) violations did not differ. Across all 25 pairs that ran the ClarkNet-trained predictor, S4 ran 16.5 ms faster on average, with a 95% interval from 188.6 ms faster to 184.5 ms slower (one-sided p = 0.448). An earlier July batch reached p = 0.0312, but its manifest records no predictor, so it is reported as history. The GRU model reaches 5.2% RMSE on synthetic data. On the ClarkNet trace, accuracy falls below target because the load is non-stationary.

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

#include chapter("ch01-introduction")
#include chapter("ch02-literature")
#include chapter("ch03-methodology")
#include chapter("ch04-results")
#include chapter("ch05-conclusion")

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

#include chapter("appendices")

#pagebreak()

//=============================================================================
// BIOGRAPHY
//=============================================================================

#set heading(numbering: none)
#include "content/biography.typ"
