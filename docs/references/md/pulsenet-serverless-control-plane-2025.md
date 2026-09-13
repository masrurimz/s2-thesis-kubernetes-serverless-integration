---
# --- bibliographic record ---
entry_type: misc
title: "Melding the Serverless Control Plane with the Conventional Cluster Manager for Speed and Resource Efficiency"
authors:
  - "Leonid Kondrashov"
  - "Lazar Cvetković"
  - "Hancheng Wang"
  - "Boxi Zhou"
  - "Dmitrii Ustiugov"
year: 2025
venue: "arXiv preprint"
volume: ""
issue: ""
pages: ""
publisher: ""
doi: ""
arxiv: "2505.24551"
url: "https://arxiv.org/abs/2505.24551"

# --- archive record ---
source_pdf: pulsenet-serverless-control-plane-2025.pdf
source_sha256: 5eefec9341a10bd4ab84d4549ec8ee56ee51c2af7cb7a6b9fa7ca1ff8739c87a
pdf_pages: 16
converted: 2026-09-13
record_source: arxiv
key_insight: "Dual-track: expedited (burst→serverless) + sustainable (baseline→VMs), 65-70% cost reduction"
first_page: "Melding the Serverless Control Plane with the Conventional Cluster Manager for Speed and Resource Efficiency Leonid Kondrashov NTU Singapore Lazar Cvetkovi´c ETH Zurich Hancheng Wang Nanjing Universit"
---
# **Melding the Serverless Control Plane with the Conventional Cluster Manager for Speed and Resource Efficiency** 

Leonid Kondrashov _NTU Singapore_ 

Lazar Cvetkovi´c Hancheng Wang Boxi Zhou _ETH Zurich Nanjing University NTU Singapore_ 

Dmitrii Ustiugov _NTU Singapore_ 

## **Abstract** 

Serverless platforms face a trade-off: conventional cluster managers like Kubernetes offer compatibility for colocating Function-as-a-Service (FaaS) and Backend-as-aService (BaaS) components of serverless applications, at the cost of high cold-start latency, whereas specialized FaaSonly systems like Dirigent achieve low latency by sacrificing compatibility, preventing integrated management and optimization. Our analysis reveals that FaaS traffic is bimodal: predictable, sustainable traffic consumes >98% of cluster resources, whereas sporadic, excessive bursts stress the control plane’s scaling latency, not its throughput. 

With these insights, we design _PulseNet_ , a serverless architecture that uses a dual-track control plane tailored to both traffic types. PulseNet’s standard track manages sustainable traffic with long-lived, full-featured Regular Instances under a conventional cluster manager, preserving compatibility for the majority of the workload. To handle excessive traffic, an expedited track bypasses the slow manager to rapidly create short-lived, disposable Emergency Instances, minimizing cold-start latency and resource waste from idle instances. This hybrid approach achieves 35% better performance than Dirigent, a FaaS-only system, on a production workload at the same cost and outperforms other Kubernetes-compatible systems by 1.5–3.5 _×_ , reducing the cost by up to 70%. 

## **1 Introduction** 

Serverless cloud applications today comprise stateless Function-as-a-Service (FaaS) and conventional stateful Backend-as-a-Service (BaaS) components, organized as DAG workflows. Developers deploy their business logic as functions while offloading the management of the underlying cloud infrastructure, for both FaaS and BaaS, entirely to the providers. The control plane is key to providing fast and timely scaling and resource efficiency when running these applications at the massive cloud scale, which can be achieved by careful placement and load balancing, and timely scaling. 

Unfortunately, despite the tight coupling of FaaS and BaaS components in cloud applications, their control planes lack coordination, often rendering co-design and optimization impractical. For example, AWS Lambda [26] and Dirigent [32] manage their own fleets of bare-metal nodes allocated exclusively for FaaS. Other works focus on designs for specific BaaS services [49, 55] used by serverless applications, such as storage and database. In contrast, a decade ago, the success of Google’s Borg cluster manager demonstrated the benefits of running various services under a single control plane, achieving better cluster utilization and reducing operational costs without compromising performance [70,75]. Since then, practitioners have designed many open-source production systems [6, 10, 17, 18] running atop Borg’s successor, Kubernetes [13], which features numerous optimizations and highly-optimized technologies (e.g., intelligent placement, load balancing, networking, and authentication) and can colocate any services in the same cluster. However, state-of-the-art prior works [32, 62, 68] have concluded that a heavyweight control plane, as in Kubernetes, is too slow to keep up with highly dynamic FaaS workloads [67], calling for a full revamp of technologies already available for BaaS services running under a conventional control plane. 

In contrast, we show that a conventional cluster manager’s control plane, although heavyweight, can be seamlessly extended to provide sufficient scaling speed for FaaS workloads, thereby unlocking efficient co-location of FaaS and BaaS systems without compromising performance. Using production Azure Functions traces [67], we present a thorough analysis of the FaaS workload and performance characteristics in systems representative of leading commercial offerings [8, 25] and open-source systems [12,28]. First, we identify two kinds of invocation traffic, _sustainable_ and _excessive_ , showing that the former utilizes _>_ 98% of the cluster CPU resources while the latter stresses the control plane but consumes _<_ 2% of the cluster resources. Second, we demonstrate that control planes suffer from long instance-creation delays due to frequent interaction with the centralized cluster manager, e.g., when allocating cluster resources and IP addresses, and setting up 

1 

|System|React.<br>time|CM<br>Perf.|Predict.<br>Comp.|FaaS-<br>BaaS<br>coloc.|Resour.<br>Waste|
|---|---|---|---|---|---|
|AWS Lambda(sync)|✓|✓|✗|✗|High|
|OpenWhisk(sync)|✓|✗|✗|✓|High|
|Knative(async)|✗|✗|✓|✓|Moder.|
|Dirigent[32]|✗|✓|✓|✗|Low|
|PulseNet(ours)|✓|✓|✓|✓|Low|



Table 1: Comparison of the existing approaches and the proposed PulseNet in reaction time (React. time), cluster manager performance (CM Perf.), compatibility with predicting models (Predict. Comp.), ability to colocate FaaS and BaaS (FaaS-BaaS coloc.), and Resource Waste. 

network routes. However, we show that these systems’ control planes can be tuned to deliver throughput sufficient for a dynamic large-scale FaaS deployment, in contrast to the prior work [32] that has optimized for control-plane performance. Finally, we identify that current systems waste 70-87% of memory and 9-20% of CPU resources due to prolonged idle instance lifetime and high instance churn, respectively. 

Based on the obtained insights, we introduce _PulseNet_ ,<sup>1</sup> a serverless system designed to achieve high performance and low cost while maintaining compatibility with conventional cluster managers, such as Kubernetes [13]. _PulseNet_ employs a novel dual-track control plane comprising _standard_ and _expedited_ tracks. The standard track is based on Knative atop Kubernetes, the industry-standard serverless cluster manager, managing long-lived, full-featured _Regular Instances_ to handle the sustainable traffic. This track adjusts the number of instances off the critical path in cooperation with the underlying cluster manager, thereby preserving full compatibility with its rich feature set. Concurrently, the expedited track serves the excessive traffic bursts by rapidly creating _Emergency Instances_ that completely bypass the cluster manager and its bookkeeping. This track communicates directly with a nodelocal agent that spawns single-use instances, which it shuts down after processing a single invocation, minimizing idle instance lifetime and associated resource waste. These disposable instances are fully compatible with FaaS workloads, albeit they forego the conventional cluster manager’s features for long-running instances, such as readiness and liveliness probes, and advanced networking capabilities, which they do not need, in exchange for much faster instance creation. 

We prototype PulseNet in vHive [73] as a seamless extension of the Knative control plane running atop unchanged Kubernetes. Evaluation with a production workload shows that _PulseNet_ provides 35% performance improvement while maintaining cost parity with Dirigent [32]. Additionally, when compared with other Kubernetes-compatible alternatives, _PulseNet_ delivers 1.5-3.5 _×_ better performance than the systems with a synchronous control plane, as in AWS Lambda [22], while reducing the operational cost by 8-70%; 

> 1We will release the code, traces, and toolchain after publication. 



<!-- Start of picture text -->
Knative with an asynch. contr. plane (Kn)<br>100<br>50<br>0<br>Knative modification with a synch. contr. plane (Kn-Sync)<br>100<br>50<br>0<br>PulseNet<br>100 Request concurrency<br>#regular instances<br>#emergency instances<br>50 #instances<br>0<br>0 50 100 150 200 250 300<br>Time, seconds<br>Number of instances, invocations<br><!-- End of picture text -->

Figure 1: Instance number scaling over time in response to the changes in the in-flight request concurrency in the state-of-theart systems and PulseNet. Kn scales too slowly, whereas KnSync incurs high costs by keeping instances idle for prolonged periods. Dirigent’s behavior is similar to Kn (not shown). 

and achieves 1.7-3.5 _×_ better performance than the systems with an asynchronous control plane, as in Knative, while reducing the cost by 3-65%. Finally, compared with the systems featuring a linear regression and the state-of-the-art NHITS prediction models [30, 47], _PulseNet_ delivers up to 4 _×_ better performance while reducing costs by 35-40%. 

We summarize the comparisons across state-of-the-art systems in Table 1 and illustrate the scaling speed and resource efficiency in Figure 1 on a trace snippet taken from Azure Functions trace [67]. In contrast to the baselines, PulseNet closely tracks traffic changes by rapidly creating emergency instances whenever the standard track lags behind and quickly tearing them down once the traffic trend settles. 

Our main contributions are: 

• We identify two types of invocation traffic, _sustainable_ and _excessive_ , with the former consuming _>_ 98% of the cluster resources and the latter stressing the control plane. 

