"""K3d agent-node shaping — converge the static agent count to a target."""

import json

import structlog

from infra.commands import run

logger = structlog.get_logger(__name__)


def list_nodes(cluster: str) -> list[dict]:
    """Return the cluster's k3d nodes as [{"name", "role", "state"}] dicts."""
    result = run(["k3d", "node", "list", "-o", "json"])
    if result.returncode != 0:
        logger.warning("k3d_node_list_failed", stderr=result.stderr)
        return []
    try:
        items = json.loads(result.stdout)
    except json.JSONDecodeError:
        logger.warning("k3d_node_list_parse_failed")
        return []
    # Cluster membership lives in runtimeLabels, not a top-level field, and the
    # node state arrives as a nested object keyed "State" with a "Status" inside.
    parsed = []
    for item in items:
        if (item.get("runtimeLabels") or {}).get("k3d.cluster") != cluster:
            continue
        state = item.get("state")
        if not state:
            state = (item.get("State") or {}).get("Status", "")
        parsed.append({"name": item.get("name", ""), "role": item.get("role", ""), "state": state})
    return parsed


def k8s_node_names(container_name: str) -> list[str]:
    """Candidate Kubernetes node names for a k3d container name.

    k3d appends a per-node instance suffix to the container and Kubernetes does
    not always carry it: a static agent declared as ``agent-1`` runs in container
    ``agent-1-0`` and registers as node ``agent-1``, while a node created at
    runtime registers with the suffix intact. Both are tried.
    """
    names = [container_name]
    if container_name.endswith("-0"):
        names.append(container_name[:-2])
    return names


def is_live_k8s_node(node_name: str, containers: set[str]) -> bool:
    """True when some k3d container is this node or is its suffixed counterpart."""
    return any(name == node_name or name.startswith(f"{node_name}-") for name in containers)


def remove_node(cluster: str, name: str, *, dry_run: bool = False) -> None:
    """Delete a node's container and its Kubernetes node object.

    k3d removes the container and stops there, so the node object stays behind
    reading NotReady: every readiness check then inherits a node that no longer
    exists, and the run refuses on a machine that is actually fine.
    """
    if dry_run:
        return
    run(["k3d", "node", "delete", name, "--cluster", cluster])
    for k8s_name in k8s_node_names(name):
        run(["kubectl", "--context", f"k3d-{cluster}", "delete", "node", k8s_name, "--ignore-not-found"])


def _agent_index(cluster: str, name: str) -> int | None:
    prefix = f"k3d-{cluster}-agent-"
    if not name.startswith(prefix):
        return None
    tail = name.removeprefix(prefix)
    if tail.endswith("-0"):
        # k3d appends a per-node instance suffix to the docker container name.
        tail = tail[:-2]
    return int(tail) if tail.isdigit() else None


def converge_agent_count(cluster: str, target: int, *, dry_run: bool = False) -> dict:
    """Bring the named k3d cluster to exactly `target` non-dynamic agent nodes.

    Dynamic nodes (names containing "dynamic") are never deleted. When the cluster
    has more agents than target, delete the highest-numbered static agents first.
    When it has fewer, create static agents named f"{cluster}-agent-{n}".

    Returns {"cluster": str, "before": int, "after": int, "actions": [str, ...],
             "dynamic_agents": int, "dry_run": bool}
    """
    nodes = list_nodes(cluster)
    agents = [node for node in nodes if node["role"] == "agent"]
    dynamic_agents = [node for node in agents if "dynamic" in node["name"]]
    static_agents = [node for node in agents if "dynamic" not in node["name"]]

    before = len(static_agents)
    current = before
    actions: list[str] = []

    if current > target:

        def deletion_order(node: dict) -> tuple[bool, int]:
            index = _agent_index(cluster, node["name"])
            return (index is not None, index if index is not None else 0)

        victims = sorted(static_agents, key=deletion_order, reverse=True)[: current - target]
        for node in victims:
            # remove_node clears the container and the node object: k3d alone leaves
            # the object behind reading NotReady.
            remove_node(cluster, node["name"], dry_run=dry_run)
            actions.append(f"delete agent {node['name']}")
            current -= 1
    elif current < target:
        next_index = (
            max(
                (
                    index
                    for index in (_agent_index(cluster, node["name"]) for node in static_agents)
                    if index is not None
                ),
                default=-1,
            )
            + 1
        )
        while current < target:
            name = f"{cluster}-agent-{next_index}"
            next_index += 1
            result = run(
                ["k3d", "node", "create", name, "--cluster", cluster, "--role", "agent"],
                dry_run=dry_run,
            )
            if result.returncode != 0:
                logger.error("k3d_node_create_failed", node=name, stderr=result.stderr)
                break
            actions.append(f"create agent {name}")
            current += 1

    logger.info("agent_count_converged", cluster=cluster, before=before, after=current, actions=len(actions))
    return {
        "cluster": cluster,
        "before": before,
        "after": current,
        "actions": actions,
        "dynamic_agents": len(dynamic_agents),
        "dry_run": dry_run,
    }
