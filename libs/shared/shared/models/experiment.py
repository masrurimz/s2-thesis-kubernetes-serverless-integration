"""Experiment result models — per-run data and statistical comparisons.

Converted from dataclasses in scripts/run_phase_b_experiments.py to Pydantic BaseModels
for schema validation and JSON serialization.
"""

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ExperimentResult(BaseModel):
    """Single experiment run result — all fields per methodology Tables 3-4..3-7."""

    scenario: str
    run_id: int
    timestamp: str

    # k6 primary metrics (Table 3-4)
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    error_rate: float = 0.0
    throughput_rps: float = 0.0
    total_requests: int = 0
    slo_violations_k6: int = 0
    app_duration_avg_ms: float = 0.0
    app_duration_p50_ms: float = 0.0
    app_duration_p95_ms: float = 0.0
    app_duration_serverless_avg_ms: float = 0.0
    app_duration_serverless_p95_ms: float = 0.0
    app_duration_k8s_avg_ms: float = 0.0

    # Prometheus corroboration
    prom_p99_latency_ms: float = 0.0

    # Routing / control-plane metrics (Table 3-5)
    maintain_count: int = 0
    scale_out_count: int = 0
    predictive_count: int = 0
    optimize_cost_count: int = 0
    weight_change_count: int = 0
    time_in_serverless_pct: float = 0.0
    prediction_usage_rate: float = 0.0

    # Algorithm 2 replica scaling metrics (Table 3-6)
    scale_up_events: int = 0
    scale_down_events: int = 0
    scale_up_success: int = 0
    scale_down_success: int = 0
    desired_replicas_final: int = 0
    available_replicas_final: int = 0

    # Control-loop latency (Table 3-5)
    control_loop_latency_avg_ms: float = 0.0

    # Algorithm 2 derived metrics (Table 3-6)
    scale_up_latency_sec: float = 0.0
    oscillation_index: int = 0

    # Cost proxy metrics (Table 3-7)
    k8s_weight_time_product: float = 0.0
    serverless_weight_time_product: float = 0.0
    k8s_replica_seconds: float = 0.0
    knative_active_seconds: float = 0.0

    # GRU metrics (S4 only)
    gru_predictions_used: int = 0
    gru_predictions_failed: int = 0

    # Resource utilization (Table 3-7, via metrics-server)
    avg_cpu_millicores: float = 0.0
    peak_cpu_millicores: float = 0.0
    avg_memory_mib: float = 0.0
    peak_memory_mib: float = 0.0
    resource_utilization_path: str = ""
    avg_cluster_cpu_utilization_pct: float = 0.0
    peak_cluster_cpu_utilization_pct: float = 0.0
    avg_cluster_mem_utilization_pct: float = 0.0
    avg_pod_density: float = 0.0

    # Run metadata
    duration_sec: int = 0
    t_start: float = 0.0
    t_end: float = 0.0
    k6_summary_path: str = ""
    daemon_log_path: str = ""
    prom_export_path: str = ""

    # Raw Prometheus time-series paths (stored per-run)
    replica_timeline_path: str = ""

    # Node provisioning metrics (v4)
    nodes_provisioned: int = 0
    first_provision_delay_sec: float = 0.0
    total_provision_events: int = 0
    provision_log_path: str = ""

    # Multi-node validity gates
    k8s_pod_nodes: List[str] = Field(default_factory=list)
    knative_pod_nodes: List[str] = Field(default_factory=list)
    distinct_workload_nodes: int = 0
    dynamic_node_pod_count: int = 0
    cross_node_observed: bool = False
    validity_gate_passed: bool = True
    validity_gate_notes: List[str] = Field(default_factory=list)
    run_validity_passed: bool = True
    run_validity_notes: List[str] = Field(default_factory=list)
    stress_validity_passed: bool = True
    stress_validity_notes: List[str] = Field(default_factory=list)


class RunManifest(BaseModel):
    """Per-run configuration snapshot for reproducibility."""

    scenario: str
    run_id: int
    run_order_idx: int
    random_seed: int
    git_commit: str
    k6_script: str
    k6_stages_json: str
    replay_manifest: Dict[str, Any]
    daemon_config: Dict[str, Any]
    scaling_config: Dict[str, Any]
    timestamp: str


class BatchManifest(BaseModel):
    """Manifest for a batch of experiment runs."""

    batch_id: str
    date: str
    phase: str
    scenarios: List[str]
    workload: Dict[str, Any]
    runs_per_scenario: int = 1
    git_commit: str = ""
    timestamp: str = ""


class StatisticalComparison(BaseModel):
    """Statistical comparison between two scenarios."""

    baseline_scenario: str
    comparison_scenario: str
    metric: str
    baseline_mean: float
    comparison_mean: float
    difference: float
    percent_change: float
    welch_t_stat: float
    welch_p_value: float
    mannwhitney_u_stat: float
    mannwhitney_p_value: float
    ci_lower: float
    ci_upper: float
    cohens_d: float
    effect_size_interpretation: str
    n_baseline: int
    n_comparison: int


class ExperimentConfig(BaseModel):
    """Configuration for an experiment run."""

    phase: str = "phase-b"
    runs: int = 5
    duration_sec: int = 300
    seed: int = 42
    k6_script: str = ""
    k6_stages_json: str = ""
    replay_manifest: Dict[str, Any] = Field(default_factory=dict)
    daemon_config: Dict[str, Any] = Field(default_factory=dict)
    scaling_config: Dict[str, Any] = Field(default_factory=dict)
