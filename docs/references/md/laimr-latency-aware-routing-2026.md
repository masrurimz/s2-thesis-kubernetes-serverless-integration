---
# --- bibliographic record ---
entry_type: misc
title: "LA-IMR: Latency-Aware, Predictive In-Memory Routing and Proactive Autoscaling for Tail-Latency-Sensitive Cloud Robotics"
authors:
  - "Eunil Seo"
  - "Chanh Nguyen"
  - "Erik Elmroth"
year: 2025
venue: "arXiv preprint"
volume: ""
issue: ""
pages: ""
publisher: ""
doi: ""
arxiv: "2505.07417"
url: "https://arxiv.org/abs/2505.07417"

# --- archive record ---
source_pdf: laimr-latency-aware-routing-2026.pdf
source_sha256: e1ce24df72e82699ee75d9096ac3c3e8db3753f05862835c93d62904d5099e96
pdf_pages: 12
converted: 2026-09-13
record_source: arxiv
key_insight: "Closed-form latency model, capacity-driven routing, proactive K8s scaling, 20.7% P99 reduction"
first_page: "LA-IMR: Latency-Aware, Predictive In-Memory Routing & Proactive Autoscaling for Tail-Latency-Sensitive Cloud Robotics Eunil Seo∗, Chanh Nguyen∗, Erik Elmroth∗ ∗Department of Computing Science, Ume˚a U"
---
# LA-IMR: Latency-Aware, Predictive In-Memory Routing & Proactive Autoscaling for Tail-Latency-Sensitive Cloud Robotics 

Eunil Seo<sup>_∗_</sup> , Chanh Nguyen<sup>_∗_</sup> , Erik Elmroth<sup>_∗_</sup> 

_∗_ Department of Computing Science, Ume˚a University, 90187 Ume˚a, Sweden Email: _{_ eunil.seo, chanh, elmroth _}_ @cs.umu.se 

**_Abstract_ —Hybrid cloud–edge infrastructures now support latency-critical workloads ranging from autonomous vehicles and surgical robotics to immersive AR/VR. However, they continue to experience crippling** **_long-tail_ latency spikes whenever bursty request streams exceed the capacity of heterogeneous edge and cloud tiers. To address these** **_long-tail_ latency issues, we present Latency-Aware, Predictive In-Memory Routing and Proactive Autoscaling (LA-IMR). This control layer integrates a closedform, utilization-driven latency model with event-driven scheduling, replica autoscaling, and edge-to-cloud offloading to mitigate 99th-percentile (P99) delays. Our analytic model decomposes endto-end latency into processing, network, and queuing components, expressing inference latency as an affine power-law function of instance utilization. Once calibrated, it produces two complementary functions that drive: (i) millisecond-scale routing decisions for traffic offloading, and (ii) capacity planning that jointly determines replica pool sizes. LA-IMR enacts these decisions through a quality-differentiated, multi-queue scheduler and a custom-metric Kubernetes autoscaler that scales replicas proactively—before queues build up—rather than reactively based on lagging CPU metrics. Across representative vision workloads (YOLOv5m and EfficientDet) and bursty arrival traces, LA-IMR reduces P99 latency by up to 20.7% compared to traditional latency-only autoscaling, laying a principled foundation for nextgeneration, tail-tolerant cloud–edge inference services.** 

**_Index Terms_ —hybrid cloud–edge computing, tail-latency mitigation, predictive autoscaling, in-memory routing, SLO-aware scheduling, edge offloading, latency modeling, microservice architecture, Kubernetes HPA, 99th-percentile (P99) latency.** 

## I. INTRODUCTION 

Mitigating long-tail latency in hybrid cloud–edge systems is increasingly critical as these environments scale in complexity [1], [2]. Workloads span a heterogeneous continuum—from high-accuracy, resource-intensive cloud models to lightweight, low-latency edge models—making it challenging to meet strict worst-case latency targets like P99 [3]. While average latency is well studied, rare yet severe spikes can deteriorate user trust and degrade performance [4], [5]. These long-tail anomalies are particularly harmful in mission-critical applications such as autonomous vehicles, industrial automation, and medical robotics [6], [7]. 

This work introduces an **SLO-aware, in-memory control loop** that sits inside a tiered microservice architecture. As illustrated in Fig. 1, inference is decomposed into lightweight edge models for low-latency requests and high-accuracy cloud 



Fig. 1. LA-IMR: an in-memory SLO-aware controller that routes requests across edge–cloud tiers. 

models for precision tasks. The controller steers each request to the corresponding tier that can enable its SLO—or pre-emptively off-loads it upstream when an early-warning spike is detected—thereby suppressing tail-latency anomalies. 

The LA-IMR router maintains all telemetry data—including the EWMA-smoothed arrival rate, queue depth, and utilization—in process memory, updating it with every request. At the first sign of a load spike, it either (1) scales replicas using Kubernetes HPA or (2) defers excess traffic to the cloud or a faster upstream tier, thereby mitigating P99 latency. Since no external cache (e.g., Redis [8]) is involved, these decisions incur only microseconds of access time, enabling millisecondlevel responses that are essential for handling bursty, latencycritical workloads in highly latency-sensitive scenarios [9], [10]. 

We introduce a closed-form, end-to-end latency model that predicts the response time of any inference request routed through an edge–cloud continuum. The model decomposes latency into three components: (i) an inference-processing term that scales with instance utilization according to an affine power law, (ii) a task-agnostic network round-trip time 

(RTT), and (iii) an analytically derived M/M/c queuing delay. Calibrated using only three parameters per hardware tier—the model’s reference latency _Lm_ , the hardware speed-up _Sm,i_ , and a super-linearity exponent _γ_ —the model effectively captures how latency increases under bursty loads, heterogeneous hardware, and varying replica counts. Extensive measurements demonstrate that this single equation tracks observed latencies within a few percent across a wide operational range, enabling the runtime to anticipate SLO violations and to support proactive routing, autoscaling, and offloading decisions throughout the system. 

By combining proactive latency-spike detection with utilization-driven autoscaling and real-time, in-memory telemetry, LA-IMR adapts within milliseconds to traffic bursts or faults, shrinking long-tail latency and bolstering overall system reliability. Building on this foundation, our work contributes: 

- 1) **Closed-form, dual-purpose latency model** . We derive a single analytic equation that decomposes end-to-end delay into processing, network, and M _/_ M _/_ c queuing terms and captures super-linear contention with one exponent. Two complementary instantiations—fixed-replica _gm,i_ ( **_λ_** ) and fixed-traffic _gm,i_ ( _Nm,i_ )—drive millisecond-scale routing decisions as well as slower capacity-planning optimisation. 

- 2) **Tail-aware, quality-stratified request routing** . LA-IMR is an event-driven, in-memory controller that predicts imminent P99 breaches, routes requests across latency/accuracy-differentiated queues, and pre-emptively offloads traffic or instantiates replicas before long-tail spikes materialise. 

- 3) **Proactive autoscaling from model-predicted metrics** . By exporting the required replica count, as computed from the latency model, as a custom Kubernetes metric, the system eliminates the 60–120s lag and oscillations of CPU-driven HPA, scaling just-in-time to keep queues short. 

- 4) **Empirical gains on bursty vision workloads** . Experiments with YOLOv5m and EfficientDet under bursty traces show that LA-IMR trims P99 latency by up to 20.7%, confirming the practical impact of the theory-driven design. 

