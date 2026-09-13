---
# --- bibliographic record ---
entry_type: article
title: "AutoScale"
authors:
  - "Anshul Gandhi"
  - "Mor Harchol-Balter"
  - "Ram Raghunathan"
  - "Michael A. Kozuch"
year: 2012
venue: "ACM Transactions on Computer Systems"
volume: "30"
issue: "4"
pages: "1-26"
publisher: "Association for Computing Machinery (ACM)"
doi: "10.1145/2382553.2382556"
arxiv: ""
url: "https://doi.org/10.1145/2382553.2382556"

# --- archive record ---
source_pdf: gandhi-autoscale-capacity-management-2012.pdf
source_sha256: 7b48eb54bb9da7a372335f66498d9864e6e42cfc43755b10721d063cbb60146b
pdf_pages: 26
converted: 2026-09-13
record_source: crossref
key_insight: "Queueing-signal (requests-in-system) capacity inference; sizing just above need + conservative scale-down beats prediction-based and over-provisioning policies on unpredictable load"
first_page: "14 AutoScale: Dynamic, Robust Capacity Management for Multi-Tier Data Centers ANSHUL GANDHI, MOR HARCHOL-BALTER, and RAM RAGHUNATHAN, Carnegie Mellon University MICHAEL A. KOZUCH, Intel Labs Energy co"
---
**14** 

# **AutoScale: Dynamic, Robust Capacity Management for Multi-Tier Data Centers** 

## ANSHUL GANDHI, MOR HARCHOL-BALTER, and RAM RAGHUNATHAN, 

Carnegie Mellon University MICHAEL A. KOZUCH, Intel Labs 

Energy costs for data centers continue to rise, already exceeding $15 billion yearly. Sadly much of this power is wasted. Servers are only busy 10–30% of the time on average, but they are often left on, while idle, utilizing 60% or more of peak power when in the idle state. 

We introduce a dynamic capacity management policy, _AutoScale_ , that greatly reduces the number of servers needed in data centers driven by unpredictable, time-varying load, while meeting response time SLAs. _AutoScale_ scales the data center capacity, adding or removing servers as needed. _AutoScale_ has two key features: (i) it autonomically maintains just the right amount of spare capacity to handle bursts in the request rate; and (ii) it is robust not just to changes in the request rate of real-world traces, but also request size and server efficiency. 

We evaluate our dynamic capacity management approach via implementation on a 38-server multi-tier data center, serving a web site of the type seen in Facebook or Amazon, with a key-value store workload. We demonstrate that AutoScale vastly improves upon existing dynamic capacity management policies with respect to meeting SLAs and robustness. 

Categories and Subject Descriptors: C.4 [ **Performance of Systems** ]: _reliability, availability, and serviceability_ 

General Terms: Design, Management, Performance 

Additional Key Words and Phrases: Data centers, power management, resource provisioning 

#### **ACM Reference Format:** 

Gandhi, A., Harchol-Balter, M., Raghunathan, R., and Kozuch, M. A. 2012. AutoScale: Dynamic, robust capacity management for multi-tier data centers. ACM Trans. Comput. Syst. 30, 4, Article 14 (November 2012), 26 pages. DOI = 10.1145/2382553.2382556 http://doi.acm.org/10.1145/2382553.2382556 

### **1. INTRODUCTION** 

Many networked services, such as Facebook and Amazon, are provided by multi-tier data center infrastructures. A primary goal for these applications is to provide good 

This work is supported by the National Science Foundation, under CSR Grant 1116282, and by a grant from the Intel Science and Technology Center on Cloud Computing. 

Some of the work in this article is based on a recent publication by the authors: “Are sleep states effective in data centers?”, Anshul Gandhi, Mor Harchol-Balter, and Michael Kozuch, International Green Computing Conference, 2012. 

Authors’ addresses: A. Gandhi, M. Harchol-Balter, and R. Raghunathan, Carnegie Mellon University, 5000 Forbes Avenue, Pittsburgh, PA 15213; email: anshulg@cs.cmu.edu, harchol@andrew.cmu.edu, rraghuna@andrew.cmu.edu; M. A. Kozuch, Intel Labs Pittsburgh, 4720 Forbes Avenue, Suite 410, Pittsburgh, PA 15213; email: michael.a.kozuch@intel.com. 

Permission to make digital or hard copies of part or all of this work for personal or classroom use is granted without fee provided that copies are not made or distributed for profit or commercial advantage and that copies show this notice on the first page or initial screen of a display along with the full citation. Copyrights for components of this work owned by others than ACM must be honored. Abstracting with credit is permitted. To copy otherwise, to republish, to post on servers, to redistribute to lists, or to use any component of this work in other works requires prior specific permission and/or a fee. Permission may be requested from Publications Dept., ACM, Inc., 2 Penn Plaza, Suite 701, New York, NY 10121-0701, USA, fax +1 (212) 869-0481, or permissions@acm.org. _⃝_ c 2012 ACM 0734-2071/2012/11-ART14 $15.00 DOI 10.1145/2382553.2382556 http://doi.acm.org/10.1145/2382553.2382556 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

A. Gandhi et al. 

14:2 

response time to users; these response time targets typically translate to some response time Service Level Agreements (SLAs). In an effort to meet these SLAs, data center operators typically over-provision the number of servers to meet their estimate of peak load. These servers are left “always on,” leading to only 10–30% server utilization [Armbrust et al. 2009; Barroso and H¨olzle 2007]. In fact, Snyder [2010] reports that the average data center server utilization is only 18% despite years of deploying virtualization aimed at improving server utilization. Low utilization is problematic because servers that are on, while idle, still utilize 60% or more of peak power. 

To reduce wasted power, we consider intelligent _dynamic capacity management_ , which aims to match the number of active servers with the current load, in situations where future load is unpredictable. Servers that become idle when load is low could be either turned off, saving power, or loaned out to some other application, or simply released to a cloud computing platform, thus saving money. Fortunately, the bulk of the servers in a multi-tier data center are application servers, which are stateless, and are thus easy to turn off or give away–for example, one reported ratio of application servers to data servers is 5:1 [Facebook 2011]. We therefore focus our attention on dynamic capacity management of these front-end application servers. 

Part of what makes dynamic capacity management difficult is the setup cost of getting servers back on/ready. For example, in our lab the setup time for turning on an application server is 260 seconds, during which time power is consumed at the peak rate of 200W. Sadly, little has been done to reduce the setup overhead for servers. In particular, sleep states, which are prevalent in mobile devices, have been very slow to enter the server market. Even if future hardware reduces the setup time, there may still be software imposed setup times due to software updates which occurred when the server was unavailable [Facebook 2011]. Likewise, the setup cost needed to create virtual machines (VMs) can range anywhere from 30s–1 minute if the VMs are locally created (based on our measurements using kvm [Kivity 2007]) or 10–15 minutes if the VMs are obtained from a cloud computing platform (see, e.g., Amazon Inc. [2008]). All these numbers are extremely high, when compared with the typical SLA of half a second. 

The goal of dynamic capacity management is to scale capacity with unpredictably changing load in the face of high setup costs. While there has been much prior work on this problem, all of it has only focussed on one aspect of changes in load, namely, fluctuations in request rate. This is already a difficult problem, given high setup costs, and has resulted in many policies, including reactive approaches [Elnozahy et al. 2002; Fan et al. 2007; Leite et al. 2010; Nathuji et al. 2010; Wang and Chen 2008; Wood et al. 2007] that aim to react to the current request rate, predictive approaches [Castellanos et al. 2005; Horvath and Skadron 2008; Krioukov et al. 2010; Qin and Wang 2007] that aim to predict the future request rate, and mixed reactivepredictive approaches [Bobroff et al. 2007; Chen et al. 2005, 2008; Gandhi et al. 2011a; Gmach et al. 2008; Urgaonkar and Chandra 2005; Urgaonkar et al. 2005]. However, in reality there are many other ways in which load can change. For example, _request size_ (work associated with each request) can change, if new features or security checks are added to the application. As a second example, _server efficiency_ can change, if any abnormalities occur in the system, such as internal service disruptions, slow networks, or maintenance cycles. These other types of load fluctuations are all too common in data centers, and have not been addressed by prior work in dynamic capacity management. 

We propose a new approach to dynamic capacity management, which we call _AutoScale_ . To describe _AutoScale_ , we decompose it into two parts: _AutoScale_ -- (see Section 3.5), which is a precursor to _AutoScale_ and handles only the narrower case of 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

AutoScale: Dynamic, Robust Capacity Management for Multi-Tier Data Center 

14:3 

unpredictable changes in request rate, and the full _AutoScale_ policy (see Section 4.3), which builds upon _AutoScale_ -- to handle all forms of changes in load. 

While _AutoScale_ -- addresses a problem that many others have looked at, it does so in a very different way. Whereas prior approaches aim at predicting the future request rate and scaling _up_ the number of servers to meet this predicted rate, which is clearly difficult to do when request rate is, by definition, unpredictable, _AutoScale_ -- does not attempt to predict future request rate. Instead, _AutoScale_ -- demonstrates that it is possible to achieve SLAs for real-world workloads by simply being conservative in scaling _down_ the number of servers: not turning servers off recklessly. One might think that this same effect could be achieved by leaving a fixed buffer of, say, 20% extra servers on at all times. However, the extra capacity (20% in the above example) should _change_ depending on the current load. _AutoScale_ -- does just this – it maintains just the right number of servers in the on state at every point in time. This results in much lower power/resource consumption. In Section 3.5, we evaluate _AutoScale_ -- on a suite of six different real-world traces, comparing it against five different capacity management policies commonly used in the literature. We demonstrate that in all cases, _AutoScale_ -- significantly outperforms other policies, meeting response time SLAs while greatly reducing the number of servers needed, as shown in Table III. 

