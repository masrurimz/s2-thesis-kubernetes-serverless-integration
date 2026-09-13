---
# --- bibliographic record ---
entry_type: inproceedings
title: "HyPA: Hybrid Horizontal Pod Autoscaling with Automated Model Updates"
authors:
  - "Kaan Aykurt"
  - "Răzvan-Mihai Ursu"
  - "Johannes Zerwas"
  - "Patrick Krämer"
  - "Navidreza Asadi"
  - "Leon Wong"
  - "Wolfgang Kellerer"
year: 2023
venue: "2023 IEEE Conference on Network Function Virtualization and Software Defined Networks (NFV-SDN)"
volume: ""
issue: ""
pages: "8-14"
publisher: "IEEE"
doi: "10.1109/NFV-SDN59219.2023.10329742"
arxiv: ""
url: "https://doi.org/10.1109/NFV-SDN59219.2023.10329742"

# --- archive record ---
source_pdf: hypa-hybrid-hpa-automated-model-updates-2023.pdf
source_sha256: 2b8ecf07efabcc5f85edc9d477627c90d58df0c1dfb2693c93dec1a9e00f06af
pdf_pages: 7
converted: 2026-09-13
record_source: crossref
key_insight: "Blends proactive+reactive; auto-updates model on distributional shift; asymmetric scale-up/down recommended for dynamic workloads"
first_page: "HYPA: Hybrid Horizontal Pod Autoscaling with Automated Model Updates Kaan Aykurt∗, R˘azvan-Mihai Ursu∗, Johannes Zerwas∗, Patrick Krämer∗, Navidreza Asadi∗, Leon Wong† and Wolfgang Kellerer∗ ∗Technica"
---
# HYPA: Hybrid Horizontal Pod Autoscaling with Automated Model Updates 

Kaan Aykurt<sup>_∗_</sup> , R˘azvan-Mihai Ursu<sup>_∗_</sup> , Johannes Zerwas<sup>_∗_</sup> , Patrick Krämer<sup>_∗_</sup> , Navidreza Asadi<sup>_∗_</sup> , Leon Wong<sup>_†_</sup> and Wolfgang Kellerer<sup>_∗_</sup> 

_∗_ Technical University of Munich, _†_ Rakuten Mobile Inc. 

**_Abstract_ —Due to changing demand patterns driven by technological advancements and the rise of new applications and services, the provisioning of heterogeneous workloads is a crucial component of the resource allocation problem. Traditional resource allocation strategies such as reactive autoscaling or prediction-based proactive solutions, fail to meet the desired performance goals when the underlying demand arrival pattern changes.** 

**In this paper, we present HYPA, which combines reactive and proactive components to autoscale pods in a Kubernetes environment. In contrast to previous approaches of hybrid autoscaling, HYPA automatically reacts to drifts in the request arrival pattern. Specifically, it updates the model of its proactive component when the prediction performance decreases. The evaluation in a simulation on a variety of real-world traces, spanning multiple days, demonstrates that HYPA improves upon existing purely reactive and purely proactive horizontal pod autoscalers.** 

**_Index Terms_ —Kubernetes, horizontal pod autoscaling, demand forecasting** 

## I. INTRODUCTION 

In today’s rapidly evolving world of digitalization, the provisioning of containerized workloads is a crucial aspect of modern network management strategies. Examples of such workloads are web applications and mobile networks which become more modularized as white-box concepts like OpenRAN are adopted [1]. Kubernetes (k8s) is one of the most popular frameworks for managing and scaling containerized applications and it is being adopted by many Telco Providers where network functions are containerized. One of the key features of k8s is that it offers to tackle the challenges of scalability with its Horizontal Pod Autoscaler (HPA). 

Traditional resource provisioning methods require expertise and human intervention in the decision-making process to allocate the required resources. This leads to a tedious and error-prone process, where a wrong estimation in the capacity requirements can lead to under or over-provisioning of resources [2]. In addition to application performance issues caused by under-provisioning, or waste of resources created by over-provisioning, rapid fluctuations in demand patterns render manual resource allocation methods infeasible and impractical. To this end, the k8s HPA aims to autonomously scale the number of running pods, i.e. autoscale, in response to critical performance metrics such as CPU utilization, memory utilization, or the Request Completion Time (RCT). 

State-of-the-art autoscaling methods from the research community consider reactive, proactive, and hybrid autoscaling [3]. 

