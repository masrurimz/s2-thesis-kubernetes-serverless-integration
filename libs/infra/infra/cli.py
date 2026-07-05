"""Infrastructure management CLI — Typer app.

Commands:
    thesis infra setup              Full infrastructure setup
    thesis infra teardown           Tear down everything
    thesis infra health             Health check all components
    thesis infra status             Show infrastructure status
    thesis infra cluster create     Create k3d cluster
    thesis infra cluster delete     Delete k3d cluster
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

    # 2. Install Knative
    knative = KnativeInstaller()
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
