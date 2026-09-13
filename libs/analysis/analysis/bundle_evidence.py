"""Evidence tables a reader — human or agent — asks a bundle for.

The experiment runner writes a bundle of per-run artifacts; answering a question about
it used to mean opening those files by hand, which is how two different p-values for
one pair and a phantom-field DCI survived as long as they did. Each builder here takes
a bundle directory and returns typed rows over the artifacts, so a question is a
function call and a table is a rendering of its result.

Four questions, one per builder:

* ``run_evidence`` — what did each run measure, and under what conditions? The
  validity verdict, the latency and SLO outcome, the node tier's engagement, the
  forecast delivery and the host load the measurement was taken under.
* ``mechanism_rows`` — when did the extra node arrive relative to the load, and what
  did the tail do? The node tier is the mechanism the hybrid design exists to add, so
  a reader needs its timing beside the latency it is supposed to explain. Each row
  also carries the treatment's engagement: the serverless weight share over the
  trace's ramp window, and proactive actions per eligible prediction cycle —
  reported, never gated (an accurate forecast may legitimately decide to act zero
  times).
* ``mechanism_pairs`` — the same evidence per S3/S4 pair: the node-arrival lead the
  predictive arm did or did not buy, beside both arms' ramp routing shares. This is
  what separates "the treatment never fired" from "it fired and made no
  difference" — an underpowered null and an absent treatment look identical in a
  whole-run p99 alone.
* ``variance_summary`` — how much does the arm move run to run? A paired verdict is
  only as meaningful as the spread around it, and the smallest p an n-pair design can
  attain is 2^-n.
"""

from __future__ import annotations

import functools
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, stdev
from typing import Any, Sequence

from pydantic import BaseModel, Field
from shared.artifacts import (
    read_manifest,
    read_paired_analysis,
    read_prometheus_export,
    read_provision_events,
    read_result,
)

from analysis.k6_stages import ramp_stage_indices, ramp_window_sec

# libs/analysis/analysis/bundle_evidence.py -> 4 levels up to repo root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_CANONICAL_STAGES_JSON = PROJECT_ROOT / "data" / "trace-replay" / "clarknet_k6_stages.json"


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
    ramp_serverless_share_pct: float | None = None
    prediction_use_ratio: float | None = None
    prediction_use_source: str = ""


class PairMechanism(BaseModel):
    """One pair: the lead the predictive arm bought, beside the routing it did."""

    run_id: int
    baseline_scenario: str
    comparison_scenario: str
    baseline_node_at_s: float | None = None
    comparison_node_at_s: float | None = None
    lead_s: float | None = None
    baseline_ramp_share_pct: float | None = None
    comparison_ramp_share_pct: float | None = None
    baseline_prediction_use: float | None = None
    comparison_prediction_use: float | None = None
    prediction_use_source: str = ""


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
        prediction_use_ratio, prediction_use_source = _prediction_use(run_dir, result)
        rows.append(
            MechanismRow(
                scenario=result.scenario,
                run_id=result.run_id,
                p99_latency_ms=result.p99_latency_ms,
                provisioning_delay_sec=result.first_provision_delay_sec,
                node_arrival_offset_sec=offset,
                serverless_share_pct=result.time_in_serverless_pct,
                slo_violations=result.slo_violations_k6,
                ramp_serverless_share_pct=_ramp_serverless_share(run_dir),
                prediction_use_ratio=prediction_use_ratio,
                prediction_use_source=prediction_use_source,
            )
        )
    return rows


def mechanism_pairs(bundle: Path) -> list[PairMechanism]:
    """Per pair: both arms' node arrivals, the lead, and the ramp routing share."""
    rows = mechanism_rows(bundle)
    by_scenario: dict[str, dict[int, MechanismRow]] = {}
    for row in rows:
        by_scenario.setdefault(row.scenario, {})[row.run_id] = row
    scenarios = sorted(by_scenario)
    if len(scenarios) != 2:
        return []
    baseline, comparison = by_scenario[scenarios[0]], by_scenario[scenarios[1]]
    pairs: list[PairMechanism] = []
    for run_id in sorted(set(baseline) & set(comparison)):
        base, comp = baseline[run_id], comparison[run_id]
        lead = (
            base.node_arrival_offset_sec - comp.node_arrival_offset_sec
            if base.node_arrival_offset_sec is not None and comp.node_arrival_offset_sec is not None
            else None
        )
        sources = [row.prediction_use_source for row in (base, comp) if row.prediction_use_source]
        pairs.append(
            PairMechanism(
                run_id=run_id,
                baseline_scenario=scenarios[0],
                comparison_scenario=scenarios[1],
                baseline_node_at_s=base.node_arrival_offset_sec,
                comparison_node_at_s=comp.node_arrival_offset_sec,
                lead_s=lead,
                baseline_ramp_share_pct=base.ramp_serverless_share_pct,
                comparison_ramp_share_pct=comp.ramp_serverless_share_pct,
                baseline_prediction_use=base.prediction_use_ratio,
                comparison_prediction_use=comp.prediction_use_ratio,
                prediction_use_source="; ".join(dict.fromkeys(sources)),
            )
        )
    return pairs


