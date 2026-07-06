"""Canonical constants for experiment analysis.

Single source of truth for outlier IDs, cost-proxy beta weights, Phase A1
decision log, cold-start measurements, and cloud pricing. Previously
duplicated across cold_start_analysis.py, reanalyze_phase_b.py, and
cost_analyzer.py.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Outlier run IDs — discovered by identify_outlier_runs.py (now archived).
# These runs had stale/reset Prometheus metrics (p99 < 15ms, impossible for
# HTTP through HAProxy). Excluded from clean-data statistics.
# ---------------------------------------------------------------------------
OUTLIER_RUNS: dict[str, list[int]] = {
    "s1-k8s-only": [2],
    "s2-serverless-only": [5],
    "s3-hybrid-reactive": [5],
}

# ---------------------------------------------------------------------------
# Cost-proxy beta weights per thesis §3.5.2.
# cost(β) = k8s_WTP + β × srv_WTP, normalized so S1 mean = 1.0.
# β models the serverless cost premium (Lambda PC > K8s node).
# ---------------------------------------------------------------------------
BETA_VALUES: list[float] = [0.5, 0.7, 1.0, 1.5]

# ---------------------------------------------------------------------------
# Comparison definitions per thesis §3.5.2.
# (baseline_scenario, comparison_scenario, metric, label)
# ---------------------------------------------------------------------------
H1_COMPARISONS: list[tuple[str, str, str, str]] = [
    ("s1-k8s-only", "s2-serverless-only", "p99_latency_ms", "Platform baseline"),
    ("s1-k8s-only", "s2-serverless-only", "error_rate", "Platform baseline"),
    ("s1-k8s-only", "s3-hybrid-reactive", "p99_latency_ms", "Reactive vs K8s"),
    ("s1-k8s-only", "s3-hybrid-reactive", "slo_violations_k6", "Reactive vs K8s"),
    ("s2-serverless-only", "s3-hybrid-reactive", "p99_latency_ms", "Reactive vs Serverless"),
    ("s1-k8s-only", "s4-hybrid-predictive", "p99_latency_ms", "Predictive vs K8s"),
    ("s1-k8s-only", "s4-hybrid-predictive", "slo_violations_k6", "Predictive vs K8s"),
]

H2_COMPARISONS: list[tuple[str, str, str, str]] = [
    ("s3-hybrid-reactive", "s4-hybrid-predictive", "p99_latency_ms", "Predictive vs Reactive"),
    ("s3-hybrid-reactive", "s4-hybrid-predictive", "slo_violations_k6", "Predictive vs Reactive"),
]

# ---------------------------------------------------------------------------
# Cold-start measurements (from infrastructure/results/knative-real/RESULTS-SUMMARY.md)
# and Knative autoscaler config (from infrastructure/k3d/knative-install.sh).
# ---------------------------------------------------------------------------
COLD_START_MS_S3 = 682.0  # Pre-warm cold start for S3 reactive
COLD_START_MS_S4 = 1235.0  # Pre-warm cold start for S4 predictive
COLD_START_RANGE = (682.0, 1235.0)  # Range across measurements

KNATIVE_SCALE_TO_ZERO_GRACE = 30  # seconds
KNATIVE_STABLE_WINDOW = 60  # seconds
KNATIVE_MIN_SCALE = 0  # minScale annotation

# Algorithm 1 config (from controller/intelligent_router/algorithm1_controller.py)
WEIGHT_STEP = 10  # +10% per SCALE_OUT
COOLDOWN_SEC = 15  # seconds between adjustments
MAX_KNATIVE_WEIGHT = 50  # max serverless weight

# ---------------------------------------------------------------------------
# Phase A1 decision log (from report.md) — weight transition + p99 per decision.
# ---------------------------------------------------------------------------
PHASE_A1_DECISIONS: list[dict] = [
    {"decision": 1, "action": "MAINTAIN", "p99_ms": None, "weights": (100, 0)},
    {"decision": 2, "action": "MAINTAIN", "p99_ms": 6516.0, "weights": (100, 0)},
    {"decision": 3, "action": "SCALE_OUT", "p99_ms": 3648.0, "weights": (90, 10)},
    {"decision": 4, "action": "SCALE_OUT", "p99_ms": 2060.0, "weights": (80, 20)},
    {"decision": 5, "action": "SCALE_OUT", "p99_ms": 1120.0, "weights": (70, 30)},
    {"decision": 6, "action": "SCALE_OUT", "p99_ms": 632.0, "weights": (60, 40)},
    {"decision": 7, "action": "SCALE_OUT", "p99_ms": 278.0, "weights": (50, 50)},
    {"decision": 8, "action": "OPTIMIZE_COST", "p99_ms": 110.0, "weights": (55, 45)},
    {"decision": 9, "action": "PREDICTIVE", "p99_ms": 146.0, "weights": (50, 50)},
    {"decision": 10, "action": "MAINTAIN", "p99_ms": 158.0, "weights": (50, 50)},
    {"decision": 11, "action": "MAINTAIN", "p99_ms": 266.0, "weights": (50, 50)},
    {"decision": 18, "action": "OPTIMIZE_COST", "p99_ms": 118.0, "weights": (55, 45)},
]

# ---------------------------------------------------------------------------
# Pod resource configuration — derived from CalibrationConfig (single source of truth)
from shared.models.calibration import CALIBRATION

POD_CPU_REQUEST = CALIBRATION.pod_cpu_request  # 0.300 (from pod_cpu_millicores=300)
POD_MEM_REQUEST_GIB = CALIBRATION.pod_memory_request_mib / 1024  # 64Mi
KNATIVE_TARGET_CONCURRENCY = 10  # autoscaling.knative.dev/target: "10"

# EKS control plane (us-east-1, 2025)
EKS_CONTROL_PLANE_RATE = 0.10  # $/hour

# Real cloud node sizing (production projection)
CLOUD_NODES: dict[str, dict] = {
    "t3.medium": {"vcpu": 2, "allocatable_cpu": 1.8, "mem_gib": 4.0, "allocatable_mem_gib": 3.5, "rate": 0.0416},
    "m5.xlarge": {"vcpu": 4, "allocatable_cpu": 3.8, "mem_gib": 16.0, "allocatable_mem_gib": 15.0, "rate": 0.192},
}
DEFAULT_CLOUD_NODE = "t3.medium"

# Production sizing targets (conservative for burst headroom + DaemonSets)
TARGET_CPU_UTIL = 0.60
TARGET_MEM_UTIL = 0.70

# Lambda overhead (network + runtime init per invocation)
LAMBDA_OVERHEAD_SEC = 0.010  # 10ms typical
# Lambda memory derived from CPU allocation (AWS: 1 vCPU at 1769MB)
LAMBDA_MEM_MB = CALIBRATION.lambda_mem_mb
LAMBDA_MEM_GB = CALIBRATION.lambda_mem_gb

# AWS Lambda Provisioned Concurrency (x86, us-east-1, 2025 list prices)
LAMBDA_PC_RATE = 0.0000041667  # $/GB-s provisioned (warm) capacity
LAMBDA_PC_EXEC_RATE = 0.0000097222  # $/GB-s execution while provisioned
LAMBDA_ONDEMAND_RATE = 0.0000166667  # $/GB-s on-demand (overflow)
LAMBDA_REQUEST_RATE = 0.20  # $/1M requests

# EC2 reference node
EC2_T3_MEDIUM_RATE = 0.0416  # $/hour (2 vCPU, 4 GiB)
