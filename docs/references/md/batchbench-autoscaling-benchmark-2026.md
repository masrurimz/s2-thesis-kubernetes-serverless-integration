---
# --- bibliographic record ---
entry_type: misc
title: "BatchBench: Toward a Workload-Aware Benchmark for Autoscaling Policies in Big Data Batch Processing -- A Proposed Framework"
authors:
  - "Venkata Krishna Prasanth Budigi"
  - "Siri Chandana Sirigiri"
year: 2026
venue: "arXiv preprint"
volume: ""
issue: ""
pages: ""
publisher: ""
doi: ""
arxiv: "2605.12272"
url: "https://arxiv.org/abs/2605.12272"

# --- archive record ---
source_pdf: batchbench-autoscaling-benchmark-2026.pdf
source_sha256: e2b5860ea68e11a855445151f994c127db7876dc8cd673c1ba22ba07b6e1ac12
pdf_pages: 5
converted: 2026-09-13
record_source: arxiv
key_insight: "Five-axis evaluation: cost, SLA, responsiveness, thrash, interpretability; paired Wilcoxon + bootstrap CIs"
first_page: "BatchBench: Toward a Workload-Aware Benchmark for Autoscaling Policies in Big Data Batch Processing A Proposed Framework (Position Paper) Venkata Krishna Prasanth Budigi Sunnyvale, CA, USA krishnapras"
---
# BatchBench: Toward a Workload-Aware Benchmark for Autoscaling Policies in Big Data Batch Processing 

A Proposed Framework (Position Paper) 

Venkata Krishna Prasanth Budigi 

Venkata Krishna Prasanth Budigi Siri Chandana Sirigiri Sunnyvale, CA, USA USA krishnaprasanth.bv@gmail.com sirisirigiri@gmail.com 

**_Abstract_ —Autoscaling has become a baseline expectation for cloud-native big data processing, and the design space has expanded beyond rule-based heuristics to include learned controllers and, most recently, large language model (LLM) agents. Yet despite a growing body of work spanning these paradigms, the community lacks a shared benchmark for comparing them. Existing evaluations rely on synthetic TPC-style queries, vendor blog posts with proprietary baselines, or narrow trace replays. Each new policy reports favorable numbers against a different baseline, on a different workload, with a different cost model, making cross-paper comparison effectively impossible.** 

**This is a position paper. We propose BatchBench, an open benchmarking framework designed to place rule-based, learned, and agentic autoscaling policies on equal experimental footing. The contribution is the design of the framework, not empirical results. We contribute: (1) a workload taxonomy of six batch processing classes synthesized from published autoscaling benchmarks and publicly released cluster traces; (2) the design of a parameterized workload generator with a validation methodology based on two-sample Kolmogorov–Smirnov and earth-mover distance; (3) a five-axis evaluation harness specification covering cost, SLA attainment, scaling responsiveness, scaling thrash, and decision interpretability, with first-class accounting for LLM inference cost; and (4) a standardized agent interface that lets LLM-based and reinforcement-learning autoscalers be evaluated alongside rule-based controllers with a single API. We discuss the expected evaluation surface, identify open research questions the framework is designed to answer, and outline a roadmap for the empirical paper that will follow. BatchBench’s reference implementation is in active development and will be released as open source.** 

**_Index Terms_ —big data, autoscaling, benchmarking, Apache Spark, agentic AI, large language models, reinforcement learning, cloud computing, position paper** 

## I. INTRODUCTION 

Cloud-native big data platforms have made autoscaling table stakes. Apache Spark ships dynamic resource allocation; Google Dataproc Serverless transparently manages cluster size; Amazon EMR on EKS offers vertical pod autoscaling; Databricks markets an optimized autoscaler that adapts executor counts to shuffle and stage statistics. The question is no longer whether to autoscale — it is which autoscaler to trust, under what workload conditions, and at what cost. 

