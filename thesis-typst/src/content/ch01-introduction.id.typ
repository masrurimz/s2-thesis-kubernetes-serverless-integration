// Chapter 1 — Introduction (Pendahuluan)
// English-first body. Structure restored per advisory.
#import "headings.typ": H


= #H("ch1")

Adopsi komputasi awan meningkat pesat selama sepuluh tahun terakhir. Komputasi awan mengubah cara organisasi men-_deploy_, menskalakan, dan mengelola sistem perangkat lunak. Laporan Flexera 2023 State of the Cloud Report menunjukkan bahwa 87% perusahaan memakai strategi _multi-cloud_. Angka ini mencerminkan pergeseran industri ke arsitektur _cloud-native_. Arsitektur ini menyesuaikan diri dengan permintaan yang berubah dan menjaga biaya operasional tetap terkendali. Pertumbuhan tersebut melahirkan dua paradigma untuk men-_deploy_ aplikasi _cloud-native_, yaitu orkestrasi kontainer dan komputasi _serverless_. Setiap paradigma punya keunggulan. Setiap paradigma juga membawa kompromi. Kompromi ini menjadi penting pada beban kerja yang dinamis seperti di dunia nyata.

Kubernetes adalah standar de facto untuk orkestrasi kontainer. Kubernetes menyediakan _deployment_ otomatis, penskalaan horizontal, dan pemulihan mandiri bagi aplikasi dalam kontainer. Kubernetes mengelola beban kerja di seluruh _cluster_ mesin. Ia memakai konfigurasi deklaratif dan arsitektur _control loop_. Horizontal Pod Autoscaler (HPA) memantau metrik pemakaian sumber daya, seperti pemakaian CPU dan memori. HPA lalu menyesuaikan jumlah _pod_ yang berjalan. Namun, HPA bereaksi terhadap ambang pada metrik yang teramati. HPA tidak mengantisipasi permintaan di masa depan @hypa2023. Sifat reaktif ini menimbulkan jeda antara awal lonjakan beban kerja dan selesainya tindakan penskalaan. Pelanggaran Service Level Objective (SLO) dapat terjadi selama jeda tersebut.

Komputasi _serverless_ menawarkan model yang berbeda. Platformnya antara lain AWS Lambda, Google Cloud Functions, dan kerangka kerja sumber terbuka Knative. Pengembang men-_deploy_ fungsi satu per satu dan tidak mengelola infrastruktur di bawahnya @sadaqat2018serverless @savage2018going @sewak2018winning. Platform _cloud_ menyediakan sumber daya komputasi untuk setiap pemanggilan. Platform menskalakan sampai nol saat tidak ada beban. Dengan demikian perencanaan kapasitas tidak lagi diperlukan. Namun, _serverless_ punya tantangan sendiri. Latensi _cold start_ adalah penundaan saat instans fungsi dimulai dari nol @golec2023cold @yu2020characterizing. Penundaan ini dapat menambah puluhan sampai ratusan milidetik pada waktu respons. Besarnya bergantung pada _runtime_ dan kerumitan fungsi. Selain itu, biaya _serverless_ naik linear mengikuti jumlah pemanggilan. Biaya ini mahal untuk beban kerja yang berlangsung terus-menerus @dehigama2024 @demystifying2025.

Kekuatan dan kelemahan tersebut mendorong pendekatan _hybrid_ @dehigama2024. Pendekatan ini merutekan lalu lintas antara _backend_ Kubernetes dan _serverless_ berdasarkan beban teramati dan kapasitas siap pakai tiap _backend_. Kubernetes menangani lalu lintas dasar. _Pod_ Kubernetes yang selalu aktif memberi latensi rendah yang konsisten dan pemakaian sumber daya yang hemat biaya. _Serverless_ menyerap lonjakan lalu lintas. Penskalaannya yang nyaris seketika mencegah penundaan antrean akibat penyediaan _pod_ Kubernetes. Sistem terdahulu sudah memakai fungsi _serverless_ untuk menutup jeda mulai _virtual machine_ @zhang2019mark @gunasekaran2019spock. Tantangan utamanya adalah memutuskan _kapan_ dan _seberapa banyak_ lalu lintas dirutekan ke tiap _backend_. Penskalaan replika membutuhkan lintasan beban kerja jangka pendek, sehingga prakiraan menjadi masukan bagi keputusan tersebut.

