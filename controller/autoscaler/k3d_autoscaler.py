#!/usr/bin/env python3
"""
K3d Autoscaler with Prometheus Metrics

Automatically scales k3d cluster agent nodes based on CPU utilization.
Exposes Prometheus metrics on port 9102.
"""

import subprocess
import time
import sys
from typing import Optional, Set

import structlog
from prometheus_client import Counter, Gauge, Histogram, start_http_server

logger = structlog.get_logger(__name__)

# Prometheus Metrics
k3d_nodes = Gauge("k3d_nodes", "Current k3d agent node count")
k3d_scale_up_events_total = Counter("k3d_scale_up_events_total", "Total scale up events")
k3d_scale_down_events_total = Counter("k3d_scale_down_events_total", "Total scale down events")
k3d_node_provision_latency_seconds = Histogram(
    "k3d_node_provision_latency_seconds",
    "Time from scale_up() to node Ready",
    buckets=(5.0, 10.0, 30.0, 60.0, 120.0, 300.0, float("inf")),
)

# Configuration defaults
DEFAULT_CLUSTER_NAME = "autoscaler-cluster"
DEFAULT_MIN_NODES = 1
DEFAULT_MAX_NODES = 5
DEFAULT_CPU_UPPER_THRESHOLD = 80
DEFAULT_CPU_LOWER_THRESHOLD = 30
DEFAULT_CHECK_INTERVAL = 60
DEFAULT_COOLDOWN_PERIOD = 120
DEFAULT_NODE_MEMORY_LIMIT = "512M"
DEFAULT_NODE_CPU_LIMIT = "1"
DEFAULT_NODE_MEMORY_SWAP_LIMIT = "512M"
DEFAULT_METRICS_PORT = 9102