Reactive autoscalers take action when the performance metrics exceed a pre-defined threshold. Hence, their reaction is delayed or even too late to keep the performance metrics within the desired range. Avoiding this situation usually results in over-provisioning resources to have some slack resources (and lead time) to deploy additional resources when needed. Moreover, frequently collecting critical performance metrics from large-scale distributed systems introduces challenges to system design. 

With the advances in data-driven modeling and forecasting methods, a proactive approach to HPA emerged [4]–[6]. The HPA predicts the incoming demand for a certain time horizon and scales out the resources accordingly. While this allows the system to prepare for future load variations, the performance of such an approach strictly depends on the quality of the forecast [6], [7]. In addition, user and application behavior is subject to (sudden) changes that may only be for a short duration or more long term, e.g., when an update of the application is deployed. In general, short-term effects appear in the form of bursts. For instance, for an online food delivery website, the incoming request numbers increase during lunch or dinner times. On the other hand, long-term effects reflect distributional shifts in the data where an increase or a decrease in the mean occurs due to seasonal effects. An example of such effects can be the increased number of requests for footballrelated web pages during periods of the World Cup. These changes reflect in the request arrival patterns as bursts or socalled distributional shifts for more persistent changes, and in turn may lead to wrong forecasts and ultimately, reduced performance. 

In order to respond to changing user behaviors and the resulting deficiencies of proactive HPAs, _hybrid_ HPAs were introduced [3]. Existing designs of such systems feature a combination of proactive and reactive approaches. Specifically, they rely on scaling decisions from the proactive component as long as the forecast quality is high and fall back to the reactive component if needed. A specific example is Chameleon [7]. Chameleon features two proactive components that use different prediction models and comes with a sophisticated mechanism to handle conflicting scheduling decisions. It periodically evaluates the forecast quality and falls back to a reactive approach when the forecast quality is below a given threshold. While this approach works well for shortperiod bursts, it lacks an integrated approach to update the forecasting models in case of long-term distributional shifts 

such as observed during the COVID19 pandemic [8]. 

In this paper, we propose HYPA, a hybrid HPA that automatically reacts to distributional shifts in the demand patterns. Similar to other systems, HYPA combines a proactive and a reactive HPA component. In normal operation mode, it monitors and checks the proactive component’s performance. In case of performance degradation, HYPA enters into burst mode and applies reactive autoscaling in addition to the proactive scaling. If it continuously detects bursts for a longer time period, HYPA considers the model of the proactive component to be outdated and starts data collection for the update of the model. We evaluate HYPA in simulations on traces from production systems in a variety of settings, comparing it to purely proactive and purely reactive HPAs. HYPA outperforms the baselines in all these situations or performs at least as well while putting more focus on our primary metric, the RCT. 



<!-- Start of picture text -->
Node 1<br>Meta  RR Network Node N<br>LB<br>Request Metrics<br>Monitor Server<br>Proactive Reactive<br><!-- End of picture text -->

Fig. 1: Cluster setup for the Change Point Detection use-case. 

## II. RELATED WORK 

The performance of an orchestration tool depends on its ability to use the resources efficiently with respect to changes in application characteristics, i.e., it should scale the resources provisioned to their applications in a smart manner. Hence, a considerable part of the literature focuses on designing autoscalers. A survey by Qu [3] elaborates on various methodologies to scale the resources of web applications. Mainly, the design of autoscalers is divided into three categories: reactive, proactive, and hybrid autoscalers. 

Reactive autoscalers update the autoscaling decision when a pre-defined reaction threshold is reached. The default k8s HPA implements this as a control loop that queries the resource utilization and by comparing it with a pre-defined target utilization value, it reactively scales pods. Although this approach manages to scale after a certain threshold is reached, it has no ability to anticipate changes in workload patterns in the future. Hence, it can scale only after the control loop reacts to an increase in resource utilization. 

Proactive autoscalers predict the required resource consumption in the future in order to scale by avoiding the need for reactive autoscaling. Among this category, the authors of [5] propose an LSTM based-model to scale based on the predicted workload. The authors of [4] present AutoScale– as a holistic approach that incorporates Load Balancing of requests and reactive autoscaling and it scales servers according to the current request arrival rate. Gandhi et al. [9] present an Extended Kalman Filter based method to estimate unobservable parameters in a three-tier web application, and use those estimates for autoscaling decisions. Luong et al. [10] proposes to combine a long-term and a short-term prediction to scale the number of application instances. The authors of [11] propose an algorithm to detect bursts and act proactively upon the detection of bursts. However, these methods do not include a reactive component. Therefore, in case of poor prediction performance, the autoscaler’s performance degrades significantly. To overcome this problem, state-of-the-art in literature focuses on hybrid autoscalers. 

