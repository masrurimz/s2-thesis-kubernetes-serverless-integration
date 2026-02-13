## 2.3 Performa Aplikasi Cloud (Cloud Application Performance)

Measuring and managing cloud application performance requires a structured framework of metrics, targets, and monitoring approaches [9], [10].

### 2.3.1 SLA, SLO, dan SLI (Service Level Agreements)

A **Service Level Agreement (SLA)** is a contractual commitment between a service provider and consumer that defines expected performance levels and the consequences of failing to meet them [9].

An SLA is operationalized through:
- **SLI (Service Level Indicator)**: A quantitative measure of a service aspect (e.g., request latency, error rate, throughput).
- **SLO (Service Level Objective)**: A target value or range for an SLI (e.g., "p99 latency < 200ms").

**Table 2-4: Common SLO Targets**

| Metric | Typical Target | This Research |
|--------|---------------|---------------|
| p50 Latency | < 50ms | Measured |
| p95 Latency | < 100ms | Measured |
| p99 Latency | < 200ms | **Primary SLO** |
| Error Rate | < 0.1% | Measured |
| Availability | > 99.9% | Not evaluated |

This research uses p99 (99th percentile) latency as the primary SLO indicator, following the tail-at-scale principle articulated by Dean and Barroso [10]: in distributed systems, overall user-perceived latency is determined by the slowest component in the request path. Optimizing tail latency—rather than mean or median—is therefore essential for maintaining consistent user experience.

### 2.3.2 Waktu Respons Permintaan (Request Response Time)

Response time is the total duration from when a client sends a request to when it receives the complete response. It decomposes into:

$$\text{Total Response Time} = \text{Network Latency} + \text{Queue Time} + \text{Processing Time}$$

In a hybrid architecture, network latency includes routing overhead (HAProxy decision + backend selection), queue time includes any waiting in the Kubernetes or serverless request queue, and processing time is the actual application computation. Cold start latency in serverless adds to the processing time component for the first invocation.

**Tail latency** (p99, p99.9) represents the response time experienced by the slowest 1% or 0.1% of requests. Dean and Barroso [10] demonstrate that at scale, tail latency has outsized impact on user experience because any single slow backend can delay an entire aggregated request. The routing controller in this research monitors p99 latency specifically because it captures degradation before it affects the majority of users.

### 2.3.3 Utilisasi Sumber Daya (Resource Utilization)

Key resource metrics for evaluating cloud application efficiency include:

- **CPU Utilization**: Percentage of allocated CPU capacity consumed. Over-provisioning (low utilization) wastes cost; under-provisioning (high utilization) risks latency degradation.
- **Memory Utilization**: Percentage of allocated memory consumed. Memory pressure can trigger OOM (Out of Memory) kills, causing pod restarts.
- **Network I/O**: Bytes sent and received, relevant for detecting bandwidth saturation.

Aslanpour et al. [9] provide a comprehensive taxonomy of performance evaluation metrics for cloud, fog, and edge computing, noting that the most informative metrics depend on the deployment model and workload characteristics.

### 2.3.4 Skalabilitas dan Elastisitas (Scalability and Elasticity)

**Scalability** is the ability of a system to handle increasing workload by adding resources. Two types exist:
- **Vertical scaling** (scale-up): Adding CPU, memory, or storage to existing instances.
- **Horizontal scaling** (scale-out): Adding more instances to distribute load.

**Elasticity** extends scalability with the ability to both acquire and release resources automatically in response to demand changes. An elastic system scales out during traffic surges and scales in during lulls, matching resource allocation to actual demand over time [9].

Kubernetes achieves elasticity through the Horizontal Pod Autoscaler (HPA), which reacts to observed CPU or custom metrics. Serverless platforms offer inherent elasticity by provisioning function instances per invocation. The distinction between scalability (can the system grow?) and elasticity (does it grow and shrink automatically?) is central to this research, as the hybrid system combines Kubernetes's controlled scalability with serverless's rapid elasticity.
