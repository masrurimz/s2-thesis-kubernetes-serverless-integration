# Calibration Guide: Repeating and Adapting Capacity Measurements

This document explains how the capacity calibration works, how to re-run it, and how to adapt it for a new application or workload.

---

## What Calibration Produces

The calibration measures the **saturation point** of the test application — the RPS at which a single replica's p99 latency crosses the SLO threshold (200 ms). This value (`r_saturation_per_replica`) drives the controller's capacity model:

```
alpha = 1 / r_saturation_per_replica      # replicas per RPS
r_effective = r_saturation × target_cpu_util  # safe RPS per pod
k8s_capacity = min_replicas × r_effective  # total K8s capacity
R_target = ceil(alpha × load × buffer)     # Algorithm 2 replica target
```

### Key Parameters (CalibrationConfig)

| Parameter | Current Value | Source | Description |
|---|---|---|---|
| `fib_n` | 33 | App config | Fibonacci computation depth (determines CPU cost per request) |
| `r_saturation_per_replica` | 66.7 | **Measured** | RPS at which p99 crosses 200ms SLO |
| `target_cpu_util` | 0.5 | Design choice | Safety margin: use 50% of saturation |
| `lambda_compute_ms` | 24.0 | **Measured** | CPU compute time per fib(33) request |
| `io_wait_ms` | 50.0 | Design choice | Simulated I/O wait (SeBS methodology) |
| `min_k8s_replicas` | 3 | Design choice | Minimum warm pods |
| `max_k8s_replicas` | 10 | Cluster limit | Maximum pods |
| `pod_cpu_millicores` | 300 | K8s config | CPU allocation per pod |

**Single source of truth:** `libs/shared/shared/models/calibration.py` → `CALIBRATION` singleton.

---

## Current Calibration (fib33, July 2026)

### How It Was Measured

1. Deployed test-app with `/fib?n=33` endpoint, `GOMAXPROCS=1`, 300m CPU per pod
2. Ran k6 capacity envelope test (`t7-capacity-envelope.js`) against 3 pods
3. Ramped RPS from 50→500 in 15 stages (30 seconds each)
4. Found p99 crossing 200ms at ~200 RPS total (66.7 RPS/pod)
5. Fitted `r_saturation_per_replica = 66.7`

### Validation

- 3 pods × 66.7 = 200 RPS theoretical saturation
- With `target_cpu_util = 0.5`: effective capacity = 3 × 66.7 × 0.5 = **100 RPS**
- ClarkNet trace mean = 73 RPS (under capacity), peak = 164 RPS (above capacity → triggers routing)
- 85% of ClarkNet stages exceed single-pod capacity → scaling mechanisms exercised

---

## How to Re-Calibrate (Same Application)

If the application binary, CPU allocation, or infrastructure changes:

### Step 1: Deploy the application

```bash
HSA_OVERRIDE_GFX_VERSION=11.0.0 \
  uv run python -m infra.cli deploy-app
```

This builds the Go test-app container and deploys it to both K8s and Knative. The deploy verifies both endpoints respond with `compute_ms` and `io_wait_ms` fields.

### Step 2: Run the capacity envelope test

```bash
# Against K8s backend (3 pods, no autoscaling)
k6 run apps/experiment/experiment/load_tests/calibration/t7-capacity-envelope.js \
  -e ENDPOINT=http://localhost:18082/fib?n=33

# Alternative: use the experiment runner
uv run python -m experiment.calibration \
  --scenarios baseline \
  --rps 50,100,150,200,250,300 \
  --duration 30
```

### Step 3: Find r_saturation

Look for the RPS stage where p99 first crosses 200ms:

```
Stage 5 (150 RPS): p99 = 180ms  ← under SLO
Stage 6 (200 RPS): p99 = 240ms  ← OVER SLO ← r_saturation = 200/3 = 66.7
```

### Step 4: Update CalibrationConfig

Edit `libs/shared/shared/models/calibration.py`:

```python
class CalibrationConfig(BaseModel):
    fib_n: int = 33                          # your endpoint's compute depth
    r_saturation_per_replica: float = 66.7   # ← update this from Step 3
    target_cpu_util: float = 0.5             # adjust if you want more/less headroom
    lambda_compute_ms: float = 24.0          # from deploy-app verification output
    io_wait_ms: float = 50.0                # match WORK_DURATION_MS in deployment YAML
```

