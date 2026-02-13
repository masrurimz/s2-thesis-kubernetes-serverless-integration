## 2.6 Ringkasan Tinjauan Pustaka (Literature Review Summary)

This chapter has established the theoretical foundations for the proposed hybrid Kubernetes-serverless architecture. Table 2-6 summarizes the key concepts and their relevance to this research:

**Table 2-6: Literature Review Summary**

| Topic | Key References | Relevance to This Research |
|-------|---------------|---------------------------|
| Cloud computing models | [1], [17] | Motivates hybrid deployment strategy |
| Kubernetes orchestration | [2], [4], [12] | Baseline platform for container workloads |
| Serverless and cold starts | [3], [8], [19], [20] | Elastic overflow backend; cold start drives predictive pre-warming |
| SLO and tail latency | [9], [10] | Primary performance metric (p99 < 200ms) |
| GRU prediction | [5], [6], [15], [16] | Workload forecasting for proactive routing |
| ElaX elastic scaling | [7] | Algorithmic framework extended for hybrid routing |
| Kubernetes autoscaling | [11], [12] | Reactive baseline that prediction augments |

The identified research gap is the absence of an integrated system that combines: (a) GRU-based workload prediction with real-time SLO monitoring, (b) cross-platform traffic routing between Kubernetes and serverless, and (c) a priority-based decision framework that balances performance and cost. The methodology for addressing this gap is presented in Chapter 3.
