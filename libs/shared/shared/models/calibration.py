"""Centralized calibration configuration for experiment workload parameters.

All calibration-sensitive values live here as a single source of truth.
Values are overwritten from measured capacity envelope test results —
defaults are starting guesses, NOT validated constants.

Config injection: use CalibrationConfig.load(path=...) for explicit merge,
or get_calibration() to resolve CALIBRATION_OVERRIDE env at call time.
The module-level CALIBRATION singleton is NEVER mutated by env at import.
"""

import json as _json
import os as _os
from pathlib import Path as _Path
from typing import Any, Mapping, Optional

from pydantic import BaseModel, ConfigDict


class CalibrationConfig(BaseModel):
    """Workload calibration invariants — set from measured capacity test.

    The workload tuple (CPU + fib_n + GOMAXPROCS) determines per-pod compute
    cost. r_saturation_per_replica is the RPS at which p99 latency crosses the
    SLO threshold, measured by ramping load against 3 pods. alpha = 1/r_saturation
    is the linear coefficient for Algorithm 2 (replicas = alpha * load + beta).
    """

    model_config = ConfigDict(extra="forbid")

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

    # Capacity model — MEASURED fib(33), no pod limits, node --cpus=1.0 (2 workload nodes)
    # Calibrated July 11: S1 saturates at 100 RPS (p99 crosses 200ms)
    # r_sat = 100/3 = 33.3 (total saturation / baseline replicas)
    # 3 pods × 16.65 r_effective = 50 RPS model capacity (conservative vs ~83 actual)
    # ClarkNet mean 73 > 50 → S1 saturates → S4 hybrid routing valuable
    r_saturation_per_replica: float = 33.3
    target_cpu_util: float = 0.5

    # Replica bounds
    min_k8s_replicas: int = 3
    max_k8s_replicas: int = 6  # Cap to match schedulable capacity (2 nodes × 3 pods at 300m)
    baseline_replicas_s3_s4: int = 3  # MUST equal min_k8s_replicas

    # Algorithm 2 (ClusterController) linear model
    beta: float = 0.0
    buffer: float = 1.2
    scale_down_threshold: float = 0.5
    alpha_override: Optional[float] = None

    # Controller tuning (V3 burn-rate PI + proactive routing)
    # NOTE: Three tuning attempts all failed n=5 holdout vs defaults (SLO=702, p99=188ms):
    #   1. Aggressive HPO (cpu=0.659, kp=1.49): single-run SLO=232 → holdout mean SLO=2886
    #   2. GP surrogate candidate (cpu=0.45, kp=0.6): single-run SLO=565 → holdout mean SLO=5803
    #   3. All other screening trials: worse than defaults in single-run
    # Root cause: shared-resource system variance is too high for any param deviation.
    # Defaults calibrated from capacity ramp test remain optimal.
    kp_burn: float = 0.5
    ki_burn: float = 0.05
    proactive_trend_threshold: float = 3.0
    proactive_approach_ratio: float = 0.8  # Raise from 0.6: trigger at 80% capacity, not 60%

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

    @classmethod
    def load(
        cls,
        path: str | _Path | None = None,
        overrides: Mapping[str, Any] | None = None,
    ) -> "CalibrationConfig":
        """Load defaults, then merge optional JSON file and/or dict overrides.

        Merge semantics: only provided keys replace defaults; unknown keys raise
        ValidationError (Pydantic). Partial trial JSONs are valid.

        Uses model_dump → dict merge → model_validate to ensure full re-validation
        (model_copy skips validation in Pydantic v2).
        """
        base = cls().model_dump()
        if path is not None:
            p = _Path(path)
            if not p.is_file():
                raise FileNotFoundError(f"Calibration override not found: {p}")
            data = _json.loads(p.read_text())
            if not isinstance(data, dict):
                raise TypeError(f"Calibration JSON must be an object, got {type(data)}")
            base.update(data)
        if overrides:
            base.update(dict(overrides))
        return cls.model_validate(base)


def get_calibration() -> CalibrationConfig:
    """Resolve active calibration: CALIBRATION_OVERRIDE env if set, else defaults.

    Prefer injecting CalibrationConfig via constructors/CLI over calling this
    repeatedly. Exists so subprocess-spawned daemons keep working.
    """
    path = _os.environ.get("CALIBRATION_OVERRIDE")
    return CalibrationConfig.load(path) if path else CalibrationConfig()


# Module-level default for production/import convenience — NOT mutated by env
# at import time. HPO subprocesses must call get_calibration() or pass path.
CALIBRATION = CalibrationConfig()
