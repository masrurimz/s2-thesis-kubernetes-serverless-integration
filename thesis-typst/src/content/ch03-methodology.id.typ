#import "ch03-figures.typ": *
#import "headings.typ": H, cap

// ---------------------------------------------------------------------------
// Algorithm block — matches the proposal docx style: a bordered box with a
// bold "Algorithm N: Title" heading, a bold Input/Parameters preamble, and
// numbered steps (1:, 2:, ...) with bold control-flow keywords and `<-`
// assignment. An algorithm is NOT a Gambar figure.
// ---------------------------------------------------------------------------
#let algo(title, head, steps) = block(
  stroke: 0.7pt + rgb("#5a6b80"),
  inset: (x: 12pt, y: 10pt),
  radius: 3pt,
  breakable: true,
)[
  #align(center, text(size: 11pt)[#title])
  #v(5pt)
  #head
  #v(4pt)
  #for (n, b) in steps [
    #grid(
      columns: (2.6em, 1fr),
      column-gutter: 0.5em,
      align(right)[#n:],
      b,
    )
  ]
]

= #H("ch3")

Bab ini menjelaskan metodologi yang dipakai untuk menjawab pertanyaan penelitian dan mencapai tujuan penelitian. Isinya meliputi alur penelitian, pengumpulan data, arsitektur sistem, implementasi model prediksi dan pengendali _online_, serta rencana evaluasi. Rencana evaluasi memuat skenario eksperimen, metrik, dan ancaman terhadap validitas.

== #H("ch3-flow")

Penelitian ini mengikuti metodologi enam fase. Fase-fase itu bergerak dari landasan teori ke perancangan sistem, implementasi, lalu evaluasi eksperimen.

Studi Literatur mengkaji arsitektur komputasi awan, metode prediksi beban kerja, dan algoritma penskalaan elastis. Fase ini membangun landasan teori dan menunjukkan celah penelitian. Pengumpulan Data membangkitkan pola beban kerja sintetis untuk melatih model GRU. Fase ini juga menambahkan dataset _trace_ HTTP nyata, yaitu ClarkNet @clarknet dan Calgary @calgary, untuk perbandingan _baseline_ dan validasi. Perancangan Metode menetapkan arsitektur _hybrid_ Kubernetes-_serverless_, algoritma perutean dan penskalaan, serta kerangka keputusan berbasis SLO. Implementasi membangun server prediksi GRU dan pengendali perutean (Algoritma 1). Fase ini juga membangun pengendali _cluster_ terintegrasi (Algoritma 2) yang menskalakan replika Kubernetes secara nyata, infrastruktur pemantauan, dan lapisan perutean lalu lintas. Evaluasi menjalankan eksperimen sistematis pada empat skenario penerapan. Evaluasi ini mencakup validasi mekanisme (Fase A1), perbandingan berulang berbasis _trace_ dengan _replay_ ClarkNet (Fase B), validasi _burst_ dinamis (Fase C), dan analisis statistik. Penulisan Laporan mendokumentasikan temuan dengan klaim yang selaras dengan bukti. Klaim ini membedakan mekanisme yang tervalidasi dari klaim keunggulan yang belum terbukti.

Setiap fase menghasilkan artefak untuk fase berikutnya. Studi literatur menjadi dasar perancangan sistem. Data yang terkumpul melatih model prediksi. Sistem yang sudah dibangun menjalani evaluasi eksperimen. Hasil evaluasi menjadi dasar kesimpulan tesis. Alurnya berjenjang dan tidak sepenuhnya linear. Jika hasil evaluasi belum memuaskan, pekerjaan kembali ke perancangan metode untuk direvisi sebelum kesimpulan ditarik.

#figure(
  align(center, fig-research-flow()),
  caption: [Alur metodologi penelitian],
) <fig:research-flow>

== #H("ch3-data")

Model prediksi GRU memerlukan data deret waktu beban kerja untuk pelatihan dan validasi. Penelitian ini memakai dua sumber data, yaitu pola beban kerja sintetis dan dataset _trace_ HTTP nyata. Penggunaan data ini perlu dibedakan menjadi dua. *Data pelatihan* dipakai untuk membangun dan memvalidasi model prediksi. *Beban _replay_* dipakai untuk menyusun beban kerja eksperimen. Keduanya bukan artefak yang sama.

=== #H("ch3-training")

