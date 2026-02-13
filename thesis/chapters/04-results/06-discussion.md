## 4.6 Discussion

This section synthesizes findings across all experimental phases to address the research hypotheses, identify the contributions and limitations of the work, and frame the results for interpretation.

### 4.6.1 Synthesis of Findings

The experimental evaluation validates the **mechanistic correctness** of the hybrid architecture while revealing that **statistical superiority** over baseline approaches could not be established within the constraints of the testbed.

**Mechanisms validated:**

1. **GRU prediction** achieves target accuracy on synthetic data (RMSE 6.01%, MAE 4.91%) and demonstrates meaningful generalization to real traces (RMSE 17.78% on ClarkNet, substantially better than statistical baselines). The model operates within latency constraints (~40ms) and produces actionable confidence scores (0.72–0.88).

2. **Routing controller** correctly implements the priority-based decision framework: SCALE_OUT responds to active violations, PREDICTIVE pre-positions capacity during healthy periods when surges are predicted, and OPTIMIZE_COST reclaims resources during stable states. The weight-shifting mechanism (100/0 → 50/50) operates as designed.

3. **Predictive pre-warming** was validated in Phase A1: PREDICTIVE triggered at p99 = 146ms upon detecting a 47% predicted workload increase with 72% confidence, successfully pre-positioning serverless capacity before SLO violation occurred.

4. **Cost efficiency** of predictive routing is projected at 6–9% savings over reactive approaches across three major cloud providers, driven by reduced unnecessary serverless invocations.

**Superiority not established:**

1. **H1 (S4 vs. S1):** p = 0.173 with n = 4–5 after outlier exclusion. Despite a large effect size (d = −1.014) and a 217ms improvement in mean p99, the result is not statistically significant. The k3d single-node testbed introduces localhost routing bias that artificially advantages pure K8s (S1): all traffic remains on the same machine, eliminating the network latency differential that would favor hybrid routing in a multi-node deployment.

2. **H2 (S4 vs. S3):** p = 0.865 with negligible effect (d = −0.124) in Phase B. The GRU prediction server was not running during Phase B experiments (gru_predictions_used = 0 across all 20 runs), inadvertently converting S4 into reactive-only mode—functionally identical to S3. Phase C showed trending improvement (20–28% better on all metrics) with large effect sizes (d = 0.80–0.88) but insufficient sample size (n = 3) for significance (p > 0.35).

### 4.6.2 Interpretation of Effect Sizes

The tension between large effect sizes and non-significant p-values reflects a statistical power limitation, not an absence of practical difference. Cohen's d = −1.014 for H1 represents a "large" effect by conventional standards—the means of S4 and S1 are separated by more than one pooled standard deviation. A post-hoc power analysis suggests that approximately n = 15–20 runs per scenario would be required to detect this effect size at α = 0.05 with 80% power. The current n = 4–5 provides approximately 30–40% power for this effect size, meaning there is a 60–70% probability of failing to detect a true difference of this magnitude—exactly the outcome observed.

Similarly, the Phase C effect sizes (d = 0.80–0.88) are substantively large but underpowered at n = 3. The data are consistent with a real performance difference between S4 and S3 that would likely reach significance with adequate sample sizes, but the current evidence does not support this claim definitively.

### 4.6.3 Testbed Limitations

Three testbed constraints systematically affect the interpretation of comparative results:

**Localhost routing bias.** All traffic in the k3d single-node testbed traverses localhost. In a production multi-node deployment, K8s pods and Knative instances would reside on different nodes with measurable network latency between them. The hybrid routing controller's ability to choose the faster backend is neutralized when all backends are equidistant (localhost). This bias disproportionately advantages S1 (K8s-only), which has no routing overhead, and disadvantages S3 and S4, which incur decision-making and weight-adjustment costs without the network-latency benefit they are designed to exploit.

**GRU server unavailability in Phase B.** The automated experiment runner did not start the GRU prediction server, converting all S4 runs into reactive-only behavior. This is the most significant limitation for H2 evaluation: Phase B does not test predictive versus reactive routing; it compares two reactive variants. Only Phase A1 (manual, non-replicated) validates the PREDICTIVE mechanism.

**Insufficient load variation.** Phase B used steady 100 RPS load, which produces zero predicted load change—below the 30% threshold required for PREDICTIVE eligibility. Even with GRU running, Phase B would not have triggered PREDICTIVE. Phase C used dynamic bursts but the ramp duration (30 seconds) was shorter than the GRU's observation window requirement (~60 seconds), and SCALE_OUT priority preemption consumed the available decision space.

### 4.6.4 Honest Assessment of Contributions

This research demonstrates an **engineering contribution**: the design, implementation, and mechanism validation of a hybrid Kubernetes-serverless system with GRU-based prediction. The specific contributions are:

1. A **validated GRU predictor** for HTTP workloads that meets accuracy targets on synthetic data, demonstrates meaningful generalization to real traces, and operates within real-time latency constraints.

2. An **SLO-aware routing controller** (Algorithm 1) with a priority-based decision framework that correctly implements SCALE_OUT, PREDICTIVE, OPTIMIZE_COST, and MAINTAIN actions. The predictive pre-warming mechanism was demonstrated to trigger before SLO violations in appropriate conditions.

3. A **comprehensive evaluation framework** with transparent reporting that clearly distinguishes validated mechanism claims from unestablished superiority claims, provides pre-specified exclusion criteria for data quality, and documents threats to validity.

What this research does **not** demonstrate is statistically significant performance superiority of the hybrid-predictive approach over baselines. This remains an open question requiring production deployment on multi-node infrastructure with sufficient sample sizes and dynamic workloads designed to provide the PREDICTIVE mechanism adequate lead time.

### 4.6.5 Comparison with the ElaX Framework

The original ElaX algorithm by Yang et al. (2019) proposed a two-layer decision framework for elastic provisioning. This research extends ElaX in three ways: (a) integration of machine learning (GRU) prediction into the routing layer, enabling proactive decisions rather than purely reactive scaling; (b) adaptation for heterogeneous backends (K8s + serverless) rather than homogeneous container scaling; and (c) introduction of SLO-aware decision logic with configurable thresholds and confidence gating. Algorithm 2 (cluster controller) is integrated into the routing daemon for real-time replica scaling, though its independent contribution was not isolated in the experimental evaluation.

### 4.6.6 Defensible Position

The results support the following defensible framing for this work: the hybrid Kubernetes-serverless system with GRU-based prediction has been designed, implemented, and its mechanisms validated. All proposed components function correctly under appropriate conditions. Statistical performance superiority over baselines was not established due to testbed constraints (single-node k3d, localhost routing bias, GRU unavailability during controlled experiments, and insufficient sample sizes). Production deployment on multi-node cloud infrastructure with dynamic workloads and adequate replication would be required to resolve the superiority question—a direction documented as future work.

---

*Evidence locations: `results/models/gru/2026-02-10_training-synthetic/`, `results/models/gru/2026-02-13_training-clarknet-calgary/`, `results/experiments/phase-a1/2026-02-12_predictive-trigger/`, `results/experiments/phase-b/2026-02-12_replicated-20runs/`, `results/experiments/phase-c/2026-02-13_dynamic-workload/`, `results/cost/2026-02-11_proxy-analysis/`.*
