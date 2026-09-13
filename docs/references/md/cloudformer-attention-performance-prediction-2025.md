---
# --- bibliographic record ---
entry_type: misc
title: "CloudFormer: An Attention-based Performance Prediction for Public Clouds with Unknown Workload"
authors:
  - "Amirhossein Shahbazinia"
  - "Darong Huang"
  - "Luis Costero"
  - "David Atienza"
year: 2025
venue: "arXiv preprint"
volume: ""
issue: ""
pages: ""
publisher: ""
doi: ""
arxiv: "2509.03394"
url: "https://arxiv.org/abs/2509.03394"

# --- archive record ---
source_pdf: cloudformer-attention-performance-prediction-2025.pdf
source_sha256: 9cc9d3909171e251e818f8fde86eb61a663fe23977a0318a6fd7b6fb0ffc6b68
pdf_pages: 12
converted: 2026-09-13
record_source: arxiv
key_insight: "Dual-branch transformer for VM performance degradation; baselines DT/RF/LR/GLR/LSTM (Seq2Seq excluded from benchmark)"
first_page: "CloudFormer: An Attention-based Performance Prediction for Public Clouds with Unknown Workload Amirhossein Shahbazinia ESL, EPFL Lausanne, Switzerland amirhossein.shahbazinia@epfl.ch Darong Huang ESL,"
---
# CloudFormer: An Attention-based Performance Prediction for Public Clouds with Unknown Workload 

|Amirhossein Shahbazinia|Darong Huang|Luis Costero|David Atienza|
|---|---|---|---|
|_ESL, EPFL_|_ESL, EPFL_|_UCM_|_ESL, EPFL_|
|Lausanne, Switzerland|Lausanne, Switzerland|Madrid, Spain|Lausanne, Switzerland|
|amirhossein.shahbazinia@epfl.ch|darong.huang@epfl.ch|lcostero@ucm.es|david.atienza@epfl.ch|



**_Abstract_ —Cloud platforms are increasingly relied upon to host diverse, resource-intensive workloads due to their scalability, flexibility, and cost-efficiency. In multi-tenant cloud environments, virtual machines are consolidated on shared physical servers to improve resource utilization. While virtualization guarantees resource partitioning for CPU, memory, and storage, it cannot ensure performance isolation. Competition for shared resources such as last-level cache, memory bandwidth, and network interfaces often leads to severe performance degradation. Existing management techniques, including VM scheduling and resource provisioning, require accurate performance prediction to mitigate interference. However, this remains challenging in public clouds due to the black-box nature of VMs and the highly dynamic nature of workloads. To address these limitations, we propose CloudFormer, a dual-branch Transformer-based model designed to predict VM performance degradation in black-box environments. CloudFormer jointly models temporal dynamics and system-level interactions, using 206 system metrics at a onesecond resolution across both static and dynamic scenarios. This design enables the model to capture transient interference effects and adapt to varying workload conditions without scenariospecific tuning. Complementing the methodology, we provide a fine-grained dataset that significantly expands the temporal resolution and metric diversity compared to existing benchmarks. Experimental results demonstrate that CloudFormer consistently outperforms state-of-the-art baselines across multiple evaluation metrics, achieving robust generalization across diverse and previously unseen workloads. In particular, CloudFormer achieves a mean absolute error (MAE) of just 7.8%, representing a substantial improvement in predictive accuracy and outperforming existing methods at least by 28%.** 

**_Index Terms_ —Performance Prediction, Machine Learning, Virtual Machines, Public Clouds, Unknown Workloads, Resource Interference, System-level Metrics** 

## I. INTRODUCTION 

Global end-user spending on public cloud services has increased, exceeding 700 billion dollars in 2025, with sustained double digit growth expected in the coming years [1]. This expanding demand brings significant energy implications: global data center electricity consumption reached an estimated 240-340 terawatt hours (TWh) in 2022, or roughly 1.0–1.3% of global electricity demand, and US consumption hit 176 TWh (4.4%) in 2023, rising rapidly thereafter [2]. The International Energy Agency projects that the global 

demand for power from data centers will more than double to approximately 945 TWh by 2030 [3], intensifying the need for more efficient resource allocation strategies and robust mechanisms to mitigate performance interference. 

Virtualization technologies such as Intel VT and AMD-V [4, 5] enable providers to consolidate multiple virtual machines (VMs) on a single physical server, improving hardware utilization [6]. Although resource isolation between VMs is guaranteed for dedicated CPU cores, memory allocations, and disk partitions, performance isolation remains a persistent challenge. VMs still compete for shared resources, such as last-level cache (LLC), memory bandwidth, and network interfaces, among others. This contention can significantly degrade VM performance, particularly under multi-tenant workloads [7]. 

In practice, cloud providers operate under strict privacy constraints: VMs are treated as black-boxes, with no access to the application source code or internal runtime metrics. Performance monitoring is therefore limited to host-level hardware counters, which complicates runtime performance prediction [8]. The challenge intensifies under dynamic workloads, where performance variation may arise from both interference due to co-located tenants and intrinsic workload variation. Disentangling these effects is not trivial, yet essential for guiding resource management decisions. Accurate performance forecasting serves as a critical primitive for intelligent orchestration, enabling schedulers to optimize VM placement to minimize interference [9, 6], trigger resource throttling mechanisms for noisy neighbors [10], and ensure strict Service Level Agreement (SLA) compliance through proactive migration [11]. Without a reliable quantitative signal, these downstream systems are forced to react only after QoS violations have already occurred. 

Despite significant research on VM performance monitoring and prediction [7, 12, 13], existing methods face two key limitations. First, from a methodological point of view, prior models often rely on scenario-specific configurations (e.g., CPU- or network-intensive workloads), limiting their generalization to diverse and evolving cloud environments [14, 15, 16, 10]. These methods primarily focus on static workload 

scenarios as they are easier to control and reproduce, avoiding the complexities introduced by dynamic workload patterns and their temporal variability. Second, from a data perspective, publicly available datasets either lack fine-grained temporal resolution or provide only limited metrics or data [17, 18, 6, 19], restricting their utility for training robust predictive models. 

To address these limitations, we propose CloudFormer, a dual-branch Transformer-based architecture that jointly models temporal dynamics and system-level interactions to predict VM performance degradation. The temporal branch captures transient workload behavior at second-level granularity, while the system branch learns cross-metric dependencies. This design enables adaptation to both static and dynamic workloads without scenario-specific tuning, supported by a fine-grained dataset that significantly expands metric diversity and temporal detail compared to prior benchmarks. 

In summary, this work makes the following contributions: 

- We introduce CloudFormer, a dual-branch transformer architecture that jointly models temporal and system-level dynamics for VM performance degradation prediction in black-box cloud environments. 

- We integrate CloudPerfTrace<sup>1</sup> , a rich dataset that captures 206 system metrics with a resolution of one second in diverse static and dynamic scenarios, allowing finegrained modeling of transient interference effects. 

