---
# --- bibliographic record ---
entry_type: misc
title: "Taming Cold Starts: Proactive Serverless Scheduling with Model Predictive Control"
authors:
  - "Chanh Nguyen"
  - "Monowar Bhuyan"
  - "Erik Elmroth"
year: 2025
venue: "arXiv preprint"
volume: ""
issue: ""
pages: ""
publisher: ""
doi: ""
arxiv: "2508.07640"
url: "https://arxiv.org/abs/2508.07640"

# --- archive record ---
source_pdf: taming-cold-starts-mpc-prewarming-2025.pdf
source_sha256: 0aa873b7351f309b7b5c7249b24389a419d271b874e2d457526ea160365adc38
pdf_pages: 8
converted: 2026-09-13
record_source: arxiv
key_insight: "MPC scheduler jointly optimizes prewarming and dispatch on OpenWhisk; single platform, no cross-platform routing"
first_page: "Taming Cold Starts: Proactive Serverless Scheduling with Model Predictive Control Chanh Nguyen∗, Monowar Bhuyan∗, Erik Elmroth∗† ∗Department of Computing Science, Ume˚a University, SE-90187, Sweden †E"
---
# Taming Cold Starts: Proactive Serverless Scheduling with Model Predictive Control 

Chanh Nguyen<sup>_∗_</sup> , Monowar Bhuyan<sup>_∗_</sup> , Erik Elmroth<sup>_∗†_</sup> 

_∗Department of Computing Science, Ume˚a University, SE-90187, Sweden_ 

_†Elastisys AB, Ume˚a, Sweden_ 

Email: _{_ chanh, monowar, elmroth _}_ @cs.umu.se 

**_Abstract_ —Serverless computing has transformed cloud application deployment by introducing a fine-grained, event-driven execution model that abstracts away infrastructure management. Its on-demand nature makes it especially appealing for latencysensitive and bursty workloads. However, the cold start problem, i.e., where the platform incurs significant delay when provisioning new containers, remains the Achilles’ heel of such platforms.** 

**This paper presents a predictive serverless scheduling framework based on Model Predictive Control to proactively mitigate cold starts, thereby improving end-to-end response time. By forecasting future invocations, the controller jointly optimizes container prewarming and request dispatching, improving latency while minimizing resource overhead.** 

**We implement our approach on Apache OpenWhisk, deployed on a Kubernetes-based testbed. Experimental results using realworld function traces and synthetic workloads demonstrate that our method significantly outperforms state-of-the-art baselines, achieving up to 85% lower tail latency and a 34% reduction in resource usage.** 

**_Index Terms_ —Serverless, Cloud Computing, Orchestration, Cold Start, Function-as-a-service, Model Predictive Control, Prediction, Request Shaping** 

## I. INTRODUCTION 

**Background.** Serverless computing [1], [2] is a cloud execution model that provides _Function-as-a-Service (FaaS)_ capabilities, abstracting away infrastructure management while enabling fine-grained, event-driven function execution. While traditional Infrastructure-as-a-Service (IaaS) and Platform-asa-Service (PaaS) models offer varying degrees of automation in provisioning and scaling, serverless platforms go further by providing per-request automatic provisioning, transparent scaling, and fine-grained billing based on actual execution time. This advantage eliminates the need for developers to manage runtime environments, instance lifecycles, or idle resource allocation. Today, serverless platforms are increasingly adopted across a variety of domains, including web applications, data processing pipelines, IoT workloads, and machine learning inference [3], [4]. This growth has been supported by the availability of both commercial platforms, such as AWS Lambda<sup>1</sup> , Google Cloud Functions<sup>2</sup> , and Azure Functions<sup>3</sup> , 

> This work was supported by the European Commission through the Horizon Europe project SovereignEdge.COGNIT (grant no. 101092711). Additional support was provided by the Wallenberg AI, Autonomous Systems and Software Program (WASP) funded by Knut and Alice Wallenberg Foundation. 

and open-source alternatives like Apache OpenWhisk<sup>4</sup> and OpenFaaS<sup>5</sup> , which offer developers greater flexibility and deployment control. 

Despite its advantages, serverless computing suffers from **cold start latency** , i.e, the delay introduced when no warm function replica is available to serve a request. In such cases, the platform must initialize a new container, allocate resources, and load dependencies, leading to significantly higher response times compared to requests handled by already warm containers. Such delays are especially harmful in _latency-sensitive applications_ , particularly those involving _user-defined functions_ with large dependencies (e.g., machine learning models) [5], where they can cause missed deadlines, failed requests, and significant QoS degradation, as illustrated in the real-world use case below. 



<!-- Start of picture text -->
(a) Response Time per Request<br>10<br>0<br>Warm Avg Exec Time<br>Cold start<br>(b) Warm Container Count Over Time<br>8<br>6<br>4<br>2<br>21:26:12 21:26:47 21:27:21<br>Time<br>RT (s)<br>Count<br><!-- End of picture text -->

Fig. 1. (a) Response time per request (in seconds). (b) Number of warm containers over time during 50 function invocations. 

**Real world example.** Consider an object detection function running the EfficientDet model [6] as part of a robotic application [7]. The function is deployed on OpenWhisk, which runs on top of a Kubernetes cluster. Robots send frames captured by their cameras to the function to detect relevant objects and obstacles. Figure 1 shows the response time and the number of warm containers over time after sending 50 requests to the platform with randomly distributed arrival times. The average warm execution time is approximately 280 ms. However, during a cold start (eight cold start events are observed, highlighted in red, resulting in eight warm containers by the end of the experiment) – primarily due to the overhead of 

