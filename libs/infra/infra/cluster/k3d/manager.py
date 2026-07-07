"""K3d cluster management — create, delete, status.

Replaces deploy/k3d/create-cluster.sh and deploy/k3d/delete-cluster.sh.
"""

import importlib.resources
import time

import structlog

from infra.commands import check_command, console, run

logger = structlog.get_logger(__name__)

CLUSTER_NAME = "thesis-hybrid"
CLUSTER_NAME_SERVERLESS = "thesis-serverless"


class K3dManager:
    """Manages k3d clusters for thesis hybrid experiments.

    Two clusters:
    - thesis-hybrid: K8s with K3dAutoscaler (node scaling), HPA/Algorithm 2
    - thesis-serverless: Knative with KPA (no node autoscaler, scale-to-zero)
    """

    def __init__(self, cluster_name: str = CLUSTER_NAME) -> None:
        self.cluster_name = cluster_name
        # Resolve cluster config paths from package data
        self._cluster_yaml = importlib.resources.files("infra").joinpath("cluster", "k3d", "cluster.yaml")
        self._serverless_yaml = importlib.resources.files("infra").joinpath("cluster", "k3d", "cluster-serverless.yaml")

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

        All agent nodes at 1.0 CPU fit ~3 pods at 300m each.
        Knative is now in a separate cluster (thesis-serverless).
        Tolerates per-node failure (logs warning, continues).
        """
        # (container_name, cpus, memory)
        nodes = [
            ("k3d-thesis-hybrid-server-0", "1.0", "1g"),
            ("k3d-thesis-hybrid-agent-0", "1.0", "1g"),
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
        """Label nodes with node-type for scheduling isolation.

        All agent nodes are workload type (Knative moved to separate cluster).
        Waits for node registration, then applies labels.
        """
        time.sleep(5)

        labels = [
            ("k3d-thesis-hybrid-server-0", "system"),
            ("k3d-thesis-hybrid-agent-0", "workload"),
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

    # ------------------------------------------------------------------
    # Serverless cluster (thesis-serverless for Knative)
    # ------------------------------------------------------------------

    def create_serverless(self, clean: bool = True) -> bool:
        """Create the thesis-serverless k3d cluster for Knative.

        Separate control plane from thesis-hybrid ensures K3dAutoscaler
        node scaling doesn't affect Knative scheduling.
        """
        if clean and self.is_serverless_running():
            self.delete_serverless()

        console.print(f"[bold]Creating k3d cluster '{CLUSTER_NAME_SERVERLESS}'...[/bold]")
        result = run(["k3d", "cluster", "create", CLUSTER_NAME_SERVERLESS, "--config", str(self._serverless_yaml)])

        if result.returncode != 0:
            logger.error("k3d_serverless_create_failed", stderr=result.stderr)
            return False
        logger.info("k3d_serverless_create_ok", cluster=CLUSTER_NAME_SERVERLESS)
        console.print(f"[green]✓ Cluster '{CLUSTER_NAME_SERVERLESS}' created.[/green]")

        self._apply_serverless_node_resources()
        return True

    def _apply_serverless_node_resources(self) -> None:
        """Apply Docker CPU/memory limits to serverless cluster nodes."""
        nodes = [
            (f"k3d-{CLUSTER_NAME_SERVERLESS}-server-0", "1.0", "1g"),
            (f"k3d-{CLUSTER_NAME_SERVERLESS}-agent-0", "1.5", "2g"),
        ]
        for container, cpus, memory in nodes:
            result = run(
                ["docker", "update", "--cpus", cpus, "--memory", memory, "--memory-swap", memory, container],
                check=False,
            )
            if result.returncode != 0:
                logger.warning(
                    "docker_update_serverless_node_failed",
                    container=container,
                    cpus=cpus,
                    memory=memory,
                    stderr=result.stderr,
                )

    def delete_serverless(self) -> bool:
        """Delete the thesis-serverless cluster."""
        console.print(f"[bold]Deleting k3d cluster '{CLUSTER_NAME_SERVERLESS}'...[/bold]")
        run(["k3d", "cluster", "delete", CLUSTER_NAME_SERVERLESS])
        logger.info("k3d_serverless_delete_ok", cluster=CLUSTER_NAME_SERVERLESS)
        console.print(f"[green]✓ Cluster '{CLUSTER_NAME_SERVERLESS}' deleted.[/green]")
        return True

    def is_serverless_running(self) -> bool:
        """Check whether the serverless cluster exists."""
        result = run(["k3d", "cluster", "list"])
        return CLUSTER_NAME_SERVERLESS in (result.stdout or "")
