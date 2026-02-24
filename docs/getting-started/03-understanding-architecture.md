# Understanding the Hybrid Architecture

## System Overview

This system implements a hybrid approach that intelligently routes traffic between Kubernetes baseline capacity and elastic serverless functions based on real-time performance metrics and machine learning predictions.

## Core Concept

### The Traditional Problem
- **Kubernetes**: Cost-effective but slow to scale, limited capacity
- **Serverless**: Instant scaling but expensive for sustained loads
- **Manual Management**: Human intervention required for traffic routing

### Our Hybrid Solution
```
Normal Traffic (100 RPS)    →  Kubernetes Cluster (low cost)
Traffic Spike (1000 RPS)    →  Serverless Functions (instant scale)
Sustained Load (800 RPS)    →  Return to Kubernetes (cost optimization)
```

## Architecture Evolution

Our implementation follows a 5-sprint evolution from simple to sophisticated:

### Sprint 1: Basic Foundation
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   k3s       │    │  HAProxy    │    │ Serverless  │
│ (nginx app) │◄──►│ (80/20)     │◄──►│ (Docker)    │
└─────────────┘    └─────────────┘    └─────────────┘
```
- **Manual routing** with fixed weights
- **Basic monitoring** with Prometheus
- **Proof of concept** validation

### Sprint 2: Simple Intelligence
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Historical  │    │ Linear Reg  │    │ Auto Router │
│ Data Store  │───►│ Predictor   │───►│ (Python)    │
└─────────────┘    └─────────────┘    └─────────────┘
```
- **Automated decisions** based on load prediction
- **Linear regression** for simple pattern recognition
- **Threshold-based routing** (RPS-focused)

### Sprint 3: SLO Awareness
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Tail Latency│    │ SLO Monitor │    │ Algorithm 1 │
│ Monitor     │───►│ (5s window) │───►│ Controller  │
└─────────────┘    └─────────────┘    └─────────────┘
```
- **99th percentile latency** monitoring
- **SLO violation detection** (200ms threshold)
- **Thesis Algorithm 1** implementation

### Sprint 4: ML Integration
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ ClarkNet/   │    │ GRU Model   │    │ 30-Second   │
│ Calgary Data│───►│ Training    │───►│ Predictions │
└─────────────┘    └─────────────┘    └─────────────┘
```
- **Real HTTP trace data** (4M+ requests)
- **GRU neural network** for advanced prediction
- **30-second horizon** matching thesis specification

### Sprint 5: Complete System
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ ElaX        │    │ Resource    │    │ Complete    │
│ Algorithm   │───►│ Allocator   │───►│ Evaluation  │
│ (R=α·x+β)   │    │ (OLS tuning)│    │ Framework   │
└─────────────┘    └─────────────┘    └─────────────┘
```
- **Full ElaX implementation** with formal resource allocation
- **OLS coefficient tuning** for optimal resource modeling
- **Comprehensive evaluation** with RMSE and cost analysis

## Key Components Deep Dive

### 1. Workload Predictor (Evolution)

**Sprint 2: Simple Linear Regression**
```python
def predict_load(historical_rps):
    # Linear regression on recent 60-minute trend
    # Predicts next 5 minutes
    return predicted_rps
```

**Sprint 4: GRU Neural Network** 
```python
class GRUPredictor:
    def predict_workload(self, sequence_60s):
        # GRU model trained on real HTTP traces
        # Predicts next 30 seconds
        return prediction_array_30s
```

### 2. Routing Controller (Evolution)

**Sprint 1: Manual Configuration**
```bash
# Manual HAProxy weight adjustment
echo "set weight servers/k3s 60" | socat - /var/run/haproxy.sock
```

**Sprint 3: Algorithm 1 (Thesis)**
```python
# Formal thesis algorithm implementation
if tail_latency > SLO and violation_timer >= 5:
    reroute_to_serverless()
elif tail_latency <= SLO and compliance_timer >= 5:
    reroute_to_kubernetes()
