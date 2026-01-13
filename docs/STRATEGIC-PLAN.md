# Thesis Strategic Plan

**Generated**: January 2026  
**Status**: Active Planning Document  
**Thread Reference**: http://127.0.0.1:8317/threads/T-019bb86b-46e3-72db-bd8e-5d6e7a024749

---

## Executive Summary

This thesis is **experimental** - the GRU-based approach may not outperform simpler methods. The strategy below assumes uncertainty and provides contingency branches.

### Key Insight
> Design the work so you can **graduate even if GRU is not better** than simple models. The thesis becomes about **systematic comparison and hybrid decision-making**, not "GRU wins."

---

## Hypothesis Hierarchy

| Level | Hypothesis | Fallback if False |
|-------|------------|-------------------|
| **H1** | A learned predictor (LR/GRU) can forecast traffic with RMSE <10% | Focus on "why prediction is hard" + SLO-reactive control |
| **H2** | Prediction-based routing improves SLO compliance vs reactive | Analyze when proactive control harms SLOs |
| **H3** | GRU outperforms linear regression | Document "GRU not superior under resource constraints" |

---

## Phase Plan (Replaces Sprint 2-5)

### Phase 0: Consolidation (Now → 2 weeks)

**Goal**: Setup experiment tracking + MVE-1 (offline LR vs baselines)

**Tasks**:
- [ ] Create `experiments/` directory structure
- [ ] Implement `experiment_logger.py` (SQLite-based)
- [ ] Process ClarkNet dataset → RPS time series
- [ ] Run LR vs naive baselines offline
- [ ] Generate first thesis-ready table/plot

**Go/No-Go Criteria**:
- ✅ Go: LR outperforms naive baselines
- ⚠️ Partial: LR ≈ naive → adjust thesis to "prediction difficulty analysis"
- ❌ No-Go: Pipeline fails → fix data processing before continuing

---

### Phase 1: Sprint 2 Validation (2 weeks)

**Goal**: Validate existing code against real HAProxy

**Tasks**:
- [ ] Get prediction_server running with health checks
- [ ] Test data_collector against real HAProxy stats
- [ ] Verify weight_adjuster with HAProxy admin socket
- [ ] Add minimal pytest coverage
- [ ] Measure actual RMSE in live environment

**Go/No-Go Criteria**:
- ✅ Go: System stable enough for long tests
- ❌ No-Go: Too brittle → shift to simulation/replay mode

---

### Phase 2: GRU Implementation + Comparison (3 weeks)

**Goal**: Implement GRU and compare offline vs LR

**Tasks**:
- [ ] Implement GRU training script (`ml_models/gru_predictor.py`)
- [ ] Run controlled experiments on ClarkNet + Calgary
- [ ] Fixed horizon (30s), fixed splits (70/15/15)
- [ ] Log all runs via experiment logger
- [ ] Generate comparison tables/plots

**Go/No-Go Criteria**:
- ✅ Go: GRU clearly better → use in live controller
- ⚠️ Partial: GRU ≈ LR → keep LR as main, GRU as secondary
- ❌ No-Go: GRU worse → thesis about "why GRU doesn't help here"

---

### Phase 3: SLO Monitoring + Closed-Loop (3 weeks)

**Goal**: Implement Algorithm 1 and run full experiments

**Scenarios to Test**:
1. Static 80/20 routing (baseline)
2. Reactive-only routing (Algorithm 1, no prediction)
3. Proactive routing with LR
4. Proactive routing with GRU (if Phase 2 positive)

**Tasks**:
- [ ] Implement SLO monitoring (p99 from Prometheus/HAProxy)
- [ ] Wire Algorithm 1 to existing router
- [ ] Run load tests: steady, spike, endurance
- [ ] Collect per-scenario metrics

**Go/No-Go Criteria**:
- ✅ Go: Any improvement with prediction → strong result
- ❌ No-Go: No improvement → "limits of proactive control" paper

---

### Phase 4: Thesis Writing (2-3 weeks)

**Goal**: Write thesis with reproducible experiments

**Deliverables**:
- Chapter 4: Results (structured by hypotheses)
- Chapter 5: Discussion (when prediction helps/hurts)
- Reproducibility appendix
- Academic paper draft

---

## Project Structure (Recommended)

