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
    cd controller && uv run python ../thesis/scripts/run_phase_b_experiments.py \\
        --phase full --runs 5

    cd controller && uv run python ../thesis/scripts/run_phase_b_experiments.py \\
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

SCRIPT_DIR = Path(__file__).resolve().parent  # thesis/scripts/
PROJECT_ROOT = SCRIPT_DIR.parent.parent       # repo root
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
K6_SCRIPT = PROJECT_ROOT / "infrastructure" / "load-tests" / "clarknet_replay.js"
K6_STAGES = PROJECT_ROOT / "data" / "trace-replay" / "clarknet_k6_stages.json"
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
NAMESPACE = "default"

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

    # Cost proxy metrics (Table 3-7)
    k8s_weight_time_product: float = 0.0
    serverless_weight_time_product: float = 0.0

    # GRU metrics (S4 only)
    gru_predictions_used: int = 0
    gru_predictions_failed: int = 0

    # Run metadata
    duration_sec: int = 0
    t_start: float = 0.0
    t_end: float = 0.0
    k6_summary_path: str = ""
    daemon_log_path: str = ""
    prom_export_path: str = ""

    # Raw Prometheus time-series paths (stored per-run)
    replica_timeline_path: str = ""


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

    def reset(self, scenario: str) -> bool:
        logger.info("scenario_reset_start", scenario=scenario)

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
        r = _kubectl([
            "autoscale", f"deployment/{DEPLOYMENT}",
            "--cpu-percent=50", "--min=1", "--max=10",
        ])
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
        """S2: ensure Knative KPA is active, wait for scale-to-zero."""
        # Knative annotations should already be set; verify pods are zero
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
        """S3/S4: delete HPA, scale to baseline (1 replica), wait ready."""
        # Delete HPA
        _kubectl(["delete", "hpa", DEPLOYMENT, "--ignore-not-found"])
        time.sleep(2)

        # Scale to baseline replicas (1 — resource-constrained, Algorithm 2 scales up)
        r = _kubectl(["scale", f"deployment/{DEPLOYMENT}", "--replicas=1"])
        if r.returncode != 0:
            logger.error("scale_baseline_failed", stderr=r.stderr.strip())
            return False

        # Wait for readyReplicas == 1
        for _ in range(30):
            time.sleep(2)
            dr = _kubectl(["get", f"deployment/{DEPLOYMENT}", "-o", "json"])
            if dr.returncode == 0:
                dep = json.loads(dr.stdout)
                available = dep.get("status", {}).get("availableReplicas", 0) or 0
                if available >= 1:
                    logger.info("baseline_replicas_ready", replicas=1)
                    return True
        logger.warning("baseline_replicas_timeout")
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
            logger.error("haproxy_weight_mismatch",
                        expected={"k3s": k3s_w, "knative": kn_w}, actual=actual)
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
                capture_output=True, text=True, timeout=5,
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
            sys.executable, "-m", "daemon.routing_daemon",
            "--scenario", scenario,
            "--haproxy-host", HAPROXY_HOST,
            "--haproxy-port", str(HAPROXY_SOCKET_PORT),
            "--haproxy-stats", HAPROXY_STATS_URL,
            "--gru-url", GRU_URL,
            "--interval", "15",
            "--api-port", str(DAEMON_API_PORT),
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
                        logger.error("daemon_scenario_mismatch",
                                    expected=scenario, got=health.get("scenario"))
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
            K6_PATH, "run",
            "--out", "json=/dev/null",  # disable verbose json streaming
            "-e", f"TARGET_URL={TARGET_URL}",
            "-e", "ENDPOINT=/fib?n=32",
            "-e", f"SCENARIO={scenario}",
            "-e", f"RUN_ID={run_id}",
            "-e", f"RESULTS_DIR={k6_results_dir}",
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
            logger.info("k6_complete", scenario=scenario, run_id=run_id,
                       p99=summary.get("metrics", {}).get("p99_latency_ms"),
                       total_requests=summary.get("metrics", {}).get("total_requests"))
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
        "prom_p99_ms": 'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[1m])) by (le)) * 1000',
        "prom_rps": 'sum(rate(http_requests_total[1m]))',
        # Routing daemon
        "daemon_decisions": 'routing_daemon_decision_total',
        "daemon_weight_k3s": 'routing_daemon_current_weight{backend="k3s"}',
        "daemon_weight_knative": 'routing_daemon_current_weight{backend="knative"}',
        "daemon_predictions_used": 'routing_daemon_prediction_used_total',
        "daemon_predictions_failed": 'routing_daemon_prediction_failed_total',
        # Algorithm 2 replica scaling
        "k8s_desired_replicas": 'k8s_deployment_desired_replicas',
        "k8s_available_replicas": 'k8s_deployment_available_replicas',
        "k8s_scale_up_success": 'k8s_scaling_events_total{direction="up",result="success"}',
        "k8s_scale_up_fail": 'k8s_scaling_events_total{direction="up",result="fail"}',
        "k8s_scale_down_success": 'k8s_scaling_events_total{direction="down",result="success"}',
        "k8s_scale_down_fail": 'k8s_scaling_events_total{direction="down",result="fail"}',
        # Control-loop metrics (Table 3-5)
        "daemon_decision_latency_ms": 'routing_daemon_decision_latency_ms_sum / routing_daemon_decision_latency_ms_count',
        # Resource metrics (Table 3-7)
        "cpu_usage_cores": 'sum(rate(container_cpu_usage_seconds_total{namespace="default",container="test-app-warm"}[1m]))',
        "memory_usage_bytes": 'sum(container_memory_working_set_bytes{namespace="default",container="test-app-warm"})',
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
            return np.mean([v for _, v in ts]) if ts else 0.0

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
        weight_changes = sum(1 for i in range(1, len(k3s_ts)) if k3s_ts[i][1] != k3s_ts[i-1][1])

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
        }

    @staticmethod
    def _weight_time_integral(ts: List[Tuple[float, float]]) -> float:
        """Trapezoidal integration of weight × time."""
        if len(ts) < 2:
            return 0.0
        total = 0.0
        for i in range(1, len(ts)):
            dt = ts[i][0] - ts[i-1][0]
            avg_w = (ts[i][1] + ts[i-1][1]) / 2
            total += avg_w * dt
        return total