Hybrid autoscalers combine reactive and proactive components for autoscaling decisions. The authors of [12] propose a hybrid controller, where the reactive component is responsible for scale-out decisions and the proactive component accounts for scale-in decisions. Overall, they show that their autoscaler outperforms purely reactive-based autoscalers. Most recently, Chameleon [7] and Chamulteon [13] frameworks combine proactive scaling mechanisms with reactive fallback. In their paper, the proactive components use two time series models to predict the future request arrival rate. The reactive component makes scaling decisions based on the current request arrival rate and the estimated application resource consumption profile. Further, the controller allows the integration of queuing models into the decision-making process, enabling the controller to use structural application knowledge. However, they do not consider updating the model parameters during runtime, i.e. they rely on a pre-trained model without considering distributional shifts in request patterns. 

To the best of our knowledge, the literature lacks a comprehensive and lightweight hybrid autoscaler that automatically updates its proactive component in case of distributional shifts, and falls back to reactive autoscaling when the prediction performance of the proactive component decreases. To close this gap, we present HYPA. 

## III. SCENARIO DESCRIPTION 

Figure 1 shows the envisioned scenario. We consider a deployment with 10s of pods and multiple stages of load balancers as considered in prior work [14], [15]. A meta load balancer distributes incoming requests across the second stage of load balancers using round robin. In the second stage, load balancers distribute the requests across the pods of the service(s). They might use more advanced load balancing techniques, e.g., based on the load of the pods. Two sets of monitoring data are collected from the system. The first set consists of platform metrics such as CPU utilization _u_ ( _t_ ), memory utilization, disk I/O, and network utilization. The Metrics Server component available in k8s collects these 



<!-- Start of picture text -->
100<br>75<br>50<br>25<br>0<br>01.2019 05.2019 09.2019 01.2020<br>Time<br> (in thousands)<br>Requests per Second<br><!-- End of picture text -->

Fig. 2: Distributional Shift: The mean of the dataset faces a shift in the indicated time period. Hence, a performant proactive component needs to account for structural changes in the request patterns. 

metrics from all nodes in the cluster. The reactive autoscaler component uses platform metrics for its scaling decisions. The second set of monitoring data is request-level data such as the number of arrived requests in a time interval _nreq_ ( _t_ ). A dedicated request monitor collects this data from (a subset of) the load balancers. The proactive component uses the requestlevel data to evaluate the quality of its forecasting model and to perform burst detection. We consider _horizontal_ autoscaling, _vertical_ scaling is out-of-scope for this work. 

## _A. Workload Characterisation_ 

The existence of distributional shifts of demand patterns has been observed in prior work, e.g., [8]. To provide another example, we analyze the request arrivals of the BibSonomy system [16]. We investigate the request arrivals to the cluster in fixed time intervals _tiar_ . Specifically, requests are binned and counted with _tiar_ = 1 min. Our analysis shows that the number of requests that arrive every _tiar_ in the BibSonomy traces form a seasonal time series. Hence, the time series expresses regular and predictable changes that occur at specific times, i.e., after removing seasonal effects, the time series is stationary. 

Moreover, our analysis also considers the time series of request arrivals may express random bursts in demand. Given the fact that the time series is stationary given the seasonality, we define a burst as a finite period of time during which the number of arrived requests is larger (or smaller) than an upper (or lower) bound on the predicted request arrivals. 

Figure 2 shows the number of requests per second in the year 2019 for the BibSonomy dataset. The plot shows that in the marked period, the mean shifts for a period of 1 _._ 5 months, and then returns to the old mean. This is an example of possible abrupt changes in the request patterns. Motivated by this, we propose a hybrid autoscaling scheme consisting of a proactive and a reactive component, where the proactive component continuously predicts the required number of pods in the future and updates the model parameters in case of a reduction in prediction quality and falls back to reactive autoscaling in such cases. 

## IV. HYBRID AUTOSCALING WITH HYPA 

HYPA combines the decisions of two autoscaling components: proactive and reactive. The two components both estimate the number of desired replicas in the cluster, _rp_ ( _t_ ) for the proactive, and _rr_ ( _t_ ) for the reactive component. The proactive component uses a model of the demand pattern to forecast the request arrival rate in the next forecast period, whereas the reactive component reacts to the utilization of the pods. Both scale the number of replicas to reach a target utilization _ut_ on average. The currently configured number of replicas is _rc_ ( _t_ ). The control loop estimates the number of replicas in the next iteration as _rc_ ( _t_ ) = max( _rr_ ( _t_ ) _, rp_ ( _t_ )). This policy prevents pre-mature scale-in decisions. 