Kendali _hybrid_ yang efektif bergantung pada pengetahuan tentang kondisi saat ini dan lintasan beban kerja jangka pendek. Prakiraan dengan akurasi dan waktu tunggu yang memadai dapat menyiapkan replika Kubernetes sebelum permintaan melampaui kapasitas @yuan2024time @he2020novel. Pengendali perutean tetap memakai beban teramati, kapasitas siap pakai, dan status SLO untuk membagi lalu lintas. Pemisahan ini mempertahankan respons cepat perutean terhadap beban teramati. Prediksi hanya dipakai pada jalur penskalaan replika yang lebih lambat. Prakiraan deret waktu dengan model _deep learning_ menjanjikan di bidang ini @mondal2023toward. Kinerja Gated Recurrent Unit (GRU) sebanding dengan LSTM dalam pemodelan urutan @chung2014empirical, dan prediktor GRU untuk beban Kubernetes dilaporkan akurat sekaligus efisien @mondal2023toward.

Fondasi algoritmanya bertumpu pada algoritma ElaX yang diusulkan oleh @yang2019elax. ElaX menggabungkan prediktor beban kerja, model alokasi sumber daya $R = alpha dot.op x + beta$, dan pengendali _online_ dengan penskalaan berbasis _slack_. LSTM milik ElaX memprediksi 60 titik per menit satu kali setiap jam. Aturan reservasinya mengambil beban kerja prediksi terbesar dalam satu jam ke depan. Tesis ini mengubah faktor keputusan dalam tiga hal. Pertama, GRU menggantikan LSTM dan memprediksi sembilan langkah 15 detik (135 s), yang diperbarui setiap 15 s. Kedua, Algoritma 2 mempertahankan aturan nilai terbesar, tetapi menerapkannya pada _upper envelope_ GRU dan target teramati, lalu menahan (_hold_) target yang dinaikkan selama 90 s. Ketiga, Algoritma 1 menambahkan keputusan yang tidak dibuat ElaX, yaitu pembagian lalu lintas antara Kubernetes dan _serverless_. Tesis ini tidak mengimplementasikan ulang pengendali _online_ berbasis _slack_ maupun penskalaan vertikal ElaX. Algoritma-algoritma khusus tesis ini tidak diatribusikan kepada ElaX sendiri.

Tesis ini meneliti apakah arsitektur _hybrid_ Kubernetes-_serverless_ dapat mengelola skalabilitas elastis di lingkungan _cloud_ yang heterogen. Arsitektur ini menambahkan prediksi beban kerja berbasis GRU untuk penskalaan replika dan pembagian lalu lintas yang sadar kapasitas. Penelitian ini merancang, mengimplementasikan, dan mengevaluasi setiap komponen, yaitu model prediksi, pengendali perutean, dan arsitektur _hybrid_ terpadu. Komponen-komponen ini diuji lewat eksperimen sistematis pada _trace_ beban kerja sintetis dan dunia nyata.

== #H("ch1-problem")

Berdasarkan analisis latar belakang di atas, penelitian ini menjawab rumusan masalah berikut:

1. *Bagaimana merancang prediksi lalu lintas beban kerja untuk aplikasi web memakai GRU?*  
   Pertanyaan ini menyangkut perancangan dan pelatihan model jaringan saraf GRU. Model memprediksi lalu lintas _request_ HTTP dari waktu ke waktu. Pertanyaan ini mencakup pemilihan fitur masukan dan horizon prediksi. Pertanyaan ini juga mencakup data pelatihan sintetis yang menangkap pola beban kerja yang representatif (siklus harian, lonjakan mendadak, kenaikan bertahap). Terakhir, pertanyaan ini mencakup validasi akurasi prediksi terhadap kumpulan data _trace_ HTTP nyata (ClarkNet dan Calgary). Model harus mencapai latensi prediksi yang cocok untuk keputusan perutean waktu nyata (target: inferensi di bawah 50 ms).

