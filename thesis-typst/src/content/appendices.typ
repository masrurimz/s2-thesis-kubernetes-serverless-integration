// Appendix A — Experiment Configuration
// Appendix B — Raw Experiment Results
// Appendix C — Code Listings
// Appendix D — Four-Scenario Replication Data
// Appendix E — Experiment Index
// Ported from archived/thesis-latex/src/chapters/104-106-appendix-*.tex

#import "headings.typ": H, cap

= #H("app-a")

== #H("app-a-calib")

The table below lists the calibration parameters used in the experiments.

#figure(
  kind: table,
  table(
    columns: (auto, auto),
    [Parameter], [Value],
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
  caption: [Calibration parameters (default)],
)

*Calibration override:* the paired H2 batches use the experiment-specific overrides `max_k8s_replicas = 10` and `prediction_horizon = 9` instead of the defaults above. The override matters because it explains why S1 did not saturate in the four-scenario replication.

== #H("app-a-alloc")

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto),
    [Component], [CPU (Docker)], [Pod/Replica],
    [K8s server node], [1.0], [---],
    [K8s workload nodes], [1.0 each (2)], [---],
    [Serverless agent node], [3.0], [---],
    [Dynamic workload nodes], [1.0 each], [---],
    [K8s baseline pods], [---], [3 x 300m],
    [Knative pods (KPA)], [---], [3 (min-scale)],
  ),
  caption: [Cluster resource allocation],
)

== #H("app-a-trace")

#figure(
  kind: table,
  table(
    columns: (auto, auto),
    [Parameter], [Value],
    [Stages], [40],
    [Stage duration], [30 s],
    [Total duration], [1200 s (20 min)],
    [Minimum RPS], [22],
    [Maximum RPS], [164],
    [Mean RPS], [73],
    [Requests per run], [87840],
  ),
  caption: [ClarkNet trace replay parameters],
)

#pagebreak()

= #H("app-b")

== #H("app-b-primary")

The table below lists p99 latency per pair for the pre-registered batch (E10 in Appendix E), the H2 result of @sec:h2. Each pair ran S3 and S4 back to back on the ClarkNet replay, alternating which arm ran first.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto),
    [Pair], [S3 p99 (ms)], [S4 p99 (ms)], [Difference (ms)], [S4 faster?],
    [1], [101.2], [113.7], [+12.5], [No],
    [2], [301.3], [123.0], [-178.3], [Yes],
    [3], [166.9], [169.5], [+2.6], [No],
    [4], [158.3], [299.8], [+141.5], [No],
    [5], [127.0], [119.6], [-7.4], [Yes],
    [6], [154.9], [96.0], [-59.0], [Yes],
    [7], [158.3], [102.4], [-55.9], [Yes],
    [8], [110.6], [150.2], [+39.5], [No],
    [9], [158.0], [187.8], [+29.7], [No],
    [10], [167.1], [106.1], [-61.0], [Yes],
  ),
  caption: [Per-pair p99 latency in the pre-registered batch],
) <tab:app-primary-pairs>

== #H("app-b-pairs")

The table below lists p99 latency per pair for the July batch (E3 in Appendix E), reported as history in @sec:h2-history. Its design is the same: five counterbalanced pairs (10 runs) on the ClarkNet replay.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto),
    [Pair], [S3 p99 (ms)], [S4 p99 (ms)], [Difference (ms)], [S4 faster?],
    [1], [235.6], [101.4], [-134.2], [Yes],
    [2], [192.2], [104.9], [-87.3], [Yes],
    [3], [151.4], [100.5], [-50.9], [Yes],
    [4], [164.0], [155.7], [-8.3], [Yes],
    [5], [199.2], [167.4], [-31.8], [Yes],
  ),
  caption: [Per-pair p99 latency (July paired bundle, history)],
)

== #H("app-b-stats")

#figure(
  kind: table,
  table(
    columns: (auto, auto),
    [Statistic], [Value],
    [S3 mean p99 (ms)], [188.5],
    [S4 mean p99 (ms)], [126.0],
    [Mean difference (ms)], [-62.5 (-33.1%)],
    [95% paired CI (ms)], [-100.9 to -26.2],
    [One-sided permutation test], [p = 0.0312],
    [Paired Cohen's d], [-1.26 (large)],
    [Pairs won by S4], [5 of 5],
    [Mean SLO violations], [S3 656; S4 130],
    [Monthly cost], [USD 163 vs USD 163],
  ),
  caption: [Statistical results of the July paired bundle (history)],
)

All 5 pairs in the July batch were valid, all 280 GRU predictions were delivered, and each S4 run carried 4 to 5 PREDICTIVE labels. The secondary metrics are descriptive after Bonferroni correction (corrected p = 0.1248). The value p = 0.0312 is the floor of the design, 1/32 at n = 5, reached because all five pairs went the same way. It is what the current `thesis experiment analyze` computes; the stored analysis file holds 0.0304 from an older routine.

The batch cannot be credited to the ClarkNet-trained predictor. Its manifest records no predictor. The deployed model `data/models/gru_model.pt` entered version control only on 2026-09-12 (commit 98e17d1, LFS oid 7f8244bcc403c59a3e2be5d31b1ee5586f01c0052416c2705c0a325d1cc3099d), and the model deployed in July was later identified as the synthetic-trained one. @sec:h2 reports the H2 verdict.

#pagebreak()

= #H("app-c")

== #H("app-c-signal")

The excerpt below is the capacity signal in `algorithm1_v3.py`. The forecast feeds Algorithm 2's replica planning, while the Algorithm 1 routing split keeps using observed load and ready-replica capacity:

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