Each component of the autoscaler operates in its own synchronization period _tr_ (reactive) and _tp_ (proactive). During normal operation, we assume that _tr > tp_ , i.e., the proactive component operates more often than the reactive component. The reason for this lies in the cost to obtain necessary monitoring data from the cluster nodes. Obtaining all platform metrics from a large number of nodes is much more costly than collecting request data from a small number of load balancers. One goal is the reduction of this overhead by relying on the predictive model in the proactive component. Moreover, a dominant proactive component allows one to follow the demand pattern more closely and increase resource efficiency. The difference _tr − tp_ is such, that the reactive component has enough time to react to demand peaks, i.e., bursts. The difference must be chosen with respect to the provisioning time of new replicas, the monitoring frequency of request arrivals, and an expectation of the speed with which bursts occur, i.e., how fast demand increases during bursts. 

## _A. HPA Components_ 

The following describes the scaling logic of the two HPA components of HYPA more in detail. 

_1) Reactive:_ The reactive component builds on the default HPA available in k8s. It uses the CPU utilization of the application pods to determine the number of needed replicas. Specifically, it calculates the average utilization over all pods and compares it against the given target value _ut_ : 



_2) Proactive:_ The proactive component uses data-driven models to forecast the expected number of requests in each category for the next time slot. Based on the estimated number of requests and a model of the work that each request causes, the so-called application profile [17], the proactive component estimates the number of replicas in the system: 



Here, E[ _u_ ( _t_ + 1)] uses the forecast request arrivals and the application profile to estimate the expected utilization of the cluster in the next time slot. 



<!-- Start of picture text -->
 within<br>bound<br>Normal<br>Mode<br> outside bound condition to end<br>data collection*<br> within bound<br>Burst Panic<br>Mode Mode<br> outside bound<br>for more than  3 hours<br> outside  in the last 6 hours not enough<br>bound data<br><!-- End of picture text -->

Fig. 3: Hybrid HPA State Machine. HYPA consists of 3 states. Depending on different conditions specified in the figure, the states, and hence the operation mode of the HPA changes. 

The proactive component works on a minute granularity (to account for the reaction times of the k8s cluster, e.g., for pod scheduling and application initialization). Specifically, the proactive component predicts the request arrival rate per second averaged over one-minute time windows. Designing the forecasting model for the resulting time series is an engineering task on its own. We found that for the used trace from the BibSonomy production system, a rather simple model consisting of a fixed offset and a seasonal component suffices. Moreover, we identified a strong diurnal and weekly pattern. Therefore, the seasonal component _s_ ( _x_ ) is given by a look-up table with a single value for every minute of a week (10 080 values in total). As a result, we obtain 



where _mow_ ( _._ ) returns the minute of the week for the given timestamp _t_ (in minutes). We obtain these values by averaging each time slot over multiple weeks. Besides the mean value, the model also provides the standard deviation _std_ ( _._ ) as a measure of prediction confidence. 

## _B. Operation Modes_ 

Figure 3 overviews the state machine of HYPA and the different operation modes. When it detects deviations of the forecast from the observed values, HYPA first enters the socalled “Burst mode”. If it is frequently in the Burst mode, HYPA transitions to the Panic mode. Here, it collects new data and updates the model. The modes and the transition conditions are described in more detail in the following. 

## _C. Burst Detection & Burst Mode_ 

The autoscaler detects a burst at a time slot based on the predicted number of requests _n_ ˜ _req_ ( _t_ ) ( _a_ ( _t_ ) _·_ 60 s), and the actual observed number of requests in that time slot _nreq_ ( _t_ ). Currently, the burst detection focuses on positive bursts, i.e., time intervals in which the actual demand _exceeds_ 

the predicted demand, since such bursts have an impact on _nreq_ <u>(</u> _t_ <u>)</u> the RCT. Specifically, HYPA detects a burst if 60 _s ∈_ [ _a_ ( _t_ ) _− std_ ( _t_ ) _, a_ ( _t_ ) + _std_ ( _t_ )]. 

