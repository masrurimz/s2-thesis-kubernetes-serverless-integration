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