The design space has expanded faster than the evaluation methodology. Learned database tuning systems such as Db2une [5], EAST [7], LOFTune [6], and Hyper [16] apply reinforcement learning to configurations that include resource sizing. Retrieval-augmented controllers such as Rabbit [10] treat tuning as a knowledge-retrieval problem. Agentic systems including D-Bot [11], AgentTune [9], and GaussMaster [12] use LLMs as autonomous administrators capable of proposing, justifying, and revising scaling decisions in natural language. Each new system reports favorable numbers against a different baseline, on a different workload, with a different cost model. The result is a literature in which practitioner-relevant questions cannot be answered from published evidence: does dynamic allocation outperform learned policies on shuffleheavy ETL? Do LLM agents generalize across workload classes, or do they overfit to in-context examples? When does the inference cost of an agentic controller outweigh its cost savings? 

**Position.** We argue that the field needs a workload-aware benchmark for autoscaling — one that (i) is grounded in batch workload characteristics drawn from published cluster traces, (ii) reports a multi-objective evaluation surface that captures cost, SLA, responsiveness, stability, and interpretability, (iii) supports plug-in policies across the rule-based, learned, and agentic paradigms on equal footing, and (iv) is released as an open artifact. This paper presents the design of such a benchmark, which we call **BatchBench** , and motivates each design choice with reference to limitations in the current literature. We deliberately defer empirical results to a followup paper. The reasons for this separation are explained in Section IX. 

**Contributions of this position paper.** (1) A literaturegrounded workload taxonomy of six batch processing classes, synthesized from published benchmark suites and publicly available cluster traces. (2) The design of a parameterized workload generator, with a validation methodology based on two-sample Kolmogorov–Smirnov and earth-mover distance metrics. (3) A specification of a five-axis evaluation harness measuring cost, SLA attainment, scaling responsiveness, scal- 

ing thrash, and decision interpretability. (4) A standardized agent interface that places rule-based, learned, and LLMagentic policies on equal experimental footing, including firstclass accounting for LLM inference cost — the literature’s most common omission. (5) A discussion of the expected evaluation surface and the open research questions BatchBench is designed to answer. 

## II. RELATED WORK AND GAP ANALYSIS 

## _A. Rule-Based Autoscaling in Big Data Engines_ 

Apache Spark’s dynamic resource allocation [1] adjusts executor count from pending and running task counts, using an external shuffle service for safe downscaling. The policy is reactive and configuration-heavy; defaults are rarely tuned per workload, and industry studies [14], [15] have reported over-provisioning on shuffle-heavy and skewed jobs. Managed services extend Spark’s allocation with cluster-level scaling: Dataproc Serverless autoscales executors and nodes; EMR on EKS offers signature-driven vertical pod autoscaling [15]; Databricks’s optimized autoscaler leverages shuffle and stage statistics [3]. The closest published evaluation in this space is benchspark [4], which releases a Spark trace dataset on Dataproc Serverless. benchspark is a valuable artifact but it is limited to a single environment, a hand-constructed workload set, and does not evaluate learned or agentic policies. BatchBench is intended to extend the benchspark methodology along all three axes. 

## _B. Learned Autoscaling and Configuration Tuning_ 

Learned tuning has progressed rapidly. Db2une [5] applies deep reinforcement learning to database tuning. LOFTune [6] proposes a low-overhead Spark SQL tuner. EAST [7] introduces interpretable knob estimation. Hyper [16] applies multi-agent RL to joint physical-design and resource tuning. Three weaknesses recur across this literature and motivate the BatchBench design: (i) evaluation rests heavily on TPCDS and TPC-H, omitting iterative ML preprocessing and production-style ETL; (ii) generalization to unseen workload distributions is rarely measured; (iii) the inference cost of the learned policy itself is often excluded from the cost model, biasing comparisons. 

## _C. Agentic AI for Data Systems_ 