During a burst, _rr_ ( _t_ ) _> rp_ ( _t_ ) and the estimate of the reactive component is chosen. Once the burst is over, _rr_ ( _t_ ) _≤ rp_ ( _t_ ), and the excessive number of replicas is scaled-in. Moreover, when the autoscaler detects a burst, the cluster changes the configuration of the reactive component. HYPA enters the socalled “Burst mode”. Specifically, the synchronization period _tr_ is reduced to burst synchronization period _t_<sup>_′_</sup> _r_<sup>.Finally,the</sup> collection of the platform metrics and reactive components is triggered. In the case of a burst, the reactive component alone is responsible for choosing the adequate number of replicas, i.e., _rc_ ( _t_ + 1) = _rr_ ( _t_ ) due to the definition of bursts. Thus, the cluster actively changes the configuration of the reactive component. Since obtaining fresh measurements and the provisioning of new instances takes time, a scale-out threshold must be set such that the reactive component reacts when the cluster is not yet over-utilized. 

## _D. Change points detection & Panic Mode_ 

Next to expected unpredictable bursts, the cluster further monitors the accuracy of the forecasting model, specifically, the cluster performs a change point analysis. At a change point, the predictions of the forecasting model deviate significantly from the actually measured values. The difference to a burst is that for a burst, the predictions are off for a finite (short) duration. After some time, the burst is over and the model is accurate again. In case of a change point, the predictions of the models are inaccurate for at least _icp_ prediction intervals within an observed time window _wcp_ : 



**1** ( _._ ) is an indicator function that = 1 if the condition evaluates to true. 

For example, the total demand level could decrease and the forecast would always be too high, resulting in increased costs due to over-provisioning. Similarly, the estimates could be too low, resulting in Service-Level Agreement (SLA) violations since the reactive component does not have enough time to scale-out. 

If the cluster detects a change point, the system enters “Panic mode” and starts data collection in order to update the model of the demand. This approach reduces the overhead of constant data collection. Moreover, for the whole duration of the data collection, the HPA operation of the burst mode is enforced. For data collection, HYPA records the observed arrival rates and fits the updated model when a sufficient number of samples was collected. 

In principle, the duration of the panic mode is a trade-off between model accuracy and the time until the new model is available. It depends on the details of the used model and the observed data. It can either be fixed or determined 



<!-- Start of picture text -->
Measured Estimated<br>30<br>20<br>10<br>0<br> 19.06   20.06   20.06   20.06   20.06   21.06   21.06<br>18:00 00:00 06:00 12:00 18:00 00:00 06:00<br>Arrival rate [1/s]<br><!-- End of picture text -->

Fig. 4: Measured and estimated arrival rate over time. Traces are taken from simulation data with 24-hour data collection period and 70% utilization threshold. Background shades indicate burst modes. After spending 3 hours in the burst mode, the period marked with red indicates the panic mode. After data collection ends, the estimates are updated. 

dynamically, e.g., based on the performance or convergence criteria of the model. 

In this paper, we explore the fixed approaches where data collection (and Panic mode) stop after a given time duration. 

When the new model is available, HYPA leaves the Panic mode and resumes normal operation. The parameters of the reactive component are reverted to their normal values and the proactive component dominates the scaling of the replicas. 

## V. EVALUATION 

In this section, we evaluate HYPA and compare it against a range of baselines. All presented results are obtained from the discrete event-based simulator presented in [17]. It combines data-driven models as well as white-box re-implementations of k8s’ components. 

## _A. Settings_ 

_1) Simulated Cluster:_ The cluster contains a single node with 64 CPU cores. Each pod occupies one CPU core and the simulator assumes resource limits per pod with isolated CPUs so that there is no interference between the pods on the CPU. Thus, a maximum of 64 pods can be allocated.<sup>1</sup> Requests arrive at a load balancer that distributes them across the available pods according to a round-robin policy. Request processing on the pods happens in a first-in-first-out manner for a given duration. The simulator resembles the metric collection pipeline from k8s and the collected data is available to all considered HPAs. 

_2) Metrics:_ HYPA trades off different objectives which serve as metrics for the comparison: 

- **Request completion time (RCT):** RCT is defined as the time difference between the completion and the arrival time of the request in the system. Operators are usually interested in the 99th (or higher) percentiles of the RCT. 

- **Total pod seconds:** This metric directly relates to the cost of the deployment and is often used for billing in managed k8s environments<sup>2</sup> . We consider the integral of 

> 1Note that due to the strict isolation between pods, no significant change in the observed results is expected when evaluating in a multi-node cluster or increased number of CPU cores per pod. 

> 2For instance, https://cloud.google.com/kubernetes-engine/pricing. 

the number of CPUs allocated for pods over time. Since in our case, each pod requests exactly one CPU, we refer to it as the “total pod seconds”. 

_3) Algorithms:_ We compare three variants of HPAs. The candidates are described in the following: 

