# Hybrid Kubernetes–Serverless Integration Research

## Overview

This repository evaluates a hybrid Kubernetes and serverless architecture for tail-latency control. The final design uses GRU workload prediction to anticipate **Kubernetes replica scaling** (Algorithm 2), while Algorithm 1 performs capacity-driven traffic routing from **observed load** and observed ready capacity. Observed-load trend extrapolation is allowed to make proactive decisions only when GRU confidence gates it (V3, post Bug-13); the forecast does not directly set HAProxy weights.

## Research objectives

- Evaluate ElaX-derived scaling and routing in a Kubernetes + Knative testbed.
- Use a direct multi-horizon GRU forecast of **9 × 15-second samples = 135 seconds**.
- Train the GRU on synthetic diurnal, burst, and ramp series; use ClarkNet and Calgary as validation corpora, with ClarkNet also used for trace replay.
- Maintain the primary SLO of **p99 < 200 ms** while measuring tail latency, SLO violations, capacity, request distribution, and directional proxy cost.
- Compare four controlled scenarios: S1 K8s + HPA, S2 serverless-only, S3 hybrid-reactive, and S4 hybrid-predictive.

## Documentation structure

### Getting started

- [Overview](getting-started/00-overview.md)
- [Quick start](getting-started/02-quick-start.md)
- [Prerequisites](getting-started/01-prerequisites.md)
- [Architecture](getting-started/03-understanding-architecture.md)
- [Deploying services](getting-started/03-deploying-services.md)
- [Teardown](getting-started/04-teardown.md)

### Thesis implementation

- [Experiment plan](thesis-implementation/01-experiment-plan.md)
- [Methodology and implementation](thesis-implementation/02-methodology-implementation.md)
- [Running experiments](thesis-implementation/03-running-experiments.md)

### Specifications and operations

- [Algorithm 1 specification](specs/algorithm-1-spec.md)
- [SLO definition](specs/slo-definition.md)
- [Calibration guide](CALIBRATION_GUIDE.md)
- [Current experiment runbook](experiments/RUNNING_EXPERIMENTS.md)
- [Deployment guide](deployment/VPS_DEPLOYMENT.md)

### Reference and historical material

- [Experiment results template](reference/experiment-results-template.md)
- [References](references/REFERENCES.md)
- [Archived methodology](archived/experimental-methodology.md) (historical; not a current protocol)
- [Initial hybrid plan](archived/initial-hybrid-plan.md) (historical; not a current protocol)

## Final evaluation snapshot

- **H2 (definitive paired n=5):** S3 mean p99 **188.5 ms** versus S4 **126.0 ms**, p = **0.0304**, Cohen's d = **−1.26**; S4 won all five pairs. The proxy monthly cost is **USD 163 for both** scenarios.
- **H1 (directional diagnostic n=1):** S4 p99 **118.2 ms** versus S1 **2,421.3 ms**. This is directional mechanism evidence, not an inferential result.
- The result interpretation is SLO-first: p99 < 200 ms is the target; cost is a directional proxy, not measured cloud billing.

## Current control flow

```text
synthetic training -> GRU (9-step / 135 s forecast)
                              |
                              v
                   Algorithm 2 replica scaling
                              |
observed load + ready capacity -> Algorithm 1 V3 routing -> HAProxy
                              |
                       Kubernetes / Knative backends
```

The calibrated workload is the deterministic `/fib?n=33` endpoint. The shared calibration model uses `r_saturation_per_replica = 33.3`, `min_k8s_replicas = 3`, and `max_k8s_replicas = 6`; see [CALIBRATION_GUIDE.md](CALIBRATION_GUIDE.md).

## Current pipeline quick start

```bash
uv run thesis-experiment preflight
uv run thesis-experiment run --phase full --runs 5 --duration 300
uv run thesis-experiment paired-run --pairs 5
uv run thesis-experiment evidence audit
uv run thesis-experiment evidence reconcile --apply
uv run thesis-experiment evidence catalog refresh
uv run thesis-experiment evidence journal
```

For infrastructure lifecycle, use `uv run thesis infra apply-resources`, `uv run thesis infra deploy-app`, and `uv run thesis infra health`. The prediction service listens on port 8090; the routing daemon listens on port 9104; Prometheus is on 9090, HAProxy HTTP on 18082, and HAProxy stats on 18404.