- We demonstrate that CloudFormer consistently outperforms state-of-the-art baselines across multiple evaluation metrics, delivering robust generalization across diverse and previously unseen workloads. In particular, CloudFormer achieves a mean absolute error (MAE) of only 7.8%, which represents a significant improvement in predictive accuracy over existing methods by at least 28%. 

- We provide an in-depth evaluation and ablation study that analyzes the contribution of each architectural branch, offering insights into the roles of temporal and system-level modeling. This not only validates design choices, but also demonstrates CloudFormer’s adaptability to varying workload patterns. 

The remainder of this paper is structured as follows. Section II reviews related work in the area of performance prediction. Section III formally defines the problem and introduces the key challenges addressed in this work. Section IV describes the dataset used in this study, including the collection methodology and the composition of the scenarios. Section V introduces CloudFormer, our proposed deep learning-based methodology to model performance degradation. Section VI presents the experimental setup along with a detailed analysis of the results. Finally, Section VII concludes the paper with a summary of the findings and potential directions for future work. 

> 1This dataset is publicly available at https://huggingface.co/datasets/Amir Shahbaz/CloudPerfTrace 

## II. RELATED WORKS 

## _A. VM Performance Challenges and Mitigation_ 

Virtual machines (VMs) are widely used in modern cloud environments to provide isolation and flexible resource management among co-located tenants. Traditionally, VM management strategies have focused on workload-based resource provisioning, relying on predicted load levels to optimize utilization and cost. However, managing VMs solely on the basis of workload does not account for performance degradation caused by resource interference among multiple VMs sharing the same physical host. To address such degradation, prior works explored runtime performance-level management through heuristic prediction or sandbox-based cloning approaches [11, 20], comparing the performance of a virtual machine with that of a clone running in a controlled environment. Although this approach can detect degradation, it incurs significant computational overhead and is impractical at scale. To reduce these costs, Wang et al. [21] proposed an analytical model to predict interference among co-running Apache Spark tasks, but it is limited to Spark and lacks generality. Similarly, ML-based runtime prediction methods, such as those in [22], focus on latency-sensitive Spark applications, restricting their applicability to broader cloud workloads. 

Other approaches, including collaborative filtering [9], attempt to preemptively schedule applications to minimize interference. However, these methods operate only during deployment and cannot adapt to runtime dynamics, thus failing to address performance variations after initial placement. Source code-dependent approaches such as Aspen [23], Palm [24], PEMOGEN [25], and COMPASS [26] achieve high accuracy but require internal application knowledge and runtime states. This reliance on detailed instrumentation makes them unsuitable for black-box public cloud scenarios. To overcome some of these limitations, Pham et al. [27] introduced a twostage ML-based prediction method using runtime metadata; however, it only predicts execution time and does not address interference effects. 

More recent methods have shifted toward explicit performance degradation analysis, but typically use classification rather than quantitative prediction. For example, ISOLATE [28] formulates performance monitoring as an anomaly detection task, identifying metric correlation violations to signal QoS issues. Horchulhack [29] classifies whether a VM is experiencing interference or operating normally. Although these methods can detect when degradation occurs, they do not forecast future performance metrics or quantify degradation levels, limiting their utility for proactive mitigation and finegrained resource planning. 

_B. Performance Prediction Methods_ 

Performance prediction in cloud computing has evolved significantly, employing diverse strategies ranging from statistical analyses and regression techniques to advanced neural network models. Despite considerable progress, existing methods exhibit certain limitations that impede their generalizability and practical applicability. 

Table I provides a detailed comparison of prominent methods based on critical criteria, including A) the capability to handle interference between multiple applications, B) scenario variety (e.g., CPU-intensive, network-intensive, etc.), C) explicit prediction of performance degradation, D) modeling of temporal behavior, E) number of metrics utilized, F) applicability to black-box scenarios, and G) handling of unknown applications. 

TABLE I 

COMPARISON OF DIFFERENT METHODS ACROSS METRICS A–G. 

|**Method**|**A**|**B**|**C**|**D**|**E**|**F**|**G**|
|---|---|---|---|---|---|---|---|
|Cloud White [14]|✗|✗|✓|✗|10|✓|✗|
|Seq2Seq [15]|✗|✓|✓|✓|9|✓|✗|
|Rusty [16]|✓|✓|✗|✓|3|✓|✓|
|Seer [10]|✓|✓|✗|✓|1|✗|✗|
|Monitorless [30]|✓|✓|✗|✗|117|✓|✓|
|CloudProphet [19]|✓|✓|✓|✗|53|✓|✗|
|**Ours**|✓|✓|✓|✓|**206**|✓|✓|



_Cloud White_ [14] leverages multivariate regression to predict latency degradation among latency-critical workloads. However, it is limited by its scenario specificity and the lack of explicit temporal modeling. The Seq2Seq model proposed by Buchaca et al. [15], despite effectively capturing temporal behavior, focuses primarily on pairwise scenarios, restricting scalability to larger-scale multi-tenant environments. Although it does not explicitly output a single performance degradation metric, its proposed percentage completion (PC) feature can be adapted to serve as an indirect measure of slowdown or performance degradation in co-scheduled settings. 

_Rusty_ [16] employs long-short-term memory (LSTM) networks for fine-grained predictions but does not directly model QoS degradation explicitly. Similarly, _Seer_ [10] relies on detailed application instrumentation, limiting its practicality in typical black-box scenarios from public clouds. _Monitorless_ [30] overcomes this limitation by relying solely on platform metrics to detect saturation; however, it is limited to binary classification, lacking the ability to quantify the magnitude of performance degradation. 

_CloudProphet_ [19] significantly advances performance prediction through neural networks and a degradation index but fails to model explicit temporal behaviors and still requires prior knowledge of the type of application. 

Collectively, these methods exhibit shortcomings in addressing generalizability across diverse scenarios, dynamic workload handling, and the black-box nature typical in real-world cloud environments. Most approaches rely heavily on predefined scenarios (e.g., CPU, memory, network-intensive workloads), using only scenario-specific metrics. Consequently, they fail to generalize across mixed and dynamically evolving workload scenarios, hindering their practical deployment. 



Fig. 1. General overview of the performance degradation prediction problem in multi-tenant cloud environments. Multiple VMs compete for shared resources, causing interference and variable execution times. Due to the blackbox nature of public clouds, only system-level traces observable from the host can be used for modeling and prediction. 

## _C. Performance Monitoring and Prediction Datasets_ 

