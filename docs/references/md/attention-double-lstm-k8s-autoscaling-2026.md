---
# --- bibliographic record ---
entry_type: misc
title: "Mitigating Temporal Blindness in Kubernetes Autoscaling: An Attention-Double-LSTM Framework"
authors:
  - "Faraz Shaikh"
  - "Gianluca Reali"
  - "Mauro Femminella"
year: 2026
venue: "arXiv preprint"
volume: ""
issue: ""
pages: ""
publisher: ""
doi: ""
arxiv: "2603.28790"
url: "https://arxiv.org/abs/2603.28790"

# --- archive record ---
source_pdf: attention-double-lstm-k8s-autoscaling-2026.pdf
source_sha256: 7929aa57e2ad6d92b588dfca1cac67e70bf03373c7a1354d9818508063f4b4fa
pdf_pages: 12
converted: 2026-09-13
record_source: arxiv
key_insight: "Extends prior DRe-SCale PPO; baselines HPA, DDQN, single-LSTM ablation; OpenFaaS on MicroK8s, no cross-platform routing"
first_page: "1 Mitigating Temporal Blindness in Kubernetes Autoscaling: An Attention-Double-LSTM Framework Faraz Shaikh, Student Member, IEEE, Gianluca Reali, Member, IEEE, and Mauro Femminella, Member, IEEE Abstr"
---
1 

# Mitigating Temporal Blindness in Kubernetes Autoscaling: An Attention-Double-LSTM Framework 

Faraz Shaikh, _Student Member, IEEE,_ Gianluca Reali, _Member, IEEE,_ and Mauro Femminella, _Member, IEEE_ 

**_Abstract_ —In the emerging landscape of edge computing, the stochastic and bursty nature of serverless workloads presents a critical challenge for autonomous resource orchestration. Traditional reactive controllers, such as the Kubernetes Horizontal Pod Autoscaler (HPA), suffer from inherent reaction latency, leading to Service Level Objective (SLO) violations during traffic spikes and resource flapping during ramp-downs. While Deep Reinforcement Learning (DRL) offers a pathway toward proactive management, standard agents suffer from** **_temporal blindness_ , an inability to effectively capture long-term dependencies in nonMarkovian edge environments. To bridge this gap, we propose a novel stability-aware autoscaling framework unifying workload forecasting and control via an Attention-Enhanced DoubleStacked LSTM architecture integrated within a Proximal Policy Optimization (PPO) agent. Unlike shallow recurrent models, our approach employs a deep temporal attention mechanism to selectively weight historical states, effectively filtering highfrequency noise while retaining critical precursors of demand shifts. We validate the framework on a heterogeneous cluster using real-world Azure Functions traces. Comparative analysis against industry-standard HPA, stateless Double DQN, and a single-layer LSTM ablation demonstrates that our approach reduces 90th percentile latency by approximately 29% while simultaneously decreasing replica churn by 39%, relative to the single-layer LSTM baseline. These results confirm that mitigating temporal blindness through deep attentive memory is a prerequisite for reliable, low-jitter autoscaling in production edge environments.** 

**_Index Terms_ —Autoscaling, Kubernetes, LSTM, PPO, DRQN, edge, cloud.** 

## I. INTRODUCTION 

**T** HE architectural paradigm of modern digital services hasundergone a fundamental transformation toward cloudnative, edge, and serverless computing. Driven by the strict low-latency requirements of 5G/6G applications and the Internet of Things (IoT), computational resources are increasingly getting decentralized and positioned toward the network edge [1]. Within this ecosystem, applications are no longer monolithic, and are decomposed into loosely coupled microservices or serverless functions orchestrated by platforms such as Kubernetes [2]. This modularity provides unprecedented agility, allowing individual components to scale independently. Conversely, it introduces an important challenge in autonomous resource orchestration. Unlike traditional data center workloads 

All authors are with the Department of Engineering, University of Perugia, Perugia, Italy. E-mail: faraz@dottorandi.unipg.it, gianluca.reali@unipg.it, mauro.femminella@unipg.it. M. Femminella and G. Reali are also with Consorzio Nazionale Interuniversitario per le Telecomunicazioni (CNIT), 43124 Parma, Italy. 

manifesting predictable diurnal patterns, serverless functions in edge-cloud environments are subject to highly stochastic, non-stationary, and bursty invocation patterns [3]. Therefore, service providers face the complex optimization problem of dynamically adjusting resources i.e., _autoscaling_ , to adhere to strict Service Level Objectives (SLOs) and Quality of Service (QoS) standards while minimizing operational expenditure (OPEX) and avoiding resource wastage. 

The industry-standard for horizontal autoscaling, represented by the Kubernetes Horizontal Pod Autoscaler (HPA), operates primarily through reactive feedback-control loops, as illustrated in Fig. 1, scaling container replicas based on observed resource utilization metrics. These controllers monitor aggregate metrics, such as CPU and/or memory utilization, and trigger scaling actions only when a threshold is violated for a specific duration. While robust in steady-state scenarios, reactive techniques suffer from a fundamental _reaction latency_ , i.e., the unavoidable delay between the onset of a traffic surge and the eventual readiness of new function replicas [4]. This delay is further complemented by container cold starts and initialization overheads, leading to periods of underprovisioning where SLO violations are unavoidable. Furthermore, to prevent _flapping_ (i.e., rapid oscillation), reactive controllers often employ hysteresis, also known as cooling periods, leading to resource misalignment by either retaining idle resources during ramp-downs or by failing to react quickly enough to successive bursts [5]. Beyond the temporal limitations of reaction latency, heuristic and threshold-based approaches fundamentally struggle to capture the complex, non-linear mapping between infrastructure metrics and application performance [6]. In heterogeneous edge environments, the correlation between resource utilization and user-perceived latency is hardly static, fluctuating dynamically based on request complexity, downstream service dependencies, and background interference [7]. Hence, a static threshold that ensures SLO compliance during one operational window may result in severe violations or resource wastage during another, as infrastructure metrics often fail to serve as accurate proxies for application-level QoS. This variability renders the manual tuning of scaling policies complex at scale, as human operators cannot continuously adjust parameters to match the evolving system dynamics [3]. 

To cope with these challenges, researchers have found Deep Reinforcement Learning (DRL) as a viable strategy for autonomous service management. DRL agents can learn optimal scaling strategies by interacting with system en- 

2 



<!-- Start of picture text -->
Standard Approach: Proposed Approach:<br>Reactive, Rule-based HPA Proactive, Learning-based RL Autoscaler<br>Threshold<br>Breach Prediction<br>Simple Rule System State RL Agent<br>(If-then) (Environment) (Policy<br>Network)<br>Workload System Metrics Monitor<br>(Pods) (CPU, Memory)<br>Learn &<br>New State<br>Update<br>Reward Signal<br>Latency<br>/ Delay<br>Action<br>Action taken after metric exceeds limit. System (Proactive)<br>(Pods)<br>Scaling Action(React) Action taken based on predicted future<br>state & reward.<br>Scaling Action<br>(Predict)<br><!-- End of picture text -->

Fig. 1. Conceptual comparison of autoscaling paradigms. _(Left)_ The standard HPA approach vs. _(Right)_ Proposed stability-aware Reinforcement Learning framework 

vironment, making real-time decisions on when to retain, increase, or decrease the number of instances (replicas) to handle fluctuating traffic loads effectively [8]. Early adoption involved value-based methods such as Deep Q-Networks (DQN) [9], [10], which demonstrated improvements over static thresholds in optimizing energy and execution time. More recently, policy-gradient methods, such as, Proximal Policy Optimization (PPO) have been applied to serverless edge computing, marking superior stability in continuous control tasks [11]. A critical limitation of these approaches lies in their failure to address the non-Markovian nature of edge workloads [12], [13]. While functions as a service (FaaS) architectures simplify scaling by decoupling computation from state, standard DRL agents fail to capture the historical context required for accurate forecasting [14]. By operating on a single-step observation window, these agents suffer from partial observability, manifesting as _temporal blindness_ , a failure to differentiate between momentary jitter and genuine shifts in traffic intensity. Recent efforts have tried to mitigate this shortcoming by integrating Recurrent Neural Networks (RNNs) or Long Short-Term Memory (LSTM) units. However, existing frameworks are predominantly based on shallow, single-layer architectures [15]. These standard recurrent models lack the representational depth to capture multi-scale dependencies, such as differentiating short-lived outliers from the onset of sustained diurnal trends [16], and process historical sequences with uniform weight. Hence, they fail to selectively attend to critical precursors, such as the rapid initiation of a concurrent user spike, while filtering out irrelevant background noise [17]. 

