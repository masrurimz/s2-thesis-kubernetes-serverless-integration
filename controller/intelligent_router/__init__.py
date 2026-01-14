"""
Sprint 2: Intelligent Router Package

Automated traffic weight adjustment based on load predictions.
Provides routing controller, HAProxy integration, and decision logging.
"""

__version__ = "2.0.0"

from .routing_controller import IntelligentRoutingController
from .weight_adjuster import HAProxyWeightAdjuster
from .algorithm1_controller import Algorithm1Controller, Algorithm1Config, RoutingDecision
from .decision_logger import DecisionLogger
from .fallback_handler import FallbackHandler

__all__ = [
    "IntelligentRoutingController",
    "HAProxyWeightAdjuster",
    "Algorithm1Controller",
    "Algorithm1Config",
    "RoutingDecision",
    "DecisionLogger",
    "FallbackHandler",
]
