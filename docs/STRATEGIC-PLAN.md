# Thesis Strategic Plan

**Updated**: January 2026  
**Status**: Active Planning Document  
**Thread Reference**: http://127.0.0.1:8317/threads/T-019bb88a-01c6-7653-afec-5aaa2c6d0618

---

## Executive Summary

This strategic plan defined how to evaluate a **hybrid approach (K8s + Serverless)** and **prediction-based routing** against baseline scenarios.

### Core Thesis Statement
> In a heterogeneous cloud environment, an SLO-aware hybrid autoscaling and routing mechanism using workload prediction can be evaluated against pure Kubernetes, pure serverless, and reactive-only hybrid approaches for mechanism validity, SLO behavior, and workload-dependent cost outcomes.

### Current Alignment Note

This document is a planning artifact. Current thesis-facing claims should follow `results/claims/CLAIMS_TO_EVIDENCE.md` and rerun-v2 cost framing: cost rankings are workload- and execution-signal-dependent, and rerun-v2 (`n=1`) is directional rather than inferential.

---

## Hypothesis Hierarchy

| Level | Hypothesis | What to Evaluate | Evaluation Method |
|-------|------------|---------------|-------------------|
| **H1 (System)** | Hybrid > Pure approaches | Whether hybrid mechanism and outcomes exceed pure baselines under valid conditions | Scenario 1,2 vs 4 comparison |
| **H2 (Control)** | Predictive > Reactive | Whether prediction improves SLO/cost outcomes vs reactive hybrid under valid conditions | Scenario 3 vs 4 comparison |
| **H3 (Model)** | GRU justification | GRU provides adequate prediction for the controller | Offline RMSE + closed-loop validation |

### Key Insight
> H1 and H2 are the main comparative contributions, while H3 supports model adequacy. Superiority conclusions depend on experiment validity and should be framed conservatively when evidence is non-inferential.

---

## Evaluation Scenarios (From Thesis Proposal 3.5.2)

| Scenario | Configuration | Purpose |
|----------|---------------|---------|
| **S1: K8s-Only** | All traffic → Kubernetes | Baseline: traditional container orchestration |
| **S2: Serverless-Only** | All traffic → Knative | Baseline: pure FaaS approach |
| **S3: Hybrid Reactive** | Algorithm 1 (SLO-based routing), no prediction | Control: hybrid without prediction |
| **S4: Hybrid Predictive** | Algorithm 1 + Algorithm 2 (GRU prediction) | Proposed: full system |

### Comparison Matrix

| Comparison | Tests Hypothesis | Expected Result |
|------------|------------------|-----------------|
| S4 vs S1 | H1 (Hybrid > K8s) | Evaluate latency/SLO tradeoffs under controlled load |
| S4 vs S2 | H1 (Hybrid > Serverless) | Evaluate cost/latency tradeoffs by workload profile |
| S4 vs S3 | H2 (Predictive > Reactive) | Evaluate SLO violations and preemptive actions |
| GRU vs LR (offline) | H3 (Model choice) | Justify GRU selection |

---

## Phase Plan

### Phase 0: Sprint 2 Validation (Now → 1 week)

**Goal**: Validate existing 2,677 lines of Sprint 2 code against real infrastructure

**Tasks**:
- [ ] Start prediction_server, verify API endpoints
- [ ] Test data_collector against real HAProxy stats
- [ ] Verify weight_adjuster with HAProxy admin socket
- [ ] Execute one complete routing cycle end-to-end
- [ ] Measure baseline RMSE with current linear model

**Success Criteria**:
- System runs stable for 10+ minutes
- API responds correctly to prediction requests
- Weight adjustments reflect in HAProxy

---

### Phase 1: Four Scenarios Infrastructure (1-2 weeks)

**Goal**: Build infrastructure to run all 4 evaluation scenarios

**Tasks**:
- [ ] **S1 Setup**: K8s-only routing configuration
- [ ] **S2 Setup**: Serverless-only routing configuration  
- [ ] **S3 Setup**: Reactive hybrid (Algorithm 1 without prediction)
- [ ] **S4 Setup**: Full predictive hybrid (current Sprint 2)
- [ ] Load test scripts for: steady, spike, endurance patterns
- [ ] Metrics collection: p50/p95/p99 latency, error rate, cost proxy