> 1https://aws.amazon.com/lambda/ 

> 2https://cloud.google.com/functions 

> 3https://azure.microsoft.com/en-us/services/functions 

> 4https://openwhisk.apache.org/ 

> 5https://www.openfaas.com/ 

> © 2025 IEEE. Personal use of this material is permitted. Permission from IEEE must be obtained for all other uses, in any current or future media, including reprinting/republishing this material for advertising or promotional purposes, creating new collective works, for resale or redistribution to servers or lists, or reuse of any copyrighted component of this work in other works. 

DOI: 10.1109/MASCOTS67699.2025.11283271 

loading the TensorFlow runtime and the object detection model – the response time for requests that triggered cold starts reaches approximately 10.5 seconds, corresponding to a 38 _×_ increase compared to the warm execution time. The earlier analysis [8], [9] shows a similar finding, with cold start delays on platforms like AWS Lambda and Microsoft Azure reported to be 16 _×_ –166 _×_ longer than the execution time. 

Most serverless platforms adopt a reactive, event-driven scheduling model that triggers a cold start as soon as no warm container is available, without deferring or batching incoming requests. While this strategy ensures responsiveness under load, it can lead to unnecessary delays. As illustrated in Figure 2, consider a request _r_ 1 arriving at time _t_ 1 and assigned to an idle warm container, completing at _t_ 1 + exec time. If a second request _r_ 2 arrives at _t_ 2 shortly before _r_ 1 completes, and no other warm container is available, the platform launches a cold container for _r_ 2, resulting in a significantly longer response time. However, if the system supports _shaping incoming requests_ to briefly wait for a soon-to-be-available warm container (i.e., ∆ _t_ = ( _t_ 1 + exec time) _− t_ 2), the cold start could be avoided, reducing the response time substantially. 



<!-- Start of picture text -->
Δt<br>r2 Cold Start<br>r1 Idle<br>t1 t2 t1 + exec time Time<br><!-- End of picture text -->

Fig. 2. Unnecessary cold start due to lack of short-term request shaping. 

**State of the art.** Existing efforts to reduce cold starts either shorten initialization time or limit their frequency. Cloud platforms like AWS Lambda and Azure Functions use static keep-alive windows (10–20 minutes) [10], which help under some workloads but are _blind to invocation patterns, wasting resources_ . Research efforts [8], [11]–[13] propose runtimelevel optimizations like container reuse and sharing, but often raise deployment challenges due to _security and isolation concerns_ . Others apply reactive or predictive prewarming [14], [15], yet often _lack coordination with request admission_ , causing delays under bursty workloads. We revisit these approaches in Section II. 

**Key insights and contributions.** We propose a novel Model Predictive Control (MPC) approach to mitigate cold start delays in serverless computing. MPC [16], [17] optimizes system behavior over a receding time horizon by solving a constrained optimization problem at each control step. It is particularly well-suited for this problem because it: (1) enables joint optimization over request admission, container provisioning, and reclamation; and (2) naturally incorporates resource constraints such as container pool size and service limits, avoiding overprovisioning and queue overload. 

Our key insight is that cold start delays can be reduced not just through provisioning, but also through predictive shaping, i.e., selectively deferring requests when short delays 

allow them to hit warm containers, thereby improving overall response latency. 

We model serverless scheduling as a predictive control loop. The MPC controller uses Fourier-based forecasting to anticipate incoming request rates and decides at each control step how many containers to prewarm, reclaim, or serve, balancing latency and resource efficiency. 

Our contributions are as follows: 

- **Predictive shaping for cold start mitigation.** We show that short deferrals of request dispatch when guided by predictive logic can significantly reduce cold starts without degrading responsiveness (Section V). 

- **An MPC-based serverless scheduler.** We formulate cold start mitigation as a constrained optimization problem and design an MPC controller that jointly manages provisioning, reclamation, and dispatch under forecasted load (Section III). 

- **Practical deployment in Apache OpenWhisk.** We implement our controller as a middleware layer that shapes and routes invocation traffic in real time, requiring no changes to the OpenWhisk core (Sections IV and V). 

- **Comprehensive evaluation on real and synthetic traces.** We benchmark our system using production and synthetic workloads, demonstrating consistent improvements in response latency and resource efficiency compared to state-of-the-art baselines (Section V). 

## II. RELATED WORK 

Prior work has tackled the cold start problem by either reducing its duration or minimizing its occurrence, typically falling into two main categories: 

First, runtime-level optimizations intervene at the resource management layer to reduce the need for repeated function initialization. Solutions in this area focus on enabling container reuse, retention, or inter-function sharing [8], [11]–[13]. For example, Zhou et al. [11] propose a multi-level container reuse strategy across functions with similar environments, employing deep reinforcement learning for optimal reuse. Similarly, Pagurus by Li et al. [12] mitigates cold start latency through inter-function container sharing, repurposing idle containers into lightweight zygotes for rapid specialization. Complementary efforts like Pan et al. [13] and Xiao et al. [8] focus on retention-aware caching frameworks, particularly in edge computing, to jointly manage container caching, request distribution, and cost. 

