# Thesis Proposal

**Title (Indonesian)**: Pengambilan Keputusan dan Pengaturan Skalabilitas Elastis pada Lingkungan Cloud yang Heterogen dengan Berbasiskan pada Prediksi Workload

**Title (English)**: Decision Making and Elastic Scalability Management in Heterogeneous Cloud Environments Based on Workload Prediction

**Author**: Muhammad Zahid Masruri  
**NRP**: 6025222041  
**Institution**: Institut Teknologi Sepuluh Nopember  
**Year**: 2024

---

## Document Structure

| File | Content |
|------|---------|
| [00-abstract.md](./00-abstract.md) | Abstract (Indonesian & English) |
| [01-introduction.md](./01-introduction.md) | Chapter 1: Background, Problem Formulation, Objectives |
| [02-literature-review.md](./02-literature-review.md) | Chapter 2: Cloud Computing, K8s, Serverless, Prediction Algorithms |
| [03-methodology.md](./03-methodology.md) | Chapter 3: Research Methodology, System Design, Algorithms |
| [04-references.md](./04-references.md) | References |

---

## Quick Reference

### Research Questions

1. How to design workload traffic prediction for an application using GRU?
2. How to design and perform decision making by modifying ElaX for scaling on a server cluster and distributing traffic to different cluster types?
3. How to evaluate the modified ElaX mechanism for automatic scaling and load distribution in Kubernetes and serverless integration?

### Key Contributions

1. **GRU-based Workload Prediction**: Multi-point traffic prediction (30 seconds ahead)
2. **Modified ElaX Algorithm**: Hybrid K8s-serverless routing with SLO-awareness
3. **Comprehensive Evaluation Framework**: RMSE accuracy, latency, cost analysis

### Core Algorithm

**Routing Controller** (Algorithm 1):
- Monitor tail latency (p99) against SLO threshold
- 5-second violation detection window
- Binary routing: K8s ↔ Serverless

### Resource Allocation Model

$$R = \alpha \cdot x + \beta$$

Where:
- $R$: CPU resources required
- $x$: Traffic volume (requests/second)
- $\alpha, \beta$: OLS-derived coefficients

### Datasets

| Dataset | Description |
|---------|-------------|
| ClarkNet | ~2M HTTP requests from ClarkNet WWW server |
| Calgary | ~2M HTTP requests from University of Calgary CS Department |
