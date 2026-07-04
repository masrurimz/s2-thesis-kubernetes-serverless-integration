"""Test application deployment manager — docker build + kubectl.

Replaces deploy/test-app/ shell logic.
"""

import importlib.resources

import structlog

from infra.commands import console, run

logger = structlog.get_logger(__name__)


class TestAppManager:
    """Build and deploy the Go test application to k3d."""

    def __init__(self, namespace: str = "default") -> None:
        self.namespace = namespace
        self._base = importlib.resources.files("infra").joinpath("workloads", "test_app")

    def build(self) -> bool:
        """Build the test-app Docker image."""
        dockerfile = str(self._base.joinpath("Dockerfile"))
        console.print("[bold]Building test-app Docker image...[/bold]")
        result = run(["docker", "build", "-t", "test-app:latest", "-f", dockerfile, "."])
        if result.returncode != 0:
            logger.error("test_app_build_failed", stderr=result.stderr)
            return False
        logger.info("test_app_build_ok")
        console.print("[green]✓ Test-app image built.[/green]")
        return True

    def deploy(self) -> bool:
        """Apply Kubernetes manifests for the test app."""
        manifests = [
            "k8s-deployment.yaml",
            "nodeport-services.yaml",
        ]
        console.print("[bold]Deploying test-app to cluster...[/bold]")
        for m in manifests:
            path = str(self._base.joinpath(m))
            result = run(["kubectl", "apply", "-f", path, "-n", self.namespace])
            if result.returncode != 0:
                logger.error("test_app_deploy_failed", manifest=m, stderr=result.stderr)
                return False
        logger.info("test_app_deploy_ok")
        console.print("[green]✓ Test-app deployed.[/green]")
        return True

    def undeploy(self) -> bool:
        """Remove test app from the cluster."""
        console.print("[bold]Removing test-app from cluster...[/bold]")
        manifests = ["k8s-deployment.yaml", "nodeport-services.yaml"]
        for m in manifests:
            path = str(self._base.joinpath(m))
            run(["kubectl", "delete", "-f", path, "-n", self.namespace, "--ignore-not-found"])
        logger.info("test_app_undeploy_ok")
        console.print("[green]✓ Test-app removed.[/green]")
        return True
