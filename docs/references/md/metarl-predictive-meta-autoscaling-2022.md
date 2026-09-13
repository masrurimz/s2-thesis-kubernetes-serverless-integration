---
# --- bibliographic record ---
entry_type: misc
title: "A Meta Reinforcement Learning Approach for Predictive Autoscaling in the Cloud"
authors:
  - "Siqiao Xue"
  - "Chao Qu"
  - "Xiaoming Shi"
  - "Cong Liao"
  - "Shiyi Zhu"
  - "Xiaoyu Tan"
  - "Lintao Ma"
  - "Shiyu Wang"
  - "Shijun Wang"
  - "Yun Hu"
  - "Lei Lei"
  - "Yangfei Zheng"
  - "Jianguo Li"
  - "James Zhang"
year: 2022
venue: "arXiv preprint"
volume: ""
issue: ""
pages: ""
publisher: ""
doi: ""
arxiv: "2205.15795"
url: "https://arxiv.org/abs/2205.15795"

# --- archive record ---
source_pdf: metarl-predictive-meta-autoscaling-2022.pdf
source_sha256: f0cbc56451948815ccc4b26db103ef2349404282aaa294ef895d378fbfa708cb
pdf_pages: 10
converted: 2026-09-13
record_source: arxiv
key_insight: "DAPM periodic-attention forecaster + Attentive Neural Process in differentiable RL; deployed at Alipay"
first_page: "A Meta Reinforcement Learning Approach for Predictive Autoscaling in the Cloud Siqiao Xue∗,Chao Qu∗,+,Xiaoming Shi, Cong Liao, Shiyi Zhu, Xiaoyu Tan, Lintao Ma, Shiyu Wang, Shijun Wang+, Yun Hu, Lei L"
---
# **A Meta Reinforcement Learning Approach for Predictive Autoscaling in the Cloud** 

Siqiao Xue<sup>∗</sup> ,Chao Qu<sup>∗</sup><sup>_,_+</sup> ,Xiaoming Shi, Cong Liao, Shiyi Zhu, Xiaoyu Tan, Lintao Ma, Shiyu Wang, Shijun Wang<sup>+</sup> , Yun Hu, Lei Lei, Yangfei Zheng, Jianguo Li, James Zhang 

{siqiao.xsq,peter.sxm,liaocong.lc,zhushiyi.zsy,yulin.txy,lintao.mlt,weiming.wsy,shiyu.wang}@antgroup.com 

{huyun.h,jason.ll,yangfei.zyf,lijg.zero,james.z}@antgroup.com 

+{chaoqu.technion,sjwang05}@gmail.com 

Ant Group 

Hangzhou, China 

## **ABSTRACT** 

Predictive autoscaling (autoscaling with workload forecasting) is an important mechanism that supports autonomous adjustment of computing resources in accordance with fluctuating workload demands in the Cloud. In recent works, Reinforcement Learning (RL) has been introduced as a promising approach to learn the resource management policies to guide the scaling actions under the dynamic and uncertain cloud environment. However, RL methods face the following challenges in steering predictive autoscaling, such as lack of accuracy in decision-making, inefficient sampling and significant variability in workload patterns that may cause policies to fail at test time. To this end, we propose an end-to-end predictive meta model-based RL algorithm, aiming to optimally allocate resource to maintain a stable CPU utilization level, which incorporates a specially-designed deep periodic workload prediction model as the input and embeds the Neural Process [11, 16] to guide the learning of the optimal scaling actions over numerous application services in the Cloud. Our algorithm not only ensures the predictability and accuracy of the scaling strategy, but also enables the scaling decisions to adapt to the changing workloads with high sample efficiency. Our method has achieved significant performance improvement compared to the existing algorithms and has been deployed online at Alipay, supporting the autoscaling of applications for the world-leading payment platform. 

## **CCS CONCEPTS** 

• **Computing methodologies** → **Machine learning** ; • **Information systems** → **Process control systems** . 

## **KEYWORDS** 

autoscaling, reinforcement learning 

#### **ACM Reference Format:** 

Siqiao Xue<sup>∗</sup> ,Chao Qu<sup>∗</sup><sup>_,_+</sup> ,Xiaoming Shi, Cong Liao, Shiyi Zhu, Xiaoyu Tan, Lintao Ma, Shiyu Wang, Shijun Wang<sup>+</sup> , Yun Hu, Lei Lei, Yangfei Zheng, 

Permission to make digital or hard copies of all or part of this work for personal or classroom use is granted without fee provided that copies are not made or distributed for profit or commercial advantage and that copies bear this notice and the full citation on the first page. Copyrights for components of this work owned by others than ACM must be honored. Abstracting with credit is permitted. To copy otherwise, or republish, to post on servers or to redistribute to lists, requires prior specific permission and/or a fee. Request permissions from permissions@acm.org. _KDD ’22, August 14–18, 2022, Washington, DC, USA_ 

© 2022 Association for Computing Machinery. ACM ISBN 978-1-4503-9385-0/22/08...$15.00 

https://doi.org/10.1145/3534678.3539063 

Jianguo Li, James Zhang. 2022. A Meta Reinforcement Learning Approach for Predictive Autoscaling in the Cloud. In _Proceedings of the 28th ACM SIGKDD Conference on Knowledge Discovery and Data Mining (KDD ’22), August 14–18, 2022, Washington, DC, USA._ ACM, New York, NY, USA, 10 pages. https://doi.org/10.1145/3534678.3539063 

## **1 INTRODUCTION** 

One of the key characteristics of operating in the Cloud is autoscaling<sup>1</sup> , which elastically scales the resources _horizontally_ (the number of virtual machines (VMs) assigned is changed) or _vertically_ (the CPU and memory reservations are adjusted), to match the changing workload. According to the timing of scaling, the autoscaling strategies can be divided into responsive and predictive strategies. Compared to the responsive ones, predictive strategies forecast the workloads and prepare the resources _in advance_ to meet the future demands, therefore yielding better scaling timeliness [29] and becoming popular in industrial practises [5, 21]. 

In this paper, we focus on building the **predictive horizontal scaling** strategies at the Cloud of Alipay, the world’s leading digital payment platform, to ensure this large-scale system meets its stringent service level objectives (SLOs)<sup>2</sup> . The system consists of over 3000 running applications/services<sup>3</sup> on over 1 million VMs. The operator allocates VMs to applications based on performance indicators (e.g., CPU utilization) dependent on workloads. The workload of applications in Alipay is mainly driven by the traffic of several subtypes, e.g, Remote Procedure Calls (RPC), Message Subscription (MsgSub), etc, and we formulate it as a **multi-dimensional vector** throughout the paper. Figure 1a illustrates the evolution of two subtypes of the workload of an online application and Figure 1b shows that its CPU utilization fluctuates with the workload. Without the scaling, the operator usually allocates resources based on the peak CPU utilization, which produces notably wastage because most of the time, the utilization is far below the peak. Therefore, we aim at timely adjusting the number of VMs according to the needs of workload to **keep the CPU utilization of applications running stably at the desired target level** to maximize resource savings. 

> *These authors contributed equally to this work 

> 1Please see Appendix A.1.1- A.1.2 for a detailed introduction on autoscaling. 

> 2Please see Appendix A.1.3 for a detailed description of the cloud system. 

> 3In this paper, we interchangeably use these two terms. 

KDD ’22, August 14–18, 2022, Washington, DC, USA 

Xue and Qu, et al. 



