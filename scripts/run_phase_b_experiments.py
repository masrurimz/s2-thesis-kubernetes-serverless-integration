#!/usr/bin/env python3
"""
Phase B: Replicated Comparison with Trace-Driven Workload.

Implements the experiment protocol from thesis Section 3.5.4:
- k6 ClarkNet trace-driven replay (ramping-arrival-rate, 30s stages)
- Per-run scenario reset (HPA/KPA/Algorithm 2 management)
- Time-window Prometheus metric export (query_range)
- Algorithm 2 replica scaling metrics
- k6 handleSummary JSON as primary metric source
- Statistical analysis (Welch, Mann-Whitney U, bootstrap CI, Cohen's d)

Usage:
    uv run python scripts/run_phase_b_experiments.py \\
        --phase full --runs 5

    uv run python scripts/run_phase_b_experiments.py \\
        --phase experiments --runs 5 --seed 42
"""

import argparse
import json
import os
import random
import shutil
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import requests
import structlog
from scipy import stats as scipy_stats

logger = structlog.get_logger(__name__)

# Add path for k3d autoscaler module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "infrastructure" / "k3d"))
from k3d_autoscaler import K3dAutoscalerAdapter

SCRIPT_DIR = Path(__file__).resolve().parent  # scripts/
PROJECT_ROOT = SCRIPT_DIR.parent  # repo root
CONTROLLER_DIR = PROJECT_ROOT / "controller"

# Tool paths (mise-managed)
K6_PATH = os.environ.get(
    "K6_PATH",
    str(Path.home() / ".local/share/mise/installs/k6/1.6.0/k6-v1.6.0-linux-amd64/k6"),
)
KUBECTL_PATH = os.environ.get(
    "KUBECTL_PATH",
    str(Path.home() / ".local/share/mise/installs/kubectl/1.35.0/kubectl"),
)

# Infrastructure defaults
K6_SCRIPT = PROJECT_ROOT / "infrastructure" / "load-tests" / "canonical" / "clarknet_replay.js"
K6_STAGES = PROJECT_ROOT / "data" / "trace-replay" / "clarknet_k6_stages.json"
K6_STAGES_TEST = PROJECT_ROOT / "data" / "trace-replay" / "clarknet_k6_stages_test.json"
REPLAY_MANIFEST = PROJECT_ROOT / "data" / "trace-replay" / "clarknet_replay_manifest.json"

HAPROXY_HOST = "localhost"
HAPROXY_SOCKET_PORT = 19999
HAPROXY_STATS_URL = "http://localhost:18404/stats;csv"
PROMETHEUS_URL = "http://localhost:9090"
GRU_URL = "http://localhost:8090"
DAEMON_API = "http://localhost:9104"
TARGET_URL = "http://localhost:18082"
DAEMON_API_PORT = 9104
DEPLOYMENT = "test-app-warm"
HPA_NAME = "test-app-warm-hpa"
NAMESPACE = "default"
K6_ENDPOINT = "/fib?n=34"
K8S_DEPLOYMENT_FILTER = f'deployment="{DEPLOYMENT}",namespace="{NAMESPACE}"'

SCENARIOS = ["s1-k8s-only", "s2-serverless-only", "s3-hybrid-reactive", "s4-hybrid-predictive"]

WARMUP_SEC = 30
COOLDOWN_SEC = 60
INTER_RUN_PAUSE_SEC = 60


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ExperimentResult:
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
    k8s_pod_nodes: List[str] = field(default_factory=list)
    knative_pod_nodes: List[str] = field(default_factory=list)
    distinct_workload_nodes: int = 0
    dynamic_node_pod_count: int = 0
    cross_node_observed: bool = False
    validity_gate_passed: bool = True
    validity_gate_notes: List[str] = field(default_factory=list)
    run_validity_passed: bool = True
    run_validity_notes: List[str] = field(default_factory=list)
    stress_validity_passed: bool = True
    stress_validity_notes: List[str] = field(default_factory=list)


@dataclass
class RunManifest:
    """Per-run configuration snapshot for reproducibility."""

    scenario: str
    run_id: int
    run_order_idx: int
    random_seed: int
    git_commit: str
    k6_script: str
    k6_stages_json: str
    replay_manifest: dict
    daemon_config: dict
    scaling_config: dict
    timestamp: str


@dataclass
class StatisticalComparison:
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_cmd(cmd: List[str], timeout: int = 30, **kwargs) -> subprocess.CompletedProcess:
    """Run a command with timeout, return CompletedProcess."""
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **kwargs)


def _kubectl(args: List[str], timeout: int = 15) -> subprocess.CompletedProcess:
    """Run kubectl with standard args."""
    return _run_cmd([KUBECTL_PATH, "-n", NAMESPACE] + args, timeout=timeout)


def _git_commit_hash() -> str:
    try:
        r = _run_cmd(["git", "rev-parse", "--short", "HEAD"], timeout=5)
        return r.stdout.strip() if r.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def _prom_query(expr: str) -> Optional[float]:
    """Instant Prometheus query."""
    try:
        r = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": expr}, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("status") == "success":
            results = data.get("data", {}).get("result", [])
            if results:
                return float(results[0]["value"][1])
    except Exception as e:
        logger.debug("prom_query_failed", expr=expr[:80], error=str(e))
    return None


def _prom_query_range(expr: str, start: float, end: float, step: str = "15s") -> List[Tuple[float, float]]:
    """Prometheus query_range → list of (timestamp, value)."""
    try:
        r = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query_range",
            params={"query": expr, "start": start, "end": end, "step": step},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("status") == "success":
            results = data.get("data", {}).get("result", [])
            if results:
                return [(float(v[0]), float(v[1])) for v in results[0]["values"]]
    except Exception as e:
        logger.debug("prom_query_range_failed", expr=expr[:80], error=str(e))
    return []


def _parse_haproxy_stats_weights() -> Optional[Dict[str, int]]:
    """Parse HAProxy stats CSV to get current k3s/knative weights."""
    try:
        r = requests.get(HAPROXY_STATS_URL, timeout=5)
        if r.status_code != 200:
            return None
        weights: Dict[str, int] = {}
        for line in r.text.strip().split("\n"):
            if line.startswith("#") or not line.strip():
                continue
            fields = line.split(",")
            if len(fields) < 19 or fields[0] != "servers":
                continue
            svname = fields[1]
            if svname in ("k3s", "k3s-cluster"):
                weights["k3s"] = int(fields[18])
            elif svname in ("knative", "serverless-sim"):
                weights["knative"] = int(fields[18])
        return weights if weights else None
    except Exception as e:
        logger.debug("haproxy_stats_parse_failed", error=str(e))
        return None


class NodeProvisioner:
    """Simulates cloud node provisioning via cordon/uncordon with delay."""

    WORKLOAD_NODES = [
        "k3d-thesis-hybrid-agent-1",  # baseline (always schedulable)
        "k3d-thesis-hybrid-agent-2",
        "k3d-thesis-hybrid-agent-3",
    ]
    BASELINE_NODES = ["k3d-thesis-hybrid-agent-1"]

    def __init__(self, provision_delay_min_sec: int = 45, provision_delay_max_sec: int = 120):
        self.provision_delay_min_sec = provision_delay_min_sec
        self.provision_delay_max_sec = provision_delay_max_sec
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._provisioned_nodes: List[str] = []
        self._provision_log: List[Tuple[float, str, Dict[str, Any]]] = []
        self._log_lock = threading.Lock()

    @staticmethod
    def _kubectl_cluster(args: List[str], timeout: int = 15) -> subprocess.CompletedProcess:
        """Run cluster-scoped kubectl command (no namespace flag)."""
        return _run_cmd([KUBECTL_PATH] + args, timeout=timeout)

    def reset(self) -> bool:
        """Reset all workload nodes: uncordon all, then cordon non-baseline."""
        self.stop()
        self._provisioned_nodes = list(self.BASELINE_NODES)
        with self._log_lock:
            self._provision_log = []

        # Uncordon all first (clean state)
        for node in self.WORKLOAD_NODES:
            r = self._kubectl_cluster(["uncordon", node])
            if r.returncode != 0:
                logger.warning("uncordon_nonfatal", node=node, stderr=r.stderr.strip())

        # Cordon non-baseline nodes
        for node in self.WORKLOAD_NODES:
            if node in self.BASELINE_NODES:
                continue
            r = self._kubectl_cluster(["cordon", node])
            if r.returncode != 0:
                logger.error("cordon_failed", node=node, stderr=r.stderr.strip())
                return False

        logger.info(
            "node_provisioner_reset",
            schedulable=self.BASELINE_NODES,
            cordoned=[n for n in self.WORKLOAD_NODES if n not in self.BASELINE_NODES],
            provision_delay_range=(self.provision_delay_min_sec, self.provision_delay_max_sec),
        )
        return True

    def start_background(self) -> None:
        """Start background thread that watches for Pending pods."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._provision_loop, daemon=True)
        self._thread.start()
        logger.info("node_provisioner_started")

    def stop(self) -> None:
        """Stop the provisioner thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=10)
            self._thread = None

    def get_log(self) -> List[Tuple[float, str, Dict[str, Any]]]:
        """Return provision events for experiment metadata."""
        with self._log_lock:
            return list(self._provision_log)

    def _append_event(self, event_type: str, details: Dict[str, Any]) -> None:
        with self._log_lock:
            self._provision_log.append((time.time(), event_type, details))

    def _provision_loop(self) -> None:
        """Poll for Pending warm pods -> wait delay -> uncordon next node."""
        cordoned = [n for n in self.WORKLOAD_NODES if n not in self._provisioned_nodes]

        while not self._stop_event.is_set() and cordoned:
            if self._stop_event.wait(2):
                return

            r = _kubectl(
                [
                    "get",
                    "pods",
                    "-l",
                    "app=test-app-warm",
                    "--field-selector=status.phase=Pending",
                    "-o",
                    "json",
                ]
            )
            if r.returncode != 0:
                continue

            try:
                pods = json.loads(r.stdout).get("items", [])
            except json.JSONDecodeError:
                continue

            pending_unschedulable: List[str] = []
            for pod in pods:
                conditions = pod.get("status", {}).get("conditions", [])
                for cond in conditions:
                    if cond.get("reason") == "Unschedulable":
                        pending_unschedulable.append(pod.get("metadata", {}).get("name", "unknown"))
                        break

            if not pending_unschedulable:
                continue

            next_node = cordoned[0]
            self._append_event(
                "pending_detected",
                {"pods": pending_unschedulable, "next_node": next_node},
            )
            logger.info(
                "node_provisioning_triggered",
                pending_pods=len(pending_unschedulable),
                next_node=next_node,
                delay_range=(self.provision_delay_min_sec, self.provision_delay_max_sec),
            )

            delay = random.randint(self.provision_delay_min_sec, self.provision_delay_max_sec)
            self._append_event(
                "provision_delay_started",
                {"delay_sec": delay, "next_node": next_node},
            )
            logger.info("node_provision_delay", delay_sec=delay, next_node=next_node)

            for _ in range(delay):
                if self._stop_event.wait(1):
                    return

            r = self._kubectl_cluster(["uncordon", next_node])
            if r.returncode == 0:
                self._provisioned_nodes.append(next_node)
                cordoned.pop(0)
                self._append_event("node_provisioned", {"node": next_node})
                logger.info("node_provisioned", node=next_node, remaining_cordoned=len(cordoned))
            else:
                self._append_event("uncordon_failed", {"node": next_node, "stderr": r.stderr.strip()})
                logger.error("uncordon_failed", node=next_node, stderr=r.stderr.strip())


