## 3.1 Research Flow (Alur Penelitian)

The research follows a six-phase methodology, progressing from theoretical foundations through system design, implementation, and experimental evaluation:

1. **Literature Study** — Survey of cloud computing architectures, workload prediction methods, and elastic scaling algorithms to establish the theoretical foundation and identify the research gap.
2. **Data Collection** — Generation of synthetic workload patterns for GRU model training, supplemented by real HTTP trace datasets (ClarkNet and Calgary) for baseline comparison and validation.
3. **Method Design** — Architecture design of the hybrid Kubernetes-serverless system, specification of routing and scaling algorithms, and definition of the SLO-based decision framework.
4. **Implementation** — Development of the GRU prediction server, routing controller (Algorithm 1), integrated cluster controller (Algorithm 2) with real Kubernetes replica scaling, monitoring infrastructure, and traffic routing layer.
5. **Evaluation** — Systematic experimental evaluation across four deployment scenarios with mechanism validation (Phase A1), trace-driven replicated comparison using ClarkNet replay (Phase B), dynamic burst validation (Phase C), and statistical analysis.
6. **Report Writing** — Documentation of findings with truth-aligned claims that distinguish validated mechanisms from unestablished superiority claims.

Each phase produces artifacts that feed into subsequent phases: the literature study informs the system design, the collected data trains the prediction model, the implemented system undergoes experimental evaluation, and the evaluation results inform the thesis conclusions.