<!-- Start of picture text -->
RPC<br>4000 MsgSub<br>3000<br>2000<br>1000<br>(a) The RPC and MsgSub traffic of a cloud application.<br>0.40<br>0.35 no scaling<br>0.30 after scaling<br>0.25<br>0.20<br>0.15<br>0.10<br>(b) The CPU utilization of the same application.<br>01:00 13:00 01:00 13:00 01:00 13:00 01:00<br>01:00 13:00 01:00 13:00 01:00 13:00 01:00<br>Num of Requests<br>CPU Utilization<br><!-- End of picture text -->



<!-- Start of picture text -->
0.25<br>0.20<br>0.15<br>0.10<br>0.05<br>150 300 450 75 90 105 1500 3000 4500<br>RPC (App 1) RPC (App 2) RPC (App 3)<br>(a) The fitted correlation between RPC traffic and CPU Utilization.<br>0.25<br>0.20<br>0.15<br>0.10<br>0.05<br>200 400 40 80 120 160 200 400 600 800 1000<br>MsgSub (App 1) MsgSub (App 2) MsgSub (App 3)<br>(b) The fitted correlation between MsgSub traffic and CPU Utilization.<br>CPU Utilization<br>CPU Utilization<br><!-- End of picture text -->

**Figure 2: The correlation between two subtypes of the workload and CPU utilization of three randomly chosen applications from July 29th to Aug 1st, 2021.** 

**Figure 1: The multidimensional workload and CPU utilization of a cloud application from July 29th to Aug 1st, 2021.** 

## **2 PRELIMINARIES** 

Considering the Cloud is a dynamic and uncertain environment, Reinforcement Learning (RL) serves as a good candidate for autoscaling since it is capable of learning transparent (with no human intervention), dynamic (no static plans) and adaptable (constantly updated) resource management policies to execute scaling actions. Recently, several RL-based methods have been proposed [7, 8, 14, 22, 29], achieving excellent performance in resource saving. However, the existing RL-based methods face several challenges: (i) The prediction of workloads relies on classical time series models (e.g., ARIMA), which have been proven to have limited learning ability compared to the deep learning models [19, 23, 30]; (ii) Most of existing RL algorithms for autoscaling are model-free, which involves prohibitively risky and costly operations in the cloud because they require numerous and direct interactions with the online environment during training; (iii) The variability in the performance of VMs across different applications is neglected. Previous works either naively think all VMs perform identically or cope with this heterogeneity by modeling them separately, but neglecting the commonalities across them. 

**Contributions:** In this paper, we propose a novel RL-based predictive autoscaling approach: 

- We develop a deep attentive periodic model for multi-dimensional multi-horizon workload prediction, which provides high-precision and reliable workload information for scaling. 

- We employ a meta-learning model to train a dynamic prior of the map from the workload to CPU utilization, with rapid adaptation to the changing environment, embedded to guide the learning of optimal scaling actions over thousands of online applications. The meta model-based RL algorithm enables safe and data-efficient learning. 

- To the best of our knowledge, our approach is the first fully differentiable RL-based predictive autoscaling strategy, which has been successfully deployed to support autoscaling at Alipay, the world-leading payment platform. 

In this section, we firstly present three key insights on the problem as background and motivations and then briefly introduce **Neural Process** and **Markov Decision Process** that are building blocks of our proposed approach. 

## **2.1 Background and Characterization** 

**Insight 1: The workload patterns usually have a complex composition of various periodicity.** The workloads of the most applications at Alipay Cloud are driven by repeatable business behavior (e.g., daily payment during rush hours) with occasional interventions from the platform (e.g., online marketing campaign), and hence usually exhibit a composition of periodicity with abrupt changes, as shown in Figure 1a. Many existing works use either classical regression techniques [29] or simple neural networks [15, 24] to forecast the workload, which are ineffective in capturing either inherent periodicity or complex temporal dependencies. We resort to deep time series models that have achieved notable success recently [19, 30]. 

**Insight 2: The workload has heterogeneous impact on CPU utilization.** As illustrated in Figure 2, the heterogeneity exists in two perspectives: (i) The mapping from workload to CPU utilization varies for different applications; (ii) For the same application, the subtypes of workload have diverse correlation with the CPU utilization. A naive solution is to train a model to learn such mapping for each application, which may have high performance but suffers from unaffordable time and maintenance cost. By defining the learning of the mapping for an application as a _task_ , we are motivated to apply the meta-learning techniques [10] to train a universal model for all the tasks which exploits commonalities and differences across tasks simultaneously. 

**Insight 3: Finding optimal resources given CPU utilization estimation forms a dynamic decision process.** The ultimate goal of our approach is to decide accurate resources allocation (VMs) for the application according to the estimation of CPU utilization. The relationship between resources and CPU utilization is complex and adjusting the resources usually incur certain costs in the Cloud 

KDD ’22, August 14–18, 2022, Washington, DC, USA 

A Meta Reinforcement Learning Approach for Predictive Autoscaling in the Cloud 

(e.g., engineering cost when switching VMs for applications). We resort to RL to find such optimal numbers of VMs while minimizing cost over the long term. Noted that model-based RL is more reliable than model-free methods for large scale Cloud systems because it samples efficiently and effectively avoids the potential risk caused by direct interactions between the scaling model and the online environment during training. 

## **2.2 Neural Processes and Meta learning** 

By taking the **meta-learning framework** , Neural Process (NP) learns to learn a regression method that maps a context set of observed input-output ( _𝑥𝑖,𝑦𝑖_ ) to a distribution over regression function [11]. Each function models the distribution of the output given an input, conditioned on the context. In particular, condition on observed **<u>Contexts</u>** ( _𝑥𝐶,𝑦𝐶_ ) := ( _𝑥𝑖,𝑦𝑖_ ) _𝑖_ ∈ _𝐶_ each function models **<u>Targets</u>** ( _𝑥𝑇 ,𝑦𝑇_ ) := ( _𝑥𝑖,𝑦𝑖_ ) _𝑖_ ∈ _𝑇_ , which is _𝑝_ ( _𝑦𝑇_ | _𝑥𝑇 ,𝑥𝐶,𝑦𝐶_ ). The latent version of NP includes a _global_ latent variable _𝑧_ to account for uncertainty in the predictions of _𝑦𝑇_ for a given context: 



with _𝑟𝐶_ := _𝑟_ ( _𝑥𝐶,𝑦𝐶_ ) where _𝑟_ is a deterministic function that aggregates ( _𝑥𝐶,𝑦𝐶_ ) into a finite dimensional representation with permutation invariance in _𝐶_ . The parameters of the encoder _𝑞_ ( _𝑧_ | _𝑠𝐶_ ) and the decoder _𝑝_ ( _𝑦𝑇_ | _𝑥𝑇 ,𝑟𝐶,𝑧_ ) are learned by maximising the ELBO: 



NP can be interpreted as a _meta learning_ approach [11, 16, 25], since the probabilistic representation _𝑧_ captures the current uncertainty over the task, allowing the network to explore in new tasks in a similarly structured manner. 

## **2.3 Markov Decision Process** 

