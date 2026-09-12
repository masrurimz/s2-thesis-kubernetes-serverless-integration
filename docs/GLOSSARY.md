# Glossary

The words this repository uses in a specific way. Each entry says what the term means here, not in computing at large. Where a term is defined in code, the file is named.

## The system

**Scenario.** One of the four designs compared under the same workload: S1 K8s-only, S2 serverless-only, S3 hybrid-reactive, S4 hybrid-predictive. Defined in `libs/shared/shared/scenarios.py`.

**Arm.** One of the two places a request can be served: the Kubernetes deployment or the Knative service. "K8s arm" and "serverless arm."

**Node tier.** The k3d agent nodes that the autoscaler adds and removes. The pod tier is the replicas inside those nodes. A hybrid run that never reached the node tier measured the pod tier alone.

**Static agent.** An agent node that is present before a run starts. The count is set by `uv run thesis infra shape-nodes --agents N` and is part of what a profile declares.

**Dynamic node.** An agent node the autoscaler creates during a run, after a pod cannot be scheduled. Its name starts with `k3d-dynamic-`.

**Provisioning delay.** The modelled 45 to 120 second machine boot between the autoscaler deciding to add a node and that node being Ready. The daemon tracks its own estimate in an EWMA.

**Weight-time product.** The way the traffic split is computed: `serverless_weight_time / (k8s_weight_time + serverless_weight_time)`. It is not `time_in_serverless_pct`.

## The controllers

**Algorithm 1.** The routing controller. V1 and V2 are superseded; V3 is what runs. It decides the HAProxy weights from observed load, observed ready capacity, and the p99 derived from HAProxy `rtime`. Specified in `docs/specs/algorithm-1-spec.md`.

**Algorithm 2.** The pod scaler. `ClusterController` computes a Kubernetes replica target from the predicted or observed load, using `replicas = alpha * load + beta` with a buffer. With S4 the load is the GRU forecast; with S3 it is the observed value.

**Priority order.** `SCALE_OUT > PREDICTIVE > OPTIMIZE_COST > MAINTAIN`. A higher entry wins when several conditions hold.

**Confidence gate.** The rule that the predictive path may act only when the GRU's confidence passes a threshold. Without it, Algorithm 1 falls back to observed-load behaviour.

**Forecast horizon.** 9 steps of 15 seconds, 135 seconds ahead. The window covers the longest measured provisioning delay (120 s) plus a 15 second margin.

**Sequence length.** The number of past samples the model consumes per prediction: 30 samples, 7.5 minutes at 15 seconds each.

**Calibration.** The measured constants that make the controllers match this testbed's hardware. One source of truth: `CalibrationConfig` in `libs/shared/shared/models/calibration.py`. Two that appear often: `r_saturation_per_replica` (the RPS at which one pod's p99 reaches the SLO) and `target_cpu_util` (the safety margin applied to it).

## Running an experiment

**Profile.** A named run recipe: the scenarios, the design, how many pairs or runs, the static agent count, whether the prediction server is needed, and any controller environment. Defined in `apps/experiment/experiment/profiles.py`.

**Conditions gate.** The checks every run passes before it starts: testbed converged and residue cleared, nodes Ready, both arms serving, a predictor when the profile needs one, and a host quiet enough to measure on. Implemented in `apps/experiment/experiment/conditions.py`.

**`run_refused`.** The recorded outcome when a run fails the conditions gate. The run produces no result and is never silently retried.

**Series.** A chain of profiles run as one unit, with one retry per stage: `uv run thesis experiment series --stage ...`.

**Bundle.** The dated directory under `results/experiments/<phase>/` that holds one experiment's evidence: `meta.yaml`, `events.jsonl`, the per-run directories under `raw/`, the computed `paired_analysis.json`, and `SUMMARY.md`.

**Pair.** One S3 run and one S4 run under the same conditions. A paired design runs them in counterbalanced order so that a time trend cannot masquerade as a treatment effect.

**Regime.** The testbed shape a run ran under: static agents, residue, host load. Recorded in the run's conditions, because the same design gives opposite answers in different regimes.

**Validity gate.** A rule that rejects a run rather than counting it. Three exist: the conditions gate, node engagement (`NodeEngagement` in `libs/shared/shared/models/evidence.py`), and S4 treatment fidelity.

**Treatment fidelity.** For S4: GRU preflight passed and every eligible cycle received a prediction. A run with `treatment_fidelity.delivered=False` is excluded from paired analysis.

**Host load ratio.** The gate's measure of how busy the machine is: CPU busy time over the interval, divided by core count, read from `/proc/stat`. Above 0.5 it warns; at 1.0 it refuses.

## The evidence

**Evidence registry.** The typed index of every bundle: `results/evidence/registry.yaml`, maintained by `thesis experiment evidence audit` and `reconcile --apply`. The implementation is `apps/experiment/experiment/evidence/registry.py`.

**Catalog.** The local DuckDB database built from the bundles, queried with `thesis experiment evidence query`. It is a cache: rebuild it with `catalog refresh`, never trust it as the record.

**Claims map.** `results/claims/CLAIMS_TO_EVIDENCE.md`: every thesis claim beside the bundle that supports it.

**Definitive bundle.** The bundle named in `results/claims/FINAL_NUMBERS.md` as the source of the numbers the thesis may quote. For H2 that is `2026-07-14_clarknet-tuned-paired-n5`.

**Superseded.** Invalidated by a later fix and marked as such. Do not cite it, and do not delete it: it is the reason the fix is visible.

**Phase.** A family of experiments: `phase-a1` (predictive trigger), `phase-b` (the main paired and baseline work), `phase-c` (dynamic ramp and burst).

## The workload

**k6.** The load generator. It replays a stage file from `data/trace-replay/` against the testbed.

**`/fib?n=33`.** The deterministic CPU endpoint the workload calls. The value of `n` and the pod CPU request together decide how much load one replica absorbs.

**r_saturation.** See Calibration.

**Knative and Kourier.** The serverless runtime and its gateway. Knative runs in `thesis-serverless`, its own k3d cluster, so that its control plane cannot starve the measured workload.

**sslip.io.** The hostname scheme that gives the Knative service a resolvable name without DNS.