```
├── AGENTS.md                    # LLM workflow
├── CLAUDE.md                    # Project context
├── experiments/                 # NEW: Experiment tracking
│   ├── offline-prediction/
│   │   ├── configs/            # YAML experiment configs
│   │   └── runs/               # Timestamped run outputs
│   ├── closed-loop/
│   │   ├── scenarios/          # Load test scenarios
│   │   └── runs/               # Run outputs
│   ├── experiments.db          # SQLite tracking
│   └── experiment_logger.py    # Logging utility
├── ml_models/                   # NEW: ML model implementations
│   ├── baselines/
│   │   ├── naive.py            # Last-value baseline
│   │   └── moving_avg.py       # Moving average
│   ├── linear_model.py         # From sprint-2 (refactored)
│   └── gru_predictor.py        # GRU implementation
├── data/                        # Datasets
│   ├── raw/                    # Original logs
│   │   ├── clarknet/
│   │   └── calgary/
│   └── processed/              # RPS time series
├── sprint-1/                    # Baseline infrastructure (keep as-is)
├── sprint-2/                    # V1 Decision Engine (keep, validate)
├── docs/
│   ├── thesis-proposal/        # Extracted proposal
│   ├── thesis-implementation/  # Experiment → Chapter mapping
│   └── ...
└── results/                     # Final thesis results
    ├── tables/
    ├── figures/
    └── raw/
```

---

## Experiment Tracking (Lightweight MLOps)

### What to Track Per Run

```yaml
run_id: "20260115-1430_gru_clarknet_30s"
git_commit: "abc1234"
model_type: "gru"
dataset: "clarknet"
data_window: "days_1_3"
prediction_horizon: 30
hyperparameters:
  units: 64
  layers: 2
  dropout: 0.2
  learning_rate: 0.001
  batch_size: 32
  epochs: 100
metrics:
  rmse: 8.5
  mae: 5.2
  mape: 12.3
  training_time_sec: 450
environment:
  python: "3.13"
  sklearn: "1.4.0"
  torch: "2.2.0"
```

### SQLite Schema

```sql
CREATE TABLE runs (
    run_id TEXT PRIMARY KEY,
    timestamp TEXT,
    git_commit TEXT,
    model_type TEXT,
    dataset TEXT,
    horizon INTEGER,
    config_json TEXT
);

CREATE TABLE metrics (
    run_id TEXT,
    metric_name TEXT,
    metric_value REAL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);
```

---

## Validation Milestones

| Milestone | Phase | Criteria | Decision |
|-----------|-------|----------|----------|
| **M1** | Phase 0 | LR RMSE computed, outperforms naive | Go/No-Go for prediction approach |
| **M2** | Phase 1 | Sprint 2 validated against HAProxy | Go/No-Go for live experiments |
| **M3** | Phase 2 | GRU vs LR comparison complete | Choose primary model |
| **M4** | Phase 3 | Closed-loop benefits measured | Determine thesis contribution |

---

## Immediate Actions (Next 2 Weeks)

### Week 1: Experiment Infrastructure

```bash
# 1. Create experiment structure
mkdir -p experiments/{offline-prediction,closed-loop}/{configs,runs}
mkdir -p ml_models/baselines
mkdir -p data/{raw,processed}/{clarknet,calgary}
mkdir -p results/{tables,figures,raw}

# 2. Create experiment logger
# 3. Download ClarkNet dataset
# 4. Implement CLF → RPS pipeline
```

### Week 2: First Results

```bash
# 1. Run LR vs naive comparison
# 2. Validate Sprint 2 with HAProxy
# 3. Add minimal pytest
# 4. Generate first thesis table
```

---

## Contingency Branches

```
                    ┌─── LR works ──► Phase 2 (GRU comparison)
                    │
Phase 0 (MVE-1) ────┤
                    │
                    └─── LR fails ──► Pivot to "prediction difficulty" thesis
                    
                    ┌─── GRU better ──► Use GRU in Phase 3
                    │
Phase 2 (GRU) ──────┼─── GRU ≈ LR ───► Keep LR, GRU as secondary
                    │
                    └─── GRU worse ──► "Why GRU doesn't help" contribution
                    
                    ┌─── Prediction helps ──► Strong positive result
                    │
Phase 3 (Closed) ───┤
                    │
                    └─── No improvement ──► "Limits of proactive control"
```

---

## Beads to Create

Based on this plan, create the following beads:

1. **Phase 0: Experiment Infrastructure** (P0, epic)
2. **Phase 0: CLF to RPS Pipeline** (P0, task)
3. **Phase 0: LR vs Naive Comparison** (P0, task)
4. **Phase 1: Sprint 2 Validation** (P0, epic) - existing beads
5. **Phase 2: GRU Implementation** (P1, epic)
6. **Phase 3: SLO Monitoring** (P1, epic)
7. **Phase 4: Thesis Writing** (P2, epic)

---

## References

- TU Dublin 2025: "Business-Day Cloud: Hybrid K8s-Serverless"
- ACM ICPE 2023: "Autoscaler Evaluation: A Practitioner's Guideline"
- Wandb: "Intro to MLOps: ML Experiment Tracking"
- PMC 2024: "Auto-Scaling Techniques in Cloud Computing"
