// Chapter 4 — Results and Discussion
// Numbers in this chapter come from results/claims/FINAL_NUMBERS.md and the
// six experiment bundles listed below. Earlier bundles (February 2026 and
// 2026-07-08/10) are invalidated by Bugs 1–13 documented in
// results/claims/INCONSISTENCIES.md and are not used.
#import "figures.typ": *
#import "headings.typ": H, cap

= #H("ch4")

Bab ini menyajikan hasil eksperimen untuk arsitektur _hybrid_ Kubernetes-_serverless_ dengan prediksi beban kerja berbasis GRU.
Hasilnya disusun dalam beberapa bagian: kinerja model GRU, validasi mekanisme sistem, evaluasi komparatif antarskenario _deployment_, analisis biaya, dan diskusi.
Setiap klaim kuantitatif di bab ini berasal dari eksperimen yang tercantum di Lampiran E, yang memetakan setiap nama di sini ke folder hasilnya.
Catatan penting: hasil komparatif empat skenario dan hasil biaya berasal dari diagnostik empat skenario, satu _run_ per skenario.
Diagnostik ini adalah _run_ dengan n = 1 (H1).
Hasil tersebut dibingkai sebagai diagnostik, bukan konfirmatori.
Enam perbaikan infrastruktur (Bug 8 sampai 13) membuat semua _bundle_ eksperimen sebelumnya (Februari dan 8 sampai 10 Juli 2026) tidak berlaku lagi.
Perbaikan itu adalah (1) pembatasan CPU _node_ yang ditegakkan dan (2) kalibrasi ulang `r_saturation_per_replica`.
Perbaikan lain adalah (3) batas keadilan untuk replika Kubernetes dan (4) perangkat kalibrasi.
Terakhir, ada (5) gerbang keras untuk server GRU dan (6) pemisahan prediksi dari perutean.
Perbandingan prediktif lawan reaktif (H2) bertumpu pada satu _batch_ konfirmatori pra-registrasi berisi 10 pasangan (@sec:h2).
_Batch_ berpasangan sebelumnya, termasuk _batch_ Juli yang mencapai p = 0,0312 dengan prediktor yang tidak dapat diverifikasi, diringkas pada @sec:h2-history.
Bukti prediktor juga memuat pencarian representasi dan uji coba target persilangan tanggal 2026-09-13, yang dilaporkan bersama hasil GRU di bab ini.

== #H("ch4-gru") <sec:gru-model>

Model prediksi dilatih dan dievaluasi dengan protokol kronologis yang bebas kebocoran data.
Resolusi ClarkNet diubah menjadi 15 detik dan diskalakan dengan faktor yang sama seperti pada _replay_, sehingga model dilatih pada amplitudo yang kelak dilayaninya.
Bagian pelatihan, validasi, dan uji dipisahkan oleh _embargo_ sebesar `sequence_length + horizon - 1` sampel.
Statistik normalisasi hanya berasal dari bagian pelatihan.
Tidak ada jendela masukan atau target yang melintasi batas bagian.
Hiperparameter dan jumlah _epoch_ dipilih pada bagian validasi.
Model dilatih ulang pada bagian pelatihan dan validasi dengan jumlah _epoch_ tersebut.
Bagian uji dinilai satu kali per _seed_.
Jendela _replay_, 1995-09-02 04:35:30 sampai 04:55:00 UTC, berada di dalam bagian uji yang ditahan.
Model tidak pernah dilatih pada lalu lintas yang kelak dilayaninya.
Karena itu, kelompok _deployment_ melayani beban di luar sampel pelatihan.
Bagian pelatihan dan validasi tidak memuat _bucket_ akhir pekan.
Bagian uji terdiri dari 81,9% akhir pekan, sehingga kinerja dilaporkan per jenis hari.
Di sepanjang pembagian itu, tingkat beban turun dari 45,70 menjadi 34,08 hitungan per _bucket_ 15 s.
Ini setara dengan 3,05 sampai 2,27 RPS.

Pencarian Tree-structured Parzen Estimator @optuna2019 memilih jaringan dua lapis dengan 256 unit tersembunyi dan jendela masukan 30 sampel.
Pencarian itu juga memilih _dropout_ pada _head_ sebesar 0,055 dan laju pembelajaran $#"1,53" times 10^(-4)$ pada anggaran tetap 23 _epoch_.
Tabel @tab:gru-performance melaporkan akurasi pada bagian uji yang ditahan, dari tiga _seed_.
Semua _baseline_ dinilai pada jendela yang sama.

#figure(
  kind: table,
  table(
    columns: (auto, auto),
    [Metrik], [Nilai],
    [RMSE _holdout_], [29,635 $\pm$ 0,016],
    [MAE _holdout_], [22,486 $\pm$ 0,079],
    [RMSE sebagai persentase beban rata-rata], [39,6%],
    [_Skill_ terhadap _persistence_], [0,216],
    [Cakupan _upper envelope_ pada target yang menanjak], [0,921],
    [RMSE _rolling-origin_ pada bagian uji], [29,039 $\pm$ 6,893],
    [RMSE _baseline_ _persistence_], [37,813],
    [RMSE _baseline_ tren linear], [46,534],
    [RMSE _baseline_ _seasonal naive_], [53,688],
    [RMSE autoregresi linear, jendela sama], [29,465],
    [Latensi inferensi (median, _bundle_ September)], [4,0 ms (p95 5,1 ms)],
  ),
  caption: [Kinerja model GRU dengan protokol bebas kebocoran data],
) <tab:gru-performance>

Ada dua kesimpulan, dan yang kedua kurang menyenangkan.
Pertama, prakiraan memuat sinyal yang nyata.
Prakiraan menurunkan galat 21,6 persen dibandingkan _persistence_.
Penurunan itu stabil antar-_seed_ (simpangan baku 0,016).
Model ini tetap bekerja pada arketipe sintetis yang belum pernah dilihatnya (lonjakan 26,58, tanjakan 24,27, periodik 25,42, stasioner 4,74).
Satu putaran _rolling-origin_ pada bagian uji menghasilkan tingkat yang sama, yaitu 29,039 dibandingkan 29,635.
Kedua, jaringan ini tidak mengalahkan autoregresi linear pada jendela 30 sampel yang sama: 29,635 dibandingkan 29,465.
Karena itu, keunggulan akurasi atas model linear tidak dapat diklaim pada resolusi 15 detik.
Galat absolut jauh di atas target yang didaftarkan sebelumnya.
RMSE adalah 39,6 persen dari beban rata-rata, sedangkan targetnya 10 persen.
Selisih galat ini adalah sifat tugasnya, bukan sifat jaringan.
Prakiraan _persistence_ mengulang pengamatan terakhir.
Pada resolusi ini, prakiraan itu sudah mencapai 50,5 persen dari beban rata-rata.