Second, scaling-based approaches aim to ensure warm container availability by managing function replicas either reactively, in response to current load fluctuations, or proactively, based on workload prediction [14], [15]. Wang et al. introduce LaSS [14], a serverless edge computing platform that uses a queuing theoretic model for reactive replica scaling to meet high-percentile latency SLOs. However, LaSS is fundamentally reactive, adjusting container counts at fixed intervals without incorporating direct forecasting or fine-grained request-level responsiveness. This can lead to suboptimal 

performance for bursty workloads, as requests arriving before scaling completes may still experience full cold start latency. Another notable work is IceBreaker by Roy et al. [15], a serverless scheduling framework that reduces cold start latency and keep-alive costs by leveraging heterogeneous servers for function prewarming. IceBreaker employs a function invocation predictor to capture time-varying patterns and a utilitybased placement strategy. Despite its predictive prewarming, IceBreaker does not coordinate prewarming completion with request dispatch, nor does it shape incoming requests to wait for warm containers. Consequently, requests arriving before a prewarmed container is truly ready still incur the full cold start latency. 

In this paper, we address these limitations by proposing a solution that leverages Model Predictive Control (MPC) to proactively schedule both container prewarming and request shaping, enabling faster adaptation to workload fluctuations and reducing the impact of cold starts. To forecast incoming request rates, we adopt a Fourier harmonic prediction method inspired by [15], and apply statistical clipping to constrain the predicted values within a plausible operational range, preventing overreaction to transient outliers in workload dynamics. 

## III. PROACTIVE SERVERLESS SCHEDULING WITH MODEL PREDICTIVE CONTROL 

In this section, we present the architecture of the MPCbased proactive scheduler for serverless computing. Figure 3 illustrates the main components and demonstrates how the scheduler interacts with an OpenWhisk deployment on a Kubernetes cluster. We assume that Prometheus<sup>6</sup> and Grafana Loki<sup>7</sup> are deployed on the cluster: Prometheus is used to collect system metrics such as invocation rates and the number of active containers, while Loki is used to trace container behavior and determine when a container completes an activation. 



<!-- Start of picture text -->
queue length<br>OpenWhisk on<br>Kubernetes cluster<br>MPC-based scheduler<br>Requests s= {s0, s1, ...}<br>historical s= {s0, s1, ...}<br>rate Invocation<br>Forecast Dispatch<br>systemstate Optimizer xr PrewarmReclaim xr<br><!-- End of picture text -->

Fig. 3. MPC-based proactive serverless scheduling architecture. 

In essence, the MPC scheduler is executed at every control interval ∆ _t_ , following the sequence: **1 Forecast future invocations** : the Invocation Forecast component uses historical metrics (e.g., invocation rate) from Prometheus to predict the number of incoming requests over the next _H_ time steps; 

> 6https://prometheus.io/ 

> 7https://grafana.com/oss/loki/ 

**2 Optimization** : Based on the forecast, the MPC solves an optimization problem over the _H_ -step horizon to determine how many containers to prewarm per time step, whether to reclaim idle containers, and how many requests to dispatch; and **3 Execute current-step actions** : From the optimized plan, only the control actions for the current time step are executed via the corresponding actuators (dispatch, prewarm, reclaim), which interact with the OpenWhisk platform. Below, we present the components involved in each process. 

## _A. Invocation Forecast_ 

At step **1** of the control cycle, the scheduler forecasts incoming function invocations over a prediction horizon of H time steps. Prior work [10], [18] has shown that many serverless workloads exhibit periodic patterns that evolve over time. Traditional models such as histograms and ARIMA often struggle with such variability [15]. To address this, we adopt a Fourier-based extrapolation method [19], which captures multiple frequency components and offers greater robustness to shifting periodicity, enabling more accurate forecasting of both invocation timing and concurrency. We emphasize that forecasting is not the central contribution of this work. Rather, we employ and extend the predictor proposed in [15] to better align with the needs of our scheduling framework. 

The forecast at time step _t_ is given by: 



where _at_<sup>2</sup> + _bt_ + _c_ represents the quadratic trend estimated from historical data; _Ai_ and _ϕi_ denote the amplitude and phase of the _i_ -th harmonic component; _fi_ is the corresponding frequency obtained from the discrete Fourier transform; and _k_ is the number of harmonics used in the reconstruction. 

While Fourier-based forecasts effectively capture periodic trends, they are unbounded and can return negative or overly large values, especially when trained on short or noisy histories [20]. To improve robustness under non-stationary conditions, we apply _statistical clipping_ [21] to constrain predictions within a realistic and safe operating range: 



Here, _λ_<sup>ˆ</sup> ( _t_ ) denotes the raw forecast at time _t_ , _µ_ and _σ_ represent the mean and standard deviation of recent request rates, and _γ_ is a tunable confidence parameter. We implement the Fourier-based forecasting method in Python using standard scientific libraries, including NumPy for polynomial trend fitting and Fast Fourier Transform (FFT). 

## _B. Optimizer_ 

In step **2** , the MPC controller solves an optimization problem over a horizon of _H_ time steps to make scheduling decisions. We present below the individual cost components that define the objective function. For clarity, Table I summarizes the variables and parameters used in the MPC formulation. 

TABLE I 

SUMMARY OF VARIABLES AND PARAMETERS USED IN THE MPC FORMULATION 

