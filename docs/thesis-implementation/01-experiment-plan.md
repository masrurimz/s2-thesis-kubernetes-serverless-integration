# Experiment Plan (Final Protocol)

## 1. Research question and evaluation boundary

The final evaluation asks whether prediction-augmented scaling improves a reactive hybrid controller while preserving the p99 < 200 ms SLO. The system is evaluated in a reproducible local Kubernetes + Knative testbed, not as a claim about measured cloud billing.

The four scenarios are:

| ID | Scenario | Control path |
|---|---|---|
| S1 | K8s + HPA | Kubernetes baseline |
| S2 | Serverless-only | Knative backend |
| S3 | Hybrid-reactive | V3 routing with observed load |
| S4 | Hybrid-predictive | Same routing plus GRU-informed Algorithm 2 scaling |

H1 is a directional n=1 diagnostic: S4 p99 118.2 ms versus S1 2,421.3 ms. H2 is the definitive counterbalanced paired n=5 S3/S4 comparison: S3 188.5 ms versus S4 126.0 ms, p=0.0304, d=-1.26, with identical USD 163 proxy cost.

## 2. Workload and data roles

The deployed workload is the deterministic CPU-bound `/fib?n=33` endpoint. Workload traces are replayed by k6 and are collected independently from model training.

- **GRU training:** synthetic diurnal, burst, and ramp RPS series.
- **Validation:** ClarkNet and Calgary HTTP traces.
- **Replay/evaluation:** ClarkNet variable-load replay (Calgary remains a validation corpus).
- **Forecast:** nine direct steps sampled every 15 seconds, giving a **135-second horizon**.

This split avoids presenting validation/replay traces as the training set and makes the predictor mechanism testable under a workload shape not copied into training.

## 3. Final architecture

```text
synthetic RPS -> GRU (9 x 15 s = 135 s)
                       |
                       v
               Algorithm 2 replica scaling
                       |
observed load + ready capacity -> Algorithm 1 V3 -> HAProxy weights
                       |                                  |
                 Kubernetes replicas                 K8s / Knative
```

The GRU's confidence-gated upper forecast is an input to Algorithm 2's target-replica calculation. Algorithm 1 does not translate the raw prediction directly into a Knative weight. Its routing decisions use observed load, observed ready capacity, HAProxy rtime-derived p99, and observed-load trend extrapolation gated by GRU confidence.

## 4. Control and calibration parameters

- Primary SLO: p99 < 200 ms.
- Control interval: 15 s.
- `r_saturation_per_replica`: 33.3 RPS.
- Effective capacity uses the configured target utilization margin.
- Replica bounds: minimum 3, maximum 6 for the final static envelope.
- Serverless routing uses graduated weight changes with cooldown and hysteresis.
- Node resource limits are applied through the thesis infrastructure command before runs.

See [CALIBRATION_GUIDE.md](../CALIBRATION_GUIDE.md) for the measured capacity procedure and [../specs/algorithm-1-spec.md](../specs/algorithm-1-spec.md) for decision priority.

## 5. Governed execution

```bash
uv run thesis-experiment preflight
uv run thesis-experiment run --phase full --runs 5 --duration 300
uv run thesis-experiment paired-run --pairs 5
uv run thesis-experiment dynamic --runs 3
uv run thesis-experiment calibrate
uv run thesis-experiment trace-replay
uv run thesis-experiment evidence audit
uv run thesis-experiment evidence reconcile --apply
uv run thesis-experiment evidence catalog refresh
uv run thesis-experiment evidence journal
```

For H2, use `paired-run --pairs 5` with ClarkNet and the V3 controller. Every run is reset, warmed, measured, cooled, collected, and checked for treatment fidelity. S4 predictions must be delivered and the forecast horizon must be sufficient before the run is admitted to the definitive comparison.

## 6. Measures

Collect p50/p95/p99 latency, SLO violations, request rate, errors, backend distribution, Kubernetes replica targets and readiness, prediction delivery/confidence, scale decisions, and directional proxy cost. H2 uses paired p99 as the primary endpoint. Secondary p95 and SLO counts are descriptive after multiplicity correction.

## 7. Interpretation constraints

The definitive H2 result supports predictive control for this ClarkNet replay and calibrated testbed. The H1 result is directional because it has n=1. Cost is a proxy model; identical USD 163 values establish no universal cloud-cost claim. Historical proposal documents and superseded result bundles remain historical records and are not this protocol.