Pencarian representasi kemudian menguji apakah ada representasi masukan atau target yang mengalahkan model linear itu.
Dua belas variasi ditetapkan terhadap autoregresi per-_fold_ dengan protokol _fold_ bebas kebocoran data (Lampiran E).
Kedua belas variasi tercatat hasilnya.
Tak satu pun mengalahkan model linear.
_Skill_ pada _fold_ seleksi berkisar dari -0,01 persen untuk `robust_scale`, yang setara sampai desimal keempat, hingga -5,08 persen untuk `calendar`.
Variasi terdekat adalah `nlinear` dengan -0,30 persen, dan p Diebold-Mariano 0,29.
Kesetaraan berlaku di setiap jenis hari.
Kesetaraan juga berlaku secara agregat.
Untuk `nlinear` dibandingkan autoregresi, Jumat malam mencapai 46,0 dibandingkan 45,6.
Sabtu mencapai 27,8 dibandingkan 27,9.
Minggu mencapai 25,2 dibandingkan 25,3.
Senin mencapai 27,8 dibandingkan 27,7, dalam RPS pada amplitudo yang dilayani.
`nlinear` mengalahkan autoregresi pada bagian uji, tetapi tetap gagal pada gerbang seleksi.
_Fold_ seleksi yang menentukan.
Kesimpulan yang diungkapkan adalah bahwa prediktor titik pada _deployment_ sebaiknya autoregresi linear.
Kesetaraan jaringan ini adalah keterbatasan tesis ini, bukan fakta yang disembunyikan.

Dua uji coba lanjutan membatasi pilihan _deployment_.
Pertama, pengambilan sampel yang lebih kasar menurunkan galat absolut untuk model mana pun.
Pada _bucket_ 60 detik, galat _fold_ turun dari 36,69 menjadi 25,18 untuk autoregresi.
Untuk jaringan, galat turun dari 36,69 menjadi 25,30.
Galat ini dalam RPS pada amplitudo yang dilayani.
Targetnya menjadi lebih kasar, dan horizon jam dinding bertambah dari 135 menjadi 180 detik.
Ini perubahan interval dan horizon, bukan keberhasilan pemodelan.
Kedua, target relatif terhadap kapasitas mendeteksi titik beban melewati kapasitas, yang tidak terdeteksi oleh prakiraan titik (Lampiran E).
_Recall_ persilangan adalah 0,988 $plus.minus$ 0,009, dibandingkan 0,008 sampai 0,042 untuk autoregresi ditambah ambang dan 0,119 sampai 0,163 untuk _persistence_.
Keluaran mentah jaringan terlalu percaya diri (Brier per langkah 0,236 dibandingkan 0,049 pada acuan linear).
Pemetaan isotonik dipasang per _fold_ hanya pada langkah validasi dalam dari _fold_ itu.
Brier terkalibrasi turun menjadi 0,043, di bawah acuan.
Aturan keputusan untuk target ini adalah _recall_ pada laju alarm palsu yang dibatasi.
Pada target _recall_ 0,80, titik operasi terkalibrasi berada pada ambang 0,45.
Titik itu memiliki presisi 0,543, laju alarm palsu 0,210, dan rata-rata waktu mendahului 3,9 langkah, sekitar 58 detik.
Label hanya ada ketika batas kapasitas didekati, yaitu bawaan kode sebanyak enam replika, bukan sepuluh seperti pada konfigurasi berpasangan.

Satu temuan operasional membentuk rancangan pengendali prediktif.
Selama eksperimen langsung, prediksi GRU tertinggal dari lonjakan beban yang sebenarnya.
Karena itu, prakiraan masuk ke perencanaan replika Kubernetes pada Algoritma 2 melalui _upper envelope_.
Algoritma 1 merutekan berdasarkan beban teramati, kapasitas replika yang siap, dan status SLO.
Prakiraan tidak menentukan pembagian perutean.
Pada model bebas kebocoran, kepercayaan yang dilaporkan adalah 0,6.
Skor ini diturunkan dari rasio RMSE validasi terhadap beban rata-rata.
Rasio itu kini melebihi ambang 0,15, sehingga skor turun dari 0,8 menjadi 0,6.
Skor hanya mengambil dua nilai ini (prediktor saat ini).
Diagnostik Juli mencatat nilai 0,72 sampai 0,89 pada prediktor yang lebih lama.
Algoritma 1 membandingkan skor itu dengan ambang 0,5, dan kedua nilai lolos.
Algoritma 2 tidak memeriksanya.
Karena itu, ambang tidak pernah memblokir prakiraan, dan skor tidak berubah dalam satu _run_.

Kelompok sintetis dari _setup_ uji yang sama menurunkan ulang target akurasi yang didaftarkan sebelumnya, dengan protokol yang identik.
_Bundle_ studi melaporkan hasilnya, bukan mencampurnya ke tabel di atas.

== #H("ch4-phasea1")

Fase A1 memvalidasi bahwa setiap mekanisme sistem bekerja dengan benar pada profil beban menanjak yang terkontrol.
Fase ini menjalankan pengendali perutean tangga prioritas yang lebih awal, yang kemudian digantikan oleh pengendali V3 berbasis kapasitas.
Selama eksperimen, pengendali perutean membuat 18 keputusan.
Keputusan ini menunjukkan keempat jenis aksi dalam urutan prioritas yang benar: SCALE_OUT (7), MAINTAIN (8), OPTIMIZE_COST (2), dan PREDICTIVE (1).

#figure(
  kind: table,
  table(
    columns: (auto, auto),
    [Aksi], [Jumlah],
    [SCALE_OUT], [7],
    [MAINTAIN], [8],
    [OPTIMIZE_COST], [2],
    [PREDICTIVE], [1],
    [Total], [18],
  ),
  caption: [Distribusi keputusan pengendali perutean (Fase A1)],
) <tab:phase-a1-decisions>

Eksperimen memvalidasi pergeseran bobot.
Bobot lalu lintas bergeser dari 100/0 (Kubernetes murni) melalui langkah _scale-out_ berturut-turut menjadi 50/50 (keterlibatan _serverless_ maksimum) saat _tail latency_ melampaui ambang SLO.
Setiap langkah menggeser pembagian sebesar sepuluh poin persentase.
Eksperimen juga memvalidasi aksi PREDICTIVE saat sistem sehat (p99 = 146 ms).
GRU memprediksi kenaikan beban kerja 47% dengan kepercayaan 72%, dan pengendali memicu PREDICTIVE untuk mempertahankan pembagian 50/50.
Ini menjaga kesiapan _serverless_ sebelum pelanggaran SLO terjadi.
Pada pengendali awal itu, prakiraan memengaruhi perutean.
Pengendali V3 yang dipakai dalam semua _run_ berpasangan tidak demikian (Bab 3).

