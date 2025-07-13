# Thesis Implementation: ElaX-GRU Hybrid System

## Formal Research Documentation

This directory contains the formal implementation documentation for the thesis research:

**"Decision Making and Elastic Scalability Management in Heterogeneous Cloud Environments Based on Workload Prediction"**

## Research Objectives

The thesis demonstrates a novel hybrid architecture that:
- Implements **ElaX algorithm** with GRU-based workload prediction
- Uses **real HTTP trace data** from ClarkNet and Calgary datasets  
- Focuses on **tail latency optimization** with SLO-aware routing
- Employs **formal resource allocation** using R = α·x + β with OLS tuning
- Provides **comprehensive evaluation** with RMSE accuracy and cost analysis

## Documentation Structure

### [01-experiment-plan.md](01-experiment-plan.md)
**Complete ElaX-GRU Experiment Design**
- System architecture based on ElaX algorithm
- GRU workload predictor implementation
- Real dataset integration methodology
- Formal evaluation framework

### [02-methodology-implementation.md](02-methodology-implementation.md)  
**Detailed Technical Implementation**
- ClarkNet/Calgary dataset processing
- GRU model training pipeline
- Resource allocation model (R = α·x + β)
- Controller implementation (Algorithm 1)
- Comprehensive evaluation methodology

### [03-running-experiments.md](03-running-experiments.md)
**Formal Experiment Execution**
- SLO-focused monitoring setup
- Tail latency measurement procedures
- RMSE evaluation for GRU predictor
- Cost analysis with Google Cloud pricing
- Comparative analysis methodology

## Key Research Components

### 1. ElaX Algorithm Foundation
- **Base**: ElaX (Yang et al., 2019) with GRU modification
- **Enhancement**: GRU replaces LSTM based on efficiency findings (Mondal et al., 2023)
- **Integration**: Hybrid K8s-serverless routing strategy

### 2. GRU Workload Predictor
- **Model**: Multi-point prediction (30 seconds ahead)
- **Training Data**: ClarkNet and Calgary HTTP traces (4M+ requests)
- **Architecture**: GRU layers with dropout for efficiency
- **Evaluation**: RMSE metric for prediction accuracy

### 3. Formal Resource Allocation
- **Model**: Linear equation R = α·x + β
- **Tuning**: OLS (Ordinary Least Squares) using scikit-learn
- **Adaptation**: Online coefficient correction based on error feedback
- **Optimization**: Dynamic resource allocation for cost efficiency

### 4. SLO-Aware Routing
- **Metric**: 99th percentile tail latency monitoring
- **Threshold**: 5-second SLO violation detection window
- **Algorithm**: Routing Controller (Algorithm 1 from thesis)
- **Decision**: Binary routing between K8s and serverless

### 5. Comprehensive Evaluation
- **Predictor**: RMSE accuracy measurement
- **Performance**: Request running time, tail latency, throughput
- **Resource**: CPU/memory allocation and utilization
- **Cost**: Google Cloud pricing-based estimation
- **Comparison**: Control variables (deployment/scaling methods)

## Dataset Specifications

### ClarkNet HTTP Trace
- **Source**: ClarkNet WWW server logs
- **Format**: Combined Common Log Format (CLF)  
- **Volume**: ~2M HTTP requests
- **Period**: Historical web server access patterns

### Calgary University Trace
- **Source**: University of Calgary Computer Science Department
- **Format**: Combined Common Log Format (CLF)
- **Volume**: ~2M HTTP requests  
- **Pattern**: Academic environment usage patterns

### Processing Pipeline
```
Raw HTTP Logs → CLF Parsing → RPS Conversion → Time Series → GRU Training Data
```

## Implementation Phases

### Phase 1: Dataset Integration
- Download and process ClarkNet/Calgary traces
- Convert to RPS (Requests Per Second) time series
- Create training/validation/test splits
- Implement data preprocessing pipeline

### Phase 2: GRU Model Development  
- Design GRU architecture for 30-second prediction
- Implement training pipeline with PyTorch
- Evaluate model performance using RMSE
- Optimize hyperparameters for accuracy

### Phase 3: ElaX Algorithm Implementation
- Implement separated controller architecture
- Develop resource allocation model with OLS tuning
- Create online feedback correction system
- Integrate GRU predictions with routing decisions

### Phase 4: SLO Monitoring System
- Implement 99th percentile tail latency monitoring
- Develop 5-second SLO violation detection
- Create routing decision algorithm (Algorithm 1)
- Integrate cost tracking and analysis

### Phase 5: Formal Evaluation
- Execute comprehensive experiment scenarios
- Collect performance, resource, and cost metrics
- Perform comparative analysis with baselines
- Generate thesis-ready results and documentation

## Success Criteria

### Technical Metrics
- **RMSE**: <10% prediction accuracy for GRU model
- **Tail Latency**: <200ms p99 under normal load, <500ms during spikes
- **Cost Efficiency**: 60-80% reduction vs pure serverless
- **SLO Compliance**: >99.9% availability during load variations

### Research Contributions
- Novel GRU-based modification of ElaX algorithm
- Real-world dataset validation of hybrid approach
- Formal resource allocation model with online tuning
- Comprehensive evaluation framework for hybrid systems

## Getting Started

1. **Review [Experiment Plan](01-experiment-plan.md)** for complete system design
2. **Study [Methodology](02-methodology-implementation.md)** for technical details
3. **Follow [Experiment Guide](03-running-experiments.md)** for execution
4. **Use [Incremental Development](../incremental-development/)** for implementation

## For Development Teams

While this documentation focuses on formal thesis requirements, developers should start with the [incremental development approach](../incremental-development/) to build understanding progressively before implementing the complete thesis system.

## Academic References

- **ElaX Algorithm**: Yang et al. (2019) - Base algorithm for modification
- **GRU Efficiency**: Mondal et al. (2023) - Justification for GRU selection
- **Hybrid Strategies**: Senjab et al. (2023), Mampage et al. (2022) - Integration patterns
- **Dataset Sources**: ClarkNet and Calgary University HTTP trace repositories