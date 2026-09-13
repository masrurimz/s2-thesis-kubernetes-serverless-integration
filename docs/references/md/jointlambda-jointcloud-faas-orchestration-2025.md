---
# --- bibliographic record ---
entry_type: misc
title: "Joint$\\lambda$: Orchestrating Serverless Workflows on Jointcloud FaaS Systems"
authors:
  - "Rui Li"
  - "Jianfei Liu"
  - "Zhilin Yang"
  - "Peichang Shi"
  - "Guodong Yi"
  - "Huaimin Wang"
year: 2025
venue: "arXiv preprint"
volume: ""
issue: ""
pages: ""
publisher: ""
doi: ""
arxiv: "2505.21899"
url: "https://arxiv.org/abs/2505.21899"

# --- archive record ---
source_pdf: jointlambda-jointcloud-faas-orchestration-2025.pdf
source_sha256: 89e6b2e40b6be6328cdbf143aa44b094e4e55725d2cce2f7e4143d36b36f4322
pdf_pages: 21
converted: 2026-09-13
record_source: arxiv
key_insight: "Multi-provider FaaS workflow orchestration; no prediction, no confidence gating"
first_page: "Received: Added at production Revised: Added at production Accepted: Added at production DOI: xxx/xxxx A R T I C L E T Y P E Jointλ: Orchestrating Serverless Workflows on Jointcloud FaaS Systems Rui L"
---
Received: Added at production 

Revised: Added at production 

Accepted: Added at production 

DOI: xxx/xxxx 

#### **A R T I C L E T Y P E** 

# **Joint** _λ_ **: Orchestrating Serverless Workflows on Jointcloud FaaS Systems** 

**Rui Li**<sup>_∗_</sup><sup>**1**</sup> **Jianfei Liu**<sup>_∗_</sup><sup>**1**</sup> **Wang**<sup>**1**</sup> 

**Zhilin Yang**<sup>**1**</sup> 

**Peichang Shi**<sup>**1**</sup> 

**Guodong Yi**<sup>**2**</sup> **Huaimin** 

- 1State Key Laboratory of Complex & Critical Software Environment, College of Computer Science and Technology, National University of Defense Technology, Changsha, Hunan, China 

- 2Xiangjiang Lab, Hunan University Of Technology and Business, Changsha, Hunan, China 

##### **Correspondence** 

Huaimin Wang, National Key Laboratory of Parallel and Distributed Computing, National University of Defense Technology, Changsha, Hunan, China. Email: whm_w@163.com 

### **Abstract** 

Existing serverless workflow orchestration systems are predominantly designed for a single-cloud FaaS system, leading to vendor lock-in. This restricts performance optimization, cost reduction, and availability of applications. However, orchestrating serverless workflows on Jointcloud FaaS systems faces two main challenges: (1) additional overhead caused by centralized cross-cloud orchestration; and (2) a lack of reliable failover and fault-tolerant mechanisms for cross-cloud serverless workflows. 

To address these challenges, we propose Joint _λ_ , a distributed runtime system designed to orchestrate serverless workflows on multiple FaaS systems without relying on a centralized orchestrator. Joint _λ_ introduces a compatibility layer, Backend-Shim, leveraging inter-cloud heterogeneity to optimize makespan and reduce costs with on-demand billing. By using function-side orchestration instead of centralized nodes, it enables independent function invocations and data transfers, reducing cross-cloud communication overhead. For high availability, it ensures exactly-once execution via datastores and failover mechanisms for serverless workflows on Jointcloud FaaS systems. We validate Joint _λ_ on two heterogeneous FaaS systems, AWS and Aliyun, with four workflows. Compared to the most advanced commercial orchestration services for single-cloud serverless workflows, Joint _λ_ reduces makespan by up to 3.3 _×_ while saving up to 65% in cost. Joint _λ_ is also up to 4.0 _×_ faster than state-of-the-art orchestrators for cross-cloud serverless workflows, while achieving competitive cost in representative scenarios and providing strong execution guarantees. 

##### **K E Y W O R D S** 

Cloud computing, Serverless Computing, Jointcloud Computing, Function-as-a-service, Workflows 

## **1 INTRODUCTION** 

Serverless computing simplifies cloud programming<sup>1</sup> , separates application development and infrastructure management (e.g., auto-scaling), enables fine-grained on-demand billing, and charges users only for the resources they actually use. Serverless computing provides two simple but efficient high-level abstractions: stateless basic computing units (Function as a Service, FaaS) and scalable backend services (Backend as a Service, BaaS) such as data storage. Developers decompose applications into a series of logically independent functions, using external storage to transfer intermediate data. However, the fine-grained division also creates complex workflows for FaaS applications. Users typically need to logically define workflows (e.g., Directed Acyclic Graphs, DAGs), and then use an orchestrator to organize and coordinate the dispersed functions to complete the defined workflow. 

There are many implementations of serverless workflow orchestration systems<sup>2,3,4,5,6,7,8,9,10</sup> nowadays. However, almost all serverless workflow orchestration systems are designed to work on a single FaaS system, leading to vendor lock-in, potentially compromising the performance, cost, and availability of applications. The serverless workflows on a single FaaS platform face several limitations: 1) **The lack of support for heterogeneous accelerators.** There have been many works<sup>11,12,13,14,15</sup> exposing the performance differences among multiple homogeneous FaaS systems (e.g., CPU-only support). However, few FaaS systems<sup>16,17,18</sup> currently support heterogeneous accelerators, which are crucial for accelerating computation. 2) **Different FaaS** 

> _†_ Rui Li and Jianfei Liu contributed equally to this work and share first authorship. 

© 2023 Copyright Holder Name **1** 

_Journal_ 2023;00:1–21 

wileyonlinelibrary.com/journal/ 

**2** 

Li ET AL. 

**systems incur varying costs.** The FaaS system uses a pay-as-you-go billing model. Functions running on different FaaS systems generate significantly different charges. External serverless workflow orchestrators often charge based on state transitions rather than actual resource consumption, leading to unfair billing. 3) **Availability of cloud services.** Strict regulations on data and operational sovereignty (e.g., the General Data Protection Regulation, GDPR) dictate where data can be stored and where jobs can be executed. Not all cloud providers have data centers in every country, making it challenging to comply with these regulations<sup>19</sup> . Additionally, cloud customers suffer significant losses from reduced availability during regional or cloud-wide failures<sup>20</sup> . 

We believe that future FaaS applications will be built on multiple clouds, such as Jointcloud computing<sup>21</sup> and Sky computing<sup>22</sup> , which facilitate workload deployment and migration across clouds as well as peer-to-peer collaboration between multiple cloud service providers (CSPs). However, orchestrating serverless workflows on Jointcloud FaaS systems faces two main challenges: 1) **Additional overhead caused by centralized cross-cloud orchestration.** Functions are short-lived, so state transitions at the orchestrator occur frequently<sup>6</sup> . Each centralized state transition adds at least one additional communication hop, leading to non-negligible latency overhead. Moreover, a centralized cross-cloud orchestrator incurs additional cost due to long-running orchestration nodes (e.g., virtual machines, VMs) and frequent cross-cloud data transfers. 2) **A lack of reliable failover and fault-tolerant mechanisms.** Function execution and invocation may fail for many reasons in multi-cloud environments, e.g., cloud failures. FaaS systems typically provide only weak at-least-once execution guarantees (e.g., retries), which may cause repeated executions and inconsistent workflow outputs. Without reliable failover and exactly-once execution semantics for cross-FaaS workflows, it is difficult to ensure workflow reliability. 

To overcome single-cloud limitations and address these challenges, we present Joint _λ_ , a distributed runtime system for orchestrating serverless workflows on multiple FaaS systems. Without a centralized orchestrator, Joint _λ_ located with each user function as an additional runtime library (function-side workflow orchestrator), enables the control flow from function to function. This can accelerate makespan and reduce costs via inter-cloud heterogeneity, ensure high availability with fault tolerance and failover, and avoid extra communication during state transitions. To achieve this, we prototyped the Joint _λ_ upon Unum<sup>5</sup> which is an application-level distributed FaaS workflow orchestrator based on a single cloud. 

In Joint _λ_ , we introduce a distributed compatibility layer, Backend-Shim, implemented based on the APIs of different FaaS systems and data storages, providing a standard interface for the function-side workflow orchestrator. Joint _λ_ manages data reads/writes and function invocations across various backend systems via the Backend-Shim. We also extend the intermediate representation of workflows to express complex invocation primitives and transfer primitives using function meta-information (sub-graph). We introduce a wrapper to manage function node entry/export, parsing cloud event objects (Joint _λ_ Object) and transferring data efficiently. The function-side workflow orchestrator inside the wrapper implements current function orchestration using function invocation and data transfer primitives provided by the sub-graph. For high availability in unstable environments, we implement fault-tolerant and failover mechanisms. We also employ the majority rule principle for data storage location and a bitmap for cross-platform function collaboration, defining unique key naming for function reusability. 

The main contributions of this paper are as follows. 

1) We present Joint _λ_ , a distributed runtime system for orchestrating serverless workflows on multiple FaaS systems, leveraging inter-cloud heterogeneity. It uses function-side distributed orchestration instead of centralized nodes to reduce cross-cloud communication overhead. 

2) We achieve exactly-once execution guarantees and failover mechanisms to ensure high availability for serverless workflows on Jointcloud FaaS. 

3) We validate Joint _λ_ on two heterogeneous FaaS systems, Amazon Web Services (AWS) Lambda<sup>23</sup> and Alibaba Cloud (Aliyun) Function Compute (FC)<sup>24</sup> , with four workflows. Compared with AWS Step Functions and Aliyun CloudFlow, our evaluation shows that Joint _λ_ reduces makespan by up to 3.3 _×_ and saves up to 65% in cost. Joint _λ_ is also up to 4.0 _×_ faster than state-of-the-art orchestrators for cross-cloud serverless workflows with competitive cost in representative scenarios. Joint _λ_ further supports reliable failover for serverless workflows, incurring negligible additional overhead relative to the overall runtime and cost. 

## **2 BACKGROUND AND MOTIVATION** 

In serverless computing, developers write and upload functions to a FaaS platform, and these functions can be implemented in multiple high-level languages. A function responds to request events, including HTTP requests and BaaS events. When the function is invoked, the CSP configures a sandbox (e.g., a container<sup>25</sup> or a virtual machine<sup>26,27</sup> ), deploys the user code, and 

Joint _λ_ 

**3** 

routes the request. FaaS platforms can quickly absorb bursty workloads, relieving developers from low-level operations and infrastructure management. In this section, we introduce the advantages of serverless workflows on Jointcloud FaaS systems and the limitations of existing cross-cloud FaaS workflow orchestrators. 

## **2.1 Why Serverless Workflows Can Benefit From Jointcloud FaaS Systems?** 

**_Observation 1:_** _Existing FaaS systems vary in performance, with most lacking support for heterogeneous accelerators. Utilizing inter-cloud heterogeneity in workflows can significantly reduce the makespan._ 

