# Sprint 1 Monitoring Guide

**Day 3 Implementation**: Complete Monitoring Stack ✅  
**Tools**: Lightweight Monitoring Scripts + Optional Prometheus  
**Resource Usage**: 0MB (script-based) or 1GB (Prometheus)

## Overview

Sprint 1 implements a dual monitoring approach:

1. **Lightweight Monitoring** (Primary): Real-time dashboard and health checking via scripts
2. **Prometheus Monitoring** (Optional): Full metrics collection with 1h retention

## Primary Monitoring Tools

### 1. Real-Time Monitoring Dashboard

**Command**: `./scripts/monitor-system.sh`

```bash
# Single snapshot
./monitor-system.sh

# Continuous monitoring (30-second updates)
./monitor-system.sh --watch
```

**Output Features**:
- Component health status (K3s, Knative, HAProxy, Stats)
- HAProxy backend analysis with request counts
- Traffic distribution calculation and validation
- Resource utilization tracking
- Live traffic flow testing (10 requests)

**Sample Output**:
```
📊 Sprint 1 System Monitoring Dashboard
========================================
Timestamp: Sun Jul 13 22:33:27 WIB 2025

🔍 Component Health Check:
----------------------------
K3s Backend: ✅ UP
Knative Serverless: ✅ UP
HAProxy Router: ✅ UP
HAProxy Stats: ✅ UP

🎯 Traffic Distribution:
------------------------
K3s Cluster: 20 requests (83%)
Serverless: 4 requests (16%)
Total: 24 requests
✅ Distribution: HEALTHY (within 80/20 ±10%)

🛑 Traffic Flow Test (10 requests):
----------------------------------
Results:
  K3s: 8/10 (80%)
  Serverless: 2/10 (20%)
  Errors: 0/10 (0%)
✅ Traffic Flow: HEALTHY
```

### 2. Comprehensive Health Check

**Command**: `./scripts/check-health.sh`

```bash
# Full system health validation
./check-health.sh

# Exit codes:
# 0 = All systems healthy
# 1 = Healthy with warnings  
# 2 = System issues detected
```

**Validation Features**:
- Component availability testing
- Traffic distribution within tolerance (±10%)
- Performance threshold checking (<200ms)
- Resource usage monitoring
- Prometheus metrics validation (if available)

## Monitoring Endpoints

### HAProxy Stats (Primary Data Source)

```bash
# Web interface
open http://localhost:8404/stats

# CSV data for parsing
curl -s "http://localhost:8404/stats?stats;csv"

# Key metrics extracted:
# - Backend status (UP/DOWN)
# - Request counts and distribution
# - Response times and health check status
# - Connection statistics
```

### System Component Endpoints

```bash
# K3s cluster backend
curl http://localhost:8080
curl http://localhost:8080/health

# Knative serverless backend  
curl -H "Host: serverless-sim.default.localhost" http://localhost:8081
curl -H "Host: serverless-sim.default.localhost" http://localhost:8081/health

# HAProxy hybrid endpoint
curl http://localhost:8082

# Prometheus metrics (if running)
curl http://localhost:9090/-/healthy
curl "http://localhost:9090/api/v1/query?query=up"
```

## Traffic Distribution Monitoring

### Real-Time Distribution Tracking

```bash
# Monitor traffic distribution
./monitor-system.sh | grep "Traffic Distribution"

# Continuous monitoring
watch -n 5 './scripts/monitor-system.sh | grep -A 4 "Traffic Distribution"'
```

### Expected Distribution Ranges

- **Target**: 80% K3s, 20% Knative
- **Healthy Range**: 70-90% K3s, 10-30% Knative
- **Warning Range**: 60-95% K3s, 5-40% Knative
- **Critical**: Outside warning range or any backend DOWN

### Manual Traffic Testing

```bash
# Test traffic distribution (20 requests)
./scripts/test-traffic.sh

# Custom traffic test
for i in {1..50}; do
  curl -s http://localhost:8082 | grep -o "K3s\|Knative" | sort | uniq -c
done
```

## Performance Monitoring

### Response Time Baselines (Days 1-3)

```bash
# Hybrid endpoint performance
time curl http://localhost:8082
# Expected: <50ms total time

# K3s backend direct
time curl http://localhost:8080
# Expected: <10ms total time

# Knative backend direct (warm)
time curl -H "Host: serverless-sim.default.localhost" http://localhost:8081
# Expected: <20ms (warm), <100ms (cold start)
```

### Performance Thresholds

#### Normal Operation ✅
- Hybrid endpoint: <50ms p95
- K3s direct: <10ms p95
- Knative warm: <20ms p95
- Error rate: 0%
- Both backends: UP

#### Warning Levels ⚠️
- Hybrid endpoint: 50-100ms p95
- Backend response: 10-50ms p95
- Traffic distribution: Outside 70-90% K3s range
- Memory usage: >200MB per container

#### Critical Levels ❌
- Any backend: DOWN status
- Response time: >100ms p95
- Error rate: >0%
- Memory usage: >250MB per container

## Resource Monitoring

### Container Resource Usage

```bash
# Real-time container stats
docker stats --no-stream

# Sprint 1 container filtering
docker stats --no-stream | grep -E "(sprint1|haproxy)"

# Expected usage:
# sprint1-haproxy: <256MB RAM, <0.25 CPU
# sprint1-prometheus: <1GB RAM, <0.25 CPU (if running)
```

