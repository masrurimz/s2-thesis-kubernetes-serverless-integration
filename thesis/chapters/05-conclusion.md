# BAB 5: KESIMPULAN DAN SARAN

## 5.1 Kesimpulan (Conclusion)

This research designed, implemented, and evaluated a hybrid Kubernetes-serverless architecture with GRU-based workload prediction for intelligent traffic routing. The system addresses elastic scalability management in heterogeneous cloud environments through SLO-aware decision making. Three research questions were posed; each is answered below with direct reference to experimental evidence.

### RQ1: How to design workload traffic prediction for an application using GRU?

A GRU (Gated Recurrent Unit) neural network was designed with two recurrent layers (64 and 32 units) and dropout regularization (0.2) to predict short-term HTTP workload trends. The model takes a sliding window of recent request-per-second (RPS) observations and outputs a predicted RPS value along with a confidence score.

The GRU predictor meets all predefined accuracy targets on synthetic workload patterns:

- **RMSE**: 6.01% (target <10%) ✅
- **MAE**: 4.91% (target <5%) ✅
- **Inference latency**: ~40ms (target <50ms) ✅
- **Confidence scores**: 0.72–0.88 during live predictions ✅

The model was trained on synthetic workload patterns incorporating periodic, bursty, and ramp characteristics. Validation against ClarkNet and Calgary HTTP trace baselines confirmed that the GRU architecture captures temporal patterns effectively, though real-trace accuracy (RMSE 17.78%) does not meet the original thresholds due to non-stationarity and irregular burst patterns absent in synthetic training data. This gap between synthetic and real-trace performance is a known limitation documented for future work.

*(Evidence: `results/models/gru/2026-02-10_training-synthetic/`, `results/models/gru/2026-02-13_training-clarknet-calgary/`)*

### RQ2: How to design decision making by modifying ElaX for scaling and traffic distribution?

Two algorithms were designed by extending the ElaX framework for heterogeneous cloud environments:

**Algorithm 1 — Routing Controller** (fully implemented): An SLO-aware routing controller that monitors tail latency (p99) against configurable thresholds and makes four types of decisions in priority order:

1. **SCALE_OUT** (priority 1): Triggered when p99 exceeds the SLO threshold (200ms), immediately shifting traffic toward serverless backends.
2. **SCALE_IN** (priority 2): Triggered when sustained low latency indicates over-provisioning, consolidating traffic back to Kubernetes.
3. **PREDICTIVE** (priority 3): Triggered when the system is healthy but GRU predicts a workload surge above the confidence threshold, pre-warming serverless capacity before violations occur.
4. **OPTIMIZE_COST** (priority 4): Triggered during stable periods to minimize serverless usage when not needed.

Traffic distribution is implemented through weight-based routing via HAProxy, dynamically adjusting the Kubernetes-to-serverless split from 100/0 (all K8s) through intermediate states to 50/50 (maximum serverless engagement). The predictive pre-warming mechanism was validated in Phase A1, where PREDICTIVE triggered at p99=146ms (healthy state) upon detecting a predicted 47% workload surge with 72% confidence, successfully pre-positioning serverless capacity before SLO violation.

**Algorithm 2 — Cluster Controller** (integrated into routing daemon): A horizontal scaling formula R = αx + β is integrated into the routing daemon for real-time Kubernetes replica scaling, operating in reactive mode (S3, using observed load) or predictive mode (S4, using GRU forecast).

*(Evidence: `results/experiments/phase-a1/2026-02-12_predictive-trigger/`)*

### RQ3: How to evaluate the modified ElaX mechanism?

A comprehensive evaluation framework was designed spanning three experimental phases across four scenarios (S1: K8s-only, S2: Knative-Only (KPA), S3: Hybrid Reactive, S4: Hybrid Predictive):

- **Phase A1** (mechanism validation): Confirmed that weight shifting, serverless engagement, SLO monitoring, and predictive pre-warming all function correctly under controlled ramp conditions.
- **Phase B** (comparative evaluation): 20 replicated experiment runs (5 per scenario) with randomized execution order and 300-second duration at 100 RPS steady-state load. Robust statistical analysis applied: Welch's t-test, Mann-Whitney U, bootstrap confidence intervals, and Cohen's d effect sizes.
- **Phase C** (dynamic workload): 6 additional runs (3 per scenario) with burst workload pattern (30→150 RPS ramp/burst cycles) to provide favorable conditions for predictive triggering.

**Hypothesis outcomes:**