First, there have been many works<sup>11,12,13,14,15</sup> exposing the performance differences among multiple homogeneous FaaS systems (e.g., CPU-only support). Moreover, many important applications rely on heterogeneous accelerators (e.g., GPUs) to accelerate computation. However, very few FaaS systems<sup>16,17,18</sup> currently support heterogeneous accelerators. This limitation will be a serious obstacle for FaaS applications seeking to optimize makespan. In addition, workflow orchestrators supported by FaaS systems (e.g., orchestration services provided by major cloud service providers, CSPs) exhibit large performance differences when orchestrating multiple patterns<sup>28</sup> . These limitations collectively constrain the overall performance of single-cloud FaaS workflows. 



<!-- Start of picture text -->
1000 1000<br>8192 329 585 X 113 215 220 X 211 8192 755 1035 X 99 374 473 X 274<br>6144 458 544 X 98 254 370 X 188 6144 835 1025 X 109 424 368 X 259<br>5120 455 659 190 98 261 253 325 212 800 5120 1093 1064 213 103 461 480 340 261 800<br>4096 541 615 168 79 302 304 271 199 4096 1023 1014 176 91 520 460 356 264<br>3584 659 470 171 83 355 286 272 201 3584 1250 939 190 100 589 493 349 269<br>3072 737 513 179 92 358 314 261 216 600 3072 1451 913 187 90 643 532 350 269 600<br>2560 807 568 X X 398 337 X X 2560 1668 1100 X X 661 584 X X<br>2048 1053 748 X X 477 372 X X 2048 2006 1404 X X 811 690 X X<br>1792 1161 818 X X 562 427 X X 400 1792 2279 1520 X X 934 798 X X 400<br>1536 1418 922 X X 615 511 X X 1536 2830 2050 X X 1051 1008 X X<br>12801024 1755 11412448 1519 XX XX 1051789 603907 XX XX 200 12801024 3585 29344660 3695 XX XX 1312 11411746 X XX XX 200<br>512 5230 X X X 2217 X X X 512 9148 X X X X X X X<br>(a) P95 latency under batching of 2 (b) P95 latency under batching of 4<br>Bert-aws-cpuBert-ali-cpuBert-ali-gpu4Bert-ali-gpu8ResNet50-aws-cpuResNet50-ali-cpuResNet50-ali-gpu4ResNet50-ali-gpu8<br>Bert-aws-cpuBert-ali-cpuBert-ali-gpu4Bert-ali-gpu8ResNet50-aws-cpuResNet50-ali-cpuResNet50-ali-gpu4ResNet50-ali-gpu8<br>Function Memory(MB) Function Memory(MB)<br><!-- End of picture text -->

**FIGURE 1** P95 Inference Latency across Heterogeneous FaaS Configurations with Varying Memory Allocations. Note: The suffixes -aws-cpu, -ali-cpu, -ali-gpu4, and -ali-gpu8 denote AWS Lambda (CPU) and Aliyun Function Compute (CPU, 4GB A10 GPU, and 8GB A10 GPU) runtimes, respectively. ’X’ indicates execution failure (e.g., OOM). 

The serverless architecture provides function abstraction to the user while hiding the specific details of resource management, e.g., the developer only knows the configured memory size but not the vCPU, network, and other relevant runtime data. This "function black box" results in underlying performance differences at runtime. Applications such as deep learning rely on hardware accelerators to accelerate computation. Figure 1 presents the P95 latency distribution for BERT<sup>29</sup> and ResNet50<sup>30</sup> . We evaluate these models across diverse FaaS runtimes, including mainstream CPU instances (Bert-aws-cpu, Bert-ali-cpu) and GPU-accelerated instances (Bert-ali-gpu4/8). The inference of BERT achieved up to a 7 _×_ and 15 _×_ acceleration on GPU-enabled FaaS systems compared to CPU-only FaaS systems for batch sizes of 2 and 4, respectively. The performance gap will be more pronounced with increasing model size or batch size. 

**_Observation 2:_** _The FaaS model charges on demand based on GB*s, with total workflow cost positively correlated with total runtime. Leveraging inter-cloud heterogeneity, workflows can reduce execution costs._ 

**4** 

Li ET AL. 

The FaaS system employs a pay-as-you-go billing model, where the total cost comprises the execution cost and the invocation cost. Execution cost is determined by the GB*s model (allocated resources multiplied by runtime) and depends on the resource unit price, allocated resources, and runtime. As a result, functions running on different FaaS systems generate significantly different charges. 

Figures 2 show the total cost of running the inference function of BERT on different clouds. Deploying the workflow on _ali_  gpu_ results in maximum savings of 61.9% and 82.2% compared to _aws_  cpu_ , depending on the batch size. Functions running on CPUs have longer execution times than those on GPUs; although CPUs may be cheaper, they ultimately cost more due to the increased runtime. Additionally, some serverless cloud providers do not offer GPU resources, and even when they do, the prices vary between clouds. This variability presents opportunities for optimization. 



<!-- Start of picture text -->
ali_cpu aws_cpu ali_gpu4 ali_gpu8<br>Total cost with batch=2 Total cost with batch=4<br>45<br>90<br>40 80<br>35 70<br>60<br>30<br>50<br>25<br>40<br>20 30<br>15 20<br>Allocated Memory Size in MB Allocated Memory Size in MB<br>51276810241280153617922048 2560 3072 3584 4096 4608 5120 6144 8192 51276810241280153617922048 2560 3072 3584 4096 4608 5120 6144 8192<br>Cost per 1M Invocations in USD<br><!-- End of picture text -->

**F I G U R E 2** Average total cost per 1M invocations for BERT inference across heterogeneous FaaS configurations with Batch Size 2 and 4. Note: aws_cpu, ali_cpu, ali_gpu4, and ali_gpu8 denote AWS Lambda (CPU) and Aliyun Function Compute (CPU, 4GB A10 GPU, and 8GB A10 GPU) runtimes, respectively. The cost is measured in USD based on the memory-time resource pricing model of each provider. 

## **2.2 Limitations of Existing Cross-cloud FaaS Workflows Orchestrators** 

While FaaS model was initially used for simple applications with a single function, this paradigm has recently increasingly proved to be useful for complex applications consisting of many functions<sup>31,32,33</sup> , i.e., combining them into function workflows. To organize complex function workflows in the expected order and ensure exactly-once semantics<sup>7,34,4</sup> , a common solution is to introduce a central orchestrator. Users need to logically define workflows and submit them to the orchestrator, e.g., by describing the interaction of each function. The orchestrator then realizes the defined workflow logic by invoking functions and managing runtime state (e.g., intermediate data and execution progress). 

Recently, several studies<sup>35,36,37</sup> have noted the performance limitations of single-cloud FaaS workflows and have explored using multiple CPU-based FaaS systems to optimize makespan. These cross-cloud orchestration solutions are almost all based on centralized designs (Master-Worker mode). The orchestrator acts as a coordination point for functions distributed across multiple FaaS systems. A centralized orchestrator can record the execution result of each function, decide which function to invoke next based on workflow progress, and avoid duplicate executions. 

However, centralized orchestrators have significant drawbacks when orchestrating serverless workflows on Jointcloud FaaS systems. Functions in a workflow can be distributed across multiple clouds or regions, and the orchestrator is likely far away from most functions. Frequent cross-cloud state transitions therefore impose additional overhead on a centralized orchestrator. Figure 3 shows the extra overhead incurred when orchestrating cross-cloud workflows. Centralized state transitions add at least one additional communication link (red arrows in Figure 3), resulting in non-negligible latency overhead and high data-egress charges. In addition, the logically centralized architecture limits the performance of highly concurrent tasks<sup>36</sup> and incurs extra cost due to long-running orchestration services on nodes (e.g., virtual machines, VMs). External serverless workflow orchestrators<sup>38,39,40,41</sup> offered by CSPs also view workflows as state machines and charge separately (25$ per 1M state transitions) for each state transition in a workflow, rather than for the actual resources consumed, which leads to unfair billing. 

Joint _λ_ 

**5** 



<!-- Start of picture text -->
Function invocation flow Data Storage<br>Data transfer flow<br>FaaS System  FaaS System<br>on AWS on Aliyun<br>F4<br>F2<br>F1 3 F3<br>Workflow Definition 1 1 3 2-1 2-1 2-2<br>2-2<br>F2<br>Centralized Orchestrator<br>F1 F4<br>F3 Long-running orchestration services in nodes (VMs)<br><!-- End of picture text -->

**F I G U R E 3** Logically centralized orchestrator organizing serverless workflows on Jointcloud FaaS systems. 

To address these limitations, we propose Joint _λ_ , a distributed runtime system for cross-cloud heterogeneous serverless computing, accelerating makespan by leveraging inter-cloud heterogeneity, and function-side orchestration instead of centralized nodes. 

## **3 RELATED WORK** 

**Orchestrating serverless workflows on single-FaaS.** There is a long line of research<sup>2,8,3,42,6,43,5,44</sup> on serverless workflow orchestration for a single FaaS system. Some orchestrators<sup>2,8,3,45,46</sup> outsource work threads to cloud FaaS systems to accelerate tasks. The cloud function is designed as a generic worker. However, workers often suffer from large runtime initialization overhead. Some orchestrators<sup>42,40,47,48,16</sup> are integrated with FaaS systems and enhance fault tolerance and scalability with message queues and databases. To guarantee the correct execution of the workflow, AFT<sup>4</sup> proposes a fault-tolerant shim between the FaaS system and the datastore, while Olive<sup>49</sup> and Boki<sup>34</sup> design fault-tolerant mechanisms based on function logs stored in the datastore. However, logically centralized controllers hinder orchestration performance. FaaSFlow<sup>6</sup> presents a worker-side workflow scheduling pattern for serverless workflow execution, namely a distributed orchestrator at the VM level. Wukong<sup>43</sup> , Pheromone<sup>10</sup> , and Netherite<sup>44</sup> also optimize performance with decentralized orchestration. Unum<sup>5</sup> is an application-level, decentralized orchestration system. Compared to master-worker orchestrators, it performs well, offers greater flexibility, and lowers expenses. Joint _λ_ integrates the above insights and introduces distributed orchestration and datastore-based execution guarantees for serverless workflows on Jointcloud FaaS systems. **Orchestrator support for workflows on multiple FaaS.**<sup>9</sup> extends Hyperflow<sup>50</sup> to run scientific computing serverless workflows on multiple clouds. Lithops<sup>51</sup> views functions as homogeneous workers and leverages multi-cloud FaaS to optimize parallel tasks. To address the limitations of the number of concurrent functions, xAFCL<sup>36</sup> implements a middleware that can schedule and execute different functions in a workflow across multiple FaaS. FaaSt<sup>35</sup> added new features to xAFCL to enhance fault tolerance across multiple clouds. Globalflow<sup>52</sup> uses connector functions to connect workflows across multiple regions in AWS. Based on the same idea, XFaaS<sup>37</sup> presents a cross-platform orchestrator for FaaS workflows based on existing cloud orchestration services. To our knowledge, cross-cloud orchestrators for serverless workflows are logically centralized. However, Joint _λ_ is different from these systems. 

