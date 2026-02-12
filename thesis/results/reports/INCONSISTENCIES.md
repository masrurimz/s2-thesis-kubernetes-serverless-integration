# Known Inconsistencies & Resolutions

**Date:** 2026-02-13
**Purpose:** Audit trail of inconsistencies found during thesis evidence validation.

---

## Resolved Inconsistencies

### 1. Hypothesis Validation Report vs Honest Assessment
- **Issue:** `results/HYPOTHESIS_VALIDATION_REPORT.md` claimed "ALL HYPOTHESES VALIDATED" using cherry-picked stress test throughput numbers, while `thesis/appendices/PHASE_B_HONEST_ASSESSMENT.md` shows H1 p=0.0677 (not significant) and H2 had no difference.
- **Resolution:** HYPOTHESIS_VALIDATION_REPORT.md rewritten to align with honest assessment. Now correctly reports mechanism validation only.

### 2. GRU Training Data: Synthetic vs Real
- **Issue:** Thesis proposal (Section 3.2) specifies ClarkNet and Calgary HTTP traces for training. Actual GRU training used synthetic data.
- **Resolution:** Documented in CLAIMS_TO_EVIDENCE.md. ClarkNet/Calgary parquets exist in `data/processed/` and were used for model comparison evaluation, but GRU was trained on synthetic patterns. Acknowledged as threat to validity.

### 3. Model Format: PyTorch vs Joblib
- **Issue:** `GRU_TRAINING_RESULTS.md` references `gru_model.pt` (PyTorch), while `STRESS_TEST_SUMMARY.md` mentions loading `gru_model.joblib` (sklearn).
- **Resolution:** Two implementations existed during development. The canonical model is `gru_model.pt` (PyTorch). The joblib reference was from an earlier sklearn-based model loader that wraps the PyTorch model. Both are valid representations of the same model.

### 4. Empty thesis/results/raw/ Directories
- **Issue:** Documentation referenced `thesis/results/raw/` paths that were empty.
- **Resolution:** Populated with actual data from scattered locations (results/, infrastructure/results/, etc.).

### 5. Non-existent Evidence Paths
- **Issue:** CLAIMS_TO_EVIDENCE.md referenced paths that didn't exist (e.g., `results/phase_b/experiments_final.json`).
- **Resolution:** Paths updated to point to actual file locations in the canonical `thesis/results/` structure.

### 6. Stress Test Error Rates vs Proposal Targets
- **Issue:** Proposal targets error rate < 0.1%, but stress tests show 79-97% error rates.
- **Resolution:** Stress tests were intentional saturation tests, not SLO compliance tests. Documented as separate from controlled experiments. Phase B experiments at 100 RPS had 0% error rate but insufficient to stress the system.

---

## Acknowledged Limitations (Not Resolved)

### 1. k3d Localhost Bias
S1 (K8s-only) benefits from localhost routing, making it artificially fast. Cannot be resolved without multi-node or cloud deployment.

### 2. Load Insufficiency  
100 RPS insufficient to demonstrate predictive advantage. Higher load or real cloud deployment needed.

### 3. Missing MAE Evaluation
Proposal targets MAE < 5% but MAE was not reported as percentage in results. Raw MAE=4.91 requests exists but percentage was not computed against average.

### 4. Cost Analysis is Proxy-Based
Proposal asks for real cost comparison. Only proxy/estimated costs were computed, not actual billing data.