Several publicly available datasets have significantly contributed to performance monitoring and prediction research in cloud computing environments. Google’s Borg cluster traces [17, 31], Alibaba’s cluster dataset [18], and Microsoft’s Azure Resource Central [6] provide insights into resource usage at scale, covering thousands of nodes running various realistic workloads. However, these datasets typically offer limited granularity, ranging from minutes to hours, and focus exclusively on resource metrics such as CPU and memory usage, often lacking explicit performance indicators like throughput or latency. Moreover, workload specifics are usually abstracted, with no direct correlation between resource usage and application-level performance. The CloudProphet dataset [19] partially addresses these limitations by capturing applicationlevel performance for five CloudSuite benchmarks [32], yet it remains restricted to approximately 250-hour experiments with fewer resource metrics. 

In summary, existing works on VM performance management and prediction either focus on limited scenarios, rely on extensive instrumentation, or lack explicit temporal modeling and generalizability. Additionally, publicly available datasets often fall short in capturing fine-grained, diverse metrics necessary to train and evaluate robust models under realistic cloud dynamics. These methodological and data-related gaps highlight the urgent need for comprehensive, flexible, and generalizable approaches to the prediction of performance degradation. Addressing this need, our work introduces a novel dual-branch Transformer-based architecture capable of modeling both temporal and system-level interactions without relying on source code or scenario-specific tuning. Complemented by a rich, fine-grained dataset, our approach bridges critical gaps in existing research and provides a foundation for more reliable and adaptive cloud performance prediction. 

## III. PROBLEM DEFINITION 

Figure 1 illustrates the general formulation of the performance prediction problem in multi-tenant cloud environments. In such environments, multiple virtual machines (VMs) are consolidated on the same physical server to maximize resource utilization. While virtualization technologies guarantee allocation of dedicated resources (e.g., vCPUs, memory quotas, 

storage partitions), they cannot ensure complete performance isolation. VMs inevitably compete for shared resources such as last-level cache (LLC), memory bandwidth, I/O subsystems, and network interfaces. This competition, referred to as performance interference, can lead to significant variability in execution times and throughput, even for identical applications running under nominally similar configurations. 

The challenge is compounded by the black-box nature of public cloud environments. Cloud providers typically have no access to the source code or internal state of user applications due to privacy constraints. Therefore performance prediction must rely solely on system-level signals that are observable from outside the VM. These traces are inherently indirect and noisy, requiring robust modeling to accurately infer the performance impact of workload variations and resource contention. 

In this study, our objective is to predict the performance of applications in cloud computing environments based on observed system-level metrics, where each application is executed alone within its own virtual machine. Each execution, whether the VM runs alone or in conjunction with other VMs, produces a data matrix _xi ∈_ R<sup>_S×Ti_</sup> , where _S_ is the number of system features and _Ti_ is the number of time steps corresponding to its duration. Although all executions share the same number of features _S_ , the duration _Ti_ may vary depending on the specific application and workload dynamics. <mark>Because performance degradation</mark> is <mark>non-</mark> li <mark>near and may</mark> o <mark>ccur</mark> at <mark>any point during</mark> exec <mark>ution, the model</mark> is d <mark>esigned</mark> to <mark>map the</mark> c <mark>umulative system-level</mark> intera <mark>ctions within</mark> _Ti_ to a <mark>scalar performance</mark> i <mark>ndex</mark> P. The performance _P_ for each execution is typically quantified as the ratio of the ideal Performance Metric _PM_ ideal to the actual observed Performance Metric _PM_ actual. To e <mark>nsure</mark> a <mark>fair baseline for</mark> d <mark>ynamic scenarios,</mark> _PM_ ideal is o <mark>btained</mark> by r <mark>eplaying the identical workload</mark> re- <mark>quest-rate trace</mark> in an <mark>isolated</mark> env <mark>ironment (i.e., the VM running alone</mark> on <mark>the physical host), thus capturing the</mark> applic <mark>ation’s peak performance</mark> u <mark>nder that specif</mark> i <mark>c workload pattern without</mark> exte <mark>rnal</mark> inte <mark>rference.</mark> Formally, this metric is defined as: 



where 0 _< P ≤_ 1. A value of _P_ = 1 corresponds to no degradation, while values approaching zero indicate significant performance degradation. The definition of the performance metric may differ depending on the characteristics of the application or its execution context. These alternative formulations will be discussed in detail in Section IV. 

Building on this problem formulation, we propose a novel scheme to predict performance degradation under these constraints. Our approach combines fine-grained system-level observations with advanced learning mechanisms to disentangle the effects of workload dynamics and interference. To support this, we introduce CloudPerfTrace (Section IV), a comprehensive dataset that captures system traces across diverse static and dynamic scenarios, and CloudFormer (Section V), a dual-branch Transformer architecture designed to jointly 

model temporal and system-level dependencies for accurate performance prediction. 

## IV. CLOUDPERFTRACE<sup>1</sup> : A COMPREHENSIVE DATASET FOR PERFORMANCE ANALYSIS 

As discussed in Section II, there is currently no comprehensive dataset that fully captures performance degradation in various scenarios. Our study presents a uniquely detailed dataset collected over two months from a test server, explicitly designed to explore diverse behaviors through systematically varied workloads. Unlike other datasets, we capture systemlevel metrics at an unprecedented granularity of one-second intervals, enabling high-resolution analysis of transient system behaviors. Our dataset includes 206 different resource metrics gathered from Linux perf, hypervisor statistics, and Intel’s top-down analysis [33], significantly surpassing the feature richness of datasets such as CloudProphet (which covers fewer metrics in only five cloud applications). We also expand the workload coverage to 11 different cloud applications (which will be introduced later in Table III), offering broader behavioral insights compared to previous work. This detailed, feature-rich, and temporally extensive dataset is particularly suited to fine-grained, machine learning-driven performance modeling, going beyond traditional utilization forecasting toward precise prediction of application-level performance dynamics. Following the similar setup described in [19], we run multiple virtual machines concurrently to emulate realistic cloud environments. The following subsection details the experimental setup and application scenarios. 

## _A. Testbed Server Setup_ 

The experiments in this study are conducted on a test server equipped with two Intel Xeon Gold 6240 processors. Each processor has 36 virtual CPUs (vCPUs) and operates at a base frequency of 2.6 GHz. The server also features 384 GB of ECC memory and a 6 TB NVMe solid-state drive. 

For the software setup, the server runs Ubuntu 20.04. Virtualization is managed using a combination of libvirt [34], QEMU [35], OpenvSwitch [36], and KVM [37]. Each VM has allocated 4 vCPUs and 8 GB of memory, allowing each CPU socket to host up to 9 VMs concurrently. Therefore, any VM can experience random performance interference from the other 8 VMs located in the same CPU socket. 

To simulate realistic scenarios in which server VMs receive requests from clients, the second CPU socket is dedicated to running 9 client VMs. The client and server VMs are interconnected via Open vSwitch. This setup ensures that server VMs are isolated from client-side interference while still allowing for performance interference among the server VMs themselves. 

## _B. Profiling Features_ 

