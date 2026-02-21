# Chapter 1: Introduction (Pendahuluan)

## 1.1 Background (Latar Belakang)

The use of cloud computing services has experienced significant growth in recent years, driven by the need for scalability, cost efficiency, and flexibility in running applications. According to Flexera's 2023 report, 87% of enterprises have adopted a multi-cloud strategy, demonstrating the increasing reliance on cloud technology for business operations.

In the cloud computing ecosystem, **Kubernetes** has emerged as the de facto standard for container orchestration, enabling automated deployment, scaling, and management of containerized applications. Meanwhile, **serverless computing** offers a paradigm shift where developers can deploy functions without managing the underlying infrastructure, with the cloud provider handling all server management tasks.

### The Challenge of Dynamic Workloads

Both Kubernetes and serverless architectures face challenges when dealing with dynamic workloads:

**Kubernetes Challenges:**
- Requires careful resource provisioning to avoid over-provisioning (cost waste) or under-provisioning (performance degradation)
- Horizontal Pod Autoscaler (HPA) reacts to metrics but doesn't predict future demand
- Cold start for scaling can cause latency spikes during traffic bursts

**Serverless Challenges:**
- Cold start latency when functions are not warm
- Cost increases linearly with invocations (expensive at high volumes)
- Limited execution duration and resource constraints

### The Hybrid Approach

A hybrid approach that combines Kubernetes and serverless can leverage the strengths of both:

| Aspect | Kubernetes | Serverless | Hybrid |
|--------|------------|------------|--------|
| **Baseline Load** | ✅ Predictable warm capacity | ⚠️ Invocation-based cost | ✅ Route by workload state |
| **Traffic Spikes** | ❌ Scaling delay | ✅ Instant scale | ✅ Use Serverless |
| **Resource Efficiency** | ⚠️ Manual tuning | ✅ Automatic | ⚠️ Workload- and policy-dependent |
| **Cold Start** | ✅ Always warm | ❌ Cold start | ✅ Warm baseline |

### Workload Prediction

To implement an effective hybrid system, workload prediction is essential. By predicting future traffic patterns, the system can:
1. **Proactively allocate resources** before demand increases
2. **Route traffic intelligently** between K8s and serverless
3. **Minimize SLA violations** through anticipatory scaling

Research has shown that Gated Recurrent Unit (GRU) neural networks are effective for time-series prediction with lower computational cost than LSTM (Mondal et al., 2023).

### ElaX Algorithm Foundation

The ElaX algorithm (Yang et al., 2019) provides a foundation for elastic resource provisioning in containerized environments. This research proposes modifying ElaX to:
1. Incorporate GRU-based workload prediction
2. Add routing decisions between K8s and serverless
3. Implement SLO-aware decision making with tail latency monitoring

---

## 1.2 Problem Formulation (Rumusan Masalah)

Based on the background analysis, this research addresses the following problems:

1. **How to design workload traffic prediction for an application using GRU?**
   - Time-series modeling of HTTP request patterns
   - Multi-point prediction (30 seconds ahead)
   - Training with real HTTP trace datasets

2. **How to design and perform decision making by modifying ElaX for scaling on a server cluster and distributing traffic to different cluster types?**
   - Integration of prediction with routing decisions
   - SLO-aware routing controller implementation
   - Resource allocation model optimization

3. **How to evaluate the modified ElaX mechanism for automatic scaling and load distribution in Kubernetes and serverless integration?**
   - RMSE accuracy for prediction model
   - Latency and throughput metrics
   - Cost analysis and comparison

---

## 1.3 Research Objectives (Tujuan Penelitian)

The objectives of this research are:

1. **Design and implement** a GRU-based workload prediction model capable of forecasting traffic patterns with high accuracy (RMSE < 10%)

2. **Develop a modified ElaX algorithm** that integrates:
   - Workload prediction for proactive resource allocation
   - Intelligent routing between Kubernetes and serverless
   - SLO monitoring with 99th percentile tail latency tracking

3. **Evaluate the hybrid system** using:
   - Synthetic workload patterns (trained model)
   - Real HTTP trace datasets for validation (ClarkNet, Calgary)
   - Performance metrics (latency, throughput, error rate)
   - Cost efficiency analysis

---

## 1.4 Research Benefits (Manfaat Penelitian)

### Academic Benefits
- Contribution to cloud computing research on hybrid architectures
- Novel approach combining GRU prediction with ElaX modification
- Validated methodology using real-world datasets

### Practical Benefits
- Improved cost control through workload-aware resource allocation (not a fixed savings guarantee)
- Improved application performance with proactive scaling
- Minimized SLA violations through predictive decision making

---

## 1.5 Research Contribution (Kontribusi Penelitian)

This research makes the following contributions:

1. **GRU-based Workload Predictor**
   - Multi-point prediction model for HTTP traffic
   - Trained on synthetic workload patterns
   - Validated against real HTTP trace logs
   - Accuracy evaluated using RMSE, MAE, and MAPE metrics

2. **Modified ElaX Algorithm (Routing Controller)**
   - Integration with GRU prediction output (Algorithm 1)
   - Hybrid routing decision logic between K8s and serverless
   - SLO-aware traffic routing with predictive pre-warming
   - Note: Cluster resource scaling (Algorithm 2) proposed for future work

3. **Comprehensive Evaluation Framework**
   - Prediction accuracy assessment
   - System performance benchmarking
   - Cost-benefit analysis methodology

---

## 1.6 Problem Constraints (Batasan Masalah)

To focus the research scope, the following constraints are applied:

1. **Platform**: Kubernetes (K3s for resource efficiency) and Knative for serverless
2. **Prediction Model**: GRU neural network (not LSTM or Transformer)
3. **Training Data**: Synthetic workload patterns (ClarkNet/Calgary for validation)
4. **Metrics Focus**: Tail latency (p99), throughput, and cost
5. **SLO Target**: 200ms p99 latency threshold
6. **Environment**: Single-region deployment (no geo-distribution)
7. **Traffic Pattern**: HTTP request workloads (not streaming or batch)