Dua sumber data dipakai, dan masing-masing dinilai sebagai jalur terpisah. Jalur utama adalah _trace_ penerapan itu sendiri. ClarkNet disampel ulang ke interval 15 detik dan dikalikan dengan faktor _replay_ (33). Dengan begitu model dilatih pada amplitudo yang kelak dilayaninya. Penelitian ini membagi _trace_ secara kronologis menjadi bagian pelatihan, validasi, dan uji. _Embargo_ sebesar `sequence_length + horizon - 1` sampel pada setiap batas mencegah jendela masukan atau target melintasi batas itu. Tidak ada jendela pelatihan yang tumpang tindih dengan jendela validasi atau uji. Statistik normalisasi hanya dihitung dari bagian pelatihan. Penelitian ini memilih hiperparameter dan anggaran _epoch_ pelatihan pada bagian validasi. Model lalu dilatih ulang pada bagian pelatihan dan validasi dengan anggaran yang sudah dibekukan itu. Bagian uji dinilai satu kali untuk setiap _seed_. Jendela _replay_ yang dijelaskan di bawah berada di dalam bagian uji. Karena itu model tidak pernah dilatih pada lalu lintas yang kelak dilayaninya. Jalur kedua adalah pola beban kerja sintetis. Pola ini mewakili bentuk lalu lintas yang umum, yaitu siklus harian, _burst_ acak, dan kenaikan bertahap. Pola dibangkitkan pada resolusi 1 detik dan ditahan di sepanjang interval 15 detik. Jalur ini dipertahankan karena target akurasi yang ditetapkan sebelumnya didefinisikan pada data sintetis. Jalur ini dinilai dengan protokol yang sama pada horizon yang sama. Agregasi _trace_ nyata pada interval 1 menit, 5 menit, dan 10 menit yang dijelaskan pada _run_ sebelumnya termasuk protokol yang sudah digantikan. Calgary diarsipkan karena terlalu jarang untuk tugas 15 detik.

=== #H("ch3-replay")

Beban eksperimen adalah satu jendela sampel dari _trace_ ClarkNet, terpisah dari data pelatihan. Log ClarkNet dan Calgary adalah _trace_ kontinu selama beberapa bulan. Memutar ulang seluruh _trace_ tidak mungkin dilakukan pada _testbed_. Eksperimen ini karena itu memilih satu jendela beban variabel yang representatif, yaitu 1995-09-02 04:35:30 sampai 04:55:00 UTC. Jendela ini memiliki varians tinggi (koefisien variasi 0,468), dengan kenaikan dan lonjakan, bukan dataran datar. Jendela ini memberi ruang bagi keputusan kontrol reaktif maupun prediktif. Jendela dikodekan sebagai profil _stage_ k6, yaitu 40 _stage_ berdurasi 30 detik, total 1.200 detik (~20 menit). Lajunya 22 sampai 164 RPS dengan rata-rata 73 RPS. Rata-rata mentah 2,22 RPS dikalikan faktor 33 agar mencapai rentang beban _testbed_ yang relevan bagi penskalaan. Fase B memutar ulang profil ini melalui _executor_ ramping-arrival-rate milik k6.

== #H("ch3-arch")

Sistem yang diusulkan memadukan tiga subsistem, yaitu jalur pelatihan _offline_, bidang prediksi dan kontrol _online_, dan infrastruktur eksekusi _hybrid_. Arsitekturnya berlapis dua dan terinspirasi kerangka algoritma ElaX. Peran yang khas tesis ini dinyatakan secara eksplisit. Algoritma 1 mengatur perutean lalu lintas berdasarkan beban teramati, kapasitas replika yang siap, dan status SLO. Algoritma 2 mengelola penskalaan replika Kubernetes berdasarkan beban teramati atau prakiraan batas atas GRU. Kedua algoritma berjalan dalam satu _daemon_ perutean. _Daemon_ menjalankannya dalam _control loop_ 15 detik yang terkoordinasi. Algoritma 1 segera mengalihkan lalu lintas ke _serverless_. Algoritma 2 menskalakan replika Kubernetes untuk memulihkan kapasitas. Setelah itu Algoritma 1 mengembalikan lalu lintas ke Kubernetes.

Infrastruktur eksekusi adalah simulasi penerapan dua platform nyata pada satu _testbed_ fisik. Penerapan produksi akan menjalankan Kubernetes dan _serverless_ sebagai dua platform terkelola yang terpisah (misalnya layanan Kubernetes terkelola di samping platform Knative/_serverless_ terkelola). Mereproduksinya dengan setia membutuhkan dua _cluster_ fisik. Itu akan mempersulit eksperimen _control loop_ 15 detik yang terkendali. Sebagai gantinya, kedua platform berjalan pada satu _cluster_ k3d fisik. Itu adalah satu _host_ yang mengisolasi kedua platform dengan mekanisme di bawah ini.

=== #H("ch3-infra")

HAProxy adalah titik masuk bagi seluruh lalu lintas HTTP. HAProxy membagi _request_ antara _backend_ Kubernetes dan _serverless_ dengan aturan perutean berbobot. HAProxy memperlakukan kedua _backend_ sebagai dua _endpoint upstream_ yang independen, dan memberinya bobot yang dapat diubah saat berjalan. Algoritma 1 mengubah bobot secara dinamis melalui HAProxy Runtime API (antarmuka soket TCP). HAProxy juga membuka _endpoint_ statistik. _Endpoint_ ini menyediakan metrik _throughput_ dan latensi waktu nyata yang dipakai subsistem pemantauan.

