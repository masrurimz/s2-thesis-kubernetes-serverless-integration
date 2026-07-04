"""Kubernetes deployment scaling."""

from .scaler import DeploymentStatus, K8sScaler, K8sScalerConfig

__all__ = ["K8sScaler", "K8sScalerConfig", "DeploymentStatus"]
