## 4.4 Cost Analysis

Cost analysis maps the experiment's local k3s architecture to equivalent AWS services, producing a unified cost projection from measured resource consumption. The mapping is: K8s HPA pods → EKS control plane + EC2 nodes, Knative KPA pods → AWS Lambda Provisioned Concurrency.

### 4.4.1 Architecture-to-AWS Mapping

Each scenario uses a different subset of AWS services based on its traffic routing:

- **S1 (K8s-only):** EKS control plane ($0.10/hr) + EC2 nodes (t3.medium, $0.0416/hr). No Lambda.
- **S2 (Serverless-only):** Lambda Provisioned Concurrency only. No EKS or EC2.
- **S3/S4 (Hybrid):** EKS + EC2 for the K8s share + Lambda for the serverless share.

EC2 nodes are sized from K8s CPU demand only: `nodes = max(ceil(avg_k8s_cpu / 1.08), ceil(avg_k8s_mem / 2.45)) + 1 HA`, where 1.08 = 1.8 vCPU × 0.60 target utilization and 2.45 = 3.5 GiB × 0.70 target utilization. Lambda execution time uses a signal hierarchy: serverless-specific app duration first, S2 scenario app duration second, and CPU-derived fallback (`cpu_per_request_ms / 0.2 + 10ms`) only when app-duration signals are unavailable.

### 4.4.2 Unified AWS Cost Comparison (All-Scenarios Rerun v2, n=1)

**Table 4.21: AWS Cost per 1200s Experiment Run**

| Component | S1 (K8s-only) | S2 (Knative-only) | S3 (Hybrid Reactive) | S4 (Hybrid Predictive) |
|-----------|---:|---:|---:|---:|
| EKS control plane | $0.033 | — | $0.033 | $0.033 |
| EC2 compute | $0.028 | — | $0.028 | $0.028 |
| Lambda capacity | — | $0.047 | $0.124 | $0.109 |
| Lambda execution | — | $0.106 | $0.290 | $0.252 |
| Lambda requests | — | $0.016 | $0.010 | $0.010 |
| **Total** | **$0.061** | **$0.169** | **$0.486** | **$0.432** |

**Table 4.22: Monthly Projection (30 Days Continuous at Experiment Load)**

| Scenario | AWS Total |
|----------|----------:|
| S1 (K8s-only) | $132 |
| S2 (Knative-only) | $364 |
| S3 (Hybrid Reactive) | $1,049 |
| S4 (Hybrid Predictive) | $934 |

**Table 4.23: Cost per 1M Successful Requests**

| Scenario | $/1M Successful |
|----------|----------------:|
| S1 (K8s-only, 100% success) | $0.70 |
| S2 (Knative-only, 47.1% success) | $4.46 |
| S3 (Hybrid Reactive, 51.5% success) | $15.70 |
| S4 (Hybrid Predictive, 52.1% success) | $13.28 |

### 4.4.3 Key Findings

**S1 is cheapest in this rerun-v2 sample.** In the 2026-02-21 all-scenarios rerun-v2 (`n=1` each), S1 has the lowest total cost ($0.061/run). Under app-duration-informed sizing, S2 rises to $0.169/run and hybrid scenarios are highest (S3 $0.486, S4 $0.432).

**Serverless-specific execution sizing materially changes hybrid estimates.** S3/S4 are no longer priced from blended or underreported execution duration. With serverless-specific duration signals, Lambda capacity and execution components dominate, and S4 is lower than S3 ($0.432 vs $0.486) in this run.

**Whole-run totals and fairness-normalized metrics must be interpreted together.** Raw totals capture infrastructure spend per run, while `$ / 1M successful` captures output efficiency under each scenario's success rate. In rerun-v2, both views are reported and used jointly for interpretation.

**Directionality only (not inferential ranking).** The rerun-v2 bundle is `n=1` per scenario and is intended for pipeline validation and directional interpretation. Final ranking claims require the planned replicated main study (n=10–15 per scenario).

### 4.4.4 Limitations

1. **Projected, not billed.** Costs are computed from 2025 list prices (us-east-1) applied to measured resource consumption. They do not reflect free tiers, reserved instances, savings plans, or volume discounts.

2. **Stress-harness success rates.** Success rates can vary materially across runs under the artificial node constraint (400m allocatable). Cost-per-successful-request figures should therefore be interpreted as run-dependent and not direct production performance.

3. **Linear monthly projection.** The 30-day projection assumes constant load at experiment intensity. Real workloads vary, making actual monthly costs lower.

4. **Single-run directionality.** The 2026-02-21 all-scenarios rerun-v2 includes one run per scenario. Its rankings and absolute totals are directional, not inferential final evidence.

5. **Single workload profile.** Results are specific to fib(34) with 200m CPU pods. Different CPU allocations or workload characteristics would change the cost ratios.

---

*Evidence: `results/cost/2026-02-21_all-scenarios-rerun-v2-unified-aws-cost/cost_results.json` and `results/cost/2026-02-21_all-scenarios-rerun-v2-unified-aws-cost/report.md`. Source experiment: `results/experiments/phase-b/2026-02-21_all-scenarios-rerun-v2/results_final.json`. Analyzer: `thesis/scripts/cost_analyzer.py` v5.*
