---
# --- bibliographic record ---
entry_type: misc
title: "ClusterLess: Deadline-Aware Serverless Workflow Orchestration on Federated Edge Clusters"
authors:
  - "Reza Farahani"
  - "Mario Colosi"
  - "Ilir Murturi"
  - "Stefan Nastic"
  - "Massimo Villari"
  - "Schahram Dustdar"
  - "Radu Prodan"
year: 2026
venue: "arXiv preprint"
volume: ""
issue: ""
pages: ""
publisher: ""
doi: ""
arxiv: "2605.04310"
url: "https://arxiv.org/abs/2605.04310"

# --- archive record ---
source_pdf: clusterless-deadline-edge-orchestration-2026.pdf
source_sha256: 32379b933007a3dc0069e0efde4538915c5a1ff75808d3b104874b255ec3b6e6
pdf_pages: 11
converted: 2026-09-13
record_source: arxiv
key_insight: "Deadline-aware serverless workflow placement on federated K8s edge clusters; measured state only, no predictive model"
first_page: "ClusterLess: Deadline-Aware Serverless Workflow Orchestration on Federated Edge Clusters Reza Farahani∗, Mario Colosi†, Ilir Murturi‡, Stefan Nastic∗, Massimo Villari†, Schahram Dustdar∗, Radu Prodan§"
---
# ClusterLess: Deadline-Aware Serverless Workflow Orchestration on Federated Edge Clusters 

Reza Farahani<sup>_∗_</sup> , Mario Colosi<sup>_†_</sup> , Ilir Murturi<sup>_‡_</sup> , Stefan Nastic<sup>_∗_</sup> , Massimo Villari<sup>_†_</sup> , Schahram Dustdar<sup>_∗_</sup> , Radu Prodan<sup>_§_</sup> 

_∗_ Distributed Systems Group (DSG), TU Wien, Vienna, Austria 

_†_ MIFT Department, University of Messina, Messina, Italy 

_‡_ Department of Mechatronics, University of Prishtina, Prishtina, Kosova 

_§_ Department of Computer Science, University of Innsbruck, Innsbruck, Austria 

**_Abstract_ —The recent convergence of edge computing, serverless execution, and Kubernetes (K8s)-based container orchestration has enabled the processing of application workflows close to data sources. While effective within a single-edge cluster, existing schemes do not generalize to federated multi-edge environments, where multiple workflows execute concurrently under strict end-to-end (E2E) deadline constraints. This paper introduces ClusterLess, a deadline-aware serverless workflow** **_orchestration_ method for federated multi-edge K8s clusters. ClusterLess manages the E2E lifecycle of workflow execution, including dependency analysis, execution-mode selection, and resource-aware placement. To this end, it integrates structured** **_intra-cluster_ orchestration with a leader-selected,** **_supermaster_ –driven** **_inter-cluster coordination_ layer, determining where and how each workflow function should be executed across the federated edge clusters. We implement ClusterLess using OpenFaaS as the serverless execution substrate and Argo for workflow management, and deploy it on a realistic testbed of** **_six_ edge clusters comprising** 64 **heterogeneous edge nodes. Experimental results with concurrent serverless workflows, spanning** 18 **workload configurations across different input sizes and deadline classes, show that ClusterLess reduces workflow completion time by up to** 40 % **, increases deadline satisfaction from below** 50 % **to over** 90 % **, and confines deadline violations to single-digit seconds compared to four baseline methods.** 

**_Index Terms_ —Edge Computing; Serverless Computing; Kubernetes; Workflow; Multi-Cluster Orchestration.** 

## I. INTRODUCTION 

Recent industry analyses predict that over 50 % of critical enterprise applications will run outside centralized public clouds or traditional data centers by 2027, reflecting the accelerating shift toward distributed edge computing [1]. In parallel, serverless computing has become one of the de facto cloud execution models, with production traces reporting billions of function invocations per day on commercial platforms [2], [3]. To support this growth at the edge, Kubernetes (K8s), predominantly employed as the orchestration layer, provides container-based isolation, rapid scaling, and uniform resource management across heterogeneous edge clusters [4], [5]. While effective within a single edge cluster, these mechanisms do not readily generalize to federated multi-edge environments, where application workflows with strict end-to-end (E2E) deadlines must be executed concurrently across clusters with diverse compute capacities and network conditions [6]. In such scenarios, cold starts, resource fragmentation, and 

inter-cluster communication delays can degrade performance, posing challenges to deadline-aware orchestration [7], [8], [9]. 

Serverless workflows, typically expressed as directed acyclic graphs (DAGs), require fine-grained, function-level orchestration that respects dependency order, deadline constraints, and interference from concurrent executions. Misplacing an upstream function can propagate delays across the workflow. for example, placing _f_ 1 in a workflow _f_ 1 _→ f_ 2 _→ f_ 3 on a congested compute instance delays all downstream functions and can violate the E2E deadline despite available downstream resources. Although recent efforts have explored multi-cluster K8s [10], [11], [12], orchestration support for serverless workflows across multiple edge clusters remains limited. Moreover, existing centralized orchestration methods [13] often overlook workflow-level deadlines, dependency structures, and cross-cluster heterogeneity, limiting their effectiveness in real multi-edge environments with dynamic loads and asymmetric computing and networking conditions. 

To address these challenges, we introduce ClusterLess, a deadline-aware serverless workflow orchestration method for federated multi-edge K8s clusters. ClusterLess orchestrates the execution of workflow functions by jointly considering dependency constraints, workflow deadlines, and interference from concurrent workflows. Each cluster runs a local master that performs _intra-cluster orchestration_ ; for each function invocation, this master selects among four execution modes using native K8s and serverless mechanisms: 1) _warm execution_ on edge nodes already hosting an active function instance and offering the lowest completion time; 2) _warm scaling_ when existing deployments are saturated but additional replicas remain deadline-feasible; 3) _cold scaling_ on suitable edge nodes when warm execution and autoscaling risk violating the workflow deadline; 4) _offloading_ when no local execution option can satisfy the workflow deadline. In the offloading mode, control is transferred to _inter-cluster orchestration_ , where one cluster master is dynamically elected as a logically central _super-master_ . The super-master operates alongside its local master responsibilities, aggregates clusterlevel state, and evaluates feasible execution placements across clusters based on communication delay, deployment overhead, queueing state, and execution time, minimizing E2E workflow latency while respecting deadline constraints. It is re-elected 

upon failure or overload, preserving orchestration continuity. 

To our knowledge, ClusterLess is the first orchestration method that jointly incorporates workflow-level deadline guarantees, DAG-aware function scheduling and execution, cross-cluster coordination, and resource heterogeneity into a unified orchestration model for K8s-based edge serverless environments. We implement ClusterLess using OpenFaaS as the serverless execution substrate and Argo for workflow management, and deploy it on a real-world multi-cluster edge testbed comprising six K8s clusters. The testbed consists of 64 heterogeneous edge instances, including Jetson-class devices (Nano, Orin Nano, AGX), Raspberry Pis, and x86-based virtual machines. We evaluate ClusterLess using concurrent serverless workflows with different deadline tightness and input sizes. Experiments show that ClusterLess lowers completion time by up to 40 % and raises deadline satisfaction from below 50 % to over 90 % under heterogeneous workloads. 

## II. RELATED WORK 

Multi-cluster K8s solutions interconnect and coordinate separate clusters, enabling seamless workload placement and migration (e.g., microservices) across heterogeneous infrastructures ranging from the edge to the cloud. Michalke et al. [11] evaluated three multi-cluster connectivity solutions (Submariner, Clusternet, Skupper), demonstrating that intercluster communication overhead significantly affects latency and throughput for distributed microservices. Bachar et al. [12] introduced a multi-cluster optimized service-selection system for geo-distributed K8s deployments that employs a centralized broker with Domain Name System (DNS)-based routing to balance cost and latency, ignoring workflow dependencies and deadline constraints. Park et al. [14] introduced a scheduler for K8s-based multi-replica services that profiles each replica’s performance and dynamically routes requests to the one with the lowest predicted E2E latency. Early Cloud Native Computing Foundation (CNCF) initiatives such as KubeFed provided foundational support for propagating K8s resources across clusters, but focused primarily on resource replication rather than fine-grained orchestration. More recent systems, such as Karmada [15], enable coarse-grained crosscluster service discovery and failover, yet remain agnostic to serverless workflow orchestration and deadline guarantees. 

_State-of-the-art limitations:_ Existing systems address microservice placement and cross-cluster connectivity, yet lack deadline-aware orchestration for serverless workflows. By ignoring deadlines, function dependencies, and inter-cluster latency, they fall short in resource-limited edge environments. 