In this work, we adopt the black-box scenario assumption, where cloud providers have no visibility into the applications running inside VMs due to privacy constraints. Consequently, we can only rely on basic hardware usage information that 



Fig. 2. For applications with dynamic workloads, four distinct scenarios are and (d) random workload. 

considered: (a) static workload, (b) monotonic workload, (c) periodic workload, 

TABLE II 

REPRESENTATIVE LIST OF TYPICAL COLLECTED HARDWARE METRICS AND THE NUMBER OF FEATURES PER CATEGORY 

|**Category**|**Count**|**Typical extracted metrics**|
|---|---|---|
|VM metrics|53|CPU utilization level (%)<br>Unused Memory (KB)|
|||Cycles (#)|
|Linux Perf|38|LLC misses (#)<br>Retired instructions (#)|
|Top-Down Analysis|12|Frontend bound (%)<br>Backend bound (%)|



can be accessed from the host server (hypervisor) without breaching the VM’s internal state. 

For example, 53 VM-level metrics such as CPU utilization and memory usage are collected using the libvirt API. 38 lowlevel hardware metrics, including retired instructions and lastlevel cache (LLC) misses, are gathered via the Linux perf tool. Additionally, we employ Intel’s Top-Down Analysis Method to identify the additional 12 performance bottleneck metrics. 

Utilizing these hardware metrics does not violate the blackbox assumption as all the profiling is done from outside the VM, i.e., on the host server. Key representatives of these metrics are listed in Table II. 

The raw dataset provides performance metrics for each application at different timestamps on various virtual machines (VMs). This yields a total of 103 base features for the primary VM. Recognizing the importance of inter-VM interactions, we also compute the average of these 103 metrics across all concurrent neighborhood VMs. This aggregation doubles the feature space, resulting in a comprehensive set of 206 distinct system metrics (103 from the primary VM + 103 from the aggregated neighbors). 

## _C. Application Scenarios_ 

To comprehensively cover various cloud application scenarios, this work selects 11 representative cloud benchmarks, as listed in Table III. In addition, cloud applications are inherently subject to varying workload levels, depending on incoming client requests. To capture this behavior, five of the applications (marked with an asterisk in Table III) are configured with dynamic workload scenarios. 

Figure 2 illustrates the workload configuration settings. As shown in Figure 2(a), the static workload scenario represents the simplest case, where the application does not experience a variation in workload over time for different workload levels. Figures 2(b)–(d) depict the dynamic workload scenarios: Figure 2(b) presents the monotonic workload scenario, in which the workload either increases (blue line) or decreases (orange line) over time. For more complex behavior, Figure 2(c) depicts the periodic workload scenario, where the workload fluctuates in a regular repeating pattern in which three different frequencies of workload variation are considered. Finally, we include a random workload scenario to emulate unpredictable user request patterns that cloud applications may encounter in real-world settings (Figure 2(d)). 

## _D. Data_ 

Table III summarizes the collected traces for all 11 applications, detailing the total number of runs, the proportion of static workload configurations, the cumulative recording duration, and the observed performance degradation range (Min. % and Max. %) for each application. Trace counts vary by application, reflecting differences in execution duration and scenario configurations. The percentages of static workload highlight that some applications (Graph Analytics, Data Analytics, MLPerf, HBase, TPCC, Flink) were exclusively evaluated under static conditions, while others (Data Serving, Redis, Web Search, Alluxio, Minio) were extensively tested with both static and dynamic scenarios (monotonic, 

TABLE III 

OVERVIEW OF APPLICATION SCENARIOS, PURPOSES, PERFORMANCE METRICS, TOTAL COUNTS, PERCENTAGE OF STATIC WORKLOAD SCENARIOS, AND 

DURATION IN DAYS. 

|**Application**|**Purpose**|**Performance Metric**|**Count**|**Static %**|**Duration**|**Min. %**|**Max. %**|
|---|---|---|---|---|---|---|---|
|Data Serving*|Stress the data store and serving server|Operations/s|4209|65|16.43|67.16|100|
|Redis*|Evaluate in-memory data structure server|Requests/s|4862|51|18.57|6.03|98.88|
|Web Search*|Simulate a search engine handling queries|Operations/s|2849|76|11.66|26.49|99.98|
|Graph Analytics|Analyze large-scale graph computations|Execution time|3195|100|49.69|85.76|98.37|
|Data Analytics|Evaluate batch processing of large-scale datasets|Execution time|3085|100|118.95|87.63|97.47|
|MLPerf|Benchmark machine learning models|Requests/s|3355|100|27.11|84.02|96.92|
|Hbase|Assess a distributed NoSQL database|Latency (s)|4759|100|6.93|57.95|98.08|
|Alluxio*|Evaluate memory-centric distributed storage system|Throughput|3085|83|7.04|57.88|92.61|
|Minio*|Evaluate lightweight object storage performance|Throughput|3139|82|7.09|10.65|99.46|
|TPCC|Simulate a transaction processing systems|Latency (ms)|2985|100|27.03|28.4|99.98|
|Flink|Benchmark real-time stream performance|Operations/ms|3181|100|26.96|32.01|99.99|



periodic, and random). The duration column further indicates the total days of data recorded for each benchmark, with longrunning experiments such as Data Analytics (118.95 days) and Graph Analytics (49.69 days) providing substantial coverage for steady-state and transient performance behaviors. The minimum and maximum performance percentages highlight the variability in degradation observed across runs, with some interactive applications like Redis and Minio experiencing severe degradation (down to _∼_ 6-10%), while other workloads like Data Analytics remained relatively stable. 

In total, the dataset spans approximately 317 days of recorded traces across all applications, representing a comprehensive view of VM performance under diverse workloads. This diverse set of traces, which span thousands of runs, provides a rich dataset that captures both short-term variability and long-term workload trends. The breadth of applications, workload types, and temporal coverage make it well-suited for developing and evaluating generalizable performance prediction models in realistic multi-tenant cloud environments. 

## V. CLOUDFORMER: A UNIFIED APPROACH TO BLACK-BOX VM PERFORMANCE PREDICTION 

Herein, we introduce CloudFormer, a novel deep learningbased architecture designed to predict performance degradation in multi-tenant cloud environments. Performance degradation in such environments arises from two fundamentally different types of dynamics: (i) _temporal dynamics_ , describing how workloads evolve over time (e.g., sudden CPU bursts or periodic I/O spikes), and (ii) _system-level interactions_ , representing relationships among system metrics (e.g., LastLevel Cache occupation influencing the Cache Miss). These dynamics are highly nonlinear and often interdependent, making them challenging to capture with a single unified model. 

To address this, CloudFormer employs a dual-branch Transformer structure that explicitly separates temporal and systemlevel modeling. Figure 3 illustrates the architecture. The input is processed in parallel through two branches: a _temporal branch_ (left), which models transient sequence dependencies using positional encoding and masked attention to accommodate variable-length executions; and a _system branch_ (right), which captures global cross-metric interactions by first ag- 



Fig. 3. Overview of CloudFormer architecture illustrating dual branches for temporal and system-level modeling. 

gregating the execution trace. This design explicitly separates the modeling of time-varying fluctuations from the holistic resource contention profile, allowing the system branch to efficiently learn metric dependencies without assuming any specific ordering. 

This separation is intentional: in multi-tenant environments, evolving workloads and resource contention impact performance in distinct but complementary ways. By allowing each branch to specialize while maintaining a shared transformerbased encoder design, the model can capture rich domainspecific patterns. The outputs from both branches are merged through the prediction head, using complementary representations from temporal and system perspectives to produce 

accurate performance degradation forecasts. The following subsections provide a detailed description of its structure. 

## _A. Input Representation_ 

The input data is represented as a matrix of shape _S × T_ , where _S_ denotes the number of system metrics (e.g., CPU, memory, network, LLC miss), which is fixed across samples, and _T_ denotes execution time steps, which can vary per sample. 

## _B. Temporal Branch_ 

In the temporal branch, each time step is first normalized and mapped from the high-dimensional feature space (S=206) to a compact embedding space _dt_ through a dense layer with ReLU activation. This learnable projection effectively distills the raw metrics into a concise latent representation, allowing the model to automatically extract salient features before temporal processing. A learnable class token is added to the sequence to capture a global temporal summary. To retain temporal order, sinusoidal positional encoding is added as follows: 



This results in a shape embedding ( _T_ +1) _×dt_ . The temporal branch then passes through _BT_ transformer encoder blocks, each containing Masked Multi-Head Self-Attention (MHA) (to handle variable-length sequences with padding masks), dropout, residual connections with layer normalization, and position-wise feedforward layers. In this branch, the learnable class token effectively ’attends’ to all time steps, aggregating relevant global temporal features into a single representation. 

## _C. System Branch_ 

For the system branch, the input is first averaged over the time dimension, effectively reducing temporal variability and summarizing each system feature. A 1D convolution then projects these pooled features into a system embedding space of dimension _ds_ . A learnable class token is prepended, resulting in an embedding of shape ( _S_ + 1) _× ds_ . No positional encoding is applied here, as system metrics are unordered by nature. The system branch then passes through _BS_ Transformer encoder blocks, each comprising standard MHA (without masking), dropout, residual connections with layer normalization, and position-wise feed-forward layers. Here too, the learnable class token acts as a global summary vector, capturing interactions among system metrics. 

## _D. Attention Mechanism_ 

In both the temporal and system branches, the core operation for modeling dependencies is the self-attention mechanism [38], which enables each token to attend to every other token in the same branch. This mechanism computes a weighted sum of value vectors _V_ , where the weights are 

determined by the similarity between query vectors _Q_ and key vectors _K_ . Formally, the attention operation is defined as: 



where _Q_ , _K_ , _V_ are learned linear projections of input embeddings, and _d_ is the dimensionality of each attention head. 

The multi-head design further enhances representational power by learning multiple independent attention patterns in parallel, each focusing on different aspects of the data. The outputs are concatenated and passed through a feedforward projection, allowing the model to combine fine-grained relational cues with global contextual information. In both branches, the presence of a learnable class token ensures that the most salient information is aggregated into a single vector representation which will later be fused in the prediction head. 

## _E. Fusion and Prediction Head_ 

After the final encoder blocks, the representations corresponding to the class tokens of both branches are concatenated, forming a comprehensive joint embedding. This fused representation is passed through a multi-layer perceptron consisting of dense layers, normalization, dropout, and a final dense layer. In the end, a sigmoid activation is applied to produce a continuous scalar prediction of performance degradation, constrained between 0 and 1. The use of learnable class tokens ensures that each branch provides a highly expressive and global informed summary, enabling more accurate final predictions. 

Overall, by combining temporal and system-level perspectives, CloudFormer is able to extract rich, complementary information, leading to superior prediction accuracy compared to single-branch models. 

## VI. EXPERIMENTS 

## _A. Experimental Setup_ 

We evaluated the model’s generalization capabilities by partitioning the 11 applications (see Section IV) into seven training applications (four static, three dynamic) and four entirely unseen testing applications (two static, two dynamic). This balanced split ensures the model captures diverse system behaviors during training while being assessed under realistic, complex conditions. To mitigate selection bias, we repeated this randomized partitioning process six times and report the aggregate results. 

## _B. Implementation_ 

As discussed in Section V, CloudFormer explicitly separates temporal and system-level modeling. In the temporal branch, the input is projected in a dimension space _dt_ = 64, followed by the addition of a class token and positional encoding. A sequence of _BT_ = 4 transformer encoder blocks with masked Multi-Head Attention (MHA) handles variable-length time sequences. The system branch first applies mean pooling over time and projects them to a dimension _ds_ = 64 through a 1D convolution. This branch also prepends a class token 

but does not use positional encoding since the system metrics are unordered. The system features are then processed by _BS_ = 4 transformer encoder blocks with standard (unmasked) MHA. Finally, the class token outputs from both branches are concatenated and passed through an MLP head with Swish activation, layer normalization, and dropout (rate 0.4), producing a scalar output via a sigmoid activation. The Multi-Head Attention (MHA) modules were configured with a head size of 16 and four attention heads, while the feedforward network within each Transformer block was set to a dimension of 256, providing a good trade-off between model expressiveness and computational efficiency. Specifically, the resulting model is exceptionally lightweight, containing a total of _∼_ 228 _k_ trainable parameters. Of these, the temporal branch accounts for _∼_ 222 _k_ parameters, while the system branch is extremely compact with only _∼_ 6 _k_ parameters. 

For training, the data was first normalized. The model was then trained using the Adam optimizer with a low initial learning rate of 1e _−_ 5 to ensure stable convergence. A logarithmic cosh loss function was employed to handle potential outliers smoothly. <mark>The log-cosh loss was chosen over standard Mean</mark> _<u>x</u>_<sup>2</sup> <mark>Squared</mark> E <mark>rror (MSE)</mark> b <mark>ecause</mark> it is a <mark>pproximately equal</mark> to 2 <mark>for small</mark> e <mark>rrors and</mark> _<mark>|x| −</mark>_ <mark>log(2) for large</mark> e <mark>rrors, providing</mark> a r <mark>obust and twice-differentiable</mark> altern <mark>ative that</mark> is <mark>less sensitive</mark> to <mark>noise.</mark> To further improve generalization and efficiency, a learning rate scheduler combining linear warm-up and cosine decay was applied. 

## _C. Baseline Methods_ 

For benchmarking our proposed model, we considered five widely used regression methods: Decision Trees (DT) [39], Random Forests (RF) [27, 30], Linear Regression (LR), Gamma Regression with an Inverse Power Link function (GLR) [14], and long-short-term memory networks (LSTM) [16]. Decision Trees build prediction models by recursively partitioning the feature space to minimize prediction errors, resulting in straightforward predictive structures. Random forests extend this concept by creating an ensemble of decision trees trained on random subsets of features and data, enhancing prediction robustness and reducing variance. 

Both Decision Trees and Random Forests underwent hyperparameter optimization using Bayesian search combined with cross-validation. Specifically, for Decision Trees, we optimized hyperparameters including maximum depth, minimum samples required at each leaf, minimum samples required for splitting, and feature selection criteria. For Random Forests, we optimized parameters such as the number of estimators (trees), minimum samples per leaf, and feature selection methods. Hyperparameter optimization ensures these baselines represent competitive and reliable benchmarks against which we can effectively compare our model’s performance. 

Additionally, we included Linear Regression as a simpler baseline method, which fits a linear relationship between the input features and the target variable. This method provides a fundamental performance reference point that assesses the predictive complexity of the dataset. 

TABLE IV 

PERFORMANCE COMPARISON OF METHODS (MEAN _±_ STD) 

|**Method**|**MSE**|**MAE**|
|---|---|---|
|LR|5465_._67_±_4047_._98<br>|49_._09_±_12_._45|
|GLR [14]|1_._05_×_10<sup>10</sup> _±_2_._58_×_10<sup>10</sup>|477_._12_±_1008_._71|
|DT [39]|419_._67_±_183_._68|15_._03_±_3_._96|
|RF [27, 30]|205_._67_±_94_._82|10_._78_±_3_._29|
|LSTM [16]|427_._67_±_228_._93|15_._42_±_4_._17|
|CF|142_._67_±_49_._71|7_._80_±_1_._55|



The Gamma Regression (GLR) baseline, implemented with an inverse power link function using a Generalized Linear Model, was also employed. GLR is particularly suitable for modeling strictly positive, continuous outcomes that exhibit skewness, making it a relevant baseline for comparison against more complex nonlinear models. 

Lastly, we incorporated long-short-term memory networks (LSTM) to evaluate performance from a time-domain perspective. Unlike other baselines, LSTM models explicitly capture sequential dependencies, which makes them particularly effective for modeling temporal dynamics in the data. For evaluation, we thus considered both feature domain solutions (Decision Trees, Random Forests, Linear Regression, Gamma Regression) and a time-domain solution (LSTM), providing a comprehensive benchmarking framework for assessing our proposed model’s effectiveness. 

Finally, we note that while prominent works such as Seer [10], Seq2Seq [15], and CloudProphet [19] were discussed in Section II, they are excluded from this quantitative benchmark due to fundamental differences in problem formulation. Seer and Monitorless formulate performance monitoring as a classification task (predicting the probability of QoS violations and resource saturation, respectively) rather than a regression of degradation. Similarly, Seq2Seq focuses on forecasting multivariate resource usage traces (e.g., generating future CPU and memory time-series) rather than predicting a unified scalar performance index. Lastly, CloudProphet relies on application-specific profiles from a known set of benchmarks, making it unsuitable for our evaluation setting, where the model must generalize to entirely unknown applications. 

## _D. Results_ 

The performance results, summarized in Table IV, clearly demonstrate the effectiveness of the CloudFormer (CF) compared to baseline methods. CF achieved the lowest mean squared error (MSE) of 142 _._ 67 _±_ 49 _._ 71 and the lowest mean absolute error (MAE) of 7 _._ 80 _±_ 1 _._ 55, significantly outperforming all baseline methods by at least 28%. Among the baseline models, Random Forests (RF) exhibited the next best performance, with an MSE of 205 _._ 67 _±_ 94 _._ 82 and MAE of 10 _._ 78 _±_ 3 _._ 29. 

In contrast, linear methods such as LR and GLR performed notably worse, underscoring the complexity and nonlinearity of the dataset. The time-domain method, LSTM, achieved moderate performance with an MSE of 427 _._ 67 _±_ 228 _._ 93 and an 

TABLE V 

COMPARING PERFORMANCE OF INDIVIDUAL BRANCHES AND THE FULL CF MODEL (MEAN _±_ STD) 

|**Method**|**MSE**|**MAE**|
|---|---|---|
|CF-Temporal|156_._33_±_70_._24|8_._47_±_1_._89|
|CF-System|171_._33_±_57_._73|8_._65_±_1_._55|
|CF|142_._67_±_49_._71|7_._80_±_1_._55|



MAE of 15 _._ 42 _±_ 4 _._ 17, emphasizing the importance of capturing information in both the temporal and feature domains. In general, the superior performance of CF indicates that effective modeling of both temporal and system dynamics provides substantial benefits for accurate prediction of performance. 



Fig. 4. Stacked bar plot illustrating the distribution of prediction errors across different models, showing the percentage of samples falling within specific error segments. 

To provide a more interpretable view of the prediction error distributions, Figure 4 illustrates the percentage of predictions that fall within specific error bands (i.e., _<_ 5%, _<_ 10%, _<_ 15%, _<_ 20%, _<_ 25%, and _>_ 25%). This plot reveals a clear trend: CF exhibits the highest concentration of accurate predictions in the lower error bands, particularly below 5% and 10%, and the smallest proportion of large errors above 25%. In contrast, linear models such as LR and GLR suffer from a large proportion of high-error predictions, while DT, RF, and LSTM show intermediate behavior. These results reinforce that CF’s dual-domain attention design leads to both higher accuracy and more consistent prediction reliability across scenarios. 

## _E. Ablation Study_ 

_1) Impact of Temporal and System Branches:_ To better understand the contribution of each domain-specific attention mechanism, we conducted an ablation study by independently evaluating the temporal and system branches of CloudFormer. Specifically, we constructed two variants of the model: CFTemporal, including only the temporal self-attention branch, and CF-System, which includes only the system self-attention branch. The results of this study are presented in Table V. 

The results highlight the distinct and complementary roles of each branch. Notably, the CF-System branch achieves an MAE of 8 _._ 65 _±_ 1 _._ 55, outperforming the Random Forest baseline (10 _._ 78 _±_ 3 _._ 29) despite containing only _∼_ 6 _k_ parameters. This demonstrates that the branch’s dense embedding strategy effectively distills the 206 metrics into a concise global profile. While the CF-Temporal branch achieves a slightly lower MAE of 8 _._ 47 _±_ 1 _._ 89, it requires the majority of the model’s capacity ( _∼_ 222 _k_ parameters) to capture transient dynamics. Ultimately, the full CF model fuses these representations to achieve the best overall performance, confirming that integrating the efficient, global system-level context with finegrained temporal dynamics enables the model to extract richer representations than either branch could achieve in isolation. 

_2) Per-Application Error Analysis:_ To better understand the robustness of the model and generalization at the application level, we conducted a detailed per-application error analysis on all seeds tested. Figure 5 illustrates the mean absolute error (MAE) performance of different models across six random seeds, evaluated on four applications per seed. In each heatmap, the rows correspond to the baseline methods and CloudFormer (CF), while the columns represent the four test applications (two static-only and two with dynamic scenarios). The color intensity encodes the MAE value for each methodapplication pair, where lighter colors indicate lower errors (better performance) and darker shades indicate higher errors. For better visual contrast, the color bar is capped at 20% MAE. 

