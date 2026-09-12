"""Controller selection: which Algorithm-1 controller a scenario runs.

The daemon used to decide this with an if/elif chain that read `CONTROLLER_VERSION`
twice and encoded the precedence in control flow, so adding a controller meant
editing the daemon and the precedence lived in two places. The rule is a table now,
and the table is the only place it lives.

Precedence, as the daemon has always applied it: V3 drives the hybrid scenarios when
asked for; V2 is the predictive-only variant; anything else runs V1. A version the
registry does not know falls back to V1 rather than failing a run at start-up.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from routing.algorithm.algorithm1_v1 import Algorithm1Config, Algorithm1Controller
from routing.algorithm.algorithm1_v2 import Algorithm1ConfigV2, Algorithm1ControllerV2
from routing.algorithm.algorithm1_v3 import Algorithm1ConfigV3, Algorithm1ControllerV3
from routing.monitoring.slo_monitor import SLOMonitor
from shared.models.calibration import get_calibration
from shared.scenarios import Scenario

AnyController = Algorithm1Controller | Algorithm1ControllerV2 | Algorithm1ControllerV3


@dataclass(frozen=True)
class ControllerDeps:
    """What every controller factory needs, resolved once by the daemon."""

    slo_monitor: SLOMonitor
    decision_interval: int
    default_k3s_weight: int
    default_knative_weight: int
    use_predictions: bool


ControllerFactory = Callable[[ControllerDeps], AnyController]


def _make_v1(deps: ControllerDeps) -> AnyController:
    return Algorithm1Controller(
        slo_monitor=deps.slo_monitor,
        config=Algorithm1Config(
            cooldown_sec=deps.decision_interval,
            default_k3s_weight=deps.default_k3s_weight,
            default_knative_weight=deps.default_knative_weight,
            load_change_threshold=0.15 if deps.use_predictions else 0.3,
        ),
    )


def _make_v2(deps: ControllerDeps) -> AnyController:
    return Algorithm1ControllerV2(
        slo_monitor=deps.slo_monitor,
        config=Algorithm1ConfigV2(
            cooldown_sec=deps.decision_interval,
            default_serverless_weight=deps.default_knative_weight,
        ),
    )


def _make_v3(deps: ControllerDeps) -> AnyController:
    return Algorithm1ControllerV3(
        slo_monitor=deps.slo_monitor,
        config=Algorithm1ConfigV3(
            cooldown_sec=deps.decision_interval,
            **get_calibration().to_v3_config_overrides(),
        ),
    )


CONTROLLER_REGISTRY: dict[str, ControllerFactory] = {
    "v1": _make_v1,
    "v2": _make_v2,
    "v3": _make_v3,
}

HYBRID_SCENARIOS = (Scenario.S3_HYBRID_REACTIVE, Scenario.S4_HYBRID_PREDICTIVE)


def select_controller(scenario: Scenario, version: str, deps: ControllerDeps) -> AnyController:
    """The controller this scenario runs, by the precedence the daemon always had.

    A version that applies to nothing — an unknown value, or v2 outside S4 — falls to
    V1, which is what the daemon's final ``else`` did and what keeps a typo in
    CONTROLLER_VERSION from stopping a run at start-up.
    """
    if version == "v3" and scenario in HYBRID_SCENARIOS:
        return CONTROLLER_REGISTRY["v3"](deps)
    if version == "v2" and scenario == Scenario.S4_HYBRID_PREDICTIVE:
        return CONTROLLER_REGISTRY["v2"](deps)
    return CONTROLLER_REGISTRY["v1"](deps)
