"""Provisioning models for node-level autoscaler contracts."""

from typing import Any

from pydantic import BaseModel, Field


class ProvisionEvent(BaseModel):
    """Single node provisioning lifecycle event."""

    timestamp: float
    event_type: (
        str  # "pending_detected" | "provision_delay_started" | "node_created" | "node_deleted" | "autoscaler_reset"
    )
    details: dict[str, Any] = Field(default_factory=dict)


class AutoscalerConfig(BaseModel):
    """Configuration for k3d node autoscaler — shared between CLI, adapter, and tests."""

    cluster_name: str = "thesis-hybrid"
    k3d_path: str = ""
    kubectl_path: str = ""
    k3s_image: str = "rancher/k3s:v1.28.5-k3s1"
    min_nodes: int = 0
    max_nodes: int = 2
    provision_delay_min_sec: int = 45
    provision_delay_max_sec: int = 120
    node_memory: str = "1g"
    namespace: str = "default"


class RunInvariantResult(BaseModel):
    """Pre-run state assertions for experiment reproducibility."""

    hpa_expected: bool
    hpa_actual: bool
    initial_k3s_weight: int
    initial_knative_weight: int
    dynamic_node_count: int
    baseline_replicas: int
    stale_pending_pods: int
    passed: bool
    notes: list[str] = Field(default_factory=list)