As seen consistently in the last row of each subfigure, CloudFormer (CF) outperforms all other methods on average across all seeds and application scenarios. Although there are isolated instances where certain baseline methods achieve slightly lower MAE on specific applications, e.g., in Seed 2 on Static 1, where three methods show marginally better performance, these gains are not consistent across other applications and come at the cost of significantly higher errors elsewhere. This indicates that while some methods may overfit simpler static applications, they fail to generalize effectively to dynamic or more complex scenarios, resulting in poorer overall performance for that seed. 

Furthermore, the heatmaps suggest that static scenarios are generally easier for models to predict, as evidenced by the lower error values compared to dynamic scenarios. This aligns with expectations: static applications involve more stable and predictable behavior, requiring the model to learn fewer complex relationships. However, dynamic scenarios introduce additional variability and resource interference, making prediction inherently more challenging. In particular, there are a few exceptions where certain static applications exhibit higher errors, for instance, in Seed 0 Static 2, Seed 2 Static 2, and Seeds 5 Static 1 and Static 2. These higher errors in static scenarios can be attributed to specific applications such as TPCC and Flink, which display more distinctive or irregular behavior compared to other static workloads. Overall, CF’s robust and consistent performance across both static and dynamic cases highlights its superior generalization capability and adaptability to complex cloud environments. 



