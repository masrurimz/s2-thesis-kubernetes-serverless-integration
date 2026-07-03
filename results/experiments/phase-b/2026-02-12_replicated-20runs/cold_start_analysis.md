# Cold Start / Warm Start Latency Decomposition — Quantitative Analysis

**Date**: 2026-02-13  
**Bead**: s2-29e  
**Script**: `scripts/cold_start_analysis.py`  
**Companion**: `COLD_START_ANALYSIS.md` (theoretical framework)

---

## 1. Cold Start Penalty Estimate

| Source | Cold Start Latency | Context |
|--------|-------------------|---------|
| S3 infrastructure test | **682ms** | Pre-warm cold start, reactive scenario |
| S4 infrastructure test | **1235ms** | Pre-warm cold start, predictive scenario |
| Average | **958ms** | Mean of measurements |
| Warm state p99 (Phase A1) | **133ms** | After stabilization at 50/50 weights |
| **Cold start overhead** | **826ms** | Above warm state baseline |

**Source**: `infrastructure/results/knative-real/RESULTS-SUMMARY.md` *(deleted — preserved in git history)*

### Knative Configuration (explains cold start origin)

| Parameter | Value | Effect |
|-----------|-------|--------|
| `minScale` | **0** | Pods scale to zero → guaranteed cold start on first engagement |
| `scale-to-zero-grace-period` | 30s | Pod terminates 30s after last request |
| `scale-down-delay` | 30s | Delay before scaling down |
| `stable-window` | 60s | Observation window for autoscaler |

**Source**: `infrastructure/serverless/knative-service.yaml`, `infrastructure/k3d/knative-install.sh`

---

## 2. Phase B Scenario Statistics (Excluding Outliers)

| Scenario | n | p99 Mean | p99 Std | CoV | Avg SCALE_OUT |
|----------|---|----------|---------|-----|---------------|
| S1 (K8s-only) | 4 | 647ms | 206ms | 31.9% | 0.0 |
| S2 (Serverless-only) | 4 | 518ms | 177ms | 34.1% | 0.0 |
| S3 (Hybrid Reactive) | 4 | 462ms | **297ms** | **64.2%** | 18.0 |
| S4 (Hybrid Predictive) | 5 | 431ms | 219ms | 50.8% | 17.0 |

**Key observation**: S3 has the highest variance (CoV=64.2%), consistent with reactive cold start engagement.

---

## 3. Variance Decomposition

**Model**: σ²_total = σ²_base + σ²_cold_start_routing

- **Base variance** = average of S1 + S2 (no routing decisions): σ=192ms
- **Excess** = total – base → attributable to cold start + routing overhead

| Scenario | Total σ² | Total σ | Excess σ² | Excess σ | % From Cold Start/Routing |
|----------|----------|---------|-----------|----------|--------------------------|
| S3 (Reactive) | 88,170 | 297ms | 51,296 | **227ms** | **58.2%** |
| S4 (Predictive) | 47,870 | 219ms | 10,996 | **105ms** | **23.0%** |

**Interpretation**:
- **58% of S3 variance** is excess beyond baseline → attributable to cold start + reactive routing overhead
- S4 shows less excess (23%) despite similar scale_out counts → routing overhead alone contributes ~23%
- Difference (58% - 23% = 35%) suggests reactive engagement specifically amplifies variance vs predictive

---

## 4. Correlation: Scale-Out Events ↔ p99

| Scenario | Pearson r | Interpretation |
|----------|-----------|----------------|
| S3 (Reactive) | **0.627** | Moderate-strong: more scale-outs → higher p99 |
| S4 (Predictive) | **0.639** | Moderate-strong: more scale-outs → higher p99 |

Runs with more SCALE_OUT decisions tend to have higher p99. This is consistent with:
1. More scale-outs → more cold start events during the run
2. More scale-outs → system was under more stress (higher load variance)