To fully investigate the applicability of _AutoScale_ --, we experiment with multiple setup times ranging from 260 seconds all the way down to 20 seconds in Section 3.7 and with multiple server idle power consumption values ranging from 140 Watts all the way down to 0 Watts in Section 3.8. Our results indicate that _AutoScale_ -- can provide significant benefits across the entire spectrum of setup times and idle power, as shown in Figures 9 and 10. 

To handle a broader spectrum of possible changes in load, including unpredictable changes in the request size and server efficiency, we introduce the _AutoScale_ policy in Section 4.3. While prior approaches to dynamic capacity management of multi-tier applications react only to changes in the request rate, _AutoScale_ uses a novel capacity inference algorithm, which allows it to determine the appropriate capacity regardless of the source of the change in load. Importantly, _AutoScale_ achieves this _without_ requiring any knowledge of the request rate or the request size or the server efficiency, as shown in Tables V, VI, and VII. 

To evaluate the effectiveness of _AutoScale_ , we build a three-tier testbed consisting of 38 servers that uses a key-value based workload, involving multiple interleavings of CPU and I/O within each request. While our implementation involves physically turning servers on and off, one could instead imagine that any idle server that is turned off is instead “given away”, and there is a setup time to get the server back. To understand the benefits of _AutoScale_ , we evaluate all policies on three metrics: **T95** , the 95th percentile of response time, which represents our SLA; **Pavg** , the average power usage; and **Navg** , the average capacity, or number of servers in use (including those idle and in setup). Our goal is to meet the response time SLA, while keeping **Pavg** and **Navg** as low as possible. The drop in **Pavg** shows the possible savings in power by turning off servers, while the drop in **Navg** represents the potential capacity/servers available to be given away to other applications or to be released back to the cloud so as to save on rental costs. 

This article makes the following contributions. 

- We overturn the common wisdom that says that capacity provisioning requires “knowing the future load and planning for it,” which is at the heart of existing predictive capacity management policies. Such predictions are simply not possible when workloads are unpredictable, and, we furthermore show they are unnecessary, at least for the range of variability in our workloads. We demonstrate that 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

A. Gandhi et al. 

14:4 



Fig. 1. Our experimental testbed. 

simply provisioning carefully and not turning servers off recklessly achieves better performance than existing policies that are based on predicting current load or over-provisioning to account for possible future load. 

— We introduce our capacity inference algorithm, which allows us to determine the appropriate capacity at any point of time in response to changes in request rate, request size and/or server efficiency, without any knowledge of these quantities (see Section 4.3). We demonstrate that _AutoScale_ , via the capacity inference algorithm, is robust to all forms of changes in load, including unpredictable changes in request size and unpredictable degradations in server speeds, within the range of our traces. In fact, for our traces, _AutoScale_ is robust to even a 4-fold increase in request size. To the best of our knowledge, _AutoScale_ is the first policy to exhibit these forms of robustness for multi-tier applications. As shown in Tables V, VI, and VII, other policies are simply not comparable on this front. 

### **2. EXPERIMENTAL SETUP** 

### **2.1. Our Experimental Testbed** 

Figure 1 illustrates our data center testbed, consisting of 38 Intel Xeon servers, each equipped with two quad-core 2.26 GHz processors. We employ one of these servers as the front-end load generator running httperf [Mosberger and Jin 1998] and another server as the front-end load balancer running Apache, which distributes requests from the load generator to the application servers. We modify Apache on the load balancer to also act as the capacity manager, which is responsible for turning servers on and off. Another server is used to store the entire data set, a billion key-value pairs, on a database. 

Seven servers are used as memcached servers, each with 4GB of memory for caching. The remaining 28 servers are employed as application servers, which parse the incoming php requests and collect the required data from the back-end memcached servers. Our ratio of application servers to memcached servers is consistent with the typical ratio of 5:1 [Facebook 2011]. 

We employ capacity management on the stateless application servers only, as they maintain no volatile state. Stateless servers are common among today’s application platforms, such as those used by Facebook [Facebook 2011], Amazon [DeCandia et al. 2007] and Windows Live Messenger [Chen et al. 2008]. We use the SNMP communication protocol to remotely turn application servers on and off via the power distribution unit (PDU). We monitor the power consumption of individual servers by reading the 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

AutoScale: Dynamic, Robust Capacity Management for Multi-Tier Data Center 

14:5 

power values off of the PDU. The idle power consumption for our servers is about 140W (with C-states enabled) and the average power consumption for our servers when they are busy or in setup is about 200W. 

In our experiments, we observed the setup time for the servers to be about 260 seconds. However, we also examine the effects of lower setup times that could either be a result of using sleep states (which are prevalent in laptops and desktop machines, but are not well supported for server architectures yet), or using virtualization to quickly bring up virtual machines. We replicate this effect by not routing requests to a server if it is marked for sleep, and by replacing its power consumption values with 0W. When the server is marked for setup, we wait for the setup time before sending requests to the server, and replace its power consumption values during the setup time with 200W. 

### **2.2. Workload** 

We design a key-value workload to model realistic multi-tier applications such as the social networking site, Facebook, or e-commerce companies like Amazon [DeCandia et al. 2007]. Each generated request (or job) is a php script that runs on the application server. A request begins when the application server requests a value for a key from the memcached servers. The memcached servers provide the value, which itself is a collection of new keys. The application server then again requests values for these new keys from the memcached servers. This process can continue iteratively. In our experiments, we set the number of iterations to correspond to an average of roughly 3,000 key requests per job, which translates to a mean request size of approximately 120 ms, assuming no resource contention. The request size distribution is highly variable, with the largest request being roughly 20 times the size of the smallest request. 

We can also vary the distribution of key requests by the application server. In this paper we use the Zipf [Newman 2005] distribution, whereby the probability of generating a particular key varies inversely as a power of that key. To minimize the effects of cache misses in the memcached layer (which could result in an unpredictable fraction of the requests violating the **T95** SLA), we tune the parameters of the Zipf distribution so that only a negligible fraction of requests miss in the memcached layer. 

### **2.3. Trace-Based Arrivals** 

We use a variety of arrival traces to generate the request rate of jobs in our experiments, most of which are drawn from real-world traces. Table I describes these traces. In our experiments, the seven memcached servers can together handle at most 800 job requests per second, which corresponds to roughly 300,000 key requests per second at each memcached server. Thus, we scale the arrival traces such that the maximum request rate into the system is 800 req/s. Further, we scale the duration of the traces to 2 hours. We evaluate our policies against the full set of traces (see Table III for results). 

### **3. RESULTS: CHANGING REQUEST RATES** 

This section and the next both involve implementation and performance evaluation of a range of capacity management policies. Each policy will be evaluated against the six traces described in Table I. We will present detailed results for the Dual phase trace and show summary results for all traces in Table III. The Dual phase trace is chosen because it is quite bursty and also represents the diurnal nature of typical data center traffic, whereby the request rate is low for a part of the day (usually the night time) and is high for the rest (day time). The goal throughout will be to meet 95%ile 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

A. Gandhi et al. 

14:6 

Table I. Description of the Traces We Use for Experiments 













guarantees of **T95** = 400 − 500 ms<sup>1</sup> , while minimizing the average power consumed by the application servers, **Pavg** , or the average number of application servers used, **Navg** . Note that **Pavg** largely scales with **Navg** . 

For capacity management, we want to choose the number of servers at time _t_ , _k_ ( _t_ ), such that we meet a 95 percentile response time goal of 400 − 500 ms. Figure 2 shows measured 95 percentile response time at a single server versus request rate. According to this figure, for example, to meet a 95 percentile goal of 400 ms, we require the request rate to a single server to be no more than _r_ = 60 req/s. Hence, if the total request rate into the data center at some time _t_ is say, _R_ ( _t_ ) = 300 req/s, we know that we need at least _k_ = ⌈300 _/r_ ⌉ = 5 servers to ensure our 95 percentile SLA. 

### **3.1. AlwaysOn** 

The _AlwaysOn_ policy [Chen et al. 2008; Horvath and Skadron 2008; Verma et al. 2009] is important because this is what is currently deployed by most of the industry. The 

> 1It would be equally easy to use 90%ile guarantees or 99%ile guarantees. Likewise, we could easily have aimed for 300ms or 1 second response times rather than 500ms. Our choice of SLA is motivated by recent studies [DeCandia et al. 2007; Krioukov et al. 2010; Meisner et al. 2011; Urgaonkar and Chandra 2005] that indicate that 95 percentile guarantees of hundreds of milliseconds are typical. 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

14:7 

AutoScale: Dynamic, Robust Capacity Management for Multi-Tier Data Center 





Fig. 2. A single server can optimally handle 60 req/s. 



<!-- Start of picture text -->
Fig. 3. AlwaysOn .<br><!-- End of picture text -->

policy selects a fixed number of servers, _k_ , to handle the peak request rate and always leaves those servers on. In our case, to meet the 95 percentile SLA of 400ms, we set _k_ = ⌈ _Rpeak/_ 60⌉, where _Rpeak_ = 800 req/s denotes the peak request rate into the system. Thus, _k_ is fixed at ⌈800 _/_ 60⌉ = 14. 

Realistically, one doesn’t know _Rpeak_ , and it is common to overestimate _Rpeak_ by a factor of 2 (see, e.g., [Krioukov et al. 2010]). In this article, we empower _AlwaysOn_ , by assuming that _Rpeak_ is known in advance. 

Figure 3 shows the performance of _AlwaysOn_ . The solid line shows _kideal_ , the _ideal_ number of servers/capacity which should be on at any given time, as given by _k_ ( _t_ ) = ⌈ _R_ ( _t_ ) _/_ 60⌉. Circles are used to show _kbusy_ + _idle_ , the number of servers which are actually on, and crosses show _kbusy_ + _idle_ + _setup_ , the actual number of servers that are on or in setup. For _AlwaysOn_ , the circles and crosses lie on top of each other since servers are never in setup. Observe that **Navg** = ⌈<sup><u>800</u></sup> 60<sup>⌉=14for</sup><sup>_AlwaysOn_,while</sup><sup>**Pavg**=2323</sup><sup>_W_,with</sup> similar values for the different traces in Table III. 