== #H("ch4-comparative")

Evaluasi komparatif membandingkan empat skenario _deployment_: S1 (Kubernetes dengan HPA), S2 (hanya _serverless_), S3 (_hybrid_ dengan perutean reaktif), dan S4 (_hybrid_ dengan penskalaan replika prediktif).
Semua skenario me-_replay_ _trace_ HTTP ClarkNet dengan rata-rata 73 _request_ per detik (puncak 164 RPS).
Setiap skenario memakai kapasitas _node_ terkalibrasi berupa Docker `--cpus=1.0` per _node_ beban kerja (total 2,0 CPU).
Konfigurasi ini menetapkan `max_k8s_replicas = 6` sesuai kapasitas yang dapat dijadwalkan dan tidak memakai batas CPU per _pod_.
Hasil ini adalah diagnostik n = 1 dari diagnostik empat skenario.
Perbandingan empat skenario (H1) kemudian direplikasi pada n = 5, seperti dilaporkan di bawah.
Perbandingan berpasangan S3 lawan S4 (H2) disajikan pada @sec:h2.
Keempat skenario berjalan pada infrastruktur tetap yang sama, sehingga perbandingan setara dalam satu _bundle_.
_Bundle_ empat skenario 8 sampai 10 Juli tidak dipakai, karena di dalamnya _run_ S1 dan S2 serta _run_ S3 dan S4 berasal dari konfigurasi pengendali yang berbeda.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    [Skenario], [p99 (ms)], [Pelanggaran SLO], [Tingkat pelanggaran SLO], [Waktu di _serverless_ (%)], [PREDICTIVE],
    [S1 (K8s+HPA)], [2.421,3], [6.717], [7,66%], [0,0%], [0],
    [S2 (_Serverless_)], [77,7], [19], [0,02%], [100,0%], [0],
    [S3 (Reaktif)], [98,8], [3], [0,00%], [31,8%], [0],
    [S4 (Prediktif)], [118,2], [104], [0,12%], [24,7%], [9],
  ),
  caption: [Ringkasan per skenario (diagnostik n = 1)],
) <tab:scenario-summary>

Keempat skenario terpisah menjadi dua rezim.
S1 (Kubernetes murni dengan HPA) jenuh di bawah beban ClarkNet.
p99-nya mencapai 2.421,3 ms dan mencatat 6.717 pelanggaran SLO (tingkat pelanggaran 7,66%), jauh melampaui ambang SLO 200 ms.
Tiga skenario lain menjaga p99 jauh di bawah SLO.
S2 (hanya _serverless_) mencapai 77,7 ms, S3 (_hybrid_ reaktif) 98,8 ms, dan S4 (_hybrid_ prediktif) 118,2 ms.
Tingkat pelanggaran SLO ketiganya nol atau mendekati nol (berturut-turut 0,02%, 0,00%, dan 0,12%).
Dua perbandingan terarah menilai skenario _hybrid_.
Satu membandingkan skenario prediktif dengan skenario reaktif (S4 lawan S3).
Yang lain membandingkan skenario _hybrid_ prediktif dengan Kubernetes murni (S4 lawan S1).
Tabel ini hanya memiliki satu _run_ per skenario.
Tidak ada statistik inferensial (uji t, ukuran efek, rentang kepercayaan) yang dihitung di sini.
Putusan S4 lawan S1 bersifat deskriptif, yaitu diagnostik n = 1.
Perbandingan S4 lawan S3 (H2) memakai rancangan berpasangan pada @sec:h2.
Pada tabel, ambang SLO adalah p99 < 200 ms.
Pelanggaran SLO dan tingkat pelanggaran SLO berasal dari satu _run_.
Waktu di _serverless_ adalah bagian waktu _run_ dengan bobot Knative di atas nol.
Pangsa lalu lintas, dihitung sebagai hasil kali bobot-waktu HAProxy, adalah 6,1% untuk S3 dan 3,0% untuk S4.
PREDICTIVE menghitung kenaikan bobot yang terjadi saat predicted_upper melebihi beban teramati.
Label itu tidak mengubah pembagian (Bab 3).
Jumlahnya rendah karena label memerlukan kenaikan beban di atas 3 RPS per siklus, beban di atas 80% kapasitas, dan nilai prediksi di atas beban teramati.
Pada _run_ ini, 8 dari 9 label PREDICTIVE berasal dari ekstrapolasi beban teramati, dengan prakiraan GRU di bawah beban teramati.
Dalam eksperimen 1.200 detik (sekitar 80 siklus kontrol), hanya 9 siklus menghasilkan label PREDICTIVE.
Sebagian besar siklus berada dalam kapasitas siap (MAINTAIN atau RECOVERY).

Replikasi empat skenario berjalan pada 8 Agustus 2026 dan 9 Agustus 2026 (Lampiran D).
_Bundle_-nya tidak memuat berkas analisis, sehingga setiap statistik di sini dihitung ulang dari 20 hasil _run_.
Replikasi menjalankan 4 skenario dengan 5 _run_ masing-masing (20 _run_ bersih).
Semua gerbang validitas lolos (5/5 per skenario), dan fidelitas perlakuan terpenuhi di setiap _run_ S4.
Kelompok S4 berjalan sebelum GRU bebas kebocoran pada @sec:gru-model dilatih pada 10 September 2026, sehingga mengukur prediktor yang lebih awal.
Pada log _daemon_ _run_ S4 pertama, prakiraan titiknya 76,2 RPS dan _upper envelope_-nya 85,9 RPS, berselisih sekitar 10 RPS.
Model bebas kebocoran memprakirakan 55 sampai 60 RPS untuk beban yang sama.
Karena itu, perbandingan S1 dan S2 pada _batch_ ini berlaku untuk arsitektur, bukan untuk prakiraan pada @sec:gru-model.
Rata-rata p99 per skenario adalah S1 110,3 ms, S2 79,7 ms, S3 151,6 ms, dan S4 99,1 ms.
Pelanggaran SLO yang dijumlahkan atas lima _run_ adalah S1 253, S2 2, S3 1.998, dan S4 92 (rata-rata per _run_ 50,6; 0,4; 399,6; dan 18,4).
Replikasi tidak mereproduksi saturasi S1 pada diagnostik n = 1.
Penyebabnya adalah batas replika.
Diagnostik n = 1 memakai `max_k8s_replicas = 6`, yang memaksa Kubernetes murni jenuh (p99 2.421,3 ms).
Replikasi memakai pengaturan kalibrasi `max_k8s_replicas = 10`.
Dengan ruang sebesar itu, HPA saja mampu menampung beban ClarkNet.
S1 tidak jenuh, sehingga hasil itu tidak tereproduksi pada n = 5.
S4 lawan S1 adalah -10,2% dengan p = 0,151 (tidak signifikan).
Ini temuan metodologis yang penting.
Keunggulan _hybrid_ atas Kubernetes murni muncul ketika _baseline_ dibatasi kapasitasnya, bukan ketika HPA punya ruang yang lega.

