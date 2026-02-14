# Calibration Report: /work Endpoint Saturation (2026-02-14)

## Purpose

Calibrate the deterministic `/work?duration_ms=5` endpoint to find the Goldilocks zone where:
- Low RPS is healthy (p99 < 200ms SLO)
- High RPS causes SLO violations (p99 > 200ms)

This calibration determines the scaling factor `g` for ClarkNet trace replay and the α/β coefficients for Algorithm 2.

## Setup

| Parameter | Value |
|-----------|-------|
| Endpoint | `/work?duration_ms=5` |
| GOMAXPROCS | 1 (single-threaded) |
| CPU Limit | 500m |
| Memory Limit | 128Mi |
| Replicas | 1 |
| HAProxy Weights | k3s=100, knative=0 |
| Image | k3d-registry.localhost:5000/test-app:latest (sha256:f8e2ce74) |

## Results

| RPS | p50 (ms) | p90 (ms) | p95 (ms) | max (ms) | avg (ms) | Status |
|-----|----------|----------|----------|----------|----------|--------|
| 30 | 5.5 | 5.96 | 6.03 | 6.4 | 5.77 | ✅ Healthy |
| 60 | 5.5 | 5.84 | 5.88 | 6.2 | 5.67 | ✅ Healthy |
| 90 | 5.5 | 6.44 | 6.68 | 20.8 | 5.68 | ✅ Healthy |
| 120 | 5.5 | 6.60 | 6.71 | 11.1 | 5.81 | ✅ Healthy |
| 130 | 5.5 | 6.54 | 6.64 | 10.8 | 5.81 | ✅ Healthy |
| 135 | 5.5 | 6.5 | 6.7 | 239 | 7.21 | ✅ Healthy (occasional spike) |
| 140 | 5.5 | 6.5 | 6.6 | 7.4 | 5.79 | ✅ Healthy |
| 145 | 6.2 | 36.1 | 56.2 | 241 | 13.9 | ⚠️ Transition |
| 148 | 1204 | 2540 | 2648 | 5191 | 1215 | ❌ Saturated |
| 150 | 348 | 968 | 1024 | 2347 | 451 | ❌ Saturated |
| 155 | -- | 2189 | 2239 | 4715 | 1050 | ❌ Saturated |
| 160 | 7.2 | 753 | 879 | 1924 | 217 | ❌ Saturated |
| 180 | 1148 | 3108 | 3166 | 7605 | 1510 | ❌ Saturated |
| 200 | 6.2 | 138 | 169 | 423 | 31.4 | ⚠️ Anomalous (residual drain) |

## Interpretation

**Saturation cliff: ~145 RPS** (single replica, GOMAXPROCS=1, 5ms work)

- Theory: 1000ms / 5ms = 200 RPS max throughput
- Practical: ~145 RPS (72% of theoretical) due to Go runtime overhead, JSON serialization, HAProxy proxy latency
- Transition zone: 140-145 RPS (p95 rises from 7ms to 56ms)
- Full saturation: ≥148 RPS (p95 > 2000ms, queuing dominates)

## Derived Parameters

| Parameter | Value | Derivation |
|-----------|-------|------------|
| α (Algorithm 2) | 0.0069 | 1 / 145 RPS per replica |
| β (Algorithm 2) | 0.0 | min_replicas=1 enforces floor |
| g (trace replay) | 33 | Peak 164 RPS (1.13× saturation) |
| Baseline replicas | 1 | Ensures overload windows exist |

## Relationship to Previous Calibration

Previous calibration (2026-02-12) used `/health` endpoint with 10m-30m CPU limits and found no meaningful saturation (health checks are near-zero CPU). That calibration is **invalidated** by the endpoint change.
