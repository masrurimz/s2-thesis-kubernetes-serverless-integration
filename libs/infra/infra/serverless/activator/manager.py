"""Knative cold-start activator — build and deploy lifecycle.

Manages the Go-based serverless-activator: builds the Docker image,
deploys RBAC + Deployment + Service to the cluster.
"""

import importlib.resources

import structlog

from infra.commands import console, run

logger = structlog.get_logger(__name__)


class ActivatorManager:
    """Build and deploy the Knative cold-start activator."""

    def __init__(self, image_name: str = "k3d-registry.localhost:5000/serverless-activator:latest") -> None:
        self.image_name = image_name
        self._asset_dir = str(importlib.resources.files("infra").joinpath("serverless", "activator"))

    def build(self) -> bool:
        """Build the activator Docker image."""
        console.print("[bold]Building serverless-activator image...[/bold]")
        result = run(["docker", "build", "-t", self.image_name, self._asset_dir])
        if result.returncode != 0:
            logger.error("activator_build_failed", stderr=result.stderr)
            return False
        logger.info("activator_build_ok", image=self.image_name)
        console.print("[green]✓ Activator image built.[/green]")
        return True

    def deploy(self) -> bool:
        """Apply RBAC, Deployment, and Service manifests."""
        console.print("[bold]Deploying serverless-activator...[/bold]")
        for manifest in ["rbac.yaml", "deployment.yaml", "service.yaml"]:
            manifest_path = f"{self._asset_dir}/{manifest}"
            result = run(["kubectl", "apply", "-f", manifest_path])
            if result.returncode != 0:
                logger.error("activator_deploy_failed", manifest=manifest, stderr=result.stderr)
                return False
        logger.info("activator_deploy_ok")
        console.print("[green]✓ Activator deployed.[/green]")
        return True

    def undeploy(self) -> bool:
        """Remove the activator from the cluster."""
        console.print("[bold]Removing serverless-activator...[/bold]")
        for manifest in ["service.yaml", "deployment.yaml", "rbac.yaml"]:
            manifest_path = f"{self._asset_dir}/{manifest}"
            run(["kubectl", "delete", "-f", manifest_path], check=False)
        logger.info("activator_undeploy_ok")
        console.print("[green]✓ Activator removed.[/green]")
        return True

    def is_running(self) -> bool:
        """Check if the activator pod is running."""
        result = run(
            ["kubectl", "get", "deployment", "serverless-activator", "-o", "jsonpath={.status.readyReplicas}"],
        )
        return result.stdout.strip() not in ("", "0")