# ---------------------------------------------------------------------------
# Infrastructure preflight  (s2-omz)
# ---------------------------------------------------------------------------


class PreflightChecker:
    """Validates cluster and service readiness before experiments."""

    def check_all(self) -> Tuple[bool, Dict[str, bool]]:
        checks = {
            "k6_binary": Path(K6_PATH).exists(),
            "kubectl_binary": Path(KUBECTL_PATH).exists(),
            "k6_script": K6_SCRIPT.exists(),
            "k6_stages": K6_STAGES.exists(),
            "prometheus": self._check_http(f"{PROMETHEUS_URL}/-/healthy"),
            "haproxy_stats": self._check_http(HAPROXY_STATS_URL.replace(";csv", "")),
            "gru_server": self._check_http(f"{GRU_URL}/health"),
            "cluster_nodes": self._check_nodes(),
            "target_deployment": self._check_deployment(),
            "knative_serving": self._check_knative(),
        }
        all_ok = all(checks.values())
        for name, ok in checks.items():
            status = "✅" if ok else "❌"
            logger.info("preflight", check=name, status=status)
        return all_ok, checks

    @staticmethod
    def _check_http(url: str) -> bool:
        try:
            return requests.get(url, timeout=5).status_code == 200
        except Exception:
            return False

    @staticmethod
    def _check_nodes() -> bool:
        r = _kubectl(["get", "nodes", "-o", "json"])
        if r.returncode != 0:
            return False
        data = json.loads(r.stdout)
        for node in data.get("items", []):
            for cond in node.get("status", {}).get("conditions", []):
                if cond.get("type") == "Ready" and cond.get("status") != "True":
                    return False
        return True

    @staticmethod
    def _check_deployment() -> bool:
        r = _kubectl(["get", f"deployment/{DEPLOYMENT}", "-o", "json"])
        return r.returncode == 0

    @staticmethod
    def _check_knative() -> bool:
        r = _kubectl(["get", "ksvc", "-o", "json"], timeout=10)
        return r.returncode == 0


# ---------------------------------------------------------------------------
# Per-run scenario reset  (s2-rsg, s2-5xb)
# ---------------------------------------------------------------------------


class ScenarioResetter:
    """Implements per-run reset procedure per methodology Section 3.5.4(B)."""

    def reset(self, scenario: str, provisioner=None) -> bool:
        logger.info("scenario_reset_start", scenario=scenario)

        controller_ver = os.environ.get("CONTROLLER_VERSION", "v3")
        if provisioner and scenario in ("s1-k8s-only", "s3-hybrid-reactive", "s4-hybrid-predictive"):
            if scenario == "s4-hybrid-predictive" and controller_ver == "v3":
                # V3 capacity-driven: keep 1 dynamic node alive for immediate K8s capacity
                # Instead of full reset (deletes all nodes), just cordon extras
                provisioner.stop()
                logger.info("V3 soft reset: keeping dynamic nodes alive", scenario=scenario)
            else:
                if not provisioner.reset():
                    logger.error("node_provisioner_reset_failed", scenario=scenario)
                    return False

        if scenario == "s1-k8s-only":
            ok = self._reset_s1()
        elif scenario == "s2-serverless-only":
            ok = self._reset_s2()
        elif scenario in ("s3-hybrid-reactive", "s4-hybrid-predictive"):
            ok = self._reset_s3_s4()
        else:
            logger.error("unknown_scenario", scenario=scenario)
            return False

        if ok:
            # Reset HAProxy weights to scenario baseline (fatal if fails)
            if not self._reset_haproxy_weights(scenario):
                logger.error("scenario_reset_haproxy_failed", scenario=scenario)
                return False
            logger.info("scenario_reset_complete", scenario=scenario)
        return ok

    def _reset_s1(self) -> bool:
        """S1: ensure HPA, delete any manual scaling artifacts."""
        # Delete HPA if it exists (clean slate), then recreate
        _kubectl(["delete", "hpa", DEPLOYMENT, "--ignore-not-found"])
        # Scale to 1 replica baseline before HPA takes over
        _kubectl(["scale", f"deployment/{DEPLOYMENT}", "--replicas=1"])
        time.sleep(5)
        r = _kubectl(
            [
                "autoscale",
                f"deployment/{DEPLOYMENT}",
                "--cpu-percent=50",
                "--min=1",
                "--max=10",
            ]
        )
        if r.returncode != 0:
            logger.error("hpa_create_failed", stderr=r.stderr.strip())
            return False

        # Wait for HPA to have metrics (not <unknown>)
        for _ in range(20):
            time.sleep(3)
            hr = _kubectl(["get", "hpa", DEPLOYMENT, "-o", "json"])
            if hr.returncode == 0:
                hpa = json.loads(hr.stdout)
                conditions = hpa.get("status", {}).get("conditions", [])
                current = hpa.get("status", {}).get("currentMetrics", [])
                # HPA ready when currentReplicas > 0
                if hpa.get("status", {}).get("currentReplicas", 0) > 0:
                    logger.info("hpa_ready", replicas=hpa["status"]["currentReplicas"])
                    return True
        logger.warning("hpa_metrics_timeout")
        return True  # Proceed anyway; HPA may still work

    def _reset_s2(self) -> bool:
        """S2: ensure K8s path is drained and Knative KPA scales to zero."""
        # Remove any lingering HPA and scale warm deployment down.
        _kubectl(["delete", "hpa", HPA_NAME, "--ignore-not-found"])
        r = _kubectl(["scale", f"deployment/{DEPLOYMENT}", "--replicas=0"])
        if r.returncode != 0:
            logger.error("scale_s2_to_zero_failed", stderr=r.stderr.strip())
            return False

        for _ in range(20):
            time.sleep(3)
            dr = _kubectl(["get", f"deployment/{DEPLOYMENT}", "-o", "json"])
            if dr.returncode == 0:
                dep = json.loads(dr.stdout)
                available = dep.get("status", {}).get("availableReplicas", 0) or 0
                if available == 0:
                    logger.info("k8s_scaled_to_zero")
                    break

        # Knative annotations should already be set; verify pods are zero.
        for attempt in range(12):
            r = _kubectl(["get", "pods", "-l", "serving.knative.dev/service=test-app", "-o", "json"])
            if r.returncode == 0:
                pods = json.loads(r.stdout).get("items", [])
                running = [p for p in pods if p.get("status", {}).get("phase") == "Running"]
                if len(running) == 0:
                    logger.info("knative_scaled_to_zero")
                    return True
                logger.debug("knative_pods_still_running", count=len(running))
            time.sleep(10)
        logger.warning("knative_scale_to_zero_timeout")
        return True  # Proceed anyway

    def _reset_s3_s4(self) -> bool:
        """S3/S4: delete HPA, scale to baseline (3 replicas), wait ready."""
        # Delete HPA
        _kubectl(["delete", "hpa", DEPLOYMENT, "--ignore-not-found"])
        time.sleep(2)

        baseline_replicas = 2
        r = _kubectl(["scale", f"deployment/{DEPLOYMENT}", f"--replicas={baseline_replicas}"])
        if r.returncode != 0:
            logger.error("scale_baseline_failed", stderr=r.stderr.strip())
            return False

        # Wait for readyReplicas >= baseline
        for _ in range(30):
            time.sleep(2)
            dr = _kubectl(["get", f"deployment/{DEPLOYMENT}", "-o", "json"])
            if dr.returncode == 0:
                dep = json.loads(dr.stdout)
                available = dep.get("status", {}).get("availableReplicas", 0) or 0
                if available >= baseline_replicas:
                    logger.info("baseline_replicas_ready", replicas=baseline_replicas)
                    return True
        logger.warning(
            "baseline_replicas_timeout",
            available=available,
            target=baseline_replicas,
            note="continuing anyway — V3 handles 0 replicas",
        )
        return True

    @staticmethod
    def _reset_haproxy_weights(scenario: str) -> bool:
        """Reset HAProxy weights via admin socket and verify via stats CSV."""
        weight_map = {
            "s1-k8s-only": (100, 0),
            "s2-serverless-only": (0, 100),
            "s3-hybrid-reactive": (80, 20),
            "s4-hybrid-predictive": (80, 20),
        }
        k3s_w, kn_w = weight_map.get(scenario, (100, 0))
        import socket as _socket

        try:
            reset_sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
            reset_sock.settimeout(5)
            reset_sock.connect((HAPROXY_HOST, HAPROXY_SOCKET_PORT))
            reset_sock.send(b"clear counters all\n")
            reset_sock.recv(4096)
            reset_sock.close()
            for server, weight in [("k3s", k3s_w), ("knative", kn_w)]:
                sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((HAPROXY_HOST, HAPROXY_SOCKET_PORT))
                sock.send(f"set server servers/{server} weight {weight}\n".encode())
                resp = sock.recv(4096).decode().strip()
                sock.close()
                if "no such" in resp.lower() or "error" in resp.lower():
                    logger.error("haproxy_set_weight_rejected", server=server, response=resp)
                    return False
        except Exception as e:
            logger.error("haproxy_weight_reset_failed", error=str(e))
            return False

        # Verify weights via stats CSV
        time.sleep(0.5)
        actual = _parse_haproxy_stats_weights()
        if actual is None:
            logger.error("haproxy_weight_verify_failed", reason="could not read stats CSV")
            return False
        if actual.get("k3s") != k3s_w or actual.get("knative") != kn_w:
            logger.error("haproxy_weight_mismatch", expected={"k3s": k3s_w, "knative": kn_w}, actual=actual)
            return False
        logger.info("haproxy_weights_reset_verified", k3s=k3s_w, knative=kn_w)
        return True


