#import "ch02-figures.typ": *
#import "headings.typ": H, cap

= #H("ch2")

Bab ini meninjau landasan teori dan penelitian terdahulu yang mendukung penelitian ini. Bab ini membahas model layanan komputasi awan, orkestrasi kontainer dengan Kubernetes, dan komputasi _serverless_ beserta masalah _cold start_. Bab ini juga membahas pola integrasi _hybrid_, metrik kinerja aplikasi _cloud_, prediksi beban kerja dengan jaringan saraf rekuren, dan strategi penskalaan Kubernetes, termasuk algoritma ElaX yang dikembangkan oleh penelitian ini.

== #H("ch2-cloud")

NIST mendefinisikan komputasi awan sebagai "model yang memungkinkan akses jaringan yang ada di mana-mana, nyaman, dan sesuai permintaan ke sekumpulan sumber daya komputasi yang dapat dikonfigurasi dan dipakai bersama" @mell2011nist. Sumber daya itu berupa jaringan, server, penyimpanan, aplikasi, dan layanan. Pengguna dapat memperoleh dan mengembalikannya dengan cepat, dengan sedikit kerja pengelolaan dan sedikit kontak dengan penyedia. Model ini kini menjadi cara utama untuk menjalankan sistem perangkat lunak berskala besar. Dalam survei industri pada 2023, 87% responden melaporkan pemakaian _multi-cloud_ @flexera2023.

Layanan komputasi awan terbagi menjadi empat model. Setiap model menetapkan batas tanggung jawab yang berbeda antara penyedia dan pengguna:

- IaaS (_Infrastructure as a Service_) menyediakan komputasi, penyimpanan, dan jaringan mentah. Pengguna mengelola aplikasi, data, _runtime_, _middleware_, dan sistem operasi. Penyedia mengelola virtualisasi, server, penyimpanan, dan jaringan.

- PaaS (_Platform as a Service_) menambahkan _runtime_ dan _middleware_ yang dikelola penyedia. Pengguna hanya mengelola aplikasi dan data.

- SaaS (_Software as a Service_) menyediakan aplikasi yang lengkap. Pengguna hanya mengelola datanya.

- FaaS (_Function as a Service_) adalah model yang paling terperinci. Pengembang menerapkan fungsi tunggal dan menyerahkan pengoperasian infrastruktur di bawahnya kepada penyedia _cloud_ @wurster2018modeling.

Penelitian ini berada di antara IaaS/PaaS (orkestrasi kontainer Kubernetes) dan FaaS (fungsi _serverless_ Knative).

Model _hybrid cloud_ relevan bagi penelitian ini. Arsitektur yang diusulkan merutekan lalu lintas antara _cluster_ Kubernetes dan platform _serverless_. _Cluster_ Kubernetes setara dengan lingkungan privat yang dikelola sendiri. Platform _serverless_ setara dengan layanan publik yang elastis. Sistem memilih _backend_ yang tepat berdasarkan kinerja saat ini dan kondisi beban kerja yang diprediksi.

== #H("ch2-containers")

Kontainer adalah paket eksekusi yang ringan dan berdiri sendiri. Kontainer mengemas bagian-bagian aplikasi bersama _middleware_, biner, dan pustaka yang diperlukan untuk menjalankannya @pahl2019cloud. Mesin virtual menjalankan sistem operasi tamu yang utuh. Sebaliknya, kontainer berjalan sebagai proses di atas sistem operasi _host_ yang dipakai bersama. Sistem operasi itu memisahkan kontainer satu dari yang lain dengan mekanisme kernel seperti _namespaces_ dan _cgroups_ @pahl2019cloud. Perbedaan rancangan ini memberi tiga keuntungan praktis. Waktu mulai turun dari menit ke detik. Beban sumber daya turun menjadi sebatas jejak kernel bersama. Kepadatan penerapan naik dari puluhan menjadi ratusan instans per _host_.

Kubernetes (K8s) adalah platform orkestrasi kontainer sumber terbuka. Google merancangnya dari pengalaman lebih dari satu dekade dengan sistem manajemen _cluster_ Borg dan Omega. Kubernetes mengotomatiskan penerapan, penskalaan, dan pengelolaan aplikasi berkontainer di banyak mesin. Kubernetes memakai konfigurasi deklaratif dan _control loop_ rekonsiliasi.

