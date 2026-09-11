"""Tests for the node-tier validity gate.

A scenario that runs the node autoscaler only measures the capacity dimension the
hybrid design adds when a pod actually goes pending. These tests pin that the gate
records engagement and rejects a hybrid run that never reached the node tier.
"""

from __future__ import annotations

from shared.models.experiment import ExperimentResult

from experiment.stages.validate import evaluate_node_engagement


def _result(**fields) -> ExperimentResult:
    return ExperimentResult(scenario=fields.pop("scenario", "s4-hybrid-predictive"), run_id=1, **fields)


def test_hybrid_run_without_a_pending_pod_is_rejected():
    result = _result(first_provision_delay_sec=0.0)

    result = evaluate_node_engagement(
        result,
        scenario="s4-hybrid-predictive",
        events=["autoscaler_started", "autoscaler_stopped"],
        nodes_provisioned=0,
    )

    assert result.node_engagement is not None
    assert result.node_engagement.required is True
    assert result.node_engagement.autoscaler_engaged is False
    assert result.run_validity_passed is False
    assert result.validity_gate_passed is False
    assert any("node tier not exercised" in note for note in result.run_validity_notes)


def test_hybrid_run_that_provisions_a_node_is_accepted():
    result = _result(first_provision_delay_sec=97.5)

    result = evaluate_node_engagement(
        result,
        scenario="s3-hybrid-reactive",
        events=["autoscaler_started", "pending_detected", "node_created", "pending_detected", "node_created"],
        nodes_provisioned=2,
    )

    assert result.node_engagement is not None
    assert result.node_engagement.autoscaler_engaged is True
    assert result.node_engagement.pending_events == 2
    assert result.node_engagement.nodes_provisioned == 2
    assert result.node_engagement.first_provision_delay_sec == 97.5
    assert result.run_validity_passed is True
    assert result.run_validity_notes == []


def test_serverless_only_has_no_node_tier_to_exercise():
    result = _result(scenario="s2-serverless-only")

    result = evaluate_node_engagement(
        result,
        scenario="s2-serverless-only",
        events=[],
        nodes_provisioned=0,
    )

    assert result.node_engagement is not None
    assert result.node_engagement.required is False
    assert result.run_validity_passed is True
    assert result.run_validity_notes == []
