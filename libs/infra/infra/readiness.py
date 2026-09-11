"""Testbed readiness — converge cluster and support services to a runnable state."""

import structlog

from infra.cluster.k3d.shaping import converge_agent_count, list_nodes
from infra.commands import run
from infra.networking.haproxy.manager import HAProxyManager
from infra.observability.prometheus.manager import PrometheusManager

logger = structlog.get_logger(__name__)


def _cluster_up(nodes: list[dict]) -> bool:
    return any(node["role"] == "server" and node["state"] == "running" for node in nodes)


def ensure_testbed(cluster: str = "thesis-hybrid", *, servers: int = 1, agents: int = 1) -> dict:
    """Converge the testbed to a runnable state and report what it changed.

    Steps, each idempotent and each reported in `actions` only when it changed
    something: start the named k3d cluster; start the HAProxy compose service from
    libs/infra/infra/networking/haproxy/docker-compose.yml; start the Prometheus
    compose service from libs/infra/infra/observability/prometheus/docker-compose.yml;
    converge the agent count via converge_agent_count.

    Returns {"cluster": str, "changed": bool, "actions": [str, ...],
             "nodes": {"servers": int, "agents": int},
             "haproxy": bool, "prometheus": bool}
    """
    actions: list[str] = []

    if not _cluster_up(list_nodes(cluster)):
        result = run(["k3d", "cluster", "start", cluster])
        if result.returncode == 0:
            actions.append(f"started cluster {cluster}")
            logger.info("k3d_cluster_started", cluster=cluster)
        else:
            logger.error("k3d_cluster_start_failed", cluster=cluster, stderr=result.stderr)

    haproxy = HAProxyManager()
    haproxy_up = haproxy.is_running()
    if not haproxy_up and haproxy.start():
        haproxy_up = True
        actions.append("started haproxy")

    prometheus = PrometheusManager()
    prometheus_up = prometheus.is_running()
    if not prometheus_up and prometheus.start():
        prometheus_up = True
        actions.append("started prometheus")

    actions.extend(converge_agent_count(cluster, agents)["actions"])

    final_nodes = list_nodes(cluster)
    server_count = sum(1 for node in final_nodes if node["role"] == "server")
    agent_count = sum(1 for node in final_nodes if node["role"] == "agent")
    if server_count < servers:
        # Server nodes are reported, not converged: the testbed runs a single server.
        logger.warning("testbed_server_count_below_expected", cluster=cluster, have=server_count, want=servers)

    return {
        "cluster": cluster,
        "changed": bool(actions),
        "actions": actions,
        "nodes": {"servers": server_count, "agents": agent_count},
        "haproxy": haproxy_up,
        "prometheus": prometheus_up,
    }
