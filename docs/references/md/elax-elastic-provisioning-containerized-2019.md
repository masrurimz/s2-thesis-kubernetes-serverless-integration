---
# --- bibliographic record ---
entry_type: inproceedings
title: "ElaX: Provisioning Resource Elastically for Containerized Online Cloud Services"
authors:
  - "Yanan Yang"
  - "Laiping Zhao"
  - "Zhigang Li"
  - "Lihai Nie"
  - "Peiqi Chen"
  - "Keqiu Li"
year: 2019
venue: "2019 IEEE 21st International Conference on High Performance Computing and Communications; IEEE 17th International Conference on Smart City; IEEE 5th International Conference on Data Science and Systems (HPCC/SmartCity/DSS)"
volume: ""
issue: ""
pages: "1987-1994"
publisher: "IEEE"
doi: "10.1109/HPCC/SmartCity/DSS.2019.00274"
arxiv: ""
url: "https://doi.org/10.1109/HPCC/SmartCity/DSS.2019.00274"

# --- archive record ---
source_pdf: elax-elastic-provisioning-containerized-2019.pdf
source_sha256: 6aec58908ee68d04790535cd7372f523ea5abe36261de90fb95914ed2e964170
pdf_pages: 10
converted: 2026-09-13
record_source: crossref
key_insight: "LSTM predictor + resource reservation + online feedback controller (thesis base algorithm)"
first_page: "ElaX: Provisioning Resource Elastically for Containerized Online Cloud Services Yanan Yang, Laiping Zhao*, Zhigang Li, Lihai Nie, Peiqi Chen, and Keqiu Li Tianjin Key Laboratory of Advanced Networking"
---
# ElaX: Provisioning Resource Elastically for Containerized Online Cloud Services 

Yanan Yang, Laiping Zhao*, Zhigang Li, Lihai Nie, Peiqi Chen, and Keqiu Li Tianjin Key Laboratory of Advanced Networking, College of Intelligence and Computing, Tianjin University, China 

**_Abstract_ —To reduce the cost of online cloud services, service providers often employ the elastic approach that allows tenants to “scale out” or “scale up” their applications at runtime. However, the traditional virtual machine-based approach cannot meet the fine-grained fluctuating demand due to its slow startup time and high reconfiguration cost. To address this challenge, we present** **_ElaX_ , an online service manager that minimizes the resource provisioning cost for containerized online services while guaranteeing their tail latency requirement.** **_ElaX_ designs a workloadaware resource allocation mechanism for containerized online services through the collaboration of three key components: First,** **_workload predictor_ is able to precisely predict the workload in periodic scenario, through a LSTM (Long Short-Term Memory) network; Second,** **_resource reservation_ allocates the just-right amount of resource supporting the predicted workload, using the combination of both scale-up and scale-out operations; Third,** **_online controller_ guarantees the tail latency requirement through a feedback-based control method, and further reduces the provisioning cost through resource reclamation. Our experiments on the two production workloads demonstrate that, when compared with existing methods,** **_ElaX_ can reduce the average resource over-provisioning cost by more than 32.6% while guaranteeing the tail latency requirement.** 

**_Index Terms_ —Cloud Computing, Resource provisioning, Tail Latency, Containers** 

## I. INTRODUCTION 

Cloud computing frees service developers from complex and complicated maintenance work on hardware infrastructure, through simply renting the needed computing capacities (e.g., servers, storage, network.) from cloud providers, and paying for resource on demand. While users would always like to cut the cost of renting through precise shaping of resource requirements of their services, cloud providers cannot offer stable quality of services (QoS) due to the constantly changing workload [4] and unpredictable resource contention from the tenants sharing the cloud [6, 13, 21]. Hurting user experience is rather costly, for example, just one-second slowdown of page loading could cost $1.6 billion in sales of Amazon [10]. In this case, users have to resort to resource overprovisioning for guaranteeing their QoS. However, wasteful over-provisioning results in low resource utilization, thereby increasing the cost of cloud services. For example, resource reservations by Twitter could reach up to 80% of total capacity, while their production cluster’s CPU utilization is constantly below 20% [7]. Similarly, traces from both Google [28] and Aliyun [23] showed that they merely achieve aggregate CPU 

*Corresponding author: laiping@tju.edu.cn 

utilization of 25-35% and aggregate memory utilization of 40%. 

How to reduce the resource provisioning cost while guaranteeing the QoS is a significant challenge. To address this challenge, the existing work [12, 30] have been able to scale service cluster through increasing or decreasing the number of virtual machines (VMs), according to the fluctuating workload. However, workload-aware resource scaling systems [20, 31] support resource scaling only for batch jobs, and can not be directly applied to resource allocation for online service due to the long-term running feature. Even for online services, the VM-based scaling approaches are rather costly, since starting or reconfiguring a VM usually takes minutes, which is far longer than the millisecond-level tail latency SLO (service level objective) [5, 19]. If the workload towards a service changes significantly in a short time, a reactive VM scaling operation could be too slow to take effect. Fortunately, the advent of the lightweight container model [9] enables runtime resource reconfiguration in a small-time granularity, making scaling much simple and easy. _EFRA_ [4] supports resource scaling-up for container-enabled cloud systems. However, their solution can only applicable in workload with strong stable periodic features, and does not support the flexible scalingout and scaling-up combined decision. In addition, while Kubernetes [2] can both scale-out or scale-up the service cluster, its feedback-based approach cannot strictly guarantee the SLO. 

In this work, we aim to further reduce the resource provisioning cost for long-running online services with the tail latency SLO guarantee. Since reducing the provisioned resources highly risk SLO violations, when and how many resources to scale should be very carefully decided. We suggest to scale the allocated resources both horizontally (scale-out) and vertically (scale-up), depending on the workload and cloud system status. There are several challenges towards this goal. First, although the production workload has shown periodic features, their periods are not always stable. Noises, like incremental periodical load, bursts and weekend drop, severely increases the prediction error, making the workload prediction extremely difficult. Second, given the workload estimates, how to derive the just-right amount of resources supporting this workload is also not easy. In particular, although the container technique provides a lightweight way for resource scaling, scaling-up and scaling-out still perform differently on startup costs. The optimal combination of scale-up and scale-out should be derived. Third, as the prediction error is inevitable, 



<!-- Start of picture text -->
10 4<br>25 40 3<br>History data History data QPS<br>20 Peak-basedPRESS 30 Peak-basedPRESS trend<br>EFRA EFRA 2<br>15<br>20<br>10<br>1<br>10<br>5<br>0 0 0<br>24 48 72 96 120 144 168 24 48 72 96 120 144 168 25 50 75 100<br>Time (hour) Time (hour) CPU utilization (%)<br>(a) Comparison of prediction results with ClarkNet (b) Comparison of prediction results with Calgary (c) Resource-Performance bottleneck<br>CPU utilization (%) CPU utilization (%) Performance (QPS)<br><!-- End of picture text -->