- This work is the first to _comprehensively_ characterize the performance and cost in systems with synchronous and asynchronous control planes. We also show that previously proposed intelligent scaling predictors [30,47] incur a substantial cost overhead, with nearly 5 _×_ resource overprovisioning. 

• We propose PulseNet, a novel _dual-track_ control-plane architecture that unlocks fast, resource-efficient scaling of FaaS workloads while retaining full compatibility with conventional cluster managers and their rich feature set. 

- PulseNet outperforms Kubernetes-compatible _and_ FaaSspecialized systems [32] by 1.5-3.5 _×_ with a sampled production workload, reducing cost by up to 70%, when running synthetic and real-world benchmarks. 

2 

## **2 Background** 

Here, we describe two serverless application deployment approaches, disaggregated and co-located, and detail the state-ofthe-art control-plane architectures and associated trade-offs. 

## **2.1 FaaS&BaaS: Disaggregated or Co-Located** 

Serverless applications comprise functions (FaaS) along with conventional microservices (BaaS), e.g., for cross-function communication. To date, cloud providers have followed two deployment approaches: disaggregated with FaaS and BaaS components running in separate clusters with independent FaaS- [32,40,58,68] and BaaS-specialized [49,55,61] control planes, vs. co-located with both FaaS and BaaS orchestrated by the same cluster manager [6, 10, 18, 28]. 

Following the disaggregated approach, system architects design the cluster manager tailored for highly sporadic FaaS workloads, unlocking orders of magnitude faster scaling speed, which conventional, microservice-centric cluster managers cannot deliver [32]. However, despite the promised scaling-speed benefits, foregoing compatibility with the conventional cluster manager requires the cumbersome re-implementation of many essential features that academic prototypes often overlook, e.g., authentication, DNS, and service mesh deployments for West-East traffic [31], and rules out affinity-based optimizations [27, 50]. 

In contrast, the colocation approach is fundamentally superior, as it jointly manages FaaS and BaaS components, significantly reducing overheads and cost. Two notable examples that showcase colocation benefits are Nightcore [46], which exploits shared memory for low-latency communication, 2 _×_ faster than with RPC, and SPRIGHT [60], which reduces the data plane’s CPU overhead with eBPF by an order of magnitude. These works rely on locality-aware scheduling, which is hard to implement across clusters. Besides, many open-source production systems adopt the colocation approach [6, 10, 18, 28], as it allows them to benefit from Kubernetes’ integrated management and placement optimizations [29,75,79], support for monitoring [7,9,19,21], network control and mounts [4, 20], and versioned deployments [14]. 

The key obstacle to unlocking same-cluster management is designing an efficient joint control plane that meets the scaling-speed requirements of FaaS workloads while retaining the rich optimization and feature space of conventional managers like Kubernetes – which is the focus of our work. 

## **2.2 FaaS Control-Plane Architectures** 

To understand the bottlenecks in current FaaS control planes, we detail the control-plane architectures and operations, similar to those used by leading commercial and open-source systems. Figure 2 overviews two of the most common serverless system architectures, both of which comprise a load bal- 



<!-- Start of picture text -->
Load Cluster<br>Instances<br>Balancer Manager<br>Nodes<br>(a) System with a synchronous control plane.<br>Cluster<br>Manager<br>Load<br>Instances<br>Balancer<br>Nodes<br>(b) System with an asynchronous control plane.<br><!-- End of picture text -->

Figure 2: High-level overview of serverless architecture. The cluster manager is on the path only for cold invocations. 

ancer, a cluster manager, and worker nodes that run function instances. Load balancers and function instances constitute the data plane. Serverless function invocations arrive from the application users to the scaled-out load balancers, which route invocations to function instances for execution. If a function has no available instances to process the invocation, the cluster manager creates more instances. 

Control-plane architectures in state-of-the-art commercial [2, 12] and open-source systems [10, 18, 28] tend to fall into two categories based on whether they create instances synchronously (on the critical path) or asynchronously (off the critical path). The synchronous approach, employed by production systems such as AWS Lambda [2] and some opensource systems [28], allows for an immediate scaling reaction as soon as an invocation arrives. There, the cluster manager issues an instance creation command on the critical path of an invocation to the worker node, binding the invocation for execution in the instance freshly started on that node. 

Other systems, including Knative [10], Google Cloud Run [8], and FunctionGraph [53], use the asynchronous approach associated with a slower reaction time: these systems typically aggregate function invocation statistics over a period of time and only start scaling when they can confirm the change in the invocation traffic. Hence, in the worst case, an invocation can wait for the entire autoscaling period (which is 2 seconds in Knative [11]) before the cluster manager requests an instance creation. Moreover, prior works [32, 53] have found that asynchronous approaches may exhibit higher tail latencies, e.g., related to their higher queuing delays in the control plane. For example, when a single instance serves invocations, all invocations have to wait until the control plane decides and starts creating more instances. 

## **3 Characterization of the Traffic Patterns & Existing Control Planes’ Performance** 

In this section, we first study the traffic patterns occurring in production deployments (§3.1). Then, we study the system implications of these patterns, decomposing the scaling delays in existing state-of-the-art systems with synchronous 

3 

and asynchronous control planes (§3.2). We also evaluate the control planes’ instance-creation throughput (§3.3) and cluster-resource usage efficiency (§3.4). 

We use vHive [73] research framework to configure two setups based on Knative [10] and Kubernetes [13] for our experiments, which are widely used in commercial serverless deployments [1, 12]. The first configuration uses vanilla Knative that features an asynchronous control plane. The second configuration is a modified Knative version that features a synchronous control plane, with an autoscaling policy similar to AWS Lambda [25, 26, 71]. Section 6 provides more details about these configurations and the evaluation methodology that uses sampled production traces [56, 72]. 

## **3.1 Invocation Traffic Patterns** 

To identify key traffic patterns and system requirements, we simulate a serverless system with a synchronous control plane, and a keep-alive period of 10 minutes when replaying an hour-long production trace [56, 67]. We develop a simulator that models request concurrency (i.e., the total number of inflight function invocations) and the number of active and idle instances at each moment in time. We assume instantaneous instance scaling and that each instance runs on one CPU core. 

We observe that FaaS traffic has two distinct components. The bulk of the traffic (99.9%), further referred to as _sustainable_ , is handled by alive instances without any involvement of the control plane. Sustainable traffic uses over 98% of the CPU resources. Only the remaining 0.1% of traffic, which we term _excessive_ , triggers the creation of new instances, causing most of the load in the control plane. Our observation corroborates the data from a major cloud provider [48], reporting that only 0.01% of invocations trigger cold starts. 

This dichotomy motivates for a dual optimization strategy tailored to the distinct needs of each traffic component. For sustainable traffic, which dominates cluster resource consumption, the control plane must prioritize cost efficiency, leveraging features such as careful placement and background scaling to optimize cluster utilization. Conversely, excessive traffic consists of latency-sensitive bursts that require fast scaling. Crucially, excessive traffic accounts for a tiny fraction of total resources (2%), thus the system can trade off resource efficiency for lower latency when handling these requests without bloating overall operational costs. 



<!-- Start of picture text -->
1.0<br>0.5 Kn<br>Kn-Sync<br>0.0<br>10 1 10 0 10 1 10 3 10 1 10 1<br>Instance Creation Delay, sec Decision Delay, sec<br>CDF<br><!-- End of picture text -->

Figure 3: Cumulative distribution functions (CDFs) for the components of delays occurring in the systems with synchronous (Kn-Sync) and asynchronous (Kn) control planes. 



<!-- Start of picture text -->
Readiness Probe<br>1.0 Reverse Proxy Creation<br>Function Sandbox Creation<br>0.5 Namespaces Creation<br>Control Plane Interactions<br>Average delay, sec 0.0<br><!-- End of picture text -->

Figure 4: Instance creation time breakdown in Knative. 

We identify and study two sources of delays in serverless control planes: the instance creation delays and the decision delays. We plot cumulative distribution functions (CDFs) for each source in Figure 3 for vanilla Knative (Kn) and its modified synchronous analogue (Kn-Sync). The experiment shows that the component of the queuing delays in the range from milliseconds to 10s of seconds, i.e., comparable to the invocation execution time range [67]. Hence, if any of those delays happen on the critical path of invocation handling, they would be seen as noticeable delays to end-to-end request latency. We discuss each delay source in detail below. 

### **3.2.1 Instance Creation Delay** 

We find that instance creation takes 1–3s to complete, a delay dominated by features in conventional cluster managers like Kubernetes (Figure 4). _Readiness probes_ introduce a 500ms average delay, a result of the 1-second minimum polling interval Kubernetes uses to protect the control plane at scale. _Namespace and networking setup_ requires multiple roundtrips to the cluster manager, adding over 400ms. _Reverse (Queue) Proxy_ and function sandbox creation contribute over 250ms. Finally, the Golang runtime in the function images we deploy has minimal initialization overhead, but other runtimes like Java can compound this delay by seconds [71]. 

### **3.2.2 Decision-Making Delay** 

## **3.2 Control-Plane Scaling Delays Analysis** 

To understand the implications of the workload characteristics we discussed above, we analyze the delays that occur in the control plane of real-world synchronous and asynchronous Knative-based systems under load. In these experiments, we use the In-Vitro [72] load generator that replays a sampled production trace containing 400 functions. 

We find that decision-making latency is fast in most cases (65-85% under 10ms), particularly when creating the first instance of a function. However, when scaling functions that are already active, confirming the traffic trend by averaging arrivals over a time window creates a long tail delay of up to 20 seconds, especially for the asynchronous control plane. We find that adjusting the number of instances, i.e., scaling not from zero, often leads to such delayed decisions, as the 

4 



