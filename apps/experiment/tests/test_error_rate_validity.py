"""Request-failure reporting: ``error_rate`` must come from k6 ``http_req_failed``.

Regression guard for the 2026-09-11 invalid bundle: a run with 91% failed
requests recorded ``error_rate: 0.0`` because the extractor read the custom
``errors`` metric without its ``values`` nesting, and the validity gate never
consulted the request failure rate.
"""

from __future__ import annotations

import pytest
from experiment.stages.validate import evaluate_run_validity
from experiment.stages.workload import K6Summary
from shared.models.experiment import ExperimentResult


def _k6_summary(failed_rate: float) -> dict:
    """Synthetic k6 handleSummary payload shaped like the evidence bundle."""
    return {
        "metrics": {
            "http_req_failed": {
                "type": "rate",
                "contains": "default",
                "values": {"rate": failed_rate, "passes": 79983, "fails": 7857},
                "thresholds": {"rate<0.10": {"ok": failed_rate < 0.10}},
            },
            "errors": {
                "type": "rate",
                "contains": "default",
                "values": {"fails": 7856, "rate": failed_rate, "passes": 79983},
            },
            "http_reqs": {
                "type": "counter",
                "contains": "default",
                "values": {"count": 87840, "rate": 73.19},
            },
            "http_req_duration": {
                "type": "trend",
                "contains": "time",
                "values": {
                    "med": 0,
                    "max": 159.89,
                    "p(90)": 0,
                    "p(95)": 68.43,
                    "p(99)": 77.65,
                    "avg": 6.35,
                    "min": 0,
                },
            },
        }
    }


def _delivered_daemon() -> dict:
    """Daemon status with complete prediction delivery (fidelity alone passes)."""
    return {
        "prediction_eligible_cycles": 10,
        "prediction_delivery_failures": 0,
        "model_history_ready": True,
        "forecast_horizon_sufficient": True,
        "forecast_actionable_cycles": 3,
        "proactive_scaleups": 2,
    }


class TestErrorRateExtraction:
    def test_error_rate_comes_from_http_req_failed(self):
        summary = K6Summary.from_handle_summary(_k6_summary(0.91), "s4-hybrid-predictive", 1)
        assert summary.metrics.error_rate == pytest.approx(0.91)

    def test_the_tail_falls_back_to_p95_when_k6_omits_p99(self):
        """A summary without a tail number must not be read as a zero tail."""
        raw = _k6_summary(0.0)
        del raw["metrics"]["http_req_duration"]["values"]["p(99)"]

        summary = K6Summary.from_handle_summary(raw, "s3-hybrid-reactive", 2)

        assert summary.metrics.p99_latency_ms == pytest.approx(68.43)


class TestFailureRateValidityGate:
    def test_rejects_failure_rate_above_tolerance(self):
        result = ExperimentResult(scenario="s4-hybrid-predictive", run_id=1, error_rate=0.91)
        out = evaluate_run_validity(
            result,
            scenario="s4-hybrid-predictive",
            preflight_passed=True,
            daemon_status=_delivered_daemon(),
        )
        assert out.run_validity_passed is False
        assert out.validity_gate_passed is False
        assert any("failure rate" in note for note in out.run_validity_notes)

    def test_accepts_failure_rate_below_tolerance(self):
        result = ExperimentResult(scenario="s4-hybrid-predictive", run_id=1, error_rate=0.05)
        out = evaluate_run_validity(
            result,
            scenario="s4-hybrid-predictive",
            preflight_passed=True,
            daemon_status=_delivered_daemon(),
        )
        assert out.run_validity_passed is True
        assert out.run_validity_notes == []

    def test_rejects_failure_rate_at_tolerance_boundary(self):
        result = ExperimentResult(scenario="s4-hybrid-predictive", run_id=1, error_rate=0.10)
        out = evaluate_run_validity(
            result,
            scenario="s4-hybrid-predictive",
            preflight_passed=True,
            daemon_status=_delivered_daemon(),
        )
        assert out.run_validity_passed is False

    def test_rejects_non_predictive_failure_rate(self):
        result = ExperimentResult(scenario="s3-hybrid-reactive", run_id=1, error_rate=0.91)
        out = evaluate_run_validity(
            result,
            scenario="s3-hybrid-reactive",
            preflight_passed=True,
        )
        assert out.run_validity_passed is False
        assert any("failure rate" in note for note in out.run_validity_notes)