This work presents LA-IMR, an SLO-aware control layer that proactively routes, scales, and off-loads AI inference to suppress long-tail latency in hybrid edge–cloud systems: Section II surveys related tail-latency and resource-allocation work; Section III formalises a closed-form latency model and optimisation framework; Section IV details the LA-IMR architecture—multi-queue scheduler, predictive router, and custom-metric Kubernetes autoscaler; Section V demonstrates up to 20.7% P99-latency reductions under bursty loads; and Section VI sketches future paths toward resilient, tail-tolerant AI services. 

## II. RELATED WORK 

## _A. Tail Latency Mitigation_ 

Early work formulated long-tail delay as a fault to be masked rather than eliminated. _C3_ steers reads toward the 

fastest-responding replica while throttling overly aggressive clients, trimming the 99th-percentile (P99) latency without global coordination [1]. In large fan-out services, Dean and Barroso advocate hedged or tied requests so that a straggler no longer determines end-to-end response time [2]. These “speculative” techniques are powerful, yet they operate _after_ latency inflation has already begun and provide little guidance on resource sizing. 

More recent systems push decision making inside the service graph. _GrandSLAm_ predicts per-stage completion times, then reorders or batches microservice calls to respect job-level SLAs while sustaining throughput [3]. Complementary edge–cloud frameworks model DNN inference pipelines and split them across heterogeneous hardware to keep worst-case delay bounded under fluctuating bandwidth and load [4], [5], [11], [12]. These platforms, however, typically rely on threshold-based autoscalers or coarse queue metrics, which react only after the utilisation spike is visible. 

Offloading augments local scheduling by opportunistically handing work to faster or less-loaded tiers. Queue-length-aware fog dispatchers [13], partial offload optimisers that jointly minimise energy and latency [14], and reinforcement-learning controllers for mobile MEC [9] all illustrate the benefit of decoupling execution sites. Extensions with IRS-assisted channels [6], dependency-aware scheduling [7], or sub-task partitioning [10] further reduce tail variance, yet they rarely couple the offloading trigger to a predictive latency model that spans processing, network, and queueing effects. 

LA-IMR bridges these gaps by (i) deriving a closed-form, utilisation-driven latency law that can be evaluated in microseconds, (ii) embedding that model in an event-driven multi-queue router that makes per-request routing and offloading decisions, and (iii) exporting a custom metric to Kubernetes so replicas scale _proactively_ , before queues build. 

## _B. Autoscaling and Resource Management_ 

Early autoscalers integrated queueing theory with thresholdor model-driven control. Gandhi et al.’s adaptive model-driven autoscaler reduces SLA violations by accurately forecasting required capacity [15]. Cluster managers implemented isolation mechanisms similar to Borg’s priority and quota controls for latency-critical jobs [16]. With microservices, the focus has shifted to replicas for each service and resource management that is aware of Service Level Objectives (SLOs). Kubernetes’s Horizontal Pod Autoscaler (HPA) scales pods based on resource or custom metrics [17], while FIRM and Sinan utilize telemetry-driven or learned models for controlling microservice resources [18], [19]. LA-IMR utilizes a closed-form, utilization-driven model to forecast SLO pressure, trigger event-driven routing, and provide custom replica targets to Kubernetes before tail latency becomes an issue. 

## _C. In-Memory Processing and Dynamic Routing_ 

Prior efforts to address tail-latency spikes have focused on three key factors—in-memory state, dynamic offloading, 

and fine-grained replica control—yet none has unified them under a single predictive model, as LA-IMR does. Heracles partitions cores, memory, and caches to confine datacenter interference, but it cannot forecast request-level SLO breaches in advance [20]. FaRM and FASTER lower the latency floor through RDMA-backed and hybrid in-memory key–value stores, respectively, but both leave queue buildup to the application layer rather than modeling it as a firstclass control signal [21], [22]. A closer line of work couples dynamic placement with edge–cloud inference. Neurosurgeon partitions DNN execution between mobile devices and the cloud to reduce response time [23], while Jellyfish considers inference serving with end-to-end latency SLOs over dynamic edge networks [24]. 

LA-IMR extends this lineage by (i) holding all routing telemetry in process memory for sub-millisecond decisions, (ii) predicting per-replica latency with a calibrated utilization model so replicas can be prepared to begin _before_ queues surge, and (iii) integrating offloading, routing, and autoscaling into one event-driven loop. 

## _D. Cloud Robotics_ 

Object detection in cloud robotics balances accuracy against latency amid bursty, location-dependent demand. High-precision detectors such as Faster and Mask R-CNN excel in the cloud but suffer multi-hundred-millisecond delays when GPU queues saturate [25]. Conversely, edge-optimised one-stage models (e.g., EfficientDet, MobileNet-SSD) return sub-50ms results on lightweight devices, yet their lower mAP limits use in safety-critical contexts [26]. Foundational work—from R-CNN through PASCAL VOC—still guides model-selection policy [27], [28], and Huang _et al._ showed that no single network meets all SLOs across traffic regimes [29]. 

Traditional cloud-edge schedulers rely on coarse utilisation thresholds, scaling only after queues build, which drives P99 latencies to exceed the mean by more than 5× during bursts [1], [2]. LA-IMR embeds a closed-form, utilisation-aware latency model and a quality-differentiated multi-queue scheduler directly in the inference path. It scales replicas or off-loads traffic _proactively_ , maintaining task-level P99 within SLOs despite workload spikes, fluctuating RTT, and hardware heterogeneity—offering a principled antidote to tail-latency anomalies in cloud-robotic perception. 

## III. SYSTEM MODEL AND PROBLEM FORMULATION 

Inspired by foundational research on latency modeling and resource allocation in edge–cloud environments, particularly the surveys conducted by Mao et al. [30], [31]—we develop a closed-form latency expression specifically adapted to our multi-replica hybrid infrastructure. This formulation incorporates conventional latency factors such as computation, communication, and queuing delays, while also integrating empirical latency patterns drawn from recent experimental analyses [24], [32]. 

## _A._ **_Latency Components_** 

The end-to-end latency experienced by a task _t ∈T_ is the sum of processing, network, and queuing delays: 



where 

- _L_<sup>infer</sup> _m,i_<sup>—</sup><sup>_inferenceprocessingdelay_:latencyofmodel</sup><sup>_m_</sup> when served by instance _i_ under its current load; 

- _Dt,i_<sup>net—</sup><sup>_network(RTT)delay_:round-tripdata-transfer</sup> latency between the data source and instance _i_ ; 

- _Qt,i_ — _queuing delay_ : waiting time in the input queue of instance _i_ before execution begins. 

TABLE I 

NOTATION TABLE 

|**Symbol**|**Description**|
|---|---|
|_Lm_|Mean latency of model _m_ on the CPU baseline|
|_Sm,i_|Speed-up of instance _i_ for model _m_|
|_λm_|Aggregate arrival rate for model _m_|
|_Nm,i_|Replica count of model _m_ on instance _i_|
|_Rm_|Mean compute time per request of model _m_|
|_R_<sup>max</sup><br>_i_|Sustainable compute budget of instance _i_|
|_Bi_|Background (co-tenant) load on instance _i_|
|_γ >_1|Empirical super-linear exponent|



## _B._ **_Entities and Notation_** 

