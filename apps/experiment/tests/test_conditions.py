"""Tests for the run-conditions gate.

Every entry point that runs an experiment goes through this gate, so it has to be
right in both directions: refuse when the testbed or the host is not in a state
where the run would mean anything, and say which check failed when it does.
"""

from __future__ import annotations

import pytest
from experiment import conditions as conditions_module
from experiment.conditions import ConditionsUnmet, RunConditions, apply

CLEAN_TESTBED = {
    "cluster": "thesis-hybrid",
    "changed": False,
    "actions": [],
    "nodes": {"servers": 1, "agents": 1, "dynamic_agents": 0},
    "haproxy": True,
    "prometheus": True,
}


def _patch(monkeypatch, *, testbed=None, nodes_ready=True, endpoints=(True, True), load_ratio=0.2, port_open=True):
    from experiment.stages import daemon as daemon_stage
    from infra import readiness as readiness_module

    monkeypatch.setattr(readiness_module, "ensure_testbed", lambda **kw: testbed or dict(CLEAN_TESTBED))
    monkeypatch.setattr(readiness_module, "cluster_nodes_ready", lambda cluster: nodes_ready)
    monkeypatch.setattr(readiness_module, "app_endpoints_serving", lambda: endpoints)
    monkeypatch.setattr(daemon_stage, "is_port_listening", lambda port: port_open)
    monkeypatch.setattr(
        conditions_module,
        "_host_load",
        lambda **kwargs: {"load1": load_ratio * 16, "cores": 16.0, "ratio": load_ratio, "loadavg_ratio": load_ratio},
    )


def test_for_scenarios_derives_the_conditions_each_design_needs():
    paired = RunConditions.for_scenarios(["s3-hybrid-reactive", "s4-hybrid-predictive"], agents=1)
    serverless_only = RunConditions.for_scenarios(["s2-serverless-only"], agents=1)
    pure_k8s = RunConditions.for_scenarios(["s1-k8s-only"], agents=1)

    assert paired.needs_prediction_server is True
    assert paired.agents == 1
    # S2 has no node autoscaler, so there is no static agent count to converge.
    assert serverless_only.needs_prediction_server is False
    assert serverless_only.agents == 0
    assert pure_k8s.needs_prediction_server is False
    assert pure_k8s.agents == 1


def test_passes_and_reports_when_every_condition_holds(monkeypatch):
    _patch(monkeypatch)

    report = apply(RunConditions(agents=1), scenario="s4-hybrid-predictive")

    assert report["ok"] is True
    assert all(report["checks"].values())
    assert report["nodes"]["agents"] == 1
    assert report["load"]["cores"] == 16.0


def test_refuses_when_the_node_tier_was_not_converged(monkeypatch):
    _patch(monkeypatch, testbed={**CLEAN_TESTBED, "haproxy": False})

    with pytest.raises(ConditionsUnmet) as excinfo:
        apply(RunConditions(agents=1), scenario="s3-hybrid-reactive")

    assert "haproxy_up" in str(excinfo.value)


def test_refuses_on_an_oversubscribed_host_and_names_the_culprits(monkeypatch):
    _patch(monkeypatch, load_ratio=1.4)
    monkeypatch.setattr(conditions_module, "_busiest_processes", lambda limit=3: ["465.0 omp", "143.0 thesis"])

    with pytest.raises(ConditionsUnmet) as excinfo:
        apply(RunConditions(agents=1), scenario="s4-hybrid-predictive")

    message = str(excinfo.value)
    assert "host_load" in message
    assert "omp" in message


def test_the_host_is_measured_but_not_enforced_when_the_caller_says_so(monkeypatch):
    _patch(monkeypatch, load_ratio=1.4)

    report = apply(RunConditions(agents=1, check_host_load=False), scenario="s4-hybrid-predictive")

    assert report["ok"] is True
    assert report["load"]["ratio"] == 1.4


def test_a_high_but_tolerable_load_is_recorded_as_a_note(monkeypatch):
    _patch(monkeypatch, load_ratio=0.7)

    report = apply(RunConditions(agents=1), scenario="s3-hybrid-reactive")

    assert report["ok"] is True
    assert any("busy on" in note for note in report["notes"])


def test_prediction_scenarios_require_a_listener_on_the_prediction_port(monkeypatch):
    _patch(monkeypatch, port_open=False)

    with pytest.raises(ConditionsUnmet) as excinfo:
        apply(RunConditions(agents=1, needs_prediction_server=True), scenario="s4-hybrid-predictive")

    assert "prediction_port" in str(excinfo.value)


def test_serverless_only_runs_do_not_require_the_k8s_endpoint(monkeypatch):
    """S2 drains the K8s deployment on purpose; requiring it would refuse every S2 run."""
    _patch(monkeypatch, endpoints=(False, True))

    report = apply(RunConditions(agents=0), scenario="s2-serverless-only")

    assert report["ok"] is True
    assert "k8s_endpoint_serving" not in report["checks"]