# ---------------------------------------------------------------------------
# Statistical analysis  (s2-sm0)
# ---------------------------------------------------------------------------

class StatisticalAnalyzer:
    """Welch t-test, Mann-Whitney U, bootstrap CI, Cohen's d, outlier detection."""

    OUTLIER_P99_FLOOR_MS = 15.0  # p99 < 15ms is measurement artifact

    def detect_outliers(self, results: List[ExperimentResult]) -> Tuple[List[ExperimentResult], List[ExperimentResult]]:
        """Returns (clean, excluded) results."""
        clean, excluded = [], []
        for r in results:
            if r.p99_latency_ms < self.OUTLIER_P99_FLOOR_MS:
                excluded.append(r)
                logger.warning("outlier_detected", scenario=r.scenario, run_id=r.run_id,
                             p99=r.p99_latency_ms, reason="p99 < 15ms")
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
        self.analyzer = StatisticalAnalyzer()

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
        if not self.resetter.reset(scenario):
            logger.error("reset_failed", scenario=scenario)
            return None

        # Start daemon (S1/S2 still need daemon for metrics even if no algorithm)
        daemon_log = run_dir / "daemon.log"
        daemon_proc = self.daemon.start(scenario, daemon_log)
        if daemon_proc is None:
            return None

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
                    "interval": 15, "haproxy_host": HAPROXY_HOST,
                    "haproxy_port": HAPROXY_SOCKET_PORT, "gru_url": GRU_URL,
                    "endpoint": "/fib?n=32",
                    "gomaxprocs": 1, "fib_n": 32,
                },
                scaling_config={"alpha": 0.0167, "beta": 0.0, "buffer": 1.2,
                               "min_replicas": 1, "max_replicas": 10},
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

            # Record t_start
            t_start = time.time()

            # (C.2) Execute k6 trace replay
            k6_summary = self.k6.run(scenario, run_id, run_dir)

            # (C.3) Post-k6 cooldown to capture delayed scaling effects
            logger.info("cooldown_start", seconds=COOLDOWN_SEC)
            time.sleep(COOLDOWN_SEC)

            # Record t_end
            t_end = time.time()

            # Get daemon status before stopping
            daemon_status = self.daemon.get_status() or {}

            # (D) Export Prometheus metrics for [t_start, t_end]
            prom_summary = self.exporter.export_run(t_start, t_end, run_dir / "prometheus")

            # Find k6 summary file
            k6_files = list((run_dir / "k6").glob("clarknet_replay_*.json")) if (run_dir / "k6").exists() else []
            k6_summary_path = str(k6_files[0]) if k6_files else ""

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
                # Prometheus corroboration
                prom_p99_latency_ms=prom_summary.get("prom_p99_ms", 0),
                # Routing metrics
                maintain_count=daemon_status.get("maintain_count", 0),
                scale_out_count=daemon_status.get("scale_out_count", 0),
                predictive_count=daemon_status.get("predictive_count", 0),
                optimize_cost_count=daemon_status.get("optimize_cost_count", 0),
                weight_change_count=prom_summary.get("weight_change_count", 0),
                time_in_serverless_pct=prom_summary.get("time_in_serverless_pct", 0),
                # Algorithm 2
                scale_up_events=prom_summary.get("scale_up_success", 0) + prom_summary.get("scale_up_fail", 0),
                scale_down_events=prom_summary.get("scale_down_success", 0) + prom_summary.get("scale_down_fail", 0),
                scale_up_success=prom_summary.get("scale_up_success", 0),
                scale_down_success=prom_summary.get("scale_down_success", 0),
                desired_replicas_final=prom_summary.get("desired_replicas_final", 0),
                available_replicas_final=prom_summary.get("available_replicas_final", 0),
                # Cost proxy
                k8s_weight_time_product=prom_summary.get("k8s_weight_time", 0),
                serverless_weight_time_product=prom_summary.get("kn_weight_time", 0),
                # GRU
                gru_predictions_used=prom_summary.get("predictions_used", 0),
                gru_predictions_failed=prom_summary.get("predictions_failed", 0),
                # Run metadata
                duration_sec=replay_manifest.get("duration_sec", 1200),
                t_start=t_start,
                t_end=t_end,
                k6_summary_path=k6_summary_path,
                daemon_log_path=str(daemon_log),
                prom_export_path=prom_summary.get("export_path", ""),
                replica_timeline_path=str(run_dir / "prometheus" / "prometheus_export.json"),
            )

            # Save result
            with open(run_dir / "result.json", "w") as f:
                json.dump(asdict(result), f, indent=2)

            logger.info("run_complete", scenario=scenario, run_id=run_id,
                       p99=result.p99_latency_ms, error_rate=result.error_rate)
            return result

        finally:
            self.daemon.stop(daemon_proc)

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
                logger.error("precondition_haproxy_weight_wrong",
                            scenario=scenario, expected=expected, actual=weights)
                return False
        else:
            # S3/S4: daemon may adjust weights during warmup (OPTIMIZE_COST
            # can reduce knative to 0 if latency is healthy). Just verify k3s
            # has weight > 0 (primary backend must be reachable).
            if not weights.get("k3s", 0) > 0:
                logger.error("precondition_hybrid_k3s_zero",
                            scenario=scenario, actual=weights)
                return False
            if weights.get("knative", 0) == 0:
                logger.warning("precondition_hybrid_knative_zero_ok",
                              scenario=scenario, actual=weights,
                              reason="daemon OPTIMIZE_COST during warmup")

        # 2. Daemon /health scenario matches
        try:
            r = requests.get(f"{DAEMON_API}/health", timeout=5)
            health = r.json()
            if health.get("scenario") != scenario:
                logger.error("precondition_daemon_scenario_mismatch",
                            expected=scenario, got=health.get("scenario"))
                return False
        except Exception as e:
            logger.error("precondition_daemon_health_failed", error=str(e))
            return False

        # 3. Daemon /status decision_count < 5 (fresh daemon)
        try:
            r = requests.get(f"{DAEMON_API}/status", timeout=5)
            status = r.json()
            if status.get("decision_count", 999) >= 5:
                logger.error("precondition_daemon_not_fresh",
                            decision_count=status.get("decision_count"))
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
            logger.info("run_progress", current=idx + 1, total=len(schedule),
                       scenario=scenario, run_id=run_id)

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
                stat = self.analyzer.compare(clean, baseline, comp, metric)
                comparisons.append(stat)
            except ValueError as e:
                logger.warning("comparison_skipped", error=str(e))

        # Save comparisons
        with open(self.output_dir / "statistical_analysis.json", "w") as f:
            json.dump([asdict(c) for c in comparisons], f, indent=2)

        # Generate report
        report = self._generate_report(clean, excluded, comparisons)
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
        excluded: List[ExperimentResult],
        comparisons: List[StatisticalComparison],
    ) -> str:
        lines = [
            f"# Phase B: Replicated Comparison Results",
            f"",
            f"**Date:** {datetime.now().isoformat()}",
            f"**Git:** {_git_commit_hash()}",
            f"**Runs:** {len(clean)} clean, {len(excluded)} excluded",
            f"",
            f"## Per-Scenario Summary",
            f"",
            f"| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | Error% | RPS | SLO Violations | Scale-Up | Scale-Down |",
            f"|----------|---|----------|----------|----------|--------|-----|----------------|----------|------------|",
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

        lines.extend(["", "## Statistical Comparisons", ""])

        for c in comparisons:
            sig = "✅ Significant" if c.welch_p_value < 0.05 else "⚠️ Not significant"
            lines.extend([
                f"### {c.comparison_scenario} vs {c.baseline_scenario} ({c.metric})",
                f"",
                f"| Metric | Value |",
                f"|--------|-------|",
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
                f"",
            ])

        if excluded:
            lines.extend(["## Excluded Runs", ""])
            for r in excluded:
                lines.append(f"- {r.scenario} run {r.run_id}: p99={r.p99_latency_ms:.1f}ms (< 15ms threshold)")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Phase B: Replicated Comparison Experiments")
    parser.add_argument("--phase", choices=["preflight", "experiments", "analysis", "full"], default="full")
    parser.add_argument("--runs", type=int, default=5, help="Runs per scenario")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for run order")
    parser.add_argument("--output", type=str, default=None, help="Output directory")
    parser.add_argument("--scenarios", type=str, default=None,
                       help="Comma-separated scenario list (default: all 4)")
    parser.add_argument("--results-file", type=str, default=None,
                       help="Path to results JSON for analysis-only mode")
    args = parser.parse_args()

    datestamp = datetime.now().strftime("%Y-%m-%d")
    output_dir = args.output or f"results/experiments/phase-b/{datestamp}_clarknet-replay"
    scenarios = args.scenarios.split(",") if args.scenarios else SCENARIOS

    runner = ExperimentRunner(output_dir=str(PROJECT_ROOT / output_dir))

    # Preflight
    if args.phase in ("preflight", "full"):
        print("\n" + "=" * 70)
        print("PREFLIGHT CHECKS")
        print("=" * 70)
        ok, checks = runner.preflight.check_all()
        if not ok:
            failed = [k for k, v in checks.items() if not v]
            print(f"\n❌ Preflight failed: {failed}")
            if args.phase == "full":
                return 1
        else:
            print("\n✅ All preflight checks passed")

    # Experiments
    results = []
    if args.phase in ("experiments", "full"):
        print("\n" + "=" * 70)
        print(f"PHASE B EXPERIMENTS — {args.runs} runs × {len(scenarios)} scenarios")
        print(f"Seed: {args.seed}  |  Output: {output_dir}")
        print("=" * 70)

        results = runner.run_replicated(scenarios, args.runs, args.seed)
        print(f"\n✅ {len(results)} runs completed")

    # Analysis
    if args.phase in ("analysis", "full"):
        if not results and args.results_file:
            with open(args.results_file) as f:
                raw = json.load(f)
            results = [ExperimentResult(**r) for r in raw]

        if results:
            print("\n" + "=" * 70)
            print("STATISTICAL ANALYSIS")
            print("=" * 70)
            report = runner.run_analysis(results)
            print("\n" + report)
        else:
            print("❌ No results to analyze")

    return 0


if __name__ == "__main__":
    sys.exit(main())