_1) Inference tasks.:_ The set of independent inference tasks is _T_ = _{_ 1 _, . . . , T }_ . Each task _t_ specifies an accuracy requirement _αt_<sup>req</sup> and, optionally, a latency service-level objective (SLO) _τt_ . 

_2) Inference models.:_ The catalogue of ML models is _M_ = _{_ 1 _, . . . , M }_ . Every model _m ∈M_ is described by 

- _L_<sup>infer</sup> _m_<sup>,steady-stateinferencelatencyona</sup><sup>_reference_de-</sup> vice; 

- _am ∈_ [0 _,_ 1], steady-state accuracy; 

- _Rm_ , per-inference resource demand (e.g., CPU-seconds). 

Instance _i_ offers a per-inference CPU budget _Ri_<sup>max</sup> . When model _m_ executes on instance _i_ its measured latency is _L_<sup>infer</sup> _m,i_<sup>as</sup> in Eq. (5). We track two canonical computer-vision backbones: 



Their steady-state inference latencies and CPU demands on a Raspberry Pi 4 are summarised in Table II. Note that the lightweight EfficientDe is nearly two orders of magnitude cheaper in _Rm_ than the heavier YOLOv5m. 

_3) Hybrid Infrastructure as VM Instances:_ We consider an edge–cloud continuum provisioned as virtual machine instances. Hence 



TABLE II 

MODEL PROFILE ON A REFERENCE EDGE INSTANCE PROVISIONED WITH A RASPBERRY PI 4 VM CONFIGURED WITH 3 CPU CORES. _Rm_ IS EXPRESSED IN CPU-SECONDS PER INFERENCE; _Lm_<sup>INFER</sup> IS THE STEADY-STATE LATENCY ( _±_ STD. ERR.). 

- _Sm,i_ is the hardware speed-up factor of instance _i_ for model _m_ (Table III); 

- _γ ≥_ 0 controls how sharply latency rises as utilisation increases; 

- _Ui_ is the instantaneous utilisation of instance _i_ : 

|Model|_L_<sup>infer</sup><br>_m_<br>[s]|_Rm_ [CPU-s]|
|---|---|---|
|EfficientDet (_m_1)|0_._09_±_1_._2_×_10<sup>_−_3</sup>|0.10|
|YOLOv5m (_m_2)|0_._73_±_3_._0_×_10<sup>_−_3</sup>|1.00|





<!-- Start of picture text -->
� λm′Rm′ + Bi<br>m ′ ∈M<br>Ui = . (6)<br>Ri max<br><!-- End of picture text -->

Here: 

Their union yields the global instance set _I_ = _C ∪E_ . Each **instance**<sup>1</sup> _i ∈I_ exposes a finite resource budget _Ri_<sup>max</sup> (e.g., CPU-seconds, GPU-seconds) and may be subject to an exogenous background load _Bi_ . 

- _λm′_ is the arrival rate of model _m_<sup>_′_</sup> . 

- _Rm_<sup>_′_</sup> is the resource consumption per inference for _m_<sup>_′_</sup> . 

- _Bi_ denotes the background (co-tenant) load on instance _i_ . 

- _• Ri_<sup>max</sup> is the total capacity of instance _i_ . 

_4) Decision Variable:_ The binary variable 



The hardware scaling factor _Sm,i_ represents the hardwaredependent acceleration and is typically determined empirically. For example, Oh et al. [33] show that CPUs can be up to 20 times faster in certain scenarios, while Jouppi et al. [32] report that TPUs are approximately 15 to 30 times faster than contemporary GPUs (e.g., the NVIDIA K80). However, performance may vary significantly depending on the underlying technology and specific commercial hardware. 

encodes the joint _model-selection_ and _task-placement_ decision. _5) Resource and Assignment Constraints:_ Each task must be assigned exactly once: 



To provide a conceptual understanding of the hardware scaling factor, this work approximates typical values, as summarized in Table III. 

The aggregate resource demand on each node shall not exceed its capacity: 



### TABLE III 

TYPICAL SCALABILITY OF HARDWARE IN SINGLE- AND MULTI-INSTANCE SCENARIOS. 

## _C._ **_Inference Processing Delay_** 

|**Hardware Type**|**Typical** **_Sm,i_**|
|---|---|
|CPU|1|
|GPU|2–20|
|TPU|30–100+|



_a)_ **_Latency as a Function of Model Size_** _:_ Nigade _et al._ [24] empirically observe that the inference latency of a deeplearning model grows sub-linearly with the input batch size. For a model _mj_ with parameter file size _sj_ and batch size _b_ , the mean per-inference latency is 

_c)_ **_Affine Power-Law Form_** _:_ During calibration we vary only the traffic of the model under study and keep co-tenancy fixed. Writing the _per-replica_ arrival rate as _λ_<sup>˜</sup> _m,i_ = _λm/Nm,i_ and expanding _Ui_<sup>_γ_yields</sup> 



where _α_ is a hardware- and framework-dependent constant and 0 _< γ <_ 1 captures the sub-linear batching benefit. 



_b)_ **_Utilisation-based Latency Model_** _:_ Extending the principles of utilization-based performance modeling proposed by Wang et al. [30], [31] and inspired by hardware-performance scaling insights from Jouppi et al [32], we formulate the inference latency of model _m_ running on instance _i_ as a function of _instance utilization Ui_ : 





where 

- _Lm_ is the single-inference latency of model _m_ on the _reference_ hardware; 

> 1While instance and replica are not strictly synonymous in Kubernetes—replica denotes the desired number of concurrently running pods—this work uses the terms interchangeably for simplicity and consistency in discussion. 

The baseline _αi_ is the latency paid even at idle utilisation, whereas the second term _βm,iλ_<sup>˜</sup><sup>_γ_</sup> _m,i_<sup>growssuper-linearlyonce</sup> traffic increases. 

|T<br>_Nm_2_,i_|HE ACTUAL LATE<br>=_{_1_,_2_,_4_}_ PER R<br>R|TABLE IV<br>NCY GIVEN BY <br>EPLICA(E.G., <br>EPLICA) (SECO|_λm_2 =_{_1_,_2_,_3_,_ <br>_m_2, YOLOV5M, <br>NDS).|4_}_ AND<br> 3 CPUS PER|
|---|---|---|---|---|
|_Nm,i_|_λm_ = 1|_λm_ = 2|_λm_ = 3|_λm_ = 4|
|1|0_._73_±_0_._004|4_._97_±_0_._02|7_._71_±_0_._03|10_._46_±_0_._04|
|2|0_._73_±_0_._004|1_._26_±_0_._19|3_._76_±_0_._33|5_._12_±_0_._53|
|4|0_._73_±_0_._004|0_._90_±_0_._06|1_._12_±_0_._12|1_._77_±_0_._29|



_d)_ **_Empirical Validation._** _:_ Table IV reports the measured mean per-inference latencies of YOLOv5m ( _m_ 2) for different arrival rates _λm_ 2 and replica counts _Nm_ 2 _,i_ . 

Fig. 2 shows that Eq. (8), with calibrated parameters _αi_ = 0 _._ 73, _βm,i_ =1 _._ 29, and _γ_ =1 _._ 49, closely matches the measurements. Because the three parameters are re-estimated whenever the hardware mix ( _Sm,i, Ri_<sup>max</sup> ) or co-tenant load ( _Bi_ ) changes, the model remains accurate under a wide range of deployment conditions. Such predictive capability is valuable for proactive resource provisioning and request routing during workload fluctuations. 



