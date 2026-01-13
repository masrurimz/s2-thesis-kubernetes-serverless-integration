# Monitoring Queries and Dashboard Reference

**Sprint**: 1 - Basic Hybrid Foundation  
**Component**: Monitoring and Observability  
**Last Updated**: July 2025

## Overview

This document provides essential monitoring queries and dashboard configurations for the Sprint 1 hybrid k3s-serverless system. Both Prometheus-based queries and script-based monitoring commands are covered to support different resource environments.

## Quick Health Check Commands

### System Status

```bash
# Complete system health check
./scripts/check-health.sh

# Real-time system monitoring
./scripts/monitor-system.sh

# Continuous monitoring (press Ctrl+C to stop)
./scripts/monitor-system.sh --watch
```

### Individual Component Checks

```bash
# K3s cluster status
curl -s http://localhost:8080 && echo "✅ K3s OK" || echo "❌ K3s DOWN"

# Knative serverless status
curl -s -H "Host: serverless-sim.default.localhost" http://localhost:8081 && echo "✅ Knative OK" || echo "❌ Knative DOWN"

# HAProxy router status
curl -s http://localhost:8082 && echo "✅ HAProxy OK" || echo "❌ HAProxy DOWN"

# HAProxy stats
curl -s http://localhost:8404/stats | head -10
```

## Prometheus Queries (If Monitoring Stack Deployed)

### System Health Queries

#### Component Availability

```promql
# All components up/down status
up

# Specific component status
up{job="haproxy"}
up{job="k3s-cluster"}
up{job="knative-serving"}
```

#### HTTP Request Metrics

```promql
# Total HTTP requests by backend
rate(http_requests_total[5m])

# Request rate by status code
rate(http_requests_total[5m]) by (status_code)

# Error rate percentage
rate(http_requests_total{status_code!~"2.."}[5m]) / rate(http_requests_total[5m]) * 100
```

### Performance Queries

#### Response Time Analysis

```promql
# Average response time
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# 95th percentile response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# 99th percentile response time
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```

#### Traffic Distribution

```promql
# Requests per backend (from HAProxy stats)
haproxy_server_http_responses_total

# Traffic distribution percentage
rate(haproxy_server_http_responses_total[5m]) by (server) /
ignoring(server) group_left sum(rate(haproxy_server_http_responses_total[5m]))
```

### Resource Utilization

#### Memory Usage

```promql
# Container memory usage
container_memory_usage_bytes{container!="POD",container!=""}

# Memory usage percentage
container_memory_usage_bytes / container_spec_memory_limit_bytes * 100

# System memory pressure
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
```

#### CPU Usage

```promql
# Container CPU usage rate
rate(container_cpu_usage_seconds_total{container!="POD",container!=""}[5m])

# CPU usage percentage
rate(container_cpu_usage_seconds_total[5m]) / container_spec_cpu_quota * 100

# System CPU utilization
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

## HAProxy Stats Queries

### CSV Stats Access

```bash
# Get HAProxy stats in CSV format
curl -s "http://localhost:8404/stats;csv"

# Parse backend server stats
curl -s "http://localhost:8404/stats;csv" | grep -E "(k3s|knative)" | cut -d, -f1,2,8,9,10
```

### Traffic Distribution Analysis

```bash
# Current traffic distribution
./scripts/check-health.sh | grep -A2 "Traffic Distribution"

# Historical distribution (if Prometheus available)
curl -s "http://localhost:9090/api/v1/query?query=haproxy_server_http_responses_total" | jq '.data.result'
```

## Alert Conditions

### Critical Alerts

```promql
# System down (any component)
up == 0

# High error rate (>5%)
rate(http_requests_total{status_code!~"2.."}[5m]) / rate(http_requests_total[5m]) > 0.05

# High response time (>500ms average)
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m]) > 0.5
```

### Warning Alerts

```promql
# Elevated error rate (>2%)
rate(http_requests_total{status_code!~"2.."}[5m]) / rate(http_requests_total[5m]) > 0.02

# High memory usage (>80%)
container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.8

# Traffic imbalance (>10% deviation from expected 80/20)
abs(rate(haproxy_server_http_responses_total{server="k3s"}[5m]) /
    sum(rate(haproxy_server_http_responses_total[5m])) - 0.8) > 0.1