To summarize the above discussion, Table 1 compares Joint _λ_ with several representative systems along three dimensions. “Supporting Multi-FaaS?” indicates whether a system can operate across multiple FaaS platforms. “Supporting serverless workflow?” indicates whether it natively supports workflow-oriented control flow, such as sequences, DAGs, fan-out/fan-in, or other explicit dependencies among functions, rather than treating functions only as independent or embarrassingly parallel tasks. “Distributed or Centralized?” indicates whether the orchestration architecture is distributed or relies on a centralized coordinator. Beyond the specific domain of workflow orchestration, recent literature highlights the rapid evolution of the broader FaaS ecosystem. For instance, to facilitate serverless research, tools like faas-sim<sup>53</sup> have been developed for platform simulation, 

**6** 

Li ET AL. 

**T A B L E 1** The design space of Joint _λ_ against existing works of serverless workflow orchestrator. 

||Joint_λ_|xAFCL <sup>36</sup>|Lithops <sup>51</sup>|FaaSFlow <sup>6</sup>|XFaaS <sup>37</sup>|Unum <sup>5</sup>|
|---|---|---|---|---|---|---|
|Supporting<br>Multi-FaaS?|�|�|�|�|�|�|
|Supporting<br>serverless workflow?|�|�|�|�|�|�|
|Distributed<br>or Centralized?|Distributed|Centralized|Centralized|Distributed|Semi-<br>centralized|Distributed|



whereas Joint _λ_ focuses on building a real-world runtime system. From an architectural perspective, Zhu et al.<sup>54</sup> proposed RADF to modularize FaaS platforms for better maintainability. Furthermore, the application landscape of FaaS is expanding into complex workloads, such as distributed deep neural network inference across the cloud-to-things continuum<sup>55</sup> . These structural and applicative advancements demonstrate the growing demand for flexible, heterogeneous FaaS environments, a landscape that Joint _λ_ further enriches by providing robust, cross-cloud workflow orchestration with exactly-once execution semantics. 

## **4 RATIONALE OF JOINT** _λ_ 

This section introduces Joint _λ_ , a function-side workflow orchestration system designed for orchestrating serverless workflows on Jointcloud FaaS systems. Compared to existing systems, Joint _λ_ aims to achieve the following underexplored goals: 1) Joint _λ_ leverages inter-cloud heterogeneous FaaS systems, such as those supporting GPU accelerators, to accelerate completion time and reduce costs. 2) Instead of relying on centralized orchestration nodes to manage and execute workflows, Joint _λ_ uses function-side orchestration to enable independent function invocations and data transfers, reducing the overhead of cross-cloud communication. 3) Joint _λ_ supports exactly-once execution semantics for workflows, introducing fault tolerance and failover in unstable multi-FaaS environments. 

## **4.1 Architecture Overview** 



<!-- Start of picture text -->
NextFunctionInfo WorkflowState<br>Function or<br>runtime  library Str: PreFunctionName, FunctionName Str: FunctionName, FucntionId, FaasSystem<br>JSON file Str or Dict: InvokeMode Str: WorkflowId, Step, BranchIndex, Checkpointkeys<br>Str: Conditional, Failover, BranchIndex, BranchSize Class: DsBackend<br>Cloud<br>Class: FaasBackend, DsBackend List: [ Class: NextFunctionInfo ]<br>Jointλ<br>List: [Str: ModifyEventOperation] Bool: Start, End, IsIndirect<br>Structure<br>Event: JointλObject<br>B User Function Wrapper<br>A D<br>Sub-graph  Orchestrator<br>C<br>Workflow on Jointcloud Backend-Shim<br>FaaS Systems<br>Function<br>Compute Backend Datastore Backend<br>LambdaAWS Aliyun FunctionCompute .... S3 OSS TableStrore Dynamodb Datastores<br><!-- End of picture text -->

**FIGURE 4** Abstraction for Joint _λ_ . The data structure for the management of function invocation and data transfer in the function-side workflow orchestrator. 

Joint _λ_ 

**7** 

Figure 4 provides an architectural overview of the three main components of Joint _λ_ : the wrapper, the function-side orchestration library, and Backend-Shim. The developer writes a sub-graph for each function based on the workflow logic. The wrapper handles function entry and exit, parses the incoming _JointλObject_ , passes user data to the function, and encapsulates the output for downstream calls. The orchestration library then executes the invocation and data-transfer logic specified by the sub-graph, while Backend-Shim maps these operations to the native APIs of the target FaaS and storage backends. 

## **4.2 Backend-Shim** 

As shown in Figure 4, Backend-Shim is a compatibility layer designed as an independent library that allows each function to invoke downstream functions and access storage through a uniform interface. It currently supports functions built on the Python runtime and is composed of Compute-Backend-Shim and DataStore-Backend-Shim. First, Backend-Shim is dedicated to shielding cloud heterogeneity, providing a unified abstraction for function execution and data access. The function-side workflow orchestrator accesses various data storages and cross-cloud function invocations through Backend-Shim. Second, Backend-Shim is implemented based on the APIs of different FaaS systems and data storages, providing a standard interface for the function-side workflow orchestrator, as shown in Table 2. 

**T A B L E 2** Backend-Shim APIs. Object storage and table storage in DSBackend implement the red APIs for indirect data transfer. 

|**Class**|**API**|**Description**|
|---|---|---|
|**DSBackend**|create(ds)<br>store_output_data(key, data)<br>get_value(key)<br>create_invocation_list(key)<br>append_and_get_list(key, func_list)<br>create_bitmap(size, key)<br>update_bitmap(index, key)|Create a datastore client.<br>Conditionally create an item/object,<br>i.e. create an item if it does not exist.<br>Strong consistency read an item/object.<br>Conditionally create a list of strings,<br>i.e. create an item if it does not exist.<br>Append list items and return the latest list.<br>Conditionally create a bitmap,<br>i.e. create an item if it does not exist.<br>Update a bitmap by corresponding position.|
|**FaaSBackend**|create(faas)<br>async_invoke(function, payload)|Create a FaaS client.<br>Asynchronous http invocation.|



We abstract data operations into a set of unified APIs as shown in Table 2. These APIs are categorized into two groups based on their roles in the workflow: 1) Data Transfer: Primitives such as store_output_data and get_value are used for large payload persistence. In practice, object storage mainly carries large intermediate payloads, whereas table storage maintains checkpoint metadata and runtime coordination state. 2) Workflow Coordination: To support complex patterns like fan-in, we implement specialized primitives including atomic bitmaps and invocation lists. For instance, update_bitmap is invoked by parallel upstream functions to signal completion, enabling the shim layer to trigger downstream tasks without a centralized scheduler, whose detailed design is described in Section 5.3.2. 

Our current prototype implements Backend-Shim as a Python library embedded in the Joint _λ_ wrapper, leveraging mature Python runtimes and stable SDKs on mainstream FaaS platforms such as AWS Lambda and Aliyun FC. Porting Joint _λ_ to another language mainly requires equivalent wrapper/shim bindings while preserving the same sub-graph IR and Joint _λ_ Object schema, including (i) Joint _λ_ Object (de)serialization, (ii) the small set of DSBackend atomic primitives, and (iii) an adapter to the platform’s asynchronous invocation API; BYOR/container-image packaging (e.g., AWS Lambda container images) can bundle the runtime and dependencies, although practical portability is still constrained by provider differences in event models and SDK feature sets. 

## **4.3 Distributed Orchestration Capabilities** 

In Joint _λ_ , there is no centralized orchestration node managing the workflow state and executing workflows (data transfer, function invocation). Each function obtains a local _sub-graph_ of the workflow and the runtime state of the workflow ( _WorkflowState_ ) 

**8** 

Li ET AL. 

through a function-side workflow orchestrator to perform function invocations, data transfer, and other orchestration logic, as shown in Figure 4. Since the sub-graph may contain complex structures and functions may be distributed across multiple FaaS systems, designing and organizing data structure is crucial for orchestrating workflows. 

**Structure organization in function-side workflow orchestrator.** In the workflow, functions need to maintain their own workflow state and invoke functions across different FaaS systems while transferring data upon completion. To allow each function to independently manage orchestration logic, the _WorkflowState_ structure was introduced, as shown in Figure 4. This structure acts as the maintainer of the workflow sub-graph and runtime state. The _WorkflowState_ saves the workflow runtime state obtained from input events, including unique _WorkflowId_ , execution stage _step_ , and branch number _branchIndex_ . Additionally, the _WorkflowState_ structure records the metadata of the current and all subsequent functions within the local sub-graph, where _NextFunctionInfo_ maintains the metadata for each subsequent function. 

**Data and Control Transfer with** _JointλObject_ **.** To support the transfer of workflow runtime data and control information across multiple FaaS systems, a new cloud event object, _JointλObject_ , and a wrapper were introduced. The format of _JointλObject_ is depicted in Figure 4. Within the wrapper, the Unwrap function retrieves input data from the incoming _JointλObject_ and passes it to the user function, while generating a unique ID for the current function based on the ’Control’ field in _JointλObject_ . The input data is either transferred directly via the Direct field of _JointλObject_ or pulled indirectly by the Unwrap function from data storage, which are also output checkpoints of previous functions. The unique ID is primarily used for naming storage items as checkpoints and for cross-cloud collaboration points. The Wrap function generates a new _JointλObject_ for each subsequent function invocation based on the current workflow state. 

**The design of sub-graph, invocation primitives and transfer primitives.** FaaS workflows are commonly represented as DAGs, where functions are defined as work nodes and edges represent data flows between these functions. Widely used FaaS orchestrators, such as AWS Step Functions, often utilize high-level descriptive languages to express interactions between function nodes. This concise workflow invocation primitive is sufficient to represent basic patterns such as direct invocation (Sequence, Parallel), dynamic invocation (Map), and conditional invocation (Cycle, Fan-In, Choice). Consequently, we continue to use this form to express serverless workflows across multiple FaaS systems. 

Due to the absence of a global graph in function-side workflow orchestration, a local sub-graph containing invocation primitives and data transfer primitives is introduced to provide metadata for functions and data storage within the sub-graph. Figure 5 illustrates the sub-graph definition of basic workflow patterns. The function-side workflow orchestrator creates _NextFunctionInfo_ objects based on the subsequent function’s FaaS system and invocation primitives, and creates checkpoints for fault tolerance and data storage backends for indirect data transfer through data transfer primitives. 

Joint _λ_ implements fault tolerance via idempotent checkpoints backed by provider storage primitives: object storage (e.g., S3<sup>56</sup> /OSS<sup>57</sup> ) for large intermediate objects and table/kv storage for checkpoint metadata and coordination. For payload handling, Joint _λ_ uses direct transfer for small payloads and indirect transfer through object storage with a stable reference carried in the Joint _λ_ Object for large payloads or when request sizes exceed provider limits. 

