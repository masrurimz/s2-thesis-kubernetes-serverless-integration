# Calibration Guide (Final Protocol)

Calibration measures the single-replica request rate at which the deterministic workload approaches the p99 < 200 ms SLO. The result feeds Algorithm 2's capacity model and is not a generic benchmark constant.

## Final values

| Parameter | Final value | Meaning |
|---|---:|---|
| `fib_n` / endpoint | 33 / `/fib?n=33` | Deterministic CPU-bound workload |
| `r_saturation_per_replica` | **33.3 RPS** | Calibrated saturation rate per replica |
| `target_cpu_util` | 0.5 | Capacity safety margin |
| `lambda_compute_ms` | 24.0 ms | Measured CPU component used by the cost model |
| `io_wait_ms` | 50.0 ms | Simulated I/O component used by the cost model |
| `min_k8s_replicas` | 3 | Warm baseline |
| `max_k8s_replicas` | **6** | Final static K8s envelope (default; the definitive paired H2 bundle overrode this to **10** via `results/calibration/2026-08-06_definitive-repro.json` to exercise node-level autoscaling) |
| `pod_cpu_millicores` | 300m | Per-pod CPU request/limit contract |

The shared model in `libs/shared/shared/models/calibration.py` is the source of truth for the calibration fields. `apps/experiment/experiment/calibration.py` runs the sweep and parses k6 output. If a deployed endpoint or workload tuple changes, rerun calibration and update the injected `CalibrationConfig`; do not silently reuse these values.

## Where each value comes from

A value is usable in a claim only when the report says how it was obtained. Three origins appear below: measured in this repository, chosen as a design decision, and taken from a published measurement. A design decision needs the reason, and a published measurement needs the paper.

| Value | How it was derived | Origin |
|---|---:|---|
| `fib_n` = 33, endpoint `/fib?n=33` | CPU-bound request with a stable cost, so the saturation rate is a property of the deployment and not of the payload | Design choice |
| `r_saturation_per_replica` = **33.3 RPS** | Measured: the request rate at which the p99 approaches the 200 ms service level objective (SLO) with one replica at 300m CPU. `uv run thesis-experiment calibrate` runs the sweep | Measured here |
| `target_cpu_util` = 0.5 | Usable capacity is half the measured saturation rate, which leaves headroom for the ramp | Design choice |
| `alpha` = 1 / (`r_saturation_per_replica` x `target_cpu_util`) | Derived, so the scaling model and the routing model use one number | Derived from a measurement |
| `min_k8s_replicas` = 3 | Warm baseline that keeps the pod tier serving before any scale-up | Design choice |
| `max_k8s_replicas` = 6 default, **10** for the definitive H2 pairs | The default envelope. The definitive paired bundle replaced the cap with 10 through `results/calibration/2026-08-06_definitive-repro.json` | Design choice, declared per profile |
| `pod_cpu_millicores` = 300m | Per-pod request and limit contract, applied to the deployment before each run | Deployed configuration |
| `slo_threshold_ms` = 200 | Tail-latency target of the study | Design target |
| `sample_interval_sec` = 15 | Interval of the replayed trace and of the control loop | Data choice |
| `prediction_horizon` = 9 steps (135 s) | Sized to cover the maximum simulated provisioning delay (120 s) plus one control interval. ADAPT requires the forecast look-ahead to cover the measured provisioning delay and uses the same EWMA estimator for it | Cited: ADAPT, `@adapt2026` |
| `provision_delay_min_sec` / `max_sec` = 45 / 120 s | Simulated node boot in `K3dAutoscaler`. The range brackets measured cold-start times of common cloud virtual machines: 55.9 s (AWS Linux), 124.1 s (GCP Linux), with warm starts between 22 s and 34 s. The Kubernetes Cluster Autoscaler documentation gives 3 to 4 minutes for node provisioning on GCE, which is above this range, so the testbed models a fast boot. Since 2026-09-12 the delay is matched within a pair; see below | Published measurements plus a testbed decision |
| `provisioning_delay_default_sec` = 60, `_ewma_alpha` = 0.3, `_safety_sec` = 15 | The daemon's online estimate of scale-up latency. ADAPT uses the same update rule with alpha 0.3. `ROUTING_PROVISIONING_DELAY_SEC` replaces the estimate with the declared pair delay | Cited: ADAPT, with a declared override |
| `ROUTING_PREDICTIVE_SHRINK` = 1.0 | Scales the forecast before sizing. A blend of a proactive and a reactive signal is standard: HyPA composes them as `max(reactive, proactive)`, OptScaler gives foreseeable patterns to the proactive side, and AutoScale reports that sizing just above need with conservative scale-down beats prediction-only policies. No source recommends forecasting low, so this factor is a margin control and not a claim | Cited for the blend, no source for a value below 1 |
| `proactive_hold_sec` = 90, `proactive_trend_threshold` = 3.0, `proactive_approach_ratio` = 0.8 | Controller tuning against the 135 s horizon | Design choice |
| Node consolidation at 50 % of allocatable, cooldown 120 s, dwell 90 s | The CPU threshold matches the Cluster Autoscaler scale-down threshold default. The two time values are testbed parameters | One cited default, two testbed decisions |

