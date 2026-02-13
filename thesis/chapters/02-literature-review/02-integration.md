## 2.2 Integrasi Kubernetes dan Serverless (Kubernetes-Serverless Integration)

The complementary strengths and weaknesses of Kubernetes (consistent low latency, cost-efficient for sustained loads, requires capacity planning) and serverless (instant elasticity, zero idle cost, cold start penalty) motivate their integration into hybrid architectures [3], [7].

### Hybrid Architecture Benefits

Integrating Kubernetes and serverless provides four key advantages:

1. **Cost optimization**: Use Kubernetes for predictable baseline load (avoiding per-invocation serverless costs) and serverless for burst traffic (avoiding over-provisioning Kubernetes resources).
2. **Performance**: Warm Kubernetes pods avoid cold start latency for the majority of requests, while serverless handles overflow that would otherwise queue behind a saturated K8s backend.
3. **Flexibility**: Different workload components can be assigned to the most appropriate execution platform based on their characteristics.
4. **Reliability**: Cross-platform routing provides fallback capability if either backend experiences degradation.

### Integration Patterns

Two primary patterns have been identified in the literature for integrating container orchestration with serverless platforms:

**Pattern 1: Overflow Model**

In the overflow pattern, Kubernetes handles all traffic up to its provisioned capacity. When Kubernetes reaches saturation (as detected by CPU, memory, or latency metrics), excess traffic overflows to the serverless backend.

```
                 Normal Load           High Load
                     │                     │
                     ▼                     ▼
              ┌─────────────┐       ┌─────────────┐
              │ Kubernetes  │       │ Kubernetes  │
              │ (handles    │       │ (at max)    │───┐
              │  100%)      │       │             │   │ Overflow
              └─────────────┘       └─────────────┘   │
                                                      ▼
                                           ┌─────────────────┐
                                           │   Serverless    │
                                           │   (handles      │
                                           │    overflow)    │
                                           └─────────────────┘
```

**Figure 2-3: Overflow Integration Pattern**

This pattern is reactive—it responds to saturation after it occurs. The latency between detecting saturation and serverless capacity becoming available (including potential cold starts) creates a window during which SLO violations may occur.

**Pattern 2: Predictive Routing**

The predictive routing pattern uses a forecasting model to anticipate traffic changes and proactively adjust the traffic distribution between backends before capacity limits are reached:

```
     Traffic ──► Predictor ──► Router ──┬──► Kubernetes
                                        │
                                        └──► Serverless
```

**Figure 2-4: Predictive Routing Pattern**

This pattern is the basis for the architecture proposed in this research. By forecasting workload 30 seconds ahead using a GRU neural network and combining the prediction with real-time SLO monitoring, the system can pre-warm serverless capacity and shift traffic proactively. The ElaX algorithm [7] provides the algorithmic framework for implementing this pattern, as detailed in Section 2.5.2.