Invocation primitives can be flexibly combined with data transfer primitives. Among these combinations, patterns that coordinate multiple inputs, such as fan-in, typically require indirect transfer. To reduce cross-cloud data egress in such cases, Joint _λ_ selects the data placement backend at runtime, typically choosing the cloud where the majority of functions in the sub-graph are located. 

Additionally, to introduce greater flexibility, we have also designed invocation primitives to enable multiple workflows in different spaces to collaborate across different temporal dimensions, as shown in Figure 6. The batch invocation primitive invokes other workflows to process after accumulating a specific amount of data across multiple workflows. The redundancy invocation primitive is utilized to manage redundant requests to mitigate the effects of stragglers. A key insight is that geographically distributed functions can achieve local collaboration through strongly consistent data storage. However, this increased flexibility requires users to meticulously design the interactions between workflows. 

## **5 DESIGN OF JOINT** _λ_ 

In this section, we introduce how Joint _λ_ achieves two important objectives in serverless workflow orchestration across multiple FaaS systems: exactly-once execution semantics and distributed collaboration. 

Joint _λ_ 

**9** 



<!-- Start of picture text -->
Chain Parallel<br>{  "Name" : "A",<br>   "Ds" : " ObjectStore ",<br>{   "Name" : "A",    "TransferByDs" :  true ,<br>    "Ds" : " NosqlKVDs ",     "Next" : [<br>    "Next" : { JointλObj B {<br>"Name" : "B", "Name" : "B",<br>A JointλObj B     "Start" : true"FaaS" : "lambda","InvokeMode" : " Sequence "}, A JointλObj { "FaaS" : "lambda","InvokeMode" : " Sequence " },<br>} C "Name" : "C",<br>"FaaS" : "alifc",<br>"InvokeMode" : " Sequence " } ] }<br>Map FanIn<br>{  "Name" : "B",<br>    "Ds" : " ObjectStore ",<br>For Each Element in List      "TransferByDs" :  true ,<br>{   "Name" : "A",     "Next" : {<br>JointλObj     "Ds" : "    "Next" : { NosqlKVDs ", B JointλObj     "Name" : "D",    "FaaS" : "lambda",<br>JointλObj "Name" : "B",     "InvokeMode" : {<br>A JointλObj B "FaaS" : "lambda","InvokeMode" : " Map " } } A D   " FanIn "Branch" : [" : {<br>C " s3-B_1-bindex-0 "," s3-C_1-bindex-1 " ] } },<br>    "ModifyEvent" : ["PopAndMerge"] } }<br>Cycle Choice<br>{  "Name" : "A",<br>   "FaaS" : "lambda",<br>{   "Name" : "B",    "Ds" : " ObjectStore ",<br>A   "Iterator" : 0 JointλObj B     "Ds" : "    "TransferByDs" :     "Next" : {"Name" : "B","FaaS" : "lambda","InvokeMode" : ""Choice" : "Iterator < 8","ModifyEvent" : ["Iterator+=1"] }} NosqlKVDstrueSequence ", , ", A JointλObjJointλObj B1B2     "Next" : [{{ "Name" : "B1","FaaS" : "lambda","InvokeMode" : ""Choice" : " FaaS=='lambda' " },"Name" : "B2","FaaS" : "alifc", Sequence ",<br>"InvokeMode" : " Sequence ",<br>"Choice" : " FaaS=='alifc' " } ] }<br><!-- End of picture text -->

**F I G U R E 5** Sub-graph definitions and major primitives for workflow basic patterns. Invocation primitives and data transfer primitives (bold text in the figure) can be combined flexibly. 



<!-- Start of picture text -->
ByBatch ByRedundant<br>Workflow1 Workflow3 {   "Name" : "B",    "Ds" : " NosqlKVDs ", Workflow1 Workflow3 {   "Name" : "B",    "Ds" : " ObjectStore ",<br>A B X Y     "TransferByDs" :     "Next" : { true , A B X Y     "TransferByDs" :     "Next" : { true ,<br>Workflow2 "Name" : "X","FaaS" : "lambda", Workflow2 "Name" : "X","FaaS" : "lambda",<br>"InvokeMode" : { "InvokeMode" : {<br>C D E " ByBatch " : { A1 B2 " ByRedundant " : {<br>"BatchSize" : 32, "Completion" : 1,<br>Invoke after accumulation of "WorkflowWait" : [ "WorkflowWait" : [<br>batchsize number of data. i.e.,workflow 1 and workflow 2 areexecuted x times total. "B_1","E_2"] } } } } Invoke after completion of anyk workflows of n workflows. "B_1","B1_1"] } } } }<br><!-- End of picture text -->

**F I G U R E 6** Sub-graph definitions and major primitives for workflow collaboration across time and space. 

## **5.1 Exactly-once Execution** 

In a distributed computing environment that combines multiple FaaS systems, serverless workflow functions run across different cloud regions and FaaS systems. Intermediate data is distributed and transferred across multiple cloud storage systems. As a result, orchestrating serverless workflows on Jointcloud FaaS systems faces increased instability, such as cross-cloud communication link failures or computing service outages. Functions can fail at any execution stage, but FaaS systems typically offer weak execution guarantees. Most FaaS systems only provide **at-least-once** execution guarantees, meaning that if a failure occurs, retries might result in the same function executing multiple times. Specifically, when a FaaS system receives an asynchronous invocation request, it doesn’t execute the function immediately but responds to the invoker and queues the request, triggering the function via a message queue. If the function crashes, the FaaS system can retry the execution using the persisted request. In Joint _λ_ , the execution semantics are ensured by a checkpointing protocol based on conditional writes and strongly consistent reads. Optional storage features such as S3 Object Lock may provide additional hardening, but they are not required by our prototype. To ensure exactly-once execution semantics in such a challenging environment, Joint _λ_ treats function execution as two stages: data production and function invocation. It saves checkpoints using APIs outlined in Table 2 to guarantee that each stage executes only once. Given the at-least-once execution guarantees of the FaaS systems, together with at-most-once data production and at-most-once function invocation, we achieve exactly-once execution semantics. Next, we explain how we achieve at-most-once data production and at-most-once function invocation. 

**10** 

Li ET AL. 

## **5.1.1 Output Data Checkpoints** 

Joint _λ_ calculates the globally unique ID ( _FunctionId_ ) of the function based on the runtime state of the _JointλObject_ and adds a suffix to derive the key for the output data checkpoint ( _outputKey_ ). It attempts to retrieve the output result checkpoint of the function. If the checkpoint exists, the checkpoint data is used as the output. Otherwise, it executes the user function and uses _store_  output_  data_ within the _Wrap_ function to save the output data checkpoint. To accommodate user code containing logic of uploading data, Joint _λ_ exposes the outputKey to the user function and uses the _isStored_ flag to indicate whether it has been stored. The checkpoint ensures that the output data from the first successful execution is transferred, and repeated executions do not alter the execution result, achieving at-most-once data production. We currently do not rely on instance-local /tmp cache as a correctness-critical optimization. Since /tmp is non-durable and local to a specific warm instance, retries, failover, or cross-cloud re-execution may observe a different instance where the cache is absent or stale. We therefore treat storage-backed checkpoints as the source of truth; /tmp can still be used as a best-effort cache if validated against checkpoint metadata such as the output key or object Entity Tag (ETag). 

## **5.1.2 Invocation Checkpoints.** 

Similarly, Joint _λ_ appends a suffix to the globally unique ID ( _FunctionId_ ) of the function to derive the key ( _ivkKey_ ) for the invocation checkpoint. The invocation checkpoint is designed as an initially empty string list stored in a table storage system on the cloud where the function resides. Joint _λ_ first queries whether the invoked function has been recorded in the checkpoint. If it doesn’t exist, it modifies the _JointλObject_ and runs the invocation logic based on the _InvokeMode_ of the invoked function. Joint _λ_ uses asynchronous invocation (FaaSBackend.async_invoke) for cross-platform downstream calls to avoid double-billing (charging the invoker while it waits and the callee while it runs). Upon successful invocation of the subsequent function, it appends the name of the successfully invoked function(s) to the invocation checkpoint. The checkpoint ensures recording the first successful invocation of the function, achieving at-most-once function invocation. 

In practical running, we encountered unacceptable delays when invoking a large number of concurrent functions. Upon investigation, we identified that the performance degradation stemmed from extensive checkpoint reads and writes, as well as asynchronous invocation delays. Therefore, Joint _λ_ optimizes the latency of reading and writing to table storage for all concurrent invocations (fan-out) exceeding 10 subsequent functions by **grouping checkpoint** . Joint _λ_ also utilizes concurrent invocations with 10 threads for fan-out. It invokes every 10 functions in the order of _nextFuncs_ , and upon successful invocation, appends them to the invocation checkpoint as a group. 

In the most extreme scenario, a function crashes and retries after executing an asynchronous invocation statement, without yet saving the invocation checkpoint for that function, which leads to duplicate invocations. However, Joint _λ_ ensures that the function uses the same data through output result checkpoints and guarantees at-most-once invocation by means of repeated function invocation checkpoints. Thus, even in extreme cases of duplicate function invocations, it does not affect the exactly-once execution of subsequent workflow steps, ensuring correct execution. 

## **5.2 Failover** 

Failover leveraging multi-cloud environments are viable solutions for enhancing availability. However, they often rely on manual backup procedures and operations personnel for recovery in traditional cloud computing paradigms, facing limitations such as low resource utilization and high costs. Fortunately, the serverless paradigm’s on-demand billing and automatic scaling eliminate these drawbacks. Backup functions in workflows consume no resources and incur no costs until they are invoked. Leveraging these insights, Joint _λ_ implements failover during the function invocation stage, efficiently and automatically transferring workflows in case of FaaS system failures, as depicted in Figure 7. The "Failover" field of functions in the sub-graph specifies alternative FaaS systems, indicating pre-deployed backups (e.g., B of FaaS System2 in Figure 7). 

When a function fails to invoke subsequent functions (possibly due to FaaS system failures or network issues), Joint _λ_ does not immediately fail but rather captures the exception and enters the exception handling process. Joint _λ_ then uses the Backend-Shim to create a client for a backup FaaS system and re-invokes the function on the backup FaaS platform via asynchronous invocation (async_invoke). This capability allows Joint _λ_ to seamlessly migrate workflows in multi-cloud environments, enhancing availability without compromising cost or resource utilization. 

Joint _λ_ 

**11** 



<!-- Start of picture text -->
Failover<br> Exception! FaaS System1 {   "Name" : "A",<br>1     "Ds" : " NosqlKVDs ",<br>A B     "Next" : {<br>2 "Name" : "B",<br>FaaS System2 "FaaS" : "lambda",<br>InvocationFlow "Failover" : "alifc","InvokeMode" : " Sequence "}<br>B }<br><!-- End of picture text -->

**F I G U R E 7** An example of failover and its sub-graph definition. 

## **5.3 Data Transfer and Collaboration** 