### **3.2. Reactive** 

The _Reactive_ policy (see, e.g., Urgaonkar and Chandra [2005]) reacts to the current request rate, attempting to keep exactly ⌈ _R_ ( _t_ ) _/_ 60⌉ servers on at time _t_ , in accordance with the solid line. However, because of the setup time of 260s, _Reactive_ lags in turning servers on. In our implementation of _Reactive_ , we sample the request rate every 20 seconds, adjusting the number of servers as needed. 

Figure 4(a) shows the performance of _Reactive_ . By reacting to current request rate and adjusting the capacity accordingly, _Reactive_ is able to bring down **Pavg** and **Navg** by as much as a factor of two or more, when compared with _AlwaysOn_ . This is a huge win. Unfortunately, the response time SLA is almost never met and is typically exceeded by a factor of at least 10–20 (as in Figure 4(a)), or even by a factor of 100 (see Table III). 

### **3.3. Reactive with Extra Capacity** 

One might think the response times under _Reactive_ would improve a lot by just adding some _x_ % extra capacity at all times. This _x_ % extra capacity can be achieved by running _Reactive_ with a different _r_ setting. Unfortunately, for this trace, it turns out that to bring **T95** down to our desired SLA, we need 100% extra capacity at all times, which corresponds to setting _r_ = 30. This brings **T95** down to 487 ms, but causes power to jump up to the levels of _AlwaysOn_ , as illustrated in Figure 4(b). It is even more problematic that each of our six traces in Table I requires a different _x_ % extra capacity to achieve 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

A. Gandhi et al. 

14:8 





Fig. 4. (a) _Reactive_ and (b) _Reactive_ with extra capacity. 

the desired SLA (with _x_ % typically ranging from 50% to 200%), rendering such a policy impractical. 

### **3.4. Predictive** 

Predictive policies attempt to predict the request rate 260 seconds from now. This section describes two policies that were used in many papers [Bod´ık et al. 2009; Grunwald et al. 2000; Pering et al. 1998; Verma et al. 2009] and were found to be the most powerful by Krioukov et al. [2010]. 

_Predictive - Moving Window Average (MWA)._ In the _MWA_ policy, we consider a “window” of some duration (say, 10 seconds). We average the request rates during that window to deduce the predicted rate during the 11th second. Then, we slide the window to include seconds 2 through 11, and average those values to deduce the predicted rate during the 12th second. We continue this process of sliding the window rightward until we have predicted the request rate at time 270 seconds, based on the initial 10 seconds window. 

If the estimated request rate at second 270 exceeds the current request rate, we determine the number of additional servers needed to meet the SLA (via the _k_ = ⌈ _R/r_ ⌉ formula) and turn these on at time 11, so that they will be ready to run at time 270. If the estimated request rate at second 270 is lower than the current request rate, we look at the maximum request rate, _M_ , during the interval from time 11 to time 270. If _M_ is lower than the current request rate, then we turn off as many servers as we can while meeting the SLA for request rate _M_ . Of course, the window size affects the performance of _MWA_ . _We empower_ MWA _by using the best window size for each trace._ 

Figure 5(a) shows that the performance of _Predictive MWA_ is very similar to what we saw for _Reactive_ : low **Pavg** and **Navg** values, beating _AlwaysOn_ by a factor of 2, but high **T95** values, typically exceeding the SLA by a factor of 10 to 20. 

_Predictive - Linear Regression (LR)._ The _LR_ policy is identical to _MWA_ except that, to estimate the request rate at time 270 seconds, we use linear regression to match the best linear fit to the values in the window. Then we extend our line out by 260 seconds to get a prediction of the request rate at time 270 seconds. 

The performance of _Predictive LR_ is worse than that of _Predictive MWA_ . Response times are still bad, but now capacity and power consumption can be bad as well. The problem, as illustrated in Figure 5(b), is that the linear slope fit used in _LR_ can end up overshooting the required capacity greatly. 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

AutoScale: Dynamic, Robust Capacity Management for Multi-Tier Data Center 

14:9 





Fig. 5. (a) _Predictive: MWA_ and (b) _Predictive: LR_ . 

Table II. The (In)sensitivity of _AutoScale_ --’s Performance to _twait_ 



<!-- Start of picture text -->
twait<br>60s 120s 260s<br>hhh Trace hhhhhhhh<br>T95 503ms 491ms 445ms<br>Dual phase<br>[nlanr 1995] Pavg 1,253W 1,297W 1,490W<br>Navg 7.0 7.2 8.8<br><!-- End of picture text -->

### **3.5. AutoScale** −− 

One might think that the poor performance of the dynamic capacity management policies we have seen so far stems from the fact that they are too slow to turn servers on when needed. However, an equally big concern is the fact that these policies are quick to turn servers _off_ when not needed, and hence do not have those servers available when load subsequently rises. This rashness is particularly problematic in the case of bursty workloads, such as those in Table I. 

_AutoScale_ -- addresses the problem of _scaling down_ capacity by being very conservative in turning servers off while doing nothing new with respect to turning servers on (the turning on algorithm is the same as in _Reactive_ ). We will show that by simply taking more care in turning servers off, _AutoScale_ -- is able to outperform all the prior dynamic capacity management policies we have seen with respect to meetings SLAs, while simultaneously keeping **Pavg** and **Navg** low. 

_When to Turn a Server Off?_ Under _AutoScale_ --, each server decides autonomously when to turn off. When a server goes idle, rather than turning off immediately, it sets a timer of duration _twait_ and sits in the idle state for _twait_ seconds. If a request arrives at the server during these _twait_ seconds, then the server goes back to the busy state (with zero setup cost); otherwise, the server is turned off. In our experiments for _AutoScale_ --, we use a _twait_ value of 120s. Table II shows that _AutoScale_ -- is largely insensitive to _twait_ in the range _twait_ = 60 _s_ to _twait_ = 260 _s_ . There is a slight increase in **Pavg** (and **Navg** ) and a slight decrease in **T95** when _twait_ increases, due to idle servers staying on longer. 

The idea of setting a timer before turning off an idle server has been proposed before (see, e.g., Kim and Rosing [2006], Lu et al. [2000], and Iyer and Druschel [2001]), however, only for a single server. For a multi-server system, _independently_ setting timers for each server can be inefficient, since we can end up with too many idle servers. Thus, we need a more coordinated approach for using timers in our multiserver system that takes routing into account, as explained here. 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

A. Gandhi et al. 

14:10 





Fig. 6. For a single server, packing factor, _p_ = 10. Fig. 7. _AutoScale_ --. 

_How to Route Jobs to Servers?._ Timers prevent the mistake of turning off a server just as a new arrival comes in. However, they can also waste power and capacity by leaving too many servers in the idle state. We’d basically like to keep only a small number of servers (just the _right_ number) in this idle state. 

To do this, we introduce a routing scheme that tends to concentrate jobs onto a small number of servers, so that the remaining (unneeded) servers will naturally “time out.” Our routing scheme uses an _index-packing_ idea, whereby all on servers are indexed from 1 to _n_ . Then, we send each request to the lowest numbered on server that currently has fewer than _p_ requests, where _p_ stands for _packing factor_ and denotes the maximum number of requests that a server can serve concurrently and meet its response time SLA. For example, in Figure 6, we see that to meet a 95%ile guarantee of 400 ms, the packing factor is _p_ = 10 (in general, the value of _p_ depends on the system in consideration). When all on servers are already packed with _p_ requests each, additional request arrivals are routed to servers via the join-the-shortest-queue routing. 

In comparison with all the other policies, _AutoScale_ -- hits the “sweet spot” of low **T95** as well as low **Pavg** and **Navg** . As seen from Table III, _AutoScale_ -- is close to the response time SLA in all traces except for the Big spike trace. Simultaneously, the mean power usage and capacity under _AutoScale_ -- is typically significantly better than _AlwaysOn_ , saving as much as a factor of two in power and capacity. 

Figure 7 illustrates how _AutoScale_ -- is able to achieve these performance results. Observe that the crosses and circles in _AutoScale_ -- form flat constant lines, instead of bouncing up and down, erratically, as in the earlier policies. This comes from a combination of the _twait_ timer and the index-based routing, which together keep the number of servers just slightly above what is needed, while also avoiding toggling the servers between on and off states when the load goes up and down. Comparing Figures 7 and 4(b), we see that the combination of timers and index-based routing is far more effective than using _Reactive_ with extra capacity, as in Section 3.3. 

### **3.6. Opt** 

As a yardstick for measuring the effectiveness of _AutoScale_ --, we define an optimal policy, _Opt_ , which behaves identically to _Reactive_ , but with a setup time of zero. Thus, as soon as the request rate changes, _Opt_ reacts by immediately adding or removing the required capacity, without having to wait for setup. 

Figure 8 shows that under _Opt_ , the number of servers on scales exactly with the incoming request load. _Opt_ easily meets the **T95** SLA, and consumes very little power and resources (servers). Note that while _Opt_ usually has a **T95** of about 320–350ms, 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

AutoScale: Dynamic, Robust Capacity Management for Multi-Tier Data Center 

14:11 

Table III. Comparison of All Policies. Setup Time = 260s Throughout 