- **HYPA (H)** combines proactive and reactive component. The proactive component runs every _tp_ = 60s. The reactive one runs every _tr_ = 180s and every _t_<sup>_′_</sup> _r_<sup>=15s</sup> in Burst mode. The target utilization is the same in both modes. We select these values to ensure the best RCT in a variety of scenarios, and we use a fixed **(F)** data collection duration of 24 hours. 

- **Proactive (P)** uses only the proactive component as described in Section IV-A2. It synchronizes every _tp_ = 60s. 

- **Reactive (R)** uses only the reactive component following Equation 1. We vary the synchronization period _tr_ among 60s, 180s. 

_4) Application and request pattern:_ We compare the algorithms on request arrivals from four continuous time periods from the Bibsonomy trace. The request arrivals follow the trace, i.e., use the provided timestamps. The inputs are shown in Figure 5. The duration of the periods varies between 48 and 120h and each of the selected periods has distinct characteristics such as high bursts or distributional shifts/drifts. 

The evaluation considers a single request type with a fixed processing time. As the average arrival rate of the BibSonomy trace is low ( _≈_ 4 _−_ 8 requests per second), we use a processing time of 500ms to induce a substantial load on the system. 

## _B. Temporal analysis of_ HYPA 

Figure 4 shows the measured (dark blue line) and estimated (dark green line) arrival rate over a time over a period of 2 days for illustrating the behavior of HYPA with respect to changes in the demand patterns. The estimator’s certainty bounds are shown with the green shaded area. Burst periods are also indicated with the shades in the background, and the period highlighted by the red bar at the top illustrates the Panic mode. HYPA continuously checks the performance of the proactive component by checking if the estimated _nreq_ ( _t_ ) is within the pre-defined bounds (green shaded area). At the 



<!-- Start of picture text -->
30 20<br>20<br>8<br>20 15<br>6<br>10<br>10<br>10<br>4<br>5<br>0 24 48 72 0 24 48 72 0 16 32 48 0 40 80 120<br>Time [h] Time [h] Time [h] Time [h]<br>(a) Period 1 (b) Period 2 (c) Period 3 (d) Period 4<br>Req/s Req/s Req/s Req/s<br><!-- End of picture text -->

Fig. 5: Request arrival rate over time for the four considered input traces. All traces contain some deviation from a regular periodic (diurnal) pattern, e.g., a burst or a (temporary) shift of the mean value. 



<!-- Start of picture text -->
R-60s P-60s ut = 0.5 ut = 0.7<br>R-180s H-F-24h ut = 0.6 ut = 0.8<br>10 3 10 4<br>10 4 10 4<br>10 2 10 3<br>10 2<br>10 2 10 2<br>10 1<br>1.0 1.2 1.4 1.6 1.0 1.5 2.0 1.2 1.4 1.6 1.8 2 3<br>Total Pod Seconds [ 10 6 ] Total Pod Seconds [ 10 6 ] Total Pod Seconds [ 10 6 ] Total Pod Seconds [ 10 6 ]<br>(a) Period 1 (b) Period 2 (c) Period 3 (d) Period 4<br>99%-ile RCT [s] 99%-ile RCT [s] 99%-ile RCT [s] 99%-ile RCT [s]<br><!-- End of picture text -->

Fig. 6: Pareto-plot of the two performance metrics. Colors and line styles indicate the algorithm configurations. **R** stands for the _reactive_ , **P** stands for _proactive_ , **H** stands for _hybrid_ HPA, and **F-24h** indicates a fixed data collection duration of 24 hours, whereas the time periods indicate the time intervals between consecutive synchronization periods in the legend. The markers show the desired average pod utilization. For two of the shown traces, HYPA outperforms the purely reactive and proactive solutions. For the other two traces, HYPA performs similarly as a purely reactive solution but trades off the two metrics differently (the line is shifted). 

beginning of the plot, it can be seen that HYPA enters Burst mode. However, as the bursts are not persistent, it falls back to the normal operation mode. 

When HYPA observes a frequent occurrence of bursts within a 6-hour window, HYPA recognizes that the bursts are persistent, enters into Panic mode, and starts data collection. This is also outlined by the area designated with red color. For this example, data collection continues for 24 hours, and at the end of the period, the model is updated. After the model update, the estimations capture the distributional shift in the demand patterns. Overall, this illustrates how the HYPA behaves with respect to changes in request patterns. 

## _C. Comparison of HPAs_ 

We start by analyzing the two metrics for the different time periods on an aggregated level. Figure 6 shows Pareto plots of the two metrics and several values of _ut_ (different markers) and all the algorithms. By varying the utilization threshold _ut_ , we aim to find the best configuration per algorithm. For both metrics, smaller values are preferred, i.e., markers and curves closer to the lower left corner represent better performance. 