Arsitekturnya memiliki dua bidang. _Control Plane_ mengelola keadaan seluruh _cluster_ dan keputusan penjadwalan. _Control Plane_ memakai empat komponen. API Server adalah entitas manajemen pusat dan membuka API REST Kubernetes. Scheduler memilih _node_ yang tepat untuk _pod_ baru berdasarkan kebutuhan sumber daya dan kebijakan batasan. Controller Manager menjalankan proses rekonsiliasi. Proses ini mengamati keadaan _cluster_ dan mengarahkannya ke keadaan yang diinginkan. etcd adalah basis data kunci-nilai terdistribusi. etcd menyimpan seluruh keadaan _cluster_ dan menjaga salinannya tetap konsisten dan tersedia.

_Data Plane_ terdiri dari _Worker Node_. _Node_ ini menjalankan beban kerja aplikasi. Setiap _node_ menjalankan Kubelet dan Kube-proxy. Kubelet adalah agen yang memastikan kontainer dalam spesifikasi _pod_ berjalan dan tetap sehat. Kube-proxy adalah _proxy_ jaringan. Kube-proxy menjaga aturan yang memungkinkan komunikasi ke _pod_. K3s adalah distribusi Kubernetes ringan yang dipakai dalam penelitian ini. Distribusi ini tetap kompatibel penuh dengan API Kubernetes dan menurunkan kebutuhan memori menjadi sekitar 512 MB RAM. Hal ini membuatnya cocok untuk lingkungan dengan sumber daya terbatas.

#figure(
  fig-k8s-architecture(),
  caption: [Arsitektur _cluster_ Kubernetes @kubernetes2024components],
) <fig:k8s-architecture>

== #H("ch2-serverless")

Komputasi _serverless_ adalah model eksekusi _cloud_. Penyedia mengambil alih penyediaan, penskalaan, dan pemeliharaan server @sadaqat2018serverless. Server tetap ada meskipun namanya demikian. Abstraksi ini mengambil pengelolaan server dari tanggung jawab pengembang @savage2018going. Ciri utamanya adalah eksekusi berbasis peristiwa, pemrosesan tanpa status, _autoscaling_ otomatis, dan harga bayar sesuai pemakaian. Fungsi berjalan saat peristiwa memicunya, tidak terus-menerus. Tidak ada status yang bertahan di antara pemanggilan. Penskalaan berjalan dari nol sampai ribuan menurut laju peristiwa. Tagihan hanya mencakup sumber daya yang dipakai fungsi selama berjalan. AWS Lambda, misalnya, membulatkan durasi ke atas sampai 1 ms terdekat @mampage2022holistic.

Platform komersial utama antara lain AWS Lambda, Google Cloud Functions, dan Azure Functions. Di ekosistem sumber terbuka, Knative menyediakan _runtime serverless_ asli Kubernetes. OpenFaaS menawarkan model penerapan fungsi yang lebih sederhana. Penelitian ini memakai Knative Serving sebagai _backend serverless_. Knative berjalan di _cluster_ Kubernetes yang sama. Hal ini memungkinkan perbandingan yang adil dan perutean lalu lintas yang sederhana melalui _namespace_ jaringan bersama.

#figure(
  fig-serverless-architecture(),
  caption: [Arsitektur komputasi _serverless_ @mampage2022holistic],
) <fig:serverless-architecture>

Gambar berikut menunjukkan model layanan _cloud_ dan pembagian tanggung jawabnya @kavis2014.

#figure(
  fig-cloud-services(),
  caption: [Layanan _cloud_ dan pembagian tanggung jawab @kavis2014],
) <fig:cloud-services>