```

### 3. Resource Allocation (Evolution)

**Sprint 2: Simple Thresholds**
```python
if predicted_rps > k3s_capacity:
    increase_serverless_weight()
```

**Sprint 5: Formal Model (Thesis)**
```python
# R = α·x + β with OLS coefficient tuning
required_resources = alpha * predicted_load + beta
# Coefficients updated via online learning
```

## Performance Characteristics

### Latency Profile
```
Normal Load (100 RPS):     50ms p50, 100ms p99
Traffic Spike (1000 RPS):  80ms p50, 200ms p99 (with serverless)
Without Serverless:        200ms p50, 2000ms p99 (overwhelmed)
```

### Cost Profile (Illustrative, Workload-Dependent)
```
Cost ranking depends on execution-time signals and workload shape.
Latest rerun-v2 (1200s, n=1 each):
S1 K8s-only:        $0.061
S2 Serverless-only: $0.169
S3 Hybrid Reactive: $0.097
S4 Hybrid Predict.: $0.098
```

### Scaling Response
```
Kubernetes Autoscaler:  3-5 minutes to add capacity
Serverless Functions:   <30 seconds cold start
Hybrid Routing:         <5 seconds to detect and route
```

## Data Flow

### Normal Operation
1. **Monitor**: Prometheus collects metrics every 15 seconds
2. **Predict**: GRU model forecasts next 30 seconds of load
3. **Decide**: Compare prediction with current SLO compliance
4. **Route**: Adjust traffic weights based on optimal cost/performance
5. **Learn**: Update model coefficients based on actual performance

### Spike Handling
1. **Detect**: Tail latency exceeds 200ms for 5 seconds
2. **React**: Immediately route traffic to serverless (Algorithm 1)
3. **Monitor**: Track performance and cost during spike
4. **Optimize**: Return to Kubernetes when load stabilizes
5. **Adapt**: Update prediction model with spike patterns

## Integration Points

### Monitoring Stack
- **Prometheus**: Core metrics collection and querying
- **Grafana**: Visualization and dashboards
- **InfluxDB**: Time-series storage for ML training data
- **Custom Exporters**: Hybrid-specific metrics

### Machine Learning Pipeline
- **Data Processing**: ClarkNet/Calgary HTTP trace parsing
- **Model Training**: GRU training with PyTorch
- **Model Serving**: Real-time inference for predictions
- **Accuracy Tracking**: RMSE measurement and model retraining

### Infrastructure Integration
- **HAProxy**: Traffic routing and load balancing
- **K3s**: Kubernetes cluster management
- **Docker**: Serverless function simulation
- **Python Controllers**: Intelligent decision making

## Success Metrics

### Technical Performance
- **Prediction Accuracy**: RMSE <10% on real HTTP trace data
- **SLO Compliance**: >99% uptime with <200ms p99 latency
- **Scaling Speed**: <30 seconds response to traffic changes
- **System Stability**: No oscillation or hunting behavior

### Business Impact
- **Cost Optimization**: 60-80% cost reduction vs pure serverless
- **Performance Maintenance**: <10% latency increase during hybrid mode
- **Resource Efficiency**: >85% utilization in Kubernetes clusters
- **Availability**: 99.9% uptime during load variations

## Next Steps

### For Developers
1. **Start with [Sprint 1](../incremental-development/phase-1-basic-hybrid.md)** - Build basic foundation
2. **Follow incremental approach** - Complete each sprint before proceeding
3. **Validate at each step** - Ensure working system throughout

### For Researchers
1. **Review [Thesis Implementation](../thesis-implementation/)** - Formal research documentation
2. **Understand ElaX algorithm** - Base algorithm for modification
3. **Study evaluation methodology** - RMSE, SLO compliance, cost analysis

### For Production
1. **Validate on realistic workloads** - Use your actual traffic patterns
2. **Integrate with existing monitoring** - Adapt to your observability stack
3. **Customize for your constraints** - Adjust SLO thresholds and cost models

The hybrid architecture demonstrates that intelligent routing can combine Kubernetes baseline capacity with serverless elasticity. The cost outcome must be evaluated empirically for each workload and execution-time model.
