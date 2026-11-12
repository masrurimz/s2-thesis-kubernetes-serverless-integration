// Appendix A — Experiment Configuration
// Appendix B — Raw Experiment Results
// Appendix C — Code Listings
// Appendix D — Four-Scenario Replication Data
// Appendix E — Experiment Index
// Ported from archived/thesis-latex/src/chapters/104-106-appendix-*.tex


#import "headings.typ": H, cap
#show raw.where(block: true): set text(size: 8pt)

= #H("app-a")

== #H("app-a-calib")

Tabel berikut menyajikan parameter kalibrasi yang dipakai dalam eksperimen.

#figure(
  kind: table,
  table(
    columns: (auto, auto),
    [Parameter], [Nilai],
    [fib_n], [33],
    [io_wait_ms], [50,0],
    [lambda_compute_ms], [24,0],
    [r_saturation_per_replica], [33,3],
    [target_cpu_util], [0,5],
    [min_k8s_replicas], [3],
    [max_k8s_replicas], [6],
    [pod_cpu_millicores], [300],
    [node_cpu_limit], [1,0 per _node_ beban kerja],
    [proactive_trend_threshold], [3,0],
    [proactive_approach_ratio], [0,6],
    [proactive_lookahead_steps], [9],
  ),
  caption: [Parameter kalibrasi (nilai bawaan)],
)

*Penggantian kalibrasi:* _batch_ berpasangan H2 memakai nilai pengganti khusus eksperimen `max_k8s_replicas = 10` dan `prediction_horizon = 9`, bukan nilai bawaan pada tabel di atas. Nilai pengganti ini penting karena menjelaskan mengapa S1 tidak jenuh pada replikasi empat skenario.

== #H("app-a-alloc")

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto),
    [Komponen], [CPU (Docker)], [_Pod_/replika],
    [_Node_ server K8s], [1,0], [---],
    [_Node_ beban kerja K8s], [1,0 per _node_ (2)], [---],
    [_Node_ agen _serverless_], [3,0], [---],
    [_Node_ beban kerja dinamis], [1,0 per _node_], [---],
    [_Pod baseline_ K8s], [---], [3 x 300m],
    [_Pod_ Knative (KPA)], [---], [3 (skala minimum)],
  ),
  caption: [Alokasi sumber daya _cluster_],
)

== #H("app-a-trace")

#figure(
  kind: table,
  table(
    columns: (auto, auto),
    [Parameter], [Nilai],
    [Jumlah tahap], [40],
    [Durasi per tahap], [30 detik],
    [Total durasi], [1.200 detik (20 menit)],
    [RPS minimum], [22],
    [RPS maksimum], [164],
    [RPS rata-rata], [73],
    [Jumlah _request_ per _run_], [87.840],
  ),
  caption: [Parameter _replay trace_ ClarkNet],
)

#pagebreak()

= #H("app-b")

== #H("app-b-primary")

Tabel berikut menyajikan latensi p99 per pasangan pada _batch_ pra-registrasi (E10 di Lampiran E), yaitu hasil H2 pada @sec:h2. Setiap pasangan menjalankan S3 dan S4 berurutan pada _replay_ ClarkNet, dengan urutan yang bergantian.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto),
    [Pasangan], [p99 S3 (ms)], [p99 S4 (ms)], [Selisih (ms)], [S4 lebih cepat?],
    [1], [101,2], [113,7], [+12,5], [Tidak],
    [2], [301,3], [123,0], [-178,3], [Ya],
    [3], [166,9], [169,5], [+2,6], [Tidak],
    [4], [158,3], [299,8], [+141,5], [Tidak],
    [5], [127,0], [119,6], [-7,4], [Ya],
    [6], [154,9], [96,0], [-59,0], [Ya],
    [7], [158,3], [102,4], [-55,9], [Ya],
    [8], [110,6], [150,2], [+39,5], [Tidak],
    [9], [158,0], [187,8], [+29,7], [Tidak],
    [10], [167,1], [106,1], [-61,0], [Ya],
  ),
  caption: [Latensi p99 per pasangan pada _batch_ pra-registrasi],
) <tab:app-primary-pairs>

