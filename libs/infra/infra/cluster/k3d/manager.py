"""K3d cluster management — create, delete, status.

Replaces deploy/k3d/create-cluster.sh and deploy/k3d/delete-cluster.sh.
"""

import importlib.resources

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
