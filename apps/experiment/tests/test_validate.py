"""Tests for the S4 prediction-delivery treatment-fidelity validity gate.

Pure-function tests over ``evaluate_run_validity``: no daemon, no cluster, no
network. The daemon is mocked via the ``daemon_status`` mapping.
"""

from __future__ import annotations

from experiment.stages.validate import evaluate_run_validity
from shared.models.evidence import TreatmentFidelity
from shared.models.experiment import ExperimentResult


def _make_result(scenario: str = "s4-hybrid-predictive") -> ExperimentResult:
    return ExperimentResult(
        scenario=scenario,
        run_id=1,
        timestamp="2026-07-12T00:00:00",
    )


class TestS4FullDelivery:
    """S4 with full prediction delivery passes the gate."""

    def test_s4_full_delivery_passes(self):
        out = evaluate_run_validity(
            _make_result(),
            scenario="s4-hybrid-predictive",
            preflight_passed=True,
            daemon_status={
                "prediction_eligible_cycles": 10,
                "prediction_delivery_failures": 0,
            },
        )
        tf = out.treatment_fidelity
        assert tf is not None
        assert tf.required is True
        assert tf.delivered is True
        assert tf.eligible_cycles == 10
        assert tf.successful_predictions == 10
        assert tf.failed_predictions == 0
        assert tf.delivery_rate == 1.0
        assert out.run_validity_passed is True
        assert out.validity_gate_passed is True


class TestS4PreflightFailure:
    """A failed GRU health preflight invalidates the run before any workload."""

    def test_s4_preflight_fails(self):
        out = evaluate_run_validity(
            _make_result(),
            scenario="s4-hybrid-predictive",
            preflight_passed=False,
            daemon_status={"prediction_eligible_cycles": 0, "prediction_delivery_failures": 0},
        )
        tf = out.treatment_fidelity
        assert tf is not None
        assert tf.delivered is False
        assert tf.preflight_passed is False
        assert out.run_validity_passed is False
        assert out.validity_gate_passed is False
        assert any("preflight" in r for r in tf.reasons)


class TestS4ZeroEligible:
    """No prediction-eligible cycles means the treatment was never exercised."""

    def test_s4_zero_eligible(self):
        out = evaluate_run_validity(
            _make_result(),
            scenario="s4-hybrid-predictive",
            preflight_passed=True,
            daemon_status={"prediction_eligible_cycles": 0, "prediction_delivery_failures": 0},
        )
        tf = out.treatment_fidelity
        assert tf is not None
        assert tf.delivered is False
        assert tf.delivery_rate == 0.0
        assert any("no prediction-eligible cycles" in r for r in tf.reasons)
        assert out.run_validity_passed is False


class TestS4PartialDelivery:
    """Partial delivery (some eligible cycles failed) is not full treatment."""

    def test_s4_partial_delivery(self):
        out = evaluate_run_validity(
            _make_result(),
            scenario="s4-hybrid-predictive",
            preflight_passed=True,
            daemon_status={
                "prediction_eligible_cycles": 10,
                "prediction_delivery_failures": 2,
            },
        )
        tf = out.treatment_fidelity
        assert tf is not None
        assert tf.delivered is False
        assert tf.eligible_cycles == 10
        assert tf.successful_predictions == 8
        assert tf.failed_predictions == 2
        assert tf.delivery_rate == 0.8
        assert any("delivery failures" in r for r in tf.reasons)
        assert out.run_validity_passed is False


class TestS3Unaffected:
    """S3 (reactive) has no prediction requirement and is left untouched."""

    def test_s3_unaffected(self):
        result = _make_result(scenario="s3-hybrid-reactive")
        result.run_validity_passed = True
        result.validity_gate_passed = True
        out = evaluate_run_validity(
            result,
            scenario="s3-hybrid-reactive",
            preflight_passed=True,
            daemon_status={
                "prediction_eligible_cycles": 99,
                "prediction_delivery_failures": 99,
            },
        )
        assert out.treatment_fidelity == TreatmentFidelity()
        assert out.run_validity_passed is True
        assert out.validity_gate_passed is True
