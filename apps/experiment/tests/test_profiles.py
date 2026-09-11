"""Profiles must stay runnable, not just descriptive."""

from __future__ import annotations

import pytest

from experiment.profiles import PROFILES, get_profile, profile_names


def test_every_profile_names_a_known_scenario():
    from shared.scenarios import Scenario

    known = {scenario.value for scenario in Scenario}
    for profile in PROFILES.values():
        assert set(profile.scenarios) <= known, profile.name


def test_no_profile_leaves_the_design_undefined():
    for profile in PROFILES.values():
        assert bool(profile.pairs) != bool(profile.runs), f"{profile.name} needs exactly one of pairs or runs"


def test_paired_profiles_are_the_two_hybrid_arms():
    for profile in PROFILES.values():
        if profile.pairs:
            assert set(profile.scenarios) == {"s3-hybrid-reactive", "s4-hybrid-predictive"}, profile.name


def test_profiles_that_run_s4_serve_a_predictor():
    for profile in PROFILES.values():
        if any(scenario.startswith("s4") for scenario in profile.scenarios):
            assert profile.prediction_server, profile.name


def test_routing_env_only_uses_levers_the_daemon_reads():
    known = {"ROUTING_SIZING_SIGNAL", "ROUTING_PREDICTIVE_SHRINK"}
    for profile in PROFILES.values():
        assert set(profile.routing_env) <= known, profile.name


def test_unknown_profile_lists_the_known_ones():
    with pytest.raises(KeyError) as excinfo:
        get_profile("nope")
    assert "h2-pair" in str(excinfo.value)


def test_profile_names_are_sorted_and_complete():
    assert profile_names() == sorted(PROFILES)


def test_a_profile_declares_the_conditions_its_scenarios_need():
    """A profile is a claim about the testbed, and the tooling acts on it.

    A hybrid profile that leaves the agent count at zero cannot provision a node,
    and a predictive profile without a prediction server cannot deliver its
    treatment: both would produce runs that look complete and measure nothing.
    """
    from experiment.conditions import RunConditions

    for profile in PROFILES.values():
        conditions = RunConditions.for_scenarios(profile.scenarios, agents=profile.k8s_agents)
        assert conditions.needs_prediction_server == profile.prediction_server, profile.name
        if any("s3" in s or "s4" in s for s in profile.scenarios):
            assert profile.k8s_agents >= 1, f"{profile.name} needs a node autoscaler to have capacity to bind"
        if all("s2" in s for s in profile.scenarios):
            assert profile.k8s_agents == 0, f"{profile.name} runs no node autoscaler"


def test_the_baseline_profile_keeps_a_static_agent():
    """S1 provisions nodes at one agent, which is what makes it the reactive reference."""
    baselines = get_profile("baselines")

    assert baselines.k8s_agents == 1
    assert baselines.prediction_server is False