Fig. 2. The inference latency measured in the real operations and predicted by Eq. 8 with _αi_ =0.73, _βm,i_ = 1.29, and _γ_ =1.49 (3 CPUs per replica). 

## _D._ **_Queueing Delay for Multi-Replica Services_** 

Let _Nm,i ∈_ Z _>_ 0 denote the _replica count_ of model _m_ on instance _i_ . With exponential inter-arrival and service times, the replica pool forms an M/M/ _Nm,i_ queue. The service rate is 



and the traffic intensity 



_a) Load Distribution.:_ Tasks destined for _model m_ arrive at rate _λm_ and are distributed among the _Nm,i_ replicas via round-robin or similar policies, yielding per-replica arrival rate 



_b) M/M/c Queue.:_ Assuming exponential inter-arrival and service times, each replica behaves as an M/M/ _c_ queue with _c_ = _Nm,i_ servers. Denoting the service rate by _µm,i_ = _Sm,i_ _<u>λm</u> L_<sup>infer</sup> _m_<sup>_,_thetrafficintensitybecomes</sup><sup>_ρm,i_=</sup> _Nm,iµm,i_<sup>_._</sup> Using Erlang- _C_ [34] 



the expected queueing delay becomes 



A task bound to exactly one ( _m, i_ ) therefore experiences 



which collapses to the unique non-zero term selected by _xt,m,i_ . 

## _E._ **_Task-level Queue Delay Selection_** 

Because each task is bound to exactly one ( _m, i_ ) via (2), the queueing delay actually experienced by task _t_ is the indicator-weighted sum 



which collapses to the unique non-zero term for the chosen pair. 

## _F._ **_Latency Function for Fixed Replica Layout_** 

When the replica counts _{Nm,i}_ are _fixed_ , the per-instance end-to-end latency becomes an explicit function of the arrival-rate vector **_λ_** : 



with stability constraint _ρm,i <_ 1 for all ( _m, i_ ). Substituting (15) into (1) yields the task-level latency 



Fig. 3 illustrates the service’s latency characteristics across varying arrival rates **_λ_** = 1 _, . . . ,_ 6 with _Nm,i_ = 4, revealing distinct behaviors for average, P95, and P99 latencies. The average latency increases gradually, reflecting growing queuing delays as load intensifies. In contrast, the P95 latency exhibits a steeper rise, indicating a broader spread in response times and the beginning of tail latency. The P99 latency escalates even more sharply, highlighting significant performance degradation under peak load conditions. 









<!-- Start of picture text -->
(a) Average Latency (b) 95th Percentile (P95) Latency (c) 99th Percentile (P99) Latency<br><!-- End of picture text -->

Fig. 3. Latency metrics for user robot19 under varying arrival rates, showing super-linear growth in average, P95, and P99 latencies. 

## _G._ **_Per-Instance Latency as a Function of the Number of Replicas_** 

With the arrival-rate vector **_λ_** held fixed, the only degree of freedom left in the per-instance latency expression is the replica count _Nm,i_ . Making this dependence explicit gives 



where 

Processing and network delays are unaffected by the replica count once **_λ_** is fixed. Queueing delay shrinks as _Nm,i_ grows because both the service-pool capacity _Nm,iµm,i_ increases linearly and the utilisation _ρm,i_ ( _Nm,i_ ) falls hyperbolically. 

As an M _/_ M _/Nm,i_ model is required, we adjust the factor _C_ ( _ρ, N_ ) by using the Erlang- _C_ formula: 



The marginal benefit of adding replicas is largest near the instability boundary ( _Nm,iµm,i_ ≳ _λm_ ) and flattens rapidly once _ρm,i_ ≲ 0 _._ 3. This shape is crucial for choosing a costoptimal replica layout that still satisfies latency SLOs. Therefore, we define the task-level latency by substituting (17) into 



yields a closed-form, differentiable objective that can be handed for automatic replica-layout tuning. 

## _H._ **_Optimisation Problems with Two Latency Models_** 

The latency of a request routed through replica group ( _m, i_ ) can be expressed in _two_ complementary closed-form models: 



Define the corresponding task-level latencies 



Two optimisation stages naturally arise. 

_a) Workload routing (_ fixed replica layout, _Nm,i_ ) _:_ It is about a problem to route which replica is choosen out of the _Nm,i_ replicas. Given the current replica counts _{Nm,i}_ and arrival-rate vector **_λ_** , the router chooses _x_ : 



_b) Capacity planning & routing (_ fixed traffic _):_ For longer-term provisioning the operator sizes the replica pools and chooses routing simultaneously: 





Here _cm,i_ is the per-replica cost and _β_ trades off latency versus spend. 

IV. LATENCY-AWARE, PREDICTIVE IN-MEMORY ROUTING AND PROACTIVE AUTOSCALING (LA-IMR) 

Based on the sub-linear model proposed in §III-C and the instance utilisation-oriented delay expression in (15) and (17), We design a control layer that _schedules, routes, and offloads_ requests so that _tail-latency_ ( _P_ 99) stays within each task’s SLO _τt_ even under bursty traffic and heterogeneous hardware. 

Furthermore, the proposed LA-IMR framework leverages the modular nature of microservice architecture to improve overall service quality. By reducing tail latency—the slowest response times—it ensures more consistent and predictable system performance. 

LA-IMR comprises three tightly-coupled components: 

## _A._ **_Quality-Differentiated Multi-Queue Scheduler_** 

The SLO-Aware Inference Router maintains and monitors the status of the different SLO requests by using its corresponding queue at the code level, leading to the real-time monitoring and the early-latency spiks detection. 

To address diverse quality of service (QoS) requirements – such as accuracy and latency – we decompose inference capabilities into specialized _microservices_ aligned with following performance tiers: 

- Low-Latency Services (e.g., edge-optimized service like ultra-low latency): Lightweight models such as EfficientDet are deployed on resource-constrained edge nodes to support real-time, latency-sensitive tasks. 

- Balanced Services: Mid-range models such as YOLOv5m offer a trade-off between latency and accuracy, ideal for tasks with moderate performance demands. 

- Precision Services (e.g., accuracy-prioritized): Computationally heavier models such as Faster R-CNN run in the cloud, delivering high accuracy for use cases where latency is less critical. 

We partition traffic into _quality classes Q_ = _{_ Low-Latency _,_ BALANCED _,_ PRECISE _}_ , each backed by an run-time queue _Qq_ . 

- Low-Latency lane (Low-Latency) : latency-critical tasks use small-footprint EfficientDet-Lite0 streams and inherit the highest dispatch priority. 

- BALANCED lane (BALANCED) : accuracy-bound tasks are serviced by YOLO5m replicas and accept longer—but still bounded—delays. 

- PRECISE lane (PRECISE) : accuracy-bound tasks (e.g. fine-grained inspection) are serviced by R-CNN replicas. 

TABLE V 

COMPARISON OF YOLOV5M AND EFFICIENTDET-LITE0 

|**Attribute**|**YOLOv5m** [35]|**EfficientDet-Lite0** [36]|
|---|---|---|
|Architecture|Ultralytics YOLOv5|Google EfficientDet-Lite|
|Model Size|21.2M|4.3M|
|mAP@0.5|64.1%|˜ 25%|
|mAP@0.5:0.95|45.4%|˜ 20%|
|Use Case|Balanced performance|Edge/mobile efficiency|



