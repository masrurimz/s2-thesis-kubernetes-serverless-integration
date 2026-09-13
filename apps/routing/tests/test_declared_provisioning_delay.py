"""Declared provisioning delay sizes the forecast lead.

The 2026-09-12 S4 batch recorded zero actionable forecast cycles in every run:
the horizon sized itself to the pod-readiness EWMA instead of the node VM boot
the prediction must cover, so the predictive target never exceeded the observed
one. A declared ROUTING_PROVISIONING_DELAY_SEC pins the lead to the testbed's
boot cost; unset keeps the adaptive EWMA path exactly as before.
"""

from __future__ import annotations

import math
import time
from unittest.mock import Mock

import pytest


def _daemon(monkeypatch, **env):
    monkeypatch.setenv("CONTROLLER_VERSION", "v3")
    monkeypatch.delenv("ROUTING_PROVISIONING_DELAY_SEC", raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    from routing.daemon.service import RoutingDaemon

    daemon = RoutingDaemon(scenario="s4-hybrid-predictive")
    monkeypatch.setattr(daemon.gru_client, "check_availability", Mock(return_value=True))
    return daemon


@pytest.mark.parametrize(
    ("declared_sec", "expected_steps"),
    [("120", 9), ("60", 5)],
)
def test_declared_delay_sizes_the_horizon(monkeypatch, declared_sec, expected_steps):
    daemon = _daemon(monkeypatch, ROUTING_PROVISIONING_DELAY_SEC=declared_sec)
    assert daemon._required_prediction_horizon_steps() == expected_steps


def test_declared_delay_survives_pod_readiness(monkeypatch):
    """Pod readiness must not move the horizon of a declared run."""
    daemon = _daemon(monkeypatch, ROUTING_PROVISIONING_DELAY_SEC="120")
    daemon._pending_scale_target = 4
    daemon._pending_scale_issue_time = time.monotonic() - 100.0
    daemon._check_scale_readiness(Mock(available_replicas=4))
    assert daemon._provisioning_delay_samples == 0
    assert daemon._required_prediction_horizon_steps() == 9


def test_unset_delay_keeps_the_adaptive_ewma(monkeypatch):
    daemon = _daemon(monkeypatch)
    # Calibration seed: 60 s delay + 15 s safety over 15 s samples.
    assert daemon._required_prediction_horizon_steps() == 5

    daemon._pending_scale_target = 4
    daemon._pending_scale_issue_time = time.monotonic() - 100.0
    daemon._check_scale_readiness(Mock(available_replicas=4))
    assert daemon._provisioning_delay_samples == 1
    moved = daemon._provisioning_delay_ewma
    assert moved != pytest.approx(60.0)
    expected = math.ceil((moved + daemon._provisioning_delay_safety_sec) / daemon._model_sample_interval_sec)
    assert daemon._required_prediction_horizon_steps() == expected
    # The pending measurement is consumed either way.
    assert daemon._pending_scale_target is None


def test_status_reports_which_delay_sized_the_horizon(monkeypatch):
    declared = _daemon(monkeypatch, ROUTING_PROVISIONING_DELAY_SEC="120")
    status = declared.get_status()
    assert status["provisioning_delay_source"] == "declared"
    assert status["provisioning_delay_estimate_sec"] == 120.0

    adaptive = _daemon(monkeypatch)
    status = adaptive.get_status()
    assert status["provisioning_delay_source"] == "ewma"
    assert status["provisioning_delay_estimate_sec"] == 60.0