Several serverless platforms like Knative and Fission leverage K8s primitives for elastic containerized function lifecycle management and resource allocation, but face challenges such as cold-start latency, resource oversubscription, and limited support for workflow-aware or dependency-sensitive orchestration [16]. Lin and Glikson [17] tackled Knative’s coldstart bottleneck by introducing a warm pool of pre-provisioned function containers, reducing response latency for sporadic or latency-sensitive invocations. Cvetkovi´c et al. [18] introduced 

TABLE I: Related work comparison (SL: Serverless; P: Pod; WF: Workflow; MC: Multi-cluster; AT: Autoscaling; ND: New Deployment; DL: Deadline-aware; Intra: Intra-cluster; Inter: Inter-cluster). 



<!-- Start of picture text -->
Work SL ProcessinP WF g MC AT ND DL OrchestrationIntra Inter Evaluation infrastructure<br>[11] ✓ ✓ × ✓ × × × × ✓ 2 k3s clusters, Knative.<br>[12] × ✓ × ✓ × × × × ✓ Simulation and 5 K8s clusters.<br>[13] ✓ ✓ × ✓ × ✓ × × ✓ 2 K8s clusters on OpenStack.<br>[14] × ✓ × × × ✓ × ✓ × Single K8s cluster (5 nodes).<br>[17] ✓ ✓ × × ✓ ✓ × ✓ × Single K8s cluster, Knative.<br>[18] ✓ ✓ × × ✓ ✓ × ✓ × 93-node cluster, Knative.<br>[19] ✓ ✓ × ✓ × ✓ × × ✓ 4 RPis, x64 node, VM, Knative.<br>[20] ✓ ✓ ✓ × ✓ ✓ × ✓ × K8s cluster (5 nodes) and IBM cloud.<br>[21] ✓ ✓ × × ✓ ✓ × ✓ × 10 RPis and 10 servers, OpenWhisk.<br>ClusterLess ✓ ✓ ✓ ✓ ✓ ✓ ✓ ✓ ✓ 64 Jetsons, RPis, VMs, OpenFaaS, Argo.<br><!-- End of picture text -->

a K8s-inspired cluster manager for function scheduling that employs a centralized function scheduler and a lightweight runtime for function invocation throughput, in contrast to traditional layered designs. Simion et al. [19] extended Knative with edge-aware offloading by leveraging latency estimates and location-aware placement, improving throughput for IoT workloads. López et al. [20] proposed Triggerflow, a triggerbased serverless workflow orchestrator for K8s/Knative, but it emphasizes event-driven control-flow extensibility rather than deadline-aware federated multi-edge orchestration. Serenari et al. [21] proposed GreenWhisk, an Apache OpenWhisk-based system evaluated on Raspberry Pi edge clusters, enabling carbon-aware energy-aware function placement. Poggiani et al. [13] proposed live migration of multi-container K8s pods across clusters via container-level checkpointing to preserve state and reduce cold-start overheads, focusing on stateful relocation rather than workflow-level serverless orchestration. 

_State-of-the-art limitations:_ Most existing systems improve per-function scheduling, but operate strictly within single clusters and offer no distributed orchestration across multiple K8s clusters. They also overlook functional dependencies, workflow-level deadlines, and cross-cluster computing and bandwidth constraints, limiting their use for concurrent serverless workflows in multi-cluster edge environments. 

## III. PROBLEM FORMULATION 

## _A. Function and workflow model_ 

We consider a set of _serverless workflows W_ executed at different time intervals. Each workflow _w ∈W_ is modeled as a DAG _Gw_ = ( _Fw, Ew_ ), where _Fw_ denotes the set of workflow functions and _Ew ⊆ Fw × Fw_ denotes dependency edges, such that ( _g, f_ ) _∈ Ew_ implies that function _f_ can start only after _g_ completes. Each workflow _w_ arrives at time _Aw_ and is subject to a strict end-to-end (E2E) deadline _Dw_ , where delays in individual functions may propagate and result in workflow-level deadline violations. Each function _f ∈ Fw_ is characterized by: 1) computational demands, given by _C_<sup>_f_</sup> (CPU-seconds) and _M_<sup>_f_</sup> (bytes of memory); and 2) input and output data sizes ( _X_ in<sup>_f, X_</sup> out<sup>_f_)inMB,whichdetermineinter–</sup> function communication overhead. Multiple workflows may execute concurrently and contend for compute, memory, and network bandwidth resources across federated edge clusters. 

## _B. Cluster model_ 

We consider a set of _N_ federated K8s edge clusters _K_ = _{K_ 1 _, . . . , KN }_ deployed at distinct locations. Each clus- 

ter _Kn ∈K_ comprises: 1) a _local master Mn_ responsible for _intra-cluster_ orchestration decisions, including execution-mode selection (warm execution, warm scaling, cold scaling, or offloading); and 2) a set of _worker nodes Zn_ = _{zn_ 1 _, . . . , zn|Zn|}_ At time _t_ , each worker _zni ∈Zn_ provides available CPU and memory capacities _Cni_ ( _t_ ) and _Mni_ ( _t_ ), and maintains a local execution queue, inducing a queuing delay _Qni_ ( _t_ ) due to concurrent workloads. Let Γ _ni_ ( _t_ ) denote the number of active function instances on worker _zni_ at _t_ , and let _Rni_ be its maximum concurrency capacity. We define the normalized load of cluster _Kn_ at time _t_ as: 



which captures the average utilization of worker-level concurrency capacity and enables load comparison across clusters. 

While each local master independently performs intracluster orchestration, deadline-feasible execution cannot always be guaranteed locally due to resource contention, coldstart overheads, or bursty arrivals. To orchestrate _inter-cluster_ across clusters, the system maintains a _logically centralized_ coordinator, referred to as the _super-master_ , elected among the local masters _{M_ 1 _, . . . , MN }_ . We model the super-master as a time-indexed selection function _SM_ ( _te_ ) _∈K ∪{∅}_ , where _te_ = _e ·_ ∆ _T_ denotes a discrete control epoch and _SM_ ( _te_ ) = _∅_ represents a transient state in which no eligible super-master is available (e.g., due to failures or overload). Each local master _Mn_ periodically emits heartbeat messages to signal its availability. Let _t_<sup>_HB_</sup> _n_ denote the most recent heartbeat received from _Mn_ . Cluster _Kn_ is considered _alive_ at epoch _te_ if: 



where _T_ fail is the failure-detection timeout. Thus, only clusters that satisfy Eq. 3 are eligible to act as super-master: 



where _l_ shows the acceptable super-master overhead. 

## _C. Intra-cluster model_ 

When a function _f ∈ Fw_ becomes _ready_ for execution (i.e., all predecessor functions in _Ew_ have completed), the local master _Mn_ of the cluster _Kn_ to which the request is initially submitted performs an _intra-cluster orchestration_ decision. For each ready function _f_ , the local master selects an execution mode _em_<sup>_f_</sup> from the following set: 

_1) Warm execution:_ serves _f_ by an already active container on worker _zni_ , incurring only queuing delay _Qni_ ( _t_ ) and execution time _Tni_<sup>_f_.</sup> 

_2) Warm scaling:_ spawns an additional replica of _f_ on _zni_ using existing images, incurring an autoscaling delay _WSni_<sup>_f_</sup> before execution. 

_3) Cold scaling:_ deploys _f_ from scratch (image pull, initialization, and container setup) on _zni_ , incurring a coldstart overhead _CSni_<sup>_f_priortoexecution.</sup> 

_4) Offloading:_ forwards the execution request to the supermaster _SM_ ( _t_ ) for placement on a remote cluster. 

If _f_ is assigned locally to worker _zni_ under execution mode _em_<sup>_f_</sup> , its _serving time χ_<sup>_f_</sup> _n_<sup>isgivenby:</sup> 



For dependent functions _g → f ∈ Ew_ , the data-transfer delay _θ_<sup>_gf_</sup> is: 





where _bn,i,j_ ( _t_ ) is the available intra-cluster bandwidth. We define _Sn_<sup>_f_asthestarttimeof</sup><sup>_f_conditionalonexecutingin</sup> _Kn_ defined in Eqs. (6): 



where _Fn_<sup>_g_denotes the completion time of predecessor function</sup> _g_ when executed in _Kn_ , computed by Eq. (7). 



## _D. Inter-cluster model_ 

If the local master _Mn_ cannot place a ready function _f ∈ Fw_ within _Kn_ such that the workflow deadline constraint can still be satisfied, it offloads _f_ to the super-master _SM_ ( _te_ ) at control epoch _te_ . For each candidate cluster _Kn_<sup>_′_</sup> _∈K\{Kn}_ , _SM_ ( _te_ ) calculates the function completion time of _f_ as: 



