# Reference Papers — Thesis Controller Redesign

All papers downloaded as PDF for offline access. Located in `docs/references/`.

## Controller Algorithm Papers

| Paper | File | arxiv/DOI | Key Insight |
|-------|------|-----------|-------------|
| **AAPA** — Archetype-Aware Predictive Autoscaler | `aapa-archetype-aware-predictive-autoscaler-2025.pdf` | arxiv:2507.05653 | Classifies workloads (SPIKE/PERIODIC/RAMP/STATIONARY), confidence-weighted scaling, 50% SLO reduction |
| **ADAPT** — Self-Calibrating Proactive Autoscaler | `adapt-self-calibrating-proactive-autoscaler-2026.pdf` | arxiv:2605.15788 | Online EWMA cold-start estimation, dynamic MPC horizon, <5% SLA violation |
| **STaleX** — Spatiotemporal Adaptive Autoscaling | `stalex-spatriotemporal-autoscaling-2025.pdf` | arxiv:2501.18734 | Per-service weighted PID with spatiotemporal features, 26.9% resource reduction vs HPA |
| **PulseNet** — Serverless Control Plane | `pulsenet-serverless-control-plane-2025.pdf` | arxiv:2505.24551 | Dual-track: expedited (burst→serverless) + sustainable (baseline→VMs), 65-70% cost reduction |
| **LA-IMR** — Latency-Aware Routing | `laimr-latency-aware-routing-2026.pdf` | arxiv:2505.07417 | Closed-form latency model, capacity-driven routing, proactive K8s scaling, 20.7% P99 reduction |
| **BACC** — Budget-Aware Calibration and Control | `bacc-budget-aware-autoscaling-2026.pdf` | arxiv:2606.20575 | PI controller on burn-rate, ACI uncertainty calibration, budget-paced provisioning |
| **ARIMA-PID** — Container Autoscaling | `arima-pid-container-autoscaling-2023.pdf` | doi:10.1007/s11042-023-16587-0 | ARIMA prediction + PID control for container autoscaling |
| **ElaX** — Elastic Provisioning | `elax-elastic-provisioning-containerized-2019.pdf` | doi:10.1109/HPCC/SmartCity/DSS.2019.00274 | LSTM predictor + resource reservation + online feedback controller (thesis base algorithm) |
| **HyMetricScaler** — Hybrid Autoscaling | `hymetricscaler-hybrid-autoscaling-2025.pdf` | doi:10.1109/HPCC67675.2025.00038 | Multi-metric hybrid (horizontal + vertical), PID for vertical, EMA for horizontal |
| **Dehigama et al.** — Hybrid VM+Serverless Cost | `dehigama-hybrid-vm-serverless-cost-2024.pdf` | HotInfra 2024 | VMs for baseline, serverless for burst, 7.5-28.5% cost savings |

## How Papers Map to Controller Versions

| Paper | V1 | V2 (PID+FF) | V3 (Capacity-Driven) |
|-------|-----|-------------|---------------------|
| ElaX | ✅ Base algorithm | ✅ | ✅ |
| AAPA | — | ✅ Confidence weighting | ✅ |
| ADAPT | — | ✅ Cold-start EWMA | ✅ |
| STaleX | — | ✅ PID + hysteresis | — |
| PulseNet | — | — | ✅ Dual-track routing |
| LA-IMR | — | — | ✅ Capacity-driven scaling |
| BACC | — | — | ✅ Burn-rate PI pacing |
| ARIMA-PID | — | ✅ PID gains | — |
| HyMetricScaler | — | — | — |
| Dehigama | — | — | ✅ Baseline+burst architecture |

## Methodology & Cost Model References

