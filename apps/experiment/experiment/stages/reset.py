"""Reset stage: per-run scenario reset (HPA/KPA/Algorithm 2 management).

Extracted from scripts/run_phase_b_experiments.py lines 524-689 (ScenarioResetter).
"""

import json
import os
import socket as _socket
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import structlog

from shared.config import settings
from shared.models.pipeline import PipelineContext
from shared.protocols import ProvisionerClient

from experiment.stages.base import BaseStage

logger = structlog.get_logger(__name__)

# Tool paths
KUBECTL_PATH = os.environ.get(
    "KUBECTL_PATH",
    str(Path.home() / ".local/share/mise/installs/kubectl/1.35.0/kubectl"),
)

# Infrastructure constants
DEPLOYMENT = "test-app-warm"
HPA_NAME = "test-app-warm-hpa"
NAMESPACE = "default"

HAPROXY_HOST = settings.HAPROXY_HOST
HAPROXY_SOCKET_PORT = settings.HAPROXY_SOCKET_PORT
HAPROXY_STATS_URL = settings.HAPROXY_STATS_URL


def _run_cmd(cmd: List[str], timeout: int = 30, **kwargs: Any) -> subprocess.CompletedProcess:
    """Run a command with timeout."""
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **kwargs)


def _kubectl(args: List[str], timeout: int = 15) -> subprocess.CompletedProcess:
    """Run kubectl with standard args."""
    return _run_cmd([KUBECTL_PATH, "-n", NAMESPACE] + args, timeout=timeout)


def _parse_haproxy_stats_weights() -> Optional[Dict[str, int]]:
    """Parse HAProxy stats CSV to get current k3s/knative weights."""
    try:
        r = requests.get(HAPROXY_STATS_URL, timeout=5)
        if r.status_code != 200:
            return None
        lines = r.text.strip().split("\n")
        if len(lines) < 2:
            return None
        headers = lines[0].split(",")
        weights = {}
        for line in lines[1:]:
            fields = line.split(",")
            svname = fields[headers.index("svname")] if "svname" in headers else ""
            if svname in ("k3s", "knative"):
                weight_val = fields[headers.index("weight")] if "weight" in headers else "0"
                weights[svname] = int(weight_val)
        return weights if len(weights) == 2 else None
    except Exception:
        return None


class ResetStage(BaseStage):
    """Implements per-run reset procedure per methodology Section 3.5.4(B).

    Resets HPA/KPA/Algorithm 2 state and HAProxy weights for each scenario.
    """

    name = "reset"

    def __init__(self, provisioner: Optional[ProvisionerClient] = None):
        self._provisioner = provisioner

    def _run(self, ctx: PipelineContext) -> None:
        scenario = ctx.scenario
        if not self._reset(scenario):
            raise RuntimeError(f"Scenario reset failed for {scenario}")

    def _reset(self, scenario: str) -> bool:
        logger.info("scenario_reset_start", scenario=scenario)

        if self._provisioner and scenario in ("s1-k8s-only", "s3-hybrid-reactive", "s4-hybrid-predictive"):
            if not self._provisioner.reset():
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
            if not self._reset_haproxy_weights(scenario):
                logger.error("scenario_reset_haproxy_failed", scenario=scenario)
                return False
            logger.info("scenario_reset_complete", scenario=scenario)
        return ok

    def _reset_s1(self) -> bool:
        """S1: ensure HPA, delete any manual scaling artifacts."""
        _kubectl(["delete", "hpa", DEPLOYMENT, "--ignore-not-found"])
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

        # Wait for HPA to have metrics
        for _ in range(20):
            time.sleep(3)
            hr = _kubectl(["get", "hpa", DEPLOYMENT, "-o", "json"])
            if hr.returncode == 0:
                hpa = json.loads(hr.stdout)
                if hpa.get("status", {}).get("currentReplicas", 0) > 0:
                    logger.info("hpa_ready", replicas=hpa["status"]["currentReplicas"])
                    return True
        logger.warning("hpa_metrics_timeout")
        return True

    def _reset_s2(self) -> bool:
        """S2: ensure K8s path is drained and Knative KPA scales to zero."""
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
        return True

    def _reset_s3_s4(self) -> bool:
        """S3/S4: delete HPA, scale to baseline (2 replicas), wait ready."""
        _kubectl(["delete", "hpa", DEPLOYMENT, "--ignore-not-found"])
        time.sleep(2)

        baseline_replicas = 2
        r = _kubectl(["scale", f"deployment/{DEPLOYMENT}", f"--replicas={baseline_replicas}"])
        if r.returncode != 0:
            logger.error("scale_baseline_failed", stderr=r.stderr.strip())
            return False

        for _ in range(30):
            time.sleep(2)
            dr = _kubectl(["get", f"deployment/{DEPLOYMENT}", "-o", "json"])
            if dr.returncode == 0:
                dep = json.loads(dr.stdout)
                available = dep.get("status", {}).get("availableReplicas", 0) or 0
                if available >= baseline_replicas:
                    logger.info("baseline_replicas_ready", replicas=baseline_replicas)
                    return True
        logger.warning("baseline_replicas_timeout", note="continuing anyway")
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