<!-- Start of picture text -->
1.0<br>Control plane delay<br>0.8<br>P50, Kn-Sync<br>0.6 P99, Kn-Sync<br>P50, Kn<br>0.4 P99, Kn<br>0.2<br>0.0<br>10 0 10 1 10 2 10 3<br>Instance creation rate, instance/sec<br>Delay, sec<br><!-- End of picture text -->

Figure 5: The delays occurring in the Knative control plane under various instance-creation rates, measured with a microbenchmark. The red and black lines show the required instance creation rates at the 50<sup>-th</sup> and 99<sup>-th</sup> percentiles, respectively, when replaying invocations from a sampled production trace in simulated synchronous (Kn-Sync) and asynchronous (Kn) control planes. 

control plane takes time to confirm the changing trend in the traffic by averaging the arrival rate over a time window (1 minute by default). 

In summary, instance creation delays are the biggest driver of median latency, prompting a redesign of the critical path. While decision-making has a low median latency, system architects should focus on optimizing its tail. An ideal system could achieve <200ms end-to-end scaling with fast instance creation, quick decision-making, and no internal congestion. 

stance placement and bootstrapping, consume 9% (sync) and 20% (async) of CPU cycles across the cluster nodes. 

This motivates an efficient control plane that provisions instances just-in-time, but also minimizes resource waste by reducing instance churn and avoiding a large pool of idle instances with low reuse probability. 

## **3.5 Summary and Takeaways** 

• **Sustainable and excessive traffic.** FaaS traffic is bimodal (§3.1): _sustainable_ traffic consumes the majority (>98%) of cluster resources with low control-plane load, whereas sporadic _excessive_ traffic strains the control plane with instance creation requests despite using few (<2%) resources. A well-designed system must cater to both. 

• **Conventional cluster manager is too slow for FaaS coldstart requirements.** While these managers can sustain the required instance creation _rate_ , their creation _delay_ is too high for FaaS. This necessitates bypassing the manager for speed, while retaining its rich features (e.g., consistent resource allocation, placement, networking) to ensure compatibility and enable co-location with other services (§2.1). 

• **Existing control planes waste cluster resources.** Asynchronous control planes waste CPU cycles on high instance churn, while synchronous control planes waste memory on keeping many instances idle. An efficient system should limit the churn and instance lifetime when reuse is unlikely. 

## **3.3 Conventional Control-Plane Throughput** 

We evaluate if a conventional control plane can handle the high instance creation rates of FaaS deployments [67]. Using a microbenchmark on a tuned Knative-Kubernetes control plane with emulated worker nodes via KWOK [16], we test its throughput limits (§6). 

Our tuned control plane sustains 50 cold starts/sec, a 25 _×_ increase over the throughput reported by prior work [32]<sup>2</sup> (Figure 5). However, when compared to production trace demands, this throughput is 3 _×_ lower than the median rate required by an asynchronous system, confirming it can be a bottleneck [32]. While sufficient for a synchronous system’s median load, rare 99<sup>-th</sup> percentile bursts demand 1.2 _×_ to 40 _×_ more throughput, overwhelming either control plane. 

## **3.4 Cluster Resource Efficiency Analysis** 

We analyze CPU and memory usage – a major operational cost [26] – in our synchronous and asynchronous Knative systems in the same setup as in (§3.2). We find high overheads from two sources: idle instances consume 70% (sync) and 87% (async) of total instance memory, while the control plane’s management tasks, which include activities like in- 

> 2This is not a contradiction: our careful configuration and tuning, discussed in §6, have substantially increased Knative control plane’s throughput. 

## **4 PulseNet Design** 

Based on the above insights, we organize the control plane in two loosely-coupled tracks to naturally fit the bimodal nature of the serverless traffic (§3.1). The proposed system combines rapid scaling and compatibility with conventional cluster managers, unlocking efficient colocation of stateless and stateful services in the same cluster. 

The first, _standard_ , track is tailored to sustainable traffic. Given that sustainable traffic accounts for the majority of the cluster resource usage, the standard track needs to carefully distribute the sustainable traffic among the existing instances, which this track needs to carefully place and scale following the sustainable-traffic trends. The conventional control plane, such as Knative, is a perfect fit for this goal, with its rich feature set and strictly consistent tracking and allocation of cluster resources §2.1. 

The second, _expedited_ , control-plane track should deliver rapid scaling for sporadic bursts specific to excessive traffic. The system creates disposable, single-use instances to process these bursts, accounting for a tiny fraction of cluster resources. Hence, this track can substantially improve the speed of instance creation – without tipping the load balance across the cluster, by safely bypassing the standard track’s strictly consistent bookkeeping of cluster resource usage. 

5 



<!-- Start of picture text -->
function invocations<br>PulseNet route excessive traffic<br>Load Balancer Fast Placement<br>send metrics<br>route sustainable traffic<br>Cluster<br>request emergency instances<br>Manager  & forward invocations<br>Worker Node<br>Kubelet Pulselet<br>Regular Emergency<br>Instances Instances<br>Standard Track Expedited Track<br><!-- End of picture text -->

Figure 6: The PulseNet architecture that combines the added expedited control plane with the conventional one. 

## **4.1 PulseNet Architecture Overview** 

Figure 6 shows PulseNet’s workflow when processing invocations and cold starts of new function instances. Function invocations arrive at _PulseNet_ that comprises two components: _Load Balancer_ and _Fast Placement_ . Similar to the existing designs (§2), Load Balancer identifies the target function and finds a Node with an existing non-busy instance of that function to route the invocation for processing. As in systems with a vanilla asynchronous control plane, Cluster Manager continuously monitors and predicts trends in function invocation traffic, adjusting the number of instances for functions that experience up or down trends in invocation traffic. We refer to these instances as _Regular Instances_ . Importantly, Regular Instance creations are off the function invocations’ critical path. PulseNet manages Regular Instances similarly to how microservice replicas are managed in conventional managers, such as Kubernetes. 

The Load Balancer chooses the track for each request based on the availability of the Regular Instances.<sup>3</sup> If there are available Regular Instances in the standard track, Load Balancer uses one of them. Otherwise, it sends the request to expedited track’s Fast Placement component. Fast Placement triggers an _Emergency Instance_ creation by sending a request to PulseNet’s agent, called _Pulselet_ , on one of the cluster nodes in a Round-Robin. Pulselet spawns an Emergency Instance to process the excessive traffic. Similar to Kubernetes’ kubelet [13] and Borg’s borglet [75], Pulselet manages the lifecycle of the hosting node’s Emergency Instances, shutting down each instance once it completes processing the request it was created for. 

This track choice rule prioritizes optimally allocated Regular Instances, resorting to Emergency Instances in cases dur- 

> 3We consider an instance available if its per-instance queue is not full. 

ing traffic bursts and fast changes in the traffic trends. 

## **4.2 The Expedited Track: Fast, Disposable Emergency Instances** 

PulseNet’s expedited track achieves speed by spawning Emergency Instances _transparently_ to the cluster manager, limiting the supported feature set, and using checkpoint-restore. PulseNet also lowers the cost by disposing of these instances after processing a single invocation. 

**No cluster manager interaction.** Pulselet does not register the Emergency Instance with the conventional cluster manager. This eliminates all associated overheads, including state persistence in etcd, scheduling, and declarative state reconciliation [32]. Fast placement periodically retrieves and caches the following information from the cluster manager: function image ID, CPU and memory quotas, and revision information. Since this metadata changes only upon function redeployment or new revision roll-out. 

**Limited feature set.** Emergency Instances support only the features required for processing a single function invocation: OCI container image deployment, outbound network connections via NAT, and locally-enforced CPU and memory quotas [15], foregoing the features required for long-running, reusable Regular Instances and other microservices. First, for Emergency Instances, PulseNet uses local IP addresses rather than complex CNI integration for service meshes, which requires sending outbound traffic via the centralized frontend to access other services, e.g., storage. Given that Emergency Instances account for a tiny fraction of cluster resources (§3.1), this traffic cannot substantially overload the frontend. Second, Pulselet checks the readiness of Emergency Instances independently, reducing the load on the centralized cluster manager. Note, the features PulseNet supports are enough to execute arbitrary user-function code both in Regular and Emergency Instances. 

**Optimized Sandbox Start.** Pulselet uses common techniques to reduce the sandbox creation time: VM snapshot-restore and a pool of pre-initialized virtual network devices that Pulselet can quickly bind to the newly restored VMs. 

**Disposable Instances to Minimize Footprint** To prevent resource waste, Emergency Instances are single-use and disposed of after they finish processing an invocation. This ensures that the resources used to handle transient traffic bursts are reclaimed instantly, avoiding the prevalence of idle instances in the existing systems (§3.4). Emergency Instances process their dedicated invocations to completion and have the same scheduling priority as Regular Instances. 

## **4.3 The Standard Track: Efficiently Managing Sustainable Traffic with Smart Filtering** 

While the expedited track ensures low-latency cold starts, the standard track is designed for resource efficiency. Its primary 

6 

goal is to manage the pool of Regular Instances – while minimizing memory waste and avoiding high instance churn that might overload the heavyweight standard track. 

The key to achieving these goals is to filter the metrics coming from the expedited track, which handles the traffic spikes, before passing them to the standard track. Hence, PulseNet Load Balancer reports to the standard track only a fraction of invocations handled by Emergency Instances, i.e., the invocations that represent long-term trend changes rather than sporadic bursts. 

In practice, we find that the function’s inter-arrival time (IAT) is a good indicator of trend consistency when compared with the keep-alive period used by the system for Regular Instances. Thus, Load Balancer collects and periodically updates the IAT distribution for each function. When the Load Balancer steers an invocation to the expedited track, it also compares the function’s median IAT against PulseNet’s keepalive period. If the median IAT is lower than the keep-alive period, it is worth creating an additional long-living Regular Instance for future invocations of that function. Hence, Load Balancer includes this invocation into the metrics reported to the cluster manager. Otherwise, the Load Balancer treats the invocation as sporadic and filters it out from the metrics. PulseNet’s keep-alive and filtering percentile are configurable parameters we empirically evaluate in §7.1. 

