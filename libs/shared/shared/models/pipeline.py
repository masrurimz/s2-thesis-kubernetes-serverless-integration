"""Pipeline context and stage result models for experiment orchestration.

These models define the typed contracts between pipeline stages.
Each stage reads from and writes to PipelineContext.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from shared.models.experiment import ExperimentConfig, ExperimentResult, RunManifest, StatisticalComparison
from shared.models.metrics import MetricsExport


class PreflightResult(BaseModel):
    """Result of the preflight stage."""

    passed: bool
    checks: dict[str, bool] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)


class WorkloadResult(BaseModel):
    """Result of the workload (k6) stage."""

    success: bool
    k6_summary_path: str = ""
    total_requests: int = 0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    error_rate: float = 0.0
    throughput_rps: float = 0.0
    app_duration_avg_ms: float = 0.0
    app_duration_p50_ms: float = 0.0
    app_duration_p95_ms: float = 0.0
    app_duration_serverless_avg_ms: float = 0.0
    app_duration_serverless_p95_ms: float = 0.0
    app_duration_k8s_avg_ms: float = 0.0


class PipelineContext(BaseModel):
    """Mutable context threaded through experiment pipeline stages.

    Stages write their results into this context for downstream stages to read.
    """

    batch_id: str
    scenario: str
    run_id: int
    config: ExperimentConfig
    manifest: Optional[RunManifest] = None

    # Stages write their results here:
    preflight: Optional[PreflightResult] = None
    workload: Optional[WorkloadResult] = None
    metrics: Optional[MetricsExport] = None
    result: Optional[ExperimentResult] = None
    statistics: Optional[StatisticalComparison] = None

    # Output directory for this run
    output_dir: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True}


class StageResult(BaseModel):
    """Result of a single pipeline stage execution."""

    stage_name: str
    success: bool
    duration_sec: float = 0.0
    error: Optional[str] = None
    artifacts: List[str] = Field(default_factory=list)
