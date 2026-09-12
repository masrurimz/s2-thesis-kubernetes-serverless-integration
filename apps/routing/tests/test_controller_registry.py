"""Controller selection: the precedence the daemon always had, in one table.

The matrix is the contract. It was read off the if/elif chain the daemon used
before the registry existed, so a change here that the daemon did not ask for is a
behaviour change, not a refactor.
"""

import pytest

from routing.algorithm.algorithm1_v1 import Algorithm1Controller
from routing.algorithm.algorithm1_v2 import Algorithm1ControllerV2
from routing.algorithm.algorithm1_v3 import Algorithm1ControllerV3
from routing.algorithm.registry import CONTROLLER_REGISTRY, ControllerDeps, select_controller
from routing.monitoring.slo_monitor import SLOMonitor, SLOConfig
from shared.scenarios import Scenario


@pytest.fixture
def deps() -> ControllerDeps:
    return ControllerDeps(
        slo_monitor=SLOMonitor(config=SLOConfig(prometheus_url="http://localhost:9090")),
        decision_interval=15,
        default_k3s_weight=80,
        default_knative_weight=20,
        use_predictions=True,
    )


@pytest.mark.parametrize(
    ("scenario", "version", "expected"),
    [
        (Scenario.S3_HYBRID_REACTIVE, "v3", Algorithm1ControllerV3),
        (Scenario.S4_HYBRID_PREDICTIVE, "v3", Algorithm1ControllerV3),
        (Scenario.S4_HYBRID_PREDICTIVE, "v2", Algorithm1ControllerV2),
        # V3 is the hybrid controller: outside those scenarios the request falls to V1.
        (Scenario.S1_K8S_ONLY, "v3", Algorithm1Controller),
        (Scenario.S2_SERVERLESS_ONLY, "v3", Algorithm1Controller),
        (Scenario.S1_K8S_ONLY, "v1", Algorithm1Controller),
        (Scenario.S3_HYBRID_REACTIVE, "v1", Algorithm1Controller),
        # The predictive variant is S4's; anywhere else it does not apply.
        (Scenario.S3_HYBRID_REACTIVE, "v2", Algorithm1Controller),
        (Scenario.S1_K8S_ONLY, "v2", Algorithm1Controller),
    ],
)
def test_selection_matrix(deps, scenario, version, expected):
    assert isinstance(select_controller(scenario, version, deps), expected)


def test_unknown_version_runs_the_default_controller(deps):
    """A typo in CONTROLLER_VERSION must not stop a run at start-up."""
    assert isinstance(select_controller(Scenario.S3_HYBRID_REACTIVE, "v9", deps), Algorithm1Controller)


def test_registry_holds_a_factory_for_every_known_version(deps):
    assert set(CONTROLLER_REGISTRY) == {"v1", "v2", "v3"}
    for name, factory in CONTROLLER_REGISTRY.items():
        assert factory(deps) is not None, name


def test_deps_are_immutable(deps):
    with pytest.raises(Exception):
        deps.decision_interval = 30  # type: ignore[misc]
