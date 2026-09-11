"""Infrastructure management CLI — Typer app.

Commands:
    thesis infra setup              Full infrastructure setup (clusters + Knative + HAProxy)
    thesis infra teardown           Tear down everything
    thesis infra health             Health check all components
    thesis infra status             Show infrastructure status
    thesis infra cluster create     Create k3d cluster
    thesis infra cluster delete     Delete k3d cluster
    thesis infra deploy-app         Build + deploy test-app to both clusters
    thesis infra verify             Verify node CPU allocation fairness
"""

import typer
from rich.console import Console

app = typer.Typer(help="Infrastructure management", no_args_is_help=True)
console = Console()


@app.command()
def setup(
    clean: bool = typer.Option(False, "--clean", help="Delete existing cluster before setup"),
    skip_monitoring: bool = typer.Option(False, "--skip-monitoring", help="Skip Prometheus deployment"),
) -> None:
    """Full infrastructure setup: cluster, serverless, networking, monitoring."""
    from infra.cluster.k3d.manager import K3dManager
    from infra.networking.haproxy.manager import HAProxyManager
    from infra.serverless.knative.installer import KnativeInstaller

    console.rule("[bold]Infrastructure Setup")

    # 1. Create cluster
    k3d = K3dManager()
    if not k3d.create(clean=clean):
        console.print("[red]Cluster creation failed.[/red]")
        raise typer.Exit(1)

    # 1b. Create serverless cluster (Knative)
    if not k3d.create_serverless():
        console.print("[red]Serverless cluster creation failed.[/red]")
        raise typer.Exit(1)

    # 2. Install Knative
    knative = KnativeInstaller(context="k3d-thesis-serverless")
    if not knative.install():
        console.print("[red]Knative installation failed.[/red]")
        raise typer.Exit(1)

    # 3. Start HAProxy
    haproxy = HAProxyManager()
    if not haproxy.start():
        console.print("[red]HAProxy start failed.[/red]")
        raise typer.Exit(1)

    # 4. Start Prometheus (optional)
    if not skip_monitoring:
        from infra.observability.prometheus.manager import PrometheusManager

        prom = PrometheusManager()
        if not prom.start():
            console.print("[yellow]Prometheus start failed (non-fatal).[/yellow]")

    console.rule("[bold green]Setup Complete")


@app.command()
def teardown(
    fast: bool = typer.Option(False, "--fast", help="Skip verification"),
) -> None:
    """Tear down all infrastructure components."""
    from infra.cluster.k3d.manager import K3dManager
    from infra.networking.haproxy.manager import HAProxyManager
    from infra.observability.prometheus.manager import PrometheusManager

    console.rule("[bold]Infrastructure Teardown")

    # Stop components in reverse order
    PrometheusManager().stop()
    HAProxyManager().stop()
    K3dManager().delete()

    if not fast:
        console.rule("[bold green]Teardown Complete")
    else:
        console.print("[green]Teardown done.[/green]")


@app.command()
def health() -> None:
    """Health check all infrastructure components."""
    from infra.diagnostics.checker import HealthChecker

    console.rule("[bold]Infrastructure Health Check")

    checker = HealthChecker()
    results = checker.check_all()

    healthy = sum(1 for v in results.values() if v)
    total = len(results)

    console.print(f"\n[bold]Result: {healthy}/{total} components healthy[/bold]")
    if healthy < total:
        raise typer.Exit(1)


@app.command()
def verify() -> None:
    """Verify node CPU allocation fairness and configuration."""
    from infra.diagnostics.verifier import ClusterVerifier

    console.rule("[bold]Node CPU Allocation Verification")

    verifier = ClusterVerifier()
    results = verifier.verify_all()

    for name, passed in results.items():
        icon = "[green]✓[/green]" if passed else "[red]✗[/red]"
        console.print(f"  {icon} {name}")

    passed_count = sum(1 for v in results.values() if v)
    total = len(results)

    console.print(f"\n[bold]Result: {passed_count}/{total} checks passed[/bold]")
    if passed_count < total:
        raise typer.Exit(1)


@app.command(name="apply-resources")
def apply_resources() -> None:
    """Apply Docker CPU/memory limits to existing k3d cluster nodes.

    Idempotent: safe to re-run. Enforces CalibrationConfig values for
    node-level CPU limits on both hybrid and serverless clusters.
    Use after cluster creation or after manual changes to restore correct limits.
    """
    from infra.cluster.k3d.manager import K3dManager

    k3d = K3dManager()

    console.rule("[bold]Applying Docker Resource Limits")

    # Hybrid cluster nodes
    console.print("[bold cyan]Hybrid cluster (thesis-hybrid)[/bold cyan]")
    hybrid_ok = k3d.apply_node_resources()
    if hybrid_ok:
        console.print("  [green]✓ All hybrid nodes updated[/green]")
    else:
        console.print("  [yellow]⚠ Some hybrid nodes failed (see logs)[/yellow]")

    # Serverless cluster nodes
    console.print("[bold cyan]Serverless cluster (thesis-serverless)[/bold cyan]")
    serverless_ok = k3d.apply_serverless_node_resources()
    if serverless_ok:
        console.print("  [green]✓ All serverless nodes updated[/green]")
    else:
        console.print("  [yellow]⚠ Some serverless nodes failed (see logs)[/yellow]")

    if hybrid_ok and serverless_ok:
        console.rule("[bold green]All Resource Limits Applied")
    else:
        console.print("[yellow]⚠ Some updates failed — check cluster status[/yellow]")
        raise typer.Exit(1)