### Kubernetes Resource Usage

```bash
# Node resource usage
kubectl top nodes

# Pod resource usage
kubectl top pods

# Knative-specific pods
kubectl top pods -l serving.knative.dev/service=serverless-sim

# Expected usage:
# k3s system: <2GB RAM, <1 CPU
# nginx-app: <128MB RAM, <0.1 CPU
# knative pods: <128MB RAM, <0.1 CPU (when scaled up)
```

### System Resource Summary

```bash
# Total system resource usage
docker system df
echo "Current allocation: ~2.6GB RAM, ~1.6 CPU cores"
echo "6GB system buffer: ~3.4GB available"
```

## Optional: Prometheus Monitoring

### Prometheus Setup (Resource Intensive)

```bash
# Deploy Prometheus stack
cd sprint-1/infrastructure/monitoring
docker-compose up -d

# Verify deployment
curl http://localhost:9090/-/healthy
open http://localhost:9090
```

### Key Prometheus Queries

```bash
# Service discovery status
curl "http://localhost:9090/api/v1/query?query=up"

# HAProxy backend status
curl "http://localhost:9090/api/v1/query?query=haproxy_backend_up"

# Traffic distribution percentage
curl "http://localhost:9090/api/v1/query?query=hybrid:traffic_distribution:k3s_percentage"

# Weighted average response time
curl "http://localhost:9090/api/v1/query?query=hybrid:response_time:weighted_average"

# Total request rate
curl "http://localhost:9090/api/v1/query?query=hybrid:request_rate:total"
```

### Prometheus Configuration Highlights

- **Retention**: 1 hour (resource constrained)
- **Scrape Interval**: 15 seconds
- **Memory Limit**: 512MB
- **Storage Limit**: 512MB
- **Alert Rules**: Backend down, high response time, traffic imbalance
- **Recording Rules**: Traffic percentages, weighted averages

## Alerting and Notifications

### Manual Alert Checking

```bash
# Check for warning conditions
./scripts/check-health.sh

# Monitor continuously for issues
./scripts/monitor-system.sh --watch

# Look for:
# - Any component marked as DOWN
# - Traffic distribution outside 70-90% range
# - Response times >100ms
# - Error rates >0%
```

### Alert Response Procedures

#### Backend Down Alert

```bash
# 1. Identify failed backend
./scripts/monitor-system.sh | grep "Component Health"

# 2. Test backend directly
curl http://localhost:8080  # K3s
curl -H "Host: serverless-sim.default.localhost" http://localhost:8081  # Knative

# 3. Restart if needed
kubectl rollout restart deployment/nginx-app  # K3s
kubectl delete ksvc serverless-sim && kubectl apply -f infrastructure/serverless/knative-service.yaml  # Knative

# 4. Verify recovery
./scripts/check-health.sh
```

#### Traffic Distribution Alert

```bash
# 1. Check current distribution
./scripts/monitor-system.sh | grep "Traffic Distribution"

# 2. Check backend health
curl http://localhost:8404/stats | grep -E "k3s-cluster|serverless-sim"

# 3. Manual weight adjustment if needed
./scripts/adjust-weights.sh 80 20

# 4. Verify correction
./scripts/test-traffic.sh
```

#### Performance Alert

```bash
# 1. Check response times
time curl http://localhost:8082
time curl http://localhost:8080
time curl -H "Host: serverless-sim.default.localhost" http://localhost:8081

# 2. Check system load
top
kubectl top nodes

# 3. Check HAProxy logs
docker logs sprint1-haproxy --tail 20

# 4. Consider traffic adjustment
./scripts/adjust-weights.sh 60 40  # Favor serverless if K3s overloaded
```

## Monitoring Best Practices

### Regular Monitoring Tasks

```bash
# Daily health check
./scripts/check-health.sh

# Weekly performance baseline
time curl http://localhost:8082  # Document response times

# Monitor resource trends
docker stats --no-stream | grep sprint1
kubectl top nodes
```

### Troubleshooting Workflow

1. **Start with comprehensive check**: `./scripts/check-health.sh`
2. **Use real-time monitoring**: `./scripts/monitor-system.sh`
3. **Check individual components** if issues detected
4. **Review logs** for detailed error information
5. **Apply fixes** and validate with monitoring tools

### Performance Optimization

```bash
# Monitor traffic patterns
./scripts/monitor-system.sh --watch

# Adjust weights based on performance
./scripts/adjust-weights.sh 70 30  # More serverless for high load
./scripts/adjust-weights.sh 90 10  # More K3s for cost optimization

# Validate optimization
./scripts/test-traffic.sh
time curl http://localhost:8082
```

## Integration with Days 4-5

### Load Testing Monitoring (Day 4)

```bash
# Monitor system during load tests
./scripts/monitor-system.sh --watch &

# Run load tests (to be implemented)
k6 run load-testing/steady-load.js
k6 run load-testing/spike-load.js

# Validate performance under load
./scripts/check-health.sh
```

### Stability Testing Monitoring (Day 5)

```bash
# 30-minute endurance monitoring
./scripts/monitor-system.sh --watch &
sleep 1800  # 30 minutes
./scripts/check-health.sh

# Document stability results
echo "30-minute stability test: $(date)" >> results/stability-monitoring.log
```

This monitoring guide provides comprehensive coverage of Sprint 1's monitoring capabilities, supporting both lightweight script-based monitoring and optional Prometheus integration for complete system visibility.