|hhhhhhh<br>Trace|hhhh<br>Policy|_AlwaysOn_|_Reactive_|_Predictive_<br>_MWA_|_Predictive_<br>_LR_|_Opt_|_AutoScale_--|
|---|---|---|---|---|---|---|---|
|Sll i|**T95**|271ms|673ms|3,464ms|618ms|366ms|435ms|
|owy varyng<br>[ita 1998]|**Pavg**|2,205W|842W|825W|964W|788W|1,393W|
||**Navg**|14.0|4.1|4.1|4.9|4.0|5.8|
|ikl|**T95**|303ms|20,005ms|3,335ms|12,553ms|325ms|362ms|
|Qucy<br>varying|**Pavg**|2,476W|1,922W|2,065W|3,622W|1,531W|2,205W|
||**Navg**|14.0|10.1|10.6|22.1|8.2|15.1|
|Bi ik|**T95**|229ms|3,426ms|9,337ms|1,753ms|352ms|854ms|
|g spe<br>[nlanr 1995]|**Pavg**|2,260W|985W|998W|1,503W|845W|1,129W|
||**Navg**|14.0|4.9|4.9|8.1|4.5|6.6|
|Dl h|**T95**|291ms|11,003ms|7,740ms|2,544ms|320ms|491ms|
|ua pase<br>[nlanr 1995]|**Pavg**|2,323W|1,281W|1,276W|2,161W|1,132W|1,297W|
||**Navg**|14.0|6.2|6.3|11.8|5.9|7.2|
|Large|**T95**|289ms|4,227ms|13,399ms|20,631ms|321ms|474ms|
|variations<br>|**Pavg**|2,363W|1,391W|1,461W|2,576W|1,222W|1,642W|
|[nlanr 1995]|**Navg**|14.0|7.8|8.1|16.4|7.1|10.5|
|S i h|**T95**|377ms|_>_1 min|_>_1 min|661ms|446ms|463ms|
|teep tr pase<br>[sap 2011]|**Pavg**|2,263W|849W|1,287W|3,374W|1,004W|1,601W|
||**Navg**|14.0|5.2|7.2|20.5|5.1|8.0|





Fig. 8. _Opt_ . 

and thus it might seem like _Opt_ is over-provisioning, it just about meets the **T95** SLA for the Tri phase trace (see Table III) and hence cannot be made more aggressive. 

In support of _AutoScale_ --, we find that _Opt_ ’s power consumption and server usage is only 30% less than that of _AutoScale_ --, averaged across all traces, despite _AutoScale_ -- having to cope with the 260s setup time. 

### **3.7. Lower Setup Times** 

While production servers today are only equipped with “off” states that necessitate huge setup times (260s for our servers), future servers may support sleep states, 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

A. Gandhi et al. 

14:12 





Fig. 9. Effect of lower setup times for (a) Big spike trace [nlanr 1995] and (b) Dual phase trace [nlanr 1995]. 

which can lower setup times considerably. Further, with virtualization, the setup time required to bring up additional capacity (in the form of virtual machines) might also go down. In this section, we again contrast the performance of _AutoScale_ -- with simpler dynamic capacity management policies, for the case of lower setup times. We achieve these lower setup times by tweaking our experimental testbed as discussed at the end of Section 2.1. Furthermore, for _AutoScale_ --, we reduce the value of _twait_ in proportion to the reduction in setup time. 

When the setup time is very low, approaching zero, then by definition, all policies approach _Opt_ . For moderate setup times, one might expect that _AutoScale_ -- does not provide significant benefits over other policies such as _Reactive_ , since **T95** should not rise too much during the setup time. This turns out to be false since the **T95** under _Reactive_ continues to be high even for moderate setup times. 

Figure 9(a) shows our experimental results for **T95** for the Big spike trace [nlanr 1995], under _Reactive_ and _AutoScale_ --. We see that as the setup time drops, the **T95** drops almost linearly for both _Reactive_ and _AutoScale_ --. However, _AutoScale_ -- continues to be superior to _Reactive_ with respect to **T95** for any given setup time. In fact, even when the setup time is only 20s, the **T95** under _Reactive_ is almost twice that under _AutoScale_ --. This is because of the huge spike in load in the Big spike trace that cannot be handled by _Reactive_ even at low setup times. We find similar results for the Steep tri phase trace [sap 2011], with **T95** under _Reactive_ being more than three times as high as that under _AutoScale_ --. The **Pavg** and **Navg** values for _Reactive_ and _AutoScale_ -- also drop with setup time, but the changes are not as significant as for **T95** . 

Figure 9(b) shows our experimental results for **T95** for the Dual phase trace [nlanr 1995], under _Reactive_ and _AutoScale_ --. This time, we see that as the setup time drops below 100s, the **T95** under _Reactive_ approaches that under _AutoScale_ --. This is because of the relatively small fluctuations in load in the Dual phase trace, which can be handled by _Reactive_ once the setup time is small enough. However, for setup times larger than 100s, _AutoScale_ -- continues to be significantly better than _Reactive_ . We find similar results for the Quickly varying trace and the Large variations trace [nlanr 1995]. 

In summary, depending on the trace, _Reactive_ can perform poorly even for low setup times (see Figure 9(a)). We expect similar behavior under the _Predictive_ policies as well. Thus, _AutoScale_ -- can be very beneficial even for more moderate setup times. Note that _AlwaysOn_ and _Opt_ are not affected by setup times. 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

14:13 

AutoScale: Dynamic, Robust Capacity Management for Multi-Tier Data Center 





Fig. 10. Effect of lower idle power for (a) Big spike trace [nlanr 1995] and (b) Dual phase trace [nlanr 1995]. 

### **3.8. Lower Idle Power** 

The idle power for the servers in our testbed is about 140W (with C-states enabled), as mentioned in Section 2.1. However, with advances in processor technology, it is very likely that the server idle power will drop. This claim is also supported by recent literature [Gandhi et al. 2011b; Meisner et al. 2009, 2011]. The drop in server idle power should greatly benefit the static capacity management policy, _AlwaysOn_ , by lowering its **Pavg** , since a lot of servers are idle under _AlwaysOn_ . However, for the dynamic capacity management policies, we only expect **Pavg** to drop slightly, since servers are rarely idle under such policies. To explore the effects of lower server idle power, we contrast the performance of _AutoScale_ -- with that of _AlwaysOn_ . We achieve lower idle power by tweaking our experimental testbed along the same lines as discussed at the end of Section 2.1. 

Figures 10(a) and 10(b) show our experimental results for **Pavg** for the Big spike trace [nlanr 1995] and the Dual phase trace [nlanr 1995] respectively, under _AlwaysOn_ and _AutoScale_ --. We see that the **Pavg** value for _AlwaysOn_ drops almost linearly with the server idle power. This is to be expected since the number of servers idle under _AlwaysOn_ for a given trace is constant, and thus, a drop in server idle power lowers the power consumption of these idle servers proportionately. The **Pavg** value for _AutoScale_ -- also drops with the idle power, but this drop is negligible. It is interesting to note that the **Pavg** value for _AlwaysOn_ drops below that of _AutoScale_ -- only when the idle power is extremely low (less than 15W). We found similar results for the other traces as well. Note that we are being particularly conservative in assuming that while the server idle power drops, the power consumed by the servers when they are in setup remains the same. This assumption hurts the **Pavg** value for _AutoScale_ --. The **T95** value is not affected by the server idle power and is thus not shown. 

In summary, while lower server idle power favors _AlwaysOn_ , the power savings under _AutoScale_ -- continue to be greater than those under _AlwaysOn_ , unless the idle power is extremely low. 

### **4. RESULTS: ROBUSTNESS** 

Thus far, in our traces, we have only varied the request rate over time. However, in reality there are many other ways in which load can change. For example, if new features or security checks are added to the application, the request size might increase. We mimic such effects by increasing the number of key-value lookups associated with each request. As a second example, if any abnormalities occur in the system, such as internal service disruptions, slow networks, or maintenance cycles, servers may respond 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

A. Gandhi et al. 

14:14 





Fig. 11. A single server can no longer handle 60 Fig. 12. For a single server, setting _nsrv_ = _p_ = 10 req/s when the request size increases. works well for all request sizes. 

more slowly, and requests may accumulate at the servers. We mimic such effects by slowing down the frequency of the application servers. All the dynamic capacity management policies described thus far, with the exception of _Opt_ , use the request rate to scale capacity. However, using the request rate to determine the required capacity is somewhat _fragile_ . If the request _size_ increases, or if servers become _slower_ , due to any of the reasons mentioned above, then the number of servers needed to maintain acceptable response times ought to be increased. In both cases, however, no additional capacity will be provisioned if the policies only look at request rate to scale up capacity. 

### **4.1. Why Request Rate Is not a Good Feedback Signal** 

In order to assess the limitations of using request rate as a feedback signal for scaling capacity, we ran _AutoScale_ -- on the Dual phase trace with a 2x request size (meaning that our request size is now 240ms as opposed to the 120ms size we have used thus far). Since _AutoScale_ -- does not detect an increase in request size, and thus doesn’t provision for this, its **T95** shoots up ( **T95** = 51 _,_ 601 _ms_ ). This is also true for the _Reactive_ and _Predictive_ policies, as can be seen in Tables V and VI for the case of increased request size and in Table VII for the case of slower servers. 

Figure 11 shows measured 95%ile response time at a single server versus request rate for different request sizes. It is clear that while each server can handle 60 req/s without violating the **T95** SLA for a 1x request size, the **T95** shoots up for the 2x and 4x request sizes. An obvious way to solve this problem is to determine the request size. However, it is not easy to determine the request size since the size is usually not known ahead of time. Trying to derive the request size by monitoring the response times doesn’t help either since response times are usually affected by queueing delays. Thus, we need to come up with a better feedback signal than request rate or request size. 

### **4.2. A Better Feedback Signal that’s Still not Quite Right** 

We propose using the number of requests in the system, _nsys_ , as the feedback signal for scaling up capacity rather than the request rate. We assert that _nsys_ more faithfully captures the dynamic state of the system than the request rate. If the system is underprovisioned either because the request rate is too high _or_ because the request size is too big or because the servers have slowed down, _nsys_ will tend to increase. If the system is over-provisioned, _nsys_ will tend to decrease below some expected level. Further, calculating _nsys_ is fairly straightforward; many modern systems (including our Apache load balancer) already track this value, and it is instantaneously available. 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

