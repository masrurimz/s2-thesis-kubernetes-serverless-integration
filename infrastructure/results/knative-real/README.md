# Real Knative Experiments

**Status:** Ready for Execution
**Date:** 2026-01-20
**Implementation Thread:** T-019bd968-f68b-7509-8ce1-e13af32e60f1

## Architecture Summary

This experiment setup uses **real Knative Serving** with native scale-to-zero, replacing the simulated serverless-activator from v1 experiments.

### Key Differences from simulated-v1

| Aspect | simulated-v1 | knative-real |
|--------|--------------|--------------|
| Cold start | Deterministic 5s | Variable 100ms-10s |
| Scale-to-zero | Custom idle checker (30s TTL) | Native Knative activator |
| Activation | K8s Deployment scale 0→1 | Knative Pod Autoscaler |
| Default weights | 80/20 (bug) | **100/0 (correct)** |
| Backend state | Always enabled | **DISABLED by default** |
| Reproducibility | High | Cluster-state dependent |

### Target Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     HAProxy (localhost:18082)                        │
│  Default: 100% K8s / 0% Serverless (DISABLED)                       │
│  SCALE_OUT: ENABLE backend → PRE-WARM → RAMP weight                 │
│  OPTIMIZE_COST: RAMP down → DISABLE backend (scale-to-zero)         │
└─────────────────┬─────────────────────────┬─────────────────────────┘
                  │                         │
                  ▼                         ▼
┌─────────────────────────────┐   ┌─────────────────────────────────┐
│   test-app-warm (K8s)       │   │   test-app (Knative ksvc)       │
│   - NodePort 30080          │   │   - Kourier gateway (port 80)   │
│   - Always running (warm)   │   │   - Native scale-to-zero        │
│   - CPU: 50m-200m limit     │   │   - Host: test-app.default.localhost
└─────────────────────────────┘   └─────────────────────────────────┘
```

## Infrastructure Setup

### Prerequisites

- K3d cluster running
- Knative Serving + Kourier installed
- HAProxy with knative-real config

### Verification Commands

```bash
# Check Knative is ready
kubectl get pods -n knative-serving
kubectl get pods -n kourier-system

# Check Knative service
kubectl get ksvc test-app

# Check HAProxy status
curl -s "http://localhost:18404/stats;csv" | grep servers

# Verify K8s backend
curl -s http://localhost:18082/health
# Should return: {"backend":"K8s-Warm","status":"ok"}
```

### HAProxy Backend Control

```bash
# Enable serverless backend (for SCALE_OUT)
echo "enable server servers/knative" | nc localhost 19999
echo "set server servers/knative weight 50" | nc localhost 19999
echo "set server servers/k3s-cluster weight 50" | nc localhost 19999

# Disable serverless backend (for OPTIMIZE_COST)
echo "disable server servers/knative" | nc localhost 19999
echo "set server servers/knative weight 0" | nc localhost 19999
echo "set server servers/k3s-cluster weight 100" | nc localhost 19999
```

## Algorithm 1 SCALE_OUT Flow

The updated Algorithm 1 controller follows this flow for real Knative:

```
1. DETECT:    p99 > 200ms for 30s (or GRU predicts spike)
2. ENABLE:    enable server servers/knative (via HAProxy socket)
3. PRE-WARM:  Send synthetic request with Host header to trigger activation
              curl -H "Host: test-app.default.localhost" http://192.168.156.2:80/health
4. RAMP:      Increase serverless weight in steps
              - 100/0 → 90/10 → 80/20 → 70/30...
5. MONITOR:   Continue adjusting based on SLO status
6. SCALE-IN:  When healthy, ramp weights back toward 100/0
7. DISABLE:   When weight=0, disable server (allows scale-to-zero)
```

## Cold Start Observations

Initial testing shows:
- **Cold start time: ~1-2 seconds** (vs 5s simulated)
- **Scale-to-zero timeout: ~60 seconds** (Knative default)
- **Pod ready time: varies by cluster state**

## Running Experiments

### S1: K8s Only (100/0)

```bash
# Set weights
echo "set server servers/k3s-cluster weight 100" | nc localhost 19999
echo "set server servers/knative weight 0" | nc localhost 19999
echo "disable server servers/knative" | nc localhost 19999

