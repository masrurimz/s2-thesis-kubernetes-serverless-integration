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
