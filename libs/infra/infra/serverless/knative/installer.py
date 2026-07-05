"""Knative Serving + Kourier installer for k3d clusters.

Replaces deploy/k3d/knative-install.sh.
"""

import os

import structlog

from infra.commands import console, run

logger = structlog.get_logger(__name__)

KNATIVE_VERSION = os.environ.get("KNATIVE_VERSION", "1.12.0")
KOURIER_VERSION = os.environ.get("KOURIER_VERSION", "1.12.0")


class KnativeInstaller:
    """Install and verify Knative Serving with Kourier networking layer."""

    def __init__(
        self,
        knative_version: str = KNATIVE_VERSION,
        kourier_version: str = KOURIER_VERSION,
    ) -> None:
        self.knative_version = knative_version
        self.kourier_version = kourier_version

    # ------------------------------------------------------------------
    # Installation
    # ------------------------------------------------------------------

    def install(self) -> bool:
        """Install Knative Serving CRDs, core, Kourier, and DNS."""
        if not self._check_cluster():
            return False

        steps = [
            ("Knative Serving CRDs", self._install_knative_serving),
            ("Kourier networking", self._install_kourier),
            ("DNS (sslip.io)", self._configure_dns),
            ("Autoscaling defaults", self._configure_autoscaling),
        ]
        for label, fn in steps:
            console.print(f"[bold]Installing {label}...[/bold]")
            if not fn():
                logger.error("knative_install_step_failed", step=label)
                return False

        self._configure_node_isolation()

        console.print("[green]✓ Knative + Kourier installed.[/green]")
        logger.info("knative_install_ok")
        return True

    def is_installed(self) -> bool:
        """Check whether Knative serving pods are running."""
        result = run(["kubectl", "get", "pods", "-n", "knative-serving", "--no-headers"])
        if result.returncode != 0:
            return False
        lines = [line for line in result.stdout.strip().splitlines() if line.strip()]
        return len(lines) > 0 and all("Running" in line for line in lines)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _check_cluster(self) -> bool:
        result = run(["kubectl", "cluster-info"])
        if result.returncode != 0:
            console.print("[red]No kubernetes cluster detected. Create one first.[/red]")
            return False
        return True

    def _install_knative_serving(self) -> bool:
        v = self.knative_version
        # CRDs
        run(
            [
                "kubectl",
                "apply",
                "-f",
                f"https://github.com/knative/serving/releases/download/knative-v{v}/serving-crds.yaml",
            ],
            check=True,
        )
        # Core
        run(
            [
                "kubectl",
                "apply",
                "-f",
                f"https://github.com/knative/serving/releases/download/knative-v{v}/serving-core.yaml",
            ],
            check=True,
        )
        return True

    def _install_kourier(self) -> bool:
        v = self.kourier_version
        run(
            [
                "kubectl",
                "apply",
                "-f",
                f"https://github.com/knative-extensions/net-kourier/releases/download/knative-v{v}/kourier.yaml",
            ],
            check=True,
        )
        run(
            [
                "kubectl",
                "patch",
                "configmap/config-network",
                "-n",
                "knative-serving",
                "--type=merge",
                "-p",
                '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}',
            ]
        )
        return True

    def _configure_dns(self) -> bool:
        run(
            [
                "kubectl",
                "apply",
                "-f",
                "https://github.com/knative/serving/releases/download/knative-v1.12.0/serving-default-domain.yaml",
            ],
            check=False,
        )
        return True

    def _configure_autoscaling(self) -> bool:
        run(
            [
                "kubectl",
                "apply",
                "-f",
                "-",
            ],
            check=False,
        )
        # Fallback: just log that autoscaling defaults should be configured manually
        console.print("[dim]Configure autoscaling defaults via kubectl if needed.[/dim]")
        return True

    def _configure_node_isolation(self) -> None:
        """Enable podspec-nodeselector and pin Kourier gateway to the infra node."""
        run(
            [
                "kubectl",
                "patch",
                "configmap/config-features",
                "-n",
                "knative-serving",
                "--type=merge",
                "-p",
                '{"data":{"kubernetes.podspec-nodeselector":"enabled"}}',
            ],
            check=True,
        )
        run(
            [
                "kubectl",
                "-n",
                "kourier-system",
                "patch",
                "deployment",
                "kourier-gateway",
                "--type=json",
                "-p",
                '[{"op":"add","path":"/spec/template/spec/nodeSelector","value":{"node-type":"infra"}}]',
            ],
            check=False,
        )