This filtering mechanism prevents the system from creating costly Regular Instances that would likely sit idle, thus reducing the overall memory usage compared to the systems that rely on long keep-alive periods [25] or aggressive predictive scaling [47, 62], as we show in §7.3.3. 

## **4.4 Discussion** 

**Accuracy of Traffic Classification.** Despite the simplicity of our IAT-based filtering technique, it is highly efficient: PulseNet steers the bulk of traffic to Regular Instances (§7.3). Misclassifications are benign: overly conservative filtering may increase the use of Emergency Instances, whereas overly permissive filtering may create more Regular Instances that are recycled by the keep-alive mechanism. We leave the design of a more intelligent traffic classifier to future work. **Resource Allocation.** Effectively, PulseNet places Emergency Instances in the CPU and memory utilization margin of the cluster that is typically in the 20-60% range in production [70,75] – more than enough to accommodate a mere 10% fraction used by these instances in our experiments (§7.3). **PulseNet Limitations.** The PulseNet design relies on the observation that unpredictable bursts comprise a small fraction in production deployments, whereas the majority of function invocations can be tracked with a window-based or predictorbased autoscaler, as we show in §3.1, corroborating prior works [47, 67]. In the hypothetical scenarios where bursts dominate the traffic, PulseNet’s expedited track might be utilized on par with the standard track, requiring a more sophis- 

ticated load balancing policy. 

## **5 PulseNet Implementation** 

We implement PulseNet prototype in vHive [73], an opensource framework widely used for serverless systems research in academia and industry. vHive deploys Knative [10] production FaaS framework, used in commercial serverless offerings [12], atop the Kubernetes [13] cluster manager. We modify several Knative components, namely Activator and Autoscaler, leaving Kubernetes completely unchanged. **PulseNet Load Balancer and Metric Filtering.** We modify the Knative Activator component to serve as a Load Balancer that routes requests to the standard track or expedited track based on the availability of Regular Instances. It also implements the metric filtering as described in §4.3. 

**Standard Track and Regular Instances.** For a thorough evaluation, it is paramount to deploy a production-grade control plane for the PulseNet standard track to have representative overheads present in a real system. Hence, we deploy modified Knative’s control plane that follows the AWS Lambda scaling policy [25] atop _vanilla_ Kubernetes – with representative interactions across the control plane, cluster manager, and instances.<sup>4</sup> 

**Expedited Path: Fast Placement, Pulselet, and Emergency Instances.** To evaluate PulseNet dual-track design, we need to make sure that our expedited track’s delays are representative of state-of-the-art systems. Hence, we utilize AWS Firecracker MicroVMs as sandboxes for Emergency Instances using their snapshot-restore technology, as in AWS Lambda [3, 26]. For Fast Placement, we use a Round-Robin placement algorithm inside Knative Activator to uniformly distribute this load across all worker nodes in the cluster. Emergency Instances run invisibly to the cluster manager without tipping the load balance, as they account for a tiny fraction of CPU and memory resources, hence effectively running in the cluster’s overprovisioning margin. We implement Pulselet in Golang and deploy it alongside the regular kubelet. 

## **6 Methodology** 

**Hardware setup.** We run PulseNet and other serverless systems on an 8-node c220g5 Cloudlab cluster [5]. Each node has two Intel Xeon Silver 4114 CPUs @ 2.20GHz, each with 10 physical cores, 192 GB DRAM, and an Intel SSD. **Real Control-Plane Deployment with an Emulated LargeScale Cluster.** For some experiments in §3 and §7, we use 

> 4This approach has a limitation: Knative deploys instances in containers, rather than in MicroVMs like in commercial systems [24, 26], which might show shorter sandbox startup latencies. Open-source production-grade MicroVM solutions, e.g., Firecracker or gVisor, come without a productiongrade control plane, and re-implementing it in-house with a complete set of features supported by a system like AWS Lambda or Kubernetes might undermine representativity of the control-plane interactions. 

7 

KWOK [16] v0.6.1 to simulate large numbers of worker nodes while retaining a real Knative-Kubernetes control plane, enabling high-scale evaluation of our serverless system without the prohibitive cost of provisioning physical clusters. KWOK supports modeling node and instance behavior to stress-test control-plane performance and experiment with scenarios, such as high-rate sandbox creation by the control plane (§3.3) or configurable instance creation time (§7.2.3), which is difficult to observe with real hardware outside a production environment. This approach uses real control-plane components with all their interactions, as in a large-scale production deployment, while modeling the load on worker nodes. This makes large-scale and configurable experiments (§7.4) feasible in a small-scale research setting. 

**Software setup.** We use vHive [73], i.e., Knative v1.13 running on top of Kubernetes v1.29. Regular Instances run atop containerd v1.6.18, while Emergency Instances execute in AWS Firecracker VMs v1.10.1, with snapshot-restore enabled. We limit each Knative instance’s concurrency to 1 (i.e., maximum number of concurrent requests per instance), similarly to AWS Lambda [25]. To prove the generality of our approach, we evaluate other values for per-instance concurrency separately in §7.5. We assume all container images and VM snapshots are cached in memory on each node, similarly to prior work [32]. To ensure measurement stability, we disable SMT and fix the CPU frequency to the base frequency, and set the Load Balancer’s (called Activator in Knative) replica count to 1, but ensure that it never becomes a bottleneck.<sup>5</sup> 

**Workload.** We use the In-Vitro [72] methodology for representative trace sampling and load generation. In all experiments, we use a 400-function trace sample with per-function IAT and duration distributions, chosen to apply the maximum possible load to the cluster without reaching 100% CPU utilization at any point throughout the experiment. Only in §7.4, we use a bigger trace with 2000 functions to evaluate the performance of a larger, 50-node cluster. We run experiments for an hour, discarding the first 20 minutes as a warm-up. Similar to the prior work [32, 72], we use a synthetic spin-loop function with a programmed duration taken from the trace. To confirm our findings with the synthetic functions, we then use a set of realistic serverless functions (encryption, authentication, fibonacci, and image-rotate) from vSwarm [64], which are written in Go, Python, and Node.js, in §7.5. To achieve the load representative of a production setup, we replicate these functions so that each replica corresponds to one of the functions from the same 400-function sample derived from the Azure traces to fit the sample’s execution duration and memory footprint distributions. 

**Baselines.** We compare PulseNet to five state-of-the-art serverless systems. We use four baselines based on Knative [10], which is a Kubernetes-based serverless system widely used in commercial offerings [12]. First is vanilla 

> 5During the peak utilization periods in our experiments, Knative Activator uses less than one CPU core with a 99<sup>-th</sup> percentile _<_ 10ms routing delay. 

Knative ( **Kn** ) with an asynchronous control plane, which uses its default concurrency-based autoscaling policy with a 60-second autoscaling window. We carefully configure the Knative deployment to maximize the baseline control plane’s performance.<sup>6</sup> The second one is Knative-Synchronous ( **KnSync** ), the Knative version we implement with synchronous instance creation similar to AWS Lambda. Specifically, we have modified Autoscaler to trigger new instance creations when it cannot find an available instance for a new request and retain the instances for a fixed period of inactivity. We use a 10-minute keep-alive period, which is estimated to be the keep-alive duration for AWS Lambda [71]. We also use **Dirigent** [32], a clean-slate serverless cluster manager with a high-performance asynchronous control plane, which is the state-of-the-art academic system. Finally, ( **Kn-NHITS** ) and ( **Kn-LR** ) that use NHITS [30] and lightweight linear regression prediction models (demonstrated as the most accurate predictors for FaaS by the prior work [47]), respectively, replacing the default Knative autoscaling policy. We train the models on the one-hour-long part of the trace that precedes the part used in the evaluation. 

**Performance and Cost Metrics.** We are using several metrics to evaluate the systems. Our main characteristics of the systems are function invocation performance and the costs that the serverless system incurs to provide that level of performance. To evaluate performance, we use the geometric mean of the tail (99<sup>-th</sup> percentiles) of per-function slowdown. Lower slowdown is better, with the slowdown of 1 meaning that the system’s end-to-end response time is as low as measured in an unloaded system.<sup>7</sup> To estimate the cost-efficiency, we use the total memory footprint of all instances in the cluster, normalized to the total memory footprint of non-idle instances. We call this metric _normalized cost_ . We also evaluate other cost sources, such as instance creation rates and the CPU cycles used by control-plane components. We derive these metrics by collecting cluster-wide metrics with Prometheus [21] and Kubernetes Metrics Server [23]. 

## **7 Evaluation** 

We evaluate PulseNet to answer the following questions: (1) How to set PulseNet’ parameters for the best performance and lowest overhead? (§7.1) (2) How does PulseNet’s performance compare with existing systems? (§7.2) (3) How does PulseNet’s cluster resource utilization compare with existing systems? (§7.3) (4) How does PulseNet balance performance and cost trade-offs? (§7.4) 

6We increase concurrency and request rate limits to the Kubernetes API Server in Knative components and Kubernetes Controller Manager, and also increase the CPU and memory quotas for Knative core components. 

7We first calculate per-invocation slowdown by dividing the end-to-end response time by expected execution duration. Then we compute the perfunction 99<sup>-th</sup> percentile of slowdown. Finally, we aggregate per-function slowdown with the geometric mean. 

8 



<!-- Start of picture text -->
10 5.75<br>5.50<br>5 5.25<br>7.5<br>3.0<br>5.0<br>2.5<br>2.5<br>10 1 10 2 50 100<br>Keep-alive duration, sec Filtering percentile<br>(a) Keep-alive duration. (b) Filtering percentile.<br>P99 slowdown P99 slowdown<br>Normalized cost      Normalized cost<br><!-- End of picture text -->

