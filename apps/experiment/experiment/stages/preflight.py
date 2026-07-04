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
    HAProxy stats, GRU server, cluster nodes, target deployment, Knative serving.
    """

    name = "preflight"

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