Due to its high modularity, the microservice architecture offers several advantages over the monolithic service architecture, where all necessary services are deployed within a single instance. Fig.4 presents a comparison of the latency between the two architectures. Fig.4a shows the average latency, Fig.4b illustrates the 95th percentile (P95) latency, and Fig.4c presents the 99th percentile (P99) latency for both architectures. Overall, the microservice architecture demonstrates superior latency performance—especially when sufficient resources, such as an increased number of replicas _Nm,i_ , are available. This is primarily because context switching among different models imposes a higher burden on a monolithicbased instance. 

## _B._ **_SLO-Aware Adaptive Routing_** 

A dedicated _SLO-Aware Inference Router_ (Fig. 1) dynamically forwards robotic and general inference requests to the most suitable micro-service tier. Each arriving request is represented as the tuple 



where _m_ is the model, _i_ the tier index, _t_ the arrival time, and _λm_ [req _/_ s] is the 1-s sliding-window arrival rate maintained in memory. 

Given the current replica layout _{Nm,i}_ and the instantaneous arrival-rate vector **_λ_** , the router executes the following steps: 

- = 

- i) **Compute the model-specific latency budget** : _τm x L_<sup>infer</sup> _m_ with a global multiplier _x>_ 1 that budgets headroom for networking and queueing delays shown in Algorithm 1. 

- ii) **Predict per-instance latency** : look up _gm,i_ ( **_λ_** ) in an in-memory table pre-computed by the analytic model (§III-C,III-G) and refreshed every ∆ seconds. 

- iii) **Filter feasible replicas** : retain only the pairs _⟨m, i⟩_ whose predicted latency satisfies the SLO _gm,i_ ( **_λ_** ) _≤ τm_ . 

- iv) **Select the target replica** : choose 



breaking ties by the lower cost _cm,i_ to avoid unnecessary over-provisioning. 

- v) **Enqueue the request** : push _r_ into the queue of tier _i_<sup>_⋆_</sup> . If no local replica meets the budget ( _gm,i > τm ∀i_ ), offload _r_ to the upstream (faster or cloud) tier as prescribed by Algorithm 1. 

## _C._ **_Edge–Cloud Offloading & Replica Autoscaling_** 

The SLO-Aware Inference Router detects the workload fluctuation and decide when to offload to the cloud and other edge service by using the per-instance latency determined by the inputs of the arrval rate and the current resource, such as the number of the replicas. 

The event-driven LA-IMR controller reacts on every incoming request instead of running at fixed intervals. It first computes a 1-second sliding-window arrival rate _λm_ to judge whether the just-arrived request would breach the latency 





<!-- Start of picture text -->
(a) Average Latency<br><!-- End of picture text -->







<!-- Start of picture text -->
(b) 95th Percentile (P95) Latency (c) 99th Percentile (P99) Latency<br><!-- End of picture text -->

Fig. 4. Inference latency comparison between the microservice and monolithic service architecture as the number of replica _Nm,i_ increases when the arrival rate _λ_ =4 is given. Overall, the microservice architecture shows the superior latency. 



Fig. 5. Real-time latency prediction uses the arrival rate _λ_ to meet the target latency _τ_ . If latency exceeds _τ_ , the system increases replicas _Nm,i_ . This prediction also enables proactive offloading based on _λ_ and _Nm,i_ . 

where _Nm,i_ ( _t_ ) is the replica count computed in line 15 of Algorithm 1. 

The metric is scraped by Prometheus and surfaced to the HPA through the k8s-prometheus-adapter. The HPA’s reconciliation loop then executes, every 5 s: 

- i) **Read the custom metric** and compare it with the current Pod count. 

- ii) **Scale out** (or in) by the exact difference, bounded by the per-Deployment cap _Nm,i_<sup>maxandclusterquotas.</sup> 

- iii) **Respect graceful-termination** : drained Pods are held until in-flight requests finish, preventing mid-request losses. 

Because the scaling trigger is the _predicted_ latency budget ( _τm_ = _x L_<sup>infer</sup> _m_<sup>)ratherthanlaggingutilisation,extrareplicas</sup> are spun up _before_ queueing delay violates the SLO and are shed once utilisation drops below _ρ_ low. In practice this removes the 60–120 s reaction lag typical of threshold-based autoscalers, keeps the _p_ 99 latency inside the _x L_<sup>infer</sup> _m_ envelope, and avoids chronic over-provisioning. 

## V. PERFORMANCE ANALYSIS 

## _A._ **_Experiment Environment_** 

SLO; if so, the request is immediately off-loaded to the faster/cloud tier. In parallel, it maintains an EWMA-smoothed accumulated rate _λ_<sup>_accumul_</sup> _m_ that captures sustained demand. This second metric drives replica scaling and bulk off-load decisions, ensuring resources grow only when higher load persists and shrink when utilisation stays low shown in Fig. 5. By combining per-request mitigation with stable long-term control, the algorithm keeps tail-latency low while avoiding unnecessary resource oscillations, detailed in Algorithm 1. 

## _D._ **_Implementation of Dynamic Scaling in a Kubernetes Environment_** 

We realise the replica decisions of Algorithm 1 with the _Kubernetes Horizontal Pod Autoscaler (HPA)_ . Instead of relying on generic resource indicators such as CPU %, the LA-IMR controller exports a desired_replicas **custom metric** for every Deployment _⟨m, i⟩_ : 

_1)_ **_Hardware Specifications_** _:_ We utilize the CloudGripper testbed—a scalable, open-source, rack-mounted cloud robotics platform optimized for large-scale manipulation tasks. Each cell features a low-cost, 5-DOF Cartesian robot with a rotatable parallel-jaw gripper, controlled via a Raspberry Pi 4B (Quad-core Cortex-A72, 1.8GHz) and a Teensy 4.1 for realtime actuation. Dual RGB cameras (top and bottom views) capture multi-angle data at up to 30 FPS. As shown in Fig. 6, each robot operates in a standardized, enclosed cell (274 mm × 356 mm × 400 mm) with dedicated lighting, ensuring uniform and parallelized data collection. Five of them are connected to our SLO-Aware interference router to get services by sending an image taken by its camera and receiving the coordinates of the object. 

_2)_ **_Cloud/edge Computing Continuum_** _:_ CloudGripper leverages a cloud-edge continuum to support scalable, distributed robotic control and experimentation. The edge infrastructure includes a 32-robot rack connected via 1 Gbit/s Ethernet to a 10 Gbit/s switch, forming an on-campus edge 

desired_replicas _m,i_ = _Nm,i_ ( _t_ ) _,_ 

**Algorithm 1:** Event-driven LA-IMR with _x_ -scaled latency SLO 