Fig. 1: The resource reservation by Peak, PRESS, EFRA under ClarkNet (a) and Calgary traces (b); The resource-performance bottleneck in Redis service node (c). 

how to guarantee the tail latency SLO under prediction error is also a challenge. 

We present _ElaX_ , a resource scaling engine that minimizes the resource provisioning cost for containerized online services while guaranteeing the tail latency SLO. _ElaX_ reduces the resource over-provisioning cost through a workload-aware resource scaling method. Compared with existing systems [4, 12, 30], _ElaX_ improves the prediction accuracy in nonstable periodic workload and supports the combined scalingup and scaling-out operation for minimizing the startup cost. It also integrates the feedback-based QoS management policy to avoid the possible SLO violations under prediction error. Our contributions can be summarized as follows: 

- 1) To improve the prediction accuracy under non-stable workload, we filter out the noises in the historical workload data series using the SSA (Singular Spectrum Analysis) method [26], and utilize a deep learning method to predict the future workload. The evaluation result shows that our method can improve the prediction accuracy significantly, especially for the non-stable periodical workload. 

- 2) We build a resource-performance model to characterize the relation between resource allocation and service throughput, directing the resource requirement for supporting the predicted workload. Then, we consider the resource-performance bottleneck and the heterogeneity of servers and derive the optimal combination of scaling-out and scaling-up operations for resource reservation. 

- 3) We employ a feedback-based online controller to avoid the possible SLO violations due to the prediction error and present a resource reclamation mechanism to reallocate the over-provisioned resources at a small-time granularity. 

- 4) <mark>We implement</mark> _<mark>ElaX</mark>_ <mark>based on Docker engine [3] and evaluate its eff</mark> i <mark>ciency in</mark> _<mark>redis</mark>_ <mark>cluster and</mark> _<mark>e-commerce</mark>_ <mark>with two different production workloads. Experimental results show that, when compared with existing four methods,</mark> _<mark>ElaX</mark>_ <mark>reduces the average resource over-provisioning cost by</mark> _<mark>></mark>_ <mark>32.6% while guaranteeing the tail latency SLO</mark> . 

## II. MOTIVATION 

The periodic feature of access load towards an online service has been detected and confirmed repeatedly [4]. It is straightforward to reduce the over-provisioning cost through a workload-aware resource allocation method. However, previous work either is rather conservative in prediction, leaving a significant space for further reducing the cost, or underestimates the workload, resulting in SLO violations. We deploy an online service of _redis_ [27] cluster, and experimentally evaluate the four existing resource scaling methods (including _Peak_ [11], _PRESS_ [12], _EFRA_ [4] and _Kubernetes_ [2]) using two production workloads _ClarkNet_ and _Calgary_ [18] as the request workload modes. The results are showed in Table I. 

TABLE I: Comparison of existing methods 

|**Method**|**Predictio**|**n Error**|**SLO**|**Sc**|**ale**|
|---|---|---|---|---|---|
||**ClarkNet**|**Calgary**|**Guarantee**|**up**|**out**|
|Peak|82%|148%|Yes|Yes|No|
|PRESS|5%|18%|No|Yes|No|
|EFRA|37%|73%|Yes|Yes|No|
|Kubernetes|–|–|No|Yes|Yes|
|ElaX|6%|15%|Yes|Yes|Yes|



**Peak** [11] always chooses the maximum workload from the corresponding point in each historical period as the predicted value. Although this conservative policy can be very safe in enforcing the tail latency SLO, it wastes a large number of resources. Fig. 1(a) and Fig. 1(b) show that it provisions 75% and 124% more resources than the actual demands in _ClarkNet_ and _Calgary_ cases, respectively. 

**PRESS** [12] derives the mean value of the corresponding points in each historical period as the predicted workload. It decreases the prediction error to 5% and 18% in _ClarkNet_ and _Calgary_ respectively. However, we find that this way always underestimates the actual resource demand and cannot strictly guarantee the SLO (see section IV). 

**EFRA** [4] derives the “best-fit” period pattern based on the historical data and predicts the resource usage through a collaborative filtering-based recommendation method. It can 



<!-- Start of picture text -->
Request History Data<br>Singular Spectrum Analysis<br>History<br>Decision Making - SLO slack Reprovisioning data<br>Elastical provisioning<br>Trace Data Denoising Heterogeneous<br>capacity Log collection<br>Server 1 Server 2 Server 3<br>normal noise noise Performancebottleneck Scale-out LC LC LC LC LC<br>LC<br>LC LC LC<br>Predict CPU/RAM/Disk/Network<br>Actual Burst Peakworkload Docker Engine<br>Operation System<br>LSTM Training Scale-up<br>1. Workload Prediction   2. Resource Reservation 3. Online Controller<br><!-- End of picture text -->

Fig. 2: ElaX System Architecture 

achieve a very low prediction error only when the periodic feature is stable. However, the periodic feature may vary over time. For example, the seven days trace for _ClarkNet_ shows a significant drop in the weekends (Fig. 1(a)), while the actual resource requirements in each period of _Calgary_ continuously increase from Monday to Sunday (Fig. 1(b)). These trends do not affect the period length, but the actual resource requirements are different among periods. Thus, the overall prediction error by _EFRA_ could achieve as high as 73% in _Calgary_ case. 

**Kubernetes** [2] supports both scale-out and scale-up operations through the HPA (Horizontal Pod Auto-scaling) and VPA (Vertical Pod Auto-scaling) techniques, respectively. However, they make resource scaling decisions only relying on the passive feedback from QoS monitoring, and does not support the workload prediction. 

Workload-aware resource scaling engine heavily relies on the accuracy of workload prediction to reduce the resource over-provisioning cost. However, there still lacks a precise predictor that works well in unstable workload environment. In <mark>addition, the scale-up and scale-out operations may generate completely different performance improvement effects. Even for the same operation (either scale-up or scale-out), its impact on QoS also varies over the intensity of workload. Fig. 1(c) shows that when the CPU utilization exceeds 40%, the scaleup operation will not improve the throughput of</mark> _<mark>redis</mark>_ <mark>quickly any more. That is, CPU is no longer the bottleneck resource for</mark> _<mark>redis</mark>_ <mark>at this time, and it is better to employ the scale-out operation to support the processing of more requests in this case.</mark> Hence, the resource scaling engine should launch the scale-out and scale-up operation in a combined consideration based on the resource status and precise workload prediction. 

## III. ELAX DESIGN 

In this section, we present our design of _ElaX_ and show how _ElaX_ can reduce the resource over-provisioning cost based on the workload prediction. 

_A. Overview_ 

Fig. 2 shows the system architecture of _ElaX_ . It is designed to operate in a container-enabled system where each service instance runs as a container. We choose the container instead of virtual machine because it enables the resource adjustment operations without stopping and restarting the container, and the operation can take effect in tens of milliseconds. _ElaX_ consists of three components as follows: 