|**Symbol**|**Description**|
|---|---|
|_qk_|Queue length at time step _k_<br>|
|_wk_|Number of warm containers at time step _k_|
|_sk_|Number of requests served at time step _k_|
|_xk_|Number of cold starts initiated at time step _k_|
|_rk_|Number of containers reclaimed at time step _k_|
|_λk_<br>|Number of incoming requests at time step _k_|
|_µ_= 1_/L_warm|Service rate of a warm container|
|_w_max<br>|Maximum number of warm containers|
|readyCold(_k_)|Cold-started containers ready at time _k_|
|_L_warm|Warm container execution latency (s)|
|_L_cold|Cold start initialization latency (s)|
|_α_|Cost weight for cold start delay|
|_β_|Cost weight for warm queue wait|
|_γ_|Cost weight for overprovisioning|
|_δ_|Cost weight for initiating cold starts|
|_η_|Reward weight for reclaiming containers|
|_ρ_1_, ρ_2|Weights for provisioning smoothness|



_1) Cold delay penalty:_ Let ColdDelay _k_ denote the latency penalty at time step _k_ incurred when the number of available warm containers is insufficient to serve all incoming requests. 

We define _L_ cold as the initialization latency of a cold container, and _L_ warm as the execution time in a warm container. Let _λk_ represent the number of incoming requests at time step _k_ , and let _wk_ denote the number of warm containers available at that time. The cold delay penalty at time step _k_ is computed as: 

where _xk_ is the number of cold starts initiated at time step _k_ . 

_4) Overprovisioning penalty:_ We define OverProvision _k_ as a penalty term that discourages excessive allocation of warm containers at time step _k_ : 



Here, _γ ≥_ 0 is a tunable weight that penalizes unused capacity. Increasing _γ_ encourages the controller to minimize overprovisioning, while a lower value allows more slack in warm container allocation to prioritize responsiveness. 

_5) Reclaim Reward:_ We define ReclaimReward _k_ as a reward that encourages the controller to reclaim unused warm containers, which is computed as: 



Here, _η ≥_ 0 is a reward weight that incentivizes reclaiming idle containers, and _rk_ is the number of containers reclaimed at time step _k_ . 

_6) Smoothness Penalty:_ Finally, to avoid abrupt changes in provisioning, we define Smoothness _k_ as a penalty on fluctuations in cold start and warm container counts. This term aims to stabilize the system and prevent oscillatory behavior, and is calculated as: 



ColdDelay _k_ = _α ·_ max (0 _, λk − µ · wk_ ) _·_ ( _L_ cold + _L_ warm) (3) 

where _µ_ = _L_ warm1<sup>istheservicerateperwarmcontainer,and</sup> _α ≥_ 0 is a tunable cost weight that determines the importance of cold start penalties. Setting _α_ = 0 disables cold start awareness in the controller, while higher values encourage more aggressive prewarming to avoid latency. _2) Queue waiting cost:_ Let WaitCost _k_ denotes the accumulated delay experienced by queued requests, assuming each must wait for a warm container available. We estimate WaitCost _k_ as: 

Here, _ρ_ 1 and _ρ_ 2 are tunable weights that penalize variations in the number of warm containers _wk_ and cold starts _xk_ , respectively. 

Having defined the individual cost components, we now formulate the overall objective of the MPC as minimizing the total cost over a prediction horizon of _H_ time steps. The objective balances response latency and resource usage, while also discouraging frequent changes in the number of active containers to reduce management overhead and system instability: 



where _β ≥_ 0 is a tunable cost weight that determines the penalty assigned to request queuing, and _qk_ is the number of queued requests at time step _k_ . 

_3) Cold start cost:_ Let ColdStartCost _k_ denote the overhead of initializing new containers when no warm ones are available. This cost includes container allocation, function loading, runtime setup, and dependency initialization (e.g., ML model loading), making it significantly more expensive than warm execution. To discourage frequent cold starts unless necessary, we introduce a tunable weight _δ ≥_ 0 that balances responsiveness and efficiency in the MPC objective. 

Accordingly, the cold start cost at time step _k_ is estimated as: 





At each control step _k ∈{_ 0 _,_ 1 _, . . . , H −_ 1 _}_ , the MPC decides the number of cold starts _xk_ , container reclaims _rk_ , and requests to serve _sk_ , while updating the system states: queue length _qk_ and number of warm containers _wk_ . These decisions are subject to the following system dynamics and constraints: 

|_qk_+1 =_qk_+_λk −sk_|(queue dynamics)|(10)|
|---|---|---|
|_wk_+1 =_wk_+readyCold(_k_)_−rk_|(warm container up|date)<br>(11)|
|_sk ≤_min(_qk, µ · wk_)|(serving capacity)|(12)|
|_rk ≤wk_|(reclaim bound)|(13)|
|0_≤xk ≤w_max|(cold start limits)|(14)|
|0_≤rk ≤wk_|(reclaim limits)|(15)|
|0_≤wk ≤w_max|(warm container li|mits)<br>(16)|
|0_≤sk, qk_|(non-negativity)|(17)|
|_rk · xk_ = 0|(mutual exclusivity|)<br>(18)|



Here, 



models the number of cold-started containers that become available at time step _k_ , based on a discrete cold start delay of _D_ steps, where _D_ = _⌊L_ cold _/_ ∆ _t⌋_ and ∆ _t_ is the MPC control interval. 

To solve the MPC optimization problem, we use the cvxpy library [22], a Python-embedded modeling language for convex optimization. 

## _C. Actuators_ 

At step **3** in the control cycle, the actuators: _dispatch_ , _prewarm_ , and _reclaim_ serve as the operational interface between the MPC controller and the OpenWhisk platform. Given the MPC decisions at time step _k_ , specifically _sk_ , and either _xk_ or _rk_ (which are mutually exclusive as per constraint (18)), these actuators execute the selected actions on the platform. 