### Two rules that follow

**A profile declares what it runs.** The default cap is 6 and the definitive H2 batch ran at 10. A run at the default would use a different system under the same scenario name, and nothing in the bundle recorded the difference. Every profile now names its calibration file, and `thesis experiment preflight` refuses a run whose declared capacity disagrees with the calibration it resolves.

**The provisioning delay is matched within a pair.** One delay is drawn per pair and applied to both arms, so both arms of a pair face the same boot time. Values still differ between pairs. The July batch drew a delay for each run, so a paired difference from that batch includes the difference in boot time. Matching removes that term.

### When a value has no source

Write the origin as a testbed decision. Do not attach a citation that does not make the claim. The 50 % consolidation threshold is the Cluster Autoscaler default, not a finding from the routing literature, and an earlier draft of the thesis cited it to the wrong paper.

## Capacity model

```text
r_effective = r_saturation_per_replica × target_cpu_util
alpha = 1 / r_effective
R_target = clamp(ceil(alpha × observed_or_forecast_load × buffer + beta), 3, 6)
```

The GRU upper forecast is used by Algorithm 2 for the forecast-informed target. Algorithm 1 routes on observed load, ready capacity, HAProxy rtime p99, and confidence-gated observed-load trend extrapolation.

## Infrastructure prerequisite

Apply node CPU limits before calibration or evaluation. This keeps the Docker/k3d node envelope aligned with the measured workload:

```bash
uv run thesis infra apply-resources
uv run thesis infra deploy-app
uv run thesis infra health
```

The endpoint should respond through HAProxy at `http://localhost:18082/fib?n=33`. Prometheus is on `:9090`, and HAProxy stats are on `:18404`.

## k6 calibration flow

The k6 script must retain percentile fields in its summary. In particular, use `summaryTrendStats` with `p(95)` and `p(99)` (alongside avg/min/med/max) so the measured p99 can be compared with the 200 ms SLO:

```javascript
summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)']
```

Run the governed calibration command:

```bash
uv run thesis-experiment calibrate
```

The command sweeps configured scenarios and RPS levels, runs the k6 constant-arrival-rate workload, reads p50/p95/p99/error-rate fields, and writes the calibration analysis under `results/calibration/`. A capacity stage is acceptable only when the endpoint is healthy and the p99/error thresholds are classified correctly.

## Cost-model fields

The calibration tuple also supplies the serverless proxy cost model:

- `lambda_compute_ms` is the measured CPU compute time for the configured Fibonacci request.
- `io_wait_ms` is the simulated I/O wait that must match the deployment configuration.

These values estimate directional proxy cost; they are not provider billing measurements.

## When to recalibrate

Recalibrate after changing `/fib?n=33`, `GOMAXPROCS`, pod CPU limits, node CPU limits, the SLO threshold, or the number of warm replicas. Record the resulting configuration with the experiment bundle and run the evidence audit/reconciliation workflow before using it in a claim.