where _Sn_<sup>_f′_iscomputedviaEq.(6)basedontheremote</sup> cluster state, _δnn′_ is the inter-cluster transfer delay from cluster _Kn_ to _Kn′_ and _χ_<sup>_f_</sup> _n_<sup>_′_istheservingtimeof</sup><sup>_f_incluster</sup><sup>_Kn′_,</sup> computed using the same execution modes as in Eq. (4) based on the remote cluster state. The super-master considers the set of feasible target clusters only when the cluster satisfies the deadline-feasibility constraint: 







The selection of _Kn∗_ constitutes a binding inter-cluster placement decision, and function _f_ is dispatched to cluster _Kn∗_ for execution. If _K_<sup>_f_</sup> = ∅, no deadline-feasible inter-cluster placement exists; function _f_ is declared infeasible, and workflow _w_ is marked as deadline-violated. In addition, when multiple offloading requests are pending at _SM_ ( _te_ ), it processes them according to an earliest-deadline-first policy. 



<!-- Start of picture text -->
Cluster 1 Status Exchange Clustern<br>Master 1 Master n<br>Inter-cluster Orchestration (Active as SM at Epoch t) Inter-cluster Orchestration (Inactive at Epoch t)<br>SM Selector Cluster StateController Inter-clusterScheduling DispatcherOffloading SM Selector Cluster StateController Inter-clusterScheduling DispatcherOffloading<br>Intra-cluster Orchestration (Always Active) Intra-cluster Orchestration (Always Active)<br>Workflows  Workflow Analyzer Intra-cluster Scheduler Deployment Engine Workflow Analyzer Intra-cluster Scheduler Deployment Engine Workflows<br>Resource Monitoring Execution Engine Resource Monitoring Execution Engine<br>Time Estimator Offloading Agent Communication Engine ... Time Estimator Offloading Agent Communication Engine<br>Worker1 Workerm Worker1 Workerm<br>FaaS  Execution Agent FaaS  Execution Agent FaaS  Execution Agent FaaS  Execution Agent<br>Runtime Metric Exporter ... Runtime Metric Exporter Runtime Metric Exporter ... Runtime Metric Exporter<br>Route Agent Route Agent Route Agent Route Agent<br>Function Offloading<br><!-- End of picture text -->

Fig. 1: ClusterLess system architecture. 

## _E. Resource feasibility model_ 

A placement decision for function _f_ on worker _zni_ at time _t_ is _resource-feasible_ only if sufficient compute and memory resources are available on the worker node: 



In addition, data transfers induced by workflow dependencies must be _bandwidth-feasible_ . For a dependency _g → f ∈ Ew_ executed on workers _zni_ and _znj_ within the same cluster _Kn_ , the required data transfer is feasible only if: 



where _bn,i,j_ ( _t_ ) denotes the currently available intra-cluster bandwidth between the two workers at time _t_ . For inter-cluster execution, when _g_ is executed in cluster _Kn_ and _f_ is offloaded to cluster _Kn_<sup>_′_</sup> , the dependency transfer is feasible only if: 



where _bn,n′_ ( _t_ ) denotes the available inter-cluster bandwidth between clusters _Kn_ and _Kn′_ . 

## _F. Completion-time model_ 

For each function _f ∈ Fw_ , the orchestration process (intraor inter-cluster execution) induces a unique execution cluster. Accordingly, the effective completion time of _f_ is: 



The end-to-end (E2E) completion time of workflow _w_ is defined in Eq. (15) and is considered _deadline-feasible_ if it satisfies the workflow deadline. 



Fig. 1 depicts the ClusterLess architecture spanning _N_ federated K8s-based edge clusters. Each cluster consists of a _local master_ responsible for control-plane decisions and a set of _worker nodes_ that execute serverless functions. 

_1) Local master nodes:_ support two logically distinct orchestration paths, corresponding to intra- and inter-cluster decision-making, which jointly enable deadline-aware workflow execution across the federation. 

_a) Intra-cluster orchestration:_ is _always active_ on every master and realizes local workflow execution decisions within a cluster. Upon workflow submission, the _workflow analyzer_ parses the workflow structure and dependency relations, while the _resource monitoring_ module continuously tracks worker-level compute, memory, queuing, and bandwidth conditions. Based on this information, the _time estimator_ derives execution-time estimates for different execution modes (warm execution, warm scaling, cold scaling). The _intra-cluster scheduler_ then determines a feasible worker and execution mode for each ready function. When no such placement exists locally, the _offloading agent_ escalates the function to the inter-cluster orchestration path. The selected decisions are enforced through the _deployment_ , _execution_ , and _communication_ engines, which collectively realize the selected placement, execution mode, and dependency-aware data transfers on worker nodes. 

_b) Inter-cluster orchestration:_ is deployed on every master but _remains inactive_ unless the master is designated as the super-master. When active, it enables orchestration by aggregating cluster-level state and arbitrating offloaded functions. The _SM selector_ maintains cluster liveness and load information, while the _cluster state controller_ constructs a global view of the federation. Using this information, the _inter-cluster scheduler_ evaluates offloaded functions across clusters considering their execution feasibility and deadline urgency, and the _offloading dispatcher_ communicates the resulting placement decisions back to the destination masters. Inter-cluster orchestration relies on two logical communication paths: a _status exchange_ disseminates load and liveness information among masters, and a _function offloading_ transfers execution requests and placement decisions across clusters. 

_2) Worker nodes:_ implement the data-plane components required to execute functions delegated by the local master. Each worker hosts a lightweight serverless _FaaS runtime_ and 

a minimal set of agents, including an _execution agent_ for triggering function execution, a _metric exporter_ for reporting execution and resource statistics, and a _route agent_ for managing dependency-aware data transfers between functions on the appropriate intra- or inter-cluster links. 

## V. CL U S T E RLE SS DECISION-MARKING ALGORITHMS 

## _A. Super-master maintenance_ 

Alg. 1 presents the epoch-based super-master maintenance procedure, ensuring that ClusterLess operates under a responsive, load-aware, and fault-tolerant coordinator for intercluster orchestration. The algorithm takes as input the set of clusters _K_ , the control epoch length ∆ _T_ , the heartbeat failure timeout _T_ fail, and the admissible coordination-load threshold _l_ , and publishes the super-master _SM_ ( _te_ ) at each epoch _te_ . At system startup ( _e_ = 0), each cluster initializes its heartbeat timestamp and computes its normalized load L _n_ ( _t_ 0) based on worker concurrency (lines 2–4). The cluster with the minimum load is deterministically selected as the initial super-master (line 5), yielding a lightweight coordinator at bootstrap. At each subsequent epoch _te_ = _e ·_ ∆ _T_ , clusters update their load estimates if a heartbeat is received during ( _te−_ 1 _, te_ ]; otherwise, the previous value is retained to avoid oscillations under transient reporting delays (lines 6–12). 

Cluster liveness is then evaluated using the timeout condition in Eq. (2) (lines 13–14). The current super-master is validated against the eligibility constraint in Eq. (3); it is invalidated if it is unavailable, not alive, or exceeds the admissible load threshold (line 15). If invalid, the algorithm deterministically re-selects the alive and load-eligible cluster with the minimum normalized load (lines 16–17); if no such cluster exists, no super-master is assigned for the epoch (line 19), deferring inter-cluster coordination to subsequent epochs. Otherwise, the previous super-master is retained unchanged (line 21). At the end of each epoch, the resulting _SM_ ( _te_ ), either newly selected, retained, or empty, is published to the inter-cluster orchestration layer (line 22), enabling continuous, stable, and epoch-consistent decisions. 

## _B. Intra-cluster orchestration_ 

Alg. 2 presents the intra-cluster orchestration procedure executed by the local master _Mn_ when a workflow _w_ is submitted to cluster _Kn_ at time _t_ . The algorithm takes as input the workflow DAG _Gw_ , its arrival time _Aw_ , deadline _Dw_ , and the target cluster _Kn_ , and outputs the local orchestration plan _LOrch_ , specifying for each function _f ∈ Fw_ its execution mode _em_<sup>_f_</sup> , local placement _z_<sup>_f_</sup> (if any), and the corresponding start and completion times ( _Sn_<sup>_f, F_</sup> _n_<sup>_f_). At initialization (line 1),</sup> all functions are marked as local ( _ext_ = 0), assigned the default execution mode _warm execution_ , and left unscheduled with infinite completion time. The algorithm then iteratively refines _LOrch_ while the workflow-level completion time exceeds the deadline, i.e., WFINISH( _LOrch_ ) _> Aw_ + _Dw_ (line 2), where WFINISH() implements Eq. (15), ensuring correctness for arbitrary DAG structures, including parallel terminal branches. In each iteration, IDENTIFYBOTTLENECK( _LOrch_ ) is invoked 