**Workload predictor** learns from historical workload and makes prediction on the next workload. To improve the accuracy of prediction under unstable periodic workload, we preprocess the historical data using the SSA method, then train a LSTM (Long Short-Term Memory) [17] network for prediction. 

**Resource reservation** builds a resource-performance model to estimate the required resources supporting the predicted workload. It formulates the resource scaling as a mathematical programming problem considering the operation cost of scaleup and scale-out. Then, it derives the optimal scale-up and scale-out combination with minimum cost. 

**Online controller** dynamically adjusts the allocated resources for the service during runtime. It is activated whenever the tail latency is close to SLO violation. Meanwhile, when the SLO returns to the safe level, we also design a resource reclamation algorithm to recycle the unnecessary resources for higher resource efficiency. The controller is implemented based on Linux’s _cgroups_ . 

<mark>For</mark> _<mark>workload predictor</mark>_ <mark>, since training a LSTM network takes time (around 30 minutes) and the model is usually stable enough within one period (e.g., one day in production environment), we just update the LSTM network once a day (at midnight). Then, the</mark> _<mark>workload predictor</mark>_ <mark>runs once an hour, for predicting the workload per minute in the next hour (i.e., 60 points). Given the maximum predicted workload in next hour and the current system status,</mark> _<mark>resource reservation</mark>_ <mark>also runs once per hour for reconf</mark> i <mark>guring the containers. We do not update container conf</mark> i <mark>gurations every minute due to its</mark> 



<!-- Start of picture text -->
2000<br>Raw data<br>1600 SSA preprocessing<br>1200<br>800<br>400<br>0<br>0 50 100 150 200 250 300<br>Time (hour)<br>Num of Requests<br><!-- End of picture text -->

<mark>Fig. 3: Workload data series after processing with SSA. The blue line represents the original data series which contains a large number of noises, and the orange line represents the processed data using SSA, which is smoother than before. (Requests are collected by hours).</mark> 

<mark>high cost. Finally,</mark> _<mark>online controller</mark>_ <mark>continuously monitors the SLO and activates the resource adjustment whenever a SLO violation tends to occur.</mark> 

## _B. Workload Predictor_ 

_1) Preprocessing:_ The production workload clearly shows periodic patterns in Fig. 1. However, these patterns are often unstable: Noises like weekend drop, incremental workload, burst peaks make the traditional prediction methods (e.g., exponential smoothing, optimal fitting, etc.) do not work. To address this challenge, we adopt the deep learning algorithm and train a LSTM network model to precisely predict the future workload. 

Before the prediction, we process the historical workload data using the SSA method to filter out the local shortterm noises. SSA [14] is commonly used to analyze onedimensional time series data. It constructs a trajectory matrix according to the observed time series, and decompose it into a sum of components (e.g., long-term trend signal, periodic signal, noise signal) to analyze the structure of time series. Fig. 3 shows the reconstructed workload series after SSA processing, the processed data series is much smoother than before. 

_2) Prediction model:_ As the workload always changes in small-time granularity, single-point prediction generates frequent resource reconfigurations, leading to high cost. Hence, we instead predict multiple future points, for reducing the possible reconfiguration cost. For predicting the future workload, the existing literature is generally divided into two categories: statistical methods [15, 22] and machine learning methods [17]. We do not choose statistical methods, because they perform poorly for predicting multiple future points. While statistical methods, like Holt-Winters, may show high precision on single-point prediction, they predict the next token conditioned on its previously predicted token, and the approximation errors are iteratively accumulated. 

<mark>Fig. 4 shows the prediction results by both LSTM and Holt-Winters, and Fig. 5(a) shows the accumulated errors by</mark> 



<!-- Start of picture text -->
100<br>History Data<br>LSTM<br>50<br>0<br>100<br>History Data<br>Holt-Winters<br>50<br>0<br>0 20 40 60 80 100 120<br>Time (hour)<br>Fig. 4: LSTM vs. Holt-Winters<br>them. We see that LSTM performs much better accuracy than<br>the latter with the prediction length increasing, so we choose<br>LSTM as the prediction method in our system.<br>400<br>Holt-Winters 100 80<br>300 LSTM<br>200 50 60<br>100 0 40<br>100<br>0 50  1000 20<br>1 2 4 8 16 24 0   0    500<br>Length of Prediction<br>(a) LSTM vs. Holt-Winters (b) Parameter tuning<br>Fig. 5: Training the LSTM network model.<br>hidden layer Iterations<br>Workload (%)<br>Accuracy (%)<br>Prediction Error<br><!-- End of picture text -->

<mark>The structure of the LSTM leads to the signif</mark> i <mark>cant difference in the above comparison result. It can update parameters automatically by propagated gradients and make a long-term prediction by building loss function on the entire generated workloads instead of every single one.</mark> 



<!-- Start of picture text -->
wh+1 wh+k<br>Predicted<br>workloads<br>Output<br>LSTM States Outputs<br>Block<br>Roll out LSTM LSTM Ci LSTM<br>Block Block Block<br>w i Hi<br>w1 wi wh Inputs<br>Fig. 6: LSTM Structure<br><!-- End of picture text -->

Fig. 6 illustrates the design of LSTM network: The left shows a single LSTM block, which is trained recurrently by states and input data. While the generated states of a block and input data (i.e., _wi_ ) are fed into the next block, the next block further computes an output and new states for the next. In this way, sequential features in historical data are maintained. Each state consists of two vectors: the block state vector _ci_ and the hidden state vector _hi_ . They are fed into the next block to initialize its corresponding states. Then, given the _h_ outputs of LSTM blocks, we leverage a MLP (Multi-Layer Perceptron) network to generate _k_ predictions denoting the _k_ continuous workloads in the next period. That is, we have 

( _wh_ +1 _, ...wh_ + _k−_ 1 _, wh_ + _k_ ) = _LSTM_ ( _w_ 1 _, ..., wh−_ 1 _, wh_ ) (1) 

where _wi_ , _∀i ∈_ [1 _, .., h_ ] is the historical workload at time _i_ , and _wj_ , _∀j ∈_ [ _h_ +1 _, .., h_ + _k_ ] denotes the predicted workload at time _j_ . For training the network, we record ( _h_ + _k_ ) continuous points by sliding time windows on raw workload data. The first _h_ points in each window are regarded as training data and the rest are treated as target data. Upon obtaining the training data, we use RMSE to measure the loss of predicted workloads and actual ones as: 



where _θ_ denotes the parameters set in LSTM model, and _pt_ and _wt_ are the predicted workloads and real value at time _t_ respectively. For solving (2), we update _θ_ using the common SGD (Stochastic Gradient Descent) method. 

In our experiments, we conduct nearly 200 experiments to find the optimal parameter configurations with different combinations of neural layers and iterations (Fig. 5(b)). We finally get a well-trained LSTM model with 80 hidden layers and 520 iterations and the total training time is less than 30 minutes. 

## _C. Resource reservation_ 



