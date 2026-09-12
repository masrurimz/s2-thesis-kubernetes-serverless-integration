"""Treatment-fidelity evaluation: hard S4 prediction-delivery validity gate.

For S4 (predictive) runs the experiment is only analytically valid when the
prediction service was actually delivered on every prediction-eligible control
cycle. This module turns the daemon's delivery counters into a typed
``TreatmentFidelity`` DTO and tightens ``run_validity_passed`` accordingly.

S1-S3 (non-predictive) runs are untouched: they receive default fidelity.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Mapping

from shared.models.evidence import NodeEngagement, TreatmentFidelity
from shared.models.experiment import ExperimentResult

# Mirrors the canonical k6 threshold ``http_req_failed: rate<0.10``
# (load_tests/canonical/clarknet_replay.js); k6 crosses it at rate >= 0.10.
REQUEST_FAILURE_RATE_TOLERANCE = 0.10


def _is_predictive_scenario(scenario: str) -> bool:
    """True for S4 / predictive scenarios only."""
    s = scenario.lower()
    return "s4" in s or "predictive" in s


def evaluate_node_engagement(
    result: ExperimentResult,
    *,
    scenario: str,
    events: Sequence[str],
    nodes_provisioned: int,
) -> ExperimentResult:
    """Record whether the node tier was exercised and tighten validity when it was not.

    A scenario that runs the node autoscaler measures the capacity dimension the
    hybrid design adds. When no pod ever goes pending, that dimension is absent:
    the reactive arm pays no provisioning penalty and the predictive arm has
    nothing to warm, so the run cannot support a claim about the node tier. Such a
    run is marked invalid with the reason, rather than silently counting as a
    comparison. S2 has no node autoscaler and is never required to engage one.
    """
    engagement = NodeEngagement.from_provision_events(
        scenario,
        events,
        nodes_provisioned=nodes_provisioned,
        first_provision_delay_sec=result.first_provision_delay_sec,
    )

    result.node_engagement = engagement

    if engagement.reasons:
        result.run_validity_passed = False
        result.validity_gate_passed = False
        result.run_validity_notes = [*result.run_validity_notes, *engagement.reasons]

    return result


def evaluate_run_validity(
    result: ExperimentResult,
    *,
    scenario: str,
    preflight_passed: bool = True,
    daemon_status: Mapping[str, Any] | None = None,
) -> ExperimentResult:
    """Evaluate treatment fidelity and tighten validity flags in place.

    The daemon is the single source of truth for prediction delivery accounting:
    ``prediction_eligible_cycles`` and ``prediction_delivery_failures`` are
    incremented together on the same control loop, so successful deliveries are
    ``eligible - failed`` by construction. Deriving all three counts from the
    daemon (rather than mixing in the Prometheus ``gru_predictions_failed``
    delta) keeps the gate self-consistent and immune to Prometheus scrape gaps.

    A PREDICTIVE *action* is never required: an accurate forecast may correctly
    decide no proactive scaling is needed. Only *delivery* of the forecast is
    gated.
    """
    daemon_status = daemon_status or {}

    if result.error_rate >= REQUEST_FAILURE_RATE_TOLERANCE:
        result.run_validity_passed = False
        result.validity_gate_passed = False
        result.run_validity_notes = [
            *result.run_validity_notes,
            f"request failure rate {result.error_rate:.2%} exceeds k6 threshold http_req_failed: rate<0.10",
        ]

    if not _is_predictive_scenario(scenario):
        result.treatment_fidelity = TreatmentFidelity()
        return result

    eligible = int(daemon_status.get("prediction_eligible_cycles", 0))
    failed = int(daemon_status.get("prediction_delivery_failures", 0))
    successful = max(0, eligible - failed)
    delivery_rate = successful / eligible if eligible > 0 else 0.0

    model_history_ready = bool(daemon_status.get("model_history_ready", False))
    forecast_horizon_sufficient = bool(daemon_status.get("forecast_horizon_sufficient", False))
    forecast_actionable = int(daemon_status.get("forecast_actionable_cycles", 0))
    proactive_scaleups = int(daemon_status.get("proactive_scaleups", 0))

    delivered = (
        preflight_passed
        and eligible > 0
        and failed == 0
        and delivery_rate >= 1.0
        and model_history_ready
        and forecast_horizon_sufficient
    )

    reasons: list[str] = []
    if not preflight_passed:
        reasons.append("prediction preflight failed")
    if eligible == 0:
        reasons.append("no prediction-eligible cycles")
    if failed > 0:
        reasons.append(f"{failed} prediction delivery failures")
    if eligible > 0 and delivery_rate < 1.0:
        reasons.append(f"delivery rate {delivery_rate:.2%} < 100%")
    if not model_history_ready:
        reasons.append("model history never reached true input window (mean-value padding excluded)")
    if not forecast_horizon_sufficient:
        reasons.append("forecast horizon shorter than measured provisioning delay")

    result.treatment_fidelity = TreatmentFidelity(
        required=True,
        preflight_passed=preflight_passed,
        eligible_cycles=eligible,
        successful_predictions=successful,
        failed_predictions=failed,
        delivery_rate=delivery_rate,
        delivered=delivered,
        model_history_ready=model_history_ready,
        forecast_horizon_sufficient=forecast_horizon_sufficient,
        forecast_actionable_cycles=forecast_actionable,
        proactive_scaleups=proactive_scaleups,
        reasons=reasons,
    )

    if not delivered:
        result.run_validity_passed = False
        result.validity_gate_passed = False
        result.run_validity_notes = [*result.run_validity_notes, *reasons]

    return result