AutoScale: Dynamic, Robust Capacity Management for Multi-Tier Data Center 

14:15 





Fig. 13. Our proposed policy overshoots while scaling up capacity, resulting in high **Pavg** and **Navg** . 

Fig. 14. A doubling of request rate can lead to a tripling of number of requests at a single server. 

Figure 12 shows the measured 95%ile response time at a single server versus the number of requests at a single server, _nsrv_ , for different request sizes. Note that _nsrv_ = _nsys_ in the case of a single-server system. Surprisingly, the 95%ile response time values do not shoot up for the 2x and 4x request sizes for a given _nsrv_ value. In fact, setting _nsrv_ = 10, as in Section 3.5, provides acceptable **T95** values for all request sizes (note that **T95** values for the 2x and 4x request sizes are higher than 500ms, which is to be expected as the work associated with each request is naturally higher). This is because an increase in the request size (or a decrease in the server speed) increases the rate at which “work” comes into each server. This increase in work is reflected in the consequent increase in _nsrv_ . By limiting _nsrv_ using _p_ , the packing factor (the maximum number of requests that a server can serve concurrently and meet its SLA), we can limit the rate at which work comes in to each server, thereby adjusting the required capacity to ensure that we meet the **T95** SLA. Based on these observations, we set _p_ = 10 for the 2x and 4x request sizes. Thus, _p_ is agnostic to request sizes for our system, and only needs to be computed once. The insensitivity of _p_ to request sizes is to be expected since _p_ represents the degree of parallelism for a server, and thus depends on the specifications of a server (number of cores, hyperthreading, etc), and not on the request size. 

Based on our observations from Figure 12, we propose a plausible solution for dynamic capacity management based on looking at the total number of requests in the system, _nsys_ , as opposed to looking at the request rate. The idea is to provision capacity to ensure that the number of requests at a server is _nsrv_ = 10. In particular, the proposed policy is exactly the same as _AutoScale_ --, except that it estimates the required capacity as _kreqd_ = ⌈ _nsys/_ 10⌉, where _nsys_ is the total number of requests in the system at that time. In our implementation, we sample _nsys_ every 20 seconds, and thus, the proposed policy re-scales capacity, if needed, every 20 seconds. Note that the proposed policy uses the same method to scale down capacity as _AutoScale_ --, viz., using a timeout of 120s along with the index-packing routing. 

Figure 13 shows how our proposed policy behaves for the 1x request size. We see that our proposed policy successfully meets the **T95** SLA, but it clearly overshoots in terms of scaling up capacity when the request rate goes up. Thus, the proposed policy results in high power and resource consumption. One might think that this overshoot can be avoided by packing more requests at each server, thus allowing _nsrv_ to be higher than 10. However, note that the **T95** in Figure 13 is already quite close to the 500ms SLA, and increasing the number of requests packed at a server beyond 10 can result in SLA violations. 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

A. Gandhi et al. 

14:16 

Figure 14 explains the overshoot in terms of scaling up capacity for our proposed policy. We see that when the request rate into a single server, _rsrv_ , doubles from 60 req/s to 120 req/s, _nsrv_ more than doubles from 10 to 32. Thus, our proposed policy scales up capacity by a factor of 3, whereas ideally capacity should only be scaled up by a factor of 2. Clearly our proposed policy does not work so well, even in the case where the request size is just 1x. 

We now introduce our _AutoScale_ policy, which solves our problems of scaling up capacity. 

### **4.3. AutoScale: Incorporating the Right Feedback Signal** 

We now describe the _AutoScale_ policy and show that it not only handles the case where request rate changes, but also handles cases where the request size changes (see Tables V and VI) or where the server efficiency changes (see Table VII). 

_AutoScale_ differs from the capacity management policies described thus far in that it uses the number of requests in the system, _nsys_ , as the feedback signal rather than request rate. However, _AutoScale_ does not simply scale up the capacity linearly with an increase in _nsys_ , as was the case with our proposed policy. This is because _nsys_ grows _super-linearly_ during the time that the system is under-provisioned, as is well known in queueing theory. Instead, _AutoScale_ tries to infer the _amount of work_ in the system by monitoring _nsys_ . The amount of work in the system is proportional to both the request rate and the request size (the request size in turn depends also on the server efficiency), and thus, we try to infer the product of request rate and request size, which we call _system load_ , _ρsys_ . Formally, 



where the average 1x request size is 120ms. Fortunately, there is an easy relationship (which we describe soon) between the number of requests in the system, _nsys_ , and the system load, _ρsys_ , obviating the need to ever measure load or request rate or the request size. Once we have _ρsys_ , it is easy to get to the required capacity, _kreqd_ , since _ρsys_ represents the amount of work in the system and is hence proportional to _kreqd_ . We now explain the translation process from _nsys_ to _ρsys_ and then from _ρsys_ to _kreqd_ . We refer to this entire translation algorithm as the _capacity inference algorithm_ . The full translation from _nsys_ to _kreqd_ will be given in Eq. (4). A full listing of all the variables used in this section is provided in Table IV for convenience. 

_The Capacity Inference Algorithm._ In order to understand the relationship between _nsys_ and _ρsys_ , we first derive the relationship between the number of requests at a single server, _nsrv_ , and the load at a single server, _ρsrv_ . Formally, the load at a server is defined as 



where the average 1x request size is 120ms and _rsrv_ is the request rate into a single server. If the request rate to a server, _rsrv_ , is made as high as possible without violating the SLA, then the resulting _ρsrv_ from Eq. (1) is referred to as the reference load, _ρref_ . For our system, recall that the maximum request rate into a single server without violating the SLA is _rsrv_ = 60 req/s (see Figure 2). Thus, 



ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

14:17 

AutoScale: Dynamic, Robust Capacity Management for Multi-Tier Data Center 

Table IV. Description of Variables 

|Variable|Description|
|---|---|
|_rsrv_|Request rate into a single server|
|_R_|Request rate into the data center|
|_nsys_|Number of requests in the system|
|_nsrv_|Number of requests at a server|
|_p_|Packing factor (maximum_nsrv_ without violating SLA)|
|_ρsys_|System load|
|_ρsrv_|Load at a server|
|_ρref_|Reference load (for a single server)|
|_kreqd_|Required capacity (number of servers)|
|_kcurr_|Current capacity|





Fig. 15. Load at a server as a function of the number of requests at a server for various request sizes. Surprisingly, the graph is invariant to changes in request size. 

meaning that a single server can handle a load of at most 7 without violating the SLA, assuming a 1x request size of 120ms. 

Returning to the discussion of how _ρsrv_ and _nsrv_ are related, we expect that _ρsrv_ should increase with _nsrv_ . Figure 15(a) shows our experimental results for _ρsrv_ as a function of _nsrv_ . Note that _ρsrv_ = _ρref_ = 7 corresponds to _nsrv_ = _p_ = 10, where _p_ is the packing factor. We obtain Figure 15(a) by converting _rsrv_ in Figure 14 to _ρsrv_ using Eq. (1). Observe that when _ρsrv_ doubles from 7 to 14, we see that _nsrv_ more than triples from 10 to 32, as was the case in Figure 14. 

We’ll now estimate _ρsys_ , the system load, using the relationship between _nsrv_ and _ρsrv_ . To estimate _ρsys_ , we first approximate _nsrv_ as _k_<sup>_n_</sup> _curr_<sup>_sys_, where</sup><sup>_kcurr_is the current number of</sup> on servers. We then use _nsrv_ in Figure 15(a) to estimate the corresponding _ρsrv_ . Finally, we have _ρsys_ = _kcurr_ × _ρsrv_ . In summary, given the number of requests in the system, _nsys_ , we can derive the system load, _ρsys_ , as follows: 



Surprisingly, the relationship between the number of requests at a server, _nsrv_ , and the load at a server, _ρsrv_ , does not change when request size changes. Figure 15(b) shows our experimental results for the relationship between _nsrv_ and _ρsrv_ for different request sizes. We see that the plot is invariant to changes in request size. Thus, while calculating _ρsys_ = _kcurr_ × _ρsrv_ , we don’t have to worry about the request size and we 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

A. Gandhi et al. 

### 14:18 

can simply use Figure 15(a) to estimate _ρsys_ from _nsys_ irrespective of the request size. Likewise, we find that the relationship between _nsrv_ and _ρsrv_ does not change when the server speed changes. This is because a decrease in server speed is the same as an increase in request size for our system. 

The reason why the relationship between _nsrv_ and _ρsrv_ is agnostic to request size is because _ρsrv_ , by definition (see Eq. (1)), takes the request size into account. If the request size doubles, then the request rate into a server needs to drop by a factor of 2 in order to maintain the same _ρsrv_ . These changes result in exactly the same amount of work entering the system per unit time, and thus, _nsrv_ does not change. The insensitivity of the relationship between _nsrv_ and _ρsrv_ to changes in request size is consistent with queueing-theoretic analysis [Kleinrock 1975]. Interestingly, this insensitivity, coupled with the fact that the packing factor, _p_ , is a constant for our system ( _p_ = 10, see Section 4.2), results in the reference load, _ρref_ , being a constant for our system, since _ρref_ = _ρsrv_ for the case when _nsrv_ = _p_ = 10 (see Figure 15(a)). Thus, we only need to compute _ρref_ once for our system. 

Now that we have _ρsys_ from Eq. (3), we can translate this to the required capacity, _kreqd_ , using _ρref_ . Since _ρsys_ corresponds to the total system load, while _ρref_ corresponds to the load that a single server can handle, we deduce that the required capacity is: 



In summary, we can get from _nsys_ to _kreqd_ by first translating _nsys_ to _ρsys_ , which leads us to _kreqd_ , as follows: 