<!-- Start of picture text -->
48 44<br>Sample points Sample points<br>MaxLoad Fitting<br>36 33<br>24 22<br>12 11<br>0 0<br>0 5k 10k 15k 20k 25k 30k 35k 0 5k 10k 15k 20k 25k<br>Workload (QPS) Workload (QPS)<br>(a) The actual CPU utilization under (b) Model linearly fitting.<br>different workloads for Redis.<br>CPU utilization (%) CPU utilization (%)<br><!-- End of picture text -->

Fig. 7: The resource-performance model. 

_1) Deriving the required resources:_ Given the predicted workload, we construct a resource-performance model to derive the amount of required resource. Fig. 7(a) shows the actual CPU utilization under different workloads for _redis_ . Note that this analysis method can be applied in other online services. The CPU utilization and the workloads obviously have a non-linear relationship. We see that the CPU utilization increases linearly at the beginning, followed by a steady state. It means that increasing the CPU resources would improve the performance at the beginning, but become ineffective after a knee point. We denote the QPS (Query Per Second) at the knee in this case as _maxload_ . Since the CPU resource will not be the performance bottleneck anymore after workload exceeds _maxload_ , we can just allocate the maximum allowable resources in case of _> maxload_ , and a fine-grained resource reconfiguration process would reduce the service cost only when the actual workload is less than _maxload_ . 

Considering the case of _< maxload_ , we fit a linear model to describe the relationship between resource allocation and workload (Fig. 7(b)): 



where _R_ represents the required resources, _y_ denotes the workload, _σ_ and _β_ are the coefficients of this linear model. 

To improve the accuracy of model fitting, we detect and remove outliers using the _Nearest Neighbor_ approach: For each data point, we compute its distance to the _k_ -th nearest neighbor. The points that have the largest distances are identified as outliers. After removing the outliers, we derive the linear model that leads to the minimum euclidean distance to sample points. 

_2) Scale up and scale out:_ Given the required resources (denoted by _R_ ), it is a big challenge to derive the right number of containers and their configurations based on the existing container configurations and available physical machine resources because the “scale up” and “scale out” perform significantly different operation cost. Starting a new container involves the operations includes creating a container ( _Ccreate_ ), adding the container into cluster ( _Cadd_ ), configuring the load balancer ( _Cbalance_ ) and the forwarding cost ( _Cforward_ ) generated by cache miss due to the re-balancing mechanism in the cluster. Hence, the operation cost of scale-out ( _Cscaleout_ ) is defined as follows: 



On the other hand, the scale-up operation, i.e., updating the configuration of a container, only involves the operation cost on changing the number of CPU cores and memory that allocated to the container. So we define the operation cost of scale-up ( _Cscaleup_ ) as follows: 



where _Ccpu_ and _Cmemory_ represent the operation cost on varying the CPU and memory configuration, respectively. Note that the operation cost for scale-in and scale-down can be derived in the same way, and in fact, they are the same as the scale-out and scale-up operations. 

In general, we prefer scaling-up the container cluster to scaling-out operation for processing the increased workload, because _Cscaleup < Cscaleout_ is usually established for scaleout’s more operations than scale-up. However, it is not possible to scale up resources unboundedly due to the limited capacity of the physical machine. Moreover, the dominant resource may change over the workload, and scaling up a container could become useless after the workload reaches _maxload_ . 

Suppose the service cluster has _n_ physical machines and can hold at most _m_ containers. Let _yi_<sup>0,</sup><sup>_∀i∈_[1</sup><sup>_, ..m_]bethe</sup> resources initially allocated to container _i_ , and _Hj_ , _∀j ∈_ [1 _, .., n_ ] be the maximum capacity of physical machine _j_ . Then, given the resource requirement _R_ , the resource capacity _Hj_ , _∀j ∈_ [1 _, .., n_ ] and _yi_<sup>0,</sup><sup>_∀i ∈_[1</sup><sup>_, ..n_],ourgoalistofindthe</sup> 

new configurations for all containers: _yi_ , _∀i ∈_ [1 _, ..n_ ], so that the overall operation costs are minimized: 



where _Nscaleup_ denotes the number of containers whose resource configuration is changed, and _Nscaleout_ denotes the number of new container instances. 

Besides the variable _yi_ , we also define two other variables to formalize the problem as a MINLP (Mixed Integer Nonlinear Programming) problem: 

- _xij_ : a binary variable, which has the value “1” if container _i_ is assigned to machine _j_ . Otherwise, it is set to “0”. 

- _zi_ : a binary variable, denoting whether there is a change on resource configuration for container _i_ . It has the value “1” if _yi̸_ = _yi_<sup>0.Otherwise,itissetto“0”.</sup> 

- Constraint (16) enforces that each container can only be deployed on at most one physical machine. 

- Constraint (17) and (18) refer to the domain constraints. 



<!-- Start of picture text -->
1M 300<br>Fitting Fitting<br>0.8M Samples Samples<br>200<br>0.6M<br>0.4M<br>100<br>0.2M<br>0 0<br>0 100 200 300 0 100 200 300<br>Num of Variates (m*n+m) Num of Variates (m*n+m)<br>(a) Iterations (b) Time<br>Num of Iterations Solution Time (s)<br><!-- End of picture text -->

<mark>Fig. 8: The number of iterations and solution time required for solving the MINLP.</mark> 

Let _x_<sup>0</sup> _ij_<sup>be the initial assignment of container</sup><sup>_i_. If �</sup> _j_<sup>_x_</sup> _ij_<sup>0=</sup> 

0, it means container _i_ has not been created yet. Thus, we have, 



## **Objective:** 





- Constraint (10) ensures that the required resources are fully satisfied. 

- Constraint (11) makes sure that the aggregated resources allocated to containers deployed on a machine do not exceed the capacity of the machine. 

- Constraint (12), (13) together with constraint (17) make sure that either _zi_ = 1 if and only if _yi̸_ = _yi_<sup>0or</sup><sup>_zi_=0</sup> if and only if _yi_ = _yi_<sup>0.</sup> 

- Constraint (14), (15) together with constraint (17) make sure that when container _i_ has been created, its configuration _yi_ should not be “0”. Otherwise, it is set to “0”. 

<mark>We solve the above problem using LINGO and generate the conf</mark> i <mark>guration updating plan based on the current conf</mark> i <mark>gurations and the derived solution. Fig. 8 shows the number of iterations and time for solving this MINLP. We see that the number of iterations grows exponential over the number of variables</mark> _<mark>m ∗ n</mark>_ <mark>+</mark> _<mark>m</mark>_ <mark>, and the solution time approaches to 100 seconds when the number of variables is 300. As the container reconf</mark> i <mark>guration is activated once per hour, this cost is acceptable.</mark> 