For Period 1 (Figure 6a), there are clear performance differences between classes of the algorithms. P-60s performs 

worst, followed by R-60s and all variants of HYPA, which overlap in this figure. Reducing _ut_ results in a lower 99%ile of the RCT but increases the total pod seconds. This is intuitive since scale-out happens earlier. In principle, R-60s can achieve similar RCTs like HYPA by using a lower _ut_ (e.g., the markers for R-60s( _ut_ = 0 _._ 7) and H-F-24h( _ut_ = 0 _._ 8) are at _≈_ 30s). However, this comes at the cost of increased total pod seconds ( _≈_ 10%). This behavior continues similarly for lower _ut_ . 

The observations for Period 2 (Figure 6b) are similar but the performance gap between R-60s and HYPA is smaller, i.e. the two variants behave almost the same. HYPA has a slightly smaller RCT but higher total pod seconds. Only for _ut_ = 0 _._ 5, R-60s is slightly better than HYPA. Considering the input pattern (Figure 5b), the arrival rate is almost constant except for two bursts towards the end of the trace. Here, HYPA enters the burst mode (but not panic mode) and essentially behaves like the reactive HPA. 

More differences are visible for Periods 3 and 4 (Figure 6c and 6d). For Period 3, we again observe that HYPA outperforms the pure variants. Here, there are the largest gains for HYPA. Lastly, for Period 4, the results are closer again. However, closer inspection reveals, that HYPA explores a 

different trade-off of RCT and total pod seconds compared to R-60s. The minimal achieved 99%-ile RCT is lower than for R-60s, however at significantly higher total pod seconds. 

In conclusion, HYPA performs similarly or better than pure reactive or proactive solutions on a variety of input patterns. In particular, in the presence of mean shifts in the arrival pattern, we observe that HYPA can adjust the trade-off between RCT and deployment cost to outperform the vanilla HPA approaches. 

## VI. CONCLUSION 

Efficient autoscaling is an important aspect of cluster operation. Proactive approaches that forecast the demand have shown benefits over purely reactive approaches that operate on system utilization. However, the former fall short in case of changes or shifts in the underlying demand patterns or distributions. Hybrid solutions have emerged to improve upon this. In this paper, we presented HYPA, a hybrid HPA that falls back to a reactive approach when the error between the predicted and the measured request arrivals increases. Moreover, if the mismatch persists for a longer time period, HYPA automatically updates its model to utilize again the proactive approach. Our evaluation demonstrates that HYPA outperforms previous approaches that are purely reactive or proactive. 

This paper presents only an initial assessment of HYPA. Improving demand forecasting models and evaluations of HYPA in a physical testbed environment are possible avenues for future work. 

## REFERENCES 