# Disable routing daemon
# Run load test
k6 run -e BASE_URL=http://localhost:18082 infrastructure/load-tests/spike.js \
  --out json=infrastructure/results/knative-real/s1-k8s-only/metrics.json
```

### S2: Serverless Only (0/100)

```bash
# Enable and warm up Knative
echo "enable server servers/knative" | nc localhost 19999
curl -s -H "Host: test-app.default.localhost" http://192.168.156.2:80/health

# Set weights
echo "set server servers/k3s-cluster weight 0" | nc localhost 19999
echo "set server servers/knative weight 100" | nc localhost 19999

# Disable routing daemon
# Run load test
k6 run -e BASE_URL=http://localhost:18082 infrastructure/load-tests/spike.js \
  --out json=infrastructure/results/knative-real/s2-serverless-only/metrics.json
```

### S3: Hybrid Reactive (Algorithm 1 only)

```bash
# Reset to default 100/0
echo "set server servers/k3s-cluster weight 100" | nc localhost 19999
echo "set server servers/knative weight 0" | nc localhost 19999
echo "disable server servers/knative" | nc localhost 19999

# Start routing daemon WITHOUT GRU prediction
cd controller && uv run python -m daemon.routing_daemon --mode reactive

# Run load test
k6 run -e BASE_URL=http://localhost:18082 infrastructure/load-tests/spike.js \
  --out json=infrastructure/results/knative-real/s3-hybrid-reactive/metrics.json
```

### S4: Hybrid Predictive (Algorithm 1 + GRU)

```bash
# Reset to default 100/0
echo "set server servers/k3s-cluster weight 100" | nc localhost 19999
echo "set server servers/knative weight 0" | nc localhost 19999
echo "disable server servers/knative" | nc localhost 19999

# Start GRU prediction server
cd controller && uv run python -m prediction_engine.server --port 8090

# Start routing daemon WITH GRU prediction
cd controller && uv run python -m daemon.routing_daemon --mode predictive

# Run load test
k6 run -e BASE_URL=http://localhost:18082 infrastructure/load-tests/spike.js \
  --out json=infrastructure/results/knative-real/s4-hybrid-predictive/metrics.json
```

## Expected Differences from simulated-v1

| Metric | simulated-v1 | knative-real (expected) |
|--------|--------------|-------------------------|
| Cold start | 5s (fixed) | 1-2s (variable, faster) |
| First request latency | Predictable | Higher variance |
| Scale-to-zero | 30s custom TTL | 60s Knative default |
| Reproducibility | High | Medium |
| Backend state | Always enabled | Disabled by default |

## Files

| Path | Description |
|------|-------------|
| `infrastructure/haproxy/haproxy-knative.cfg` | HAProxy config for real Knative |
| `infrastructure/haproxy/docker-compose-knative.yml` | Docker compose for Knative setup |
| `infrastructure/test-app/knative-service.yaml` | Knative Service manifest |
| `controller/intelligent_router/algorithm1_controller.py` | Updated Algorithm 1 with ENABLE/DISABLE flow |
| `controller/intelligent_router/weight_adjuster.py` | HAProxy weight adjuster (updated server names) |

## Configuration Changes

### Algorithm1Config (new fields)

```python
@dataclass
class Algorithm1Config:
    # ... existing fields ...
    # Real Knative integration settings
    default_k3s_weight: int = 100  # Default: 100% K8s
    default_knative_weight: int = 0  # Default: 0% serverless (disabled)
    knative_host: str = "test-app.default.localhost"
    knative_url: str = "http://192.168.156.2:80"
    prewarm_timeout_sec: int = 30
```

### HAProxy Server Names

```
servers/k3s-cluster   -> K8s backend (unchanged)
servers/knative       -> Real Knative (was: serverless-sim)
```

## Validity Statement

These experiments use **real Knative Serving** with native scale-to-zero, providing:

1. **Production-realistic cold starts:** Variable 1-2s (cluster-state dependent)
2. **Native serverless mechanics:** Knative Pod Autoscaler handles activation
3. **Correct default behavior:** 100% K8s / 0% serverless by default
4. **Dynamic backend control:** ENABLE/DISABLE via Algorithm 1

### Trade-offs

1. **Reproducibility:** Lower than simulation due to Knative timing variability
2. **Cold start variance:** Results may vary between runs
3. **Cluster dependency:** Performance depends on K3d/Knative cluster state