```

## Dashboard Configurations

### Grafana Dashboard JSON (Basic)

```json
{
	"dashboard": {
		"id": null,
		"title": "Sprint 1 Hybrid System",
		"tags": ["kubernetes", "serverless", "haproxy"],
		"timezone": "browser",
		"panels": [
			{
				"title": "Component Status",
				"type": "stat",
				"targets": [
					{
						"expr": "up",
						"legendFormat": "{{job}}"
					}
				]
			},
			{
				"title": "Request Rate",
				"type": "graph",
				"targets": [
					{
						"expr": "rate(http_requests_total[5m])",
						"legendFormat": "{{method}} {{status_code}}"
					}
				]
			},
			{
				"title": "Response Time",
				"type": "graph",
				"targets": [
					{
						"expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
						"legendFormat": "95th percentile"
					}
				]
			}
		]
	}
}
```

## Script-Based Monitoring Commands

### Resource Monitoring

```bash
# Docker container resource usage
docker stats --no-stream

# Kubernetes resource usage
kubectl top nodes
kubectl top pods --all-namespaces

# System resource usage
free -h
df -h
```

### Log Analysis

```bash
# HAProxy logs
docker logs haproxy-haproxy-1 --tail 50

# K3s cluster logs
kubectl logs -n kube-system -l k3s-app=metrics-server --tail 50

# Knative logs
kubectl logs -n knative-serving -l app=controller --tail 50
```

### Performance Testing Integration

```bash
# Run load test with monitoring
./load-testing/run-load-tests.sh --monitor

# Monitor during load test
./scripts/monitor-system.sh --watch &
./load-testing/run-load-tests.sh --quick
pkill -f monitor-system
```

## Troubleshooting Queries

### Common Issues

```bash
# Check port conflicts
lsof -i :8080,:8081,:8082,:8404,:9090

# Check Docker container status
docker ps -a | grep -E "(haproxy|prometheus)"

# Check Kubernetes pod status
kubectl get pods --all-namespaces | grep -v Running

# Check network connectivity
curl -v http://localhost:8082
```

### Performance Issues

```bash
# Check for resource exhaustion
./scripts/check-health.sh | grep -A5 "Resource Usage"

# Check for memory leaks
docker stats --no-stream | grep -E "(haproxy|prometheus)"

# Check for CPU throttling
kubectl top pods --all-namespaces --sort-by=cpu
```

## Historical Data Analysis

### Retention Queries (Short-term)

```promql
# Last hour performance
rate(http_requests_total[1h])

# Last day error trends
rate(http_requests_total{status_code!~"2.."}[1d])

# Peak traffic periods
max_over_time(rate(http_requests_total[5m])[1d:1h])
```

### Data Export

```bash
# Export metrics for analysis
curl -s "http://localhost:9090/api/v1/query_range?query=rate(http_requests_total[5m])&start=$(date -d '1 hour ago' +%s)&end=$(date +%s)&step=60" > metrics_export.json

# Export HAProxy stats
curl -s "http://localhost:8404/stats;csv" > haproxy_stats.csv
```

## Integration with Load Testing

### k6 Metrics Collection

```javascript
// In k6 test files, add custom metrics
import { Counter } from "k6/metrics";

export let k3s_responses = new Counter("k3s_responses");
export let knative_responses = new Counter("knative_responses");

// Track backend distribution
if (response.headers["Backend-Type"] === "k3s") {
	k3s_responses.add(1);
} else if (response.headers["Backend-Type"] === "knative") {
	knative_responses.add(1);
}
```

### Real-time Monitoring During Tests

```bash
# Monitor system during load test
./scripts/monitor-system.sh --watch &
MONITOR_PID=$!

./load-testing/run-load-tests.sh

kill $MONITOR_PID
```

## Sprint 2 Preparation

### Baseline Metrics for Prediction

```promql
# Request pattern analysis
rate(http_requests_total[5m]) by (hour_of_day)

# Response time patterns
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) by (hour_of_day)

# Resource usage patterns
avg_over_time(container_memory_usage_bytes[1h]) by (container)
```

### Data Collection for ML Training

```bash
# Collect training data for Sprint 2
./scripts/collect-training-data.sh --duration 1h --interval 30s
```

---

**Note**: This monitoring setup provides comprehensive visibility for Sprint 1's manual hybrid system. Sprint 2 will extend these queries with automated prediction and intelligent routing metrics.

**Resource-Constrained Alternative**: If full Prometheus monitoring exceeds resource limits, use script-based monitoring commands throughout this document for equivalent visibility.