Masalah _cold start_ adalah salah satu tantangan kinerja terpenting dalam komputasi _serverless_ @golec2023cold. _Cold start_ terjadi saat pemanggilan fungsi tiba tetapi tidak ada instans fungsi hangat (sudah diinisialisasi) yang dapat menanganinya. Platform kemudian harus menjalankan beberapa langkah inisialisasi berurutan. Langkah itu adalah penyediaan kontainer, inisialisasi _runtime_, pemuatan kode fungsi, dan inisialisasi dependensi. Latensi _cold start_ yang umum berkisar 100 sampai 500 ms untuk AWS Lambda, 200 sampai 600 ms untuk Google Cloud Functions, dan 1.000 sampai 3.000 ms untuk Knative di Kubernetes. Knative harus menyediakan _pod_ Kubernetes yang utuh, bukan _sandbox_ kontainer yang ringan. #cite(<beni2021reducing>, form: "prose") menunjukkan bahwa berbagi pustaka antarkontainer, membuat kontainer jaringan lebih dulu, dan membuat kontainer secara paralel mengurangi waktu tunda mulai saat penskalaan elastis di Kubernetes. Temuan ini mendorong pendekatan _pre-warming_ prediktif yang dipakai dalam penelitian ini. _Benchmark serverless_ mengukur latensi _cold start_ @yu2020characterizing @sebs2020, dan SeBS menunjukkan bahwa granularitas penagihan membuat waktu dan memori yang tidak terpakai ikut ditagih @sebs2020. Prakiraan telah dipakai untuk memulai fungsi _serverless_ sebelum _request_ tiba @jegannathan2022time, dan _reinforcement learning_ dipakai untuk memutuskan berapa lama fungsi dijaga tetap hangat @vahidinia2023mitigating.

Penalti _cold start_ besar bagi aplikasi yang peka terhadap latensi dengan target SLO yang ketat. Jika latensi p99 harus tetap di bawah 200 ms, satu pemanggilan _cold start_ dapat menyebabkan pelanggaran SLO. Kompromi antara elastisitas _serverless_ dan latensi _cold start_ ini mendorong arsitektur _hybrid_ yang diusulkan dalam tesis ini. Kubernetes menyediakan _pod_ yang selalu hangat untuk lalu lintas _baseline_. _Serverless_ menampung kelebihan lalu lintas, tetapi hanya jika prediksi menunjukkan waktu tunggu yang cukup untuk _warm-up_.

== #H("ch2-integration")

Kubernetes dan _serverless_ memiliki kelebihan dan kekurangan yang saling melengkapi. Kubernetes memberi latensi rendah yang konsisten dan hemat biaya untuk beban yang berkelanjutan, tetapi memerlukan perencanaan kapasitas. _Serverless_ memberi elastisitas seketika dan biaya nol saat menganggur, tetapi memiliki penalti _cold start_. Perbedaan ini mendorong penggabungan keduanya menjadi arsitektur _hybrid_ @dehigama2024. #cite(<dehigama2024>, form: "prose") menunjukkan bahwa penerapan _hybrid_ VM-_serverless_ dapat memangkas total biaya 7,5% dibandingkan pengaturan hanya VM yang disediakan secara optimal. Penerapan itu juga menjaga kepatuhan SLO. PulseNet @pulsenet2025 mengusulkan _control plane_ dua jalur. _Control plane_ ini memisahkan lalu lintas yang berkelanjutan dari lalu lintas berlebih. Kinerjanya 35% lebih baik daripada Dirigent, sebuah sistem hanya-FaaS, pada biaya yang sama. MArk menyediakan _virtual machine_ berdasarkan prakiraan beban dan melayani lonjakan lewat AWS Lambda @zhang2019mark. Spock memakai fungsi _serverless_ untuk menutup jeda _scale-out_ pada _virtual machine_ @gunasekaran2019spock.

Penggabungan Kubernetes dan _serverless_ memberi empat keuntungan utama:

- Optimasi biaya: Kubernetes melayani beban _baseline_ yang dapat diprediksi dan menghindari biaya per pemanggilan _serverless_; _serverless_ melayani lalu lintas _burst_ dan menghindari penyediaan berlebih.

- Kinerja: _pod_ Kubernetes yang hangat menghindari latensi _cold start_ untuk sebagian besar _request_; _serverless_ menangani kelebihan lalu lintas.

- Fleksibilitas: setiap komponen beban kerja berjalan di platform yang paling sesuai.

- Keandalan: perutean lintas platform menyediakan cadangan.

LA-IMR @laimr2026 menunjukkan penurunan latensi P99 hingga 20,7% di lingkungan _hybrid cloud-edge_. Sistem ini memakai perutean prediktif di memori dan _autoscaling_ proaktif.