**Input:** incoming request _r_ for service instance ( _m, i_ ) at time _t_ now **1 Function** SLIDINGRATE( _m, tnow_ ) **: 2 while** _Qm̸_ = ∅ **_and_** _tnow − Qm.front_ () _>_ 1 **do 3** _Qm._ pop <u>front()</u> ; // discard arrivals _>_ 1 s old **4 end 5** _Qm._ push back( _t_ now); **6 return** _λm ←|Qm|_ [req _/_ s]; **Parameters:** _x >_ 1 (latency multiplier), EWMA weight _α_ , utilization floor _ρ_ low, per-instance replica cap _Nm,i_<sup>max</sup> **7** _λm ←_ SLIDINGRATE( _m, t_ now); **8** _τm ← x L_<sup>infer</sup> _m_ ; // **Per-model SLO 9** _g_ � _m,i_<sup>inst</sup><sup>_←gm,i_(</sup><sup>_λm_);</sup> **10 if** _g_ � _m,i_<sup>_inst> τm_</sup><sup>**then**</sup> // protect this single request **11 offload** _r_ to nearest fast/cloud tier; **12 return 13 end 14** read _Nm,i, ρm,i_ from shared state; **15** _λ_<sup>accum</sup> _m ← α λ_<sup>accum</sup> _m_ + (1 _− α_ ) _λm_ ; **16** _g_ � _m,i ← gm,i_ ( _λm_<sup>accum</sup> ); **17 if** _g_ � _m,i > τm_ **then** // predicted SLO breach **18 if** _Nm,i < Nm,i_<sup>max</sup><sup>**then**</sup> **19 scale out** one replica on the current tier; **20 else 21** _ϕ ←_ min 1 _,_<sup>_<u>g</u>_�</sup><sup>_m,i −τm_</sup> ; � � _g_ � _m,i_ **22 offload** fraction _ϕ_ upstream (balanced _→_ low-latency tier); **23 end 24 end 25 else if** _ρm,i < ρlow_ **_and_** _Nm,i >_ 1 **then 26 scale** **<u>in</u>** one replica to save cost; **27 end 28** route request _r_ to the chosen local replica; 

cluster. Each robot is operated through a REST API on a Raspberry Pi 4B, enabling low-latency control and dualcamera streaming at 30 FPS. The edge cluster comprises 32 Raspberry Pis (32x4 cores) running on Kubernetes with Prometheus-based monitoring, achieving an average container startup time of 1.8 seconds on ARM64. 

A remote cloud cluster, hosted by Ericsson, supplements this with 19 dedicated CPU cores and a 36 ms network delay over a 10 Gbit/s link. 

This setup enables dynamic offloading between edge and cloud, optimizing for latency, resource constraints, and performance. Benchmarks highlight the impact of deployment location on responsiveness, underscoring the need for adaptive orchestration in real-time robotics. 







<!-- Start of picture text -->
(a) Cube manipulation. (b) Strip manipulation.<br><!-- End of picture text -->

Fig. 6. CloudGripper work cells performing object manipulation with dualcamera views and consistent cell configurations. 

_3)_ **_Predictive-Metric Horizontal Pod Autoscaling (PM-HPA)_** _:_ We introduce Predictive-Metric Horizontal Pod Autoscaling (PM-HPA), a proactive and latencyaware enhancement to Kubernetes’ standard HPA. Rather than relying solely on traditional resource metrics, each microservice computes and exports a single custom metric, desired replicas, based on an internal closed-form queuing model that translates real-time request rates into the optimal number of replicas to mitigate the 99th percentile (P99). Latency measurements are collected via Prometheus, and the computed replica count is exposed to the native HPA, enabling it to scale pods responsively without altering the Kubernetes control plane. PM-HPA responds to traffic surges in milliseconds and maintains graceful shutdowns during scale-in. This results in improved tail-latency performance while maintaining full compatibility with both standard and managed Kubernetes environments. 

_4)_ **_Experimental Setup and Test Scenario_** _:_ LA-IMR runs on a Kubernetes edge cluster hosting a YOLOv5m object-detection microservice. A single CPU replica averages _L_<sup>infer</sup> _m ≈_ 0 _._ 8 s; the robot _→_ router _→_ edge _→_ robot round-trip contributes another _≈_ 1 s. Hence the latency SLO is set to 



with a safety margin _x_ = 2 _._ 25 to absorb transient network and queueing delays. 

Unless stated otherwise, all experiments use the following calibrated parameters: 

- EWMA smoothing weight: _α_ = 0 _._ 8 

- Cost–latency trade-off in Eq. (23): _β_ = 2 _._ 5 

- Utilisation–latency exponent: _γ_ = 0 _._ 90 

To evaluate latency robustness, we steadily increase the arrival rate _λ_ —equivalently, the number of robots issuing requests—while recording the P95 and P99 response time. Whenever the predicted latency for a replica pool exceeds the SLO, LA-IMR automatically scales the pool horizontally by incrementing the replica count _Nm,i_ in accordance with Algorithm 1. This closed-loop reaction keeps the system below the instability boundary and maintains tail-latency within the configured envelope. 





<!-- Start of picture text -->
(a) Average, P95, and P99 latencies of the proposed LA-IMR approach.<br><!-- End of picture text -->



(b) The latencies of the baseline method using Prometheus-measured latency. 

Fig. 7. Latency comparison of LA-IMR and the baseline latency-based method across varying arrival rates _λ ∈{_ 1 _,_ 2 _,_ 3 _,_ 4 _,_ 5 _,_ 6 _}_ . LA-IMR significantly reduces tail latencies, particularly the P99 latency, indicating better performance under high load. 

## _B._ **_Latency Evaluation under Workload Fluctuations_** 

Fig. 7 illustrates a comparison between LA-IMR and a conventional _latency-focused_ autoscaling strategy as the incoming request rate _λ_ varies from 1 to 6 requests per second. When the system operates under light load conditions ( _λ ≤_ 3), both mechanisms maintain the service-level objective (SLO), exhibiting comparable median response times. However, as the demand rises, the traditional baseline shows noticeable latency variability. Specifically, at _λ_ = 6, the 99th percentile latency (P99) reaches 6.8 seconds, whereas LA-IMR constrains P99 to no more than 5.4 seconds. This improvement is primarily attributed to its anticipatory scaling of replicas and targeted offloading strategies. As a result, LA-IMR achieves significantly more consistent tail latency while maintaining similar average performance levels. 

## _C._ **_Mitigation of Long-Tail Latency_** 

The Prometheus telemetry in Fig. 8 highlights LA-IMR’s superior tail-latency control: its inter-quartile range is narrower, and extreme outliers are absent. Algorithm 1 predicts 







<!-- Start of picture text -->
(a) LA-IMR (b) Baseline<br><!-- End of picture text -->

Fig. 8. Box plots of P99 latencies using Prometheus measurements for arrival rates _λ_ = 1–6 req _/_ sec. LA-IMR reduces the interquartile range by 27% and the maximum outlier by 41%. 

queue build-ups from the closed-form model and either scales out or off-loads _before_ long queues materialise, thereby suppressing otherwise destructive spikes. 

Table VI shows that LA-IMR consistently achieves lower or equal P95 latency compared to the baseline, with the largest reduction of 14% at _λ_ = 5 req/s. For P99, the gains grow 

TABLE VI 

P95 AND P99 LATENCIES (MEAN _±_ SD, SEC) ACROSS ARRIVAL RATES _λ_ ; LOWER NUMBERS ARE **BOLD** . 