== #H("app-b-pairs")

Tabel berikut menyajikan latensi p99 per pasangan pada _batch_ Juli (E3 di Lampiran E), yang dilaporkan sebagai sejarah pada @sec:h2-history. Desainnya sama: lima pasangan (10 _run_) yang diimbangi urutannya pada _replay_ ClarkNet.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto),
    [Pasangan], [p99 S3 (ms)], [p99 S4 (ms)], [Selisih (ms)], [S4 lebih cepat?],
    [1], [235,6], [101,4], [-134,2], [Ya],
    [2], [192,2], [104,9], [-87,3], [Ya],
    [3], [151,4], [100,5], [-50,9], [Ya],
    [4], [164,0], [155,7], [-8,3], [Ya],
    [5], [199,2], [167,4], [-31,8], [Ya],
  ),
  caption: [Latensi p99 per pasangan (_bundle_ berpasangan Juli, sejarah)],
)

== #H("app-b-stats")

#figure(
  kind: table,
  table(
    columns: (auto, auto),
    [Statistik], [Nilai],
    [Rata-rata p99 S3 (ms)], [188,5],
    [Rata-rata p99 S4 (ms)], [126,0],
    [Selisih rata-rata (ms)], [−62,5 (−33,1%)],
    [Rentang kepercayaan 95% berpasangan (ms)], [-100,9 sampai -26,2],
    [Uji permutasi satu sisi], [p = 0,0312],
    [Cohen's d berpasangan], [-1,26 (besar)],
    [Pasangan yang dimenangi S4], [5/5],
    [Pelanggaran SLO rata-rata], [S3 656; S4 130],
    [Biaya bulanan], [USD 163 lawan USD 163],
  ),
  caption: [Hasil statistik _bundle_ berpasangan Juli (sejarah)],
)

Seluruh 5 pasangan pada _batch_ Juli valid, seluruh 280 prediksi GRU terkirim, dan setiap _run_ S4 membawa 4 sampai 5 label PREDICTIVE. Metrik sekunder bersifat deskriptif setelah koreksi Bonferroni (p terkoreksi = 0,1248). Nilai p = 0,0312 adalah batas bawah desain, yaitu 1/32 pada n = 5, yang tercapai karena kelima pasangan jatuh searah. Nilai ini adalah hasil hitung ulang dengan `thesis experiment analyze` yang berlaku sekarang. Berkas analisis yang tersimpan berisi 0,0304 dari rutin yang lebih lama.

_Batch_ ini tidak dapat dikaitkan dengan prediktor yang dilatih pada ClarkNet. Manifesnya tidak mencatat prediktor. Model terpasang `data/models/gru_model.pt` baru masuk kontrol versi pada 2026-09-12 (_commit_ 98e17d1, LFS oid 7f8244bcc403c59a3e2be5d31b1ee5586f01c0052416c2705c0a325d1cc3099d). Model yang terpasang pada bulan Juli kemudian diketahui sebagai model yang dilatih pada data sintetis. @sec:h2 melaporkan putusan H2.

#pagebreak()

= #H("app-c")

== #H("app-c-signal")

Berikut potongan kode sinyal kapasitas pada `algorithm1_v3.py`. Sinyal prediksi diteruskan ke perencanaan replika Algoritma 2, sedangkan pembagian perutean Algoritma 1 tetap memakai beban teramati dan kapasitas replika yang siap:

```
# Track actual load for real-time trend detection
self._load_history.append(current_load or 0)
if len(self._load_history) > 5:
    self._load_history.pop(0)

if prediction and confidence >= threshold:
    raw_pred = prediction.get("predicted_requests", 0)
    if len(self._load_history) >= 3:
        n = len(self._load_history)
        load_trend = (self._load_history[-1] - self._load_history[0]) / (n - 1)
        approach_ratio = current_load / k8s_capacity

        if load_trend > 3.0 and approach_ratio > 0.6:
            amplified = current_load + load_trend * 9  # 135s ahead
            predicted_upper = max(raw_pred, amplified)
            # predicted_upper is consumed by Algorithm 2 replica planning
```

== #H("app-c-capacity")