Figure 7: Effects of keep-alive duration (a) and filtering percentile (b) on PulseNet performance and cost. Results are collected under realistic samples from Azure Functions trace. 

## **7.1 PulseNet Sensitivity Studies** 

As discussed in §4.3, PulseNet’s performance is primarily affected by two parameters: (1) keep-alive duration and (2) metric filtering percentile. Below, we study PulseNet sensitivity to these parameters and identify the sweet spot in the performance-cost trade-off to choose these parameters’ values when running sampled production traces. 

**Keep-Alive Duration.** The keep-alive duration determines how long a Regular Instance can remain idle before it is terminated. A smaller keep-alive increases the cold start probability, degrading performance. A higher keep-alive causes resource wastage, increasing cost. We sweep the keep-alive duration from 2s to 600s to measure its impact on system performance and cost. As Figure 7(a) shows, when the keep-alive duration reaches 60s, further increasing it significantly increases the cost with minimal performance improvement. Thus, we set the keep-alive duration to 60s. 

**Filtering Percentile.** The filtering percentile determines the confidence threshold to create new function instances. Specifically, a lower filtering percentile increases the likelihood of creating new instances, leading to resource over-allocation and higher costs. A higher filtering percentile makes the system more conservative in creating new instances, increasing the number of cold starts and degrading performance. We vary the percentile from 25% to 99%. Figure 7(b) shows that PulseNet achieves the best balance between performance and cost when the filtering percentile is 50%, which we use below. 

Given the obtained results, we choose the 60-second keepalive period and the 50<sup>-th</sup> percentile as metric filtering percentile in PulseNet as our parameters for evaluation. 



<!-- Start of picture text -->
1.00<br>Kn<br>0.75 Kn-NHITS<br>Kn-LR<br>0.50 Dirigent<br>Kn-Sync<br>0.25<br>PulseNet<br>0.00<br>10 3 10 2 10 1 10 0 10 1<br>Average per-function scheduling time, sec<br>CDF<br><!-- End of picture text -->

Figure 8: CDFs of average per-function scheduling delay in evaluated systems under a sampled production workload. 

### **7.2.1 Instance Creation Delay Breakdown** 

We first compare the creation delays of Regular and Emergency instances. PulseNet eliminates all interactions with the cluster manager and uses a pool of pre-allocated local IP addresses to create the Emergency Instance in under 150ms, nearly 10 _×_ faster than creating a Regular Instance in Knative (Figure 4). Importantly, Regular Instance creation delays always occur off the critical path when handling invocations in PulseNet. Hence, PulseNet exposes only the cold-start delays of Emergency Instances to the application. 

### **7.2.2 Scheduling Delays Analysis** 

We continue the evaluation with the scheduling delays of different serverless systems. Scheduling delay includes coldstart time, data-plane queuing, request routing, and load balancing. To measure the scheduling delay, we subtract the function’s execution time from the end-to-end invocation latency. Figure 8 shows the distribution of average scheduling delay for each system. 

As shown in Figure 8, Knative, Dirigent, and PulseNet show median delays of 1s, 200ms, and 150ms, respectively, matching their instance creation times. In addition to faster instance creation delays, PulseNet eliminates the worst-case latencies of up to 4 seconds that sporadically occur in Knative and Dirigent due to their window-based autoscaling policies. Kn-NHITS and Kn-Sync, due to their high instance retention, have 40-50% of functions that experience warm starts below 20ms. However, the remaining functions are delayed up to 2s due to slow instance creation. Kn-LR shows high latency, up to 4 seconds, indicating its high prediction error. Compared with the above baselines, PulseNet reduces worst-case scheduling delays by quickly creating Emergency Instances when no Regular Instances are present or when all Regular Instances are busy, while minimizing cluster resource usage. 

## **7.2 Control-Plane Performance Analysis** 

In this section, we evaluate PulseNet’s control-plane performance from three perspectives: instance creation delays, scheduling delays, and sensitivity to instance creation delays. 

### **7.2.3 Sensitivity to Various Instance Creation Delays** 

Different providers use different deployment and sandbox technologies, from regular VMs to FaaS-specialized solu- 

9 



<!-- Start of picture text -->
Kn<br>10 2<br>Kn-Sync<br>PulseNet<br>10 1<br>10 1 10 0 10 1 10 2<br>Instance creation delay, seconds<br>Figure 9: Slowdowns of the systems in cluster managers with<br>different simulated instance creation delays, measured for<br>sampled production workload. Lower is better.<br>11.3<br>4<br>1.5    Overheads<br>3 W orker Node<br>Co ntrol Plane<br>1.0<br>2 Pr edictor<br>User Functions<br>1 0.5 Em ergency Instances<br>Re gular Instances<br>0 0.0<br>(a) Instance creat. rate. (b) CPU utilization breakdown.<br>Kn-NHITSKn Kn-LRDirigentKn-SyncPulseNet Kn-NHITSKn Kn-LRDirigentKn-SyncPulseNet<br>P99 slowdown<br>Pod creation rate, pods/s Normalized C PU utilization<br><!-- End of picture text -->

Figure 10: Cluster-wide instance creation rates observed (a) and CPU utilization breakdown (b) in the systems under sampled production workload. 

tions, to isolate Regular Instances. Hence, we evaluate the impact of their corresponding instance creation delays on the performance of the baseline systems and PulseNet. We use KWOK [16] to set up the simulated instance creation delay from 100ms, as in container bootstrapping, to 100s, similar to the booting time of a general-purpose VM, and measure the performance of different serverless systems under the same sampled production trace. 

Figure 9 shows that increasing instance creation delay leads to a significant performance degradation for the baseline systems, whereas PulseNet shows no sensitivity because its fastpath control plane can quickly create Emergency Instances to handle burst traffic. 

In summary, by creating Emergency Instances for excessive traffic, PulseNet effectively eliminates worst-case scheduling delays. Furthermore, based on this design, even in environments with high instance creation delays, PulseNet delivers more stable performance. 

## **7.3 Control-Plane Resource Efficiency** 

Next, we analyze PulseNet’s control-plane resource efficiency from three perspectives: instance creation rate and CPU and memory utilization across the cluster. 

### **7.3.1 Instance Creation Rate** 

In this experiment, we measure the instance creation rate over time while executing the Azure Functions trace and show the results in Figure 10(a). A lower instance creation rate reduces the control-plane overhead and improves system stability. 

As shown in Figure 10(a), Kn-Sync has the lowest instance creation rate (0.1 instances/s) as it uses a long 10-minute keepalive duration, allowing most instances to be reused. Knative and Dirigent show comparable instance creation rates (1.8 and 1.6 instances/s, respectively) as they employ similar autoscaling policies. The prediction model-based Kn-NHITS and Kn-LR have the highest instance creation rates (2.4 and 11.3 instances/s, respectively). This is because they need to adjust the number of instances based on prediction results frequently. Compared with Knative, PulseNet reduces the instance creation rate by 60% to 0.8 instances/s. This is because PulseNet’s filtering mechanism intelligently avoids creating unnecessary Regular Instances for functions with little, instead handling those with Emergency Instances. This design can reduce the computational overhead in the serverless system’s control plane and improve system stability. We study the additional computational resources required to handle instance creation in the following section. 

### **7.3.2 Cluster-wide CPU Cycles Utilization Breakdown** 

We define CPU overhead as additional CPU consumption beyond the resources required to serve user functions, which incurs costs for service providers. CPU overhead includes all control-plane components (sandbox management, traffic predictions, health and metric gathering), data-plane components (load balancer, ingress), and any computation overhead produced by prediction mechanisms. 

As shown in Figure 10(b), Emergency Instances account for only 10% of total CPU usage by the instances. PulseNet has similar overhead as Knative (24%) since it adds extra overhead for Emergency Instance management, while reducing the load on the control plane due to fewer instances created. Prediction-based systems, Kn-NHITS and Kn-LR, have the highest CPU overhead due to additional compute resources required for predictions and handling more instance creations (we exclude their training time as an overhead): 45% and 64%, respectively. Dirigent can handle the same instance creation rate as Knative with 2% computational overhead due to its lighter cluster management implementation. Kn-Sync, due to its longer keep-alive period, reduces the frequency of instance creation, thereby decreasing CPU overhead to 9%. Although PulseNet CPU overhead is higher than that of Kn-Sync, PulseNet achieves a better balance of resource usage by trading slightly increased CPU overhead for significantly reduced memory usage. We will analyze this in depth in §7.3.3. 

10 



<!-- Start of picture text -->
7.5<br>5.0<br>Idle Instances<br>Emergency Instances<br>2.5<br>Regular Instances<br>0.0<br>Kn-NHITSKn Kn-LRDirigentKn-SyncPulseNet<br>Norm. memory usage<br><!-- End of picture text -->

Figure 11: Memory usage for different serverless systems under sampled production workload normalized to the number of active instances. Lower is better. 

### **7.3.3 Memory Usage** 

In this section, we evaluate the memory usage of various serverless systems by replaying the Azure Functions trace. We show our results in Figure 11. Kn-Sync exhibits the highest memory usage because it employs a long keep-alive period of 10 minutes to handle requests, using 7 _×_ more memory for idle instances than for active ones. The prediction accuracy of Kn-NHITS and Kn-LR leads to overprovisioning of instances of 5 _×_ and 4.5 _×_ , respectively. Dirigent, due to its fast instance creation speed, can create instances more quickly, reducing queuing and preventing subsequent overreaction by the autoscaler. PulseNet uses our proposed metric-filtering technique, which allows some requests to be handled by an Emergency Instance without creating a long-lived Regular Instance. These Emergency Instances account for 10% of the total non-idle instance memory usage. Compared with Knative and Kn-Sync, PulseNet improves memory utilization by 8% and 60%, respectively. PulseNet uses 5% more memory for instances than Dirigent, which could be improved with better metric filtering mechanisms (§4.3). 

