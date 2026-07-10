// Appendix A — Experiment Configuration
// Appendix B — Raw Experiment Results
// Appendix C — Code Listings
// Ported from archived/thesis-latex/src/chapters/104-106-appendix-*.tex

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
    [r_saturation_per_replica], [66.7],
    [target_cpu_util], [0.5],
    [min_k8s_replicas], [3],
    [max_k8s_replicas], [10],
    [pod_cpu_millicores], [300],
    [node_cpu_limit], [1.0],
    [proactive_trend_threshold], [3.0],
    [proactive_approach_ratio], [0.6],
    [proactive_lookahead_steps], [5],
  ),
  caption: [Calibration parameters],
)

== Alokasi Sumber Daya Kluster

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto),
    [Komponen], [CPU (Docker)], [Pod/Replica],
    [K8s server node], [3.0], [---],
    [K8s agent node], [3.0], [---],
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

== Hasil Per-Run (n=5)

Tabel berikut menyajikan hasil individu untuk setiap run pada eksperimen fib33_proactive (S3, S4) dan fib33_n5 (S1, S2).

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    [Skenario], [Run], [p99 (ms)], [p95 (ms)], [SLO], [Biaya (USD)],
    [S1], [1], [112], [77], [43], [0.091],
    [S1], [2], [116], [77], [69], [0.092],
    [S1], [3], [112], [77], [58], [0.091],
    [S1], [4], [99], [75], [30], [0.091],
    [S1], [5], [110], [78], [6], [0.091],
    [S2], [1], [77], [75], [8], [0.191],
    [S2], [2], [79], [75], [4], [0.189],
    [S2], [3], [78], [75], [9], [0.191],
    [S2], [4], [78], [76], [8], [0.192],
    [S2], [5], [77], [75], [6], [0.189],
    [S3], [1], [447], [233], [3533], [0.069],
    [S3], [2], [143], [86], [191], [0.069],
    [S3], [3], [389], [167], [3818], [0.070],
    [S3], [4], [178], [108], [522], [0.069],
    [S3], [5], [390], [200], [5963], [0.069],
    [S4], [1], [184], [102], [605], [0.072],
    [S4], [2], [189], [94], [701], [0.072],
    [S4], [3], [199], [104], [857], [0.072],
    [S4], [4], [224], [92], [1093], [0.072],
    [S4], [5], [143], [86], [253], [0.073],
  ),
  caption: [Per-run results across all scenarios (n=5)],
)

== Output Uji Statistik

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto),
    [Metrik], [p99 (ms)], [SLO],
    [Welch t-statistic], [-1.919], [-1.922],
    [Welch p-value], [0.1216], [0.1247],
    [Mann-Whitney U], [9.0], [9.0],
    [Mann-Whitney p], [0.5476], [0.5476],
    [Cohen's d], [-1.214], [-1.215],
    [95% CI lower], [-229.35], [-3995.60],
    [95% CI upper], [-10.33], [-239.80],
  ),
  caption: [Statistical test output (S4 vs S3, n=5)],
)

#pagebreak()

= LAMPIRAN C: Code Listings

== Proactive Routing (V3 Controller)

Berikut adalah potongan kode mekanisme proactive routing pada `algorithm1_v3.py`:

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
            amplified = current_load + load_trend * 5  # 75s ahead
            predicted_upper = max(raw_pred, amplified)
```

== Kapasitas Efektif K8s

```
def _compute_k8s_capacity(self, available_replicas):
    return max(0, available_replicas) * self.r_effective_per_replica

# r_effective = r_saturation * target_cpu_util
# = 66.7 * 0.5 = 33.35 RPS/pod
# 3 pods * 33.35 = 100.05 RPS total capacity

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
    r_saturation_per_replica: float = 66.7
    target_cpu_util: float = 0.5  # cap = 3 * 66.7 * 0.5 = 100 RPS
    min_k8s_replicas: int = 3
    proactive_trend_threshold: float = 3.0
    proactive_approach_ratio: float = 0.6
    proactive_lookahead_steps: int = 5  # 75s ahead
```