```
def _compute_k8s_capacity(self, available_replicas):
    return max(0, available_replicas) * self.r_effective_per_replica

# r_effective = r_saturation * target_cpu_util
# = 33.3 * 0.5 = 16.65 RPS/pod
# 3 pods * 16.65 = 49.95 RPS model capacity

def _compute_routing_split(self, total_load, k8s_capacity):
    if total_load <= k8s_capacity:
        return 100, 0, False  # 100% K8s
    burst_ratio = (total_load - k8s_capacity) / total_load
    knative_pct = burst_ratio * 100
```

== #H("app-c-config")

```
class CalibrationConfig(BaseModel):
    fib_n: int = 33
    io_wait_ms: float = 50.0
    lambda_compute_ms: float = 24.0
    r_saturation_per_replica: float = 33.3
    target_cpu_util: float = 0.5
    min_k8s_replicas: int = 3
    max_k8s_replicas: int = 6
    pod_cpu_millicores: int = 300
    node_cpu_limit: float = 1.0
    proactive_trend_threshold: float = 3.0
    proactive_approach_ratio: float = 0.6
    proactive_lookahead_steps: int = 9  # 135s ahead
```

#pagebreak()

= #H("app-d")

== #H("app-d-raw")

Tabel berikut menyajikan hasil per _run_ dari replikasi empat skenario (E7 di Lampiran E), dengan 5 _run_ per skenario. Nilai p99 dibulatkan satu desimal.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto),
    [_Run_], [Skenario], [p99 (ms)], [Pelanggaran SLO],
    [1], [S1 (K8s + HPA)], [117,5], [124],
    [2], [S1 (K8s + HPA)], [98,8], [20],
    [3], [S1 (K8s + HPA)], [115,2], [29],
    [4], [S1 (K8s + HPA)], [107,5], [17],
    [5], [S1 (K8s + HPA)], [112,7], [63],
    [1], [S2 (_Serverless_)], [78,0], [1],
    [2], [S2 (_Serverless_)], [78,7], [0],
    [3], [S2 (_Serverless_)], [83,4], [0],
    [4], [S2 (_Serverless_)], [79,0], [0],
    [5], [S2 (_Serverless_)], [79,4], [1],
    [1], [S3 (_Hybrid_ reaktif)], [239,4], [1.363],
    [2], [S3 (_Hybrid_ reaktif)], [151,6], [321],
    [3], [S3 (_Hybrid_ reaktif)], [103,4], [26],
    [4], [S3 (_Hybrid_ reaktif)], [153,9], [232],
    [5], [S3 (_Hybrid_ reaktif)], [109,5], [56],
    [1], [S4 (_Hybrid_ prediktif)], [88,9], [1],
    [2], [S4 (_Hybrid_ prediktif)], [130,2], [77],
    [3], [S4 (_Hybrid_ prediktif)], [88,2], [1],
    [4], [S4 (_Hybrid_ prediktif)], [94,4], [12],
    [5], [S4 (_Hybrid_ prediktif)], [93,8], [1],
  ),
  caption: [Hasil per _run_ replikasi empat skenario],
)

== #H("app-d-summary")

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto),
    [Skenario], [n], [p99 (ms)], [Pelanggaran SLO], [RPS],
    [S1 (K8s + HPA)], [5], [110,3], [253], [73,2],
    [S2 (_Serverless_)], [5], [79,7], [2], [73,2],
    [S3 (_Hybrid_ reaktif)], [5], [151,6], [1.998], [73,2],
    [S4 (_Hybrid_ prediktif)], [5], [99,1], [92], [73,2],
  ),
  caption: [Ringkasan rata-rata per skenario],
)

== #H("app-d-stats")

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto),
    [Perbandingan], [Hasil], [Kesimpulan],
    [S2 lawan S1], [Welch p = 0,0004; Cohen's d = -5,58], [Signifikan],
    [S4 lawan S3], [Welch p = 0,097; Mann-Whitney p = 0,0317; Cohen's d = -1,30], [Signifikan (Mann-Whitney)],
    [S4 lawan S1], [p = 0,151], [Tidak signifikan],
    [S3 lawan S1], [+37,4%; p = 0,165], [Tidak signifikan],
    [S4 lawan S3 (pelanggaran SLO)], [-95,4%; Mann-Whitney p = 0,0345], [Signifikan],
  ),
  caption: [Uji statistik replikasi empat skenario],
)

