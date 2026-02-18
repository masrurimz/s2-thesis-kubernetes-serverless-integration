## 4.4 Cost Analysis

Cost analysis applies three cloud billing models to actual measured resource consumption from Phase B v4 experiments. Unlike the performance results (which use a stress-harness testbed), cost projections use production-grade node sizing to produce realistic estimates.

### 4.4.1 Evaluation Context: Stress Harness vs Production Projection

The Phase B experiments used `system-reserved=15600m` on k3d workload nodes, reducing allocatable CPU to ~400m per node (~2 pods at 200m request). This deliberately forces Cluster Autoscaler triggers within 20-minute runs — valid for mechanism validation but not representative of production node capacity.

For cost projection, clusters are sized using t3.medium instances (1.8 vCPU allocatable, ~9 pods/node at 200m request) with EKS control plane ($0.10/hr) and +1 node for HA headroom. At the tested load (~53–73 RPS), all desired replicas fit on 1–2 production nodes without triggering Cluster Autoscaler.

Resource consumption metrics (CPU-seconds, pod counts, service times) are taken directly from experiment measurements, as these reflect actual application behavior independent of node sizing.

### 4.4.2 Three-Model Cost Comparison

Three billing models capture different aspects of the K8s-vs-serverless cost trade-off:

- **Model 1 (Lambda Provisioned Concurrency):** Maps Knative's always-warm pods (`min-scale=1`) to Lambda PC instances. Each pod with `target-concurrency=10` maps to 10 Lambda instances. Execution billed at wall-clock service time derived from Little's Law.
- **Model 2 (Cloud Run Always-Allocated):** Bills actual CPU-seconds and GiB-seconds consumed, immune to the wall-clock inflation that affects Lambda billing.
- **Model 3b (EC2 Production):** Infrastructure-level cost using t3.medium nodes ($0.0416/hr) plus EKS control plane ($0.10/hr). Node count = ceil(total CPU requested / 1.8 vCPU) + 1 HA headroom.

**Table 4.21: Cost per 1200s Experiment Run**

| Scenario | Lambda PC | Cloud Run | EC2 Production |
|----------|----------:|----------:|---------------:|
| S1 (K8s-only) | $0.075 | $0.036 | $0.075 |
| S2 (Knative-only) | $1.077 | $0.056 | $0.089 |
| S3 (Hybrid Reactive) | $0.294 | $0.054 | $0.089 |
| S4 (Hybrid Predictive) | $0.415 | $0.053 | $0.103 |

**Table 4.22: Monthly Projection (30 Days Continuous at Experiment Load)**

| Scenario | Lambda PC | Cloud Run | EC2 Production |
|----------|----------:|----------:|---------------:|
| S1 (K8s-only) | $162 | $79 | $162 |
| S2 (Knative-only) | $2,326 | $121 | $192 |
| S3 (Hybrid Reactive) | $636 | $116 | $192 |
| S4 (Hybrid Predictive) | $897 | $115 | $222 |

**Table 4.23: Cost per 1M Successful Requests**

| Scenario | Lambda PC | Cloud Run | EC2 Production |
|----------|----------:|----------:|---------------:|
| S1 (K8s-only, 40.3% success) | $2.91 | $1.42 | $2.91 |
| S2 (Knative-only, 89.6% success) | $13.72 | $0.71 | $1.13 |
| S3 (Hybrid Reactive, 76.7% success) | $4.41 | $0.81 | $1.33 |
| S4 (Hybrid Predictive, 79.2% success) | $6.14 | $0.79 | $1.52 |

### 4.4.3 Key Findings

**The billing model determines the cost ranking, not the architecture.** Under Lambda Provisioned Concurrency, S1 is cheapest ($0.075/run) and S2 most expensive ($1.077/run). Under EC2 Production pricing, all scenarios are within 1.4× of each other ($0.075–$0.103/run). Under Cloud Run, all scenarios cost roughly the same ($0.036–$0.056/run).

**CPU throttling creates a hidden serverless cost multiplier.** Each Knative pod (200m CPU, target-concurrency=10) gives each concurrent request only 20m effective CPU. The fib(32) workload that completes in ~10ms on a full core takes 2.5–3.6s wall-clock under this throttling. Lambda bills wall-clock time, creating a ~364× cost inflation relative to CPU time. This is the dominant factor making S2 expensive under Lambda PC pricing.

**S4 does not save money compared to S3.** Under all three models, S4 costs more than S3 because GRU prediction routes more traffic to serverless (6.7 avg Knative pods vs 5.2), increasing the pod footprint. However, S4 achieves 2.5 percentage points better success rate (79.2% vs 76.7%), which may justify the premium in SLA-sensitive environments.

**S1 is cheapest but least reliable.** S1 costs the least per run ($0.075 under Lambda PC and EC2 Production) but delivers only 40.3% success rate under stress-harness conditions. Its cost-per-successful-request ($2.91/1M under EC2 Production) is the worst of all scenarios. The low success rate is an artifact of the stress-harness constraint (max 6 schedulable pods vs 9 desired); in production at this load, S1 would likely achieve >95% success.

### 4.4.4 Limitations

These cost estimates carry several limitations:

1. **Projected, not billed.** All costs are computed from published 2025 list prices (us-east-1) applied to measured resource consumption. They do not reflect free tiers, reserved instances, savings plans, or volume discounts.

2. **Stress-harness success rates.** The 40.3% S1 success rate reflects the artificial node constraint (400m allocatable), not production K8s performance. Cost-per-successful-request figures should be interpreted cautiously for S1.

3. **Linear monthly projection.** The 30-day projection assumes constant load at experiment intensity. Real workloads vary, making actual monthly costs lower.

4. **Knative exceeded configured max-scale.** S2 scaled to 26 pods despite a configured `max-scale=10`, likely due to KPA panic mode under sustained load. This inflates S2's resource consumption beyond what a production configuration with enforced limits would incur.

5. **Single workload profile.** Results are specific to fib(32) with 200m CPU pods. Different CPU allocations or workload characteristics would change the cost ratios significantly — particularly the throttling-driven wall-clock inflation that dominates Lambda PC costs.

---

*Evidence: `controller/results/cost_analysis/cost_analysis_20260217_144437.json`. Methodology: `results/cost/2026-02-17_three-model-cost-comparison/report.md`. Analyzer: `thesis/scripts/cost_analyzer.py`.*