Even in LSTM-PPO autoscalers such as DRe-SCale [15], (i) shallow recurrence still exhibits an information bottleneck, (ii) the control interface is often replica-centric rather than Kubernetes knob-centric, and (iii) safe translation from policy actions to operational configurations is typically not explicit. 

In light of these limitations, we propose a novel, stabilityaware autoscaling framework unifying prediction and control via an Attention-enhanced Double-Stacked LSTM agent, a concept of which is also illustrated in Fig. 2. Unlike prior works that often decouple forecasting from the control loop, our approach tightly integrates a deep temporal model within the PPO policy network. We employ a double-stacked LSTM architecture to model high-order traffic dependencies, capturing both immediate fluctuations and long-term trends, and a learned attention mechanism to dynamically weigh the significance of recent historical states. As a result, the agent constructs a context-aware representation of the workload, effectively filtering out stochastic noise while retaining critical precursors of demand shifts. Furthermore, to handle the operational complexity of production environments, our agent operates in a multi-dimensional discrete action space, simultaneously optimizing HPA CPU targets and throughput multipliers. 

The scientific contributions of this article are threefold: 

- 1) We introduce an Attention-enhanced Double-Stacked LSTM policy network that specifically addresses the _temporal blindness_ of stateless DRL and improves over single-layer LSTM-PPO policies by attending to critical historical timesteps while filtering transient noise. 

- 2) We provide a formal, comparative benchmarking against a stateless Double DQN (DDQN) agent, Single-LSTM PPO variant, and a standard rule-based HPA explicitly isolating the gain from (i) stacking depth and (ii) attention under non-Markovian workloads. 

- 3) We conduct an extended stability analysis using realworld Azure Functions invocation traces. Beyond standard metrics, such as, latency and CPU usage, we quantify operational stability using replica churn and oscillation frequency, demonstrating that our proposed 

3 

framework reduces unnecessary scaling actions by a significant margin compared to reactive HPA and standard DRL baselines. 

This manuscript extends the preliminary conference version [18], revising the controller design (action interface and reward definition) and adopting a disjoint multi-day train/test evaluation protocol. In addition, the overall setup has been tested on a different and more performing server, equipped with a GPU. These changes alter both the optimized objective and the workload exposure, so numerical results are expected to significantly differ. 

The remainder of the paper is arranged as follows. Section II discusses the state-of-the art in this specific research domain. Section III details the methodology used for this approach. Section IV discusses the results of the simulations conducted. Finally, section V concludes the paper with a discussion on the proposed approach, its current limitations, and potential avenues for future research. 

## II. RELATED WORK 

The evolution of autoscaling in cloud-native environments has transitioned from reactive, rule-based heuristics to sophisticated data-driven controllers. This progression is differentiated by a shift from mathematical stability models to modelfree reinforcement learning (RL), and most recently, to hybrid architectures that attempt to solve the ”temporal blindness” of pure RL agents. This section categorizes the state-ofthe-art into reactive control, pure RL, and hybrid recurrent architectures. 

The earliest generation of autoscaling systems focused on establishing mathematical stability through feedback control. The industry-standard Kubernetes HPA operates on a reactive, threshold-based loop, monitoring CPU/memory metrics at discrete intervals (typically 15 seconds) and triggering scaling only when thresholds are violated [19], [20]. In steady-state scenarios with predictable workloads, HPA maintains stable performance. However, under bursty traffic, utilization-based scaling lags behind workload changes result in transient overload and SLO violations [21], [22]. This latency is intensified by container startup times averaging 259ms and reaching up to 329ms augment the delay between detection and mitigation [23]. To address these limitations, hierarchical approaches, such as _Gwydion_ [24], decouple application goals from infrastructure metrics, achieving approximately 28% improvement in multi-tier topologies. However, the problem often lies in assuming homogeneous infrastructure incompatible with the non-stationary nature of edge-cloud environments [25]. 

Further, to overcome the rigidity of static thresholds, early research pivoted toward value-based RL methods capable of learning non-linear dynamics. Lee et al. [10] applied Deep Q- Networks (DQN) to manage server instance scaling in multiaccess edge computing (MEC) environments. Their approach demonstrated that learning-based agents could outperform static thresholds in optimizing energy and execution time by adapting to different workload phases. Similarly, Benedetti et al. [26] explored Q-Learning for edge autoscaling, offering a computationally lightweight solution for resource-constrained 

nodes. However, these value-based systems typically rely on low-dimensional state representations and discrete action spaces. This limits their applicability to containerized microservices/serverless platforms where continuous control and precise resource percentages are required. Furthermore, Q- Learning often demonstrates instability in the high-variance, bursty traffic patterns typical of production environments [26]. 

Recognizing the limitations of Q-Learning in continuous action spaces, recent efforts have shifted toward policygradient methods, specifically PPO. Gan et al. [27] proposed a PPO framework for edge computing achieving an 86% improvement over Q-Learning by stabilizing the policy update process through clipping. Addressing specific workload types, the KIS-S framework [28] utilized PPO for GPU inference autoscaling, bridging the gap between simulation and real hardware. To improve temporal awareness without recurrent architectures, Femminella and Reali [29] integrated cyclic time-of-day encoding with a PPO agent. While this allowed the agent to differentiate between peak and off-peak hours, the agent remained fundamentally reactive, lacking an internal memory mechanism to forecast future demand based on historical sequences. 

Alternative approaches have attempted to operate at the OS level. FaaSCtrl [30] used an Advantage Actor-Critic (A2C) controller to manage tail latency by tuning Linux scheduling parameters. However, by operating at the OS level rather than the orchestration level, these solutions lack direct portability to standard Kubernetes deployments. The current frontier of research addresses the non-Markovian nature of edge workloads by integrating time-series forecasting with control loops. Initial attempts focused on decoupled architectures, known as _Separation of Concerns_ . Peng et al. [31] and Yan et al. [32] used Bi-LSTM networks for workload prediction, achieving high accuracy of up to 92.3%. However, decoupling prediction from control often leads to error propagation, where small forecast errors trigger cascading scaling oscillations [33], [34]. Gupta et al. [35] combined proactive Machine Learning (ML)-based scaling with reactive safety nets, reducing SLO violations to 6%. However, the cons for this approach included a significant increase in configuration complexity and potential conflicts between the dual control loops. 

More recently, the research has pivoted more towards the lightweight predictive models and heavy-duty RL agents. On the predictive front, Guruge and Priyadarshana [36] proposed a hybrid forecasting framework combining Facebook Prophet with LSTM networks, especially aiming at resolving the coldstart latency of standard HPA by predicting HTTP request patterns ahead of time, addressing the complexity of multiobjective decision-making without the training overhead of ML. Further, novel mathematical formulations, such as _qAHP_ [37] have been introduced to enable real-time autoscaling in edge clusters, reducing decision latencies by orders of magnitude compared to traditional analytic hierarchy processes. 

To unify prediction and control, researchers are increasingly embedding memory directly into the RL policy. Ma et al. [38] proposed combining Fuzzy Q-Learning with LSTM networks, though the fuzzy logic introduced computational overheads unsuitable for the edge. The tightest integration to date is 

4 

_DRe-SCale_ by Agarwal et al. [15], which embeds an LSTM layer directly within a PPO policy. In serverless environments, this LSTM-PPO architecture improved throughput by 18% compared to non-recurrent baselines by addressing partial observability. 

Despite these advancements, a critical architectural gap remains. Current hybrid approaches, such as, _DRe-SCale_ rely on shallow, single-layer LSTM architectures that suffer from the information bottleneck, where the entire history is compressed into a fixed-size hidden state. Consequently, these approaches struggle to filter noise from signal over long horizons, often failing to selectively attend to critical precursors, such as, the onset of a micro-burst, masked by background fluctuations [33]. Our work addresses this limitation by introducing an Attention-enhanced Double-Stacked LSTM policy. By integrating deep temporal attention, our model retains the sequential context of LSTMs while gaining the ability to explicitly weigh high-importance historical events, thereby unifying prediction and control. 

## III. METHODOLOGY AND SYSTEM ARCHITECTURE 

This study reformulates the challenge of Kubernetes autoscaling as a sequential decision-making problem under uncertainty, solved via a DRL approach. Unlike previous iteration of this work [18], we present a comprehensive control framework integrating short-term forecasting with a multiobjective policy network. To validate the proposed architecture, we establish a comparative experimental design involving four different scaling strategies deployed on a heterogeneous hardware cluster. 

## _A. Problem Formulation and Observation Space (S)_ 

We formally model the autoscaling domain as a Partially Observable Markov Decision Process (POMDP). Unlike a standard Markov Decision Process (MDP) where the agent has perfect knowledge of the environment, a POMDP assumes the agent only observes a partial representation of the true system state [15]. In a Kubernetes cluster, factors such as network queue depths and instantaneous request arrival processes are often hidden or noisy. Therefore, the agent must rely on a constructed observation vector **s** _t_ to infer the system’s true health and make optimal scaling decisions. 

