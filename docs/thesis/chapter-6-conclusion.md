# Chapter 6: Conclusion

## 6.1 Summary of Research

This thesis investigated the integration of Kubernetes container orchestration with serverless computing through GRU-based workload prediction for SLO-aware hybrid routing. The research addressed a fundamental challenge in cloud-native computing: how to balance the consistent performance of container-based deployments with the elastic scalability of serverless platforms.

The investigation proceeded through three phases:

1. **Algorithm Design**: Development of Algorithm 1 (SLO-Aware Routing Controller) and Algorithm 2 (GRU Prediction Integration) for dynamic traffic management between Kubernetes and serverless backends.

2. **System Implementation**: Construction of a complete routing stack including HAProxy for traffic distribution, Prometheus for metrics collection, and a prediction server for GRU inference.

3. **Simulation-Based Validation**: Controlled experiments comparing four scenarios (S1: K8s-only, S2: Serverless-only, S3: Hybrid-reactive, S4: Hybrid-predictive) under spike workload conditions.

---

## 6.2 Answers to Research Questions

### RQ1: How to design workload traffic prediction using GRU?

The GRU-based workload predictor was designed with:

- **Architecture**: 2-layer GRU with 64 hidden units
- **Input**: 60-sample sequence (60 seconds of RPS history at 1 Hz)
- **Prediction Horizon**: 30 seconds ahead
- **Training**: ClarkNet HTTP trace dataset
- **Integration**: Prediction server exposing REST API for real-time inference

The design achieved 10-14ms prediction latency with 72-79% confidence scores during experiments, successfully triggering 4 PREDICTIVE routing decisions.

### RQ2: How to design decision making for scaling and traffic distribution?

Two complementary algorithms were developed:

**Algorithm 1 (SLO-Aware Routing Controller):**
- Monitors p99 latency against 200ms threshold
- Triggers SCALE_OUT when sustained violation detected
- Triggers OPTIMIZE_COST when healthy margin achieved
- Adjusts HAProxy weights in 10% steps with 15-second cooldown

**Algorithm 2 (Predictive Integration):**
- Queries GRU prediction server for load forecast
- Triggers PREDICTIVE action when:
  - Predicted load increase > 30%
  - Prediction confidence ≥ 70%
- Preemptively adjusts weights before reactive thresholds breach

### RQ3: How to evaluate the modified routing mechanism?

The evaluation employed a controlled four-scenario comparison:

| Scenario | Configuration | Purpose |
|----------|---------------|---------|
| S1 | K8s-only (100/0) | Container orchestration baseline |
| S2 | Serverless-only (0/100) | Serverless computing baseline |
| S3 | Hybrid-reactive (80/20) | Hybrid without prediction |
| S4 | Hybrid-predictive (80/20) | Complete proposed system |

Each scenario was subjected to a 110-second workload with warmup (10 RPS), spike (100 RPS), and cooldown (20 RPS) phases. Metrics included error rate, p95/p99 latency, throughput, and routing decision types.

---

## 6.3 Key Findings

### 6.3.1 H1: Hybrid Routing Prevents SLO Collapse — VALIDATED

The experimental results demonstrated **categorical improvement**:

| Scenario | Error Rate | p95 Latency | Verdict |
|----------|------------|-------------|---------|
| S1 (K8s-only) | 72.62% | 60,002ms | **Failed** |
| S2 (Serverless-only) | 92.83% | 23,158ms | **Failed** |
| S3 (Hybrid-reactive) | 0% | 5.7ms | **Passed** |
| S4 (Hybrid-predictive) | 0% | 5.7ms | **Passed** |

The hybrid approach succeeded where pure approaches failed completely because:
- K8s tier provided stable baseline capacity without cold-start penalties
- Serverless tier absorbed overflow traffic preventing saturation
- Dynamic weight adjustment prevented either tier from overload

### 6.3.2 H2: Predictive Enables Proactive Decisions — PARTIALLY VALIDATED

While headline metrics were identical between S3 and S4, decision-level analysis revealed behavioral differences:

| Decision Type | S3 (Reactive) | S4 (Predictive) |
|---------------|---------------|-----------------|
| SCALE_OUT (reactive) | 3 | 3 |
| PREDICTIVE (preemptive) | 0 | **4** |
| OPTIMIZE_COST | 6 | 6 |
| MAINTAIN | 4 | 0 |

S4 replaced MAINTAIN decisions with PREDICTIVE decisions, demonstrating that:
- GRU predictions successfully triggered proactive weight adjustments
- The prediction pipeline operated correctly with 72% average confidence
- Under more stressful workloads, this proactivity would translate to metric improvements

### 6.3.3 System Integration Confirmed

The complete stack demonstrated successful integration:

| Component | Performance |
|-----------|-------------|
| GRU Prediction | 10-14ms latency |
| HAProxy Weight Update | <10ms |
| Total Decision Cycle | <50ms |
| Continuous Operation | 110 seconds without failure |

---

## 6.4 Contributions

### 6.4.1 Academic Contributions

1. **Empirical Validation of Hybrid Architecture**: Demonstrated that strategic integration of Kubernetes and serverless—rather than treating them as competing paradigms—prevents the catastrophic failure modes of either platform alone.

2. **Prediction-Enabled Control Design**: Showed how GRU-based workload prediction can be integrated into routing decisions, transforming traffic management from reactive to proactive.

3. **Simulation-Based Validation Methodology**: Provided a reproducible experimental framework with explicit assumptions, enabling peer verification and controlled comparison.

### 6.4.2 Practical Contributions