For example, if _nsys_ = 320 and _kcurr_ = 10, then we get _nsrv_ = 32, and from Figure 15(a), _ρsrv_ = 14, irrespective of request size. The load for the system, _ρsys_ , is then given by _kcurr_ × _ρsrv_ = 140, and since _ρref_ = 7, the required capacity is _kreqd_ = ⌈ _kcurr_ × _ρ_<sup>_<u>ρ</u>_</sup> _ref_<sup>_<u>srv</u>_⌉=20.</sup> Consequently, _AutoScale_ turns on 10 additional servers. In our implementation, we reevaluate _kreqd_ every 20s to avoid excessive changes in the number of servers. 

The insensitivity to request size of the relationship between _nsrv_ and _ρsrv_ from Figure 15(b) allows us to use Eq. (4) to compute the desired capacity, _kreqd_ , in response to any form of load change. Further, as previously noted, _p_ and _ρref_ are constants for our system, and only need to be computed once. These properties make _AutoScale_ a very robust capacity management policy. 

_Performance of AutoScale._ Tables V and VI summarize results for the case where the number of key-value lookups per request (or the request size) increases by a factor of 2 and 4 respectively. Because request sizes are dramatically larger, and because the number of servers in our testbed is limited, we compensate for the increase in request size by scaling down the request rate by the same factor. Thus, in Table V, request sizes are a factor of two larger than in Table III, but the request rate is half that of Table III. The **T95** values are expected to increase as compared with Table III because each request now takes longer to complete (since it does more key-value lookups). 

Looking at _AutoScale_ in Table V, we see that **T95** increases to around 700ms, while in Table VI, it increases to around 1200ms. This is to be expected. By contrast, for all other dynamic capacity management policies, the **T95** values exceed one minute, both in Tables V and VI. Again, this is because these policies react only to changes in the request rate, and thus end up typically under-provisioning. We do not show the results for _AutoScale_ -- in Tables V and VI, but its performance is just as bad as the other dynamic capacity management policies that react only to changes in the request 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

14:19 

AutoScale: Dynamic, Robust Capacity Management for Multi-Tier Data Center 

Table V. Comparison of All Policies for 2x Request Size.<sup>2</sup> 

|hhhhhhh<br>Trace|hhhh<br>h<br>Policy|_AlwaysOn_|_Reactive_|_Predictive_<br>_MWA_|_Predictive_<br>_LR_|_Opt_|_AutoScale_|
|---|---|---|---|---|---|---|---|
|Sll i|**T95**|478ms|_>_1 min|_>_1 min|_>_1 min|531ms|701ms|
|owy varyng<br>[ita 1998]|**Pavg**|2,127W|541W|597W|728W|667W|923W|
||**Navg**|14.0|3.2|2.7|3.8|4.0|5.4|
|Dl h|**T95**|424ms|_>_1 min|_>_1 min|_>_1 min|532ms|726ms|
|ua pase<br>[nlanr 1995]|**Pavg**|2,190W|603W|678W|1,306W|996W|1,324W|
||**Navg**|14.0|3.0|2.6|6.6|5.8|7.3|



Table VI. Comparison of All Policies for 4x Request Size.<sup>2</sup> 

|hhhhhhh<br>Trace|hhhh<br>h<br>Policy|_AlwaysOn_|_Reactive_|_Predictive_<br>_MWA_|_Predictive_<br>_LR_|_Opt_|_AutoScale_|
|---|---|---|---|---|---|---|---|
||**T95**|759ms|_>_1 min|_>_1 min|_>_1 min|915ms|1,155ms|
|Slowly varying<br>[ita 1998]|**Pavg**|2,095W|280W|315W|391W|630W|977W|
||**Navg**|14.0|1.9|1.7|2.1|4.0|5.7|
||**T95**|733ms|_>_1 min|_>_1 min|_>_1 min|920ms|1,217ms|
|Dual phase<br>[nlanr 1995]|**Pavg**|2,165W|340W|389W|656W|985W|1,304W|
||**Navg**|14.0|1.7|1.8|3.2|5.9|7.2|



rate. _AlwaysOn_ knows the peak load ahead of time, and thus, always keeps **Navg** = 14 servers on. As expected, the **T95** values for _AlwaysOn_ are quite good, but **Pavg** and **Navg** are very high. Comparing _AutoScale_ and _Opt_ , we see that _Opt_ ’s power consumption and server usage is again only about 30% less than that of _AutoScale_ . 

Figure 16 shows the server behavior under _AutoScale_ for the Dual phase trace for request sizes of 1x, 2x and 4x. Clearly, _AutoScale_ is successful at handling the changes in load due to both, changes in request rate and changes in request size. 

Table VII illustrates another way in which load can change. Here, we return to the 1x request size, but this time all servers have been slowed down to a frequency of 1.6 GHz as compared with the default frequency of 2.26 GHz. By slowing down the frequency of the servers, **T95** naturally increases. We find that for all the dynamic capacity management policies, except for _AutoScale_ , the **T95** shoots up. The reason is that these other dynamic capacity management policies provision capacity based on the request rate. Since the request rate has not changed as compared to Table III, they typically end up under-provisioning, now that servers are slower. The **T95** for _AlwaysOn_ does not shoot up because even in Table III, it is greatly over-provisioning by provisioning for the peak load at all times. Since the _AutoScale_ policy is robust to all changes in load, it provisions correctly, resulting in acceptable **T95** values. **Pavg** and **Navg** values for _AutoScale_ continue to be much lower than that of _AlwaysOn_ , similar to Table III. 

> 2For a given arrival trace, when request size is scaled up, the size of the application tier should ideally be scaled up as well so as to accommodate the increased load. However, since our application tier is limited to 28 servers, we follow up an increase in request size with a proportionate decrease in request rate for the arrival trace. Thus, the peak load (request rate times request size) is the same before and after the request size increase, and our 28 server application tier suffices for the experiment. In particular, _AlwaysOn_ , which knows the peak load ahead of time, is able to handle peak load by keeping 14 servers on even as the request size increases. 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

A. Gandhi et al. 

14:20 



Fig. 16. Robustness of _AutoScale_ to changes in request size. The request size is 1x (or 120ms) in (a), 2x (or 240ms) in (b), and 4x (or 480ms) in (c). 

Table VII. Comparison of All Policies for Lower CPU Frequency 

|hhhhhhh<br>Trace|hhhh<br>h<br>Policy|_AlwaysOn_|_Reactive_|_Predictive_<br>_MWA_|_Predictive_<br>_LR_|_Opt_|_AutoScale_|
|---|---|---|---|---|---|---|---|
||**T95**|572ms|_>_1 min|_>_1 min|3,339ms|524ms|760ms|
|Slowly varying<br>[ita 1998]|**Pavg**|2,132W|903W|945W|863W|638W|1,123W|
||**Navg**|14.0|5.7|5.9|4.8|4.0|7.2|
|Dl h|**T95**|362ms|24,401ms|23,412ms|2,527ms|485ms|564ms|
|ua pase<br>[nlanr 1995]|**Pavg**|2,147W|1,210W|1,240W|2,058W|1,027W|1,756W|
||**Navg**|14.0|6.3|7.4|12.2|5.9|10.8|



Tables V, VI, and VII clearly indicate the superior robustness of _AutoScale_ which uses _nsys_ to respond to changes in load, allowing _AutoScale_ to respond to all forms of changes in load. 

### **4.4. Alternative Feedback Signal Choices** 

_AutoScale_ employs the number of requests in the system, _nsys_ , as opposed to request rate, as the feedback signal for provisioning capacity. An alternative feedback signal that we could have employed in _AutoScale_ is **T95** , the performance metric. Using the performance metric as a feedback signal is a popular choice in control-theoretic approaches [Leite et al. 2010; Li and Nahrstedt 1999; Lu et al. 2006; Nathuji et al. 2010]. While using **T95** as the feedback signal might allow _AutoScale_ to achieve the same robustness properties as provided by _nsys_ , we would first have to come up with an analogous capacity inference algorithm for the **T95** feedback signal. As discussed in Section 4.2, using an inaccurate capacity inference algorithm can result in poor capacity management. For single-tier systems, one can use simple empirical models or analytical approximations to derive the capacity inference algorithm, as was the case in Li and Nahrstedt [1999], Lu et al. [2006], and Chen et al. [2005]. However, for multitier systems, coming up with a capacity inference algorithm can be quite difficult, as noted in Nathuji et al. [2010]. Further, performance metrics such as **T95** depend not only on the system load, _ρsys_ , but also on the request size, as is well known in queueing theory [Kleinrock 1975]. Thus, the capacity inference algorithm for the **T95** feedback signal will not be invariant to the request size. 

Other choices for the feedback signal that have been used in prior work include system-level metrics such as CPU utilization [Gandhi et al. 2002; Horvath and Skadron 2008; Li and Nahrstedt 1999], memory utilization [Gandhi et al. 2002], 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

AutoScale: Dynamic, Robust Capacity Management for Multi-Tier Data Center 

14:21 

network bandwidth [Li and Nahrstedt 1999], etc. A major drawback of employing these feedback signals, as mentioned in Horvath and Skadron [2008], is that utilization and bandwidth values saturate at 100%, and thus, the degree of under-provisioning cannot be determined via these signals alone. This makes it difficult to derive a capacity inference algorithm for these feedback signals. 

### **5. LIMITATIONS OF OUR WORK** 

Our evaluation thus far has demonstrated the potential benefits of using _AutoScale_ . However, there are some limitations to our work, which we discuss in this section. 

- (1) The design of _AutoScale_ includes a few key parameters: _twait_ (see Table II), _p_ (derived in Figure 6), _ρref_ (derived in Eq. (2)), and the _ρsrv_ vs. _nsrv_ relationship (derived in Figure 15(a)). In order to deploy _AutoScale_ on a given cluster, these parameters need to be determined. Fortunately, all of these parameters only need to be determined once for a given cluster. This is because these parameters depend on the specifications of the system, such as the server type, the setup time, and the application, which do not change at runtime. Request rate, request size, and server speed, can all change at runtime, but these do not affect the value of these key parameters (see Section 4 for more details). 