In summary, with our proposed dual-path control-plane architecture and intelligent filtering mechanism, PulseNet achieves the best balance between memory and CPU resources among Kubernetes-compatible systems. Specifically, PulseNet reduces the memory utilization by 8-60% compared to the baselines (and only 5% more than the FaaS-specialized Dirigent) and imposes negligible CPU overhead. 

## **7.4 Performance & Cost Trade-off Analysis** 

In this section, we compare the performance and resource usage of different serverless systems. We also validate these results in a large-scale cluster with emulated worker nodes. **Experiments with a Real System.** In this section, we evaluate the trade-off between performance and cost for different systems. We obtain the performance-cost trade-off by varying instance retention-related parameters ( _e.g.,_ keep-alive period, autoscaling window) from 6 seconds to 10 minutes. As shown in Figure 12, PulseNet achieves the best tradeoff between performance and cost. Compared with Knative and its variants (such as Kn-NHITS and Kn-LR), PulseNet 



<!-- Start of picture text -->
25 Kn<br>Kn-NHITS<br>20 Kn-LR<br>Dirigent<br>15 Kn-Sync<br>PulseNet<br>10<br>5<br>2 3 4 5 6 7<br>Normalized cost<br>P99 slowdown<br><!-- End of picture text -->

Figure 12: Performance-cost trade-off comparison for different serverless systems under sampled production workload. Lower is better for both axes. 

achieves higher performance at lower resource costs. Specifically, PulseNet outperforms Kubernetes-compatible systems with synchronous control planes by 1.5-3.5 _×_ at 8-70% lower cost, and surpasses asynchronous counterparts by 1.7-3.5 _×_ at 3-65% lower cost. PulseNet achieves 35% faster end-to-end performance at a comparable cost to the Dirigent system. The reason behind PulseNet’s optimal tradeoff is its dual-track control-plane design. This design effectively manages sustainable traffic with Regular Instances and excessive traffic with Emergency Instances, thereby achieving higher performance with fewer resource costs. 

**Large-Scale Experiments.** Then, we use the same methodology and metrics to evaluate the performance-cost trade-offs in the large-scale cluster by simulating 50 worker nodes with KWOK and running real control-plane components. The experimental results show that at this larger scale, PulseNet still demonstrates significant improvements compared with state-of-the-art systems. Specifically, PulseNet outperforms Kubernetes-compatible systems with both synchronous and asynchronous control planes by up to 3 _×_ at up to 3 _×_ lower cost. As the cluster size increases, traditional systems experience severe control-plane congestion. Additionally, system configurations that performed well in smaller clusters can overload the control plane under larger workloads. PulseNet effectively addresses this problem through the filtering mechanism between its expedited and standard tracks. 

## **7.5 Generalizability of PulseNet** 

**Sensitivity to Per-Instance Concurrency.** As some providers, such as Google Cloud Run [8], recommend setting up per-instance concurrency (CC) larger than 1, we compare PulseNet performance and cost to the Knative baseline with larger CC. For the Knative baseline, increasing CC from 1 to 10 improves performance by about 20%, with the speedup saturating at CC of 5. Hence, a higher CC value can modestly 

11 



<!-- Start of picture text -->
1<br>Kn (Synthetic)<br>PulseNet (Synthetic)<br>Kn (Real)<br>0 PulseNet (Real)<br>10 1 10 3<br>Per-function tail slowdown (p99)<br>CDF<br><!-- End of picture text -->

Figure 13: Tail slowdown for real-world functions and synthetic applications under production workload. 

shrink the gap in performance between PulseNet and the baseline (as CC does not affect the expedited track of PulseNet, PulseNet performance does not change), but the latter remains more than 3 _×_ faster. Furthermore, operating Knative at CC of 5 increases the overall operational cost by 3 _×_ , assuming that concurrency-enabled instances incur proportionally higher resource costs. 

**Real-World Applications.** We verify the generality of our findings by running real-world workloads from vSwarm written in Go, Python, and Node.js. We observe a 4.3 _×_ reduction in tail slowdowns, as shown in Figure 13, with a negligible impact on the number of instances in PulseNet relative to the Knative baseline. This performance gain is similar to previous experiments, however, with a larger performance improvements over the baseline with real functions compared to with synthetic ones, confirming the effectiveness of PulseNet in real-world deployments.<sup>8</sup> 

## **8 Related Work** 

**Cluster manager designs.** Both practitioners and academics explore many designs for datacenter cluster managers primarily targeting long-running services and microservices [13, 41, 42, 44, 65, 74]. Some works [59, 65] explore trade-offs between centralized and decentralized cluster manager designs. Other works [33–35] study the interference among the services co-located in the same cluster. The advent of Borg [70, 75] has mostly closed the research area for generalpurpose cluster managers, making its open-source alternative Kubernetes [13] the system of choice for long-running services and the foundational ecosystem for cloud offerings. PulseNet is fully compatible with the cluster managers, such as Kubernetes, benefiting from their mature ecosystem and optimizations. Although we show that conventional control planes based on Kubernetes deliver enough throughput to avoid queuing delays when creating instances at the datacenter scale, KOLE [78] adapts Kubernetes for large-scale edge deployments but foregoes run-time instance creation essential for highly-dynamic serverless workloads. 

**FaaS-Oriented Control-Plane Optimizations.** Recent works explore FaaS-specialized control planes, specifically 

> 8We attribute those differences to the limitations of mapping 400 functions from Azure Trace to a set of replicated 11 vSwarm functions. 

focusing on FaaS workloads and often excluding the BaaS services from their consideration. Some works [47,54,57,62,67] focus on predicting the arrival time or request concurrency of future invocations to pre-allocate function instances ahead of time. Ilúvatar [39] reduces the scheduling overhead for warm starts. PulseNet is complementary to the above works, as it supports predictor-informed scaling in the standard track, and uses the conventional components in its warm-start path. Finally, other works [32, 40, 58, 68] take a radical approach designing FaaS-only scalable high-throughput control planes, foregoing the benefits of FaaS and BaaS application components colocation in the same cluster. 

**BaaS-Oriented Control-Plane Optimizations.** Several works have proposed BaaS-oriented control-plane designs tailored for serverless applications. Some works [49, 55, 61] optimize BaaS control planes for ephemeral storage by automatically scaling cache resources and dynamically selecting storage backends based on application workload patterns. Other works [36,45,76] propose fast technologies to facilitate data movement across functions, transparently to the application. PulseNet is complementary to these BaaS-specialized control planes, which can potentially be implemented as Kubernetes scheduler plug-ins. Furthermore, SPRIGHT [60] and Nightcore [46] mitigate overheads in data movement between co-located instances by replacing TCP/IP networking with eBPF and IPC, respectively. FUYAO [52] extends this approach to optimize intra-node communication by eliminating the TCP/IP stack, in addition to DPU-accelerated inter-node data movement. Similarly, Apiary [50] places the function execution into the database’s user-defined functions. These works underscore the benefits of data locality, which can be achieved through scheduling policies in conventional cluster managers such as Kubernetes [29, 79]. 

**Other optimizations for serverless systems: cold-start delays, microvms, and hypervisors.** Many recent works [37, 43, 51, 63, 66, 69] redesign the runtimes to improve the performance and efficiency of serverless and cloud deployments. Other works [38, 77] apply similar approaches for GPUcentric workloads. These works are orthogonal to PulseNet and can be seamlessly incorporated into the PulseNet tracks. 

## **9 Conclusion** 

This work resolves the long-standing serverless trade-off between the performance of clean-slate systems and the compatibility of conventional managers. We introduce PulseNet, a hybrid architecture built on the insight that FaaS traffic is bimodal—split between sustainable and excessive patterns. Its dual-track control plane melds a standard, compatible path for sustainable traffic with an expedited path using disposable fast instances for excessive bursts. PulseNet proves that serverless platforms can achieve high performance and full compatibility simultaneously, without compromise. 

12 

## **References** 

- [1] CNCF Survey, 2020. Available at https: //www.cncf.io/wp-content/uploads/2020/ 11/CNCF_Survey_Report_2020.pdf. 

- [2] AWS Lambda, 2025. Available at https://aws. amazon.com/. 

- [3] AWS Lambda SnapStart, 2025. Available at https://docs.aws.amazon.com/lambda/latest/ dg/snapstart.html. 

- [4] Calico, 2025. Available at https://docs.tigera.io/ calico/latest/about/. 

- [5] CloudLab, 2025. Available at https://www.cloudlab. us/. 

- [6] Fission: Open Source, Kubernetes-Native Serverless Framework, 2025. Available at https://fission.io. 

- [7] Fluentd, 2025. Available at https://www.fluentd. org/. 

- [8] Google cloud run, 2025. Available at https://cloud. google.com/run. 

- [9] Grafana, 2025. Available at https://grafana.com/. 

- [10] Knative, 2025. Available at https://knative.dev/. 

- [11] Knative Autoscaling Configuration, 2025. Available at https://github.com/knative/serving/blob/ main/config/core/configmaps/autoscaler. yaml#L126. 

- [12] Knative offerings, 2025. Available at https://knative.dev/docs/install/knativeofferings/. 

- [13] Kubernetes, 2025. Available at https://kubernetes. io. 

- [14] Kubernetes, 2025. Available at https: //kubernetes.io/docs/concepts/workloads/ controllers/deployment/. 

- [15] Kubernetes, 2025. Available at https://kubernetes. io/docs/concepts/configuration/manageresources-containers/. 

- [16] Kwok, 2025. Available at https://kwok.sigs.k8s. io/. 