||**P**|**95**|**P9**|**9**|
|---|---|---|---|---|
|_λ_ (req/s)|LA-IMR|Baseline|LA-IMR|Baseline|
|1|**1.947**_±_**0.003**|1.950_±_0.004|**1.989**_±_**0.001**|2.012_±_0.106|
|2|2.287_±_0.568|**2.278**_±_**0.288**|**2.858**_±_**0.826**|2.933_±_0.598|
|3|**2.928**_±_**0.494**|3.107_±_0.566|**4.042**_±_**0.856**|4.201_±_0.863|
|4|3.692_±_0.703|**3.634**_±_**0.575**|**4.167**_±_**0.902**|4.782_±_0.526|
|5|**3.314**_±_**0.471**|3.963_±_1.091|**4.782**_±_**0.639**|5.632_±_1.717|
|6|**4.051**_±_**0.599**|4.649_±_1.125|**5.435**_±_**0.827**|6.855_±_2.208|



with load—from 1% at _λ_ = 1 to 20.7% at _λ_ = 6—averaging around 9% overall. At peak load, LA-IMR also cuts the P99 standard deviation by over 60% (2.21 s _→_ 0.83 s), greatly reducing outliers and improving SLO stability. 

## _D._ **_Discussion_** 

**Experimental setup.** LA-IMR was evaluated on a shared Kubernetes cluster whose pod start-up and tear-down times fluctuate with node availability, image caching, and network contention, introducing real-world noise that can mask fine-grained effects. For tractability we limited the study to two vision workloads—EfficientDet-Lite0 and YOLOv5m—and tuned the EWMA weight _α_ , utilisation floor _ρ_ low, and latency-budget multiplier _x_ offline for their specific SLOs. Deployments with stricter SLOs or more volatile demand may therefore need adaptive self-tuning. 

**Limitations and future work.** Load bursts were emulated with a bounded-Pareto process, whereas real incidents (e.g., holiday shopping) often cause correlated spikes across services. We also left global off-loading and cross-cluster load balancing unoptimised from the cloud-provider’s perspective—an open problem for future work. 

## VI. CONCLUSION 

We advance latency-sensitive edge–cloud inference by coupling a closed-form latency model—capturing processing, network, and queueing delays—with LA-IMR, a predictive, 

SLO-aware control layer that unites quality-stratified microservices, event-driven autoscaling, and selective offloading. Kubernetes experiments show LA-IMR trims P99 latency by up to 20.7% and cuts its variance by more than half compared with a reactive autoscaler, owing to prediction-guided offloading that deflects bursts before queues form and proactive replica provisioning that adds capacity before utilisation nears instability. 

We will extend LA-IMR by incorporating memory-intensive, variable-batch workloads to stress-test its latency model, replacing static control knobs with an online self-tuner that continuously maximises “SLOs met per dollar,” and combining fast- and slow-window arrival-rate estimators to catch sudden spikes without destabilising steady traffic. 

## ACKNOWLEDGMENT 

## REFERENCES 

- [1] L. Suresh, M. Canini, S. Schmid, and A. Feldmann, “C3: Cutting tail latency in cloud data stores via adaptive replica selection,” in _12th USENIX Symposium on Networked Systems Design and Implementation (NSDI 15)_ . USENIX Association, 2015, pp. 513–528. [Online]. Available: https://www.usenix.org/conference/nsdi15/technical-sessions/ presentation/suresh 

- [2] J. Dean and L. A. Barroso, “The tail at scale,” _Communications of the ACM_ , vol. 56, no. 2, pp. 74–80, 2013. 

- [3] R. S. Kannan, L. Subramanian, A. Raju, J. Ahn, J. Mars, and L. Tang, “GrandSLAm: Guaranteeing SLAs for jobs in microservices execution frameworks,” in _Proceedings of the Fourteenth EuroSys Conference 2019_ . ACM, 2019, pp. 1–16. 

- [4] X. Wang, A. Khan, J. Wang, A. Gangopadhyay, C. E. Busart, and J. Freeman, “An edge-cloud integrated framework for flexible and dynamic stream analytics,” _Future Generation Computer Systems_ , vol. 137, pp. 323–335, 2022. 

- [5] A. Abouaomar, S. Cherkaoui, Z. Mlika, and A. Kobbane, “Resource provisioning in edge computing for latency sensitive applications,” 2022. [Online]. Available: https://arxiv.org/abs/2201.11837 

- [6] T. Bai, C. Pan, Y. Deng, M. Elkashlan, A. Nallanathan, and L. Hanzo, “Latency minimization for intelligent reflecting surface aided mobile edge computing,” 2019. [Online]. Available: https: //arxiv.org/abs/1910.07990 

- [7] J. Zhang, X. Wang, P. Yuan, H. Dong, P. Zhang, and Z. Tari, “Dependency-aware task offloading based on application hit ratio,” _IEEE Transactions on Services Computing_ , vol. 17, no. 6, pp. 3373–3387, 2024. 

- [8] Redis Ltd., “Redis,” 2026, accessed: May 22, 2026. [Online]. Available: https://redis.io/ 

- [9] H. Zhang, Y. Yang, X. Huang, C. Fang, and P. Zhang, “Ultra-low latency multi-task offloading in mobile edge computing,” _IEEE Access_ , vol. 9, pp. 32 569–32 580, 2021. 

- [10] J. Liu and Q. Zhang, “Offloading schemes in mobile edge computing for ultra-reliable low latency communications,” _IEEE Access_ , vol. 6, pp. 12 825–12 837, 2018. 

- [11] Q. Liang, W. A. Hanafy, A. Ali-Eldin, and P. Shenoy, “Model-driven cluster resource management for AI workloads in edge clouds,” _ACM Transactions on Autonomous and Adaptive Systems_ , vol. 18, no. 1, pp. 1–26, 2023. 

- [12] K. Rao, G. Coviello, W.-P. Hsiung, and S. Chakradhar, “ECO: Edgecloud optimization of 5g applications,” in _2021 IEEE/ACM 21st International Symposium on Cluster, Cloud and Internet Computing (CCGrid)_ . IEEE, 2021, pp. 649–658. 

- [13] R.-H. Hwang, Y.-C. Lai, and Y.-D. Lin, “Queue-length-based offloading for delay sensitive applications in federated cloud-edge-fog systems,” in _2024 IEEE 21st Consumer Communications & Networking Conference (CCNC)_ . IEEE, 2024, pp. 406–411. 

- [14] J. Ahmad, M. S. Hossain, F. A. Awsaf, A. K. M. M. Islam, and S. K. M. Hasan, “Partial offloading schemes for latency and computation sensitive tasks,” in _2022 IEEE Region 10 Symposium (TENSYMP)_ . IEEE, 2022, pp. 1–6. 

- [15] A. Gandhi, P. Dube, A. Karve, A. Kochut, and L. Zhang, “Adaptive, model-driven autoscaling for cloud applications,” in _11th International Conference on Autonomic Computing (ICAC 14)_ . USENIX Association, 2014, pp. 57–64. [Online]. Available: https://www. usenix.org/conference/icac14/technical-sessions/presentation/gandhi 

- [16] A. Verma, L. Pedrosa, M. R. Korupolu, D. Oppenheimer, E. Tune, and J. Wilkes, “Large-scale cluster management at google with Borg,” in _Proceedings of the Tenth European Conference on Computer Systems (EuroSys ’15)_ . ACM, 2015, pp. 1–17. 

- [17] Kubernetes Authors, “Horizontal pod autoscaling,” 2026, last modified: March 15, 2026; accessed: May 22, 2026. [Online]. Available: https://kubernetes.io/docs/concepts/workloads/ autoscaling/horizontal-pod-autoscale/ 