## **Algorithm 1:** Super-master maintenance. 



<!-- Start of picture text -->
Input: K = {K 1 , . . . , KN } , ∆ T  , T fail, l<br>Output: SM ( te )<br>1 e ← 0 t 0 ← 0<br>2 forall Kn ∈K do<br>3 t HB n ← t 0 1 Γ ni ( t 0)<br>4 L n ( t 0) ← �<br>|Zn| zni∈Zn Rni<br>5 SM ( t 0) ← arg Kn min ∈K L n ( t 0)<br>6 for e ← 1 to ∞ do<br>7 te ← e ·  ∆ T<br>8 forall Kn ∈K do<br>9 if t HB n > te− 1 then 1 Γ ni ( te )<br>10 L n ( te ) ← �<br>|Zn| zni∈Zn Rni<br>11 else<br>12 L n ( te ) ← L n ( te− 1)<br>13 forall Kn ∈K do<br>14 Alive n ( te ) ← I� te − t HB n ≤ T fail�<br>15 if SM ( te− 1) = ∅∨ (Alive SM ( te− 1)( te ) =<br>0 ∨ L SM ( te− 1)( te ) > l ) then<br>16 if ∃ Kn ∈K : Alive n ( te ) = 1 ∧ L n ( te ) ≤ l then<br>17 SM ( te ) ← arg Kn∈K :Alive n min( te )=1 ∧ L n ( te ) ≤l L n ( te )<br>18 else<br>19 SM ( te ) ←∅<br>20 else<br>21 SM ( te ) ← SM ( te− 1)<br>22 PUBLISH( SM ( te ))<br><!-- End of picture text -->

(line 3) to extract three components: a committed partial plan _LOrch c_ , a bottleneck function _f_<sup>_bn_</sup> selected among nonoffloaded functions with the largest current completion time, and a pending set _P_ containing all other functions whose execution may be affected by changes to _f_<sup>_bn_</sup> . To ensure progress, functions that have already been evaluated under all execution modes without yielding an improvement are excluded from bottleneck selection in the current refinement cycle; however, a function may be selected again as a bottleneck if updates to predecessor functions reduce its effective completion time. 

The algorithm initializes a control flag _success_ (line 5) to track whether an improving execution-mode update for the bottleneck function can be found. While no improvement is achieved and the bottleneck has not been escalated to offloading (lines 6–8), the execution mode of _f_<sup>_bn_</sup> is deterministically advanced using NEXTMODE() following the ordered policy _warm execution→warm scaling→cold scaling→offloading_ . For each mode, APPLYMODE() evaluates feasibility using the serving-time model in Eq. (4), the dependency constraints in Eqs. (6)–(7), and the resource and bandwidth feasibility conditions in Eqs. (11)–(13). The flag _success_ is set to 1 only if a feasible and improving update is obtained; offloading succeeds only upon acknowledgement from the super-master. If an improvement is found, the updated bottleneck decision is committed to _LOrch_ (lines 9–10). Otherwise, if all execution modes fail to yield a feasible update, the pending set _P_ is restored unchanged (lines 11–13), and the algorithm proceeds to the next iteration without altering prior decisions. 

After committing the bottleneck update, the algorithm orchestrates the remaining pending functions (lines 15–20). For 

**Algorithm 2:** Intra-cluster orchestration by _Mn_ at time _t_ . 

**Algorithm 3:** Inter-cluster orchestration by _SM_ ( _te_ ). 



<!-- Start of picture text -->
Input: w with Gw = ( Fw, Ew ), Aw , Dw , Kn , t<br>Output: LOrch<br>1 LOrch ←{ ( w, f, ext = 0 , z f = ∅, em f = warm exec , Sn f = ∞, F n f =<br>∞ ) | f ∈ Fw}<br>2 while WFINISH( LOrch ) > Aw +  Dw do<br>3 ( LOrch c, f bn , P  ) ← IDENTIFYBOTTLENECK( LOrch )<br>4 LOrch ← LOrch c<br>5 success ← 0<br>6 while ( success = 0) ∧ ( em fbn̸ = offloading ) do<br>7 em fbn ← NEXTMODE( em fbn )<br>8 ( success, fs bn , P  ) ←<br>APPLYMODE( f bn , em fbn , LOrch, P, Kn, t )<br>9 if success = 1 then<br>10 LOrch ← LOrch ∪{fs bn }<br>11 else<br>12 LOrch ← LOrch ∪ P<br>13 continue<br>14 LOrch p ← ∅<br>15 forall fs ∈ P do<br>16 ( w, f, ext, z f , em f , Sn f , F n f ) ← fs<br>17 if ext = 1 then<br>18 continue<br>19 I avail f ← GETAVAIL( f, emf , Kn, t )<br>fs ′ ← FUNCORCH( LOrch ∪ LOrch p, fs, I avail f , Kn, t )<br>20 LOrch p ← LOrch p ∪{fs ′ }<br>21 LOrch ← LOrch ∪ LOrch p<br>22 return LOrch<br><!-- End of picture text -->

each function _fs ∈ P_ that is not marked external, _Mn_ retrieves the set of available execution instances via GETAVAIL() (line 19), restricting evaluation to runnable pods or scalable targets. The function-level orchestration module FUNCORCH() then selects a resource- and bandwidth-feasible placement and computes ( _Sn_<sup>_f, F_</sup> _n_<sup>_f_)accordingtoEqs.(4)–(7)andEqs.(11)–</sup> (13) (line 20). These decisions are merged into _LOrch_ (lines 20–21), completing one refinement step. The process terminates once the workflow deadline is satisfied, and the final plan _LOrch_ is returned (line 22). 

## _C. Inter-cluster orchestration_ 

Alg. 3 presents the inter-cluster orchestration procedure executed by the super-master _SM_ ( _te_ ) at control epoch _te_ for handling the set of offloaded functions _Offload_ ( _te_ ). The algorithm takes as input the set of pending offload requests _Offload_ ( _te_ ) and the federated cluster set _K_ , and outputs the global orchestration plan _GOrch_ ( _te_ ), specifying one destination cluster per offloaded function. At the beginning of the epoch, all offload requests are ordered by earliest-deadlinefirst (EDF) using the workflow deadline _Aw_ + _Dw_ (line 1), prioritizing functions on critical deadline paths. The global decision set _GOrch_ ( _te_ ) is then initialized to empty (line 2). The super-master evaluates all candidate destination clusters for each offload request in EDF order (lines 3–4) for each candidate, computes the dependency-aware earliest start time _Sn_<sup>_f′_basedonpredecessorcompletiontimesandinter-cluster</sup> transfer delays (lines 5–8), followed by the corresponding remote completion time _Fn_<sup>_f′_atepoch</sup><sup>_te_(line9).</sup> 

The algorithm then constructs the feasible-improving set _K_<sup>_f_</sup> (line 10), containing only those clusters that both satisfy the workflow deadline constraint and strictly improve upon the best local completion time _Fn_<sup>_f_.Ifnosuchcluster</sup> 



<!-- Start of picture text -->
Input: te , Offload ( te ) = { ( w, f, Kn, Fn f ) } , K<br>Output: GOrch ( te )<br>1 Offload ( te ) ← argsort( w,f,Kn,Fnf ) ∈Offload ( t e )( Aw +  Dw )<br>2 GOrch ( te ) ← ∅<br>3 forall ( w, f, Kn, Fn f ) ∈ Offload ( te ) do<br>4 forall Kn′ ∈K \ {Kn} do<br>5 if ∄ g → f ∈ Ew then<br>6 Sn f′ ← Aw<br>7 else<br>8 Sn f′ ← g→ max f ∈Ew{Fn g′ +  θ n gf′ }<br>9 Fn f′ ← max {S n f′ , te}  +  δnn′ +  χf n ′<br>10 K f ←<br>� Kn′ ∈K \ {Kn} ��� ( F nf ′ ≤ Aw +  Dw ) ∧ ( F n f′ < F n f ) �<br>11 if K f = ∅ then<br>12 GOrch ( te ) ← GOrch ( te )  ∪{ ( w, f, Kn ) }<br>13 else<br>14 Kn∗ ← arg min n ′<br>Kn′ ∈K f F f<br>15 GOrch ( te ) ← GOrch ( te )  ∪{ ( w, f, Kn∗ ) }<br>16 return GOrch ( te )<br><!-- End of picture text -->

