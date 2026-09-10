# Laporan Kemajuan Tesis

**Nama** : Muhammad Zahid Masruri  
**NRP** : 6025221041  
**Program Studi** : Magister Komputer (M.Kom), Teknik Informatika — ITS Surabaya  
**Dosen Pembimbing** : Prof. Tohari Ahmad dan Royyana Muslim Ijtihadie, S.Kom, M.Kom  
**Tanggal** : 10 September 2026  

**Judul tesis**  
*Decision Making and Elastic Scalability Management in Heterogeneous Cloud Environments Based on Workload Prediction*

---

Assalamu’alaikum Wr. Wb.

Dengan hormat, saya izin melaporkan kemajuan tesis saya. Mohon maaf sebelumnya karena sudah cukup lama tidak bimbingan. Alhamdulillah penelitian sudah berjalan jauh: eksperimen sudah selesai dijalankan, dan naskah tesis sudah saya susun. Saya mohon kesediaan Bapak/Ibu untuk mereview naskah ini dan memberikan bimbingan serta arahan langkah selanjutnya.

## 1. Ringkasan topik

Penelitian ini membahas cara mengatur kapasitas aplikasi di lingkungan cloud yang menggabungkan Kubernetes dan serverless. Sistem diberi prediksi beban kerja (model GRU) agar kapasitas bisa ditambah sebelum puncak permintaan datang, bukan setelahnya. Empat skenario dibandingkan: Kubernetes saja (S1), serverless saja (S2), hibrida reaktif (S3), dan hibrida prediktif (S4).

## 2. Yang sudah dikerjakan

1. Membangun platform eksperimen hibrida Kubernetes + serverless (Knative) beserta perangkat prediksi dan pengendali skala.
2. Menjalankan eksperimen perbandingan empat skenario, termasuk uji berpasangan S3 vs S4.
3. Menyusun ulang naskah tesis secara lengkap (siap dibaca dalam bentuk PDF).
4. Menyusun catatan perubahan dari proposal ke pelaksanaan penelitian (analisis drift), lengkap dengan rujukan.
5. Mengulang eksperimen utama untuk memastikan hasilnya dapat direproduksi.

## 3. Hasil utama

Pada perbandingan utama, skenario hibrida prediktif (S4) lebih baik daripada hibrida reaktif (S3): waktu respons p99 sekitar 126 ms dibanding 188,5 ms, pelanggaran SLO turun sekitar 80%, dengan perkiraan biaya yang sama. Hasil ini juga saya ulang secara mandiri; arah temuan tetap sama (S4 unggul pada sebagian besar ulangan).

Saya juga mencatat keterbatasan secara terbuka. Akurasi prediksi bagus pada data latihan, tetapi lebih kasar pada jejak trafik nyata. Angka biaya yang dilaporkan berasal dari model perkiraan, bukan tagihan cloud langsung.

## 4. Hal yang berbeda dari proposal

Ada beberapa perubahan dari proposal awal, dan semuanya sudah saya catat:

1. **Platform.** Semula direncanakan di GCP. Pelaksanaan akhirnya di lingkungan lokal (k3d + Knative) karena keterbatasan akses sumber daya. Komponen yang diuji tetap sama, dan eksperimen menjadi lebih mudah diulang.
2. **Peran prediksi.** Semula prediksi juga diarahkan ke routing lalu lintas. Pada pelaksanaan, prediksi dipakai untuk menentukan kapasitas yang ditambah, agar perbandingan S3 dan S4 hanya berbeda pada input prediksinya.

Rincian lengkap ada pada dokumen Analisis Drift (13 butir perubahan, 17 rujukan). Dokumen ini siap saya bawa saat bimbingan.

## 5. Dokumen yang sudah siap

- Naskah tesis (PDF)
- Analisis drift proposal → pelaksanaan
- Catatan dan bukti eksperimen (termasuk hasil ulangan)

## 6. Mohon arahan Bapak/Ibu

1. Kesediaan waktu bimbingan — saya menyesuaikan jadwal Bapak/Ibu.
2. Masukan atas naskah, khususnya terkait perubahan platform, peran prediksi, dan cara pelaporan akurasi model.
3. Arahan terkait waktu yang tepat untuk mendaftar sidang.

Demikian laporan kemajuan ini saya sampaikan. Atas perhatian dan bimbingan Bapak/Ibu, saya ucapkan terima kasih.

Wassalamu’alaikum Wr. Wb.

Hormat saya,  
Muhammad Zahid Masruri  
NRP 6025221041
