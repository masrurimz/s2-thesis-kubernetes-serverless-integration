"""Provisioning models for node-level autoscaler contracts."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProvisionEvent(BaseModel):
    """Single node provisioning lifecycle event, named as it is persisted.

    The wire shape is ``{"ts", "event", "data"}``; the field names match it so the
    loader and the writer need no aliases to agree with the file. ``event`` is one of
    ``autoscaler_started``, ``pending_detected``, ``provision_delay_started``,
    ``node_created``, ``node_resource_applied``, ``scale_down_detected``,
    ``node_deleted``, ``autoscaler_reset``, ``autoscaler_stopped``.
    """

    model_config = ConfigDict(extra="ignore")

    ts: float
    event: str
    data: dict[str, Any] = Field(default_factory=dict)


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