**The** **_prewarm_ actuator** , exposed via the function launchColdContainers( _xk_ ), triggers container initialization by issuing _xk_ parallel wsk CLI calls to the function (specified via function_name) with a custom forcePrewarm=true parameter, as shown in Listing 1. The serverless function’s handler checks this flag and skips actual execution logic, enabling lightweight warmup. 

cmd = f"seq {count} | xargs -P{parallelism} -I{{}} wsk -i action invoke \ {function_name} --param forcePrewarm true" result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) 

Listing 1. Prewarm count = _xk_ containers. 

**The** **_dispatch_ actuator** , implemented as dispatchRequests( _sk_ ), is described in Algorithm 1. It sends _sk_ requests in batches, based on the number of available warm containers _wk_ (line 2-5). Requests are retrieved from a Redis queue<sup>8</sup> (line 3) and dispatched asynchronously to the OpenWhisk API endpoint (line 5). 

**Algorithm 1** Dispatch Requests **Require:** Requests to send _sk_ **Require:** Number of warm containers _wk_ 1: **while** _sk >_ 0 **do** 2: _B ←_ min( _sk, wk_ ) _▷_ Batch size for this round 3: _R ←_ next _B_ requests from queue 4: **for all** _r ∈ R_ **in parallel do** 5: submitRequestAsync( _r_ ) 6: **end for** 7: _sk ← sk −|R|_ 8: **end while** 

**Algorithm 2** Reclaim Idle Function Containers 

- 1: _P ←_ rankPods( _rk_ ) 2: **if** _P_ = _∅_ **then** 3: **exit:** no container available 4: **end if** 5: _L ←_ listRunningFunctionPods() 6: _S ←{p ∈ P | p ∈/ L} ▷_ Safe to reclaim 7: **for all** _p ∈ S_ **do** 8: drainAndReclaimPod( _p_ ) 9: **end for** 

**The** **_reclaim_ actuator** , exposed via the function reclaimIdleContainers( _rk_ ), must ensure that no in-flight activations are disrupted during reclamation. The full logic is shown in Algorithm 2. To guarantee safety, it restricts reclamation to containers confirmed to be idle: containers are ranked using a composite score that prioritizes _low CPU/memory usage and long idle duration_ , which helps reduce churn and prevent thrashing. 

From this ranking, the top _rk_ containers are selected as candidates (line 1). Before reclaiming, the system verifies that each candidate is no longer processing requests by querying the Loki log aggregation system. Specifically, it checks for the log message [MessagingActiveAck] posted completion of activation to confirm that the container has completed all assigned in-flight activations (line 5- 6). Only containers that pass this check are considered safe and are reclaimed accordingly (lines 7–9). 

## IV. EXPERIMENTAL SETUP 

**Experimental Platform.** We deploy a single-node Kubernetes cluster using k3s on a server running Ubuntu 20.04, equipped with an AMD Opteron 6272 CPU (32 vCPUs at up to 2.1 GHz) and 48 GB of RAM. The node serves as both control plane and worker, with OpenWhisk installed to support serverless execution. A monitoring stack comprising Prometheus and Grafana Loki is also deployed to expose APIs for collecting metrics and logs from the MPC controller. As our contribution centers on scheduling logic and request shaping rather than container placement or distributed orchestration, a single- 

8https://redis.io/glossary/redis-queue/ 

node deployment is sufficient to validate the proposed control strategy. 

To avoid resource contention and ensure stable, interferencefree evaluation of scheduling decisions, we deploy the MPC scheduler and request generator on a separate local machine (Ubuntu 20.04, Intel Core i5-13500, 32 GB RAM) on the same network as the Kubenertes cluster. 

**Function.** We implement a serverless function image for object detection using EfficientDet [6]. On cold start, the function initializes the TensorFlow library, which dominates the startup latency. Profiling shows that warm executions average _L_ warm = 280 ms, while the initialization time due to cold starts is approximately _L_ cold = 10 _._ 5 seconds. 

Each replica is limited to 256 MB of memory and an estimated CPU usage of 0.5 vCPU. Under these constraints, the serverless platform can support up to 64 concurrent replicas, bounded by CPU resources. 

**Workload.** We implement a configurable workload generator to produce invocation requests to the serverless platform. The generator allows control over both the request arrival rate and the number of requests sent concurrently. To create interlarrival rate, we use: 

- **Azure Function Traces.** We extract inter-arrival times from real-world invocation logs collected over two weeks from Microsoft Azure Functions [10]. 

- **Synthetic Workload.** We synthesize inter-arrival patterns by randomly sampling burst durations (1–5) s, idle periods (50–800) s, and request rates (5–300) req/s. 

**Baseline Approaches.** We compare our MPC scheduler against the following baseline strategies: 

- **OpenWhisk Default Policy.** By default, OpenWhisk triggers a cold start when no warm container is available to handle an invocation. It keeps function containers in a warm state for up to 10 minutes after their most recent use. 

- **IceBreaker** [15] reduces cold starts and keep-alive costs through proactive prewarming and predictive function placement. It employs Fourier-based forecasting to estimate future invocations. Its key innovation lies in leveraging server heterogeneity: functions are initially placed on low-end servers for extended warm retention and later migrated to high-end servers as invocation likelihood increases. Since our evaluation assumes a single-server setup, we adapt IceBreaker to a homogeneous environment by disabling server-type–specific placements. 