The most recent wave of work introduces LLMs as autonomous agents for data system management. D-Bot [11] demonstrates an LLM-powered DBA copilot. AgentTune [9] frames database knob tuning as LLM-driven planning with proposal, execution, and revision. Rabbit [10] adds retrievalaugmented generation over historical tuning logs. GaussMaster [12] extends agentic operation to end-to-end database management. The technical core is convergent: an LLM is given a structured observation, a tool interface, and a reward signal; it proposes actions, optionally explains them, and revises strategy when outcomes diverge from expectations. A separate strand of recent work has examined the data layer that supports such retrieval-augmented agents in production [28], 

finding that unified Postgres-based retrieval substrates with native vector search materially reduce latency and tenantisolation failures compared to split-system architectures — a design choice we adopt for BatchBench’s retrieval-augmented policy. The quantitative evidence base for agentic autoscalers themselves nonetheless remains thin — most evaluations cover a single workload, omit inference cost, and do not measure decision variance. BatchBench is designed to be, to our knowledge, the first benchmark to evaluate agentic autoscalers under controlled conditions against rule-based and learned baselines with reported variance and statistical tests. 

## _D. Public Cluster Traces_ 

Publicly available cluster traces inform BatchBench’s workload taxonomy. The Alibaba cluster trace [25] released approximately 4,000 machines worth of batch and online job data. The Google Borg traces [26] released cell-level resource usage at large scale. The SWIM benchmark suite [27] derives Hadoop workloads from Facebook traces. These public artifacts let BatchBench’s taxonomy be grounded in real-world batch processing characteristics without requiring access to proprietary data — an explicit design choice motivated by reproducibility. 

## III. LITERATURE-GROUNDED WORKLOAD TAXONOMY 

BatchBench’s workload classes are synthesized from three sources: (i) the structural categories used by established benchmarks such as TPC-DS, TPC-H, TPCx-BB, HiBench, and SparkBench; (ii) the resource-usage distributions reported in publicly released cluster traces from Alibaba [25], Google [26], and the SWIM suite [27]; and (iii) workload characterizations published in industry engineering blogs from cloud vendors operating Spark at scale [3], [14], [15]. We retained six classes that span the structural and statistical diversity of batch processing workloads documented in this literature. 

## _A. The Six Workload Classes_ 

**Class 1 — Shuffle-Heavy ETL.** Multi-stage transformations dominated by wide dependencies. Typical shuffle-toinput ratios of 2–3 _×_ . Common in nightly fact-table builds and slowly-changing-dimension updates, as documented in [14], [15]. 

**Class 2 — Skewed Multi-Way Joins.** Three- or four-way joins with one or more participants exhibiting heavy key skew. Documented as a persistent failure mode of default autoscalers in [14]. Modeled in BatchBench using class-specific Zipf exponents fit from public trace key-frequency distributions. 

**Class 3 — Iterative ML Preprocessing.** Featureengineering pipelines that loop over a stable input set, exhibiting cache-sensitive resource profiles. Underrepresented in TPC-style benchmarks but prominent in cluster trace analyses [25]. 

**Class 4 — Time-Windowed Aggregations.** Rolling aggregations over fixed time windows with one large groupBy and 

sort-and-rank operations. Predictable within-window resource profile, documented across multiple public traces. 

**Class 5 — Broadcast-Bounded Lookups.** Pipelines whose largest stage is a broadcast hash join against a small dimension table. Executor scaling provides limited benefit beyond a threshold — an autoscaler failure mode rarely surfaced in benchmark literature. 

**Class 6 — Bursty SLA-Driven Reporting.** Event-triggered pipelines with hard deadlines, bursty submission patterns, and high inter-invocation variance. Documented as the hardest class for reactive autoscalers in [14], [15] and in public trace analyses [26]. 

BatchBench retains all six base classes and defines six derived subclasses that vary input scale and skew within each base class, producing twelve evaluation subclasses. Six will be designated in-distribution and six held-out for generalization measurement; the split is constructed so that no in-distribution subclass shares both base class and skew level with its held-out counterpart, forcing genuine generalization rather than nearestneighbor lookup. 

