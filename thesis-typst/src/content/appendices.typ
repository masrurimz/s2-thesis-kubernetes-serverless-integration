// Appendix A — Experiment Configuration
// Appendix B — Raw Experiment Results
// Appendix C — Code Listings
// Ported from archived/thesis-latex/src/chapters/104-106-appendix-*.tex

#import "headings.typ": H, cap

= #H("app-a")

== #H("app-a-calib")

Tabel berikut menyajikan parameter kalibrasi yang digunakan dalam eksperimen.

#figure(
  kind: table,
  table(
    columns: (auto, auto),
    [Parameter], [Nilai],
    [fib_n], [33],
    [io_wait_ms], [50.0],
    [lambda_compute_ms], [24.0],
    [r_saturation_per_replica], [33.3],
    [target_cpu_util], [0.5],
    [min_k8s_replicas], [3],
    [max_k8s_replicas], [6],
    [pod_cpu_millicores], [300],
    [node_cpu_limit], [1.0 per workload node],
    [proactive_trend_threshold], [3.0],
    [proactive_approach_ratio], [0.6],
    [proactive_lookahead_steps], [9],
  ),
  caption: cap([Calibration parameters (default)], [Parameter kalibrasi (default)]),
)

*Catatan (override definitif):* Bundle berpasangan definitif H2 menggunakan override khusus eksperimen `max_k8s_replicas = 10, prediction_horizon = 9`, bukan nilai default pada tabel di atas. Override ini penting karena menjelaskan mengapa S1 tidak jenuh pada replikasi n=5.

== #H("app-a-alloc")

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto),
    [Komponen], [CPU (Docker)], [Pod/Replica],
    [K8s server node], [1.0], [---],
    [K8s workload nodes], [1.0 each (2)], [---],
    [Serverless agent node], [3.0], [---],
    [Dynamic workload nodes], [1.0 each], [---],
    [K8s baseline pods], [---], [3 x 300m],
    [Knative pods (KPA)], [---], [3 (min-scale)],
  ),
  caption: cap([Cluster resource allocation], [Alokasi sumber daya klaster]),
)

== #H("app-a-trace")

#figure(
  kind: table,
  table(
    columns: (auto, auto),
    [Parameter], [Nilai],
    [Jumlah tahap], [40],
    [Durasi per tahap], [30 detik],
    [Total durasi], [1200 detik (20 menit)],
    [RPS minimum], [22],
    [RPS maksimum], [164],
    [RPS rata-rata], [73],
    [Jumlah request per run], [87840],
  ),
  caption: cap([ClarkNet trace replay parameters], [Parameter replay trace ClarkNet]),
)

#pagebreak()

= #H("app-b")

== #H("app-b-pairs")

Tabel berikut menyajikan nilai p99 per pasangan dari bundle definitif `2026-07-14_clarknet-tuned-paired-n5`. Desainnya counterbalanced: lima pasangan (10 run) mengalternasikan urutan S3 dan S4 pada beban trace ClarkNet.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto),
    [Pair], [S3 p99 (ms)], [S4 p99 (ms)], [Selisih (ms)], [S4 lebih baik?],
    [1], [235.6], [101.4], [-134.2], [Ya],
    [2], [192.2], [104.9], [-87.3], [Ya],
    [3], [151.4], [100.5], [-50.9], [Ya],
    [4], [164.0], [155.7], [-8.3], [Ya],
    [5], [199.2], [167.4], [-31.8], [Ya],
  ),
  caption: cap([Per-pair p99 latency (definitive ClarkNet bundle)], [Per-pair p99 latency (bundle definitif ClarkNet)]),
)

== #H("app-b-stats")

#figure(
  kind: table,
  table(
    columns: (auto, auto),
    [Metrik], [Nilai],
    [Rata-rata p99 S3 (ms)], [188.5],
    [Rata-rata p99 S4 (ms)], [126.0],
    [Selisih rata-rata (ms)], [-62.5 (-33.1%)],
    [95% CI berpasangan (ms)], [-100.9 hingga -26.2],
    [Uji permutasi satu sisi], [p = 0.0304],
    [Cohen's d berpasangan], [-1.26 (besar)],
    [Kemenangan pasangan S4], [5/5],
    [Pelanggaran SLO rata-rata], [S3 656; S4 130],
    [Biaya bulanan], [USD 163 vs USD 163],
  ),
  caption: cap([Statistical results of the definitive bundle], [Hasil statistik bundle definitif]),
)