#figure(
  fig-p99-boxplot(),
  caption: [Latensi p99 per skenario (n = 5, replikasi empat skenario)],
) <fig:p99-box-n5>

#figure(
  fig-slo-violations(),
  caption: [Rata-rata pelanggaran SLO per _run_ pada replikasi empat skenario (5 _run_ per skenario)],
) <fig:slo-violations-n5>

=== #H("ch4-h2") <sec:h2>

H2 memprediksi bahwa penskalaan replika prediktif (S4) memberi latensi p99 lebih rendah daripada penskalaan reaktif (S3).
Ujinya adalah satu _batch_ konfirmatori berisi 10 pasangan S3/S4 dengan urutan diseimbangkan (20 _run_), dijalankan pada 20 September 2026 dan didaftarkan sebelumnya (pra-registrasi) sebelum mulai.
Titik akhir utama adalah selisih p99 berpasangan, diuji dengan uji permutasi berpasangan satu sisi.
Setiap _run_ S4 memakai GRU yang dilatih pada ClarkNet (@sec:gru-model), dan manifes setiap _run_ mencatat model itu.

_Batch_ ini berjalan dengan gerbang beban _host_, karena _batch_ sebelumnya menunjukkan p99 naik bersama beban CPU _host_ (@sec:h2-history).
Gerbang mengambil sampel beban _host_ sebelum _run_ pada rasio 0,07, di bawah ambang peringatan 0,5.
Gerbang hanya memeriksa satu sampel sebelum setiap _run_ dan tidak memantau beban selama _run_.
Selama _run_, rata-rata porsi CPU _host_ sibuk adalah 0,14 sampai 0,27 per _run_, dan puncaknya melebihi 0,5 pada 7 dari 20 _run_.
Semua 20 _run_ lolos gerbang validitas.
@tab:h2-primary melaporkan hasilnya.

#figure(
  kind: table,
  table(
    columns: (auto, auto),
    [Statistik], [Nilai],
    [Rata-rata p99 S3 (ms)], [160,4],
    [Rata-rata p99 S4 (ms)], [146,8],
    [Selisih rata-rata (ms)], [-13,6],
    [Rentang kepercayaan berpasangan 95% (ms)], [-63,5 sampai +35,6],
    [p permutasi satu sisi], [0,307],
    [Cohen's d berpasangan], [-0,16 (diabaikan)],
    [Pasangan dimenangkan S4], [5 dari 10],
  ),
  caption: [Perbandingan berpasangan S4 lawan S3 yang didaftarkan sebelumnya (10 pasangan, 20 September 2026)],
) <tab:h2-primary>

Rata-rata S4 lebih cepat 13,6 ms, tetapi rentang kepercayaan 95% mencakup nol dan p = 0,307.
S4 menang pada 5 dari 10 pasangan.
Karena itu, H2 tidak didukung pada uji p99 utama yang ditetapkan sebelumnya.

Dua estimasi menempatkan hasil ini dalam konteks.
Pertama, penggabungan seluruh 25 pasangan yang memakai prediktor hasil latihan ClarkNet (_batch_ ini dan dua _batch_ tanggal 13 September 2026) menghasilkan -16,5 ms (rentang kepercayaan 95% [-188,6; +184,5], p satu sisi = 0,448, d = -0,03).
Kedua, _batch_ ini didaftarkan sebelumnya karena sebuah estimasi sementara tampak menjanjikan.
Estimasi itu memakai delapan pasangan dari _batch_ konfirmatori 13 September 2026 dengan puncak beban _host_ di bawah 40% (-101,3 ms, p = 0,039).
Estimasi itu tidak bertahan pada _batch_ yang didaftarkan sebelumnya, yang menunjukkan bahwa hasilnya muncul dari pemilihan subset setelah data terlihat.

=== #H("ch4-h2-history") <sec:h2-history>

Delapan _batch_ membandingkan S3 dan S4 sebelum _batch_ pra-registrasi.
@tab:h2-history mencantumkan masing-masing beserta alasan mengapa _batch_ itu bukan hasil H2, dan @fig:replication-batches memplot _batch_ yang berjalan dengan konfigurasi pengendali akhir.
Dua _batch_ lain dari 7 Agustus 2026 tidak dimasukkan, karena berkas hasilnya terhapus sebelum di-_commit_.

#[
#set par(justify: false)
#figure(
  kind: table,
  table(
    columns: (1.2fr, auto, auto, auto, 2fr),
    align: (left, center, center, center, left),
    [_Batch_], [Pasangan], [Selisih rata-rata (ms)], [p], [Mengapa bukan hasil H2],
    [Pra-kalibrasi (11 Juli 2026)], [5], [+10,0], [--], [Target replika menghitung margin keamanan dua kali, sehingga S4 menentukan jumlah replika persis seperti S3],
    [Awal (12 Juli 2026)], [5], [-8,1], [0,38], [Horizon prakiraan lima langkah (75 s) dan _baseline_ reaktif yang belum disetel],
    [Juli (14 Juli 2026)], [5], [-62,5], [0,0312], [Manifes tidak menyebut prediktor, dan model yang dipasang saat itu dilatih pada data sintetis (Lampiran B)],
    [Agustus A (8 Agustus 2026)], [5], [-4,0], [0,436], [Prediktor dilatih sebelum protokol bebas kebocoran pada @sec:gru-model],
    [Agustus B (8 Agustus 2026)], [5], [-58,0], [0,062], [Prediktor sama dengan Agustus A],
    [Replikasi empat skenario (9 Agustus 2026)], [5 _run_ per kelompok], [-52,5], [0,032], [_Run_ tidak berpasangan dengan prediktor awal yang sama; uji Welch memberi p = 0,097],
    [Pasangan September (13 September 2026)], [5], [+153,3], [0,656], [Beban _host_ tidak dicatat; _batch_ 10 pasangan menyusul pada hari yang sama],
    [Konfirmatori pertama (13 September 2026)], [10], [-104,2], [0,168], [p99 naik bersama beban CPU _host_ (r = 0,69); tiga _run_ paling lambat memiliki puncak CPU sibuk 66 sampai 100%],
  ),
  caption: [_Batch_ S4 lawan S3 sebelumnya. Selisih negatif menguntungkan S4.],
) <tab:h2-history>
]