Markov Decision Process (MDP) is described by a 5-tuple (S _,_ A _,𝑟, 𝑝,𝛾_ ): S is the state space, A is the action space, _𝑝_ is the transition probability, _𝑟_ is the expected reward, and _𝛾_ ∈[0 _,_ 1) is the discount factor [26]. That is, for _𝑠_ ∈S and _𝑎_ ∈A, _𝑟_ ( _𝑠,𝑎_ ) is the expected reward, _𝑝_ ( _𝑠_<sup>′</sup> | _𝑠,𝑎_ ) is the probability to reach the state _𝑠_<sup>′</sup> . A policy is used to select actions in the MDP. In general, the policy is stochastic and denoted by _𝜋_ , where _𝜋_ ( _𝑎𝑡_ | _𝑠𝑡_ ) is the conditional probability density at _𝑎𝑡_ associated with the policy. The state value evaluated on policy _𝜋_ can be represented by _𝑉_<sup>_𝜋_</sup> ( _𝑠_ ) = E _𝜋_ [<sup>�</sup> _𝑡_<sup>∞</sup> =0<sup>_𝛾𝑡𝑟_(</sup><sup>_𝑠𝑡,𝑎𝑡_)|</sup><sup>_𝑠_0=</sup><sup>_𝑠_]on</sup> immediate reward return _𝑟_ with discount factor _𝛾_ ∈(0 _,_ 1) along the horizon _𝑡_ . The agent aims to seek a policy that maximizes the long term return. In model-based RL, the agent uses a predictive model of the world to ask questions of the form “what will happen if I do action _a_ ?” to choose the best policy. In the alternative modelfree approach, the modeling step is bypassed altogether in favor of learning a control policy directly through the interaction with the environment. In general, the model-based RL is more sampleefficient than the model-free counterpart [9]. 

## **3 PROBLEM SETUP** 

Given the historical workload of an application _𝒙𝑡_ − _𝐿_ : _𝑡_ at time _𝑡_ , we aim to find the optimal VM allocations _𝑎𝑡_ +1: _𝑡_ + _𝐻_ over the future period _𝐻_ to make the CPU Utilization running stably at a target level 

|Symbol|Description|
|---|---|
|I|The set of applications|
|_𝐿, 𝐻_∈R+|The lengths of historical and forecast windows<br>i|
|ID∈R+<br>_𝒙𝑡_∈R<sup>_𝑑_</sup><br>_𝒖𝑡_∈R<sup>2</sup>|The unique identifier of each application<br>_𝑑_-dim workload of an application at_𝑡_<br>2-dim time-based covariate at_𝑡_|
|_𝑐𝑡_∈R+|CPU utilization of an application at_𝑡_|
|^_𝑐𝑡_∈R+|Predicted CPU utilization of an application at_𝑡_|
|_𝑐_[_𝑡,𝑡_+1) ∈R+|Average CPU of an application at [_𝑡,𝑡_+1)|
|_𝑙𝑡_∈R+|The number of allocated VMs|
|_𝑎𝑡_∈[−0_._5_,_2]<br>_𝒔𝑡_∈R<sup>_𝑑𝑚_</sup>|The adjustment rate of # allocated VMs<br>The state of MDP for an application at_𝑡_|
|¯_𝒙𝑡_∈R<sup>_𝑑_</sup><br>¯_𝒙_<sup>**′**</sup><br>_𝑡_<sup>∈R</sup><sup>_𝑑_</sup>|The unit workload of an application at_𝑡_<br>The unit workload of an application<br>after the adjustment at t|
|¯_𝑿𝑡_∈R<sup>_𝑑_+2</sup><br>|¯_𝑿𝑡_:= (_𝒖𝑡,_¯_𝒙𝑡_)|
|¯_𝑿_<sup>′</sup><br>_𝑡_<sup>∈R</sup><sup>_𝑑_+2</sup>|¯_𝑿_<sup>′</sup><br>_𝑡_<sup>:= (</sup><sup>_𝒖𝑡,_ ¯</sup><sup>_𝒙_′</sup><sup>_𝑡_)</sup>|



**Table 1: Table of Notations** 

( e.g., in Figure 1b the target CPU utilization is 40%). In addition, we want to build a _universal_ controller for thousands of heterogeneous tasks which can adapt to the rapidly changing environment or even unseen tasks, guaranteeing the flexibility and the robustness of the controller in the real industrial system. To satisfy the demanding requests, we propose one reasonable assumption to simplify the problem that is generally satisfied in practise: 

**Assumption 1:** The workload of an application are evenly allocated in VMs, e.g., if the workload is represented as a 2-dim vector of traffic ( _𝑅𝑃𝐶, 𝑀𝑠𝑔𝑆𝑢𝑏_ ) = (100 _,_ 50) running on 5 VMs, then the unit workload per VM is (20 _,_ 10). 

We leverage the assumption to build the latent dynamic model in model-based RL. The notation used throughout the paper is in Table 1. In general, **we use the bar over the alphabet to denote the unit value** , e.g., the unit workload ¯ _𝑥𝑡_ . The superscript<sup>′</sup> stands for the value after the adjustment. 

## **4 END-TO-END LEARNING TO AUTOSCALE** 

Three primary components comprise our approach: 

- (1) A deep attentive periodic time series model that that holds sufficient capacity to capture complex periodicity of workload patterns discussed in _Insight 1_ . 

- (2) A neural process model that meta-learns the map from the workload to the CPU utilization of applications, which addresses the heterogeneous effect discussed in _Insight 2_ . 

- (3) An MDP with the above two models embedded to seek the optimal numbers of VMs so that the CPU utilization is kept at a target level, resulting in a model-based RL that avoids the potential deficiencies described in _Insight 3_ . 

The three components are marked as 1 _,_ 2 _,_ 3 in Figure 3 and described below respectively. Different from the previous works [20, 29], the components are all amenable to auto-differentiation, which effectively avoid issues of convergence stability and dataefficiency, constituting a single global autoscaling strategy. 

KDD ’22, August 14–18, 2022, Washington, DC, USA 

Xue and Qu, et al. 



<!-- Start of picture text -->
1 Workload Forecaster  2 CPU Utilization Meta Predictor Task  Policy 3 DeciderScaling<br>Embedding<br>Periodicity  Attention Latent Task  Reward Network Action<br>Historical Workload  Extractor  Decoder Workload Prediction Context SetEncoder DecoderTarget  UtilizationCPU  FunctionValue<br>…<br>Update<br>Back-Propagation<br>(a) Synergy diagram of Workload Forecaster, CPU Utilization Meta Predictor, and Scaling Decider.<br>Keys Query<br>e 1 p e 2 p e n p x ˆ t +1 … x ˆ t + H Deterministic PathLatent Path + x ¯1<br>LSTM… Periodicity ExtractorLSTM … LSTM … hp Keys MLPPeriodicity Attn… MLP + Concatenation Values +…+ xx ¯¯23 + x ¯ t State Hidden Layer Action<br>e 1 1 e 2 1 e n 1 Values … r 1<br>Multi-Head<br>LSTM LSTM … LSTM h 1 Attention + x ¯1 c 1 AttnSelf r 2 CrossAttn rt MLP c ˆ t + x ¯ t<br>Period 1 Period n Target Period r 3<br>e 1 1 … e 1 p … e n 1 … en p et +1 … et + H + x ¯2 c 2 s 1 z at<br>c ˆ t<br>Feature Embedding Layer + x ¯3 c 3 AttnSelf s 2 + sm z<br>… s 3<br>x ¯1 … xp … xt−p +1…  xt … Context Set<br>Encoder Decoder<br>Past Inputs Known Future Inputs 2 Attentive Neural Process 3 Deep Policy Network<br>1 Deep Attentive Periodic Model<br>(c) The architecture of CPU Utilization Meta Pre- (d) The architecture of Scaling De-<br>(b) The architecture of Workload Forecaster. dictor cider.<br><!-- End of picture text -->

**Figure 3: The end-to-end predictive autoscaling framework.** 

## **4.1 Stage 1: Predict Workload Pattern via Deep Attentive Periodic Time Series Model** 

In our approach, workload prediction is needed to estimate the incoming workload of the applications for future periods. As mentioned in _Insight 1_ , most of the previous works utilize classical time series models and the application of advanced deep models are less well studied. Nonetheless, instead of directly applying the stateof-the arts, such as _Informer_ [30] and _ConvTransformer_ [19], we propose Deep Attentive Periodic Model ( **DAPM** ) with two distinctive characteristics for workload predictions: 