- [17] Nuclio, 2025. Available at https://nuclio.io/. 

- [18] OpenFaaS, 2025. Available at https://www. openfaas.com/. 

- [19] Opentelemetry, 2025. Available at https:// opentelemetry.io/. 

- [20] Persistent Volumes - Kubernetes, 2025. Available at https://kubernetes.io/docs/concepts/ storage/persistent-volumes/. 

- [21] Prometheus, 2025. Available at https://prometheus. io/. 

- [22] Ray Serve Autoscaling — Ray 2.37.0, 2025. Available at https://docs.ray.io/en/latest/serve/ autoscaling-guide.html. 

- [23] Resource metrics pipeline - Kubernetes, 2025. Available at https://kubernetes.io/docs/tasks/debug/debugcluster/resource-metrics-pipeline/. 

- [24] The container Security Platform, 2025. Available at https://gvisor.dev/. 

- [25] Understanding Lambda function scaling - AWS Documentation, 2025. Available at https://docs.aws.amazon.com/lambda/latest/ dg/lambda-concurrency.html. 

- [26] Alexandru Agache, Marc Brooker, Alexandra Iordache, Anthony Liguori, Rolf Neugebauer, Phil Piwonka, and Diana-Maria Popa. Firecracker: Lightweight Virtualization for Serverless Applications. In _Proceedings of the 17th Symposium on Networked Systems Design and Implementation (NSDI)_ , pages 419–434, 2020. 

- [27] Amazon Web Services. Amazon S3 Object Lambda, 2025. Available at https://aws.amazon.com/s3/ features/object-lambda/. 

- [28] Apache. OpenWhisk, 2025. Available at https:// openwhisk.apache.org/. 

- [29] Hamid Hajabdolali Bazzaz, Yingjie Bi, Weiwu Pang, Minlan Yu, Ramesh Govindan, Neal Cardwell, Nandita Dukkipati, Meng-Jung Tsai, Chris DeForeest, Yuxue Jin, Charles J. Carver, Jan Kopanski, Liqun Cheng, and Amin Vahdat. Preventing Network Bottlenecks: Accelerating Datacenter Services with Hotspot-Aware Placement for Compute and Storage. In _Proceedings of the 22nd Symposium on Networked Systems Design and Implementation (NSDI)_ , pages 317–333, 2025. 

- [30] Cristian Challu, Kin G. Olivares, Boris N. Oreshkin, Federico Garza Ramírez, Max Mergenthaler Canseco, and Artur Dubrawski. NHITS: Neural Hierarchical Interpolation for Time Series Forecasting. In _Thirty-Seventh AAAI Conference on Artificial Intelligence, AAAI_ , pages 6989–6997, 2023. 

13 

- [31] Christian Posta. Application Network Functions With ESBs, API Management, and Now.. Service Mesh?, 2025. Available at https://blog.christianposta. com/microservices/application-networkfunctions-with-esbs-api-management-andnow-service-mesh/. 

- [32] Lazar Cvetkovic, François Costa, Mihajlo Djokic, Michal Friedman, and Ana Klimovic. Dirigent: Lightweight Serverless Orchestration. In _Proceedings of the 30th ACM Symposium on Operating Systems Principles (SOSP)_ , pages 369–384, 2024. 

- [33] Christina Delimitrou and Christos Kozyrakis. Paragon: QoS-aware scheduling for heterogeneous datacenters. In _Proceedings of the 18th International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS-XVIII)_ , pages 77–88, 2013. 

- [34] Christina Delimitrou and Christos Kozyrakis. Quasar: resource-efficient and QoS-aware cluster management. In _Proceedings of the 19th International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS-XIX)_ , pages 127–144, 2014. 

- [35] Christina Delimitrou, Daniel Sánchez, and Christos Kozyrakis. Tarcil: reconciling scheduling speed and quality in large shared clusters. In _Proceedings of the 2015 ACM Symposium on Cloud Computing (SOCC)_ , pages 97–110, 2015. 

- [36] Dong Du, Qingyuan Liu, Xueqiang Jiang, Yubin Xia, Binyu Zang, and Haibo Chen. Serverless computing on heterogeneous computers. In _Proceedings of the 27th International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS-XXVII)_ , pages 797–813, 2022. 

- [37] Joshua Fried, Gohar Irfan Chaudhry, Enrique Saurez, Esha Choukse, Íñigo Goiri, Sameh Elnikety, Rodrigo Fonseca, and Adam Belay. Making Kernel Bypass Practical for the Cloud with Junction. In _Proceedings of the 21st Symposium on Networked Systems Design and Implementation (NSDI)_ , pages 55–73, 2024. 

- [38] Yao Fu, Leyang Xue, Yeqi Huang, Andrei-Octavian Brabete, Dmitrii Ustiugov, Yuvraj Patel, and Luo Mai. ServerlessLLM: Low-Latency Serverless Inference for Large Language Models. In _Proceedings of the 18th Symposium on Operating System Design and Implementation (OSDI)_ , pages 135–153, 2024. 

- [39] Alexander Fuerst, Abdul Rehman, and Prateek Sharma. Ilúvatar: A Fast Control Plane for Serverless Computing. In _Proceedings of the 32nd International Symposium on_ 

_High-Performance Parallel and Distributed Computing (HPDC)_ , pages 267–280, 2023. 

- [40] Alexander Fuerst and Prateek Sharma. FaasCache: keeping serverless computing alive with greedy-dual caching. In _Proceedings of the 26th International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS-XXVI)_ , pages 386–400, 2021. 

- [41] Ionel Gog, Malte Schwarzkopf, Adam Gleave, Robert N. M. Watson, and Steven Hand. Firmament: Fast, Centralized Cluster Scheduling at Scale. In _Proceedings of the 12th Symposium on Operating System Design and Implementation (OSDI)_ , pages 99–115, 2016. 

- [42] Benjamin Hindman, Andy Konwinski, Matei Zaharia, Ali Ghodsi, Anthony D. Joseph, Randy H. Katz, Scott Shenker, and Ion Stoica. Mesos: A Platform for FineGrained Resource Sharing in the Data Center. In _Proceedings of the 8th Symposium on Networked Systems Design and Implementation (NSDI)_ , 2011. 

- [43] Jialiang Huang, Mingxing Zhang, Teng Ma, Zheng Liu, Sixing Lin, Kang Chen, Jinlei Jiang, Xia Liao, Yingdi Shan, Ning Zhang, Mengting Lu, Tao Ma, Haifeng Gong, and YongWei Wu. TrEnv: Transparently Share Serverless Execution Environments Across Different Functions and Nodes. In _Proceedings of the 30th ACM Symposium on Operating Systems Principles (SOSP)_ , pages 421–437, 2024. 

- [44] Michael Isard, Vijayan Prabhakaran, Jon Currey, Udi Wieder, Kunal Talwar, and Andrew V. Goldberg. Quincy: fair scheduling for distributed computing clusters. In _Proceedings of the 22nd ACM Symposium on Operating Systems Principles (SOSP)_ , pages 261–276, 2009. 

- [45] Shyam Jesalpura, Dmitrii Ustiugov, Michal Baczun, Bora A. Malper, Rustem Feyzkhanov, Edouard Bugnion, Marios Kogias, and Boris Grot. Shattering the Ephemeral Storage Cost Barrier for Data-Intensive Serverless Workflows. In _The 3rd Workshop on SErverless Systems, Applications and MEthodologies (SESAME’ 25)_ , pages 33–41, 2025. 

- [46] Zhipeng Jia and Emmett Witchel. Nightcore: efficient and scalable serverless computing for latency-sensitive, interactive microservices. In _Proceedings of the 26th International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOSXXVI)_ , pages 152–166, 2021. 

- [47] Artjom Joosen, Ahmed Hassan, Martin Asenov, Rajkarn Singh, Luke Nicholas Darlow, Jianfeng Wang, and Adam Barker. How Does It Function?: Characterizing Long-term Trends in Production Serverless Workloads. 

14 

In _Proceedings of the 2023 ACM Symposium on Cloud Computing (SOCC)_ , pages 443–458, 2023. 

- [48] Artjom Joosen, Ahmed Hassan, Martin Asenov, Rajkarn Singh, Luke Nicholas Darlow, Jianfeng Wang, Qiwen Deng, and Adam Barker. Serverless Cold Starts and Where to Find Them. In _Proceedings of the 2025 EuroSys Conference_ , pages 938–953, 2025. 

- [49] Ana Klimovic, Yawen Wang, Patrick Stuedi, Animesh Trivedi, Jonas Pfefferle, and Christos Kozyrakis. Pocket: Elastic Ephemeral Storage for Serverless Analytics. In _Proceedings of the 13th Symposium on Operating System Design and Implementation (OSDI)_ , pages 427–444, 2018. 

- [50] Peter Kraft, Qian Li, Kostis Kaffes, Athinagoras Skiadopoulos, Deeptaanshu Kumar, Danny Cho, Jason Li, Robert Redmond, Nathan W. Weckwerth, Brian S. Xia, Peter Bailis, Michael J. Cafarella, Goetz Graefe, Jeremy Kepner, Christos Kozyrakis, Michael Stonebraker, Lalith Suresh, Xiangyao Yu, and Matei Zaharia. Apiary: A dbms-backed transactional function-as-a-service framework. _CoRR_ , abs/2208.13068, 2022. 

- [51] Tom Kuchler, Pinghe Li, Yazhuo Zhang, Lazar Cvetkovic, Boris Goranov, Tobias Stocker, Leon Thomm, Simone Kalbermatter, Tim Notter, Andrea Lattuada, and Ana Klimovic. Unlocking True Elasticity for the Cloud-Native Era with Dandelion. In _Proceedings of the 31st ACM Symposium on Operating Systems Principles (SOSP)_ , pages 944–961, 2025. 