## **5.3.1 Cross-platform Data Transfer** 

The "TransferByDs" primitive in the sub-graph determines the transfer method, while the "Ds" primitive specifies the type of data storage in Figure 5. Joint _λ_ supports **direct data transfer** through the _JointλObject_ in HTTP requests. For direct transfer, Joint _λ_ creates output data checkpoints on storage services co-located with the current FaaS platform, e.g., using AWS Lambda together with Amazon S3 or Amazon DynamoDB. Joint _λ_ also supports **indirect data transfer** via external storage when the request 



<!-- Start of picture text -->
intra-cloudtransfer egress storage A function cloud<br>E A B A B A A B A B<br>C C C C<br>A<br>E D E D E D E D<br>E<br>Sequence: [E]—>[A] FanIn: [B,C,D,E]—>[A] FanOut: [A]—>[B,C,D,E]<br><!-- End of picture text -->

**F I G U R E 8** The indirect data transfer for three invocation modes with different data placement. 

payload exceeds the hard quota of the FaaS platform (e.g., the size limit for asynchronous request payloads is 256 KB on AWS Lambda and 128 KB on Aliyun Function Compute). For indirect transfer, we aim to reduce data egress fees through strategic data placement. Analysis of data flows reveals that 1:1 (sequence) and n:1 (fan-in) invocation relationships cannot reduce the amount of egress traffic through data placement, as shown on the left and in the middle of Figure 8. However, concurrent 1:n invocations (fan-out) can optimize the number of egress data through data placement. We have devised a simple yet effective method for selecting the location of data storage based on the **majority rule principle** . Specifically, Joint _λ_ first counts the number of FaaS systems in the sub-graph and then selects the most frequent FaaS system to create data storage at the same location. This data storage is used to store the output data checkpoints, from which the next functions can read the data. As shown in the right of Figure 8, we can reduce the number of egress data by placing the data in the cloud where B, C and D functions are located. 

## **5.3.2 Cross-platform Function Collaboration** 

In distributed serverless Workflows on Jointcloud FaaS Systems, functions cannot directly communicate to check each other’s completion status. Therefore, multiple functions working together (e.g., invoking an aggregation function after accumulating four invocation requests) require a local coordination point. We believe that the _List_ data type in strongly consistent NoSQL _Key-Value_ storage is sufficient to serve as the local coordination point. Additionally, the sub-graph lists the metadata of all collaborating functions in the invocation primitives. Figure 9 shows how Joint _λ_ organizes the orchestration process for collaboration. Using the fan-in within the workflow on the left figure as an example, we explain how Joint _λ_ uses the bitmap primitive in Table 2 as the coordination mechanism. Joint _λ_ appends a suffix (e.g., -bitmap) to the unique ID of the aggregation function (function D in the figure) to obtain the coordination point’s key and creates the Boolean bitmap as an item in the DSBackend table-storage (i.e., AWS DynamoDB<sup>58</sup> or Aliyun TableStore<sup>59</sup> ), and is strategically co-located with the cloud provider that hosts 

**12** 

Li ET AL. 

the majority of the fan-in branches to minimize cross-cloud communication overhead. The boolean bitmap indicates whether a function has been executed. Functions A, B, and C update their corresponding boolean values in the bitmap to True after execution and perform a strongly consistent read of the bitmap. The function (B) that reads the target value (all elements of the bitmap being True) will invoke the aggregation function (D). 

_ByBatch_ and _ByRedundant_ on the right figure follow a similar orchestration process. However, to accommodate dynamics, the coordination point is set as a string List and is created in the same data storage as the invoked function. The key of the coordination point differs fan-in within the workflow on the left figure, using the concatenated names of all functions in the sub-graph as the key. 



<!-- Start of picture text -->
FanIn Values in Sub-graph: [A, B, C] WorkflowWait in Sub-graph: [B, E]<br>Cloud A B Cloud A X<br>2.Watch [1,1,1] Table 3.Invoke<br>A Table 1.Set True 3.Invoke StringList [outputkey1, ..., outputKey31]<br>bitmap [1,0,1] 1.Append outputKey2.Watch len(list)=32<br>Cloud B Cloud C Cloud B Cloud C<br>C D B E<br>Fan I n: [A,B,C]—>D ByBatch: [B,E]—>X, BatchS i ze=32<br>Function of a WorkflowEnd Function Start Functionof a Workflow CompletedOperation Orchestration Flow<br><!-- End of picture text -->

**F I G U R E 9** Cross-platform functions collaborate through partial coordination point. 

## **5.4 Unique Key and Function’s Reusability** 

Each workflow generates a workflow ID using a UUID in the initial function, and this ID is passed through the _JointλObject_ . The workflow ID serves as a common prefix for all names in the current workflow invocations, facilitating garbage collection after completion. Although the use of global function names and workflow IDs can distinguish different functions in different workflows, this is not sufficient for unique function naming. A single workflow may invoke the same function multiple times, such as in mappings, loops, or repeated usage. Joint _λ_ introduces step index and branch index to uniquely name function nodes. The step index increments with each step, while the branch index depends on the Branch field in the _JointλObject_ , relating to fan-out and fan-in operations. By calculating unique function names, Joint _λ_ supports unique data storage keys, ensuring the correctness of orchestration and the reusability of functions. 

As illustrated in Figure 10, Joint _λ_ appends a step index to function names at the same stage. Joint _λ_ uses a branch index to distinguish fan-out branches. For example, functions C and D are at step 2, located in branches 0 and 1, respectively, thus named C_2-bindex-0 and D_2-bindex-1. Joint _λ_ uses "+" to distinguish multiple branch levels. During a fan-out invocation, Joint _λ_ adds the corresponding Branch stack to the function’s name, as seen with function B. The purple numbers in the figure represent the new numbers to stack, with 0 and 1 are pushed onto name stacks of functions C and D, respectively. The Branch field continues to propagate until encountering a fan-in. The fan-in invocation primitive is used with _PopAndMerge_ , as fan-in involves merging at least one branch level, modifying the Branch field. For example, with functions F and E, Joint _λ_ names functions according to the order of the fan-in Branch in the sub-graph: E_3-bindex-0+0, E_3-bindex-1+0, and F_3-bindex-1. Then, it calculates the unique ID for function A. First, Joint _λ_ pops one level from all fan-in branches (e.g., from bindex-1+0 to bindex-0), resulting in E_3-bindex-0, E_3-bindex-0, and F_3. Next, Joint _λ_ merges the fan-in branches. The merge selects the highest index and level branch index and updates the Branch stack in the _JointλObject_ . Thus, this branch index becomes part of the unique ID for function A, i.e., A_4-index-0. Joint _λ_ treats Choice invocation the same as Sequence invocation within a single branch. 

**Garbage collection in a workflow.** During orchestration, Joint _λ_ stores data across multiple data storage systems. The intermediate data generated by FaaS workflows has a very short lifecycle because it is typically only valid within the current workflow. If left unmanaged, this temporary data will accumulate with each workflow invocation, leading to increased storage costs. The distribution of intermediate data across multiple clouds presents additional challenges for garbage collection. To 

Joint _λ_ 

**13** 



<!-- Start of picture text -->
Setp Index= 2<br>E_3-bindex- 0 +0<br>map<br>C_2-bindex- 0 fanin<br>sequence paraller E_3-bindex- 1 +0<br>A_0 B_1 A_4-bindex- 0<br>Event: JointλObject<br>...' WorkflowId ' : UUID, choice<br>' Step ' : 2, D_2-bindex- 1 F_3-bindex- 1<br>' Branch ' : {<br>' Index ' : 1,<br>' Size ' : 2,<br>}<br>G_3-bindex- 1<br><!-- End of picture text -->

**F I G U R E 10** Unique Id of functions in workflow. The _workflowId/_ prefix is omitted. 

address this, Joint _λ_ introduces a garbage collection mechanism. The GC function is an independent, parallel function that can automatically scale up or down based on demand. 

Joint _λ_ deploys Garbage Collection (GC) functions on compatible FaaS systems. The garbage collector is designed to be invoked by the workflow’s terminal function. Once the workflow ends, all GC functions in the cloud are invoked concurrently. The GC functions extract the workflow ID from the received _JointλObject_ and heterogeneously clean all data storage items with the workflow ID as their prefix, based on different storage backends. This process effectively cleans data across various cloud storage systems since all data items produced by a workflow share a common prefix. 

While object storage services such as Amazon S3 provide lifecycle rules for automatic expiration, Joint _λ_ retains an explicit GC mechanism for two reasons. First, lifecycle rules are typically coarse-grained (e.g., one day), whereas our GC reclaims short-lived workflow data immediately after completion. Second, Joint _λ_ spans multiple clouds and storage backends, so an independent GC function provides a unified cleanup mechanism across both object stores and table storage. 

## **6 EVALUATION** 

## **6.1 Experimental Setup** 

In this section, our evaluation answers the following questions: 

- _Question-1_ : Can Joint _λ_ achieve better performance and lower cost than serverless workflows on a single FaaS system? (§6.2) 

- _Question-2_ : Can Joint _λ_ enable efficient failover? (§6.3) 

- _Question-3_ : How does Joint _λ_ compare with state-of-the-art cross-cloud serverless workflow orchestrators? (§6.4) 

- _Question-4_ : What latency overheads are incurred when orchestrating workflows with Joint _λ_ ? (§6.5) 

**Setup.** We implement Joint _λ_ on two FaaS platforms, AWS Lambda and Aliyun Function Compute (FC), including configurations with GPU accelerators. We use fully managed NoSQL storage services provided by the CSPs to store checkpoints and coordination points, i.e., DynamoDB<sup>58</sup> and TableStore<sup>59</sup> . In our experiments, we do not modify the user functions’ upload and download logic; therefore, large data objects such as videos and datasets are still transferred through object storage (Amazon S3 and OSS, i.e., Alibaba Cloud Object Storage Service). The output data checkpoints record only the intermediate data produced by user functions. All services are co-located in the same region (ap-northeast-1 for AWS and ap-north-1 for Aliyun), except for Aliyun CloudFlow, which is deployed in us-west-1 due to regional support limitations. Each workflow uses a separate table and is warmed up in advance to reduce the effect of cold starts. 

**Baseline.** We compare Joint _λ_ with the following baselines. 

- **AWS Step Functions (ASF)**<sup>**38**</sup> **:** We use the ASF standard pattern to orchestrate serverless workflows on AWS Lambda as it implements exactly-once execution semantics. 

- **Aliyun CloudFlow (AC)**<sup>**41**</sup> **:** AC also uses the state-machine model and implements exactly-once execution semantics. It is used to orchestrate serverless workflows on Aliyun FC. 

**14** 

Li ET AL. 

- **xAFCL**<sup>**36,35**</sup> **:** xAFCL implements a middleware that can schedule and execute different functions in a workflow across multiple FaaS systems, with centralized orchestration. It consists of an orchestrator and a database node. 

