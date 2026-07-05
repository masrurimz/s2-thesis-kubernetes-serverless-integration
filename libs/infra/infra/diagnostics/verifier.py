"""Cluster CPU allocation fairness verifier.

Mirrors the HealthChecker pattern: verify_all() returns dict[str, bool],
each check is a separate method. Used by both `thesis infra verify` CLI
and the E2E pytest suite.
"""

import subprocess

import structlog

logger = structlog.get_logger(__name__)

CLUSTER_NAME = "thesis-hybrid"
NODE_SERVER = f"k3d-{CLUSTER_NAME}-server-0"
NODE_INFRA = f"k3d-{CLUSTER_NAME}-agent-0"
NODE_WORKLOAD = f"k3d-{CLUSTER_NAME}-agent-1"


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
        """Run all checks and return a named mapping of results."""
        results: dict[str, bool] = {
            "docker_cpus_server": self.check_docker_cpus(NODE_SERVER, expected=1.0),
            "docker_cpus_infra": self.check_docker_cpus(NODE_INFRA, expected=2.0),
            "docker_cpus_workload": self.check_docker_cpus(NODE_WORKLOAD, expected=1.0),
            "workload_node_allocatable_bounded": self.check_allocatable_bounded(NODE_WORKLOAD, max_cores=2.0),
            "infra_node_allocatable_bounded": self.check_allocatable_bounded(NODE_INFRA, max_cores=3.0),
            "node_labels_correct": (
                self.check_node_label(NODE_SERVER, "node-type", "system")
                and self.check_node_label(NODE_INFRA, "node-type", "infra")
                and self.check_node_label(NODE_WORKLOAD, "node-type", "workload")
            ),
            "capacity_ratio_acceptable": self.check_capacity_ratio(NODE_INFRA, NODE_WORKLOAD, max_ratio=4.0),
        }
        return results