To resolve the partial observability characteristic of bursty edge workloads, the agent constructs a comprehensive 14dimensional state vector **s** _t_ . This vector acts as a sufficient statistic, aggregating immediate infrastructure health with predictive workload trends to ensure the Markov property is approximately satisfied. The state is formally defined as the concatenation of five feature groups, in Eq. (1): 



where: 

- **m**<sup>_perf_</sup> _t ∈_ R<sup>3</sup> : Captures the Quality of Experience (QoE) and load intensity, specifically the average request latency _lt_ , the success ratio _SRt_ , and the _effective_ incoming request rate _λt_ (i.e., the rate of requests successfully admitted by the API gateway after filtering). 

- **m**<sup>_res_</sup> _t ∈_ R<sup>5</sup> : Represents the resource saturation levels, including the current replica count _ρt_ , average pod utilization ( _u_<sup>_cpu_</sup> _t , u_<sup>_ram_</sup> _t_ ), and total cluster-wide resource consumption ( _Ucpu_<sup>_total, U_</sup> _ram_<sup>_total_).Integratingcluster-widemet-</sup> rics allows the agent to sense node-level saturation risks. 

- **m**<sup>_conf_</sup> _t ∈_ R<sup>3</sup> : Encodes the active control configuration to provide context on previous decisions, comprising the current HPA CPU target and the _throughput multiplier_ (a scalar modulating the API gateway’s rate-limiting threshold to throttle overload), and an enhancement level _et_ (a discrete policy mode indicator). 

- **x**<sup>_time_</sup> _t ∈_ R<sup>2</sup> : Cyclic temporal embeddings [cos( _T_<sup><u>2</u></sup> _day_<sup>_<u>πt</u>_)</sup><sup>_,_sin(</sup> _T_<sup><u>2</u></sup> _day_<sup>_<u>πt</u>_)]</sup> allowing the policy to learn and predict diurnal traffic periodicities ( _Tday_ = 1440 min). 

- _N_ ˆ _t ∈_ R<sup>1</sup> : A short-horizon demand estimate computed from a sliding window over recent requests (window _w_ = 3) with exponential smoothing to stabilize the signal used by the controller. 

## _B. Multi-Dimensional Discrete Action Space (A)_ 

- The agent controls the cluster via a Multi-Discrete action 

- space _A ∈_ Z<sup>4</sup> , allowing simultaneous manipulation of four different operational parameters at each time step _t_ . The action vector is defined as **a** _t_ = � _a_<sup>_targ_</sup> _t , a_<sup>_lr_</sup> _t_<sup>_, amult_</sup> _t , a_<sup>_enh_</sup> _t_ �, where: 

- HPA CPU Target ( _a_<sup>_targ_</sup> _∈ {_ 0 _,_ 1 _,_ 2 _,_ 3 _}_ ): Dynamically adjusts the target utilization setpoint for the underlying HPA. This is mapped to the discrete set _{_ 30% _,_ 50% _,_ 70% _,_ 90% _}_ , allowing the agent to switch strategies between conservative resource buffering (low target) and aggressive consolidation (high target) based on workload volatility. 

- Learning Rate (LR) Schedule ( _a_<sup>_lr_</sup> _∈{_ 0 _,_ 1 _,_ 2 _}_ ): Selects a discrete training-mode indicator recorded by the environment during interaction (decrease/base/increase). PPO uses a cosine annealing learning-rate schedule; _a_<sup>_lr_</sup> is logged and does not modify the optimizer, instead, it is retained for future integration of optimizer-level control. 

- Throughput Multiplier ( _a_<sup>_mult_</sup> _∈{_ 0 _,_ 1 _,_ 2 _}_ ): Scales the API gateway’s admitted request rate / rate-limit, mapped to _{_ 1.0, 2.0, 3.0 _}_ . Unlike a multiplier that exceeds capacity, this action acts as a _circuit breaker_ , allowing the agent to actively shed load during extreme bursts to preserve the stability of existing workloads. 

- Enhancement Level ( _a_<sup>_enh_</sup> _∈ {_ 0 _,_ 1 _,_ 2 _}_ ) Selects one of three predefined runtime stabilization modes _{_ OFF, MOD, AGGR _}_ . Higher levels enable progressively stronger safety/stability heuristics that may dampen or override unsafe scaling decisions during SLO violations (e.g., prevent thrashing or force a scale-out in overload). This flag does not change the offered load, but it only changes how conservatively the controller applies scaling actions. 

At each step, discrete action indices are mapped deterministically to valid configuration values (HPA target and gateway multiplier) and applied via Kubernetes API updates. Actions are clipped to deployment bounds, such as, target setpoints and multiplier ranges, to ensure feasibility. 

5 