# ---------------------------------------------------------------------------
# Daemon management  (s2-i72 fix: log to files, not PIPE)
# ---------------------------------------------------------------------------


class DaemonManager:
    """Start/stop the routing daemon with proper IO handling."""

    @staticmethod
    def _kill_stale_daemon() -> None:
        """Kill any process listening on DAEMON_API_PORT before starting fresh."""
        import socket as _socket

        try:
            sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect(("localhost", DAEMON_API_PORT))
            sock.close()
        except (ConnectionRefusedError, OSError):
            return  # Port free — nothing to kill

        logger.warning("stale_daemon_detected", port=DAEMON_API_PORT)
        try:
            r = subprocess.run(
                ["ss", "-tlnp", f"sport = :{DAEMON_API_PORT}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in r.stdout.strip().split("\n"):
                if f":{DAEMON_API_PORT}" in line and "pid=" in line:
                    pid_str = line.split("pid=")[1].split(",")[0]
                    pid = int(pid_str)
                    logger.warning("killing_stale_daemon", pid=pid)
                    os.kill(pid, signal.SIGKILL)
                    time.sleep(1)
        except Exception as e:
            logger.warning("stale_daemon_kill_failed", error=str(e))

    def start(self, scenario: str, log_path: Path) -> Optional[subprocess.Popen]:
        self._kill_stale_daemon()

        cmd = [
            sys.executable,
            "-m",
            "daemon.routing_daemon",
            "--scenario",
            scenario,
            "--haproxy-host",
            HAPROXY_HOST,
            "--haproxy-port",
            str(HAPROXY_SOCKET_PORT),
            "--haproxy-stats",
            HAPROXY_STATS_URL,
            "--gru-url",
            GRU_URL,
            "--interval",
            "15",
            "--api-port",
            str(DAEMON_API_PORT),
        ]
        env = {**os.environ, "HSA_OVERRIDE_GFX_VERSION": "11.0.0", "KUBECTL_PATH": KUBECTL_PATH}

        log_file = open(log_path, "w")
        proc = subprocess.Popen(
            cmd,
            cwd=str(CONTROLLER_DIR),
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        proc._log_file = log_file  # type: ignore[attr-defined]

        # Wait for daemon API + validate scenario and freshness
        for _ in range(20):
            time.sleep(1)
            try:
                r = requests.get(f"{DAEMON_API}/health", timeout=3)
                if r.status_code == 200:
                    health = r.json()
                    if health.get("scenario") != scenario:
                        logger.error("daemon_scenario_mismatch", expected=scenario, got=health.get("scenario"))
                        self.stop(proc)
                        return None
                    # Verify freshness via /status uptime
                    sr = requests.get(f"{DAEMON_API}/status", timeout=3)
                    if sr.status_code == 200:
                        status = sr.json()
                        if status.get("uptime_seconds", 999) > 30:
                            logger.error("daemon_not_fresh", uptime=status.get("uptime_seconds"))
                            self.stop(proc)
                            return None
                    logger.info("daemon_started", scenario=scenario, pid=proc.pid)
                    return proc
            except Exception:
                pass

        logger.error("daemon_failed_to_start", scenario=scenario)
        self.stop(proc)
        return None

    @staticmethod
    def stop(proc: Optional[subprocess.Popen]) -> None:
        if proc is None:
            return
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except (ProcessLookupError, OSError):
            proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, OSError):
                proc.kill()
            proc.wait()
        if hasattr(proc, "_log_file"):
            proc._log_file.close()  # type: ignore[attr-defined]
        logger.info("daemon_stopped")

    @staticmethod
    def get_status() -> Optional[Dict]:
        try:
            r = requests.get(f"{DAEMON_API}/status", timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None


# ---------------------------------------------------------------------------
# k6 runner  (s2-5l9, s2-gk8)
# ---------------------------------------------------------------------------


class K6Runner:
    """Run k6 ClarkNet trace replay and capture output."""

    def run(self, scenario: str, run_id: int, results_dir: Path) -> Optional[Dict]:
        """Execute k6 and return parsed metrics dict."""
        k6_results_dir = results_dir / "k6"
        k6_results_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            K6_PATH,
            "run",
            "--out",
            "json=/dev/null",  # disable verbose json streaming
            "-e",
            f"TARGET_URL={TARGET_URL}",
            "-e",
            f"ENDPOINT={K6_ENDPOINT}",
            "-e",
            f"SCENARIO={scenario}",
            "-e",
            f"RUN_ID={run_id}",
            "-e",
            f"RESULTS_DIR={k6_results_dir}",
            "-e",
            f"K6_STAGES_PATH={K6_STAGES}",
            str(K6_SCRIPT),
        ]

        logger.info("k6_start", scenario=scenario, run_id=run_id)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800,  # 30 min max
            cwd=str(PROJECT_ROOT),
        )

        # k6 exit code 99 = thresholds crossed (test completed, data valid)
        if result.returncode not in (0, 99):
            logger.error("k6_failed", returncode=result.returncode, stderr=result.stderr[:500])
            return None
        if result.returncode == 99:
            logger.warning("k6_threshold_crossed", scenario=scenario, run_id=run_id)

        # k6 handleSummary saves the detailed JSON to k6_results_dir.
        # Read the saved file (stdout contains k6 banner + summary text).
        k6_files = sorted(k6_results_dir.glob("clarknet_replay_*.json"))
        if not k6_files:
            logger.error("k6_no_output_file", dir=str(k6_results_dir))
            return None

        try:
            with open(k6_files[-1]) as f:
                raw = json.load(f)
            summary = self._extract_metrics(raw, scenario, run_id)
            logger.info(
                "k6_complete",
                scenario=scenario,
                run_id=run_id,
                p99=summary.get("metrics", {}).get("p99_latency_ms"),
                total_requests=summary.get("metrics", {}).get("total_requests"),
            )
            return summary
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("k6_parse_failed", error=str(e), file=str(k6_files[-1]))
            return None

    @staticmethod
    def _extract_metrics(raw: Dict, scenario: str, run_id: int) -> Dict:
        """Extract structured metrics from raw k6 handleSummary JSON."""
        m = raw.get("metrics", {})
        dur = m.get("http_req_duration", {}).get("values", {})
        reqs = m.get("http_reqs", {}).get("values", {})
        errs = m.get("errors", {})
        slo = m.get("slo_violations", {}).get("values", {})

        p99 = dur.get("p(99)")
        p95 = dur.get("p(95)") or 0
        if p99 is None:
            p99 = p95  # k6 raw JSON may omit p99; fall back to p95

        return {
            "scenario": scenario,
            "run_id": run_id,
            "metrics": {
                "p50_latency_ms": dur.get("med") or 0,
                "p95_latency_ms": p95,
                "p99_latency_ms": p99,
                "avg_latency_ms": dur.get("avg") or 0,
                "max_latency_ms": dur.get("max") or 0,
                "error_rate": errs.get("rate", 0) if isinstance(errs, dict) else 0,
                "total_requests": reqs.get("count") or 0,
                "actual_rps": reqs.get("rate") or 0,
                "slo_violations": slo.get("count") or 0,
                "app_duration_avg_ms": m.get("app_duration_ms", {}).get("values", {}).get("avg") or 0,
                "app_duration_p50_ms": m.get("app_duration_ms", {}).get("values", {}).get("p(50)") or 0,
                "app_duration_p95_ms": m.get("app_duration_ms", {}).get("values", {}).get("p(95)") or 0,
                "app_duration_serverless_avg_ms": m.get("app_duration_serverless_ms", {}).get("values", {}).get("avg")
                or 0,
                "app_duration_serverless_p95_ms": m.get("app_duration_serverless_ms", {}).get("values", {}).get("p(95)")
                or 0,
                "app_duration_k8s_avg_ms": m.get("app_duration_k8s_ms", {}).get("values", {}).get("avg") or 0,
            },
        }


# ---------------------------------------------------------------------------
# Metric exporter  (s2-3mc, s2-dx8)
# ---------------------------------------------------------------------------


class MetricExporter:
    """Export time-series metrics from Prometheus for a run window."""

    # Queries aligned with thesis Tables 3-4..3-7
    QUERIES = {
        # Performance (corroboration)
        "prom_p99_ms": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[1m])) by (le)) * 1000",
        "prom_rps": "sum(rate(http_requests_total[1m]))",
        # Routing daemon
        "daemon_decisions": "routing_daemon_decision_total",
        "daemon_weight_k3s": 'routing_daemon_current_weight{backend="k3s"}',
        "daemon_weight_knative": 'routing_daemon_current_weight{backend="knative"}',
        "daemon_predictions_used": "routing_daemon_prediction_used_total",
        "daemon_predictions_failed": "routing_daemon_prediction_failed_total",
        # Algorithm 2 replica scaling
        "k8s_desired_replicas": f"k8s_deployment_desired_replicas{{{K8S_DEPLOYMENT_FILTER}}}",
        "k8s_available_replicas": f"k8s_deployment_available_replicas{{{K8S_DEPLOYMENT_FILTER}}}",
        "k8s_scale_up_success": 'k8s_scaling_events_total{direction="up",result="success"}',
        "k8s_scale_up_fail": 'k8s_scaling_events_total{direction="up",result="fail"}',
        "k8s_scale_down_success": 'k8s_scaling_events_total{direction="down",result="success"}',
        "k8s_scale_down_fail": 'k8s_scaling_events_total{direction="down",result="fail"}',
        # Control-loop metrics (Table 3-5)
        "daemon_decision_latency_ms": "routing_daemon_decision_latency_ms_sum / routing_daemon_decision_latency_ms_count",
        # Resource metrics (Table 3-7)
        "cpu_usage_cores": 'sum(rate(container_cpu_usage_seconds_total{namespace="default",container="test-app-warm"}[1m]))',
        "memory_usage_bytes": 'sum(container_memory_working_set_bytes{namespace="default",container="test-app-warm"})',
        # Node provisioning metrics (v4)
        "node_count_schedulable": "count(kube_node_spec_unschedulable == 0)",
        "pods_pending_count": 'count(kube_pod_status_phase{phase="Pending",namespace="default"})',
    }

    def export_run(self, t_start: float, t_end: float, output_dir: Path) -> Dict[str, Any]:
        """Export all metrics for [t_start, t_end] window. Returns summary dict."""
        output_dir.mkdir(parents=True, exist_ok=True)
        series = {}

        for name, expr in self.QUERIES.items():
            ts = _prom_query_range(expr, t_start, t_end, step="15s")
            series[name] = ts

        # Save raw time-series
        export_path = output_dir / "prometheus_export.json"
        with open(export_path, "w") as f:
            json.dump({k: [(t, v) for t, v in vs] for k, vs in series.items()}, f, indent=2)

        # Derive summary values
        summary = self._summarize(series, t_start, t_end)
        summary["export_path"] = str(export_path)
        return summary

    def _summarize(self, series: Dict, t_start: float, t_end: float) -> Dict[str, Any]:
        """Derive scalar summary from time-series."""
        duration = max(1, t_end - t_start)

        def _last_val(key: str) -> float:
            ts = series.get(key, [])
            return ts[-1][1] if ts else 0.0

        def _mean_val(key: str) -> float:
            ts = series.get(key, [])
            vals = [v for _, v in ts if np.isfinite(v)]
            return float(np.mean(vals)) if vals else 0.0

        def _counter_delta(key: str) -> float:
            ts = series.get(key, [])
            if len(ts) < 2:
                return 0.0
            return max(0, ts[-1][1] - ts[0][1])

        # Weight time products (integral via trapezoidal)
        k3s_wt = self._weight_time_integral(series.get("daemon_weight_k3s", []))
        kn_wt = self._weight_time_integral(series.get("daemon_weight_knative", []))

        # Time in serverless = fraction of time knative weight > 0
        kn_series = series.get("daemon_weight_knative", [])
        time_in_serverless = sum(1 for _, v in kn_series if v > 0) / max(1, len(kn_series))

        # Weight change count
        k3s_ts = series.get("daemon_weight_k3s", [])
        weight_changes = sum(1 for i in range(1, len(k3s_ts)) if k3s_ts[i][1] != k3s_ts[i - 1][1])

        # k8s_replica_seconds: trapezoidal integral of desired replicas × time
        k8s_replica_seconds = self._weight_time_integral(series.get("k8s_desired_replicas", []))

        # knative_active_seconds: sum of time intervals where knative weight > 0
        knative_active_seconds = 0.0
        for i in range(1, len(kn_series)):
            if kn_series[i][1] > 0 or kn_series[i - 1][1] > 0:
                knative_active_seconds += kn_series[i][0] - kn_series[i - 1][0]

        # Oscillation index: direction changes in desired_replicas series
        desired_ts = series.get("k8s_desired_replicas", [])
        oscillations = 0
        for i in range(2, len(desired_ts)):
            prev_dir = desired_ts[i - 1][1] - desired_ts[i - 2][1]
            curr_dir = desired_ts[i][1] - desired_ts[i - 1][1]
            if (prev_dir > 0 and curr_dir < 0) or (prev_dir < 0 and curr_dir > 0):
                oscillations += 1

        # Scale-up latency: time from first scale-up event to ready replicas matching desired
        avail_ts = series.get("k8s_available_replicas", [])
        scale_up_latency = 0.0
        if desired_ts and avail_ts:
            initial_desired = desired_ts[0][1] if desired_ts else 0
            first_scale_up_t = next((t for t, v in desired_ts if v > initial_desired), None)
            if first_scale_up_t is not None:
                target_at_scale = next((v for t, v in desired_ts if t >= first_scale_up_t), initial_desired)
                ready_t = next((t for t, v in avail_ts if t >= first_scale_up_t and v >= target_at_scale), None)
                if ready_t is not None:
                    scale_up_latency = ready_t - first_scale_up_t

        return {
            "prom_p99_ms": _mean_val("prom_p99_ms"),
            "scale_up_success": int(_counter_delta("k8s_scale_up_success")),
            "scale_down_success": int(_counter_delta("k8s_scale_down_success")),
            "scale_up_fail": int(_counter_delta("k8s_scale_up_fail")),
            "scale_down_fail": int(_counter_delta("k8s_scale_down_fail")),
            "desired_replicas_final": int(_last_val("k8s_desired_replicas")),
            "available_replicas_final": int(_last_val("k8s_available_replicas")),
            "predictions_used": int(_counter_delta("daemon_predictions_used")),
            "predictions_failed": int(_counter_delta("daemon_predictions_failed")),
            "k8s_weight_time": k3s_wt,
            "kn_weight_time": kn_wt,
            "time_in_serverless_pct": time_in_serverless * 100,
            "weight_change_count": weight_changes,
            "daemon_decision_latency_avg_ms": _mean_val("daemon_decision_latency_ms"),
            "cpu_usage_avg_cores": _mean_val("cpu_usage_cores"),
            "memory_usage_avg_bytes": _mean_val("memory_usage_bytes"),
            "k8s_replica_seconds": k8s_replica_seconds,
            "knative_active_seconds": knative_active_seconds,
            "oscillation_index": oscillations,
            "scale_up_latency_sec": scale_up_latency,
        }

    @staticmethod
    def _weight_time_integral(ts: List[Tuple[float, float]]) -> float:
        """Trapezoidal integration of weight × time."""
        if len(ts) < 2:
            return 0.0
        total = 0.0
        for i in range(1, len(ts)):
            dt = ts[i][0] - ts[i - 1][0]
            avg_w = (ts[i][1] + ts[i - 1][1]) / 2
            total += avg_w * dt
        return total


