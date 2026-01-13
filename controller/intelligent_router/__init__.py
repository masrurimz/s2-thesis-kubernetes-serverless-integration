"""
Sprint 2: Intelligent Router Package

Automated traffic weight adjustment based on load predictions.
Provides routing controller, HAProxy integration, and decision logging.
"""

__version__ = "2.0.0"

from .routing_controller import IntelligentRoutingController

__all__ = ["IntelligentRoutingController"]