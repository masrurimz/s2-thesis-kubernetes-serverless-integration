# Ringkasan Progres Tesis

**Dari:** [Nama] · NIM [NIM] · [Prodi] · 7 Agustus 2026
**Judul:** *Decision Making and Elastic Scalability Management in Heterogeneous Cloud Environments Based on Workload Prediction*

---

## Status sekarang

Penelitian sudah selesai. Naskah tesis siap dibaca. Saya ingin bimbingan dulu sebelum daftar sidang.

## Intinya tentang apa

Kalau aplikasi di cloud sibuk, sistem harus nambah kapasitas. Kubernetes caranya stabil tapi agak lambat. Serverless caranya cepat tapi mahal kalau skalanya besar. Tesis saya menggabungkan keduanya — namanya arsitektur hibrida — dan menambahkan prediksi beban kerja (pakai model GRU) supaya sistem bisa nambah kapasitas *sebelum* puncaknya datang, bukan setelah.

## Yang diuji

Saya bandingkan 4 skenario:

| Kode | Isinya |
|---|---|
| S1 | Kubernetes saja |
| S2 | Serverless saja |
| S3 | Hibrida, tapi reaktif (baru nambah kapasitas setelah beban naik) |
| S4 | Hibrida, prediktif (nambah kapasitas berdasarkan ramalan) |

## Hasilnya

Yang paling penting: **S4 lebih baik dari S3**.

- Waktu respons p99: 126 ms vs 188,5 ms (lebih cepat kira-kira 33%)
- Pelanggaran SLO (p99 di atas 200 ms) turun 80%
- Biayanya sama

Hasil ini juga saya coba ulang sendiri (replikasi). Dari 10 pasangan percobaan, S4 menang 9. Jadi arahnya konsisten, bukan kebetulan sekali jalan.

## Yang jujur saya akui

- Model prediksinya bagus di data latihan (RMSE 4,75%), tapi di jejak trafik nyata lebih kasar (MAPE 17,78%). Saya tulis apa adanya. Meski prediksinya tidak sempurna, keputusan skalanya tetap lebih bagus.
- Angka biayanya dari model perkiraan, bukan tagihan cloud beneran.

## Yang berubah dari proposal dulu

Ada beberapa hal yang beda dari proposal awal, dan saya catat semua:

1. **Platform.** Dulu rencananya pakai GCP. Sekarang dijalankan di k3d + Knative (lokal). Alasannya akses resource, dan justru lebih mudah diulang eksperimennya. Komponen yang diuji tetap sama (HPA, KPA, node autoscaler).
2. **Peran prediksi.** Dulu prediksi ikut mengarahkan routing trafik. Sekarang prediksi cuma dipakai untuk keputusan *berapa* kapasitas yang ditambah — routing tetap berdasarkan kapasitas yang tersedia. Tujuannya supaya perbandingan S3 vs S4 bersih (beda cuma di input prediksinya).

Semua perubahan (13 item) saya tulis lengkap di **Analisis Drift**, lengkap dengan 17 sitasi. Bisa saya bawa saat bimbingan.

## Yang sudah siap

- Naskah tesis (PDF) — siap dikirim atau dibawa
- Analisis drift proposal → pelaksanaan
- 139 bundle eksperimen, tercatat rapi di sistem eviden

## Yang saya minta

1. Waktu bimbingan — saya bisa [Senin jam 9 / Selasa jam 1 / Rabu jam 10], atau menyesuaikan jadwal Bapak/Ibu
2. Masukan terutama soal: pindah platform, peran prediksi, dan cara saya melaporkan akurasi model
3. Kepastian kapan bisa daftar sidang

Terima kasih.