exists, the function is retained at its origin cluster _Kn_ and recorded accordingly in _GOrch_ ( _te_ ) (lines 11–12). Otherwise, the destination cluster that minimizes _Fn_<sup>_f′_is selected (lines 14–</sup> 15). This process is repeated for all offload functions, and _GOrch_ ( _te_ ) is returned at the end of the epoch (line 16). 

## _D. Time complexity_ 

Alg. 1 performs a linear scan over clusters once per epoch, yielding _O_ ( _|K|_ ). Alg. 2 updates the local plan by resolving a single bottleneck per iteration across a bounded mode set, giving _O_ ( _|Fw|_ ) per workflow. Alg. 3 sorts offloaded functions by EDF and evaluates all destination clusters, resulting in _O_ ( _|Offload |_ log _|Offload |_ + _|Offload | · |K|_ ) per epoch. 

## VI. EVALUATION SETUP 

## _A. Multi-cluster edge testbed_ 

We evaluate ClusterLess on a realistic edge testbed comprising six K8s clusters, spanning 50 physical edge devices and 14 edge KVM-virtualized machines. All clusters run Kubernetes 1.32 with containerd 1.7 and are interconnected via Submariner (Globalnet mode), enabling transparent cross-cluster pod addressing, service discovery, and function offloading. Table II summarizes the hardware composition, while Table III details the per-cluster distribution of workers. We employ Argo Workflows 3.6 to orchestrate workflows, where each workflow step corresponds to a containerized OpenFaaS function invoked through HTTPS templates. OpenFaaS acts as the FaaS execution substrate for ClusterLess, providing per-node function runtimes and exposing warm execution, warm scaling, cold scaling modes. All function images are stored in a Harbor registry to ensure consistent versioning and low-latency pulls. Workflow inputs, intermediate artifacts, and final outputs are stored in an S3-compatible MinIO backend used by both Argo and OpenFaaS, guaranteeing storage-consistent, cross-cluster execution and seamless offloading of data-dependent functions. 

TABLE II: Hardware composition of the six-cluster edge testbed. 



<!-- Start of picture text -->
Node type Node class CPU cores RAM GPU cores Count<br>XLarge VM 12 32 GB – 2<br>Intel VMs Large VM 8 32 GB – 2<br>Medium VM 4 24 GB – 6<br>Small VM 2 16 GB – 4<br>RPi 4 4 4 GB – 25<br>RPis RPi 4BRPi 3B+ 42 4 GB1 GB –– 49<br>Jetson Nano (JN) 4 4 GB 128 6<br>Jetsons Jetson Orin Nano (JON) 6 8 GB 1024 2<br>Jetson Orin AGX (JOA) 12 64 GB 2048 2<br>AMD server Physical server 24 32 GB 1536 2<br><!-- End of picture text -->



<!-- Start of picture text -->
Profanity<br>GetInput Merge Censor StoreAudio<br>T2S Conversion Compression<br>(a)<br>Training 1<br>GetInput Dataset Creation Model Selection Evaluation<br>Training 2<br>(b)<br><!-- End of picture text -->

Fig. 2: Case study serverless workflows. 

TABLE III: Summary of the six-cluster edge testbed. 



<!-- Start of picture text -->
Total Total Workers<br>Cluster# Master CPU Memory (GB) XLVMsL M S 4BRPis4 3B+ JN JetsonsJON JOA<br>C 1 AMD server 82 210 – – 2 2 1 3 2 2 1 1<br>C 2 AMD server 76 202 – – 2 2 1 3 2 2 – 1<br>C 3 Large VM 54 98 – – 1 – 1 6 2 1 1 –<br>C 4 Large VM 36 80 – – 1 – 1 4 – 1 – –<br>C 5 XLarge VM 34 51 – – – – – 4 3 – – –<br>C 6 XLarge VM 28 48 – – – – – 4 – – – –<br><!-- End of picture text -->

We emulate time-varying network conditions using six independent 4G LTE bandwidth traces [22], enforced via Linux traffic control with wondershaper. Each cluster is assigned a distinct trace, and worker-level traces are phaseshifted to avoid synchronized bandwidth fluctuations. The imposed bandwidth limits uniformly affect both inter-cluster control traffic (e.g., heartbeats and state exchange) and dataplane transfers, ensuring consistent and realistic network dynamics. We collect system telemetry using Prometheus, cAdvisor, and scripts, providing fine-grained metrics on resource utilization and function lifecycle that ClusterLess uses for monitoring during experiments. 

## _B. Case-study serverless workflows_ 

We reimplemented two serverless applications from prior open-source systems: a _text-to-speech censoring (T2SC)_ [23] and a _regression-model training_ (RT) [24]. We containerized both workflows and made them compatible with OpenFaaS and Argo, enabling automated DAG execution, artifact propagation, and seamless integration with ClusterLess intraand inter-cluster orchestration schemes. Each workflow is evaluated under three input sizes ( _small_ , _medium_ , _large_ ) and three deadline classes ( _strict_ , _moderate_ , _lenient_ ), producing 18 workflow instances per experiment. 

_1) Text-to-Speech Censoring (T2SC):_ transforms input text into speech while detecting and censoring profanities. It features an eight-function DAG with a mixture of parallelism and sequential audio-processing steps (Fig. 2 (a)): (a) _GetInput_ receives the input text and normalizes it for downstream processing; (b) _T2S_ generates a raw speech waveform from the text; (c) _Conversion_ transforms the audio to the target format (e.g., sample rate, codec); (d) _Compression_ reduces the audio stream size before distribution; (e) _Profanity_ runs in parallel with speech generation, detecting profane tokens in the input text; (f) _Merge_ joins the compressed audio with the profanity annotations to build a time-aligned censoring map; (g) _Censor_ applies muting or beep overlays at profanity locations; (h) _StoreAudio_ persists the final censored audio file to the object store. The parallel _text2speech_ / _profanity_ branch and subsequent merge–censor chain create a critical path 

dominated by processing-intensive audio processing, exposing ClusterLess ability to coordinate concurrent branches and offload heavy functions under tight E2E deadlines. 

_2) Regression Tuning (RT):_ performs E2E regression model selection on a structured dataset. The workflow follows a branched DAG of six functions (Fig. 2 (b)): (a) _GetInput_ receives the raw dataset and prepares it for processing; (b) _Dataset Creation_ parses, cleans, and partitions the data; (c) _Training 1_ and (d) _Training 2_ train two regression models with distinct CPU and memory footprints; (e) _Model Selection_ compares model accuracy and selects the superior model; (f) _Evaluation_ validates the chosen model on a held-out test set. The parallel training stage creates a fork–join structure that stresses resource allocation, while the final selection–evaluation sequence introduces a delay-sensitive path. 

## _C. Baseline methods_ 

Since no existing serverless workflow orchestration system jointly supports 1) explicit separation between intra- and inter– cluster orchestration and 2) super-master–based coordination across federated clusters, we compare ClusterLess (CLU) against four baselines that reflect common design choices in serverless and multi-cluster workflow execution. 

_1) NKS (Native K8s):_ represents the standard K8s–Argo execution model, where each workflow function is deployed as a pod and orchestrated independently using default scoring and bin-packing policies. No workflow-level deadline awareness, dependency-aware start-time analysis, execution-mode selection, or inter-cluster orchestration is supported; all functions execute in the submission cluster. Autoscaling relies on the Horizontal Pod Autoscaler, which we configure to follow OpenFaaS-style scaling by comparing the number of active requests against a target concurrency per instance. 

_2) CLI:_ isolates ClusterLess _intra-cluster orchestration_ , enabling dependency-aware earliest-start analysis, resource and bandwidth feasibility checks, and execution-mode selection within a single cluster. However, inter-cluster orchestration is disabled, i.e., if a function cannot be placed locally in a deadline-feasible manner, it is forced to execute on the same cluster, potentially violating the deadline. 

_3) RRX:_ extends CLI with deterministic inter-cluster offloading, assigning offloaded functions to clusters in a fixed round-robin order without deadline or load awareness. 

_4) RNX:_ augments CLI with inter-cluster offloading by assigning each workflow category (type, payload size, deadline class) to a fixed randomly selected remote cluster. Like RRX, it ignores deadlines and load awareness. 



