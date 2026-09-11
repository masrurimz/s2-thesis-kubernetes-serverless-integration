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
| **HyMetricScaler** — Hybrid Autoscaling | _no PDF (DOI-only)_ | doi:10.1109/HPCC67675.2025.00038 | Multi-metric hybrid (horizontal + vertical), PID for vertical, EMA for horizontal |
| **Dehigama et al.** — Hybrid VM+Serverless Cost | `dehigama-hybrid-vm-serverless-cost-2024.pdf` | HotInfra 2024 | VMs for baseline, serverless for burst, 7.5-28.5% cost savings |
| **Serracanta et al.** — HPA Stability Proof | `serracanta-hpa-stability-control-loop-2025.pdf` | doi:10.1109/ACCESS.2025.3526751 | Formal proof of HPA control-loop stability (global asymptotic, zero steady-state error) at any utilization target 30--80%. Justifies threshold tuning. |
| **HyPA** — Hybrid HPA with Model Updates | `hypa-hybrid-hpa-automated-model-updates-2023.pdf` | doi:10.1109/NFV-SDN59219.2023.10329742 | Blends proactive+reactive; auto-updates model on distributional shift; asymmetric scale-up/down recommended for dynamic workloads |
| **Tiny Autoscalers** — Lightweight Scaling | `tiny-autoscalers-2022.pdf` | arxiv:2203.00592 | Bottoming mechanism prevents rapid resource swings; small moving-average window for smoothing utilization |
| **OptScaler** — Collaborative Predictive Autoscaling | `optscaler-collaborative-predictive-autoscaling-2023.pdf` | arxiv:2311.12864 | MPC + chance constraints over proactive+reactive modules; Fourier+Flow-Attention forecaster; >36% SLO reduction; deployed at Alipay |
| **Meta-RL** — Predictive Meta Model-Based RL | `metarl-predictive-meta-autoscaling-2022.pdf` | arxiv:2205.15795 | DAPM periodic-attention forecaster + Attentive Neural Process in differentiable RL; deployed at Alipay |
| **Taming Cold Starts** — MPC Prewarming | `taming-cold-starts-mpc-prewarming-2025.pdf` | arxiv:2508.07640 | MPC scheduler jointly optimizes prewarming and dispatch on OpenWhisk; single platform, no cross-platform routing |
| **Attention-Double-LSTM** — K8s Autoscaling | `attention-double-lstm-k8s-autoscaling-2026.pdf` | arxiv:2603.28790 | Extends prior DRe-SCale PPO; baselines HPA, DDQN, single-LSTM ablation; OpenFaaS on MicroK8s, no cross-platform routing |
| **Jointλ** — Jointcloud FaaS Orchestration | `jointlambda-jointcloud-faas-orchestration-2025.pdf` | arxiv:2505.21899 | Multi-provider FaaS workflow orchestration; no prediction, no confidence gating |
| **ClusterLess** — Deadline-Aware Edge Orchestration | `clusterless-deadline-edge-orchestration-2026.pdf` | arxiv:2605.04310 | Deadline-aware serverless workflow placement on federated K8s edge clusters; measured state only, no predictive model |
| **CloudFormer** — Attention Performance Prediction | `cloudformer-attention-performance-prediction-2025.pdf` | arxiv:2509.03394 | Dual-branch transformer for VM performance degradation; baselines DT/RF/LR/GLR/LSTM (Seq2Seq excluded from benchmark) |
| **CNN-BiLSTM-ATT** — Traffic Flow Prediction | `cnn-bilstm-attention-traffic-flow-2023.pdf` | doi:10.32604/cmc.2023.039274 | Kalman + CNN-BiLSTM-attention; the architecture is the contribution; road traffic domain, not cloud autoscaling |
| **CBA-HDL** — Hybrid Cloud Workload Forecasting | _no PDF (DOI-only)_ | doi:10.1007/s10586-025-05646-w | Hybrid DL cloud workload forecaster; paywalled, claims not verified against primary text |