Literatur menjelaskan dua pola utama. Pola Overflow Model merutekan semua lalu lintas ke Kubernetes sampai kejenuhan muncul pada metrik CPU, memori, atau latensi. Setelah itu, kelebihan lalu lintas mengalir ke _backend serverless_. Pola ini reaktif. Pola ini bereaksi terhadap kejenuhan setelah kejenuhan terjadi. Jeda antara deteksi dan tersedianya kapasitas _serverless_ menciptakan sebuah jendela. Pelanggaran SLO dapat terjadi di jendela ini. Pola Predictive Scaling memakai model prakiraan untuk mengantisipasi permintaan. Pola ini menyesuaikan kapasitas Kubernetes sebelum batas tercapai. Pola ini mendorong arsitektur yang diusulkan dalam penelitian ini. Pengendali perutean arsitektur itu tetap memakai beban teramati dan kapasitas yang siap. Dalam simulasi, AAPA @aapa2025 menurunkan pelanggaran SLO dibandingkan HPA Kubernetes dengan menskalakan per arketipe beban kerja dan melebarkan marginnya saat keyakinan pengklasifikasi rendah.

Penelitian terdahulu mencakup sebagian dari masalah ini. @table-prior-work menunjukkan apa yang dicakup setiap penelitian dan apa yang tidak.

#figure(
  kind: table,
  {
    table(
    columns: (auto, auto, auto, auto),
    align: (left, left, left, left),
    [*Jalur*], [*Karya representatif*], [*Dicakup*], [*Tidak dicakup*],
    [Biaya penerapan _hybrid_], [@dehigama2024], [Perbandingan biaya VM-_serverless_], [Tidak ada perutean lalu lintas yang dinamis],
    [Kendali _serverless_ dua jalur], [@pulsenet2025], [Perutean _overflow_ dan prediksi tren di Knative], [Tidak ada perutean Kubernetes-FaaS],
    [_Autoscaling_ prediktif dengan keyakinan], [@aapa2025], [Penskalaan per arketipe dengan margin berbasis keyakinan], [Satu platform, tidak ada perutean lintas platform],
    [Perutean _cloud-edge_ prediktif], [@laimr2026], [Perutean prediktif dan _autoscaling_ proaktif], [Penskalaan dan perutean tidak dipisahkan],
    [Prediksi GRU untuk Kubernetes], [@mondal2023toward], [Prakiraan pemakaian CPU _cluster_ dengan GRU], [Tidak ada perutean, tidak ada _backend serverless_],
    [Prediksi dan alokasi terpadu], [@yang2019elax], [Prediktor, model sumber daya, pengendali _online_], [Satu platform, tidak ada perutean yang sadar SLO],
  )
  },
  caption: [Sebagian penelitian terdahulu pada setiap jalur penelitian],
) <table-prior-work>

Penelitian terdahulu mencakup setiap jalur. Tidak ada satu jalur pun yang baru. Kontribusi penelitian ini menggabungkan tiga bagian. Perutean lintas platform memindahkan lalu lintas antara Kubernetes dan platform _serverless_ yang independen. Prediksi GRU menggerakkan penskalaan replika melalui perluasan keputusan penskalaan nilai terbesar milik ElaX. Perutean membaca beban teramati dan kapasitas yang siap, dan tidak membaca prakiraan. Belum ada sistem terdahulu yang menggabungkan ketiga bagian ini. Dibangun di atas model alokasi sumber daya ElaX, gabungan ini menutup celah penelitian.

== #H("ch2-metrics")

Mengukur dan mengelola kinerja aplikasi _cloud_ memerlukan kerangka metrik, target, dan pendekatan pemantauan yang terstruktur.

_Service Level Agreement_ (SLA) adalah kontrak antara penyedia layanan dan pengguna. SLA menetapkan tingkat kinerja yang diharapkan dan akibat jika tingkat itu tidak terpenuhi. _Service Level Indicator_ (SLI) adalah ukuran kuantitatif dari satu aspek layanan, seperti latensi _request_, laju galat, atau _throughput_. _Service Level Objective_ (SLO) adalah nilai atau rentang target untuk sebuah SLI, seperti "latensi p99 di bawah 200 ms." SLA dinyatakan melalui SLI dan SLO.