- A lightweight _periodicity extractor_ that captures inherent seasonality of the workload, where the data exhibits constant patterns of rises and falls, as seen in Figure 1a. 

- A _periodicity attention_ module that learns complicated periodic dependencies of the workload. 

We reduce the problem to learning a universal prediction model for all applications 



where _𝜃_ is the parameters of the function _𝑓_ and _𝒖𝑡_ − _𝐿_ : _𝑡_ + _𝐻_ is a set of 2-dim covariates _𝒖𝑡_ = { _𝑢𝑡,𝑑,𝑢𝑡,ℎ_ } assumed to be known over the entire time period: day-of-the-week _𝑢𝑡,𝑑_ and hour-of-the-day _𝑢𝑡,ℎ_ . We firstly initialize a feature embedding layer to generate input 

embedding _𝒆𝑡_ ∈ R<sup>_𝑚_</sup> at each timestamp 



where _𝑓_ is an embedding map of the covariates. Secondly, we cluster all the _𝒆𝑖_ into _𝑛_ groups with _𝑝_ vectors in each. Then we construct _𝑛_ LSTM layers with the _𝑖_ -th LSTM layer taking { _𝒆𝑖_<sup>_𝑗, 𝑗_=1:</sup><sup>_𝑛_} as</sup> the input. The rationale behind is, by setting _𝑝_ to be the seasonality length of the workload, we can utilize LSTM to learn the dynamics of inherent periodical behaviors, e.g., rise and fall pattern every 24 hours, explicitly at each snapshot. 

Finally, we pass the last hidden state of each LSTM layers into the multihead attention [28] as _𝐾_ = _𝑉_ = { _𝒉_ 1 _, ..., 𝒉𝑝_ } with embeddings form known future covariates are taken as Queries _𝑄_ = { _𝒆𝑡_ +1 _, ..., 𝒆𝑡_ + _𝐻_ }, which learns a weighted combination of hidden representations of periodicity: 



where _𝑊ℎ_<sup>_𝑄_∈R</sup><sup>_𝑑𝑄_×</sup><sup>_𝑑,𝑊_</sup> _ℎ_<sup>_𝐾_∈R</sup><sup>_𝑑𝐾_×</sup><sup>_𝑑_and</sup><sup>_𝑊_</sup> _ℎ_<sup>_𝑉_∈R</sup><sup>_𝑑𝑉_×</sup><sup>_𝑑_are learned</sup> linear transformation matrices for query, key and value respectively. The _multihead_ lies in using different sets of weight { _𝑊ℎ_<sup>_𝑄,𝑊_</sup> _ℎ_<sup>_𝐾,𝑊_</sup> _ℎ_<sup>_𝑉_}</sup> _ℎ_<sup>_𝐻_</sup> =1 to compute a set of attention output { _𝑺_ 1 _, ..., 𝑺𝐻_ } and the final output of the attention is _𝑺_ = [ _𝑺_ 1 _, ..., 𝑺𝐻_ ] _𝑊_<sup>_𝑂_</sup> , which is followed by MLP to produce the multi-step predictions _𝒙_ ^ _𝑡_ +1: _𝑡_ + _𝐻_ . The model is trained by minimizing the RMSE loss between _𝒙𝑡_ +1: _𝑡_ + _𝐻_ and _𝒙_ ^ _𝑡_ +1: _𝑡_ + _𝐻_ . 

KDD ’22, August 14–18, 2022, Washington, DC, USA 

A Meta Reinforcement Learning Approach for Predictive Autoscaling in the Cloud 

## **4.2 Stage 2: Learn the Mapping From Workload to CPU Utilization via Neural Process** 

As discussed in _Insight 2_ , the fact that VMs perform heterogeneously _across the applications_ motivates **the use of meta-learning on the uncertainty over tasks of learning the heterogeneous mapping from the unit workload** _𝒙_ ¯ _𝑡_ :=<sup>_<u>𝒙</u>_</sup> _𝑙𝑡_<sup>_<u>𝑡</u>_</sup><sup>**to CPU utilization**</sup><sup>_𝑐𝑡_.</sup> We choose Attentive Neural Process (ANP), a state-of-the-art NP from DeepMind [16]. As depicted in Figure 3c, ANP uses an attention module to encode complex dependencies between the context along with a probabilistic representation vector capturing the global distribution of uncertainty over tasks, helping automate downstream scaling decision-making problem. 

Considering the existence of heterogeneity among applications, we introduce the covariate _𝒖𝑡_ as an auxiliary feature to the model input along with the unit workload: _𝑿𝑡_ = ( _𝒖𝑡 ,_ ¯ _𝒙𝑡_ ). Then we define the context set as C = {( _𝑿𝑠,𝑐𝑠_ )} _𝑠_<sup>_𝐼𝐷_</sup> ∈[<sup>∈I</sup> _𝑡_ − _𝐿_ : _𝑡_ ]<sup>andtargetsetas</sup> T = {( _𝑿𝑠,𝑐𝑠_ )} _𝑠_<sup>_𝐼𝐷_</sup> ∈[<sup>∈I</sup> _𝑡_ +1: _𝑡_ + _𝐻_ ]<sup>. An input embedding layer is designed</sup> to transform _𝑋𝑡_ into a dense vector before feeding into the model. In particular, we map the context information ( _𝑥_ ¯ _𝑖,𝑐𝑖_ ) into a finite dimensional representation _𝑟𝑖_ through a self-attention module. Given the target input, i.e., the query in Figure 3c, we do the cross multihead attention, whose formulation is described in Equation 5, over the key-value pairs to predict the target output _𝑟𝑡_ . 

As depicted in Figure 3c, besides this deterministic representation, ANP has a stochastic path, where the output _𝑧_ is a global latent variable to account for uncertainty in the prediction of _𝑐𝑡_ for a given observed ( _𝑿𝑠,𝑐𝑠_ ). The structure is similar to the deterministic one, but now we aggregate _𝑠𝑖_ into a single vector _𝑠_ by taking the mean. _𝑧_ is modelled as a factorized Gaussian distribution using the reparameterization trick with its mean and variance [18]. 

The encoder _𝑞_ outputs the hidden representation _𝑧_ and the reference _𝑟_ while the decoder _𝑝_ aggregates the information of _𝑟𝑐,𝑧,𝑋𝑇_ and outputs the target output _𝑦𝑡_ . ANP is trained by optimizing Equation 2 over the context and target sets, with two folds of output: 

- Predicted CPU utilization ^ _𝑐𝑡_ on the target set<sup>4</sup> . 

- A global probabilistic latent representation _𝑧_ , which can be seen as the _task embedding_ encoding salient information of the task given the context information. Intuitively, it tells the agents what kind of tasks they face. 

In the following, we demonstrate how to leverage the learned ANP in the dynamic model of the model-based RL. 

## **4.3 Stage 3: Autoscale via Meta Model-based RL** 

Based on _Insight 3_ , we establish the scaling process as a model-based RL algorithm. Given the workload prediction from _Stage 1_ , the agent learns to continually scale the number of VMs by interacting with the CPU utilization estimator trained from _Stage 2_ . The goal is to keep the CPU utilization stable in the future period. 

_4.3.1 The MDP Formulation._ We define the MDP of the scaling strategy as: 