#pagebreak()

= #H("app-e")

#set par(justify: false)

== #H("app-e-bundles")

Setiap eksperimen yang dikutip pada Bab 3 sampai 5 tercantum di sini, dengan label yang dipakai teks dan folder yang menyimpan _run_, manifes, dan analisisnya. Folder dihitung dari `results/experiments/phase-b/` dan diawali tanggal eksperimen berjalan. Manifes _run_ mencatat _commit_ kode, konfigurasi, dan, mulai E8, _hash_ prediktor.

#figure(
  kind: table,
  table(
    columns: (auto, 1fr, 1fr, auto),
    align: left,
    [Label], [Desain], [Dipakai untuk], [Folder],
    [E1], [Diagnostik empat skenario, 1 _run_ masing-masing], [Evaluasi komparatif dan biaya (Bab 4)], [`2026-07-11_scaling_fix_n1`],
    [E2], [Diagnostik beban tinggi, 1 _run_ masing-masing], [Penyediaan _node_ dan _offload_ ke _serverless_], [`2026-07-13_dynamic-node-offload`],
    [E3], [S3/S4, 5 pasangan], [Sejarah H2: _batch_ Juli], [`2026-07-14_clarknet-tuned-paired-n5`],
    [E4], [S3/S4 dengan konsolidasi _node_, 1 _run_ masing-masing], [Diagnostik konsolidasi], [`2026-07-14_clarknet-util-scaledown-n1`],
    [E5], [S3/S4, 5 pasangan], [Sejarah H2: Agustus A], [`2026-08-08_paired-h2_195150`],
    [E6], [S3/S4, 5 pasangan], [Sejarah H2: Agustus B], [`2026-08-08_paired-h2_233726`],
    [E7], [Empat skenario, 5 _run_ masing-masing], [Replikasi empat skenario (Lampiran D)], [`2026-08-09_clarknet-replay_032257`],
    [E8], [S3/S4, 5 pasangan], [Sejarah H2: pasangan September], [`2026-09-13_h2-pair-5p`],
    [E9], [S3/S4, 10 pasangan], [Sejarah H2: konfirmatori pertama], [`2026-09-13_h2-confirmatory-10p`],
    [E10], [S3/S4, 10 pasangan, pra-registrasi], [Hasil H2 (@sec:h2)], [`2026-09-20_h2-confirmatory-10p`],
    [--], [S3/S4, 5 pasangan], [Sejarah H2: sebelum kalibrasi], [`2026-07-11_paired-h2`],
    [--], [S3/S4, 5 pasangan], [Sejarah H2: awal], [`2026-07-12_paired-h2-clean-v2`],
  ),
  caption: [_Bundle_ eksperimen yang dikutip dalam buku ini],
) <tab:app-e-bundles>

== #H("app-e-models")

Studi prediktor dan model biaya di balik Bab 4 disimpan di luar _bundle_ eksperimen.

#figure(
  kind: table,
  table(
    columns: (1fr, auto, 2fr),
    align: left,
    [Studi], [Dipakai untuk], [Lokasi],
    [Pencarian representasi dengan dua belas variasi], [Bab 4, kinerja GRU], [`results/models/gru/2026-09-13_probes-representation/`],
    [Transfer lintas _trace_ (T-cross)], [Bab 4, kinerja GRU], [`results/models/gru/2026-09-13_probe-t-cross/`],
    [Kalibrasi T-cross], [Bab 4, kinerja GRU], [`results/models/gru/2026-09-13_t-cross-calibration/`],
    [Model biaya diagnostik empat skenario], [Analisis biaya (E1)], [`results/cost_analysis/cost_analysis_20260711_112337.json`],
    [Prediktor terpasang], [Setiap _run_ S4 mulai E8], [`data/models/gru_model.pt`],
  ),
  caption: [Studi prediktor, model biaya, dan prediktor terpasang],
) <tab:app-e-models>