**Evaluation Metrics.** We evaluate the proposed approach and the baselines using the following metric: 

- **Total response time per request** : the end-to-end latency observed by the user, defined as the sum of queueing delay, cold start time, and execution time. 

- **Resource efficiency** : measured by the number of containers and total keep-alive duration, reflecting the cost of maintaining warm containers to handle incoming requests. 



<!-- Start of picture text -->
1 2<br>ARIMA Error<br>0 1 Fourier Error<br>0<br>1<br>1<br>2 ARIMA Error<br>Fourier Error 2<br>1000 1500 2000 2500 3000 0 2000 4000<br>Time Step Time Step<br>(a) Microsoft Azure Function (b) Synthetic data<br>Normalized Error Normalized Error<br><!-- End of picture text -->

Fig. 4. Forecast error of Fourier and ARIMA models in two experiments: (a) with Microsoft Azure Functions and (b) with synthetic data. 



<!-- Start of picture text -->
23.6% 82.9% 85.5% 82.6%<br>20.6% 80<br>20 17.9% 17.1% 18.0% 67.7%<br>15 13.9% 60 51.1%<br>45.4%<br>10 40<br>5 MPC Scheduler 20 MPC Scheduler<br>IceBreaker IceBreaker<br>0 0<br>Average 90th Percentile 95th Percentile Average 90th Percentile 95th Percentile<br>(a) Microsoft Azure Function (b) Synthetic data<br>% Improvement  Over OpenWhisk % Improvement  Over OpenWhisk<br><!-- End of picture text -->

Fig. 5. Percentage improvement in total response time (average, 90th, and 95th percentiles) over OpenWhisk. (a) with Microsoft Azure Functions; (b) with synthetic data. 

## V. EVALUATION 

## _A. Prediction accuracy_ 

Before evaluating the full control loop, we isolate the forecasting component to assess its accuracy, as accurate prediction of request arrival rates is critical for enabling proactive and effective scheduling decisions. To this end, we evaluate the predicted versus actual arrival rates in two experimental scenarios: using real-world traces from Azure Functions, and using synthetically generated arrival patterns. We implement the ARIMA time series model as a baseline for comparison with the Fourier-based forecasting approach. Figure 4 presents the forecast errors of the two methods. In both experiments, the Fourier-based predictor outperforms ARIMA. Specifically, on the Azure Function dataset, Fourier achieves an accuracy of 86.2%, compared to 82.5% for ARIMA. On the synthetic dataset, both methods achieve comparable accuracy (ARIMA: 95.9%, Fourier: 95.3%). Notably, the runtime of the Fourier predictor (0.1 ms) is over 100× faster than ARIMA (10 ms) when performing rolling updates and prediction. 

## _B. Total response time per request_ 

All three approaches are evaluated under the same arrival patterns over a 60-minute period, using both the Azure Function trace and synthetic workloads. Each experiment begins with no warm containers available on the OpenWhisk platform. Figure 5 shows the percentage improvement in end-toend response time over OpenWhisk’s default policy for the two approaches: MPC-Scheduler and IceBreaker. 

The high accuracy of the Fourier-based forecasting enables both IceBreaker and MPC-Scheduler to proactively prewarm 









a) Microsoft Azure Function 



<!-- Start of picture text -->
b) Synthetic data<br><!-- End of picture text -->

a) Microsoft Azure Function 

b) Synthetic data 

Fig. 6. Percentage reduction in total warm container usage by MPC-Scheduler and IceBreaker compared to OpenWhisk’s default policy, measured at 1- minute intervals. (a) with Microsoft Azure Functions; (b) with synthetic data. 

Fig. 7. Percentage reduction in keep-alive duration achieved by MPCScheduler and IceBreaker, relative to OpenWhisk’s default policy. 

an appropriate number of function replicas, effectively mitigating cold start overhead in both the Azure trace and synthetic workload experiments. In the experiment using the Azure Function trace, the extracted inter-arrival rates exhibit steady, non-bursty behavior, resulting in limited improvement in response time compared to the default OpenWhisk policy. Specifically, MPC-Scheduler achieves a 17.9% reduction in mean response time, while the improvements in the 90th and 95th percentile tail latencies are more pronounced at 20.6% and 23.6%, respectively. The IceBreaker approach also shows improvements in end-to-end response time compared to the default OpenWhisk policy, with reductions of 13.9% in average response time, 17.1% in the 90th percentile, and 18% in the 95th percentile tail latencies. 

Under the synthetic workload, where request arrivals exhibit pronounced burstiness, i.e., many invocations occur within short time intervals, the improvements in response time over the default OpenWhisk policy are substantially greater for both MPC-Scheduler and IceBreaker. MPC-Scheduler achieves reductions of 82.9%, 85.5%, and 82.6% in average, 90th percentile, and 95th percentile response times, respectively. IceBreaker also improves performance, with corresponding reductions of 67.7%, 51.1%, and 45.4%. 

In both experiments, MPC-scheduler consistently outperforms IceBreaker, despite both approaches employing the same underlying Fourier-based forecasting technique. This improvement is largely attributed to MPC’s joint optimization of request dispatching and container prewarming. By briefly queuing requests and aligning them with available warm containers, MPC-Scheduler effectively avoids unnecessary cold starts. In contrast, IceBreaker immediately forwards incoming requests to OpenWhisk, which can result in cold starts if no warm containers are available, even when forecasts are accurate. 