**Deliverable**: `./run-scenario.sh [s1|s2|s3|s4] [steady|spike|endurance]`

---

### Phase 2: GRU Implementation (2 weeks)

**Goal**: Implement GRU predictor and validate against LR baseline

**Tasks**:
- [ ] Download and process ClarkNet + Calgary datasets
- [ ] Implement GRU training pipeline (`controller/prediction/gru_predictor.py`)
- [ ] Run offline comparison: GRU vs LR vs naive baselines
- [ ] Generate thesis-ready comparison table (RMSE, MAE, MAPE)
- [ ] Integrate best model into prediction_server

**Success Criteria**:
- RMSE < 10% of average traffic (thesis target)
- Training pipeline reproducible with fixed seeds

---

### Phase 3: Full Evaluation (2-3 weeks)

**Goal**: Run complete evaluation across all 4 scenarios with real datasets

**Experiments**:
```
For each scenario [S1, S2, S3, S4]:
  For each workload [steady, spike, endurance]:
    For each dataset [ClarkNet, Calgary]:
      Run 3 repetitions
      Collect: p50, p95, p99, error_rate, resource_usage, cost_proxy
```

**Tasks**:
- [ ] Execute experiment matrix (4 × 3 × 2 × 3 = 72 runs)
- [ ] Statistical analysis with confidence intervals
- [ ] Generate comparison tables and figures
- [ ] Document anomalies and edge cases

**Deliverables**:
- Table: H1 proof (S4 vs S1, S4 vs S2)
- Table: H2 proof (S4 vs S3)
- Figure: Latency distribution per scenario
- Figure: Cost comparison across workload patterns

---

### Phase 4: Thesis Writing (2-3 weeks)

**Goal**: Write thesis chapters with reproducible results

**Chapter Structure**:
- **Chapter 4: Results**
  - 4.1 Prediction Model Evaluation (H3)
  - 4.2 Hybrid vs Pure Approaches (H1)
  - 4.3 Predictive vs Reactive Control (H2)
- **Chapter 5: Discussion**
  - When hybrid excels vs when it doesn't
  - Cost-benefit analysis
  - Limitations and threats to validity
- **Appendix**: Reproducibility instructions

---

## Project Structure

```
├── AGENTS.md                    # Project context + agent instructions
├── experiments/                 # Experiment tracking
│   ├── scenarios/              # S1, S2, S3, S4 configurations
│   ├── workloads/              # steady, spike, endurance configs
│   ├── runs/                   # Timestamped run outputs
│   └── experiments.db          # SQLite tracking
├── controller/prediction/         # ML model implementations
│   ├── baselines/
│   │   ├── naive.py            # Last-value baseline
│   │   └── moving_avg.py       # Moving average
│   ├── linear_model.py         # From sprint-2
│   └── gru_predictor.py        # GRU implementation
├── data/                        # Datasets
│   ├── raw/                    # Original logs
│   │   ├── clarknet/
│   │   └── calgary/
│   └── processed/              # RPS time series
├── sprint-1/                    # ✅ Complete - Hybrid infrastructure
├── sprint-2/                    # 🔧 Validation needed - Prediction engine
├── docs/
│   ├── thesis-proposal/        # Extracted proposal
│   └── thesis-implementation/  # Experiment → Chapter mapping
└── results/                     # Final thesis results
    ├── tables/                 # LaTeX-ready tables
    ├── figures/                # Publication-quality figures
    └── raw/                    # Raw experiment data
```

---

## Metrics & Targets (From Thesis Proposal)

### Performance Metrics

| Metric | Description | Target | Measured In |
|--------|-------------|--------|-------------|
| p50 Latency | Median response time | < 50ms | All scenarios |
| p95 Latency | 95th percentile | < 100ms | All scenarios |
| p99 Latency | Tail latency (SLO) | < 200ms | All scenarios |
| Error Rate | Failed requests | < 0.1% | All scenarios |
| Throughput | Requests/second | No degradation | All scenarios |

### Prediction Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| RMSE | Root Mean Square Error | < 10% of avg traffic |
| MAE | Mean Absolute Error | < 5% of avg traffic |
| MAPE | Mean Absolute Percentage Error | < 15% |

