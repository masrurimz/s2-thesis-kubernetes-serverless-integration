"""Canonical evidence DTOs for experiment lifecycle, treatment fidelity, and registry.

These models are shared across the experiment runner, analysis pipeline, and
evidence registry/catalog — never embedded in a CLI or script.
"""

from datetime import date, datetime
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
    reasons: list[str] = Field(default_factory=list)


JournalEventName = Literal[
    "run_started",
    "reset_completed",
    "daemon_started",
    "prediction_preflight_passed",
    "prediction_preflight_failed",
    "warmup_completed",
    "workload_completed",
    "collection_completed",
    "validity_evaluated",
    "run_completed",
    "run_failed",
    "pair_excluded",
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