Fig. 5. Heatmaps showing the mean absolute error (MAE _±_ STD) of different models across six random seeds and four test applications (two static-only and two dynamic scenarios). For better visual contrast, the color bar is capped at 20% MAE. 

## VII. CONCLUSIONS 

Ensuring reliable performance in multi-tenant cloud environments remains a critical challenge due to the dynamic nature of workloads and the complex resource contention among co-located virtual machines. Performance degradation not only undermines the quality of service guarantees, but also limits the efficiency of resource management strategies. Accurate prediction of degradation is therefore essential for proactive mitigation and optimized cloud operations. 

In this work, we have introduced CloudFormer, a dualbranch Transformer-based architecture explicitly designed to address these challenges. CloudFormer separates temporal and system-level modeling to better capture the distinct sources of performance variability. The temporal branch focuses on workload evolution over time, while the system branch models cross-metric interactions that influence performance. These complementary representations are fused to provide a unified prediction of VM performance degradation. 

Our approach is supported by a rich dataset comprising 206 system metrics, collected at one-second resolution, across both static and dynamic workload scenarios. This dataset provides a high-fidelity view of both transient and long-term behaviors in realistic cloud environments. The experimental evaluation has shown that CloudFormer consistently outperforms stateof-the-art baselines across multiple metrics, achieving robust generalization across diverse workloads. In particular, the model has a mean absolute error of just 7.8%, which highlights its predictive accuracy and reliability. 

