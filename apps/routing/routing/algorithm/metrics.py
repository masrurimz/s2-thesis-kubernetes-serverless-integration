#!/usr/bin/env python3
"""
Centralized Prometheus metrics definitions for Algorithm 1 controller.

Provides metrics for H2 evaluation (proactive vs reactive adjustments).
"""

from prometheus_client import Counter, Histogram

# SLO violation counter - tracks violations by SLO name
slo_violation_total = Counter("slo_violation_total", "Total SLO violations detected", ["slo_name"])

# Routing decision counter - tracks decisions by type
routing_decision_total = Counter("routing_decision_total", "Total routing decisions made", ["decision_type"])

# Reaction time histogram - time from violation detection to weight adjustment
reaction_time_ms = Histogram(
    "reaction_time_ms",
    "Time between SLO violation detection and weight adjustment",
    buckets=[10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000],
)


def get_counter_value(counter, labels: dict) -> float:
    """Get the current value of a counter with labels (for testing)."""
    return counter.labels(**labels)._value.get()


def get_histogram_sum(histogram) -> float:
    """Get the sum of observed values in a histogram (for testing)."""
    return histogram._sum.get()