The table below lists per-run results of the four-scenario replication (E7 in Appendix E), with 5 runs per scenario. p99 values are rounded to one decimal.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto),
    [Run], [Scenario], [p99 (ms)], [SLO violations],
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
    [1], [S3 (Hybrid reactive)], [239.4], [1363],
    [2], [S3 (Hybrid reactive)], [151.6], [321],
    [3], [S3 (Hybrid reactive)], [103.4], [26],
    [4], [S3 (Hybrid reactive)], [153.9], [232],
    [5], [S3 (Hybrid reactive)], [109.5], [56],
    [1], [S4 (Hybrid predictive)], [88.9], [1],
    [2], [S4 (Hybrid predictive)], [130.2], [77],
    [3], [S4 (Hybrid predictive)], [88.2], [1],
    [4], [S4 (Hybrid predictive)], [94.4], [12],
    [5], [S4 (Hybrid predictive)], [93.8], [1],
  ),
  caption: [Per-run results of the four-scenario replication],
)

== #H("app-d-summary")

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto, auto, auto),
    [Scenario], [n], [p99 (ms)], [SLO violations], [RPS],
    [S1 (K8s + HPA)], [5], [110.3], [253], [73.2],
    [S2 (Serverless)], [5], [79.7], [2], [73.2],
    [S3 (Hybrid reactive)], [5], [151.6], [1998], [73.2],
    [S4 (Hybrid predictive)], [5], [99.1], [92], [73.2],
  ),
  caption: [Mean summary per scenario],
)

== #H("app-d-stats")

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto),
    [Comparison], [Result], [Conclusion],
    [S2 vs S1], [Welch p = 0.0004; Cohen's d = -5.58], [Significant],
    [S4 vs S3], [Welch p = 0.097; Mann-Whitney p = 0.0317; Cohen's d = -1.30], [Significant (Mann-Whitney)],
    [S4 vs S1], [p = 0.151], [Not significant],
    [S3 vs S1], [+37.4%; p = 0.165], [Not significant],
    [S4 vs S3 (SLO)], [-95.4%; Mann-Whitney p = 0.0345], [Significant],
  ),
  caption: [Statistical tests of the four-scenario replication],
)

#pagebreak()

= #H("app-e")

#set par(justify: false)

== #H("app-e-bundles")

Every experiment cited in Chapters 3 to 5 is listed here with the label the text uses and the folder that holds its runs, manifests and analysis. Folders are relative to `results/experiments/phase-b/` and start with the date the experiment ran. A run manifest records the code commit, the configuration and, from E8 on, the hash of the predictor.

#figure(
  kind: table,
  table(
    columns: (auto, 1fr, 1fr, auto),
    align: left,
    [Label], [Design], [Used for], [Folder],
    [E1], [Four-scenario diagnostic, 1 run each], [Comparative evaluation and cost (Chapter 4)], [`2026-07-11_scaling_fix_n1`],
    [E2], [High-load diagnostic, 1 run each], [Node provisioning and serverless offload], [`2026-07-13_dynamic-node-offload`],
    [E3], [S3/S4, 5 pairs], [H2 history: July batch], [`2026-07-14_clarknet-tuned-paired-n5`],
    [E4], [S3/S4 with node consolidation, 1 run each], [Consolidation diagnostic], [`2026-07-14_clarknet-util-scaledown-n1`],
    [E5], [S3/S4, 5 pairs], [H2 history: August A], [`2026-08-08_paired-h2_195150`],
    [E6], [S3/S4, 5 pairs], [H2 history: August B], [`2026-08-08_paired-h2_233726`],
    [E7], [Four scenarios, 5 runs each], [Four-scenario replication (Appendix D)], [`2026-08-09_clarknet-replay_032257`],
    [E8], [S3/S4, 5 pairs], [H2 history: September pair], [`2026-09-13_h2-pair-5p`],
    [E9], [S3/S4, 10 pairs], [H2 history: first confirmatory], [`2026-09-13_h2-confirmatory-10p`],
    [E10], [S3/S4, 10 pairs, pre-registered], [H2 result (@sec:h2)], [`2026-09-20_h2-confirmatory-10p`],
    [--], [S3/S4, 5 pairs], [H2 history: pre-calibration], [`2026-07-11_paired-h2`],
    [--], [S3/S4, 5 pairs], [H2 history: initial], [`2026-07-12_paired-h2-clean-v2`],
  ),
  caption: [Experiment bundles cited in the book],
) <tab:app-e-bundles>

== #H("app-e-models")

The predictor studies and the cost model behind Chapter 4 are stored outside the experiment bundles.

#figure(
  kind: table,
  table(
    columns: (auto, auto, auto),
    align: left,
    [Study], [Used for], [Location],
    [Twelve-lever representation search], [Chapter 4, GRU performance], [`results/models/gru/2026-09-13_probes-representation/`],
    [Cross-trace transfer (T-cross)], [Chapter 4, GRU performance], [`results/models/gru/2026-09-13_probe-t-cross/`],
    [T-cross calibration], [Chapter 4, GRU performance], [`results/models/gru/2026-09-13_t-cross-calibration/`],
    [Cost model of the four-scenario diagnostic], [Cost analysis (E1)], [`results/cost_analysis/cost_analysis_20260711_112337.json`],
    [Deployed predictor], [Every S4 run from E8 on], [`data/models/gru_model.pt`],
  ),
  caption: [Predictor studies, cost model and deployed predictor],
) <tab:app-e-models>
