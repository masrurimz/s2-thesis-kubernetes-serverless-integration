# Infrastructure Validation Tests (T0–T4)

**Purpose:** Pre-experiment validation to confirm testbed mechanisms work correctly and inform scenario design decisions.

## Environment

- **Cluster:** k3d v5.x, k3s v1.28.5+k3s1
- **Nodes:** 2 (1 server + 1 agent), 16 CPU / 30 GB RAM each
- **Tools:** k6 v1.6.0, Knative Serving with Kourier, HAProxy
- **Workload target:** `test-app-warm` — 2 replicas, 25m CPU request, 50m CPU limit

## Test Results

### T0: Cluster Health — PASS

- 2 nodes Ready, metrics-server operational.
- `kubectl top` returns data (agent 59m CPU, server 88m CPU).
- Prometheus 14/17 targets UP.
  - HAProxy exporter not deployed (expected).
  - Knative `svc-discovery` DOWN due to scale-to-zero (expected).
- HAProxy → K8s: HTTP 200, 2 ms.
- HAProxy → Knative: HTTP 200 via `sslip.io` host, 1.68 s cold start.

### T1: k6 Load Generation — PASS

- **Basic test:** 5 VUs, 10 s → 183 RPS, 0 % errors, p95 = 100 ms.
- **ramping-arrival-rate:** 5 → 50 → 10 RPS over 40 s → 1 262 requests, 31.6 avg RPS, 0 % errors, p95 = 53 ms.

### T2: HPA Scales Pods on k3d — PASS (CRITICAL)

- Created HPA: cpu 30 %, min 2, max 10.
- Drove 100 RPS `/fib?n=25` for 90 s.
- Scale-up sequence:
  - 2 → 4 at t = 45 s
  - 4 → 8 at t = 60 s
  - 8 → 10 at t = 75 s — all pods Running.
- Scale-down after load stopped: 10 → 2 in ~7.5 min (5-min stabilization + scale event).

**Conclusion:** HPA works correctly on k3d. S1 can use native HPA as autoscaling baseline.

### T3: kubectl scale + HPA Coexistence — PASS (CRITICAL)

- **Without HPA:** `kubectl scale` works instantly (1 → 5, 5 → 1).
- **With HPA active:** `kubectl scale` to 5 accepted initially (`ScaleDownStabilized` 5 min), then HPA reverted replicas to 2 (based on 4 % CPU).

**Conclusion:** HPA **fights** `kubectl scale`. They are mutually exclusive for replica control.

**Architectural Decision:** S3/S4 must delete HPA; Algorithm 2 owns replicas via `kubectl scale`.

### T4: Knative KPA Autoscaling — PASS

- Cold start (0 → 1): 1.19 s.
- `/health` too lightweight for KPA (concurrency target = 100, actual concurrency ~0.4 at 200 RPS).
- `/fib?n=30` triggers scaling: 1 → 3 (15 s), 3 → 5 (30 s), 5 → 7 (45 s).
- Scale-to-zero: ~60 s after load cessation.

**Conclusion:** KPA works. S2 viable as Knative-only baseline. Need CPU-heavy workload to trigger KPA scaling.

## Design Decisions from Validation

1. **S1** uses native HPA (cpu-based) — validated by T2.
2. **S2** uses Knative KPA (concurrency-based) — validated by T4.
3. **S3/S4** delete HPA; Algorithm 2 uses `kubectl scale` exclusively — mandated by T3.
4. Experiment workload must include CPU-heavy endpoints (not just `/health`) to exercise both HPA and KPA scaling.

## Commands Used

```bash
# T0 — Cluster Health
kubectl get nodes -o wide
kubectl top nodes
curl http://localhost:18082/health
curl -H "Host: test-app.default.127.0.0.1.sslip.io" http://localhost:8081/health

# T2 — HPA Scaling
kubectl autoscale deployment test-app-warm --cpu-percent=30 --min=2 --max=10
k6 run t2_hpa_load.js  # 100 RPS /fib?n=25 for 90s

# T3 — kubectl scale + HPA Coexistence
kubectl scale deploy test-app-warm --replicas=5  # with HPA active

# T4 — Knative KPA
k6 run t4_knative_fib.js  # 10→200 RPS /fib?n=30
```