<!-- Start of picture text -->
Payload Size Deadline Strictness Payload Size Deadline Strictness<br>Small Medium Large Lenient Moderate Strict Small Medium Large Lenient Moderate Strict<br>Uniform Skewed Dynamic<br>C1 t2scrt<br>C2 t2scrt<br>C3 t2scrt<br>C4 t2scrt<br>C5 t2scrt<br>C6 t2scrt<br>0 25 50 75 0 25 50 75 400 425 450 475 500<br>Uniform Skewed Dynamic Uniform Skewed Dynamic Request Arrival Time (s)<br>(a) Request size and deadline class distribution per cluster. (b) Workflow arrival times per cluster.<br>Request Distribution (%) C1 C2 C3 C4 C5 C6 C1 C2 C3 C4 C5 C6 C1 C2 C3 C4 C5 C6 C1 C2 C3 C4 C5 C6 C1 C2 C3 C4 C5 C6 C1 C2 C3 C4 C5 C6<br><!-- End of picture text -->

Fig. 3: Workload composition and temporal arrival behavior across clusters for different arrival rates. 

## _D. Experimental design_ 

We implemented all ClusterLess components and algorithms in Python 3.12, interacting with the K8s API. 

_1) Orchestration parameters:_ We fix the control epoch to ∆ _T_ = 1 s, the heartbeat timeout to _T_ fail = 5 s, and the admissible load threshold to _l_ = 0 _._ 75. 

_2) Concurrency limits and resource capacities:_ For each worker _zni_ , we set the concurrency capacity _Rni_ proportional to its physical CPU core count, enforcing at most one nonpreemptive function per core. The normalized cluster loads L _n_ ( _t_ ) in Eq. (1) and feasibility checks in Eqs. (11)–(13) use the instantaneous computational and bandwidth measurements exported by Prometheus/cAdvisor. Execution modes, warm execution, warm scaling, and cold scaling, are implemented through a custom autoscaling and container-lifecycle controller, designed to replicate OpenFaaS-style behavior while allowing explicit control over replica creation, cold-start delays, and concurrency limits on each worker node. 

_3) Workflow instances:_ We evaluate all size–deadline combinations defined by the workflow templates, resulting in 18 workload configurations. For the _T2SC_ workflow, input sizes are _small_ (500 characters), _medium_ (1250 characters), and _large_ (3750 characters), with deadline classes _lenient_ , _moderate_ , and _strict_ specified as (130 _,_ 180 _,_ 150), (100 _,_ 130 _,_ 180), and (70 _,_ 90 _,_ 110), respectively, where each tuple corresponds to (small, medium, large). For the _RT_ workflow, dataset sizes are _small_ (25 000), _medium_ (100 000), and _large_ (250 000) samples, combined with _lenient_ (120 _,_ 180 _,_ 250), _moderate_ (100 _,_ 150 _,_ 200), and _strict_ (80 _,_ 110 _,_ 150) deadlines. 

_4) Requests arrival model:_ Workflow requests are generated by first selecting a concrete workflow instance and then assigning an arrival time. Workflow instances are drawn from a _Zipf distribution_ [25] over the _K_ = 18 size–deadline combinations, with selection probability of _i_<sup>_th_</sup> instance _P_ ( _i_ ) = 1 _<u>/i</u>_<sup>_α_</sup> <u>�</u> _Kj_ =1<sup>1</sup><sup>_/jα, α_= 0</sup><sup>_._75. Workflow request arrivals follow</sup> a _Poisson_ process. We evaluate three arrival regimes by controlling the arrival rate _λ_ over time: a _uniform load_ applies a fixed and identical arrival rate _λ_ = 0 _._ 33 across all clusters; b _skewed load_ assigns heterogeneous but fixed arrival rates ( _λ ∈{_ 0 _._ 1 _,_ 0 _._ 05 _,_ 0 _._ 55 _,_ 0 _._ 5 _,_ 0 _._ 4 _,_ 0 _._ 4 _}_ ) to have persistent spatial load imbalance; and c _dynamic load_ , models temporal variations where _λ_ evolves over time, starting from the uniform regime and transitioning to a high-load configuration at pre- 

defined time points. The maximum arrival rate is empirically measured and set to 2 based on the highest stable rate observed on the federated testbed. 

## VII. EVALUATION RESULTS 

This section compares ClusterLess ( _CLU_ ) with baselines, reporting average results and standard deviations. 

## _A. Workload analysis_ 

Fig. 3 summarizes the workload composition and temporal arrival behavior across the six clusters. Fig. 3a shows that the request mix is intentionally controlled and consistent across clusters and arrival regimes: the proportions of payload sizes (small/medium/large) and deadline classes (strict/moderate/lenient) remain stable under different loads. This design isolates the impact of orchestration decisions, such as queueing, execution-mode selection, and offloading, from variations in workload difficulty. Fig. 3b depicts workflow arrival times per cluster. Under the _uniform_ regime, arrivals are evenly distributed across clusters over the shown early execution window, yielding balanced concurrency. The _skewed_ regime introduces persistent spatial imbalance, with a subset of clusters receiving a disproportionate share of arrivals. The _dynamic_ regime shows a later execution window ( _t ∈_ [400 _,_ 500] s) where arrivals become bursty and temporally correlated across clusters, creating short periods of overlapping submissions. This spatial–temporal variability increases instantaneous contention at dependency-constrained stages and thus stresses inter-cluster coordination and deadline-feasible offloading under non-stationary demand. 

## _B. Load-aware super-master analysis_ 

Fig. 4 traces the evolution of orchestration behavior over a 400 s interval as the load on cluster _C_ 1 increases. The shaded area reports the normalized cluster load, while markers show the decision latency of _intra-cluster_ and _inter-cluster_ orchestration. In the initial phase ( _t <_ vertical dashed line), the master of _C_ 1 holds the super-master role and thus performs both local intra-cluster and inter-cluster orchestration. As the arrival rate to _C_ 1 increases (from 0 _._ 4 to 0 _._ 8), its normalized load rises steadily, reflecting increasing local concurrency and queueing pressure. Throughout this phase, intra-cluster orchestration latency on _C_ 1 remains low and stable, while inter-cluster orchestration incurs higher, but bounded, latency due to its global coordination scope. 



<!-- Start of picture text -->
C1 C2<br>1.0<br>Load<br>0.8 Intra Orchestration Inter Orchestration 10 2<br>0.6<br>10 0<br>0.4<br>0.2 10 −2<br>0.0<br>0 100 200 300 400 0 100 200 300 400<br>Time (s) Time (s)<br>SM Change SM Change<br>Normalized Load<br>Orchestration Latency (ms)<br><!-- End of picture text -->

Fig. 4: Super-master behavior under increasing cluster load. 



<!-- Start of picture text -->
NKS CLI RNX RRX CLU<br>300<br>240<br>180<br>120<br>60<br>0<br>rt t2sc rt t2sc rt t2sc<br>Uniform Skewed Dynamic<br>Average<br>Completion Time (s)<br><!-- End of picture text -->

Fig. 5: Average workflow completion time across all clusters. 

When the load of _C_ 1 reaches the admissible threshold ( _l_ = 0 _._ 75; vertical dashed line), continuing inter-cluster orchestration on the same master would directly compete with local orchestration for control-plane resources. From this point onward, the super-master role is handled by the master of _C_ 2, while _C_ 1 continues exclusively with intra-cluster orchestration. Consequently, inter-cluster orchestration activity disappears from _C_ 1, and its intra-cluster scheduling latency remains unchanged despite sustained workload. This behavior demonstrates that ClusterLess confines global coordination to clusters with sufficient capacity headroom, preventing intercluster orchestration from amplifying contention and preserving stable intra-cluster orchestration under increasing load. 

## _C. Completion time analysis_ 

Fig. 6 reports the average workflow completion time per cluster for RT and T2SC workflows under the three arrival regimes, while Fig. 5 summarizes the corresponding behavior across all clusters. Across all regimes, _CLU_ achieves the lowest (or tied-lowest) completion time and the smallest variability, indicating robust orchestration under both spatial and temporal load heterogeneity. Under the _uniform_ load, arrivals are evenly distributed and completion times remain bounded. _NKS_ yields the highest completion times due to the lack of dependency-aware orchestration, execution-mode selection, and offloading, which amplifies queuing along workflow critical paths. _CLI_ improves over _NKS_ through modeaware local orchestration but remains constrained under local saturation. _RNX_ and _RRX_ further reduce completion time by exporting load, yet uninformed target selection introduces unnecessary remote queueing. In contrast, _CLU_ achieves the lowest completion times by combining mode-aware intracluster execution with deadline-feasible inter-cluster placement, reducing RT completion time by 15 %–21 % relative to _RNX_ / _RRX_ and by about 10 % for T2SC (Fig. 5). The per-cluster results (Fig. 6) show that these gains are most pronounced on resource-constrained clusters ( _C_ 5– _C_ 6). 