Penelitian ini memakai latensi p99 (persentil ke-99) sebagai indikator SLO utama. Pilihan ini mengikuti prinsip _tail-at-scale_ @dean2013tail. Dalam sistem terdistribusi, komponen paling lambat di jalur _request_ menentukan latensi keseluruhan yang dirasakan pengguna. Karena itu, mengoptimalkan _tail latency_, bukan latensi rata-rata atau median, penting untuk menjaga pengalaman pengguna yang konsisten.

Waktu respons terbagi menjadi tiga komponen. Latensi jaringan mencakup beban perutean dan pemilihan _backend_. Waktu antre adalah waktu tunggu di antrean _request_ Kubernetes atau _serverless_. Waktu pemrosesan adalah komputasi aplikasi yang sebenarnya. Latensi _cold start_ di _serverless_ menambah waktu pemrosesan pada pemanggilan pertama. _Tail latency_ adalah ujung atas distribusi waktu respons, yang dilaporkan sebagai persentil tinggi seperti p99 atau p99.9 @dean2013tail. _Tail latency_ menangkap penurunan kinerja sebelum penurunan itu memengaruhi sebagian besar pengguna.

Skalabilitas adalah kemampuan sistem menangani beban kerja yang lebih besar dengan menambah sumber daya. Elastisitas menambahkan kemampuan memperoleh dan melepas sumber daya secara otomatis saat permintaan berubah. Kubernetes mencapai elastisitas melalui _Horizontal Pod Autoscaler_ (HPA). HPA bereaksi terhadap pemakaian CPU atau metrik khusus yang teramati. Platform _serverless_ menawarkan elastisitas bawaan. Platform ini menyediakan instans fungsi pada setiap pemanggilan.

== #H("ch2-prediction")

Prediksi beban kerja mengubah penskalaan reaktif menjadi penskalaan proaktif. Penskalaan reaktif menanggapi metrik saat ini. Penskalaan proaktif bersiap untuk permintaan yang diantisipasi. Jaringan saraf rekuren memprakirakan pemakaian CPU pada sebuah _trace cluster_ sedikit lebih akurat daripada ARIMA @mondal2023toward. Penskala berbasis prakiraan untuk Kubernetes memakai model deret waktu atas pemakaian sumber daya atau laju _request_ @mondal2023toward @yuan2024time.

LSTM (_Long Short-Term Memory_) adalah arsitektur jaringan saraf rekuren. Hochreiter dan Schmidhuber memperkenalkannya. LSTM mempelajari ketergantungan jangka panjang dalam data berurutan. Inovasi utamanya adalah _cell state_. _Cell state_ menyimpan informasi dan diatur oleh tiga gerbang, yaitu _forget gate_, _input gate_, dan _output gate_. LSTM adalah metode yang umum dalam studi prediksi beban untuk _autoscaling_ @mondal2023toward. Namun, arsitektur tiga gerbangnya menimbulkan beban komputasi yang besar. Untuk _hidden state_ berukuran $h$, setiap sel LSTM memerlukan $4h(h + x) + 4h$ parameter, dengan $x$ adalah dimensi masukan. Beban ini membuat pelatihan lebih lambat dan jumlah parameter lebih banyak.