<!-- Start of picture text -->
performance cap for single service node<br>100% 80%50% resource usedresource can be scaled-up allocate consistent resource for service<br>nodes because of the load balancing<br>service node can not reach scale-out service nodes<br>the performance cap sincethe capacity limit of server scale out 70%<br>50% scale out 70% 70%70%<br>50% 50% 70% 70%<br>Machine A(160%) Machine B(300%)<br>scale-up capacity of each node<br>heterogeneous capacity across servers<br><!-- End of picture text -->

<mark>Fig. 9: When the workload increases from 150% to 350%, we scale out two container instances and scale up the resources of three existing containers from 50% to 70%.</mark> 

<mark>Fig. 9 shows an example of the resource scaling process of</mark> _<mark>ElaX</mark>_ <mark>: machine A’s resource capacity is 160% and holds two container instances, while machine B’s capacity is 300% and there is only one container running on it at present. Each container has a performance cap of 100%. When the workload increases from 150% to 350%. The existing three active containers cannot satisfy the new requirement because the maximum capacity for them is only 260% (A can only reach the 80% of their performance cap because A only has 160% resource capacity, and the capacities of all containers are kept consistent for load balancing), so the cluster has to be extended to fve</mark> i <mark>nodes: while we scale up the existing three containers to 70% resources, we also scale out two new containers.</mark> 



<!-- Start of picture text -->
16 20 Calgary workload<br>No-scalingPeak-based PRESSEFRA ElaXActual demand 16 No-scalingPeak-based PRESSEFRA ElaXActual demand 200 No-scaling Peak-based EFRA ElaX<br>12<br>100<br>12<br>8 0 ClarkNet workload<br>8 200 No-scaling Peak-based EFRA ElaX<br>4<br>4 100<br>0 0 0<br>24 48 72 96 120 24 48 72 96 120 24 48 72 96 120<br>Time (minute) Time (minute) Time (minute)<br>(a) Resource provisioning (Calgary, Redis) (b) Resource provisioning (ClarkNet, Redis) (c) Over-provisioning cost in Redis<br>20 No-scalingPeak-based PRESSEFRA ElaXActual demand 20 No-scalingPeak-based PRESSEFRA ElaXActual demand 400 No-scaling CalgPeak-basedary workload EFRA ElaX<br>15 15 200<br>10 10 0 ClarkNet workload<br>400 No-scaling Peak-based EFRA ElaX<br>5 5<br>200<br>0 0 0<br>24 48 72 96 120 24 48 72 96 120 24 48 72 96 120<br>Time (minute) Time (minute) Time (minute)<br>(d) Resource provisioning (Calgary, e-commerce) (e) Resource provisioning (ClarkNet, e-commerce) (f) Over-provisioning cost in e-commerce<br>Fig. 10: Resource over-provisioning comparison of four methods (enabling only scale-up operation).<br>1 1 1 1<br>469us 681us 352us 569us 518ms 1114ms 542ms 967ms<br>0.8 0.8 0.8 0.8<br>0.6 0.6 0.6 0.6<br>0.4 0.4 0.4 0.4<br>ElaX ElaX ElaX ElaX<br>EFRA EFRA EFRA EFRA<br>0.2 Peak-based 0.2 Peak-based 0.2 Peak-based 0.2 Peak-based<br>PRESS PRESS PRESS PRESS<br>0 90th 0 90th 0 90th 0 90th<br>200 400 600 800 200 400 600 800 500 1000 1500 200 600 1000 1400<br>Latency (us) Latency (us) Latency (ms) Latency (ms)<br>(a) Latency (Calgary, Redis) (b) Latency (ClarkNet,Redis) (c) Latency (Calgary, e-commerce) (d) Latency (ClarkNet, e-commerce)<br>Fig. 11: Tail latency CDF of four methods (SLO is set to 90 th percentile latency <  500 us in Redis, 650 ms in e-commerce).<br>Allocated CPU cores Allocated CPU cores CPU over-provision (%)<br>Allocated CPU cores Allocated CPU cores CPU over-provision (%)<br>Cumulative Probability Cumulative Probability Cumulative Probability Cumulative Probability<br><!-- End of picture text -->

## _D. Online Controller_ 

The inevitable prediction error by _workload predictor_ possibly leads to SLO violations. Therefore, we further design an _online controller_ to adjust the resources at runtime according to the SLO-violation feedback from performance monitoring. It works as a daemon process and monitors the real-time latency of long running service, when the service performance declines or approaches a dangerous level, the resource reallocation mechanism will be activated and protect the service from violating the SLO. 

<mark>The detailed control method is shown in Algorithm 1. We denote</mark> _<mark>SLO Target</mark>_ <mark>as the latency target of long running service, and it is set as the 90</mark> _<mark>th</mark>_ <mark>percentile latency under the</mark> _<mark>maxload</mark>_ <mark>while with suff</mark> i <mark>cient resource. By continuously monitoring the tail latency performance in consecutive 30second windows, we derive a</mark> _<mark>slack</mark>_ <mark>indicating the gap between current latency and SLO. If</mark> _<mark>slack <</mark>_ <mark>0, it means the SLO has been violated, and the system will allocate additional 0</mark> _<mark>.</mark>_ <mark>1</mark> _<mark>×</mark>_ <mark>reserved resource for the service. If 0</mark> _<mark>< slack <</mark>_ <mark>0</mark> _<mark>.</mark>_ <mark>05, it means the latency is closely approaching the</mark> _<mark>SLO</mark>_ _<u><mark>T</mark></u>_ _<mark>arget</mark>_ <mark>and may</mark> 

## **Algorithm 1:** Online control algorithm 

- **1 while** _True_ **do** 

- **2** _slack_ = ( _SLO Target − latency_ ) _/SLO_ _<u>T</u> arget_ ; **3 if** _slack <_ 0 **then 4** increResource(curResource*0.1); 

- **5 else if** 0 _< slack <_ 0 _._ 05 **then** 

- **6** increResource(curResource*0.05); 

- **7 else 8** _extraResource_ = _curResource − preResource_ ; **9 if** _extraResource >_ 0 **then** 

- **10** removeResource(extraResource*0.5); **11** sleep(2s); 

<mark>soon violate the SLO. In this case, we allocate 0</mark> _<mark>.</mark>_ <mark>05</mark> _<mark>×</mark>_ <mark>additional resource for preventing the possible violation of SLO. Otherwise, the latency is still safe enough for guaranteeing the SLO, we activate the</mark> _<mark>recycling</mark>_ <mark>process, such that the overallocated resources are recycled for other services. In lines 8-</mark> 

<mark>10, we f</mark> i <mark>rst derive the over-allocated resources (</mark> _<mark>extraResource</mark>_ <mark>) using the currently allocated resources (</mark> _<mark>curResource</mark>_ <mark>) and the predicted resources (</mark> _<mark>preResource</mark>_ <mark>). Then, we recycle half of the over-allocated resource each time to reduce the waste.</mark> 

## IV. PERFORMANCE EVALUATION 

## _A. Experiment Setup_ 

