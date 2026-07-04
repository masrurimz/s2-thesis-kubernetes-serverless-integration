"""Go-based Knative cold-start activator."""

try:
    from .manager import ActivatorManager
except ImportError:
    pass

__all__ = ["ActivatorManager"]
