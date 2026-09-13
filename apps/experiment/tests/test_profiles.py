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


def test_paired_profiles_pair_two_arms_of_one_regime():
    """A paired profile compares two arms on one testbed, so it must declare both.

    H2 pairs the two hybrid arms. H1 pairs pure Kubernetes against the predictive
    hybrid at capacity parity, so the arms are not always the same scenarios. What
    every paired profile owes is two scenarios and a declared capacity contract,
    because a pair whose arms run different envelopes measures the envelope.
    """
    for profile in PROFILES.values():
        if profile.pairs:
            assert len(profile.scenarios) == 2, profile.name
            assert profile.capacity, profile.name


def test_profiles_that_run_s4_serve_a_predictor():
    for profile in PROFILES.values():
        if any(scenario.startswith("s4") for scenario in profile.scenarios):
            assert profile.prediction_server, profile.name


def test_routing_env_only_uses_levers_the_daemon_reads():
    known = {"ROUTING_SIZING_SIGNAL", "ROUTING_PREDICTIVE_SHRINK", "ROUTING_PROVISIONING_DELAY_SEC"}
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


def test_paired_hybrid_profiles_declare_capacity_and_delay_sequence():
    """The paired H2 design is only interpretable against a stated testbed.

    The July and September batches measured different systems (pod CPU request
    200m -> 300m, replica cap 6 -> 10, static agent count) with nothing in the
    bundle saying so, and the delay the autoscaler drew randomly inside each pair
    moved the p99 with it. A paired profile that declares no capacity contract
    can silently measure a different system again, and one without a delay
    sequence leaves that confound in place.
    """
    required_capacity = {"pod_cpu_request", "max_k8s_replicas", "node_cpus", "k8s_agents"}
    for profile in PROFILES.values():
        if not profile.pairs:
            continue
        assert required_capacity <= set(profile.capacity), (
            f"{profile.name} must declare the full capacity contract: {sorted(required_capacity)}"
        )
        assert profile.provision_delay_seq, f"{profile.name} must declare a per-pair provision delay sequence"
        assert all(45 <= delay <= 120 for delay in profile.provision_delay_seq), (
            f"{profile.name} declares a delay outside the modelled 45..120s VM boot range"
        )


def test_provision_delay_cycles_over_pair_indices():
    """Pair i uses seq[i % len(seq)]; both arms of a pair share the one delay."""
    profile = get_profile("h2-pair")
    seq = profile.provision_delay_seq

    first_cycle = [profile.provision_delay_for_pair(i) for i in range(len(seq))]
    second_cycle = [profile.provision_delay_for_pair(i) for i in range(len(seq), 2 * len(seq))]

    assert first_cycle == list(seq)
    assert second_cycle == list(seq)
    assert get_profile("baselines").provision_delay_for_pair(0) is None


def test_paired_predictive_profiles_pin_their_forecast_levers():
    """The treatment's strength belongs in the profile, not in daemon defaults.

    The 2026-09-12 batch declared no sizing levers, so the treatment ran on
    whatever the daemon's defaults were that day. A paired predictive profile
    must declare the shrink and the sizing signal it was designed around.
    """
    for profile in PROFILES.values():
        if not profile.pairs:
            continue
        assert profile.routing_env.get("ROUTING_PREDICTIVE_SHRINK") == "1.0", profile.name
        assert profile.routing_env.get("ROUTING_SIZING_SIGNAL") == "upper", profile.name


def test_a_declared_capacity_contract_must_match_the_resolved_calibration():
    """The contract and the calibration the run resolves must agree.

    A profile declaring max_k8s_replicas 10 with no calibration path resolves
    the code default 6, which is the silent regime change the 2026-09-12 batch
    measured. Such a profile must be refused, not run.
    """
    from dataclasses import replace

    from experiment.profiles import check_calibration_agrees_with_capacity

    uncalibrated = replace(get_profile("h2-pair"), calibration_path="")
    with pytest.raises(ValueError, match="max_k8s_replicas"):
        check_calibration_agrees_with_capacity(uncalibrated)

    check_calibration_agrees_with_capacity(get_profile("h2-pair"))
    check_calibration_agrees_with_capacity(get_profile("baselines"))
