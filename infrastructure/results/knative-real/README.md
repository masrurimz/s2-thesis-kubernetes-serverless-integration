# Real Knative Experiments

**Status:** Pending - Requires architecture refactor (see issue `lhp`)

## Target Configuration

### Default Behavior
- **100% K8s / 0% Serverless** by default
- Serverless enabled ONLY when Algorithm 1 triggers SCALE_OUT
- HAProxy health checks disabled on serverless when weight=0

### Real Knative Integration
- Use Knative Service (ksvc) with native scale-to-zero
- Host header routing for Knative activation
- Variable cold start (100ms-10s depending on cluster state)

### Algorithm 1 SCALE_OUT Flow
```
1. DETECT:    p99 > 200ms for 30s (or GRU predicts spike)
2. ENABLE:    Set serverless backend to READY in HAProxy
3. PRE-WARM:  Send synthetic request to trigger Knative activation
4. RAMP:      Increase serverless weight (95/5 → 85/15 → 75/25...)
5. MONITOR:   Continue adjusting based on SLO status
6. SCALE-IN:  When healthy, ramp weights back toward 100/0
7. DISABLE:   Set serverless backend to MAINT (allows scale-to-zero)
```

## Prerequisites

1. Complete issue `lhp`: Refactor to real Knative
2. Deploy Knative Serving to cluster
3. Update HAProxy config for host-header routing
4. Modify Algorithm 1 controller for ENABLE/DISABLE flow

## Expected Differences from simulated-v1

| Metric | simulated-v1 | knative-real (expected) |
|--------|--------------|-------------------------|
| Cold start | 5s (fixed) | 100ms-10s (variable) |
| First request latency | Predictable | Higher variance |
| Scale-to-zero | Custom TTL | Native Knative |
| Reproducibility | High | Medium |
