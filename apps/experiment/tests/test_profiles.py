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
