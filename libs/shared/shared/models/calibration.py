"""Centralized calibration configuration for experiment workload parameters.

All calibration-sensitive values live here as a single source of truth.
Values are overwritten from measured capacity envelope test results —
defaults are starting guesses, NOT validated constants.

Supports CALIBRATION_OVERRIDE env var: path to JSON file with partial
CalibrationConfig fields to override at import time (used by controller HPO).
"""

import json as _json
import os as _os
from typing import Optional

from pydantic import BaseModel


class CalibrationConfig(BaseModel):
    """Workload calibration invariants — set from measured capacity test.

    The workload tuple (CPU + fib_n + GOMAXPROCS) determines per-pod compute
    cost. r_saturation_per_replica is the RPS at which p99 latency crosses the
    SLO threshold, measured by ramping load against 3 pods. alpha = 1/r_saturation
    is the linear coefficient for Algorithm 2 (replicas = alpha * load + beta).
    """

    # Workload tuple — fib(33): 3ms CPU compute, verified by deploy-app
    fib_n: int = 33
    gomaxprocs: int = 1
    slo_threshold_ms: float = 200.0

    # Pod resources (K8s AND Knative MUST match these values)
    pod_cpu_millicores: int = 300
    pod_memory_mib: int = 128  # memory limit
    pod_memory_request_mib: int = 64  # memory request (lower than limit)

    # Node resources (Docker --cpus per k3d node)
    # thesis-hybrid: server=1.0, agent=1.0 each (2 agents) + up to 2 dynamic=1.0 each
    # thesis-serverless: server=1.0, agent=3.0 (matches K8s static+1 dynamic = 4.0 total)
    k8s_node_cpu_limit: float = 1.0  # Per-node Docker --cpus (thesis-hybrid agents)
    serverless_agent_cpu: float = 3.0  # thesis-serverless agent Docker --cpus
    k8s_static_cpu_total: float = 3.0  # 2 agents × 1.0 + server (server doesn't run workload pods)
    k8s_peak_cpu_total: float = 5.0  # 3 static + 2 dynamic nodes
    serverless_cpu_total: float = 4.0  # 1.0 server + 3.0 agent (no dynamic nodes)
    node_memory_gb: float = 1.0

    # Lambda billing (SeBS: arXiv:2012.14132 — Lambda bills wall-clock duration)
    # fib(33) = 3ms CPU + 50ms simulated I/O wait (DB query per SeBS/SeBS-Flow).
    # WORK_DURATION_MS in deployment YAMLs MUST match io_wait_ms.
    lambda_compute_ms: float = 24.0  # Measured fib(33) CPU compute time
    io_wait_ms: float = 50.0  # Simulated I/O wait (DB query, SeBS methodology)

    # Capacity model — MEASURED fib(33), no CPU limits, 50ms I/O wait
    # p99 < 200ms up to 150 RPS (50/pod), cliff at 200 RPS (66.7/pod)
    # K8s actual saturation: 150 RPS. ClarkNet peak 164 > 150 → S1 saturates
    # r_sat=66.7 (first p99 crossing), util=0.5 → cap=100 (model capacity)
    r_saturation_per_replica: float = 66.7
    target_cpu_util: float = 0.5

    # Replica bounds
    min_k8s_replicas: int = 3
    max_k8s_replicas: int = 10
    baseline_replicas_s3_s4: int = 3  # MUST equal min_k8s_replicas

    # Algorithm 2 (ClusterController) linear model
    beta: float = 0.0
    buffer: float = 1.2
    scale_down_threshold: float = 0.5
    alpha_override: Optional[float] = None

    # Controller tuning (V3 burn-rate PI + proactive routing)
    # NOTE: Controller HPO screening (10 trials) found target_cpu_util=0.659, kp_burn=1.49
    # performed best in single-run (SLO=232). However, n=5 holdout validation showed
    # these params OVERFIT: mean SLO=2886 vs 702 with defaults. Conservative defaults
    # (target_cpu_util=0.5) provide better robustness under system variance.
    kp_burn: float = 0.5
    ki_burn: float = 0.05
    proactive_trend_threshold: float = 3.0
    proactive_approach_ratio: float = 0.6

    # GRU model params — tuned via Optuna HPO (30 trials, val RMSE 4.75%)
    # HPO date: 2026-07-09. Prior manual tuning: hidden=64, layers=2, RMSE=6.01%
    gru_hidden_size: int = 128
    gru_num_layers: int = 1
    gru_learning_rate: float = 0.000380
    gru_sequence_length: int = 30
    gru_dropout: float = 0.104  # Note: nn.GRU ignores dropout when num_layers=1

    @property
    def pod_cpu_request(self) -> float:
        """Pod CPU request in vCPU units (e.g., 0.300 for 300m)."""
        return self.pod_cpu_millicores / 1000

    @property
    def lambda_mem_mb(self) -> int:
        """AWS Lambda memory: 1 vCPU at 1769MB, memory scales with CPU allocation."""
        import math

        return math.ceil(self.pod_cpu_request * 1769)

    @property
    def lambda_mem_gb(self) -> float:
        return self.lambda_mem_mb / 1024

    @property
    def alpha(self) -> float:
        """Linear coefficient: replicas per RPS. Derived from r_saturation."""
        return self.alpha_override or (1.0 / self.r_saturation_per_replica)

    @property
    def r_effective(self) -> float:
        """Effective RPS per pod with safety margin."""
        return self.r_saturation_per_replica * self.target_cpu_util

    @property
    def k8s_capacity_rps(self) -> float:
        """Total K8s capacity at min replicas with safety margin."""
        return self.min_k8s_replicas * self.r_effective

    @property
    def endpoint(self) -> str:
        """K6 workload endpoint derived from fib_n."""
        return f"/fib?n={self.fib_n}"

    def to_v3_config_overrides(self) -> dict:
        """Kwargs for Algorithm1ConfigV3(...) constructor."""
        return {
            "r_saturation_per_replica": self.r_saturation_per_replica,
            "target_cpu_util": self.target_cpu_util,
            "min_k8s_replicas": self.min_k8s_replicas,
            "max_k8s_replicas": self.max_k8s_replicas,
            "slo_target_p99_ms": self.slo_threshold_ms,
            "kp_burn": self.kp_burn,
            "ki_burn": self.ki_burn,
            "proactive_trend_threshold": self.proactive_trend_threshold,
            "proactive_approach_ratio": self.proactive_approach_ratio,
        }

    def to_scaling_config_overrides(self) -> dict:
        """Kwargs for ScalingConfig(...) constructor."""
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "buffer": self.buffer,
            "min_replicas": self.min_k8s_replicas,
            "max_replicas": self.max_k8s_replicas,
            "scale_down_threshold": self.scale_down_threshold,
        }

    def to_gru_config_kwargs(self) -> dict:
        """Kwargs for GRUConfig(...) constructor — HPO-tuned params."""
        return {
            "hidden_size": self.gru_hidden_size,
            "num_layers": self.gru_num_layers,
            "learning_rate": self.gru_learning_rate,
            "sequence_length": self.gru_sequence_length,
            "dropout": self.gru_dropout,
        }


_override_path = _os.environ.get("CALIBRATION_OVERRIDE")
if _override_path:
    with open(_override_path) as _f:
        _overrides = _json.load(_f)
    CALIBRATION = CalibrationConfig(**_overrides)
else:
    CALIBRATION = CalibrationConfig()
