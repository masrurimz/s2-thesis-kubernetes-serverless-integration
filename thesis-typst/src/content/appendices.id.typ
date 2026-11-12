// Appendix A — Experiment Configuration
// Appendix B — Raw Experiment Results
// Appendix C — Code Listings
// Ported from archived/thesis-latex/src/chapters/104-106-appendix-*.tex

#import "headings.typ": H, cap

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

*Catatan (penggantian kalibrasi):* _Bundle_ berpasangan H2 memakai nilai pengganti khusus eksperimen `max_k8s_replicas = 10, prediction_horizon = 9`, bukan nilai bawaan pada tabel di atas. Nilai pengganti ini penting karena menjelaskan mengapa S1 tidak jenuh pada replikasi n=5.

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

== #H("app-b-pairs")

Tabel berikut menyajikan nilai p99 per pasangan dari _bundle_ Juli `2026-07-14_clarknet-tuned-paired-n5` (sejarah). Desainnya menyeimbangkan urutan: pada lima pasangan (10 _run_), urutan S3 dan S4 bergantian, dengan beban _trace_ ClarkNet.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto),
    [Pasangan], [p99 S3 (ms)], [p99 S4 (ms)], [Selisih (ms)], [S4 lebih baik?],
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
    [Metrik], [Nilai],
    [Rata-rata p99 S3 (ms)], [188,5],
    [Rata-rata p99 S4 (ms)], [126,0],
    [Selisih rata-rata (ms)], [-62,5 (-33,1%)],
    [Rentang kepercayaan 95% berpasangan (ms)], [-100,9 sampai -26,2],
    [Uji permutasi satu sisi], [p = 0,0312],
    [Cohen's d berpasangan], [-1,26 (besar)],
    [Pasangan yang dimenangi S4], [5/5],
    [Pelanggaran SLO rata-rata], [S3 656; S4 130],
    [Biaya bulanan], [USD 163 vs USD 163],
  ),
  caption: [Hasil statistik _bundle_ berpasangan Juli (sejarah)],
)

_Bundle_ ini adalah perbandingan berpasangan _batch_ Juli untuk H2. Penelitian ini kini melaporkannya sebagai sejarah. Seluruh 5 pasangan valid dan seluruh 280 prediksi GRU terkirim. Nilai `predictive_count` berada pada 4 sampai 5 per _run_ S4. Metrik sekunder dilaporkan secara deskriptif setelah koreksi Bonferroni (p terkoreksi = 0,1248). Nilai p = 0,0312 adalah batas bawah desain, yaitu 1/32 pada n = 5, karena kelima pasangan jatuh searah. Nilai ini adalah hasil hitung ulang dengan rutin `thesis experiment analyze` saat ini. Artefak _bundle_ yang tersimpan menyimpan 0,0304 dari rutin analisis lama. Prediktor terpasang `data/models/gru_model.pt` baru masuk kontrol versi pada 2026-09-12 (_commit_ 98e17d1, LFS oid 7f8244bcc403c59a3e2be5d31b1ee5586f01c0052416c2705c0a325d1cc3099d). Manifes _bundle_ 2026-07-14 tidak mencatat prediktor. Artefak pada periode itu kemudian terbukti berupa model pemenang yang dilatih dengan data sintetis, sehingga _batch_ ini tidak dapat diatribusikan ke ClarkNet. Putusan akhir H2 (Bab 4, bagian replikasi) adalah hipotesis tidak didukung. Tiga _batch_ yang dapat diatribusikan ke ClarkNet (p = 0,656; 0,168; 0,307) semuanya tidak menunjukkan selisih nyata. Gabungan 25 pasangan memberi selisih −16,5 ms (rentang kepercayaan 95% −188,6 sampai +184,5 ms, p satu sisi = 0,448; `paper/derive_numbers.py`).

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

Tabel berikut menyajikan hasil per _run_ dari replikasi empat skenario `2026-08-09_clarknet-replay_032257` yang telah selesai (n=5 per skenario). Nilai p99 dibulatkan satu desimal.

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
  caption: [Hasil per _run_ replikasi n=5],
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
    [S2 vs S1], [Welch p = 0,0004; Cohen's d = -5,58], [Signifikan],
    [S4 vs S3], [Welch p = 0,097; Mann-Whitney p = 0,0317; Cohen's d = -1,30], [Signifikan (Mann-Whitney)],
    [S4 vs S1], [p = 0,151], [Tidak signifikan],
    [S3 vs S1], [+37,4%; p = 0,165], [Tidak signifikan],
    [S4 vs S3 (pelanggaran SLO)], [-95,4%; Mann-Whitney p = 0,0345], [Signifikan],
  ),
  caption: [Ringkasan uji statistik replikasi n=5.],
)