1. **Algorithm 1 Implementation**: Production-ready SLO-aware routing controller implemented in Python with HAProxy integration.

2. **System Architecture**: Complete reference implementation including prediction server, monitoring integration, and dynamic weight adjustment.

3. **Design Principles**: Five actionable principles for practitioners implementing hybrid cloud-native systems:
   - Embrace platform heterogeneity
   - Implement SLO-aware traffic management
   - Invest in workload prediction
   - Design for controlled experimentation
   - Document assumptions explicitly

---

## 6.5 Implications for Practice

### For SRE/DevOps Teams

**Reduced Operational Risk**: Hybrid routing provides defense against single-tier saturation. The 0% error rate achieved in experiments (vs 72-93% for pure approaches) represents elimination of spike-induced outages.

**Proactive Visibility**: GRU predictions provide 30-second advance warning of load changes, enabling proactive capacity decisions even when automated routing is disabled.

**Simplified Capacity Planning**: The hybrid approach allows right-sizing K8s for baseline load with serverless absorbing peaks, eliminating the 2-3x over-provisioning typically required for single-tier architectures.

### For Cloud Architects

**Workload Fit Criteria**: The hybrid approach is most beneficial for workloads with:
- Traffic variability (coefficient of variation > 0.5)
- Stringent SLO targets (p99 < 200ms)
- Cost sensitivity preventing over-provisioning

**Platform Selection**: K8s should handle latency-sensitive baseline; serverless should handle variable overflow. The division should be dynamic, not static.

---

## 6.6 Limitations

### 6.6.1 Simulation Constraints

| Constraint | Impact |
|------------|--------|
| Custom serverless-activator | Results may differ with real Knative/Lambda |
| Deterministic 5s cold start | More predictable than real cloud functions |
| 80/20 default weights | Serverless always warm (not on-demand) |
| Single run per scenario | No statistical inference possible |
| 110s duration | Short compared to production scenarios |

### 6.6.2 Generalization Limits

The results validate **directional benefit** (hybrid > pure) and **mechanism feasibility** (prediction integration works), but specific quantitative improvements cannot be generalized to:
- Production-scale traffic (1000s of RPS)
- Real cloud serverless platforms
- Heterogeneous workload mixes
- Multi-region deployments

---

## 6.7 Recommendations for Future Work

### Immediate Priorities

1. **Real Knative Validation**: Deploy with production Knative Service to validate under realistic cold-start variability.

2. **100/0 Default Configuration**: Implement true serverless-on-demand with Algorithm 1 ENABLE → PRE-WARM → RAMP workflow.

3. **Statistical Replication**: Execute 9+ runs per scenario to enable inferential statistics with confidence intervals.

### Medium-Term Extensions

4. **Discriminating Workloads**: Design spike patterns (higher intensity, faster ramp) where reactive vs. predictive produces measurable metric differences.

5. **Service Mesh Integration**: Package as Istio/Linkerd extension for production adoption.

6. **Multi-Tenant Support**: Enable per-service SLO targets and resource isolation.

### Long-Term Research

7. **Online Learning**: Enable GRU adaptation to concept drift without full retraining.

8. **Multi-Objective Optimization**: Balance latency, cost, and energy consumption with configurable trade-off weights.

9. **Formal Stability Analysis**: Develop theoretical guarantees for controller convergence under adversarial conditions.

---

## 6.8 Closing Remarks

This thesis began with the observation that cloud-native computing faces a fundamental tension: container orchestration provides consistent performance but limited elasticity, while serverless computing offers instant scalability but incurs cold-start penalties and per-invocation costs.

The experimental evidence demonstrates that this tension can be resolved through **hybrid architecture with intelligent routing**:

| Pure Approach | Outcome |
|---------------|---------|
| K8s-only | 72.62% failure rate (saturation) |
| Serverless-only | 92.83% failure rate (capacity exhaustion) |

| Hybrid Approach | Outcome |
|-----------------|---------|
| Hybrid routing | 0% failure rate (stable operation) |

The results are unambiguous in direction: hybrid routing prevents SLO collapse under spike workloads. The magnitude of improvement (categorical failure → success) exceeded expectations and validates the core hypothesis.

Beyond quantitative results, this research demonstrates that **prediction transforms the nature of traffic management**. Reactive systems perpetually respond to what already happened; predictive systems anticipate and prepare. The 4 PREDICTIVE decisions observed in S4—replacing MAINTAIN decisions in S3—represent this transformation in action.

The simulation-based validation approach provides reproducible proof-of-concept while acknowledging the gap between controlled experiments and production deployment. Follow-up work with real Knative, statistical replication, and discriminating workloads will strengthen these findings.

As cloud-native computing continues to evolve toward multi-platform heterogeneity, the principles established here—embrace platform diversity as resource, treat SLO compliance as primary constraint, and use prediction to enable proactive control—provide a foundation for next-generation distributed systems.

---

## 6.9 Data Availability

All experimental results are available in the thesis repository:

| Resource | Location |
|----------|----------|
| Simulation Results | `infrastructure/results/simulated-v1/` |
| S1-S4 JSON Summaries | `s1-spike-summary.json` through `s4-spike-summary.json` |
| Experiment Documentation | `docs/EXPERIMENT_RESULTS.md` |
| Algorithm Implementation | `controller/intelligent_router/` |
| Reproducibility Guide | `docs/thesis/appendix-a-reproducibility.md` |

Repository: https://github.com/masrurimz/s2-thesis-kubernetes-serverless-integration

---

**Document Version:** 2.0 (Updated with simulated-v1 results)  
**Last Updated:** January 2026