K3s (_backend_ Kubernetes) adalah distribusi Kubernetes ringan yang tersertifikasi. Distribusi ini dipasang melalui k3d (k3s-in-Docker). K3s menjalankan beban kerja aplikasi utama sebagai _pod_ yang selalu hangat. Cara ini memberi respons berlatensi rendah yang konsisten untuk lalu lintas dasar. Dalam penelitian ini, K3s adalah kapasitas hangat _baseline_. Penelitian ini menilai keunggulan biaya relatifnya secara empiris pada setiap _run_, bukan sebagai asumsi yang dibuat di awal.

Knative Serving (_backend serverless_) berjalan pada _cluster_ k3d fisik yang sama, tetapi dioperasikan sebagai platform independen. Knative memakai Kourier sebagai _ingress controller_-nya sendiri. Knative menyediakan kemampuan _scale-to-zero_ dan _autoscaling_ cepat untuk lalu lintas _burst_. Saat pengendali perutean mengaktifkan _backend serverless_, Knative mengelola siklus hidup _pod_ secara otomatis. Itu termasuk inisialisasi _cold start_. _Backend serverless_ aktif hanya saat terjadi pelanggaran SLO atau saat model GRU memprediksi lonjakan beban yang segera datang.

Empat mekanisme menjaga isolasi logis antara kedua platform. Pertama, _namespace_ dan instans aplikasi yang terpisah. Beban kerja hangat berjalan sebagai _deployment_ Kubernetes (test-app-warm) dengan Service sendiri, sedangkan beban kerja _serverless_ berjalan sebagai Knative Service. Kedua, jalur _ingress_ yang terpisah. _Backend_ Kubernetes dijangkau melalui NodePort Service sendiri. _Backend serverless_ dijangkau melalui _ingress controller_ milik Knative (Kourier), yang merutekan berdasarkan _header_ Host Knative. Ketiga, _autoscaling_ yang independen. KPA milik Knative menskalakan berdasarkan konkurensi dan dapat menskalakan ke nol. Replika Kubernetes diskalakan oleh HPA (S1) atau oleh Algoritma 2 melalui kubectl (S3/S4). Keempat, siklus hidup yang independen. _Backend serverless_ dapat melakukan _cold start_ dan menskalakan ke nol, sementara _pod_ Kubernetes yang hangat tetap stabil. Kedua platform terisolasi secara logis, dan bidang kontrol tidak bergantung pada platform. Simulasi pada satu _testbed_ ini karena itu mereproduksi perilaku penerapan nyata, tempat Kubernetes dan _serverless_ adalah platform terkelola yang terpisah.

=== #H("ch3-monitoring")

Sistem memakai Prometheus untuk pengumpulan metrik. Sistem juga memakai komponen pemantau SLO untuk pemeriksaan kepatuhan waktu nyata. Prometheus mengambil statistik HAProxy pada interval 1 detik. Prometheus mengumpulkan jumlah _request_, waktu respons, dan status kesehatan _backend_. Pemantau SLO menghitung _tail latency_ persentil ke-99 (p99) dari deret waktu Prometheus. Pemantau ini juga menjaga jendela pelanggaran bergulir untuk mendeteksi pelanggaran SLO yang berkelanjutan.

#figure(
  align(center, scale(90%, reflow: true, fig-control-loop())),
  caption: [Arsitektur sistem hibrida],
) <fig:control-loop>

== #H("ch3-impl")

=== #H("ch3-predictor")

Model prediksi beban kerja memakai jaringan saraf Gated Recurrent Unit (GRU) dengan kepala keluaran multi-horizon langsung. Model menerima jendela masukan berupa jumlah _request_ per interval pada resolusi 15 detik. Model mengeluarkan sembilan langkah 15 detik ke depan (total 135 detik). Keluaran langsung menghilangkan penumpukan galat autoregresif. Arsitektur dan hiperparameter pelatihan tidak ditetapkan manual. Pencarian Tree-structured Parzen Estimator @bergstra2011tpe memilih hiperparameter hanya pada bagian validasi. Pencarian itu mencakup ukuran lapisan tersembunyi, jumlah lapisan rekuren, laju _dropout_, laju pembelajaran, dan panjang jendela masukan. Pencarian memakai _fold_ validasi _expanding-window_ yang membawa _embargo_ yang sama dengan pembagian pelatihan. Pelatihan memakai pengoptimal Adam dengan fungsi kerugian galat kuadrat rata-rata (_Mean Squared Error_) dan ukuran _batch_ 32. Penghentian dini menentukan anggaran _epoch_, yang lalu dibekukan untuk pelatihan ulang pada bagian pelatihan dan validasi. Bab 4 melaporkan konfigurasi terpilih dan akurasinya pada data _holdout_. Penelitian ini menurunkan offset batas atas per horizon sebagai persentil ke-90 dari residual validasi yang positif. Offset ini ditambahkan ke prakiraan titik. Hasilnya adalah _upper envelope_ yang konservatif (`upper_forecasts`), yang langsung mengatasi prediksi yang terlalu rendah saat beban naik.