Looking ahead, future work could explore extending Cloud- 

Former to multi-node settings, integrating online adaptation for changing workload patterns, and incorporating energyefficiency objectives alongside performance prediction. These directions hold promise in enabling more intelligent, resourceaware cloud platforms capable of providing stronger performance guarantees at scale. 

## ACKNOWLEDGMENTS 

<mark>This work was supported i</mark> n <mark>part</mark> b <mark>y the HeatingBits S4S project</mark> of <mark>EPFL, Grants PID2021126576NB-I00, PID2024-158311NB-I00 funded b</mark> y <mark>MCIN/AEI/10.13039/501100011033 and FEDER, EU.</mark> 

## REFERENCES 

- [1] Gartner. _Gartner Forecasts Worldwide Public Cloud End-User Spending to Total $723 Billion in 2025_ . Nov. 2024. 

- [2] D. Mytton. _Data center energy and AI in 2025. In: Dev Sustainability._ Feb. 2022. 

- [3] IEA. _AI is set to drive surging electricity demand from data centres while offering the potential to transform how the energy sector works_ . Apr. 2025. 

- [4] G. Neiger et al. “Intel® Virtualization Technology”. In: _Intel Technology Journal_ 10.03 (June 2006). 

- [5] A. S. for HCI et al. _https://www.amd.com/en/solutions/hci-andvirtualization.html_ . 

- [6] E. Cortez et al. “Resource Central: Understanding and Predicting Workloads for Improved Resource Management in Large Cloud Platforms”. In: _26th Symposium on Operating Systems Principles_ . Shanghai China, Oct. 2017. 

- [7] S.-G. Kim et al. “Virtual machine consolidation based on interference modeling”. In: _J. Supercomput._ 66.3 (Dec. 2013). 

- [8] T. Wood et al. “Sandpiper: Black-box and gray-box resource management for virtual machines”. In: _Computer Networks_ . Virtualized Data Centers (Dec. 2009). 

- [9] C. Delimitrou et al. “Paragon: QoS-aware scheduling for heterogeneous datacenters”. In: ASPLOS ’13. Mar. 2013. 

- [10] Y. Gan et al. “Seer: Leveraging Big Data to Navigate the Complexity of Performance Debugging in Cloud Microservices”. In: ASPLOS ’19. Apr. 2019. 

- [11] D. Novakovi´c et al. “DeepDive: Transparently Identifying and Managing Performance Interference in Virtualized Environments”. In: _USENIX_ . 2013. 

- [12] A. H. Anwar et al. “A Game-Theoretic Framework for the Virtual Machines Migration Timing Problem”. In: _IEEE TCC_ 9.3 (July 2021). 

   - [33] A. Yasin. “A Top-Down method for performance analysis and counters architecture”. In: _ISPASS_ . Mar. 2014. 

   - [34] Libvirt. _libvirt: The virtualization API_ . 

   - [35] QEMU. _https://www.qemu.org/_ . 

   - [36] OpenVSwitch. _https://www.openvswitch.org/_ . 

   - [37] KVM. _https://linux-kvm.org/_ . 

   - [38] A. Vaswani et al. “Attention is All you Need”. In: _NeurIPS_ . 2017. 

   - [39] R. Cao et al. “Load Prediction for Data Centers Based on Database Service”. In: _COMPSAC_ . Vol. 01. July 2018. 

- [13] S. Akbar et al. “A Game-based Thermal-Aware Resource Allocation Strategy for Data Centers”. In: _IEEE Transactions on Cloud Computing_ 9.3 (July 2021). 

- [14] L. Pons et al. “Cloud White: Detecting and Estimating QoS Degradation of Latency-Critical Workloads in the Public Cloud”. In: _FGCS_ 138 (Jan. 2023). 

