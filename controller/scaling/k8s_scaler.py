#!/usr/bin/env python3
"""
K8s Scaler: Real Kubernetes replica scaling via kubectl.

Provides subprocess-based kubectl interface for Algorithm 2 integration.
"""

import json
import subprocess
from dataclasses import dataclass
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class K8sScalerConfig:
    """Configuration for K8s scaler."""
    namespace: str = "default"
    deployment: str = "test-app-warm"
    kubectl_path: str = "kubectl"
    timeout_sec: int = 5


@dataclass
class DeploymentStatus:
    """Current deployment replica status."""
    spec_replicas: int
    available_replicas: int
    updated_replicas: int
    ready: bool

    def __str__(self) -> str:
        return (
            f"spec={self.spec_replicas} available={self.available_replicas} "
            f"updated={self.updated_replicas} ready={self.ready}"
        )


class K8sScaler:
    """Manages Kubernetes deployment scaling via kubectl subprocess."""

    def __init__(self, config: Optional[K8sScalerConfig] = None):
        self.config = config or K8sScalerConfig()
        logger.info(
            "K8sScaler initialized",
            namespace=self.config.namespace,
            deployment=self.config.deployment,
        )

    def _run_kubectl(self, args: list[str]) -> Optional[str]:
        """Run a kubectl command and return stdout, or None on failure."""
        cmd = [self.config.kubectl_path, "-n", self.config.namespace] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_sec,
            )
            if result.returncode != 0:
                logger.error(
                    "kubectl command failed",
                    cmd=cmd,
                    stderr=result.stderr.strip(),
                    returncode=result.returncode,
                )
                return None
            return result.stdout
        except subprocess.TimeoutExpired:
            logger.error("kubectl command timed out", cmd=cmd, timeout=self.config.timeout_sec)
            return None
        except FileNotFoundError:
            logger.error("kubectl not found", path=self.config.kubectl_path)
            return None

    def scale(self, replicas: int) -> bool:
        """Scale the deployment to the given replica count."""
        output = self._run_kubectl([
            "scale",
            f"deployment/{self.config.deployment}",
            f"--replicas={replicas}",
        ])
        if output is not None:
            logger.info(
                "k8s_scale_executed",
                deployment=self.config.deployment,
                replicas=replicas,
            )
            return True
        return False

    def get_deployment_status(self) -> Optional[DeploymentStatus]:
        """Query current deployment status via kubectl get -o json."""
        output = self._run_kubectl([
            "get",
            f"deployment/{self.config.deployment}",
            "-o", "json",
        ])
        if output is None:
            return None

        try:
            data = json.loads(output)
            spec_replicas = data.get("spec", {}).get("replicas", 0)
            status = data.get("status", {})
            available = status.get("availableReplicas", 0) or 0
            updated = status.get("updatedReplicas", 0) or 0

            return DeploymentStatus(
                spec_replicas=spec_replicas,
                available_replicas=available,
                updated_replicas=updated,
                ready=(available == spec_replicas and spec_replicas > 0),
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to parse deployment status", error=str(e))
            return None

    def is_ready(self) -> bool:
        """Check if available replicas match desired replicas."""
        status = self.get_deployment_status()
        if status is None:
            return False
        return status.ready

    def check_hpa_conflict(self) -> bool:
        """Check if an HPA exists targeting this deployment. Returns True if conflict found."""
        output = self._run_kubectl(["get", "hpa", "-o", "json"])
        if output is None:
            return False

        try:
            data = json.loads(output)
            for item in data.get("items", []):
                target = item.get("spec", {}).get("scaleTargetRef", {})
                if (target.get("kind") == "Deployment"
                        and target.get("name") == self.config.deployment):
                    logger.error(
                        "HPA conflict detected — Algorithm 2 manual scaling may conflict with HPA",
                        hpa_name=item.get("metadata", {}).get("name"),
                        deployment=self.config.deployment,
                    )
                    return True
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Failed to parse HPA list", error=str(e))

        return False
