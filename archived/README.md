# Archived

Historical experiments and resources that are no longer actively used but preserved for reference.

## Contents

| Folder | Original Location | Description |
|--------|-------------------|-------------|
| `apps-rust/` | `apps/` | Rust test application versions (v1-v5) |
| `autoscaler-experiments/` | `autoscaler/` | 7 autoscaling research experiments |
| `cluster-configs/` | `cluster-configs/` | Multi-cluster A/B/C configurations |
| `monitoring-versions/` | `monitoring/` | Prometheus v1 and v2 setups |
| `references/` | `references/` | Tutorial and reference materials |

## Why Archived

These folders were created during early research and exploration phases. The thesis now uses:

- **sprint-1/infrastructure/** instead of cluster-configs/ and monitoring/
- **sprint-2/** for the intelligent routing implementation
- **ml_models/** for prediction models (replacing controller/)
- **experiments/** for formal thesis evaluation

## Potentially Useful

- `autoscaler-experiments/experiment-7-zscaler/` - Contains k3d autoscaler implementation that may inform GRU controller
- `apps-rust/v1-basic/` - Simple test application if needed for benchmarking