> 4The input of target set uses ground truths of _𝒙_ ¯ _𝑠,𝑠_ ∈[ _𝑡_ − _𝐿_ : _𝑡_ ] in training stage while using predicted<sup>**�**</sup> _𝒙_ ¯<sup>_𝑖_</sup> _𝑠_<sup>_,𝑠_∈[</sup><sup>_𝑡_+ 1 :</sup><sup>_𝑡_+</sup><sup>_𝐻_]in the test stage.</sup> 

- State space S: State _𝒔𝑡_ := ( _𝑿_<sup>¯</sup> _𝑡 ,𝑧,_ ^ _𝑐𝑡 ,𝑙𝑡_ ) is a tuple of unit workload, task embedding _𝑧_ , the corresponding estimated CPU utilization, and the number of allocated VMs. 

- Action space A: We design the adjustment rates _𝑎𝑡_ , so that the number of VMs allocated _𝑙𝑡_ typically takes the form of _𝑙𝑡_ +1 = _𝑙𝑡_ × (1 + _𝑎𝑡_ ) where _𝑎𝑡_ is the adjustment rate. In practice, we set the lower bound and the upper bound of the _𝑎𝑡_ to be −0 _._ 5 and 2, respectively. 

- Reward _𝑟𝑡_ : The immediate reward at time step _𝑡_ is defined as _𝑟𝑡_ := −( _𝑐_ [ _𝑡,𝑡_ +1) − _𝑐𝑡𝑎𝑟𝑔𝑒𝑡_ )<sup>2</sup> − _𝜂_ ( _𝑙𝑡_ +1 − _𝑙𝑡_ )<sup>2</sup> , which is the weighted sum of two terms: (i) a distance between current CPU utilization and the target one; (ii) a switching cost to penalize the adjustments of VMs, which makes our strategy applicable in the real-world setting. The hyper parameter _𝜂_ is a positive constant to balance between the two terms. 

• Discount factor _𝛾_ : In our case we set to _𝛾_ = 0 _._ 95. _Assumption 1_ indicates _𝒙_ ¯ _𝑡_<sup>′=</sup> _𝑙𝑡_ (1 _<u>𝒙</u>_ + _<u>𝑡𝑎𝑡</u>_ )<sup>and we use ANP trained in</sup> _Stage 2_ to predict the CPU utilization ^ _𝑐𝑡_ after the adjustment. In particular, 



Recall that the first term of reward function is −( _𝑐_ [ _𝑡,𝑡_ +1) − _𝑐𝑡𝑎𝑟𝑔𝑒𝑡_ )<sup>2</sup> and in practice, we use the predicted value ^ _𝑐𝑡_<sup>′to replace</sup><sup>_𝑐_[</sup><sup>_𝑡,𝑡_+1).</sup> Then we plug _𝑙𝑡_ +1 = _𝑙𝑡_ (1 + _𝑎𝑡_ ) into the second term, and we have the reward function: 



Notice that _𝑟𝑡_ is a function of _𝑠𝑡_ and _𝑎𝑡_ , i.e., _𝑟𝑡_ = _𝑟_ ( _𝑠𝑡 ,𝑎𝑡_ ). After imposing the action _𝑎𝑡_ , the system arrives at the next state _𝑠𝑡_ +1 = ( _𝑿_<sup>¯</sup> _𝑡_ +1 _,𝑧,_ ^ _𝑐𝑡_ +1 _,𝑙𝑡_ +1) _._ Regarding the term _𝑿_<sup>¯</sup> _𝑡_ +1 and ^ _𝑐𝑡_ +1, we use the predicted workload at _𝑡_ + 1 obtained from the time series model to estimate _𝑿_<sup>¯</sup> _𝑡_ +1, which is then fed into _𝑓𝐴𝑁𝑃_ to obtain ^ _𝑐𝑡_ +1. _𝑧_ is a time invariant term to characterize the property of tasks. _𝑙𝑡_ +1 = _𝑙𝑡_ (1+ _𝑎𝑡_ ) is the dynamics over the allocated VMs. To ease the exposition, we denote overall dynamics over the state by 



**Key observations** : Both reward and dynamic models are differentiable w.r.t. the input action _𝑎𝑡_ . In particular, ^ _𝑐𝑡_<sup>′is</sup><sup>_differentiable_</sup> w.r.t. the action _𝑎𝑡_ through the mapping of _𝑓𝐴𝑁𝑃_ and therefore the _𝑟𝑡_ is also a differentiable function w.r.t. _𝑎𝑡_ . We will leverage these key properties in the derivation of the following model-based RL algorithm. 

_4.3.2 Policy Learning._ The policy _𝜋_ ( _𝑎𝑡_ | _𝑠𝑡_ ) is a mapping from the state to the distribution of action. For simplicity, we assume the policy is deterministic and is parameterized by a neural network, i.e., _𝑎𝑡_ = _𝜋𝜓_ ( _𝒔𝑡_ ), where _𝜓_ are the weights of the neural network. Different from the model-free RL algorithm such as Q-learning [27] and Actor-Critic [26], we do not learn the optimal policy from the interactions with environment by TD-learning. Remind that we have already obtained the dynamic model _𝑠𝑡_ +1 = _𝑔_ ( _𝑠𝑡 ,𝑎𝑡_ ) and reward model _𝑟_ ( _𝑠𝑡 ,𝑎𝑡_ ). To find the optimal _𝜓_ to maximize the long term reward, we embed above two models into the Bellman equation. Recall that Bellman equation for the value function: 



KDD ’22, August 14–18, 2022, Washington, DC, USA 

Xue and Qu, et al. 

where the expectation is over the randomness of the dynamic model. We unroll the Bellman equation _𝐻_ steps, which is 



In practice, we discard the term _𝛾_<sup>_𝐻_+1</sup> _𝑉_<sup>_𝜋_</sup> ( _𝑠𝑡_ + _𝐻_ +1). On one hand, we have the a discount factor _𝛾_<sup>_𝐻_+1</sup> ≪ 1 and this term has a negligible effect. On the other hand, the length of forecast window is _𝐻_ in Section 4.1 and we do not know the dynamics and reward beyond _𝐻_ steps. Therefore, we have a simplified form: 



We simulate the trajectory from _𝑡_ to _𝑡_ + _𝐻_ using the dynamic model and current policy _𝜋_ as that in [12] to obtain a MonteCarlo approximation. In particular, we have _𝑠𝑡_ +1 = _𝑔_ ( _𝑠𝑡 , 𝜋𝜓_ ( _𝑠𝑡_ )), _𝑠𝑡_ +2 = _𝑔_ ( _𝑔_ ( _𝑠𝑡 ,𝑎𝑡_ ) _, 𝜋𝜓_ ( _𝑠𝑡_ +1)) and so on. The next step is to conduct the policy improvement over the current policy. Remark that the right hand side of Equation 9 is a differentiable function w.r.t. _𝜓_ and we can carry out the gradient ascent to improve the policy by the automatic differentiation in Tensorflow [1], known as stochastic value gradient [13]. 



We combine all pieces together to obtain our Meta Model-based Predictive Autoscaling (MMPA), with the pseudocode presented in Algorithm 1. 

**Algorithm 1** Learning Algorithm of MMPA 

**Input:** 1) The dataset { _𝒙𝑡_ − _𝐿_ : _𝑡 , 𝒙𝑡_ +1: _𝑡_ + _𝐻_ } to train DAPM (Section 4.1 ). 2) Context set C and target set T to train the ANP Model (Section 4.2 ). 

### **Pretrain DAPM:** 

Optimize the RMSE loss between _𝒙𝒕_ **+** 1: _𝒕_ **+** _𝑯_ and _𝒙_ ^ _𝒕_ **+** 1: _𝒕_ **+** _𝑯_ . **Pretrain ANP:** 

