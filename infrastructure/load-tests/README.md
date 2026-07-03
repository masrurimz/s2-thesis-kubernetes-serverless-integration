# Load Tests

k6 load test scripts organized by category. All `.js` files target the hybrid k3s-serverless architecture and use the `/work` or `/fib` endpoints.

## Directory Layout

```
load-tests/
├── canonical/     # Primary experiment workloads (Phase A1/B)
├── calibration/   # Capacity and SLO calibration tests (T7 series)
├── legacy/        # Earlier sprint-era tests (superseded by canonical)
└── *.sh           # Shell harnesses for running k6
```

## JavaScript Load Tests

### `canonical/` — Primary Experiment Workloads

| File | Purpose | Status | Used By | Run Command |
|------|---------|--------|---------|-------------|
| `clarknet_replay.js` | ClarkNet trace-driven replay with per-endpoint custom metrics (app_duration_k8s, app_duration_serverless) | canonical | Phase A1 (S3/S4 hybrid scenarios) | `k6 run canonical/clarknet_replay.js -e TARGET_URL=… -e SCENARIO=s4-hybrid-predictive` |
| `clarknet_replay_fib34.js` | ClarkNet trace replay (fib34 fixed endpoint, simplified metrics) | canonical | Phase A1 (S3/S4 hybrid scenarios) | `k6 run canonical/clarknet_replay_fib34.js -e TARGET_URL=… -e SCENARIO=s4-hybrid-predictive` |
| `spike.js` | Sudden traffic spike (baseline → 10x spike → baseline) | canonical | Phase A1 baseline comparison | `k6 run canonical/spike.js` |
| `stress.js` | Capacity pressure ramp to 1000+ RPS, overwhelms throttled K8s pods | canonical | Phase A1 baseline comparison | `k6 run canonical/stress.js` |
| `endurance.js` | 30-min sine-wave load pattern for long-running stability | canonical | Phase A1 baseline comparison | `k6 run canonical/endurance.js` |
| `steady.js` | Constant 100 RPS for 5 min, baseline measurement | canonical | Phase A1 baseline comparison | `k6 run canonical/steady.js` |
| `dynamic_burst.js` | Multi-phase ramp/burst cycles (30→150 RPS) for PREDICTIVE triggering | canonical | Phase A1 predictive validation | `k6 run canonical/dynamic_burst.js` |

### `calibration/` — Capacity and SLO Calibration

| File | Purpose | Status | Used By | Run Command |
|------|---------|--------|---------|-------------|
| `calibration.js` | Workload calibration — find "Goldilocks" load (configurable RPS via env) | calibration | Pre-experiment tuning | `k6 run calibration/calibration.js -e RPS=100 -e DURATION=3` |
| `calibrate_work.js` | Single-RPS calibration runner with JSON summary output | calibration | Per-RPS calibration sweeps | `k6 run calibration/calibrate_work.js -e TARGET_RPS=30 -e WORK_MS=5` |
| `t7-capacity-health.js` | T7a: /work endpoint capacity envelope (100→3000 RPS ramp) | calibration | T7 capacity analysis | `k6 run calibration/t7-capacity-health.js` |
| `t7-capacity-fib.js` | T7b: /fib?n=25 CPU-intensive capacity envelope (10→500 RPS) | calibration | T7 capacity analysis | `k6 run calibration/t7-capacity-fib.js` |
| `t7-fib-slo-finder.js` | T7c: Fine-grained SLO threshold finder for /fib (10→200 RPS with holds) | calibration | T7 SLO threshold analysis | `k6 run calibration/t7-fib-slo-finder.js` |
| `t7-capacity-envelope.js` | T7 combined: /work or /fib capacity envelope (50→500 RPS, 15 stages) | calibration | T7 capacity analysis | `k6 run calibration/t7-capacity-envelope.js -e ENDPOINT=/work?duration_ms=5` |

### `legacy/` — Earlier Sprint-Era Tests

| File | Purpose | Status | Used By | Run Command |
|------|---------|--------|---------|-------------|
| `spike-load-legacy.js` | Spike load with HAProxy stats tracking (Sprint 1 era) | legacy | Sprint 1 validation | `k6 run legacy/spike-load-legacy.js` |
| `endurance-test-legacy.js` | 30-min endurance with HAProxy stats and health checks (Sprint 1 era) | legacy | Sprint 1 validation | `k6 run legacy/endurance-test-legacy.js` |
| `steady-load-legacy.js` | Steady 50 RPS with HAProxy backend distribution tracking | legacy | Sprint 1 validation | `k6 run legacy/steady-load-legacy.js` |
| `spike-stress.js` | Spike-with-idle pattern targeting SCALE_OUT triggering (fib35) | legacy | Pre-Phase A1 tuning | `k6 run legacy/spike-stress.js` |
| `spike-with-idle.js` | Spike-with-idle for H1/H2 SLO validation (steady→idle→spike cycles) | legacy | Pre-Phase A1 tuning | `k6 run legacy/spike-with-idle.js` |
| `stress-slo-violation.js` | SLO violation stress test using /fib endpoint | legacy | Pre-Phase A1 tuning | `k6 run legacy/stress-slo-violation.js` |
| `ramp.js` | Ramp 20→100 RPS for PREDICTIVE action triggering (4 min) | legacy | Phase A1 PREDICTIVE validation (used by `run-experiment.sh`) | `k6 run legacy/ramp.js` |

## Shell Harnesses

Located at the `load-tests/` root. These wrap k6 execution with environment setup, result collection, and multi-scenario orchestration.

| File | Purpose | Run Command |
|------|---------|-------------|
| `run-load-tests.sh` | Full load test suite orchestrator — runs multiple scenarios sequentially | `bash run-load-tests.sh` |
| `run-load-test.sh` | Single load test runner with configurable parameters | `bash run-load-test.sh <scenario> <target>` |
| `run-experiment.sh` | Phase A1/B experiment runner — executes S1-S4 scenarios with result collection | `bash run-experiment.sh <phase> <scenario>` |
| `run-stress-test.sh` | Stress test runner with progressive load increase | `bash run-stress-test.sh` |

## Environment Variables

All k6 scripts accept these via `-e KEY=VALUE`:

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` / `TARGET_URL` | `http://localhost:18082` | Application endpoint |
| `ENDPOINT` | varies per script | HTTP path to target |
| `RPS` | `100` | Target requests per second (calibration scripts) |
| `DURATION` | `3m` | Test duration |
| `FIB_N` | `30`/`35` | Fibonacci N for CPU-intensive endpoint |
| `SCENARIO` | `s4-hybrid-predictive` | Experiment scenario identifier |

## Notes

- Canonical scripts output JSON summaries to `results/load-tests/` (configured in each script's `handleSummary`).
- The `ramp.js` in `legacy/` is actively used by `run-experiment.sh` — it is the canonical ramp workload despite living in legacy.
- Calibration scripts output to stdout as JSON for easy piping to analysis tools.
