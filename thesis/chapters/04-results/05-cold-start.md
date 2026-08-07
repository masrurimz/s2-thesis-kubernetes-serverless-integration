> **Historical-data banner:** The measurements in this section were derived from the invalidated February Phase B bundles (Bugs 1–7 in `results/claims/INCONSISTENCIES.md`). They are retained only as historical context and are not current comparative evidence. For the current cold-start threat and its interpretation, see [`protocol/THREATS_TO_VALIDITY.md`](../../protocol/THREATS_TO_VALIDITY.md).
## 4.5 Cold Start Latency Analysis

Knative serverless backends introduce cold start latency when scaling from zero instances. This section quantifies the cold start penalty and its contribution to tail latency variance in the hybrid scenarios.

### 4.5.1 Cold Start Penalty Measurement

**Table 4.23: Cold Start Latency Measurements**

| Source | Cold Start Latency (ms) | Context |
|--------|------------------------|---------|
| S3 infrastructure test | 682 | Pre-warm cold start, reactive scenario |
| S4 infrastructure test | 1,235 | Pre-warm cold start, predictive scenario |
| Average | 959 | Mean of both measurements |
| Warm state p99 (Phase A1) | 133 | After stabilization at 50/50 weights |
| **Cold start overhead** | **826** | Above warm-state baseline |

The Knative configuration uses `minScale=0` (pods scale to zero after idle), `scale-to-zero-grace-period=30s`, and `stable-window=60s`. This configuration guarantees cold starts on first serverless engagement in each experiment run, contributing an estimated 826ms overhead above warm-state p99.

### 4.5.2 Variance Decomposition

The hybrid scenarios (S3, S4) exhibit higher tail-latency variance than pure scenarios (S1, S2) due to the interaction of cold starts with traffic routing decisions. A variance decomposition model isolates the contribution of cold-start and routing overhead.

**Table 4.24: Variance Decomposition (Phase B, Cleaned Dataset)**

| Component | S3 (Reactive) | S4 (Predictive) |
|-----------|---------------|------------------|
| Total σ² | 88,171 | 47,870 |
| Total σ | 297ms | 219ms |
| Base σ² (avg S1+S2) | 36,875 | 36,875 |
| Base σ | 192ms | 192ms |
| Excess σ² | 51,296 | 10,996 |
| Excess σ | 227ms | 105ms |
| % from cold start/routing | **58.2%** | **23.0%** |

For S3 (reactive), 58.2% of total variance is attributable to cold-start and routing overhead—beyond the baseline variance observed in pure scenarios. For S4 (predictive), this figure drops to 23.0%, indicating that the predictive variant produces substantially less excess variance despite similar SCALE_OUT counts (17–18 per run). The 35 percentage-point difference (58% − 23%) suggests that the presence of the prediction pipeline—even without explicitly triggering PREDICTIVE—contributes to more stable routing behavior.

### 4.5.3 Correlation with Scale-Out Events

**Table 4.25: Pearson Correlation: Scale-Out Count ↔ p99 Latency**

| Scenario | Pearson r | Interpretation |
|----------|-----------|----------------|
| S3 (Reactive) | 0.627 | Moderate-strong positive |
| S4 (Predictive) | 0.639 | Moderate-strong positive |

Runs with more SCALE_OUT decisions tend to exhibit higher p99 latency (r ≈ 0.63 for both scenarios). This is consistent with the causal chain: more scale-outs indicate more cold start events during the run, and cold starts inflate tail latency. However, with n = 4–5 per scenario, these correlations are suggestive rather than statistically conclusive.

### 4.5.4 Phase A1 Transition Analysis

The Phase A1 ramp test provides per-decision latency data that illustrates the cold-start-to-warm-state transition:

**Table 4.26: Cold Start → Warm State Transition (Phase A1)**

| Decision | Action | p99 (ms) | Weights | State |
|----------|--------|----------|---------|-------|
| 2 | MAINTAIN | 6,516 | 100/0 | Pre-serverless (SLO violation) |
| 3 | SCALE_OUT | 3,648 | 90/10 | First cold start engagement |
| 4 | SCALE_OUT | 2,060 | 80/20 | Cold start absorbing |
| 5 | SCALE_OUT | 1,120 | 70/30 | Ramp |
| 6 | SCALE_OUT | 632 | 60/40 | Near warm |
| 7 | SCALE_OUT | 278 | 50/50 | Approaching warm |
| 8 | OPTIMIZE_COST | 110 | 55/45 | **Warm state** |

The p99 latency drops from 3,648ms (first cold start engagement at 90/10 weights) to 110ms (warm state at 55/45 weights) across six decisions—a 33× reduction. The high initial latencies (3,648ms, 2,060ms) compound the SLO violation from increased load with the cold start penalty from Knative pod initialization.

### 4.5.5 Implications

At 100 RPS over 300 seconds (30,000 total requests), the cold start window affects approximately 50 requests (10% weight × 100 RPS × 5 seconds during first SCALE_OUT). This represents 0.17% of total requests—below the 1% threshold that defines p99. However, cold starts coincide with SLO violations (the trigger for SCALE_OUT), creating a compounding effect: cold-start-affected requests (682–1,235ms) combine with the broader violation population (200–3,000ms) to inflate aggregate p99 beyond what either factor would produce alone.

For production deployments, setting `minScale=1` would eliminate the cold start penalty entirely, removing a significant confounding factor from performance comparisons and reducing the observed 826ms overhead.

---
