# SLO Definition and Metrics Specification

## Overview

This document defines the Service Level Objectives (SLOs) and metrics for the hybrid K8s-Serverless routing system per thesis section 3.4.3.

## SLO Targets

### Primary SLO: Response Latency

| Percentile | Target | Measurement Window |
|------------|--------|-------------------|
| p50 | < 50ms | 30 seconds |
| p95 | < 100ms | 30 seconds |
| **p99** | **< 200ms** | **30 seconds** |

### Secondary SLOs

| Metric | Target | Description |
|--------|--------|-------------|
| Error Rate | < 0.1% | HTTP 5xx / total requests |
| Availability | > 99.9% | Uptime per hour |
| Throughput | No degradation | Compared to baseline |

## Algorithm 1: SLO Violation Detection

Per thesis section 3.4.3.1, the routing controller monitors p99 latency:

```
Algorithm 1: SLO-Aware Routing Controller
Input: 
  - current_p99: Current p99 latency (ms)
  - slo_threshold: SLO target (200ms)
  - violation_window: Detection window (30s)
  - current_weights: {k3s: int, knative: int}

Output:
  - new_weights: Adjusted traffic weights

Logic:
  1. IF current_p99 > slo_threshold for violation_window:
     - violation_detected = True
  2. IF violation_detected:
     - Increase knative_weight by 10% (better scaling)
     - Decrease k3s_weight accordingly
  3. IF current_p99 < slo_threshold * 0.7 (healthy margin):
     - Gradually restore k3s_weight (cost efficiency)
  4. Ensure weights sum to 100
```

## Prometheus Metrics

### Required Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `http_request_duration_seconds` | Histogram | backend, status | Request latency |
| `http_requests_total` | Counter | backend, status, method | Total requests |
| `haproxy_backend_weight` | Gauge | backend, server | Current weights |
| `slo_violation_total` | Counter | slo_name | SLO violation count |
| `routing_decision_total` | Counter | decision_type | Routing decisions |

### Prometheus Queries

```promql
# P99 latency (last 30s)
histogram_quantile(0.99, 
  sum(rate(http_request_duration_seconds_bucket[30s])) by (le)
)

# P95 latency
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket[30s])) by (le)
)

# Error rate
sum(rate(http_requests_total{status=~"5.."}[1m])) /
sum(rate(http_requests_total[1m]))

# Request rate by backend
sum(rate(http_requests_total[1m])) by (backend)

# SLO compliance (1 = compliant, 0 = violation)
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[30s])) by (le)) < 0.2
```

## Metrics Collection Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   HAProxy   │────▶│  Prometheus │────▶│  Controller │
│  (metrics)  │     │  (storage)  │     │  (queries)  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌─────────────┐
│   Grafana   │     │  Alerting   │
│ (dashboard) │     │  (optional) │
└─────────────┘     └─────────────┘
```

## Implementation Notes

1. **HAProxy Exporter**: Use haproxy-exporter for Prometheus metrics
2. **Scrape Interval**: 15 seconds (matches routing decision interval)
3. **Retention**: 7 days for experiment data
4. **Alert Threshold**: p99 > 180ms (warning before SLO breach)