<!-- Start of picture text -->
Feature Extractor<br>Soft-Attention<br>Action<br>Double-Stacked Mechanism PPO Distribution Action<br>LSTM Layers Actor Sampling &<br>Score Calc Head Decoding<br>( )<br>LSTM<br>Kubernetes Layer 1<br>Environment<br>Softmax Scalar Value<br>pod pod Layer 2LSTM CriticPPO ( ) Estimation &Advantage<br>Head Loss Calc<br>node node<br>Weighted<br>Sum<br>Multi-Discrete Action<br>K8s API Commands<br>(patch HPA, etc.)  Action Updating the network weights<br>Translation<br> (<br>Context Vector<br>( = 128) d<br>Observation Construction<br>Observer Module Linear Projection<br>Hidden States<br><!-- End of picture text -->

Fig. 2. Attention-enhanced Double-Stacked LSTM–PPO autoscaler: embeds Kubernetes observations, applies soft attention over stacked LSTMs for actor–critic action selection, and translates actions into Kubernetes API commands with PPO updates. 

## _C. Optimization Objective_ 

We employ PPO, an on-policy gradient method, for its stability. To prevent destructive policy updates during volatile training phases, we augment the standard clipped objective with a Kullback-Leibler (KL) penalty, given in Eq. (2). 



where _ϵ_ = 0 _._ 2 is the clipping range and _β_ dynamically scales the KL penalty. Here, _rt_ ( _θ_ ) = _πθoldπθ_ <u>(</u> **a** ( _t_ **a** _<u>|t</u>_ **s** _|t_ **s** <u>)</u> _t_ )<sup>denotesthe</sup> probability ratio of the action under the current and previous policies, and _A_<sup>ˆ</sup> _t_ represents the generalized advantage estimate [39], which measures how better an action is compared to the expected baseline. This formulation ensures the new policy _πθ_ does not deviate excessively from the behavioral policy _πθold_ . 

## _D. SLO-Aware Reward Engineering_ 

The reward function _Rt_ is a composite scalar designed to guide the agent toward a Pareto-optimal balance between strict SLO compliance and resource efficiency. It is computed as a weighted sum, shown in Eq. (3). 



where the components are defined as follows: 

- SLO Compliance ( _RSLO_ ): To enforce low-latency guarantees, we define a target latency _Ltarget_ = 20ms as the desired _good QoE_ operating target and a hard violation threshold _Lthresh_ = 50ms to create a two-tier latency objective that rewards staying fast while strongly penal- 

izing overload. The reward is formulated as a piecewise function, given in Eq. (4): 



This structure provides a maximum reward for meeting the target, a linear decay for _graceful degradation_ within the threshold, and a sharp negative penalty for SLO violations. 

- Resource Efficiency ( _RCP U_ ): To prevent overprovisioning, we model efficiency as a Gaussian function centered at the agent’s chosen HPA target _Thpa_ , given in Eq. (5): 



This incentivizes the agent to align the actual cluster usage _u_<sup>_cpu_</sup> _t_ with its selected target _Thpa_ , inclusive of a _±_ 10% tolerance buffer to prevent micro-adjustments. 

- Stability ( _RStab_ ): A penalty term proportional to the magnitude of scaling actions ( _|_ ∆ _ρt|_ ) to discourage control oscillation (flapping). The penalty is formulated in Eq. (6): Specifically, small changes ( _|_ ∆ _ρt| ≤_ 2) pursue a minor penalty, while larger jumps are penalized more heavily to promote smooth transitions. 



- Forecast Alignment ( _RF cst_ ): A penalty applied when the system’s effective request rate deviates from the 

6 

forecasted trend _N_<sup>ˆ</sup> _t_ . This term, defined in Eq. (7) provides a dense guiding signal: 

**Algorithm 1** Attention-Enhanced Double-Stacked LSTM-PPO **Require:** Update interval ∆ _t_ , Horizon _w_ , Discount _γ_ , Clip _ϵ_ . **Ensure:** Optimized Policy _πθ_ , Value Function _Vϕ_ . 



- 1: **Initialize:** Neural networks _θ, ϕ_ and Buffer _B ←∅_ . 

- 2: **for** episode _k_ = 1 _, . . . , K_ **do** 

- 3: Reset environment for episode _k_ 4: **Reset:** LSTM states **h**<sup>(</sup> 0<sup>_l_)</sup><sup>_,_</sup><sup>**c**(</sup> 0<sup>_l_)</sup> _←_ **0** for layers _l ∈{_ 1 _,_ 2 _}_ 

where _C_ is the nominal request capacity per replica. This encourages the agent to scale proactively in anticipation of demand changes rather than reacting solely to latency degradation. 

   - 5: _t ←_ 0 

   - 6: **while** _t < Tmax_ **do** 

   - 7: **State Encoding (Sec. III-A)** 

- ( _RSucc_ ): To ensure the agent maintains high service reliability, we reward the successful completion of requests ( _SRt_ ) as shown in Eq. (8): 

- 8: Collect metrics **o** _t_ = [ **m**<sup>_perf_</sup> _,_ **m**<sup>_res_</sup> _,_ **m**<sup>_conf_</sup> ] 9: _N_ ˆ _t ←_ Forecast( _λt−w_ +1: _t_ ) _{_ Predict short-horizon load from last _w_ steps _}_ 



- 10: **s** _t ←_ [ **o** _t,_ **x**<sup>_time_</sup> _t , N_<sup>ˆ</sup> _t_ ] _{_ Construct full state _}_ 11: **Temporal Processing (Sec. III-E)** 12: **e** _t ←_ ReLU( **W** _e_ **s** _t_ + **b** _e_ ) _{_ Feature embedding _}_ 13: Update LSTM Layer 1: **h**<sup>(1)</sup> _t_<sup>_,_</sup><sup>**c**(1)</sup> _t ←_ LSTM<sup>(1)</sup> ( **e** _t,_ **h**<sup>(1)</sup> _t−_ 1<sup>_,_</sup><sup>**c**(1)</sup> _t−_ 1<sup>)</sup> 

- 14: Update LSTM Layer 2: **h**<sup>(2)</sup> _t_<sup>_,_</sup><sup>**c**(2)</sup> _t ←_ LSTM<sup>(2)</sup> ( **h**<sup>(1)</sup> _t_<sup>_,_</sup><sup>**h**(2)</sup> _t−_ 1<sup>_,_</sup><sup>**c**(2)</sup> _t−_ 1<sup>)</sup><sup>_{_Deephistorytracking</sup><sup>_}_</sup> 

## _E. Attention-enhanced LSTM Policy Architecture_ 

To address the _information bottleneck_ observed in standard RNNs, where fixed-size hidden states struggle to retain highfrequency details over long horizons, we implement a custom feature extractor. The raw state vector **s** _t_ is first projected via a fully connected linear layer to a hidden embedding dimension _d_ = 128. This embedding sequence is then processed by a two-layer stacked LSTM network to capture temporal dependencies. To enable the policy to selectively focus on critical historical events (e.g., sudden load spikes) regardless of their position in the observation window, we apply a deterministic soft-attention mechanism over the LSTM hidden states _H_ = _{_ **h** 1 _, . . . ,_ **h** _w}_ . The attention score _ei_ for each timestep is computed via a learned linear transformation, given in Eq. (9). 

- 15: **Attention Mechanism (Sec. III-E)** 16: Retrieve history _Ht_ = _{_ **h**<sup>(2)</sup> _t−w_ +1<sup>_, . . . ,_</sup><sup>**h**</sup> _t_<sup>(2)</sup><sup>_}{w_hid-</sup> den states _}_ 

- 17: Compute attention scores **e** _attn_ from _Ht_ 18: **_α_** _←_ softmax( **e** _attn_ ) _{_ Attention weights _}_ 19: **c** _ctx ←_<sup>�</sup><sup>_w_</sup> _j_ =1<sup>_αj_</sup><sup>**h**</sup> _t_<sup>(2)</sup> _−w_ + _j_<sup>_{_Contextvector</sup><sup>_}_</sup> 

- 20: **Decision Making (Sec. III-B)** 

- 21: Sample action **a** _t ∼ πθ_ ( _· |_ **c** _ctx_ ) _{_ Policy inference _}_ 22: Apply _Ck_ 8 _s_ to cluster; Wait ∆ _t_ 

- 23: **Feedback Loop (Sec. III-D)** 

Measure reward _Rt_ based on SLOs & Stability 

- 24: 

- 25: Store transition ( **s** _t,_ **a** _t, Rt_ ) in Buffer _B_ 



- **PPO Learning Step** 

26: 

- **if** _|B| ≥ Nbatch_ **then** 



- Calculate advantages _A_<sup>ˆ</sup> _t_ and returns using _Vϕ_ **for** epoch _j_ = 1 _. . . M_ **do** 



- _Lclip ←_ PPO clipped surrogate loss 

- _Lvf ←_ MSE( _Vϕ,_ returns) 

Optimize _θ, ϕ_ to minimize ( _Lclip_ + _Lvf −_ Entropy) 

- **end for** 

33: **end for** 34: Clear Buffer _B_ 35: **end if** 36: _t ← t_ + 1 37: **end while** 

where **w** _a_ and _ba_ are learnable weights. The resulting context vector **c** _ctx_ , i.e., a weighted sum of the history, as given in Eq. (11), is then concatenated with the most recent features and fed into the actor and critic heads of the PPO agent. This architecture allows the agent to bypass the vanishing gradient problem and react proactively to precursors of instability. The complete execution flow of the proposed agent is given in Algorithm 1 and illustrated in Fig 2. This algorithm formalizes the sequential interaction between the environment and the agent, explicitly detailing the forward pass through the doublestacked LSTM layers and the computation of the context vector via the soft-attention mechanism. Furthermore, it also illustrates how the PPO update law is integrated within the training loop to iteratively refine the policy parameters _θ_ and value function weights _ϕ_ based on the collected trajectories in buffer _B_ . 

38: **end for** 

## IV. EXPERIMENTAL RESULTS 

## _A. Hardware and Cluster Testbed_ 

Experiments are conducted on a heterogeneous edge-cloud cluster hosted within a virtualized lab environment, deployed as a two-node MicroK8s Kubernetes setup connected via a low-latency internal network. This configuration is planned to isolate the learning compute from the application workload to ensure experimental accuracy. The master node (Control 

7 

TABLE I 

SIMULATION PARAMETERS AND HYPERPARAMETERS 

|**Parameter**|**Symbol**|**Value**|
|---|---|---|
|**_Environment & Cons_**|**_traints_**||
|Control Interval|∆_t_|60 s|
|Target Latency|_Ltarget_|20 ms|
|Violation Threshold|_Lthresh_|50 ms|
|Max Replicas|_Rmax_|200|
|Forecast Window|_w_|3 steps|
|State Dimension|_dim_(_S_)|14|
|Action Dimension|_dim_(_A_)|4 (Multi-Discrete)|
|**_Reward Function We_**|**_ights_**||
|SLO Compliance|_wsla_|0.50|
|Resource Efficiency|_wcpu_|0.25|
|Success Ratio|_wsucc_|0.12|
|Stability|_wstab_|0.08|
|Forecast Alignment|_wfcst_|0.05|
|**_PPO Optimization_**|||
|Discount Factor|_γ_|0.99|
|GAE Parameter|_λ_|0.93|
|Entropy Coeff.|_cent_|0.01<br>|
|Learning Rate|_α_|2_×_10<sup>_−_4</sup> _→_0 (Cosine Decay)|
|Mini-batch Size|_B_|128|
|Rollout Buffer|_Nsteps_|512|
|Update Epochs|_K_|10|
|**_Neural Network Arch_**|**_itecture_**||
|Hidden Dimension|_dmodel_|128|
|LSTM Layers|_Nstack_|2 (Stacked)|
|Dropout|_pdrop_|0.1|
|Attention|-|Soft-Attention|
|Optimizer|-|Adam|



& Learning Plane) is configured with 10 vCPUs, 64 GB RAM, 100 GB disk storage, and an NVIDIA L40S GPU. This node hosts the Kubernetes control plane and executes the heavy-duty RL training loops including LSTM/Attention inference, offloading complex policy updates to the GPU to prevent CPU overhead. On the other hand, the worker Node (Execution Plane) is configured with 8 vCPUs, 64 GB RAM, and a 50 GB disk. To ensure high-fidelity workload reproduction, we replay real Azure Functions invocation traces [40] using the _hey_ load generator [41] within a discrete-time control loop. We randomly sample 7 days from the trace and use 5 days for training and 2 days for testing; each day is discretized into 500 control intervals, yielding 2,500 training and 1,000 testing timesteps with a fixed control interval of 60 s per step. At each step _t_ , the controller computes the target request rate _N_<sup>¯</sup> _t_ from the trace and configures hey to inject the corresponding load into the OpenFaaS [42] gateway, targeting a CPU-bound factorizator serverless function whose deterministic compute profile makes latency changes attributable primarily to scaling decisions. 

The parameters and hyper-parameters used for these experiments are reported in Table I. 

## _B. Comparative Experimental Framework_ 

We conduct a comparative evaluation against three baselines under identical environmental conditions to validate 



<!-- Start of picture text -->
StaticHPA50 SingleLSTM<br>35 DDQN DoubleLSTM<br>30<br>25<br>20<br>15<br>10<br>5<br>0<br>0 200 400 600 800 1000<br>Time Step<br>Replica Count<br><!-- End of picture text -->

Fig. 3. Number of active replicas allocated by each agent over the 1,000-step simulation 

the effectiveness of the proposed Attention-enhanced PPO. For fairness, all _RL-based_ controllers share the identical action-decoding and runtime stabilization pipeline (same mapping/clipping and the same enhancement-mode rules); only the policy network differs. For the HPA baseline, RL-specific actuators are not used and are held constant throughout (gateway throughput multiplier = 1 _._ 0, enhancement mode = OFF), while the rest of the testbed and workload replay remain identical. These strategies are selected to isolate the contributions of specific architectural components (ablation study) and to benchmark against alternative RL paradigms: 

- Proposed (Attn-LSTM-PPO): The complete architecture as detailed in Section III-E. This agent uses a DoubleStacked LSTM for temporal feature extraction and a soft-attention mechanism to identify critical historical precursors, operating on the full 14-dimensional state space with all actuation parameters enabled. 

- Baseline 1: Recurrent PPO (Ablation Study): A variant representing the state-of-the-art LSTM-PPO framework (DRe-SCale) proposed by Agarwal et al. [15]. Because their original architecture relies on a standard LSTM backbone and does not include an attention mechanism, we accurately replicate their design by disabling the soft-attention module in our agent. This baseline serves as a direct ablation study to isolate the performance gain achieved specifically by the attention mechanism in mitigating the information bottleneck for long-horizon control. 

- Baseline 2: Double Deep Q-Network (Value-Based RL): A Double DQN (DDQN) agent implemented with the same state representation and the same multi-discrete actuation interface as the PPO agents. Drawing inspiration from foundational value-based control approaches for edge and serverless environments, such as those explored by Lee et al. [10] and Tarnaras et al. [43], this baseline represents standard value-based control in bursty edge environments. We utilize the Double DQN variant to mitigate the well-known overestimation bias of standard Q-learning, minimizing the Bellman error using an offpolicy replay buffer. 

- Baseline 3: Standard HPA (Reactive Benchmark): The industry-standard Kubernetes HPA, configured with a 

8 

TABLE II 

PERFORMANCE SUMMARY OF EVALUATED AGENTS ACROSS RESOURCE UTILIZATION, LATENCY, SLO COMPLIANCE, AND PROVISIONING STABILITY 

|**Agent**|**Avg CPU**|**Avg Latency**|**Fraction of**|**Target SLO**|**Hard SLO**|**Replicas Replica Churn**||
|---|---|---|---|---|---|---|---|
||**(%)**|**(ms)**|**Missed Calls**|**Compliance (20ms)**|**Compliance (50ms)**|**(Avg** _±_ **Std)**|**Replica Churn**|
|StaticHPA50|15.44|58.82|0.565|10.3%|43.5%|1.52 _±_ 1.09|97|
|DDQN|87.29|77.33|0.754|9.0%|24.6%|1.00 _±_ 0.00|0|
|SingleLSTM|31.00|32.37|0.080|15.6%|92.0%|3.15 _±_ 3.54|716|
|DoubleLSTM|38.22|24.11|0.031|46.2%|96.9%|2.83 _±_ 3.03|432|





<!-- Start of picture text -->
200 StaticHPA50 SingleLSTM<br>DDQN DoubleLSTM<br>175<br>150<br>125<br>100<br>75<br>50<br>25<br>0<br>0 200 400 600 800 1000<br>Time Step<br>CPU Utilization (%)<br><!-- End of picture text -->

Fig. 4. CPU utilization percentage relative to the allocated limit for each agent. 

static 50% CPU utilization target, a quite common value. This serves as the control baseline for reactive, PID-style orchestration [44], [45]. 



<!-- Start of picture text -->
1.0<br>0.8<br>0.6<br>0.4<br>0.2 DoubleLSTM<br>SingleLSTM<br>DDQN<br>0.0 StaticHPA<br>0 25 50 75 100 125 150 175 200<br>CPU Utilization (%)<br>Cumulative Probability<br><!-- End of picture text -->

Fig. 5. Comparison of CPU usage by each agent, shown as a Cumulative Distribution Function (CDF) 

## _C. Comparative Telemetry Analysis_ 

To evaluate the operational usage of the proposed architecture, we conducted a comparative telemetry analysis of the Double-LSTM agent against the Single-LSTM ablation, the DDQN benchmark, and the industry-standard Static HPA. Importantly, all presented figures and performance metrics are derived exclusively from the evaluation (test) phase with exploratory learning disabled, and do not include the initial training phase. Figures 3 through 7 visualize the performance dynamics over a 1,000-step evaluation window on unseen data, isolating the critical trade-offs between provisioning stability, resource efficiency, and service level assurance. Further, Performance metrics for each agent are summarized in Table II to support reproducibility. This table details average CPU utilization, mean latency, and the fraction of missed calls. Reliability is quantified using SLO compliance against 20 ms (target) and 50,ms (hard) thresholds. Finally, provisioning stability is captured through the average replica count (mean _±_ std) and cumulative replica churn. 

_1) Provisioning Dynamics and Control Stability:_ The replica count metric in Fig. 3 reveals fundamental differences in provisioning dynamics. To quantitatively assess this, we analyze the average replica footprint alongside operational jitter. We define replica churn as<sup>�</sup><sup>_T_</sup> _t_ =2<sup>_|ρt−ρt−_1</sup><sup>_|_over the evaluation</sup> horizon, where _ρt_ is the active replica count at step _t_ . Lower churn indicates fewer sudden scale transitions and reduced control oscillation. As detailed in Table II, the baseline DDQN agent fails to scale during critical traffic surges, flatlining entirely (averaging 1.00 _±_ 0.00 replicas with a churn of 0), likely 

