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


@app.command(name="deploy-app")
def deploy_app(
    skip_build: bool = typer.Option(False, "--skip-build", help="Skip Docker build (use existing image)"),
) -> None:
    """Build and deploy test-app to both clusters (K8s + Knative).

    Idempotent: safe to re-run. Rebuilds Docker image, pushes to registry,
    imports to thesis-serverless, applies YAMLs, restarts deployments,
    and verifies both endpoints return expected response with I/O wait.
    """
    import importlib.resources
    import time

    from infra.commands import run

    app_dir = importlib.resources.files("infra").joinpath("workloads", "test_app")
    image = "k3d-registry.localhost:5000/test-app:latest"
    serverless_ctx = "k3d-thesis-serverless"

    # 1. Build Docker image
    if not skip_build:
        console.rule("[bold]Building test-app Docker image")
        run(["docker", "build", "-t", image, str(app_dir)], check=True)
        console.print("[green]✓ Image built[/green]")

        # 2. Push to k3d registry
        run(["docker", "push", image], check=True)
        console.print("[green]✓ Pushed to registry[/green]")

        # 3. Import to thesis-serverless (FAIL if import fails)
        run(["k3d", "image", "import", image, "-c", "thesis-serverless"], check=True)
        console.print("[green]✓ Imported to thesis-serverless[/green]")

    # 3b. Patch Knative to skip tag resolution for local registry
    run(
        [
            "kubectl",
            "--context",
            serverless_ctx,
            "patch",
            "configmap",
            "config-deployment",
            "-n",
            "knative-serving",
            "--type",
            "merge",
            "-p",
            '{"data":{"registries-skipping-tag-resolving":"kind.local,ko.local,dev.local,k3d-registry.localhost:5000"}}',
        ],
        check=False,
    )

    # 4. Apply K8s deployment
    k8s_yaml = str(app_dir.joinpath("test-app-warm-deployment.yaml"))
    run(["kubectl", "apply", "-f", k8s_yaml], check=True)
    run(["kubectl", "rollout", "restart", "deployment/test-app-warm"], check=True)
    console.print("[green]✓ K8s deployment updated[/green]")

    # 5. Force Knative redeploy (delete + recreate picks up new image)
    knative_yaml = str(app_dir.joinpath("knative-service.yaml"))
    run(["kubectl", "--context", serverless_ctx, "delete", "ksvc", "test-app", "--ignore-not-found"], check=False)
    run(["kubectl", "--context", serverless_ctx, "apply", "-f", knative_yaml], check=True)
    console.print("[green]✓ Knative service recreated[/green]")

    # 6. Wait for K8s rollout
    console.print("[bold]Waiting for K8s rollout...")
    run(["kubectl", "rollout", "status", "deployment/test-app-warm", "--timeout=90s"], check=True)

    # 7. Wait for Knative readiness
    console.print("[bold]Waiting for Knative service...")
    run(
        ["kubectl", "--context", serverless_ctx, "wait", "--for=condition=Ready", "ksvc/test-app", "--timeout=120s"],
        check=False,
    )
    time.sleep(5)

    # 8. Verify endpoints
    console.rule("[bold]Verification")
    import requests
    import os

    # K8s endpoint
    haproxy_port = os.environ.get("HAPROXY_HTTP_PORT", "18082")
    r = requests.get(f"http://localhost:{haproxy_port}/fib?n=33", timeout=10)
    k8s_data = r.json()
    k8s_ok = k8s_data.get("io_wait_ms", 0) > 0
    console.print(
        f"  K8s: duration={k8s_data.get('duration_ms')}ms compute={k8s_data.get('compute_ms')}ms io_wait={k8s_data.get('io_wait_ms')}ms"
    )

    # Knative endpoint
    try:
        r2 = requests.get(
            "http://localhost:8083/fib?n=33", headers={"Host": "test-app.default.192.168.0.2.sslip.io"}, timeout=10
        )
        kn_data = r2.json()
        kn_ok = kn_data.get("io_wait_ms", 0) > 0
        console.print(
            f"  Knative: duration={kn_data.get('duration_ms')}ms compute={kn_data.get('compute_ms')}ms io_wait={kn_data.get('io_wait_ms')}ms"
        )
    except Exception as e:
        kn_ok = False
        console.print(f"  [red]Knative: FAILED ({e})[/red]")

    if k8s_ok and kn_ok:
        console.rule("[bold green]Deploy Complete — Both endpoints verified")
    else:
        console.print("[yellow]⚠ One or both endpoints may need time to stabilize[/yellow]")