### Cost Metrics

| Metric | Description | Expected Result |
|--------|-------------|-----------------|
| K8s Cost | Resource hours × unit cost | Baseline reference under warm-capacity assumptions |
| Serverless Cost | Invocations × time × unit cost | Sensitive to execution-time signal and concurrency |
| Hybrid Cost | K8s + Serverless | Workload- and routing-policy-dependent (no fixed ordering) |

---

## Validation Milestones

| Milestone | Phase | Criteria | Proves |
|-----------|-------|----------|--------|
| **M1** | Phase 0 | Sprint 2 runs end-to-end | Infrastructure ready |
| **M2** | Phase 1 | All 4 scenarios executable | Evaluation framework ready |
| **M3** | Phase 2 | GRU RMSE < 10% | H3 (model adequate) |
| **M4** | Phase 3 | Valid comparison dataset produced for S4 vs S1/S2 | H1 evaluation readiness |
| **M5** | Phase 3 | Valid comparison dataset produced for S4 vs S3 | H2 evaluation readiness |

---

## Contingency Branches

```
                    ┌─── S4 beats S1 & S2 ──► H1 PROVEN ✅
                    │
Phase 3 (H1) ───────┤
                    │
                    └─── S4 ≈ or worse ──► Analyze specific conditions where hybrid helps
                    
                    ┌─── S4 beats S3 ──► H2 PROVEN ✅
                    │
Phase 3 (H2) ───────┤
                    │
                    └─── S4 ≈ S3 ──► "Prediction overhead may not justify benefit under X conditions"
                    
                    ┌─── GRU >> LR ──► Strong model contribution
                    │
Phase 2 (H3) ───────┼─── GRU ≈ LR ──► "GRU chosen for pattern learning; LR sufficient for simple cases"
                    │
                    └─── GRU < LR ──► "GRU overfits; simpler models preferred for this domain"
```

**Key**: Even if H3 shows GRU ≈ LR, the thesis still succeeds if H1 and H2 are proven.

---

## Immediate Actions (Next Week)

### Priority 1: Sprint 2 Validation
```bash
cd sprint-2

# 1. Test prediction server
uv run python -m prediction_engine.prediction_server &
curl http://localhost:8090/health
curl -X POST http://localhost:8090/predict -d '{"current_rps": 100}'

# 2. Test with Sprint 1 infrastructure
cd ../sprint-1 && ./scripts/setup.sh
cd ../sprint-2

# 3. Test HAProxy weight adjustment
uv run python -c "
from intelligent_router.weight_adjuster import HAProxyWeightAdjuster
adjuster = HAProxyWeightAdjuster()
print(adjuster.test_connection())
"

# 4. Execute one routing cycle
uv run python -m intelligent_router.routing_controller --once
```

### Priority 2: Scenario Infrastructure
```bash
# Create scenario configurations
# NOTE: experiments/scenarios/ is now archived at archived/experiments-framework/

# Create scenario runner script
# ./run-scenario.sh [s1|s2|s3|s4] [steady|spike|endurance]
```

---

## Beads to Create

Based on this plan:

1. **Phase 0: Sprint 2 Validation** (P0, epic) - existing, update notes
2. **Phase 1: Scenario Infrastructure** (P0, epic)
   - S1 K8s-only setup (task)
   - S2 Serverless-only setup (task)
   - S3 Reactive hybrid setup (task)
   - Scenario runner script (task)
3. **Phase 2: GRU Implementation** (P1, epic)
   - Dataset processing pipeline (task)
   - GRU training script (task)
   - Model comparison (task)
4. **Phase 3: Full Evaluation** (P1, epic)
   - H1 evaluation (task)
   - H2 evaluation (task)
   - Results analysis (task)
5. **Phase 4: Thesis Writing** (P2, epic)

---

## References

- Thesis Proposal: `docs/thesis-proposal/03-methodology.md`
- Sprint 1 Results: `sprint-1/results/performance-baseline.md`
- Sprint 2 Code: `sprint-2/` (2,677 lines, validation pending)
- Algorithm 1: Routing Controller (Thesis Proposal Section 3.4.3.1)
- Algorithm 2: Cluster Controller (Thesis Proposal Section 3.4.3.2)