converging on a risk-averse policy that prioritizes resource costs over SLO compliance. Similarly, the reactive Static HPA baseline demonstrates rigid, delayed scaling (churn of 97) that misses macro-level spikes entirely due to its mandatory cooldown hysteresis. Conversely, both LSTM-based agents successfully anticipate macro-level workload spikes. However, the Single-LSTM baseline suffers from high-frequency oscillatory behavior, commonly known as _thrashing_ or _pingpong effect_ by rapidly over-provisioning and de-provisioning replicas in response to temporary noise [46]. This instability is quantitatively captured by its massive replica churn of 716 and a highly volatile active replica count (3.15 _±_ 3.54). In contrast, the DoubleL-STM agent demonstrates a stabilized, dampened control response that filters stochastic noise while accurately tracking the true demand curve. By utilizing its deep attentive memory, the agent achieves a more efficient provisioning footprint (2.83 _±_ 3.03 average replicas) and reduces replica churn to 432. For instance, during the primary workload spikes, the agent decisively provisions over 30 replicas to fully absorb the massive traffic volume. Crucially, it maintains replicas throughout the duration of the burst rather than prematurely scaling down during momentary traffic dips, hence preventing the severe latency penalties associated with repeated container cold-starts. 

_2) Resource Utilization and Efficiency:_ Resource efficiency is analyzed through the temporal CPU utilization trends in Fig. 4 and the Cumulative Distribution Function (CDF) in Fig. 5. An optimal autoscaler maximizes resource density, operating 

9 



<!-- Start of picture text -->
StaticHPA50 SingleLSTM StaticHPA50 SingleLSTM<br>175 DDQN DoubleLSTM 300 DDQN DoubleLSTM<br>150<br>250<br>125<br>200<br>100<br>150<br>75<br>100<br>50<br>50<br>25<br>0<br>0 200 400 600 800 1000 0 200 400 600 800 1000<br>Time Step Time Step<br>Average Latency (ms)<br>90th Percentile Latency (ms)<br><!-- End of picture text -->

Fig. 6. Average request latency (ms) measured at each time step 

