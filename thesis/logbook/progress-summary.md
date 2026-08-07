# Ringkasan Progres Tesis — untuk Bimbingan

**Dari:** [Nama] · NIM [NIM] · [Prodi] · 2026-08-07
**Judul:** *Decision Making and Elastic Scalability Management in Heterogeneous Cloud Environments Based on Workload Prediction*

---

## Status: penelitian selesai, naskah siap direview, siap bimbingan sebelum sidang

**Masalah yang diteliti.** Autoscaling di cloud punya trade-off: Kubernetes (K8s) stabil tetapi lambat menambah kapasitas; serverless cepat tetapi biayanya tinggi saat skala besar. Tesis ini menggabungkan keduanya dalam satu platform **hibrida**, dengan **prediksi beban kerja (GRU)** untuk mengambil keputusan skala lebih awal.

**Yang diuji.** Empat skenario arsitektur:

| Skenario | Deskripsi |
|---|---|
| S1 | Kubernetes murni (HPA) |
| S2 | Serverless murni (Knative) |
| S3 | Hibrida K8s + serverless, skala reaktif (berdasarkan beban teramati) |
| S4 | Hibrida K8s + serverless, skala **prediktif** (berdasarkan ramalan GRU) |

**Hasil utama.** S4 (prediktif) mengungguli S3 (reaktif) pada latensi p99: **126 ms vs 188.5 ms (lebih cepat ~33%)**, pelanggaran SLO (p99 < 200 ms) turun **80%**, dengan biaya yang sama. Hasil ini **direplikasi secara independen** — S4 menang 9 dari 10 pasangan percobaan. Efeknya konsisten di tiga batch percobaan, termasuk satu batch yang direplikasi ulang dengan nilai p identik dengan eksperimen utama.

**Kejujuran terhadap keterbatasan.** Prediksi GRU akurat pada data sintetis (RMSE 4.75%) tetapi lebih kasar pada jejak nyata (MAPE 17.78%) — keterbatasan ini dilaporkan apa adanya; keunggulan S4 tetap muncul karena keputusan skala memanfaatkan prediksi walau tidak sempurna. Biaya dilaporkan sebagai model proxy, bukan billing cloud.

**Perubahan dari proposal (drift, dilaporkan jujur).** Platform berpindah dari GCP ke lingkungan lokal k3d + Knative karena kendala akses; primitif cloud yang diuji (HPA, KPA, node autoscaler) sama persis dan lingkungan lokal justru membuat eksperimen reproducible. Prediksi GRU digunakan untuk **keputusan skala**, bukan routing trafik (agar perbandingan S3 vs S4 bersih). Seluruh 13 perubahan terdokumentasi lengkap dengan 17 sitasi di **Analisis Drift** (terlampir/disediakan saat bimbingan).

**Kelengkapan.**
- Naskah tesis selesai (Typst → PDF, kompilasi bersih) — siap dikirim/dibawa
- Analisis drift proposal→pelaksanaan: 13 item, 17 sitasi terarsip
- 139 bundle eksperimen dalam sistem eviden terkelola (registry + jurnal)

**Yang saya butuhkan dari Bapak/Ibu:**
1. Waktu bimbingan untuk memaparkan ringkasan ini + analisis drift (saya bisa hadir [Senin 09.00 / Selasa 13.00 / Rabu 10.00] atau menyesuaikan)
2. Review naskah dan masukan terutama pada: perubahan platform (D1), penggunaan prediksi untuk scaling (D5), dan pelaporan akurasi GRU (D9)
3. Konfirmasi timeline pendaftaran sidang

---

*Semua angka diverifikasi terhadap `results/claims/FINAL_NUMBERS.md` dan bundle eksperimen (tercatat di logbook). PDF naskah: `thesis-typst/build/thesis.pdf`.*
