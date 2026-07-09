# Abstrak

Pertumbuhan layanan cloud computing mendorong kebutuhan akan arsitektur yang mampu menangani beban kerja dinamis secara efisien. Penelitian ini merancang arsitektur hybrid dua-kluster yang mengintegrasikan Kubernetes dan serverless computing dengan prediksi beban kerja berbasis GRU untuk distribusi lalu lintas proaktif.

Sistem mengimplementasikan pengontrol routing V3 berbasis kapasitas dengan mekanisme proactive routing (ekstrapolasi tren beban aktual, 75 detik ke depan, gated oleh GRU confidence). Evaluasi: 30 eksperimen (4 skenario × n=5), trace ClarkNet (40 stages × 30s, RPS 22–164).

Hasil: S4 (Hybrid-predictive) p99=188ms, SLO=702/run — 75% lebih sedikit dari S3 (Cohen's d=1.21). S4 20% lebih murah dari S1 ($149 vs $187/mo) dengan 98.4% SLO compliance. GRU 400/400 prediksi sukses, 9 PREDICTIVE actions/run.

**Kata Kunci**: Cloud Computing, Kubernetes, Serverless, GRU, Proactive Routing, Hybrid Architecture

---

# Abstract

Modern cloud architecture faces a scalability vs cost trade-off. This research designs a two-cluster hybrid architecture integrating Kubernetes and serverless with GRU-based proactive traffic routing.

The V3 capacity-driven controller implements proactive routing via actual load trend extrapolation (75s ahead, GRU-gated). Evaluation: 30 experiments (4 scenarios × n=5), ClarkNet trace (40 stages × 30s, RPS 22–164).

Results: S4 (Hybrid-predictive) p99=188ms, SLO=702/run — 75% fewer than S3 (Cohen's d=1.21). S4 is 20% cheaper than S1 ($149 vs $187/mo) at 98.4% SLO compliance. GRU 400/400 successful predictions, 9 PREDICTIVE actions/run.

**Keywords**: Cloud Computing, Kubernetes, Serverless, GRU, Proactive Routing, Hybrid Architecture
