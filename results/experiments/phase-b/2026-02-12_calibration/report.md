# Phase B Calibration

**Date:** 2026-02-12
**Purpose:** Find "Goldilocks" load where S1 shows stress but doesn't collapse.

## Results

| Scenario | RPS | p99 (ms) | Throughput (RPS) | Violations | Error Rate |
|----------|-----|----------|------------------|------------|------------|
| S1 (K8s-only) | 50 | 374.3 | 35.3 | 1 | 0% |
| S1 (K8s-only) | 100 | 515.9 | 41.1 | 1 | 0% |
| S1 (K8s-only) | 150 | 546.7 | 42.9 | 1 | 0% |
| S3 (Hybrid Reactive) | 50 | 165.1 | 49.1 | 0 | 0% |
| S3 (Hybrid Reactive) | 100 | 167.8 | 69.9 | 0 | 0% |
| S3 (Hybrid Reactive) | 150 | 136.8 | 85.7 | 0 | 0% |

## Key Findings

- Script selected 50 RPS as Goldilocks, but the actual Phase B replicated experiments used **100 RPS**
- S1 is stressed at ALL load levels (p99 > 200ms) due to k3d single-node limitations
- S3 handles all levels comfortably (p99 < 200ms) — hybrid routing prevents violations
- Actual throughput is well below target RPS at all levels (system bottleneck)

## Source

Raw data: `raw/calibration_analysis.json`