Bundle ini adalah perbandingan definitif counterbalanced untuk H2. Seluruh 5 pasangan valid, seluruh 280 prediksi GRU terkirim, dan `predictive_count` berada pada 4--5 per run S4. Metrik sekunder dilaporkan deskriptif setelah koreksi Bonferroni (p terkoreksi = 0.1216).

#pagebreak()

= #H("app-c")

== #H("app-c-signal")

Berikut adalah potongan kode sinyal kapasitas pada `algorithm1_v3.py`; sinyal prediksi diteruskan untuk perencanaan replika Algorithm 2, sedangkan pembagian routing Algorithm 1 tetap menggunakan beban teramati dan kapasitas replika siap:

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

Tabel berikut menyajikan hasil per-run replikasi empat skenario `2026-08-09_clarknet-replay_032257` yang telah selesai (n=5 per skenario); nilai p99 dibulatkan satu desimal.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto),
    [Run], [Skenario], [p99 (ms)], [Pelanggaran SLO],
    [1], [S1 (K8s + HPA)], [117.5], [124],
    [2], [S1 (K8s + HPA)], [98.8], [20],
    [3], [S1 (K8s + HPA)], [115.2], [29],
    [4], [S1 (K8s + HPA)], [107.5], [17],
    [5], [S1 (K8s + HPA)], [112.7], [63],
    [1], [S2 (Serverless)], [78.0], [1],
    [2], [S2 (Serverless)], [78.7], [0],
    [3], [S2 (Serverless)], [83.4], [0],
    [4], [S2 (Serverless)], [79.0], [0],
    [5], [S2 (Serverless)], [79.4], [1],
    [1], [S3 (Hybrid-reaktif)], [239.4], [1363],
    [2], [S3 (Hybrid-reaktif)], [151.6], [321],
    [3], [S3 (Hybrid-reaktif)], [103.4], [26],
    [4], [S3 (Hybrid-reaktif)], [153.9], [232],
    [5], [S3 (Hybrid-reaktif)], [109.5], [56],
    [1], [S4 (Hybrid-prediktif)], [88.9], [1],
    [2], [S4 (Hybrid-prediktif)], [130.2], [77],
    [3], [S4 (Hybrid-prediktif)], [88.2], [1],
    [4], [S4 (Hybrid-prediktif)], [94.4], [12],
    [5], [S4 (Hybrid-prediktif)], [93.8], [1],
  ),
  caption: cap([Per-run results of the n=5 replication], [Hasil per-run replikasi n=5]),
)

== #H("app-d-summary")

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto),
    [Skenario], [n], [p99 (ms)], [Pelanggaran SLO], [RPS],
    [S1 (K8s + HPA)], [5], [110.3], [253], [73.2],
    [S2 (Serverless)], [5], [79.7], [2], [73.2],
    [S3 (Hybrid-reaktif)], [5], [151.6], [1998], [73.2],
    [S4 (Hybrid-prediktif)], [5], [99.1], [92], [73.2],
  ),
  caption: cap([Mean summary per scenario], [Ringkasan rata-rata per skenario]),
)

== #H("app-d-stats")

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto),
    [Perbandingan], [Hasil], [Kesimpulan],
    [S2 vs S1], [Welch p = 0.0004; Cohen's d = -5.58], [Signifikan],
    [S4 vs S3], [Welch p = 0.097; Mann-Whitney p = 0.0317; Cohen's d = -1.30], [Signifikan (Mann-Whitney)],
    [S4 vs S1], [p = 0.24], [Tidak signifikan],
    [S3 vs S1], [+37.4%; p = 0.165], [Tidak signifikan],
    [S4 vs S3 (SLO)], [-95.4%; Mann-Whitney p = 0.0345], [Signifikan],
  ),
  caption: cap([Summary of statistical tests for the n=5 replication.], [Ringkasan uji statistik replikasi n=5.]),
)
