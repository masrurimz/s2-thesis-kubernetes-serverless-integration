# Abstrak

Pertumbuhan layanan cloud computing mendorong kebutuhan akan arsitektur yang mampu menangani beban kerja dinamis secara efisien. Kubernetes sebagai platform orkestrasi container dan serverless computing yang menawarkan elastisitas tinggi merupakan dua pendekatan utama, namun masing-masing memiliki keterbatasan jika digunakan secara terpisah. Penelitian ini merancang, mengimplementasikan, dan memvalidasi arsitektur hybrid yang mengintegrasikan Kubernetes dan serverless computing dengan prediksi beban kerja berbasis Gated Recurrent Unit (GRU) untuk distribusi lalu lintas yang cerdas.

Sistem yang diusulkan mengimplementasikan pengontrol routing berbasis SLO (Service Level Objective) yang secara dinamis menggeser lalu lintas antara backend Kubernetes yang hemat biaya dan backend serverless yang elastis berdasarkan pemantauan tail latency. Model prediksi GRU dilatih menggunakan pola beban kerja sintetis dan divalidasi terhadap baseline ClarkNet dan Calgary. Evaluasi dilakukan melalui 20 eksperimen terkontrol yang direplikasi pada empat skenario: K8s-only, serverless-only, hybrid-reactive, dan hybrid-predictive.

Hasil menunjukkan model GRU mencapai RMSE 6,01% (target <10%) dan MAE 4,91% (target <5%) dengan latensi inferensi ~40ms. Mekanisme sistem berhasil divalidasi: perpindahan bobot lalu lintas berfungsi (100/0 → 50/50), aksi prediktif berhasil terpicu sebelum pelanggaran SLO terjadi, dan pemodelan biaya menunjukkan potensi penghematan 6-9%. Namun, superioritas statistik atas pendekatan baseline tidak dapat ditetapkan karena keterbatasan lingkungan pengujian (k3d single-node, bias routing localhost). Penelitian ini memberikan kontribusi berupa: (1) prediktor GRU yang tervalidasi untuk beban kerja HTTP, (2) pengontrol routing berbasis SLO dengan kemampuan pre-warming prediktif, dan (3) kerangka evaluasi yang mengidentifikasi kebutuhan deployment produksi untuk validasi lebih lanjut.

**Kata Kunci**: Cloud Computing, Kubernetes, Serverless, Prediksi Beban Kerja, GRU, Distribusi Lalu Lintas, SLA, Arsitektur Hybrid

---

# Abstract

The growth of cloud computing services drives the need for architectures capable of handling dynamic workloads efficiently. Kubernetes as a container orchestration platform and serverless computing offering high elasticity represent two primary approaches, yet each has limitations when used in isolation. This research designs, implements, and validates a hybrid architecture integrating Kubernetes and serverless computing with Gated Recurrent Unit (GRU)-based workload prediction for intelligent traffic routing.

The proposed system implements an SLO (Service Level Objective)-aware routing controller that dynamically shifts traffic between cost-effective Kubernetes and elastic serverless backends based on tail latency monitoring. The GRU prediction model is trained on synthetic workload patterns and validated against ClarkNet and Calgary baselines. Evaluation is conducted through 20 replicated controlled experiments across four scenarios: K8s-only, serverless-only, hybrid-reactive, and hybrid-predictive.

Results show the GRU model achieves 6.01% RMSE (target <10%) and 4.91% MAE (target <5%) with ~40ms inference latency. System mechanisms are successfully validated: traffic weight shifting functions correctly (100/0 → 50/50), predictive actions trigger before SLO violations occur, and cost modeling indicates 6-9% savings potential. However, statistical superiority over baseline approaches could not be established due to testbed limitations (single-node k3d, localhost routing bias). This research contributes: (1) a validated GRU predictor for HTTP workloads, (2) an SLO-aware routing controller with predictive pre-warming capability, and (3) a comprehensive evaluation framework identifying production deployment requirements for further validation.

**Keywords**: Cloud Computing, Kubernetes, Serverless, Workload Prediction, GRU, Traffic Distribution, SLA, Hybrid Architecture
