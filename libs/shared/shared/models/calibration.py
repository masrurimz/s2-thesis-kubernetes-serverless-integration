"""Centralized calibration configuration for experiment workload parameters.

All calibration-sensitive values live here as a single source of truth.
Values are overwritten from measured capacity envelope test results —
defaults are starting guesses, NOT validated constants.
"""

from typing import Optional

from pydantic import BaseModel


class CalibrationConfig(BaseModel):
    """Workload calibration invariants — set from measured capacity test.

    The workload tuple (CPU + fib_n + GOMAXPROCS) determines per-pod compute
    cost. r_saturation_per_replica is the RPS at which p99 latency crosses the
    SLO threshold, measured by ramping load against 3 pods. alpha = 1/r_saturation
    is the linear coefficient for Algorithm 2 (replicas = alpha * load + beta).
    """

    # Workload tuple — fib(30): 3ms CPU compute, verified by deploy-app
    fib_n: int = 30
    gomaxprocs: int = 1
    slo_threshold_ms: float = 200.0

    # Pod resources (K8s AND Knative MUST match these values)
    pod_cpu_millicores: int = 300
    pod_memory_mib: int = 128  # memory limit
    pod_memory_request_mib: int = 64  # memory request (lower than limit)

    # Node resources (Docker --cpus for k3d nodes, applied by manager.py/autoscaler.py)
    node_cpu_limit: float = 1.0
    node_memory_gb: float = 1.0

    # Lambda billing (SeBS: arXiv:2012.14132 — Lambda bills wall-clock duration)
    # fib(30) = 3ms CPU + 50ms simulated I/O wait (DB query per SeBS/SeBS-Flow).
    # WORK_DURATION_MS in deployment YAMLs MUST match io_wait_ms.
    lambda_compute_ms: float = 3.0  # Measured fib(30) CPU compute time
    io_wait_ms: float = 50.0  # Simulated I/O wait (DB query, SeBS methodology)

    # Capacity model — MEASURED fib(30), 300m CPU limits, 50ms I/O wait
    # p99 < 200ms up to 200 RPS (66.7/pod), cliff at 250 RPS (83.3/pod)
    # r_sat=66.7 (last good level), util=0.5 → cap = 3 × 66.7 × 0.5 = 100 RPS
    # Above ClarkNet mean (73), 8 stages >100 overflow to Knative
    r_saturation_per_replica: float = 66.7  # Measured: last good level before p99 cliff
    target_cpu_util: float = 0.5  # Forces overflow during peaks (cap=100, 8 stages exceed)

    # Replica bounds
    min_k8s_replicas: int = 3
    max_k8s_replicas: int = 10
    baseline_replicas_s3_s4: int = 3  # MUST equal min_k8s_replicas

    # Algorithm 2 (ClusterController) linear model
    beta: float = 0.0
    buffer: float = 1.2
    scale_down_threshold: float = 0.5
    alpha_override: Optional[float] = None

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


CALIBRATION = CalibrationConfig()
