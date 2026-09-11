"""Testbed readiness — converge cluster and support services to a runnable state."""

import structlog

from infra.cluster.k3d.residue import prune_dynamic_nodes, prune_orphaned_pods
from infra.cluster.k3d.shaping import converge_agent_count, list_nodes
from infra.commands import run
from infra.networking.haproxy.manager import HAProxyManager
from infra.observability.prometheus.manager import PrometheusManager

logger = structlog.get_logger(__name__)

_SERVERLESS_CLUSTER = "thesis-serverless"


def _cluster_up(nodes: list[dict]) -> bool:
    return any(node["role"] == "server" and node["state"] == "running" for node in nodes)


def rebuild_testbed(
    cluster: str = "thesis-hybrid",
    *,
    agents: int = 1,
    skip_build: bool = False,
) -> dict:
    """Tear the testbed down and bring it back up, then converge it to `agents`.

    Every experiment inherits the previous one's residue: dynamic nodes the
    autoscaler kept, pods left warm, a cluster that has carried months of objects.
    Individually each is small; together they decide whether a run exercises node
    provisioning at all. Rebuilding removes the class at the cost of a few minutes,
    which belongs before an experiment rather than between its runs.

    Returns {"cluster", "ready", "actions", "summary"}.
    """
    from infra.cluster.k3d.manager import K3dManager
    from infra.networking.haproxy.manager import HAProxyManager
    from infra.observability.prometheus.manager import PrometheusManager
    from infra.serverless.knative.installer import KnativeInstaller
    from infra.workloads.deploy import deploy_test_app

    actions: list[str] = []

    PrometheusManager().stop()
    HAProxyManager().stop()
    actions.append("stopped haproxy and prometheus")

    manager = K3dManager()
    manager.delete()
    manager.create(clean=True)
    manager.create_serverless()
    manager.apply_node_resources()
    actions.append("recreated the hybrid and serverless clusters")

    if not KnativeInstaller(context=f"k3d-{_SERVERLESS_CLUSTER}").install():
        logger.error("knative_install_failed")
        return {"cluster": cluster, "ready": False, "actions": actions, "summary": "knative install failed"}
    actions.append("installed knative")

    if not HAProxyManager().start():
        logger.error("haproxy_start_failed")
        return {"cluster": cluster, "ready": False, "actions": actions, "summary": "haproxy did not start"}
    PrometheusManager().start()

    deployed = deploy_test_app(skip_build=skip_build)
    actions.extend(deployed["actions"])
    if not (deployed["k8s_ok"] and deployed["knative_ok"]):
        return {
            "cluster": cluster,
            "ready": False,
            "actions": actions,
            "summary": f"deploy failed: k8s={deployed['k8s_ok']} knative={deployed['knative_ok']}",
        }

    converged = ensure_testbed(cluster, agents=agents)
    actions.extend(converged["actions"])
    nodes = converged["nodes"]
    summary = (
        f"nodes: servers={nodes['servers']} agents={nodes['agents']} "
        f"(+{nodes['dynamic_agents']} dynamic) | haproxy={'up' if converged['haproxy'] else 'down'} "
        f"| prometheus={'up' if converged['prometheus'] else 'down'}"
    )
    ready = bool(converged["haproxy"] and converged["prometheus"] and converged["nodes"]["servers"])
    return {"cluster": cluster, "ready": ready, "actions": actions, "summary": summary}


def ensure_testbed(
    cluster: str = "thesis-hybrid",
    *,
    servers: int = 1,
    agents: int = 1,
    prune_dynamic: bool = True,
    dry_run: bool = False,
) -> dict:
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

    actions.extend(converge_agent_count(cluster, agents, dry_run=dry_run)["actions"])

    # Residue from earlier runs: a dynamic node left behind is free capacity, and a
    # pod left behind on a deleted node still holds CPU on the nodes that remain.
    if prune_dynamic:
        actions.extend(prune_dynamic_nodes(cluster, dry_run=dry_run))
    actions.extend(prune_orphaned_pods(cluster, dry_run=dry_run))

    final_nodes = list_nodes(cluster)
    server_count = sum(1 for node in final_nodes if node["role"] == "server")
    static_agents = sum(1 for node in final_nodes if node["role"] == "agent" and "dynamic" not in node["name"])
    dynamic_agents = sum(1 for node in final_nodes if node["role"] == "agent" and "dynamic" in node["name"])
    if server_count < servers:
        # Server nodes are reported, not converged: the testbed runs a single server.
        logger.warning("testbed_server_count_below_expected", cluster=cluster, have=server_count, want=servers)

    return {
        "cluster": cluster,
        "changed": bool(actions),
        "actions": actions,
        "nodes": {"servers": server_count, "agents": static_agents, "dynamic_agents": dynamic_agents},
        "haproxy": haproxy_up,
        "prometheus": prometheus_up,
    }
