"""Cluster CPU allocation fairness verifier.

Mirrors the HealthChecker pattern: verify_all() returns dict[str, bool],
each check is a separate method. Used by both `thesis infra verify` CLI
and the E2E pytest suite.
"""

import subprocess

import structlog

logger = structlog.get_logger(__name__)

CLUSTER_NAME = "thesis-hybrid"
CLUSTER_NAME_SERVERLESS = "thesis-serverless"
NODE_SERVER = f"k3d-{CLUSTER_NAME}-server-0"
NODE_WORKLOAD_0 = f"k3d-{CLUSTER_NAME}-agent-0"
NODE_WORKLOAD_1 = f"k3d-{CLUSTER_NAME}-agent-1"
NODE_SERVERLESS_SERVER = f"k3d-{CLUSTER_NAME_SERVERLESS}-server-0"
NODE_SERVERLESS_AGENT = f"k3d-{CLUSTER_NAME_SERVERLESS}-agent-0"


class ClusterVerifier:
    """Verify node CPU allocation fairness and configuration."""

    def __init__(self) -> None:
        self.cluster_name = CLUSTER_NAME

    def _run(self, cmd: list[str], timeout: int = 15) -> subprocess.CompletedProcess[str]:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def check_docker_cpus(self, container_name: str, expected: float) -> bool:
        """Check that a Docker container has the expected NanoCpus limit."""
        r = self._run(["docker", "inspect", container_name, "--format", "{{.HostConfig.NanoCpus}}"])
        if r.returncode != 0:
            logger.warning("docker_inspect_failed", container=container_name, stderr=r.stderr.strip())
            return False
        try:
            actual_cpus = int(r.stdout.strip()) / 1e9
        except ValueError:
            logger.warning("docker_inspect_parse_failed", container=container_name, output=r.stdout.strip())
            return False
        passed = abs(actual_cpus - expected) < 0.01
        if not passed:
            logger.info(
                "docker_cpus_mismatch",
                container=container_name,
                expected=expected,
                actual=actual_cpus,
            )
        return passed

    def check_allocatable_bounded(self, node_name: str, max_cores: float) -> bool:
        """Check that a node's allocatable CPU is within the expected bound.

        This is the CRITICAL check: validates Docker --cpus actually constrains
        the kubelet's reported allocatable.
        """
        r = self._run(["kubectl", "get", "node", node_name, "-o", "json"])
        if r.returncode != 0:
            logger.warning("kubectl_node_failed", node=node_name, stderr=r.stderr.strip())
            return False
        import json

        try:
            node_info = json.loads(r.stdout)
            cpu_str = node_info["status"]["allocatable"]["cpu"]
        except (json.JSONDecodeError, KeyError, TypeError):
            logger.warning("allocatable_parse_failed", node=node_name)
            return False

        # Parse millicores or cores: "930m" -> 0.93, "930" -> 930.0
        if cpu_str.endswith("m"):
            cores = int(cpu_str.rstrip("m")) / 1000
        else:
            cores = float(cpu_str)

        passed = cores <= max_cores
        if not passed:
            logger.info(
                "allocatable_exceeds_bound",
                node=node_name,
                allocatable_cores=cores,
                max_cores=max_cores,
            )
        return passed

    def check_node_label(self, node_name: str, key: str, expected: str) -> bool:
        """Check that a node has the expected label value."""
        r = self._run(["kubectl", "get", "node", node_name, "-o", f"jsonpath={{.metadata.labels.{key}}}"])
        if r.returncode != 0:
            return False
        actual = r.stdout.strip()
        return actual == expected

    def check_capacity_ratio(self, infra_node: str, workload_node: str, max_ratio: float = 4.0) -> bool:
        """Check that infra/workload allocatable CPU ratio is acceptable."""
        r_infra = self._run(["kubectl", "get", "node", infra_node, "-o", "json"])
        r_workload = self._run(["kubectl", "get", "node", workload_node, "-o", "json"])
        if r_infra.returncode != 0 or r_workload.returncode != 0:
            return False

        import json

        try:
            infra_info = json.loads(r_infra.stdout)
            workload_info = json.loads(r_workload.stdout)
            infra_cpu = self._parse_cpu(infra_info["status"]["allocatable"]["cpu"])
            workload_cpu = self._parse_cpu(workload_info["status"]["allocatable"]["cpu"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return False

        if workload_cpu <= 0:
            return False
        ratio = infra_cpu / workload_cpu
        return ratio <= max_ratio

    @staticmethod
    def _parse_cpu(cpu_str: str) -> float:
        """Parse Kubernetes CPU string to cores: '930m' -> 0.93, '2' -> 2.0."""
        if cpu_str.endswith("m"):
            return int(cpu_str.rstrip("m")) / 1000
        return float(cpu_str)

    def verify_all(self) -> dict[str, bool]:
        """Run all checks and return a named mapping of results.

        Both hybrid agents are workload nodes at 1.0 CPU each.
        Serverless agent has 3.0 CPU for Knative capacity.
        """
        results: dict[str, bool] = {
            # Hybrid cluster — Docker CPU limits
            "docker_cpus_hybrid_server": self.check_docker_cpus(NODE_SERVER, expected=1.0),
            "docker_cpus_hybrid_agent0": self.check_docker_cpus(NODE_WORKLOAD_0, expected=1.0),
            "docker_cpus_hybrid_agent1": self.check_docker_cpus(NODE_WORKLOAD_1, expected=1.0),
            # Hybrid cluster — allocatable bounded by Docker limit
            "allocatable_hybrid_agent0_bounded": self.check_allocatable_bounded(NODE_WORKLOAD_0, max_cores=1.5),
            "allocatable_hybrid_agent1_bounded": self.check_allocatable_bounded(NODE_WORKLOAD_1, max_cores=1.5),
            # Hybrid cluster — node labels
            "node_labels_correct": (
                self.check_node_label(NODE_SERVER, "node-type", "system")
                and self.check_node_label(NODE_WORKLOAD_0, "node-type", "workload")
                and self.check_node_label(NODE_WORKLOAD_1, "node-type", "workload")
            ),
            # Serverless cluster — Docker CPU limits
            "docker_cpus_serverless_server": self.check_docker_cpus(NODE_SERVERLESS_SERVER, expected=1.0),
            "docker_cpus_serverless_agent": self.check_docker_cpus(NODE_SERVERLESS_AGENT, expected=3.0),
        }
        return results
