"""Experiment analysis CLI — Typer sub-app ported from apps/scripts/.

Thin orchestration layer over ``libs/analysis`` (domain) and ``libs/shared``
(stats primitives, scenario constants, models). Each command reproduces the
stdout / file output of a former standalone script while delegating the
reusable logic to the shared libraries.
"""