2. *Bagaimana merancang dan mengimplementasikan pengambilan keputusan dengan memodifikasi algoritma ElaX untuk penskalaan pada _cluster_ server dan pembagian lalu lintas ke jenis _cluster_ yang berbeda?*  
   Pertanyaan ini membahas modifikasi lapisan prediksi beban kerja dan kendali sumber daya ElaX untuk pembagian lalu lintas _hybrid_. Komponen penskalaan tingkat _cluster_ (Algoritma 2) memakai prakiraan batas atas GRU dalam mode prediktif. Algoritma 1 menetapkan bobot lalu lintas antara _backend_ Kubernetes dan _serverless_ dari beban teramati dan kapasitas replika yang siap. Bobot perutean tidak memakai prakiraan.

3. *Bagaimana mengevaluasi mekanisme ElaX yang dimodifikasi untuk penskalaan otomatis dan pembagian beban di lingkungan terpadu Kubernetes dan _serverless_?*  
   Pertanyaan ini menyangkut metodologi eksperimen untuk mengevaluasi sistem _hybrid_. Evaluasi menilai beberapa dimensi, yaitu akurasi prediksi (RMSE, MAE, MAPE), kinerja sistem (_tail latency_, _throughput_, laju galat), dan efisiensi biaya. Evaluasi membandingkan empat skenario: _baseline_ K8s + HPA, Knative-Only (KPA), _hybrid_-reaktif, dan _hybrid_-prediktif. Skenario-skenario ini memvalidasi kebenaran tiap mekanisme dan perilaku sistem terpadu.
== #H("ch1-hypotheses")

Rumusan masalah dioperasionalkan menjadi tiga hipotesis yang dapat diuji:

  - #strong[H1 (_hybrid_ dibanding murni)]: Arsitektur _hybrid_ Kubernetes-_serverless_ dengan perutean lalu lintas dinamis mengungguli _baseline_ Kubernetes murni (HPA) pada _tail latency_ dan kepatuhan SLO dengan biaya sebanding. Pengujiannya S4 dibanding S1. Hasilnya hanya menunjukkan arah pada n = 1.

  - #strong[H2 (prediktif dibanding reaktif)]: Penambahan prediksi beban kerja berbasis GRU pada pengendali _hybrid_ (penskalaan prediktif) mengungguli pengendali yang sama yang digerakkan beban teramati saja (penskalaan reaktif) pada _tail latency_ dan kepatuhan SLO dengan biaya yang sama. Pengujiannya S4 dibanding S3. Pada 25 pasangan, S4 rata-rata 16,5 ms lebih cepat, tetapi rentang kepercayaan 95% untuk selisih rata-rata mencakup nol, sehingga data tidak menunjukkan keunggulan yang jelas. Satu _batch_ awal tampak signifikan (p = 0,0312, d = -1,26, nilai terkecil yang mungkin pada n = 5). Namun catatan prediktornya tidak lengkap, dan setiap _batch_ ClarkNet sesudahnya tidak menunjukkan perbedaan yang signifikan. Bab 4 memuat catatan lengkapnya.

  - #strong[H3 (kecukupan prediktor)]: Prediktor beban kerja GRU mencapai target akurasi yang didaftarkan sebelumnya (RMSE < 10% dari rentang ternormalisasi, MAE < 5%, inferensi < 50 ms) pada data uji sintetis. Target tercapai pada data sintetis dengan protokol bebas kebocoran data (RMSE 5,2% dari rata-rata, MAE 4,1%). Target tidak tercapai pada wilayah _holdout_ dari _trace_ penerapan nyata (RMSE 39,6% dari rata-rata), tempat jaringan ini setara dengan autoregresi linear pada jendela masukan yang sama. Pencarian representasi dengan dua belas variasi di bawah protokol _fold_ bebas kebocoran data tidak menemukan varian yang mengalahkan model linear. Kesimpulan yang diungkapkan adalah prediktor titik yang diterapkan seharusnya autoregresi linear.


== #H("ch1-objectives")

Tujuan penelitian ini adalah:

1. *Merancang dan mengimplementasikan model prediksi beban kerja berbasis GRU* yang mampu memprakirakan pola lalu lintas HTTP untuk keputusan kendali waktu nyata. Model yang diterapkan dilatih pada deret ClarkNet per 15 detik dengan pembagian kronologis dan _embargo_. Satu lengan sintetis mewakili bentuk lalu lintas yang umum (harian, lonjakan mendadak, kenaikan bertahap) dan dipelajari terpisah. Validasi memakai kumpulan data _trace_ HTTP nyata (ClarkNet dan Calgary). Akurasi target adalah RMSE di bawah 10% dari rentang lalu lintas ternormalisasi pada data uji sintetis, dengan latensi inferensi di bawah 50 ms.