@functools.lru_cache(maxsize=1)
def _ramp_window() -> tuple[float, float, int, int] | None:
    """The canonical trace's ramp window in run-relative seconds and stages.

    The replay script pins its stages file (workload stage and preflight both
    point at ``data/trace-replay/clarknet_k6_stages.json``), so the trace on
    disk is the layout every bundle in this repo ran; the window rule is the
    one both the script and ``analysis.k6_stages`` implement.
    """
    try:
        stages = json.loads(_CANONICAL_STAGES_JSON.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    window = ramp_window_sec(stages)
    indices = ramp_stage_indices([float(stage.get("target", 0)) for stage in stages])
    if window is None or indices is None:
        return None
    return (window[0], window[1], indices[0], indices[1])


_K6_END_TS_RE = re.compile(r"_(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d+)Z\.json$")


def _k6_test_start_epoch(run_dir: Path) -> float | None:
    """The k6 scenario start as a wall-clock epoch, from the run's own artifact.

    handleSummary stamps the data file's name when the test ends and the data
    object carries ``state.testRunDurationMs``; start = end − duration. This
    anchors the ramp window onto the Prometheus sample clock (both absolute
    epochs; measured skew on existing bundles is under one second).
    """
    files = sorted((run_dir / "k6").glob("clarknet_replay_*.json"), key=lambda p: p.stat().st_mtime)
    if not files:
        return None
    match = _K6_END_TS_RE.search(files[-1].name)
    if not match:
        return None
    try:
        data = json.loads(files[-1].read_text())
        duration_ms = data["state"]["testRunDurationMs"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        return None
    if not isinstance(duration_ms, (int, float)):
        return None
    ended = datetime.strptime(match.group(1), "%Y-%m-%dT%H-%M-%S-%f").replace(tzinfo=timezone.utc)
    return ended.timestamp() - duration_ms / 1000.0


def _ramp_serverless_share(run_dir: Path) -> float | None:
    """Mean serverless weight share over the ramp window's Prometheus samples.

    ``daemon_weight_knative / (daemon_weight_knative + daemon_weight_k3s)``
    per sample, averaged over samples inside the window. None — not a blank —
    when the run recorded no weight series or no k6 artifact to place it.
    """
    window = _ramp_window()
    start = _k6_test_start_epoch(run_dir)
    if window is None or start is None:
        return None
    export = read_prometheus_export(run_dir)
    knative = export.get("daemon_weight_knative") or []
    k3s = {ts: value for ts, value in export.get("daemon_weight_k3s") or []}
    lo, hi = start + window[0], start + window[1]
    shares = [
        knative_value / (knative_value + k3s[ts])
        for ts, knative_value in knative
        if lo <= ts < hi and k3s.get(ts) is not None and (knative_value + k3s[ts]) > 0
    ]
    return 100.0 * mean(shares) if shares else None


def _prediction_use(run_dir: Path, result: Any) -> tuple[float | None, str]:
    """Engagement: proactive actions per eligible prediction cycle.

    Prefers the run's own treatment-fidelity block (``proactive_scaleups /
    eligible_cycles`` from result.json); falls back to the Prometheus export's
    daemon counters (``daemon_predictions_used`` / ``daemon_decisions``, as
    run deltas) only when the DTO is absent. Reported, never gated: the
    validity stage deliberately does not require a proactive action, because
    an accurate forecast may legitimately decide none is needed. The second
    return value names the source the number came from.
    """
    fidelity = result.treatment_fidelity
    if fidelity is not None:
        if fidelity.eligible_cycles > 0:
            return fidelity.proactive_scaleups / fidelity.eligible_cycles, "treatment_fidelity"
        return None, "treatment_fidelity"
    export = read_prometheus_export(run_dir)
    decisions = export.get("daemon_decisions") or []
    used = export.get("daemon_predictions_used") or []
    decision_delta = decisions[-1][1] - decisions[0][1] if len(decisions) >= 2 else 0.0
    used_delta = used[-1][1] - used[0][1] if len(used) >= 2 else 0.0
    if decision_delta > 0:
        return used_delta / decision_delta, "prometheus"
    return None, "prometheus"


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


def paired_verdict(bundle: Path) -> dict[str, Any] | None:
    """The paired analysis a bundle stored, or None when it has none.

    Exists so a caller above the artifact layer (the `thesis` home view) can report a
    bundle's verdict without importing `shared.artifacts`, which only `experiment`,
    `analysis` and `analysis_cli` may do.
    """
    return read_paired_analysis(bundle)


def as_payload(rows: Sequence[BaseModel] | BaseModel) -> Any:
    """The machine-readable form of any table above.

    Sequence, not list: a list of one model subclass is not a list of BaseModel, and
    the tables here are always concrete rows.
    """
    if isinstance(rows, BaseModel):
        return rows.model_dump()
    return [row.model_dump() for row in rows]
