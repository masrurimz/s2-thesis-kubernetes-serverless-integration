"""Tests for prediction-delivery counters in RoutingDaemon._execute_decision_loop.

These counters are the load-bearing input to the S4 treatment-fidelity gate, so
we verify the eligible/failure accounting directly: a prediction-eligible cycle
(>=5 history samples) increments ``_prediction_eligible_cycles``; an unavailable
or failing prediction increments ``_prediction_delivery_failures``; short
history and non-predictive (S3) scenarios never count as eligible.
"""

from __future__ import annotations

from collections import deque
from unittest.mock import Mock


def _make_daemon(scenario: str):
    from routing.daemon.service import RoutingDaemon

    daemon = RoutingDaemon(scenario=scenario)
    # Stub heavy collaborators so the decision loop runs to completion.
    daemon.slo_monitor.check_slo = Mock(return_value=Mock(p99_latency_ms=100.0))
    daemon.k8s_scaler.get_deployment_status = Mock(return_value=None)
    daemon._execute_algorithm2 = Mock()  # bypass Algorithm 2 internals
    return daemon


def _maintain_decision(daemon):
    from routing.algorithm.algorithm1_v1 import RoutingDecision

    return RoutingDecision(
        weights=daemon.current_weights.copy(),
        reason="test",
        action="MAINTAIN",
        metrics={"p99": 100.0},
    )


def _wire_loop(daemon, *, history_len: int, model_seq_len: int = 5):
    daemon._load_history = deque([100.0] * history_len, maxlen=60)
    # The loop refreshes the history from Prometheus when it can reach it, which adds a
    # sample to the history this test sets exactly — and makes the result depend on
    # whether a live Prometheus is answering. It answered for the first time on
    # 2026-09-12 (the scrape config fed prom_rps at last), and this boundary case
    # flipped from 0 eligible cycles to 1 without a line of routing code changing.
    daemon._update_load_history = Mock()
    daemon.algorithm_controller.make_decision = Mock(return_value=_maintain_decision(daemon))
    # Bypass real model-status fetch; simulate a validated model.
    daemon._model_status_validated = True
    daemon._model_sequence_length = model_seq_len
    daemon._model_prediction_horizon = 5
    daemon._model_sample_interval_sec = 15


class TestPredictionDeliveryCounters:
    def test_s4_successful_prediction_counts_eligible(self):
        daemon = _make_daemon("s4-hybrid-predictive")
        _wire_loop(daemon, history_len=6)
        daemon.gru_client.check_availability = Mock(return_value=True)
        daemon.gru_client.predict = Mock(
            return_value=Mock(
                success=True,
                predicted_requests=100,
                confidence=0.9,
                point_forecasts=[1],
                upper_forecasts=[2],
            )
        )

        daemon._execute_decision_loop()

        assert daemon._prediction_eligible_cycles == 1
        assert daemon._prediction_delivery_failures == 0
        status = daemon.get_status()
        assert status["prediction_eligible_cycles"] == 1
        assert status["prediction_delivery_failures"] == 0

    def test_s4_unavailable_increments_failure(self):
        daemon = _make_daemon("s4-hybrid-predictive")
        _wire_loop(daemon, history_len=6)
        daemon.gru_client.check_availability = Mock(return_value=False)

        daemon._execute_decision_loop()

        assert daemon._prediction_eligible_cycles == 1
        assert daemon._prediction_delivery_failures == 1

    def test_s4_failed_prediction_increments_failure(self):
        daemon = _make_daemon("s4-hybrid-predictive")
        _wire_loop(daemon, history_len=6)
        daemon.gru_client.check_availability = Mock(return_value=True)
        daemon.gru_client.predict = Mock(return_value=Mock(success=False, error="boom"))

        daemon._execute_decision_loop()

        assert daemon._prediction_eligible_cycles == 1
        assert daemon._prediction_delivery_failures == 1

    def test_s4_short_history_not_eligible(self):
        daemon = _make_daemon("s4-hybrid-predictive")
        _wire_loop(daemon, history_len=3)  # < model_seq_len (5) → not eligible
        daemon.gru_client.check_availability = Mock(return_value=True)

        daemon._execute_decision_loop()

        assert daemon._prediction_eligible_cycles == 0
        assert daemon._prediction_delivery_failures == 0

    def test_s3_keeps_counters_zero(self):
        daemon = _make_daemon("s3-hybrid-reactive")
        _wire_loop(daemon, history_len=6)
        daemon.gru_client.check_availability = Mock(return_value=True)

        daemon._execute_decision_loop()

        assert daemon._prediction_eligible_cycles == 0
        assert daemon._prediction_delivery_failures == 0
        status = daemon.get_status()
        assert status["prediction_eligible_cycles"] == 0
        assert status["prediction_delivery_failures"] == 0

    def test_s4_below_model_sequence_length_not_eligible(self):
        """With a model requiring 30 input samples, 29 samples must not be eligible."""
        daemon = _make_daemon("s4-hybrid-predictive")
        _wire_loop(daemon, history_len=29, model_seq_len=30)
        daemon.gru_client.check_availability = Mock(return_value=True)

        daemon._execute_decision_loop()

        assert daemon._prediction_eligible_cycles == 0
        assert daemon._prediction_delivery_failures == 0

    def test_s4_at_model_sequence_length_eligible(self):
        """With 30 samples matching model sequence_length, prediction IS eligible."""
        daemon = _make_daemon("s4-hybrid-predictive")
        _wire_loop(daemon, history_len=30, model_seq_len=30)
        daemon.gru_client.check_availability = Mock(return_value=True)
        daemon.gru_client.predict = Mock(
            return_value=Mock(
                success=True,
                predicted_requests=100,
                confidence=0.9,
                point_forecasts=[1],
                upper_forecasts=[2],
            )
        )

        daemon._execute_decision_loop()

        assert daemon._prediction_eligible_cycles == 1
        assert daemon._prediction_delivery_failures == 0