- [15] D. Buchaca et al. “Sequence-to-sequence models for workload interference prediction on batch processing datacenters”. In: _FGCS_ 110 (Sept. 2020). 

- [16] D. Masouros et al. “Rusty: Runtime Interference-Aware Predictive Monitoring for Modern Multi-Tenant Systems”. In: _IEEE TPDS_ 32.1 (Jan. 2021). 

- [17] J. Wilkes. _More Google cluster data_ . Google research blog. Nov. 2011. 

- [18] H. Tian et al. “Characterizing and Synthesizing Task Dependencies of Data-Parallel Jobs in Alibaba Cloud”. In: SoCC ’19. New York, NY, USA, Nov. 2019. 

- [19] D. Huang et al. “CloudProphet: A Machine Learning-Based Performance Prediction for Public Clouds”. In: _IEEE TSC_ 9.4 (July 2024). 

- [20] N. Vasi´c et al. “DejaVu: accelerating resource allocation in virtualized environments”. In: _ACM SIGARCH Computer Architecture News_ 40.1 (Mar. 2012). 

- [21] K. Wang et al. “Modeling Interference for Apache Spark Jobs”. In: _IEEE CLOUD_ . 2016. 

- [22] S. Shekhar et al. “Performance Interference-Aware Vertical Elasticity for Cloud-Hosted Latency-Sensitive Applications”. In: _IEEE CLOUD_ . July 2018. 

- [23] K. L. Spafford et al. “Aspen: A domain specific language for performance modeling”. In: _SC ’12_ . Nov. 2012. 

- [24] N. R. Tallent et al. “Palm: easing the burden of analytical performance modeling”. In: ICS ’14. June 2014. 

- [25] A. Bhattacharyya et al. “PEMOGEN: Automatic adaptive performance modeling during program runtime”. In: _PACT_ . Aug. 2014. 

- [26] S. Lee et al. “COMPASS: A Framework for Automated Performance Modeling and Prediction”. In: ICS ’15. June 2015. 

- [27] T.-P. Pham et al. “Predicting Workflow Task Execution Time in the Cloud Using A Two-Stage Machine Learning Approach”. In: _IEEE TCC_ 8.1 (Jan. 2020). 

- [28] W. Gu et al. “Identifying Performance Issues in Cloud Service Systems Based on Relational-Temporal Features”. In: _ACM TOSEM_ 34.3 (Feb. 2025). 

- [29] P. Horchulhack et al. “Detection of quality of service degradation on multi-tenant containerized services”. In: _JNCA_ 224 (Apr. 2024). 

- [30] J. Grohmann et al. “Monitorless: Predicting Performance Degradation in Cloud Applications with Machine Learning”. In: _20th Int. Middleware Conference_ . Middleware ’19. New York, NY, USA, Dec. 2019. 

- [31] J. Wilkes. _Google cluster-usage traces v3_ . Technical Report. Mountain View, CA, USA: Google Inc., 2020. 

- [32] T. Palit et al. “Demystifying cloud benchmarking”. In: _ISPASS_ . Apr. 2016. 

ARTIFACT APPENDIX FOR “CLOUDFORMER: AN ATTENTION-BASED PERFORMANCE PREDICTION FOR PUBLIC CLOUDS WITH UNKNOWN WORKLOAD” 

## _A. abstract_ 

This artifact provides the _CloudPerfTrace_ dataset, a collection of 206 system-level metrics captured at a one-second resolution over 317 days. Specifically designed for black-box multi-tenant cloud environments where internal VM telemetry is unavailable. The dataset enables precise prediction of performance degradation. It encompasses 11 diverse application tasks and captures the complex interplay between intrinsic workload variations and external resource interference. 

## _B. Artifact Summary_ 

- **Dataset Title:** CloudPerfTrace: A High-Resolution Dataset for VM Performance Prediction. 

- **Persistent Identifier:** https://doi.org/10.57967/hf/7847 

- **Repository:** https://huggingface.co/datasets/AmirShahba z/CloudPerfTrace 

- **License:** Creative Commons Attribution 4.0 International (CC-BY-4.0). 

- **Persistence Statement:** This artifact is permanently archived with a unique DOI to ensure guaranteed persistence and open access for research reproducibility. 

## _C. Schema and Features_ 

The dataset models system-level interactions by providing 206 metrics, split equally between the target VM and its concurrent neighbors. All features are collected from the hostlevel hypervisor to respect the black-box privacy constraints of public clouds. 

- **perf ori** : The target performance ratio (0 _< P ≤_ 1) representing observed vs. ideal performance. 

- **tr** **<u>self / tr oth</u>** : 53 VM-level metrics (e.g., CPU/Memory utilization) via libvirt. 

- **lin self / lin oth** : 38 hardware counters (e.g., LLC misses, cycles) via Linux perf. 

- **td** **<u>self</u> / td** **<u>oth</u>** : 12 Intel Top-Down analysis metrics. 

### TABLE VI 

TASK ID TO APPLICATION MAPPING 

|**ID**|**Application**|**ID**|**Application**|
|---|---|---|---|
|4|Data Serving|11|HBase|
|5|Redis|13|Alluxio|
|6|Web Search|14|Minio|
|7|Graph Analytics|15|TPC-C|
|9|Data Analytics|16|Flink|
|10|MLPerf|||



## _E. Accessibility and Usage_ 

The mapping below allows users to utilize predicate pushdown to filter specific benchmarks evaluated in the paper. 

_1) Environment Setup:_ Accessing the dataset requires pyarrow and huggingface_hub for high-performance columnar processing: 

pip install pyarrow huggingface_hub 

_2) Downloading and Loading the Dataset:_ The use of Hive-partitioning via PyArrow is recommended for performance: 

import pyarrow.dataset as ds 

from huggingface_hub import snapshot_download 

repo_path = snapshot_download( 

repo_id="AmirShahbaz/CloudPerfTrace", repo_type="dataset" 

) 

dataset = ds.dataset( 

f"{repo_path}/parquet_ds", format="parquet", partitioning="hive" 

) 

Data can also be loaded partially, such as the Web Search data (Task ID 6): 

#Ensure pandas is installed to use this command web_search_df = dataset.to_table( 

filter=ds.field("tasks") == 6 

).to_pandas() 

## _D. Dataset Context and Format_ 

To efficiently handle the large dataset collected over 317 days, we utilized the Apache Parquet format with Hive-style partitioning, which resulted in a compressed storage size of 18 GB. 

- **Partitioning Strategy:** Data is organized by tasks (Application ID), enabling the filtering and loading of specific workloads without full-memory residency. 

- **Temporal Resolution:** 1-second intervals, providing the granularity needed to analyze transient interference effects. 

- **Coverage:** 317 days of recording across 11 applications, including static, monotonic, periodic, and random workloads. 

