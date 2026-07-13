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
#let nrp = "6025222041"
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
)

// English-first drafting: body in English, keep ITS Indonesian chrome (BAB etc)
#set text(lang: "en")

// Gate Indonesian citation rewrites (uncomment only for final Indonesian body pass)
// #show "et al.": "dkk"
// #show " & ": " dan "

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
  NRP: 6025222041
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
Arsitektur *cloud* modern menghadapi tantangan *trade-off* antara skalabilitas dan efisiensi biaya. *Kubernetes* menyediakan kontrol infrastruktur yang baik namun lambat merespons lonjakan lalu lintas, sementara komputasi *serverless* menawarkan elastisitas tinggi dengan biaya per-*request* yang lebih mahal. Penelitian ini merancang, mengimplementasikan, dan mengevaluasi arsitektur *hybrid* yang mengintegrasikan kluster *Kubernetes* dan *serverless* dengan prediksi beban kerja berbasis *Gated Recurrent Unit* (GRU) untuk distribusi lalu lintas yang proaktif.

Sistem yang diusulkan mengimplementasikan pengontrol routing V3 berbasis kapasitas (*capacity-driven*) yang menggeser lalu lintas secara dinamis antara *backend Kubernetes* dan *serverless* berdasarkan pemantauan *tail latency*. Mekanisme *proactive routing* menggunakan ekstrapolasi tren beban kerja aktual (5 langkah × 15 detik = 75 detik ke depan) yang dipicu oleh tingkat kepercayaan GRU. Evaluasi dilakukan melalui 30 eksperimen terkontrol yang direplikasi pada empat skenario: K8s+HPA (*baseline*), *Serverless*-only, *Hybrid-reactive*, dan *Hybrid-predictive*, dengan beban *trace* ClarkNet (40 tahap × 30 detik = 20 menit, RPS 22--164).

Hasil diagnostik n = 1 menunjukkan S4 (*Hybrid-predictive*) mencapai latensi p99 = 118,2 ms, penurunan 95,1% dibandingkan S1 (K8s-only) pada 2.421,3 ms. Pada perbandingan berpasangan S3/S4 yang berimbang (n = 5, perlakuan penuh), S4 menunjukkan rata-rata p99 128,5 ms vs 136,6 ms untuk S3 (selisih −8,1 ms, CI 95% [−36,7, +14,5] ms, p = 0,38). Arah efek berbalik menjadi menguntungkan S4 setelah perbaikan kalibrasi (*alpha* = 1/kapasitas-efektif), namun belum signifikan secara statistik. S4 juga menunjukkan 56% lebih sedikit pelanggaran SLO (Cohen's d = −0,54, efek sedang). H2 tidak didukung secara statistik namun arahnya konsisten dengan hipotesis. Model GRU mencapai RMSE 4,75% pada data sintetis; akurasi pada *trace* ClarkNet berada di bawah ambang batas target akibat non-stasioneritas beban kerja.

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
Modern cloud architecture faces a trade-off between scalability and cost efficiency. Kubernetes provides strong infrastructure control but is slow to respond to traffic spikes, while serverless computing offers high elasticity at a higher per-request cost. This research designs, implements, and evaluates a hybrid architecture integrating Kubernetes and serverless clusters with Gated Recurrent Unit (GRU)-based workload prediction for proactive traffic distribution.

The proposed system implements a V3 capacity-driven routing controller that dynamically shifts traffic between Kubernetes and serverless backends based on tail latency monitoring. The proactive routing mechanism uses actual workload trend extrapolation (5 steps × 15 seconds = 75 seconds ahead) gated by GRU confidence. Evaluation is conducted through 30 replicated controlled experiments across four scenarios: K8s+HPA (baseline), Serverless-only, Hybrid-reactive, and Hybrid-predictive, using the ClarkNet HTTP trace (40 stages × 30 seconds = 20 minutes, RPS 22--164).

Diagnostic n = 1 results show S4 (Hybrid-predictive) achieves p99 = 118.2 ms, a 95.1% reduction versus S1 (K8s-only) at 2,421.3 ms. In the counterbalanced S3/S4 paired comparison (n = 5, full treatment delivery), S4 shows mean p99 128.5 ms versus 136.6 ms for S3 (mean difference -8.1 ms, 95% CI [-36.7, +14.5] ms, p = 0.38). The effect direction reversed to S4's favor after the calibration repair (alpha = 1/effective-capacity), but is not statistically significant. S4 also shows 56% fewer SLO violations (Cohen's d = -0.54, medium effect). H2 is not statistically supported but the direction is consistent with the hypothesis. The GRU model achieves 4.75% RMSE on synthetic data; real-trace accuracy falls below the 10% target due to workload non-stationarity.

#v(1em)
#par(first-line-indent: 0pt)[
  #text(weight: "bold")[Keywords:] Cloud Computing, Kubernetes, Serverless, Workload Prediction, GRU, Traffic Distribution, Hybrid Architecture.
]

#pagebreak()

//=============================================================================
// 5. TABLE OF CONTENTS
//=============================================================================

#outline(
  title: [#align(center, text(size: 14pt, weight: "bold")[#upper("DAFTAR ISI")])],
  indent: auto,
  depth: 3,
)

#pagebreak()

//=============================================================================
// 6. LIST OF TABLES
//=============================================================================

#outline(
  title: [#align(center, text(size: 14pt, weight: "bold")[#upper("DAFTAR TABEL")])],
  target: figure.where(kind: table),
)

#pagebreak()

//=============================================================================
// 7. LIST OF FIGURES
//=============================================================================

#outline(
  title: [#align(center, text(size: 14pt, weight: "bold")[#upper("DAFTAR GAMBAR")])],
  target: figure.where(kind: image),
)

#pagebreak()

#include "content/ch01-introduction.typ"
#include "content/ch02-literature.typ"
#include "content/ch03-methodology.typ"
#include "content/ch04-results.typ"
#include "content/ch05-conclusion.typ"

//=============================================================================
// BIBLIOGRAPHY
//=============================================================================

#set heading(numbering: none)

= DAFTAR PUSTAKA
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