# ---------------------------------------------------------------------------
# Statistical analysis  (s2-sm0)
# ---------------------------------------------------------------------------


class StatisticalAnalyzer:
    """Welch t-test, Mann-Whitney U, bootstrap CI, Cohen's d, outlier detection."""

    OUTLIER_P99_FLOOR_MS = 0.0  # disabled; low-latency can be legitimate for S2

    def detect_outliers(self, results: List[ExperimentResult]) -> Tuple[List[ExperimentResult], List[ExperimentResult]]:
        """Returns (clean, excluded) results."""
        clean, excluded = [], []
        for r in results:
            if (
                r.total_requests <= 0
                or r.p99_latency_ms <= self.OUTLIER_P99_FLOOR_MS
                or not np.isfinite(r.p99_latency_ms)
            ):
                excluded.append(r)
                logger.warning(
                    "outlier_detected",
                    scenario=r.scenario,
                    run_id=r.run_id,
                    p99=r.p99_latency_ms,
                    reason="invalid/empty metrics",
                )
            else:
                clean.append(r)
        return clean, excluded

    def compare(
        self,
        results: List[ExperimentResult],
        baseline: str,
        comparison: str,
        metric: str,
    ) -> StatisticalComparison:
        baseline_vals = [getattr(r, metric) for r in results if r.scenario == baseline]
        comp_vals = [getattr(r, metric) for r in results if r.scenario == comparison]

        if not baseline_vals or not comp_vals:
            raise ValueError(f"Insufficient data for {baseline} vs {comparison} on {metric}")

        # Welch's t-test
        t_stat, t_p = scipy_stats.ttest_ind(comp_vals, baseline_vals, equal_var=False)

        # Mann-Whitney U
        try:
            u_stat, u_p = scipy_stats.mannwhitneyu(comp_vals, baseline_vals, alternative="two-sided")
        except ValueError:
            u_stat, u_p = 0.0, 1.0

        # Bootstrap 95% CI (10000 resamples)
        diffs = []
        rng = np.random.default_rng(seed=42)
        for _ in range(10000):
            bs = rng.choice(baseline_vals, size=len(baseline_vals), replace=True)
            cs = rng.choice(comp_vals, size=len(comp_vals), replace=True)
            diffs.append(np.mean(cs) - np.mean(bs))
        ci_lo, ci_hi = np.percentile(diffs, [2.5, 97.5])

        # Cohen's d
        pooled_std = np.sqrt((np.std(baseline_vals, ddof=1) ** 2 + np.std(comp_vals, ddof=1) ** 2) / 2)
        d = (np.mean(comp_vals) - np.mean(baseline_vals)) / pooled_std if pooled_std > 0 else 0.0

        if abs(d) < 0.2:
            interp = "negligible"
        elif abs(d) < 0.5:
            interp = "small"
        elif abs(d) < 0.8:
            interp = "medium"
        else:
            interp = "large"

        base_mean = float(np.mean(baseline_vals))
        comp_mean = float(np.mean(comp_vals))

        return StatisticalComparison(
            baseline_scenario=baseline,
            comparison_scenario=comparison,
            metric=metric,
            baseline_mean=base_mean,
            comparison_mean=comp_mean,
            difference=comp_mean - base_mean,
            percent_change=((comp_mean - base_mean) / base_mean * 100) if base_mean != 0 else 0,
            welch_t_stat=float(t_stat),
            welch_p_value=float(t_p),
            mannwhitney_u_stat=float(u_stat),
            mannwhitney_p_value=float(u_p),
            ci_lower=float(ci_lo),
            ci_upper=float(ci_hi),
            cohens_d=float(d),
            effect_size_interpretation=interp,
            n_baseline=len(baseline_vals),
            n_comparison=len(comp_vals),
        )