For each iteration, we randomly sample tasks from context set _𝐶_ and target set _𝑇_ to train the ANP model by optimizing the ELBO in Equation 2. Finish the training until ANP converges. 

### **Train Policy:** 

**for** each RL step **do** 

### **Unroll the dynamic model and calculate reward:** 

Using dynamic model _𝑔_ to simulate the state _𝑠𝑡_ +1 to _𝑠𝑡_ + _𝐻_ and corresponding reward _𝑟𝑡_ +1 to _𝑟𝑡_ + _𝐻_ . Obtain a Monte-Carlo approximation of Equation 9. 

### **Update policy:** 

- Update policy _𝜓_ using stochastic value gradient, i.e., Equation 10. 

### **end for** 

vector, containing traffics of Remote Procedure Calls (RPC), Message Subscription (MsgSub), Message Push (MsgPush), External Application (EA), Database Access (DA), Write Buffer (WB) and Page View (PV). The details of dataset could be found in Appendix A.2.1. 

The first three weeks are the train period while the last week is the test period. Illustrated in Table 2, we perform the **online evaluation** of 5 representative applications for the end-to-end scaling over the period of a week, where we scale the application every 4 hour based on predicted workload, i.e., the historical and predictive windows are set to 288 and 24, respectively. 

|Symbol|Service domain|Dominant traffic|
|---|---|---|
|A1|file service|RPC, EA|
|A2|database|DA, WB|
|A3|web|RPC, PV|
|A4|tool|RPC, DA|
|A4|messaging|RPC, MsgSub, MsgPush|



**Table 2: Descriptions of 5 sample applications** 

_5.1.2 Baselines and Metrics._ Firstly we compare the workload prediction performance of DAMP with two state-of-the-arts: _Informer_ [30] and _ConvTransformer_ [19]. Then we validate NP by comparing its capability of CPU utilization estimation with two widely-applied classic methods including _LR_ and _XGBoost_ in the context of autoscaling. Finally, we compare our end-to-end scaling approach against two industrial benchmarks: 

- Autopilot [8]: a workload-based autoscaling method proposed by Google, which builds the optimal resource configuration by seeking the best matched historical time window to the current window. We implement Autopilot based on its public paper [8]. 

- FIRM [22]: a RL-based autoscaling method, which solves the problem through learning feedback adjustment with the online cloud environment. Specifically, FIRM finds applications with abnormal response time (RT) through SVM-based anomaly detection algorithms and adjusts multiple resources for the service through RL algorithms. We implement FIRM using the author’s gitlab code _https://gitlab.engr.illinois.edu/DEPEND/firm_ . 

We evaluate the workload and CPU utilization prediction by MAE and RMSE. For end-to-end autoscaling, we set the target CPU utilization at 40% and evaluate the performance of the strategy by RCS (Relative CPU Stability rate) with a 2% error, i.e., the percentage of time the CPU utilization is within 40% ± 2%. 

_5.1.3 Implementation of Our Approach._ We implemented our approach based on Python 3.6.3 and Tensorflow 1.13.1. The details of the implementation and sample code<sup>5</sup> can be found in Appendix A.2.2. 

## **5 EXPERIMENTS** 

## **5.1 Setup** 

_5.1.1 Dataset._ We collected one month 10min-frequency data of the workload and CPU utilization of 50 core applications from the cloud system of Alipay for **offline evaluation** of the workload and CPU prediction. The workload is constructed as a 7-dimensional 

## **5.2 Experiment Results** 

_5.2.1 Effectiveness of Workload Prediction._ Generally, Informer and ConvTransformer have failed to capture certain complex temporal patterns of the time series, e.g, in Figure 4a, change points at 3 am 5 _https://github.com/iLevyFan/meta_rl_scaling_ 

KDD ’22, August 14–18, 2022, Washington, DC, USA 

A Meta Reinforcement Learning Approach for Predictive Autoscaling in the Cloud 

|Target|Method|MAE|RMSE|
|---|---|---|---|
|Workload|Informer<br>ConvTransformer|1.75<br>(0.15)<br>1.50<br>(0.19)|202.10<br>(19.8)<br>172.84<br>(18.9)|
||**Ours**|**1.10**<br>(0.09)|**112.59**<br>(13.1)|
||LR|1.40<br>(0.15)|2.48<br>(0.24)|
|CPU|XGB|1.23|1.93|
|Utilization|oost<br>**Ours**|(0.14)<br>**0.86**<br>(0.09)|(0.20)<br>**1.11**<br>(0.11)|



#### **(a) Workload and CPU utilization prediction evaluation.** 

|Method|A1|A2|A3|A4|A5|
|---|---|---|---|---|---|
|Ail|0.77|0.75|0.65|0.66|0.84|
|utopot|(0.056)|(0.044)|(0.062)|(0.059)|(0.041)|
||0.81|0.79|0.85|0.80|0.86|
|FIRM|(0.086)|(0.084)|(0.069)|(0.077)|(0.061)|
|O|**0.95**|**0.93**|**0.92**|**0.95**|**0.91**|
|urs|(0.076)|(0.094)|(0.083)|(0.099)|(0.071)|



#### **(b) Relative CPU stability rate of autoscaling strategy evaluation.** 

|# Test Applications|50|100|200|500|
|---|---|---|---|---|
|RMSE|1.11<br>(0.14)|1.19<br>(0.13)|1.31<br>(0.13)|1.33<br>(0.15)|



**(c) CPU utilization prediction error over large-size test set.** 

**Table 3: Mean and standard deviation (in bracket) of experiment results on test period** 





<!-- Start of picture text -->
(a) The workload (RPC traffic) forecast of application A1.<br>(b) The CPU utilization prediction of application A1.<br>40<br>20<br>0<br>-20<br>-40<br>-80 60 40 -20 0 20 40 60 80<br><!-- End of picture text -->

**(c) Visualization of dense representations of input** _𝑋𝑡_ **in the training set of ANP with t-SNE.** 

of Application A1 are not well captured. Instead, our approach generates predictions that follows closely in the rise and fall of various periodicity because we employ modules especially designed to better capture composition of temporal patterns and periodicities. As a result, our model achieves a better MSE/RMSE ratio summarized in Table 3a. 

_5.2.2 Effectiveness of CPU Utilization Prediction._ As in Figure 4b and Table 3a, both LR and XGboost perform relatively poor due to their inability to handle complex nonlinear data. 

To validate the effectiveness of the meta-learning in our model, we firstly use t-SNE to plot the dense representations of all training inputs specified in Section 4.2, which shows 6 cluster centroids in the latent space, illustrated in Figure 4c, suggesting that when a new CPU utilization prediction task comes, its inputs may be possibly categorized into one of the groups in the latent space so that we can perform the prediction in a similarly structured manner. Then we train our model ANP, the-state-of-art meta model in the domain of CV, and run the prediction on the target set. The results in Table 3a demonstrate that our approach obtains smaller errors in the test period with around 25% improvement in MSE/RMSE, 

**Figure 4: Experiment results on workload and CPU utilization prediction.** 

which more effectively learns the heterogeneous relation between the workload and the CPU utilization. 

_5.2.3 Effectiveness of Online Predictive Scaling._ Due to space limitation, we only show the scaling results of A1 and A2 in Figure 5. The summary of all five services are presented in Table 3b. As in Figure 5, our approach achieves a steady CPU utilization around the target level during the entire day while Autopilot and FIRM have substantial fluctuations, e.g., Application 1 experiences utilization swings (rise and fall ) under FIRM from 23:00-6:00 and is always under target level from 19:00-6:00. 

