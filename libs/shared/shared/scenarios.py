"""Canonical scenario definitions.

Unifies the three duplicate Scenario/ScenarioConfig definitions from:
- controller/daemon/routing_daemon.py
- controller/experiments/runner/__main__.py
- scripts/run_phase_b_experiments.py
"""

from enum import Enum
from typing import Dict

from pydantic import BaseModel


class Scenario(str, Enum):
    """Experiment scenarios."""

    S1_K8S_ONLY = "s1-k8s-only"
    S2_SERVERLESS_ONLY = "s2-serverless-only"
    S3_HYBRID_REACTIVE = "s3-hybrid-reactive"
    S4_HYBRID_PREDICTIVE = "s4-hybrid-predictive"


class ScenarioConfig(BaseModel):
    """Configuration for each scenario."""

    name: str
    k3s_weight: int
    knative_weight: int
    use_algorithm: bool
    use_predictions: bool
    description: str


SCENARIO_CONFIGS: Dict[Scenario, ScenarioConfig] = {
    Scenario.S1_K8S_ONLY: ScenarioConfig(
        name="S1: K8s Only",
        k3s_weight=100,
        knative_weight=0,
        use_algorithm=False,
        use_predictions=False,
        description="Static routing to K8s cluster only",
    ),
    Scenario.S2_SERVERLESS_ONLY: ScenarioConfig(
        name="S2: Serverless Only",
        k3s_weight=0,
        knative_weight=100,
        use_algorithm=False,
        use_predictions=False,
        description="Static routing to serverless only",
    ),
    Scenario.S3_HYBRID_REACTIVE: ScenarioConfig(
        name="S3: Hybrid Reactive",
        k3s_weight=80,
        knative_weight=20,
        use_algorithm=True,
        use_predictions=False,
        description="Algorithm 1 reactive routing without predictions",
    ),
    Scenario.S4_HYBRID_PREDICTIVE: ScenarioConfig(
        name="S4: Hybrid Predictive",
        k3s_weight=80,
        knative_weight=20,
        use_algorithm=True,
        use_predictions=True,
        description="Algorithm 1 with GRU predictions (Algorithm 2)",
    ),
}


def get_scenario_config(scenario: Scenario) -> ScenarioConfig:
    """Get the configuration for a scenario."""
    return SCENARIO_CONFIGS[scenario]


def scenario_from_string(value: str) -> Scenario:
    """Parse a scenario from its string value."""
    for s in Scenario:
        if s.value == value:
            return s
    raise ValueError(f"Unknown scenario: {value}. Valid: {[s.value for s in Scenario]}")


# ---------------------------------------------------------------------------
# Display constants — single source of truth for labels, colors, ordering.
# Consumed by apps/dashboard (panels), apps/analysis (CLI plots), apps/experiment.
# Canonical format is "S1: K8s Only" (colon style); do not use the parenthesized
# "S1 (K8s-Only)" variant that appeared in older analysis scripts.
# ---------------------------------------------------------------------------
SCENARIO_ORDER: list[str] = [s.value for s in Scenario]

SCENARIO_LABELS: dict[str, str] = {
    "s1-k8s-only": "S1: K8s Only",
    "s2-serverless-only": "S2: Serverless Only",
    "s3-hybrid-reactive": "S3: Hybrid Reactive",
    "s4-hybrid-predictive": "S4: Hybrid Predictive",
}

SCENARIO_COLORS: dict[str, str] = {
    "s1-k8s-only": "#4C72B0",
    "s2-serverless-only": "#DD8452",
    "s3-hybrid-reactive": "#55A868",
    "s4-hybrid-predictive": "#C44E52",
}

SLO_THRESHOLD_MS: float = 200.0
