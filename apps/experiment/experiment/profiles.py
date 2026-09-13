"""Experiment profiles: the testbed state and controller settings a run needs.

An experiment is only repeatable if the conditions it ran under are part of the
specification. Two runs of the same scenarios differ in result if the cluster
carried a spare node that absorbed the ramp, or if the prediction server was
absent. A profile names those conditions so a command can converge to them and a
bundle can record them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from shared.models.calibration import CalibrationConfig


@dataclass(frozen=True)
class ExperimentProfile:
    """Conditions an experiment runs under."""

    name: str
    description: str
    scenarios: tuple[str, ...]
    pairs: int = 0
    runs: int = 0
    k8s_agents: int = 1
    prediction_server: bool = False
    routing_env: Mapping[str, str] = field(default_factory=dict)
    # The simulated VM boot delay, one value per pair: pair i uses seq[i % len(seq)],
    # applied to every provisioning in BOTH arms of that pair. The delay belongs to
    # the testbed, not the treatment; randomising it across the two arms of a pair
    # adds a confound that no amount of counterbalancing removes. Matching it within
    # a pair keeps realism (it still varies run to run) and removes the confound.
    # Empty means legacy behaviour: the autoscaler's own random range.
    provision_delay_seq: tuple[int, ...] = ()
    # The capacity contract the run is only valid under. The July and September
    # batches measured different systems (pod CPU request 200m -> 300m, replica cap
    # 6 -> 10, static agents) with nothing in the bundle declaring it; these values
    # are checked against the live testbed before a run starts. Empty means no
    # contract declared.
    capacity: Mapping[str, float | int | str] = field(default_factory=dict)
    # The calibration overlay the run resolves through CALIBRATION_OVERRIDE, so
    # both arms of a pair and the spawned daemon see the same numbers (e.g.
    # max_k8s_replicas). Empty means code defaults.
    calibration_path: str = ""
    # Pre-registered endpoints, so the analysis cannot shop for a metric after
    # the runs are in.
    endpoints: Mapping[str, str] = field(default_factory=dict)
    alpha: float = 0.05
    design: str = "counterbalanced-pairs"

    def provision_delay_for_pair(self, pair_index: int) -> int | None:
        """The boot delay pair `pair_index` (0-based) runs with, or None for legacy randomness."""
        if not self.provision_delay_seq:
            return None
        return self.provision_delay_seq[pair_index % len(self.provision_delay_seq)]

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "scenarios": list(self.scenarios),
            "pairs": self.pairs,
            "runs": self.runs,
            "k8s_agents": self.k8s_agents,
            "prediction_server": self.prediction_server,
            "routing_env": dict(self.routing_env),
            "provision_delay_seq": list(self.provision_delay_seq),
            "capacity": dict(self.capacity),
            "calibration_path": self.calibration_path,
            "endpoints": dict(self.endpoints),
            "alpha": self.alpha,
            "design": self.design,
        }


_S3 = "s3-hybrid-reactive"
_S4 = "s4-hybrid-predictive"

# Simulated VM boot delays covering the modelled 45..120 s range, one per pair.
# Matched within a pair (see provision_delay_seq) so the paired difference never
# carries a boot-time confound; varied across pairs so realism survives.
_DELAY_SEQ = (60, 90, 120, 75, 45)

# The capacity contract the hybrid profiles run under, read from the deployed
# testbed: test-app-warm-deployment.yaml (pod_cpu_request 300m), hpa.yaml
# (maxReplicas 10), and the 1.0-CPU agent containers the k3d manager pins.
_CAPACITY = {
    "pod_cpu_request": "300m",
    "max_k8s_replicas": 10,
    "node_cpus": 1.0,
    "k8s_agents": 1,
}

_ENDPOINTS = {
    "primary": "p99_latency_ms",
    "co_primary": "ramp_p99_ms",
    "mechanism": "ramp_serverless_share",
}

PROFILES: dict[str, ExperimentProfile] = {
    "h2-pair": ExperimentProfile(
        name="h2-pair",
        description=(
            "Counterbalanced S3/S4 pairs with one static agent node, so node provisioning "
            "is in the path. This is the regime H2 was written for."
        ),
        scenarios=(_S3, _S4),
        pairs=5,
        k8s_agents=1,
        prediction_server=True,
        routing_env={"ROUTING_PREDICTIVE_SHRINK": "1.0", "ROUTING_SIZING_SIGNAL": "upper"},
        provision_delay_seq=_DELAY_SEQ,
        calibration_path="results/calibration/2026-08-06_definitive-repro.json",
        capacity=_CAPACITY,
        endpoints=_ENDPOINTS,
    ),
    "h2-pair-tight": ExperimentProfile(
        name="h2-pair-tight",
        description=(
            "A six-replica ceiling, declared to make the forecast exceed capacity more "
            "often than the ten-replica paired design does. Measured on 2026-09-13 "
            "(2026-09-13_h2-pair-tight-5p), the premise was inverted: six replicas at "
            "33.3 RPS each is 199.8 RPS and the replayed ClarkNet trace peaks at 164, so "
            "no stage saturates the ceiling, no forecast can exceed it, and the "
            "predictive arm produced 0 actionable cycles in 57 eligible ones against 3 "
            "to 5 at the ten-replica ceiling. S4's p99 came out 1885 to 4694 ms against "
            "1151 to 1573 for S3, 4x the cap-10 runs. The sizing law is why: the "
            "threshold for a proactive scale-up is the reactively-required target, which "
            "with alpha 0.0601 is about 16.65 RPS per replica, so a tighter ceiling "
            "lowers that threshold and can only reduce the forecast's headroom. Kept as "
            "the regression case the capacity-headroom refusal in experiment.conditions "
            "is written against; it cannot run, and that is the point. Use h2-pair."
        ),
        scenarios=(_S3, _S4),
        pairs=5,
        k8s_agents=1,
        prediction_server=True,
        routing_env={"ROUTING_PREDICTIVE_SHRINK": "1.0", "ROUTING_SIZING_SIGNAL": "upper"},
        provision_delay_seq=_DELAY_SEQ,
        calibration_path="results/calibration/2026-09-13_cap6-tight.json",
        capacity={**_CAPACITY, "max_k8s_replicas": 6},
        endpoints=_ENDPOINTS,
    ),
    "h2-pair-abundant": ExperimentProfile(
        name="h2-pair-abundant",
        description=(
            "Counterbalanced S3/S4 pairs with two static agent nodes. The node autoscaler "
            "does not fire, so the reactive arm pays no provisioning penalty."
        ),
        scenarios=(_S3, _S4),
        pairs=5,
        k8s_agents=2,
        prediction_server=True,
        routing_env={"ROUTING_PREDICTIVE_SHRINK": "1.0", "ROUTING_SIZING_SIGNAL": "upper"},
        provision_delay_seq=_DELAY_SEQ,
        capacity={**_CAPACITY, "k8s_agents": 2},
        endpoints=_ENDPOINTS,
    ),
    "h2-confirmatory": ExperimentProfile(
        name="h2-confirmatory",
        description=(
            "The pre-registered confirmatory H2 batch: ten counterbalanced S3/S4 pairs, one static "
            "agent, the declared forecast lead and the matched boot delay. Ten pairs resolve a "
            "difference near 43 ms at 80 percent power if the paired spread stays near July's 50 ms."
        ),
        scenarios=(_S3, _S4),
        pairs=10,
        k8s_agents=1,
        prediction_server=True,
        routing_env={"ROUTING_PREDICTIVE_SHRINK": "1.0", "ROUTING_SIZING_SIGNAL": "upper"},
        provision_delay_seq=_DELAY_SEQ,
        calibration_path="results/calibration/2026-08-06_definitive-repro.json",
        capacity=_CAPACITY,
        endpoints=_ENDPOINTS,
    ),
    "s4-point-sizing": ExperimentProfile(
        name="s4-point-sizing",
        description="S4 alone, sizing capacity from the central forecast instead of the upper envelope.",
        scenarios=(_S4,),
        runs=3,
        k8s_agents=1,
        prediction_server=True,
        routing_env={"ROUTING_SIZING_SIGNAL": "point"},
    ),
    "s4-point-sizing-shrink": ExperimentProfile(
        name="s4-point-sizing-shrink",
        description="S4 alone, central-forecast sizing with a deliberate under-forecast on top.",
        scenarios=(_S4,),
        runs=3,
        k8s_agents=1,
        prediction_server=True,
        routing_env={"ROUTING_SIZING_SIGNAL": "point", "ROUTING_PREDICTIVE_SHRINK": "0.85"},
    ),
    "baselines": ExperimentProfile(
        name="baselines",
        description="Pure Kubernetes and pure serverless arms, for the H1 comparison.",
        scenarios=("s1-k8s-only", "s2-serverless-only"),
        runs=5,
        k8s_agents=1,
        calibration_path="results/calibration/2026-08-06_definitive-repro.json",
        capacity=_CAPACITY,
    ),
    "h1-parity": ExperimentProfile(
        name="h1-parity",
        description=(
            "H1 with capacity parity: pure Kubernetes and hybrid-predictive arms share one "
            "calibration, so both may grow to the same replica cap and the same node tier. The "
            "difference between the arms is then the routing and scaling policy, not the envelope."
        ),
        scenarios=("s1-k8s-only", _S4),
        pairs=5,
        k8s_agents=1,
        prediction_server=True,
        routing_env={"ROUTING_PREDICTIVE_SHRINK": "1.0", "ROUTING_SIZING_SIGNAL": "upper"},
        provision_delay_seq=_DELAY_SEQ,
        calibration_path="results/calibration/2026-08-06_definitive-repro.json",
        capacity=_CAPACITY,
        endpoints={"primary": "p99_latency_ms", "co_primary": "ramp_p99_ms", "mechanism": "dynamic_nodes"},
    ),
    "quad": ExperimentProfile(
        name="quad",
        description="All four arms, same protocol, for a full comparison.",
        scenarios=("s1-k8s-only", "s2-serverless-only", _S3, _S4),
        runs=5,
        k8s_agents=1,
        prediction_server=True,
        calibration_path="results/calibration/2026-08-06_definitive-repro.json",
        capacity=_CAPACITY,
    ),
    "smoke": ExperimentProfile(
        name="smoke",
        description="One S3/S4 pair, for checking the testbed before a long run.",
        scenarios=(_S3, _S4),
        pairs=1,
        k8s_agents=1,
        prediction_server=True,
        routing_env={"ROUTING_PREDICTIVE_SHRINK": "1.0", "ROUTING_SIZING_SIGNAL": "upper"},
        provision_delay_seq=_DELAY_SEQ,
        calibration_path="results/calibration/2026-08-06_definitive-repro.json",
        capacity=_CAPACITY,
        endpoints=_ENDPOINTS,
    ),
}


def check_calibration_agrees_with_capacity(profile: ExperimentProfile) -> None:
    """A declared replica cap must match the calibration the run will resolve.

    The 2026-09-12 batch declared a capacity contract of max_k8s_replicas 10
    while the code default resolved 6, so both arms ran a tighter regime than
    the bundle claimed. The profile's calibration (or the defaults, when no
    path is declared) must resolve the same cap the contract states.
    """
    if "max_k8s_replicas" not in profile.capacity:
        return
    calibration = CalibrationConfig.load(profile.calibration_path) if profile.calibration_path else CalibrationConfig()
    declared = int(profile.capacity["max_k8s_replicas"])
    resolved = calibration.max_k8s_replicas
    if declared != resolved:
        source = f"calibration at {profile.calibration_path}" if profile.calibration_path else "code defaults"
        raise ValueError(
            f"{profile.name} declares max_k8s_replicas={declared} but the {source} resolve "
            f"{resolved}; declare a calibration_path whose cap matches the contract"
        )


def get_profile(name: str) -> ExperimentProfile:
    if name not in PROFILES:
        raise KeyError(f"unknown profile {name!r}; known: {', '.join(sorted(PROFILES))}")
    return PROFILES[name]


def profile_names() -> list[str]:
    return sorted(PROFILES)