_1) Services:_ We deployed two online services _e-commerce website_ and _redis_ , considering their representativeness in service architecture and response time: 

- _E-commerce_ adopts the multi-tier architecture and usually responds in milliseconds. We use the TPC-W [24] as the transactional web e-commerce benchmark. 

- _Redis_ is an in-memory data structure store and is used as a database, cache and message broker. It adopts the fanout architecture and usually responds in microseconds. 

_2) Workloads:_ We simulate the access workload towards the two services using production workload from ClarkNet and Calgary trace [18], by comparing _ElaX_ with _EFRA_ , _PRESS_ and _Peak_ methods, we evaluate the efficiency using resource utilization and 90 _th_ percentile latency. 

_3) System environment:_ We deploy the _redis_ cluster with 22 service nodes and the _e-commerce_ cluster with 20 nodes across four servers, and each container is initially allocated with 1 CPU cores and 2GB RAM. Clients are deployed in another server to avoid resource contention with service nodes. Each server is configured with 40 cores of 2.0 GHz Intel Xeon E74820 v4 and 128GB of DRAM. We use the operating system of Ubuntu 14.04 and the docker engine 18.03. All servers are connected to a 1000 Mbps switch. After deploying _ElaX_ on this system, we measure that its average CPU utilization is _<_ 5% and memory utilization is _<_ 400 _MB_ . 

## _B. Results_ 

_1) Scale-up:_ Since the compared algorithms can only support scale-up operation, we evaluate _ElaX_ by only enabling the scale-up operation at first. 

**Resource provision** : Fig. 10 shows the allocated resources by the four algorithms. We only show the CPU resource here, but it can be extended to other resources easily. In the case of _redis_ (Fig. 10(a)-Fig. 10(c)), although _PRESS_ always utilizes the least resources (even less than the actual demand), it leads to very high tail latency and cannot guarantee the tail latency SLO (Fig. 11). Among _ElaX_ , _Peak_ , _EFRA_ and _No-scaling_ , we find that, _No scaling_ wastes the largest amount of CPU (by an average of 141%) because of the fluctuating CPU demands of the workload. _Peak_ can dynamically allocate CPU resource for the varying workloads, but it also causes a significant waste of 46% resources, since its conservative approach that uses worst-case peak demand as the predicted workload in next period. The over-provisioning cost by _EFRA_ is around 34%, which is much less than _No Scaling_ and _Peak_ . However, it also exceeds 70% in the first period, since its prediction does not work well in unstable periodic workload. _ElaX_ performs much better than the former algorithms, and its over-provisioning 

cost is generally less than 10% because of its high prediction accuracy. 

In case of _e-commerce_ , Fig. 10(d)-Fig. 10(f) shows the similar results. While _No-scaling_ , _Peak_ and _EFRA_ averagely generate over-provisioning cost of 200 _._ 3%, and 29 _._ 6%, respectively, our _ElaX_ only generates less than 18% of overprovisioning cost. 

**Tail latency** : The tail latency SLO of online service must be guaranteed while allocating the resource elastically. Fig. 11 shows the CDF (Cumulative Distribution Function) of latency by four algorithms: _Peak_ , _EFRA_ , _PRESS_ and _ElaX_ . We set the tail latency SLO as the 90 _th_ percentile latency under the _maxload_ while allocated with sufficient resources, which are 500 _us_ and 650 _ms_ for _redis_ and _e-commerce_ , respectively. We find that _PRESS_ cannot guarantee the SLO in all cases: its 90 _th_ percentile latency for _redis_ under _Calgary_ and _ClarkNet_ trace are 681us and 569us, respectively, and for _e-commerce_ under _Calgary_ and _ClarkNet_ trace are 1114ms and 967ms, respectively. On the other hand, _Peak_ and _EFRA_ can guarantee the SLO because of its over-provisioned resources, and _ElaX_ can guarantee the SLO because of its high prediction precision and online control mechanism. 



<!-- Start of picture text -->
10 5 10 5<br>10 10<br>Actual QPS EFRA Actual QPS<br>ElaX Peak-based ElaX<br>8 PRESS 8 PRESS EFRA<br>Peak-based<br>6 6<br>4 4<br>2 2<br>0 0<br>1 2 3 4 5 1 2 3 4 5<br>Time (span=24 mins) Time (span=24 mins)<br>(a) QPS (Calgary, Redis) (b) QPS (ClarkNet, Redis)<br>12k 12k<br>Actual QPS Actual QPS<br>ElaX ElaX<br>PRESS PRESS<br>9k EFRAPeak-based 9k EFRAPeak-based<br>6k 6k<br>3k 3k<br>0 0<br>1 2 3 4 5 1 2 3 4 5<br>Time (span=24 mins) Time (span=24 mins)<br>(c) QPS (Calgary, e-commerce) (d) QPS (ClarkNet, e-commerce)<br>Throughput (QPS) Throughput (QPS)<br>Throughput (QPS) Throughput (QPS)<br><!-- End of picture text -->

<mark>Fig. 12: System Throughput (scale-up)</mark> . 

**<mark>Throughput</mark>** <mark>:</mark> _<mark>ElaX</mark>_ <mark>provides a highly precise prediction on workload and the amount of required resources. However, when we actually allocate the corresponding amount of resources, the actual system throughput (i.e., QPS) is slightly decreased. Fig. 12 shows the system throughput generated by the four methods. We see that</mark> _<mark>Peak</mark>_ <mark>,</mark> _<mark>EFRA</mark>_ <mark>,</mark> _<mark>ElaX</mark>_ <mark>decrease the throughput by an average of 0</mark> _<mark>.</mark>_ <mark>52%, 0</mark> _<mark>.</mark>_ <mark>81% and 0</mark> _<mark>.</mark>_ <mark>69%, respectively, all of them are less than 1%. The instability of</mark> 



<!-- Start of picture text -->
20 ElaX 100 CPU over-provsion 1 1<br>Actual demand 75 average<br>EFRA 442us 30140us<br>15 EFRA only supports Scale-up/down 50 0.8 0.8<br>25<br>0 0.6 0.6<br>10 24 48 72 96 120<br>1M No-scalingTime (minute)EFRA ElaX 0.4 0.4<br>5<br>0.5M 0.2 ElaX 0.2 EFRA<br>90th 90th<br>0 0 0 0<br>24 48 72 96 120 1 2 3 4 5 200 300 400 500 600 20k 40k 60k 80k100k<br>Time (minute) Time (span=24 mins) Latency (us) Latency (us)<br>(a) Resource provisioning cost (b) Throughput (c) Latency of ElaX (d) Latency of EFRA<br>Over-provision (%)<br>Allocated CPU cores<br>QPS Cumulative Probability Cumulative Probability<br><!-- End of picture text -->