_These observations highlight that short deferrals of request dispatch, when guided by predictive logic, can significantly reduce the impact of cold starts without compromising responsiveness._ 

## _C. Resource usage and Keep-alive cost_ 

We collect the number of warm containers used by all three approaches at 1-minute intervals throughout the experiments. To quantify the relative change in resource usage, we compute the percentage difference in warm container count at each time 

step. Additionally, for each container invoked by the serverless platform, we track the duration from its last activation until reclamation to evaluate the effective keep-alive time. 

Figure 6 presents the reduction in warm container usage achieved by MPC-Scheduler and IceBreaker, relative to the default OpenWhisk policy. Figure 7 further illustrates the corresponding reduction in keep-alive duration for the two approaches compared to OpenWhisk. 

In both experiments, accurate invocation forecasting enabled timely container reclamation, significantly improving resource efficiency. Under the Azure Function trace, MPC-Scheduler reduced the total number of warm containers by 34.8% and cut keep-alive duration by 64.3%, while IceBreaker achieved reductions of 17.4% and 43%, respectively – relative to OpenWhisk’s default 10-minute keep-alive policy. Under the synthetic bursty workload, although warm containers were more actively utilized due to high request arrival rates (resulting in less idle time), both MPC-Scheduler and IceBreaker still reduced resource usage relative to OpenWhisk. Specifically, MPC-Scheduler and IceBreaker reduced warm container usage by 19.1% and 14.8%, respectively, while also shortening keepalive durations by 15.7% and 11.3%. 

IceBreaker’s gains rely on exploiting server heterogeneity for cost-effective function placement. However, in our homogeneous testbed, its utility function loses this advantage, limiting its ability to minimize keep-alive costs and maintain warm containers under tight budgets. This limitation largely explains why IceBreaker underperforms compared to MPCScheduler in our experimental setting. 

_Overall, the observations show that the MPC-Scheduler effectively reduces resource usage and shortens function keepalive durations, thereby lowering the overall cost of maintaining warm containers._ 

## _D. Control overhead_ 

Our MPC-based scheduler adds minimal overhead, making it suitable for real-time deployment. At each control interval, it performs two tasks: forecasting future invocation rates and solving the optimization problem. As shown in Figure 8, the forecasting step is fast, averaging just 0.1 ms, while the optimizer completes in 38ms on average. 

_These results demonstrate that the control logic can operate at fine-grained intervals without introducing a performance bottleneck._ 



<!-- Start of picture text -->
60<br>40<br>20<br>0<br>Forecast Optimizer<br>Execution Time (ms)<br><!-- End of picture text -->

Fig. 8. Breakdown of execution time for each component of the MPC scheduler. 

## _E. Limitation_ 

The effectiveness of the MPC scheduler relies on the accuracy of the invocation forecast, as these predictions guide decisions on how many requests to serve and how many function replicas to prewarm. Furthermore, as observed in our experiments, when the request arrival pattern is steady – such as in typical Azure Functions workloads – the benefits of MPC in reducing cold start latency become marginal. In these scenarios, even OpenWhisk’s default behavior of keeping containers warm for up to 10 minutes is generally sufficient to handle regular traffic without triggering frequent cold starts. 

Another important consideration is MPC parameter tuning, as performance is sensitive to choices like the control horizon and objective weights. Our parameters were empirically calibrated, but this ad hoc approach is workload-specific. Future work should explore automated online tuning (e.g., Bayesian optimization, reinforcement learning, meta-learning) to adapt under dynamic workloads. 

## VI. CONCLUSION AND FUTURE WORK 

Serverless computing simplifies cloud deployment with an event-driven model that hides infrastructure complexity. Yet, cold start delays remain a major challenge for latency-sensitive workloads. 

This paper introduced a novel scheduling framework based on MPC to proactively reduce cold start impact and minimize end-to-end latency. By forecasting future request arrivals, the controller jointly optimizes container prewarming and request shaping, enabling smoother load handling and improved responsiveness. We implemented our approach in Apache OpenWhisk and evaluated it on a Kubernetes-based testbed. Results show that MPC-Scheduler outperforms state-of-theart approaches, achieving up to 85% lower 90th percentile tail latency and 34% fewer resource usages compared to the default OpenWhisk policy. 

Future work includes extending this framework to heterogeneous multi-platform orchestration, enabling coordinated scheduling across hybrid or edge–cloud deployments. 

## REFERENCES 

- [1] M. S. Aslanpour, A. N. Toosi, C. Cicconetti, B. Javadi, P. Sbarski, D. Taibi, M. Assuncao, S. S. Gill, R. Gaire, and S. Dustdar, “Serverless edge computing: vision and challenges,” in _Proceedings of the 2021 Australasian computer science week multiconference_ , pp. 1–10, 2021. 

- [2] E. Jonas, J. Schleier-Smith, V. Sreekanti, C.-C. Tsai, A. Khandelwal, Q. Pu, V. Shankar, J. Carreira, K. Krauth, N. Yadwadkar, _et al._ , “Cloud programming simplified: A berkeley view on serverless computing,” _arXiv preprint arXiv:1902.03383_ , 2019. 

- [3] Z. Hong, J. Lin, S. Guo, S. Luo, W. Chen, R. Wattenhofer, and Y. Yu, “Optimus: warming serverless ml inference via inter-function model transformation,” in _Proceedings of the Nineteenth European Conference on Computer Systems_ , pp. 1039–1053, 2024. 