### Step 5: Validate

Run a smoke experiment with the new calibration:

```bash
HSA_OVERRIDE_GFX_VERSION=11.0.0 \
  uv run python scripts/run_phase_b_experiments.py --phase experiments --runs 1 --duration 300
```

Check that:
- S1 (K8s-only) handles mean load without saturating
- S3/S4 (hybrid) trigger serverless routing when load exceeds `k8s_capacity_rps`
- No immediate cold-start cascades at the routing boundary

---

## How to Calibrate for a New Application

When integrating the controller with a different workload (real web app, microservice, etc.):

### What changes

| Component | Reusable? | Action |
|---|---|---|
| Algorithm 1 (routing) | ✅ | No change — reads `r_saturation` from config |
| Algorithm 2 (scaling) | ✅ | No change — reads `alpha` from config |
| GRU model | ⚠️ Retrain | Generate synthetic data matching new traffic shape |
| **r_saturation_per_replica** | ❌ Recalibrate | Must measure against new endpoint |
| **lambda_compute_ms** | ❌ Remasure | Different compute cost per request |
| **fib_n / endpoint** | ❌ Replace | Point to new application's endpoint |
| **io_wait_ms** | ❌ Remasure | Measure actual I/O wait (DB, cache, external API) |

### Step-by-step

1. **Deploy your application** to both K8s and Knative clusters
2. **Choose your SLO threshold** (default 200ms p99 — adjust in `CalibrationConfig.slo_threshold_ms`)
3. **Measure compute_ms and io_wait_ms** by hitting the endpoint directly:
   ```bash
   curl http://localhost:18082/your-endpoint | jq '.compute_ms, .io_wait_ms'
   ```
   (Your endpoint must return these fields, or use the `/debug` variant)
4. **Run the capacity envelope** with k6 against your endpoint at 3 replicas
5. **Find r_saturation** (p99 crossing point) from the k6 results
6. **Update CalibrationConfig** with all measured values
7. **Retrain GRU** on traffic patterns representative of your workload
8. **Run validation experiments** (S1 baseline, S4 hybrid)

### Expected time

- Same application re-calibration: ~30 minutes
- New application calibration: ~2-4 hours (deploy + calibrate + retrain GRU + validate)

---

## Limitations

1. **Linear model assumption**: R = αx + β assumes linear scaling. Real applications may have non-linear saturation curves (memory-bound, connection-pool limits). The linear fit is adequate near the SLO boundary but degrades at extreme load.

2. **Offline calibration only**: α and β are measured once and stored. Online recalibration (updating during runtime) is not implemented. Recent work by @bacc2026 (BACC) and @aapa2025 (AAPA) explores online uncertainty calibration and workload-archetype adaptation — these are future directions.

3. **Single-node testbed**: The calibration was measured on a single-node k3d cluster. Multi-node deployments may have different saturation characteristics due to network overhead and pod distribution.

4. **Application-specific**: `r_saturation = 66.7` is specific to fib(33) with GOMAXPROCS=1 and 300m CPU. Different applications, CPU allocations, or workloads require full recalibration.

5. **I/O wait simulation**: `io_wait_ms = 50ms` simulates a database query per request (SeBS methodology @sebs2020). Real applications have variable I/O patterns. The cost model assumes uniform I/O per request.

---

## File Reference

| File | Purpose |
|---|---|
| `libs/shared/shared/models/calibration.py` | CalibrationConfig — single source of truth |
| `apps/experiment/experiment/calibration.py` | Calibration runner (curl-based sweep) |
| `apps/experiment/experiment/load_tests/calibration/t7-capacity-envelope.js` | k6 capacity test (15-stage ramp) |
| `apps/experiment/experiment/load_tests/calibration/t7-fib-slo-finder.js` | Fine-grained SLO threshold finder |
| `apps/routing/routing/algorithm/algorithm1_v3.py` | V3 controller (consumes `r_saturation`) |
| `apps/routing/routing/algorithm/scaling/cluster_controller.py` | Algorithm 2 (consumes `alpha`, `beta`) |
| `libs/infra/infra/cli.py` | `deploy-app` command (deploys + verifies) |
| `results/experiments/validation/2026-02-13_t7-capacity-envelope/` | Original capacity measurement data |