Overall, our approach obtains **a higher CPU utilization steady rate and a less total number of VMs** : estimated from Table 3b and related statistics, the average steady rate of our approach is 19%/10% higher than Autopilot/FIRM and number of VMs of our 

KDD ’22, August 14–18, 2022, Washington, DC, USA 

Xue and Qu, et al. 





<!-- Start of picture text -->
(a) CPU utilization of application A1.<br>(b) CPU utilization of application A2.<br><!-- End of picture text -->

**Figure 5: CPU utilization trend of application A1 and A2 on a test period.** 

method is 21%/9% lower than Autopilot/FIRM. We summarize the reasons in three-folds: 

- Autopilot and FIRM adjust the resource based on exception detection instead of high-performance predictive techniques, therefore when encountering CPU utilization fluctuations, it takes time to bring it back to the target level by adjusting the numbers of VMs, during which the changing workload patterns may lead to swings in CPU utilization again. 

- Our approach, based on effective predictions of workload and CPU utilization, is able to adjust the VMs in advance with minor error, which stabilizes the CPU utilization. 

- With the embedded meta model of utilization estimation, our agent makes more accurate scaling decisions than that of FIRM trained in a model-free manner. 

- _5.2.4 Scalability._ Our approach has two particular characteristics that help with scalability: 

- We have trained a meta CPU utilization predictor ANP, facilitating fast adaptation to solve new prediction tasks without retraining the whole data again. As seen from Table 3c, the RMSE only increases by 20% while the number of predicted applications increase by 10 times, which proves that our approach can be effectively applied to performing the prediction on a large scale of applications. 

- As discussed in Section 4.3, our approach forms a fully differentiable scaling strategy that adequately avoid issues of convergence stability and data-efficiency, and is therefore applicable in large scale cloud systems. 

_5.2.5 Deployment._ Evidenced by the effectiveness and scalibility , our framework has been deployed in the real-world daily practices of Alipay Cloud. Compared to the _rule-based method_ in production, the CPU stability rate has been improved by over 20% with around 50% cloud resources saved. 

## **6 RELATED WORK** 

The recent works of autoscaling can be categorized into _rule-based_ approaches and _learning-based_ approaches. In typical rule-based approaches [5, 21], the key goal is to find the threshold that triggers the scaling mechanism, such as a fixed CPU value or an average response time. However such approaches usually require significant human efforts and experience and may fail to respond to changing workload swiftly. The learning-based approaches [2–4, 24, 29], which apply machine learning models to find abnormal states (e.g., CPU utilization is too high) of the system and optimize the resource, help to address these challenges. For example, [2] applies regression trees to model the relationship between the number of machines and response time and then generates the recommended number of machines to avoid service response time over time. 

Considering the scaling decision is taken under dynamic and uncertain environment in the online cloud, RL-based learning methods [6–8, 22] have been proposed to model the autoscaling as decisionmaking problems. **A distinctive difference** between our method and theirs is that we build a high-performance fully differentiable framework with a meta model-based RL algorithm to perform an end-to-end scaling strategy. It is noted that traditional model-based RL works [9, 12, 13] can not be directly applied because their algorithms only aim to solve a single task, which is impractical in dealing with numerous different applications in the industrial context. Instead, our RL algorithm is specially tailored for an industrial autoscaling system, incorporating specially-designed modules such as workload forecaster and CPU utilization meta predictor. 

## **7 CONCLUSION** 

We proposed a novel meta RL-based model, which is, to the best of our knowledge, the first RL-based fully differentiable framework for predictive scaling in the Cloud. Our approach is effective in stabilizing CPU utilization of applications and has been deployed in the real world to support the scaling in the Cloud of a worldleading mobile payment platform, with around 50% resource saved compared to the rule-based method in production. 

## **REFERENCES** 

> [1] Martín Abadi, Paul Barham, Jianmin Chen, Zhifeng Chen, Andy Davis, Jeffrey Dean, Matthieu Devin, Sanjay Ghemawat, Geoffrey Irving, Michael Isard, et al. 2016. TensorFlow: A System for Large-Scale Machine Learning. In _12th USENIX symposium on operating systems design and implementation (OSDI)_ . 265–283. 

> [2] Muhammad Abdullah, Waheed Iqbal, Josep Lluis Berral, Jorda Polo, and David Carrera. 2020. Burst-Aware Predictive Autoscaling for Containerized Microservices. _IEEE Transactions on Services Computing_ (2020), 1–1. https://doi.org/10. 1109/TSC.2020.2995937 

> [3] Muhammad Abdullah, Waheed Iqbal, Abdelkarim Erradi, and Faisal Bukhari. 2019. Learning Predictive Autoscaling Policies for Cloud-Hosted Microservices Using Trace-Driven Modeling. In _2019 IEEE International Conference on Cloud Computing Technology and Science (CloudCom)_ . 119–126. https://doi.org/10.1109/ CloudCom.2019.00028 

> [4] Giovanni Acampora, Mario Luca Bernardi, Marta Cimitile, Genoveffa Tortora, and Autilia Vitiello. 2017. A fuzzy-based autoscaling approach for process centered cloud systems. In _2017 IEEE International Conference on Fuzzy Systems (FUZZIEEE)_ . 1–8. https://doi.org/10.1109/FUZZ-IEEE.2017.8015768 

KDD ’22, August 14–18, 2022, Washington, DC, USA 

A Meta Reinforcement Learning Approach for Predictive Autoscaling in the Cloud 

- [5] Amazon. 2020. AWS auto scaling documentation. https://docs.aws.amazon.com/ autoscaling/index.html 

- [6] Hamid Arabnejad, Pooyan Jamshidi, Giovani Estrada, Nabil El Ioini, and Claus Pahl. 2016. An Auto-Scaling Cloud Controller Using Fuzzy Q-Learning - Implementation in OpenStack. In _ESOCC_ . 

- [7] J. V. Bibal Benifa and D. Dejey. 2019. RLPAS: Reinforcement Learning-Based Proactive Auto-Scaler for Resource Provisioning in Cloud Environment. _Mob. Netw. Appl._ 24, 4 (2019), 1348–1363. 

- [8] Mingxi Cheng, Ji Li, and Shahin Nazarian. 2018. DRL-Cloud: Deep Reinforcement Learning-Based Resource Provisioning and Task Scheduling for Cloud Service Providers. In _Proceedings of the 23rd Asia and South Pacific Design Automation Conference (ASPDAC ’18)_ . 129–134. 

- [9] Kurtland Chua, Roberto Calandra, Rowan McAllister, and Sergey Levine. 2018. Deep reinforcement learning in a handful of trials using probabilistic dynamics models. In _Advances in Neural Information Processing Systems (NeurIPS)_ . 

- [10] Chelsea Finn, Kelvin Xu, and Sergey Levine. 2018. Probabilistic model-agnostic meta-learning. In _Advances in neural information processing systems (NeurIPS)_ . 

- [11] Marta Garnelo, Dan Rosenbaum, Chris J. Maddison, Tiago Ramalho, David Saxton, Murray Shanahan, Yee Whye Teh, Danilo J. Rezende, and S. M. Ali Eslami. 2018. Conditional Neural Processes. In _International Conference on Machine Learning (ICML)_ . 

- [12] Danijar Hafner, Timothy Lillicrap, Jimmy Ba, and Mohammad Norouzi. 2020. Dream to control: Learning behaviors by latent imagination. In _International Conference on Learning Representations (ICLR)_ . 

- [13] Nicolas Heess, Greg Wayne, David Silver, Timothy Lillicrap, Yuval Tassa, and Tom Erez. 2015. Learning continuous control policies by stochastic value gradients. In _Advances in Neural Information Processing Systems (NIPS)_ . 