<!-- Start of picture text -->
Fig. 13: Resource utilization of Redis under Calgary (enabling both scale-up and scale-out operations).<br>15 100 generated by both ElaX and EFRA . We see that<br>Reprovision Recycled<br>Recycled Average guarantee the SLO with a 90 th latency of 442 us .<br>10 80 EFRA , its 90 th percentile latency even exceeds 30<br>is much larger than the SLO target, thus it cannot<br>the tail latency SLO under unstable periodic workload.<br>5  60 Resource recycling : We also present the eff i<br>recycling mechanism of ElaX . Fig. 14 shows the<br>0  40 the resource re-provisioning process in our<br>0 1 2 3 4 5 6 7 8 9 10 1 2 3 4 5 see that, the re-provisioning mechanism is triggered i<br>Time (minute) Sample points<br>times, and is followed by fveve i times of recycling.<br>(a) Re-provisioning and recycling (b) Recycled resources When ElaX detects that the current tail latency<br>Recycled ratio (%)<br>Resource Reprovision (%)<br><!-- End of picture text -->

generated by both _ElaX_ and _EFRA_ . We see that _ElaX_ can guarantee the SLO with a 90 _th_ latency of 442 _us_ . In case of _EFRA_ , its 90 _th_ percentile latency even exceeds 30 _ms_ , which is much larger than the SLO target, thus it cannot guarantee the tail latency SLO under unstable periodic workload. **<mark>Resource recycling</mark>** <mark>: We also present the eff</mark> i <mark>ciency of resource recycling mechanism of</mark> _<mark>ElaX</mark>_ <mark>. Fig. 14 shows the timeline of the resource re-provisioning process in our experiment. We see that, the re-provisioning mechanism is triggered for fve</mark> i <mark>times, and is followed by fveve</mark> i <mark>times of recycling.</mark> 

<mark>When</mark> _<mark>ElaX</mark>_ <mark>detects that the current tail latency will soon approach SLO (i.e.,</mark> _<mark>slack <</mark>_ <mark>0</mark> _<mark>.</mark>_ <mark>05), it allocates additional 5% more resources. If SLO has been violated, it allocates additional 10% more resources to guarantee SLO. After the allocation of additional resources, the recycling algorithm recycles extra resources in a bisection way if the SLO is recovered. We highlight the amount of recycled resources in Fig. 14(a), and f</mark> i <mark>nd that the recycling mechanism recycles 79% of resources averagely during this time (Fig. 14(b)).</mark> 



<!-- Start of picture text -->
Fig. 14: Recycling resources .<br><!-- End of picture text -->

the system may lead to fluctuations in QPS, so we suggest allocating slight more resources for the online service after we get the resource allocation using the resource-performance model. For _PRESS_ , it cannot guarantee the throughput in all experimental groups. 

_2) Scale-up and scale-out:_ We change the system configurations by constraining the maximum usable capacity of two containers to 60% of its original capacity, that is, resulting in a heterogeneous system. We run _ElaX_ on the heterogeneous system, and enable both scale-up and scale-out operations. We compare _ElaX_ only with _EFRA_ because _EFRA_ performs the best among the other algorithms. 

## V. RELATED WORK 

**Cloud management framework** : Many cloud resource management systems, such as Yarn [32], Borg [33], Omega [29], Mesos [16], have been proposed to improve the resource efficiency of cloud systems. However, they never focus on the long-running online services, and do not provide the efficient resource allocation for online services. Kubernetes [2] supports both scale-out and scale-up operations by the HPA and VPA techniques, according to the feedback from latency monitoring. However, as the online service’s workload often shows periodic patterns, it is possible to further reduce the provisioning cost through workload-aware resource allocations. 

**Resource provision** : Fig. 13(a) shows allocated CPU resources by _EFRA_ and _ElaX_ . We see that the workload increases by almost 0 _._ 5% from the first time window to second window, _EFRA_ can only provision resource by scale-up/down and cannot guarantee the increased workload in second timespan, while _ElaX_ can continually provide resource for the workload using scale-up/out. The top figure in Fig. 13(b) shows the resource over-provisioning cost by _ElaX_ over time. We see that the over-provisioning cost is rather high at the beginning, but it declines quickly due to the continuous reconfigurations. The average CPU over-provisioning cost is about 11.4%. For the system throughput, the bottom figure in Fig. 13(b) shows that _ElaX_ can achieve comparable throughput as the _Noscaling_ while _EFRA_ reduces the throughput by around 12%. The limitation of _EFRA_ leads to the lower throughput in this heterogeneous system. 

**Resource allocation** : There has been some work supporting workload-aware resource allocation for batch work to achieve the SLO effect without over-provisioning. Morpheus [20] is able to automatically allocate resources learning from historical resource usage. TetriSched [31] estimates the job runtime for planning ahead for a busty preferred resource type. Quasar [7] increases resource utilization through a prediction on interference between applications. HCloud [8], a hybrid provisioning system that uses both reserved and on-demand resources in a combined way for reducing the service cost. 

**Tail latency** : Fig. 13(c) and Fig.13(d) show the tail latency 

However, there is still a lack of study on the access load pattern of the online service, for further reducing the resource provisioning cost. 

**Long-term online service** : For long-running services, PRESS [12] extracts fine-grained dynamic patterns from application resource requirements and automatically adjusts the allocation of their resources. CloudScale [30] uses an online resource demand forecasting scheme to achieve adaptive resource allocation. However, due to under-estimation, PRESS and CloudScale cannot strictly guarantee the tail latency SLO. AGILE [25] dynamically adjusts the number of VMs allocated to cloud applications to keep up with load changes. However, starting or stopping a VM (or server) usually takes a few minutes, and these methods are not sufficient to effectively cope with the uncertain needs of long-term operation, especially for online services [1]. EFRA [4] supports the finegrained resource allocation with a workload-aware allocation mechanism, but their workload prediction is highly inaccurate in the very common unstable periodic workload scenarios. 

## VI. CONCLUSION AND FUTURE WORK 

In this paper, we design an elastic resource provisioning framework: _ElaX_ , which can dynamically adjust the resource allocation for periodical workload while guarantee tail latency SLO for online service. _ElaX_ can precisely predict the complex workload variations, and scale the resources efficiently using both scale-up and scale-out operations in a combined way. Experiment results demonstrate the efficiency of _ElaX_ . In the future, we would like to further improve the resource efficiency employing the hardware and software interference isolation techniques. 

## REFERENCES 

- [1] Omer Y Adam, Young Choon Lee, and Albert Y Zomaya. Constructing performance-predictable clusters with performance-varying resources of clouds. _IEEE Transactions on Computers_ , (9):2709–2724, 2016. 

- [2] David Bernstein. Containers and cloud: From lxc to docker to kubernetes. _IEEE Cloud Computing_ , (3):81–84, 2014. 

- [3] Carl Boettiger. An introduction to docker for reproducible research. _Acm Sigops Operating Systems Review_ , 49(1):71–79, 2015. 

- [4] Binlei Cai, Rongqi Zhang, Laiping Zhao, and Keqiu Li. Less provisioning: A fine-grained resource scaling engine for long-running services with tail latency guarantees. In _Proceedings of the 47th International Conference on Parallel Processing_ , page 30. ACM, 2018. 