@app.command()
def status() -> None:
    """Show infrastructure status."""
    from infra.cluster.k3d.manager import K3dManager
    from infra.networking.haproxy.manager import HAProxyManager
    from infra.observability.prometheus.manager import PrometheusManager

    console.rule("[bold]Infrastructure Status")

    items = [
        ("K3d Cluster", K3dManager().is_running()),
        ("HAProxy", HAProxyManager().is_running()),
        ("Prometheus", PrometheusManager().is_running()),
    ]

    for name, running in items:
        icon = "[green]✓ running[/green]" if running else "[red]✗ stopped[/red]"
        console.print(f"  {name}: {icon}")


@app.command()
def cluster(
    action: str = typer.Argument("status", help="Cluster action: create, delete, status"),
    clean: bool = typer.Option(False, "--clean", help="Delete existing cluster before create"),
) -> None:
    """Manage the k3d cluster."""
    from infra.cluster.k3d.manager import K3dManager

    k3d = K3dManager()

    if action == "create":
        if not k3d.create(clean=clean):
            raise typer.Exit(1)
    elif action == "delete":
        k3d.delete()
    elif action == "status":
        running = k3d.is_running()
        status_text = "[green]running[/green]" if running else "[red]not running[/red]"
        console.print(f"  Cluster '{k3d.cluster_name}': {status_text}")
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        raise typer.Exit(1)


@app.command()
def ensure(
    cluster: str = typer.Option("thesis-hybrid", help="k3d cluster name"),
    agents: int = typer.Option(1, help="Static agent nodes the cluster should carry"),
    servers: int = typer.Option(1, help="Server nodes the cluster should carry"),
) -> None:
    """Converge the testbed to a runnable state: clusters, HAProxy, Prometheus, node count.

    Idempotent. Prints only the actions it had to take, so a second run with the
    same arguments reports none.
    """
    from infra.readiness import ensure_testbed

    console.rule("[bold]Ensure Testbed")
    result = ensure_testbed(cluster=cluster, servers=servers, agents=agents)

    for action in result["actions"]:
        console.print(f"  [yellow]changed[/yellow] {action}")
    if not result["actions"]:
        console.print("  [green]already in the requested state[/green]")

    nodes = result["nodes"]
    console.print(
        f"  nodes: servers={nodes['servers']} agents={nodes['agents']}"
        f" (+{nodes['dynamic_agents']} dynamic)"
        f"  |  haproxy={'up' if result['haproxy'] else 'down'}"
        f"  |  prometheus={'up' if result['prometheus'] else 'down'}"
    )

    if not (result["haproxy"] and result["prometheus"]):
        raise typer.Exit(1)


@app.command(name="shape-nodes")
def shape_nodes(
    cluster: str = typer.Option("thesis-hybrid", help="k3d cluster name"),
    agents: int = typer.Option(1, help="Static agent nodes to converge to"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Report the change without making it"),
) -> None:
    """Converge the number of static agent nodes.

    The node count decides whether the experiment exercises node provisioning at
    all: with spare agents the node autoscaler never fires, which changes what a
    predictive-scheduling comparison can measure.
    """
    from infra.cluster.k3d.shaping import converge_agent_count

    result = converge_agent_count(cluster, agents, dry_run=dry_run)
    verb = "would change" if dry_run else "changed"
    console.print(f"  agents: {result['before']} -> {result['after']} ({result['dynamic_agents']} dynamic untouched)")
    for action in result["actions"]:
        console.print(f"  [yellow]{verb}[/yellow] {action}")
    if not result["actions"]:
        console.print("  [green]already at the requested count[/green]")


@app.command(name="deploy-app")
def deploy_app(
    skip_build: bool = typer.Option(False, "--skip-build", help="Skip Docker build (use existing image)"),
) -> None:
    """Build and deploy test-app to both clusters (K8s + Knative)."""
    from infra.workloads.deploy import deploy_test_app

    console.rule("[bold]Deploy test-app")
    result = deploy_test_app(skip_build=skip_build)
    for action in result["actions"]:
        console.print(f"  [green]{action}[/green]")

    console.print(
        f"  k8s={'ok' if result['k8s_ok'] else 'FAILED'}  |  knative={'ok' if result['knative_ok'] else 'FAILED'}"
    )
    if not (result["k8s_ok"] and result["knative_ok"]):
        raise typer.Exit(1)


@app.command()
def rebuild(
    agents: int = typer.Option(1, help="Static agent nodes the rebuilt cluster should carry"),
    skip_build: bool = typer.Option(False, "--skip-build", help="Reuse the existing test-app image"),
) -> None:
    """Tear the testbed down and bring it back up, then converge it.

    A run inherits whatever the last one left: nodes the autoscaler kept, pods the
    previous workload left warm, a cluster carrying months of objects. Rebuilding
    removes the whole class. It costs minutes, so it belongs before an experiment,
    not between its runs.
    """
    from infra.readiness import rebuild_testbed

    console.rule("[bold]Rebuild Testbed")
    result = rebuild_testbed(agents=agents, skip_build=skip_build)
    for action in result["actions"]:
        console.print(f"  [yellow]{action}[/yellow]")
    console.print(f"  {result['summary']}")

    if not result["ready"]:
        console.print("[red]Testbed did not come back ready.[/red]")
        raise typer.Exit(1)