#figure(
  image("../figures/fig04_6_replication_batches_id.png", width: 90%),
  caption: [Selisih p99 S4 lawan S3 dengan rentang kepercayaan 95% untuk setiap _batch_ yang berjalan dengan konfigurasi pengendali akhir],
) <fig:replication-batches>

Dua _batch_ sebelumnya mencapai p < 0,05: _batch_ Juli dan uji Mann-Whitney pada replikasi empat skenario.
Keduanya tidak memakai prediktor hasil latihan ClarkNet, dan tiga _batch_ yang memakainya tidak menemukan perbedaan yang signifikan.
Peralihan dari _batch_ awal ke _batch_ Juli juga mengubah tiga hal sekaligus.
Horizon prakiraan bertambah dari 75 s menjadi 135 s, konsolidasi _node_ ditambahkan, dan _baseline_ reaktif disetel.
Seandainya keuntungan pada _batch_ Juli nyata, keuntungan itu tidak dapat dikreditkan pada salah satunya.

=== #H("ch4-s4vs1")

Dengan infrastruktur yang dibatasi dengan benar (`--cpus=1.0` per _node_ ditegakkan, `max_k8s_replicas = 6`), Kubernetes murni (S1) jenuh sesuai rancangan di bawah beban ClarkNet.
Skenario _hybrid_ prediktif memberikan perbaikan besar (@tab:s4-vs-s1).

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto),
    [Metrik], [S1 (K8s+HPA)], [S4 (Prediktif)], [Perbaikan],
    [Latensi p99 (ms)], [2.421,3], [118,2], [-2.303,1 (-95,1%)],
    [Pelanggaran SLO], [6.717], [104], [-6.613 (-98,5%)],
    [Tingkat pelanggaran SLO], [7,66%], [0,12%], [-7,54 pp],
  ),
  caption: [_Hybrid_ prediktif (S4) lawan Kubernetes murni (S1)],
) <tab:s4-vs-s1>

Skenario _hybrid_ prediktif menurunkan latensi p99 sebesar 95,1% (dari 2.421,3 ms menjadi 118,2 ms) dan pelanggaran SLO sebesar 98,5% (dari 6.717 menjadi 104) dibandingkan Kubernetes murni.
Ini membalik temuan negatif sebelumnya.
Hasil H1 sebelumnya (S4 lebih buruk daripada S1) adalah artefak Bug 8 dan 11.
Batas CPU _node_ tidak pernah ditegakkan.
_Pod_ memakai seluruh 16 inti _host_.
HPA pada S1 menyediakan _node_ dinamis (4,0 CPU dibandingkan 2,0 CPU untuk S3/S4).
Akibatnya, S1 tidak pernah jenuh.
Dengan `--cpus=1.0` per _node_ ditegakkan dan replika dibatasi pada kapasitas yang dapat dijadwalkan, S1 jenuh sesuai maksud, dan perutean _hybrid_ (S4) memberi manfaat yang jelas.
H1 didukung pada arahnya pada n = 1.
Satu _run_ tidak dapat menetapkan signifikansi statistik.



== #H("ch4-cost")

Analisis biaya memetakan _testbed_ lokal ke layanan _cloud_ yang setara.
Analisis ini memetakan _pod_ Kubernetes HPA ke _control plane_ terkelola ditambah _node_ komputasi, dan konkurensi Knative ke konkurensi fungsi yang disediakan.
Analisis ini kemudian memproyeksikan biaya bulanan terpadu dari konsumsi sumber daya yang terukur.
Proyeksi di bawah berasal dari _baseline_ diagnostik n = 1 dan merupakan estimasi diagnostik satu _run_.

Proksi biaya adalah model, bukan pengamatan tagihan.
Analisis titik impas membedakan tingkat beban kerja pada saat keunggulan relatif _serverless_ dan kapasitas berbasis VM berubah @skyrise2025.
Granularitas penagihan dan penjadwalan dapat membuat biaya sumber daya _serverless_ terukur melebihi konsumsi mentah @demystifying2025.
Menjaga instans _serverless_ tetap hangat menambah _overhead_ CPU dan memori @highcost2025, dan perbandingan biaya _hybrid_ perlu memperhitungkannya.
Acuan ini mendukung pelaporan proksi hanya pada arahnya.
Acuan ini mendukung dipertahankannya hasil biaya sama pada eksperimen berpasangan, bukan klaim penghematan universal.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto),
    [Skenario], [_Node_ awal→puncak (jam dinamis)], [Permintaan _serverless_ (PC)], [Total/bln = EKS+EC2+Lambda], [USD/1 juta SLO-OK],
    [S1 (hanya K8s)], [2→2 (0)], [0 (0)], [USD 132 = 72+60+0], [USD 0,79],
    [S2 (_Serverless_)], [0→0], [87.840 (8)], [USD 395 = 0+0+395], [USD 2,19],
    [S3 (_Hybrid_ reaktif)], [2→2 (0)], [5.354 (1)], [USD 147 = 72+60+15], [USD 0,81],
    [S4 (_Hybrid_ prediktif)], [2→2 (0)], [2.666 (1)], [USD 143 = 72+60+11], [USD 0,79],
  ),
  caption: [Proyeksi biaya bulanan AWS (diagnostik n = 1)],
) <tab:cost-analysis>

S1 adalah skenario termurah (USD 132/bln), tetapi gagal total memenuhi SLO (p99 = 2.421 ms, tingkat pelanggaran 7,66%).
Biayanya yang rendah mencerminkan layanan yang buruk, bukan efisiensi.
S2 (hanya _serverless_) paling mahal (USD 395/bln), tetapi mencapai latensi mentah terbaik (77,7 ms).
Pada tabel, kolom _Node_ berisi awal→puncak dengan jam-_node_ dinamis dalam tanda kurung, dan Total/bln terurai menjadi EKS+EC2+Lambda.
Proyeksi biaya n = 1 ini hanya perkiraan diagnostik yang menunjukkan arah.
Proyeksi itu tidak boleh dipakai untuk mengurutkan S3 dan S4 atau untuk mengklaim penghematan bulanan.
Kolom USD/1 juta SLO-OK menormalkan total biaya bulanan dengan jumlah _request_ yang memenuhi SLO.