- [4] G. Merlino, G. Tricomi, L. D’agati, Z. Benomar, F. Longo, and A. Puliafito, “Faas for iot: Evolving serverless towards deviceless in i/oclouds,” _Future Generation Computer Systems_ , vol. 154, pp. 189–205, 2024. 

- [5] Y. Sui, H. Yu, Y. Hu, J. Li, and H. Wang, “Pre-warming is not enough: Accelerating serverless inference with opportunistic pre-loading,” in _Proceedings of the 2024 ACM Symposium on Cloud Computing_ , pp. 178–195, 2024. 

- [6] M. Tan, R. Pang, and Q. V. Le, “Efficientdet: Scalable and efficient object detection,” in _Proceedings of the IEEE/CVF conference on computer vision and pattern recognition_ , pp. 10781–10790, 2020. 

- [7] C. Nguyen, E. Seo, M. Zahid, O. Larsson, F. T. Pokorny, and E. Elmroth, “tinykube: A middleware for dynamic resource management in cloudedge platforms for large-scale cloud robotics,” in _IEEE/IFIP 2025, The 38th IEEE/IFIP Network Operations and Management Symposium (NOMS), Honolulu, HI, USA, May 12-16, 2025_ , 2025. 

- [8] K. Xiao, S. Yang, F. Li, L. Zhu, X. Chen, and X. Fu, “Making serverless not so cold in edge clouds: A cost-effective online approach,” _IEEE Transactions on Mobile Computing_ , vol. 23, no. 9, pp. 8789–8802, 2024. 

- [9] A. Bauer, M. Gonthier, H. Pan, R. Chard, D. Grzenda, M. Straesser, J. G. Pauloski, A. Kamatar, M. Baughman, N. Hudson, _et al._ , “An empirical investigation of container building strategies and warm times to reduce cold starts in scientific computing serverless functions,” in _2024 IEEE 20th International Conference on e-Science (e-Science)_ , pp. 1–10, IEEE, 2024. 

- [10] M. Shahrad, R. Fonseca, I. Goiri, G. Chaudhry, P. Batum, J. Cooke, E. Laureano, C. Tresness, M. Russinovich, and R. Bianchini, “Serverless in the wild: Characterizing and optimizing the serverless workload at a large cloud provider,” in _2020 USENIX annual technical conference (USENIX ATC 20)_ , pp. 205–218, 2020. 

- [11] A. C. Zhou, R. Huang, Z. Ke, Y. Li, Y. Wang, and R. Mao, “Tackling cold start in serverless computing with multi-level container reuse,” in _2024 IEEE international parallel and distributed processing symposium (IPDPS)_ , pp. 89–99, IEEE, 2024. 

- [12] Z. Li, L. Guo, Q. Chen, J. Cheng, C. Xu, D. Zeng, Z. Song, T. Ma, Y. Yang, C. Li, _et al._ , “Help rather than recycle: Alleviating cold startup in serverless computing through _{_ Inter-Function _}_ container sharing,” in _2022 USENIX Annual Technical Conference (USENIX ATC 22)_ , pp. 69– 84, 2022. 

- [13] L. Pan, L. Wang, S. Chen, and F. Liu, “Retention-aware container caching for serverless edge computing,” in _IEEE INFOCOM 2022-IEEE Conference on Computer Communications_ , pp. 1069–1078, IEEE, 2022. 

- [14] B. Wang, A. Ali-Eldin, and P. Shenoy, “Lass: Running latency sensitive serverless computations at the edge,” in _Proceedings of the 30th international symposium on high-performance parallel and distributed computing_ , pp. 239–251, 2021. 

- [15] R. B. Roy, T. Patel, and D. Tiwari, “Icebreaker: Warming serverless functions better with heterogeneity,” in _Proceedings of the 27th ACM International Conference on Architectural Support for Programming Languages and Operating Systems_ , pp. 753–767, 2022. 

- [16] C. E. Garcia, D. M. Prett, and M. Morari, “Model predictive control: Theory and practice—a survey,” _Automatica_ , vol. 25, no. 3, pp. 335–348, 1989. 

- [17] W. H. Kwon and S. H. Han, _Receding horizon control: model predictive control for state models_ . Springer Science & Business Media, 2005. 

- [18] A. Bauer, H. Pan, R. Chard, Y. Babuji, J. Bryan, D. Tiwari, I. Foster, and K. Chard, “The globus compute dataset: An open function-as-aservice dataset from the edge to the cloud,” _Future Generation Computer Systems_ , vol. 153, pp. 558–574, 2024. 

- [19] P. P. Dyke and P. Dyke, _An introduction to Laplace transforms and Fourier series_ , vol. 517. Springer, 2001. 

- [20] R. Yang, L. Cao, J. YANG, _et al._ , “Rethinking fourier transform from a basis functions perspective for long-term time series forecasting,” _Advances in Neural Information Processing Systems_ , vol. 37, pp. 8515– 8540, 2024. 

- [21] A. Fr¨omming, L. H¨aring, and A. Czylwik, “Spectral properties of clipping noise,” _Mathematics_ , vol. 9, no. 20, p. 2592, 2021. 

- [22] S. Diamond and S. Boyd, “Cvxpy: A python-embedded modeling language for convex optimization,” _Journal of Machine Learning Research_ , vol. 17, no. 83, pp. 1–5, 2016. 