Under the _skewed_ load with persistent spatial imbalance, performance gaps widen markedly. _NKS_ exhibits the highest completion times in hotspot clusters (e.g., _C_ 4– _C_ 6), while _CLI_ improves local execution but remains constrained by the lack of inter-cluster load redistribution. _RNX_ and _RRX_ partially alleviate local pressure, yet uninformed target selection results in elevated completion times. In contrast, _CLU_ maintains consistently lower RT completion times of about 105 s across clusters, yielding improvements of roughly 30 % over _RRX_ and 

40 % over _RNX_ . Under temporal load variations (i.e., _dynamic_ regime), _NKS_ , _RNX_ , and _RRX_ exhibit elevated completion times during burst phases, while _CLI_ stabilizes local execution but remains affected by transient saturation. Fig. 5 shows that _CLU_ achieves the lowest completion times, improving RT by about 21 %–24 % over _RNX_ and _RRX_ and T2SC by roughly 22 %–30 %. The per-cluster results in Fig. 6 further show reduced variance across clusters, indicating that _CLU_ absorbs bursty arrivals through mode-aware intra-cluster orchestration combined with deadline-aware inter-cluster redistribution. 

## _D. Deadline violation analysis_ 

Fig. 7a reports deadline satisfaction rates across arrival regimes. Under the _uniform_ regime, _CLU_ achieves the highest satisfaction (92 _._ 3 %), outperforming _RRX_ (77 _._ 7 %), _RNX_ (73 _._ 1 %), and _CLI_ (73 _._ 7 %), while _NKS_ meets only 37 _._ 7 % of deadlines. The gap reflects fundamental design differences, i.e., _NKS_ suffers from unbounded queueing, _CLI_ is constrained by local capacity, and _RNX_ and _RRX_ incur inefficient remote queueing due to uninformed offloading. In contrast, _CLU_ jointly optimizes execution mode and offloading decisions under deadline feasibility, preserving high satisfaction even at moderate load. Under the _skewed_ regime, persistent hotspots amplify these effects. As shown in Fig. 7a, satisfaction drops below 50 % for _CLI_ , _RNX_ , and _RRX_ , whereas _CLU_ sustains 83 _._ 4 %. Fig. 8a explains this gap; for _strict_ deadlines under _skewed_ regime, _CLU_ satisfies 74 _._ 5 % of workflows, compared to 35 _._ 8 % for _CLI_ and 18 _._ 2 % for _NKS_ . Deadline-aware intercluster selection enables _CLU_ to relocate only those functions whose end-to-end completion can still meet constraints, preventing deadline loss in overloaded clusters. The _dynamic_ regime further stresses temporal adaptability. Fig. 7a shows that satisfaction for _RNX_ and _RRX_ falls below 83 % during burst phases, while _CLU_ reaches 96 _._ 4 %. 

Fig. 7b quantifies violation severity. _NKS_ exhibits the longest violations, frequently exceeding 200 s under _skewed_ load due to cascading queue delays along workflow dependencies. _CLI_ , _RNX_ , and _RRX_ reduce violation duration but still incur delays on the order of tens of seconds. In contrast, _CLU_ consistently limits violation duration to single-digit seconds, indicating that even when deadlines are missed, violations remain tightly bounded. Finally, Fig. 8b conditions satisfaction on payload size. Under _skewed_ load, large-payload workflows achieve below 30 % satisfaction for all baselines, while _CLU_ maintains 71 %, showing that _CLU_ ’s deadline-aware policy 



<!-- Start of picture text -->
NKS CLI RNX RRX CLU<br>C1 C2 C1 C2 C1 C2<br>200160 10080 250200<br>120 60 150<br>80 40 100<br>40 20 50<br>0 0 0<br>rt t2sc rt t2sc rt t2sc rt t2sc rt t2sc rt t2sc<br>C3 C4 C3 C4 C3 C4<br>250200150100 320240160 250200150100<br>50 80 50<br>0 0 0<br>rt t2sc rt t2sc rt t2sc rt t2sc rt t2sc rt t2sc<br>C5 C6 C5 C6 C5 C6<br>500 750<br>400300 600450 400320240<br>200 300 160<br>100 150 80<br>0 0 0<br>rt t2sc rt t2sc rt t2sc rt t2sc rt t2sc rt t2sc<br>(a) Uniform. (b) Skewed. (c) Dynamic.<br>Fig. 6: Average workflow completion time per cluster under different arrival regimes.<br>NKS CLI RNX RRX CLU<br>Deadline Met Deadline Missed Uniform<br>100<br>75 Skewed<br>50<br>25<br>Dynamic<br>0 CLU<br>NKS CLI RNX RRX CLU NKS CLI RNX RRX CLU NKS CLI RNX RRX CLU<br>50 100 150 200 250<br>Uniform Skewed Dynamic Deadline Violation Time (s)<br>(a) Deadline satisfaction rate. (b) Violation duration.<br>Average Completion Time (s) Average Completion Time (s) Average Completion Time (s)<br>73.7 73.1 77.7 92.3 83.4 81.2 81.7 82.4 96.4<br>Requests (%) 37.7 25.5 43.3 48.7 49.9 39.0<br><!-- End of picture text -->

Fig. 7: Deadline violation behavior across strategies and arrival rates. 

explicitly accounts for both execution and inter-cluster transfer costs, which becomes critical as payload size increases. 

## _E. Offloading behavior and execution mode analysis_ 

Fig. 9a quantifies how offloading-based strategies respond to increasing arrival pressure. Under the _uniform_ regime, most workflows are executed locally, but clear differences emerge: _RNX_ and _RRX_ execute about 81 % of workflows internally, whereas ClusterLess executes 86 _._ 6 % locally, offloading selectively only when needed. Under the _skewed_ regime, offloading becomes essential. _RNX_ and _RRX_ offload aggressively yet inconsistently, retaining only 65 _._ 1 % and 64 _._ 2 % of workflows locally, respectively. In contrast, ClusterLess maintains a higher internal execution share (76 _._ 2 %), indicating deadline-aware, targeted, and stable offloading decisions. Under the _dynamic_ regime, ClusterLess further increases local execution to 94 _._ 4 %, reflecting its ability to absorb bursts through coordinated execution rather than reactive spillover. Fig. 9b reports the execution-mode distribution of ClusterLess across clusters and regimes. Warm execution remains dominant, ranging from 65 _._ 0 % to 86 _._ 1 % under the _uniform_ regime, from 67 _._ 8 % to 99 _._ 5 % under _skewed_ load, and from 74 _._ 7 % to 96 _._ 3 % under the _dynamic_ regime. Warm scaling stays bounded, peaking at 19 _._ 6 % ( _uniform_ ), 20 _._ 1 % ( _skewed_ ), and 20 _._ 1 % (dynamic). Cold scaling starts are generally limited but become noticeable on the most constrained cluster: up to 15 _._ 3 % in the _uniform_ regime and 12 _._ 1 % in the _skewed_ regime (both on _C_ 6), while remaining below 5 _._ 7 % in the _dynamic_ regime. 

## _F. CPU utilization analysis_ 

Fig. 10 shows per-cluster CPU utilization over time under different arrival regimes. Under the _uniform_ and _skewed_ regimes, all strategies exhibit a similar ramp-up followed by steady operation on most clusters, indicating that resource usage is primarily driven by sustained workload intensity rather than orchestration choices. Under the _dynamic_ load, clearer differences emerge. CPU utilization becomes uneven across clusters, reflecting the combined effect of bursty arrivals and inter-cluster execution decisions. _CLU_ shows higher utilization on some clusters (i.e., _C_ 1– _C_ 2) while maintaining noticeably lower utilization on others (i.e., _C_ 3– _C_ 6), indicating that execution pressure is redistributed across the federation rather than remaining locally concentrated. In contrast, _NKS_ , _RNX_ , and _RRX_ exhibit more uniformly elevated utilization across clusters, consistent with limited or uninformed load redistribution under _dynamic_ demand. 

## VIII. CONCLUSION 

This paper presented ClusterLess, a deadlineaware serverless workflow orchestration framework for federated multi-edge Kubernetes clusters. ClusterLess combines mode-aware intra-cluster orchestration with supermaster–based inter-cluster coordination, accounting for DAG dependencies, workflow deadlines, and heterogeneous compute and network conditions. We implemented ClusterLess on six realistic edge clusters using OpenFaaS and Argo and evaluated it with two real workflows and 18 



