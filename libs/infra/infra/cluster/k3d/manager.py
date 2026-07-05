"""K3d cluster management — create, delete, status.

Replaces deploy/k3d/create-cluster.sh and deploy/k3d/delete-cluster.sh.
"""

import importlib.resources
import time

import structlog

from infra.commands import check_command, console, run

logger = structlog.get_logger(__name__)

CLUSTER_NAME = "thesis-hybrid"


class K3dManager:
    """Manages a k3d cluster for thesis hybrid experiments."""

    def __init__(self, cluster_name: str = CLUSTER_NAME) -> None:
        self.cluster_name = cluster_name
        # Resolve the cluster.yaml path from package data
        self._cluster_yaml = importlib.resources.files("infra").joinpath("cluster", "k3d", "cluster.yaml")

    # ------------------------------------------------------------------
    # Prerequisites
    # ------------------------------------------------------------------

    def check_prerequisites(self) -> bool:
        """Check that k3d and docker are available."""
        missing = []
        if not check_command("k3d"):
            missing.append("k3d")
        if not check_command("docker"):
            missing.append("docker")
        if missing:
            console.print(f"[red]Missing prerequisites: {', '.join(missing)}[/red]")
            return False
        return True

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def create(self, clean: bool = False) -> bool:
        """Create the k3d cluster.

        If *clean* is True, any existing cluster with the same name is deleted first.
        """
        if not self.check_prerequisites():
            return False

        if clean and self.is_running():
            self.delete()

        console.print(f"[bold]Creating k3d cluster '{self.cluster_name}'...[/bold]")
        result = run(["k3d", "cluster", "create", self.cluster_name, "--config", str(self._cluster_yaml)])

        if result.returncode != 0:
            logger.error("k3d_create_failed", stderr=result.stderr)
            return False
        logger.info("k3d_create_ok", cluster=self.cluster_name)
        console.print(f"[green]✓ Cluster '{self.cluster_name}' created.[/green]")

        console.print("[bold]Applying Docker CPU/memory limits to nodes...[/bold]")
        self._apply_node_resources()

        console.print("[bold]Labeling nodes (system/infra/workload)...[/bold]")
        self._label_nodes()

        return True

    # ------------------------------------------------------------------
    # Node resource bounds (Docker --cpus/--memory to mimic cloud VM sizing)
    # ------------------------------------------------------------------

    def _apply_node_resources(self) -> None:
        """Apply Docker CPU/memory limits to each k3d node container.

        Bounds node capacity to mimic real cloud VM allocation (see PHASE_B_V4_DESIGN.md):
        agent-0 (infra/Knative) at 2.0 CPU mimics a t3.medium; workload nodes at 1.0 CPU
        fit ~4 pods at 200m each. Tolerates per-node failure (logs warning, continues).
        """
        # (container_name, cpus, memory)
        nodes = [
            ("k3d-thesis-hybrid-server-0", "1.0", "1g"),
            ("k3d-thesis-hybrid-agent-0", "2.0", "4g"),
            ("k3d-thesis-hybrid-agent-1", "1.0", "1g"),
        ]
        for container, cpus, memory in nodes:
            result = run(
                ["docker", "update", "--cpus", cpus, "--memory", memory, "--memory-swap", memory, container],
                check=False,
            )
            if result.returncode != 0:
                logger.warning(
                    "docker_update_node_failed",
                    container=container,
                    cpus=cpus,
                    memory=memory,
                    stderr=result.stderr,
                )

    def _label_nodes(self) -> None:
        """Label nodes with node-type=system/infra/workload for scheduling isolation.

        Waits for node registration, then applies labels. Tolerates per-node failure.
        """
        # Allow nodes to register with the API server before labeling.
        time.sleep(5)

        # (node_name, node-type value)
        labels = [
            ("k3d-thesis-hybrid-server-0", "system"),
            ("k3d-thesis-hybrid-agent-0", "infra"),
            ("k3d-thesis-hybrid-agent-1", "workload"),
        ]
        for node, node_type in labels:
            result = run(
                ["kubectl", "label", "node", node, f"node-type={node_type}", "--overwrite"],
                check=False,
            )
            if result.returncode != 0:
                logger.warning(
                    "kubectl_label_node_failed",
                    node=node,
                    node_type=node_type,
                    stderr=result.stderr,
                )

    # ------------------------------------------------------------------
    # Lifecycle (continued)
    # ------------------------------------------------------------------

    def delete(self) -> bool:
        """Delete the k3d cluster and clean up Docker resources."""
        console.print(f"[bold]Deleting k3d cluster '{self.cluster_name}'...[/bold]")

        # Delete cluster
        run(["k3d", "cluster", "delete", self.cluster_name])

        # Clean up orphaned volumes and networks
        run(["docker", "volume", "ls", "-q", "--filter", f"name=k3d-{self.cluster_name}"], check=False)
        run(["docker", "network", "ls", "-q", "--filter", f"name=k3d-{self.cluster_name}"], check=False)

        logger.info("k3d_delete_ok", cluster=self.cluster_name)
        console.print(f"[green]✓ Cluster '{self.cluster_name}' deleted.[/green]")
        return True

    def is_running(self) -> bool:
        """Check whether the cluster exists."""
        result = run(["k3d", "cluster", "list"])
        return self.cluster_name in (result.stdout or "")
