#!/usr/bin/env python3
"""k3d-backed dynamic workload node autoscaler for thesis experiments.

This module is intentionally standalone so it can be integrated into experiment
orchestration without modifying the existing cordon/uncordon provisioner.
"""

from __future__ import annotations

import json
import os
import random
import subprocess
import threading
import time
from typing import Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


class K3dAutoscaler:
    """Create/delete k3d agent nodes based on Pending/Unschedulable pods."""

    def __init__(
        self,
        cluster_name: str,
        k3d_path: str,
        kubectl_path: str,
        k3s_image: str,
        min_nodes: int = 1,
        max_nodes: int = 3,
        provision_delay_min_sec: int = 45,
        provision_delay_max_sec: int = 120,
        node_memory: str = "1g",
        namespace: str = "default",
        scale_down_cooldown_sec: int = 120,
        scale_down_idle_sec: int = 60,
        scale_down_utilization_threshold: float = 0.5,
        workload_pod_label: str = "app=test-app-warm",
        node_allocatable_cpu: float = 1.0,
    ) -> None:
        self.cluster_name = cluster_name
        self.k3d_path = k3d_path
        self.kubectl_path = kubectl_path
        self.k3s_image = k3s_image
        self.min_nodes = min_nodes
        self.max_nodes = max_nodes
        self.provision_delay_min_sec = provision_delay_min_sec
        self.provision_delay_max_sec = provision_delay_max_sec
        self.node_memory = node_memory
        self.namespace = namespace
        self.scale_down_cooldown_sec = scale_down_cooldown_sec
        self.scale_down_idle_sec = scale_down_idle_sec
        self.scale_down_utilization_threshold = scale_down_utilization_threshold
        self.workload_pod_label = workload_pod_label
        self.node_allocatable_cpu = node_allocatable_cpu

        self._poll_interval_sec = 2
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self._dynamic_nodes: List[str] = []
        self._events: List[Tuple[float, str, Dict]] = []
        self._next_index = 0
        self._last_scale_down_ts: float = 0.0
        self._node_idle_since: Dict[str, float] = {}

        self._lock = threading.Lock()

    def _record_event(self, event: str, data: Optional[Dict] = None) -> None:
        payload = data or {}
        with self._lock:
            self._events.append((time.time(), event, payload))

    def _run_cmd(self, cmd: List[str], timeout: int = 60) -> subprocess.CompletedProcess:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def _kubectl(self, args: List[str], timeout: int = 60) -> subprocess.CompletedProcess:
        return self._run_cmd([self.kubectl_path] + args, timeout=timeout)

    def _k3d(self, args: List[str], timeout: int = 600) -> subprocess.CompletedProcess:
        env = {**os.environ, "PATH": os.environ.get("PATH", "")}
        return subprocess.run(
            [self.k3d_path] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )

    @staticmethod
    def _k8s_node_name_from_short(short_name: str) -> str:
        return f"k3d-{short_name}-0"

    def _wait_node_ready(self, k8s_node_name: str, timeout_sec: int = 180) -> bool:
        deadline = time.time() + timeout_sec
        while time.time() < deadline and not self._stop_event.is_set():
            r = self._kubectl(["get", "node", k8s_node_name, "-o", "json"], timeout=10)
            if r.returncode == 0:
                try:
                    node_obj = json.loads(r.stdout)
                    for cond in node_obj.get("status", {}).get("conditions", []):
                        if cond.get("type") == "Ready" and cond.get("status") == "True":
                            return True
                except json.JSONDecodeError:
                    pass
            time.sleep(1)
        return False

    def _ensure_workload_label(self, k8s_node_name: str) -> bool:
        r = self._kubectl(
            ["get", "node", k8s_node_name, "-o", "jsonpath={.metadata.labels.node-type}"],
            timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip() == "workload":
            return True

        # Fallback for cases where --k3s-node-label is not reflected as expected.
        label_cmd = ["label", "node", k8s_node_name, "node-type=workload", "--overwrite"]
        lr = self._kubectl(label_cmd, timeout=20)
        if lr.returncode != 0:
            logger.error("node_label_apply_failed", node=k8s_node_name, stderr=lr.stderr.strip())
            return False
        self._record_event("node_label_applied", {"node": k8s_node_name})
        return True

    def _compute_next_node_name(self) -> str:
        existing = set(self._discover_dynamic_nodes())
        idx = self._next_index
        while True:
            candidate = f"dynamic-workload-{idx}"
            if candidate not in existing:
                self._next_index = idx + 1
                return candidate
            idx += 1

    def _discover_dynamic_nodes(self) -> List[str]:
        r = self._k3d(["node", "list", "-o", "json"], timeout=20)
        if r.returncode != 0:
            logger.warning("k3d_node_list_failed", stderr=r.stderr.strip())
            return list(self._dynamic_nodes)

        discovered: List[str] = []
        try:
            for item in json.loads(r.stdout):
                # Cluster name lives in runtimeLabels, not a top-level field
                cluster = (item.get("runtimeLabels") or {}).get("k3d.cluster", "")
                if cluster != self.cluster_name:
                    continue
                name = item.get("name", "")
                if name.startswith("k3d-dynamic-workload-"):
                    short = name.removeprefix("k3d-")
                    if short.endswith("-0"):
                        short = short[:-2]
                    discovered.append(short)
        except (json.JSONDecodeError, TypeError):
            logger.warning("k3d_node_list_parse_failed")
            return list(self._dynamic_nodes)

        with self._lock:
            self._dynamic_nodes = sorted(set(discovered))
            return list(self._dynamic_nodes)

    def create_node(self, name: str) -> bool:
        k8s_node_name = self._k8s_node_name_from_short(name)
        start = time.time()

        create_cmd = [
            "node",
            "create",
            name,
            "--cluster",
            self.cluster_name,
            "--role",
            "agent",
            "--memory",
            self.node_memory,
            "--image",
            self.k3s_image,
            "--k3s-node-label",
            "node-type=workload",
            "--k3s-arg",
            "--kubelet-arg=system-reserved=cpu=15000m",
            "--wait",
        ]

        r = self._k3d(create_cmd, timeout=600)
        if r.returncode != 0:
            logger.error("k3d_node_create_failed", node=name, stderr=r.stderr.strip())
            self._record_event("node_create_failed", {"node": name, "stderr": r.stderr.strip()})
            return False

        if not self._wait_node_ready(k8s_node_name, timeout_sec=180):
            logger.error("node_not_ready", node=k8s_node_name)
            self._record_event("node_ready_timeout", {"node": k8s_node_name})
            return False

        if not self._ensure_workload_label(k8s_node_name):
            self._record_event("node_label_failed", {"node": k8s_node_name})
            return False
        # Apply Docker CPU/memory limits to mimic cloud VM sizing
        container_name = f"k3d-{name}-0"
        r = self._run_cmd(
            ["docker", "update", "--cpus", "1.0", "--memory", "1g", "--memory-swap", "1g", container_name], timeout=30
        )
        if r.returncode != 0:
            logger.warning("docker_update_failed", container=container_name, stderr=r.stderr.strip())
            self._record_event("docker_update_failed", {"container": container_name, "stderr": r.stderr.strip()})
        else:
            self._record_event("node_resource_applied", {"container": container_name, "cpus": "1.0", "memory": "1g"})

        with self._lock:
            if name not in self._dynamic_nodes:
                self._dynamic_nodes.append(name)
                self._dynamic_nodes.sort()

        elapsed = time.time() - start
        self._record_event(
            "node_created",
            {"node": name, "k8s_node": k8s_node_name, "elapsed_sec": round(elapsed, 3)},
        )
        logger.info("node_created", node=name, k8s_node=k8s_node_name, elapsed_sec=round(elapsed, 3))
        return True

    def delete_node(self, name: str) -> bool:
        k8s_node_name = self._k8s_node_name_from_short(name)
        ok = True

        # Drain best-effort; deletion can proceed if node already disappeared.
        drain = self._kubectl(
            [
                "drain",
                k8s_node_name,
                "--ignore-daemonsets",
                "--delete-emptydir-data",
                "--force",
                "--timeout=120s",
            ],
            timeout=180,
        )
        if drain.returncode != 0:
            if "not found" not in (drain.stderr or "").lower() and "not found" not in (drain.stdout or "").lower():
                ok = False
                logger.warning("node_drain_failed", node=k8s_node_name, stderr=drain.stderr.strip())
                self._record_event("node_drain_failed", {"node": k8s_node_name, "stderr": drain.stderr.strip()})

        delete = self._k3d(["node", "delete", k8s_node_name], timeout=300)
        if delete.returncode != 0:
            if "not found" not in (delete.stderr or "").lower() and "not found" not in (delete.stdout or "").lower():
                ok = False
                logger.error("k3d_node_delete_failed", node=k8s_node_name, stderr=delete.stderr.strip())
                self._record_event("node_delete_failed", {"node": k8s_node_name, "stderr": delete.stderr.strip()})

        # Also remove the K8s node object (may linger after k3d container is gone)
        self._kubectl(["delete", "node", k8s_node_name, "--ignore-not-found"], timeout=30)

        with self._lock:
            if name in self._dynamic_nodes:
                self._dynamic_nodes.remove(name)

        if ok:
            self._record_event("node_deleted", {"node": name, "k8s_node": k8s_node_name})
            logger.info("node_deleted", node=name, k8s_node=k8s_node_name)
        return ok

    def watch_pending(self) -> List[str]:
        r = self._kubectl(
            ["get", "pods", "-n", self.namespace, "--field-selector", "status.phase=Pending", "-o", "json"],
            timeout=15,
        )
        if r.returncode != 0:
            logger.warning("pending_pod_query_failed", stderr=r.stderr.strip())
            return []

        unschedulable_pods: List[str] = []
        try:
            data = json.loads(r.stdout)
            for item in data.get("items", []):
                pod_name = item.get("metadata", {}).get("name", "")
                pod_ns = item.get("metadata", {}).get("namespace", self.namespace)
                conditions = item.get("status", {}).get("conditions", [])
                for cond in conditions:
                    if (
                        cond.get("type") == "PodScheduled"
                        and cond.get("status") == "False"
                        and cond.get("reason") == "Unschedulable"
                    ):
                        unschedulable_pods.append(f"{pod_ns}/{pod_name}")
                        break
        except json.JSONDecodeError:
            logger.warning("pending_pod_query_parse_failed")
            return []

        return unschedulable_pods

    @staticmethod
    def _parse_cpu_request(cpu_str: str) -> float:
        """Parse a Kubernetes CPU request string (e.g. '300m', '1', '0.5') to cores."""
        if cpu_str.endswith("m"):
            return int(cpu_str[:-1]) / 1000.0
        return float(cpu_str)

    def _get_workload_pods_on_node(self, k8s_node_name: str) -> List[Dict]:
        """Return raw pod dicts for workload pods on a specific node."""
        r = self._kubectl(
            [
                "get",
                "pods",
                "-n",
                self.namespace,
                "-l",
                self.workload_pod_label,
                "--field-selector",
                f"spec.nodeName={k8s_node_name}",
                "-o",
                "json",
            ],
            timeout=15,
        )
        if r.returncode != 0:
            return []
        try:
            return json.loads(r.stdout).get("items", [])
        except json.JSONDecodeError:
            return []

    def _get_node_cpu_utilization(self, k8s_node_name: str) -> float:
        """Compute CPU request utilization (0.0–1.0) for workload pods on a node.

        Returns -1.0 on error (safe: node stays).
        """
        pods = self._get_workload_pods_on_node(k8s_node_name)
        if not pods:
            return (
                0.0
                if self._kubectl(
                    [
                        "get",
                        "pods",
                        "-n",
                        self.namespace,
                        "-l",
                        self.workload_pod_label,
                        "--field-selector",
                        f"spec.nodeName={k8s_node_name}",
                        "-o",
                        "name",
                    ],
                    timeout=10,
                ).returncode
                == 0
                else -1.0
            )

        total_cpu = 0.0
        for pod in pods:
            for container in pod.get("spec", {}).get("containers", []):
                cpu_req = container.get("resources", {}).get("requests", {}).get("cpu", "0")
                total_cpu += self._parse_cpu_request(cpu_req)

        return total_cpu / self.node_allocatable_cpu if self.node_allocatable_cpu > 0 else -1.0

    def _can_pods_be_rescheduled(self, source_node: str, source_pods: List[Dict]) -> bool:
        """Check if workload pods on source_node can fit on other workload nodes.

        Mirrors Kubernetes CA reschedulability check: sum of free CPU on all
        other workload nodes must be >= sum of CPU requests on source node.
        """
        source_cpu = sum(
            self._parse_cpu_request(c.get("resources", {}).get("requests", {}).get("cpu", "0"))
            for p in source_pods
            for c in p.get("spec", {}).get("containers", [])
        )

        # Discover all workload nodes (static + dynamic) excluding source
        r = self._kubectl(
            ["get", "nodes", "-l", "node-type=workload", "-o", "json"],
            timeout=15,
        )
        if r.returncode != 0:
            return False
        try:
            all_nodes = json.loads(r.stdout).get("items", [])
        except json.JSONDecodeError:
            return False

        free_cpu = 0.0
        for node in all_nodes:
            node_name = node.get("metadata", {}).get("name", "")
            if node_name == source_node:
                continue
            # Skip cordoned/unready nodes
            if node.get("spec", {}).get("unschedulable", False):
                continue
            util = self._get_node_cpu_utilization(node_name)
            if util < 0:
                return False  # can't determine capacity; safe default
            free_cpu += max(0.0, self.node_allocatable_cpu * (1.0 - util))

        return free_cpu >= source_cpu

    def _scaling_loop(self) -> None:
        logger.info(
            "k3d_autoscaler_loop_started",
            cluster=self.cluster_name,
            min_nodes=self.min_nodes,
            max_nodes=self.max_nodes,
            poll_interval_sec=self._poll_interval_sec,
        )

        while not self._stop_event.is_set():
            pending_pods = self.watch_pending()
            current_nodes = self._discover_dynamic_nodes()

            if pending_pods:
                self._record_event(
                    "pending_detected",
                    {"count": len(pending_pods), "pods": pending_pods, "dynamic_nodes": current_nodes},
                )
                if len(current_nodes) < self.max_nodes:
                    if self.provision_delay_max_sec > 0:
                        delay = random.randint(self.provision_delay_min_sec, self.provision_delay_max_sec)
                        self._record_event("provision_delay_started", {"delay_sec": delay})
                        logger.info("provision_delay_wait", delay_sec=delay)
                        for _ in range(delay):
                            if self._stop_event.is_set():
                                break
                            time.sleep(1)

                    if not self._stop_event.is_set():
                        node_name = self._compute_next_node_name()
                        self.create_node(node_name)
                else:
                    self._record_event(
                        "max_nodes_reached",
                        {"max_nodes": self.max_nodes, "pending_count": len(pending_pods)},
                    )

            else:
                # Scale-down: consolidate underutilized dynamic nodes (CA semantics).
                # A node is a candidate when its CPU request utilization is below the
                # threshold AND its pods can be rescheduled onto other workload nodes.
                now = time.time()
                cooldown_passed = (now - self._last_scale_down_ts) >= self.scale_down_cooldown_sec

                if cooldown_passed and current_nodes:
                    # Check newest dynamic node (reverse sorted = highest index = newest).
                    newest = sorted(current_nodes)[-1]
                    k8s_name = self._k8s_node_name_from_short(newest)
                    utilization = self._get_node_cpu_utilization(k8s_name)

                    if 0 <= utilization < self.scale_down_utilization_threshold:
                        # Underutilized — check if pods can move to other nodes.
                        source_pods = self._get_workload_pods_on_node(k8s_name)
                        can_move = self._can_pods_be_rescheduled(k8s_name, source_pods) if source_pods else True

                        if can_move:
                            if newest not in self._node_idle_since:
                                self._node_idle_since[newest] = now

                            idle_duration = now - self._node_idle_since[newest]
                            if idle_duration >= self.scale_down_idle_sec:
                                self._record_event(
                                    "scale_down_detected",
                                    {
                                        "node": newest,
                                        "utilization": round(utilization, 3),
                                        "threshold": self.scale_down_utilization_threshold,
                                        "pod_count": len(source_pods),
                                        "idle_sec": round(idle_duration, 1),
                                    },
                                )
                                logger.info(
                                    "scale_down_node",
                                    node=newest,
                                    utilization=round(utilization, 3),
                                    idle_sec=round(idle_duration, 1),
                                )
                                self.delete_node(newest)
                                self._last_scale_down_ts = now
                                self._node_idle_since.pop(newest, None)
                        else:
                            self._node_idle_since.pop(newest, None)
                    else:
                        # Node above threshold or error; reset idle tracking.
                        self._node_idle_since.pop(newest, None)
            time.sleep(self._poll_interval_sec)

        logger.info("k3d_autoscaler_loop_stopped")

    def start_background(self) -> None:
        if self._thread and self._thread.is_alive():
            logger.warning("k3d_autoscaler_already_running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._scaling_loop, daemon=True, name="k3d-autoscaler")
        self._thread.start()
        self._record_event("autoscaler_started", {"cluster": self.cluster_name})

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)
        self._thread = None
        self._record_event("autoscaler_stopped", {"cluster": self.cluster_name})

    def reset(self) -> bool:
        self.stop()
        dynamic_nodes = self._discover_dynamic_nodes()
        all_ok = True

        # Delete in reverse order for stable teardown of newest nodes first.
        for short_name in sorted(dynamic_nodes, reverse=True):
            if not self.delete_node(short_name):
                all_ok = False

        with self._lock:
            self._dynamic_nodes = []

        self._record_event("autoscaler_reset", {"deleted_nodes": dynamic_nodes, "ok": all_ok})
        return all_ok

    def get_log(self) -> List[Tuple[float, str, Dict]]:
        with self._lock:
            return list(self._events)

    def clear_log(self) -> None:
        """Clear event log (call between experiment runs)."""
        with self._lock:
            self._events = []

    def get_pool_status(self) -> Dict:
        dynamic_nodes = self._discover_dynamic_nodes()
        node_states: Dict[str, Dict[str, str]] = {}

        for short_name in dynamic_nodes:
            k8s_name = self._k8s_node_name_from_short(short_name)
            r = self._kubectl(["get", "node", k8s_name, "-o", "json"], timeout=10)
            if r.returncode != 0:
                node_states[short_name] = {
                    "k8s_node": k8s_name,
                    "ready": "unknown",
                    "label_node_type": "unknown",
                }
                continue

            try:
                node_obj = json.loads(r.stdout)
                ready = "False"
                for cond in node_obj.get("status", {}).get("conditions", []):
                    if cond.get("type") == "Ready":
                        ready = cond.get("status", "False")
                        break
                node_states[short_name] = {
                    "k8s_node": k8s_name,
                    "ready": ready,
                    "label_node_type": node_obj.get("metadata", {}).get("labels", {}).get("node-type", ""),
                }
            except json.JSONDecodeError:
                node_states[short_name] = {
                    "k8s_node": k8s_name,
                    "ready": "unknown",
                    "label_node_type": "unknown",
                }

        return {
            "cluster_name": self.cluster_name,
            "namespace": self.namespace,
            "running": self._thread is not None and self._thread.is_alive(),
            "min_nodes": self.min_nodes,
            "max_nodes": self.max_nodes,
            "provision_delay_min_sec": self.provision_delay_min_sec,
            "provision_delay_max_sec": self.provision_delay_max_sec,
            "dynamic_nodes": dynamic_nodes,
            "dynamic_node_count": len(dynamic_nodes),
            "node_states": node_states,
        }


class K3dAutoscalerAdapter:
    """
    Adapter wrapping K3dAutoscaler to match NodeProvisioner interface for ExperimentRunner.

    Implements: reset(), start_background(), stop(), get_log()
    Enables swapping between cordon/uncordon (Approach A) and k3d autoscaler (Approach B) via CLI flag.
    """

    def __init__(
        self,
        cluster_name: str = "thesis-hybrid",
        k3d_path: Optional[str] = None,
        kubectl_path: Optional[str] = None,
        k3s_image: str = "rancher/k3s:v1.28.5-k3s1",
        min_nodes: int = 1,
        max_nodes: int = 3,
        provision_delay_min_sec: int = 45,
        provision_delay_max_sec: int = 120,
        node_memory: str = "1g",
        namespace: str = "default",
        scale_down_cooldown_sec: int = 120,
        scale_down_idle_sec: int = 60,
        scale_down_utilization_threshold: float = 0.5,
        workload_pod_label: str = "app=test-app-warm",
        node_allocatable_cpu: float = 1.0,
    ) -> None:
        """Initialize adapter with sensible defaults for thesis experiments."""
        # Auto-discover paths from mise shims if not provided
        if k3d_path is None:
            k3d_path = os.path.expanduser("~/.local/share/mise/shims/k3d")
        if kubectl_path is None:
            kubectl_path = os.path.expanduser("~/.local/share/mise/shims/kubectl")

        self._autoscaler = K3dAutoscaler(
            cluster_name=cluster_name,
            k3d_path=k3d_path,
            kubectl_path=kubectl_path,
            k3s_image=k3s_image,
            min_nodes=min_nodes,
            max_nodes=max_nodes,
            provision_delay_min_sec=provision_delay_min_sec,
            provision_delay_max_sec=provision_delay_max_sec,
            node_memory=node_memory,
            namespace=namespace,
            scale_down_cooldown_sec=scale_down_cooldown_sec,
            scale_down_idle_sec=scale_down_idle_sec,
            scale_down_utilization_threshold=scale_down_utilization_threshold,
            workload_pod_label=workload_pod_label,
            node_allocatable_cpu=node_allocatable_cpu,
        )

    def reset(self) -> bool:
        """Stop autoscaler and delete all dynamic nodes. Implements NodeProvisioner interface."""
        return self._autoscaler.reset()

    def start_background(self) -> None:
        """Start autoscaler background polling loop. Implements NodeProvisioner interface."""
        self._autoscaler.start_background()

    def stop(self) -> None:
        """Stop autoscaler background polling loop. Implements NodeProvisioner interface."""
        self._autoscaler.stop()

    def get_log(self) -> List[Tuple[float, str, Dict]]:
        """Retrieve event log from autoscaler. Implements NodeProvisioner interface."""
        return self._autoscaler.get_log()

    def clear_log(self) -> None:
        """Clear event log between experiment runs."""
        self._autoscaler.clear_log()

    def get_pool_status(self) -> Dict:
        """Retrieve current pool status (convenience method, not in NodeProvisioner)."""
        return self._autoscaler.get_pool_status()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="K3d autoscaler CLI for thesis experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Print pool status
  python k3d_autoscaler.py status

  # Run smoke test: create, verify, delete node
  python k3d_autoscaler.py smoke-test

  # Start autoscaler and print status every 5s (Ctrl+C to stop)
  python k3d_autoscaler.py monitor
""",
    )
    parser.add_argument(
        "command",
        choices=["status", "smoke-test", "monitor"],
        help="Command to run",
    )
    parser.add_argument(
        "--cluster",
        default="thesis-hybrid",
        help="k3d cluster name (default: thesis-hybrid)",
    )
    parser.add_argument(
        "--max-nodes",
        type=int,
        default=3,
        help="Max dynamic nodes (default: 3)",
    )
    parser.add_argument(
        "--provision-delay-min",
        type=int,
        default=45,
        help="Min delay before provisioning (default: 45)",
    )
    parser.add_argument(
        "--provision-delay-max",
        type=int,
        default=120,
        help="Max delay before provisioning (default: 120)",
    )

    args = parser.parse_args()

    # Ensure PATH includes mise shims for k3d/kubectl discovery
    PATH = os.environ.get("PATH", "")
    MISE_SHIMS = os.path.expanduser("~/.local/share/mise/shims")
    if MISE_SHIMS not in PATH:
        os.environ["PATH"] = f"{MISE_SHIMS}:{PATH}"

    adapter = K3dAutoscalerAdapter(
        cluster_name=args.cluster,
        max_nodes=args.max_nodes,
        provision_delay_min_sec=args.provision_delay_min,
        provision_delay_max_sec=args.provision_delay_max,
    )

    if args.command == "status":
        # Print current pool status
        status = adapter.get_pool_status()
        print(json.dumps(status, indent=2))

    elif args.command == "smoke-test":
        # Quick smoke test: create node, verify, delete
        logger.info("smoke_test_start", cluster=args.cluster)

        # Check cluster exists
        autoscaler = adapter._autoscaler
        discovered = autoscaler._discover_dynamic_nodes()
        logger.info("smoke_test_cluster_check", existing_nodes=discovered)

        # Create one node (use dynamic-workload prefix so discovery works)
        test_node = "dynamic-workload-smoke"
        logger.info("smoke_test_creating_node", node=test_node)
        if autoscaler.create_node(test_node):
            logger.info("smoke_test_node_created", node=test_node)

            # Verify it's in the list
            discovered = autoscaler._discover_dynamic_nodes()
            if test_node in discovered:
                logger.info("smoke_test_discovery_ok", nodes=discovered)
            else:
                logger.error("smoke_test_discovery_failed", nodes=discovered)

            # Delete it
            logger.info("smoke_test_deleting_node", node=test_node)
            if autoscaler.delete_node(test_node):
                logger.info("smoke_test_node_deleted", node=test_node)
            else:
                logger.error("smoke_test_delete_failed", node=test_node)
        else:
            logger.error("smoke_test_create_failed", node=test_node)

        # Print final log
        log = adapter.get_log()
        print(json.dumps([(ts, evt, data) for ts, evt, data in log[-10:]], indent=2))
        logger.info("smoke_test_complete")

    elif args.command == "monitor":
        # Start autoscaler and print status every 5s
        logger.info("monitor_start", cluster=args.cluster)
        adapter.start_background()

        try:
            while True:
                time.sleep(5)
                status = adapter.get_pool_status()
                print(json.dumps(status, indent=2))
        except KeyboardInterrupt:
            logger.info("monitor_stopping")
            adapter.stop()
            logger.info("monitor_stopped")