- (2) In Section 4, we considered a few different forms of changes in load, such as changes in request size and changes in server speed, as well as changes in request rate. However, in production environments, load can change in many additional ways. For example, consider a scenario where some of the servers slow down due to software updates, while other servers are being backed up, and the rest of the servers are experiencing network delays. Evaluating _AutoScale_ under all such scenarios is beyond the scope of this article. 

- (3) Our experimental evaluation is limited to a multi-tier testbed consisting of 38 servers, serving a web site with a key-value workload. Our testbed comprises an Apache load balancer, a homogenous application tier running php, and a memcached tier with a persistent back-end database. There are a variety of other application testbeds that we could have considered, ranging from single-tier stateless applications to complex multi-tier applications that are deployed in the industry today. The key feature that _AutoScale_ depends on is having some servers that are stateless, and can thus be turned off or repurposed to save power/cost. Fortunately, many applications have this feature. For example, Facebook [2011], Amazon [DeCandia et al. 2007] and Windows Live Messenger [Chen et al. 2008], all use stateless servers as part of their platform. Thus, even though we have a very specific testbed, it is representative of many real-world applications. 

### **6. PRIOR WORK** 

Dynamic capacity management can be divided into two types: reactive (a.k.a. controltheoretic) approaches and predictive approaches. Reactive approaches, for example, Leite et al. [2010], Nathuji et al. [2010], Fan et al. [2007], Wang and Chen [2008], Wood et al. [2007], and Elnozahy et al. [2002], all involve reacting to the current request rate (or the current response time, or current CPU utilization, or current power, etc.) by turning servers on or off. When the setup time is high (260s), these can be inadequate for meeting response time goals because the effect of the increased capacity only happens 260 seconds later. 

Predictive approaches, for example, Krioukov et al. [2010], Qin and Wang [2007], Castellanos et al. [2005], and Horvath and Skadron [2008], aim to predict what the 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

A. Gandhi et al. 

### 14:22 

request rate will be 260 seconds from now, so that they can start turning on servers now if needed. Predictive or combined approaches work well when workload is periodic or seasonal, for example, Chen et al. [2005, 2008], Bobroff et al. [2007], Urgaonkar et al. [2005], Gmach et al. [2008], Urgaonkar and Chandra [2005], and Gandhi et al. [2011a]. However when traffic is bursty and future arrivals are unknown, it is clearly hard to predict what will happen 260 seconds into the future. 

We now discuss in detail the relevant prior work in predictive approaches and reactive approaches. 

_Predictive Approaches._ Krioukov et al. [2010] use various predictive policies, such as Last Arrival, _MWA_ , Exponentially Weighted Average and _LR_ , to predict the future request rate (to account for setup time), and then accordingly add or remove servers from a heterogenous pool. The authors evaluate their dynamic provisioning policies by simulating a multi-tier web application. The authors find that _MWA_ and _LR_ work best for the traces they consider (Wikipedia.org traffic), providing significant power savings over _AlwaysOn_ . However, the _AlwaysOn_ version used by the authors does not know the peak request rate ahead of time (in fact, in many experiments they set _AlwaysOn_ to provision for twice the historically observed peak), and is thus not as powerful an adversary as the version we employ. 

Chen et al. [2008] use auto-regression techniques to predict the request rate for a seasonal arrival pattern, and then accordingly turn servers on and off using a simple threshold policy. The authors evaluate their dynamic provisioning policies via simulation for a single-tier application. The authors find that their dynamic provisioning policy performs well for periodic request rate patterns that repeat, say, on a daily basis. The authors evaluate their policies via simulation in a single-tier setting. While the setup in Chen et al. [2008] is very different (seasonal arrival patterns) from our own, there is one similarity to _AutoScale_ in their approach: like _AutoScale_ , the authors in Chen et al. [2008] use the index-based routing (see Section 3.5). However, the policy in Chen et al. [2008] does not have any of the robustness properties of _AutoScale_ , nor the _twait_ timeout idea. 

_Reactive and mixed approaches._ Hoffmann et al. [2011] consider a single-tier system with unpredictable load fluctuations. The authors employ a reactive approach using the quality of service (for example, the bitrate or image quality) as the feedback signal to create a robust system. However, the workload considered by the authors allows for a loss in quality of service, thus obviating the need to scale capacity during load fluctuations. In our system, we do not have any leeway on the quality of service since we have a strict **T95** SLA. Thus, during load fluctuations, _AutoScale_ must dynamically scale capacity to maintain the required SLA. 

Horvath and Skadron [2008] employ a reactive feedback mechanism, similar to the _Reactive_ policy in this article, coupled with a non-linear regression based predictive approach to provision capacity for a multi-tier web application. In particular, the authors monitor server CPU utilization and job response times, and react by adding or removing servers based on the difference between observed response time and target response time. The authors evaluate their reactive approach via implementation in a multi-tier setting. 

In Urgaonkar and Chandra [2005] and Gandhi et al. [2011a], the authors assume a different setup from our own, whereby request rate is divided into two components, a long-term trend which is predictable, and short-term variations which are unpredictable. The authors use predictive approaches to provision servers for long-term trends (over a few hours) in request rates and then use a reactive controller, similar to the _Reactive_ used in this article, to react to short-term variations in request rate. 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

AutoScale: Dynamic, Robust Capacity Management for Multi-Tier Data Center 

14:23 

While these hybrid approaches can leverage the advantages of both predictive and reactive approaches, they are not robust to changes in request size or server efficiency (see Section 4). In fact, none of the prior work has considered changes in request size or server efficiency for multi-tier applications. 

There is also a long list of papers that look at dynamic capacity management in the case of negligible setup times (see, e.g., Li and Nahrstedt [1999], Lu et al. [2006], Gandhi et al. [2002], Chase et al. [2001], and Lim et al. [2011]). However, our focus in this article is on dynamic capacity management in the face of setup times. 

### **7. CONCLUSION AND FUTURE WORK** 

This article considers dynamic capacity management policies for data centers facing bursty and unpredictable load so as to save power/resources without violating response time SLAs. The difficulty in dynamic capacity management is the large setup time associated with getting servers back on. Existing reactive approaches that simply scale capacity based on the current request rate are too rash to turn servers off, especially when request rate is bursty. Given the huge setup time needed to turn servers back on, response times suffer greatly when request rate suddenly rises. Predictive approaches that work well when request rate is periodic or seasonal, perform very poorly in our case where traffic is unpredictable. Furthermore, as we show in Section 3.3, leaving a fixed buffer of extra capacity is also not the right solution. 

_AutoScale_ takes a fundamentally different approach to dynamic capacity management than has been taken in the past. First, _AutoScale_ does not try to predict the future request rate. Instead, _AutoScale_ introduces a smart policy to automatically provision spare capacity, which can absorb unpredictable changes in request rate. We make the case that to successfully meet response time SLAs, it suffices to simply manage existing capacity carefully and not give away spare capacity recklessly (see Table III). Existing reactive approaches can be easily modified to be more conservative in giving away spare capacity so as to inherit _AutoScale_ ’s ability to absorb unpredictable changes in request rate. Second, _AutoScale_ is able to handle unpredictable changes not just in the request rate but also unpredictable changes in the request size (see Tables V and VI) and the server efficiency (see Table VII). _AutoScale_ does this by provisioning capacity using not the request rate, but rather the number of requests in the system, which it is able to translate into the correct capacity via a novel, non-trivial algorithm. As illustrated via our experimental results in Tables III to VII, _AutoScale_ outclasses existing optimized predictive and reactive policies in terms of consistently meeting response time SLAs. While _AutoScale_ ’s 95%ile response time numbers are usually less than one second, the 95%ile response times of existing predictive and reactive policies often exceed one full minute! 

Not only does _AutoScale_ allow us to save power while meeting response time SLAs, but it also allows us to save on rental costs when leasing resources (physical or virtual) from cloud service providers by reducing the amount of resources needed to successfully meet response time SLAs. 

While one might think that _AutoScale_ will become less valuable as setup times decrease (due to, for example, sleep states or virtual machines), or as server idle power decreases (due to, for example, advances in processor technology), we find that this is not the case. _AutoScale_ can significantly lower response times and power consumption when compared to existing policies even for low setup times (see Figure 9) and reasonably low idle power (see Figure 10). In fact, even when the setup time is only 20s, _AutoScale_ can lower 95%ile response times by a factor of 3. 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

A. Gandhi et al. 

14:24 

### **REFERENCES** 

AMAZON INC. 2008. Amazon Elastic Compute Cloud (Amazon EC2). 

ARMBRUST, M., FOX, A., GRIFFITH, R., JOSEPH, A. D., KATZ, R. H., KONWINSKI, A., LEE, G., PATTERSON, D. A., RABKIN, A., STOICA, I., AND ZAHARIA, M. 2009. Above the clouds: A Berkeley view of cloud computing. Tech. rep. UCB/EECS-2009-28, EECS Department, University of California, Berkeley. 

BARROSO, L. A. AND H OLZLE<sup>¨</sup> , U. 2007. The case for energy-proportional computing. _Computer 40_ , 12, 33–37. 

BOBROFF, N., KOCHUT, A., AND BEATY, K. 2007. Dynamic placement of virtual machines for managing SLA violations. In _Proceedings of the 10th IFIP/IEEE International Symposium on Integrated Network Management (IM’07)_ . 119–128. 

BOD<sup>´</sup> IK, P., GRIFFITH, R., SUTTON, C., FOX, A., JORDAN, M., AND PATTERSON, D. 2009. Statistical machine learning makes automatic control practical for internet datacenters. In _Proceedings of the 2009 Conference on Hot Topics in Cloud Computing (HotCloud’09)_ . 

CASTELLANOS, M., CASATI, F., SHAN, M.-C., AND DAYAL, U. 2005. iBOM: A platform for intelligent business operation management. In _Proceedings of the 21st International Conference on Data Engineering (ICDE’05)_ . 1084–1095. 

