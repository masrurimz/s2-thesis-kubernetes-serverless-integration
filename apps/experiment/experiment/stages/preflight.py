"""Preflight stage: validates infrastructure readiness before experiments.

Extracted from scripts/run_phase_b_experiments.py lines 467-516 (PreflightChecker).
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests
import structlog

from shared.config import settings
from shared.models.pipeline import PipelineContext, PreflightResult

from experiment.stages.base import BaseStage
from experiment.stages.daemon import is_port_listening

logger = structlog.get_logger(__name__)

# Tool paths (mise-managed)
K6_PATH = os.environ.get(
    "K6_PATH",
    str(Path.home() / ".local/share/mise/installs/k6/1.6.0/k6-v1.6.0-linux-amd64/k6"),
)
KUBECTL_PATH = os.environ.get(
    "KUBECTL_PATH",
    str(Path.home() / ".local/share/mise/installs/kubectl/1.35.0/kubectl"),
)

# Project paths
# Project paths — apps/experiment/experiment/stages/preflight.py → 5 levels up to root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
K6_SCRIPT = PROJECT_ROOT / "apps" / "experiment" / "experiment" / "load_tests" / "canonical" / "clarknet_replay.js"
K6_STAGES = PROJECT_ROOT / "data" / "trace-replay" / "clarknet_k6_stages.json"

DEPLOYMENT = "test-app-warm"
NAMESPACE = "default"

GRU_URL = f"http://localhost:{settings.GRU_PORT}"
PROMETHEUS_URL = settings.PROMETHEUS_URL
HAPROXY_STATS_URL = settings.HAPROXY_STATS_URL


def _run_cmd(cmd: List[str], timeout: int = 30, **kwargs: Any) -> subprocess.CompletedProcess:
    """Run a command with timeout."""
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **kwargs)


def _kubectl(args: List[str], timeout: int = 15) -> subprocess.CompletedProcess:
    """Run kubectl with standard args."""
    return _run_cmd([KUBECTL_PATH, "-n", NAMESPACE] + args, timeout=timeout)


class PreflightStage(BaseStage):
    """Validates cluster and service readiness before experiments.

    Checks: k6 binary, kubectl binary, k6 script, k6 stages, Prometheus,
    Prometheus probe metric, HAProxy stats, daemon port freshness, GRU server,
    cluster nodes, target deployment, Knative serving.

    When the experiment plan includes S4 (s4-hybrid-predictive), the GRU check
    requires either no listener on the GRU port or a health response with
    model_loaded=true — a listener without a loaded model would corrupt S4 runs.
    """

    name = "preflight"

    def __init__(self, s4_planned: bool = False):
        """Create the preflight stage.

        Args:
            s4_planned: True when the experiment plan includes the S4
                (s4-hybrid-predictive) scenario, which activates the GRU
                prediction-service invariant (no listener or model loaded).
        """
        self.s4_planned = s4_planned

    def _run(self, ctx: PipelineContext) -> None:
        all_ok, checks = self._check_all()
        ctx.preflight = PreflightResult(passed=all_ok, checks=checks)
        if not all_ok:
            failed = [k for k, v in checks.items() if not v]
            raise RuntimeError(f"Preflight checks failed: {failed}")

    def _check_all(self) -> Tuple[bool, Dict[str, bool]]:
        checks = {
            "k6_binary": Path(K6_PATH).exists(),
            "kubectl_binary": Path(KUBECTL_PATH).exists(),
            "k6_script": K6_SCRIPT.exists(),
            "k6_stages": K6_STAGES.exists(),
            "prometheus": self._check_http(f"{PROMETHEUS_URL}/-/healthy"),
            "prometheus_probe": self._check_prometheus_probe(),
            "haproxy_stats": self._check_haproxy_stats(),
            "daemon_port": self._check_daemon_port(),
            "gru_server": self._check_gru_server(),
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
    def _check_prometheus_probe() -> bool:
        """Prometheus must return a non-empty result for the `up` probe metric."""
        try:
            r = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": "up"}, timeout=5)
            if r.status_code != 200:
                return False
            result = r.json().get("data", {}).get("result")
            return bool(result)
        except Exception:
            return False

    def _check_haproxy_stats(self) -> bool:
        """HAProxy stats must parse to a sane (k3s, knative) weight tuple.

        Uses the shared HAProxyClient (infra.networking.haproxy) to fetch and
        parse the stats CSV; both backend weights must be present and within
        the valid 0-100 range.
        """
        try:
            from infra.networking.haproxy import HAProxyClient

            client = HAProxyClient(
                tcp_socket_host=settings.HAPROXY_HOST,
                tcp_socket_port=settings.HAPROXY_SOCKET_PORT,
                backend_name="servers",
                stats_url=settings.HAPROXY_STATS_URL,
            )
            weights = client.get_current_weights()
        except Exception:
            return False
        if not weights:
            return False
        k3s, knative = weights.get("k3s", -1), weights.get("knative", -1)
        return 0 <= k3s <= 100 and 0 <= knative <= 100

    def _check_daemon_port(self) -> bool:
        """Daemon port invariant: no listener, or a fresh daemon (<=30s uptime).

        A stale daemon left over from a previous session is killed by
        DaemonStage before each run; a daemon that is still fresh (uptime
        <= 30s) is tolerated as part of the current session.
        """
        if not is_port_listening(settings.DAEMON_API_PORT):
            return True
        try:
            r = requests.get(f"http://localhost:{settings.DAEMON_API_PORT}/status", timeout=3)
            if r.status_code != 200:
                return False
            uptime = r.json().get("uptime_seconds")
            return isinstance(uptime, (int, float)) and 0 <= uptime <= 30
        except Exception:
            return False

    def _check_gru_server(self) -> bool:
        """GRU server readiness.

        Without S4 in the plan, the server must answer /health with HTTP 200.
        With S4 planned, either no listener may be present on the GRU port
        (the service is operator-managed and started on demand), or the health
        endpoint must report model_loaded=true.
        """
        if not self.s4_planned:
            return self._check_http(f"{GRU_URL}/health")
        if not is_port_listening(settings.GRU_PORT):
            return True
        try:
            r = requests.get(f"{GRU_URL}/health", timeout=3)
            return r.status_code == 200 and bool(r.json().get("model_loaded"))
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
        # Knative is in thesis-serverless cluster (separate control plane)
        ctx = os.environ.get("K3D_SERVERLESS_CONTEXT", "k3d-thesis-serverless")
        r = _run_cmd([KUBECTL_PATH, "--context", ctx, "-n", NAMESPACE, "get", "ksvc", "-o", "json"], timeout=10)
        return r.returncode == 0
