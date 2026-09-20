# Abstrak

Pertumbuhan layanan cloud computing mendorong kebutuhan akan arsitektur yang mampu menangani beban kerja dinamis secara efisien. Penelitian ini merancang arsitektur hybrid dua-kluster yang mengintegrasikan Kubernetes dan serverless computing dengan prediksi beban kerja berbasis GRU. Dalam implementasi final, prediksi digunakan untuk scaling replika Kubernetes (Algorithm 2), sedangkan routing merespons beban teramati dan kapasitas ekor latensi (V3).

Evaluasi H2 dimulai dengan 5 pasangan counterbalanced S3/S4 (10 run) pada replay trace ClarkNet dengan horizon prediksi 9 × 15 detik = 135 detik dan konsolidasi node aktif. Diagnostic empat-skenario n=1 digunakan untuk baseline H1 dan karakterisasi sistem.

Hasil paired batch Juli menunjukkan S4 (hybrid-predictive) mencapai mean p99 126.0 ms dibanding S3 188.5 ms (selisih −62.5 ms, 95% CI [−100.9, −26.2], Cohen's d = −1.26, p = 0.0312, lantai desain 1/32 pada n = 5 karena kelima pasangan jatuh searah). Pelanggaran SLO rata-rata turun dari 656 menjadi 130 per run (−80.2%), sementara biaya proyeksi bulanan S3 dan S4 identik, USD 163. Diagnostic n=1 mencatat S1/S2/S3/S4 masing-masing 2,421.3/77.7/98.8/118.2 ms dan biaya USD 132/394/147/142. GRU memperoleh RMSE 4.75% pada data sintetis (6.01% sebelum HPO) dan 17.78% pada ClarkNet nyata. Hasil sekunder dilaporkan deskriptif setelah koreksi multiplisitas.

Provenansi prediktor mengubah verdict. Prediktor batch Juli tidak tercatat di manifest dan terbukti merupakan model terlatih-sintetis, sehingga hasilnya tidak teratribusikan ke ClarkNet. Pada tiga batch teratribusikan ClarkNet (5 + 10 + 10 pasangan), selisih p99 tidak signifikan di setiap batch (p = 0.656, 0.168, 0.307). Replikasi pre-registrasi pada host sepi dengan gerbang beban (10 pasangan, 20 run valid) menghasilkan selisih −13.6 ms (95% CI [−63.5, +35.6], p = 0.307, d = −0.16), dan pooled 25 pasangan memberi −16.5 ms (95% CI [−194.0, +182.5], p = 0.50). H2 tidak didukung; keunggulan hybrid atas Kubernetes murni (H1, p99 turun hingga 95%) tetap berdiri.

**Kata Kunci**: Cloud Computing, Kubernetes, Serverless, GRU, Predictive Scaling, Hybrid Architecture

---

# Abstract

Modern cloud architecture faces a scalability-versus-cost trade-off. This research designs a two-cluster hybrid architecture integrating Kubernetes and serverless computing with GRU-based workload prediction. In the final implementation, prediction drives Kubernetes replica scaling (Algorithm 2); routing responds to observed load, ready capacity, and tail latency (V3), rather than using GRU output as a routing weight.

The H2 evaluation began with 5 counterbalanced S3/S4 pairs (10 runs) on a ClarkNet replay with a 9 × 15-second = 135-second forecast horizon and active node consolidation. A separate n=1 four-scenario diagnostic provides the H1 baseline and mechanism characterization.

In the paired result, the July batch showed S4 (hybrid-predictive) at mean p99 latency of 126.0 ms versus 188.5 ms for S3 (difference −62.5 ms, 95% CI [−100.9, −26.2], Cohen's d = −1.26, p = 0.0312, the 1/32 design floor at n = 5 because all five pairs fell the same way). Mean SLO violations fell from 656 to 130 per run (−80.2%), while projected monthly cost was identical for S3 and S4 at USD 163. The n=1 diagnostic recorded S1/S2/S3/S4 p99 values of 2,421.3/77.7/98.8/118.2 ms and projected monthly costs of USD 132/394/147/142. The GRU achieved 4.75% RMSE on synthetic data (6.01% before HPO) and 17.78% on real ClarkNet data. Secondary metrics are reported descriptively after multiplicity correction.

Predictor provenance changed the verdict. The July batch's predictor is unrecorded in its manifest and was later shown to be the synthetic-trained model, so its result is not attributable to ClarkNet. Across the three ClarkNet-attributable batches (5 + 10 + 10 pairs), no batch clears the pre-specified test (p = 0.656, 0.168, 0.307). A pre-registered replication on a load-gated quiet host (10 pairs, 20/20 runs valid) found a −13.6 ms difference (95% CI [−63.5, +35.6], p = 0.307, d = −0.16), and pooling 25 pairs gives −16.5 ms (95% CI [−194.0, +182.5], p = 0.50). H2 is not supported; the hybrid advantage over pure Kubernetes (H1, p99 cut by up to 95%) stands.

**Keywords**: Cloud Computing, Kubernetes, Serverless, GRU, Predictive Scaling, Hybrid Architecture