#figure(
  fig-cost-comparison(),
  caption: [Proyeksi biaya bulanan AWS per skenario],
) <fig:cost-comparison>

== #H("ch4-node")

_Baseline_ diagnostik n = 1 membatasi `max_k8s_replicas = 6` agar sesuai dengan kapasitas dua _node_ yang dapat dijadwalkan.
K3dAutoscaler tidak pernah aktif, dan tingkat ketiga (_autoscaling_ tingkat _node_) tidak diuji.
Diagnostik tiga tingkat dengan beban tinggi yang terpisah (n = 1) menaikkan batas menjadi 10 replika dan memberi beban kerja konstan 200 RPS selama 1.200 detik.
Beban itu sengaja melampaui batas statis enam _pod_ agar memicu _pod_ Pending, penyediaan _node_ dinamis, dan _offload_ ke _serverless_ yang berkelanjutan sekaligus.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto),
    [Skenario], [p99 (ms)], [_Node_], [Tunda (s)], [Waktu di _serverless_ (%)], [USD bulanan], [Pelanggaran SLO],
    [S1 (K8s+HPA)], [6.665,1], [2], [54,8], [0,0%], [219], [78.257],
    [S2 (_Serverless_)], [1.401,9], [0], [---], [100,0%], [1.110], [12.859],
    [S3 (Reaktif)], [874,4], [2], [51,8], [96,5%], [387], [23.913],
    [S4 (Prediktif)], [1.393,3], [2], [70,5], [96,5%], [387], [46.245],
  ),
  caption: [Diagnostik arsitektur tiga _tier_ (n = 1)],
) <tab:dynamic-node-offload>

Diagnostik ini menguji ketiga tingkat.

- Tingkat 1 (perutean): skenario _hybrid_ menggeser bobot HAProxy antara Kubernetes dan Knative. S3 dan S4 masing-masing mengumpulkan lebih dari 24.000 hasil kali bobot-waktu _serverless_.
- Tingkat 2 (penskalaan _pod_): HPA dan Algoritma 2 menskalakan replika dari 3 sampai 10 (batas pengganti).
- Tingkat 3 (_autoscaling node_): K3dAutoscaler mendeteksi _pod_ Pending yang tidak dapat dijadwalkan dan menyediakan dua _node_ beban kerja dinamis per _run_. Setiap _run_ mencatat urutan peristiwa penyediaan (Pending terdeteksi, lalu penyediaan dimulai, lalu _node_ dibuat) dalam log peristiwa penyediaan.

Pada tabel, _Node_ menghitung _node_ dinamis yang disediakan oleh K3dAutoscaler.
Tunda adalah waktu tunda penyediaan pertama.
Waktu di _serverless_ (%) adalah bagian waktu eksperimen dengan bobot Knative di atas nol.
USD bulanan adalah perkiraan diagnostik yang menunjukkan arah.

#figure(
  fig-node-provisioning(),
  caption: [Linimasa penyediaan _node_ dinamis],
) <fig:node-provisioning>

Kompromi antara menambah _node_ dan _offload_ ke _serverless_ terlihat dalam data.
S1 (Kubernetes murni dengan dua _node_ dinamis tetapi tanpa _offload_ ke _serverless_) memiliki p99 terburuk (6.665 ms) dan tingkat keberhasilan terburuk (65,6%).
S3 (_hybrid_ reaktif dengan dua _node_ dinamis yang sama ditambah waktu _serverless_ 96,5%) mencapai p99 terbaik (874 ms).
Knative menyerap waktu tunda penyediaan 51 sampai 70 detik pada S3 dan S4 dalam diagnostik Juli ini; _batch_ berikutnya mengukur waktu tunda 50 sampai 125 s.
Waktu tunda yang sama menyebabkan degradasi latensi berat pada S1, yang tidak punya cadangan _serverless_.
Penyediaan _node_ dinamis saja bukan pengganti _offload_ ke _serverless_.
Kedua mekanisme saling melengkapi.
Arsitektur _hybrid_ mendapat nilainya dari memakai keduanya secara bersamaan.

S3 dan S4 memiliki biaya bulanan yang sama (USD 387/bln) walau p99 berbeda.
Karena itu, selisih biaya antara mode reaktif dan prediktif dapat diabaikan pada beban ini.
Biaya EC2 _node_ dinamis (USD 0,028 per _run_, dicatat terpisah dari biaya Lambda _serverless_) sama untuk semua skenario K8s karena semuanya menyediakan dua _node_ yang sama.
Proyeksi biaya n = 1 ini hanya perkiraan diagnostik yang menunjukkan arah.
Proyeksi ini tidak boleh dipakai untuk mengklaim keunggulan biaya yang universal.

S4 berkinerja lebih buruk daripada S3 pada diagnostik ini.
p99 S4 adalah 1.393 ms dibandingkan 874 ms (+59%), dan pelanggaran SLO-nya 46.245 dibandingkan 23.913 (+93%).
S4 gagal pada gerbang validitas fidelitas aktuator.
Waktu tunda penyediaan terukur (70,5 s) ditambah margin aman 15 detik memerlukan `ceil(85.5 / 15) = 6` langkah prakiraan.
Model GRU yang dipasang hanya mengeluarkan 5 langkah (jendela prakiraan 75 detik).
S4 mengirim 55 prediksi dengan tingkat pengiriman 100%, tetapi tidak mengeluarkan label PREDICTIVE sama sekali.
Prakiraan tidak mengubah perilaku aktuator.
Horizon 5 langkah memadai untuk perkiraan waktu tunda penyediaan bawaan 60 detik, tetapi tidak untuk waktu tunda yang lebih panjang pada beban tinggi.
Temuan ini sejalan dengan premis ADAPT @adapt2026: horizon prakiraan harus menyesuaikan diri dengan waktu tunda penyediaan terukur, bukan tetap statis.

=== #H("ch4-varload")