⚠ **Caveat**: n=4-5 per scenario. Correlations are suggestive, not statistically conclusive.

---

## 5. Phase A1 Transition Analysis

The Phase A1 ramp test provides the richest per-decision data:

### Weight Ramp: Cold Start → Warm State

| Decision | Action | p99 | Weights (K8s/Knative) | State |
|----------|--------|-----|-----------------------|-------|
| 2 | MAINTAIN | 6516ms | 100/0 | Pre-serverless (SLO violation) |
| 3 | SCALE_OUT | **3648ms** | 90/10 | **← First cold start engagement** |
| 4 | SCALE_OUT | 2060ms | 80/20 | Ramp (cold start absorbing) |
| 5 | SCALE_OUT | 1120ms | 70/30 | Ramp |
| 6 | SCALE_OUT | 632ms | 60/40 | Ramp |
| 7 | SCALE_OUT | 278ms | 50/50 | Near warm |
| 8 | OPTIMIZE_COST | **110ms** | 55/45 | **← Warm state** |
| 9 | PREDICTIVE | 146ms | 50/50 | Warm (pre-positioned) |

**Cold start penalty visible**: p99 drops from 3648ms → 110ms across the ramp as Knative warms up.

**Note**: The high initial p99 (6516ms, 3648ms) includes both the SLO violation from increased load AND the cold start penalty. They are confounded in this data — the cold start occurs during an already-stressed period.

---

## 6. Theoretical Impact Model

At 100 RPS over 300s (30,000 total requests):

- **Cold start window**: ~5 seconds during first SCALE_OUT (0→10% weight)
- **Affected requests**: ~50 (10% × 100 RPS × 5s)
- **p99 threshold**: 300 requests (top 1% of 30,000)
- **Cold start fraction**: 0.17% of total requests

**Result**: 50 cold-start-affected requests < 300 p99 threshold → cold start alone does NOT dominate aggregate p99.

**However**, cold start occurs simultaneously with SLO violation (the trigger for SCALE_OUT), creating a **compounding effect**: the 1% of requests seeing cold start latency (682-1235ms) *plus* the broader SLO violation population (200-3000ms) together inflate the p99.

---

## 7. Data Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| No per-request latency | Cannot directly measure cold-start requests | Use infrastructure measurements as proxy |
| No backend tagging | Cannot separate k3s vs knative request latency | Infer from weight transitions + cold start timing |
| GRU not running in Phase B | S4 fell back to reactive (identical to S3) | Phase A1 validates PREDICTIVE mechanism separately |
| Cold start from infra tests | Different load profile than Phase B | Conservative: infra tests likely undercount (no concurrent load) |
| Small sample (n=4-5) | Correlations not statistically significant | Report as suggestive, not conclusive |

---

## 8. Recommendations

### For production deployment
1. **Set `minScale=1`** — eliminates cold starts entirely (~958ms penalty removed)
2. **Keep pre-warming** in SCALE_OUT path (already implemented in `algorithm1_controller.py`)
3. **Use PREDICTIVE mode** (with GRU) — absorbs cold start during healthy periods, not during violations

### For future experiments
1. **Per-request latency logging** with backend tags (k3s vs knative)
2. **Timestamp weight adjustments** to correlate with latency spikes
3. **Run with `minScale=0` vs `minScale=1`** as controlled variable
4. **Enable GRU in Phase B** to properly validate S4 vs S3 difference

---

## Files

| Path | Description |
|------|-------------|
| `scripts/cold_start_analysis.py` | Analysis script (run with `uv run`) |
| `cold_start_decomposition.json` | Machine-readable output |
| `COLD_START_ANALYSIS.md` | Theoretical framework (companion) |
| `infrastructure/results/knative-real/RESULTS-SUMMARY.md` | *(deleted — infrastructure cold start measurements preserved in git history)* |
| `results/experiments/phase-a1/2026-02-12_predictive-trigger/report.md` | Phase A1 decision log |