Horizon 9 langkah yang diperpanjang (135 s) mencakup waktu tunda penyediaan maksimum K3dAutoscaler (120 s) ditambah margin pengaman 15 detik. Ini mengikuti aturan ADAPT bahwa horizon mencakup waktu tunda penyediaan ditambah penyangga pengaman satu langkah @adapt2026, meskipun horizon di sini tetap dan tidak diestimasi secara _online_. Sistem memvalidasi horizon prakiraan saat berjalan melalui _endpoint_ status model. Waktu tunda _boot_ simulasi sebesar 45 sampai 120 detik sesuai dengan waktu _cold start_ terukur pada mesin virtual _cloud_ publik. AWS Linux melakukan _cold start_ dalam 55,9 s dan GCP Linux dalam 124,1 s. _Warm start_ berkisar antara 22 s dan 34 s pada Linux dan Windows @hao2021vmstartup. _Cold start_ GCP Linux sedikit melebihi maksimum simulasi. Dokumentasi Kubernetes Cluster Autoscaler melaporkan 3 sampai 4 menit untuk penyediaan _node_ pada GCE. Angka ini di atas rentang tersebut, sehingga _testbed_ memodelkan _boot_ yang cepat. AutoScale melaporkan waktu penyiapan 30 detik sampai 1 menit untuk mesin virtual yang dibuat lokal, dari pengukurannya sendiri, dan 10 sampai 15 menit untuk yang disediakan _cloud_ @gandhi2012autoscale. Waktu tunda diambil satu kali per pasangan dan diterapkan pada kedua sisi pasangan, sehingga selisih berpasangan tidak memuat waktu _boot_ itu sendiri.

Model terlatih berjalan di server prediksi FastAPI. Server menerima riwayat laju _request_ terbaru sebagai masukan. Server mengembalikan prakiraan titik, prakiraan _upper envelope_, dan skor keyakinan skalar. Skor keyakinan berasal dari galat validasi ternormalisasi model (RMSE relatif terhadap rata-rata data pelatihan), bukan dari varians prediksi. Skor hanya mengambil dua nilai. Nilainya 0,8 bila galat validasi di bawah 15% dari rata-rata, dan 0,6 bila tidak. Algoritma 1 membandingkan skor dengan ambang 0,5 sebelum membaca prakiraan. Kedua nilai lolos, sehingga ambang tidak pernah menghalangi prakiraan. Jalur penskalaan Algoritma 2 tidak memeriksa skor.

=== #H("ch3-alloc")

Model alokasi sumber daya memakai bentuk linear. Dalam model ini, R adalah jumlah replika target. Di sini x adalah intensitas lalu lintas hasil prediksi atau teramati (_request_ per detik). Alpha adalah koefisien sumber daya per _request_ (replika per RPS). Beta adalah suku beban dasar. Nilai yang diterapkan adalah beta = 0, sehingga jumlah replika minimum pada lalu lintas mendekati nol berasal dari min_replicas = 3. Penelitian ini menurunkan alpha dari pengukuran saturasi yang dikalibrasi, yaitu alpha = 1/r_effective, dengan r_effective = r_saturation_per_replica × target_cpu_util. Pada setiap interval kontrol, _daemon_ menghitung jumlah replika target dengan _buffer_ pengaman gamma (umumnya 1,0). Jumlah itu dibatasi pada batas tetap [3, 6] di bawah kalibrasi bawaan. _Bundle_ September menetapkan max_k8s_replicas menjadi 10 melalui penimpaan kalibrasi. _Pod_ beban kerja meminta 300 millicore. _Bundle_ September memusatkan _cluster hybrid_ pada satu agen beban kerja statis yang dibatasi 1,0 CPU. _Batch_ H2 berpasangan memakai penimpaan kalibrasi lokal eksperimen (`max_k8s_replicas = 10`, `prediction_horizon = 9`; lihat catatan penimpaan kalibrasi). Penimpaan ini membuat puncak ClarkNet melampaui kapasitas statis enam _pod_ dan menjalankan _autoscaling_ tingkat _node_. Penimpaan ini sesuai dengan catatan kalibrasi terkonsolidasi.

=== #H("ch3-algo1")

Algoritma 1 menetapkan pembagian lalu lintas antara _backend_ Kubernetes dan _serverless_. Pengendali yang berjalan pada setiap eksperimen S3 dan S4 digerakkan oleh kapasitas (versi V3). _Bundle_ September mencatatnya dalam manifes setiap _run_. _Bundle_ yang lebih awal mencatatnya dalam log _daemon_ setiap _run_ (`controller_decision_v3`). Kubernetes membawa beban dasar sampai kapasitas efektifnya. _Serverless_ hanya membawa _burst_ di atas kapasitas itu. Setiap siklus 15 detik mengikuti empat langkah:

- *Kapasitas.* Kapasitas Kubernetes efektif C adalah jumlah replika yang siap dikali r_effective, yaitu laju efektif per replika. Yang dihitung adalah replika yang siap, bukan replika yang diinginkan.
- *Pembagian.* Bila beban teramati x sama dengan atau di bawah C, bobot _serverless_ adalah 0. Di atas C, bobot _serverless_ adalah porsi _burst_, dibulatkan ke atas: ceil(100 (x - C) / x). Bobot dibatasi maksimum 50. Saat batas itu tercapai, pengendali menandai defisit kapasitas. Bobot berpindah ke target dalam satu siklus, tanpa langkah tetap.
- *_Pacing_.* Suku proporsional-integral menambah bobot _serverless_ bila siklus dengan p99 di atas 200 ms menghabiskan anggaran pelanggaran (1.000 pelanggaran per _run_ 1.200 detik) lebih cepat daripada yang diizinkan. Pengendali menghitung paling banyak satu pelanggaran per siklus 15 detik, sehingga laju pemakaian anggaran tetap di bawah 8% dari jatah. Suku ini tidak pernah menambah bobot pada _run_ yang dilaporkan. Pada diagnostik empat skenario (n = 1), penyesuaian _pacing_ yang tercatat adalah −5 atau −7 poin, yang menurunkan bobot _serverless_. Suku ini karena itu tidak aktif pada hasil yang dilaporkan.
- *Label.* Setiap keputusan membawa label untuk log dan statistik. Kenaikan bobot berlabel PREDICTIVE bila predicted_upper melebihi beban teramati, dan REACTIVE bila tidak. Penurunan bobot berlabel RECOVERY. Tanpa perubahan berlabel MAINTAIN. Label tidak mengubah bobot.

Pada S4 pengendali menurunkan predicted_upper dari prakiraan. Bila beban teramati naik lebih dari 3 RPS per siklus dan melebihi 80% kapasitas, predicted_upper adalah yang lebih besar antara prakiraan dan ekstrapolasi linear sembilan langkah dari beban teramati. predicted_upper hanya menentukan label. Algoritma 2 menentukan jumlah replika dari sinyal prakiraan milik _daemon_ sendiri. Pembagian bobot tidak pernah membaca kedua nilai itu. Pada S3 tidak ada prakiraan, sehingga label selalu REACTIVE, RECOVERY, atau MAINTAIN. Saat _serverless_ pertama kali diaktifkan, pengendali mengirim _request_ pemeriksaan kesehatan ke _endpoint_ Knative. _Request_ itu dimaksudkan memulai _cold start_ sebelum lalu lintas tiba. Pada _batch_ konfirmatori September, _request_ itu mengembalikan HTTP 404 pada setiap _run_, dan tidak ada _run_ yang mencatat _pre-warming_ yang berhasil. _Run_ Juli mencatat _pre-warming_ yang berhasil. Kemungkinan penyebabnya, pemeriksaan itu memakai nama _host_ tetap yang tidak dijawab _cluster_ September, sehingga _pre-warming_ tidak terjadi di sana.

