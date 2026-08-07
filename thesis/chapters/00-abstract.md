# Abstrak

Pertumbuhan layanan cloud computing mendorong kebutuhan akan arsitektur yang mampu menangani beban kerja dinamis secara efisien. Penelitian ini merancang arsitektur hybrid dua-kluster yang mengintegrasikan Kubernetes dan serverless computing dengan prediksi beban kerja berbasis GRU. Dalam implementasi final, prediksi digunakan untuk scaling replika Kubernetes (Algorithm 2), sedangkan routing merespons beban teramati dan kapasitas ekor latensi (V3).

Evaluasi definitif H2 menggunakan 5 pasangan counterbalanced S3/S4 (10 run) pada replay trace ClarkNet dengan horizon prediksi 9 × 15 detik = 135 detik dan konsolidasi node aktif. Diagnostic empat-skenario n=1 digunakan untuk baseline H1 dan karakterisasi sistem.

Hasil paired menunjukkan S4 (hybrid-predictive) mencapai mean p99 126.0 ms dibanding S3 188.5 ms (selisih −62.5 ms, 95% CI [−100.9, −26.2], Cohen's d = −1.26, p = 0.030). Pelanggaran SLO rata-rata turun dari 656 menjadi 130 per run (−80.2%), sementara biaya proyeksi bulanan S3 dan S4 identik, USD 163. Diagnostic n=1 mencatat S1/S2/S3/S4 masing-masing 2,421.3/77.7/98.8/118.2 ms dan biaya USD 132/394/147/142. GRU memperoleh RMSE 4.75% pada data sintetis (6.01% sebelum HPO) dan 17.78% pada ClarkNet nyata. Hasil sekunder dilaporkan deskriptif setelah koreksi multiplikitas.

**Kata Kunci**: Cloud Computing, Kubernetes, Serverless, GRU, Predictive Scaling, Hybrid Architecture

---

# Abstract

Modern cloud architecture faces a scalability-versus-cost trade-off. This research designs a two-cluster hybrid architecture integrating Kubernetes and serverless computing with GRU-based workload prediction. In the final implementation, prediction drives Kubernetes replica scaling (Algorithm 2); routing responds to observed load, ready capacity, and tail latency (V3), rather than using GRU output as a routing weight.

The definitive H2 evaluation used 5 counterbalanced S3/S4 pairs (10 runs) on a ClarkNet replay with a 9 × 15-second = 135-second forecast horizon and active node consolidation. A separate n=1 four-scenario diagnostic provides the H1 baseline and mechanism characterization.

In the paired result, S4 (hybrid-predictive) achieved mean p99 latency of 126.0 ms versus 188.5 ms for S3 (difference −62.5 ms, 95% CI [−100.9, −26.2], Cohen's d = −1.26, p = 0.030). Mean SLO violations fell from 656 to 130 per run (−80.2%), while projected monthly cost was identical for S3 and S4 at USD 163. The n=1 diagnostic recorded S1/S2/S3/S4 p99 values of 2,421.3/77.7/98.8/118.2 ms and projected monthly costs of USD 132/394/147/142. The GRU achieved 4.75% RMSE on synthetic data (6.01% before HPO) and 17.78% on real ClarkNet data. Secondary metrics are reported descriptively after multiplicity correction.

**Keywords**: Cloud Computing, Kubernetes, Serverless, GRU, Predictive Scaling, Hybrid Architecture
