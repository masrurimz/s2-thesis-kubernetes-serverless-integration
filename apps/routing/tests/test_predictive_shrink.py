"""Predictive sizing levers.

Capacity-management literature reports that sizing from a forecast alone
over-provisions, and that asking for slightly less than the forecast while the
observed signal carries the correction does better. Two levers are covered: what
quantity sizes capacity, and a deliberate under-forecast on top of it. The tests
assert the capacity signal the controller sizes from, not the flags.
"""

from __future__ import annotations

from collections import deque
from unittest.mock import Mock

import pytest


def _daemon(monkeypatch, scenario: str, **env):
    monkeypatch.setenv("CONTROLLER_VERSION", "v3")
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    from routing.daemon.service import RoutingDaemon

    daemon = RoutingDaemon(scenario=scenario)
    daemon.k8s_scaler = Mock()
    daemon.k8s_scaler.get_deployment_status = Mock(return_value=Mock(spec_replicas=3, available_replicas=3))
    signals: list[float] = []
    daemon.cluster_controller = Mock()
    daemon.cluster_controller.compute_target_replicas = Mock(side_effect=lambda load: signals.append(load) or 3)
    daemon.cluster_controller.evaluate = Mock(return_value=Mock(action="MAINTAIN", target_replicas=3))
    return daemon, signals


def _run_algorithm2(daemon) -> None:
    daemon._execute_algorithm2(slo_status=Mock(p99_latency_ms=100.0), prediction=None, current_load=90.0)


def _drive_cycle(daemon) -> None:
    from routing.algorithm.algorithm1_v1 import RoutingDecision

    daemon._load_history = deque([100.0] * 10, maxlen=60)
    daemon._model_status_validated = True
    daemon._model_sequence_length = 5
    daemon._model_prediction_horizon = 9
    daemon._required_prediction_horizon_steps = Mock(return_value=3)
    daemon.gru_client.check_availability = Mock(return_value=True)
    daemon.gru_client.predict = Mock(
        return_value=Mock(
            success=True,
            predicted_requests=200.0,
            confidence=0.8,
            point_forecasts=[10.0, 20.0, 30.0, 40.0],
            upper_forecasts=[100.0, 110.0, 120.0, 130.0],
        )
    )
    daemon._execute_algorithm2 = Mock()
    daemon.slo_monitor.check_slo = Mock(return_value=Mock(p99_latency_ms=100.0))
    daemon.algorithm_controller.make_decision = Mock(
        return_value=RoutingDecision(
            weights=daemon.current_weights.copy(), reason="test", action="MAINTAIN", metrics={"p99": 100.0}
        )
    )
    daemon._execute_decision_loop()


@pytest.mark.parametrize("shrink", ["1.0", "0.5"])
def test_predictive_capacity_signal_is_scaled_by_the_lever(monkeypatch, shrink):
    daemon, signals = _daemon(monkeypatch, "s4-hybrid-predictive", ROUTING_PREDICTIVE_SHRINK=shrink)
    daemon._forecast_capacity_signal = 120.0
    daemon._model_status_ = None

    _run_algorithm2(daemon)

    assert signals[-1] == pytest.approx(120.0 * float(shrink))


def test_s3_never_reads_the_forecast(monkeypatch):
    daemon, signals = _daemon(monkeypatch, "s3-hybrid-reactive", ROUTING_PREDICTIVE_SHRINK="0.5")
    daemon._load_history.extend([90.0, 90.0])
    daemon._forecast_capacity_signal = 120.0

    _run_algorithm2(daemon)

    assert signals == [90.0]


def test_point_sizing_uses_the_central_forecast_at_the_provisioning_horizon(monkeypatch):
    daemon, _ = _daemon(monkeypatch, "s4-hybrid-predictive", ROUTING_SIZING_SIGNAL="point")

    _drive_cycle(daemon)

    assert daemon._forecast_capacity_signal == pytest.approx(30.0)


def test_upper_sizing_keeps_the_envelope_and_ignores_the_horizon_alignment(monkeypatch):
    daemon, _ = _daemon(monkeypatch, "s4-hybrid-predictive", ROUTING_SIZING_SIGNAL="upper")

    _drive_cycle(daemon)

    assert daemon._forecast_capacity_signal == pytest.approx(200.0)
