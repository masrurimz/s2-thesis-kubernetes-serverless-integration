# Methodology and Implementation (Final State)

## 1. System under study

The implementation is a two-layer controller for a Kubernetes + Knative testbed:

1. **Algorithm 2 (scaling):** converts observed load and the confidence-gated GRU upper forecast into a Kubernetes replica target.
2. **Algorithm 1 V3 (routing):** shifts HAProxy weights using observed load, observed ready capacity, HAProxy rtime-derived p99, and observed-load trend extrapolation. The raw GRU forecast never directly sets routing weights (post Bug-13).

The control loop runs every 15 seconds. The primary SLO is p99 < 200 ms. Routing changes use graduated steps, cooldown, hysteresis, and backend-health checks.

## 2. Workload and datasets

The experiment service exposes deterministic CPU work through `/fib?n=33`. The request path is identical for Kubernetes and Knative so that routing and scaling, rather than application behavior, are the treatment variables.

The data roles are intentionally separate:

- **Synthetic training data:** generated diurnal, burst, and ramp RPS series; split into training/validation/test partitions for GRU development.
- **ClarkNet and Calgary:** validation corpora for checking transfer to trace-shaped traffic.
- **ClarkNet:** replayed as the variable evaluation workload for the definitive paired comparison.

The predictor is a direct multi-horizon GRU with a 30-sample history at 15-second resolution and **9 output steps (135 seconds)**. Confidence gating controls whether a forecast can support a proactive capacity/trend decision.

## 3. Capacity model

The calibration model uses:

```text
r_saturation_per_replica = 33.3 RPS
r_effective = r_saturation_per_replica × target_cpu_util
alpha = 1 / r_effective
R_target = clamp(ceil(alpha × load × buffer + beta), 3, 6)
```

The final replica envelope is `min_k8s_replicas = 3` to `max_k8s_replicas = 6`. Node CPU limits are applied through the thesis infrastructure lifecycle before a capacity or evaluation run.

## 4. Prediction and routing implementation

```text
recent observed RPS -> GRU -> upper forecast + confidence
                                  |
                                  v
                         Algorithm 2 replica target
                                  |
observed RPS + ready replicas + rtime p99 -> Algorithm 1 V3
                                  |
                         HAProxy K8s/Knative weights
```

Algorithm 1 checks decisions in this order:

```text
SCALE_OUT > PREDICTIVE > OPTIMIZE_COST > MAINTAIN
```

`PREDICTIVE` means that observed-load trend extrapolation approaches the capacity boundary and the confidence gate is open. It does not mean that the GRU's predicted value is copied into a routing weight. This separation is required because the pre-Bug-13 forecast-to-routing path under-routed ramps and overused serverless capacity.

## 5. Measurement

The daemon records observed load, ready replicas, replica targets, decision types, weights, prediction delivery/confidence, and HAProxy latency. The SLO monitor derives p99 from HAProxy `rtime`. k6 reports p50, p95, p99, throughput, failures, and request counts using `summaryTrendStats` that includes `p(95)` and `p(99)`.

For the definitive H2 protocol, five counterbalanced pairs run S3 and S4 on ClarkNet under identical duration and calibration. The primary comparison is paired p99. The final result is S3 188.5 ms versus S4 126.0 ms, p=0.0304, d=-1.26, with both proxy costs USD 163. H1 remains a directional n=1 diagnostic (S4 118.2 ms versus S1 2,421.3 ms).

## 6. Services and infrastructure

```bash
uv run thesis infra apply-resources
uv run thesis infra deploy-app
uv run thesis infra health
uv run thesis-prediction-server --port 8090
uv run thesis-routing-daemon --port 9104
```

The standard endpoints are Prometheus `:9090`, HAProxy HTTP `:18082`, and HAProxy stats `:18404`. The experiment CLI owns reset, warmup, measurement, cooldown, collection, and validity gates.

## 7. Reproducibility and evidence governance

```bash
uv run thesis-experiment preflight
uv run thesis-experiment run --phase full --runs 5 --duration 300
uv run thesis-experiment paired-run --pairs 5
uv run thesis-experiment evidence audit
uv run thesis-experiment evidence reconcile --apply
uv run thesis-experiment evidence catalog refresh
uv run thesis-experiment evidence journal
```

Raw and derived artifacts remain under `results/`; this layer documents the protocol and does not replace the evidence registry. Interpret H1 as directional, H2 as the definitive paired result, and proxy cost as directional rather than measured billing.