class K3dAutoscaler:
    """K3d cluster autoscaler with Prometheus metrics."""

    def __init__(
        self,
        cluster_name: str = DEFAULT_CLUSTER_NAME,
        min_nodes: int = DEFAULT_MIN_NODES,
        max_nodes: int = DEFAULT_MAX_NODES,
        cpu_upper_threshold: int = DEFAULT_CPU_UPPER_THRESHOLD,
        cpu_lower_threshold: int = DEFAULT_CPU_LOWER_THRESHOLD,
        check_interval: int = DEFAULT_CHECK_INTERVAL,
        cooldown_period: int = DEFAULT_COOLDOWN_PERIOD,
        node_memory_limit: str = DEFAULT_NODE_MEMORY_LIMIT,
        node_cpu_limit: str = DEFAULT_NODE_CPU_LIMIT,
        node_memory_swap_limit: str = DEFAULT_NODE_MEMORY_SWAP_LIMIT,
        metrics_port: int = DEFAULT_METRICS_PORT,
    ):
        self.cluster_name = cluster_name
        self.min_nodes = min_nodes
        self.max_nodes = max_nodes
        self.cpu_upper_threshold = cpu_upper_threshold
        self.cpu_lower_threshold = cpu_lower_threshold
        self.check_interval = check_interval
        self.cooldown_period = cooldown_period
        self.node_memory_limit = node_memory_limit
        self.node_cpu_limit = node_cpu_limit
        self.node_memory_swap_limit = node_memory_swap_limit
        self.metrics_port = metrics_port
        self._metrics_server_started = False

    def start_metrics_server(self) -> None:
        """Start Prometheus metrics HTTP server."""
        if not self._metrics_server_started:
            start_http_server(self.metrics_port)
            self._metrics_server_started = True
            logger.info("prometheus_metrics_server_started", port=self.metrics_port)

    def is_metrics_server_available(self) -> bool:
        """Check if Kubernetes Metrics Server is available."""
        try:
            subprocess.run(
                ["kubectl", "top", "nodes"],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.debug("metrics_server_available")
            return True
        except subprocess.CalledProcessError:
            logger.error("metrics_server_unavailable")
            return False

    def get_average_cpu_utilization(self) -> Optional[float]:
        """Get average CPU utilization across agent nodes."""
        try:
            result = subprocess.run(
                ["kubectl", "top", "nodes", "-l", "k3s.io/role=agent", "--no-headers"],
                capture_output=True,
                text=True,
                check=True,
            )
            total_cpu = 0.0
            node_count = 0
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split()
                cpu_usage_str = parts[1]
                if cpu_usage_str.endswith("m"):
                    cpu_usage = int(cpu_usage_str.rstrip("m"))
                    cpu_percent = (cpu_usage / 1000) * 100
                else:
                    cpu_usage = float(cpu_usage_str)
                    cpu_percent = cpu_usage * 100
                total_cpu += cpu_percent
                node_count += 1
            average_cpu = total_cpu / node_count if node_count else 0.0
            logger.debug("cpu_utilization", total=total_cpu, nodes=node_count, average=average_cpu)
            return average_cpu
        except subprocess.CalledProcessError as e:
            logger.error("cpu_utilization_fetch_error", error=str(e))
            return None

    def get_current_node_count(self) -> int:
        """Get current agent node count and update Prometheus gauge."""
        try:
            result = subprocess.run(
                ["kubectl", "get", "nodes", "-l", "k3s.io/role=agent", "--no-headers"],
                capture_output=True,
                text=True,
                check=True,
            )
            node_count = len([line for line in result.stdout.strip().split("\n") if line])
            k3d_nodes.set(node_count)
            logger.debug("node_count", count=node_count)
            return node_count
        except subprocess.CalledProcessError as e:
            logger.error("node_count_fetch_error", error=str(e))
            return self.min_nodes

    def get_current_docker_containers(self) -> Set[str]:
        """Get set of current Docker container names."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=True,
            )
            containers = set(result.stdout.strip().split("\n"))
            logger.debug("docker_containers", count=len(containers))
            return containers
        except subprocess.CalledProcessError as e:
            logger.error("docker_containers_fetch_error", error=str(e))
            return set()

    def get_docker_container_by_node(self, node_name: str) -> Optional[str]:
        """Get Docker container name for a Kubernetes node."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={node_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=True,
            )
            container_name = result.stdout.strip()
            if container_name:
                logger.debug("docker_container_found", node=node_name, container=container_name)
                return container_name
            logger.warning("docker_container_not_found", node=node_name)
            return None
        except subprocess.CalledProcessError as e:
            logger.error("docker_container_lookup_error", node=node_name, error=str(e))
            return None

    def wait_for_node_ready(self, node_name: str, timeout: int = 300) -> bool:
        """Wait for node to be in Ready state."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                result = subprocess.run(
                    [
                        "kubectl",
                        "get",
                        "nodes",
                        node_name,
                        "-o",
                        "jsonpath={.status.conditions[?(@.type=='Ready')].status}",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                if result.stdout.strip() == "True":
                    logger.info("node_ready", node=node_name, elapsed=time.time() - start_time)
                    return True
            except subprocess.CalledProcessError:
                pass
            time.sleep(5)
        logger.warning("node_ready_timeout", node=node_name, timeout=timeout)
        return False

    def ensure_resource_limits_on_existing_nodes(self) -> None:
        """Apply resource limits to existing agent nodes."""
        logger.info("ensuring_resource_limits")
        try:
            result = subprocess.run(
                ["kubectl", "get", "nodes", "-l", "k3s.io/role=agent", "--no-headers"],
                capture_output=True,
                text=True,
                check=True,
            )
            node_names = [line.split()[0] for line in result.stdout.strip().split("\n") if line]

            for node in node_names:
                docker_container_name = self.get_docker_container_by_node(node)
                if not docker_container_name:
                    logger.warning("skipping_node", node=node, reason="container_not_found")
                    continue

                logger.info("applying_resource_limits", node=node, container=docker_container_name)
                try:
                    subprocess.run(
                        [
                            "docker",
                            "update",
                            "--cpus",
                            self.node_cpu_limit,
                            "--memory",
                            self.node_memory_limit,
                            "--memory-swap",
                            self.node_memory_swap_limit,
                            docker_container_name,
                        ],
                        check=True,
                    )
                    logger.info("resource_limits_applied", node=node)
                except subprocess.CalledProcessError as e:
                    logger.error("resource_limits_error", node=node, error=str(e))
        except subprocess.CalledProcessError as e:
            logger.error("fetch_nodes_error", error=str(e))

    def scale_up(self) -> None:
        """Scale up by adding a new agent node."""
        provision_start = time.time()
        node_name = f"{self.cluster_name}-agent-{int(time.time())}"
        logger.info("scaling_up", node=node_name)

        try:
            before_containers = self.get_current_docker_containers()

            subprocess.run(
                [
                    "k3d",
                    "node",
                    "create",
                    node_name,
                    "--cluster",
                    self.cluster_name,
                    "--role",
                    "agent",
                    "--k3s-node-label",
                    "k3s.io/role=agent",
                ],
                check=True,
            )
            logger.info("node_created", node=node_name)

            time.sleep(5)

            after_containers = self.get_current_docker_containers()
            new_containers = after_containers - before_containers

            if not new_containers:
                logger.error("no_new_container_found", node=node_name)
                return

            docker_container_name = new_containers.pop()
            logger.info("applying_resource_limits", container=docker_container_name)

            subprocess.run(
                [
                    "docker",
                    "update",
                    "--cpus",
                    self.node_cpu_limit,
                    "--memory",
                    self.node_memory_limit,
                    "--memory-swap",
                    self.node_memory_swap_limit,
                    docker_container_name,
                ],
                check=True,
            )
            logger.info("resource_limits_applied", container=docker_container_name)

            if self.wait_for_node_ready(node_name):
                provision_latency = time.time() - provision_start
                k3d_node_provision_latency_seconds.observe(provision_latency)
                k3d_scale_up_events_total.inc()
                self.get_current_node_count()
                logger.info(
                    "scale_up_complete",
                    node=node_name,
                    latency_seconds=provision_latency,
                )

            logger.info("cooldown", seconds=self.cooldown_period)
            time.sleep(self.cooldown_period)

        except subprocess.CalledProcessError as e:
            logger.error("scale_up_error", error=str(e))

    def get_nodes_sorted_by_load(self) -> list:
        """Get agent nodes sorted by CPU usage (descending)."""
        try:
            result = subprocess.run(
                ["kubectl", "top", "nodes", "-l", "k3s.io/role=agent", "--no-headers"],
                capture_output=True,
                text=True,
                check=True,
            )
            nodes = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split()
                name = parts[0]
                cpu_usage_str = parts[1]
                if cpu_usage_str.endswith("m"):
                    cpu_usage = int(cpu_usage_str.rstrip("m"))
                    cpu_percent = (cpu_usage / 1000) * 100
                else:
                    cpu_usage = float(cpu_usage_str)
                    cpu_percent = cpu_usage * 100
                nodes.append((name, cpu_percent))
            nodes_sorted = sorted(nodes, key=lambda x: x[1], reverse=True)
            logger.debug("nodes_sorted_by_load", nodes=nodes_sorted)
            return nodes_sorted
        except subprocess.CalledProcessError as e:
            logger.error("nodes_load_fetch_error", error=str(e))
            return []

    def scale_down(self) -> None:
        """Scale down by removing the least loaded agent node."""
        nodes_sorted = self.get_nodes_sorted_by_load()
        if not nodes_sorted:
            logger.warning("no_nodes_to_scale_down")
            return

        node_to_remove, cpu_percent = nodes_sorted[-1]
        logger.info("scaling_down", node=node_to_remove, cpu_percent=cpu_percent)

        try:
            subprocess.run(["kubectl", "cordon", node_to_remove], check=True)
            logger.debug("node_cordoned", node=node_to_remove)

            subprocess.run(
                [
                    "kubectl",
                    "drain",
                    node_to_remove,
                    "--ignore-daemonsets",
                    "--delete-emptydir-data",
                    "--force",
                ],
                check=True,
            )
            logger.debug("node_drained", node=node_to_remove)

            subprocess.run(["k3d", "node", "delete", node_to_remove], check=True)
            logger.info("node_deleted", node=node_to_remove)

            k3d_scale_down_events_total.inc()
            self.get_current_node_count()

            logger.info("cooldown", seconds=self.cooldown_period)
            time.sleep(self.cooldown_period)

        except subprocess.CalledProcessError as e:
            logger.error("scale_down_error", error=str(e))

    def run(self) -> None:
        """Main autoscaler loop."""
        logger.info("autoscaler_starting", cluster=self.cluster_name)
        self.start_metrics_server()
        self.ensure_resource_limits_on_existing_nodes()
        self.get_current_node_count()

        while True:
            if not self.is_metrics_server_available():
                logger.warning("metrics_server_unavailable_skipping_cycle")
            else:
                average_cpu = self.get_average_cpu_utilization()
                if average_cpu is None:
                    logger.warning("cpu_unavailable_skipping_cycle")
                else:
                    node_count = self.get_current_node_count()
                    logger.info(
                        "autoscaler_check",
                        average_cpu=f"{average_cpu:.2f}%",
                        node_count=node_count,
                    )

                    if average_cpu > self.cpu_upper_threshold and node_count < self.max_nodes:
                        logger.info("threshold_exceeded_scaling_up")
                        self.scale_up()
                    elif average_cpu < self.cpu_lower_threshold and node_count > self.min_nodes:
                        logger.info("below_threshold_scaling_down")
                        self.scale_down()
                    else:
                        logger.info("no_scaling_action_required")

            logger.info("sleeping", seconds=self.check_interval)
            time.sleep(self.check_interval)


def main() -> None:
    """Entry point."""
    autoscaler = K3dAutoscaler()
    try:
        autoscaler.run()
    except KeyboardInterrupt:
        logger.info("autoscaler_terminated_by_user")
        sys.exit(0)
    except Exception as e:
        logger.exception("unexpected_error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