Diagnostik beban konstan mengonfirmasi mekanismenya, tetapi tidak dapat menguji penskalaan prediktif.
Lalu lintas konstan tidak memberi prakiraan sesuatu untuk diantisipasi.
Diagnostik beban variabel ClarkNet (n = 1) memakai _trace_ ClarkNet asli (kenaikan 30 sampai 164 RPS, rata-rata 73 RPS).
Diagnostik ini menetapkan `max_k8s_replicas = 10` dan memakai horizon GRU 9 langkah yang diperpanjang (jendela 135 detik).
Puncak ClarkNet secara alami melampaui batas statis enam _pod_.
Puncak itu memicu _node_ dinamis tanpa penggelembungan beban buatan.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto, auto),
    [Skenario], [p99 (ms)], [_Node_], [Waktu di _serverless_], [Prediksi], [Pred], [SU proaktif], [USD bulanan],
    [S1 (K8s+HPA)], [118,4], [2], [0,0%], [---], [---], [---], [187],
    [S2 (_Serverless_)], [79,0], [0], [100,0%], [---], [---], [---], [403],
    [S3 (Reaktif)], [103,9], [2], [21,2%], [---], [---], [---], [196],
    [S4 (Prediktif)], [108,3], [2], [17,6%], [55], [4], [1], [196],
  ),
  caption: [Eksperimen beban variabel ClarkNet (n = 1)],
) <tab:clarknet-dynamic-node>

Pada beban variabel, prakiraan GRU menghasilkan aksi proaktif untuk pertama kalinya.
_Run_ itu mengeluarkan empat label PREDICTIVE dan satu _scale-up_ replika proaktif sebelum beban teramati mencapai target.
Label PREDICTIVE tidak mengubah pembagian (Bab 3).
Semua gerbang validitas lolos: horizon prakiraan memadai dan semua 55 prediksi terkirim.
Pada tabel, Pred menghitung label PREDICTIVE dan SU proaktif menghitung _scale-up_ replika proaktif.
USD bulanan adalah perkiraan diagnostik yang menunjukkan arah.
S4 memakai waktu _serverless_ 17,6% dibandingkan 21,2% pada S3.
_Scale-up_ proaktif menambah kapasitas Kubernetes lebih awal dan mengurangi ketergantungan pada _serverless_.
S3 mencapai p99 sedikit lebih baik (103,9 ms dibandingkan 108,3 ms, +4,3%) dan pelanggaran SLO lebih sedikit (14 dibandingkan 44), tetapi n = 1 tidak konklusif.
Biaya bulanan yang sama (USD 196/bln) mengonfirmasi tidak ada penalti biaya untuk mode prediktif pada beban ini.

=== #H("ch4-consol")

_Autoscaler node_ menerapkan konsolidasi bergaya _cluster-autoscaler_, mengikuti ambang pemakaian bawaan 50% pada Kubernetes Cluster Autoscaler @k8sca-faq.
Sebuah _node_ dinamis menjadi kandidat penghapusan bila tiga kondisi terpenuhi.
Pemakaian permintaan CPU-nya turun di bawah 50% dari kapasitas yang dapat dialokasikan.
Semua _pod_ beban kerja pada _node_ itu dapat dijadwalkan ulang ke _node_ beban kerja lain.
_Node_ itu tetap kurang terpakai setidaknya 90 detik.
Perintah `kubectl drain` mengeluarkan _pod_ ke _node_ lain sebelum kontainer _node_ dihapus.
_Cooldown_ 120 detik mencegah penghapusan beruntun.

Di bawah _trace_ beban variabel ClarkNet yang sama, konsolidasi menghasilkan pembedaan S3 lawan S4 terkuat dalam proyek ini:

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    [Skenario], [p99 (ms)], [Pelanggaran SLO], [_Node_ disediakan], [_Scale-down_], [USD bulanan],
    [S3 (Reaktif)], [228,4], [1.085], [3], [3], [162],
    [S4 (Prediktif)], [113,0], [40], [5], [3], [170],
  ),
  caption: [Beban variabel ClarkNet dengan konsolidasi _node_ (n = 1)],
) <tab:clarknet-consolidation>

S4 mencapai p99 50,5% lebih rendah (113 ms dibandingkan 228 ms).
Skenario itu mencapai pelanggaran SLO 96,3% lebih sedikit (40 dibandingkan 1.085) daripada S3.
Ini disertai kenaikan biaya 5% (USD 170/bln dibandingkan 162/bln).
Mekanismenya sebagai berikut.
Pengendali reaktif S3 secara agresif mengonsolidasikan semua _node_ dinamis ketika pemakaian turun.
Ini menyebabkan lonjakan latensi parah ketika beban ClarkNet kembali dan tidak ada kapasitas Kubernetes.
Prakiraan GRU pada S4 memprediksi kenaikan beban dan mempertahankan kapasitas Kubernetes.
Ini mencegah konsolidasi berlebihan.
Peristiwa penyediaan _scale-down_ mencatat pemakaian _node_ 0,3 terhadap ambang 0,5, dengan satu _pod_ di _node_, pada setiap konsolidasi.
Ini mengonfirmasi bahwa pemicu berbasis pemakaian berjalan dengan benar.
Putaran _autoscaling_ dua arah terlihat dalam log peristiwa.
_Node_ dibuat saat _pod_ pending terdeteksi.
Lalu _node_ dikonsolidasikan saat beban turun.
Lalu _node_ disediakan ulang saat beban naik lagi.
Pada tabel, _Scale-down_ menghitung peristiwa konsolidasi _node_, dan USD bulanan adalah perkiraan diagnostik yang menunjukkan arah, dihitung dari umur aktual per _node_ pada cap waktu peristiwa penyediaan.
Hasil ini berasal dari diagnostik konsolidasi _node_.

== #H("ch4-hpo")

Studi optimasi hiperparameter yang terpisah menjelajahi empat parameter pengendali lewat penyaringan Optuna TPE: `target_cpu_util`, `kp_burn`, `proactive_trend_threshold`, dan `proactive_approach_ratio`.
Studi itu berjalan pada infrastruktur sebelum perbaikan, yang mendahului _baseline_ diagnostik n = 1.
Temuan metodologisnya dilaporkan di sini untuk kelengkapan.
Hasil kuantitatif spesifiknya hanya menunjukkan arah dan digantikan oleh Bug 8 sampai 13.
Hasil itu bukan bagian dari _baseline_ saat ini.
Hasil itu tidak dipakai dalam evaluasi komparatif di atas.

