// Appendix A — Experiment Configuration
// Appendix B — Raw Experiment Results
// Appendix C — Code Listings
// Ported from archived/thesis-latex/src/chapters/104-106-appendix-*.tex
#import "figures.typ": *

= LAMPIRAN A: Konfigurasi Eksperimen

== Parameter Kalibrasi

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
  caption: [Calibration parameters (default; the definitive paired H2 bundle used an experiment-local override #raw("max_k8s_replicas = 10, prediction_horizon = 9"), see the calibration override file under #raw("results/calibration/2026-08-06_definitive-repro.json"))],
)

== Alokasi Sumber Daya Kluster

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
  caption: [Cluster resource allocation],
)

== Parameter Trace ClarkNet

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
  caption: [ClarkNet trace replay parameters],
)

#pagebreak()

= LAMPIRAN B: Hasil Eksperimen Mentah

== Hasil Per-Pasangan Definitif (n=5)

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
  caption: [Per-pair p99 latency pada bundle definitif ClarkNet (S3 reaktif vs S4 prediktif).],
)

== Ringkasan Uji Statistik Definitif

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
  caption: [Hasil statistik bundle definitif; p99 adalah endpoint primer yang telah dipra-spesifikasikan.],
)

Bundle ini adalah perbandingan definitif counterbalanced untuk H2. Seluruh 5 pasangan valid, seluruh 280 prediksi GRU terkirim, dan `predictive_count` berada pada 4--5 per run S4. Metrik sekunder dilaporkan deskriptif setelah koreksi Bonferroni (p terkoreksi = 0.1216).

#pagebreak()

= LAMPIRAN C: Code Listings

== Forecast-Gated Capacity Signal (V3 Controller)

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

== Kapasitas Efektif K8s

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

== CalibrationConfig

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

= LAMPIRAN D: Visualisasi Data

== Grafik Data

Berikut enam visualisasi data hasil eksperimen.

#figure(
  fig-paired-perpair(),
  caption: [p99 per pasangan pada bundle definitif H2.],
) <fig:fig04-1>

#figure(
  fig-p99-boxplot(),
  caption: [Distribusi p99 empat skenario pada replikasi n=5.],
) <fig:fig04-2>

#figure(
  fig-slo-violations(),
  caption: [Pelanggaran SLO S3 versus S4.],
) <fig:fig04-3>

#figure(
  fig-node-provisioning(),
  caption: [Lini masa provisioning node.],
) <fig:fig04-4>

#figure(
  fig-cost-comparison(),
  caption: [Biaya bulanan per skenario.],
) <fig:fig04-5>

#figure(
  image("../figures/fig04_6_replication_batches.png", width: 85%),
  caption: [Ukuran efek H2 pada replikasi antar batch.],
) <fig:fig04-6>

== Data Mentah Replikasi n=5

Tabel berikut menyajikan hasil replikasi empat skenario `2026-08-09_clarknet-replay_032257` yang telah selesai (n=5).

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
  caption: [Hasil replikasi empat skenario n=5 (run `2026-08-09_clarknet-replay_032257`).],
)

== Perbandingan Statistik n=5

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
  caption: [Ringkasan uji statistik replikasi n=5.],
)

== Catatan Replikasi

Data pada lampiran ini bersifat replikasi. Klaim definitif H2 tetap mengacu pada bundle Juli (p = 0.0304; Cohen's d = -1.26). Replikasi n=5 memakai `max_k8s_replicas = 10` sehingga S1 (HPA) tidak jenuh. Hal ini berbeda dengan diagnostik n=1 yang memakai `max_k8s_replicas = 6` dan mencatat p99 S1 sebesar 2.421 ms. Akibatnya keunggulan hybrid atas K8s murni tidak ter-reproduksi pada n=5.