Fig. 7. 90th percentile (P90) latency (ms) representing tail performance 

at higher safe CPU utilization levels without triggering service degradation. As detailed in Table II, the Double-LSTM agent achieves this balance, maintaining a higher average CPU utilization (38.22%) than the Single-LSTM baseline (31.00%) while delivering better SLO compliance. Although it briefly spikes near 175% CPU during sudden traffic surges, the system is simply working at full capacity to process pending requests while waiting for new replicas to start up, rather than suffering from continuous overload. Conversely, the Single-LSTM’s lower overall utilization is a direct symptom of predictive uncertainty. The agent being vulnerable to high-frequency noise, over-provisions replicas as a defensive buffer to mitigate potential forecast inaccuracies. While this safely protects the SLO, it slightly dilutes the CPU load across and leads to higher OpEx. 

On the other hand, the non-predictive baselines demonstrate severe resource mismanagement. The DDQN agent displays a catastrophic utilization profile, with the CDF showing it frequently saturating well beyond 100% CPU. Because the DDQN policy fails to provision additional replicas during traffic surges, its active containers become severely bottlenecked, directly causing the 24.6% SLO compliance failure recorded in Table II. However, the Static HPA baseline operates at an artificially low average utilization of 15.44%. This inefficiency is caused by the mandatory cooldown windows observed in reactive scalers, which force the retention of idle replicas long after traffic has reduced, creating significant resource slack while still failing to protect against sudden upstream demand spikes. However, simply decreasing this mandatory cooldown windows in static HPA, without an additional intelligent control algorithm, is often counterproductive, as it directly leads to increased control instability and resource thrashing. [26]. 

_3) Cold-Start Convergence and Reliability:_ The temporal latency trace in Fig. 6 reveals a critical cold start vulnerability in the DDQN benchmark, which records an immediate latency spike reaching 175ms during its initial exploration phase. This makes it unsuitable for mission-critical deployments without extensive pre-training, a flaw compounded by recurrent, severe latency failures during subsequent traffic surges. While the Static HPA baseline avoids this initial startup penalty, its strictly reactive nature consistently bottlenecks the system during macro-level workload ramp-ups, leading to catastrophic latency spikes that frequently exceed 100 ms. Among the predictive models, the Single-LSTM agent successfully bounds 

its variance within a much safer deterministic range. However, it still suffers from oscillatory instability, experiencing periodic latency degradation (spiking toward 75ms) due to its inability to filter short-term high-frequency noise. Finally, the proposed Double-LSTM agent delivers even better stability. By effectively decoupling trend forecasting from residual error correction, it maintains a consistent, tight baseline between 15 ms and 30 ms almost immediately from the first time step. While occasional minor latency spikes remain observable, they are strictly transient adaptations to extreme workload volatility and are rapidly avoided, allowing the agent to proactively absorb bursts and maintain an optimal average latency of 24.11 ms. 

_4) Tail Latency Analysis:_ To quantify reliability under stochastic demand, we analyze the 90th percentile (P90) latency, filtering out extreme outliers while capturing the worstcase performance experienced by the majority of users. The temporal trace in Fig. 7 highlight the limitations of the nonpredictive baselines. The Static HPA struggles to adapt to sudden load increases, experiencing a significant latency spike exceeding 300 ms during the primary workload surge near step 520. This degradation is rooted in the inherent provisioning delay of threshold-based policies, comprising metric collection intervals and container start times, which forces incoming requests into overloaded queues before new capacity becomes active [3]. Similarly, the DDQN agent exhibits high variance and consistent under-provisioning, leading to an elevated P90 profile that frequently plateaus between 150 ms and 200 ms. This lack of responsiveness demonstrates a policy collapse, when a agent converges on a _lazy_ local minimum that prioritizes resource savings over performance penalties, failing to correlate scaling actions with latency reduction during exploration [47]. 

Among the predictive models, the Single-LSTM agent improves overall stability, yet its tail distribution still shows notable variance. Because this single-layer architecture is sensitive to noise-induced scaling jitter, it occasionally underprovisions, causing its P90 latency to regularly reach the 100 ms to 130 ms range during volatile traffic surges. Conversely, the proposed Double-LSTM agent uses its secondary layer to correct residual forecast errors, effectively reducing volatility and yielding the lowest, most tightly clustered P90 profile among the evaluated policies. Although minor transient outliers occur during periods of sharp workload surges, the 

10 



<!-- Start of picture text -->
0.008 Agent 1.0<br>DoubleLSTM<br>0.007 SingleLSTM<br>0.8<br>0.006<br>0.005 0.6<br>0.004<br>0.4<br>0.003<br>0.002<br>0.2 DoubleLSTM<br>SingleLSTM<br>0.001<br>SLO Target (20ms)<br>Hard SLO (50ms)<br>0.000 0.0<br>0 50 100 150 200 250 300 350 400 0 20 40 60 80 100<br>Absolute Prediction Error (Requests) Average Latency (ms)<br>(a) Predictive Accuracy (Error Distribution) (b) System Stability (Latency CDF)<br>Density<br>Cumulative Probability<br><!-- End of picture text -->

Fig. 8. Comparison of the proposed Double-LSTM agent against the Single-LSTM baseline (a) Kernel Density Estimate of prediction errors. (b) Cumulative Distribution Function of latency 

Double-LSTM keeps its worst-case performance comfortably below the 50 ms Hard SLO for most of the operational horizon. 

## _D. Impact of Predictive Architecture on Latency Stability_ 

To isolate the contributions of the proposed dual-layered forecasting mechanism, we conducted an ablation study comparing the Double-LSTM agent against the baseline SingleLSTM variant. Fig. 8a illustrates the Kernel Density Estimate (KDE) of the absolute forecasting error. The Double-LSTM agent exhibits a distribution with a sharper peak near zero and a more rapid drop-off, indicating higher consistency in anticipating workload patterns. In contrast, the Single-LSTM baseline displays a lower peak with a heavier right tail extending to larger errors ( _≈_ 400 requests), reflecting a greater likelihood of substantial prediction errors that result in reactive rather than proactive scaling [48]. The operational impact of this predictive advantage appears in the Cumulative Distribution Function (CDF) of application latency (Fig. 8b). The DoubleLSTM agent (red curve) delivers a tighter latency profile, with its CDF rising more steeply and achieving higher SLO compliance at the 20 ms target. Conversely, the Single-LSTM agent shows a longer tail, where prediction shortfalls delay responses to workload spikes, causing latencies to exceed the 20 ms SLO target in a larger fraction of runs (as indicated by the lower CDF values at 20 ms). In addition, the Double-LSTM agent succeeds in keeping the 95 _th_ percentile of average latency below the hard SLO requirement, which is instead not achieved by the Single-LSTM agent. This demonstrates that the secondary LSTM layer for forecasting effectively filters noise and enhances the stability of scaling decisions in Kubernetes HPA contexts. 

## V. DISCUSSION AND LESSONS LEARNED 

The experimental results presented in Section IV support the central premise of this study that mitigating temporal blindness improves control stability under bursty workloads. By 

unifying short-term forecasting with control via an AttentionEnhanced Double-Stacked LSTM architecture, our framework shows consistently improved stability relative to the recurrent ablation and reactive baselines. The comparative ablation study (Fig. 8) highlights that memory depth alone is insufficient for robust control. While the Single-LSTM baseline improved upon the stateless DDQN and static HPA, it remained prone to _information bottlenecks_ , often failing to distinguish between jitter and the onset of sustained traffic shifts. The integration of the soft-attention mechanism proved critical in resolving this. By assigning learnable weights to historical hidden states, the agent effectively learned a temporal masking strategy, ignoring high-frequency variance while attending to significant trend precursors [17]. As evident in the recent findings, sequence modeling suggests that attention mechanisms provide the necessary inductive bias to handle the long-term dependencies integrated in diurnal edge workloads [16]. 

A recurring challenge in autoscaling is the zero-sum game between low latency and low oscillation. Reactive controllers, such as the Kubernetes HPA, prioritize stability through hysteresis (already defined in the introduction), resulting in the _reaction latency_ observed in Fig. 7. Conversely, standard RL agents often prioritize aggressive reward maximization, leading to the oscillatory behavior seen in the DDQN baseline. Our proposed reward function (Section III-D), specifically the penalty term _γ_ 3 _RStab_ , combined with the smoothed policy updates of PPO, allowed the agent to navigate this trade-off effectively. The agent learned to perform _preventive buffering_ , scaling out slightly before the predicted demand curve, thereby absorbing bursts without the flapping characteristic of purely reactive systems [5]. 