- [14] Pooyan Jamshidi, Amir Sharifloo, Claus Pahl, Hamid Arabnejad, Andreas Metzger, and Giovani Estrada. 2016. Fuzzy Self-Learning Controllers for Elasticity Management in Dynamic Cloud Architectures. In _12th International ACM SIGSOFT Conference on Quality of Software Architectures (QoSA)_ . 

- [15] Arijit Khan, Xifeng Yan, Shu Tao, and Nikos Anerousis. 2012. Workload characterization and prediction in the cloud: A multiple time series approach. In _IEEE Network Operations and Management Symposium_ . 1287–1294. 

- [16] Hyunjik Kim, Andriy Mnih, Jonathan Schwarz, Marta Garnelo, Ali Eslami, Dan Rosenbaum, Oriol Vinyals, and Yee Whye Teh. 2019. Attentive Neural Processes. In _International Conference on Learning Representations (ICLR)_ . 

- [17] Diederik Kingma and Jimmy Ba. 2015. Adam: A Method for Stochastic Optimization. https://arxiv.org/pdf/1412.6980.pdf 

- [18] Diederik P Kingma and Max Welling. 2014. Auto-encoding variational bayes. In _International Conference on Learning Representations (ICLR)_ . 

- [19] Shiyang Li, Xiaoyong Jin, Yao Xuan, Xiyou Zhou, Wenhu Chen, Yu-Xiang Wang, and Xifeng Yan. 2019. Enhancing the Locality and Breaking the Memory Bottleneck of Transformer on Time Series Forecasting. In _Advances in Neural Information Processing Systems (NeurIPS)_ . 

- [20] Duc-Hung Luong, Huu-Trung Thieu, Abdelkader Outtagarts, and Yacine GhamriDoudane. 2018. Predictive Autoscaling Orchestration for Cloud-native Telecom Microservices. In _IEEE 5G World Forum (5GWF)_ . 153–158. 

- [21] Microsoft. 2020. Azure auto scaling documentation. https://azure.microsoft. com/en-us/features/autoscale/ 

- [22] Haoran Qiu, Subho S. Banerjee, Saurabh Jha, Zbigniew T. Kalbarczyk, and Ravishankar K. Iyer. 2020. _FIRM: An Intelligent Fine-Grained Resource Management Framework for SLO-Oriented Microservices_ . 

- [23] David Salinas, Valentin Flunkert, and Jan Gasthaus. 2019. DeepAR: Probabilistic Forecasting with Autoregressive Recurrent Networks. In _Advances in Neural Information Processing Systems_ . 

- [24] Ashraf A Shahin. 2016. Automatic Cloud Resource Scaling Algorithm based on Long Short-Term Memory Recurrent Neural Network. _International Journal of Advanced Computer Science and Applications_ 7, 12 (2016). 

- [25] Gautam Singh, Jaesik Yoon, Youngsung Son, and Sungjin Ahn. 2019. Sequential Neural Processes. In _Advances in Neural Information Processing Systems (NeurIPS)_ . 

- [26] Richard S Sutton, Andrew G Barto, et al. 1998. _Introduction to reinforcement learning_ . Vol. 135. MIT press Cambridge. 

- [27] Hado Van Hasselt, Arthur Guez, and David Silver. 2016. Deep reinforcement learning with double q-learning. In _Proceedings of the AAAI conference on artificial intelligence_ . 

- [28] Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N Gomez, Łukasz Kaiser, and Illia Polosukhin. 2017. Attention is all you need. In _Advances in neural information processing systems (NIPS)_ . 5998–6008. 

- [29] Shubo Zhang, Tianyang Wu, Maolin Pan, Chaomeng Zhang, and Yang Yu. 2020. A- SARSA: A Predictive Container Auto-Scaling Algorithm Based on Reinforcement Learning. In _IEEE International Conference on Web Services (ICWS)_ . 

- [30] Haoyi Zhou, Shanghang Zhang, Jieqi Peng, Shuai Zhang, Jianxin Li, Hui Xiong, and Wancai Zhang. 2021. Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting. In _The Thirty-Fifth AAAI Conference on Artificial Intelligence_ , Vol. 35. 11106–11115. 

KDD ’22, August 14–18, 2022, Washington, DC, USA 

Xue and Qu, et al. 

## **A APPENDIX** 

## **A.1 Background on Autoscaling** 

_A.1.1 Why Autoscaling._ Autoscaling is a cloud computing feature that enables operators to scale cloud services such as server capacities or VMs up or down automatically, based on defined situations such as traffic or utilization levels. The overall benefit of autoscaling is that it eliminates the need to respond manually in real-time to traffic spikes that merit new resources and instances by automatically changing the active number of VMs. 



### **Figure 6: An illustration of autoscaling, adopted from Internet.** 

_A.1.2 Why Predictive Autoscaling._ Predictive scaling uses certain models to analyze each resource’s historical workload and regularly forecasts the future load. Using the forecast, predictive scaling generates scheduled scaling actions to make sure that the resource capacity is available **before the application needs it** , therefore yielding better scaling timeliness [29]. In industrial practises [5, 21], predictive scaling works to maintain the utilization at the target value specified by the scaling strategy. 

- Message Push (MsgPush): the traffic of message push throughout the system. 

- External Application (EA): the traffic of access from external applications. 

- Database Access (DA): the traffic of database access. 

- Write Buffer (WB): the traffic of write buffers throughout the system. 

- Page View (PV): the traffic caused by user page view. 

The data does not contain any Personal Identifiable Information (PII), is desensitized, encrypted, is only used for academic research, it does not represent any real business situation. Adequate data protection was carried out during the experiment to prevent the risk of data copy leakage, and the data set was destroyed after the experiment. 

_A.2.2 Implementation details._ We implemented our approach based on Python 3.6.3 and Tensorflow 1.13.1. The size of all hidden states in DAPM are set to 64, i.e., _𝑚_ = _𝑑_ = _𝑑𝑄_ = _𝑑𝐾_ = _𝑑𝑣_ = 64 while the number of heads of the attention module is set to 2. The ANP module uses the hidden size 64 in the encoder and the decoder. The main part of ANP is borrowed from open-source code of DeepMind _https://github.com/deepmind/neural-processes_ . The RL module uses the discount factor _𝛾_ = 0 _._ 95 and hidden size 64 in the policy network. Durign training, we set batch size 128, use early stopping and weight decay for regularization and apply Adam [17] to optimize the model. A sample code can be found at _https://github.com /iLevyFan/meta_rl_scaling._ 

_A.2.3 Environment. All experiments run on a Linux server (Ubuntu 16.04) with Intel(R) Xeon(R) Silver 4214 2.20GHz CPU, 16GB memory, with a V100 GPU._ 

_A.1.3 The Cloud system._ Our work is performed in the context of a large-scale production cloud service system from a worldleading online mobile payment provider. The system consists of over 3000 services/applications running on over 1 million VMs while the workload typically has millions of access request per minute. The payment service requires 7 × 24 hours availability and the SLO in terms of the success rate for accesses every second is required to be higher than 99 _._ 9995%. In this paper, we primarily focus on autoscaling, to ensure that this large-scale system meets its stringent SLOs. 

## **A.2 Experiment Details** 

In this section, we present the details of the experiment deferred from the main text. 

_A.2.1 Dataset._ The workload is defined as a 7-dimensional vector, each of the element corresponds to a subtype of the traffic, which is described below: 

- Remote Procedure Calls (RPC): the traffic of external access through the system. 

- Message Subscription (MsgSub): the traffic of message subscription throughout the system. 

