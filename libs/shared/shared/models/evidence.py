"""Canonical evidence DTOs for experiment lifecycle, treatment fidelity, and registry.

These models are shared across the experiment runner, analysis pipeline, and
evidence registry/catalog — never embedded in a CLI or script.
"""

from datetime import date, datetime
from collections.abc import Sequence
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer


class TreatmentFidelity(BaseModel):
    """Whether the experimental treatment (GRU prediction service) was actually delivered.

    Defaults describe a non-prediction scenario (S1-S3) where no treatment is required.
    For S4 (predictive), the runner populates counters and delivery_rate from the daemon.
    """

    required: bool = False
    preflight_passed: bool = True
    eligible_cycles: int = 0
    successful_predictions: int = 0
    failed_predictions: int = 0
    delivery_rate: float = 1.0
    delivered: bool = True
    # Actuator-fidelity fields (S4 only): ensure the forecast actually reached
    # the scale actuator with sufficient history and horizon.
    model_history_ready: bool = False
    forecast_horizon_sufficient: bool = False
    forecast_actionable_cycles: int = 0
    proactive_scaleups: int = 0
    reasons: list[str] = Field(default_factory=list)


class NodeEngagement(BaseModel):
    """Whether the node tier — the capacity the hybrid design exists to add — was exercised.

    S1, S3, and S4 all run the node autoscaler, so the node tier is part of what they
    claim to measure. When no pod ever goes pending, no node is provisioned, the
    reactive arm pays no provisioning penalty, and prediction has nothing to warm:
    the run then measures the pod tier alone and cannot support a claim about the
    node tier. Defaults describe S2, which has no node autoscaler.
    """

    required: bool = False
    autoscaler_engaged: bool = False
    pending_events: int = 0
    nodes_provisioned: int = 0
    first_provision_delay_sec: float = 0.0
    reasons: list[str] = Field(default_factory=list)

    @staticmethod
    def scenario_has_node_autoscaler(scenario: str) -> bool:
        """True when the scenario runs the node autoscaler (S1, S3, S4 — not S2)."""
        s = scenario.lower()
        return not ("s2" in s or "serverless-only" in s)

    @classmethod
    def from_provision_events(
        cls,
        scenario: str,
        events: Sequence[str],
        *,
        nodes_provisioned: int,
        first_provision_delay_sec: float = 0.0,
    ) -> "NodeEngagement":
        """Derive engagement from a run's provisioner event stream.

        The single place the rule lives, so a course of runs and a bundle read back
        from disk classify identically.
        """
        pending = sum(1 for event in events if event == "pending_detected")
        required = cls.scenario_has_node_autoscaler(scenario)
        engaged = pending > 0 or nodes_provisioned > 0
        reasons = []
        if required and not engaged:
            reasons.append(
                f"node tier not exercised: {len(events)} provisioner events, no pending pod and no node provisioned"
            )
        return cls(
            required=required,
            autoscaler_engaged=engaged,
            pending_events=pending,
            nodes_provisioned=nodes_provisioned,
            first_provision_delay_sec=first_provision_delay_sec,
            reasons=reasons,
        )


JournalEventName = Literal[
    "bundle_created",
    "run_started",
    "reset_completed",
    "daemon_started",
    "prediction_preflight_passed",
    "prediction_preflight_failed",
    "warmup_completed",
    "workload_completed",
    "collection_completed",
    "validity_evaluated",
    "run_conditioned",
    "run_refused",
    "run_completed",
    "run_failed",
    "stack_rebuilt",
    "pair_excluded",
    "profile_applied",
    "bundle_registered",
    "legacy_backfilled",
    "bundle_promoted",
    "bundle_invalidated",
    "registry_audited",
]


class ExperimentJournalEvent(BaseModel):
    """A single append-only lifecycle event in an experiment's events.jsonl."""

    schema_version: int = 1
    event_id: UUID
    timestamp: datetime
    event: JournalEventName
    experiment_id: str
    bundle_path: str
    scenario: str | None = None
    run_id: int | None = None
    pair_id: str | None = None
    git_commit: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_serializer("event_id")
    def _serialize_event_id(self, value: UUID) -> str:
        return str(value)

    @field_serializer("timestamp")
    def _serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


class ExperimentRegistryEntry(BaseModel):
    """A single experiment bundle entry in the evidence registry."""

    id: str
    root: str
    path: str
    date: date
    role: Literal["diagnostic", "intermediate", "final", "superseded"]
    status: Literal["current", "invalidated", "archived"]
    scenarios: list[str]
    n_runs_total: int
    n_runs_valid: int
    treatment_fidelity: TreatmentFidelity | None = None
    has_meta: bool
    has_report: bool
    has_paired_analysis: bool
    git_commits: list[str] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)
    results: dict[str, Any] = Field(default_factory=dict)
    claims_supported: list[str] = Field(default_factory=list)
    supersedes: list[str] = Field(default_factory=list)
    superseded_by: str | None = None
    notes: str = ""