## IV. BATCHBENCH DESIGN 

BatchBench’s reference implementation is structured as three components: a workload generator, a uniform policy interface, and an evaluation harness. This section specifies each. 

representation with bounded token count, eliminating promptlength variance. A tool-use surface exposes scaling primitives, cost queries, and historical trace lookups as functions the LLM may call, supporting retrieval-augmented decisionmaking over a unified data layer such as the Postgres + pgvector + HNSW substrate evaluated in our prior work [28]. An inference-cost accountant records token usage and decision latency per call so that the cost of the agent itself enters the evaluation — the literature’s most common omission. 

## _C. Evaluation Harness_ 

The harness will orchestrate job execution across multiple cloud environments, with initial implementation targeting Google Dataproc Serverless and Amazon EMR on EKS. A common driver injects the policy under test in place of the platform default; where the platform resists policy replacement, a shadow mode runs the platform policy in production while the test policy issues advisory actions. The harness records five families of measurements: (i) cost in vCPU-hours and normalized dollar terms; (ii) SLA attainment as the fraction of jobs completing before deadline; (iii) responsiveness as median delay between workload phase transition and scaling action; (iv) thrash as scaling actions per job-minute; (v) interpretability, scored for policies that emit justifications. 

## V. PLANNED EVALUATION METHODOLOGY 

## _A. Policies to be Evaluated_ 

## _A. Workload Generator_ 

The generator emits Spark jobs whose structural and statistical properties match a target workload class. Each class is parameterized by (i) a structural template describing the logical plan, (ii) marginal distributions for input size, partition count, key skew (modeled as a Zipf exponent fit per class from public trace data), and stage count, and (iii) a join-graph generator for multi-way join classes. Synthetic data is produced from seeded random streams, ensuring determinism across runs and diversity across seeds. The generator is validated against public trace data by computing per-class two-sample Kolmogorov– Smirnov statistics on input size and shuffle volume, and earthmover distance on key-frequency histograms. 

## _B. Policy Interface and Agent Adapter_ 

BatchBench defines a uniform policy interface. At each decision interval (default: 30 seconds), the policy receives a structured observation containing cluster state, recent task and stage metrics, the cost model, and the SLA deadline. It returns a scaling action specifying target executor count and, optionally, a natural-language justification. The interface accommodates four policy families on equal footing: (i) rulebased controllers; (ii) supervised learners that predict executor counts from workload fingerprints; (iii) RL agents with explicit reward functions; (iv) LLM-based agents that receive observations as structured prompts and emit actions and rationales. 

The agent adapter provides three features critical to making LLM-based policies practical to benchmark. A structured observation serializer converts cluster state into a compact JSON 

**Rule-based:** (R1) Spark dynamic allocation with default parameters; (R2) Databricks optimized autoscaling; (R3) Dataproc Serverless managed autoscaling. 

**Learned:** (L1) DQN controller trained on in-distribution subclasses; (L2) PPO controller with continuous action space; (L3) supervised fingerprint learner predicting optimal executor count from a workload fingerprint, in the style of EAST. 

**Agentic:** (A1) zero-shot LLM agent with the structured observation interface; (A2) few-shot LLM agent with exemplar decisions per class; (A3) retrieval-augmented LLM agent that retrieves the nearest historical workloads before each decision; (A4) hybrid agent that runs PPO by default and invokes the LLM only when PPO’s value-function epistemic uncertainty exceeds a per-class threshold. 

## _B. Experimental Protocol_ 

Each (policy _×_ subclass _×_ environment) cell will be repeated five times with independent random seeds. Acrosspolicy comparisons will use the paired Wilcoxon signedrank test on per-job cost ratios; confidence intervals on cost ratios will use the bias-corrected accelerated bootstrap (BCa, _B_ = 10 _,_ 000). Multiple comparisons across policy pairs will be controlled with Holm–Bonferroni at family-wise _α_ = 0 _._ 05. 

