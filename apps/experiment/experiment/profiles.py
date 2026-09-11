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
        }


_S3 = "s3-hybrid-reactive"
_S4 = "s4-hybrid-predictive"

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
    ),
    "quad": ExperimentProfile(
        name="quad",
        description="All four arms, same protocol, for a full comparison.",
        scenarios=("s1-k8s-only", "s2-serverless-only", _S3, _S4),
        runs=5,
        k8s_agents=1,
        prediction_server=True,
    ),
    "smoke": ExperimentProfile(
        name="smoke",
        description="One S3/S4 pair, for checking the testbed before a long run.",
        scenarios=(_S3, _S4),
        pairs=1,
        k8s_agents=1,
        prediction_server=True,
    ),
}


def get_profile(name: str) -> ExperimentProfile:
    if name not in PROFILES:
        raise KeyError(f"unknown profile {name!r}; known: {', '.join(sorted(PROFILES))}")
    return PROFILES[name]


def profile_names() -> list[str]:
    return sorted(PROFILES)