> **Note:** All controller PDFs in this directory are checked out as real PDFs (>50 KB, `%PDF` magic) except `arima-pid-container-autoscaling-2023.pdf`, which currently contains an HTML response and is listed as broken in the defense-alignment archive check (Springer paywall — DOI-only, no open PDF). `elax-elastic-provisioning-containerized-2019.pdf` was re-fetched from the author's page (ynyang1.github.io) and verified correct on 2026-08-07 (the previously archived object was an unrelated paper). `hymetricscaler-hybrid-autoscaling-2025.pdf` was removed on 2026-08-07 — the archived object was an unrelated paper and no open-access copy of the IEEE HPCC 2025 paper exists; it is now DOI-only like SATA (doi:10.3390/electronics13071242).

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
| **SATA** — SLO Threshold Adaptation | doi:10.3390/electronics13071242 (DOI-only, no PDF) | Static SLO thresholds need 35-47% margin; dynamic threshold adjustment achieves 98% SLA compliance |
| **CPU Throttling-Aware Autoscaling** | doi:10.1109/PIMRC59610.2024.10817283 | Per-pod capacity must be measured under actual CFS throttling, not assumed from CPU limits |
| **Demystifying Serverless Costs** | arXiv:2506.01283 · `demystifying-serverless-costs-2025.pdf` | Billing inflates resources up to 4.35× beyond actual consumption; OS scheduling granularity impacts cost |
| **Skyrise** — Serverless vs VM Cost Break-even | arXiv:2501.07771 · `skyrise-serverless-vm-breakeven-2025.pdf` | Derives break-even throughput: FaaS cheaper below threshold, VMs cheaper above; Q6 break-even at 558 runs/hr, Q12 at 128 runs/hr |
| **High Cost of Keeping Warm** | arXiv:2509.03104 · `high-cost-keeping-warm-2025.pdf` | Measures 10-40% serverless overhead from instance churn, 2-10× memory waste; hybrid real+simulation methodology |
| **BatchBench** — Autoscaling Benchmark | arXiv:2605.12272 · `batchbench-autoscaling-benchmark-2026.pdf` | Five-axis evaluation: cost, SLA, responsiveness, thrash, interpretability; paired Wilcoxon + bootstrap CIs |
| **SeBS** — Serverless Benchmark Suite | arXiv:2012.14132 · `sebs-serverless-benchmark-suite-2020.pdf` | Realistic FaaS workloads: CPU-bound (image processing) + I/O-bound (uploader, DB). I/O-bound shows wider latency distributions; Lambda bills wall-clock duration including I/O waits |
| **SeBS-Flow** — Serverless Workflow Benchmarks | arXiv:2410.03480 · `sebs-flow-serverless-workflows-2024.pdf` | Storage I/O dominates overhead in serverless workflows; NoSQL + object storage access patterns |
| **Let's Trace It** — Fine-Grained FaaS Benchmarking | arXiv:2205.07696 · `lets-trace-faas-benchmarking-2022.pdf` | Sync + async serverless patterns; I/O-bound workloads dominated by external services, not compute; orchestration overhead significant |

## Drift-Report Citation Archive

| Paper | File | arxiv/DOI | Key Insight |
|-------|------|-----------|-------------|
| **FaaSRail** — Representative Serverless Load | `faasrail-representative-serverless-load-2024.pdf` | zenodo.org/records/12735009 | Generates statistically representative scaled FaaS workloads |
| **In-Vitro** — Serverless Trace Synthesis | `invitro-serverless-trace-synthesis-2023.pdf` | doi:10.1145/3605181.3626191 | Synthesizes representative traces at configurable scales |
| **Mondal et al.** — GRU for Kubernetes Load Prediction | `mondal-gru-kubernetes-load-prediction-2023.pdf` | doi:10.3390/math11122675 | Uses GRU-based prediction for Kubernetes resource management. Trains LSTM, BiLSTM, and GRU under one protocol on real Google clusterdata-2011-2; GRU best on all three accuracy metrics (MSE 0.00194 vs 0.00195 both) with roughly half the training time (0.75 s vs 1.44 s, 2.41 s) |
| **Chung et al.** — GRU vs LSTM Empirical Evaluation | `chung-empirical-evaluation-gated-recurrent-2014.pdf` | arXiv:1412.3555 | Canonical head-to-head: GRU comparable to LSTM across sequence-modeling tasks, and on some datasets faster to converge in CPU time |
| **Cho et al.** — GRU Origin | `cho-learning-phrase-representations-rnn-2014.pdf` | arXiv:1406.1078 | Introduces the gated recurrent unit (reset and update gates, single hidden state) |
| **QoS vs Auto-Scaling Policy** | `qos-vs-autoscaling-policy-2024.pdf` | doi:10.3390/s24123774 | Repeats scaling-policy trials and compares latency percentiles |

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

## Forecasting Methodology References

