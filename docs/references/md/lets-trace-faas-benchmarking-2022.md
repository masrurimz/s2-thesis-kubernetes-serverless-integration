---
# --- bibliographic record ---
entry_type: misc
title: "Let&#39;s Trace It: Fine-Grained Serverless Benchmarking using Synchronous and Asynchronous Orchestrated Applications"
authors:
  - "Joel Scheuner"
  - "Simon Eismann"
  - "Sacheendra Talluri"
  - "Erwin van Eyk"
  - "Cristina Abad"
  - "Philipp Leitner"
  - "Alexandru Iosup"
year: 2022
venue: "arXiv preprint"
volume: ""
issue: ""
pages: ""
publisher: ""
doi: ""
arxiv: "2205.07696"
url: "https://arxiv.org/abs/2205.07696"

# --- archive record ---
source_pdf: lets-trace-faas-benchmarking-2022.pdf
source_sha256: efe836345e3fece15096c6f322a28f115aa6deae03ae94f5f3f97ade16a57a40
pdf_pages: 19
converted: 2026-09-13
record_source: arxiv
key_insight: "Sync + async serverless patterns; I/O-bound workloads dominated by external services, not compute; orchestration overhead significant"
first_page: "Let’s Trace It: Fine-Grained Serverless Benchmarking using Synchronous and Asynchronous Orchestrated Applications Joel Scheuner Chalmers | University of Gothenburg Sweden scheuner@chalmers.se Simon Ei"
---
# **Let’s Trace It: Fine-Grained Serverless Benchmarking using Synchronous and Asynchronous Orchestrated Applications** 

Joel Scheuner Simon Eismann _Chalmers | University of Gothenburg University of Würzburg Sweden Germany scheuner@chalmers.se eismann@uni-wuerzburg.de_ Sacheen Talluri Erwin van Eyk _Vrije Universiteit Amsterdam Vrije Universiteit Amsterdam The Netherlands The Netherlands S.Talluri@atlarge-research.com E.vanEyk@atlarge-research.com_ Cristina L. Abad Philipp Leitner _Escuela Superior Politecnica del Litoral Chalmers | University of Gothenburg Ecuador Sweden cabadr@espol.edu.ec philipp.leitner@chalmers.se_ 

Alexandru Iosup _Vrije Universiteit Amsterdam The Netherlands A.Iosup@atlarge-research.com_ 

## **Abstract** 

Making serverless computing widely applicable requires detailed performance understanding. Although contemporary benchmarking approaches exist, they report only coarse results, do not apply distributed tracing, do not consider asynchronous applications, and provide limited capabilities for (root cause) analysis. Addressing this gap, we design and implement ServiBench, a serverless benchmarking suite. ServiBench (i) leverages synchronous and asynchronous serverless applications representative of production usage, (ii) extrapolates cloud-provider data to generate realistic workloads, (iii) conducts comprehensive, end-to-end experiments to capture application-level performance, (iv) analyzes results using a novel approach based on (distributed) serverless tracing, and (v) supports comprehensively serverless performance analysis. With ServiBench, we conduct comprehensive experiments on AWS, covering five common performance factors: median latency, cold starts, tail latency, scalability, and dynamic workloads. We find that the median end-to-end latency of serverless applications is often dominated not by function computation but by external service calls, orchestration, or trigger-based coordination. We release collected experimental data under FAIR principles and ServiBench as a tested, extensible open-source tool. 

## **1 Introduction** 

Establishing computing infrastructure that is easy to manage yet performs well for all applications is a longstanding goal of the computer systems community from the 1950s [85]. Emerging in the late 2010s from the integration of multiple technological breakthroughs [76], _serverless computing_ [13, 64, 75] aims to abstract away operational concerns (e.g., autoscaling) from the developer by providing fully managed cloud platforms through self-serving application programming interfaces (APIs). Developers can leverage a rich _ecosystem of external services_ (e.g., message queues, databases, image recognition), which are glued together by a Function-as-a-Service (FaaS) platform, such as AWS Lambda. For the current generation of serverless platforms, ease of management comes with important performance trade-offs and issues, including high tail-latency and performance variability [26,55], and delays introduced by asynchronous use of external services [55,58]. Thus, understanding and comparing the performance of serverless platforms is essential. Although extensive prior work exists in empirical performance evaluation [24, 38, 47] and analysis [37, 81], synthetic [23, 26] and micro-benchmarking [63], as well as server-side benchmarking [65, 73], there currently exists no serverless benchmark 

1 

that provides detailed (white-box) analysis at application level, covering production applications and invocation patterns. Addressing this gap, in this work we design, implement, and use _ServiBench (sb)_ , an application-level, serverless benchmarking suite based on distributed tracing. 

We posit in this paper that **a serverless benchmark that provides performance information at application level is necessary** . Our argument is two-fold. First, a variety of production-ready serverless applications already exist [13, 22, 39]. These applications have distinctive performance profiles but alternative approaches insufficiently cover this diversity (e.g., in external services). Second, applicationlevel benchmarks have proven useful in related fields (e.g., DeathStarBench [26] for container-based microservices, and CloudSuite [23] for scale-out workloads). They help identify architectural bottlenecks, guide application design decisions, and inspire better programming models. 

The challenge of application-level serverless benchmarking is manifold and complex. First, there is a **need to design the benchmarks, and to validate the tools that realize the benchmark in practice (challenge C1)** . The majority of existing work attempts to reverse-engineer commercial serverless systems [81], by characterizing performance aspects such as allocated CPU power by memory size [24], cold start overhead [47], scaling policies [37], or I/O speed [38]. Such studies can guide cloud users in selecting appropriate services and configurations, but their empirical results are prone to become obsolete quickly. Server-side experimentation [65, 73] allows to control the entire serverless stack to obtain detailed profiling data, but lacks tight integration with external services, which prevents realistic system-level testing of serverless applications [40]. Finally, micro-benchmarks (e.g., of CPU performance) are not representative of real applications. Summarizing, no benchmark currently: (i) supports a variety of architectural patterns that appear commonly in serverless applications, (ii) includes representative, production-grade applications and invocation patterns, (iii) provides end-to-end performance data and white-box analysis capabilities, and (iv) enables reproducible real-world experiments. 

Second, **conducting white-box analysis requires collecting end-to-end performance data, and extracting finegrained latency information (C2).** Distributed tracing [45, 61] has been popularized at Google [67] and Facebook [77], but requires a level of cooperation with the platform that is not available for serverless applications. Various approaches exist for this broad class of problems that assume ordered events and accurate timing, and such approaches can already be useful for _synchronous_ microservice architectures [57]. In contrast, many serverless applications use multiple functions and external services, and invocations can occur _asynchronously_ . No benchmark in the field currently addresses this. 

Third, we identify the **need to share tools and data for serverless benchmarking, FAIRly (C3).** Releasing software, data, and results in packages that make 



<!-- Start of picture text -->
L5 Functions<br>𝑓 1 𝑓 2<br>Async.<br>L4 Operator Services TriggerSync. ℯ 1 Trigger<br>L3 Function Management Autoscaler Registry<br>L2 Resource Orchestration<br>L1 Resources<br>Control Flow Orchestrator Trace Point Trace Initialization Execution<br><!-- End of picture text -->

Figure 1: System model of a serverless application composed of multiple functions: f1 and f2 are user-defined functions, and e1 is an external service. 

them FAIR (“findable, accessible, interoperable, and reusable” [83]) is essential in science and engineering. We address these challenges with a four-fold contribution: 

1. **Application benchmark suite (Section 3):** Addressing C1, we present ServiBench, a comprehensive benchmark suite. In it, 10 realistic open-source applications cover different forms of orchestration, synchronous and asynchronous triggers, and real-world characteristics such as programming language, size, and external service usage. ServiBench orchestrates reproducible deployments, automates realistic load generation, collects distributed traces, and provides detailed white-box analysis. 

2. **Latency breakdown analysis (Section 4):** Addressing C2, we design novel algorithms and heuristics for detailed latency breakdown analysis of distributed serverless traces. The key capability over prior work is that our approach works in a serverless context, across asynchronous call boundaries and external services. 

3. **Empirical performance study (Section 5):** Addressing the validation aspects of C1, and the overall challenge of understanding the performance of serverless applications, we conduct a comprehensive white-box analysis of serverless application performance in the AWS environment (see also Section 6). Our results cover, e.g., cold starts, tail latency, and the impact of application type and invocation patterns on performance. 

4. **FAIR release** of the ServiBench software, data, and results (Appendix A): Addressing C3, we release ServiBench on Github, and the configurations and full data ( _±_ 50 GB) on Zenodo (links anonymized). 

## **2 System Model for Serverless Applications** 

Our work assumes a system model, introduced by the SPEC Research Group, that represents the operation of tens of existing serverless platforms [74]. In this model, the serverless stack provides resources (label <mark>L1</mark> in Figure 1), whose 

2 

use is orchestrated ( <mark>L2</mark> ), enabling complex function management <mark>( L3</mark> ) such as auto-scaling and image-registry. These elements have been covered extensively by the community [9, 66]. 

The system model further includes two layers that service directly the application and are the focus of this work. Each applications is composed of a single or, more commonly, multiple user-defined functions <mark>( L5</mark> ), which can trigger asynchronously external (operator-provided) services <mark>( L4</mark> ). Figure 1 depicts a constructed example of a serverless application. There are two user-defined functions (f1 and f2). During its execution, f1 triggers synchronously an operator-provided service, e1. At the end of its execution, f1 triggers asynchronously an operator-provided orchestrator service. 

_Production-level serverless applications_ fit this model well. The functions can communicate with external services (e1), and with each other, directly via synchronous or asynchronous triggers. They can also communicate via an orchestrator, which decides on the control flow based on user-provided instructions. They can thus construct complex execution paths, using any of the operator-provided services, e.g., object stores, databases, and ML services. A _production workload_ can incorporate multiple invocation patterns, leading to complex performance behavior that incorporates not only intra-application latency, but also cross-application delays. 

We further assume there exists a _monitoring service_ , which can provide detailed performance information and in particular trace the upper layers in the serverless stack (i.e., <mark>L4</mark> and <mark>L5</mark> ). We do _not_ assume that the other layers are observable by the application; e.g., there is no server-side tracing. These assumptions match the operation of common serverless platforms, such as AWS. Although we assume the presence of _distributed tracing_ , we do _not_ assume its results are consistent and ordered across multiple components in the system or that the application triggers can only occur synchronously. This is consistent with how popular serverless platforms, such as AWS and Microsoft Azure, operate in practice. 