- **XFaaS**<sup>**37**</sup> **:** XFaaS is a cross-platform orchestrator for serverless workflows based on connector-based cloud orchestration services. However, because the connector is a message queue, it only supports linear compositions. XFaaS is only used to evaluate sequence workflows. 

- **Lithops**<sup>**51,60,46**</sup> **:** Lithops is a distributed computing framework that leverages multi-cloud FaaS systems. It allows local embarrassingly parallel tasks to be accelerated by outsourcing. It views functions as homogeneous workers, i.e., cloud threads. Workers pull code and data before running. Lithops is only used to evaluate parallel tasks in workflows. 



<!-- Start of picture text -->
Video Question IoT Pipeline Monte Carlo (MC)<br>Analytics Answering Simulation<br>Split document_sort record data_map<br>(2048MB RAM) (512MB RAM) (512MB RAM) (1024MB RAM)<br>Map Map<br>(512MB RAM)Extract (4096MB RAM & 8G GPU)BERT (512MB RAM)record data_process(512MB RAM)<br>.... Fan-in<br>Image_process record data_aggregation<br>(2048MB RAM) (512MB RAM) (512MB RAM)<br>Fan-in<br>ResNet50 record<br>(4096MB RAM (512MB RAM)<br>& 8G GPU)<br>Function on AWS<br>Function on Aliyun FC<br>Lambda<br><!-- End of picture text -->

**F I G U R E 11** DAGs of the serverless workflows in the evaluation. 

**Workload.** Our experiments use four representative serverless workflows. These workflows have different characteristics in terms of structure, data dependencies, and FaaS systems. Figure 11 shows the DAGs of workflows, and the details are as follows. 

- **Video Analytics** is based on our modified Orion<sup>61</sup> , which consists of four stages: video split, frame extraction, image processing, and image recognition. Each workflow invocation processes a 1-minute video with 4 or 8 parallel branches. 

- **Question Answering Inference** is a batch task with the raw document datasets stored in Amazon S3. It consists of two stages: article and question sorting, and QA inference<sup>62</sup> . Each workflow execution infers 4 QA and transfers about 40KB data. 

- **IoT Pipeline** is a synthetic sequence workflow in which each stage simply receives a small IoT payload, returns it unchanged, and lets the runtime checkpoint and asynchronously forward it to the next function. We vary the number of stages in the chain, and the intermediate payload size is fixed at 1 KB. 

- **Monte Carlo (MC) Simulation** is adopted from xAFCL<sup>36</sup> and is often used for numerical simulations in scientific computing. Each workflow execution generates 1 million numbers (data_map). We estimate the PI value (data_aggregation) using a variable number of parallel branches (data_process). 

## **6.2 Benefits of Multiple FaaS in Joint** _λ_ 

We first compare Joint _λ_ with ASF and AC on two real-world applications: video analytics and QA inference. Joint _λ_ deploys ResNet50 on Aliyun FC to accelerate inference by leveraging GPUs. 

Figure 12(a) displays the P95 end-to-end makespan achieved by all orchestrators. The Joint _λ_ implementation achieves the fastest execution, reducing makespan by 26% and 21% compared to AC and ASF, respectively, when the fan-out size is 8. Joint _λ_ also reduces makespan by 43% and 21% compared to AC and ASF, respectively, when the fan-out size is 4. Joint _λ_ consistently has lower orchestration overhead for both branch sizes due to its distributed orchestration design. 

Joint _λ_ 

**15** 



<!-- Start of picture text -->
Joint<br>Fanout size = 4 Fanout size = 8 User functions Egress<br>Critical Path Functions Critical Path Functions Indirect R Checkpoint W&R<br>Orchestration Orchestration Joint runtime Coordination point W&R<br>700 ASF and AC<br>User functions<br>600<br>4000 Orchestration<br>1225.7<br>2470.6 500<br>3000 2244.02 968.5 525.0 525.0<br>400<br>914.1<br>27.3<br>2000 573.7 300 74.4<br>9.5<br>3142.5 46.0<br>1000 2088.0 1929.9 2239.4 1777.4 2470.6 200 2.2<br>100 169.7 167.2 195.9<br>0 0<br>ASF AC Joint ASF AC Joint<br>(a) P95 Makespan of video analytics workflow (b) Average cost of video analytics workflows when the fan-out size is 8<br>P95 Makespan (ms)<br>Cost per 10^6 workflow runs ($)<br><!-- End of picture text -->

**FIGURE 12** The comparison between ASF, AC and Joint _λ_ implementation for Video Analytics workflow. Costs are computed per workflow run and linearly scaled to 10<sup>6</sup> workflow runs for presentation. 

Figure 12(b) presents the total cost of video analytics workflow incurred by different orchestrators when the fan-out size is 8. Joint _λ_ saves at least 48% cost compared to AC and ASF. Independent cloud orchestration services charge $25 per 1 million state transitions and the orchestration cost accounts for at least 75% of the total cost for both AWS Step Functions and AC in this workflow. However, only 44% total cost is used for orchestration in Joint _λ_ . We observe that the cost of Checkpoint W&R (write and read) takes up most of the orchestration cost, which is worth it because it can ensure fault tolerance. 



<!-- Start of picture text -->
AWS and ALiYun Joint<br>1600 User functions User function User functions<br>Orchestration Orchestration Joint runtime<br>1400 529.8 120 Egress<br>checkpoints W&R<br>1200<br>100<br>1000<br>80<br>100<br>800 100<br>1136.7 60<br>600<br>1058.7<br>400 40 9.6<br>4.4<br>340.2<br>11.3<br>200 20<br>25.7<br>130.7 133.7 17.6 17.5<br>0 0<br>ASF AC Joint ASF AC Joint<br>(a) P95 Makespan of QA workflow (b) Average cost of QA workflow<br>P95 Makespan (ms)<br>Cost per 10^6 workflow runs ($)<br><!-- End of picture text -->

**FIGURE 13** The comparison between ASF, AC and Joint _λ_ implementation for QA workflow. Costs are computed per workflow run and linearly scaled to 10<sup>6</sup> workflow runs for presentation. 

As shown in Figure 13(a), in the QA inference workflow, the Joint _λ_ implementation exhibits the fastest execution, delivering a 2.6 _×_ and 3.3 _×_ improvement over AC and ASF, respectively. The reduced workflow makespan mainly stems from inter-cloud heterogeneity and the difference in orchestration performance. Joint _λ_ fully utilizes heterogeneous accelerators in terms of user-functions computation. In terms of cost (Figure 13(b)), Joint _λ_ achieves a 63% cost savings over AC and a 65% reduction compared to ASF. The majority of Joint _λ_ ’s orchestration cost (up to 26%) is attributed to the Joint _λ_ runtime. The second largest cost factor is the checkpoint W&R (Write and read), accounting for 22% of the total orchestration expenditure. 

**16** 

Li ET AL. 

To conclude, Joint _λ_ can leverage heterogeneous FaaS systems across clouds to accelerate functions execution thereby optimizing workflows. 

## **6.3 Failover Overhead** 

We use wrong invocations to inject failures in a controlled manner. Concretely, we intentionally configure a downstream function identifier that does not exist (e.g., an invalid function name on the target FaaS) in the MetaConfig, so that the invocation request deterministically fails and triggers Joint _λ_ ’s exception handling and failover logic. This emulates cloud-side unavailability from the orchestrator’s perspective without modifying the FaaS platform. 

Figure 14 shows the Joint _λ_ implementation (A, B, C, B1) and the single-cloud orchestrator implementation (A, B, C). Each function in the workflow executes a no operation instruction and is configured with 512 MB of RAM to ensure a fair comparison across systems. Joint _λ_ deploys function replica B1 on another FaaS platform in the same region, where the replica is launched only when invoked. For cross-cloud failover and invocation, the runtime must hold provider credentials or tokens that authorize calls to the target cloud. In our prototype, these credentials are provisioned to the runtime environment in advance; in practice, short-lived tokens or role-based credentials are preferable to long-lived static secrets to reduce security risk. We configure the workflow to be invoked every 100 ms and inject wrong invocations to simulate outages on the cloud platform hosting function B1 during the interval from the 10th to the 20th second after the start time. 



<!-- Start of picture text -->
Cloud1<br>A B C<br>Cloud2<br>B1<br><!-- End of picture text -->

**F I G U R E 14** Simulate cloud outages where a FaaS system is located. 

Figure 15 shows the end-to-end time of the workflow from 0 to 30 seconds. During the 10 to 20 second interval, the workflow on a single FaaS system exceeds the maximum number of retries for the orchestration service, resulting in a failure. It cannot execute successfully until the FaaS system recovers 20 seconds later, as shown in Figure 15(b). However, Figure 15(a) shows that Joint _λ_ enables failover even after the failure of a FaaS system on a single cloud. It can automatically transfer the workflow to an alternate FaaS system in the same region to continue execution. 

In order to succinctly compare the time overhead of failover and normal execution, Figure 15(a) shows the total execution time in both cases. The additional overhead introduced during failover averages about 78 ms. The increased makespan comes from creating alternative FaaS system clients and one additional cross-cloud invocation. Failover adds only 0.501$ per 1M invocations in extra cost. Assuming the makespan SLO of the workflow is 300 ms, Joint _λ_ only violates the SLO during cold start. It reduces SLO violations by close to 99.9% compared to a single-FaaS workflow and improves availability to nearly 1. 

In conclusion, Joint _λ_ can efficiently disaster-transfer (failover) serverless workflows, incurring negligible additional overhead relative to the overall time and costs. 

## **6.4 Function-side Orchestration** 

Besides the comparison with serverless workflows on a single FaaS, we also focus on the performance and cost overhead of Joint _λ_ and other state-of-the-art cross-platform orchestrators for orchestrating workflows on multiple FaaS systems. We choose a typical sequence workflow and a parallel-aggregate workflow to evaluate the overhead of orchestrating these basic workflow patterns. **Sequence.** We evaluate the orchestrator’s state transition overhead using an IoT pipeline that passes data alternately on two FaaS systems. Since the execution time of the user function is very short ( 10ms), the execution time of the workflow is essentially 

Joint _λ_ 

**17** 



<!-- Start of picture text -->
500<br>400<br>300<br>200<br>100<br>0<br>0 5 10 15 20 25 30<br>Start Time(s)<br>Makespan (ms)<br><!-- End of picture text -->

(a) Workflow on multiple FaaS based on Joint _λ_ 



<!-- Start of picture text -->
1000<br>900<br>800<br>700<br>600<br>500<br>400<br>0 5 10 15 20 25 30<br>Start Time(s)<br>Makespan (ms)<br><!-- End of picture text -->

(b) Workflow on single FaaS based on cloud orchestration services 

**F I G U R E 15** Makespan of workflows in the same region during cloud outage. 



<!-- Start of picture text -->
2500 xAFCL XFaaS 5000 xAFCL joint<br>joint Lithops<br>2000 4000<br>1500 3000<br>1000<br>2000<br>500<br>1000<br>0<br>1 2 3 4 5 6 7 8 9 10 2 4 8 16 32 64 128 256<br># Functions # Parallel Branches<br>P95 Makespan (ms) P95 Makespan (ms)<br><!-- End of picture text -->