#algo(
  [#text(weight: "bold")[Algoritma 1:] Pengendali Perutean (pembagian berbasis kapasitas)],
  [
    *Input:* p99 (status SLO); x (beban teramati, RPS); n_ready (replika Kubernetes yang siap); forecast = \{predicted_requests, confidence\} (hanya S4); bobot saat ini (k3s, knative), serverless_enabled \
    *Parameter:* r_effective = r_saturation \* target_cpu_util, max_knative = 50, confidence_threshold = 0,5, anggaran pelanggaran = 1.000 siklus per _run_ 1.200 detik, _gain_ PI kp dan ki, siklus = 15 s
  ],
  (
    (1, [*jika* p99 <= 0 *dan* x <= 0 *maka* *kembalikan* MAINTAIN (bobot saat ini)]),
    (2, [predicted_upper #sym.arrow.l 0; C #sym.arrow.l n_ready \* r_effective]),
    (3, [*jika* prakiraan tersedia *dan* confidence >= confidence_threshold *maka*]),
    (4, [#h(1.4em) predicted_upper #sym.arrow.l predicted_requests, yaitu nilai maksimum _upper envelope_ 9 langkah]),
    (4.5, [#h(1.4em) *jika* trend > 3 RPS/langkah *dan* x > 0,8 C *maka* predicted_upper #sym.arrow.l max(predicted_upper, x + 9 \* trend)]),
    (5, [*selesai jika*]),
    (7, [*jika* x <= C *maka* knative #sym.arrow.l 0]),
    (8, [*selain itu* burst #sym.arrow.l ceil(100 \* (x - C) / x); deficit #sym.arrow.l (100 \* (x - C) / x > max_knative); knative #sym.arrow.l min(burst, max_knative)]),
    (9, [*selesai jika*]),
    (10, [knative #sym.arrow.l min(max_knative, knative + burn_adjustment) #h(1em) \{0 dalam anggaran\}]),
    (11, [*jika* knative > knative saat ini *maka* label #sym.arrow.l PREDICTIVE *jika* predicted_upper > x *selain itu* REACTIVE]),
    (12, [*selain itu jika* knative < knative saat ini *maka* label #sym.arrow.l RECOVERY]),
    (13, [*selain itu* *kembalikan* MAINTAIN (bobot saat ini)]),
    (14, [*selesai jika*]),
    (15, [*jika* knative > 0 *dan* *bukan* serverless_enabled *maka* aktifkan + _pre-warm_ Knative]),
    (16, [*kembalikan* label (k3s = 100 - knative, knative)]),
  ),
)

=== #H("ch3-algo2")

Algoritma 2 beroperasi dalam dua mode yang berbagi model kapasitas yang sama. Pada mode reaktif (S3), sinyal penskalaan adalah rata-rata RPS teramati selama 30 detik terakhir. Pada mode prediktif (S4), _daemon_ mengambil sinyal prakiraan, yaitu prakiraan batas atas maksimum selama sembilan langkah yang diskalakan dengan ROUTING_PREDICTIVE_SHRINK (1,0), lalu menghitung target prediktif darinya. _Daemon_ memilih target ini hanya bila nilainya melebihi target teramati secara ketat. Bila tidak, target teramati yang dipakai. Interval _hold_ proaktif (90 detik) mencegah pembatalan dini atas _scale-up_ proaktif selama jendela prakiraan masih aktif. Pada kedua skenario, pengendali perutean V3 merutekan berdasarkan kapasitas replika siap yang teramati. Prakiraan hanya memengaruhi perencanaan replika Kubernetes, bukan pembagian bobot HAProxy. Pemisahan ini menyimpang dari kerangka usulan yang memakai perutean berbasis prediksi. Penyimpangan itu adalah keputusan rancangan yang didorong bukti empiris. Prediksi yang terlalu rendah saat beban naik membuat perutean langsung berbasis prakiraan mengalihkan terlalu banyak lalu lintas ke _serverless_. Penskalaan memiliki tenggang waktu yang cukup untuk memanfaatkan horizon 135 detik.

Faktor keputusan yang diubah penelitian ini adalah sinyal beban x pada R = alpha x + beta. ElaX menetapkan x sebagai beban kerja prediksi terbesar selama satu jam ke depan, yang diperbarui setiap jam. Algoritma 2 mempertahankan aturan nilai terbesar, tetapi menerapkannya pada _upper envelope_ GRU (prakiraan titik ditambah persentil ke-90 residual validasi positif per langkah) selama 135 detik ke depan, yang diperbarui setiap 15 detik. Algoritma ini lalu mengambil yang lebih besar antara R(observed) dan R(upper envelope). Target teramati memakai rata-rata beban teramati selama 30 detik. Algoritma ini juga menahan target yang naik selama 90 detik. Pada S3, x adalah beban teramati. Algoritma 2 hanya menskalakan replika. Algoritma ini tidak mengimplementasikan ulang pengendali umpan balik berbasis _slack_ milik ElaX maupun _scale-up_ vertikalnya.

Pengendali menskalakan dengan menjalankan kubectl scale deployment. Pengendali memilih perintah ini karena sifatnya deterministik dan jejak auditnya jelas. Pemeriksaan keselamatan mencakup masa _cooldown_, pembatasan jumlah replika, histeresis _scale-down_, dan verifikasi kesiapan sebelum lalu lintas kembali ke Kubernetes. Masa _cooldown_ adalah 15 detik untuk _scale-up_ dan 120 detik untuk _scale-down_ pada mode V3. _Scale-down_ juga mensyaratkan p99 di bawah 140 ms dan target yang dibatasi dari bawah pada min_replicas = 3. _Batch_ H2 berpasangan memakai _baseline_ yang sudah disetel, yaitu _cooldown_ 120 detik dengan ambang _scale-down_ 0,75.

#algo(
  [#text(weight: "bold")[Algoritma 2:] Pengendali _Cluster_ (penskalaan replika Kubernetes)],
  [
    *Input:* x_obs (rata-rata RPS teramati, 30 s terakhir); predicted_upper (prakiraan batas atas GRU; hanya S4); c (replika yang diinginkan saat ini), p99 \
    *Parameter:* alpha = 1 / (r_sat \* cpu_util), beta = 0, buffer = 1,0, min_replicas = 3, max_replicas = 6 (10 pada _bundle_ September), scale_down_threshold = 0,75, hold = 90 s, up_cooldown = 15 s, down_cooldown = 120 s
  ],
  (
    (1, [R(x) = clamp(ceil((alpha \* x + beta) \* buffer), min_replicas, max_replicas)]),
    (2, [observed_target #sym.arrow.l R(x_obs)]),
    (3, [target #sym.arrow.l observed_target; proactive #sym.arrow.l *salah*]),
    (4, [*jika* mode prediktif (S4) *dan* prakiraan tersedia *maka*]),
    (5, [#h(1.4em) predictive_target #sym.arrow.l R(predicted_upper)]),
    (6, [#h(1.4em) *jika* predictive_target > observed_target *maka* #h(1em) \{melebihi secara ketat\}]),
    (7, [#h(2.8em) target #sym.arrow.l predictive_target; proactive #sym.arrow.l *benar*]),
    (8, [#h(2.8em) hold_until #sym.arrow.l now + hold]),
    (9, [#h(1.4em) *selain itu jika* now < hold_until *dan* held_target > observed_target *maka*]),
    (10, [#h(2.8em) target #sym.arrow.l held_target; proactive #sym.arrow.l *benar* #h(1em) \{_hold_ proaktif\}]),
    (11, [#h(1.4em) *selesai jika*]),
    (12, [*selesai jika*]),
    (13, [*jika* target > c *maka* action #sym.arrow.l SCALE_UP]),
    (14, [*selain itu jika* target < c \* scale_down_threshold *maka* action #sym.arrow.l SCALE_DOWN]),
    (15, [*selain itu* action #sym.arrow.l MAINTAIN]),
    (16, [*selesai jika*]),
    (17, [*jika* action = SCALE_UP *dan* now - last_up >= up_cooldown *maka*]),
    (18, [#h(1.4em) kubectl scale deployment \-\-replicas=target]),
    (19, [*selain itu jika* action = SCALE_DOWN *dan* now - last_down >= down_cooldown]),
    (20, [#h(1.4em) *dan* p99 < healthy *dan* max(min_replicas, target) < c *maka*]),
    (21, [#h(1.4em) kubectl scale deployment \-\-replicas=max(min_replicas, target)]),
    (22, [*selesai jika*]),
  ),
)

=== #H("ch3-consolidation")

K3dAutoscaler mengimplementasikan konsolidasi _node_ berbasis pemakaian. Ambang pemakaian dan syarat penjadwalan ulangnya mengikuti Kubernetes Cluster Autoscaler @k8sca-faq. Cluster Autoscaler secara bawaan menunggu 10 menit sebelum menghapus _node_ yang tidak diperlukan, dan _testbed_ ini mempersingkat waktu tunggu itu menjadi 90 detik. _Node_ dinamis menjadi kandidat untuk dihapus bila tiga syarat terpenuhi. Pemakaian _request_ CPU-nya di bawah 50% dari kapasitas yang dapat dialokasikan. Semua _pod_ beban kerja dapat dijadwalkan ulang ke _node_ lain. _Node_ itu sudah kurang terpakai selama paling sedikit 90 detik. Perintah kubectl drain mengeluarkan _pod_ sebelum penghapusan. _Cooldown_ 120 detik mencegah penghapusan beruntun. _Scale-down_ tingkat _pod_ memakai _cooldown_ 120 detik dan ambang pemakaian 0,75.

== #H("ch3-evalplan")

=== #H("ch3-scenarios")

Penelitian ini mendefinisikan empat skenario. Skenario itu membandingkan _baseline autoscaling_ bawaan platform dengan bidang kontrol _hybrid_ kustom. Skenario itu juga memisahkan nilai prediksi GRU di dalam arsitektur _hybrid_:

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, left, left),
    [*Skenario*], [*Deskripsi*], [*Autoscaling*], [*GRU*],
    [S1 (K8s + HPA _baseline_)], [100% lalu lintas ke Kubernetes], [_Autoscaling_ bawaan HPA berbasis CPU], [nonaktif],
    [S2 (hanya Knative, KPA)], [100% lalu lintas ke Knative melalui HAProxy], [_Autoscaling_ KPA berbasis konkurensi dengan _scale-to-zero_], [nonaktif],
    [S3 (_hybrid_ reaktif)], [Perutean dinamis K8s ke Knative melalui Algoritma 1], [Penskalaan Algoritma 2 dengan RPS teramati], [nonaktif],
    [S4 (_hybrid_ prediktif)], [Perutean dinamis K8s ke Knative melalui Algoritma 1], [Penskalaan Algoritma 2 dengan prakiraan GRU (prediktif)], [aktif],
  ),
  caption: [Skenario eksperimen],
) <tab:scenarios>

Perbandingan S1 dengan S2 mengevaluasi _baseline_ bawaan platform. Perbandingan S3 dengan S1/S2 mengevaluasi apakah bidang kontrol _hybrid_ reaktif lebih baik daripada salah satu _baseline_ saja. Perbandingan S3 dengan S4 memisahkan nilai prediksi GRU. Keduanya memakai perutean _hybrid_ dan penskalaan Algoritma 2. Keduanya merutekan berdasarkan beban teramati. S4 juga memakai prakiraan batas atas GRU untuk perencanaan replika Kubernetes. Ada satu catatan praktis. Model penskalaan memetakan beban ke replika melalui $ceil(alpha dot.op x dot.op gamma)$ dengan batas bawah tiga replika. Karena itu prakiraan beban sedang (misalnya 62 RPS) dapat menghasilkan target replika yang sama dengan sinyal teramati. Akibatnya jalur prediktif dan reaktif identik secara operasional pada siklus itu. Perbandingan ini karena itu hanya dapat membedakan kedua jalur bila prakiraan menghasilkan target replika yang berbeda dari sinyal teramati. Kondisi ini bergantung pada margin kalibrasi dan dianalisis di Bab 4.

Algoritma ElaX yang asli tidak dievaluasi sebagai skenario tersendiri. ElaX mengendalikan elastisitas di dalam satu platform. ElaX tidak punya lapisan perutean lintas platform, sehingga tidak menyelesaikan masalah perutean _hybrid_ yang diteliti di sini. Tesis ini karena itu memperlakukan ElaX sebagai landasan algoritmik. Kontribusinya dipisahkan melalui ablasi S3 terhadap S4, yang hanya berbeda pada sinyal penskalaan. ADAPT mengevaluasi dengan cara yang serupa. ADAPT membandingkan pengendali proaktifnya dengan _baseline_ HPA reaktif dan mengablasi komponen horizonnya, dalam simulasi @adapt2026.

=== #H("ch3-phases")

Fase A0 memvalidasi infrastruktur dan mekanisme _autoscaler_. Fase A1 memvalidasi mekanisme sistem satu per satu di bawah beban naik bertahap yang terkendali. Fase B menjalankan perbandingan berpasangan yang diimbangi urutannya dengan beban kerja berbasis _trace_ ClarkNet (40 _stage_, masing-masing 30 detik, RPS 22 sampai 164, rata-rata 73). Pada profil _replay_ ini, S1 dan S2 berjalan dengan _autoscaling_ bawaan platform (masing-masing HPA dan KPA). S3 dan S4 menjalankan bidang kontrol kustom (perutean Algoritma 1 ditambah penskalaan Algoritma 2). Keempat skenario menerima beban _replay_ k6 yang identik. _Batch_ berpasangan bergantian urutan skenario antara S3 dan S4. _Batch_ H2 utama memakai 10 pasangan (20 _run_), dan diagnostik empat skenario dengan n = 1 melengkapinya. Replikasi empat skenario menyelesaikan Fase B pada 2026-08-09 (Lampiran D). Replikasi itu menjalankan 4 skenario, masing-masing 5 _run_ (20 _run_ bersih), dan semua gerbang validitas lolos (5/5 per skenario). Fase C menguji sistem dengan profil _burst_ terkendali.

=== #H("ch3-metrics")

Metrik kinerja yang dirasakan pengguna mencakup latensi p50, p95, dan p99, laju galat, dan _throughput_ yang dicapai. Metrik SLO utama adalah latensi p99 dengan ambang 200 ms. Metrik perutean dan bidang kontrol mencakup jumlah perubahan bobot, persentase waktu di _serverless_, laju pemakaian prediksi, dan latensi _control loop_. Metrik penskalaan replika Kubernetes mencakup replika yang diinginkan, replika saat ini, replika yang siap, kejadian dan latensi _scale-up_/_scale-down_, dan indeks osilasi. Metrik sumber daya dan proksi biaya mencakup pemakaian CPU/memori, waktu kapasitas K8s, waktu aktif Knative, dan metrik ternormalisasi biaya (USD/1 juta _request_, USD/1 juta _request_ yang memenuhi SLO).

=== #H("ch3-stats")

Perbandingan S3/S4 berpasangan memakai uji permutasi satu sisi yang ditetapkan sebelumnya pada selisih p99 berpasangan (alpha = 0,05). Ukuran hasil sekunder (p95, pelanggaran SLO, _throughput_, dan laju galat) dikoreksi dengan Bonferroni dan dilaporkan secara deskriptif. Hanya ukuran hasil utama yang boleh diklaim signifikan secara statistik. Replikasi empat skenario (S1, S2, S3, S4, masing-masing n = 5) memakai uji t Welch dan uji Mann-Whitney U pada latensi p99 per skenario. Replikasi ini memakai alpha = 0,05 yang sama. Perbandingan ini dua sisi dan dilaporkan sebagai bukti tingkat replikasi, bukan klaim yang ditetapkan sebelumnya.

=== #H("ch3-threats")

Evaluasi eksperimen memiliki beberapa ancaman yang terdokumentasi. _Testbed_ k3d multi-_node_ memakai satu atau dua _node_ beban kerja yang dibatasi CPU, tergantung _bundle_, dan perutean yang berada di dekat _localhost_. _Testbed_ ini tidak mereproduksi latensi jaringan produksi atau persaingan sumber daya jaringan. _Trace_ historis (1994-1995) mungkin tidak sesuai dengan semantik aplikasi modern. Fidelitas _replay_ mempertahankan intensitas _request_, tetapi tidak mempertahankan waktu jeda pengguna (_think time_) maupun perilaku _cache_. Batasan aplikasi _single-thread_ (GOMAXPROCS=1, /fib?n=33) menghasilkan saturasi yang dapat direproduksi. Batasan ini tidak mewakili aplikasi web multi-_thread_ yang umum. Pembatasan kapasitas _node_ secara buatan memaksa pemicu _autoscaler_ terjadi pada beban lebih rendah daripada produksi. Kedua platform memakai _node_ fisik yang sama, sehingga bersaing untuk kapasitas CPU yang sama. Penerapan terpisah yang nyata tidak akan berbagi kapasitas seperti ini. Hasil terukur karena itu adalah batas konservatif yang memvalidasi mekanisme, bukan klaim kapasitas produksi. Semua hasil sebaiknya ditafsirkan sebagai validasi mekanisme, bukan jaminan kinerja yang representatif bagi produksi.
