# Thesis: Hybrid Kubernetes-Serverless Integration with GRU-Based Workload Prediction

**Master's Thesis in Computer Science**

## Abstract

This research proposes a hybrid system integrating Kubernetes and serverless computing for optimizing traffic distribution based on workload prediction. Using a GRU-based prediction algorithm, the system proactively adjusts resource allocation between K8s clusters and serverless functions, minimizing SLA violations while improving cost efficiency.

## Validated Hypotheses (Simulation-Based Validation)

| Hypothesis | Description | Result | Key Evidence |
|------------|-------------|--------|--------------|
| **H1** | Hybrid > Pure Systems | ✅ VALIDATED | 0% error vs 72-93% error for pure backends; 5.7ms p95 vs 23-60s |
| **H2** | Predictive > Reactive | ✅ PARTIALLY VALIDATED | 4 PREDICTIVE decisions (31%); identical metrics but proactive behavior |

**Note:** These results are from simulation-based validation using a custom serverless-activator (deterministic 5s cold start, 80/20 default weights). See Chapter 4 for validity statement.

## Thesis Structure

### Part I: Introduction and Background

| Chapter | Title | Location |
|---------|-------|----------|
| 1 | Introduction | [../thesis-proposal/01-introduction.md](../thesis-proposal/01-introduction.md) |
| 2 | Literature Review | [../thesis-proposal/02-literature-review.md](../thesis-proposal/02-literature-review.md) |
| 3 | Methodology | [../thesis-proposal/03-methodology.md](../thesis-proposal/03-methodology.md) |

### Part II: Results and Analysis

| Chapter | Title | Location | Status |
|---------|-------|----------|--------|
| 4 | Results and Evaluation | [chapter-4-results.md](chapter-4-results.md) | ✅ Complete |
| 5 | Discussion | [chapter-5-discussion.md](chapter-5-discussion.md) | ✅ Complete |
| 6 | Conclusion | [chapter-6-conclusion.md](chapter-6-conclusion.md) | ✅ Complete |

### Appendices

| Appendix | Title | Location | Status |
|----------|-------|----------|--------|
| A | Reproducibility Guide | [appendix-a-reproducibility.md](appendix-a-reproducibility.md) | ✅ Complete |
| B | Algorithm Pseudocode | [appendix-b-algorithms.md](appendix-b-algorithms.md) | ✅ Complete |
| C | Raw Data Tables | `controller/results/evaluations/` | ✅ Available |
| D | Source Code | `controller/` | ✅ Available |

## Evaluation Scenarios

| Scenario | Configuration | Purpose |
|----------|---------------|---------|
| S1 | K8s-only (100% k3s) | Baseline for container orchestration |
| S2 | Serverless-only (100% Knative) | Baseline for serverless computing |
| S3 | Hybrid-reactive | Algorithm 1 without prediction |
| S4 | Hybrid-predictive | Algorithm 1 + GRU prediction (proposed) |

## Key Results (simulated-v1)

| Scenario | Configuration | Error Rate | p95 Latency | Throughput |
|----------|---------------|------------|-------------|------------|
| S1 | K8s-only (100/0) | 72.62% | 60,002ms | 13.7 req/s |
| S2 | Serverless-only (0/100) | 92.83% | 23,158ms | 45.8 req/s |
| S3 | Hybrid-reactive (80/20) | **0%** | **5.7ms** | 65.7 req/s |
| S4 | Hybrid-predictive (80/20) | **0%** | **5.7ms** | 65.8 req/s |

## Key Metrics

- **SLO Target**: p99 latency < 200ms with 30-second violation detection window
- **Cost Model**: Normalized proxy combining K8s resource hours + serverless invocations
- **Prediction Accuracy**: RMSE as percentage of average traffic volume

## Data Sources

- **Simulation Results**: `infrastructure/results/simulated-v1/`
- **S1-S4 Summaries**: `s1-spike-summary.json` through `s4-spike-summary.json`
- **Experiment Documentation**: `docs/EXPERIMENT_RESULTS.md`
- **Training Data**: ClarkNet and Calgary HTTP trace logs

## Implementation Statistics

- **Tests Passing**: 178
- **Lines of Python**: ~10,600
- **ML Models Trained**: GRU, LSTM, Linear Regression baselines

## Keywords

Cloud Computing, Kubernetes, Serverless, Workload Prediction, GRU, Traffic Distribution, SLA, SLO, Hybrid Architecture