## _C. Distribution Splits and Interpretability_ 

Six of twelve subclasses will be designated in-distribution and six held out, with the split forcing genuine generalization rather than interpolation. For agentic policies, interpretability will be scored on three axes: faithfulness (counterfactual 

TABLE I 

BATCHBENCH WORKLOAD CLASS SUMMARY (CHARACTERISTICS FROM LITERATURE SYNTHESIS). 

|**Class**|**Shuffle/Input**|**Skew**|**Defining Characteristic**|
|---|---|---|---|
|1. Shuffle-Heavy ETL|High (2–3_×_)|Low–Med|Wide dependencies dominate|
|2. Skewed Multi-Way Joins|Medium|High|Heavy key-frequency skew|
|3. Iterative ML Preprocessing|Low–Med|Low|Cache-sensitive iterations|
|4. Time-Windowed Aggregations|Medium|Low|Predictable groupBy + sort|
|5. Broadcast-Bounded Lookups|Low|Low|Broadcast-side bottleneck|
|6. Bursty SLA-Driven Reporting|Medium|Variable|Bursty arrivals + hard SLA|



perturbation), actionability (blinded reviewer task), and consistency (cross-run variance). Each axis is scored 0–3 by two independent reviewers with Cohen’s _κ_ reported. 

## VI. HYPOTHESES AND EXPECTED EVALUATION SURFACE 

BatchBench is designed to test four hypotheses that follow from gaps identified in the literature review. We articulate them here so that the framework’s empirical follow-up can be evaluated against falsifiable predictions rather than openended discovery. 

**H1 — Default over-provisioning is large.** Spark dynamic allocation in its default configuration will over-provision shuffle-heavy ETL workloads by a margin substantially larger than the gap typically reported in vendor blog comparisons. We expect the gap on Class 1 to exceed 30% relative to the cost-optimal policy. 

**H2 — Learned policies will exhibit a generalization gap.** Policies that achieve the lowest in-distribution cost will lose a substantial fraction of their advantage on held-out workloads. We expect the gap to be largest for value-based RL (DQN) and smaller for policy-gradient methods (PPO), consistent with the broader RL literature. 

**H3 — LLM agents will generalize gracefully but with high variance.** LLM-based agents will exhibit smaller generalization gaps than pure learned controllers, but they will exhibit measurably higher decision variance under distribution shift — we expect a 1.5–3 _×_ increase in standard deviation of recommended executor counts. 

**H4 — A hybrid composition will dominate pure paradigms.** A policy that runs a fast deterministic learned controller as its default path and invokes an LLM agent only on high-uncertainty decisions will achieve lower held-out cost than any pure rule-based, learned, or agentic policy. This is the central architectural prediction the benchmark is designed to test. 

These hypotheses correspond to documented gaps in the literature: H1 to industry reports of default autoscaler overprovisioning [14], [15]; H2 to the well-established distributionshift brittleness of value-based RL [18]; H3 to the broader LLM-as-agent literature in which retrieval and in-context examples reduce but do not eliminate decision variance; H4 to the emerging pattern of hybrid agent architectures in production AI systems. The contribution of an empirical BatchBench evaluation will be to confirm or refute these hypotheses with statistical rigor, on a workload set that spans the diversity of 

batch processing rather than the narrow slice covered by TPCstyle benchmarks. 

## VII. ANTICIPATED THREATS TO VALIDITY 

**Construct validity.** Cost models will use each cloud provider’s published on-demand rates. Spot, committed-use, and reserved pricing will alter absolute numbers but should not affect relative policy ordering, which is determined primarily by resource utilization. SLA deadlines will be derived from public trace annotations where available and from a default of 2 _×_ median runtime otherwise. 