- [52] Guowei Liu, Laiping Zhao, Yiming Li, Zhaolin Duan, Sheng Chen, Yitao Hu, Zhiyuan Su, and Wenyu Qu. FUYAO: DPU-enabled Direct Data Transfer for Serverless Computing. In _ASPLOS (3)_ , pages 431–447, 2024. 

- [53] Qingyuan Liu, Dong Du, Yubin Xia, Ping Zhang, and Haibo Chen. The Gap Between Serverless Research and Real-world Systems. In _Proceedings of the 2023 ACM Symposium on Cloud Computing (SOCC)_ , pages 475–485, 2023. 

- [54] Qingyuan Liu, Yanning Yang, Dong Du, Yubin Xia, Ping Zhang, Jia Feng, James R. Larus, and Haibo Chen. Harmonizing Efficiency and Practicability: Optimizing Resource Utilization in Serverless Computing with Jiagu. In _Proceedings of the 2024 USENIX Annual Technical Conference (ATC)_ , pages 1–17, 2024. 

- [55] Ashraf Mahgoub, Karthick Shankar, Subrata Mitra, Ana Klimovic, Somali Chaterji, and Saurabh Bagchi. SONIC: Application-aware Data Passing for Chained Serverless Applications. In _Proceedings of the 2021 USENIX Annual Technical Conference (ATC)_ , pages 285–301, 2021. 

- [56] Microsoft Azure. Azure Public Dataset: Azure LLM Inference Trace, 2023. Available at https: //github.com/Azure/AzurePublicDataset/blob/ master/AzureLLMInferenceDataset2023.md. 

- [57] Viyom Mittal, Shixiong Qi, Ratnadeep Bhattacharya, Xiaosu Lyu, Junfeng Li, Sameer G. Kulkarni, Dan Li, Jinho Hwang, K. K. Ramakrishnan, and Timothy Wood. Mu: An Efficient, Fair and Responsive Serverless Framework for Resource-Constrained Edge Clouds. In _Proceedings of the 2021 ACM Symposium on Cloud Computing (SOCC)_ , pages 168–181, 2021. 

- [58] Djob Mvondo, Mathieu Bacou, Kevin Nguetchouang, Lucien Ngale, Stéphane Pouget, Josiane Kouam, Renaud Lachaize, Jinho Hwang, Tim Wood, Daniel Hagimont, Noël De Palma, Bernabé Batchakui, and Alain Tchana. OFC: an opportunistic caching system for FaaS platforms. In _Proceedings of the 2021 EuroSys Conference_ , pages 228–244, 2021. 

- [59] Kay Ousterhout, Patrick Wendell, Matei Zaharia, and Ion Stoica. Sparrow: distributed, low latency scheduling. In _Proceedings of the 24th ACM Symposium on Operating Systems Principles (SOSP)_ , pages 69–84, 2013. 

- [60] Shixiong Qi, Leslie Monis, Ziteng Zeng, Ian-Chin Wang, and K. K. Ramakrishnan. SPRIGHT: extracting the server from serverless computing! high-performance eBPF-based event-driven, shared-memory processing. In _Proceedings of the ACM SIGCOMM 2022 Conference_ , pages 780–794, 2022. 

- [61] Francisco Romero, Gohar Irfan Chaudhry, Iñigo Goiri, Pragna Gopa, Paul Batum, Neeraja J. Yadwadkar, Rodrigo Fonseca, Christos Kozyrakis, and Ricardo Bianchini. Faa$T: A Transparent Auto-Scaling Cache for Serverless Applications. In _Proceedings of the 2021 ACM Symposium on Cloud Computing (SOCC)_ , pages 122–137, 2021. 

- [62] Rohan Basu Roy, Tirthak Patel, and Devesh Tiwari. IceBreaker: warming serverless functions better with heterogeneity. In _Proceedings of the 27th International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS-XXVII)_ , pages 753–767, 2022. 

- [63] Zhenyuan Ruan, Shihang Li, Kaiyan Fan, Seo Jin Park, Marcos K. Aguilera, Adam Belay, and Malte Schwarzkopf. Quicksand: Harnessing Stranded Datacenter Resources with Granular Computing. In _Proceedings of the 22nd Symposium on Networked Systems Design and Implementation (NSDI)_ , pages 147–165, 2025. 

- [64] David Schall, Artemiy Margaritov, Dmitrii Ustiugov, Andreas Sandberg, and Boris Grot. Lukewarm serverless functions: characterization and optimization. In 

15 

_Proceedings of the 49th International Symposium on Computer Architecture (ISCA)_ , pages 757–770, 2022. 

- [65] Malte Schwarzkopf, Andy Konwinski, Michael AbdEl-Malek, and John Wilkes. Omega: flexible, scalable schedulers for large compute clusters. In _Proceedings of the 2013 EuroSys Conference_ , pages 351–364, 2013. 

- [66] Carlos Segarra, Simon Shillaker, Guo Li, Eleftheria Mappoura, Rodrigo Bruno, Lluís Vilanova, and Peter R. Pietzuch. GRANNY: Granular Management of Compute-Intensive Applications in the Cloud. In _Proceedings of the 22nd Symposium on Networked Systems Design and Implementation (NSDI)_ , pages 205–218, 2025. 

- [67] Mohammad Shahrad, Rodrigo Fonseca, Iñigo Goiri, Gohar Irfan Chaudhry, Paul Batum, Jason Cooke, Eduardo Laureano, Colby Tresness, Mark Russinovich, and Ricardo Bianchini. Serverless in the Wild: Characterizing and Optimizing the Serverless Workload at a Large Cloud Provider. In _Proceedings of the 2020 USENIX Annual Technical Conference (ATC)_ , pages 205–218, 2020. 

- [68] Arjun Singhvi, Arjun Balasubramanian, Kevin Houck, Mohammed Danish Shaikh, Shivaram Venkataraman, and Aditya Akella. Atoll: A Scalable Low-Latency Serverless Platform. In _Proceedings of the 2021 ACM Symposium on Cloud Computing (SOCC)_ , pages 138– 152, 2021. 

- [69] Ariel Szekely, Adam Belay, Robert Morris, and M. Frans Kaashoek. Unifying serverless and microservice workloads with SigmaOS. In _Proceedings of the 30th ACM Symposium on Operating Systems Principles (SOSP)_ , pages 385–402, 2024. 

- [70] Muhammad Tirmazi, Adam Barker, Nan Deng, Md E. Haque, Zhijing Gene Qin, Steven Hand, Mor HarcholBalter, and John Wilkes. Borg: the next generation. In _Proceedings of the 2020 EuroSys Conference_ , pages 30:1–30:14, 2020. 

- [71] Dmitrii Ustiugov, Theodor Amariucai, and Boris Grot. Analyzing Tail Latency in Serverless Clouds with STeLLAR. In _Proceedings of the 2021 IEEE International Symposium on Workload Characterization (IISWC)_ , pages 51–62, 2021. 

   - [73] Dmitrii Ustiugov, Plamen Petrov, Marios Kogias, Edouard Bugnion, and Boris Grot. Benchmarking, analysis, and optimization of serverless function snapshots. In _Proceedings of the 26th International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS-XXVI)_ , pages 559–572, 2021. 

   - [74] Vinod Kumar Vavilapalli, Arun C. Murthy, Chris Douglas, Sharad Agarwal, Mahadev Konar, Robert Evans, Thomas Graves, Jason Lowe, Hitesh Shah, Siddharth Seth, Bikas Saha, Carlo Curino, Owen O’Malley, Sanjay Radia, Benjamin C. Reed, and Eric Baldeschwieler. Apache Hadoop YARN: yet another resource negotiator. In _Proceedings of the 2013 ACM Symposium on Cloud Computing (SOCC)_ , pages 5:1–5:16, 2013. 

   - [75] Abhishek Verma, Luis Pedrosa, Madhukar Korupolu, David Oppenheimer, Eric Tune, and John Wilkes. Largescale cluster management at Google with Borg. In _Proceedings of the 2015 EuroSys Conference_ , pages 18:1– 18:17, 2015. 

   - [76] Minchen Yu, Tingjia Cao, Wei Wang, and Ruichuan Chen. Following the Data, Not the Function: Rethinking Function Orchestration in Serverless Computing. In _Proceedings of the 20th Symposium on Networked Systems Design and Implementation (NSDI)_ , pages 1489–1504, 2023. 

   - [77] Shaoxun Zeng, Minhui Xie, Shiwei Gao, Youmin Chen, and Youyou Lu. Medusa: Accelerating Serverless LLM Inference with Materialization. In _ASPLOS (1)_ , pages 653–668, 2025. 

   - [78] Jie Zhang, Chen Jin, Yuqi Huang, Li Yi, Yu Ding, and Fei Guo. KOLE: breaking the scalability barrier for managing far edge nodes in cloud. In _Proceedings of the 2022 ACM Symposium on Cloud Computing (SOCC)_ , pages 196–209, 2022. 

   - [79] Yanqi Zhang, Iñigo Goiri, Gohar Irfan Chaudhry, Rodrigo Fonseca, Sameh Elnikety, Christina Delimitrou, and Ricardo Bianchini. Faster and Cheaper Serverless Computing on Harvested Resources. In _Proceedings of the 28th ACM Symposium on Operating Systems Principles (SOSP)_ , pages 724–739, 2021. 

- [72] Dmitrii Ustiugov, Dohyun Park, Lazar Cvetkovic, Mihajlo Djokic, Hongyu Hè, Boris Grot, and Ana Klimovic. Enabling In-Vitro Serverless Systems Research. In _Proceedings of the 4th Workshop on Resource Disaggregation and Serverless (WORDS)_ , pages 1–7, 2023. 

16 

