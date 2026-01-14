# Thesis: Hybrid Kubernetes-Serverless Integration with GRU-Based Workload Prediction

**Master's Thesis in Computer Science**

## Abstract

This research proposes a hybrid system integrating Kubernetes and serverless computing for optimizing traffic distribution based on workload prediction. Using a GRU-based prediction algorithm, the system proactively adjusts resource allocation between K8s clusters and serverless functions, minimizing SLA violations while improving cost efficiency.

## Validated Hypotheses

| Hypothesis | Description | Result | Key Metric |
|------------|-------------|--------|------------|
| **H1** | Hybrid > Pure Systems | ✅ PROVEN | 41% p99 latency improvement vs K8s; 42% cost reduction vs Serverless |
| **H2** | Predictive > Reactive | ✅ PROVEN | 74.5% SLO violation reduction; 76.1% proactive adjustment ratio |
| **H3** | GRU Model Justified | ✅ PROVEN | GRU RMSE 6.98% (target <10%); 39.7% better than Linear Regression |

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
| 6 | Conclusion | _To be written_ | ⏳ Pending |

### Appendices

| Appendix | Title | Status |
|----------|-------|--------|
| A | Reproducibility Guide | ⏳ Pending |
| B | Raw Data Tables | Available in `controller/results/evaluations/` |
| C | Source Code | Available in `controller/` |

## Evaluation Scenarios

| Scenario | Configuration | Purpose |
|----------|---------------|---------|
| S1 | K8s-only (100% k3s) | Baseline for container orchestration |
| S2 | Serverless-only (100% Knative) | Baseline for serverless computing |
| S3 | Hybrid-reactive | Algorithm 1 without prediction |
| S4 | Hybrid-predictive | Algorithm 1 + GRU prediction (proposed) |

## Key Metrics

- **SLO Target**: p99 latency < 200ms with 30-second violation detection window
- **Cost Model**: Normalized proxy combining K8s resource hours + serverless invocations
- **Prediction Accuracy**: RMSE as percentage of average traffic volume

## Data Sources

- **Model Comparison**: `results/tables/model_comparison.csv`
- **H1 Evaluation**: `controller/results/evaluations/h1/`
- **H2 Evaluation**: `controller/results/evaluations/h2/`
- **Training Data**: ClarkNet and Calgary HTTP trace logs

## Implementation Statistics

- **Tests Passing**: 178
- **Lines of Python**: ~10,600
- **ML Models Trained**: GRU, LSTM, Linear Regression baselines

## Keywords

Cloud Computing, Kubernetes, Serverless, Workload Prediction, GRU, Traffic Distribution, SLA, SLO, Hybrid Architecture