**H1 — Hybrid architecture outperforms pure approaches:**
- *Mechanism*: ✅ Validated. Weight shifting (100/0 → 50/50) and serverless engagement confirmed operational.
- *Statistical superiority*: ⚠️ Not established. S4 showed lower mean p99 than S1 (431ms vs 647ms, 217ms improvement) with large practical effect (Cohen's d = −1.014), but the difference was not statistically significant (p = 0.17, n = 4–5 after outlier exclusion). The k3d single-node testbed introduces localhost routing bias that artificially advantages pure-K8s scenarios.

**H2 — Predictive scaling outperforms reactive:**
- *Mechanism*: ✅ Validated in Phase A1. PREDICTIVE successfully triggered before SLO violation during ramp workload.
- *Statistical superiority*: ⚠️ Not demonstrated. The GRU prediction server was not running during Phase B experiments (gru_predictions_used = 0 across all 20 runs), inadvertently converting S4 into reactive-only mode. Phase C confirmed this pattern: SCALE_OUT priority preemption prevents PREDICTIVE from triggering under automated conditions. S4 vs S3 comparison yielded p = 0.87 with negligible effect (d = −0.124).

**H3 — GRU prediction adequacy:**
- ✅ **Fully validated.** All accuracy targets met on synthetic data: 6.01% RMSE (<10%), 4.91% MAE (<5%), ~40ms latency (<50ms), confidence scores 0.72–0.88.

**Cost analysis** under the unified AWS model confirms that both workload intensity and execution-time signal selection affect cost ranking. In the all-scenarios rerun-v2 (2026-02-21, `n=1` each) with serverless-specific app-duration sizing, costs are S1 $0.061, S2 $0.169, S3 $0.486, and S4 $0.432 per 1200s. This bundle is directional and pipeline-validating rather than inferential final evidence, but it confirms that hybrid/serverless pricing must use serverless-specific execution signals (not blended scenario duration) when available. The fib(34) crossover analysis still shows workload sensitivity (S1-vs-S2 crossover ~65.9 RPS for fib(34) vs ~97.9 RPS for fib(32)).

In summary, this research successfully validates all proposed **mechanisms** — the GRU predictor achieves target accuracy, the routing controller correctly shifts traffic based on SLO status, and predictive actions trigger before violations under appropriate conditions. However, **statistical superiority** over baseline approaches was not established due to testbed constraints (single-node k3d deployment, localhost routing bias, GRU unavailability during controlled experiments, and insufficient sample sizes for normality assumptions). The work represents an engineering contribution with validated mechanisms and clearly identified deployment requirements for production validation.

*(Evidence: `results/experiments/phase-b/2026-02-21_all-scenarios-rerun-v2/`, `results/experiments/phase-b/2026-02-18_fib34-validation/`, `results/experiments/phase-c/2026-02-13_dynamic-workload/`, `results/cost/2026-02-21_all-scenarios-rerun-v2-unified-aws-cost/`, `results/cost/2026-02-18_fib34-unified-aws-cost/`)*

---

## 5.2 Saran (Future Work)

Based on the limitations identified during evaluation, six directions are recommended for future research:

1. **Multi-node cloud deployment.** The most critical limitation was the single-node k3d testbed, which introduces localhost routing bias and eliminates network latency differentials between Kubernetes and serverless backends. Deploying on a multi-node cloud cluster (e.g., 3+ nodes on AWS EKS or GCP GKE with Knative on separate nodes) would provide realistic network conditions necessary to establish statistical superiority of hybrid routing. The current experiment deliberately constrains node allocatable CPU (`system-reserved=15600m`) to force Cluster Autoscaler activity; production deployment would eliminate this artificial constraint and provide realistic CA trigger frequency data.

2. **Algorithm 2 (Cluster Controller) integration with Kubernetes HPA.** The proposed horizontal scaling formula R = αx + β should be fully implemented and integrated with the Kubernetes Horizontal Pod Autoscaler. This would enable the system to not only route traffic between cluster types but also proactively scale Kubernetes replicas based on GRU predictions, completing the original ElaX modification design.

3. **Dynamic workload experiments with extended ramp periods.** Phase C demonstrated that PREDICTIVE requires a healthy observation window longer than the ramp duration (~60 seconds) to build trend predictions before SCALE_OUT preempts it. Future experiments should use workload patterns with gradual ramps (≥90 seconds) and longer baseline periods to provide the PREDICTIVE mechanism sufficient lead time. Additionally, reducing the decision interval below 15 seconds could improve responsiveness.

4. **GRU retraining on production HTTP traces.** While the GRU achieves target accuracy on synthetic data, real-trace performance (17.78% RMSE on ClarkNet) falls short of thresholds due to non-stationarity and irregular burst patterns. Retraining on production HTTP traces with appropriate feature engineering (time-of-day encoding, day-of-week seasonality) and online learning capabilities would improve real-world applicability.

5. **Knative minScale=1 configuration to eliminate cold start penalty.** Cold starts were observed as a confounding factor in both Phase B and Phase C experiments (e.g., Phase C S4-run3 outlier with p95=261ms). Setting Knative's `minScale=1` would maintain a warm serverless instance, eliminating cold start latency from the comparison and isolating the routing mechanism's contribution to performance.

6. **Extended statistical validation with larger sample sizes.** The current experiments (n=4–5 per scenario after outlier exclusion) lack sufficient statistical power to detect the observed effect sizes. Future work should target n ≥ 30 runs per scenario to satisfy normality assumptions for parametric tests and achieve adequate power (β ≥ 0.80) for the large effects observed (d ≈ 1.0). This would provide definitive evidence regarding H1 and H2 superiority claims.