CHASE, J. S., ANDERSON, D. C., THAKAR, P. N., AND VAHDAT, A. M. 2001. Managing energy and server resources in hosting centers. In _Proceedings of the 18th ACM Symposium on Operating Systems Principles (SOSP’01)_ . 103–116. 

- CHEN, G., HE, W., LIU, J., NATH, S., RIGAS, L., XIAO, L., AND ZHAO, F. 2008. Energy-aware server provisioning and load dispatching for connection-intensive internet services. In _Proceedings of the 5th USENIX Symposium on Networked Systems Design and Implementation (NSDI’08)_ . 337–350. 

CHEN, Y., DAS, A., QIN, W., SIVASUBRAMANIAM, A., WANG, Q., AND GAUTAM, N. 2005. Managing server energy and operational costs in hosting centers. In _Proceedings of the ACM SIGMETRICS International Conference on Measurement and Modeling of Computer Systems (SIGMETRICS’05)_ . 303–314. 

DECANDIA, G., HASTORUN, D., JAMPANI, M., KAKULAPATI, G., LAKSHMAN, A., PILCHIN, A., SIVASUBRAMANIAN, S., VOSSHALL, P., AND VOGELS, W. 2007. Dynamo: Amazon’s highly available key-value store. In _Proceedings of 21st ACM SIGOPS Symposium on Operating Systems Principles (SOSP’07)_ . 205–220. 

- ELNOZAHY, E., KISTLER, M., AND RAJAMONY, R. 2002. Energy-efficient server clusters. In _Proceedings of the 2nd Workshop on Power-Aware Computing Systems (WPACS’02)_ . 179–196. 

FACEBOOK. 2011. Personal communication with Facebook. 

FAN, X., WEBER, W.-D., AND BARROSO, L. A. 2007. Power provisioning for a warehouse-sized computer. In _Proceedings of the 34th Annual International Symposium on Computer Architecture (ISCA’07)_ . 13–23. 

GANDHI, A., CHEN, Y., GMACH, D., ARLITT, M., AND MARWAH, M. 2011a. Minimizing data center SLA violations and power consumption via hybrid resource provisioning. In _Proceedings of the 2nd International Green Computing Conference (IGCC’11)_ . 

GANDHI, A., HARCHOL-BALTER, M., AND KOZUCH, M. A. 2011b. The case for sleep states in servers. In _Proceedings of the 4th Workshop on Power-Aware Computing and Systems (HotPower’11)_ . 

GANDHI, N., TILBURY, D., DIAO, Y., HELLERSTEIN, J., AND PAREKH, S. 2002. MIMO control of an Apache web server: Modeling and controller design. In _Proceedings of the 2002 American Control Conference (ACC’02 Series, vol. 6)_ . 4922–4927. 

GMACH, D., KROMPASS, S., SCHOLZ, A., WIMMER, M., AND KEMPER, A. 2008. Adaptive quality of service management for enterprise services. _ACM Trans. Web 2_ , 1, 1–46. 

GRUNWALD, D., MORREY III, C. B., LEVIS, P., NEUFELD, M., AND FARKAS, K. I. 2000. Policies for dynamic clock scheduling. In _Proceedings of the 4th Conference on Symposium of Operating System Design and Implementation (OSDI’00)_ . 

- HOFFMANN, H., SIDIROGLOU, S., CARBIN, M., MISAILOVIC, S., AGARWAL, A., AND RINARD, M. 2011. Dynamic knobs for responsive power-aware computing. In _Proceedings of the 16th International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS’11)_ . 199–212. 

HORVATH, T. AND SKADRON, K. 2008. Multi-mode energy management for multi-tier server clusters. In _Proceedings of the 17th International Conference on Parallel Architectures and Compilation Techniques (PACT’08)_ . 270–279. 

ITA. 1998. The Internet Traffic Archives: WorldCup98. http://ita.ee.lbl.gov/html/contrib/WorldCup.html. 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

14:25 

### AutoScale: Dynamic, Robust Capacity Management for Multi-Tier Data Center 

- IYER, S. AND DRUSCHEL, P. 2001. Anticipatory scheduling: A disk scheduling framework to overcome deceptive idleness in synchronous I/O. In _Proceedings of the 18th ACM Symposium on Operating Systems Principles (SOSP’01)_ . 117–130. 

- KIM, J. AND ROSING, T. S. 2006. Power-aware resource management techniques for low-power embedded systems. In _Handbook of Real-Time and Embedded Systems_ . Taylor-Francis Group LLC. 

- KIVITY, A. 2007. KVM: The Linux virtual machine monitor. In _Proceedings of the 2007 Ottawa Linux Symposium (OLS’07)_ . 225–230. 

- KLEINROCK, L. 1975. _Queueing Systems, Volume I: Theory_ . Wiley-Interscience. 

- KRIOUKOV, A., MOHAN, P., ALSPAUGH, S., KEYS, L., CULLER, D., AND KATZ, R. 2010. NapSAC: Design and implementation of a power-proportional web cluster. In _Proceedings of the 1st ACM SIGCOMM Workshop on Green Networking (Green Networking’10)_ . 15–22. 

- LEITE, J. C., KUSIC, D. M., AND MOSSE<sup>´</sup> , D. 2010. Stochastic approximation control of power and tardiness in a three-tier web-hosting cluster. In _Proceeding of the 7th International Conference on Autonomic Computing (ICAC’10)_ . 41–50. 

- LI, B. AND NAHRSTEDT, K. 1999. A control-based middleware framework for quality of service adaptations. _IEEE J. Sel. Areas Commun. 17_ , 1632–1650. 

- LIM, S.-H., SHARMA, B., TAK, B. C., AND DAS, C. R. 2011. A dynamic energy management scheme for multi-tier data centers. In _Proceedings of the IEEE International Symposium on Performance Analysis of Systems and Software (ISPASS’11)_ . 257–266. 

- LU, C., LU, Y., ABDELZAHER, T., STANKOVIC, J., AND SON, S. 2006. Feedback control architecture and design methodology for service delay guarantees in web servers. _IEEE Trans. Paral. Distrib. Syst. 17_ , 9, 1014–1027. 

- LU, Y.-H., CHUNG, E.-Y., S<sup>ˇ</sup> IMUNIC<sup>´</sup> , T., BENINI, L., AND DE MICHELI, G. 2000. Quantitative comparison of power management algorithms. In _Proceedings of the Conference on Design, Automation and Test in Europe (DATE’00)_ . 20–26. 

- MEISNER, D., GOLD, B. T., AND WENISCH, T. F. 2009. PowerNap: Eliminating server idle power. In _Proceeding of the 14th International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS’09)_ . 205–216. 

- MEISNER, D., SADLER, C. M., BARROSO, L. A., WEBER, W.-D., AND WENISCH, T. F. 2011. Power management of online data-intensive services. In _Proceedings of the 38th Annual International Symposium on Computer Architecture (ISCA’11)_ . 319–330. 

MOSBERGER, D. AND JIN, T. 1998. httperf—A tool for measuring web server performance. _ACM Sigmetrics: Perf. Eval. Rev. 26_ , 3, 31–37. NATHUJI, R., KANSAL, A., AND GHAFFARKHAH, A. 2010. Q-clouds: Managing performance interference effects for QoS-aware clouds. In _Proceedings of the 5th European Conference on Computer Systems, (EuroSys’10)_ . 237–250. 

NEWMAN, M. E. J. 2005. Power laws, Pareto distributions and Zipf’s law. _Contemp. Phys. 46_ , 323–351. NLANR. 1995. National Laboratory for Applied Network Research. Anonymized access logs. 

ftp://ftp.ircache.net/Traces/. 

- PERING, T., BURD, T., AND BRODERSEN, R. 1998. The simulation and evaluation of dynamic voltage scaling algorithms. In _Proceedings of the International Symposium on Low Power Electronics and Design (ISLPED’98)_ . 76–81. 

QIN, W., AND WANG, Q. 2007. Modeling and control design for performance management of web servers via an IPV approach. _IEEE Trans. Control Syst. Tech. 15_ , 2, 259–275. SAP. 2011. SAP application trace from anonymous source. 

- SNYDER, B. 2010. Server virtualization has stalled, despite the hype. http://www.infoworld.com/print/146901. 

- URGAONKAR, B. AND CHANDRA, A. 2005. Dynamic provisioning of multi-tier internet applications. In _Proceedings of the 2nd International Conference on Automatic Computing (ICAC’05)_ . 217–228. 

- URGAONKAR, B., PACIFICI, G., SHENOY, P., SPREITZER, M., AND TANTAWI, A. 2005. An analytical model for multi-tier internet services and its applications. In _Proceedings of the 2005 ACM SIGMETRICS International Conference on Measurement and Modeling of Computer Systems (SIGMETRICS’05)_ . 291–302. 

- VERMA, A., DASGUPTA, G., NAYAK, T. K., DE, P., AND KOTHARI, R. 2009. Server workload analysis for power minimization using consolidation. In _Proceedings of the 2009 Conference on USENIX Annual Technical Conference (USENIX’09)_ . 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

### 14:26 

A. Gandhi et al. 

- WANG, X. AND CHEN, M. 2008. Cluster-level feedback power control for performance optimization. In _Proceeding of the 14th IEEE International Symposium on High-Performance Computer Architecture (HPCA’08)_ . 101–110. 

- WOOD, T., SHENOY, P. J., VENKATARAMANI, A., AND YOUSIF, M. S. 2007. Black-box and gray-box strategies for virtual machine migration. In _Proceedings of the 4th USENIX Conference on Networked Systems Design and Implementation (NSDI’07)_ . 229–242. 

Received April 2012; revised August 2012; accepted September 2012 

ACM Transactions on Computer Systems, Vol. 30, No. 4, Article 14, Publication date: November 2012. 