Pelajaran utamanya bersifat metodologis, bukan numerik.
Pada _testbed_ sumber daya bersama dengan variansi antar-_run_ yang tinggi, tidak ada penyimpangan parameter dari kalibrasi bawaan yang bertahan pada validasi _holdout_.
Konfigurasi yang tampak kuat pada satu _run_ menurun tajam saat direplikasi.
Konfigurasi itu mempersempit margin aman Kubernetes dan menyebabkan saturasi lebih sering pada variansi tinggi.
Ini konsisten dengan risiko _overfitting_ pada pemilihan model @cawley2010overfitting.
Ini juga menyoroti sulitnya HPO pada sistem daring, tempat fungsi tujuan bergeser seiring waktu @nonstationary2022 dan setiap evaluasi berisik serta mahal @falkner2018bohb. Pada _testbed_ ini setiap evaluasi adalah satu eksperimen penuh pada sumber daya bersama.
Metodologi dua tahap (penyaringan lalu konfirmasi) dan pendekatan berbantuan _surrogate_ menyesuaikan kalibrasi dengan _baseline_ yang teramati.
Tidak ada penyimpangan hasil HPO yang dipakai pada hasil diagnostik n = 1.

== #H("ch4-discussion")

Evaluasi eksperimental ini memvalidasi dua hal.
Evaluasi ini memvalidasi ketepatan mekanisme arsitektur _hybrid_.
Pada infrastruktur yang dibatasi dengan benar, evaluasi ini juga memvalidasi keunggulan kinerja yang jelas dari perutean _hybrid_ atas Kubernetes murni.

Penelitian ini memvalidasi beberapa mekanisme.
Model GRU memenuhi target akurasinya pada data sintetis.
Pada kelompok sintetis, RMSE-nya 5,2% dari beban rata-rata dengan protokol bebas kebocoran data.
Ini memenuhi target.
Pada bagian ditahan dari _trace_ _deployment_ nyata, RMSE-nya 39,6%.
Target tidak tercapai di sana, dan model setara dengan autoregresi linear pada jendela masukan yang sama.
Latensi inferensi median pada _bundle_ September adalah 4,0 ms.
Karena itu, prediksi pada lalu lintas nyata adalah validasi parsial.
Pengendali Fase A1 menerapkan kerangka keputusan berbasis prioritas dan menunjukkan keempat jenis aksi.
Pengendali V3 menggantikan kerangka itu dengan pembagian berbasis kapasitas.
Prakiraan atas dari GRU masuk ke perencanaan replika pada Algoritma 2.
_Run_ diagnostik S4 membawa 9 label PREDICTIVE.
Label itu tidak menentukan pembagian, dan prakiraan mencapai pembagian hanya lewat jumlah replika.

Untuk perbandingan _hybrid_ lawan Kubernetes murni (H1), hasilnya positif pada arahnya di n = 1.
S4 menurunkan latensi p99 sebesar 95,1% (2.421,3 ms -> 118,2 ms).
Skenario itu menurunkan pelanggaran SLO sebesar 98,5% (6.717 -> 104) dibandingkan S1.
Temuan negatif sebelumnya adalah artefak infrastruktur (batas CPU yang tidak ditegakkan dan penyediaan _node_ dinamis berlebih pada S1).
Temuan itu bukan sifat mekanisme _hybrid_.
Hasil n = 1 tidak menetapkan signifikansi inferensial.
Replikasi empat skenario n = 5 tidak mereproduksi keunggulan ini.
Replikasi itu memakai `max_k8s_replicas = 10`, sehingga S1 tidak jenuh (p99 110,3 ms).
S4 lawan S1 tidak signifikan (p = 0,151).
Karena itu, keunggulan _hybrid_ muncul ketika _baseline_ dibatasi kapasitasnya, bukan ketika HPA punya ruang yang lega.

Untuk perbandingan prediktif lawan reaktif (H2), putusannya: tidak didukung.
_Batch_ konfirmatori pra-registrasi (10 pasangan dengan urutan diseimbangkan, semua 20 _run_ valid) mendapati p99 rata-rata S4 146,8 ms dibandingkan 160,4 ms untuk S3.
Selisih rata-ratanya -13,6 ms, dengan rentang kepercayaan 95% [-63,5; +35,6] ms, p = 0,307, dan d = -0,16, efek yang dapat diabaikan.
Metrik sekunder sejalan: p95 berbeda -0,9 ms dan pelanggaran SLO +3,6 per _run_, keduanya dapat diabaikan.
Penggabungan seluruh 25 pasangan yang memakai prediktor hasil latihan ClarkNet menghasilkan -16,5 ms (rentang kepercayaan 95% [-188,6; +184,5] ms, p satu sisi = 0,448, d = -0,03).
_Batch_ Juli sebelumnya mendapati -62,5 ms (p = 0,0312), tetapi prediktornya tidak dapat diverifikasi, sehingga @sec:h2-history melaporkannya sebagai sejarah.

Dua catatan membatasi kesimpulan ini.
Pertama, diagnostik empat skenario n = 1 memberi bukti mekanisme yang menunjukkan arah, tetapi tidak ada statistik inferensial untuk H1.
Kedua, daya uji terbatas pada skala efek ini.
Simpangan baku berpasangan adalah 484,5 ms pada 25 pasangan, dan nilai per _batch_ berkisar dari 83,6 ms sampai 1.057,3 ms (dihitung ulang dari _bundle_).
_Batch_ pra-registrasi menjalankan sepuluh pasangan karena alasan ini, dan tetap menemukan selisih yang dapat diabaikan.
Uji p99 utamanya telah ditetapkan sebelumnya.
Metrik sekundernya (p95, pelanggaran SLO) tidak signifikan setelah koreksi multiplisitas (p terkoreksi = 1,0) dan dilaporkan sebagai deskriptif.

Secara keseluruhan, hasil mendukung H1 pada arahnya (arsitektur _hybrid_ mengungguli _baseline_ Kubernetes murni yang jenuh pada n = 1).
H2 tidak didukung.
_Batch_ pra-registrasi menemukan selisih yang dapat diabaikan, dan estimasi gabungan 25 pasangan sebesar -16,5 ms memiliki rentang kepercayaan yang mencakup nol.
Sebuah _batch_ dapat menguji H2 hanya bila sisi prediktif bertindak berdasarkan prakiraannya.
_Run_ yang prakiraannya tidak pernah mengubah perencanaan replika mengukur pengendali reaktif dengan label S4, dan tidak dapat memisahkan kedua sisi.
Perbaikan kalibrasi menunjukkan bahwa margin aman model penskalaan awal yang terhitung ganda menyebabkan kinerja S4 tampak buruk, bukan rancangan pengendali.
Penelitian terbaru tentang _autoscaling_ yang sadar ketidakpastian @aapa2025 dan horizon perencanaan yang diturunkan dari waktu tunda @adapt2026 memberi arah rancangan untuk perbaikan lebih lanjut.
Studi _benchmark_ @rayscale2026 menunjukkan bahwa _autoscaler_ yang canggih pun sulit mengungguli _baseline_ yang terkalibrasi baik dalam hal biaya.