# ---------------------------------------------------------------------------
# Resource utilization poller  (s2-a2k)
# ---------------------------------------------------------------------------


class ResourcePoller:
    """Poll kubectl metrics-server API for per-pod CPU/memory during experiment runs."""

    def __init__(self, poll_interval_sec: int = 15):
        self._poll_interval = poll_interval_sec
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._samples: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    @staticmethod
    def _parse_cpu(value: str) -> float:
        """Parse Kubernetes CPU string to millicores. E.g. '882019n' → 0.882, '1m' → 1.0."""
        try:
            if value.endswith("n"):
                return int(value[:-1]) / 1_000_000
            if value.endswith("u"):
                return int(value[:-1]) / 1000
            if value.endswith("m"):
                return int(value[:-1])
            return float(value) * 1000
        except (ValueError, IndexError):
            return 0.0

    @staticmethod
    def _parse_memory(value: str) -> float:
        """Parse Kubernetes memory string to MiB. E.g. '40144Ki' → ~39.2."""
        if value.endswith("Ki"):
            return int(value[:-2]) / 1024
        if value.endswith("Mi"):
            return int(value[:-2])
        if value.endswith("Gi"):
            return int(value[:-2]) * 1024
        return int(value) / (1024 * 1024)

    def _poll_once(self) -> None:
        """Single poll of metrics-server API via kubectl."""
        try:
            r = _run_cmd(
                [KUBECTL_PATH, "get", "--raw", "/apis/metrics.k8s.io/v1beta1/namespaces/default/pods"],
                timeout=10,
            )
            if r.returncode != 0:
                return
            data = json.loads(r.stdout)
            ts = time.time()
            for item in data.get("items", []):
                labels = item.get("metadata", {}).get("labels", {})
                pod_name = item.get("metadata", {}).get("name", "")
                is_k8s = labels.get("app") == "test-app-warm"
                is_knative = "serving.knative.dev/service" in labels
                if not (is_k8s or is_knative):
                    continue
                for container in item.get("containers", []):
                    cpu_str = container.get("usage", {}).get("cpu", "0n")
                    mem_str = container.get("usage", {}).get("memory", "0Ki")
                    sample = {
                        "timestamp": ts,
                        "pod": pod_name,
                        "backend": "k8s" if is_k8s else "knative",
                        "cpu_millicores": self._parse_cpu(cpu_str),
                        "memory_mib": self._parse_memory(mem_str),
                    }
                    with self._lock:
                        self._samples.append(sample)
        except Exception as e:
            logger.debug("resource_poll_failed", error=str(e))

    def _poll_loop(self) -> None:
        """Background polling loop."""
        while not self._stop_event.is_set():
            self._poll_once()
            self._stop_event.wait(self._poll_interval)

    def start(self) -> None:
        """Start background polling thread."""
        with self._lock:
            self._samples = []
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop background polling thread."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    def get_summary(self, output_dir: Path) -> Dict[str, float]:
        """Compute avg/peak CPU and memory, save raw samples to JSON."""
        with self._lock:
            samples = list(self._samples)

        output_dir.mkdir(parents=True, exist_ok=True)
        save_path = output_dir / "resource_utilization.json"
        with open(save_path, "w") as f:
            json.dump(samples, f, indent=2)

        if not samples:
            return {
                "avg_cpu_millicores": 0.0,
                "peak_cpu_millicores": 0.0,
                "avg_memory_mib": 0.0,
                "peak_memory_mib": 0.0,
                "resource_utilization_path": str(save_path),
            }

        # Aggregate per-timestamp (sum across pods), then compute avg/peak
        from collections import defaultdict

        ts_cpu: Dict[float, float] = defaultdict(float)
        ts_mem: Dict[float, float] = defaultdict(float)
        for s in samples:
            ts_cpu[s["timestamp"]] += s["cpu_millicores"]
            ts_mem[s["timestamp"]] += s["memory_mib"]

        cpu_vals = list(ts_cpu.values())
        mem_vals = list(ts_mem.values())

        return {
            "avg_cpu_millicores": float(np.mean(cpu_vals)),
            "peak_cpu_millicores": float(max(cpu_vals)),
            "avg_memory_mib": float(np.mean(mem_vals)),
            "peak_memory_mib": float(max(mem_vals)),
            "resource_utilization_path": str(save_path),
        }


# ---------------------------------------------------------------------------
# Main experiment runner
# ---------------------------------------------------------------------------