- [18] H. Qiu, S. S. Banerjee, S. Jha, Z. T. Kalbarczyk, and R. K. Iyer, “FIRM: An intelligent fine-grained resource management framework for SLO-oriented microservices,” in _14th USENIX Symposium on Operating Systems Design and Implementation (OSDI 20)_ . USENIX Association, Nov. 2020, pp. 805–825. [Online]. Available: https: //www.usenix.org/conference/osdi20/presentation/qiu 

- [19] Y. Zhang, W. Hua, Z. Zhou, G. E. Suh, and C. Delimitrou, “Sinan: MLbased and QoS-aware resource management for cloud microservices,” in _Proceedings of the 26th ACM International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS ’21)_ . New York, NY, USA: ACM, 2021, pp. 167–181. 

- [20] D. Lo, L. Cheng, R. Govindaraju, P. Ranganathan, and C. Kozyrakis, “Heracles: Improving resource efficiency at scale with flexible finegrained resource control,” in _Proceedings of the 42nd Annual International Symposium on Computer Architecture (ISCA)_ . ACM, 2015, pp. 450–462. 

- [21] A. Dragojevi´c, D. Narayanan, O. Hodson, and M. Castro, “FaRM: Fast remote memory,” in _Proceedings of the 11th USENIX Symposium on Networked Systems Design and Implementation (NSDI 14)_ . USENIX Association, 2014, pp. 401–414. [Online]. Available: https://www. usenix.org/conference/nsdi14/technical-sessions/dragojevi%C4%87 

- [22] B. Chandramouli, G. Prasaad, D. Kossmann, J. Levandoski, J. Hunter, and M. Barnett, “FASTER: A concurrent key-value store with inplace updates,” in _Proceedings of the 2018 International Conference on Management of Data (SIGMOD)_ . ACM, 2018, pp. 275–290. 

- [23] Y. Kang, J. Hauswald, C. Gao, A. Rovinski, T. N. Mudge, J. Mars, and L. Tang, “Neurosurgeon: Collaborative intelligence between the cloud and mobile edge,” in _Proceedings of the 22nd International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS)_ . ACM, 2017, pp. 615–629. 

- [24] V. Nigade, P. Bauszat, H. E. Bal, and L. Wang, “Jellyfish: Timely inference serving for dynamic edge networks,” in _2022 IEEE Real-Time Systems Symposium (RTSS)_ . IEEE, 2022, pp. 277–290. 

- [25] S. Ren, K. He, R. Girshick, and J. Sun, “Faster R-CNN: Towards real-time object detection with region proposal networks,” in _Advances in Neural Information Processing Systems_ , vol. 28, 2015, pp. 91–99. [Online]. Available: https://proceedings.neurips.cc/paper/ 5638-faster-r-cnn-towards-real-time-object-detection-with-region-proposal-networks 

- [26] J. Redmon and A. Farhadi, “YOLOv3: An incremental improvement,” 2018. [Online]. Available: https://arxiv.org/abs/1804.02767 

- [27] C. Szegedy, A. Toshev, and D. Erhan, “Deep neural networks for object detection,” in _Advances in Neural Information Processing Systems_ , vol. 26, 2013, pp. 2553– 2561. [Online]. Available: https://proceedings.neurips.cc/paper/2013/ hash/f7cade80b7cc92b991cf4d2806d6bd78-Abstract.html 

- [28] M. Everingham, L. V. Gool, C. K. I. Williams, J. Winn, and A. Zisserman, “The PASCAL visual object classes (VOC) challenge,” _International Journal of Computer Vision_ , vol. 88, no. 2, pp. 303–338, 2010. 

- [29] J. Huang, V. Rathod, C. Sun, M. Zhu, A. Korattikara, A. Fathi, I. Fischer, Z. Wojna, Y. Song, S. Guadarrama, and K. Murphy, “Speed/accuracy trade-offs for modern convolutional object detectors,” in _Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)_ , 2017, pp. 7310–7318. [Online]. Available: https://openaccess.thecvf.com/content <u>cvpr 2017/</u> html/Huang SpeedAccuracy <u>Trade-Offs</u> for CVPR 2017 <u>paper.html</u> 

- [30] E. Li, L. Zeng, Z. Zhou, and X. Chen, “Edge AI: On-demand accelerating deep neural network inference via edge computing,” _IEEE Transactions on Wireless Communications_ , vol. 19, no. 1, pp. 447–457, 2020. 

- [31] S. Wang, X. Zhang, Y. Zhang, L. Wang, J. Yang, and W. Wang, “A 

- survey on mobile edge networks: Convergence of computing, caching and communications,” _IEEE Access_ , vol. 5, pp. 6757–6779, 2017. 

- [32] N. P. Jouppi, C. Young, N. Patil, D. Patterson, G. Agrawal, R. Bajwa, S. Bates, S. Bhatia, N. Boden, A. Borchers, R. Boyle, P. luc Cantin, C. Chao, C. Clark, J. Coriell, M. Daley, M. Dau, J. Dean, B. Gelb, T. V. Ghaemmaghami, R. Gottipati, W. Gulland, R. Hagmann, C. R. Ho, D. Hogberg, J. Hu, R. Hundt, D. Hurt, J. Ibarz, A. Jaffey, A. Jaworski, A. Kaplan, H. Khaitan, D. Killebrew, A. Koch, N. Kumar, S. Lacy, J. Laudon, J. Law, D. Le, C. Leary, Z. Liu, K. Lucke, A. Lundin, G. MacKean, A. Maggiore, M. Mahony, K. Miller, R. Nagarajan, R. Narayanaswami, R. Ni, K. Nix, T. Norrie, M. Omernick, N. Penukonda, A. Phelps, J. Ross, M. Ross, A. Salek, E. Samadiani, C. Severn, G. Sizikov, M. Snelham, J. Souter, D. Steinberg, A. Swing, M. Tan, G. Thorson, B. Tian, H. Toma, E. Tuttle, V. Vasudevan, R. Walter, W. Wang, E. Wilcox, and D. H. Yoon, “In-datacenter performance analysis of a tensor processing unit,” _SIGARCH Computer Architecture News_ , vol. 45, no. 2, pp. 1–12, Jun. 2017. 

- [33] K.-S. Oh and K. Jung, “GPU implementation of neural networks,” _Pattern Recognition_ , vol. 37, no. 6, pp. 1311–1314, 2004. 

- [34] L. Kleinrock, _Queueing Systems, Volume 1: Theory_ . New York, NY, USA: Wiley-Interscience, 1975. 

- [35] G. Jocher, A. Stoken, J. Borovec, NanoCode012, ChristopherSTAN, L. Changyu, Laughing, tkianai, A. Hogan, lorenzomammana, yxNONG, AlexWang1900, L. Diaconu, Marc, wanghaoyang0106, ml5ah, Doug, F. Ingham, Frederik, Guilhen, Hatovix, J. Poznanski, J. Fang, L. Yu, changyu98, M. Wang, N. Gupta, O. Akhtar, PetrDvoracek, and P. Rai, “ultralytics/yolov5: v3.1 - bug fixes and performance improvements,” 2020. [Online]. Available: https://zenodo.org/records/4154370 

- [36] M. Tan, R. Pang, and Q. V. Le, “EfficientDet: Scalable and efficient object detection,” in _Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)_ , 2020, pp. 10 781–10 790. [Online]. Available: https://arxiv.org/abs/1911.09070 

