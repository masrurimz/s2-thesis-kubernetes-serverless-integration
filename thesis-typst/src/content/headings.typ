// ============================================================================
// Edition-aware structural headings
//
// The thesis compiles in two editions (see thesis.typ LANGUAGE MODE):
//   default        -> English headings (CHAPTER I INTRODUCTION, ...)
//   --input lang=id -> Indonesian headings (BAB I PENDAHULUAN, ...)
//
// Usage at call sites:
//   #import "headings.typ": H
//   = #H("ch1")
//   == #H("ch1-problem")
//
// Always-dual sections (ABSTRAK id + ABSTRACT en) are NOT keyed here; they
// render in both languages in both editions by design.
// ============================================================================

#let _edition = sys.inputs.at("lang", default: "en")
#let _en = _edition != "id"

#let _headings = if _en {
  (
    // Outline / back-matter titles
    toc: "TABLE OF CONTENTS",
    lot: "LIST OF TABLES",
    lof: "LIST OF FIGURES",
    bib: "BIBLIOGRAPHY",

    // Chapter 1
    ch1: "INTRODUCTION",
    "ch1-problem": "Problem Formulation",
    "ch1-hypotheses": "Hypotheses",
    "ch1-objectives": "Research Objectives",
    "ch1-benefits": "Research Benefits",
    "ch1-contribution": "Research Contribution",
    "ch1-constraints": "Problem Constraints",
    "ch1-systematics": "Writing Systematics",

    // Chapter 2
    ch2: "LITERATURE REVIEW",
    "ch2-cloud": "Cloud Computing",
    "ch2-containers": "Containers and Kubernetes",
    "ch2-serverless": "Serverless Computing and Cold Start",
    "ch2-integration": "Kubernetes-Serverless Integration",
    "ch2-metrics": "Cloud Application Performance Metrics",
    "ch2-prediction": "Workload Prediction with Recurrent Neural Networks",
    "ch2-elax": "Kubernetes Scaling and the ElaX Algorithm",

    // Chapter 3
    ch3: "METHODOLOGY",
    "ch3-flow": "Research Flow",
    "ch3-data": "Data Collection",
    "ch3-training": "Training Data",
    "ch3-replay": "Replay Load (Sampling the Real Traces)",
    "ch3-arch": "System Architecture",
    "ch3-infra": "Infrastructure Components",
    "ch3-monitoring": "Monitoring and Metrics Collection",
    "ch3-impl": "Implementation",
    "ch3-predictor": "Workload Predictor (GRU Architecture)",
    "ch3-alloc": "Resource Allocation Model",
    "ch3-algo1": "Algorithm 1: Routing Controller",
    "ch3-algo2": "Algorithm 2: Cluster Controller",
    "ch3-consolidation": "Node-Level Consolidation",
    "ch3-evalplan": "Evaluation Plan",
    "ch3-scenarios": "Evaluation Scenarios",
    "ch3-phases": "Evaluation Phases",
    "ch3-metrics": "Metrics",
    "ch3-stats": "Statistical Analysis Protocol",
    "ch3-threats": "Threats to Validity",

    // Chapter 4
    ch4: "RESULTS AND DISCUSSION",
    "ch4-gru": "GRU Prediction Model Performance",
    "ch4-phasea1": "System Mechanism Validation (Phase A1)",
    "ch4-comparative": "Comparative Evaluation",
    "ch4-h2-initial": "Predictive versus Reactive (H2, Initial Result, Superseded)",
    "ch4-calibration": "Calibration Repair and Effect Reversal",
    "ch4-h2-definitive": "Definitive Paired H2 Result (n = 5, Tuned, Variable Load)",
    "ch4-replication": "Independent Replication (2026-08-07)",
    "ch4-s4vs1": "Hybrid versus Pure Kubernetes (S4 vs S1)",
    "ch4-cost": "Cost Analysis",
    "ch4-node": "Dynamic Node Provisioning and Serverless Offload",
    "ch4-varload": "Variable-Load Validation (ClarkNet, All Tiers Exercised)",
    "ch4-consol": "Node Consolidation (Utilization-Based Scale-Down)",
    "ch4-hpo": "Controller HPO and Holdout Validation",
    "ch4-discussion": "Discussion",

    // Chapter 5
    ch5: "CONCLUSION AND SUGGESTIONS",
    "ch5-conclusion": "Conclusion",
    "ch5-rq1": "RQ1: GRU-Based Workload Prediction",
    "ch5-rq2": "RQ2: Modified ElaX Decision Making",
    "ch5-rq3": "RQ3: Evaluation of the Modified ElaX Mechanism",
    "ch5-future": "Future Work",

    // Appendices
    "app-a": "APPENDIX A: Experiment Configuration",
    "app-a-calib": "Calibration Parameters",
    "app-a-alloc": "Cluster Resource Allocation",
    "app-a-trace": "ClarkNet Trace Parameters",
    "app-b": "APPENDIX B: Raw Experiment Results",
    "app-b-pairs": "Definitive Per-Pair Results (n=5)",
    "app-b-stats": "Definitive Statistical Test Summary",
    "app-c": "APPENDIX C: Code Listings",
    "app-c-signal": "Forecast-Gated Capacity Signal (V3 Controller)",
    "app-c-capacity": "Effective K8s Capacity",
    "app-c-config": "CalibrationConfig",
    "app-d": "APPENDIX D: Raw Replication Data",
    "app-d-raw": "Raw Replication Data n=5",
    "app-d-summary": "Per-Scenario Summary n=5",
    "app-d-stats": "Statistical Comparison n=5",

    // Biography
    biography: "AUTHOR BIOGRAPHY",
  )
} else {
  (
    toc: "DAFTAR ISI",
    lot: "DAFTAR TABEL",
    lof: "DAFTAR GAMBAR",
    bib: "DAFTAR PUSTAKA",

    ch1: "PENDAHULUAN",
    "ch1-problem": "Rumusan Masalah",
    "ch1-hypotheses": "Hipotesis",
    "ch1-objectives": "Tujuan Penelitian",
    "ch1-benefits": "Manfaat Penelitian",
    "ch1-contribution": "Kontribusi Penelitian",
    "ch1-constraints": "Batasan Masalah",
    "ch1-systematics": "Sistematika Penulisan",

    ch2: "TINJAUAN PUSTAKA",
    "ch2-cloud": "Komputasi Awan",
    "ch2-containers": "Kontainer dan Kubernetes",
    "ch2-serverless": "Komputasi _Serverless_ dan _Cold Start_",
    "ch2-integration": "Integrasi Kubernetes-_Serverless_",
    "ch2-metrics": "Metrik Kinerja Aplikasi _Cloud_",
    "ch2-prediction": "Prediksi Beban Kerja dengan _Recurrent Neural Network_",
    "ch2-elax": "Pen-skalaan Kubernetes dan Algoritma ElaX",

    ch3: "METODOLOGI PENELITIAN",
    "ch3-flow": "Alur Penelitian",
    "ch3-data": "Pengumpulan Data",
    "ch3-training": "Data Pelatihan",
    "ch3-replay": "Beban _Replay_ (Sampling _Trace_ Nyata)",
    "ch3-arch": "Arsitektur Sistem",
    "ch3-infra": "Komponen Infrastruktur",
    "ch3-monitoring": "Pemantauan dan Pengumpulan Metrik",
    "ch3-impl": "Implementasi",
    "ch3-predictor": "Prediktor Beban Kerja (Arsitektur GRU)",
    "ch3-alloc": "Model Alokasi Sumber Daya",
    "ch3-algo1": "Algoritma 1: Kontroler _Routing_",
    "ch3-algo2": "Algoritma 2: Kontroler Kluster",
    "ch3-consolidation": "Konsolidasi Level _Node_",
    "ch3-evalplan": "Rencana Evaluasi",
    "ch3-scenarios": "Skenario Evaluasi",
    "ch3-phases": "Tahap Evaluasi",
    "ch3-metrics": "Metrik",
    "ch3-stats": "Protokol Analisis Statistik",
    "ch3-threats": "Ancaman terhadap Validitas",

    ch4: "HASIL DAN PEMBAHASAN",
    "ch4-gru": "Kinerja Model Prediksi GRU",
    "ch4-phasea1": "Validasi Mekanisme Sistem (Phase A1)",
    "ch4-comparative": "Evaluasi Komparatif",
    "ch4-h2-initial": "Prediktif versus Reaktif (H2, Hasil Awal, Digantikan)",
    "ch4-calibration": "Perbaikan Kalibrasi dan Pembalikan Efek",
    "ch4-h2-definitive": "Hasil H2 Berpasangan Definitif (n = 5, _Tuned_, Beban Variabel)",
    "ch4-replication": "Replikasi Independen (2026-08-07)",
    "ch4-s4vs1": "_Hybrid_ versus Kubernetes Murni (S4 vs S1)",
    "ch4-cost": "Analisis Biaya",
    "ch4-node": "_Provisioning Node_ Dinamis dan _Offload Serverless_",
    "ch4-varload": "Validasi Beban Variabel (ClarkNet, Semua _Tier_ Diuji)",
    "ch4-consol": "Konsolidasi _Node_ (_Scale-Down_ Berbasis Utilisasi)",
    "ch4-hpo": "HPO Kontroler dan Validasi _Holdout_",
    "ch4-discussion": "Diskusi",

    ch5: "KESIMPULAN DAN SARAN",
    "ch5-conclusion": "Kesimpulan",
    "ch5-rq1": "RQ1: Prediksi Beban Kerja Berbasis GRU",
    "ch5-rq2": "RQ2: Pengambilan Keputusan ElaX yang Dimodifikasi",
    "ch5-rq3": "RQ3: Evaluasi Mekanisme ElaX yang Dimodifikasi",
    "ch5-future": "Saran",

    "app-a": "LAMPIRAN A: Konfigurasi Eksperimen",
    "app-a-calib": "Parameter Kalibrasi",
    "app-a-alloc": "Alokasi Sumber Daya Kluster",
    "app-a-trace": "Parameter _Trace_ ClarkNet",
    "app-b": "LAMPIRAN B: Hasil Eksperimen Mentah",
    "app-b-pairs": "Hasil Per-Pasangan Definitif (n=5)",
    "app-b-stats": "Ringkasan Uji Statistik Definitif",
    "app-c": "LAMPIRAN C: Daftar Kode",
    "app-c-signal": "Sinyal Kapasitas Berbasis Prakiraan (Kontroler V3)",
    "app-c-capacity": "Kapasitas Efektif K8s",
    "app-c-config": "CalibrationConfig",
    "app-d": "LAMPIRAN D: Data Mentah Replikasi",
    "app-d-raw": "Data Mentah Replikasi n=5",
    "app-d-summary": "Ringkasan Per-Skenario n=5",
    "app-d-stats": "Perbandingan Statistik n=5",

    biography: "BIOGRAFI PENULIS",
  )
}

// Lookup. Fails loudly on an unknown key so a typo cannot silently
// drop a heading from the book.
#let H(key) = _headings.at(key)

// Bilingual caption / label text. Picks the active edition's variant.
// Usage (code position, e.g. figure named args): caption: cap([English caption], [Takarir Indonesia])
#let cap(en, id) = if _en { en } else { id }