While the Double-Stacked LSTM architecture offers better control, it introduces non-negligible computational complexity compared to lightweight heuristics. The inference time for the attention-based network is orders of magnitude higher than the simple arithmetic threshold check of standard HPA. In our testbed with GPU acceleration, this overhead was negligible 

11 

( _≈_ 5-10 ms per step). However, in highly constrained edge nodes (e.g., IoT gateways or micro-MECs) without hardware acceleration, the inference latency of deep recurrent networks could potentially compete with the application workload itself. Future deployments may require model quantization or knowledge distillation techniques to reduce the footprint of the policy network for deployment on embedded edge devices [27]. It is also important to acknowledge the boundaries of our experimental design. First, while the Azure Functions traces ensure realistic arrival patterns, the use of Hey load generator in a virtualized environment may not fully capture the _noisy neighbor_ interference and hardware contention present in multi-tenant bare-metal clusters. Network I/O contention and CPU cache thrashing, common in production 6G nodes [49], were modeled implicitly using the stochasticity of the environment, however, they were not explicitly controlled variables. Second, the agent was trained and evaluated on a single microservice type (CPU-bound factorization). In realworld microservice chains, an autoscaling decision in one tier (e.g., frontend) can cause back-pressure or starvation in downstream dependencies (e.g., database) [24]. Our current single-agent formulation does not account for these cascading inter-service dependencies. 

## VI. CONCLUSION 

This article presented a stability-aware autoscaling framework designed to mitigate the _temporal blindness_ in standard Reinforcement Learning agents operating within bursty edge environments. By integrating an Attention-enhanced DoubleStacked LSTM architecture into a PPO control loop, our approach successfully unified short-term workload forecasting with proactive resource orchestration. Experiments driven by real-world Azure Functions traces show that, relative to an otherwise identical single-layer LSTM PPO ablation without attention, our method reduces the 90th-percentile (tail) latency by approximately 29% and lowers replica churn by 39%, while also demonstrating competitive performance against both the industry-standard HPA baseline and the Double DQN agent across the evaluated workload trace. Despite these gains, the proposed framework introduces non-negligible inference latency, which, while manageable on GPU-accelerated nodes, may prove computationally prohibitive for resourceconstrained IoT gateways. Furthermore, our evaluation was limited to a single-tier microservice in a controlled simulation, abstracting away the complex inter-service dependencies and noisy neighbor interference typical of multi-tenant production clusters. Future research will address these limitations by extending the framework to a Multi-Agent Reinforcement Learning (MARL) setting to coordinate scaling across dependent service chains. Additionally, we aim to integrate energy consumption as a first-class optimization objective and validate the system’s robustness on a physical 6G testbed to assess the impact of radio access network (RAN) dynamics on the control loop, such as in AI-RAN architectures [50]. 

## DATA AVAILABILITY STATEMENT 

The complete source code and simulation environment used in this study, along with the results are available online [51], 

while the underlying workload data is sourced from the public Azure Functions traces [40]. 

## REFERENCES 

- [1] X. Wang, J. Li, Z. Ning, Q. Song, L. Guo, S. Guo, and M. S. Obaidat, “Wireless powered mobile edge computing networks: A survey,” _ACM Computing Surveys_ , vol. 55, no. 13s, pp. 1–37, 2023. 

- [2] J. Dogani, R. Namvar, and F. Khunjush, “Auto-scaling techniques in container-based cloud and edge/fog computing: Taxonomy and survey,” _Computer Communications_ , vol. 209, pp. 120–150, 2023. 

- [3] M. Xu, L. Wen, J. Liao, H. Wu, K. Ye, and C. Xu, “Auto-scaling approaches for cloud-native applications: A survey and taxonomy,” _arXiv preprint arXiv:2507.17128_ , 2025. 

- [4] M. Golec, G. K. Walia, M. Kumar, F. Cuadrado, S. S. Gill, and S. Uhlig, “Cold start latency in serverless computing: A systematic review, taxonomy, and future directions,” _ACM Computing Surveys_ , vol. 57, no. 3, pp. 1–36, 2024. 

- [5] The Kubernetes Authors, “Horizontal Pod Autoscaling: Flapping,” Kubernetes Documentation, 2025, accessed: 2025-1228. [Online]. Available: https://kubernetes.io/docs/concepts/workloads/ autoscaling/horizontal-pod-autoscale/#flapping 

- [6] F. Rossi, V. Cardellini, and F. L. Presti, “Hierarchical scaling of microservices in kubernetes,” in _2020 IEEE international conference on autonomic computing and self-organizing systems (ACSOS)_ . IEEE, 2020, pp. 28–37. 

- [7] A. A. Khaleq and I. Ra, “Intelligent autoscaling of microservices in the cloud for real-time applications,” _IEEE access_ , vol. 9, pp. 35 464–35 476, 2021. 

- [8] Z. Xiao and S. Hu, “Dscaler: A horizontal autoscaler of microservice based on deep reinforcement learning,” in _2022 23rd Asia-Pacific Network Operations and Management Symposium (APNOMS)_ . IEEE, 2022, pp. 1–6. 

- [9] Y. Kim, J. Park, J. Yoon, and J. Kim, “Improved q network auto-scaling in microservice architecture,” _Applied Sciences_ , vol. 12, no. 3, p. 1206, 2022. 

- [10] D.-Y. Lee, S.-Y. Jeong, K.-C. Ko, J.-H. Yoo, and J. W.-K. Hong, “Deep q-network-based auto scaling for service in a multi-access edge computing environment,” _International Journal of Network Management_ , vol. 31, no. 6, p. e2176, 2021. 

- [11] J. Santos, E. Reppas, T. Wauters, B. Volckaert, and F. De Turck, “Can reinforcement learning be generalized for efficient auto-scaling in containerized clouds?” in _NOMS 2025-2025 IEEE Network Operations and Management Symposium_ . IEEE, 2025, pp. 1–7. 

- [12] E. Cortez, A. Bonde, A. Muzio, M. Russinovich, M. Fontoura, and R. Bianchini, “Resource central: Understanding and predicting workloads for improved resource management in large cloud platforms,” in _Proceedings of the 26th Symposium on Operating Systems Principles_ , 2017, pp. 153–167. 

- [13] M. J. Hausknecht and P. Stone, “Deep recurrent q-learning for partially observable mdps.” in _AAAI fall symposia_ , vol. 45, 2015, p. 141. 

- [14] P. Hernandez-Leal, B. Kartal, and M. E. Taylor, “A survey and critique of multiagent deep reinforcement learning,” _Autonomous Agents and MultiAgent Systems_ , vol. 33, no. 6, pp. 750–797, 2019. 

- [15] S. Agarwal, M. A. Rodriguez, and R. Buyya, “A deep recurrentreinforcement learning method for intelligent autoscaling of serverless functions,” _IEEE Transactions on Services Computing_ , vol. 17, no. 5, pp. 1899–1910, 2024. 

- [16] F. Zhao, W. Lin, S. Lin, S. Tang, and K. Li, “Mscnet: multi-scale network with convolutions for long-term cloud workload prediction,” _IEEE Transactions on Services Computing_ , 2025. 

- [17] C. Meng, S. Song, H. Tong, M. Pan, and Y. Yu, “Deepscaler: Holistic autoscaling for microservices based on spatiotemporal gnn with adaptive graph learning,” in _2023 38th IEEE/ACM International Conference on Automated Software Engineering (ASE)_ . IEEE, 2023, pp. 53–65. 

- [18] F. Shaikh, G. Reali, and M. Femminella, “Intelligent autoscaling with attention-based reinforcement learning for sla-aware resource management in edge-cloud environments,” in _2025 21st International Conference on Network and Service Management (CNSM)_ , 2025, pp. 1–9. 

- [19] The Kubernetes Authors, “Horizontal pod autoscaling,” https://kubernetes.io/docs/concepts/workloads/autoscaling/ horizontal-pod-autoscale/, 2026, accessed: 2026-01-15. 

- [20] J.-M. Franc¸ois, “Kubernetes v1.33: Horizontalpodautoscaler configurable tolerance,” https://kubernetes.io/blog/2025/04/28/ kubernetes-v1-33-hpa-configurable-tolerance/, Apr. 2025, kubernetes Blog. 

12 

- [21] V. Punniyamoorthy, B. Kumar, S. Saha, L. Butra, M. Palanigounder, A. K. Agarwal, and K. Kannan, “An slo driven and cost-aware autoscaling framework for kubernetes,” _arXiv preprint arXiv:2512.23415_ , 2025. 

- [22] M.-N. Tran and Y. Kim, “Optimized resource usage with hybrid autoscaling system for knative serverless edge computing,” _Future Generation Computer Systems_ , vol. 152, pp. 304–316, 2024. 