- [5] Wesam Dawoud, Ibrahim Takouna, and Christoph Meinel. Elastic virtual machine for fine-grained cloud resource provisioning. In _Global Trends in Computing and Communication Systems_ , pages 11–25. Springer, 2012. 

- [6] Christina Delimitrou and Christos Kozyrakis. ibench: Quantifying interference for datacenter applications. In _2013 IEEE international symposium on workload characterization (IISWC)_ , pages 23–33. IEEE, 2013. 

- [7] Christina Delimitrou and Christos Kozyrakis. Quasar: resource-efficient and qos-aware cluster management. _ACM SIGPLAN Notices_ , 49(4):127– 144, 2014. 

- [8] Christina Delimitrou and Christos Kozyrakis. Hcloud: Resource-efficient provisioning in shared cloud systems. _SIGPLAN Not._ , 51(4):473–488, March 2016. 

- [9] Docker. What is a container?, 2019. https://www.docker.com/resources/what-container. 

- [10] Kit Eaton. https://www.fastcompany.com/1825005/how-one-secondcould-cost-amazon16-billion-sales, 2018. 

pool management: Policies, efficiency and quality metrics. In _DSN_ , pages 326–335. IEEE, 2008. 

   - [12] Zhenhuan Gong, Xiaohui Gu, and John Wilkes. Press: Predictive elastic resource scaling for cloud systems. _CNSM_ , 10:9–16, 2010. 

   - [13] Sriram Govindan, Jie Liu, Aman Kansal, and Anand Sivasubramaniam. Cuanta: Quantifying effects of shared on-chip resource interference for consolidated virtual machines. In _SoCC_ , pages 22:1–22:14, 2011. 

   - [14] Hossein Hassani. Singular spectrum analysis: meth. and comp. 2007. 

   - [15] Yan He, Ashley Flavel, Zihui Ge, Alexandre Gerber, Massey Dan, Christos Papadopoulos, Hiren Shah, and Jennifer Yates. Argus: Endto-end service anomaly detection and localization from an isp’s point of view. In _IEEE Infocom_ , 2012. 

   - [16] Benjamin Hindman, Andy Konwinski, Matei Zaharia, Ali Ghodsi, Anthony D Joseph, Randy H Katz, Scott Shenker, and Ion Stoica. Mesos: A platform for fine-grained resource sharing in the data center. In _NSDI_ , volume 11, pages 22–22, 2011. 

   - [17] S Hochreiter and J Schmidhuber. Long short-term memory. _Neural Computation_ , 9(8):1735–1780, 1997. 

   - [18] InternetTrafficArchive. http://ita.ee.lbl.gov/html/traces.html, December 16 2018. 

   - [19] Waheed Iqbal, Matthew N Dailey, and David Carrera. Sla-driven dynamic resource management for multi-tier web applications in a cloud. In _Proceedings of the 2010 10th IEEE/ACM International Conference on Cluster, Cloud and Grid Computing_ , pages 832–837. IEEE Computer Society, 2010. 

   - [20] Sangeetha Abdu Jyothi, Carlo Curino, Ishai Menache, Shravan Matthur Narayanamurthy, Alexey Tumanov, Jonathan Yaniv, Ruslan Mavlyutov, Inigo Goiri, Subru Krishnan, Janardhan Kulkarni, et al. Morpheus: Towards automated slos for enterprise clusters. In _OSDI_ , pages 117–134, 2016. 

   - [21] M. Kambadur, T. Moseley, R. Hank, and M. A. Kim. Measuring interference between live datacenter applications. In _High PERFORMANCE Computing, Networking, Storage and Analysis_ , pages 1–12, 2012. 

   - [22] Balachander Krishnamurthy, Subhabrata Sen, Yin Zhang, and Yan Chen. Sketch-based change detection: methods, evaluation, and applications. In _Proceedings of the 3rd ACM SIGCOMM conference on Internet measurement_ , pages 234–247, 2003. 

   - [23] Qixiao Liu and Zhibin Yu. The elasticity and plasticity in semicontainerized co-locating cloud workload: A view from alibaba trace. In _SoCC_ , pages 347–360, 2018. 

   - [24] D. A. Menasce. Tpc-w: A benchmark for e-commerce. _IEEE Internet Computing_ , 6:83–87, 05 2002. 

   - [25] Hiep Nguyen, Zhiming Shen, Xiaohui Gu, Sethuraman Subbiah, and John Wilkes. Agile: Elastic distributed resource scaling for infrastructure-as-a-service. In _ICAC_ , volume 13, pages 69–82, 2013. 

   - [26] Vicente Oropeza and Mauricio Sacchi. Simultaneous seismic data denoising and reconstruction via multichannel singular spectrum analysis. _Geophysics_ , 76(3):V25–V32, 2011. 

   - [27] Redis. Redis: an open source, in-memory data structure store, 2018. https://redis.io. 

   - [28] Charles Reiss, Alexey Tumanov, Gregory R. Ganger, Randy H. Katz, and Michael A. Kozuch. Heterogeneity and dynamicity of clouds at scale: Google trace analysis. In _Proceedings of the Third ACM Symposium on Cloud Computing_ , SoCC ’12, pages 7:1–7:13, New York, NY, USA, 2012. ACM. 

   - [29] Malte Schwarzkopf, Andy Konwinski, Michael Abd-El-Malek, and John Wilkes. Omega: flexible, scalable schedulers for large compute clusters. In _Eurosys_ , pages 351–364. ACM, 2013. 

   - [30] Zhiming Shen, Sethuraman Subbiah, Xiaohui Gu, and John Wilkes. Cloudscale: Elastic resource scaling for multi-tenant cloud systems. In _Proceedings of the 2Nd ACM Symposium on Cloud Computing_ , SOCC ’11, pages 5:1–5:14, New York, NY, USA, 2011. ACM. 

   - [31] Alexey Tumanov, Timothy Zhu, and Jun Woo et al. Park. Tetrisched: Global rescheduling with adaptive plan-ahead in dynamic heterogeneous clusters. In _EuroSys_ , pages 35:1–35:16, 2016. 

   - [32] Vinod Kumar Vavilapalli, Arun C. Murthy, and Chris et al. Douglas. Apache hadoop yarn: Yet another resource negotiator. In _SoCC_ , pages 5:1–5:16, New York, NY, USA, 2013. ACM. 

   - [33] Abhishek Verma, Luis Pedrosa, Madhukar Korupolu, David Oppenheimer, Eric Tune, and John Wilkes. Large-scale cluster management at google with borg. In _Proceedings of the Tenth European Conference on Computer Systems_ , page 18. ACM, 2015. 

- [11] Daniel Gmach, Jerry Rolia, Ludmila Cherkasova, Guillaume Belrose, Tom Turicchi, and Alfons Kemper. An integrated approach to resource 