GRU (_Gated Recurrent Unit_) lebih sederhana daripada LSTM. Cho dkk. mengusulkannya @cho2014learning. GRU menggabungkan _forget gate_ dan _input gate_ menjadi satu _update gate_. GRU juga menyatukan _cell state_ dan _hidden state_. _Reset gate_ mengatur seberapa banyak informasi lampau yang dilupakan. _Update gate_ mengatur keseimbangan antara _hidden state_ sebelumnya dan aktivasi kandidat. Chung dkk. menjalankan evaluasi empiris @chung2014empirical. Mereka menemukan bahwa kinerja GRU sebanding dengan LSTM pada pemodelan musik dan ucapan. Sel GRU memerlukan sekitar 25% parameter lebih sedikit daripada sel LSTM, karena memakai tiga perangkat parameter gerbang, bukan empat. #cite(<mondal2023toward>, form: "prose") melatih LSTM, BiLSTM, dan GRU dengan satu protokol pada urutan Google clusterdata-2011-2 yang nyata. Protokol itu memakai TensorFlow 2, Adam, 200 _epoch_, _batch_ 512, dan _loss_ MSE. Mereka menyisihkan sepuluh urutan untuk pengujian. LSTM dan GRU memakai kapasitas yang sama, yaitu 50 unit tersembunyi. GRU terbaik pada ketiga metrik akurasi: MSE 0,00194 dibandingkan 0,00195, RMSE 0,04360 dibandingkan 0,04367, dan MAE 0,03057 dibandingkan 0,03274. Pelatihan memakan 0,75 s dibandingkan 1,44 s. Waktu inferensi praktis sama, 0,0651 s dibandingkan 0,0661 s. Makalah itu tidak menyebut perangkat keras yang dipakai untuk mengukur, sehingga hanya perbandingan di dalam makalah itu yang bermakna. Setiap model juga dilaporkan pada ukuran langkah terbaiknya sendiri, 24 untuk GRU dan 47 untuk LSTM. Karena itu, penelitian ini mengukur sendiri latensinya di _testbed_ (median 4,0 ms pada _bundle_ September, terhadap target 50 ms, Bab 4) dan tidak meminjam angka mereka.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto),
    [Aspek], [LSTM], [GRU],
    [Gerbang], [3 (_forget_, _input_, _output_)], [2 (_reset_, _update_)],
    [Vektor status], [2 (_cell_ + _hidden_)], [1 (hanya _hidden_)],
    [Parameter per sel], [$4h(h+x) + 4h$], [$3h(h+x) + 3h$],
    [Kecepatan pelatihan], [_Baseline_], [Sedikit lebih cepat],
    [Akurasi prediksi], [Acuan], [Sebanding],
    [Kecocokan untuk waktu nyata], [Sedang], [Tinggi],
  ),
  caption: [Perbandingan LSTM vs GRU],
) <table-lstm-gru>

Untuk tugas prediksi beban kerja dalam penelitian ini, GRU adalah arsitektur yang dipilih. Tugasnya adalah prakiraan lalu lintas HTTP berjangka pendek (135 s, 9 × 15 s) dengan batas latensi waktu nyata (inferensi di bawah 50 ms). GRU memiliki biaya komputasi yang lebih rendah dan akurasi yang sebanding. Jumlah parameter yang lebih sedikit juga menurunkan risiko _overfitting_. Pola beban kerja sintetis hanya menyediakan data pelatihan yang terbatas.

== #H("ch2-elax")

Kubernetes menyediakan _autoscaling_ beban kerja lewat Horizontal Pod Autoscaler @kubernetes2026autoscaling dan _autoscaling_ node lewat _autoscaler_ node seperti Cluster Autoscaler @kubernetes2026nodeautoscaling. _Horizontal Pod Autoscaler_ (HPA) menskalakan jumlah replika _pod_ dalam sebuah _deployment_. HPA memakai metrik pemakaian sumber daya yang teramati. HPA menjalankan _control loop_ dengan periode bawaan 15 detik. HPA meminta data dari API metrik. HPA menghitung jumlah replika yang diinginkan sebagai rasio nilai metrik saat ini terhadap nilai yang diinginkan. HPA menskalakan dengan tunduk pada batas minimum dan maksimum serta jendela stabilisasi. #cite(<serracanta2025hpa>, form: "prose") membuktikan secara formal bahwa _control loop_ HPA untuk satu layanan stabil asimtotik secara global terhadap masukan _step_, dan memverifikasinya pada target CPU 80%. Temuan ini membenarkan penyetelan ambang sebagai pilihan rancangan yang sehat. Namun, pengendali ambang yang reaktif tetap dapat berosilasi pada beban yang bergejolak. Tiny Autoscalers @tinyautoscalers2022 memperkenalkan mekanisme _bottoming_ yang menjaga alokasi CPU hasil prediksi untuk fungsi _serverless_ agar tidak turun dengan cepat. Mekanisme ini menjadi dasar rancangan penghitung waktu menganggur untuk konsolidasi dalam tesis ini. Cluster Autoscaler bekerja pada tingkat _node_. Cluster Autoscaler menambah _node_ saat _pod_ tidak dapat dijadwalkan. Cluster Autoscaler menghapus _node_ yang kurang terpakai setelah masa tunggu yang dapat dikonfigurasi.