**Internal validity.** Per-cell repetition (planned _n_ = 5) controls run-to-run variance. Statistical significance will use paired Wilcoxon with Holm–Bonferroni correction; bootstrap confidence intervals will use 10,000 resamples. Shadow-mode evaluation on managed environments will be cross-validated against direct-replacement runs where possible. 

**External validity.** The workload taxonomy is synthesized from a finite set of public traces and published benchmarks. BatchBench’s generator is parameterized: practitioners can fit class distributions to their own traces and re-run the full benchmark, which we view as the principled path to external validity. The agent interface is model-agnostic. 

## VIII. DISCUSSION AND IMPLICATIONS 

If hypothesis H4 holds, the practical implication is significant: production-grade agentic data infrastructure should be architected as hybrid systems in which a fast deterministic learned controller handles the bulk of decisions and an LLMbased agent is invoked selectively on uncertain or novel observations. This composition pattern — fast deterministic core, slow reflective agent invoked sparingly — bounds the worst-case cost contribution of the LLM (inference is a few percent of total spend) while exploiting the LLM’s distinct value: behavior that degrades gracefully under distribution shift. 

Whether or not H4 holds, the methodological contribution of BatchBench stands. Reproducible, multi-objective, paradigmagnostic evaluation is currently absent from the autoscaling literature. Even a careful empirical refutation of one or more of our hypotheses would represent a meaningful contribution to a field that currently has no shared experimental ground truth. 

Four open problems will frame the empirical follow-up: (i) distribution-shift detection, which gates LLM invocation in 

hybrid policies; (ii) LLM inference cost amortization through distillation, caching, and shared retrieval; (iii) extension of the BatchBench methodology to sub-minute streaming intervals; (iv) trust and consistency, which remain weak axes for all agentic policies. 

## IX. IMPLEMENTATION STATUS AND ROADMAP 

BatchBench’s reference implementation is in active development. The workload generator and the policy interface have reached an early-implementation stage; the evaluation harness for Google Dataproc Serverless is under construction; baseline implementations of the rule-based and supervised policies are complete; the RL controllers and agentic policies are in design and prototyping. We anticipate releasing the open-source reference implementation alongside the empirical follow-up paper, which we target for completion within twelve months. 

We are publishing this paper as a position paper for three reasons. First, the design of an evaluation framework is itself a research contribution distinct from the empirical results it later produces — a separation common in benchmark papers (TPC, YCSB, MLPerf were each preceded by design papers or technical reports). Second, early publication solicits community input on the workload taxonomy, the evaluation axes, and the agent interface before the empirical evaluation is locked in. Third, the open research questions and hypotheses in Section VI are themselves of standalone value to researchers entering this space. 

We invite collaborators — in industry or academia — who would like to contribute workload classes, policy implementations, or independent evaluations on their own infrastructure. The reference implementation will be released under an opensource license. 

## X. CONCLUSION 

We presented BatchBench, a proposed workload-aware benchmark for big data autoscaling that places rule-based, learned, and agentic policies on equal experimental footing. Grounded in a literature synthesis of published benchmarks and public cluster traces, specified with a uniform policy interface and a five-axis evaluation harness, and designed around four falsifiable hypotheses, BatchBench is intended to give the autoscaling community a shared experimental basis it currently lacks. This is a position paper; the empirical followup will report results, releases, and refinements informed by community feedback. We welcome that feedback. 

- [2] M. Armbrust et al., “Lakehouse: A New Generation of Open Platforms that Unify Data Warehousing and Advanced Analytics,” in _Proc. CIDR_ , 2021. 

- [3] Databricks, “Introducing Databricks Optimized Auto-scaling on Apache Spark,” Databricks Engineering Blog, 2018. 

- [4] J. Will et al., “Experimentally Evaluating the Resource Efficiency of Big Data Autoscaling,” arXiv:2501.14456, 2025. 

- [5] X. Liang et al., “Db2une: Tuning Under Pressure via Deep Learning,” in _Proc. VLDB_ , 2024. 