(a) P95 Makespan of IoT Pipeline for different number of functions 

(b) P95 Makespan of MC workflows for different number of parallel branches 

**F I G U R E 16** P95 Makespan of IoT Pipeline and Monte Carlo Simulation. 

equal to the time of orchestration. Figure 16(a) shows the comparison of P95 makespan for Joint _λ_ , xAFCL, and XFaaS for different lengths of IoT pipeline. For different numbers of functions, the total makespan of Joint _λ_ is consistently lower than that of xAFCL and XFaaS. At a length of 1, the makespans of the three orchestrators are close. As the number of functions increases, this gap between Joint _λ_ and the other two is gradually larger. This is due to increased cross-cloud transfers as the number of functions increases. When the number of functions is 10, Joint _λ_ is at least 2.5 _×_ faster than xAFCL and XFaaS. Compared to the other two centralized orchestrators, Joint _λ_ can improve orchestration performance by reducing cross-cloud transfer overhead. **Parallel-aggregate.** The parallel nature of MC simulation makes it an excellent candidate for our experiment. MC spawns a large number of parallel functions to partition computation. While XFaaS doesn’t support fan-in orchestration, we compare Joint _λ_ with Lithops and xAFCL. The P95 makespan comparison of xAFCL, Lithops, and Joint _λ_ of MC workflow is shown in Figure 16(b). When the number of parallel branches is 16, Joint _λ_ reduces the makespan by 22% compared to xAFCL, and by 77% compared to Lithops. As the number of parallel branches increases, the optimization results of Joint _λ_ become more significant compared to xAFCL and Lithops, improving 2.1 _×_ and 4.0 _×_ respectively with 128 parallel branches. 

Lithops’ worker runtime initialization degrades its performance, introducing approximately 500 ms of additional makespan. xAFCL and Lithops are both limited by centralized orchestration, which incurs higher makespan as the number of branches increases. This indicates that the centralized bottleneck further limits parallel scalability. 

In short, Joint _λ_ achieves the best performance on these common workflow patterns. This result indicates that distributed control flow is beneficial for reducing workflow makespan when orchestrating workflows on Jointcloud FaaS systems. **Cost.** The cost comparison between Joint _λ_ and the baselines is presented in Table 3. Joint _λ_ achieves on-demand billing for serverless workflows on Jointcloud FaaS systems, charging only for the resources actually used. However, most existing crossplatform orchestrators require VMs to host orchestration and datastore nodes. These VMs are billed by the hour, and their total cost depends on runtime duration and resource utilization. For a relatively fair comparison among VM-hosted baselines, we 

**18** 

Li ET AL. 

**T A B L E** 3 The cost comparison between Joint _λ_ and other orchestrators. N is the number of concurrent workflow runs. Totals are computed for 10<sup>6</sup> workflow runs with _N_ =2. For external orchestration VMs, we use m6g.2xlarge to reflect that orchestration is a lightweight long-running service and to avoid orchestration becoming the bottleneck. For VM-based datastores, we use m6g.large (0.099$ per hour) as a modest configuration. 

|Workflow|Orchestrator|Function Execution & Invocation(cost)|External Orchestration|DataStore|Total(N=2)|
|---|---|---|---|---|---|
|IT|xAFCL|2.39$ per 1M|0.396$ per hour (m6g.2xlarge)|0.099$ per hour (m6g.large)|191.55$|
|o<br>Lth 10|XFaaS|4.86$ per 1M|1500$ per 1M|0$|1504.86$|
|(eng: )|Joint_λ_|5.95$per 1M|0$|48.50$per 1M(W&R)|54.45$|
||xAFCL|11.12$ per 1M|0.396$ per hour (m6g.2xlarge)|0.099$ per hour (m6g.large)|86.17$|
|MC|Lithops|59.64$ per 1M|0.396$ per hour (m6g.2xlarge)|162.24$ per 1M (W&R)|447.24$|
|(fan-out size: 32)|Joint_λ_|18.17$ per 1M|0$|279.05$ per 1M (W&R)|297.22$|
||Joint_λ_-VM|18.17$per 1M|0$|0.099$per hour(m6g.large)|28.24$|



assume that there are _N_ concurrent workflow runs (i.e., _N_ workflows execute in parallel) and that the utilization rate of the VM is 100%. Thus the cost of the VM can be estimated as ( _unit_  price ∗ M ∗ T_ )/ _N_ , where _unit_  price_ is the price of the VM per hour, _M_ is the number of workflow invocations (e.g., 10<sup>6</sup> ), and _T_ is the end-to-end time (makespan) of the workflow, as shown in Figure 16. We conservatively use the higher price between Amazon DynamoDB and Aliyun TableStore, i.e., 1.4269$ per 1M writes and 0.285$ per 1M reads. “Function Execution & Invocation” is computed from the measured average function duration (under its configured memory) using the providers’ on-demand billing rates plus the per-request charge, and then scaled to 10<sup>6</sup> workflow runs. For Joint _λ_ ’s managed datastore cost (W&R), we count protocol-induced reads and writes and multiply them by the per-million request prices, yielding 48.50$ for the IoT workflow and 279.05$ for MC (fan-out = 32). For Lithops, the managed datastore cost is computed from per-request pricing of the underlying object-storage operations, resulting in 162.24$ for MC (fan-out = 32). For XFaaS, we model the external orchestration overhead using transition-based billing of managed workflow services: following the DAG in Figure 11, an IoT pipeline of length = 10 incurs about 20 orchestration steps, and each hop involves three service-level state transitions, resulting in 3 _×_ 20=60 transitions per workflow run. Under a $0.025 per 1000-transitions price, this gives 60 _×_ 10<sup>6</sup> /1000 _×_ 0.025=$1500 per 10<sup>6</sup> runs. Since the egress fees for cross-cloud workflows under multiple orchestrators are very close, we do not discuss them. 

Joint _λ_ is more expensive in terms of function execution cost because each function needs to run additional runtime libraries. Lithops is also expensive because its worker runtime initialization time is longer. However, Joint _λ_ does not require a standalone orchestrator, so its external orchestration cost is 0. For data storage, Joint _λ_ uses managed storage services and therefore incurs charges for checkpoints and coordination points. For the IoT workflow with 10 functions, Joint _λ_ is about 3.5 _×_ and 27.6 _×_ cheaper than xAFCL and XFaaS, respectively. For the MC workflow (fan-out size = 32), xAFCL becomes cheaper when provisioned with a modest external orchestration VM, while Joint _λ_ remains 1.5 _×_ cheaper than Lithops. Joint _λ_ provides execution guarantees for a large number of parallel functions, which increases datastore cost. Based on this analysis, we can rent a VM to host the datastore node to reduce the cost, as shown by Joint _λ_ -VM in Table 3, which further reduces the total cost by about 3.1 _×_ compared to xAFCL. 

## **6.5 Orchestration Overhead of Joint** _λ_ 

To probe the latency introduced by the function-side orchestrator of Joint _λ_ , Figure 17 presents decomposed latency traces for a sequence function (from AWS Lambda to Aliyun FC), a fan-in function, and map functions from the IoT pipeline and MC simulation (fan-out size = 32). 

For sequence invocation mode, most of the overhead is writing and reading checkpoints, which take up 48.5% of the total Joint _λ_ runtime. Each record function execution introduces 3W2R (3 writes and 2 reads) datastore operations, where 2W1R are for invocation checkpoints and 1W1R are for output data checkpoints. 

For map invocation mode, asynchronous invocation is the largest overhead, accounting for 68% of the total Joint _λ_ runtime. The data_map function invokes 32 functions concurrently, resulting in higher asynchronous invocation overhead. Since the number of subsequent (downstream) functions is greater than 10, Joint _λ_ writes invocation checkpoints in batches, i.e., it performs batch writes 4 times. Each execution of the function generates 5W1R datastore operations for the invocation checkpoint, while the output data checkpoint still generates 1W1R. The performance bottleneck of data_map lies in the numerous cross-cloud parallel invocations, and the use of batched checkpoint writes effectively reduces the time overhead. The data_process function, which uses fan-in invocation mode, increases execution time due to the additional operations required for reading and writing 

Joint _λ_ 

**19** 



<!-- Start of picture text -->
User functions Coordination point W&R Async Invocation<br>Checkpoint R&W Others<br>175<br>150 62.8<br>125 4.6<br>21.9<br>100 99.9<br>75 52<br>28<br>50 5 4.1<br>25 31.1 42.9 42.8<br>0 10.1 1<br>Joint _sequence Joint _fanin Joint _map<br>Time (ms)<br><!-- End of picture text -->

**F I G U R E 17** Joint _λ_ ’s cross-cloud sequence, fan-in and map overhead. Waiting time for asynchronous queue after invocation is not added. 

the bitmap (coordination point W&R). The coordination point additionally introduces 2W2R datastore operations. The last completed parallel data_process function invokes an aggregate function. Each function execution also introduces 3W2R datastore operations. The differences between it and the record function in terms of checkpoint latency and invocation latency stem from the heterogeneity of cloud platforms. 

In summary, Joint _λ_ introduces modest orchestration latency. The main performance overhead is in reading and writing the datastore and in a large number of parallel function invocations. 

## **7 CONCLUSION** 

This paper proposes Joint _λ_ , a distributed runtime system for orchestrating serverless workflows across multiple FaaS systems. Joint _λ_ leverages inter-cloud heterogeneity to reduce completion time and cost. By using function-side orchestration instead of centralized nodes, it enables independent function invocations and data transfers, thereby reducing cross-cloud communication overhead. In addition, Joint _λ_ supports exactly-once execution semantics and provides fault tolerance and failover in multicloud environments. Joint _λ_ allows users to flexibly design workflows that exploit inter-cloud heterogeneity. Compared with standalone cloud providers’ orchestrators and state-of-the-art cross-cloud serverless workflow engines, Joint _λ_ consistently improves performance for cross-cloud workflow orchestration and can reduce cost in representative settings. 

## **ACKNOWLEDGEMENTS** 

This work is supported by the National Natural Science Foundation of China (No. 62202479 and No. 61772030) and the National Key Laboratory Funding Project (No. 2025-KJWPDL-04). During the preparation of this work, the authors used Gemini<sup>63</sup> to polish the manuscript. After using this service, the authors reviewed and edited the content as needed and take full responsibility for the content of the published article. 

### **REFERENCES** 

1. Jonas E, Schleier-Smith J, Sreekanti V, et al. Cloud Programming Simplified: A Berkeley View on Serverless Computing. _arXiv (Cornell University)._ 2019. doi: 10.4230/oasics.microservices.2020-2022.5 

2. Fouladi S, Wahby RS, Shacklett B, et al. Encoding, fast and slow:{Low-Latency} video processing using thousands of tiny threads. In: USENIX Association. 2017:363–376. 