class ExperimentRunner:
    """Orchestrates Phase B experiments per methodology Section 3.5."""

    def __init__(self, output_dir: str = "results/experiments/phase-b"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.preflight = PreflightChecker()
        self.resetter = ScenarioResetter()
        self.daemon = DaemonManager()
        self.k6 = K6Runner()
        self.exporter = MetricExporter()
        self.provisioner = K3dAutoscalerAdapter(
            cluster_name="thesis-hybrid",
            min_nodes=0,
            max_nodes=2,
            provision_delay_min_sec=45,
            provision_delay_max_sec=120,
            node_memory="1g",
            namespace="default",
        )
        self.analyzer = StatisticalAnalyzer()
        self.resource_poller = ResourcePoller()

    def run_single(
        self,
        scenario: str,
        run_id: int,
        run_order_idx: int,
        seed: int,
    ) -> Optional[ExperimentResult]:
        """Execute a single experiment run with full protocol."""
        run_dir = self.output_dir / f"{scenario}_run{run_id}"
        if run_dir.exists():
            shutil.rmtree(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)

        logger.info("run_start", scenario=scenario, run_id=run_id, order=run_order_idx)

        # (B) Per-run reset
        if not self.resetter.reset(scenario, self.provisioner):
            logger.error("reset_failed", scenario=scenario)
            return None

        # Clear autoscaler event log so this run gets its own events
        self.provisioner.clear_log()

        # Start daemon (S1/S2 still need daemon for metrics even if no algorithm)
        daemon_log = run_dir / "daemon.log"
        daemon_proc = self.daemon.start(scenario, daemon_log)
        if daemon_proc is None:
            return None

        if scenario != "s2-serverless-only":
            self.provisioner.start_background()

        try:
            # Save manifest  (s2-20e)
            manifest = RunManifest(
                scenario=scenario,
                run_id=run_id,
                run_order_idx=run_order_idx,
                random_seed=seed,
                git_commit=_git_commit_hash(),
                k6_script=str(K6_SCRIPT),
                k6_stages_json=str(K6_STAGES),
                replay_manifest=json.loads(REPLAY_MANIFEST.read_text()) if REPLAY_MANIFEST.exists() else {},
                daemon_config={
                    "interval": 15,
                    "haproxy_host": HAPROXY_HOST,
                    "haproxy_port": HAPROXY_SOCKET_PORT,
                    "gru_url": GRU_URL,
                    "endpoint": K6_ENDPOINT,
                    "gomaxprocs": 1,
                    "fib_n": 34,
                },
                scaling_config={"alpha": 0.04, "beta": 0.0, "buffer": 1.2, "min_replicas": 1, "max_replicas": 10},
                timestamp=datetime.now().isoformat(),
            )
            with open(run_dir / "manifest.json", "w") as f:
                json.dump(asdict(manifest), f, indent=2)

            # (C.warm-up) 30s idle warm-up
            logger.info("warmup_start", seconds=WARMUP_SEC)
            time.sleep(WARMUP_SEC)

            # (C.pre) Validate pre-run invariants before k6
            if not self._validate_run_preconditions(scenario):
                logger.error("precondition_check_failed", scenario=scenario, run_id=run_id)
                return None

            # Record t_start and begin resource polling
            t_start = time.time()
            self.resource_poller.start()

            # (C.2) Execute k6 trace replay
            k6_summary = self.k6.run(scenario, run_id, run_dir)

            # (C.3) Post-k6 cooldown to capture delayed scaling effects
            logger.info("cooldown_start", seconds=COOLDOWN_SEC)
            time.sleep(COOLDOWN_SEC)

            # Stop resource poller before recording t_end
            self.resource_poller.stop()

            # Record t_end
            t_end = time.time()

            provision_events_raw = self.provisioner.get_log()
            # Filter to events within this run's time window (guardrail)
            provision_events = [e for e in provision_events_raw if e[0] >= t_start - 60]
            provision_log_path = run_dir / "provision_events.json"
            with open(provision_log_path, "w") as f:
                json.dump(provision_events, f, indent=2, default=str)

            first_pending_ts = next((e[0] for e in provision_events if e[1] == "pending_detected"), None)
            first_provisioned_ts = next(
                (e[0] for e in provision_events if e[1] in ("node_provisioned", "node_created")), None
            )
            first_provision_delay_sec = (
                max(0.0, first_provisioned_ts - first_pending_ts)
                if first_pending_ts is not None and first_provisioned_ts is not None
                else 0.0
            )

            # Get daemon status before stopping
            daemon_status = self.daemon.get_status() or {}

            # (D) Export Prometheus metrics for [t_start, t_end]
            prom_summary = self.exporter.export_run(t_start, t_end, run_dir / "prometheus")

            # Find k6 summary file
            k6_files = list((run_dir / "k6").glob("clarknet_replay_*.json")) if (run_dir / "k6").exists() else []
            k6_summary_path = str(k6_files[0]) if k6_files else ""

            # (D.2) For S1, collect HPA/deployment replica metrics via kubectl
            #       (daemon Algorithm 2 metrics are only emitted for S3/S4)
            if scenario == "s1-k8s-only":
                hpa_metrics = self._collect_hpa_metrics()
                if hpa_metrics:
                    prom_summary.update(hpa_metrics)

            # Collect resource utilization from poller
            resource_summary = self.resource_poller.get_summary(run_dir)

            # Build result
            k6m = k6_summary.get("metrics", {}) if k6_summary else {}
            replay_manifest = json.loads(REPLAY_MANIFEST.read_text()) if REPLAY_MANIFEST.exists() else {}

            result = ExperimentResult(
                scenario=scenario,
                run_id=run_id,
                timestamp=datetime.now().isoformat(),
                # k6 primary metrics
                p50_latency_ms=k6m.get("p50_latency_ms", 0),
                p95_latency_ms=k6m.get("p95_latency_ms", 0),
                p99_latency_ms=k6m.get("p99_latency_ms", 0),
                error_rate=k6m.get("error_rate", 0),
                throughput_rps=k6m.get("actual_rps", 0),
                total_requests=k6m.get("total_requests", 0),
                slo_violations_k6=k6m.get("slo_violations", 0),
                app_duration_avg_ms=k6m.get("app_duration_avg_ms", 0),
                app_duration_p50_ms=k6m.get("app_duration_p50_ms", 0),
                app_duration_p95_ms=k6m.get("app_duration_p95_ms", 0),
                app_duration_serverless_avg_ms=k6m.get("app_duration_serverless_avg_ms", 0),
                app_duration_serverless_p95_ms=k6m.get("app_duration_serverless_p95_ms", 0),
                app_duration_k8s_avg_ms=k6m.get("app_duration_k8s_avg_ms", 0),
                # Prometheus corroboration
                prom_p99_latency_ms=prom_summary.get("prom_p99_ms", 0),
                # Routing metrics
                maintain_count=daemon_status.get("maintain_count", 0),
                scale_out_count=daemon_status.get("scale_out_count", 0),
                predictive_count=daemon_status.get("predictive_count", 0),
                optimize_cost_count=daemon_status.get("optimize_cost_count", 0),
                weight_change_count=prom_summary.get("weight_change_count", 0),
                time_in_serverless_pct=prom_summary.get("time_in_serverless_pct", 0),
                control_loop_latency_avg_ms=prom_summary.get("daemon_decision_latency_avg_ms", 0),
                # Algorithm 2
                scale_up_events=prom_summary.get("scale_up_success", 0) + prom_summary.get("scale_up_fail", 0),
                scale_down_events=prom_summary.get("scale_down_success", 0) + prom_summary.get("scale_down_fail", 0),
                scale_up_success=prom_summary.get("scale_up_success", 0),
                scale_down_success=prom_summary.get("scale_down_success", 0),
                desired_replicas_final=prom_summary.get("desired_replicas_final", 0),
                available_replicas_final=prom_summary.get("available_replicas_final", 0),
                scale_up_latency_sec=prom_summary.get("scale_up_latency_sec", 0),
                oscillation_index=prom_summary.get("oscillation_index", 0),
                # Cost proxy
                k8s_weight_time_product=prom_summary.get("k8s_weight_time", 0),
                serverless_weight_time_product=prom_summary.get("kn_weight_time", 0),
                k8s_replica_seconds=prom_summary.get("k8s_replica_seconds", 0),
                knative_active_seconds=prom_summary.get("knative_active_seconds", 0),
                # GRU
                gru_predictions_used=prom_summary.get("predictions_used", 0),
                gru_predictions_failed=prom_summary.get("predictions_failed", 0),
                # Resource utilization (metrics-server)
                avg_cpu_millicores=resource_summary.get("avg_cpu_millicores", 0),
                peak_cpu_millicores=resource_summary.get("peak_cpu_millicores", 0),
                avg_memory_mib=resource_summary.get("avg_memory_mib", 0),
                peak_memory_mib=resource_summary.get("peak_memory_mib", 0),
                resource_utilization_path=resource_summary.get("resource_utilization_path", ""),
                # Run metadata
                duration_sec=replay_manifest.get("duration_sec", 1200),
                t_start=t_start,
                t_end=t_end,
                k6_summary_path=k6_summary_path,
                daemon_log_path=str(daemon_log),
                prom_export_path=prom_summary.get("export_path", ""),
                replica_timeline_path=str(run_dir / "prometheus" / "prometheus_export.json"),
                nodes_provisioned=len([e for e in provision_events if e[1] in ("node_provisioned", "node_created")]),
                first_provision_delay_sec=first_provision_delay_sec,
                total_provision_events=len(provision_events),
                provision_log_path=str(provision_log_path),
            )

            # Multi-node validity evidence and gating
            pod_snapshot = self._collect_pod_node_snapshot()
            result.k8s_pod_nodes = pod_snapshot.get("k8s_pod_nodes", [])
            result.knative_pod_nodes = pod_snapshot.get("knative_pod_nodes", [])
            result.distinct_workload_nodes = pod_snapshot.get("distinct_workload_nodes", 0)
            result.dynamic_node_pod_count = pod_snapshot.get("dynamic_node_pod_count", 0)
            result.cross_node_observed = pod_snapshot.get("cross_node_observed", False)
            run_ok, run_notes, stress_ok, stress_notes = self._evaluate_validity_gates(scenario, result, pod_snapshot)
            result.run_validity_passed = run_ok
            result.run_validity_notes = run_notes
            result.stress_validity_passed = stress_ok
            result.stress_validity_notes = stress_notes
            # Backward-compatible combined gate field: run validity only.
            result.validity_gate_passed = run_ok
            result.validity_gate_notes = run_notes

            # Fix 1 (s2-nsw): Compute prediction_usage_rate from daemon decision counts
            total_decisions = (
                result.maintain_count + result.scale_out_count + result.predictive_count + result.optimize_cost_count
            )
            result.prediction_usage_rate = (
                (result.gru_predictions_used / total_decisions * 100) if total_decisions > 0 else 0.0
            )

            # Save result
            with open(run_dir / "result.json", "w") as f:
                json.dump(asdict(result), f, indent=2)

            logger.info(
                "run_complete",
                scenario=scenario,
                run_id=run_id,
                p99=result.p99_latency_ms,
                error_rate=result.error_rate,
                run_valid=result.run_validity_passed,
                stress_valid=result.stress_validity_passed,
            )
            return result

        finally:
            self.resource_poller.stop()
            self.provisioner.stop()
            self.daemon.stop(daemon_proc)

    @staticmethod
    def _collect_hpa_metrics() -> Optional[Dict[str, Any]]:
        """Collect HPA and deployment replica metrics via kubectl for S1.

        The daemon's Algorithm 2 metrics are only emitted for S3/S4.
        For S1 (HPA-managed), we query Kubernetes objects directly.
        """
        metrics: Dict[str, Any] = {}
        try:
            # Deployment replicas
            dr = _kubectl(["get", f"deployment/{DEPLOYMENT}", "-o", "json"])
            if dr.returncode == 0:
                dep = json.loads(dr.stdout)
                spec_replicas = dep.get("spec", {}).get("replicas", 0) or 0
                available = dep.get("status", {}).get("availableReplicas", 0) or 0
                metrics["desired_replicas_final"] = spec_replicas
                metrics["available_replicas_final"] = available
                logger.info("hpa_kubectl_deployment", desired=spec_replicas, available=available)

            # HPA status
            hr = _kubectl(["get", f"hpa/{DEPLOYMENT}", "-o", "json"])
            if hr.returncode == 0:
                hpa = json.loads(hr.stdout)
                hpa_desired = hpa.get("status", {}).get("desiredReplicas", 0) or 0
                hpa_current = hpa.get("status", {}).get("currentReplicas", 0) or 0
                # HPA desiredReplicas is the authoritative scaling target
                metrics["desired_replicas_final"] = hpa_desired

                # Infer scale events from HPA conditions
                conditions = hpa.get("status", {}).get("conditions", [])
                for c in conditions:
                    if c.get("type") == "AbleToScale":
                        logger.info(
                            "hpa_condition",
                            type=c["type"],
                            status=c.get("status"),
                            reason=c.get("reason"),
                            message=c.get("message", "")[:120],
                        )
                logger.info("hpa_kubectl_hpa", desired=hpa_desired, current=hpa_current)

            # Scale events: count from Kubernetes events
            er = _kubectl(
                [
                    "get",
                    "events",
                    "--field-selector",
                    f"involvedObject.name={DEPLOYMENT},reason=SuccessfulRescale",
                    "-o",
                    "json",
                ],
                timeout=10,
            )
            if er.returncode == 0:
                events = json.loads(er.stdout).get("items", [])
                scale_ups = sum(
                    1
                    for e in events
                    if "up" in e.get("message", "").lower()
                    or "scaled up" in e.get("message", "").lower()
                    or "New size:" in e.get("message", "")
                )
                scale_downs = sum(
                    1
                    for e in events
                    if "down" in e.get("message", "").lower() or "scaled down" in e.get("message", "").lower()
                )
                # If message parsing didn't split, count all as scale events
                if scale_ups == 0 and scale_downs == 0 and len(events) > 0:
                    scale_ups = len(events)
                metrics["scale_up_success"] = scale_ups
                metrics["scale_down_success"] = scale_downs
                logger.info(
                    "hpa_kubectl_events", scale_ups=scale_ups, scale_downs=scale_downs, total_events=len(events)
                )

        except Exception as e:
            logger.warning("hpa_metrics_collection_failed", error=str(e))
            return None

        return metrics if metrics else None

    @staticmethod
    def _collect_pod_node_snapshot() -> Dict[str, Any]:
        """Collect pod-to-node placement evidence for run validity checks."""
        snapshot = {
            "k8s_pod_nodes": [],
            "knative_pod_nodes": [],
            "distinct_workload_nodes": 0,
            "dynamic_node_pod_count": 0,
            "cross_node_observed": False,
        }
        try:
            pods_res = _kubectl(["get", "pods", "-o", "json"], timeout=15)
            if pods_res.returncode != 0:
                return snapshot

            pods = json.loads(pods_res.stdout).get("items", [])
            k8s_nodes = set()
            knative_nodes = set()
            dynamic_count = 0

            for pod in pods:
                meta = pod.get("metadata", {})
                labels = meta.get("labels", {})
                spec = pod.get("spec", {})
                node_name = spec.get("nodeName")
                if not node_name:
                    continue

                is_k8s = labels.get("app") == "test-app-warm"
                is_knative = labels.get("serving.knative.dev/service") == "test-app"

                if is_k8s:
                    k8s_nodes.add(node_name)
                if is_knative:
                    knative_nodes.add(node_name)
                if (is_k8s or is_knative) and "dynamic-workload" in node_name:
                    dynamic_count += 1

            all_nodes = k8s_nodes | knative_nodes
            snapshot["k8s_pod_nodes"] = sorted(k8s_nodes)
            snapshot["knative_pod_nodes"] = sorted(knative_nodes)
            snapshot["distinct_workload_nodes"] = len(all_nodes)
            snapshot["dynamic_node_pod_count"] = dynamic_count
            snapshot["cross_node_observed"] = dynamic_count > 0 or len(all_nodes) >= 2
            return snapshot
        except Exception as e:
            logger.warning("pod_node_snapshot_failed", error=str(e))
            return snapshot

    @staticmethod
    def _evaluate_validity_gates(
        scenario: str,
        result: ExperimentResult,
        pod_snapshot: Dict[str, Any],
    ) -> Tuple[bool, List[str], bool, List[str]]:
        """Evaluate run-valid and stress-valid gates separately."""
        run_notes: List[str] = []
        stress_notes: List[str] = []

        # Run-validity: data integrity and scenario-consistent evidence.
        if result.total_requests <= 0:
            run_notes.append("No requests recorded")
        if scenario in ("s2-serverless-only", "s3-hybrid-reactive", "s4-hybrid-predictive"):
            if len(pod_snapshot.get("knative_pod_nodes", [])) == 0:
                run_notes.append("No Knative pod placement evidence captured")
        if scenario == "s2-serverless-only" and result.nodes_provisioned > 0:
            run_notes.append("S2 unexpectedly provisioned dynamic K8s nodes")
        if scenario == "s2-serverless-only":
            if result.desired_replicas_final > 0:
                run_notes.append("S2 has nonzero K8s desired replicas")
            if result.k8s_replica_seconds > 0:
                run_notes.append("S2 recorded K8s replica seconds")
            if len(pod_snapshot.get("k8s_pod_nodes", [])) > 0:
                run_notes.append("S2 observed K8s workload pods")
            if result.total_requests > 0 and result.app_duration_avg_ms > 0 and result.avg_cpu_millicores > 0:
                cpu_per_req_ms = (result.avg_cpu_millicores * result.duration_sec) / result.total_requests
                if cpu_per_req_ms > 0 and (result.app_duration_avg_ms / cpu_per_req_ms) > 20:
                    run_notes.append(
                        "CPU accounting mismatch: app duration much larger than metrics-server CPU/request"
                    )

        # Stress-validity: scaling challenge actually exercised.
        if scenario in ("s1-k8s-only", "s3-hybrid-reactive", "s4-hybrid-predictive"):
            if result.nodes_provisioned <= 0:
                stress_notes.append("No dynamic node provisioning events captured")
            if pod_snapshot.get("dynamic_node_pod_count", 0) <= 0:
                stress_notes.append("No workload pod observed on dynamic nodes")
            if pod_snapshot.get("distinct_workload_nodes", 0) < 2:
                stress_notes.append("Workload pods did not span at least two nodes")

        run_ok = len(run_notes) == 0
        stress_ok = len(stress_notes) == 0
        return run_ok, run_notes, stress_ok, stress_notes

    @staticmethod
    def _validate_run_preconditions(scenario: str) -> bool:
        """Validate infrastructure state before k6 load test begins."""
        ok = True

        # 1. HAProxy weights match scenario intent
        weight_expect = {
            "s1-k8s-only": {"k3s": 100, "knative": 0},
            "s2-serverless-only": {"k3s": 0, "knative": 100},
        }
        weights = _parse_haproxy_stats_weights()
        if weights is None:
            logger.error("precondition_haproxy_stats_unreadable")
            return False

        expected = weight_expect.get(scenario)
        if expected:
            if weights.get("k3s") != expected["k3s"] or weights.get("knative") != expected["knative"]:
                logger.error("precondition_haproxy_weight_wrong", scenario=scenario, expected=expected, actual=weights)
                return False
        else:
            # S3/S4 weight check: V3 may adjust during warmup, so just verify K8s is reachable
            controller_ver = os.environ.get("CONTROLLER_VERSION", "v3")
            if controller_ver == "v3":
                # V3 capacity-driven: just check K8s has weight > 0
                if weights.get("k3s", 0) <= 0:
                    logger.error("precondition_k8s_unreachable", scenario=scenario, actual=weights)
                    return False
            else:
                # V1/V2: must retain baseline 80/20 split
                expected_hybrid = {"k3s": 80, "knative": 20}
                if weights.get("k3s") != expected_hybrid["k3s"] or weights.get("knative") != expected_hybrid["knative"]:
                    logger.error(
                        "precondition_hybrid_weight_wrong", scenario=scenario, expected=expected_hybrid, actual=weights
                    )
                    return False
        # 2. Daemon /health scenario matches
        try:
            r = requests.get(f"{DAEMON_API}/health", timeout=5)
            health = r.json()
            if health.get("scenario") != scenario:
                logger.error("precondition_daemon_scenario_mismatch", expected=scenario, got=health.get("scenario"))
                return False
        except Exception as e:
            logger.error("precondition_daemon_health_failed", error=str(e))
            return False

        # 3. Daemon /status decision_count < 5 (fresh daemon)
        try:
            r = requests.get(f"{DAEMON_API}/status", timeout=5)
            status = r.json()
            if status.get("decision_count", 999) >= 5:
                logger.error("precondition_daemon_not_fresh", decision_count=status.get("decision_count"))
                return False
        except Exception as e:
            logger.error("precondition_daemon_status_failed", error=str(e))
            return False

        logger.info("preconditions_passed", scenario=scenario, weights=weights)
        return True

    def run_replicated(
        self,
        scenarios: List[str],
        num_runs: int,
        seed: int,
    ) -> List[ExperimentResult]:
        """Phase B replicated experiments with randomized order."""
        schedule = [(s, r) for s in scenarios for r in range(1, num_runs + 1)]
        rng = random.Random(seed)
        rng.shuffle(schedule)

        # Save schedule
        schedule_doc = {
            "seed": seed,
            "num_runs": num_runs,
            "scenarios": scenarios,
            "order": [{"scenario": s, "run_id": r, "idx": i} for i, (s, r) in enumerate(schedule)],
            "timestamp": datetime.now().isoformat(),
        }
        with open(self.output_dir / "experiment_schedule.json", "w") as f:
            json.dump(schedule_doc, f, indent=2)

        logger.info("experiment_schedule", total=len(schedule), seed=seed)

        results = []
        for idx, (scenario, run_id) in enumerate(schedule):
            logger.info("run_progress", current=idx + 1, total=len(schedule), scenario=scenario, run_id=run_id)

            result = self.run_single(scenario, run_id, idx, seed)
            if result:
                results.append(result)
                # Save incremental
                self._save_results(results, "results_intermediate.json")

            # Inter-run pause
            if idx < len(schedule) - 1:
                logger.info("inter_run_pause", seconds=INTER_RUN_PAUSE_SEC)
                time.sleep(INTER_RUN_PAUSE_SEC)

        self._save_results(results, "results_final.json")
        return results

    def run_analysis(self, results: List[ExperimentResult]) -> str:
        """Statistical analysis + report generation."""
        clean, excluded = self.analyzer.detect_outliers(results)

        run_invalid = [r for r in clean if not r.run_validity_passed]
        if run_invalid:
            logger.warning("run_validity_failed", count=len(run_invalid))
            clean = [r for r in clean if r.run_validity_passed]
            excluded = excluded + run_invalid

        # Primary inferential set: stress-valid for S1/S3/S4, run-valid for S2.
        analysis_set: List[ExperimentResult] = []
        for r in clean:
            if r.scenario == "s2-serverless-only":
                analysis_set.append(r)
            elif r.stress_validity_passed:
                analysis_set.append(r)

        if excluded:
            logger.warning("outliers_excluded", count=len(excluded))
            with open(self.output_dir / "excluded_runs.json", "w") as f:
                json.dump([asdict(r) for r in excluded], f, indent=2)

        comparisons = []
        pairs = [
            # Thesis §3.5.2: Platform baseline comparison
            ("s1-k8s-only", "s2-serverless-only", "p99_latency_ms"),
            ("s1-k8s-only", "s2-serverless-only", "error_rate"),
            # Thesis §3.5.2: Hybrid vs baselines
            ("s1-k8s-only", "s3-hybrid-reactive", "p99_latency_ms"),
            ("s2-serverless-only", "s3-hybrid-reactive", "p99_latency_ms"),
            # Thesis §3.5.2: Prediction value (S3 vs S4)
            ("s3-hybrid-reactive", "s4-hybrid-predictive", "p99_latency_ms"),
            ("s3-hybrid-reactive", "s4-hybrid-predictive", "slo_violations_k6"),
            # Additional: full system vs K8s baseline
            ("s1-k8s-only", "s4-hybrid-predictive", "p99_latency_ms"),
        ]

        for baseline, comp, metric in pairs:
            try:
                stat = self.analyzer.compare(analysis_set, baseline, comp, metric)
                comparisons.append(stat)
            except ValueError as e:
                logger.warning("comparison_skipped", error=str(e))

        # Save comparisons
        with open(self.output_dir / "statistical_analysis.json", "w") as f:
            json.dump([asdict(c) for c in comparisons], f, indent=2)

        # Generate report
        report = self._generate_report(clean, analysis_set, excluded, comparisons)
        report_path = self.output_dir / "report.md"
        with open(report_path, "w") as f:
            f.write(report)

        logger.info("analysis_complete", report=str(report_path))
        return report

    def _save_results(self, results: List[ExperimentResult], filename: str) -> None:
        path = self.output_dir / filename
        with open(path, "w") as f:
            json.dump([asdict(r) for r in results], f, indent=2)

    def _generate_report(
        self,
        clean: List[ExperimentResult],
        analysis_set: List[ExperimentResult],
        excluded: List[ExperimentResult],
        comparisons: List[StatisticalComparison],
    ) -> str:
        lines = [
            "# Phase B: Replicated Comparison Results",
            "",
            f"**Date:** {datetime.now().isoformat()}",
            f"**Git:** {_git_commit_hash()}",
            f"**Runs:** {len(clean)} clean, {len(excluded)} excluded",
            "",
            "## Per-Scenario Summary",
            "",
            "| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |",
            "|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|",
        ]

        for s in SCENARIOS:
            rs = [r for r in clean if r.scenario == s]
            if not rs:
                continue
            n = len(rs)
            p50 = np.mean([r.p50_latency_ms for r in rs])
            p95 = np.mean([r.p95_latency_ms for r in rs])
            p99 = np.mean([r.p99_latency_ms for r in rs])
            err = np.mean([r.error_rate for r in rs])
            rps = np.mean([r.throughput_rps for r in rs])
            slo = sum(r.slo_violations_k6 for r in rs)
            su = sum(r.scale_up_events for r in rs)
            sd = sum(r.scale_down_events for r in rs)
            lines.append(
                f"| {s} | {n} | {p50:.1f} | {p95:.1f} | {p99:.1f} | {err:.3f} | {rps:.1f} | {slo} | {su} | {sd} |"
            )

        lines.extend(["", "## Run Validity Gates", ""])
        lines.extend(
            [
                "| Scenario | Run-Valid / Total |",
                "|----------|-------------------|",
            ]
        )
        for s in SCENARIOS:
            rs = [r for r in clean + excluded if r.scenario == s]
            if not rs:
                continue
            pass_count = sum(1 for r in rs if r.run_validity_passed)
            lines.append(f"| {s} | {pass_count}/{len(rs)} |")

        lines.extend(["", "## Stress Validity Coverage", ""])
        lines.extend(
            [
                "| Scenario | Stress-Valid / Run-Valid | Dynamic Nodes (sum) | Cross-node Runs |",
                "|----------|--------------------------|---------------------|-----------------|",
            ]
        )
        for s in ("s1-k8s-only", "s3-hybrid-reactive", "s4-hybrid-predictive"):
            rs = [r for r in clean if r.scenario == s]
            if not rs:
                continue
            stress_count = sum(1 for r in rs if r.stress_validity_passed)
            dyn_sum = sum(r.nodes_provisioned for r in rs)
            cross_runs = sum(1 for r in rs if r.cross_node_observed)
            lines.append(f"| {s} | {stress_count}/{len(rs)} | {dyn_sum} | {cross_runs}/{len(rs)} |")

        lines.extend(["", "## Analysis Set Coverage", ""])
        lines.extend(
            [
                "| Scenario | Included in Inferential Set |",
                "|----------|-----------------------------|",
            ]
        )
        for s in SCENARIOS:
            total = len([r for r in clean if r.scenario == s])
            inc = len([r for r in analysis_set if r.scenario == s])
            if total == 0:
                continue
            lines.append(f"| {s} | {inc}/{total} |")

        failing = [r for r in (clean + excluded) if (not r.run_validity_passed or not r.stress_validity_passed)]
        if failing:
            lines.extend(["", "### Gate Failures", ""])
            for r in failing:
                reasons: List[str] = []
                if not r.run_validity_passed:
                    reasons.extend(r.run_validity_notes)
                if not r.stress_validity_passed:
                    reasons.extend(r.stress_validity_notes)
                reason = "; ".join(reasons) if reasons else "unspecified"
                lines.append(f"- {r.scenario} run {r.run_id}: {reason}")

        lines.extend(["", "## Statistical Comparisons", ""])

        for c in comparisons:
            sig = "✅ Significant" if c.welch_p_value < 0.05 else "⚠️ Not significant"
            lines.extend(
                [
                    f"### {c.comparison_scenario} vs {c.baseline_scenario} ({c.metric})",
                    "",
                    "| Metric | Value |",
                    "|--------|-------|",
                    f"| Baseline mean | {c.baseline_mean:.2f} (n={c.n_baseline}) |",
                    f"| Comparison mean | {c.comparison_mean:.2f} (n={c.n_comparison}) |",
                    f"| Difference | {c.difference:+.2f} ({c.percent_change:+.1f}%) |",
                    f"| Welch t-stat | {c.welch_t_stat:.3f} |",
                    f"| Welch p-value | {c.welch_p_value:.4f} |",
                    f"| Mann-Whitney U | {c.mannwhitney_u_stat:.1f} |",
                    f"| Mann-Whitney p | {c.mannwhitney_p_value:.4f} |",
                    f"| 95% CI | [{c.ci_lower:+.2f}, {c.ci_upper:+.2f}] |",
                    f"| Cohen's d | {c.cohens_d:.3f} ({c.effect_size_interpretation}) |",
                    f"| Verdict | {sig} |",
                    "",
                ]
            )

        if excluded:
            lines.extend(["## Excluded Runs", ""])
            for r in excluded:
                if not r.run_validity_passed:
                    reason = "; ".join(r.run_validity_notes) if r.run_validity_notes else "run validity failure"
                    lines.append(f"- {r.scenario} run {r.run_id}: {reason}")
                elif (
                    r.scenario in ("s1-k8s-only", "s3-hybrid-reactive", "s4-hybrid-predictive")
                    and not r.stress_validity_passed
                ):
                    reason = (
                        "; ".join(r.stress_validity_notes) if r.stress_validity_notes else "stress validity failure"
                    )
                    lines.append(f"- {r.scenario} run {r.run_id}: {reason}")
                else:
                    lines.append(f"- {r.scenario} run {r.run_id}: invalid/empty metrics")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table

        console = Console()
    except ImportError:
        console = None

    def _print(msg, **kwargs):
        if console:
            console.print(msg, **kwargs)
        else:
            print(msg)

    parser = argparse.ArgumentParser(description="Phase B: Replicated Comparison Experiments")
    parser.add_argument("--phase", choices=["preflight", "experiments", "analysis", "full"], default="full")
    parser.add_argument("--runs", type=int, default=5, help="Runs per scenario")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for run order")
    parser.add_argument("--output", type=str, default=None, help="Output directory")
    parser.add_argument("--scenarios", type=str, default=None, help="Comma-separated scenario list (default: all 4)")
    parser.add_argument("--results-file", type=str, default=None, help="Path to results JSON for analysis-only mode")
    parser.add_argument(
        "--controller",
        type=str,
        default="v3",
        choices=["v1", "v2", "v3"],
        help="Controller version for S4 (v1=bang-bang, v2=PID+feedforward, v3=capacity-driven). Default: v3",
    )
    parser.add_argument("--skip-cost", action="store_true", help="Skip cost analysis after experiments")
    parser.add_argument("--quick", action="store_true", help="Use 2-min test stages instead of 20-min full replay")
    args = parser.parse_args()
    # Swap to test stages for quick runs (2 min vs 20 min)
    if args.quick:
        global K6_STAGES
        K6_STAGES = K6_STAGES_TEST
        os.environ["EXPERIMENT_DURATION_SEC"] = "120"
        print("⚡ Quick mode: 2-min test stages")

    datestamp = datetime.now().strftime("%Y-%m-%d")
    output_dir = args.output or f"results/experiments/phase-b/{datestamp}_clarknet-replay"
    scenarios = args.scenarios.split(",") if args.scenarios else SCENARIOS

    # Header
    if console:
        _print(
            Panel.fit(
                f"[bold]Phase B Experiments[/bold]\n"
                f"Runs: {args.runs} × Scenarios: {len(scenarios)}\n"
                f"Controller: {args.controller}  |  Seed: {args.seed}\n"
                f"Output: {output_dir}",
                border_style="cyan",
            )
        )
    else:
        print(
            f"\nPhase B: {args.runs} runs × {len(scenarios)} scenarios | Controller: {args.controller} | Seed: {args.seed}"
        )

    runner = ExperimentRunner(output_dir=str(PROJECT_ROOT / output_dir))

    # Preflight
    if args.phase in ("preflight", "full"):
        _print("\n[bold cyan]Preflight Checks[/bold cyan]" if console else "\nPREFLIGHT CHECKS")
        ok, checks = runner.preflight.check_all()
        if console:
            table = Table(show_header=True, header_style="bold")
            table.add_column("Check")
            table.add_column("Status", justify="center")
            for k, v in checks.items():
                table.add_row(k, "[green]✅[/green]" if v else "[red]❌[/red]")
            _print(table)
        else:
            for k, v in checks.items():
                print(f"  {'✅' if v else '❌'} {k}")

        if not ok:
            failed = [k for k, v in checks.items() if not v]
            _print(f"\n[red]Preflight failed: {failed}[/red]" if console else f"\n❌ Preflight failed: {failed}")
            if args.phase == "full":
                return 1
        else:
            _print("\n[green]All preflight checks passed[/green]" if console else "\n✅ All preflight checks passed")

    # Experiments
    results = []
    if args.phase in ("experiments", "full"):
        _print(f"\n[bold cyan]Running {args.runs * len(scenarios)} experiments...[/bold cyan]")
        results = runner.run_replicated(scenarios, args.runs, args.seed)
        _print(f"\n[green]✅ {len(results)} runs completed[/green]")

    # Analysis
    if args.phase in ("analysis", "full"):
        if not results and args.results_file:
            with open(args.results_file) as f:
                raw = json.load(f)
            results = [ExperimentResult(**r) for r in raw]

        if results:
            _print("\n[bold cyan]Statistical Analysis[/bold cyan]" if console else "\nSTATISTICAL ANALYSIS")
            report = runner.run_analysis(results)
            _print("\n" + report)
        else:
            _print("[red]❌ No results to analyze[/red]" if console else "❌ No results to analyze")
    # Cost Analysis
    if args.phase in ("analysis", "full") and not args.skip_cost:
        _print("\n[bold cyan]Cost Analysis[/bold cyan]" if console else "\nCOST ANALYSIS")
        try:
            sys.path.insert(0, str(SCRIPT_DIR))
            from cost_analyzer import run_experiment_analysis

            experiment_path = PROJECT_ROOT / output_dir
            if experiment_path.exists():
                run_experiment_analysis(experiment_path)
            else:
                _print("[yellow]Skipping cost analysis: experiment directory not found[/yellow]")
        except Exception as e:
            _print(f"[yellow]Cost analysis skipped: {e}[/yellow]" if console else f"Cost analysis skipped: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