- [6] Y. Zhang et al., “LOFTune: A Low-Overhead and Flexible Approach for Spark SQL Configuration Tuning,” _IEEE TKDE_ , 2025. 

- [7] R. Zhou et al., “EAST: An Interpretable Knob Estimation System for Cloud Database,” in _Proc. ICDE_ , 2025. 

- [8] X. Trummer, “The Database Gym,” in _Proc. SIGMOD_ , 2025. 

- [9] W. Wang et al., “AgentTune: An Agent-Based Large Language Model Framework for Database Knob Tuning,” in _Proc. SIGMOD_ , 2025. 

- [10] H. Sun et al., “Rabbit: Retrieval-Augmented Generation Enables Better Automatic Database Knob Tuning,” in _Proc. ICDE_ , 2025. 

- [11] X. Zhou et al., “D-Bot: An LLM-Powered DBA Copilot,” in _Proc. SIGMOD-Companion_ , 2025. 

- [12] Huawei Cloud, “GaussMaster: An LLM-based Database Copilot System,” arXiv preprint, 2025. 

- [13] J. Tan et al., “NeurDB: An AI-powered Autonomous Data System,” arXiv:2408, 2024. 

- [14] Onehouse, “Why the Apache Spark Default Autoscaler Fails Your Lakehouse,” Onehouse Engineering Blog, Sep. 2025. 

- [15] Amazon Web Services, “Improve reliability and reduce costs of your Apache Spark workloads with vertical autoscaling on Amazon EMR on EKS,” AWS Big Data Blog, 2023. 

- [16] J. Doe et al., “Hyper: Hybrid Physical Design Advisor with Multi-agent Reinforcement Learning,” in _Proc. ICDE_ , 2025. 

- [17] J. Schulman et al., “Proximal Policy Optimization Algorithms,” arXiv:1707.06347, 2017. 

- [18] V. Mnih et al., “Human-level control through deep reinforcement learning,” _Nature_ , vol. 518, 2015. 

- [19] T. Brown et al., “Language Models are Few-Shot Learners,” in _Proc. NeurIPS_ , 2020. 

- [20] P. Lewis et al., “Retrieval-Augmented Generation for KnowledgeIntensive NLP Tasks,” in _Proc. NeurIPS_ , 2020. 

- [21] X. Wang et al., “Self-Consistency Improves Chain of Thought Reasoning,” in _Proc. ICLR_ , 2023. 

- [22] Y. Gal and Z. Ghahramani, “Dropout as a Bayesian Approximation,” in _Proc. ICML_ , 2016. 

- [23] B. Efron, “Better Bootstrap Confidence Intervals,” _J. Amer. Statist. Assoc._ , 1987. 

- [24] S. Holm, “A Simple Sequentially Rejective Multiple Test Procedure,” _Scand. J. Statist._ , 1979. 

- [25] Alibaba Group, “Alibaba Cluster Trace Program,” https://github.com/ alibaba/clusterdata, 2018–2023. 

- [26] J. Wilkes, “Google Cluster-Usage Traces v3,” Technical Report, Google Inc., 2020. 

- [27] Y. Chen et al., “The Case for Evaluating MapReduce Performance Using Workload Suites (SWIM),” in _Proc. MASCOTS_ , 2011. 

- [28] V. K. P. Budigi and S. C. Sirigiri, “Beyond Similarity Search: A Unified Data Layer for Production RAG Systems,” arXiv:2605.03275, 2026. 

## ACKNOWLEDGMENTS 

We thank the open-source maintainers of Apache Spark, Apache Iceberg, and Apache Hudi, and the curators of the Alibaba, Google, and SWIM public cluster traces. 

## REFERENCES 

[1] Apache Spark Project, “Dynamic Resource Allocation,” Apache Spark Documentation, https://spark.apache.org/docs/latest/job-scheduling. html. 

