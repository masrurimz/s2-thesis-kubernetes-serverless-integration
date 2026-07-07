"""ProvisionerClient Protocol for node-level autoscaler dependency injection."""

from typing import Any, Protocol


class ProvisionerClient(Protocol):
    """Contract for node-level autoscaler backends.

    Implemented by K3dAutoscalerAdapter (libs/infra) and
    NodeProvisioner (apps/experiment/infrastructure).
    """

    def reset(self) -> bool:
        """Reset to baseline state: delete dynamic nodes, clear logs."""
        ...

    def start_background(self) -> None:
        """Start background thread watching for Pending pods."""
        ...

    def stop(self) -> None:
        """Stop background thread."""
        ...

    def get_log(self) -> list[tuple[float, str, dict[str, Any]]]:
        """Return provisioning event log for experiment metadata."""
        ...

    def clear_log(self) -> None:
        """Clear event log between experiment runs."""
        ...
