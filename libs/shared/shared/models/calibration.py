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

    # Workload tuple — fib(33) measured: p50=8.6ms, p99=27ms at 50 RPS/3pods
    fib_n: int = 33
    gomaxprocs: int = 1
    slo_threshold_ms: float = 200.0

    # Pod resources (must match deployment YAMLs) — CPU limits REMOVED (SoCC 2025)
    pod_cpu_millicores: int = 300
    pod_memory_mib: int = 128
    # Lambda bills for WALL-CLOCK duration, not CPU time (SeBS: arXiv:2012.14132).
    # fib(33) = 14ms pure CPU. Real workloads add I/O waits (50-200ms per SeBS/SeBS-Flow).
    # WORK_DURATION_MS in deployment YAMLs simulates I/O wait (currently 10ms).
    # This is a CPU-only lower bound — real serverless costs would be 3-10× higher.
    lambda_compute_ms: float = 14.0  # Measured fib(33) CPU compute time (no I/O)

    # Capacity model — MEASURED from t7-capacity-envelope test (no CPU limits)
    # fib(33): p99 < 200ms up to 150 RPS (50/pod), cliff at 200 RPS (66.7/pod)
    # target_cpu_util=0.8 → cap = 3 × 50 × 0.8 = 120 RPS (efficient, handles mean 73)
    # Peaks >120 RPS overflow to serverless (BACC methodology: tau=0.8)
    r_saturation_per_replica: float = 50.0  # Measured: last good level before p99 cliff
    target_cpu_util: float = 0.8  # High efficiency — K8s cap=120 RPS, overflow during peaks

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