## **3 Design of ServiBench** 

In this section, we design ServiBench, an application-level benchmarking suite. We design around a set of 5 design principles, creating a novel architecture and benchmarking flow. The suite includes 10 representative, open-source applications. ServiBench includes a process to generate representative workloads from existing invocation logs provided by cloud operators such as Microsoft Azure. 

In the system model introduced in Section 2, identifying the latency contribution of each service to the total response time of the application is challenging. In particular, an application can take multiple paths of execution and trigger asynchronously different methods depending on runtime conditions, which breaks straightforward distributed tracing. We address this concern through a detailed design, in Section 4. 

## **3.1 Design Principles** 

Based on guidelines on benchmarking best-practices [29, 78] and inspired by the microservice benchmark suite DeathStarBench [26], we formulate the following design principles: 

1. **Representativeness:** A representative and relevant benchmark suite closely matches the characteristics of real-world applications. We select applications from industrial workshops and academic studies based on the most common serverless application types [13, 22], programming languages [22, 39], application sizes [22, 39, 66], and external services [22, 39, 66]. 

2. **End-to-end operation:** An application-level serverless benchmark should implement end-to-end functionality starting from an incoming client request, following into individual functions, across external services, ending with a synchronous response or after a chain of asynchronous event-based function triggers. We implement realistic serverless applications and instrument them using distributed tracing to track end-to-end operation. 

3. **Heterogeneity:** A heterogeneous benchmark suite should include diverse applications by different dimensions. Beyond including the most popular choice (e.g., most prevalent programming language), we strive for generalizability by covering additional applications. 

4. **Reproducibility:** A reproducible benchmark suite mitigates threats to internal validity that could affect the ability to obtain the same results with the same method under _changed conditions_ of measurements [71]. We provide automated containerized benchmark orchestration for all applications including their configurations and pinned dependencies. 

5. **Extensibility:** An extensible suite allows for adding existing serverless applications written in any programming language, using any framework, or cloud service dependencies with no or only minor code changes. We demonstrate the extensibility of our plugin-based harness by integrating existing applications maintaining their diverse structure rather than inventing new applications. 

## **3.2 High-Level Design of ServiBench** 

_ServiBench (sb)_ uses a data-driven benchmarking method based on a suite of serverless applications described in Section 3.3 and serverless invocation patterns derived from real traces as described in Section 3.4. 

Figure 2 illustrates the data flow and main processes of a benchmark execution with sb. Each serverless application provides two additional assets in addition to its source code (Figure 2, label 1 ). First, it defines deployment instructions annotated with OCI-compatible container images for 

3 

dependency-bundled deployment. This packaging enables reproducible cross-platform builds of the application and its service dependencies, which are defined through infrastructureas-code [30]. Second, a workload scenario defines how an application is invoked. This can be a single parameterized HTTP request or a probabilistic state-machine emulating users flow through a multi-action user story. The _prepare_ process builds and deploys the application into a serverless platform and performs any preparations for benchmarking such as uploading datasets or extracting service endpoints ( 2 ). 

The invocation patterns for benchmarking are derived from an invocations dataset ( 3 ). The _process_ step takes invocation logs and upscales these to finer-grained (secondlevel) invocation frequencies, following different traffic shape patterns ( 4 ). Subsequently, the _invoke_ process combines application-specific workload scenarios with generic serverless invocation patterns to invoke the application invocation endpoints with realistic serverless traffic patterns ( 5 ). This workload generation yields client logs, which are mainly used for validation during experiment analysis as described in Section 5. The main results are detailed end-to-end (e2e) traces collected from individual application components and correlated by a trace identifier passed along inter-service calls. The _analyze traces_ process ( 6 ) uses critical path analysis to perform latency breakdown analysis (see Section 4), which provides a trace breakdown summary to the experiment analysis ( 7 ). 

We implement _sb_ as a Python package that offers a CLI and SDK to orchestrate serverless application benchmarking. To integrate with sb, an application needs to provide a Python file with three lifecycle methods to prepare, invoke, and cleanup itself. Sb supports Docker to package application-specific build and deployment dependencies, and automatically manages directory mounts and provider credentials. 

We use the Azure Function Traces [66] as the invocations dataset and the k6 [32] load testing tool as the invoker. Though sb automatically configures the trace-based invocation patterns, application-specific workload scenarios are written in JavaScript. For AWS, applications have been instrumented with X-Ray [4] and the trace analyzer works with AWS services supported by X-Ray. Other providers are currently partially supported, with two applications integrated with Azure and basic deployment infrastructure for IBM Cloud and Google Cloud. Expanding support for these providers is ongoing work. 

## **3.3 Serverless Applications** 