HPA dan Cluster Autoscaler sama-sama reaktif. Keduanya menanggapi ambang metrik yang teramati. Keduanya tidak mengantisipasi permintaan di masa depan. HPA baru menskalakan setelah _control loop_-nya bereaksi terhadap kenaikan pemakaian @hypa2023. Celah reaktif antara awal permintaan dan selesainya penskalaan ini adalah masalah inti yang diatasi oleh pendekatan prediktif. Survei penjadwalan Kubernetes memasukkan penjadwalan yang mendukung _autoscaling_ sebagai salah satu kategorinya @senjab2023survey. HyPA menggabungkan penskalaan horizontal reaktif dan penskalaan berbasis model, dan memperbarui modelnya secara daring @hypa2023. KAPETÁNIOS mengadaptasi Kubernetes lewat _digital twin_ @kapetanios2022. STaleX menyesuaikan penskalaan _microservice_ dengan fitur beban spasial dan temporal @stalex2025. BACC mengatur laju _autoscaling_ horizontal terhadap anggaran galat @bacc2026.

ElaX @yang2019elax adalah algoritma yang menyediakan elastisitas sumber daya pada layanan _cloud online_ berkontainer. ElaX memiliki tiga komponen, yaitu prediktor beban kerja, model reservasi sumber daya, dan pengendali _online_. Rancangan ini memisahkan prediksi beban kerja dari pengelolaan sumber daya. Workload Predictor memprakirakan volume lalu lintas di masa depan. Komponen ini memakai jaringan rekuren _Long Short-Term Memory_ (LSTM). Resource Allocation Model memetakan lalu lintas yang diprediksi ke sumber daya komputasi yang diperlukan. Model ini memakai model linier $R = alpha dot.op x + beta$. $R$ adalah sumber daya CPU yang diperlukan. $x$ adalah volume lalu lintas dalam _request_ per detik. $alpha$ adalah kemiringan, yaitu biaya sumber daya per _request_. $beta$ adalah beban dasar. Online Controller memantau kepatuhan SLO secara waktu nyata. Komponen ini menyesuaikan sumber daya berdasarkan selisih antara target dan _tail latency_ yang teramati. Komponen ini memakai algoritma penskalaan berbasis _slack_.

Penelitian ini mengubah ElaX dalam tiga hal. Pertama, GRU menggantikan LSTM. Horizon prakiraan menyusut dari satu jam menjadi sembilan langkah 15 detik (135 s), yang mencakup waktu tunda penyediaan _node_ yang terukur di _testbed_ (50 sampai 125 s). Prakiraan diperbarui pada setiap siklus kendali 15 detik, bukan sekali per jam. Median inferensi GRU pada _bundle_ September adalah 4,0 ms (Bab 4). Pada tiga _seed_ yang dipasangkan, GRU memperoleh skor sedikit lebih baik daripada LSTM, dan setara dengan autoregresi linier (Bab 4). Kedua, faktor keputusan berubah. ElaX mereservasi sumber daya untuk nilai prediksi terbesar sepanjang horizonnya, dan penelitian ini mempertahankan aturan nilai terbesar itu. Aturan ini diterapkan pada _upper envelope_ GRU selama 135 s, diperbarui setiap 15 s, lalu dibandingkan dengan target dari beban teramati. Algoritma 2 mengambil yang lebih besar dari kedua target replika, dan menahan target yang dinaikkan selama 90 detik. Algoritma 2 hanya menskalakan replika. Algoritma ini tidak mengimplementasikan ulang pengendali umpan balik berbasis _slack_ maupun _scale-up_ vertikal milik ElaX. Ketiga, Algoritma 1 menambahkan keputusan yang tidak dibuat ElaX. Algoritma ini membagi lalu lintas antara Kubernetes dan _serverless_ berdasarkan beban teramati dan kapasitas yang siap. Algoritma ini tidak memakai prakiraan.

Gabungan model alokasi sumber daya ElaX, perutean lintas platform, dan prediksi GRU membentuk landasan teori bagi sistem _hybrid_ yang dievaluasi dalam tesis ini.

#figure(
  fig-elax-architecture(),
  caption: [Arsitektur sistem ElaX @yang2019elax],
) <fig:elax-architecture>