<!-- Start of picture text -->
L = Lenient M = Moderate S = Strict S = Small M = Medium L = Large<br>100 100<br>NKS 54.1 44.8 25.6 39.7 27.4 18.2 57.4 43.9 27.3 NKS 52.2 39.1 23.8 33.8 27.8 16.4 47.4 42.8 28.6<br>CLI 81.6 74.7 69.4 60.2 43.4 35.8 87.6 85.5 75.6 CLI 78.4 76.6 67.1 54.7 48.0 29.9 86.6 86.4 72.1<br>RNX 88.3 80.2 61.7 69.5 55.8 35.6 95.6 87.5 71.7 50 RNX 89.2 77.7 55.2 67.3 54.4 28.5 93.5 85.1 68.6 50<br>RRX 94.6 84.8 65.5 71.9 58.2 35.5 91.6 91.7 72.6 RRX 92.0 82.3 61.3 71.6 54.0 28.4 93.8 85.0 70.4<br>CLU 97.3 95.3 88.1 93.7 91.1 74.5 99.1 98.2 94.1 CLU 96.6 95.7 85.6 92.8 88.7 71.0 98.6 97.5 93.9<br>0 0<br>L M S L M S L M S S M L S M L S M L<br>Uniform Skewed Dynamic Uniform Skewed Dynamic<br>Deadline Met (%) Deadline Met (%)<br><!-- End of picture text -->

- (a) Deadline satisfaction by deadline strictness. 

- (b) Deadline satisfaction by payload size. 

Fig. 8: Deadline satisfaction across strategies and arrival rates under different workload constraints. 



<!-- Start of picture text -->
Internal Offloaded<br>100<br>50<br>0<br>RNX RRX CLU RNX RRX CLU RNX RRX CLU<br>Uniform Skewed Dynamic<br>(a) Local vs. offloaded function execution.<br>81.3 81.9 86.6 65.1 64.2 76.2 86.9 87.6 94.4<br>Requests (%)<br><!-- End of picture text -->



<!-- Start of picture text -->
WE = Warm Execution WS = Warm Scaling CS = Cold Scaling<br>C1 83.6 11.9 4.5 94.5 3.8 1.7 74.7 20.1 5.2 100<br>C2 86.1 9.8 4.1 99.5 0.0 0.5 75.3 19.0 5.7<br>C3 81.8 12.5 5.7 78.2 15.0 6.8 90.4 7.5 2.1<br>C4 80.9 11.6 7.4 79.5 12.3 8.2 93.4 4.9 1.6 50<br>C5 76.4 16.2 7.4 76.8 15.7 7.4 87.3 9.6 3.0<br>C6 65.0 19.6 15.3 67.8 20.1 12.1 96.3 1.9 1.9<br>0<br>WE WS CS WE WS CS WE WS CS<br>Uniform Skewed Dynamic<br>Mode<br>Distribution (%)<br><!-- End of picture text -->

- (b) Execution-mode distribution of ClusterLess. 

Fig. 9: Offloading behavior and execution-mode selection under different arrival regimes. 



<!-- Start of picture text -->
NKS CLI RNX RRX CLU<br>Uniform Skewed Dynamic<br>50 C1<br>0<br>50 C2<br>0<br>50 C3<br>0<br>50 C4<br>0<br>50 C5<br>0<br>50 C6<br>0<br>0 250 0 250 0 250<br>Time (s)<br>CPU Utilization (%)<br><!-- End of picture text -->

Fig. 10: Per-cluster CPU utilization in different methods. 

- [8] H. Shafiei _et al._ , “Serverless Computing: A Survey of Opportunities, Challenges, and Applications,” _ACM Computing Surveys_ , 2022. 

- [9] S. S. Gill _et al._ , “Modern Computing: Vision and Challenges,” _Telematics and Informatics Reports_ , 2024. 

- [10] R. Farahani _et al._ , “Heftless: A Bi-Objective Serverless Workflow Batch Orchestration on the Computing Continuum,” in _IEEE Intl. Conf. on Cluster Computing_ , IEEE, 2024. 

- [11] M. Michalke _et al._ , “Evaluating the Impact of Inter-cluster Communications in Edge Computing,” in _IEEE Network Operations and Management Symp._ , IEEE, 2025. 

- [12] D. Bachar _et al._ , “Optimizing Service Selection and Load Balancing in Multi-Cluster Microservice Systems with MCOSS,” in _2023 IFIP Networking Conf._ , IEEE, 2023. 

- [13] L. Poggiani _et al._ , “Live Migration of Multi-Container Kubernetes Pods in Multi-Cluster Serverless Edge Systems,” in _Proc. of the 1st Workshop on Serverless at the Edge_ , 2024. 

- [14] H. Park _et al._ , “HEART: Heterogeneous-Aware Traffic Allocation in Multi-Replica Deployments on Kubernetes,” in _2025 IEEE 18th Intl. Conf. on Cloud Computing_ , IEEE, 2025. 

- [15] “Karmada.” Accessed: 2025-01-10. 

workload configurations. Results show that ClusterLess reduces workflow completion time and deadline violations compared to four baselines. Future work will explore multi-objective and learning-based orchestration. 

## REFERENCES 

- [1] “Gartner.” https://www.gartner.com/en/newsroom/press-releases/2023-1 0-30-gartner-says-50-percent-of-critical-enterprise-applications-will-r eside-outside-of-centralized-public-cloud-locations-through-2027. 

- [2] A. Joosen _et al._ , “How Does it Function? Characterizing Long-Term Trends in Production Serverless Workloads,” in _Proc. of the 2023 ACM Symp. on Cloud Computing_ , 2023. 

- [3] R. Farahani _et al._ , “Serverless Workflow Management on the Computing Continuum: A Mini-Survey,” in _15th ACM/SPEC Intl. Conf. on Performance Engineering_ , 2024. 

- [4] S. K. Mondal _et al._ , “Kubernetes in IT Administration and Serverless Computing: An Empirical Study and Research Challenges,” _The Journal of Supercomputing_ , 2022. 

- [5] M. S. Aslanpour _et al._ , “FaasHouse: Sustainable Serverless Edge Computing through Energy-Aware Resource Scheduling,” _IEEE Tran. on Services Computing_ , 2024. 

- [6] C. Carrión, “Kubernetes Scheduling: Taxonomy, Ongoing Issues and Challenges,” _ACM Computing Surveys_ , 2022. 

- [7] R. Farahani and R. Prodan, “EnergyLess: An Energy-Aware Serverless Workflow Batch Orchestration on the Computing Continuum,” in _IEEE Intl. Conf. on Cloud Computing_ , IEEE, 2025. 

- [16] D. Balla _et al._ , “Open Source FaaS Performance Aspects,” in _2020 43rd Intl. Conf. on Telecommunications and Signal Processing_ , IEEE, 2020. 

- [17] P.-M. Lin and A. Glikson, “Mitigating Cold Starts in Serverless Platforms: A Pool-based Approach,” _arXiv preprint arXiv:1903.12221_ , 2019. 

- [18] L. Cvetkovi´c _et al._ , “Dirigent: Lightweight Serverless Orchestration,” in _Proc. of the ACM SIGOPS Symp. on Operating Systems Principles_ , 2024. 

- [19] E. Simion _et al._ , “Towards Seamless Serverless Computing Across an Edge-Cloud Continuum,” in _Proce. of the IEEE/ACM 16th Intl. Conf. on Utility and Cloud Computing_ , 2023. 

- [20] P. G. López _et al._ , “Triggerflow: Trigger-based Orchestration of Serverless Workflows,” in _Proc. of the 14th ACM Intl. Conf. on Distributed and Event-Based Systems_ , 2020. 

- [21] J. Serenari _et al._ , “GreenWhisk: Emission-Aware Computing for Serverless Platform,” in _IEEE Intl. Conf. on Cloud Engineering_ , IEEE, 2024. 

- [22] D. Raca _et al._ , “Beyond Throughput: A 4G LTE Dataset with Channel and Context Metrics,” in _Proc. of the 9th ACM Multimedia Systems Conference_ , 2018. Available at: https://zenodo.org/records/1219679. 

- [23] S. Eismann _et al._ , “Predicting the Costs of Serverless Workflows,” in _Proc. of the 2020 ACM/SPEC International Conf. on Performance Engineering_ . Available at: https://github.com/jacopotagliabue/no-ops-m achine-learning, year = 2020. 

- [24] “Regression Tuning Workflow.” Available at https://github.com/jacopot agliabue/no-ops-machine-learning. 

- [25] L. Cherkasova and M. Gupta, “Analysis of Enterprise Media Server Workloads: Access Patterns, Locality, Content Evolution, and Rates of Change,” _IEEE/ACM Trans. on Networking_ , 2004. 