Table 1 characterizes the 10 serverless applications in the benchmark suite. We select multiple applications for each of the most common types identified by survey studies [22, 84] except for the type of _operations and monitoring_ because such applications are difficult to test in isolation. In particular, _API_ refers to synchronously invoked web endpoints (e.g., 

|**Application**|**Type**|**Lang.**|**#**|**Externa**|**l Services**|
|---|---|---|---|---|---|
|A Minimal Baseline [7]|API|JS|1|♦||
|B Thumbnail Gen. [87]|Async|Java|2|♦<sup>�</sup>||
|C Event Processing [87]|Async|JS|8|♦<br>_△_■|�|
|D Facial Recognition [6]|Async|JS|6|♦<sup>�</sup>|⋆_♠_|
|E Model Training [34]|Async|Python|1|♦<sup>�</sup>||
|F Realworld Backend [33]|API|JS|21|♦|�|
|G Hello Retail! [53]|API|JS|10|♦<sup>�</sup>|⋆<br>�□|
|H Todo API [87]|API|Go|5|♦|�|
|I Matrix Multipl. [87]|Batch|C#|6|♦<sup>�</sup>|⋆|
|J Video Processing [34]|Batch|Python|1|♦<sup>�</sup>||



Table 1: Characteristics of each end-to-end serverless application. Abbreviations: Programming language (Lang), number of functions (#), API gateway (♦), cloud storage (<sup>�</sup> ), cloud pub/sub ( _△_ ), cloud queue (■), cloud orchestration (⋆), cloud ML ( _♠_ ), cloud DB (<sup>�</sup> ), cloud streaming (□). 

REST, GraphQL), _async_ processing applications are triggered through events (e.g., an upload to a storage bucket triggers a function), and _batch_ refers to larger computation tasks often simultaneously processed by multiple functions. 

For the dominant serverless programming languages JavaScript (JS) and Python [22, 39], we select multiple applications. The popular enterprise languages Java, C#, and increasingly Go are represented by one application each. 

Our applications are of representative size, as datasets [66] and surveys [22,39] show that most applications are composed of 10 or fewer functions. 

We cover the most popular external services used in serverless applications [22, 39, 66] with a focus on API gateways, persistency services (e.g., S3 cloud storage, DynamoDB cloud database), and cloud orchestration (e.g., AWS Step Functions). Appendix B describes and motivates each application. 

## **3.4 Serverless Invocation Patterns** 

This section describes how we derive invocation patterns from the Azure Function Traces [66], a dataset invocation logs from a commercial cloud platform over two weeks. 

### **3.4.1 Selection and Classification** 

From the 74,347 functions in the Azure traces, we selected 528 functions with relevant properties for benchmarking logs [50]. We removed 45,564 temporary functions not available over the entire two-week period and skip 15,319 timer triggers because these follow predictable periodic patterns and are typically not latency-critical. Knowing that the 18.6% most popular applications with invocation rates _≥_ 1 _/min_ represent 99.6% of all function invocations [66], we selected the 2.6% most popular functions with average invocation rates _≥_ 1 _/s_ as they are relevant for high-volume benchmarking. 

We visually identified 4 typical invocation patterns by manually classifying two time ranges for 100 of the selected 

4 



<!-- Start of picture text -->
1 source  code +  2 Data Process Order<br>Serverless  deploy scripts invocation endpoints<br>Prepare<br>Applications<br>5 end-to-end  6 trace  7<br>workload scenarios Invoke traces Analyze  breakdown Experiment<br>Traces Analysis<br>3 4<br>Invocations invocation logs invocation patterns client logs<br>Process<br>Dataset<br><!-- End of picture text -->

Figure 2: Data flow of a benchmark execution in sb. 



<!-- Start of picture text -->
Azure trace Upscaled trace<br>Fluctuating Jump<br>5<br>40 4<br>30 3<br>20 2<br>10 1<br>0 0<br>Spikes Steady<br>6 1 0<br>4<br>5<br>2<br>0 0<br>0 250 500 750 1000 1250 0 250 500 750 1000 1250<br>Time [s]<br>Num. Requests<br><!-- End of picture text -->

Figure 3: Typical serverless invocation patterns over 20 min. 

granularity of seconds while maintaining the large scale properties of the Azure traces. We chose a Hurst parameter of 0.8 as empirically determined for web traffic [17]. This indicates positive correlation over time, which means an increase in the workload is likely followed by an increase and a decrease is likely followed by a decrease. We believe this to be realistic workload as it generates patterns where workload bursts are sustained instead of oscillating between peaks and valleys. 

## **4 Detailed Distributed Trace Analysis for Serverless Architectures** 

528 functions. We first created 200 individual line plots with invocation counts over 20 minutes<sup>1</sup> and grouped similar traffic shapes into several clusters. After merging similar patterns, we identified 4 common patterns (see Figure 3): (i) _steady_ (32.5%) represents stable load with low burstiness, (ii) _fluctuating_ (37.5%) combines a steady base load with continuous load fluctuations especially characterized by short bursts, (iii) _spikes_ (22.5%) represents occasional extreme load bursts with or without a steady base load, and (iv) _jump_ (7.5%) represents sudden load changes maintained for several minutes before potentially returning to a steady base load. 

### **3.4.2 Trace Upscaler** 

The trace upscaler generates invocation rates at the granularity of seconds from per-minute invocation logs. The Azure dataset [66] reports the number of function invocations per minute. However, bursty serverless invocation rates are not uniformly distributed over a minute [79]. For example, it could be that the majority of the invocations in a single minute all occur in the first five seconds. 

To generate more realistic patterns than uniformly distributed or linearly interpolated invocation rates, we use fractional Brownian motion to synthesize perturbations at the 

> 1We explored different time resolutions (2 weeks, 1 day, 4 hours, 1 hour, 30 min, 20 min, 10 min) and found that hourly patterns are similar enough to 20 minutes, which is feasible cost-wise for repeated experimentation with many different applications under varying configurations. 

We motivate distributed tracing of serverless applications and describe how to extract the critical path and a detailed latency breakdown from distributed traces. 

## **4.1 Challenges and Background** 

Distributed tracing has been adopted for various use cases [45, 61] such as distributed profiling (i.e., latency analysis), anomaly detection (i.e., identifying and debugging rare problems), or workload modeling (e.g., identifying representative workflows). Tracing systems such as Google’s Dapper [67] or Facebook’s Maelstrom [77] help improve performance, correctness, understanding, testing, and recovery of services. These insights are even more important for highly distributed serverless architectures given their ephemeral nature. However, event-based coordination is inherently asynchronous, hence hard-to-track background workflows need to be included in the tracing and cannot be ignored as for synchronous microservice architectures [57]. The limited control in serverless environments makes users dependent on provider tracing implementations or resort to less detailed third-party or custom implementations. Further, tracing issues are common at large scale and trace analysis must detect and handle clock inaccuracy and incomplete traces. 

We represent each request as an _execution trace_ where the _critical path_ determines the end-to-end latency and the _latency breakdown_ lists and classifies each time span along the critical path as visualized in Figure 4. 

5 



<!-- Start of picture text -->
Function 1: Bucket 1: Function 2: Bucket 2:<br>User UploadImage Gateway 1 Trigger Persist Image ImageStore Images TriggerAsync Make Thumb. Thumb.Store Thumbnails<br>Gateway 1 37 Original Span<br>Function 1  434 Computation<br>Function 1  - Initialization 2956 External Service<br>Function 1  - Unaccounted 2 Orchestration<br>Function 1  - Execution 267 160 Trigger<br>Bucket 1  - Get Metadata S1 1479 Queueing<br>Bucket 1  - Upload image 342 Finalization Overhead<br>Trigger (not traced) S2 1010 Runtime Initialization<br>Queueing time 59 Container Initialization<br>Function 2 A2 337 44<br>Function 2  - Initialization 1186<br>Function 2  - Unaccounted 3 140<br>Function 2  - Execution 4200 734<br>Bucket 1  -  Download 1247 237<br>Bucket 2  - Upload<br>Time [ms]<br><!-- End of picture text -->

Figure 4: Simplified depiction of an _execution trace_ (Definition 1) with annotated _latency breakdown_ (Definition 3). Data collected from App-A with two cold starts. Values represent time in milliseconds. Labels Sync/Async refer to Figure 5. 

**Definition 1** An _execution trace_ of a serverless application is a causal-time diagram of the distributed execution of a request, where a node is a _trace span_ that corresponds to an individual unit of work (e.g., computation) and an edge represents a causal relationship through a synchronous or asynchronous invocation. Each trace span contains a start and end timestamp and is correlated by a trace id. 

**Definition 2** A _critical path_ in an execution trace is the longest path weighted by duration, which starts with a client request and ends with the trace span that has the latest end time. This definition of end-to-end latency includes asynchronous background workflows that do not return to their parent spans to capture the event-based nature of serverless systems. Hence, our definition differs from a critical path of a synchronous client response in microservices [57]. 

**Definition 3** A _latency breakdown_ of an execution trace is the most detailed list of time segments along the critical path without any temporal gaps. This explicitly includes transitions between trace spans, which are often implicit in an execution trace. In its aggregated form<sup>2</sup> , each time segment is classified and summed up by the following categories common to serverless applications: (i) _computation_ represents the actual processing time of serverless functions. (ii) _external service_ represents the time waiting for the completion of a services request (e.g., database query, file upload to a storage services). (iii) _orchestration_ represents time spent coordinating serverless function executions by workflow engines (e.g., AWS Step Functions) or API gateways dispatching requests to functions. (iv) _trigger_ represents the implicit transition time between an event and a function bound to this event (e.g., time between 

> 2We use high-level categories for better readability and cross-application comparison as the full trace breakdown is very detailed. Individual external services, such as cloud storage, could be classified separately if needed. 

enqueuing a message until the event is dispatched to a function). (v) _queuing_ represents the time spent in function worker queues before it starts executing. (vi) _container initialization_ represents the time it takes to provision the function execution environment. (vii) _runtime initialization_ represents the time it takes to initialize the function language runtime during a cold start. (viii) _finalization overhead_ represents cleanup tasks after function execution and before freezing the sandbox. 

## **4.2 Latency Breakdown Extraction** 

We first extract the _critical path_ of an _execution trace_ and subsequently refine it into a detailed _latency breakdown_ . 

To extract the critical path, we use Algorithm 1, which is a modified version of the weighted longest path algorithm proposed in the context of microservices [57]. Our modifications support asynchronous invocations, unordered traces, and refined heuristics to handle timing issues [52] in fine-grained serverless tracing. A stack with all parent spans of the last ending span is used to only recurse into child spans connected to the last ending span. Line 9 defines the sorting order for child spans primarily by the _endTime_ and secondarily by the _startTime_ . The secondary sort key is required to handle the special case of a single trace span with a duration of 0 milliseconds. Our heuristic HAPPENSBEFORE detects sequential relationships and ISASYNC detects asynchronous invocations. They support a configurable error margin (default 1ms) to gracefully handle minor clock inaccuracies by implementing temporal comparisons such as _t_ 1 _< t_ 2 with _t_ 2 _− t_ 1 + _margin_ . 

We extract the detailed latency breakdown along the critical path by identifying and categorizing every time segment while accounting for all gaps between spans. Figure 5 visualizes the common cases for synchronous and asynchronous invocations while iterating pairwise ( _current_ , _next_ ) over the critical path. For synchronous invocations, we distinguish two different cases: _Sync1_ handles a traditional synchronous invocation 

6 

**Algorithm 1** Critical Path Extraction, based on [57]. 

**Require:** Serverless execution trace _T_ with 

_span_ attributes _childSpans_ , _startTime_ , _endTime_ and stack _S_ with all parent spans of the last ending span 

1: **procedure** _T_ .CRITICALPATH( _S_ , _currentSpan_ ) 

- 2: _path ←_ [currentSpan] 

- 3: **if** _S_ .top() == _currentSpan_ **then** 4: _S_ .pop() 5: **end if** 6: **if** _currentSpan.childSpans_ == _None_ **then** 7: Return _path_ 8: **end if** 9: _sortedChildSpans ←_ sortAscending( 



<!-- Start of picture text -->
Sync1:  Parent into child Sync2:  Transition across common parent<br>current parent<br>next next<br>current<br>Async1:  Overlapping Async2:  Trigger gap<br>current current<br>next next<br><!-- End of picture text -->

Figure 5: Extraction cases of latency breakdown (red segments) for pairs of current and next nodes on the critical path. 

   - _currentSpan.childSpans_ , by=[ _endTime_ , _startTime_ ]) 

- 10: _lastChild ← sortedChildSpans.last_ 

- 11: **for** each _child_ in _sortedChildSpans_ **do** 

- 12: **if** _child_ .HAPPENSBEFORE( _lastChild_ ) and not _currentSpan_ .ISASYNC( _path_ .last) **then** 

- 13: _path_ .extend(CRITICALPATH( _S, child_ )) 14: **end if** 

- 15: **end for** 

- 16: **if** ( _currentSpan_ .ISASYNC( _lastChild_ ) and _S_ .top() == _lastChild_ ) or 

   - (not _currentSpan_ .ISASYNC( _lastChild_ ) and 

   - not _currentSpan_ .ISASYNC( _path_ .last) **then** 

- 17: _path_ .extend(CRITICALPATH( _S, lastChild_ )) 18: **end if** 

- 19: Return _path_ 

- 20: **end procedure** 

21: **procedure** _current_ .HAPPENSBEFORE( _next_ ) 

type (e.g., function) as annotated in Figure 4. 

## **5 Experimental Results** 

We use in this section ServiBench to comprehensively benchmark the performance of a popular serverless platform. We deploy ServiBench on the serverless platform AWS Lambda, which various reports [22,69] indicate is much used by serverless applications in production. 

ServiBench supports many real-world performance scenarios, from which we focus in this work on (1) latency breakdown to understand the performance of warm invocations and of cold starts, and on (2) the impact of invocation patterns on (median) end-to-end latency. We make 6 observations, and discuss their implications for serverless practitioners and researchers in Section 5.4. 

- 22: Return _current.endTime < next.startTime_ 

- 23: **end procedure** 

- 24: **procedure** _current_ .ISASYNC( _next_ ) 25: Return _next.endTime > current.endTime_ 26: **end procedure** 

from a _current_ parent span into a _next_ child span. _Sync2_ handles a potentially recursive transition from the _current_ span on a synchronous invocation stack across a common _parent_ into its _next_ child span. For asynchronous invocations, we distinguish two cases: _Async1_ handles if the _next_ child span overlaps with the _current_ parent span. _Async2_ handles if there is a gap between the _current_ parent span and the _next_ child span. This scenario frequently occurs in serverless systems when triggering a function using a slow trigger. There is a third case that we can currently not detect, which is structurally equivalent to _Sync1_ except that the call to _next_ is asynchronous. To make this case detectable, trace specifications could define labels for synchronous and asynchronous parent-child relationships as discussed for Open Telemetry [54]. Finally, we assign an activity label (e.g., computation) to each breakdown segment depending on the span 

## **5.1 Experiment Design** 

We conduct a performance benchmarking experiment [29] with an open-loop load generator in the data center region Northern Virginia (us-east-1) as commonly used by other serverless studies [10, 14, 16, 81, 82]. We collected over 7.5 million traces, through over 12 months of experimentation in 2021 and 2022. 

**Application configuration** All functions are configured with the same memory size of 1,024 MB as this provides a balanced cost-performance ratio [21] between the minimal memory size of 128 MB (heavy CPU throttling) and the maximum memory size for a single CPU core of 1,769 MB [5] (inefficient for non-CPU-intensive load). For applicationspecific memory size tuning, we refer to _aws-lambda-powertuning_ [12], systematic literature reviews [59, 63], and many empirical studies [2,21,24,42,80,81,86]. All supported cloud services (API Gateway, Lambda, Step Functions) have distributed X-Ray tracing enabled to trace every request. For applications with multiple endpoints, we present one repre- 

7 



<!-- Start of picture text -->
Planned Sent Executed Ratio<br>Executed vs. Planned<br>1.10<br>1.05<br>225 1<br>0.95<br>0.9 0<br>Sent vs. Planned<br>200 1.10<br>1.05<br>1<br>0.95<br>0.90<br>0 10 20 30 40 50 0 250 500 750 1000<br>Time [s] Time [s]<br>Ratio<br>Reqs per Second<br><!-- End of picture text -->

Figure 6: Comparison of per-second invocation rates planned vs. sent vs. executed (left) and validation ratio for pairwise comparison (right). 

sentative endpoint in the paper and refer to the replication package for detailed results. 

**Load generator** For accurate load generation, we deploy an over-provisioned EC2 instance of the type _t3a.large_ in the same region as the serverless applications. We validate persecond invocation rates for accurate load generation (planned vs. sent) by correlating the load configuration with the client logs and actual load serving (generated vs. executed) by correlating the client logs with the backend traces. We combine visual comparison (see Figure 6) with FastDTW [60], an approximate Dynamic Time Warping (DTW) algorithm. We monitor application error rates client-side by checking response status codes and server-side by checking for any exceptions in each trace. Finally, we investigate any invalid traces due incomplete or invalid trace data following both logical and time-based validation. 

## **5.2 Latency Breakdown** 

We first drill down into the end-to-end latency of serverless applications to identify critical components using sb (Section 3) and trace breakdown extraction (Section 4). This applicationlevel perspective complements existing work, which primarily focused on micro-benchmarking individual components or reporting client-side response times for synchronously orchestrated applications [59, 63]. As a baseline, we focus on warm invocations and subsequently compare the latency penalty of cold invocations and tail latency. 

**Method.** For each of the 10 applications from Section B, we send 4 bursts of 20 concurrent requests with an inter-arrival time of 60 seconds between each burst. The first burst triggers up to 20 cold invocations used in Section 5.2.2 and after the function completes within 60 seconds, the following 3 bursts trigger more warm invocations used for tail-latency analysis in Section 5.2.3 and as baseline in Section 5.2.1. To collect enough samples under the same conditions, we conduct 10 trials and 14 repetitions resulting in up to 8,400 warm 



<!-- Start of picture text -->
Activity Computation External service Orchestration<br>Trigger Queueing Finalization overhead<br>1 1 194 11 17 7 2 66<br>531 6<br>0.75 685 105<br>1040<br>54 1218<br>0.50 22 40 8632 142<br>1136<br>16 23<br>1223<br>0.25<br>96 23 485<br>281 22 310<br>0<br>A B C D E F G H I J<br>Application<br>Latency breakdown<br><!-- End of picture text -->

Figure 7: Latency breakdown of warm invocations as median fraction of end-to-end latency. Values inside the bar-stacks represent absolute time per activity, in milliseconds. 

invocations (3 _×_ 20 _×_ 10 _×_ 14)<sup>3</sup> . For each of the 10 trials, we invoke each application using round-robin scheduling with inter-trial times of 50 minutes to trigger cold invocations in the first burst for Section 5.2.2. Before each of the 14 repetitions of trials, we re-deploy each application to ensure a clean state. We use trace analysis to detect cold invocations through the presence of _Initialization_ segments [8]. For applications with chained functions, we ignore “partial cold starts” and only consider “full” warm or cold invocations, where every function in the critical path shares the same cold start status. 

### **5.2.1 Warm Invocations** 

Frequently invoked applications often get warm invocations. 

**Results.** The relative latency breakdown in Figure 7 shows the median latency for each activity introduced in Definition 3. App-A exemplifies the orchestration overhead (22 ms) of a common serverless pattern where an API gateway is connected to a function. Lightweight applications such as App-H are similarly dominated by _orchestration_ time (23 ms) because they do minimal computation work and use fast external services (e.g., 6 ms database insert). App-E and App-J are examples of computation-heavy workloads. External services like blob storage or computer vision APIs are often the dominating factor, especially for many I/O operations (App-I) or larger files (App-D). Asynchronous applications are typically dominated by transition delays due to trigger and queuing time as demonstrated by the applications App-B and App-C. 

> 3A related study [72] uses 3,000 samples for individual functions; we target more per-application samples as requests can be distributed across endpoints. 

8 



<!-- Start of picture text -->
Activity Computation External service Orchestration<br>Trigger Queueing Finalization overhead<br>Runtime initialization Container initialization<br>1 61 109 150 27 46 103 1803 275<br>4425<br>0.75 111<br>167 513<br>976 2054 3810 528 2221<br>0.50 2939<br>954<br>406<br>0.25 4509 2041<br>98 266<br>0 513 303 713 759 160 648<br>A B C D E F G H I J<br>Application<br>Latency-penalty breakdown<br><!-- End of picture text -->

Figure 8: Latency-penalty breakdown for cold invocations compared to the baseline of warm invocations (Figure 7) as fraction of the difference between the medians. Values inside the bar-stacks are absolute, in milliseconds (ms), e.g., for App-B, Computation takes 4,425 ms longer. 

**Observation 1:** The median end-to-end latency of serverless applications is often dominated by external service calls and synchronous orchestration or asynchronous triggerbased coordination. The actual computation time in serverless functions is relatively little except for inherently compute-heavy workloads. 

### **5.2.2 Cold Starts** 

We now study which time categories contribute to higher cold start latency using the results from Section 5.2 as a baseline. Tracing cold starts requires access to timestamps captured within provider-internal infrastructure. Sb can extract these internal timestamps from AWS X-Ray traces and distinguish between container and runtime initialization time, which would only be possible for self-hosted [73] or providerinternal [1, 11] systems otherwise. Insights on cold starts are relevant for applications that are invoked irregularly (e.g., inter-arrival times > 10 minutes) or exhibit bursty invocation patterns and, hence, need to provision new function instances. 

**Results.** Figure 8 shows the latency difference between the medians for cold invocations compared to warm invocations. App-A depicts a common initialization overheads for a function behind an API gateway of 265 ms (98+167) in line with prior cold start studies for Node.js by Wang et al. [81, Figure 6] and Maissen et al. [46, Figure 7]. Our results are more detailed and reveal differences for realistic applications. Our trace details show that runtime initialization typically accounts for the majority of cold start overhead compared to container initialization. For App-A, the container initialization time of 98 ms is ~20 ms faster than the boot times for the 



<!-- Start of picture text -->
Activity Computation External service Orchestration<br>Trigger Queueing Finalization overhead<br>1 3 226 32 84 12 61 208<br>99 543 29<br>0.75 1618 57 40 36<br>183 603<br>1299<br>0.50 58 2427<br>115 57 1554<br>0.25 1126 73 85 33<br>202 305<br>250<br>0 2 164<br>A B C D E F G H I J<br>Application<br>Latency-penalty breakdown<br><!-- End of picture text -->

Figure 9: Latency-penalty breakdown for slow invocations compared to baseline of warm invocations (Figure 7) as fraction of the difference between the median and 99<sup>th</sup> percentile. Values inside the bar-stacks are absolute, in milliseconds (ms), e.g., for App-J, the Cloud storage service adds 2,427 ms of delay for slow invocations; this accounts for ~90% of the tail-latency slowdown. 

underlying Micro VMs as reported for pre-configured Firecracker [1, Figure 6]. In comparison to other applications, the relative latency penalty remains similar (c.f., App-J). However, other realistic applications have much higher absolute initialization times due to large packaged dependencies and chains of multiple functions in the critical path. 

Beyond runtime and container initialization, other categories can add cold start overhead that is often overlooked. Computation can contain conditional code executed only upon cold starts or trigger one-off optimizations such as just-intime compilation for interpreted languages [51] exemplified by the applications App-B in Java and App-I in C#. External service time can add connection overhead due to extra authentication upon cold starts (e.g., App-B caches S3 authentication) or database connection setup (e.g., App-H connects to DynamoDB). Finally, the following categories related to application coordination remain unaffected by cold starts: orchestration, trigger, queuing, and instrumentation overhead. 

**Observation 2:** Runtime initialization and container initialization add most overhead for cold invocations but external service connection initialization and one-off computation tasks can also contribute. 

### **5.2.3 Tail Latency** 

Tail latency is increasingly important at scale for cloud providers [19] and hence particularly challenging for massive multi-tenant serverless systems. Prior studies [38, 55, 72, 81] conducted micro-benchmarks to measure tail of individual serverless components. By leveraging our trace analysis (Section 4), we can directly identify which time categories contribute to tail latency (99th percentile) for entire applications. 

9 

|A<br>200|B<br>37|C<br>50|D<br>25|E<br>22|F<br>167|G<br>154|H<br>200|I<br>10|J<br>25|
|---|---|---|---|---|---|---|---|---|---|



Table 2: Invocation rates (in reqs./s) used per application, set at 50% of the achieved load in the scalability pre-study. 

**Results.** Figure 9 shows that external services cause major variability. In particular, storing a large file (+2,429 ms for App-J) causes massively more tail-latency delay than storing many chunks of small files (+602 ms for App-J). Database services contribute less to tail latency than object storage as demonstrated by the applications App-C, App-F, App-G, and App-H with latency penalties between 35 ms and 99 ms. 

Another factor of tail latency is the serverless overhead for orchestrating synchronous applications (i.e., _orchestration_ time) and asynchronous applications (i.e., _trigger_ and _queuing_ time). These categories double or triple their latency in comparison to the baseline in Figure 7. Computation is inherently variable in a multi-tenant system but contributes at most 25% to the latency penalty for compute-heavy App-E. 

**Observation 3:** Tail latency is primarily caused by external services, particularly by object storage. 

## **5.3 Invocation Patterns** 

Real-world applications exhibit diverse invocation patterns [66] but prior work rarely investigated dynamic workloads over time [38] or different invocation patterns [37] and if so, using artificial applications, patterns, and one-time bursts [10, 72, 81]. It remains unclear how different invocation patterns derived from the Azure Function Traces [66] (Section 3.4) affect the end-to-end latency of serverless applications. To address this gap, we investigate the performance effect of varying invocation rates over time under an equivalent average invocation rate. 

**Scalability prestudy.** We conducted a prestudy to adjust the average invocation rates to our 10 heterogeneous applications. Using the same invocation rate or concurrency level for all applications is inappropriate because it overloads some applications while others remain close to idle<sup>4</sup> . Therefore, we test increasing load levels with constant arrival rates for 90 seconds until an application exceeds a rate of 5% for trace errors or invalid traces twice in succession. Trace-based root cause analysis identified rate limits and function tracing issues<sup>5</sup> as common. To avoid overloading an application, we select 50% 

> 4We collected over 700K traces for App-B to App-J using the invocation patterns in Section 3.4 with an average rate of 20 reqs/sec. We tried different concurrency levels, but noticed that long-running applications were overloaded and short-running applications were served by few function instances. 

> 5We reported this and additional issues related to clock drifting and trace correctness to AWS for further investigation. 



<!-- Start of picture text -->
B C<br>1<br>0.75 Workload type<br>0.50 constant<br>0.25<br>0 fluctuating<br>1 2 3 4 5 0.1 0.2 0.3 jump<br>D F<br>1 on_off<br>0.75<br>0.50 spikes<br>0.25 steady<br>0<br>1.6 2 2.4 2.8 3.2 0.08 0.12 0.16<br>Trace duration [s]<br>ECDF<br><!-- End of picture text -->

Figure 10: End-to-end latency for different invocation patterns clipped at the 99th percentile due to extreme long tail. 

of the achieved load level as target average invocation rate for parameterizing the invocation patterns (Table 2). 

**Method.** We treat each application from Table 1 with 2 artificial and 4 realistic workloads derived from real-world traces as described in Section 3.4. The artificial workloads serve as baseline for fully _constant_ load and maximal burstiness simulated by _on_off_ alternations with load for 1 second and idle time of 3 seconds. We scale the average invocation rate per-application following Table 2. We discard warmup measurements of the first 60 seconds as the actual invocation rate can deviate from the target rate in the first second and initial cold starts dominate the start of every experiment. 

**Results.** Figure 10 shows the partial CDF of the e2e latency for applications that accurately followed the target invocation pattern (<10% deviation from target invocation rate and error metrics). The median latency is unaffected by invocation patterns as shown by the overlapping CDF curves. Percentiles up to p99 clipped in the CDF also show no relevant difference with the exception of App-D, where the peak invocation rates of the _spikes_ workload reach the rate limit of the facial recognition service causing external service delays. 

The number of initial cold starts differs by invocation pattern but remains very low after the 60 seconds warmup time. The _on_off_ and _spikes_ patterns have higher peak invocation rates and trigger more initial cold starts. However, after the warmup time, additional cold starts are rare (below 10). 

**Observation 6:** Different invocation patterns do not meaningfully affect the median end-to-end latency. 

## **5.4 Discussion** 

Our results emphasize the importance of serverless benchmarking that integrates fine-grained latency breakdown analysis, realistic invocation patterns, and varied benchmark ap- 

10 

plications. Furthermore, our experiments lead to relevant implications for serverless practitioners and researchers. 

**Serverless fulfills its core promise of stable performance under bursty workloads.** Our results show that serverless is indeed well-suited for bursty workloads after initial cold starts and when staying below platform-specific rate limits. Hence, serverless fulfills its promise of built-in scalability under the given load levels for our 10 applications. This result was somewhat unexpected, especially contrasting with prior research [10, 38, 72]. However, of course, bursty workloads may still negatively impact performance on different platforms or with even more rapid bursts than what we evaluated (e.g., per-microsecond bursts rather than per-second bursts). 

**Slowdowns are caused by control flow and coordination, not computation.** Our results suggest that future research should go beyond computation-optimization approaches [2, 3, 21], given how little computation time contributes to the end-to-end latency of many applications. The high fraction of external service time shows that fast data exchange between stateless functions remains a key challenge for serverless applications. Many applications would benefit from lowlatency storage solutions such as Pocket [35], Shredder [90], or Locus [56]. Finally, efficient function coordination through triggers [44, 55] and workflow orchestration [41] deserves more research attention given the high transition delays. 

**Cold start times are best improved by debloating language runtimes.** Language runtimes should be the primary focus for optimizing cold start latency given their major impact, adding >500 ms overhead for most applications. Runtimes were not designed for serverless architectures and recent optimizations for Java [25] and .NET [62] achieve large speedups of up to 10 _×_ , though sometimes at the cost of more memory usage or larger deployment sizes. Debloating system stacks [36] and application dependencies [68] is another promising optimization motivated by large initialization overheads for applications with large dependency trees (e.g., App-E and App-J). Alternatively, serverless developers can select languages with lower runtime initialization overhead, such as Golang [46]. 

**The main cause of tail-latency problems for warm invocations are external services and poorly chosen triggers.** Latency-critical applications should carefully choose external services and trigger types. Measurement studies covering different external services can guide the initial selection process [38, 55, 72, 81]. Our results confirm these findings and identify cloud storage as key contributor to performance variability [72]. Beyond that, sb can provide insights about alternative application implementations. For example, applications using database services (App-C, App-F, App-G, 

App-H) exhibit better tail latency than those using cloud storage (App-B, App-I, App-J). However, initializing a database connection can add additional cold start delay (c.f., Figure 8). For asynchronous orchestration, choosing appropriate trigger types is crucial as the cloud storage trigger introduces massive tail latency (e.g., App-B in Figure 7). In contrast, the pub/sub trigger used in App-C adds minimal tail latency. However, queuing time may become an issue as non-HTTP-triggered functions have lower scheduling priority [70]. 

## **5.5 Limitations** 

Despite careful design, we cannot avoid a small number of limitations in our design and results. First, **all results reported in Section 5 are specific to the AWS serverless platform** . Conceptually, ServiBench enables benchmarking a wider range of cloud providers. However, cloud providers may not provide detailed tracing information comparable to AWS’ X-Ray, preventing in-depth analysis. Following improved tracing capabilities, we are currently adding support for Microsoft Azure. 

Second, **we do not tune Lambda memory sizes for individual benchmark applications or functions** . This is a common decision in benchmark design, to increase fairness of comparison. Future research should investigate ideal settings for each application in our benchmark. 

Third, **the load generator currently supports invocation patterns on a per-second granularity** . For simulating extremely bursty workloads, more fine-grained configuration would be necessary, for example to configure a burst that happens within a few milliseconds. This may explain why we observed only a limited impact of different invocation patterns on end-to-end latency in Section 5.3. 

Last, we identify but **do not address the possible issue of long-term performance changes in cloud settings** . Cloud providers iterate rapidly and also operational policies can change, so performance may change or even vary over time. Future work could address this situation through techniques such as periodic, long-term measurements. 

## **6 Related Work** 

This work complements and greatly extends a large body of work on serverless benchmarks and performance analysis. 

**Serverless benchmarks and measurement frameworks** : Table 3 compares ServiBench with the most important serverless benchmarks and performance frameworks. Our study (i) has a wider scope with more applications, functions, and services, and in particular with more than one function or service, (ii) adds realistic applications and invocation patterns based on real-world characteristics [22, 66, 84], (iii) does not rely on low-level, server-side tracing, not available for public serverless platforms, and (iv) enables analysis across a variety of situations common in production, including synchronous 

11 

|**Reference**|**Focus**||**Sco**|**pe**||**Invocati**|**on Patterns**|**Insig**|**hts**||
|---|---|---|---|---|---|---|---|---|---|---|
|||apps|func/app|micro|langs|services|concurrent|trace-based|white box|async|
|faas-profiler [65]|Server-level overheads|5|1|28|2|0|||||
|vHive [73]|Cold-start breakdown|9|1|0|1|1|||||
|ServerlessBench [86]|Diverse test cases|4|1-7|10|4|1|||||
|SeBS [14]|Memory size impact|10|1|0|2|1|||||
|FunctionBench [34]|Diverse workloads|8|1|6|1|1|||||
|FaaSDom [46]|Language comparison|0|-|5|4|0|||||
|BeFaaS [27]|Application-centric|1|17|0|1|1|||||
|**ServiBench (this work)**|White-box analysis|10|1-21|0|5|7|||||



Table 3: Summary of related serverless benchmarks. 

and asynchronous invocations, end-to-end tracing including external services, and fine-grained white-box analysis. 

Closest to our work, BeFaaS [27] is an applicationcentric benchmarking framework, but uses only synchronous function-chains and a single external service (an external database). BeFaaS enables cloud-agnostic tracing through chained functions, however, the language-specific architecture does not support the analysis of orchestration, queueing, trigger, finalization overheads, and container and runtime initialization. 

**Performance analysis of serverless platforms** : Performance is an important and commonly studied aspect of serverless computing. Over 100 studies from academia and industry have already appeared [28,59,63,88]. Commonly investigated topics include scalability [37, 49], cold starts [48, 81], performance variability [15, 38], instance recycling times [43, 81], and the impact of parameters such as memory size [24,89], or programming language [20, 31]. These studies tend to rely on single-purpose micro-benchmarks and rarely utilize tracing data. Further, reproducibility [71] remains a big challenge in serverless performance studies, as analyzed recently [63]. 

collecting over 7.5 million execution traces. We observe that median end-to-end latency is most often dominated by external service calls, orchestration, or by waiting for asynchronous triggers. Excessive tail latency is similarly caused more by external services (particularly object storage) than any computation inherent to the serverless applications. Regarding cold starts, our results indicate that investment into simplifying runtime environments or slimming them down (e.g., as Golang does) is the most promising angle to speed up scaling. Finally, our experiments confirm the AWS platform can react effectively to workload differences, even to challenging bursty invocation patterns, for most applications. 

In the future, ServiBench, and the general serverless benchmarking concepts demonstrated by it, can be used by practitioners to evaluate in-detail performance problems in their own applications or serverless platform of choice. Platform engineers can use our approach and tooling to further improve their offerings. We envision ServiBench to become an integral part of the evaluation of future serverless research contributions, through its current features, and as an extensible basis. 

## **Acknowledgements** 

## **7 Conclusion** 

Due to their compositional nature, serverless applications and the platforms executing them are challenging to benchmark. We designed and implemented ServiBench, an open-source, application-level, serverless benchmarking suite. Unlike existing approaches, ServiBench: (1) leverages a suite of 10 diverse and realistic applications (importantly, including both synchronous and asynchronous cases), (2) extracts invocation patterns from cloud-provider data and generates realistic workloads, (3) supports end-to-end experiments, capturing fine-grained application-level performance and enabling reproducible results, (4) proposes a novel algorithm and heuristics to enable white-box analysis even for asynchronous applications and data produced by (distributed) serverless tracing, and (5) supports comprehensive performance analysis for real-world scenarios such as cold starts and tail latency. 

Using ServiBench, we conducted a comprehensive, largescale empirical investigation of the AWS serverless platform, 

We are grateful to the SPEC Research Group<sup>6</sup> for fruitful discussions and want to thank Johannes Grohmann, Sean Murphy and Jan-Philipp Steghöfer for their contributions. Special thanks go to our research assistants Simon Trapp and Ranim Khojah for supporting the integration of applications. We appreciate the generous support of our industry partners enabling large-scale evaluation and detailed investigation of tracing issues with the AWS service teams. This work was partially supported by the Wallenberg AI, Autonomous Systems and Software Program (WASP) funded by the Knut and Alice Wallenberg Foundation. 

## **A Replication Package** 

We provide a detailed replication package with two main goals. First, we want to enable the replication of our results 

> 6https://research.spec.org/ 

12 

by independent researchers to make the results reproducible. This also allows to track how the reported performance properties evolve over time. Secondly, we want to enable the use of ServiBench in further studies as the reported analysis in Section 5 covers only a small subset of the analysis enabled by our tool. Further studies could for example analyze different styles of applications (e.g., scientific workflows), different workload patterns (e.g., scheduled jobs), investigate influencing factors for different latency components (e.g., what influences the orchestration delays), or use ServiBench to analyze novel approaches that build on top of public serverless platforms [18, 21, 44]. 

The key component of our replication package is our opensource tool ServiBench, which encompasses the benchmark harness, the trace upscaler for the azure functions traces, and our latency breakdown analysis. It comes with ten realistic serverless applications out of the box and instructions for the integration of additional applications. The ServiBench tool fully automates the application deployment, load generation, metric collection, and trace analysis for the performance analysis of serverless applications. To enable the full replication of the presented results, we additionally include our scripts for the visual inspection of the azure trace dataset, the raw data collected during our measurements, and the scripts to replicate any analysis and figure from Section 5. The replication package is currently available as an anonymous GitHub repository<sup>7</sup> and will be archived to Zenodo with a DOI upon publication. 

## **B Serverless Application Description** 

This section describes the architecture and functionality of each application introduced in Table 1. For further details on implementation details, such as usage profile, or service configuration, we refer to our replication package. 



<!-- Start of picture text -->
User ♢  Gateway Function<br><!-- End of picture text -->

Figure 11: **Minimal Baseline (App A)** emulates an HTTP request sent to the API Gateway which triggers a simple serverless function, and returns a response. 



<!-- Start of picture text -->
User ♢  Gateway ⊗  Bucket1: Images Async ⊗Thumbnails  Bucket2:<br>Trigger<br>Function1: Function2:<br>Persist Image Generate Thumbnail<br><!-- End of picture text -->

Figure 12: **Thumbnail Generator (App B)** generates a thumbnail of an image uploaded to a storage bucket. The first function implements an HTTP API to upload an image to a storage bucket. The storage event then triggers a second function to generate a thumbnail of the image and store it in another storage bucket. 



<!-- Start of picture text -->
♢  Gateway ⬛  Queue1: ⬛  Queue2: ⊙  Database1:<br>Input Ingested Results<br>Function1: Function2:  Function3:<br>Generate Event Ingest Event Process Event<br><!-- End of picture text -->

Figure 13: **Event Processing (App C)** generates and inserts events into an input queue. The queue triggers a function which pre-processes the event and places it in the ingested queue. The placement of an event in the ingested queue triggers another function to process the event and store the results in the database. 



<!-- Start of picture text -->
🟊  Orchestrate Logical Control Flow<br>Function4:<br>♢  Gateway Make<br>Thumbnail<br>Function1: Function2: Function3: Function5:<br>UploadPhoto Detect Face Is Duplicate? Index Face Store<br>Metadata<br>♠ Image Detector 1: ♠ Image Detector 3:<br>Index Face<br>Detect Face ♠ Image Detector 2: ⊗  Bucket1: ⊙  Database1:<br>User Detect Duplicate Thumbnails Metadata<br><!-- End of picture text -->

Figure 14: **Facial Recognition (App D)** app takes a user uploaded image, extracts a face from it, and detects if the face already exists in the database. If the face does not already exist in the database, the app indexes the face and saves a thumbnail of the face to object storage. 



<!-- Start of picture text -->
♢  Gateway<br>User ⊗  Bucket1: Function1: ⊗  Bucket2: Trained<br>Datasets Train Model Models<br><!-- End of picture text -->

Figure 15: **Model Training (App E)** application reads training datasets from object storage, trains machine learning models on those datasets, and stores the trained models in another object storage bucket again. The model is a logistic regression to predict review sentiment scores on the Amazon Fine Food Review dataset. 

> 7https://github.com/ServiBench/ReplicationPackage 

13 



<!-- Start of picture text -->
Functions:<br>Handle Different Routes<br>User ♢  Gateway: ⊙  Database:<br>Route Requests User/Article DB<br><!-- End of picture text -->

Figure 16: **RealWorld Backend (App F)** uses a functions to create, read, update, and delete user and article information stored in a database. 



<!-- Start of picture text -->
♢ Gateway Generate Event Function1:  Event Queue⬛  Queue1: Process Events Function2:  ⊙  Database1:<br>Store<br>🟊  Orchestrate Database<br>User Send Function3:  Function4:  ⊗  Bucket:<br>SMS Get Photos Upload Photos Photos<br><!-- End of picture text -->

Figure 17: **Hello Retail! (App G)** is a retail inventory catalog application backed by a database. Users can upload product information and categorize products into categories. Supports sending an SMS if a product does not have an image. Uploaded images are stored in object storage. 



<!-- Start of picture text -->
Functions:<br>Handle Different Routes<br>User ♢  Gateway: ⊙  Database:<br>Route Requests ToDo Database<br><!-- End of picture text -->

Figure 18: **Todo API (App H)** is a simple to-do app which uses a FaaS to create, read, update, and delete todos stored in a database. 



<!-- Start of picture text -->
Function1: 🟊  Orchestrate<br>Generate<br>Matrix<br>♢  Gateway Write result<br>Read<br>Results<br>Function2:<br>Distribute<br>⊗  Bucket2: Function3:<br>Work<br>Results Build Result<br>Read Sub- Control<br>matrix Function2: Flow<br>User ⊗  Bucket1: Multiply Sub-matrix DataFlow Function4:<br>Sub-matrices Generate Report<br>...<br><!-- End of picture text -->

Figure 19: **Matrix Multiplication (App I)** generates a random matrix, partitions the matrix, and distributes it for multiplication. Workers perform the multiplication and write the results to S3. The results are then combined to get the final result of the multiplication. The app is directed by an orchestration service. 



<!-- Start of picture text -->
♢  Gateway<br>User ⊗  Bucket1: Videos Process Video Function1: ⊗Processed  Bucket2: Videos<br><!-- End of picture text -->

Figure 20: **Video Processing (App J)** application reads videos from object storage, applies a greyscale filter, and transcodes them. The transcoded videos are stored in object storage. 

## **References** 

- [1] Alexandru Agache, Marc Brooker, Alexandra Iordache, Anthony Liguori, Rolf Neugebauer, Phil Piwonka, and Diana-Maria Popa. Firecracker: Lightweight virtualization for serverless applications. In _17th USENIX Symposium on Networked Systems Design and Implementation NSDI_ , pages 419–434, 2020. 

- [2] Nabeel Akhtar, Ali Raza, Vatche Ishakian, and Ibrahim Matta. Cose: Configuring serverless functions using statistical learning. In _IEEE INFOCOM 2020 - IEEE Conference on Computer Communications_ , 2020. 

- [3] A. Ali, R. Pinciroli, F. Yan, and E. Smirni. Batch: Machine learning inference serving on serverless platforms with adaptive batching. In _SC20: International Conference for High Performance Computing, Networking, Storage and Analysis_ , pages 972–986, 2020. 

- [4] Amazon Web Services, Inc. Amazon X-Ray. https: //aws.amazon.com/xray/. Last accessed: Jan 2022. 

- [5] Amazon Web Services, Inc. Configuring function memory (console). Lambda documentation, https://docs.aws.amazon.com/ lambda/latest/dg/configuration-functioncommon.html#configuration-memory-console. Last accessed: Jan 2022. 

- [6] Amazon Web Services, Inc. Facial Recognition. https: //image-processing.serverlessworkshops.io. Last accessed: Jan 2022. 

- [7] Amazon Web Services, Inc. Minimal Baseline. https://serverlessland.com/patterns/ apigw-lambda-cdk. Last accessed: Jan 2022. 

- [8] Amazon Web Services, Inc. Using AWS Lambda with AWS X-Ray. https://docs.aws.amazon.com/ lambda/latest/dg/services-xray.html. Last accessed: Jan 2022. 

- [9] Ali Anwar, Mohamed Mohamed, Vasily Tarasov, Michael Littley, Lukas Rupprecht, Yue Cheng, Nannan Zhao, Dimitris Skourtis, Amit Warke, Heiko Ludwig, 

14 

Dean Hildebrand, and Ali Raza Butt. Improving docker registry design based on production workload analysis. In Nitin Agrawal and Raju Rangaswami, editors, _16th USENIX Conference on File and Storage Technologies, FAST 2018, Oakland, CA, USA, February 12-15, 2018_ , pages 265–278. USENIX Association, 2018. 

- [10] Daniel Barcelona-Pons and Pedro García-López. Benchmarking parallelism in faas platforms. _Future Generation Computer Systems_ , 124:268–284, 2021. 

- [11] Marc Brooker, Adrian Costin Catangiu, Mike Danilov, Alexander Graf, Colm MacCarthaigh, and Andrei Sandu. Restoring uniqueness in microvm snapshots. _arXiv preprint arXiv:2102.12892_ , 2021. 

- [12] Alex Casalboni. AWS Lambda Power Tuning. Github docs, https://github.com/alexcasalboni/ aws-lambda-power-tuning. Last accessed: Jan 2022. 

- [13] Paul Castro, Vatche Ishakian, Vinod Muthusamy, and Aleksander Slominski. The rise of serverless computing. _Communications of the ACM_ , 62(12):44–54, 2019. 

- [14] Marcin Copik, Grzegorz Kwasniewski, Maciej Besta, Michal Podstawski, and Torsten Hoefler. Sebs: a serverless benchmark suite for function-as-a-service computing. In Kaiwen Zhang, Abdelouahed Gherbi, Nalini Venkatasubramanian, and Luís Veiga, editors, _Middleware ’21: 22nd International Middleware Conference, Québec City, Canada, December 6 - 10, 2021_ , pages 64–78. ACM, 2021. 

- [15] Robert Cordingly, Wen Shu, and Wes J. Lloyd. Predicting performance and cost of serverless computing functions with SAAF. In _IEEE International Conference on Cloud and Big Data Computing_ , pages 640–649, 2020. 

- [16] Robert Cordingly, Hanfei Yu, Varik Hoang, David Perez, David Foster, Zohreh Sadeghi, Rashad Hatchett, and Wes J. Lloyd. Implications of programming language selection for serverless data processing pipelines. In _IEEE DASC/PiCom/CBDCom/CyberSciTech_ , pages 704–711, 2020. 

- [17] Mark Crovella and Azer Bestavros. Self-similarity in world wide web traffic: evidence and possible causes. _IEEE/ACM Trans. Netw._ , 5(6):835–846, 1997. 

- [18] János Czentye, István Pelle, András Kern, Balázs Péter Gero, László Toka, and Balázs Sonkoly. Optimizing latency sensitive applications for amazon’s public cloud platform. In _2019 IEEE Global Communications Conference GLOBECOM_ , pages 1–7, 2019. 

- [19] Jeffrey Dean and Luiz André Barroso. The tail at scale. _Communications of the ACM_ , 56(2):74–80, 2013. 

- [20] Karim Djemame, Matthew Parker, and Daniel Datsev. Open-source serverless architectures: an evaluation of apache openwhisk. In _2020 IEEE/ACM 13th International Conference on Utility and Cloud Computing (UCC)_ , pages 329–335, 2020. 

- [21] Simon Eismann, Long Bui, Johannes Grohmann, Cristina L. Abad, Nikolas Herbst, and Samuel Kounev. Sizeless: predicting the optimal size of serverless functions. In Kaiwen Zhang, Abdelouahed Gherbi, Nalini Venkatasubramanian, and Luís Veiga, editors, _Middleware ’21: 22nd International Middleware Conference, Québec City, Canada, December 6 - 10, 2021_ , pages 248–259. ACM, 2021. 

- [22] Simon Eismann, Joel Scheuner, Erwin Van Eyk, Maximilian Schwinger, Johannes Grohmann, Nikolas Herbst, Cristina Abad, and Alexandru Iosup. The state of serverless applications: Collection, characterization, and community consensus. _IEEE Transactions on Software Engineering_ , 2021. 

- [23] Michael Ferdman, Almutaz Adileh, Onur Kocberber, Stavros Volos, Mohammad Alisafaee, Djordje Jevdjic, Cansu Kaynak, Adrian Daniel Popescu, Anastasia Ailamaki, and Babak Falsafi. Clearing the clouds: A study of emerging scale-out workloads on modern hardware. _Proceedings of the 17th International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS)_ , pages 37–48, 2012. 

- [24] Kamil Figiela, Adam Gajek, Adam Zima, Beata Obrok, and Maciej Malawski. Performance evaluation of heterogeneous cloud functions. _Concurrency and Computation: Practice and Experience_ , 30(23), 2018. 

- [25] Aleksandr Filichkin. GraalVM + AWS Lambda or solving Java cold start problem. https://filia-aleks.medium.com/graalvmaws-lambda-or-solving-java-cold-startproblem-2655eeee98c6, 2021. Last accessed: Jan 2022. 

- [26] Yu Gan, Yanqi Zhang, Dailun Cheng, Ankitha Shetty, Priyal Rathi, Nayan Katarki, Ariana Bruno, Justin Hu, Brian Ritchken, Brendon Jackson, Kelvin Hu, Meghna Pancholi, Yuan He, Brett Clancy, Chris Colen, Fukang Wen, Catherine Leung, Siyuan Wang, Leon Zaruvinsky, Mateo Espinosa, Rick Lin, Zhongling Liu, Jake Padilla, and Christina Delimitrou. An open-source benchmark suite for microservices and their hardware-software implications for cloud & edge systems. In _Proceedings of the 24th International Conference on Architectural_ 

15 

_Support for Programming Languages and Operating Systems (ASPLOS)_ , pages 3–18, 2019. 

- [27] Martin Grambow, Tobias Pfandzelter, Luk Burchard, Max Schubert, Carsten Zhao, and David Bermbach. BeFaaS: An application-centric benchmarking framework for faas platforms. In _Proceedings of the 9th IEEE International Conference on Cloud Engineering (IC2E)_ , 2021. 

- [28] Hassan B. Hassan, Saman A. Barakat, and Qusay I. Sarhan. Survey on serverless computing. _Journal of Cloud Computing_ , 10(1):39, 2021. 

- [29] Wilhelm Hasselbring. Benchmarking as empirical standard in software engineering research. In Ruzanna Chitchyan, Jingyue Li, Barbara Weber, and Tao Yue, editors, _EASE 2021: Evaluation and Assessment in Software Engineering, Trondheim, Norway, June 21-24, 2021_ , pages 365–372. ACM, 2021. 

- [30] Michael Hüttermann. _Infrastructure as Code_ . Apress, 2012. 

- [31] David Jackson and Gary Clynch. An investigation of the impact of language runtime on the performance and cost of serverless functions. In _2018 IEEE/ACM International Conference on Utility and Cloud Computing Companion (UCC Companion)_ , pages 154–160. IEEE, 2018. 

- [32] k6.io. https://k6.io/. Last accessed: Jan 2022. 

- [33] Anish Karandikar. Real-world Backend. https://github.com/anishkny/realworlddynamodb-lambda. Last accessed: Jan 2022. 

- [34] Jeongchul Kim and Kyungyong Lee. FunctionBench: A suite of workloads for serverless cloud function service. In _Proceedings of the 12th IEEE International Conference on Cloud Computing (CLOUD WIP)_ , pages 502–504, 2019. 

- [35] Ana Klimovic, Yawen Wang, Patrick Stuedi, Animesh Trivedi, Jonas Pfefferle, and Christos Kozyrakis. Pocket: Elastic ephemeral storage for serverless analytics. In _13th USENIX Symposium on Operating Systems Design and Implementation (OSDI 18)_ , pages 427–444, 2018. 

- [36] Simon Kuenzer, Vlad-Andrei Badoiu, Hugo Lefeuvre, Sharan Santhanam, Alexander Jung, Gaulthier Gain, Cyril Soldani, Costin Lupu, Stefan Teodorescu, Costi Raducanu, Cristian Banu, Laurent Mathy, Razvan Deaconescu, Costin Raiciu, and Felipe Huici. Unikraft: fast, specialized unikernels the easy way. In _EuroSys ’21: Sixteenth European Conference on Computer Systems_ , pages 376–394, 2021. 

- [37] Jörn Kuhlenkamp, Sebastian Werner, Maria C. Borges, Dominik Ernst, and Daniel Wenzel. Benchmarking elasticity of FaaS platforms as a foundation for objectivedriven design of serverless applications. In _Proceedings of the 35th ACM/SIGAPP Symposium on Applied Computing (SAC)_ , pages 1576–1585, 2020. 

- [38] Hyungro Lee, Kumar Satyam, and Geoffrey C Fox. Evaluation of production serverless computing environments. In _Proceedings of the 11th IEEE CLOUD: 3rd International Workshop on Serverless Computing (WoSC)_ , pages 442–50, 2018. 

- [39] Philipp Leitner, Erik Wittern, Josef Spillner, and Waldemar Hummer. A mixed-method empirical study of function-as-a-service software development in industrial practice. _Journal of Systems and Software_ , 149:340– 359, 2019. 

- [40] Valentina Lenarduzzi and Annibale Panichella. Serverless testing: Tool vendors’ and experts’ point of view. _IEEE Software_ , 38(1):54–60, 2020. 

- [41] Changyuan Lin and Hamzeh Khazaei. Modeling and optimization of performance and cost of serverless applications. _IEEE Transactions on Parallel and Distributed Systems_ , 32(3):615–632, 2020. 

- [42] W. Lloyd, M. Vu, B. Zhang, O. David, and G. Leavesley. Improving application migration to serverless computing platforms: Latency mitigation with keep-alive workloads. In _Companion of the 11th IEEE/ACM UCC: 4th International Workshop on Serverless Computing (WoSC)_ , pages 195–00, 2018. 

- [43] Wes Lloyd, Shruti Ramesh, Swetha Chinthalapati, Lan Ly, and Shrideep Pallickara. Serverless computing: An investigation of factors influencing microservice performance. In _2018 IEEE International Conference on Cloud Engineering (IC2E)_ , pages 159–169, 2018. 

- [44] Pedro García López, Aitor Arjona, Josep Sampé, Aleksander Slominski, and Lionel Villard. Triggerflow: trigger-based orchestration of serverless workflows. In _Proceedings of the 14th ACM International Conference on Distributed and Event-based Systems_ , pages 3–14, 2020. 

- [45] Jonathan Mace. End-to-End Tracing: Adoption and Use Cases. Survey, Brown University, 2017. 

- [46] Pascal Maissen, Pascal Felber, Peter Kropf, and Valerio Schiavoni. Faasdom: A benchmark suite for serverless computing. In _Proceedings of the 14th ACM International Conference on Distributed and Event-based Systems_ , 2020. 

16 

- [47] Johannes Manner, Martin Endreß, Tobias Heckel, and Guido Wirtz. Cold start influencing factors in function as a service. In _Companion of the 11th IEEE/ACM UCC: 4th International Workshop on Serverless Computing (WoSC)_ , pages 181–88, 2018. 

- [48] Johannes Manner, Martin Endreß, Tobias Heckel, and Guido Wirtz. Cold start influencing factors in function as a service. In _2018 IEEE/ACM International Conference on Utility and Cloud Computing Companion (UCC Companion)_ , pages 181–188. IEEE, 2018. 

- [49] Garrett McGrath and Paul R. Brenner. Serverless computing: Design, implementation, and performance. In _2017 IEEE 37th International Conference on Distributed Computing Systems Workshops (ICDCSW)_ , pages 405–410, 2017. 

- [50] Microsoft, Inc. Azure Public Dataset. https: //github.com/Azure/AzurePublicDataset/blob/ master/AzureFunctionsDataset2019.md. Last accessed: Jan 2022. 

- [51] Branko Minic. Improving cold start times of Java AWS Lambda functions using GraalVM and native images. https://shinesolutions.com/2021/08/ 30/improving-cold-start-times-of-java-awslambda-functions-using-graalvm-and-nativeimages/, 2021. Last accessed: Jan 2022. 

- [52] Ali Najafi, Amy Tai, and Michael Wei. Systems research is running out of time. In _Workshop on Hot Topics in Operating Systems (HotOS ’21)_ , 2021. 

- [53] Nordstrom. Hello Retail! https://web.archive. org/web/20210119044741/https://acloudguru. com/blog/engineering/serverless-eventsourcing-at-nordstrom-ea69bd8fb7cc. Last accessed: Jan 2022. 

- [54] Open Telemetry. https://github.com/opentelemetry/opentelemetry-specification/ issues/65. Last accessed: Jan 2022. 

- [55] István Pelle, János Czentye, János Dóka, and Balázs Sonkoly. Towards latency sensitive cloud native applications: A performance study on AWS. In _Proceedings of the 12th IEEE International Conference on Cloud Computing (CLOUD)_ , pages 272–280, 2019. 

- [56] Qifan Pu, Shivaram Venkataraman, and Ion Stoica. Shuffling, fast and slow: Scalable analytics on serverless infrastructure. In _Proceedings of the 16th USENIX Symposium on Networked Systems Design and Implementation (NSDI)_ , pages 193–206, 2019. 

- [57] Haoran Qiu, Subho S. Banerjee, Saurabh Jha, Zbigniew T. Kalbarczyk, and Ravishankar K. Iyer. FIRM: An intelligent fine-grained resource management framework for slo-oriented microservices. In _14th USENIX Symposium on Operating Systems Design and Implementation (OSDI 20)_ , pages 805–825, 2020. 

- [58] Sterling Quinn, Robert Cordingly, and Wes Lloyd. Implications of alternative serverless application control flow methods. In _Proceedings of the Seventh International Workshop on Serverless Computing (WoSC7) 2021_ , WoSC ’21, pages 17–22. Association for Computing Machinery, 2021. 

- [59] Ali Raza, Ibrahim Matta, Nabeel Akhtar, Vasiliki Kalavari, and Vatche Isahagian. Function-as-a-service: From an application developer’s perspective. _JSys_ , 1(1):1–20, 2021. 

- [60] Stan Salvador and Philip Chan. Toward accurate dynamic time warping in linear time and space. _Intell. Data Anal._ , 11(5):561–580, 2007. 

- [61] Raja R Sambasivan, Rodrigo Fonseca, Ilari Shafer, and Gregory R Ganger. So, you want to trace your distributed system? key design insights from years of practical experience. _Technical Report_ , 2014. 

- [62] Bruno Schaatsbergen. Pre-jitting in AWS Lambda functions. https://www.bschaatsbergen.com/prejitting-in-lambda, 2021. Last accessed: Jan 2022. 

- [63] Joel Scheuner and Philipp Leitner. Function-as-aservice performance evaluation: A multivocal literature review. _Journal of Systems and Software (JSS)_ , 170:110708, 2020. 

- [64] Johann Schleier-Smith, Vikram Sreekanti, Anurag Khandelwal, Joao Carreira, Neeraja Jayant Yadwadkar, Raluca Ada Popa, Joseph E. Gonzalez, Ion Stoica, and David A. Patterson. What serverless computing is and should become: the next phase of cloud computing. _Commun. ACM_ , 64(5):76–84, 2021. 

- [65] Mohammad Shahrad, Jonathan Balkind, and David Wentzlaff. Architectural implications of function-asa-service computing. In _Proceedings of the 52nd IEEE/ACM International Symposium on Microarchitecture (MICRO)_ , pages 1063–1075, 2019. 

- [66] Mohammad Shahrad, Rodrigo Fonseca, Iñigo Goiri, Gohar Chaudhry, Paul Batum, Jason Cooke, Eduardo Laureano, Colby Tresness, Mark Russinovich, and Ricardo Bianchini. Serverless in the wild: Characterizing and optimizing the serverless workload at a large cloud provider. In _2020 USENIX Annual Technical Conference (ATC)_ , pages 205–218, 2020. 

17 

- [67] Benjamin H Sigelman, Luiz Andre Barroso, Mike Burrows, Pat Stephenson, Manoj Plakal, Donald Beaver, Saul Jaspan, and Chandan Shanbhag. Dapper, a largescale distributed systems tracing infrastructure. Technical report, Google, 2010. 

- [68] César Soto-Valero, Thomas Durieux, Nicolas Harrand, and Benoit Baudry. Trace-based debloat for java bytecode. _arXiv preprint arXiv:2008.08401_ , 2020. 

- [69] Josef Spillner and Mohammed Al-Ameen. Serverless Literature Dataset. https://doi.org/10.5281/ zenodo.1175423, 2019. 

- [70] Ali Tariq, Austin Pahl, Sharat Nimmagadda, Eric Rozner, and Siddharth Lanka. Sequoia: Enabling quality-of-service in serverless computing. In _Proceedings of the ACM Symposium on Cloud Computing (SoCC)_ , 2020. 

- [71] Barry N Taylor and Chris E Kuyatt. Guidelines for evaluating and expressing the uncertainty of NIST measurement results. Technical report, National Institute of Standards and Technology, 1994. 

- [72] Dmitrii Ustiugov, Theodor Amariucai, and Boris Grot. Analyzing tail latency in serverless clouds with stellar. In _2021 IEEE International Symposium on Workload Characterization (IISWC’21)_ , 2021. 

- [73] Dmitrii Ustiugov, Plamen Petrov, Marios Kogias, Edouard Bugnion, and Boris Grot. Benchmarking, analysis, and optimization of serverless function snapshots. In _ASPLOS ’21: 26th ACM International Conference on Architectural Support for Programming Languages and Operating Systems_ , pages 559–572, 2021. 

- [74] Erwin van Eyk, Alexandru Iosup, Johannes Grohmann, Simon Eismann, André Bauer, Laurens Versluis, Lucian Toader, Norbert Schmitt, Nikolas Herbst, and Cristina L. Abad. The SPEC-RG reference architecture for faas: From microservices and containers to serverless platforms. _IEEE Internet Comput._ , 23(6):7–18, 2019. 

- [75] Erwin van Eyk, Alexandru Iosup, Simon Seif, and Markus Thömmes. The SPEC Cloud group’s research vision on FaaS and serverless architectures. In _Proceedings of the 2nd International Workshop on Serverless Computing (WOSC)_ , pages 1–4, 2017. 

- [76] Erwin van Eyk, Lucian Toader, Sacheendra Talluri, Laurens Versluis, Alexandru Uta, and Alexandru Iosup. Serverless is more: From paas to present cloud computing. _IEEE Internet Comput._ , 22(5):8–17, 2018. 

- [77] Kaushik Veeraraghavan, Justin Meza, Scott Michelson, Sankaralingam Panneerselvam, Alex Gyori, David 

   - Chou, Sonia Margulis, Daniel Obenshain, Shruti Padmanabha, Ashish Shah, Yee Jiun Song, and Tianyin Xu. Maelstrom: Mitigating datacenter-level disasters by draining interdependent traffic safely and efficiently. In _13th USENIX Symposium on Operating Systems Design and Implementation (OSDI)_ , pages 373–389, 2018. 

- [78] Jóakim von Kistowski, Jeremy A. Arnold, Karl Huppler, Klaus-Dieter Lange, John L. Henning, and Paul Cao. How to build a benchmark. In _Proceedings of the 6th ACM/SPEC International Conference on Performance Engineering (ICPE)_ , pages 333–336, 2015. 

- [79] Ao Wang, Shuai Chang, Huangshi Tian, Hongqi Wang, Haoran Yang, Huiba Li, Rui Du, and Yue Cheng. Faasnet: Scalable and fast provisioning of custom serverless container runtimes at alibaba cloud function compute. In Irina Calciu and Geoff Kuenning, editors, _2021 USENIX Annual Technical Conference, USENIX ATC 2021, July 14-16, 2021_ , pages 443–457. USENIX Association, 2021. 

- [80] Hao Wang, Di Niu, and Baochun Li. Distributed machine learning with a serverless architecture. In _2019 IEEE Conference on Computer Communications (INFOCOM)_ , pages 1288–1296, 2019. 

- [81] Liang Wang, Mengyuan Li, Yinqian Zhang, Thomas Ristenpart, and Michael Swift. Peeking behind the curtains of serverless platforms. In _Proceedings of the USENIX Annual Technical Conference (ATC)_ , pages 133–146, 2018. 

- [82] Jinfeng Wen, Yi Liu, Zhenpeng Chen, Junkai Chen, and Yun Ma. Characterizing commodity serverless computing platforms. _Journal of Software: Evolution and Process_ , page e2394, 2021. 

- [83] Wilkinson et al. The FAIR Guiding Principles for scientific data management and stewardship. _Nature SciData_ , 3, 2016. 

- [84] Alex Williams. Guide to serverless technologies. Technical report, The New Stack, 2018. 

- [85] Jeffrey R. Yost. _Making IT Work: A History of the Computer Services Industry_ . The MIT Press, 2017. 

- [86] Tianyi Yu, Qingyuan Liu, Dong Du, Yubin Xia, Binyu Zang, Ziqian Lu, Pingchao Yang, Chenggang Qin, and Haibo Chen. Characterizing serverless platforms with serverlessbench. In _Proceedings of the ACM Symposium on Cloud Computing_ , pages 30–44, 2020. 

- [87] Vladimir Yussupov, Uwe Breitenbücher, Frank Leymann, and Christian Müller. Facing the unplanned 

18 

migration of serverless applications: A study on portability problems, solutions, and dead ends. In _Proceedings of the 12th IEEE/ACM International Conference on Utility and Cloud Computing_ , pages 273–283, 2019. 

- [88] Vladimir Yussupov, Uwe Breitenbücher, Frank Leymann, and Michael Wurster. A systematic mapping study on engineering function-as-a-service platforms and tools. In _Proceedings of the 12th IEEE/ACM International Conference on Utility and Cloud Computing_ , pages 229–240, 2019. 

- [89] Miao Zhang, Yifei Zhu, Cong Zhang, and Jiangchuan Liu. Video processing with serverless computing: A measurement study. In _Proceedings of the 29th ACM workshop on network and operating systems support for digital audio and video_ , pages 61–66, 2019. 

- [90] Tian Zhang, Dong Xie, Feifei Li, and Ryan Stutsman. Narrowing the gap between serverless and its state with storage functions. In _Proceedings of the ACM Symposium on Cloud Computing_ , pages 1–12, 2019. 

19 