| Paper | File | arxiv/DOI | Key Insight |
|-------|------|-----------|-------------|
| **Hewamalage et al.** — Recurrent Neural Networks for Time Series Forecasting: Current Status and Future Directions | `hewamalage-recurrent-networks-time-series-forecasting-2021.pdf` | arXiv:1909.00590 / DOI 10.1016/j.ijforecast.2020.06.008 | Survey of recurrent forecasters and the evaluation traps: compared against naive baselines the advantage is often small, hyperparameter search on the test set is the commonest way results inflate, and multiple rolling-origin folds are expected rather than a single split. |
| **Sculley et al.** — Hidden Technical Debt in Machine Learning Systems | `sculley-hidden-technical-debt-machine-learning-2015.pdf` | NeurIPS 2015, proceedings.neurips.cc/paper/2015/hash/86df7dcfd896fcaf2674f757a2463eba | Names training-serving skew as a first-class failure mode. The deployed model here predicts from a live signal whose level sits well below its training level, which is the mechanism behind the +30 rps bias the controller consumed. |
| **Makridakis et al.** — Statistical and Machine Learning forecasting methods: Concerns and ways forward | `makridakis-statistical-machine-learning-forecasting-concerns-2018.pdf` | DOI 10.1371/journal.pone.0194889 | Large-scale evidence that machine learning methods rarely beat well-specified statistical and naive baselines across many series, which is the expected frame for reporting that the GRU only matches a linear autoregression. |
| **Elsayed et al.** — Do We Really Need Deep Learning Models for Time Series Forecasting? | `elsayed-do-we-need-deep-learning-time-series-2021.pdf` | arXiv:2101.02118 | Gradient-boosted trees match or beat deep models on standard benchmarks under a controlled comparison, so architecture choice needs justification beyond fitting a single dataset. |
| **Hewamalage, Ackermann & Bergmeir** — Forecast Evaluation for Data Scientists: Common Pitfalls and Best Practices | `hewamalage-ackermann-bergmeir-forecast-evaluation-pitfalls-2023.pdf` | DOI 10.1007/s10618-022-00894-5 / arXiv:2203.10716 | The evaluation rubric this work is judged against: mandatory naive baselines, no tuning on test data, seed dispersion reported, and multiple evaluation origins. |
| **Rabanser et al.** — Failing Loudly: An Empirical Study of Methods for Detecting Dataset Shift | `rabanser-failing-loudly-detecting-dataset-shift-2019.pdf` | arXiv:1810.11953 | Deployed models fail silently under dataset shift; two-sample tests and domain classifiers detect it, and no single detector dominates. Grounds the missing input-distribution monitor. |
| **Zeng et al.** — Are Transformers Effective for Time Series Forecasting? | `zeng-transformers-effective-time-series-forecasting-2023.pdf` | DOI 10.1609/aaai.v37i9.26317 / arXiv:2205.13504 | Peer-reviewed evidence that a one-layer linear model matches or beats deep architectures on standard benchmarks, strengthening the case for parsimony when accuracy ties. |

Cited but not archived here, because every open mirror returned 403 or 404 at the time of writing:

| Paper | DOI or URL | Role in the argument |
|-------|-----------|----------------------|
| **Kim et al.** — Reversible Instance Normalization for Accurate Time-Series Forecasting against Distribution Shift (ICLR 2022) | openreview.net/forum?id=cGDAkQo1C0p | Recommended fix for the level shift: normalise each input window by its own statistics and restore them on the output, which cancels the frozen-scaler bias. |
| **Breck et al.** — The ML Test Score: A Rubric for ML Production Readiness and Technical Debt Reduction (IEEE Big Data 2017) | DOI 10.1109/BigData.2017.8258038 | Monitoring rubric that a deployed model should check its own input statistics. |
| **Dean & Barroso** — The Tail at Scale (CACM 2013) | DOI 10.1145/2408776.2408794 | Tail latency is governed by variance and queueing, not by the mean arrival rate a forecast of request rate can supply. |
| **Gandhi et al.** — AutoScale: Dynamic, Robust Capacity Management for Multi-Tier Data Centers (TOCS 2012) | DOI 10.1145/2382553.2382556 | Forecast-only capacity policies over-provision; a slightly under-forecasting hybrid with reactive correction wins. |
| **Tashman** — Out-of-sample tests of forecasting accuracy (IJF 2000) | DOI 10.1016/S0169-2070(00)00065-0 | Rolling-origin evaluation, the design the single split is measured against. |
| **Cerqueira, Torgo & Mozetič** — Evaluating time series forecasting models (Machine Learning 2020) | DOI 10.1007/s10994-020-05910-7 | Single holdout estimates are the least reliable; recommends rolling origin or repeated splits. |
| **Green & Armstrong** — Simple versus complex forecasting: The evidence (JBR 2015) | DOI 10.1016/j.jbusres.2015.03.026 | Across 32 comparisons complexity raised error by about 27 percent; parsimony when accuracy ties. |
| **Smyl** — A hybrid method of exponential smoothing and recurrent neural networks (IJF 2020) | DOI 10.1016/j.ijforecast.2019.03.017 | The M4-winning recurrent model was a global hybrid, the regime in which deep forecasters do win. |
| **Salinas et al.** — DeepAR (IJF 2020) | DOI 10.1016/j.ijforecast.2019.07.001 | Deep forecasting gains come from cross-series training and covariates, absent in a single-series pipeline. |

## Thesis-Specific References

- ClarkNet HTTP trace (August 1995): Used for trace-driven replay
- Calgary HTTP trace (October 1994): Used for baseline comparison
- GRU model: Trained on synthetic patterns, validated on ClarkNet/Calgary
