"""Node provisioner: simulates cloud node provisioning via k3d cordon/uncordon.

Extracted from scripts/run_phase_b_experiments.py lines 311-459.
"""

import json
import random
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)

# Tool paths (mise-managed)
import os
from pathlib import Path

KUBECTL_PATH = os.environ.get(
    "KUBECTL_PATH",
    str(Path.home() / ".local/share/mise/installs/kubectl/1.35.0/kubectl"),
)
NAMESPACE = "default"


def _run_cmd(cmd: List[str], timeout: int = 30, **kwargs: Any) -> subprocess.CompletedProcess:
    """Run a command with timeout, return CompletedProcess."""
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **kwargs)


def _kubectl(args: List[str], timeout: int = 15) -> subprocess.CompletedProcess:
    """Run kubectl with standard args."""
    return _run_cmd([KUBECTL_PATH, "-n", NAMESPACE] + args, timeout=timeout)


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

    def clear_log(self) -> None:
        """Clear the provision event log (for per-run isolation)."""
        with self._log_lock:
            self._provision_log = []

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