- [1] O-RAN Alliance, “O-RAN: Towards an Open and Smart RAN,” O-RAN Alliance, Alfter, Germany, Tech. Rep., October 2018. [Online]. Available: https://www.o-ran.org/resources 

   - [9] A. Gandhi, P. Dube, A. Karve, A. Kochut, and L. Zhang, “Adaptive, Model-driven Autoscaling for Cloud Applications,” in _11th International Conference on Autonomic Computing (ICAC 14)_ . Philadelphia, PA: USENIX Association, Jun. 2014, pp. 57–64. [Online]. Available: https://www.usenix.org/conference/icac14/technical-sessions/ presentation/gandhi 

   - [10] D.-H. LUONG, H.-T. THIEU, A. OUTTAGARTS, and Y. GHAMRIDOUDANE, “Predictive autoscaling orchestration for cloud-native telecom microservices,” in _2018 IEEE 5G World Forum (5GWF)_ , 2018, pp. 153–158. 

   - [11] M. Abdullah, W. Iqbal, J. L. Berral, J. Polo, and D. Carrera, “Burst-Aware Predictive Autoscaling for Containerized Microservices,” _IEEE Trans. Serv. Comput._ , vol. 15, no. 3, pp. 1448–1460, 2022. [Online]. Available: https://doi.org/10.1109/TSC.2020.2995937 

   - [12] A. Ali-Eldin, J. Tordsson, and E. Elmroth, “An adaptive hybrid elasticity controller for cloud infrastructures,” in _2012 IEEE Network Operations and Management Symposium, NOMS 2012, Maui, HI, USA, April 16-20, 2012_ , F. D. Turck, L. P. Gaspary, and D. Medhi, Eds. IEEE, 2012, pp. 204–212. [Online]. Available: https://doi.org/10.1109/NOMS.2012.6211900 

   - [13] A. Bauer, V. Lesch, L. Versluis, A. Ilyushkin, N. Herbst, and S. Kounev, “Chamulteon: Coordinated auto-scaling of micro-services,” in _2019 IEEE 39th International Conference on Distributed Computing Systems (ICDCS)_ . IEEE, 2019, pp. 2015–2025. 

   - [14] D. E. Eisenbud, C. Yi, C. Contavalli, C. Smith, R. Kononov, E. MannHielscher, A. Cilingiroglu, B. Cheyney, W. Shang, and J. D. Hosein, “Maglev: A fast and reliable software network load balancer,” in _Proceedings of the 13th Usenix Conference on Networked Systems Design and Implementation_ , ser. NSDI’16. USA: USENIX Association, 2016, p. 523–535. 

   - [15] T. Barbette, C. Tang, H. Yao, D. Kosti´c, G. Q. M. Jr., P. Papadimitratos, and M. Chiesa, “A High-Speed Load-Balancer design with guaranteed Per-Connection-Consistency,” in _17th USENIX Symposium on Networked Systems Design and Implementation (NSDI 20)_ . Santa Clara, CA: USENIX Association, Feb. 2020, pp. 667–683. [Online]. Available: https://www.usenix.org/conference/nsdi20/presentation/barbette 

   - [16] D. Benz, A. Hotho, R. Jäschke, B. Krause, F. Mitzlaff, C. Schmitz, and G. Stumme, “The social bookmark and publication management system BibSonomy,” _The VLDB Journal_ , vol. 19, no. 6, pp. 849–875, Dec. 2010. [Online]. Available: http://www.kde.cs.uni-kassel.de/pub/ pdf/benz2010social.pdf 

   - [17] J. Zerwas, P. Krämer, R.-M. Ursu, N. Asadi, P. Rodgers, L. Wong, and W. Kellerer, “Kapetánios: Automated kubernetes adaptation through a digital twin,” in _2022 13th International Conference on Network of the Future (NoF)_ , 2022, pp. 1–3. 

- [2] S. Singh and I. Chana, “Cloud resource provisioning: survey, status and future research directions,” _Knowledge and Information Systems_ , vol. 49, no. 3, pp. 1005–1069, Feb. 2016. [Online]. Available: https://doi.org/10.1007/s10115-016-0922-3 

- [3] C. Qu, R. N. Calheiros, and R. Buyya, “Auto-scaling web applications in clouds: A taxonomy and survey,” _ACM Comput. Surv._ , vol. 51, no. 4, jul 2018. [Online]. Available: https://doi.org/10.1145/3148149 

- [4] A. Gandhi, M. Harchol-Balter, R. Raghunathan, and M. A. Kozuch, “Autoscale: Dynamic, robust capacity management for multi-tier data centers,” _ACM Transactions on Computer Systems (TOCS)_ , vol. 30, no. 4, pp. 1–26, 2012. 

- [5] M. Imdoukh, I. Ahmad, and M. G. Alfailakawi, “Machine learningbased auto-scaling for containerized applications,” _Neural Computing and Applications_ , vol. 32, no. 13, pp. 9745–9760, Jul. 2020. [Online]. Available: https://doi.org/10.1007/s00521-019-04507-z 

- [6] L. Toka, G. Dobreff, B. Fodor, and B. Sonkoly, “Machine learning-based scaling management for kubernetes edge clusters,” _IEEE Transactions on Network and Service Management_ , vol. 18, no. 1, pp. 958–972, 2021. 

- [7] A. Bauer, N. Herbst, S. Spinner, A. Ali-Eldin, and S. Kounev, “Chameleon: A hybrid, proactive auto-scaling mechanism on a levelplaying field,” _IEEE Transactions on Parallel and Distributed Systems_ , vol. 30, no. 4, pp. 800–813, 2018. 

- [8] A. Feldmann, O. Gasser, F. Lichtblau, E. Pujol, I. Poese, C. Dietzel, D. Wagner, M. Wichtlhuber, J. Tapiador, N. Vallina-Rodriguez, O. Hohlfeld, and G. Smaragdakis, “The lockdown effect: Implications of the covid-19 pandemic on internet traffic,” in _Proceedings of the ACM Internet Measurement Conference_ , ser. IMC ’20. New York, NY, USA: Association for Computing Machinery, 2020, p. 1–18. [Online]. Available: https://doi.org/10.1145/3419394.3423658 