3. Fouladi S, Romero F, Iter D, et al. From laptop to lambda: outsourcing everyday jobs to thousands of transient functional containers. In: USENIX. 2019:475–488. 

4. Zhang H, Cardoza A, Chen PB, Angel S, Liu V. Fault-tolerant and transactional stateful serverless workflows. _Operating Systems Design and Implementation._ 2020:1187–1204. 

5. Liu DH, Levy A, Noghabi S, Burckhardt S. Doing more with less: Orchestrating serverless applications without an orchestrator. In: USENIX Association. 2023:1505–1519. 

6. Li Z, Liu Y, Guo L, et al. FaaSFlow: enable efficient workflow execution for function-as-a-service. In: ACM. 2022:782–796 

7. Burckhardt S, Gillum C, Justo D, Kallas K, McMahon C, Meiklejohn C. Durable functions: semantics for stateful serverless. In: . 5. ACM. 2021:1–27 

8. Ao L, Izhikevich L, Voelker GM, Porter G. Sprocket. In: ACM. 2018:263–274 

**20** 

Li ET AL. 

9. Malawski M, Gajek A, Zima A, Balis B, Figiela K. Serverless execution of scientific workflows: Experiments with hyperflow, aws lambda and google cloud functions. _Future Generation Computer Systems._ 2020;110:502–514. 

10. Yu M, Cao T, Wang W, Chen R. Following the data, not the function: Rethinking function orchestration in serverless computing. In: USENIX Association. 2023:1489–1504. 

11. Wen J, Liu Y, Chen Z, Chen J, Ma Y. Characterizing commodity serverless computing platforms. _Journal of Software: Evolution and Process._ 2023;35(10):2394–2417. 

12. Copik M, Kwa´sniewski G, Besta M, Podstawski M, Hoefler T. SeBS: A Serverless Benchmark Suite for Function-as-a-Service Computing. _Zenodo (CERN European Organization for Nuclear Research)._ 2021. doi: 10.5281/zenodo.5209001 

13. Maissen P, Felber P, Kropf P, Schiavoni V. FaaSdom. In: ACM. 2020:73–84 14. Yu T, Liu Q, Du D, et al. Characterizing serverless platforms with serverlessbench. In: ACM. 2020:30–44 15. Kim J, Lee K. Practical Cloud Workloads for Serverless FaaS. In: ACM. 2019:477–477 16. Alibaba Cloud . Function Compute - Fully Managed Serverless Compute Service. https://www.aliyun.com/product/fc; 2026. [Online; Accessed: 2026-03-24]. 

17. Yang Y, Zhao L, Li Y, et al. INFless: a native serverless system for low-latency, high-throughput inference. In: ACM. 2022:768–781 18. Du D, Liu Q, Jiang X, Xia Y, Zang B, Chen H. Serverless computing on heterogeneous computers. In: ACM. 2022:797–813 19. Yang Z, Wu Z, Luo M, et al. {SkyPilot}: An intercloud broker for sky computing. In: USENIX Association. 2023:437–455. 20. Taylor J. Google Cloud accidentally deletes UniSuper’s online account due to ’unprecedented misconfiguration’. _The Guardian_ ; 2024. Available at: https://www.theguardian.com/australia-news/article/2024/may/09/unisuper-google-cloud-issue-account-access (Accessed: March 27, 2026). 

21. Shi P, Liu H, Yang S, Zhang Y, Zhong Y. The inherent mechanism and a case study of the constructional evolution of the jointcloud ecosystem. _IEEE Internet of Things Journal._ 2019;7(3):1561–1571. 

22. Keahey K, Tsugawa M, Matsunaga A, Fortes J. Sky computing. _IEEE Internet Computing._ 2009;13(5):43–51. 23. Amazon Web Services, Inc. . Serverless Computing - AWS Lambda - Amazon Web Services. https://aws.amazon.com/cn/lambda/; 2025. Accessed March 24, 2026. 

24. Alibaba Cloud . Function Compute FC - Fully Managed Serverless Computing Service - Alibaba Cloud. https://www.aliyun.com/product/fc; 2026. Accessed March 24, 2026. 

25. Docker . The docker containerization platform,. https://www.docker.com; 2026. Accessed: 2026-03-27. 26. Agache A, Brooker M, Iordache A, et al. Firecracker: Lightweight virtualization for serverless applications. In: USENIX Association. 2020:419– 434. 

27. gVisor G. Google gvisor: Container runtime sandbox,. https://github.com/google/gvisor; 2026. Accessed: 2026-03-27. 28. Wen J, Liu Y. A Measurement Study on Serverless Workflow Services. In: IEEE. 2021:741–750 29. Devlin J, Chang MW, Lee K, Toutanova K. Bert: Pre-training of deep bidirectional transformers for language understanding. In: Association for Computational Linguistics. 2019:4171–4186. 

30. He K, Zhang X, Ren S, Sun J. Deep Residual Learning for Image Recognition. In: IEEE. 2016:770–778 31. Pu Q, Venkataraman S, Stoica I. Shuffling, Fast and Slow: Scalable Analytics on Serverless Infrastructure. _Networked Systems Design and Implementation._ 2019:193–206. 

32. Jarachanthan J, Chen L, Xu F, Li B. <i>Astrea:</i>Auto-Serverless Analytics Towards Cost-Efficiency and QoS-Awareness. _IEEE Transactions on Parallel and Distributed Systems._ 2022;33:3833–3849. doi: 10.1109/tpds.2022.3172069 

33. Wang Z, Zhang R, Zhang S, Cheng W, Wang W, Cui Y. Edge-assisted adaptive configuration for serverless-based video analytics. _IEEE Transactions on Networking._ 2025. 

34. Jia Z, Witchel E. Boki: Stateful serverless computing with shared logs. In: ACM. 2021:691–707. 35. Ristov S, Gritsch P. FaaSt: Optimize makespan of serverless workflows in federated commercial FaaS. In: IEEE. 2022:183–194 36. Ristov S, Pedratscher S, Fahringer T. xAFCL: Run Scalable Function Choreographies Across Multiple FaaS Systems. _IEEE Transactions on Services Computing._ 2021:1–1. doi: 10.1109/tsc.2021.3128137 

37. Khochare A, Khare T, Kulkarni V, Simmhan Y. XFaaS: Cross-platform Orchestration of FaaS Workflows on Hybrid Clouds. In: ACM. 2023:498–512 38. Amazon Web Services . AWS Step Functions - Visual Workflow Service. https://aws.amazon.com/cn/step-functions; 2026. [Online; Accessed: 2026-03-24]. 

39. Google . Google cloud composer,. https://cloud.google.com/composer; 2026. Accessed: 2026-03-27. 

40. Azure . Durable Functions overview. Microsoft Learn; 2026. Available at: https://learn.microsoft.com/en-us/azure/azure-functions/durable/ durable-functions-overview (Accessed: March 27, 2026). 

41. Alibaba Cloud . CloudFlow: Serverless Application Orchestration for DevOps. https://www.alibabacloud.com/en/product/serverless-workflow; 2024. Accessed: 2026-03-24. 

42. Sreekanti V, Wu C, Lin XC, et al. Cloudburst. In: . 13. VLDB Endowment. 2020:2438–2452 43. Carver B, Zhang J, Wang A, Anwar A, Wu P, Cheng Y. Wukong: A scalable and locality-enhanced framework for serverless parallel computing. In: ACM. 2020:1–15. 

44. Burckhardt S, Chandramouli B, Gillum C, et al. Netherite: Efficient execution of serverless workflows. _Proceedings of the VLDB Endowment._ 2022;15(8):1591–1604. 

45. Jonas E, Pu Q, Venkataraman S, Stoica I, Recht B. Occupy the Cloud: Distributed Computing for the 99doi: 10.48550/arxiv.1702.04024 46. Sampé J, Vernik G, Sánchez-Artigas M, García-López P. Serverless Data Analytics in the IBM Cloud. In: N. A. 2018:1–8 47. Amazon Web Services . Amazon Web Services (AWS). https://aws.amazon.com/; 2026. Accessed: 2026-03-27. 48. Google Cloud . Google Cloud Platform (GCP). https://cloud.google.com/; 2026. Accessed: 2026-03-27. 

49. Setty S, Su C, Lorch JR, et al. Realizing the {Fault-Tolerance} promise of cloud storage using locks with intent. In: USENIX Association. 2016:501–516. 

50. Bali´s B. HyperFlow: A model of computation, programming approach and enactment engine for complex distributed workflows. _Future Generation Computer Systems._ 2015;55:147–162. doi: 10.1016/j.future.2015.08.015 

51. cloud l. Lithops,. https://github.com/lithops-cloud/lithops; 2026. Accessed: 2026-03-27. 

52. Ge Z, Peng Y. GlobalFlow: A Cross-Region Orchestration Service for Serverless Computing Services. In: IEEE. 2019 

Joint _λ_ 

**21** 

53. Raith P, Rausch T, Furutanpey A, Dustdar S. faas-sim: A trace-driven simulation framework for serverless edge computing platforms. _Software: Practice and experience._ 2023;53(12):2327–2361. 

54. Zhu L, Tamburri DA, Casale G. RADF: Architecture decomposition for function as a service. _Software: Practice and Experience._ 2024;54(4):566– 594. 

55. Bueno A, Rubio B, Martín C, Díaz M. Functions as a service for distributed deep neural network inference over the cloud-to-things continuum. _Software: Practice and Experience._ 2024;54(8):1297–1311. 

56. Amazon Web Services . Amazon S3: Cloud Object Storage. https://aws.amazon.com/s3/; 2026. Accessed: 2026-03-24. 57. Alibaba Cloud . Object Storage Service (OSS): Secure, Reliable, and Low-cost Cloud Storage. https://www.alibabacloud.com/en/product/ object-storage-service; 2026. Accessed: 2026-03-24. 

58. Amazon Web Services, Inc. . Amazon DynamoDB Serverless Database - AWS Cloud Services. https://aws.amazon.com/cn/dynamodb/; 2025. Accessed March 24, 2026. 

59. Alibaba Cloud . Tablestore - Massive Structured Data Storage, Retrieval, and Analysis - Alibaba Cloud. https://www.aliyun.com/product/ots; 2026. Accessed March 24, 2026. 

60. Sánchez-Artigas M, Eizaguirre GT, Vernik G, Stuart L, García-López P. Primula: A practical shuffle/sort operator for serverless computing. In: ACM. 2020:31–37. 

61. Mahgoub A, Yi EB, Shankar K, Elnikety S, Chaterji S, Bagchi S. {ORION} and the three rights: Sizing, bundling, and prewarming for serverless {DAGs}. In: USENIX Association. 2022:303–320. 

62. Schmid P. serverless-bert-huggingface-aws-lambda-docker,. https://github.com/philschmid/serverless-bert-huggingface-aws-lambda-docker; 2026. Accessed: 2026-03-27. 

63. Google . Gemini. https://gemini.google.com/app; 2026. Accessed: 2026-03-28. 

