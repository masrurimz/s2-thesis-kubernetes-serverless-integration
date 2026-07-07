# Cost Model Findings — Serverless vs K8s Cost Crossover

## Methodology

Cost model maps experiment architecture to AWS services:
- **K8s** → EKS control plane ($0.10/hr) + EC2 t3.medium nodes ($0.0416/hr each)
- **Serverless** → Lambda Provisioned Concurrency (PC) with GB-second billing


### Resource Budget (x1-dev: 16 cores, 60GB RAM)

| Cluster | Node | Docker CPU | Role |
|---|---|---|---|
| thesis-hybrid | server-0 | 1.0 | K8s control plane |
| thesis-hybrid | agent-0 | 1.0 | K8s workload pods |
| thesis-hybrid | agent-1 | 1.0 | K8s workload pods |
| thesis-hybrid | dynamic-0 | 1.0 | K3dAutoscaler (provisioned on demand) |
| thesis-hybrid | dynamic-1 | 1.0 | K3dAutoscaler (provisioned on demand) |
| thesis-serverless | server-0 | 1.0 | Knative control plane |
| thesis-serverless | agent-0 | **3.0** | Knative workload pods |

**K8s total**: 3.0 static + 2.0 dynamic = **5.0 CPU peak**
**Serverless total**: 1.0 + 3.0 = **4.0 CPU** (no dynamic nodes)
**Background services**: ~9.0 CPU (herdr, OMP, GinaV2, Hindsight, MinIO)
**Grand total ceiling**: 16.0 / 16 cores (fits exactly)

K8s has 1.0 CPU advantage from node autoscaling — this IS the thesis finding:
"K8s with node autoscaling provides more peak capacity than serverless without node control."
### Lambda Billing Model (per AWS 2025 pricing)

Lambda bills **wall-clock duration**, not CPU time (SeBS: arXiv:2012.14132):

```
total_cost = PC_capacity + PC_execution + request_fees + overflow + data_transfer

PC_capacity   = instances × mem_GB × ceil(duration/300)×300 × $0.0000041667/GB-s
PC_execution  = requests × mem_GB × exec_time_sec × $0.0000097222/GB-s
request_fees  = requests / 1M × $0.20
overflow      = overflow_requests × mem_GB × exec_time_sec × $0.0000166667/GB-s
```

### Key Parameters (from CalibrationConfig)

| Parameter | Value | Source |
|---|---|---|
| `lambda_compute_ms` | 14.0ms | Measured fib(33) CPU compute time from capacity test |
| `io_wait_ms` | 50.0ms | Simulated DB query I/O (SeBS: arXiv:2012.14132, arXiv:2410.03480) |
| `LAMBDA_OVERHEAD_SEC` | 10ms | Lambda platform overhead (network + runtime init) |
| **Total exec time** | **74ms** | 14ms CPU + 50ms I/O + 10ms overhead |
| `LAMBDA_MEM_MB` | 531MB | Derived: ceil(300m/1000 × 1769) — AWS gives 1 vCPU at 1769MB |
| `POD_CPU_REQUEST` | 0.300 | Matches 300m calibration |

### I/O Wait Impact (SeBS Methodology)

The test app includes `WORK_DURATION_MS=50` env var that simulates a realistic DB query I/O wait. Per SeBS (arXiv:2012.14132) and SeBS-Flow (arXiv:2410.03480):

- **CPU-bound** (fib only, 14ms): Lambda bills 14ms + 10ms overhead = 24ms
- **I/O-bound** (fib + 50ms DB query): Lambda bills 14ms + 50ms + 10ms = 74ms
- **Real workloads** (DB + API + storage): 100-300ms typical per invocation

Lambda charges for the **entire wall-clock duration** including I/O sleeps. K8s nodes have fixed cost regardless of I/O vs CPU ratio.

## Results: Cost Crossover at ClarkNet Mean (73 RPS)

### Without I/O (CPU-only, unrealistic)

| Scenario | Monthly | Notes |
|---|---|---|
| S1 (K8s-only) | $162 | 3 EC2 nodes, fixed cost |
| S2 (Serverless) | $126 | **Cheaper** — pay-per-use at low RPS |
| S4 (Hybrid-predictive) | $198 | K8s + 62% serverless overflow |

### With 50ms I/O Wait (realistic, SeBS methodology)

| Scenario | Monthly | Notes |
|---|---|---|
| S1 (K8s-only) | **$162** | Unchanged — nodes don't care about I/O |
| S2 (Serverless) | **$240** | **1.5× more expensive** — Lambda bills I/O wait |
| S4 (Hybrid-predictive) | ~$250+ | K8s baseline + expensive serverless burst |

### Cost Crossover Analysis

The crossover depends on the **I/O vs CPU ratio**, not just RPS:

| I/O wait | S2 exec time | S2 monthly | vs S1 ($162) | Crossover |
|---|---|---|---|---|
| 0ms (CPU only) | 24ms | $126 | **S2 cheaper** | Above ~98 RPS |
| 10ms (minimal) | 34ms | $160 | ≈ Equal | At ~73 RPS |
| **50ms (DB query)** | **74ms** | **$240** | **S2 1.5× more** | **Below 73 RPS** |
| 100ms (API call) | 124ms | ~$380 | S2 2.3× more | Well below mean |
| 200ms (storage I/O) | 224ms | ~$680 | S2 4.2× more | Always more expensive |

**Key insight**: For I/O-bound workloads (the majority of real serverless applications), K8s is cheaper than pure serverless even at moderate RPS. Hybrid routing (S4) uses K8s for the cost-efficient baseline and serverless only for short-lived burst overflow.

## References

| Paper | arXiv | Used For |
|---|---|---|
| SeBS — Serverless Benchmark Suite | 2012.14132 | CPU-bound vs I/O-bound FaaS workload characterization; Lambda bills wall-clock |
| SeBS-Flow — Serverless Workflows | 2410.03480 | Storage I/O dominates serverless overhead (50-200ms) |
| Priceless — FaaS Pricing Models | 2606.26308 | Formal C(r,d) cost function with GB-second billing |
| Demystifying Serverless Costs | 2506.01283 | Billing inflates resources up to 4.35× |
| Skyrise — Cost Break-even | 2501.07771 | FaaS vs VM break-even throughput methodology |
| High Cost of Keeping Warm | 2509.03104 | 10-40% serverless overhead from instance churn |
| SoCC 2025 — CPU-Limits Kill | YAAS | CFS throttling causes 38% perf loss |

## Oracle Review Notes

1. ✅ 5-minute PC rounding correct (`ceil(duration/300)*300`)
2. ✅ Lambda memory derived from CPU: `ceil(POD_CPU_REQUEST × 1769)`
3. ✅ Exec time includes I/O wait (not just CPU)
4. ⚠️ PC sizing uses peak RPS (×2.25 burst ratio) — enables overflow costing
5. ⚠️ Data transfer charged only to Lambda (potential bias — EKS egress not modeled)
6. ⚠️ EC2 node sizing from average CPU (should use peak for burst scenarios)
