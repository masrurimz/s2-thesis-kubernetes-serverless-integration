"""The conditions a run starts from, applied and checked in one place.

A run is only comparable to another when both started from the same testbed and
the same quiet machine. Stating that is easy; keeping it true is the tooling's
job, because the failure is silent in both directions:

* Leave a spare agent or a leftover dynamic node in the cluster and no pod ever
  goes pending, so the node autoscaler never fires and a hybrid comparison
  measures its own pod tier.
* Run while the host is oversubscribed and the work that is not the experiment
  lands in the tail latency, which then reads as the arm's behaviour.

Every entry point that executes a run goes through ``apply`` here, so no path can
skip the conditioning, and the report it returns is written into the run's journal
and manifest.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

# Above this multiple of the core count the host is too busy to measure on.
REFUSE_LOAD_RATIO = 1.0
# Above this the measurement is still taken, with the load recorded as a caveat.
WARN_LOAD_RATIO = 0.5


class ConditionsUnmet(RuntimeError):
    """The testbed or the host is not in a state where the run would mean anything."""


@dataclass(frozen=True)
class RunConditions:
    """What must be true before a run, as the experiment's own declaration."""

    agents: int = 1
    needs_prediction_server: bool = False
    cluster: str = "thesis-hybrid"
    check_host_load: bool = True
    # Report-only mode: inspect the testbed without converging or clearing it.
    converge: bool = True

    @classmethod
    def for_scenarios(
        cls, scenarios: tuple[str, ...] | list[str], *, agents: int = 1, cluster: str = "thesis-hybrid"
    ) -> RunConditions:
        """Derive the conditions a scenario set needs.

        The predictive arm needs a prediction server; everything that runs the node
        autoscaler needs a static agent count low enough for capacity to bind.
        """
        from shared.models.evidence import NodeEngagement

        needs_server = any(s in ("s4-hybrid-predictive",) or "predictive" in s for s in scenarios)
        needs_nodes = any(NodeEngagement.scenario_has_node_autoscaler(s) for s in scenarios)
        return cls(
            agents=agents if needs_nodes else 0,
            needs_prediction_server=needs_server,
            cluster=cluster,
        )


def _cpu_busy_ratio(sample_sec: float = 1.0) -> float:
    """Fraction of all cores busy, sampled from /proc/stat.

    The load average counts runnable threads, so a large thread pool reads as
    saturation even when cores are idle. What decides whether a latency
    measurement is trustworthy is how much CPU is actually in use.
    """
    import time

    def snapshot() -> tuple[int, int]:
        with open("/proc/stat") as handle:
            fields = [int(value) for value in handle.readline().split()[1:]]
        idle = fields[3] + (fields[4] if len(fields) > 4 else 0)
        return idle, sum(fields)

    idle_a, total_a = snapshot()
    time.sleep(sample_sec)
    idle_b, total_b = snapshot()
    total_delta = total_b - total_a
    if total_delta <= 0:
        return 0.0
    return 1.0 - (idle_b - idle_a) / total_delta


def _host_load(sample_sec: float = 1.0) -> dict[str, float]:
    cores = os.cpu_count() or 1
    load1 = os.getloadavg()[0]
    busy = _cpu_busy_ratio(sample_sec)
    return {"load1": load1, "cores": float(cores), "ratio": busy, "loadavg_ratio": load1 / cores}


def _busiest_processes(limit: int = 3) -> list[str]:
    """The processes most likely to be stealing the cores, for the failure message."""
    try:
        result = subprocess.run(
            ["ps", "-eo", "pcpu,comm", "--sort=-pcpu", "--no-headers"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:  # noqa: BLE001 — diagnostics must never raise
        return []
    return [line.strip() for line in result.stdout.splitlines()[:limit] if line.strip()]


def apply(conditions: RunConditions, *, scenario: str = "", console: Any = None) -> dict:
    """Converge the testbed, run the sanity checks, and refuse when unmet.

    Returns {"ok", "checks", "nodes", "actions", "load", "notes"}. Raises
    ConditionsUnmet when a check fails, so a caller cannot ignore it by accident.
    """
    from experiment.stages.daemon import is_port_listening
    from infra.readiness import ensure_testbed, inspect_testbed
    from shared.config import settings

    checks: dict[str, bool] = {}
    notes: list[str] = []

    converged = (
        ensure_testbed(cluster=conditions.cluster, agents=conditions.agents)
        if conditions.converge
        else inspect_testbed(cluster=conditions.cluster)
    )
    checks["testbed_converged"] = bool(converged["nodes"]["servers"])
    checks["haproxy_up"] = bool(converged["haproxy"])
    checks["prometheus_up"] = bool(converged["prometheus"])
    if converged["actions"] and console is not None:
        console.print(f"  [yellow]testbed conditioned:[/yellow] {', '.join(converged['actions'])}")

    from infra.readiness import app_endpoints_serving, cluster_nodes_ready

    checks["nodes_ready"] = cluster_nodes_ready(conditions.cluster)

    # Only the arms this scenario actually serves on: S2 drains the K8s deployment
    # to zero on purpose, and S1 never routes to Knative.
    needs_k8s = scenario != "s2-serverless-only"
    needs_knative = scenario != "s1-k8s-only"
    k8s_ok, knative_ok = app_endpoints_serving()
    if needs_k8s:
        checks["k8s_endpoint_serving"] = k8s_ok
    if needs_knative:
        checks["knative_endpoint_serving"] = knative_ok

    if conditions.needs_prediction_server:
        # The service is supervised per bundle; here we only require that whatever
        # answers on the port is alive, so an S4 run cannot start against nothing.
        checks["prediction_port"] = is_port_listening(settings.GRU_PORT)

    if conditions.check_host_load:
        load = _host_load()
        checks["host_load"] = load["ratio"] < REFUSE_LOAD_RATIO
        if load["ratio"] >= WARN_LOAD_RATIO:
            notes.append(
                f"host {load['ratio']:.0%} busy on {load['cores']:.0f} cores (load average {load['load1']:.1f})"
            )
    else:
        load = _host_load()

    report = {
        "ok": all(checks.values()),
        "checks": checks,
        "nodes": converged["nodes"],
        "actions": converged["actions"],
        "load": load,
        "notes": notes,
        "scenario": scenario,
    }

    if report["ok"]:
        logger.info("run_conditions_met", scenario=scenario, **load, notes=notes)
        return report

    failed = [name for name, ok in checks.items() if not ok]
    report["failed"] = failed
    if "host_load" in failed:
        report["busiest"] = _busiest_processes()
        notes.append(
            "host is oversubscribed: "
            + ", ".join(report["busiest"])
            + " — measurements taken now would carry that load in their tail latency"
        )
    logger.error("run_conditions_unmet", scenario=scenario, failed=failed)
    raise ConditionsUnmet(
        f"conditions unmet for {scenario or 'the run'}: {', '.join(failed)}"
        + (f" ({'; '.join(notes)})" if notes else "")
    )
