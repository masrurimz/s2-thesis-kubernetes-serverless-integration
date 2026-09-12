"""Evidence tables a reader — human or agent — asks a bundle for.

The experiment runner writes a bundle of per-run artifacts; answering a question about
it used to mean opening those files by hand, which is how two different p-values for
one pair and a phantom-field DCI survived as long as they did. Each builder here takes
a bundle directory and returns typed rows over the artifacts, so a question is a
function call and a table is a rendering of its result.

Three questions, one per builder:

* ``run_evidence`` — what did each run measure, and under what conditions? The
  validity verdict, the latency and SLO outcome, the node tier's engagement, the
  forecast delivery and the host load the measurement was taken under.
* ``mechanism_rows`` — when did the extra node arrive relative to the load, and what
  did the tail do? The node tier is the mechanism the hybrid design exists to add, so
  a reader needs its timing beside the latency it is supposed to explain.
* ``variance_summary`` — how much does the arm move run to run? A paired verdict is
  only as meaningful as the spread around it, and the smallest p an n-pair design can
  attain is 2^-n.
"""

from __future__ import annotations

from pathlib import Path
from statistics import mean, stdev
from typing import Any, Sequence

from pydantic import BaseModel, Field
from shared.artifacts import read_manifest, read_provision_events, read_result


class RunEvidence(BaseModel):
    """One run: its outcome, its validity, and the conditions it was measured under."""

    scenario: str
    run_id: int
    valid: bool
    p99_latency_ms: float
    p95_latency_ms: float = 0.0
    slo_violations: int = 0
    error_rate: float = 0.0
    throughput_rps: float = 0.0
    node_tier_required: bool | None = None
    node_tier_engaged: bool | None = None
    pending_events: int = 0
    nodes_provisioned: int = 0
    first_provision_delay_sec: float = 0.0
    prediction_delivered: bool | None = None
    eligible_cycles: int = 0
    successful_predictions: int = 0
    failed_predictions: int = 0
    host_load_ratio: float | None = None
    validity_notes: list[str] = Field(default_factory=list)


class MechanismRow(BaseModel):
    """The node tier's timing beside the tail it is meant to explain."""

    scenario: str
    run_id: int
    p99_latency_ms: float
    provisioning_delay_sec: float
    node_arrival_offset_sec: float | None = None
    serverless_share_pct: float | None = None
    slo_violations: int = 0


class ArmSpread(BaseModel):
    """How far one arm moved across its runs."""

    scenario: str
    n: int
    mean_p99_ms: float
    sd_p99_ms: float
    min_p99_ms: float
    max_p99_ms: float


class VarianceSummary(BaseModel):
    """Arm spread and the paired design's resolution."""

    arms: list[ArmSpread]
    n_pairs: int
    pair_differences_ms: list[float]
    mean_difference_ms: float | None = None
    sd_difference_ms: float | None = None
    smallest_attainable_p: float | None = None
    note: str = ""


def _run_dirs(bundle: Path) -> list[Path]:
    return sorted(p for p in bundle.glob("*_run*") if p.is_dir())


def run_evidence(bundle: Path) -> list[RunEvidence]:
    """One row per run that produced a result, in scenario then run order."""
    rows: list[RunEvidence] = []
    for run_dir in _run_dirs(bundle):
        result = read_result(run_dir)
        if result is None:
            continue
        engagement = result.node_engagement
        fidelity = result.treatment_fidelity
        manifest = read_manifest(run_dir)
        conditions = manifest.conditions if manifest else {}
        rows.append(
            RunEvidence(
                scenario=result.scenario,
                run_id=result.run_id,
                valid=bool(result.run_validity_passed),
                p99_latency_ms=result.p99_latency_ms,
                p95_latency_ms=result.p95_latency_ms,
                slo_violations=result.slo_violations_k6,
                error_rate=result.error_rate,
                throughput_rps=result.throughput_rps,
                node_tier_required=engagement.required if engagement else None,
                node_tier_engaged=engagement.autoscaler_engaged if engagement else None,
                pending_events=engagement.pending_events if engagement else 0,
                nodes_provisioned=engagement.nodes_provisioned if engagement else 0,
                first_provision_delay_sec=engagement.first_provision_delay_sec if engagement else 0.0,
                prediction_delivered=fidelity.delivered if fidelity else None,
                eligible_cycles=fidelity.eligible_cycles if fidelity else 0,
                successful_predictions=fidelity.successful_predictions if fidelity else 0,
                failed_predictions=fidelity.failed_predictions if fidelity else 0,
                host_load_ratio=(conditions.get("load") or {}).get("ratio"),
                validity_notes=list(result.run_validity_notes),
            )
        )
    return rows


def mechanism_rows(bundle: Path) -> list[MechanismRow]:
    """The provisioning timeline per run, when the run recorded one."""
    rows: list[MechanismRow] = []
    for run_dir in _run_dirs(bundle):
        result = read_result(run_dir)
        if result is None:
            continue
        events = read_provision_events(run_dir)
        created = next((event for event in events if event.event == "node_created"), None)
        offset = (created.ts - events[0].ts) if (created is not None and events) else None
        rows.append(
            MechanismRow(
                scenario=result.scenario,
                run_id=result.run_id,
                p99_latency_ms=result.p99_latency_ms,
                provisioning_delay_sec=result.first_provision_delay_sec,
                node_arrival_offset_sec=offset,
                serverless_share_pct=result.time_in_serverless_pct,
                slo_violations=result.slo_violations_k6,
            )
        )
    return rows


def variance_summary(bundle: Path) -> VarianceSummary:
    """Per-arm spread, the per-pair differences, and what n pairs can resolve."""
    evidence = run_evidence(bundle)
    by_scenario: dict[str, dict[int, float]] = {}
    for row in evidence:
        if row.valid:
            by_scenario.setdefault(row.scenario, {})[row.run_id] = row.p99_latency_ms

    arms = [
        ArmSpread(
            scenario=scenario,
            n=len(values),
            mean_p99_ms=mean(values.values()),
            sd_p99_ms=stdev(values.values()) if len(values) > 1 else 0.0,
            min_p99_ms=min(values.values()),
            max_p99_ms=max(values.values()),
        )
        for scenario, values in sorted(by_scenario.items())
    ]

    scenarios = sorted(by_scenario)
    differences: list[float] = []
    if len(scenarios) == 2:
        baseline, comparison = by_scenario[scenarios[0]], by_scenario[scenarios[1]]
        differences = [comparison[i] - baseline[i] for i in sorted(set(baseline) & set(comparison))]

    n_pairs = len(differences)
    return VarianceSummary(
        arms=arms,
        n_pairs=n_pairs,
        pair_differences_ms=differences,
        mean_difference_ms=mean(differences) if differences else None,
        sd_difference_ms=stdev(differences) if n_pairs > 1 else None,
        smallest_attainable_p=2.0**-n_pairs if n_pairs else None,
        note=(
            "A paired verdict must be read against this spread: the arm means can differ by "
            "far less than either arm's run-to-run standard deviation, and 2^-n is the "
            "smallest p the design can produce."
        ),
    )


def as_payload(rows: Sequence[BaseModel] | BaseModel) -> Any:
    """The machine-readable form of any table above.

    Sequence, not list: a list of one model subclass is not a list of BaseModel, and
    the tables here are always concrete rows.
    """
    if isinstance(rows, BaseModel):
        return rows.model_dump()
    return [row.model_dump() for row in rows]