| Paper / Source | arxiv/DOI | Used For |
|----------------|-----------|----------|
| **Leopard** — Serverless Pay-For-Use | NSDI 2025 (usenix.org/system/files/nsdi25-cao.pdf) | SLIM billing model validation: Lambda mem ∝ CPU request (our 354MB = 200m/1000 × 1769MB) |
| **FaaSRail** — Representative Serverless Load | HPDC 2024 (zenodo.org/records/12735009) | Methodology for generating scaled-down FaaS workloads preserving statistical properties |
| **In-Vitro** — Serverless Trace Synthesis | SOSP 2023 (doi:10.1145/3605181.3626191) | Iterative trace sampling to synthesize representative workload summaries at multiple scales |
| **HAProxy WRR** — Weighted Round Robin | haproxy/src/lb_map.c + serverfault.com/q/909891 | Traffic distribution ∝ weights; validates weight-time product as traffic split metric |
| **DREEM** — Predictive Node Autoscaling | PoliTo 2024 (webthesis.biblio.polito.it/37712) | Node-level utilization via kubectl top nodes; cluster CPU/mem metrics methodology |
| **Naik** — K8s Adaptive Scheduling + Prediction | NCIRL 2024 (norma.ncirl.ie/9248/1/supriyasunilnaik.pdf) | Cluster utilization reporting: CPU 61% vs 42% baseline, Memory 65% vs 47% |
| **Multi-Cloud Container Orchestration** | 2025 (doi:10.62311/nesx/rphcrcscrcec2) | Reproducible multi-cloud K8s eval: Locust + Prometheus + Grafana, regression analysis |
| **QoS vs Auto-Scaling Policy** | MDPI Sensors 2024 (doi:10.3390/s24123774) | HPA vs KPA scaling-efficiency metric, latency percentile evaluation, 10-trial repeats |
| **DoE for Resource Sizing** | doi:10.3390/app151810098 | Response Surface Methodology finds optimal CPU/memory with minimal experiments; central composite design |
| **SATA** — SLO Threshold Adaptation | doi:10.3390/electronics13071242 | Static SLO thresholds need 35-47% margin; dynamic threshold adjustment achieves 98% SLA compliance |
| **CPU Throttling-Aware Autoscaling** | doi:10.1109/PIMRC59610.2024.10817283 | Per-pod capacity must be measured under actual CFS throttling, not assumed from CPU limits |
| **Demystifying Serverless Costs** | arXiv:2506.01283 | Billing inflates resources up to 4.35× beyond actual consumption; OS scheduling granularity impacts cost |
| **Skyrise** — Serverless vs VM Cost Break-even | arXiv:2501.07771 | Derives break-even throughput: FaaS cheaper below threshold, VMs cheaper above; Q6 break-even at 558 runs/hr, Q12 at 128 runs/hr |
| **High Cost of Keeping Warm** | arXiv:2509.03104 | Measures 10-40% serverless overhead from instance churn, 2-10× memory waste; hybrid real+simulation methodology |
| **BatchBench** — Autoscaling Benchmark | arXiv:2605.12272 | Five-axis evaluation: cost, SLA, responsiveness, thrash, interpretability; paired Wilcoxon + bootstrap CIs |
| **SeBS** — Serverless Benchmark Suite | arXiv:2012.14132 | Realistic FaaS workloads: CPU-bound (image processing) + I/O-bound (uploader, DB). I/O-bound shows wider latency distributions; Lambda bills wall-clock duration including I/O waits |
| **SeBS-Flow** — Serverless Workflow Benchmarks | arXiv:2410.03480 | Storage I/O dominates overhead in serverless workflows; NoSQL + object storage access patterns |
| **Let's Trace It** — Fine-Grained FaaS Benchmarking | arXiv:2205.07696 | Sync + async serverless patterns; I/O-bound workloads dominated by external services, not compute; orchestration overhead significant |

## Dataset References

| Dataset | Source | Size | Used For |
|---------|--------|------|----------|
| **ClarkNet-HTTP** | ita.ee.lbl.gov/html/contrib/ClarkNet-HTTP | 3.3M requests, 2 weeks (Aug 1995) | Primary trace-driven replay workload |
| **Calgary-HTTP** | ita.ee.lbl.gov/html/contrib/Calgary-HTTP | 700K requests (Oct 1994) | Secondary trace for baseline comparison |
| **KSWD** — Kubernetes Serverless Workload Dataset | github.com/GuilinDev/aapa-simulator/dataset | 10K+ traces, 14 days each, 144M+ points | Archetype-labeled (SPIKE/PERIODIC/RAMP/STATIONARY), ML-ready, MIT license |
| **Azure Functions** trace 2019 | github.com/Azure/AzurePublicDataset | ~185M invocations | Modern serverless workload patterns (basis for KSWD) |
| **IBM Cloud Code Engine** traces | github.com/ubc-cirrus-lab/ibm-cloud-code-engine-traces | ~52GB expanded | Real Knative/Kubernetes production data, per-request traces with pod mappings |
| **Huawei FaaS** trace | github.com/sir-lab/data-release | 85B requests, 31 days | Large-scale production serverless patterns, cold-start analysis |
| Synthetic archetypes (this thesis) | `data/trace-replay/synthetic_archetypes.py` | 4 × 40 stages | Controlled ablation: spike, periodic, ramp, stationary patterns |

## AWS Pricing References (us-east-1, 2026)

- EKS: $0.10/hr standard support
- EC2 t3.medium: $0.0416/hr on-demand (2 vCPU, 4 GiB)
- Lambda PC capacity: $0.0000041667/GB-s
- Lambda PC execution: $0.0000097222/GB-s
- Lambda on-demand: $0.0000166667/GB-s
- Lambda requests: $0.20/1M

## Thesis-Specific References

- ClarkNet HTTP trace (August 1995): Used for trace-driven replay
- Calgary HTTP trace (October 1994): Used for baseline comparison
- GRU model: Trained on synthetic patterns, validated on ClarkNet/Calgary