- [23] A. Hall and U. Ramachandran, “Opportunities for optimizing the container runtime,” in _2022 IEEE/ACM 7th Symposium on Edge Computing (SEC)_ . IEEE, 2022, pp. 265–276. 

- [24] J. Santos, E. Reppas, T. Wauters, B. Volckaert, and F. De Turck, “Gwydion: Efficient auto-scaling for complex containerized applications in kubernetes through reinforcement learning,” _Journal of Network and Computer Applications_ , vol. 234, p. 104067, 2025. 

- [25] E. Park, K. Baek, E. Cho, and I.-Y. Ko, “Fully decentralized horizontal autoscaling for burst of load in fog computing,” _Journal of Web Engineering_ , vol. 22, no. 6, pp. 849–870, 2023. 

- [26] P. Benedetti, M. Femminella, and G. Reali, “Management of autoscaling serverless functions in edge computing via q-learning,” _Future Generation Computer Systems_ , vol. 175, p. 108112, 2026. 

- [27] Z. Gan, R. Lin, and H. Zou, “Adaptive auto-scaling in mobile edge computing: A deep reinforcement learning approach,” in _2022 2nd International Conference on Consumer Electronics and Computer Engineering (ICCECE)_ . IEEE, 2022, pp. 586–591. 

- [28] G. Zhang, W. Guo, Z. Tan, Q. Guan, and H. Jiang, “Kis-s: A gpuaware kubernetes inference simulator with rl-based auto-scaling,” in _2025 IEEE International Performance, Computing, and Communications Conference (IPCCC)_ . IEEE, 2025, pp. 1–8. 

- [29] M. Femminella and G. Reali, “Application of proximal policy optimization for resource orchestration in serverless edge computing.” _Computers (2073-431X)_ , vol. 13, no. 9, 2024. 

- [30] A. Panda and S. R. Sarangi, “Faasctrl: A comprehensive-latency controller for serverless platforms,” _IEEE Transactions on Cloud Computing_ , 2024. 

- [31] Z. Peng, B. Tang, W. Xu, Q. Yang, E. Hussaini, Y. Xiao, and H. Li, “Microservice auto-scaling algorithm based on workload prediction in cloud-edge collaboration environment,” in _2023 IEEE International Conferences on Internet of Things (iThings) and IEEE Green Computing & Communications (GreenCom) and IEEE Cyber, Physical & Social Computing (CPSCom) and IEEE Smart Data (SmartData) and IEEE Congress on Cybermatics (Cybermatics)_ . IEEE, 2023, pp. 608–615. 

- [32] M. Yan, X. Liang, Z. Lu, J. Wu, and W. Zhang, “Hansel: Adaptive horizontal scaling of microservices using bi-lstm,” _Applied Soft Computing_ , vol. 105, p. 107216, 2021. 

- [44] M. Sabuhi, N. Mahmoudi, and H. Khazaei, “Optimizing the performance of containerized cloud software systems using adaptive pid controllers,” _ACM Trans. Auton. Adapt. Syst._ , vol. 15, no. 3, Aug. 2021. 

- [45] B. Burns, B. Grant, D. Oppenheimer, E. Brewer, and J. Wilkes, “Borg, omega, and kubernetes,” _Commun. ACM_ , vol. 59, no. 5, p. 50–57, Apr. 2016. [Online]. Available: https://doi.org/10.1145/2890784 

- [46] D. Trihinas, Z. Georgiou, G. Pallis, and M. D. Dikaiakos, “Improving rule-based elasticity control by adapting the sensitivity of the autoscaling decision timeframe,” in _Algorithmic Aspects of Cloud Computing_ , D. Alistarh, A. Delis, and G. Pallis, Eds. Cham: Springer International Publishing, 2018, pp. 123–137. 

- [47] Y. Gar´ı, D. A. Monge, E. Pacini, C. Mateos, and C. G. Garino, “Reinforcement learning-based application autoscaling in the cloud: A survey,” _Engineering Applications of Artificial Intelligence_ , vol. 102, p. 104288, 2021. 

- [48] D. B. Wright and J. A. Herrington, “Problematic standard errors and confidence intervals for skewness and kurtosis,” _Behavior research methods_ , vol. 43, no. 1, pp. 8–17, 2011. 

- [49] Z. H. Meybodi, A. Mohammadi, E. Rahimian, S. Heidarian, J. Abouei, and K. N. Plataniotis, “Tedge-caching: Transformer-based edge caching towards 6g networks,” in _ICC 2022-IEEE International Conference on Communications_ . IEEE, 2022, pp. 613–618. 

- [50] “AI-RAN Alliance Web page,” accessed: 2026-02-21. [Online]. Available: https://ai-ran.org/ 

- [51] F. Shaikh, “Autoscaling: Mitigating temporal blindness.” [Online]. Available: https://github.com/farazshaikh581/Autoscaling mitigating-temporal-blindness 

**Faraz Shaikh** (Student Member, IEEE) received his Master’s degree in Computational Science and Engineering from the National University of Sciences and Technology (NUST), Islamabad, Pakistan, in 2024. He is currently pursuing his PhD in the Department of Engineering at the University of Perugia, Italy. His doctoral research and research interests include advancing artificial intelligence techniques for cloud-native and edge computing environments, with particular emphasis on autoscaling, resource orchestration, and distributed intelligence in 6G net- 



works. 

- [33] K. G. Kim and B. T. Lee, “Self-attention with temporal prior: can we learn more from the arrow of time?” _Frontiers in Artificial Intelligence_ , vol. 7, p. 1397298, 2024. 

- [34] B. Lim, S. O. Arık, N. Loeff, and T. Pfister, “Temporal fusion transform-<sup>¨</sup> ers for interpretable multi-horizon time series forecasting,” _International journal of forecasting_ , vol. 37, no. 4, pp. 1748–1764, 2021. 

- [35] S. Gupta, M. T. Islam, and R. Buyya, “A hybrid reactive-proactive autoscaling algorithm for sla-constrained edge computing,” _arXiv preprint arXiv:2512.14290_ , 2025. 

- [36] P. B. Guruge and Y. Priyadarshana, “Time series forecasting-based kubernetes autoscaling using facebook prophet and long short-term memory,” _Frontiers in Computer Science_ , vol. 7, p. 1509165, 2025. 

- [37] I. Dimolitsas, D. Dechouniotis, and S. Papavassiliou, “Enabling multiapplication multi-objective autoscaling with quick analytic hierarchy process,” _IEEE Networking Letters_ , 2026. 

- [38] X. Ma, K. Zong, and A. Rezaeipanah, “Auto-scaling and computation offloading in edge/cloud computing: a fuzzy q-learning-based approach,” _Wireless Networks_ , vol. 30, no. 2, pp. 637–648, 2024. 

- [39] J. Schulman, F. Wolski, P. Dhariwal, A. Radford, and O. Klimov, “Proximal policy optimization algorithms,” _arXiv preprint arXiv:1707.06347_ , 2017. 

- [40] Microsoft Azure, “Azure functions invocation trace 2021,” https://github.com/Azure/AzurePublicDataset/blob/master/ AzureFunctionsInvocationTrace2021.md, 2021, accessed: 2026-0216. 

- [41] J. Rakyll, “hey: Http load generator, apachebench (ab) replacement,” https://github.com/rakyll/hey, 2016, accessed: 2026-02-16. 

- [42] OpenFaaS, “Openfaas - serverless functions made simple,” https://www. openfaas.com/, accessed: 2026-02-16. 

- [43] A. Zafeiropoulos, E. Fotopoulou, N. Filinis, and S. Papavassiliou, “Reinforcement learning-assisted autoscaling mechanisms for serverless computing platforms,” _Simulation Modelling Practice and Theory_ , vol. 116, p. 102461, 2022. 

**Gianluca Reali** (Member, IEEE) received the Ph.D. degree in telecommunications from the University of Perugia, Italy, in 1997. From 1997 to 2004, he was a Researcher with the Department of Electronic and Information Engineering, University of Perugia. In 1999, he visited the Computer Science Department, UCLA. Since January 2005, he has been an Associate Professor with the Department of Engineering, University of Perugia. His research interests include resource allocation over packet networks, wireless networking, network management, multimedia ser- 



vices, big data management, and nanoscale communications. 

**Mauro Femminella** (Member, IEEE) received the master’s and Ph.D. degrees in electronic engineering from the University of Perugia, Italy, in 1999 and 2003, respectively. Since July 2022, he has been an Associate Professor with the Department of Engineering, University of Perugia. Currently, he is the representative of University of Perugia in the Stakeholders Assembly of the Consortium CNIT. He has co-authored more than 120 papers in international journals and refereed international conferences. His current research interests include molecular communications, big data systems, and application of AI to network management solutions for 5G/6G networks. 

