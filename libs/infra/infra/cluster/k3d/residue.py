"""Residue an earlier run leaves in the cluster.

Runs scale the workload up and down and the node autoscaler creates and deletes
nodes underneath it. What survives is not neutral: a dynamic node left behind is
capacity the next run cannot provision, and a pod left on a deleted node still
holds CPU on the nodes that remain. Both change what the next run measures, so
they are cleared rather than inherited.
"""

from __future__ import annotations

import json

import structlog

from infra.cluster.k3d.shaping import list_nodes, remove_node
from infra.commands import run

logger = structlog.get_logger(__name__)


def prune_dynamic_nodes(cluster: str, *, dry_run: bool = False) -> list[str]:
    """Delete autoscaler-created nodes left behind by an earlier run.

    Dynamic nodes belong to the autoscaler while a run is in flight; between runs
    they are residue, and a node that already exists is capacity the run cannot
    provision — exactly the condition that decides whether the node tier is
    exercised at all.
    """
    actions: list[str] = []
    for node in list_nodes(cluster):
        if node["role"] != "agent" or "dynamic" not in node["name"]:
            continue
        actions.append(f"deleted leftover dynamic node {node['name']}")
        remove_node(cluster, node["name"], dry_run=dry_run)

    if actions:
        logger.info("dynamic_nodes_pruned", cluster=cluster, count=len(actions))
    return actions


def prune_orphaned_pods(cluster: str, *, namespace: str = "default", dry_run: bool = False) -> list[str]:
    """Delete workload pods whose node no longer exists."""
    live = {node["name"] for node in list_nodes(cluster)}
    if not live:
        return []

    context = f"k3d-{cluster}"
    listed = run(["kubectl", "--context", context, "-n", namespace, "get", "pods", "-o", "json"])
    if listed.returncode != 0:
        logger.warning("pod_list_failed", cluster=cluster, stderr=listed.stderr.strip())
        return []

    try:
        pods = json.loads(listed.stdout).get("items", [])
    except json.JSONDecodeError:
        logger.warning("pod_list_parse_failed", cluster=cluster)
        return []

    actions: list[str] = []
    for pod in pods:
        name = pod.get("metadata", {}).get("name", "")
        node = pod.get("spec", {}).get("nodeName", "")
        if not name or not node or node in live:
            continue
        actions.append(f"deleted orphaned pod {name} (node {node} is gone)")
        if not dry_run:
            run(
                [
                    "kubectl",
                    "--context",
                    context,
                    "-n",
                    namespace,
                    "delete",
                    "pod",
                    name,
                    "--force",
                    "--grace-period=0",
                    "--ignore-not-found",
                ]
            )

    if actions:
        logger.info("orphaned_pods_pruned", cluster=cluster, count=len(actions))
    return actions