2. *Mengembangkan algoritma ElaX yang dimodifikasi* yang memadukan prediksi beban kerja dengan kendali _hybrid_ yang sadar SLO. Rinciannya: Algoritma 2 (Pengendali _Cluster_) memakai prakiraan batas atas GRU untuk penskalaan replika Kubernetes dalam mode prediktif. Algoritma ini mengambil yang lebih besar antara target replika teramati dan target replika prakiraan. Algoritma 1 (Pengendali Perutean) membagi lalu lintas berdasarkan beban teramati dan kapasitas replika yang siap. Suku pacing SLO-nya merupakan bagian dari rancangan, tetapi tidak aktif pada satu pun _run_ yang dilaporkan. Algoritma 2 memakai R = α·x + β.

3. *Mengevaluasi sistem _hybrid_* lewat eksperimen sistematis yang mencakup akurasi model prediksi, validasi mekanisme, perbandingan multiskenario (S1–S4), dan penilaian jujur atas keterbatasan eksperimen.

== #H("ch1-benefits")

- *Manfaat akademis:* menyumbang pengetahuan tentang _hybrid cloud_, metodologi yang dapat direproduksi, dan perluasan ElaX.

- *Manfaat praktis:* cetak biru arsitektur yang berfungsi, validasi latensi GRU untuk waktu nyata, dan data empiris tentang kompromi yang terjadi.

== #H("ch1-contribution")

1. Arsitektur kendali terpadu yang mengoordinasikan penskalaan replika Kubernetes (Algoritma 2) dan pembagian lalu lintas yang sadar kapasitas (Algoritma 1) antara Kubernetes dan layanan _serverless_ Knative, dengan SLO p99 200 ms.

2. Perluasan keputusan penskalaan ElaX dengan prakiraan GRU multilangkah. GRU menggantikan LSTM milik ElaX, memprakirakan sembilan langkah 15 detik (135 s), dan diperbarui pada setiap siklus kendali. Algoritma 2 mengambil yang lebih besar antara target replika teramati dan target replika prakiraan (_upper envelope_), lalu menahan target yang dinaikkan selama 90 s. Perutean tidak memakai prakiraan. GRU dilatih dan dievaluasi dengan protokol kronologis bebas kebocoran data. Hasilnya RMSE 5,2% pada lengan sintetis, 39,6% pada _trace_ nyata _holdout_, dan setara dengan autoregresi linear.

3. Evaluasi mekanisme _hybrid_-prediktif (S4) terhadap Kubernetes saja (HPA, S1), _serverless_ saja (Knative KPA, S2), dan _hybrid_-reaktif (S3), dengan gerbang validitas pada setiap _run_ dan catatan beban _host_ untuk setiap _run_.

== #H("ch1-constraints")

- *Platform:* K3s + Knative + Kourier + HAProxy.

- *Prediksi:* hanya GRU. Prediksi menggerakkan penskalaan replika Algoritma 2, sedangkan perutean Algoritma 1 memakai beban teramati dan kapasitas.

- *Pelatihan:* artefak yang diterapkan dilatih pada deret ClarkNet per 15 detik dengan pembagian kronologis dan _embargo_. Lengan sintetis dipelajari terpisah. Validasi pada ClarkNet/Calgary.

- *Metrik:* p99, _throughput_, galat, dan proksi biaya.

- *SLO:* p99 200 ms.

- *Lingkungan:* k3d multi-_node_ (satu atau dua _node_ beban kerja dengan batas CPU, bergantung pada _bundle_, dengan _node_ dinamis pada diagnostik beban tinggi).

- *Lalu lintas:* _request_-respons HTTP.

== #H("ch1-systematics")

1. Bab 1: Pendahuluan (bab ini).

2. Bab 2: Tinjauan Pustaka.

3. Bab 3: Metodologi.

4. Bab 4: Hasil dan Pembahasan.

5. Bab 5: Kesimpulan dan Saran.
